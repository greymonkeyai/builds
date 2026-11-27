"""Quorum assertion ledger — append-only durable JSONL, computed views,
source-bounded confidence, launch partition, snapshots, governed cleanup.

Contract (prompt §Assertion ledger / §Confidence and selection):
- the ledger is the book of record; computed views stay subordinate to it
- corrections/supersessions append related rows; originals are never
  silently recontextualized
- effective confidence = min(row certainty, applicability, source ceiling) —
  an assertion cannot inherit more confidence than its source provides
- recency resolves a confidence tie; user-set (principal) values outrank
  derived/inferred/source values (C-UserSetSupremacy)
- peer rows import at inherited confidence (decision-candidates §3)
"""
from __future__ import annotations

import json
import os
import threading
from typing import Optional

from . import rows

# Source ceilings — the most confidence a claimant family can bestow.
CEILINGS = {
    "principal": 1.0,      # user-set supremacy (C-UserSetSupremacy)
    "persona:": 0.9,
    "steward:": 0.8,
    "model:": 0.75,        # model verdicts are bounded, never principal-voice
    "source:wikipedia": 0.85,
    "source:vetted": 0.85,
    "source:peer": 0.6,    # peer rejoin correlation
    "source:": 0.7,
    "surface:": 0.95,
    "pipeline:": 0.6,
    "engine:": 0.7,
    "tool:": 0.8,
    "peer:": 0.6,
    "exchange:": 0.4,      # imports land BELOW the action threshold by default
    "seed:": 0.65,
    "system": 0.9,
}
ACTION_THRESHOLD = 0.5     # below: recorded, inspectable, not actionable

# Predicates whose rows are purgeable on cleanup (C-TransientBoundary data).
TRANSIENT_PREDICATES = (
    "sys:transient", "ui:focus-hint", "steward:heartbeat",
)

def ceiling_for(claimant: str) -> float:
    best = 0.5
    for prefix, ceil in CEILINGS.items():
        if claimant == prefix or (prefix.endswith(":") and claimant.startswith(prefix)):
            best = max(best, ceil)
    if claimant.startswith("source:"):
        return CEILINGS.get(claimant, CEILINGS["source:"])
    return best

