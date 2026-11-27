"""Assertion ledger — the book of record.
Append-only JSONL journal + a dedicated launch partition mounted before
journal replay (C-LaunchPartition). Corrections are later assertions; nothing
is mutated in place. Computed views derive at read time from the full set.
Row shape:
    id         stable local index (a-<n>)
    at         ISO-8601 UTC timestamp
    claimant   closed vocabulary: principal | host | persona:<id> | source:<key>
               | peer:<node> | engine:<name> | system
    kind       predicate namespace — input:*, need:*, persona:*, chat:*,
               source:*, grant:*, fleet:*, exchange:*, speech:*, steward:*, ...
    claim      typed value (object)
    certainty  truth-confidence assigned to this claim (0..1)
    confidence contextual applicability rank (0..1), distinct from certainty
    basis      provenance — captured-input | derived | source-evidence |
               generated-response | execution-evidence | user-choice |
               durable-result | fixture | artifact | assertion:<id>
    relates    ids this row is about/answers/supersedes-context-for
    supersedes id of the earlier row this one corrects (or null)
"""
import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
CLAIMANTS = ("principal", "host", "system")
def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")
class Book:
    """The assertion ledger for one host."""
    def __init__(self, runtime_dir):
        self.dir = runtime_dir
        os.makedirs(self.dir, exist_ok=True)
        os.makedirs(os.path.join(self.dir, "transient"), exist_ok=True)
        self.journal_path = os.path.join(self.dir, "journal.jsonl")
        self.partition_path = os.path.join(self.dir, "partition.jsonl")
        self.rows = []
        self._lock = threading.Lock()
        self._seq = 0
    # ---------- mount ----------
    def write_partition(self, essentials):
        """Materialize the essential launch slice, ordered by modular schema
        dependencies (meta/schema rows first, then durable objects)."""
        ordered = sorted(essentials, key=lambda r: r.get("layer", 9))
        tmp = self.partition_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            for r in ordered:
                f.write(json.dumps(r) + "\n")
        os.replace(tmp, self.partition_path)
        return len(ordered)
    def mount(self):
        """Replay partition + journal into memory."""
        for path in (self.partition_path, self.journal_path):
            if not os.path.exists(path):
                continue
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    self.rows.append(row)
                    try:
                        n = int(str(row.get("id", "0")).split("-")[-1])
                        self._seq = max(self._seq, n)
                    except ValueError:
                        pass
        return len(self.rows)
    def reset_transient(self):
        tdir = os.path.join(self.dir, "transient")
        for name in os.listdir(tdir):
            p = os.path.join(tdir, name)
            if os.path.isfile(p):
                os.remove(p)
    # ---------- write ----------
    def append(self, kind, claim, claimant="host", certainty=0.8, confidence=None,
               basis="derived", relates=None, supersedes=None, durable=True):
        """Sequential commit: one row at a time under the lock."""
        with self._lock:
            self._seq += 1
            row = {
                "id": f"a-{self._seq}",
                "at": now_iso(),
                "claimant": claimant,
                "kind": kind,
                "claim": claim,
                "certainty": certainty,
                "confidence": confidence if confidence is not None else certainty,
                "basis": basis,
                "relates": list(relates or []),
                "supersedes": supersedes,
            }
            self.rows.append(row)
            if durable:
                with open(self.journal_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(row) + "\n")
            return row
    # ---------- read ----------
    def of_kind(self, prefix):
        return [r for r in self.rows if r["kind"] == prefix or r["kind"].startswith(prefix + ":")]
    def find(self, pred):
        return [r for r in self.rows if pred(r)]
    def get(self, rid):
        for r in self.rows:
            if r["id"] == rid:
                return r
        return None
    def current(self, rows=None):
        """Latest non-superseded row per subject key = (kind, claim.subject)."""
        superseded = {r["supersedes"] for r in (rows or self.rows) if r.get("supersedes")}
        best = {}
        for r in (rows or self.rows):
            if r["id"] in superseded:
                continue
            key = (r["kind"], json.dumps(r["claim"].get("subject"), sort_keys=True))
            cur = best.get(key)
            if cur is None or (r["certainty"], r["at"]) >= (cur["certainty"], cur["at"]):
                best[key] = r
        return list(best.values())
    def current_of(self, kind):
        return [r for r in self.current() if r["kind"] == kind]
    def snapshot(self):
        """Consistent read view for parallel inference (C-SnapshotInference)."""
        with self._lock:
            return list(self.rows)
    def append_committed(self, rows):
        """Sequential commit of verified inference outputs (C-SequentialCommit)."""
        out = []
        for r in rows:
            out.append(self.append(**r))
        return out
    def count(self):
        return len(self.rows)
def fresh_id(prefix):
    return f"{prefix}-{uuid.uuid4().hex[:10]}"
