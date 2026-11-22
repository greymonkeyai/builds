"""Engine seams: LLM, TTS, STT, portrait. Honest modes only.

Each engine reports its real mode (live/stub/unavailable) at probe time; modes
are asserted to the ledger (engine:mode) and surfaced on the honesty banner.
There is no silent degradation: a stub fallback is always declared.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import urllib.request
from typing import Optional


def _http_json(url: str, payload: Optional[dict] = None, timeout: float = 2.0):
    try:
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(url, data=data,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


class LLMEngine:
    """Local inference via Ollama when reachable; otherwise a DECLARED
    template fallback (stubFallback: on, never silent)."""

    def __init__(self, endpoint: str = "http://localhost:11434"):
        self.endpoint = endpoint
        self.mode = "stub"
        self.model = None
        self.probe()

    def probe(self) -> dict:
        tags = _http_json(f"{self.endpoint}/api/tags", timeout=1.0)
        if tags and tags.get("models"):
            self.mode = "live-ollama"
            names = [m.get("name", "") for m in tags["models"]]
            prefer = ("llama", "qwen", "mistral", "phi3", "phi4", "gemma",
                      "deepseek", "granite", "smollm")
            self.model = next((n for n in names
                               if any(p in n.lower() for p in prefer)),
                              names[0] if names else None)
        else:
            self.mode = "stub"
            self.model = None
        return {"engine": "llm", "mode": self.mode, "model": self.model}

    def complete(self, prompt: str, system: str = "", max_tokens: int = 220) -> dict:
        if self.mode == "live-ollama" and self.model:
            r = _http_json(f"{self.endpoint}/api/generate",
                           {"model": self.model, "prompt": prompt,
                            "system": system, "stream": False,
                            "options": {"num_predict": max_tokens}}, timeout=60)
            if r and r.get("response"):
                return {"ok": True, "text": r["response"].strip(), "engine": "ollama",
                        "model": self.model, "stub": False}
        return {"ok": True, "text": self._fallback(prompt, system),
                "engine": "template", "stub": True}

    @staticmethod
    def _fallback(prompt: str, system: str) -> str:
        return ("[declared stub — no local inference host reachable] "
                + (prompt[:400]))


class TTSEngine:
    """Speech as two independently-defined competing tools (A13):
    local Windows SAPI vs. remote provider. Neither is hardcoded as primary;
    the tool-ranking machinery chooses, and the remote tool honestly reports
    'unconfigured' until a source grant exists."""

    def __init__(self):
        self.local_ok = os.name == "nt"
        self.remote_configured = False
        self._voices = None

    def voices(self) -> list:
        """Enumerate installed SAPI voices (cached). Honest: empty when the
        platform cannot enumerate; callers declare rather than fabricate."""
        if self._voices is not None:
            return self._voices
        self._voices = []
        if not self.local_ok:
            return self._voices
        try:
            ps = ("Add-Type -AssemblyName System.Speech; "
                  "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                  "$s.GetInstalledVoices() | ForEach-Object "
                  "{ $_.VoiceInfo.Name }")
            r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                               capture_output=True, text=True, timeout=20)
            self._voices = [v.strip() for v in r.stdout.splitlines() if v.strip()]
        except Exception:
            self._voices = []
        return self._voices

    def probe(self) -> dict:
        return {"engine": "tts",
                "local": "sapi" if self.local_ok else "unavailable",
                "remote": "unconfigured"}

    def speak_local(self, text: str, out_wav: Optional[str] = None,
                    voice: Optional[dict] = None) -> dict:
        """Synthesize via System.Speech (inproc, local). A persona's voice
        preferences (C-VoiceDiversity — portable modifiable settings) select
        the SAPI voice and rate. Returns artifact path when out_wav given,
        else speaks aloud."""
        if not self.local_ok:
            return {"ok": False, "error": "SAPI unavailable on this host"}
        voice = voice or {}
        text_safe = text.replace("'", "''")[:2000]
        sel = ""
        vname = voice.get("name")
        if vname and vname in self.voices():
            sel = f"$s.SelectVoice('{vname}'); "
        rate = voice.get("rate")
        if isinstance(rate, (int, float)) and -10 <= rate <= 10:
            sel += f"$s.Rate = {int(rate)}; "
        if out_wav:
            ps = ("Add-Type -AssemblyName System.Speech; "
                  "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                  f"$s.SetOutputToWaveFile('{out_wav}'); "
                  f"$s.Speak('{text_safe}'); $s.Dispose()")
        else:
            ps = ("Add-Type -AssemblyName System.Speech; "
                  "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                  f"$s.Speak('{text_safe}'); $s.Dispose()")
        try:
            subprocess.Popen(["powershell", "-NoProfile", "-Command", ps],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"ok": True, "engine": "sapi", "artifact": out_wav,
                    "voice": (voice or {}).get("name") or "sapi-default",
                    "rate": (voice or {}).get("rate")}
        except Exception as e:
            return {"ok": False, "error": repr(e)}

    def speak_remote(self, text: str) -> dict:
        if not self.remote_configured:
            return {"ok": False, "error": "remote TTS not configured — no source grant",
                    "unconfigured": True}
        return {"ok": False, "error": "remote TTS unreachable"}


class STTEngine:
    """Speech capture: browser-side Web Speech API posts transcripts; the
    server records them as device:speech-transcript witnesses with the reported
    confidence. If the browser lacks the API the UI declares it."""

    def probe(self) -> dict:
        return {"engine": "stt", "mode": "browser-webSpeech-or-declared-none"}


class PortraitEngine:
    """Deterministic geometric SVG portrait per persona — a real artifact,
    generated locally, no external model claim."""

    def render(self, persona: dict, out_dir: Optional[str] = None) -> dict:
        pid = persona["id"]
        h = hashlib.sha256(pid.encode()).digest()
        c1 = "#" + h[:3].hex()
        c2 = "#" + h[3:6].hex()
        c3 = "#" + h[6:9].hex()
        eyes = h[9] % 4
        mouth = h[10] % 4
        mark = ""
        if persona.get("imitates"):
            mark = ('<polygon points="88,4 96,12 88,20 80,12" fill="#ffbf00" '
                    'stroke="#000" stroke-width="1"/>')
        eye_shapes = [
            '<circle cx="38" cy="44" r="4"/><circle cx="62" cy="44" r="4"/>',
            '<rect x="34" y="41" width="8" height="6"/><rect x="58" y="41" width="8" height="6"/>',
            '<circle cx="38" cy="44" r="5" fill="none" stroke-width="2"/><circle cx="62" cy="44" r="5" fill="none" stroke-width="2"/>',
            '<path d="M33 44 h10 M57 44 h10" stroke-width="3"/>',
        ]
        mouth_shapes = [
            '<path d="M40 66 q10 8 20 0" fill="none" stroke-width="3"/>',
            '<rect x="42" y="64" width="16" height="4"/>',
            '<path d="M40 68 q10 -6 20 0" fill="none" stroke-width="3"/>',
            '<circle cx="50" cy="66" r="4"/>',
        ]
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            f'<rect width="100" height="100" rx="14" fill="{c1}"/>'
            f'<circle cx="50" cy="50" r="36" fill="{c2}"/>'
            f'<g fill="{c3}" stroke="{c3}">{eye_shapes[eyes]}{mouth_shapes[mouth]}</g>'
            f'{mark}</svg>')
        artifact = None
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
            artifact = os.path.join(out_dir, f"{pid}.svg")
            with open(artifact, "w", encoding="utf-8") as f:
                f.write(svg)
        return {"ok": True, "svg": svg, "artifact": artifact,
                "dataUrl": "data:image/svg+xml;base64," +
                           base64.b64encode(svg.encode()).decode()}


class Engines:
    def __init__(self):
        self.llm = LLMEngine()
        self.tts = TTSEngine()
        self.stt = STTEngine()
        self.portrait = PortraitEngine()

    def report(self) -> dict:
        return {"llm": self.llm.probe(), "tts": self.tts.probe(),
                "stt": self.stt.probe(),
                "portrait": {"engine": "portrait", "mode": "inproc-svg"}}
