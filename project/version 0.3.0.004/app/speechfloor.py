"""Speech floor (C-SpeechFloor) — serialized playback admission.
One render at a time through a host queue. Admission holds until playback
actually completes: the local renderer blocks on the audio device, and the
played row carries a MEASURED playbackMs. Where no real playback happened no
playbackMs is claimed (J2 discipline — populated fields or no claim).
"""
from __future__ import annotations
import queue
import threading
import time
class SpeechFloor:
    def __init__(self, ctx):
        self.ctx = ctx
        self.q = queue.Queue()
        self.played = []          # [{persona, text, playbackMs, at}]
        self.holds = []           # admission log
        self.worker = threading.Thread(target=self._loop, daemon=True)
        self.worker.start()
    @property
    def depth(self):
        return self.q.qsize()
    def admit(self, persona: str, text: str, voice=None, rate=0,
              render=True) -> dict:
        item = {"persona": persona, "text": text, "voice": voice,
                "rate": rate, "render": render, "at": time.time(),
                "done": threading.Event(), "result": None}
        self.q.put(item)
        self.ctx.ledger.say("speech:floor", "speech:admitted",
                            {"persona": persona, "chars": len(text),
                             "depth": self.depth},
                            claimant="persona:" + persona, certainty=1.0,
                            basis={"kind": "execution"})
        return item
    def wait(self, item, timeout=180):
        item["done"].wait(timeout)
        return item["result"]
    def drain(self, timeout=240):
        t0 = time.time()
        while self.depth and time.time() - t0 < timeout:
            time.sleep(0.4)
    def _loop(self):
        while True:
            item = self.q.get()
            if item is None:
                return
            res = {"ok": True, "persona": item["persona"]}
            if item["render"]:
                r = self.ctx.engines.tts.render_local(
                    item["text"], voice=item["voice"], rate=item["rate"])
                res.update(r)
            else:
                res.update({"engine": "none", "playbackMs": None,
                            "heldUntilPlaybackComplete": False})
            entry = {"persona": item["persona"],
                     "text": item["text"][:160],
                     "engine": res.get("engine"),
                     "at": item["at"]}
            if res.get("playbackMs") is not None:
                entry["playbackMs"] = res["playbackMs"]
                entry["heldUntilPlaybackComplete"] = True
            self.played.append(entry)
            self.holds.append(entry)
            self.ctx.ledger.say("speech:floor", "speech:played", entry,
                                claimant="system", certainty=1.0,
                                basis={"kind": "execution"})
            item["result"] = res
            item["done"].set()
            self.q.task_done()
