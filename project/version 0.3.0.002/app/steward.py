"""Background stewardship loop (A3).

Stewardship is a configurable, assignable tool (steward-tick) run by this
daemon at a configurable interval. It never blocks the interactive request
path: it runs on its own thread, holds no locks while idle, and treats user
silence as nothing — consequential actions still require witnessed grants.
Each pass records its duration; interactive responsiveness is provable from
the API probe (the server answers while ticks run).
"""
from __future__ import annotations

import threading
import time


class Steward(threading.Thread):
    def __init__(self, ctx):
        super().__init__(daemon=True, name="steward")
        self.ctx = ctx
        self._stop = threading.Event()
        self.last_tick = None

    def interval(self) -> float:
        rows = self.ctx.ledger.query(subject="steward:main",
                                     predicate="routing:stewardship-assignment")
        if rows and rows[-1].value["v"].get("intervalSec"):
            return float(rows[-1].value["v"]["intervalSec"])
        return 15.0

    def run(self):
        while not self._stop.is_set():
            iv = self.interval()
            if self._stop.wait(iv):
                break
            try:
                self.last_tick = self.ctx.invoke("steward-tick",
                                                 {"reason": "interval"})
            except Exception as e:
                self.ctx.append("idle", "idle:steward-run",
                                {"error": repr(e)}, "steward:main",
                                basis={"kind": "execution"})

    def stop(self):
        self._stop.set()
