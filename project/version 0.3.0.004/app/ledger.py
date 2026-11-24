"""Vantage assertion ledger — append-only durable JSONL, computed views,
source-bounded confidence, launch partition, snapshots, governed cleanup.
Design contract (prompt §Assertion ledger):
- the ledger is the book of record; computed views stay subordinate to it
- corrections/supersessions append related rows; the original is never
  silently recontextualized
- an assertion cannot inherit more confidence than its source provides:
  effective confidence = min(row certainty, applicability, source ceiling)
- recency resolves a confidence tie (prompt §Confidence and selection)
- user-set values outrank derived/inferred/source values regardless of
  support (C-UserSetSupremacy) — claimant `principal` wins resolution
"""
from __future__ import annotations
import json
import os
import threading
from typing import Iterable, Optional
from . import model
DEFAULT_CEILINGS = {
    "principal": 1.0,     # the user — source of truth for their own input
    "persona:": 0.9,      # a personality speaking for itself
    "steward:": 0.8,
    "model:": 0.75,       # inference output is never fully certain
    "source:wikipedia": 0.85,
    "source:": 0.7,       # generic configured sources
    "surface:": 0.95,     # what a surface physically showed
    "pipeline:": 0.6,
    "engine:": 0.7,
    "tool:": 0.8,
    "exchange:": 0.4,     # imports land BELOW the action threshold
    "seed:": 0.65,
    "system": 0.9,
}
ACTION_THRESHOLD = 0.5    # below this: recorded, but not actionable/accepted
class Ledger:
    def __init__(self, path: str):
        self.path = path
        self.rows: list[model.Assertion] = []
        self.by_id: dict[str, model.Assertion] = {}
        self.lock = threading.RLock()
        self.subscribers = []          # fn(row_dict) — bus fan-out
        os.makedirs(os.path.dirname(path), exist_ok=True)
    # -- durability ----------------------------------------------------------
    def load(self) -> int:
        """Replay the journal. Returns row count mounted."""
        if not os.path.exists(self.path):
            return 0
        n = 0
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                a = model.Assertion.from_row(json.loads(line))
                if a.id not in self.by_id:
                    self.rows.append(a)
                    self.by_id[a.id] = a
                    n += 1
        return n
    def mount_partition(self, path: str) -> int:
        """C-LaunchPartition: the essential launch slice mounts FIRST, in
        schema-dependency order (as written), deduped against the journal."""
        if not os.path.exists(path):
            return 0
        n = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                a = model.Assertion.from_row(json.loads(line))
                if a.id not in self.by_id:
                    self.rows.append(a)
                    self.by_id[a.id] = a
                    n += 1
        return n
    def write_partition(self, path: str, predicates: list[str]) -> int:
        """Checkpoint the essential slice: newest row per (subject,predicate)
        for each partition predicate, written in the predicate order given
        (schema-dependency order chosen by the caller)."""
        picked = []
        seen = set()
        for p in predicates:
            for a in sorted(self.query(predicate=p, current=True),
                            key=lambda r: r.at):
                if a.id not in seen:
                    picked.append(a)
                    seen.add(a.id)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            for a in picked:
                f.write(json.dumps(a.row(), ensure_ascii=False) + "\n")
        os.replace(tmp, path)
        return len(picked)
    # -- writes --------------------------------------------------------------
    def append(self, a: model.Assertion) -> model.Assertion:
        """Single write seam. Every write is durable before it is visible."""
        with self.lock:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(a.row(), ensure_ascii=False) + "\n")
            self.rows.append(a)
            self.by_id[a.id] = a
        row = a.row()
        for fn in list(self.subscribers):
            try:
                fn(row)
            except Exception:
                pass
        return a
    def say(self, subject, predicate, value, claimant="system",
            certainty=1.0, applicability=1.0, basis=None, supersedes=None,
            links=None, tags=None, meta=None):
        return self.append(model.assert_that(
            subject, predicate, value, claimant, certainty, applicability,
            basis, supersedes, links, tags, meta))
    # -- reads ---------------------------------------------------------------
    def query(self, subject=None, predicate=None, claimant=None, text=None,
              limit=200, current=False, basis_kind=None, tag=None,
              include_superseded=None) -> list[model.Assertion]:
        superseded_ids = self._superseded_ids()
        out = []
        for a in reversed(self.rows):
            if subject and a.subject != subject:
                continue
            if predicate and a.predicate != predicate:
                continue
            if claimant and not a.claimant.startswith(claimant.rstrip(":") + ":") \
                    and a.claimant != claimant:
                continue
            if basis_kind and a.basis.get("kind") != basis_kind:
                continue
            if tag and tag not in a.tags:
                continue
            if current and a.id in superseded_ids:
                continue
            if include_superseded is False and a.id in superseded_ids:
                continue
            if text:
                hay = json.dumps(a.value, ensure_ascii=False).lower()
                if text.lower() not in hay and text.lower() not in a.subject.lower():
                    continue
            out.append(a)
            if len(out) >= limit:
                break
        return out
    def _superseded_ids(self) -> set:
        return {a.supersedes for a in self.rows if a.supersedes}
    def get(self, aid: str) -> Optional[model.Assertion]:
        return self.by_id.get(aid)
    # -- confidence -----------------------------------------------------------
    def ceiling(self, claimant: str) -> float:
        """Per-source ceilings (C-SourceCeilings). Config rows may override:
        predicate `source:ceiling`, subject `source:<name>` → number."""
        for a in self.query(predicate="source:ceiling"):
            v = a.value.get("v")
            if isinstance(v, dict) and claimant.startswith(v.get("claimant", "~")):
                return max(0.0, min(1.0, float(v.get("ceiling", 1.0))))
        for prefix, c in DEFAULT_CEILINGS.items():
            if prefix.endswith(":"):
                if claimant.startswith(prefix):
                    return c
            elif claimant == prefix:
                return c
        return 0.5
    def effective(self, a: model.Assertion) -> float:
        return min(a.certainty, a.applicability, self.ceiling(a.claimant))
    # -- computed views --------------------------------------------------------
    def resolve(self, subject: str, predicate: str) -> Optional[model.Assertion]:
        """Computed view: current (unsuperseded) winner for (subject, predicate).
        User-set wins regardless of support (C-UserSetSupremacy); otherwise
        highest effective confidence; recency breaks ties (C-CertaintyPrivilege)."""
        cands = self.query(subject=subject, predicate=predicate, current=True)
        if not cands:
            return None
        user = [a for a in cands if a.claimant == "principal"]
        if user:
            return max(user, key=lambda a: a.at)
        return max(cands, key=lambda a: (self.effective(a), a.at))
    def view(self, subject: str) -> dict:
        """render the whole computed view of a subject."""
        out = {}
        superseded = self._superseded_ids()
        preds = sorted({a.predicate for a in self.rows
                        if a.subject == subject and a.id not in superseded})
        for p in preds:
            a = self.resolve(subject, p)
            if a:
                out[p] = {"value": a.value.get("v"), "claimant": a.claimant,
                          "certainty": a.certainty,
                          "effective": round(self.effective(a), 3),
                          "at": a.at, "id": a.id}
        return out
    def candidates(self, subject: str, predicate: str) -> list[dict]:
        """Candidate values remain inspectable with source and confidence."""
        superseded = self._superseded_ids()
        rows = [a for a in self.rows if a.subject == subject
                and a.predicate == predicate]
        ranked = sorted(
            (a for a in rows if a.id not in superseded),
            key=lambda a: (self.effective(a), a.at), reverse=True)
        return [{"id": a.id, "value": a.value.get("v"), "claimant": a.claimant,
                 "certainty": a.certainty,
                 "effective": round(self.effective(a), 3),
                 "superseded": a.id in superseded,
                 "at": a.at} for a in ranked]
    # -- snapshots (C-SnapshotInference) ----------------------------------------
    def snapshot(self) -> "Snapshot":
        return Snapshot([a for a in self.rows], self)
    # -- governed cleanup --------------------------------------------------------
    def compact(self, predicates: list[str], keep: int = 3) -> dict:
        """Consolidation: supersede all but the newest `keep` current rows per
        (subject,predicate) for the given operational predicates. Provenance
        is preserved — the compacted ids are recorded in a cleanup summary row,
        and the rows themselves remain in the journal (superseded, not deleted).
        """
        by_sp: dict[tuple, list] = {}
        superseded = self._superseded_ids()
        for a in self.rows:
            if a.predicate in predicates and a.id not in superseded:
                by_sp.setdefault((a.subject, a.predicate), []).append(a)
        removed = []
        for (s, p), rows in by_sp.items():
            rows.sort(key=lambda a: a.at)
            for old in rows[:-keep]:
                self.say(s, p, {"v": "consolidated", "consolidatedId": old.id},
                         claimant="system", certainty=1.0,
                         basis={"kind": "execution"},
                         supersedes=old.id, tags=["cleanup"])
                removed.append(old.id)
        if removed:
            self.say("ledger", "cleanup:compacted",
                     {"removedIds": removed, "predicates": predicates,
                      "keep": keep},
                     claimant="system", certainty=1.0,
                     basis={"kind": "durable-result"})
        return {"removed": len(removed), "ids": removed}
