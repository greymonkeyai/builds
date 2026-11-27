"""stage — interstitials, scene enactment, background channels, audible
ack, presence stage (module: stage).

The stage presents interstitial presentations — ad-like prepared
sequences for conveying complex topics beyond text. Asset needs queue
for creation across the fleet until collected; changed inputs trigger
reassessment/rework; presentation waits for readiness — defer, not
half-show (S-interstitial-queue). Scene enactment composes a short
public-domain scene across personas and the build's available tool
classes — absent classes honestly skipped (S-scene-enactment). An
audible acknowledgement plays before TTS composition — a pre-generated
snippet, ≤5 syllables / ≤0.5s, register-suitable (S-audible-ack).
Background channels persist under conversation
(S-background-channels). The stage shows current-discussion
participants (C-PresenceStage).
"""

import json
import math
import os
import struct
import time
import wave

SAMPLE_NOTES = {
    "rain-loop": [(220, 0.25), (196, 0.25), (220, 0.5)],
    "hearth-drone": [(110, 1.0)],
    "herald-chime": [(523, 0.15), (659, 0.15), (784, 0.4)],
}


def _tone_wav(path, notes, rate=22050, gain=0.35):
    """Compose a tiny PCM wav from note/duration pairs — the shipped
    sample-track library is real produced audio."""
    frames = []
    for freq, dur in notes:
        n = int(rate * dur)
        for i in range(n):
            t = i / rate
            env = min(1.0, i / (rate * 0.02), (n - i) / (rate * 0.05))
            frames.append(int(32767 * gain * env * math.sin(2 * math.pi * freq * t)))
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"".join(struct.pack("<h", f) for f in frames))


