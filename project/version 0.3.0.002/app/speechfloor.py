"""Speech floor — serialized playback admission (C-SpeechFloor), the manner
beneath C-PerceivableRespondents (contributions individually perceivable) and
C-SequentialRespondents (respondents present in sequence).

The host admits exactly one speech render at a time through a FIFO queue.
Every admission and every completed playback is recorded as a ledger
assertion — the floor is evidence, not just a lock. Persona voice preferences
(portable, C-EngineMapping) ride on each admission and are mapped to engine
settings inside the renderer.
"""
from __future__ import annotations

import queue
import threading
from typing import Optional

from .model import new_id, now_ms


class SpeechFloor(threading.Thread):
    """FIFO playback queue. One render at a time — never overlapping speech."""

    def __init__(self, ctx):
        super().__init__(daemon=True, name="speech-floor")
        self.ctx = ctx
        self.q: "queue.Queue[dict]" = queue.Queue()
        self._stop = threading.Event()
        self.played: list[dict] = []

    # ---- admission ----

    def enqueue(self, text: str, persona: Optional[dict] = None,
                cause: str = "response", voice: Optional[dict] = None) -> dict:
        """Admit a playback request. Returns the admission record; the actual
        render happens in order on the floor thread."""
        adm = {"id": new_id("sp"), "at": now_ms(), "text": text,
               "personaId": (persona or {}).get("id"),
               "personaName": (persona or {}).get("name", "Meridian"),
               "cause": cause, "voice": voice or (persona or {}).get("voice") or {},
               "position": self.q.qsize() + 1}
        self.ctx.append("speech", "speech:floor-admission", adm,
                        "system", basis={"kind": "execution"})
        if not self.is_alive():
            self.start()
        self.q.put(adm)
        return adm

    def depth(self) -> int:
        return self.q.qsize()

    # ---- floor worker ----

    def run(self):
        while not self._stop.is_set():
            try:
                adm = self.q.get(timeout=0.5)
            except queue.Empty:
                continue
            t0 = now_ms()
            r = self.ctx.invoke("speak-voice",
                                {"text": adm["text"], "personaId": adm["personaId"],
                                 "voice": adm["voice"]})
            rec = {"admission": adm["id"], "personaId": adm["personaId"],
                   "personaName": adm["personaName"],
                   "voice": adm["voice"], "ok": bool(r.get("ok")),
                   "renderedBy": (r.get("result") or {}).get("renderedBy"),
                   "ms": now_ms() - t0,
                   "error": r.get("error") or
                            (r.get("result") or {}).get("error")}
            self.played.append(rec)
            self.ctx.append("speech", "speech:floor-played", rec,
                            "engine:tts", basis={"kind": "execution"})
            self.ctx.emit("card", {"kind": "speech", "summary":
                                   f"{adm['personaName']} spoke "
                                   f"({rec['renderedBy'] or 'unrendered'})",
                                   "floor": rec, "at": now_ms()})
            self.q.task_done()

    def drain(self, timeout: float = 30.0) -> bool:
        """Wait until the queue is empty (test/demo seam)."""
        import time
        t0 = time.time()
        while not self.q.empty() and time.time() - t0 < timeout:
            time.sleep(0.05)
        t1 = time.time()
        while self.played and time.time() - t1 < 10:
            # give last render a beat to record
            return True
        return self.q.empty()

    def stop(self):
        self._stop.set()
