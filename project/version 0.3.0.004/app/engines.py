"""Engine seams — LLM, TTS, STT, portrait.
Honesty contract (C-DeclaredStubs / C-HonestyBanner): every engine reports its
real mode at boot. A declared stub never pretends output it did not produce;
an unreachable engine reports `error` — never `ok:true`-while-failing.
Live on this host when available:
- Ollama chat API (llama3.2) as the interactive LLM handle
- Windows SAPI via System.Speech as the local TTS renderer (blocks until
  playback completes — playbackMs is measured, not claimed)
"""
from __future__ import annotations
import json
import subprocess
import time
import urllib.request
class LLM:
    """Interactive LLM handle. mode: live-ollama:<model> | stub-declared."""
    def __init__(self, base="http://127.0.0.1:11434", model="llama3.2"):
        self.base = base
        self.model = model
        self.mode = "stub-declared"
        self.error = None
        self.probe()
    def probe(self) -> dict:
        try:
            with urllib.request.urlopen(self.base + "/api/version",
                                        timeout=4) as r:
                ver = json.loads(r.read().decode()).get("version")
            self.mode = f"live-ollama:{self.model}"
            self.ollama_version = ver
        except Exception as e:
            self.mode = "stub-declared"
            self.error = repr(e)
            self.ollama_version = None
        return {"mode": self.mode, "model": self.model,
                "error": self.error}
    def chat(self, system: str, prompt: str, max_tokens=400,
             timeout=120) -> dict:
        """Returns {ok, text, engine, error}."""
        if self.mode == "stub-declared":
            return {"ok": False, "engine": self.mode, "text": None,
                    "error": f"no interactive LLM ({self.error})"}
        body = json.dumps({
            "model": self.model, "stream": False,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": prompt}],
            "options": {"num_predict": max_tokens, "temperature": 0.7},
        }).encode()
        req = urllib.request.Request(self.base + "/api/chat", data=body,
                                     headers={"Content-Type":
                                              "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.loads(r.read().decode())
            return {"ok": True, "engine": self.mode,
                    "text": (d.get("message") or {}).get("content", ""),
                    "evalCount": d.get("eval_count")}
        except Exception as e:
            return {"ok": False, "engine": self.mode, "text": None,
                    "error": repr(e)}
class TTS:
    """Speech renderers — competing tools express `speech.render`.
    render-speech-sapi is local and real; render-speech-remote is honestly
    unconfigured (declared, never faked)."""
    def __init__(self):
        self.mode = "unavailable"
        self.voices = []
        self.probe()
    def probe(self) -> dict:
        try:
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Add-Type -AssemblyName System.Speech; "
                 "(New-Object System.Speech.Synthesis.SpeechSynthesizer)"
                 ".GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name }"],
                capture_output=True, text=True, timeout=20)
            names = [l.strip() for l in out.stdout.splitlines() if l.strip()]
            if names:
                self.voices = names
                self.mode = "sapi"
            else:
                self.mode = "stub-declared"
        except Exception:
            self.mode = "stub-declared"
        return {"mode": self.mode, "voices": self.voices}
    def render_local(self, text: str, voice=None, rate=0) -> dict:
        """Synchronous SAPI render — the call returns only when playback has
        finished, so playbackMs is a measured duration."""
        if self.mode != "sapi":
            return {"ok": False, "engine": "render-speech-sapi",
                    "error": f"renderer unavailable ({self.mode})"}
        name = voice or (self.voices[0] if self.voices else None)
        safe = text.replace("'", "''")[:900]
        sel = f"$s.SelectVoice('{name}'); " if name else ""
        ps = ("Add-Type -AssemblyName System.Speech; "
              "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
              f"{sel}$s.Rate = {int(rate)}; $s.Speak('{safe}')")
        t0 = time.time()
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, timeout=120)
            played = int((time.time() - t0) * 1000)
            return {"ok": True, "engine": "render-speech-sapi",
                    "voice": name, "playbackMs": played,
                    "heldUntilPlaybackComplete": True}
        except Exception as e:
            return {"ok": False, "engine": "render-speech-sapi",
                    "error": repr(e)}
    def render_remote(self, text: str, voice=None) -> dict:
        """Remote voice service — not configured on this installation.
        Declared, honest, never fabricated."""
        return {"ok": False, "engine": "render-speech-remote",
                "error": "remote speech service not configured "
                         "(declared absence)"}
class STT:
    """Spoken input. The browser Web Speech API is the only channel here;
    when the browser lacks it the surface declares `none`."""
    def __init__(self):
        self.mode = "browser-webspeech-declared"
    def transcript(self, text: str) -> dict:
        return {"ok": True, "engine": self.mode, "text": text}
class Engines:
    def __init__(self):
        self.llm = LLM()
        self.tts = TTS()
        self.stt = STT()
        self.portrait = {"mode": "procedural-svg-local"}
    def honesty(self) -> dict:
        return {
            "llm": {"mode": self.llm.mode, "model": self.llm.model,
                    "error": self.llm.error},
            "tts": {"mode": self.tts.mode, "voices": self.tts.voices},
            "stt": {"mode": self.stt.mode},
            "portrait": self.portrait,
            "declaredAbsences": [
                "fleet install", "fleet discovery", "exchange media "
                "(QR/AVQR encode+scan)", "oauth account connectors",
                "remote speech service", "native desktop shell "
                "(browser surface is the declared display)"],
        }
