"""ledger — the assertion ledger, book of record (module: ledger).

Append-only durable JSONL assertion journal (C-JsonlLedger). Every user
input becomes a typed, attributed assertion retaining source (claimant),
typed value, certainty, provenance (basis), time, and relationships.
Corrections and supersessions append related assertions — the original
event is never recontextualized silently.

Conventions: C-JsonlLedger, C-LocalIndices, C-CertaintyPrivilege (certainty
top reserved for user-set values), C-UserSetSupremacy (user-set outranks
derived regardless of support), C-TransientBoundary (purgeable rows live in
a disposable boundary), C-SnapshotInference (readers fold their own
consistent snapshot), C-SequentialCommit (verified outputs commit in
order), C-ContactTags.
"""

import json
import os
import threading
import time
import uuid

CERTAINTY_TOP = 1.0           # privileged: user-set values only (C-CertaintyPrivilege)
DERIVED_CEILING = 0.9         # derived values can never reach the top
IMPORT_CEILING = 0.25         # exchange-imported assertions enter below threshold
SOURCE_CEILINGS = {}          # per-source ceilings applied at read


def _now():
    return time.time()


def new_id(prefix="a"):
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


class Journal:
    """Append-only durable journal. One file per host; readers fold
    snapshots — parallel tasks see stable state (C-SnapshotInference)."""

    def __init__(self, path):
        self.path = path
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        if not os.path.exists(path):
            open(path, "a", encoding="utf-8").close()

    def append(self, kind, value=None, claimant="system", basis="derived",
               certainty=None, confidence=None, supersedes=None, relates=None,
               tags=None, transient=False, **fields):
        """Append one typed, attributed assertion. Returns the row."""
        if certainty is None:
            certainty = CERTAINTY_TOP if claimant == "principal" and basis == "user-set" else 0.6
        if claimant != "principal" or basis != "user-set":
            certainty = min(certainty, DERIVED_CEILING)   # C-CertaintyPrivilege
        row = {
            "id": new_id(),
            "at": _now(),
            "kind": kind,
            "value": value,
            "claimant": claimant,
            "basis": basis,
            "certainty": certainty,
            "confidence": confidence if confidence is not None else certainty,
            "supersedes": supersedes,
            "relates": list(relates or []),
            "tags": list(tags or []),
            "transient": bool(transient),
        }
        row.update(fields)
        line = json.dumps(row, ensure_ascii=False)
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        return row

    def rows(self):
        """All rows as a fresh list — a consistent snapshot per caller.
        Dict-valued `value` payloads are flattened to row top level so
        consumers read fields directly; `value` stays for typed values."""
        if getattr(self, "empty_store", False):
            return []   # sabotage: the store reads empty
        out = []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            r = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if isinstance(r.get("value"), dict):
                            r = {**r["value"], **r}
                        out.append(r)
        except FileNotFoundError:
            pass
        return out


