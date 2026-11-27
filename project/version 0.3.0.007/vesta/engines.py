"""engines — model + speech plumbing, honestly declared.

LLM: Ollama at 127.0.0.1:11434 when present (live-ollama:<model>);
absent → deterministic composed fallback replies, `fallback-declared`
art — legible, never authored-claimed.  TTS: Windows SAPI via PowerShell
when present; absent → declared-absent, utterances still serialized and
measured on the floor.  Every engine mode is reported on the status bar
(C-HonestyBanner, C-DeclaredStubs).
"""

import json
import os
import subprocess
import time
import urllib.request

OLLAMA = os.environ.get("VESTA_OLLAMA", "http://127.0.0.1:11434")
CHAT_MODEL = os.environ.get("VESTA_MODEL", "llama3.2:latest")


def probe_ollama():
    try:
        with urllib.request.urlopen(OLLAMA + "/api/tags", timeout=2) as r:
            data = json.loads(r.read())
        names = [m["name"] for m in data.get("models", [])]
        model = CHAT_MODEL if CHAT_MODEL in names else (names[0] if names else None)
        return {"live": bool(model), "model": model, "models": names}
    except Exception:
        return {"live": False, "model": None, "models": []}


def llm(prompt, system="", model=None, timeout=60, temperature=0.7):
    """Chat completion via Ollama. Returns (text, elapsed_s) or (None, elapsed)."""
    t0 = time.time()
    try:
        body = {"model": model or CHAT_MODEL, "prompt": prompt,
                "stream": False, "options": {"temperature": temperature,
                                             "num_predict": 320}}
        if system:
            body["system"] = system
        req = urllib.request.Request(
            OLLAMA + "/api/generate",
            data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
        return (data.get("response") or "").strip(), round(time.time() - t0, 3)
    except Exception:
        return None, round(time.time() - t0, 3)


def sapi_voices():
    """Installed SAPI voice catalog. Empty list → declared absence."""
    try:
        ps = ("Add-Type -AssemblyName System.Speech; "
              "$v=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
              "$v.GetInstalledVoices() | ForEach-Object { "
              "$_.VoiceInfo.Name + '|' + $_.VoiceInfo.Gender } | "
              "ConvertTo-Json")
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True, timeout=15)
        raw = r.stdout.strip()
        if not raw:
            return []
        data = json.loads(raw)
        if isinstance(data, str):
            data = [data]
        out = []
        for line in data:
            name, _, gender = line.partition("|")
            out.append({"name": name.strip(), "gender": gender.strip(),
                        "engine": "sapi"})
        return out
    except Exception:
        return []


def sapi_speak_file(text, wav_path, voice=None, rate=0, timeout=30):
    """Synthesize text to a WAV file via SAPI. Returns (ok, seconds)."""
    t0 = time.time()
    try:
        esc_text = text.replace("'", "''")
        ps = [
            "Add-Type -AssemblyName System.Speech",
            "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer",
        ]
        if voice:
            ps.append(f"$s.SelectVoice('{voice.replace(chr(39), '')}')")
        ps.append(f"$s.Rate={int(rate)}")
        ps.append("$s.SetOutputToWaveFile('" + wav_path.replace("'", "") + "')")
        ps.append("$s.Speak('" + esc_text + "')")
        ps.append("$s.Dispose()")
        r = subprocess.run(["powershell", "-NoProfile", "-Command", "; ".join(ps)],
                           capture_output=True, text=True, timeout=timeout)
        ok = os.path.exists(wav_path) and os.path.getsize(wav_path) > 200
        return ok, round(time.time() - t0, 3)
    except Exception:
        return False, round(time.time() - t0, 3)


def wav_seconds(path):
    """Duration of a PCM WAV from its header (measured, not assumed)."""
    try:
        import wave
        with wave.open(path, "rb") as w:
            return round(w.getnframes() / float(w.getframerate()), 3)
    except Exception:
        return None


def probe_bt():
    """Bluetooth transport availability — honest enumeration."""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue | "
             "Select-Object -First 8 -ExpandProperty FriendlyName | ConvertTo-Json"],
            capture_output=True, text=True, timeout=15)
        raw = r.stdout.strip()
        if not raw:
            return {"radio": False, "devices": []}
        data = json.loads(raw)
        if isinstance(data, str):
            data = [data]
        radios = [d for d in data if "enumerator" in d.lower() or "radio" in d.lower() or "intel" in d.lower() or "realtek" in d.lower()]
        return {"radio": bool(data), "devices": data, "radios": radios}
    except Exception:
        return {"radio": False, "devices": []}
