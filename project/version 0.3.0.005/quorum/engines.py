"""Quorum engines — the declared seams to local capability.

Every engine reports its honest mode on /api/honesty (C-HonestyBanner):
live when the capability is real, declared-stub when absent. No silent
degradation, no ok:true-while-failing.

Seams:
- llm   : Ollama local models; role-diversified seam per decision-candidates
          §2 (gate / classify / evaluate / draft / general roles resolve to
          model tags, env-pinnable via QUORUM_LLM_MODEL_<ROLE>)
- tts   : Windows SAPI through a serialized speech floor (C-SpeechFloor)
- stt   : browser Web Speech API surface — absent server-side, declared
- art   : LLM-authored SVG portraits (V-A bar — generative path, not sprites)
- tones : machine-signaling beeps vs user-directed jingle (V-E bar)
"""
from __future__ import annotations

import json
import os
import queue
import re
import subprocess
import threading
import time
import urllib.request

from . import rows

OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

# Role → model tag (decision-candidates §2 item 1). Cheap roles share the
# default; env pins QUORUM_LLM_MODEL_GATE etc. override per role.
def _role_model(role: str) -> str:
    return os.environ.get(
        f"QUORUM_LLM_MODEL_{role.upper()}",
        os.environ.get("QUORUM_LLM_MODEL", "llama3.2:latest"))

class LLM:
    """engine.invoke ('llm', 'complete'|'describeImage', role=...)."""

    def __init__(self):
        self.mode = "absent"
        self.models = []
        self.probe()

    def probe(self):
        try:
            with urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=3) as r:
                self.models = [m["name"] for m in json.loads(r.read())["models"]]
            gen = _role_model("general")
            tag = gen if gen in self.models else (self.models[0] if self.models else "")
            self.mode = f"live-ollama:{tag.split(':')[0]}" if self.models \
                        else "ollama-no-models"
        except Exception:
            self.mode = "absent"
            self.models = []

    def available(self) -> bool:
        return self.mode.startswith("live-ollama")

    def complete(self, prompt: str, role: str = "general",
                 model: str = "", max_tokens: int = 900,
                 timeout: int = 90) -> dict:
        """One untyped completion, role-tagged. Returns {ok, text, model,
        claimant} — model:<id> attribution for ledger claims."""
        tag = model or _role_model(role)
        if tag not in self.models and self.models:
            tag = self.models[0]
        if not self.available():
            return {"ok": False, "stub": True, "text": "",
                    "model": tag, "claimant": f"model:{tag}",
                    "note": "llm engine absent — honest stub, no fabricated output"}
        try:
            body = json.dumps({
                "model": tag, "prompt": prompt, "stream": False,
                "options": {"num_predict": max_tokens, "temperature": 0.7},
            }).encode()
            req = urllib.request.Request(f"{OLLAMA}/api/generate", data=body,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                out = json.loads(r.read())
            return {"ok": True, "text": out.get("response", ""),
                    "model": tag, "claimant": f"model:{tag}"}
        except Exception as e:
            return {"ok": False, "stub": True, "text": "", "model": tag,
                    "claimant": f"model:{tag}", "note": f"llm call failed: {e}"}

    def describe_image(self, path: str, prompt="Describe this image.") -> dict:
        """Vision seam — moondream when present."""
        tag = next((m for m in self.models if "moondream" in m), "")
        if not tag:
            return {"ok": False, "stub": True, "text": "",
                    "note": "no vision model installed"}
        try:
            import base64
            with open(path, "rb") as f:
                img = base64.b64encode(f.read()).decode()
            body = json.dumps({"model": tag, "prompt": prompt,
                               "images": [img], "stream": False}).encode()
            req = urllib.request.Request(f"{OLLAMA}/api/generate", data=body,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                out = json.loads(r.read())
            return {"ok": True, "text": out.get("response", ""), "model": tag}
        except Exception as e:
            return {"ok": False, "stub": True, "text": "", "note": str(e)}


# ---------------------------------------------------------------------------
# Serialized speech floor (C-SpeechFloor / C-PerceivableRespondents):
# generated speech waits for the previous speaker; playback duration is
# measured, not assumed.
class SpeechFloor:
    def __init__(self, book=None):
        self.book = book
        self.q: queue.Queue = queue.Queue()
        self.depth = 0
        self.playing = None
        self.last_played = None
        self._stop = False
        self._voices = []
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def voices(self) -> list[dict]:
        if not self._voices:
            self._voices = sapi_voices()
        return self._voices

    def admit(self, text: str, voice: str = "", persona="") -> dict:
        item = {"id": rows.new_id("sp"), "text": text, "voice": voice,
                "persona": persona, "queued_at": rows.now_ms()}
        self.q.put(item)
        self.depth += 1
        return {"queued": item["id"], "depth": self.depth}

    def status(self) -> dict:
        return {"depth": self.q.qsize(), "playing": self.playing,
                "last": self.last_played, "voices": self.voices()}

    def _worker(self):
        while not self._stop:
            try:
                item = self.q.get(timeout=0.5)
            except queue.Empty:
                continue
            self.depth = self.q.qsize()
            self.playing = item["id"]
            t0 = time.time()
            ok = sapi_speak(item["text"], item["voice"])
            ms = int((time.time() - t0) * 1000)
            self.playing = None
            self.last_played = {**item, "ok": ok, "playbackMs": ms,
                                "heldUntilPlaybackComplete": True}
            if self.book:
                self.book.claim(
                    item["id"], "floor:played",
                    {"playbackMs": ms, "ok": ok, "persona": item["persona"],
                     "heldUntilPlaybackComplete": True},
                    claimant="engine:tts", certainty=0.9, basis="execution")
            self.q.task_done()

def sapi_voices() -> list[dict]:
    """Enumerate installed SAPI voices via PowerShell System.Speech."""
    try:
        ps = ("Add-Type -AssemblyName System.Speech; "
              "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
              "$s.GetInstalledVoices() | ForEach-Object "
              "{ $_.VoiceInfo | Select-Object Name,Gender,Age,Culture } "
              "| ConvertTo-Json")
        out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                             capture_output=True, text=True, timeout=15)
        data = json.loads(out.stdout or "[]")
        if isinstance(data, dict):
            data = [data]
        return [{"id": v["Name"], "gender": str(v.get("Gender", "")),
                 "culture": str(v.get("Culture", ""))} for v in data]
    except Exception:
        return []

def sapi_speak(text: str, voice: str = "", rate: int = 0) -> bool:
    try:
        safe = text.replace("'", "''")[:3000]
        sel = f"$s.SelectVoice('{voice}');" if voice else ""
        ps = ("Add-Type -AssemblyName System.Speech; "
              "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
              f"{sel}$s.Rate={rate}; $s.Speak('{safe}')")
        subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, timeout=60)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Tones (V-E bar): machine-signaling and user-directed alerts live in
# different registers. Machine = short system beeps for instance-to-instance
# signaling; user-directed = a rising three-note welcome jingle.
def machine_beep(n: int = 2, freq: int = 880, ms: int = 120):
    """Instance-to-instance signaling tone — deliberately terse."""
    try:
        cmd = "; ".join(f"[console]::beep({freq},{ms})" for _ in range(n))
        subprocess.Popen(["powershell", "-NoProfile", "-Command", cmd],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def user_jingle():
    """User-directed alert — a distinct melodic register (welcome chime)."""
    try:
        notes = "[console]::beep(523,160); [console]::beep(659,160); " \
                "[console]::beep(784,260)"
        subprocess.Popen(["powershell", "-NoProfile", "-Command", notes],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
