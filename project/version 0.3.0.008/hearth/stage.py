"""hearth stage — interstitials, scene enactment, background channels,
presence stage.
Scene enactment composes at run time — not canned: the composer draws on
persona characterization and available tool classes; absent classes are
honestly skipped (S-scene-enactment). Background channels are real
produced audio artifacts (R-A2).
"""
import os
import re
import time
from . import audio
class Stage:
    def __init__(self, host):
        self.h = host
        self.stage_dir = os.path.join(host.data_dir, "stage")
        os.makedirs(self.stage_dir, exist_ok=True)
    # ---- presence --------------------------------------------------------
    def presence(self):
        sel = self.h.modules["personas"].selected_personas()
        return {"participants": [p["name"] for p in sel],
                "showing": self.h.journal.rows("interstitial")[-3:]}
    # ---- background channels ------------------------------------------------
    def ensure_channels(self):
        """Persistent channels from the sample library + prompt
        references — assets produced in anticipation (S-asset-
        anticipation: creation opens the need, background fulfillment
        binds the produced asset, need closes)."""
        if self.h.journal.rows("channel"):
            return
        for mood in ("calm", "rain", "focus"):
            self.channel(mood, claimant="system")
    def channel(self, mood, prompt_ref=None, claimant="user"):
        needs = self.h.modules["needs"]
        n = needs.open("channel-asset",
                       slots={"mood": {"value": mood, "confidence": 0.9,
                                       "source": claimant}},
                       claimant=claimant)
        path = os.path.join(self.stage_dir, f"channel-{mood}.wav")
        try:
            audio.synth_ambient(path, mood=mood)
            info = audio.wav_info(path)
            produced = True
        except Exception:
            info = None
            produced = False
        row = self.h.journal.append(
            "channel",
            {"name": mood, "path": path if produced else None,
             "info": info, "produced": produced,
             "declared": "produced" if produced else
             "audio-engine-absent-declared",
             "promptRef": prompt_ref, "persistent": True},
            claimant="tool:audio.synth", basis="execution-evidence",
            refs=[n["id"]])
        if produced:
            needs.transition(n["id"], "fulfilled",
                             result={"channel": path})
        return row["value"]
    def channels(self):
        return [r["value"] for r in self.h.journal.rows("channel")]
    def media_intent(self, text):
        low = text.lower()
        mood = ("rain" if "rain" in low else
                "night" if "night" in low or "quiet" in low else
                "focus" if "focus" in low or "work" in low else "calm")
        existing = [c for c in self.channels() if c["name"] == mood]
        if not existing:
            self.channel(mood, prompt_ref=text, claimant="user")
        path = os.path.join(self.stage_dir, f"channel-{mood}.wav")
        if os.path.exists(path):
            self.h.speech_floor.enqueue(
                {"kind": "wav", "path": path,
                 "label": "channel:" + mood})
        return {"channel": mood, "path": path,
                "produced": os.path.exists(path)}
    # ---- interstitial queue -------------------------------------------------
    def queue_interstitial(self, topic, inputs=None, claimant="user"):
        needs = self.h.modules["needs"]
        n = needs.open("interstitial-asset",
                       slots={"topic": {"value": topic,
                                        "confidence": 0.8,
                                        "source": claimant}},
                       claimant=claimant)
        # fleet-addressable: the queue row names its delegation surface
        self.h.journal.append(
            "interstitial",
            {"need": n["id"], "topic": topic,
             "fleetAddressable": True,
             "inputs": inputs or {"topic": topic},
             "state": "queued"},
            claimant=claimant, basis="claim", refs=[n["id"]])
        return n["id"]
    def rework(self, inter_id, new_inputs):
        """Changed inputs trigger reassessment/rework."""
        self.h.journal.append(
            "interstitial-state",
            {"interstitial": inter_id, "state": "rework",
             "inputs": new_inputs},
            claimant="user", basis="user-choice", refs=[inter_id])
    def collect(self, inter_id):
        """Collect assets until ready; present waits for readiness —
        defer, not half-show."""
        rows = self.h.journal.rows("interstitial")
        it = next((r["value"] for r in rows
                   if r["value"].get("need") == inter_id or
                   r["id"] == inter_id), None)
        if not it:
            return None
        assets = []
        # produce assets: backing audio + a slide
        path = os.path.join(self.stage_dir,
                            "inter-" + str(abs(hash(inter_id)) % 9999)
                            + ".wav")
        try:
            audio.synth_melody(path, seed=len(inter_id))
            assets.append({"kind": "audio", "path": path})
        except Exception:
            pass
        ready = len(assets) > 0
        state = "ready" if ready else "deferred-not-ready"
        self.h.journal.append(
            "interstitial-state",
            {"interstitial": inter_id, "state": state,
             "assets": assets, "presented": ready},
            claimant="tool:audio.synth", basis="execution-evidence",
            refs=[inter_id])
        if ready:
            self.h.speech_floor.enqueue({"kind": "wav", "path": path,
                                         "label": "interstitial"})
        return {"state": state, "assets": assets, "presented": ready}
    # ---- scene enactment ------------------------------------------------------
    def enact_scene(self, kind="knock-knock", seed=None):
        """Personas enact a short public-domain scene — COMPOSED at run
        time (not canned), exercising available tool classes; absent
        classes honestly skipped."""
        pers = self.h.modules["personas"]
        roster = pers.roster()[:2]
        if len(roster) < 2:
            return {"status": "failed",
                    "reason": "need two personas to enact"}
        seed = int(seed or time.time())
        tool_classes = {"music": None, "media": None,
                        "backgrounds": None, "speech": None}
        # compose the script — persona-characterized lines (LLM-assisted
        # when the interactive handle is live)
        names = [p["name"] for p in roster]
        lines = self._compose_scene(kind, roster, seed)
        # music class: procedural synth is a real music tool in this build
        music_path = os.path.join(self.stage_dir,
                                  f"scene-music-{seed % 9999}.wav")
        try:
            audio.synth_melody(music_path, seed=seed)
            tool_classes["music"] = {"tool": "audio.music",
                                     "path": music_path}
        except Exception:
            tool_classes["music"] = {"tool": "audio.music",
                                     "absent": True}
        # backgrounds: procedural art via portrait renderer class
        try:
            from .personas import render_portrait
            bg = os.path.join(self.stage_dir,
                              f"scene-bg-{seed % 9999}.png")
            render_portrait(bg, {"id": "scene-" + str(seed)})
            tool_classes["backgrounds"] = {"tool": "art.procedural",
                                           "path": bg}
        except Exception:
            tool_classes["backgrounds"] = {"tool": "art.procedural",
                                           "absent": True}
        # speech class
        spoken = []
        if self.h.engines.get("tts", {}).get("voices"):
            for i, (p, line) in enumerate(zip(
                    (roster * ((len(lines) + 1) // 2))[:len(lines)],
                    lines)):
                voice = (p.get("voice") or {}).get("name") or \
                    self.h.engines["tts"]["voices"][0]["name"]
                w = os.path.join(self.stage_dir,
                                 f"scene-{seed % 9999}-line{i}.wav")
                info = audio.sapi_speak_to_wav(line, voice, w)
                if info:
                    spoken.append(info)
                    self.h.speech_floor.enqueue(
                        {"kind": "wav", "path": w,
                         "label": f"scene:{p['id']}"})
        tool_classes["speech"] = {"tool": "tts.sapi",
                                  "utterances": len(spoken),
                                  "absent": not spoken}
        scene = {"kind": kind, "cast": names, "lines": lines,
                 "composed": True, "toolClasses": tool_classes,
                 "spoken": len(spoken)}
        self.h.journal.append("scene-enactment", scene,
                              claimant="tool:scene.compose",
                              basis="execution-evidence")
        return scene
    def _compose_scene(self, kind, roster, seed):
        """Compose scene lines from persona registers + input — not a
        canned script (varies with seed/cast)."""
        a, b = roster[0], roster[1]
        prompt = ("Write a very short two-voice public-domain style "
                  f"{kind} between {a['name']} (register {a['register']})"
                  f" and {b['name']} (register {b['register']}). "
                  "4 lines, alternating, plain text, no stage "
                  "directions.")
        body = self.h.ollama(prompt, timeout=40, max_tokens=160)
        if body:
            lines = [l.strip("-•* ") for l in body.splitlines()
                     if l.strip() and not l.strip().endswith(":")]
            lines = [l for l in lines if len(l) > 5][:4]
            if len(lines) >= 2:
                return lines[:4]
        # deterministic composer — seed-varied, register-shaped
        openers = ["Knock, knock.", "Who's there?",
                   "A small light in the hallway.",
                   "And what brings you to the door?"]
        subjects = ["the rain", "a letter", "the kettle",
                    "an old map", "the cat", "a rumor"]
        s = subjects[seed % len(subjects)]
        lines = [
            openers[seed % 2],
            f"{b['name']} asks, plainly, about {s}.",
            f"{a['name']} answers — {s} again, {a['register']} as ever.",
            f"{b['name']} lets the door stay open."]
        return lines
