"""The ITS steward — idle turn steward. Drains the tool-call floor,
fulfills generated needs (portraits, voices, acks, assets, lists,
research), presents completed background work through a personality.
Liveness (C-MonotonicLiveness, C-StewardLiveness): pass count and age are
monotonic — they accumulate across the run AND across relaunch (restored
from the journal), never reset. A green heartbeat beside a parked need
reads as parked work, not a dead steward.
"""
import json
import os
import threading
import time
from . import personas as per
from . import stage as stg
class Steward:
    def __init__(self, host, interval=1.5):
        self.host = host
        self.interval = interval
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._loop, daemon=True)
        # monotonic across relaunch: restore pass count from journal
        prior = [r for r in host.book.rows
                 if r["kind"] == "steward:liveness"]
        self.passes = max([r["claim"].get("passes", 0) for r in prior] or [0])
        self.last_pass_at = max(
            [r["claim"].get("passAt", 0) for r in prior] or [0])
        self.busy = False
        self._t.start()
    def _loop(self):
        while not self._stop.is_set():
            self.pass_once()
            self._stop.wait(self.interval)
    def pass_once(self):
        host = self.host
        self.busy = True
        try:
            self.drain()
        finally:
            self.passes += 1
            self.last_pass_at = time.time()
            self.busy = False
            host.book.append("steward:liveness", {
                "subject": "steward", "passes": self.passes,
                "passAt": self.last_pass_at, "monotonic": True},
                claimant="host", basis="derived",
                durable=(self.passes % 20 == 1))
    def liveness(self):
        """Liveness chit data — age = real seconds since last pass."""
        return {"passes": self.passes,
                "ageS": round(time.time() - self.last_pass_at, 1)
                if self.last_pass_at else None,
                "busy": self.busy, "cadenceS": self.interval}
    def drain(self):
        """Fulfill what can be fulfilled; background work yields to
        user-facing work (C-UserFacingPriority — drained between turns)."""
        host = self.host
        if host.turn_in_flight:
            return
        # user-facing needs drain before slow asset work (C-UserFacingPriority)
        asset_kinds = ("need:portrait", "need:voice", "need:ack",
                       "need:characterize", "need:asset")
        floor = host.needs.floor()
        ordered = ([n for n in floor if n["kind"] not in asset_kinds] +
                   [n for n in floor if n["kind"] in asset_kinds])
        for need in ordered:
            k = need["kind"]
            subj = need["claim"].get("subject")
            try:
                if k == "need:portrait":
                    p = host.personas.get(subj)
                    if p and not p.get("portrait"):
                        per.fulfill_portrait(host, p)
                    self.host.needs.fulfill(need, {"bound": True})
                elif k == "need:voice":
                    p = host.personas.get(subj)
                    if p and not p.get("voice"):
                        per.fulfill_voice(host, p)
                    self.host.needs.fulfill(need, {"assigned": True})
                elif k == "need:ack":
                    p = host.personas.get(subj)
                    if p and not p.get("ack"):
                        per.fulfill_ack(host, p)
                    self.host.needs.fulfill(need, {"prepared": True})
                elif k == "need:characterize":
                    p = host.personas.get(subj)
                    if p and not p.get("characterization"):
                        per.fulfill_characterize(host, p)
                    self.host.needs.fulfill(need, {"extended": True})
                elif k == "need:list":
                    self.host.needs.fulfill_list(need)
                    host.push_event("needs", {"list": "fulfilled",
                                              "need": need["id"]})
                elif k == "need:asset":
                    stg.fulfill_asset(host, need)
                elif k == "need:request":
                    # genuine unmet ask stays open unless stale (>24h)
                    pass
            except Exception as e:
                host.book.append("steward:error", {
                    "subject": need["id"], "error": str(e)[:160]},
                    claimant="host", basis="execution-evidence")
        # present a completed background result through a distinct
        # personality when the user is quiet
        self.present_completed()
    def present_completed(self):
        host = self.host
        done = [r for r in host.book.current()
                if r["kind"] == "need:list" and
                r["claim"].get("status") == "fulfilled" and
                not r["claim"].get("presented")]
        for d in done:
            roster = host.roster_order()
            if not roster:
                return
            p = roster[-1]  # a distinct personality presents it
            lst = host.book.get(d["claim"].get("result", {}).get("listId"))
            if not lst:
                continue
            count = lst["claim"].get("memberCount", 0)
            label = lst["claim"]["criteria"]["label"]
            text = (f"That list is done — {count} members for "
                    f"{label}. It's in the library, iterable.")
            host.book.append("chat:reply", {
                "subject": "background-present", "persona": p["id"],
                "name": p["name"], "grant": "background",
                "text": text, "fidelity": "grounded",
                "presentedNeed": d["id"]},
                claimant=f"persona:{p['id']}", basis="generated-response")
            claim = dict(d["claim"])
            claim["presented"] = True
            host.book.append(d["kind"], claim, relates=[d["id"]],
                             supersedes=d["id"], claimant="host",
                             basis="derived")
            host.push_event("chat", {"background": p["name"], "text": text})
            break
    def stop(self):
        self._stop.set()
