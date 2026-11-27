"""Quorum JEV turn lane — gate → classify → evaluate, plus need:request.

(decision-candidates §2 — dual-run lane: the deterministic lexicon answers
first; the model runs asynchronously and its verdict ACTS — disagreement
opens evidence rows / need:request rows / correction cards, never blocks
the turn or mutates the reply already sent.)

- gate     : did the user make a request?  → chat:gate rows (claimant model:<id>)
- classify : what request?                  → the lexicon is primary; model
             verdict is counterfactual evidence
- evaluate : how well fulfilled?            → eval:fulfillment rows post-
             fulfillment, feeding need priority and endorse/discredit

GREY_JEV_MODE=miss-only equivalent: QUORUM_JEV_MODE=miss-only limits the
lane to lexicon failures for compute-starved hosts.
"""
from __future__ import annotations

import json
import os
import re
import threading

from . import rows

JEV_MODE = os.environ.get("QUORUM_JEV_MODE", "dual-run")

# ---------------------------------------------------------------------------
# Deterministic lexicon (primary, instant, replayable)
REQUEST_HINTS = re.compile(
    r"\b(list|show|find|get|search|send|email|publish|create|make|mint|"
    r"add|import|export|discover|scan|join|install|set|change|reorder|"
    r"select|remember|note|remind|schedule|read|summar|compile|write|"
    r"draw|portrait|give|tell me about|what are|how many)\b", re.I)

LIST_HINT = re.compile(r"\b(list|enumerate|name all)\b.*\b(cit|town|state|"
                       r"countr|member|item|of\b)", re.I)
MAIL_HINT = re.compile(r"\b(email|mail|send|message|publish|post)\b", re.I)
PERSONA_HINT = re.compile(r"\b(create|make|mint|new)\b.*\b(persona|personality|"
                          r"avatar|character)\b", re.I)

def lexicon_gate(text: str) -> dict:
    is_req = bool(REQUEST_HINTS.search(text or ""))
    cls = "conversation"
    if LIST_HINT.search(text or ""):
        cls = "list-request"
    elif PERSONA_HINT.search(text or ""):
        cls = "persona-request"
    elif MAIL_HINT.search(text or ""):
        cls = "mail-request"
    return {"isRequest": is_req, "class": cls, "via": "lexicon",
            "confidence": 0.9 if is_req else 0.7}

# ---------------------------------------------------------------------------
class JevLane:
    """The async model lane. Verdicts land as ledger rows; disagreement acts."""

    def __init__(self, book, floor, llm):
        self.book = book
        self.floor = floor
        self.llm = llm

    # ---- gate (async; never blocks the turn) --------------------------------
    def gate_turn(self, turn_id: str, user_text: str, lex: dict):
        if JEV_MODE == "miss-only" and lex["isRequest"]:
            return                                   # miss-only: lexicon hit → skip
        def run():
            prompt = (f"Did this user message make a request the system should "
                      f"act on (vs pure conversation)? Message: {user_text!r}\n"
                      f"Answer JSON: {{\"isRequest\": bool, \"confidence\": 0-1, "
                      f"\"rationale\": \"...\"}}")
            r = self.llm.complete(prompt, role="gate", max_tokens=200)
            verdict = {"isRequest": lex["isRequest"], "stub": True} if not r.get("ok") \
                else self._parse(r["text"], lex)
            row = self.book.claim(
                turn_id, "chat:gate",
                {"lexicon": lex, "model": verdict,
                 "agree": verdict.get("isRequest") == lex["isRequest"]},
                claimant=r.get("claimant", "model:stub"),
                certainty=min(verdict.get("confidence", 0.5), 0.75),
                basis="generated",
                meta={"stub": not r.get("ok")})
            # disagreement ACTS: evidence rows are already written; if the model
            # sees a request the lexicon missed and no tool matched, capture it
            if verdict.get("isRequest") and not lex["isRequest"]:
                self.capture_unmet(turn_id, user_text, verdict, "gate-disagreement")
        threading.Thread(target=run, daemon=True).start()

    # ---- unmet-request capture (§2 item 3) ----------------------------------
    def capture_unmet(self, turn_id: str, ask: str, gate_ev: dict, why: str) -> dict:
        """need:request — asked, nothing matched. Durable + drainable."""
        need = self.floor.open(
            "request", f"request:{turn_id}",
            {"ask": ask, "gate-evidence": gate_ev, "drain-path": "pending"},
            claimant="system", certainty=0.85, basis="interpretation",
            meta={"turn": turn_id, "why": why})
        return need

    # ---- evaluate (post-fulfillment, separate claimant) -----------------------
    def evaluate_fulfillment(self, subject: str, ask: str, outcome: str,
                             result_summary: str):
        """eval:fulfillment rows authored by model:<id> via role=evaluate —
        feed need priority; confident verdicts may mint endorse/discredit."""
        def run():
            prompt = (f"A user asked: {ask!r}\nThe system outcome: {outcome}\n"
                      f"Result summary: {result_summary[:600]!r}\n"
                      f"Score fulfillment JSON: {{\"verdict\": "
                      f"\"met|partial|unmet\", \"confidence\": 0-1, \"note\": \"...\"}}")
            r = self.llm.complete(prompt, role="evaluate", max_tokens=200)
            ev = {"verdict": outcome, "stub": True} if not r.get("ok") \
                else self._parse(r["text"], {"verdict": outcome})
            self.book.claim(
                subject, "eval:fulfillment",
                {"ask": ask, "verdict": ev.get("verdict", outcome),
                 "note": ev.get("note", ""), "stub": not r.get("ok")},
                claimant=r.get("claimant", "model:stub"),
                certainty=min(float(ev.get("confidence", 0.6)), 0.75),
                basis="generated", meta={"stub": not r.get("ok")})
        threading.Thread(target=run, daemon=True).start()

    def _parse(self, text: str, fallback: dict) -> dict:
        m = re.search(r"\{[\s\S]*\}", text or "")
        try:
            return dict(fallback, **json.loads(m.group(0))) if m else fallback
        except Exception:
            return fallback
