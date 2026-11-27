"""Engines — LLM, speech, art. Every mode is declared honestly:
`live-*` for a real engine, `*-declared` for an honest fallback.
"""
import base64
import json
import math
import os
import queue
import re
import struct
import subprocess
import threading
import time
import urllib.request
OLLAMA_URL = os.environ.get("CHORUS_OLLAMA", "http://localhost:11434")
LLM_MODEL = os.environ.get("CHORUS_LLM_MODEL", "llama3.2")
ART_MODEL = os.environ.get("CHORUS_ART_MODEL", LLM_MODEL)
def _http_json(url, payload, timeout):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))
class LLM:
    def __init__(self):
        self.mode = "absent-declared"
        self.model = LLM_MODEL
        try:
            tags = _http_json(OLLAMA_URL + "/api/tags", None, 4) if False else None
            with urllib.request.urlopen(OLLAMA_URL + "/api/tags", timeout=4) as r:
                tags = json.loads(r.read().decode())
            names = [m["name"] for m in tags.get("models", [])]
            if any(n.split(":")[0] == self.model.split(":")[0] for n in names):
                self.mode = f"live-ollama:{self.model}"
        except Exception:
            self.mode = "absent-declared"
    @property
    def live(self):
        return self.mode.startswith("live-ollama")
    def complete(self, prompt, system=None, timeout=45, temperature=0.7, model=None):
        """One completion. Returns (text, meta). Never fakes a model."""
        if not self.live:
            return None, {"engine": self.mode, "declared": True}
        body = {
            "model": model or self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": 512},
        }
        if system:
            body["system"] = system
        t0 = time.time()
        try:
            req = urllib.request.Request(
                OLLAMA_URL + "/api/generate",
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                out = json.loads(r.read().decode())
            return out.get("response", "").strip(), {
                "engine": self.mode, "ms": int((time.time() - t0) * 1000)}
        except Exception as e:
            return None, {"engine": self.mode, "error": str(e), "declared": True}
# ---------------- speech ----------------
def sapi_voices():
    """Enumerate installed SAPI voices via PowerShell (engine mapping surface)."""
    ps = ("Add-Type -AssemblyName System.Speech;"
          "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
          "$s.GetInstalledVoices() | ForEach-Object {"
          "  $v=$_.VoiceInfo;"
          "  Write-Output ($v.Name + '|' + $v.Gender + '|' + $v.Age) }")
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True, text=True, timeout=20)
        voices = []
        for line in out.stdout.splitlines():
            parts = line.strip().split("|")
            if len(parts) == 3 and parts[0]:
                voices.append({"name": parts[0], "gender": parts[1],
                               "age": parts[2], "engine": "sapi"})
        return voices
    except Exception:
        return []
def sapi_render(text, voice, wav_path, rate=0, timeout=60):
    """Render text to a WAV file with SAPI. Returns (ok, ms, err)."""
    safe_text = text.replace("'", "''")
    safe_voice = (voice or "").replace("'", "''")
    safe_path = wav_path.replace("'", "''")
    ps = (
        "Add-Type -AssemblyName System.Speech;"
        "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
        f"$s.Rate={rate};"
        f"try {{ $s.SelectVoice('{safe_voice}') }} catch {{}};"
        f"$s.SetOutputToWaveFile('{safe_path}');"
        f"$s.Speak('{safe_text}');"
        "$s.SetOutputToNull();$s.Dispose()")
    t0 = time.time()
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, timeout=timeout)
        ms = int((time.time() - t0) * 1000)
        if os.path.exists(wav_path) and os.path.getsize(wav_path) > 44:
            return True, ms, None
        return False, ms, "no output produced"
    except Exception as e:
        return False, int((time.time() - t0) * 1000), str(e)
def wav_duration_ms(path):
    try:
        with open(path, "rb") as f:
            data = f.read()
        if len(data) < 44 or data[:4] != b"RIFF":
            return None
        # find fmt + data chunks
        i = 12
        byte_rate = None
        data_len = None
        while i + 8 <= len(data):
            cid = data[i:i + 4]
            size = struct.unpack("<I", data[i + 4:i + 8])[0]
            if cid == b"fmt ":
                byte_rate = struct.unpack("<I", data[i + 12:i + 16])[0]
            if cid == b"data":
                data_len = size
                break
            i += 8 + size + (size & 1)
        if byte_rate and data_len:
            return int(data_len / byte_rate * 1000)
    except Exception:
        return None
    return None
