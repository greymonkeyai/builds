"""Append-only assertion ledger: durable JSONL store, computed views, trust.

Rules honored here:
- Append-only. Corrections are new rows carrying `supersedes`.
- Truth is a computed view derived at read time; no second descriptive store.
- An assertion cannot inherit more confidence than its source provides:
  effective_confidence = min(own certainty, source ceiling, context).
- Recency resolves confidence ties between otherwise comparable candidates.
- Cleanup consolidates operational rows without losing provenance.
"""
from __future__ import annotations

import json
import os
import threading
from typing import Any, Callable, Iterable, Optional

from .model import Assertion, make_assertion, now_ms, new_id
from . import governance

# C-LaunchPartition: the essential launch slice mounts from a dedicated launch
# file, materialization ordered by modular schema dependencies. Rank = mount
# order: configuration & sources first (they bound interpretation), then the
# tool/persona identities the surface routes through, then open needs.
PARTITION_RANK = {
    "user-settings": 0, "decision": 0, "routing": 0, "grant": 0,
    "source": 1, "connector": 1,
    "tool": 2, "seed": 2,
    "persona": 3, "chat": 4, "project": 4,
    "need": 5,
}
PARTITION_PREDICATES = {
    "user-settings:", "decision:weights", "routing:stewardship-assignment",
    "routing:intent-override", "grant:issued",
    "source:configured", "source:trust-class", "source:confidence",
    "connector:configured",
    "tool:exists", "tool:definition",
    "persona:exists", "persona:name", "persona:trait", "persona:interest",
    "persona:voice", "persona:lens", "persona:imitates",
    "persona:imitation-mark", "persona:art", "persona:characterization",
    "persona:display-mode", "persona:roster-priority",
    "chat:topic", "chat:context", "chat:context-item", "chat:focus",
    "project:exists", "project:title", "project:kind", "project:status",
    "project:goal", "project:due",
    "need:open", "need:candidate", "need:deferred", "need:refined",
}


def _in_partition(predicate: str) -> bool:
    return any(predicate.startswith(p) for p in PARTITION_PREDICATES)


def _dep_rank(a: Assertion) -> int:
    return PARTITION_RANK.get(a.predicate.split(":", 1)[0], 9)


class SnapshotView:
    """A per-task consistent ledger snapshot (C-SnapshotInference): a frozen
    copy of the rows at snapshot time. Parallel inference tasks read their own
    snapshot — stable state, never another task's uncommitted work."""

    def __init__(self, rows: list, superseded: set, sid: str, at_ms: int):
        self.id = sid
        self.at = at_ms
        self._rows = list(rows)
        self._live = [a for a in self._rows if a.id not in superseded]
        self._superseded = set(superseded)

    def _sel(self, subject=None, predicate=None, claimant=None, since=None,
             include_superseded=False, tag=None):
        rows = self._rows if include_superseded else self._live
        return [a for a in rows
                if (not subject or a.subjectKey == subject)
                and (not predicate or a.predicate == predicate)
                and (not claimant or a.claimant.startswith(claimant))
                and (not since or a.at >= since)
                and (not tag or tag in a.tags)]

    def query(self, subject=None, predicate=None, claimant=None, since=None,
              include_superseded=False, limit=0, tag=None):
        out = self._sel(subject, predicate, claimant, since,
                        include_superseded, tag)
        out.sort(key=lambda x: x.at)
        return out[-limit:] if limit else out

    def search(self, text: str, limit: int = 20,
               include_superseded: bool = False):
        q = text.lower()
        rows = self._rows if include_superseded else self._live
        hits = [a for a in rows if q in
                f"{a.subjectKey} {a.predicate} {json.dumps(a.value, ensure_ascii=False)}".lower()]
        hits.sort(key=lambda x: x.at, reverse=True)
        return hits[:limit]

    def source_ceiling(self, claimant: str) -> float:
        return Ledger.source_ceiling_for(self._sel, claimant)

    def effective_confidence(self, a: Assertion) -> float:
        return min(a.certainty, a.context, self.source_ceiling(a.claimant))

    def candidates_for(self, subject: str, predicate: str) -> list:
        cands = [{
            "value": a.value, "certainty": a.certainty, "context": a.context,
            "effectiveConfidence": round(self.effective_confidence(a), 4),
            "claimant": a.claimant, "assertionId": a.id, "at": a.at,
            "basis": a.basis}
            for a in self.query(subject=subject, predicate=predicate)]
        cands.sort(key=lambda c: (c["effectiveConfidence"], c["at"]),
                   reverse=True)
        return cands

    def stats(self) -> dict:
        return {"total": len(self._rows), "live": len(self._live),
                "snapshot": True, "at": self.at}


