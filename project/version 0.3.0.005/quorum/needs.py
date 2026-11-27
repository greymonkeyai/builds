"""Quorum unmet-need floor — need:* lifecycle.

(prompt §Work and unfulfilled requirements; C-UnmetNeedRecords;
decision-candidates §2 need:request, §4 display contract)

A detected tool opportunity becomes a need row governed by a template:
slots, candidate values, tests, required/optional info, satisfaction
conditions. Creation never implies execution. A need stays Open until its
satisfaction conditions are met, or it is Cancelled / Superseded.

Need predicates in force:
- need:tool-request — an open call to a KNOWN tool (open tool call)
- need:list        — a progressive list requirement (criteria preserved)
- need:response    — conversational reply owed to the user
- need:request     — the user asked for something and NOTHING matched
                     (decision-candidates §2 — the unmet-request capture)

Display contract (decision-candidates §4 item 4): every need:* predicate
MUST be counted by count_open() and projected by open_needs() — a need
that drains invisibly is a defect.
"""
from __future__ import annotations

from . import rows

NEED_PREDICATES = ("need:tool-request", "need:list", "need:response", "need:request")

STATUS_OPEN = "open"
STATUS_FULFILLED = "fulfilled"
STATUS_CANCELLED = "cancelled"
STATUS_SUPERSEDED = "superseded"

# ---------------------------------------------------------------------------
# Need templates — the shape a requirement takes. Each template declares the
# slots a tool call needs, which are required, and what satisfaction means.
TEMPLATES = {
    "tool-request": {
        "slots": ["tool", "args"],
        "required": ["tool"],
        "satisfies": "tool-result",
        "explain": "Open call to a known tool. Fulfills when the tool's "
                   "execution evidence satisfies its declared result test.",
    },
    "list": {
        "slots": ["topic", "criteria", "members", "nonmatches"],
        "required": ["topic", "criteria"],
        "satisfies": "list-complete",
        "explain": "Progressive list requirement. Criteria persist across "
                   "refinements — refinements append related rows, never "
                   "rewrite the original requirement.",
    },
    "response": {
        "slots": ["prompt", "reply"],
        "required": ["prompt"],
        "satisfies": "reply-delivered",
        "explain": "A conversational reply owed to the user on a surface.",
    },
    "request": {
        "slots": ["ask", "gate-evidence", "slot-guesses", "drain-path"],
        "required": ["ask"],
        "satisfies": "request-fulfilled",
        "explain": "Captured when the gate/lexicon says 'request' but no "
                   "classifier or tool matched — the unmet ask, durable and "
                   "drainable rather than conversational fallout.",
    },
}

def explain(predicate: str) -> str:
    return TEMPLATES.get(predicate.replace("need:", ""), {}).get(
        "explain", "A governed unfulfilled requirement.")