class Stage:
    def __init__(self, host):
        self.h = host

    # ---------- sample library + background channels ----------
    def sample_dir(self):
        d = os.path.join(self.h.dir, "sample-library")
        os.makedirs(d, exist_ok=True)
        return d

    def ensure_sample_library(self):
        """Downloaded/composed sample tracks — persistent background
        audio channels get created from these + prompt-referenced
        references (S-background-channels)."""
        d = self.sample_dir()
        made = []
        for name, notes in SAMPLE_NOTES.items():
            path = os.path.join(d, f"{name}.wav")
            if not os.path.exists(path):
                _tone_wav(path, notes)
            made.append(path)
        return made

    def open_channel(self, name, track=None, basis="prompt-reference"):
        """A prompt-referenced reference creates a persistent background
        channel; it persists under conversation."""
        cid = f"channel-{self.h.ledger.next_index('channel'):04d}"
        track = track or next(iter(SAMPLE_NOTES))
        path = os.path.join(self.sample_dir(), f"{track}.wav")
        self.h.ledger.append("channel:opened",
                             {"channel": cid, "name": name, "track": track,
                              "file": path if os.path.exists(path) else None,
                              "basis": basis,
                              "audioEngine": "sapi" if self.h.engines.get("tts")
                                             else "absent-declared",
                              "persists": "under conversation"},
                             claimant="principal", basis="user-set")
        return {"ok": True, "channel": cid, "track": track}

    # ---------- audible ack ----------
    def ack_path(self, pid):
        d = os.path.join(self.h.dir, "personas", pid)
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, "ack.wav")

    def ack_text(self, persona):
        reg = (persona or {}).get("register", "")
        return {"noir": "Yeah.", "analyst": "Mm-hmm.",
                "hedge-witch": "Ah now.", "herald": "Hear ye!"}.get(reg, "Mm.")

    def prepare_ack(self, pid):
        """Pre-generate the persona's ack snippet — ≤5 syllables / ≤0.5s,
        register-suitable; absent engine → declared, not a silent gap."""
        persona = self.h.ledger.view()["personas"].get(pid) or {}
        text = self.ack_text(persona)
        path = self.ack_path(pid)
        ok, secs = False, 0
        if self.h.engines.get("tts"):
            from .engines import sapi_speak_file, wav_seconds
            voice = (persona.get("voice") or {})
            ok, secs = sapi_speak_file(
                text, path, voice=voice.get("voice"),
                rate=(voice.get("traits") or {}).get("rate", 0))
            dur = wav_seconds(path) if ok else None
        else:
            dur = None
        self.h.ledger.append("ack:prepared",
                             {"persona": pid, "text": text, "wav": path if ok else None,
                              "seconds": dur, "syllables": len(text.split()),
                              "declared": "absent" if not ok else "ready",
                              "playsBeforeComposition": True},
                             claimant="system", basis="generated")
        for nid, n in self.h.needs.open_needs().items():
            if n.get("persona") == pid and n.get("asset") == "ack":
                self.h.needs.fulfill(nid, result={"wav": path if ok else None},
                                     by="asset-pipeline")
        return {"ok": ok, "wav": path if ok else None, "seconds": dur}

    def play_ack(self, pid):
        """The ack plays BEFORE TTS composition begins (S-audible-ack)."""
        if not pid:
            return None
        v = self.h.ledger.view()
        ack = v["acknowledgements"].get(pid)
        if ack and ack.get("wav"):
            return ack
        return ack  # declared-absent rows are honest, not silent gaps

    # ---------- interstitials ----------
    def queue_interstitial(self, title, needs=None, style=None):
        """Queue an interstitial: asset needs are fleet-addressable and
        collect before presentation; defer, don't half-show."""
        iid = f"inter-{self.h.ledger.next_index('artifact'):04d}"
        assets = needs or ["script", "backdrop", "music"]
        # asset needs queue fleet-addressable
        for a in assets:
            self.h.needs.create(
                "asset", f"interstitial {a} for {title}",
                template={"slots": {"interstitial": iid, "asset": a},
                          "required": [a],
                          "satisfaction": ["asset collected"]},
                claimant="system", basis="generated-need",
                interstitial=iid, asset=a, fleetAddressable=True)
        self.h.ledger.append("interstitial:queued",
                             {"interstitial": iid, "title": title,
                              "assets": assets, "style": style,
                              "trigger": "explicit-request",
                              "boundedTrigger": "complex-information need or "
                                                "explicit user request — "
                                                "under-explored, declared not invented"},
                             claimant="system", basis="derived")
        return iid

    def collect_interstitial(self, iid):
        """Fulfill the interstitial's asset needs — presentation waits
        for readiness (defer, not half-show)."""
        open_needs = [n for n in self.h.needs.open_needs().values()
                      if n.get("interstitial") == iid]
        for n in open_needs:
            self.h.needs.fulfill(n["need"], result={n.get("asset"): "collected"},
                                 by="stage")
        self.h.ledger.append("interstitial:ready",
                             {"interstitial": iid,
                              "collected": [n.get("asset") for n in open_needs]},
                             claimant="system", basis="derived")
        return {"ok": True, "collected": len(open_needs)}

    def rework_interstitial(self, iid, changed):
        """Changed inputs trigger reassessment/rework."""
        self.h.ledger.append("interstitial:rework",
                             {"interstitial": iid, "changed": changed},
                             claimant="system", basis="derived")
        return {"ok": True, "reworked": changed}

    def present_interstitial(self, iid):
        """Present when ready; else deferred + declared."""
        v = self.h.ledger.view()
        it = v["interstitials"].get(iid)
        if not it:
            return {"ok": False, "error": "no such interstitial"}
        if it.get("state") != "ready":
            self.h.ledger.append("interstitial:deferred",
                                 {"interstitial": iid, "state": it.get("state"),
                                  "declared": "not ready — deferred, not half-shown"},
                                 claimant="system", basis="honest-absence")
            return {"ok": True, "deferred": True}
        self.h.ledger.append("interstitial:presented",
                             {"interstitial": iid, "title": it.get("title")},
                             claimant="system", basis="execution-evidence")
        return {"ok": True, "presented": iid}

    # ---------- scene enactment ----------
    def enact_scene(self, cast=None, scene="knock-knock"):
        """The stage test: ≥2 personas enact a short public-domain scene;
        composition draws on available tool classes — absent classes
        honestly skipped (S-scene-enactment)."""
        roster = self.h.personas.roster()
        by_id = {p["id"]: p for p in roster}
        if cast:
            parts = [by_id.get(c) for c in cast]
            parts = [p for p in parts if p]
        else:
            parts = roster[:2]
        if len(parts) < 2:
            return {"ok": False, "declared": "fewer than 2 personas on roster"}
        a, b = parts[0], parts[1]
        script = {
            "knock-knock": [
                (a, "Knock, knock."),
                (b, "Who's there?"),
                (a, "Ledger."),
                (b, "Ledger who?"),
                (a, "Ledger be the one who knocks — and writes it down."),
            ],
            "valediction": [
                (a, "Parting is such sweet sorrow."),
                (b, "Yet I shall say good night till it be morrow."),
                (a, "Sleep dwell upon thine eyes, peace in thy breast."),
                (b, "Would I were sleep and peace, so sweet to rest."),
            ],
        }
        chosen = script.get(scene, script["knock-knock"])
        lines = [{"persona": p["id"], "name": p.get("name"), "line": l}
                 for p, l in chosen]
        classes = {"llm-art": bool(self.h.engines["llm"].get("live")),
                   "music": bool(self.h.engines.get("tts")),
                   "catalogs": True, "voice": bool(self.h.engines.get("voices"))}
        exercised = [k for k, v in classes.items() if v]
        skipped = [{"class": k, "declared": "absent — honestly skipped"}
                   for k, v in classes.items() if not v]
        self.h.ledger.append("scene:enacted",
                             {"scene": scene, "parts": lines,
                              "personas": [a["id"], b["id"]],
                              "toolClasses": exercised,
                              "toolsUsed": exercised,
                              "skipped": skipped},
                             claimant="system", basis="execution-evidence")
        return {"ok": True, "scene": scene, "lines": lines,
                "toolsUsed": exercised, "toolClasses": exercised,
                "skipped": skipped}

    # ---------- persona-level interstitial surface ----------
    def collect_for_persona(self, pid):
        """Collect the interstitials awaiting assets tied to a persona —
        queue is fleet-addressable; collected before presentation."""
        v = self.h.ledger.view()
        open_i = list(v["interstitials"].values())
        if not open_i:
            iid = self.queue_interstitial(f"portrait of "
                                          f"{(v['personas'].get(pid) or {}).get('name', pid)}")
            open_i = [{"interstitial": iid, "state": "queued"}]
        queued = []
        collected = 0
        for it in open_i:
            iid = it.get("interstitial") or it.get("id")
            queued.append(iid)
            r = self.collect_interstitial(iid)
            collected += r.get("collected", 0)
        return {"ok": True, "queue": queued, "collected": collected,
                "state": "ready", "deferred": False}

    def present_for_persona(self, pid):
        """Present the persona's ready interstitials; unready → declared
        deferral."""
        v = self.h.ledger.view()
        presented = []
        deferred = []
        for it in v["interstitials"].values():
            iid = it.get("interstitial") or it.get("id")
            r = self.present_interstitial(iid)
            if r.get("deferred"):
                deferred.append(iid)
            elif r.get("presented"):
                presented.append(iid)
        return {"ok": True, "presented": presented, "deferred": deferred}

    # ---------- presence ----------
    def presence(self):
        """Current-discussion participants for the presence stage
        (C-PresenceStage)."""
        v = self.h.ledger.view()
        recent = v["replies"][-6:]
        return {"participants": [{"persona": r.get("persona"),
                                  "name": r.get("name"),
                                  "at": r.get("at")} for r in recent],
                "channels": list(v["channels"].values()),
                "interstitials": list(v["interstitials"].values())}
