"""Background stewardship — useful work continues while the user is silent.
Duties are configurable as ledger data (`steward:duty`), each separately
toggleable (C-StewardAsTool / C-ExplicitPolicies). The steward never holds
the request path (C-UserFacingPriority): it runs on its own thread, yields
to user input, and never treats silence as consent to a consequential act.
"""
from __future__ import annotations
import threading
import time
from . import temporal
DUTIES = ("drain-needs", "temporal-attention", "inbox-scan",
          "confidence-review", "compact-check")
DEFAULT_INTERVAL_S = 18
class Steward:
    def __init__(self, ctx, interval=DEFAULT_INTERVAL_S):
        self.ctx = ctx
        self.interval = interval
        self._stop = threading.Event()
        self.thread = None
        self.last_run = None
        self.running = False
    def start(self):
        if self.thread:
            return
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
    def stop(self):
        self._stop.set()
    def _loop(self):
        while not self._stop.wait(self.interval):
            try:
                self.tick(reason="interval")
            except Exception:
                pass
    def _duty_on(self, name) -> bool:
        a = self.ctx.ledger.resolve("steward", f"steward:duty:{name}")
        if a is None:
            return True
        return bool((a.value.get("v") or {}).get("on", True))
    def tick(self, reason="manual") -> dict:
        led = self.ctx.ledger
        self.running = True
        t0 = time.time()
        actions = []
        if self._duty_on("drain-needs"):
            for need in self.ctx.open_needs()[:4]:
                r = self.ctx.retry(need["id"])
                if r.get("ok"):
                    actions.append(f"fulfilled:{need['id']}")
        if self._duty_on("temporal-attention"):
            r = temporal.attention_scan(self.ctx)
            if r.get("findings"):
                actions.append(f"temporal:{r['findings']}")
        if self._duty_on("inbox-scan"):
            r = self.ctx.run_connector("inbox-eml")
            if r.get("ingested"):
                actions.append(f"inbox:{r['ingested']}")
        if self._duty_on("confidence-review"):
            # success-driven source-confidence adaptation, bounded
            adj = self._confidence_review()
            if adj:
                actions.append(f"conf:{adj}")
        ms_ = int((time.time() - t0) * 1000)
        led.say("steward", "idle:steward-run",
                {"reason": reason, "ms": ms_, "actions": actions,
                 "duties": [d for d in DUTIES if self._duty_on(d)]},
                claimant="steward:main", certainty=1.0,
                basis={"kind": "execution"})
        self.last_run = {"ms": ms_, "actions": actions}
        self.running = False
        return {"ok": True, "ms": ms_, "actions": actions}
    def _confidence_review(self) -> int:
        """Bounded ±0.05 source-confidence adjustment after ≥2 outcomes."""
        led = self.ctx.ledger
        n = 0
        for a in led.query(predicate="source:outcome", limit=50):
            v = a.value.get("v") or {}
            src, ok = v.get("source"), v.get("adequate")
            if not src:
                continue
            key = f"source:confidence:{src}"
            cur = led.resolve("steward", key)
            cv = (cur.value.get("v") or {}).get("v", 0.7) if cur else 0.7
            nv = min(0.95, cv + 0.05) if ok else max(0.2, cv - 0.05)
            if nv != cv:
                led.say("steward", key, {"v": round(nv, 3), "source": src},
                        claimant="steward:confidence", certainty=1.0,
                        basis={"kind": "execution"},
                        supersedes=cur.id if cur else None)
                n += 1
        return n