class TransientStore:
    """Disposable boundary for purgeable rows (C-TransientBoundary):
    playback telemetry, liveness ticks, discovery progress — resettable
    independently of the durable journal."""

    def __init__(self, path):
        self.path = path
        os.makedirs(path, exist_ok=True)

    def write(self, name, obj):
        with open(os.path.join(self.path, name), "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)

    def read(self, name, default=None):
        try:
            with open(os.path.join(self.path, name), "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default

    def reset(self):
        for n in os.listdir(self.path):
            try:
                os.remove(os.path.join(self.path, n))
            except OSError:
                pass


class Ledger:
    """The book of record. Computed views fold rows at read time;
    supersession is resolved by certainty then recency (C-CertaintyPrivilege
    mechanics beneath C-UserSetSupremacy)."""

    def __init__(self, data_dir):
        self.dir = data_dir
        self.journal = Journal(os.path.join(data_dir, "journal.jsonl"))
        self.transient = TransientStore(os.path.join(data_dir, "transient"))
        self.indices_path = os.path.join(data_dir, "indices.json")
        self._indices = self._load_indices()

    # -- local indices for persistent objects (C-LocalIndices) --
    def _load_indices(self):
        try:
            with open(self.indices_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"persona": 0, "tool": 0, "need": 0, "project": 0, "list": 0,
                    "workshop": 0, "node": 0, "artifact": 0, "channel": 0}

    def next_index(self, kind):
        self._indices[kind] = self._indices.get(kind, 0) + 1
        with open(self.indices_path, "w", encoding="utf-8") as f:
            json.dump(self._indices, f)
        return self._indices[kind]

    # -- append helpers --
    def append(self, kind, value=None, **kw):
        return self.journal.append(kind, value=value, **kw)

    # -- computed views (subordinate to the journal, never a second truth) --
    def view(self):
        rows = self.journal.rows()
        return fold(rows)

    def snapshot(self):
        """A consistent view for a parallel inference task
        (C-SnapshotInference): the caller folds this row set and sees
        stable state, not another task's uncommitted work."""
        return self.journal.rows()

    # -- cleanup: governed consolidation preserving provenance --
    def cleanup(self):
        """Consolidate the journal: superseded rows are retained (provenance
        is never lost) but compacted alongside their supersessions; transient
        rows age out of the durable file into the transient boundary."""
        rows = self.journal.rows()
        before = len(rows)
        durable = [r for r in rows if not r.get("transient")]
        transient = [r for r in rows if r.get("transient")]
        kept_ids = {r["id"] for r in durable}
        # keep supersession chains intact — never drop a row still referenced
        for r in durable:
            sup = r.get("supersedes")
            while sup and sup not in kept_ids:
                kept_ids.add(sup)
                sup = None
        for r in transient:
            self.transient.write(f"archived-{r['id']}.json", r)
        tmp = self.journal.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            for r in durable:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        os.replace(tmp, self.journal.path)
        return {"before": before, "after": len(durable),
                "transientArchived": len(transient),
                "supersededRetained": sum(1 for r in durable if r.get("supersedes")) or
                                    sum(1 for r in durable if any(x.get("supersedes") == r["id"] for x in durable))}

    # -- launch partition (C-LaunchPartition) --
    def write_partition(self):
        """Materialize the essential launch slice into a dedicated launch
        file, ordered by modular schema dependencies."""
        v = self.view()
        partition = {
            "generatedAt": _now(),
            "order": ["settings", "personas", "needs", "sources", "projects",
                      "fleet", "stage", "exchange", "gate"],
            "settings": v.get("settings", {}),
            "personaCount": len(v.get("personas", {})),
            "openNeeds": len(v.get("needs_open", {})),
            "sourceCount": len(v.get("sources", {})),
            "journalRows": self.count(),
        }
        path = os.path.join(self.dir, "partition.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(partition, f, ensure_ascii=False, indent=1)
        return path

    def mount_partition(self):
        try:
            with open(os.path.join(self.dir, "partition.json"), "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def count(self):
        n = 0
        try:
            with open(self.journal.path, "r", encoding="utf-8") as f:
                for _ in f:
                    n += 1
        except FileNotFoundError:
            pass
        return n


def fold(rows):
    """Fold journal rows into the computed view. Superseded rows resolve
    by certainty, then recency (newer wins ties — C-CertaintyPrivilege);
    user-set claims are never superseded by derived claims
    (C-UserSetSupremacy)."""
    v = {
        "inputs": [], "needs": {}, "needs_open": {}, "personas": {},
        "roster": [], "tools": {}, "compositions": {}, "sources": {},
        "projects": {}, "lists": {}, "workshops": {}, "settings": {},
        "replies": [], "floor": [], "devices": {}, "members": {},
        "artifacts": {}, "channels": {}, "interstitials": {}, "scenes": [],
        "accounts": {}, "exchange": [], "needs_all": {}, "need_events": [],
        "grants": [], "themes": {}, "emails": [], "metrics": [],
        "liveness": [], "gate": None, "needs_fulfilled": {}, "need_candidates": {},
        "persona_sources": {}, "audience": {}, "dyadic": {}, "assignments": {},
        "context": None, "acknowledgements": {}, "assets": {}, "ui_events": [],
        "publications": [], "claims_review": [], "voice_specs": {},
    }
    by_id = {r["id"]: r for r in rows}
    superseded = {r.get("supersedes") for r in rows if r.get("supersedes")}

    def live(r):
        """A row is superseded only by a row of equal/higher standing —
        user-set (principal/user-set) rows are never displaced by derived
        rows (C-UserSetSupremacy)."""
        if r["id"] not in superseded:
            return True
        for other in rows:
            if other.get("supersedes") == r["id"]:
                if r["claimant"] == "principal" and r["basis"] == "user-set" \
                        and not (other["claimant"] == "principal" and other["basis"] == "user-set"):
                    continue  # derived cannot displace user-set
                if other["certainty"] >= r["certainty"] or other["at"] >= r["at"]:
                    return False
        return True

    for r in rows:
        k = r.get("kind", "")
        val = r.get("value")
        if k == "input:captured":
            v["inputs"].append(r)
        elif k == "need:candidate" and live(r):
            v["need_candidates"].setdefault(r.get("need"), []).append(r)
        elif k == "need:slot-filled" and live(r):
            v["need_events"].append(r)
        elif k.startswith("need:"):
            v["needs_all"].setdefault(r.get("need") or r["id"], []).append(r)
            if r.get("need") and live(r):
                st = r.get("state", "open")
                nid = r["need"]
                v["needs"][nid] = r
                if st in ("open", "focused"):
                    v["needs_open"][nid] = r
                else:
                    v["needs_open"].pop(nid, None)
                if st == "fulfilled":
                    v["needs_fulfilled"][nid] = r
            v["need_events"].append(r)
        elif k == "persona:minted" or k == "persona:extended" or k == "persona:edited":
            pid = r.get("persona")
            cur = v["personas"].get(pid, {})
            if live(r):
                merged = dict(cur)
                for fkey in ("name", "register", "interests", "projects",
                             "character", "voice", "portrait", "surface",
                             "style", "imitation", "history", "domains"):
                    if r.get(fkey) is not None:
                        merged[fkey] = r[fkey]
                merged["id"] = pid
                merged["mintedAt"] = cur.get("mintedAt") or r["at"]
                v["personas"][pid] = merged
        elif k == "roster:order" and live(r):
            v["roster"] = r.get("order", v["roster"])
        elif k == "dyadic:held-confidence" and live(r):
            v["dyadic"][r.get("persona")] = r.get("confidence")
        elif k == "persona:surface" and live(r):
            v["assignments"][r.get("persona")] = r.get("surface")
        elif k == "persona:source-grant" and live(r):
            v["persona_sources"].setdefault(r.get("persona"), []).append(r.get("source"))
        elif k == "tool:registered" and live(r):
            v["tools"][r.get("tool")] = r
        elif k == "tool:composition" and live(r):
            v["compositions"][r.get("composition")] = r
        elif k == "source:configured" and live(r):
            v["sources"][r.get("source")] = r
        elif k == "source:admission" and live(r):
            s = v["sources"].get(r.get("source"))
            if s is not None:
                s = dict(s)
                s["admission"] = r
                v["sources"][r.get("source")] = s
        elif k == "project:opened" or k == "project:advanced" or k == "project:closed":
            pid = r.get("project")
            cur = v["projects"].get(pid, {"goals": [], "events": []})
            cur = dict(cur)
            cur["id"] = pid
            if k == "project:opened":
                cur["title"] = r.get("title")
                cur["openedAt"] = r["at"]
                cur["state"] = "open"
            cur["events"] = cur.get("events", []) + [r]
            if r.get("goal"):
                cur["goals"] = cur.get("goals", []) + [r["goal"]]
            if k == "project:closed" and live(r):
                cur["state"] = "closed"
            v["projects"][pid] = cur
        elif k == "list:created" and live(r):
            v["lists"][r.get("list")] = {"id": r.get("list"), "title": r.get("title"),
                                         "criteria": r.get("criteria"), "members": [],
                                         "nonMatches": [], "createdAt": r["at"]}
        elif k == "list:member":
            l = v["lists"].get(r.get("list"))
            if l is not None:
                l["members"] = l["members"] + [r]
        elif k == "list:nonmatch":
            l = v["lists"].get(r.get("list"))
            if l is not None:
                l["nonMatches"] = l["nonMatches"] + [r]
        elif k == "workshop:minted" and live(r):
            v["workshops"][r.get("workshop")] = r
        elif k == "reply:committed" or k == "reply:uttered":
            v["replies"].append(r)
        elif k == "speech:floor":
            v["floor"].append(r)
        elif k == "settings:set" and live(r):
            inner = r.get("value")
            scalar = inner.get("value") if isinstance(inner, dict) else inner
            v["settings"][r.get("setting")] = {"value": scalar, "row": r}
        elif k == "preload:applied" and live(r):
            v["settings"]["preload"] = r
        elif k == "device:found" and live(r):
            v["devices"][r.get("ip") or r.get("device")] = r
        elif k == "fleet:member" and live(r):
            v["members"][r.get("node") or r.get("device")] = r
        elif k == "fleet:roster-report":
            v.setdefault("roster_reports", []).append(r)
        elif k == "artifact:encoded" or k == "artifact:decoded":
            v["artifacts"][r.get("artifact") or r["id"]] = r
        elif k == "exchange:exported" or k == "exchange:imported":
            v["exchange"].append(r)
        elif k == "channel:opened" and live(r):
            v["channels"][r.get("channel")] = r
        elif k == "interstitial:queued" or k == "interstitial:ready" or k == "interstitial:presented" \
                or k == "interstitial:deferred" or k == "interstitial:rework":
            iid = r.get("interstitial")
            cur = dict(v["interstitials"].get(iid, {}))
            cur["id"] = iid
            cur["state"] = k.split(":", 1)[1]
            cur.setdefault("events", []).append(r)
            for fk in ("title", "assets", "script", "style"):
                if r.get(fk) is not None:
                    cur[fk] = r[fk]
            v["interstitials"][iid] = cur
        elif k == "scene:enacted":
            v["scenes"].append(r)
        elif k == "account:configured" and live(r):
            v["accounts"][r.get("account") or r.get("source")] = r
        elif k == "email:received" or k == "email:context":
            v["emails"].append(r)
        elif k == "metric:recorded":
            v["metrics"].append(r)
        elif k == "steward:liveness":
            v["liveness"].append(r)
        elif k == "gate:passed":
            v["gate"] = r
        elif k == "context:topic" and live(r):
            v["context"] = r
        elif k == "ack:prepared" and live(r):
            v["acknowledgements"][r.get("persona")] = r
        elif k == "asset:produced" and live(r):
            v["assets"].setdefault(r.get("need") or r.get("persona") or "misc", []).append(r)
        elif k == "grant:recorded":
            v["grants"].append(r)
        elif k == "publish:produced" or k == "publish:deferred":
            v["publications"].append(r)
        elif k == "claim:review" and live(r):
            v["claims_review"].append(r)
        elif k == "voice:spec" and live(r):
            v["voice_specs"][r.get("persona")] = r
        elif k == "ui:event":
            v["ui_events"].append(r)
    return v