def synth_tone_wav(path, freqs, ms_each=120, volume=0.35, rate=22050):
    """Procedurally synthesize a short tone snippet WAV — used for persona
    acknowledgement snippets when no pre-rendered voice snippet exists, and
    for background-channel sample tracks. Honest basis: locally synthesized."""
    n = int(rate * ms_each / 1000)
    frames = []
    for f in freqs:
        for i in range(n):
            t = i / rate
            env = min(1.0, i / (rate * 0.02)) * min(1.0, (n - i) / (rate * 0.03))
            v = int(32767 * volume * env * math.sin(2 * math.pi * f * t))
            frames.append(struct.pack("<h", v))
    pcm = b"".join(frames)
    with open(path, "wb") as fh:
        fh.write(b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVE")
        fh.write(b"fmt " + struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16))
        fh.write(b"data" + struct.pack("<I", len(pcm)) + pcm)
def synth_ambient_wav(path, seconds=6, kind="rain", rate=22050):
    """Synthesize a background-channel sample track (honest local basis)."""
    import random
    random.seed(7)
    total = int(rate * seconds)
    frames = []
    phase = 0.0
    for i in range(total):
        t = i / rate
        if kind == "rain":
            v = (random.random() * 2 - 1) * 0.22
            v *= 0.6 + 0.4 * math.sin(2 * math.pi * 0.3 * t)
        elif kind == "hum":
            v = 0.18 * math.sin(2 * math.pi * 110 * t) + 0.09 * math.sin(2 * math.pi * 220 * t)
        elif kind == "drift":
            phase += (random.random() - 0.5) * 0.02
            v = 0.16 * math.sin(2 * math.pi * (180 + 60 * math.sin(2 * math.pi * 0.1 * t)) * t + phase)
        else:
            v = 0.12 * math.sin(2 * math.pi * 240 * t)
        frames.append(struct.pack("<h", int(32767 * max(-1, min(1, v)))))
    pcm = b"".join(frames)
    with open(path, "wb") as fh:
        fh.write(b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVE")
        fh.write(b"fmt " + struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16))
        fh.write(b"data" + struct.pack("<I", len(pcm)) + pcm)
class SpeechFloor:
    """Serialized playback admission through a host queue (C-SpeechFloor).
    Playback is measured (WAV duration), not assumed; the floor is held until
    each item completes. Sequential respondents keep contributions perceivable.
    """
    def __init__(self, host):
        self.host = host
        self.q = queue.Queue()
        self.log = []          # measured playback records
        self.current = None
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._run, daemon=True)
        self._t.start()
    def enqueue(self, item):
        """item: {kind: ack|utterance|tone|channel, wav, persona, text, turn}"""
        self.q.put(item)
    def _run(self):
        while not self._stop.is_set():
            try:
                item = self.q.get(timeout=0.4)
            except queue.Empty:
                continue
            self.current = item
            dur = None
            if item.get("wav") and os.path.exists(item["wav"]):
                dur = wav_duration_ms(item["wav"])
                try:
                    subprocess.run(
                        ["powershell", "-NoProfile", "-Command",
                         f"(New-Object Media.SoundPlayer '{item['wav']}').PlaySync()"],
                        capture_output=True, timeout=max(5, (dur or 1000) / 1000 + 8))
                except Exception:
                    pass
            held = dur if dur is not None else 0
            rec = {"kind": item.get("kind"), "persona": item.get("persona"),
                   "wav": item.get("wav"), "measured_ms": dur,
                   "held_ms": held, "turn": item.get("turn"),
                   "text": item.get("text"), "excerpt": item.get("excerpt", False),
                   "at": time.time()}
            self.log.append(rec)
            self.host.note_speech(rec)
            self.current = None
            self.q.task_done()
    def stop(self):
        self._stop.set()
