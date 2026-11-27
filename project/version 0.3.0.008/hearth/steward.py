"""hearth steward — the Idle Turn Steward.
C-StewardLiveness + C-MonotonicLiveness: liveness chit accumulates
monotonically — pass count up, age = real time since last pass, no
resetting counter. Background work drains the unmet-request queue
(S-need-queue-completion): executes once every required slot holds an
above-threshold candidate; background work yields to user-facing work
(C-UserFacingPriority) and never treats silence as consent to a
consequential action.
"""
import threading
import time
class Steward:
    def __init__(self, host):
        self.h = host
        prior = host.journal.transient_rows("steward-pass")
        self.passes = max((r.get("pass", 0) for r in prior), default=0)
        self.last_pass = max((r.get("ts", 0) for r in prior), default=0.0)
        self.running = False
        self.presented = []
        self._t = None
    def start(self):
        self.running = True
        self._t = threading.Thread(target=self._loop, daemon=True)
        self._t.start()
    def stop(self):
        self.running = False
    def _loop(self):
        while self.running:
            self.pass_once()
            for _ in range(40):  # ~4s cadence, interruptible
                if not self.running:
                    return
                time.sleep(0.1)
    def pass_once(self):
        h = self.h
        self.passes += 1            # monotonic — never resets
        self.last_pass = time.time()
        h.journal.transient("steward-pass", {"pass": self.passes})
        needs = h.modules["needs"]
        # drain eligible queue rows: all-required-above-threshold →
        # execute without user act (user override is a separate path)
        for n in needs.floor():
            if n["state"] != "open" or not n.get("ready"):
                continue
            from .shell import execute_template
            slots = {s: (needs.best(n["id"], s) or {"value": {"value": None}}
                         )["value"]["value"]
                     for s in n["slots"]}
            res = execute_template(_AppView(h), n["template"], slots,
                                   n["id"])
            ok = res.get("status") not in ("failed", "deferred")
            needs.transition(n["id"], "fulfilled" if ok else "open",
                             result=res)
            h.journal.append("steward-exec",
                             {"need": n["id"], "ok": ok,
                              "template": n["template"],
                              "seconds": res.get("seconds")},
                             claimant="steward",
                             basis="execution-evidence",
                             refs=[n["id"]])
        # background presentation: a completed task may become a relevant
        # opportunity for a distinct personality to summarize
        done = [r for r in h.journal.rows("steward-exec")
                if r["value"].get("ok") and
                r["id"] not in self.presented]
        if done:
            pers = h.modules["personas"]
            p = pers.roster()[-1] if pers.roster() else None
            if p:
                item = done[-1]
                self.presented.append(item["id"])
                h.journal.append(
                    "background-presentation",
                    {"persona": p["id"], "work": item["id"],
                     "note": f"{p['name']} presents finished background "
                             f"work while idle work continues"},
                    claimant="persona:" + p["id"],
                    basis="generated-response",
                    refs=[item["id"]])
    def state(self):
        age = round(time.time() - self.last_pass, 1) \
            if self.last_pass else None
        return {"passes": self.passes, "ageSeconds": age,
                "running": self.running,
                "liveCadenceSeconds": 4.0}
class _AppView:
    def __init__(self, h):
        self.host = h