class Ledger:
    def __init__(self, path: str, partition_path: Optional[str] = None):
        self.path = path
        self.partition_path = partition_path
        self.partition_mounted = 0
        self._lock = threading.RLock()
        self._rows: list[Assertion] = []
        self._by_id: dict[str, Assertion] = {}
        self._superseded: set[str] = set()
        self._subscribers: list[Callable[[Assertion], None]] = []
        if partition_path:
            self._mount_partition()
        self._load()

    # ---- C-LaunchPartition ----

    def _mount_partition(self) -> None:
        """Mount the dedicated launch file first, materializing its rows in
        modular-schema dependency order (PARTITION_RANK)."""
        if not self.partition_path or not os.path.exists(self.partition_path):
            return
        rows = []
        with open(self.partition_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(Assertion.from_row(json.loads(line)))
        rows.sort(key=lambda a: (_dep_rank(a), a.at))
        self.partition_mounted = sum(1 for a in rows if self._index(a))

    def write_partition(self) -> dict:
        """Persist the essential live slice to the launch file, rows ordered
        by schema dependency then time. Called at checkpoint/clean shutdown."""
        if not self.partition_path:
            return {"written": 0}
        rows = [a for a in self.live() if _in_partition(a.predicate)]
        rows.sort(key=lambda a: (_dep_rank(a), a.at))
        os.makedirs(os.path.dirname(self.partition_path) or ".", exist_ok=True)
        tmp = self.partition_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            for a in rows:
                f.write(json.dumps(a.to_row(), ensure_ascii=False) + "\n")
        os.replace(tmp, self.partition_path)
        return {"written": len(rows), "path": self.partition_path}

    def snapshot(self) -> SnapshotView:
        """Consistent snapshot for parallel foreground inference."""
        with self._lock:
            return SnapshotView(self._rows, self._superseded,
                                new_id("snap"), now_ms())

    @staticmethod
    def source_ceiling_for(sel, claimant: str) -> float:
        if claimant in ("principal", "system") or claimant.startswith(
                ("tool:", "persona:", "steward:", "surface:", "pipeline:",
                 "engine:", "seed:")):
            return 1.0
        if claimant.startswith("exchange:"):
            return governance.IMPORT_CEILING
        if claimant.startswith("source:"):
            sid = claimant.split(":", 1)[1]
            rows = sel(subject=f"source:{sid}", predicate="source:confidence")
            if rows:
                return min(1.0, float(rows[-1].value["v"]))
            rows = sel(subject=f"source:{sid}", predicate="source:trust-class")
            if rows:
                tc = str(rows[-1].value["v"])
                return {"endorsed": 0.95, "configured": 0.8, "observed": 0.6,
                        "unvetted": 0.4}.get(tc, 0.4)
            return 0.5
        if claimant.startswith("model:"):
            return 0.8
        return 0.5

    # ---- persistence ----

    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                a = Assertion.from_row(json.loads(line))
                self._index(a)

    def _index(self, a: Assertion) -> bool:
        """Index a row once — the same assertion may appear in both the
        launch partition and the main ledger file; id is the dedupe key."""
        if a.id in self._by_id:
            return False
        self._rows.append(a)
        self._by_id[a.id] = a
        if a.supersedes:
            self._superseded.add(a.supersedes)
        return True

    def _persist(self, a: Assertion) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(a.to_row(), ensure_ascii=False) + "\n")

    # ---- the single write seam (ledger.append system command) ----

    def append(self, subject: str, predicate: str, value, claimant: str,
               certainty: float = 1.0, context: float = 1.0,
               basis: Optional[dict] = None, supersedes: Optional[str] = None,
               relates: Optional[list] = None, tags: Optional[list] = None,
               meta: Optional[dict] = None) -> Assertion:
        if not governance.known(predicate):
            governance.register(predicate)
        a = make_assertion(subject, predicate, value, claimant, certainty,
                           context, basis, supersedes, relates, tags, meta)
        with self._lock:
            self._index(a)
            self._persist(a)
        for cb in list(self._subscribers):
            try:
                cb(a)
            except Exception:
                pass
        return a

    def append_batch(self, specs: Iterable[dict]) -> list[Assertion]:
        return [self.append(**s) for s in specs]

    def subscribe(self, cb: Callable[[Assertion], None]) -> None:
        self._subscribers.append(cb)

    # ---- queries ----

    def get(self, aid: str) -> Optional[Assertion]:
        return self._by_id.get(aid)

    def is_superseded(self, aid: str) -> bool:
        return aid in self._superseded

    def all(self) -> list[Assertion]:
        return list(self._rows)

    def live(self) -> list[Assertion]:
        return [a for a in self._rows if a.id not in self._superseded]

    def query(self, subject: Optional[str] = None, predicate: Optional[str] = None,
              claimant: Optional[str] = None, since: Optional[int] = None,
              include_superseded: bool = False, limit: int = 0,
              tag: Optional[str] = None) -> list[Assertion]:
        rows = self._rows if include_superseded else self.live()
        out = []
        for a in rows:
            if subject and a.subjectKey != subject:
                continue
            if predicate and a.predicate != predicate:
                continue
            if claimant and not a.claimant.startswith(claimant):
                continue
            if since and a.at < since:
                continue
            if tag and tag not in a.tags:
                continue
            out.append(a)
        out.sort(key=lambda x: x.at)
        if limit:
            out = out[-limit:]
        return out

    def search(self, text: str, limit: int = 20,
               include_superseded: bool = False) -> list[Assertion]:
        """Simple full-text-ish search over subjects, predicates and values."""
        q = text.lower()
        rows = self._rows if include_superseded else self.live()
        hits = []
        for a in rows:
            hay = f"{a.subjectKey} {a.predicate} {json.dumps(a.value, ensure_ascii=False)}".lower()
            if q in hay:
                hits.append(a)
        hits.sort(key=lambda x: x.at, reverse=True)
        return hits[:limit]

    # ---- trust ----

    def source_ceiling(self, claimant: str) -> float:
        """Confidence ceiling a claimant can confer. principal/user-choice and
        witnessed execution confer full; sources confer their configured trust;
        imports are capped below the action threshold."""
        return Ledger.source_ceiling_for(self._sel_for_ceiling, claimant)

    def _sel_for_ceiling(self, subject=None, predicate=None, **kw):
        return self.query(subject=subject, predicate=predicate)

    def effective_confidence(self, a: Assertion) -> float:
        return min(a.certainty, a.context, self.source_ceiling(a.claimant))

    # ---- computed view ----

    def render_view(self, subject: str) -> dict:
        """Computed view: latest non-superseded slot per predicate, resolved
        through supersession + trust. Highest effective confidence wins a slot;
        recency breaks ties."""
        slots: dict[str, dict] = {}
        for a in self.query(subject=subject):
            eff = self.effective_confidence(a)
            cur = slots.get(a.predicate)
            if cur is None or eff > cur["effectiveConfidence"] or (
                eff == cur["effectiveConfidence"] and a.at >= cur["at"]):
                slots[a.predicate] = {
                    "predicate": a.predicate, "value": a.value,
                    "certainty": a.certainty, "context": a.context,
                    "effectiveConfidence": round(eff, 4),
                    "claimant": a.claimant, "assertionId": a.id, "at": a.at,
                    "superseded": False,
                }
        return {"subjectKey": subject, "slots": slots}

    def candidates_for(self, subject: str, predicate: str) -> list[dict]:
        """All live candidate values for a slot, inspectable with source and
        confidence, ranked by effective confidence then recency."""
        cands = []
        for a in self.query(subject=subject, predicate=predicate):
            cands.append({
                "value": a.value, "certainty": a.certainty, "context": a.context,
                "effectiveConfidence": round(self.effective_confidence(a), 4),
                "claimant": a.claimant, "assertionId": a.id, "at": a.at,
                "basis": a.basis,
            })
        cands.sort(key=lambda c: (c["effectiveConfidence"], c["at"]), reverse=True)
        return cands

    # ---- governed cleanup ----

    def compact(self, claimant: str = "steward:cleanup",
                keep_ns: Optional[set] = None) -> dict:
        """Consolidate spent operational rows. Rows eligible for compaction:
        superseded rows in operational namespaces, or superseded need rows.
        Provenance is preserved: a cleanup:compacted summary row records each
        removed id, its subject/predicate, and the superseding row id."""
        keep_ns = keep_ns or set()
        removable = []
        for a in self._rows:
            if a.id not in self._superseded:
                continue
            ns = a.predicate.split(":", 1)[0]
            if ns in governance.OPERATIONAL_NS and ns not in keep_ns:
                removable.append(a)
        if not removable:
            return {"removed": 0, "kept": len(self._rows)}
        summary = [{
            "removedId": a.id, "subject": a.subjectKey, "predicate": a.predicate,
            "at": a.at, "supersededBy": next(
                (r.id for r in self._rows if r.supersedes == a.id), None),
        } for a in removable]
        removed_ids = {a.id for a in removable}
        self.append("ledger", "cleanup:compacted",
                    {"type": "list", "v": summary}, claimant,
                    basis={"kind": "execution"})
        with self._lock:
            self._rows = [a for a in self._rows if a.id not in removed_ids]
            self._by_id = {a.id: a for a in self._rows}
            self._superseded -= removed_ids
            tmp = self.path + ".compact.tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                for a in self._rows:
                    f.write(json.dumps(a.to_row(), ensure_ascii=False) + "\n")
            os.replace(tmp, self.path)
        return {"removed": len(removable), "kept": len(self._rows)}

    def stats(self) -> dict:
        live = self.live()
        ns: dict[str, int] = {}
        for a in live:
            ns[a.predicate.split(":", 1)[0]] = ns.get(a.predicate.split(":", 1)[0], 0) + 1
        return {"total": len(self._rows), "live": len(live),
                "superseded": len(self._rows) - len(live), "namespaces": ns,
                "path": self.path, "durable": os.path.exists(self.path)}