class Book:
    """The append-only ledger. Truth is computed at read time."""

    def __init__(self, journal_path: str):
        self.path = journal_path
        self.rows: list[rows.Assertion] = []
        self.by_id: dict[str, rows.Assertion] = {}
        self.lock = threading.RLock()
        self.listeners: list = []        # fn(dict) — bus subscribers
        self.seq = 0                     # durable high-water mark (peer exchange)
        os.makedirs(os.path.dirname(journal_path) or ".", exist_ok=True)

    # ---- durability -------------------------------------------------------
    def mount(self) -> int:
        """Replay the journal. Returns mounted row count."""
        if not os.path.exists(self.path):
            return 0
        n = 0
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    a = rows.Assertion.from_row(json.loads(line))
                except Exception:
                    continue
                if a.id not in self.by_id:
                    self.rows.append(a)
                    self.by_id[a.id] = a
                    n += 1
        self.seq = len(self.rows)
        return n

    def mount_partition(self, part_path: str) -> int:
        """C-LaunchPartition: mount the essential launch slice written at
        first-run seeding, before replaying the journal."""
        return self._mount_file(part_path) if os.path.exists(part_path) else 0

    def _mount_file(self, path: str) -> int:
        n = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                a = rows.Assertion.from_row(json.loads(line))
                if a.id not in self.by_id:
                    self.rows.append(a)
                    self.by_id[a.id] = a
                    n += 1
        return n

    # ---- append -----------------------------------------------------------
    def append(self, a: rows.Assertion) -> dict:
        with self.lock:
            self.rows.append(a)
            self.by_id[a.id] = a
            self.seq = len(self.rows)
            d = a.to_row()
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
        for fn in list(self.listeners):
            try:
                fn(d)
            except Exception:
                pass
        return d

    def claim(self, subject, predicate, value, **kw) -> dict:
        return self.append(rows.make(subject, predicate, value, **kw))

    # ---- reads ------------------------------------------------------------
    def find(self, predicate=None, subject=None, text=None, limit=200,
             include_superseded=False) -> list[dict]:
        with self.lock:
            out = []
            for a in self.rows:
                if predicate and a.predicate != predicate:
                    continue
                if subject and a.subject != subject:
                    continue
                if text and text.lower() not in json.dumps(a.to_row(), ensure_ascii=False).lower():
                    continue
                if not include_superseded and self.superseded(a.id):
                    continue
                out.append(a.to_row())
            return out[-limit:]

    def get(self, rid: str) -> Optional[dict]:
        a = self.by_id.get(rid)
        return a.to_row() if a else None

    def superseded(self, rid: str) -> bool:
        for a in self.rows:
            if a.supersedes == rid:
                return True
        return False

    # ---- computed views ---------------------------------------------------
    def effective_confidence(self, a: rows.Assertion) -> float:
        return round(min(a.certainty, a.applicability, ceiling_for(a.claimant)), 4)

    def resolve(self, subject: str, predicate: str) -> Optional[dict]:
        """Computed current view of subject/predicate: the non-superseded row
        with highest effective confidence; recency breaks ties; principal
        claims outrank all derived claims (C-UserSetSupremacy)."""
        cands = []
        for a in self.rows:
            if a.subject != subject or a.predicate != predicate:
                continue
            if self.superseded(a.id):
                continue
            cands.append(a)
        if not cands:
            return None
        princip = [a for a in cands if a.claimant == "principal"]
        pool = princip or cands
        pool.sort(key=lambda a: (self.effective_confidence(a), a.at))
        a = pool[-1]
        d = a.to_row()
        d["effective_confidence"] = self.effective_confidence(a)
        return d

    def view(self, subject: str) -> dict:
        """Computed profile view: latest-resolved value per predicate."""
        preds = []
        for a in self.rows:
            if a.subject == subject and a.predicate not in preds:
                preds.append(a.predicate)
        return {p: self.resolve(subject, p) for p in preds}

    def snapshot(self) -> list[dict]:
        """C-SnapshotInference: a consistent read snapshot for parallel
        foreground inference — tasks see stable state, not each other's
        uncommitted work."""
        with self.lock:
            return [a.to_row() for a in self.rows]

    # ---- peer exchange (decision-candidates §3) ----------------------------
    def rows_after(self, mark: int) -> list[dict]:
        """Delta rows after a peer's high-water mark — append-only union."""
        with self.lock:
            return [a.to_row() for a in self.rows[mark:]]

    def import_rows(self, delta: list[dict], peer_id: str) -> int:
        """Union foreign rows as peer-sourced claims at inherited confidence.
        Never rewrites; supersession resolves conflicts at read time."""
        n = 0
        for d in delta:
            if d["id"] in self.by_id:
                continue
            a = rows.Assertion.from_row(d)
            if not a.claimant.startswith("peer:") and a.claimant != "principal":
                a.claimant = f"peer:{peer_id}"
            elif a.claimant == "principal":
                a.claimant = f"peer:{peer_id}"   # foreign principal ≠ our principal
            a.certainty = min(a.certainty, 0.6)  # inherited peer ceiling
            self.rows.append(a)
            self.by_id[a.id] = a
            n += 1
        with self.lock:
            self.seq = len(self.rows)
        if n:
            with open(self.path, "a", encoding="utf-8") as f:
                for a in self.rows[-n:]:
                    f.write(json.dumps(a.to_row(), ensure_ascii=False) + "\n")
        return n

    # ---- governed cleanup -------------------------------------------------
    def cleanup(self, keep_provenance=True) -> dict:
        """Consolidate without losing provenance/confidence/exceptions.
        Transient rows are purgeable (schema-declared); everything else is
        retained — superseded rows stay for forensics."""
        before = len(self.rows)
        purged = [a for a in self.rows
                  if a.predicate in TRANSIENT_PREDICATES and self.superseded(a.id)]
        if purged:
            purged_ids = {a.id for a in purged}
            self.rows = [a for a in self.rows if a.id not in purged_ids]
            self.by_id = {a.id: a for a in self.rows}
            with open(self.path, "w", encoding="utf-8") as f:
                for a in self.rows:
                    f.write(json.dumps(a.to_row(), ensure_ascii=False) + "\n")
        self.seq = len(self.rows)
        return {"before": before, "purged": len(purged), "after": len(self.rows)}
