"""steward — background attention + liveness (needs' steward module).

The steward liveness chit accumulates monotonically — pass count up,
age = real time since last pass, no resetting counter
(C-MonotonicLiveness, C-StewardLiveness). Background work continues
while the user is idle: drain the needs floor, process source data,
complete research, and prepare relevant opportunities for presentation
— a completed task becomes a result a personality summarizes when the
user is available (prompt §Background activity; C-UserFacingPriority:
background yields to user-facing work; C-StewardAsTool: stewardship is
a configurable, assignable tool).
"""

import threading
import time


class Steward:
    def __init__(self, host):
        self.h = host
        self._stop = threading.Event()
        self._thread = None
        self.passes = 0
        self.last_pass = None

    def start(self):
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _loop(self):
        while not self._stop.is_set():
            self.pass_once()
            self._stop.wait(12)

    def pass_once(self):
        """One stewardship pass — monotonic count, real age."""
        self.passes += 1
        self.last_pass = time.time()
        self.h.ledger.append("steward:liveness",
                             {"pass": self.passes,
                              "age": 0.0,
                              "sinceStart": round(self.last_pass - self.h.booted_at, 1)},
                             claimant="system", basis="liveness",
                             transient=True)
        # drain: present completed work through a distinct personality
        self.drain_presentable()

    def liveness(self):
        age = round(time.time() - self.last_pass, 1) if self.last_pass else None
        return {"passes": self.passes, "age": age,
                "monotonic": True, "lastPass": self.last_pass}

    def drain_presentable(self):
        """A completed task becomes a relevant opportunity presented
        through a distinct personality, preserving ledger evidence
        (S-background-present)."""
        v = self.h.ledger.view()
        fresh = [n for n in v["needs_fulfilled"].values()
                 if not n.get("presented")]
        if not fresh:
            return None
        n = fresh[-1]
        roster = self.h.personas.roster()
        if not roster:
            return None
        persona = roster[-1]
        text = (f"{persona.get('name')} here — while you were away I "
                f"finished '{n.get('title', 'a need')}'."
                + (f" Result: {str(n.get('result'))[:160]}" if n.get("result") else ""))
        self.h.ledger.append("reply:committed",
                             {"persona": persona["id"], "name": persona.get("name"),
                              "text": text, "stewardPresented": True,
                              "preserving": n.get("need"),
                              "register": persona.get("register")},
                             claimant=f"persona:{persona.get('name')}",
                             basis="steward-presentation", certainty=0.6)
        self.h.ledger.append("need:fulfilled",
                             {"need": n.get("need"), "state": "fulfilled",
                              "presented": True,
                              "supersedes": n.get("id")},
                             claimant="system", basis="derived")
        return text
