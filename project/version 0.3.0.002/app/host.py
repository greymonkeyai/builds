"""Runtime context + host wiring.

Ctx is the ToolContext every component receives: the ledger, the registry, the
decision model, personas, engines, the append seam (the synchronous face of
the ledger.append system command), the card/event bus, and helpers.
"""
from __future__ import annotations

import json
import os
import threading
import time
from typing import Any, Optional

from . import governance, needs, tools
from .decision import DecisionModel
from .engines import Engines
from .ledger import Ledger
from .model import now_ms
from .personas import PersonaStore
from .speechfloor import SpeechFloor


class Bus:
    """In-process event bus: routed cards and stream events. Subscribers
    (API layer, steward) receive (kind, payload); the last N are retained
    for UI replay."""

    def __init__(self, keep: int = 500):
        self._subs = []
        self.recent: list[dict] = []
        self._keep = keep
        self._lock = threading.Lock()

    def publish(self, kind: str, payload: Any):
        ev = {"kind": kind, "payload": payload, "at": now_ms()}
        with self._lock:
            self.recent.append(ev)
            self.recent = self.recent[-self._keep:]
        for cb in list(self._subs):
            try:
                cb(ev)
            except Exception:
                pass

    def subscribe(self, cb):
        self._subs.append(cb)


class Ctx:
    def __init__(self, root: str, runtime: Optional[str] = None):
        self.root = root
        self.runtime = runtime or os.path.join(root, "runtime")
        self.artifacts = os.path.join(self.runtime, "artifacts")
        self.outbox = os.path.join(self.runtime, "outbox")
        for d in (self.runtime, self.artifacts, self.outbox):
            os.makedirs(d, exist_ok=True)
        self.ledger = Ledger(os.path.join(self.runtime, "ledger.jsonl"))
        self.registry = tools.Registry()
        self.decision = DecisionModel(self)
        self.personas = PersonaStore(os.path.join(self.runtime, "personalities.json"), self)
        self.engines = Engines()
        self.bus = Bus()
        self.floor = SpeechFloor(self)
        self.admonitions: list[str] = []
        self.boot_at = now_ms()
        self._engine_report: Optional[dict] = None
        self._engine_report_at = 0.0

    # ---- write seam (synchronous face of the ledger.append system command) ----

    def append(self, subject, predicate, value, claimant, **kw):
        return self.ledger.append(subject, predicate, value, claimant, **kw)

    # ---- component dispatch ----

    def invoke(self, cid: str, input: Optional[dict] = None,
               grant: Optional[dict] = None, need_id: Optional[str] = None) -> dict:
        return tools.invoke(self, cid, input, grant=grant, need_id=need_id)

    def engine_invoke(self, engine: str, method: str, args: dict) -> Any:
        eng = getattr(self.engines, engine, None)
        if eng is None:
            return {"ok": False, "error": f"unknown engine: {engine}"}
        fn = getattr(eng, method, None)
        if fn is None:
            return {"ok": False, "error": f"unknown engine method: {engine}.{method}"}
        return fn(**(args or {}))

    def emit(self, kind: str, payload: Any):
        self.bus.publish(kind, payload)

    # ---- config helpers (config assertions on subject user-settings) ----

    def config(self, predicate: str, default=None):
        rows = self.ledger.query(subject="user-settings", predicate=predicate)
        return rows[-1].value["v"] if rows else default

    def response_depth(self) -> int:
        return int(self.config("chat:response-depth", 2) or 2)

    def honesty(self) -> dict:
        if self._engine_report is None or time.time() - self._engine_report_at > 10:
            self._engine_report = self.engines.report()
            self._engine_report_at = time.time()
        eng = self._engine_report
        return {
            "ledger": {"durable": True, "path": self.ledger.path,
                     **self.ledger.stats()},
            "engines": eng,
            "stubDeclarations": {
                "llm": "stubFallback on — template replies declared per-card"
                       if eng["llm"]["mode"] == "stub" else "off",
                "ttsRemote": "unconfigured — declared, never silently substituted",
                "stt": "browser Web Speech API or declared-none",
            },
            "personaFrame": self.personas.frame(),
        }

    def admonish(self, msg: str):
        self.admonitions.append(msg)
        self.emit("admonition", {"message": msg})