def speakable(text):
    """Derived rendering for speech (C-SpeakableRendering): strip markup,
    citations, and non-speech punctuation; never vocalized verbatim."""
    t = re.sub(r"```.*?```", " ", text, flags=re.S)
    t = re.sub(r"[*_`#>]", "", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    t = re.sub(r"https?://\S+", "the linked source", t)
    t = re.sub(r"\[[^\]]*\]", "", t)
    t = re.sub(r"\(([^)]*)\)", r", \1,", t)
    t = re.sub(r"^[-*\d.>]+\s*", "", t, flags=re.M)
    t = re.sub(r"\s+", " ", t).strip()
    return t
def split_utterances(text, max_chars=900):
    """Split for sequential floor-held utterances at sentence boundaries —
    speech completes at boundaries, never a silent mid-sentence cut."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks, cur = [], ""
    for s in sentences:
        if cur and len(cur) + len(s) + 1 > max_chars:
            chunks.append(cur)
            cur = s
        else:
            cur = (cur + " " + s).strip()
    if cur:
        chunks.append(cur)
    # over-long single sentences: split at clause boundaries, then declare
    out = []
    for c in chunks:
        if len(c) <= max_chars:
            out.append((c, False))
            continue
        parts = re.split(r"(?<=[,;—])\s+", c)
        buf = ""
        for p in parts:
            if buf and len(buf) + len(p) + 1 > max_chars:
                out.append((buf, True))  # declared excerpt boundary
                buf = p
            else:
                buf = (buf + " " + p).strip()
        if buf:
            out.append((buf, len(out) > 0))
    return out
# ---------------- art ----------------
def fallback_portrait_svg(persona):
    """Declared-fallback portrait: procedural, bound, and marked not-authored.
    Distinct per persona via seeded geometry (C-PersonalityArt)."""
    import hashlib
    h = int(hashlib.sha1(persona["id"].encode()).hexdigest()[:8], 16)
    hue = h % 360
    hue2 = (hue + 40 + (h >> 8) % 60) % 360
    eye = 60 + (h >> 4) % 30
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">'
        f'<rect width="200" height="200" fill="hsl({hue},45%,82%)"/>'
        f'<circle cx="100" cy="105" r="62" fill="hsl({hue2},55%,72%)"/>'
        f'<circle cx="78" cy="92" r="9" fill="hsl({hue},60%,30%)"/>'
        f'<circle cx="122" cy="92" r="9" fill="hsl({hue},60%,30%)"/>'
        f'<path d="M70 132 Q100 {120 + eye % 30} 130 132" stroke="hsl({hue},60%,30%)" '
        f'stroke-width="5" fill="none" stroke-linecap="round"/>'
        f'<text x="100" y="188" font-size="13" text-anchor="middle" '
        f'fill="hsl({hue},50%,30%)">{persona["name"]} — generated mark</text></svg>')
def llm_portrait_svg(llm, persona):
    """Ask the LLM to author an SVG portrait of THIS persona (V-A bar).
    Returns (svg, meta) — None when the model can't deliver, honestly."""
    if not llm.live:
        return None, {"engine": llm.mode, "authored": False, "declared": True}
    prompt = (
        "Draw an SVG portrait avatar for a fictional persona.\n"
        f"Name: {persona['name']}\n"
        f"Persona: {persona.get('register','')} — interests: "
        f"{', '.join(persona.get('interests', []))}\n"
        "Output ONLY a single <svg ...>...</svg> element, viewBox 0 0 200 200, "
        "flat illustrated style, stylized face, distinctive for this persona, "
        "no text, no markdown fences.")
    text, meta = llm.complete(prompt, timeout=90, temperature=0.8, model=ART_MODEL)
    if not text:
        return None, {**meta, "authored": False}
    m = re.search(r"<svg.*?</svg>", text, re.S)
    if not m:
        return None, {**meta, "authored": False, "declared": True,
                      "error": "model returned no svg"}
    svg = m.group(0)
    if "<" not in svg or len(svg) < 200:
        return None, {**meta, "authored": False}
    svg = re.sub(r"<script.*?</script>", "", svg, flags=re.S)
    return svg, {**meta, "authored": True}