class Snapshot:
    """A consistent read view: parallel inference tasks each read their own
    stable snapshot — never each other's uncommitted work (C-SnapshotInference)."""
    def __init__(self, rows: list[model.Assertion], ledger: "Ledger"):
        self.rows = rows
        self.superseded = {a.supersedes for a in rows if a.supersedes}
        self._ledger = ledger  # for ceiling only (config is stable state)
    def query(self, subject=None, predicate=None, limit=100, current=False):
        out = []
        for a in reversed(self.rows):
            if subject and a.subject != subject:
                continue
            if predicate and a.predicate != predicate:
                continue
            if current and a.id in self.superseded:
                continue
            out.append(a)
            if len(out) >= limit:
                break
        return out
    def resolve(self, subject, predicate):
        cands = self.query(subject=subject, predicate=predicate, current=True)
        if not cands:
            return None
        user = [a for a in cands if a.claimant == "principal"]
        if user:
            return max(user, key=lambda a: a.at)
        return max(cands, key=lambda a: (
            min(a.certainty, a.applicability,
                self._ledger.ceiling(a.claimant)), a.at))
    def view(self, subject):
        out = {}
        preds = sorted({a.predicate for a in self.rows
                        if a.subject == subject and a.id not in self.superseded})
        for p in preds:
            a = self.resolve(subject, p)
            if a:
                out[p] = a.value.get("v")
        return out
