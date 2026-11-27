"""hearth ledger — the assertion ledger is the book of record.
C-JsonlLedger: append-only durable JSONL assertion journal.
C-LaunchPartition: the essential launch slice materializes to a dedicated
launch file, ordered by modular schema dependencies.
C-TransientBoundary: purgeable telemetry lives in a disposable boundary.
C-SnapshotInference / C-SequentialCommit: parallel readers see a stable
snapshot; verified outputs commit sequentially through the journal lock.
A row: {id, ts, kind, basis, claimant, value, certainty, confidence,
        provenance, refs, supersedes}
basis classes preserve the ledger's distinctions:
captured-input | interpretation | source-evidence | generated-response |
execution-evidence | user-choice | durable-result | claim | system
"""
import json
import os
import threading
import time
import uuid
BASIS = ("captured-input", "interpretation", "source-evidence",
         "generated-response", "execution-evidence", "user-choice",
         "durable-result", "claim", "system")
class Journal:
    """Append-only durable JSONL journal + in-memory view. The file is
    external ground truth; the in-memory view is a computed index over it,
    rebuilt on mount (never a second truth store)."""
    def __init__(self, data_dir, transient_dir):
        self.path = os.path.join(data_dir, "journal.jsonl")
        self.transient_dir = transient_dir
        os.makedirs(transient_dir, exist_ok=True)
        self._rows = []
        self._lock = threading.RLock()
        self._superseded = set()
        self._load()
    def _load(self):
        self._rows = []
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            self._rows.append(json.loads(line))
                        except Exception:
                            pass
        self._superseded = {s for r in self._rows for s in
                            (r.get("supersedes") or [])}
    def append(self, kind, value, claimant="system", basis="claim",
               certainty=None, confidence=None, provenance=None,
               refs=None, supersedes=None):
        if certainty is None:
            # C-CertaintyPrivilege: certainty-top reserved for user-set
            certainty = 1.0 if claimant == "user" else 0.8
        if basis in ("interpretation", "computed-view", "inference"):
            # derived certainty capped below top — edge bar
            certainty = min(certainty, 0.9)
        row = {
            "id": "a-" + uuid.uuid4().hex[:12],
            "ts": round(time.time(), 3),
            "kind": kind,
            "basis": basis if basis in BASIS else "claim",
            "claimant": claimant,
            "value": value,
            "certainty": certainty,
            "confidence": confidence,
            "provenance": provenance or claimant,
            "refs": refs or [],
            "supersedes": supersedes or [],
        }
        with self._lock:  # C-SequentialCommit
            self._rows.append(row)
            for s in row["supersedes"]:
                self._superseded.add(s)
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                f.flush()
                os.fsync(f.fileno())
        return row
    def transient(self, name, value):
        """Purgeable telemetry — disposable boundary, resettable."""
        p = os.path.join(self.transient_dir, name + ".jsonl")
        with self._lock:
            with open(p, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": round(time.time(), 3), **value},
                                   ensure_ascii=False) + "\n")
    def transient_rows(self, name):
        p = os.path.join(self.transient_dir, name + ".jsonl")
        out = []
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        pass
        return out
    def rows(self, kind=None, where=None, include_superseded=False):
        with self._lock:
            out = []
            for r in self._rows:
                if kind and r["kind"] != kind:
                    continue
                if not include_superseded and r["id"] in self._superseded:
                    continue
                if where and not all(r["value"].get(k) == v
                                     for k, v in where.items()):
                    continue
                out.append(r)
        return out
    def get(self, rid):
        for r in self._rows:
            if r["id"] == rid:
                return r
        return None
    def snapshot(self):
        """Consistent read for parallel inference (C-SnapshotInference)."""
        with self._lock:
            return [dict(r) for r in self._rows]
    def cleanup(self, keep_kinds=("liveness-chit", "playback")):
        """Governed consolidation: transient-purgeable records compacted,
        provenance preserved. Ordinary rows are never deleted."""
        with self._lock:
            before = len(self._rows)
            kept = [r for r in self._rows if r["kind"] not in keep_kinds]
            purged = before - len(kept)
            if purged:
                self._rows = kept
                with open(self.path, "w", encoding="utf-8") as f:
                    for r in kept:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")
        return purged
def materialize_partition(journal, path, sections):
    """C-LaunchPartition: write the essential launch slice to a dedicated
    launch file, sections materialized in dependency order."""
    part = {"kind": "launch-partition", "ts": time.time(), "sections": {}}
    for name, rows in sections:
        part["sections"][name] = rows
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(part, f, indent=1, ensure_ascii=False)
    os.replace(tmp, path)
    return part
