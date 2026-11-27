"""Quorum steward — the ITS idle-turn machine.

(prompt §Background activity and attention; decision-candidates §2 drain
path, §4 liveness contract; C-UserFacingPriority)

The steward does useful work while the user is idle: drains open needs
(reclassify need:request → trusted-source search → tool:candidate path →
ask-the-user card), runs temporal attention, and prepares persona-presented
offers. Every pass stamps `last_pass_at` — the first-screen liveness chit
renders its age (§4: a needs list without a heartbeat is a lie of
omission). User-facing work always wins the turn.
"""
from __future__ import annotations

import threading
import time

from . import rows

class Steward:
    CADENCE_S = 8

    def __init__(self, host):
        self.host = host
        self.last_pass_at = 0
        self.passes = 0
        self.user_active_until = 0
        self._stop = False
        self.thread = threading.Thread(target=self._loop, daemon=True)

    def start(self):
        self.thread.start()

    def note_user_activity(self):
        """User-facing work suppresses the idle turn (C-UserFacingPriority)."""
        self.user_active_until = time.time() + 10

    def liveness(self) -> dict:
        """§4 — the chit's data: age of last pass, escalated against the live
        cadence. ok < 2×, warning < 4×, alert beyond / never."""
        age = (rows.now_ms() - self.last_pass_at) / 1000 if self.last_pass_at \
            else None
        expect = self.CADENCE_S
        esc = "ok" if age is not None and age < 2 * expect else \
              "warning" if age is not None and age < 4 * expect else "alert"
        return {"lastPassAt": self.last_pass_at, "ageS": age,
                "expectedWakeS": expect, "escalation": esc,
                "passes": self.passes}

    def _loop(self):
        while not self._stop:
            time.sleep(self.CADENCE_S)
            if time.time() < self.user_active_until:
                continue
            try:
                self.pass_()
            except Exception:
                pass

    def pass_(self) -> dict:
        """One drain pass over the need floor."""
        acted = []
        for need in self.host.floor.open_needs():
            v = need["value"]["v"]
            kind = v.get("kind")
            try:
                if kind == "request" and v.get("slots", {}).get("drain-path") == "pending":
                    acted.append(self._drain_request(need))
                elif kind == "tool-request" and self.host.floor.executable(need):
                    acted.append(self._drain_tool(need))
            except Exception as e:
                acted.append({"need": need["id"], "error": repr(e)})
        self.passes += 1
        self.last_pass_at = rows.now_ms()
        self.host.book.claim("steward", "steward:pass",
                             {"n": self.passes, "acted": len(acted)},
                             claimant="steward:its", certainty=0.9,
                             basis="execution")
        return {"pass": self.passes, "acted": acted}

    def _drain_request(self, need: dict) -> dict:
        """need:request drain — reclassify → trusted-source search →
        tool:candidate path → ask-the-user card (decision-candidates §2/§4)."""
        ask = need["value"]["v"].get("slots", {}).get("ask", "")
        r = self.host.primitives.run("web", "search", {"query": ask}, {}, self.host.ctx)
        hits = (r or {}).get("results") or []
        if hits:
            self.host.floor.set_slot(need["id"], "drain-path",
                                     "trusted-source-search", "steward:its")
            self.host.floor.fulfill(need["id"],
                                    {"resolved": "source-candidates",
                                     "candidates": hits[:5]},
                                    claimant="steward:its")
            return {"need": need["id"], "drained": "source-candidates"}
        self.host.floor.set_slot(need["id"], "drain-path",
                                 "ask-the-user", "steward:its")
        return {"need": need["id"], "drained": "ask-the-user-card",
                "card": f"Still working on: {ask!r} — no source or tool "
                        f"matched yet. Should I keep looking?"}

    def _drain_tool(self, need: dict) -> dict:
        """Dispatch an executable tool-request — gated ones stay open and
        honestly recorded (no silent execution)."""
        slots = need["value"]["v"].get("slots", {})
        tool = slots.get("tool", "")
        res = self.host.tools.invoke(tool, slots.get("args", {}), self.host.ctx)
        if res.get("deferred"):
            return {"need": need["id"], "deferred": res["status"]}
        self.host.floor.fulfill(need["id"], res.get("result") or res,
                                claimant=f"tool:{tool}")
        return {"need": need["id"], "fulfilled": tool}

    # ---- proactive offer (S-background-present) -------------------------------
    def offer(self, text: str, persona_id: str) -> dict:
        """A completed background result presented through a distinct
        personality, evidence preserved (prompt §Background activity)."""
        self.host.book.claim("proactive", "proactive:offer",
                             {"text": text, "persona": persona_id},
                             claimant="steward:its", certainty=0.85,
                             basis="generated")
        return {"offered": text[:80]}
