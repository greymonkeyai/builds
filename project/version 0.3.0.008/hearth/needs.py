"""hearth needs — the unmet-requirement floor.
A need is a ledger assertion governed by a template: slots, candidate
values, acceptance tests, required/optional info, satisfaction conditions.
Creation != execution. The floor shows open needs only (C-FloorLifecycle):
met needs leave the open list.
Queue completion (S-need-queue-completion): the steward executes once
every required slot holds an above-threshold candidate; below threshold
the user selects the template to fix candidates or force-execute — the
recorded intentional choice that crosses the threshold.
"""
import time
# Each template declares its slots; slot = {name, required, threshold,
# test(fn candidate->bool)}. Tests are executable adequacy checks
# (C-AcceptanceChecks).
TEMPLATES = {
    "list-build": {
        "desc": "Build a formal list matching criteria",
        "slots": [
            {"name": "criteria", "required": True, "threshold": 0.5,
             "test": lambda v: isinstance(v, str) and len(v) > 2},
            {"name": "scope", "required": False, "threshold": 0.4,
             "test": lambda v: True},
        ],
        "satisfied": "list members retrieved and criteria preserved"},
    "portrait-asset": {
        "desc": "Produce and bind persona portrait art",
        "slots": [{"name": "persona", "required": True, "threshold": 0.5,
                   "test": lambda v: bool(v)}],
        "satisfied": "portrait file produced and bound"},
    "ack-asset": {
        "desc": "Pre-generate an audible ack snippet for a persona",
        "slots": [{"name": "persona", "required": True, "threshold": 0.5,
                   "test": lambda v: bool(v)}],
        "satisfied": "ack snippet wav produced and bound"},
    "channel-asset": {
        "desc": "Produce a background audio channel",
        "slots": [{"name": "mood", "required": True, "threshold": 0.5,
                   "test": lambda v: bool(v)}],
        "satisfied": "channel wav produced and playing"},
    "interstitial-asset": {
        "desc": "Prepare an interstitial presentation",
        "slots": [{"name": "topic", "required": True, "threshold": 0.5,
                   "test": lambda v: bool(v)}],
        "satisfied": "assets collected, presentation ready"},
    "source-admission": {
        "desc": "Verify a proposed configured source",
        "slots": [{"name": "sourceKey", "required": True, "threshold": 0.5,
                   "test": lambda v: bool(v)}],
        "satisfied": "admission verdict recorded"},
    "user-request": {
        "desc": "Open-ended unmet user request drained by the steward",
        "slots": [{"name": "request", "required": True, "threshold": 0.6,
                   "test": lambda v: bool(v)}],
        "satisfied": "a bound tool ran and the result satisfied"},
}
class Needs:
    def __init__(self, host):
        self.h = host
    def open(self, template, slots=None, claimant="system",
             provenance=None, desc=None):
        tpl = TEMPLATES.get(template, {})
        need = {
            "template": template, "desc": desc or tpl.get("desc", template),
            "state": "open", "openedAt": time.time(),
            "focus": False, "satisfied": None,
            "slots": {s["name"]: {"required": s["required"],
                                  "threshold": s["threshold"]}
                      for s in tpl.get("slots", [])},
            "boundTool": None,
        }
        row = self.h.journal.append("need", need, claimant=claimant,
                                    basis="claim", provenance=provenance)
        # candidates seeded from supplied slots
        for name, cv in (slots or {}).items():
            self.candidate(row["id"], name, cv["value"],
                           cv.get("confidence", 0.6),
                           cv.get("source", claimant))
        return row
    def candidate(self, need_id, slot, value, confidence, source):
        return self.h.journal.append(
            "need-candidate",
            {"need": need_id, "slot": slot, "value": value,
             "failed": False},
            claimant=source, basis="interpretation",
            confidence=confidence, provenance=source)
    def candidates(self, need_id, slot=None):
        rows = self.h.journal.rows("need-candidate",
                                 where={"need": need_id})
        if slot:
            rows = [r for r in rows if r["value"]["slot"] == slot]
        return rows
    def best(self, need_id, slot):
        cands = [r for r in self.candidates(need_id, slot)
                 if not r["value"].get("failed")]
        if not cands:
            return None
        # confidence ranks; recency breaks ties
        cands.sort(key=lambda r: (r["confidence"] or 0, r["ts"]))
        return cands[-1]
    def get(self, need_id):
        return self.h.journal.get(need_id)
    def view(self, need_id):
        row = self.get(need_id)
        if not row:
            return None
        v = dict(row["value"])
        v["id"] = row["id"]
        v["candidates"] = {s: [{"value": c["value"]["value"],
                                "confidence": c["confidence"],
                                "source": c["provenance"],
                                "failed": c["value"].get("failed", False)}
                               for c in self.candidates(need_id, s)]
                           for s in v["slots"]}
        v["ready"] = self.ready(row)
        return v
    def ready(self, need_row):
        """Every required slot holds an above-threshold candidate."""
        tpl = TEMPLATES.get(need_row["value"]["template"], {})
        for s in tpl.get("slots", []):
            if not s["required"]:
                continue
            spec = need_row["value"]["slots"].get(s["name"])
            if not spec:
                return False
            b = self.best(need_row["id"], s["name"])
            if not b or (b["confidence"] or 0) < spec["threshold"]:
                return False
            try:
                if not s["test"](b["value"]["value"]):
                    return False
            except Exception:
                return False
        return True
    def focus(self, need_id):
        self.h.journal.append("need-state", {"need": need_id,
                                             "focus": True},
                              claimant="user", basis="user-choice")
    def fill(self, need_id, slot, value, confidence=0.9,
             source="user", supersede_id=None):
        """Conversational slot-fill: a candidate appended; a fix
        supersedes the prior candidate rather than rewriting it."""
        return self.h.journal.append(
            "need-candidate",
            {"need": need_id, "slot": slot, "value": value,
             "failed": False},
            claimant=source, basis="user-choice" if source == "user"
            else "interpretation",
            confidence=confidence, provenance=source,
            supersedes=[supersede_id] if supersede_id else [])
    def bind_tool(self, need_id, tool_id):
        self.h.journal.append("need-state",
                              {"need": need_id, "boundTool": tool_id},
                              claimant="steward", basis="claim")
        row = self.get(need_id)
        row["value"]["boundTool"] = tool_id
    def transition(self, need_id, state, result=None, claimant="steward",
                   basis="durable-result"):
        self.h.journal.append("need-state",
                              {"need": need_id, "state": state,
                               "result": result},
                              claimant=claimant, basis=basis,
                              refs=[need_id])
        row = self.get(need_id)
        if row:
            row["value"]["state"] = state
            row["value"]["satisfied"] = result
    def floor(self):
        """The unmet floor — open needs only; met/cancelled/superseded
        leave the list (C-FloorLifecycle)."""
        out = []
        latest = {}
        for r in self.h.journal.rows("need"):
            latest[r["id"]] = r
        for st in self.h.journal.rows("need-state"):
            nid = st["value"].get("need")
            if nid in latest:
                if "state" in st["value"]:
                    latest[nid]["value"]["state"] = st["value"]["state"]
                    latest[nid]["value"]["satisfied"] = \
                        st["value"].get("result")
                if st["value"].get("focus"):
                    latest[nid]["value"]["focus"] = True
                if st["value"].get("boundTool"):
                    latest[nid]["value"]["boundTool"] = \
                        st["value"]["boundTool"]
        for nid, r in latest.items():
            if r["value"].get("state") == "open":
                v = self.view(nid)
                out.append(v)
        return out
    def drainable(self):
        return [n for n in self.floor() if n.get("ready")]
