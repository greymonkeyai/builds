"""needs — the unmet-requirement floor (module: needs).

User and system inputs evaluate for tool opportunities; each becomes a
need:* assertion governed by a template — slots, candidate values,
acceptance tests, required/optional information, satisfaction conditions.
Creation does not imply execution. A need stays Open until its declared
satisfaction conditions are met, or it is Cancelled or Superseded
(C-FloorLifecycle, C-UnmetNeedRecords). Candidate values remain
inspectable with source and confidence until invocation selects them
(C-AcceptanceChecks, C-DyadicConfidence for ranking semantics).

Intent routing (C-IntentRouting, C-TurnEvalLane): each distinguishable
intent classifies to its fulfillment path — name-addressed asks reach the
addressee, capability questions get answered, list requests open list
machinery, wants are not lists, and only genuine unmet asks land on the
floor. Deterministic match plus LLM review pairing
(C-DeterministicMatchReview).
"""

import re
import time

from .ledger import new_id

NEED_OPEN, NEED_FOCUSED, NEED_FULFILLED = "open", "focused", "fulfilled"
NEED_CANCELLED, NEED_SUPERSEDED = "cancelled", "superseded"


class Needs:
    def __init__(self, host):
        self.h = host

    # ---------- creation ----------
    def create(self, kind, title, template=None, claimant="system",
               basis="derived", need_id=None, state=NEED_OPEN, **fields):
        """Open a need row. The template governs: slots, candidates,
        tests, required/optional information, satisfaction conditions."""
        nid = need_id or f"need-{self.h.ledger.next_index('need'):04d}"
        tpl = template or {}
        row = self.h.ledger.append(
            f"need:{kind}", {
                "need": nid, "title": title, "state": state,
                "template": {
                    "slots": tpl.get("slots", {}),
                    "required": tpl.get("required", []),
                    "optional": tpl.get("optional", []),
                    "candidates": tpl.get("candidates", {}),
                    "tests": tpl.get("tests", []),
                    "satisfaction": tpl.get("satisfaction", []),
                },
                **fields},
            claimant=claimant, basis=basis, certainty=0.75)
        return nid, row

    def candidate(self, need_id, slot, value, source, confidence):
        """A candidate value — inspectable with source and confidence
        until invocation selects it. Recency breaks confidence ties."""
        return self.h.ledger.append(
            "need:candidate", {"need": need_id, "slot": slot, "value": value,
                               "source": source, "confidence": confidence},
            claimant="system", basis="derived", confidence=confidence)

    def candidates_for(self, need_id, slot=None):
        v = self.h.ledger.view()
        cands = [c for c in v["need_candidates"].get(need_id, [])]
        if slot:
            cands = [c for c in cands if c.get("slot") == slot]
        # rank by confidence, recency breaks ties (prompt §Confidence)
        return sorted(cands, key=lambda c: (c.get("confidence", 0), c.get("at", 0)),
                      reverse=True)

    # ---------- lifecycle ----------
    def set_state(self, need_id, state, **fields):
        prev = (self.h.ledger.view()["needs"] or {}).get(need_id)
        row = self.h.ledger.append(
            f"need:{fields.pop('kind', 'state')}", {"need": need_id, "state": state, **fields},
            claimant="system", basis="derived",
            supersedes=(prev or {}).get("id"))
        return row

    def focus(self, need_id):
        return self.set_state(need_id, NEED_FOCUSED, kind="focused")

    def fill_slot(self, need_id, slot, value, claimant="principal"):
        """Conversational slot-filling into a focused need — successive
        inputs refine the requirement through related assertions, never
        by rewriting it."""
        return self.h.ledger.append(
            "need:slot-filled", {"need": need_id, "slot": slot, "value": value},
            claimant=claimant, basis="user-input" if claimant == "principal" else "derived")

    def fulfill(self, need_id, result=None, by="steward"):
        """The need is met → fulfilled; it leaves the open list
        (C-FloorLifecycle: the floor shows only unmet needs)."""
        return self.set_state(need_id, NEED_FULFILLED, kind="fulfilled",
                              result=result, fulfilledBy=by)

    def cancel(self, need_id):
        return self.set_state(need_id, NEED_CANCELLED, kind="cancelled")

    def open_needs(self):
        return self.h.ledger.view()["needs_open"]

    # ---------- intent routing ----------
    def classify(self, text, persona_names=None, addressed=None):
        """The turn-eval lane (C-TurnEvalLane): gate → classify →
        route. Deterministic first; LLM review pairs when live
        (C-DeterministicMatchReview)."""
        t = (text or "").strip()
        low = t.lower()
        names = persona_names or [p.get("name", "") for p in self.h.ledger.view()["personas"].values()]
        addressed = addressed or [n for n in names if n and re.search(rf"\b{re.escape(n.lower())}\b", low)]

        kind = "chat"
        if addressed:
            kind = "named"
        if re.search(r"\b(list|enumerate|name all|catalogue|catalog)\b", low) and \
                re.search(r"\b(all|every|each)\b", low) or re.match(r"^(make|create|build) (a |me )?list", low):
            kind = "list"
        elif re.match(r"^(make|create|build|give me) (a |me )?(list|formal list)", low):
            kind = "list"
        elif re.search(r"\b(i want|i'd like|i would like|i need|please (get|find|fetch|bring))\b", low):
            kind = "want"        # wants are NOT lists (S-intent-routing)
        elif re.search(r"\b(what can you do|help|capabilit|who are you|what are you)\b", low):
            kind = "capability"
        elif re.search(r"\b(weather|temperature|forecast)\b", low) and "like" not in low:
            kind = "unmet"
        result = {"kind": kind, "addressed": addressed, "text": t}

        live = self.h.engines["llm"].get("live")
        # deterministic match governs; LLM review pairs as a second
        # opinion — it may promote an unmatched 'chat' input to a routed
        # kind, but never vetoes a determined non-chat classification
        if live and kind == "chat":
            reviewed = self._llm_review(t, kind)
            if reviewed:
                result["reviewedKind"] = reviewed
                if reviewed != kind:
                    result["kind"] = reviewed
        return result

    def _llm_review(self, text, deterministic_kind):
        from .engines import llm
        out, _ = llm(
            "Classify this user input into exactly one intent: "
            "named | capability | list | want | unmet | chat.\n"
            "'list' = a request to enumerate/produce a formal list. "
            "'want' = a desire, NOT a list. 'unmet' = a concrete need for "
            "work (find/fetch/research). 'capability' = asks what the "
            "system can do. 'named' = addresses a persona by name. "
            "Otherwise 'chat'.\n"
            f"Input: {text}\nReply with ONE WORD.",
            timeout=20, temperature=0.0)
        if out:
            w = out.strip().split()[0].strip(".,:'\"").lower()
            if w in ("named", "capability", "list", "want", "unmet", "chat"):
                return w
        return None

    # ---------- the turn lane ----------
    def route(self, text, classification, persona_names=None):
        """Route a classified input to its fulfillment path. Returns
        {needs: [ids], replyKind}. Only genuine unmet asks land on the
        floor; every routed need stays distinguishable."""
        kind = classification.get("kind")
        routed = []
        if kind == "list":
            nid, _ = self.create("list", f"list request: {text[:72]}",
                                 template={"slots": {"request": text},
                                           "required": ["members"],
                                           "satisfaction": ["members retrieved",
                                                            "criteria preserved",
                                                            "non-matches recorded"]},
                                 claimant="system", basis="interpretation")
            routed.append(nid)
        elif kind == "want" or kind == "unmet":
            nid, _ = self.create("tool", f"unmet ask: {text[:72]}",
                                 template={"slots": {"request": text},
                                           "required": ["fulfillment"],
                                           "satisfaction": ["declared conditions met"]},
                                 claimant="system", basis="interpretation")
            routed.append(nid)
        # capability/chat/named → conversational path, no floor row
        return routed