class Floor:
    """The need floor: open ledger rows the steward surveys. Not a store —
    a computed view over need:* predicates."""

    def __init__(self, book):
        self.book = book
        #: wired by the host — maps tool_id -> required arg names, so a
        #: tool-request's satisfaction conditions include the tool contract
        self.arg_requirements: dict = {}

    # ---- creation ----------------------------------------------------------
    def open(self, kind: str, subject: str, slots: dict, claimant="system",
             certainty=0.9, basis="interpretation", meta=None) -> dict:
        pred = f"need:{kind}"
        assert pred in NEED_PREDICATES, pred
        return self.book.claim(
            subject, pred,
            {"kind": kind, "status": STATUS_OPEN, "slots": slots,
             "candidates": [], "explain": explain(pred)},
            claimant=claimant, certainty=certainty, basis=basis,
            meta=meta or {})

    # ---- queries -----------------------------------------------------------
    def _open_rows(self) -> list[dict]:
        out = []
        for pred in NEED_PREDICATES:
            for r in self.book.find(predicate=pred):
                if (r["value"]["v"].get("status") == STATUS_OPEN):
                    out.append(r)
        return out

    def count_open(self) -> int:
        """§4 contract: ALL need predicates counted — drives steward cadence."""
        return len(self._open_rows())

    def open_needs(self) -> list[dict]:
        """§4 contract: ALL need predicates projected — the rail's floor."""
        out = self._open_rows()
        out.sort(key=lambda r: -r["at"])
        return out

    def get(self, need_id: str) -> dict | None:
        return self.book.get(need_id)

    def current(self, need_id: str) -> dict | None:
        """Resolve the supersession chain head for a need id — mutations
        append onto the CURRENT value, not the superseded original."""
        need = self.book.get(need_id)
        if not need:
            return None
        cur = self.book.resolve(need["subject"], need["predicate"])
        return cur or need

    # ---- candidate values --------------------------------------------------
    def add_candidate(self, need_id: str, slot: str, value, source: str,
                      confidence: float, evidence="") -> dict:
        """Candidates stay inspectable with source + confidence until a tool
        invocation selects them (prompt §Work)."""
        need = self.current(need_id)
        if not need:
            return {}
        cand = {"slot": slot, "value": value, "source": source,
                "confidence": confidence, "evidence": evidence,
                "at": rows.now_ms()}
        cur = dict(need["value"]["v"])
        cur.setdefault("candidates", []).append(cand)
        return self.book.claim(
            need["subject"], need["predicate"], cur,
            claimant="system", certainty=need["certainty"],
            basis="interpretation", supersedes=need["id"],
            relates=[need["id"]])

    def set_slot(self, need_id: str, slot: str, value, claimant="principal") -> dict:
        need = self.current(need_id)
        if not need:
            return {}
        cur = dict(need["value"]["v"])
        if slot.startswith("args."):
            cur.setdefault("slots", {}).setdefault(
                "args", {})[slot[5:]] = value
        else:
            cur.setdefault("slots", {})[slot] = value
        return self.book.claim(
            need["subject"], need["predicate"], cur,
            claimant=claimant, certainty=1.0 if claimant == "principal" else 0.8,
            basis="user-choice" if claimant == "principal" else "interpretation",
            supersedes=need["id"], relates=[need["id"]])

    # ---- lifecycle -----------------------------------------------------------
    def _set_status(self, need_id: str, status: str, claimant, result=None,
                    basis="execution") -> dict | None:
        need = self.current(need_id)
        if not need:
            return None
        cur = dict(need["value"]["v"])
        cur["status"] = status
        if result is not None:
            cur["result"] = result
        return self.book.claim(
            need["subject"], need["predicate"], cur, claimant=claimant,
            certainty=0.9, basis=basis, supersedes=need["id"],
            relates=[need["id"]])

    def fulfill(self, need_id: str, result, claimant="tool:quorum") -> dict | None:
        return self._set_status(need_id, STATUS_FULFILLED, claimant, result)

    def cancel(self, need_id: str, claimant="principal") -> dict | None:
        return self._set_status(need_id, STATUS_CANCELLED, claimant,
                                basis="user-choice")

    def supersede(self, need_id: str, new_slots: dict, claimant="system") -> dict | None:
        return self._set_status(need_id, STATUS_SUPERSEDED, claimant,
                                {"refined-slots": new_slots})

    # ---- gates ---------------------------------------------------------------
    def missing_required(self, need: dict) -> list[str]:
        kind = need["value"]["v"].get("kind", "tool-request")
        req = list(TEMPLATES.get(kind, {}).get("required", []))
        slots = need["value"]["v"].get("slots", {})
        missing = [s for s in req if s not in slots or slots[s] in (None, "")]
        if kind == "tool-request" and not missing:
            tool = slots.get("tool", "")
            wants = (self.arg_requirements or {}).get(tool, [])
            args = slots.get("args", {}) or {}
            missing += [f"args.{w}" for w in wants
                        if args.get(w) in (None, "")]
        return missing

    def executable(self, need: dict) -> bool:
        return (need["value"]["v"].get("status") == STATUS_OPEN
                and not self.missing_required(need))
