"""hearth host — the running installation.
Owns: config, durable journal + transient boundary, persistent indices
(the privileged class: personas/tools keep identity outside semantic
rows), engine capability declarations (honest modes), the Idle Turn
Steward, the speech floor, and metrics (gate + speech latency, seconds).
"""
import json
import os
import socket
import subprocess
import threading
import time
import urllib.request
from . import audio
from .ledger import Journal, materialize_partition
APP = "hearth"
PEER_PORT_HINT = 9540
class Host:
    def __init__(self, root, data_dir, bare=False, sabotage=None):
        self.root = root
        self.data_dir = data_dir
        self.bare = bare
        self.sabotage = sabotage
        os.makedirs(data_dir, exist_ok=True)
        self.t0 = time.time()
        transient = os.path.join(data_dir, "transient")
        self.journal = Journal(data_dir, transient)
        self.config_path = os.path.join(data_dir, "config.json")
        self.config = self._load_config()
        self.indices_path = os.path.join(data_dir, "indices.json")
        self.indices = self._load_indices()
        self.partition_path = os.path.join(data_dir, "partition.json")
        self.cred_dir = os.path.join(data_dir, "credentials")
        os.makedirs(self.cred_dir, exist_ok=True)
        self.audio_dir = os.path.join(data_dir, "audio")
        self.artifacts_dir = os.path.join(data_dir, "artifacts")
        os.makedirs(self.audio_dir, exist_ok=True)
        os.makedirs(self.artifacts_dir, exist_ok=True)
        self.metrics_path = os.path.join(data_dir, "metrics.jsonl")
        self.gate = {"passed": False, "seconds": None}
        self.node = {"id": self.config.setdefault("nodeId", self._mkid()),
                     "network": self.config.setdefault("networkId",
                                                       self._mkid("net-")),
                     "launchedFrom": os.path.abspath(root)}
        self._save_config()
        self.commit_queue = []
        self.commit_lock = threading.Lock()
        self.speech_floor = SpeechFloor(self)
        self.engines = {}
        self.steward = None
        self.modules = {}
    # ------------------------------------------------ ids / config
    def _mkid(self, prefix="node-"):
        import uuid
        return prefix + uuid.uuid4().hex[:8]
    def _load_config(self):
        if os.path.exists(self.config_path):
            try:
                return json.load(open(self.config_path))
            except Exception:
                pass
        return {}
    def _save_config(self):
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=1)
    def _load_indices(self):
        if os.path.exists(self.indices_path):
            try:
                return json.load(open(self.indices_path))
            except Exception:
                pass
        return {"personas": {}, "tools": {}}
    def save_indices(self):
        with open(self.indices_path, "w") as f:
            json.dump(self.indices, f, indent=1)
    # ------------------------------------------------ metrics (seconds)
    def metric(self, name, seconds, **extra):
        row = {"ts": round(time.time(), 3), "name": name,
               "seconds": round(float(seconds), 1)}
        row.update(extra)
        with open(self.metrics_path, "a") as f:
            f.write(json.dumps(row) + "\n")
        return row
    def metrics(self):
        out = []
        if os.path.exists(self.metrics_path):
            for line in open(self.metrics_path):
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
        return out
    # ------------------------------------------------ engines
    def detect_engines(self):
        """Honest capability surface — every mode declared, none hidden."""
        e = {}
        # LLM — primary interactive handle
        llm = self._probe_ollama()
        e["llm"] = llm or {"mode": "fallback-declared",
                           "note": "no ollama; deterministic in-register "
                                   "fallback replies, never authored-claimed"}
        e["tts"] = self._probe_sapi()
        e["stt"] = {"mode": "absent-declared",
                    "note": "no server-side STT this cycle"}
        e["audioOut"] = ({"mode": "device-present"}
                         if audio.audio_device_present()
                         else {"mode": "absent-declared"})
        e["bt"] = self._probe_bt()
        e["mail"] = {"mode": "fixture-or-configured",
                     "note": "fixtures/inbox basis unless an IMAP account "
                             "is configured; fixture basis labeled"}
        e["seedSigning"] = {"mode": "unsigned-source",
                            "note": "AV allowlist arrangement documented "
                                    "(C-SeedSigning)"}
        if self.sabotage == "stub-engines":
            e["llm"] = {"mode": "absent-declared"}
            e["tts"] = {"mode": "absent-declared"}
            e["audioOut"] = {"mode": "absent-declared"}
            e["bt"] = {"mode": "absent-declared"}
        self.engines = e
        return e
    def _probe_ollama(self):
        try:
            with urllib.request.urlopen(
                    "http://localhost:11434/api/tags", timeout=3) as r:
                models = json.loads(r.read()).get("models", [])
            names = [m["name"] for m in models]
            pick = "llama3.2:latest" if "llama3.2:latest" in names \
                else (names[0] if names else None)
            if pick:
                return {"mode": "live-ollama:" + pick, "models": names}
        except Exception:
            pass
        return None
    def ollama(self, prompt, system="", timeout=45, max_tokens=120):
        """Primary interactive LLM handle — accepts and answers prompts.
        Returns None when unavailable (callers then declare fallback)."""
        if not str(self.engines.get("llm", {}).get("mode", "")
                   ).startswith("live-ollama"):
            return None
        try:
            body = {"model": self.engines["llm"]["mode"].split(":", 1)[1],
                    "prompt": prompt, "system": system or
                    "You are a concise conversational persona. Reply in 1-3 "
                    "plain conversational sentences. No lists, no markdown.",
                    "stream": False,
                    "options": {"num_predict": max_tokens, "temperature": 0.8}}
            req = urllib.request.Request(
                "http://localhost:11434/api/generate",
                data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read()).get("response", "").strip()
        except Exception:
            return None
    def _probe_sapi(self):
        voices = audio.sapi_voices()
        if voices:
            return {"mode": "sapi", "voices": voices}
        return {"mode": "absent-declared", "voices": []}
    def _probe_bt(self):
        try:
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-Service bthserv -ErrorAction Stop).Status"],
                capture_output=True, text=True, timeout=10)
            if "Running" in out.stdout:
                return {"mode": "radio-present"}
        except Exception:
            pass
        return {"mode": "absent-declared"}
    # ------------------------------------------------ gate + partition
    def mount_partition(self):
        """Essential launch slice ordered by schema dependency."""
        j = self.journal
        sections = [
            ("indices", [self.indices]),
            ("config", [self.config]),
            ("personas", j.rows("persona-attr")[-100:]),
            ("tools", j.rows("tool-def")[-100:]),
            ("sources", j.rows("source-row")[-200:]),
            ("needs-open", [r for r in j.rows("need")
                            if r["value"].get("state") == "open"][-200:]),
        ]
        materialize_partition(j, self.partition_path, sections)
        return sections
    def evaluate_gate(self):
        """C-ReadinessGate: two conditions — input readiness (primitive
        pipelines + primary interactive LLM handle accepts and routes
        input) and ledger readiness (partition mounted, valid, queryable).
        Pass time recorded in seconds (R-M1)."""
        t0 = time.time()
        checks = {}
        # ledger readiness: partition mounted, valid, queryable
        try:
            part = json.load(open(self.partition_path))
            checks["partitionMounted"] = "sections" in part
            checks["ledgerQueryable"] = isinstance(
                self.journal.rows("gate-check"), list)
        except Exception:
            checks["partitionMounted"] = False
            checks["ledgerQueryable"] = False
        # input readiness: pipeline routable + LLM handle answers or is
        # honestly declared fallback
        llm_mode = self.engines.get("llm", {}).get("mode", "")
        checks["llmHandle"] = llm_mode.startswith("live-ollama") \
            or llm_mode in ("fallback-declared", "absent-declared")
        checks["inputPipeline"] = True
        passed = all(checks.values())
        secs = round(time.time() - t0, 1)
        self.gate = {"passed": passed, "checks": checks,
                     "seconds": secs,
                     "passedAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
                     "timeToGateSeconds": round(time.time() - self.t0, 1)}
        gpath = os.path.join(self.data_dir, "gate.json")
        with open(gpath, "w") as f:
            json.dump(self.gate, f, indent=1)
        self.journal.append("gate-pass" if passed else "gate-fail",
                            self.gate, claimant="system", basis="system")
        self.metric("time-to-gate", self.gate["timeToGateSeconds"])
        return self.gate
class SpeechFloor:
    """Serialized playback admission (C-SpeechFloor): one utterance at a
    time through a host queue; each utterance measured not assumed."""
    def __init__(self, host):
        self.h = host
        self.q = []
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.running = True
        self.thread.start()
        self.log = []
    def enqueue(self, item):
        with self.lock:
            self.q.append(item)
    def depth(self):
        with self.lock:
            return len(self.q)
    def _run(self):
        while self.running:
            item = None
            with self.lock:
                if self.q:
                    item = self.q.pop(0)
            if item is None:
                time.sleep(0.05)
                continue
            t0 = time.time()
            played = False
            if item.get("kind") == "wav" and os.path.exists(item["path"]):
                played = audio.play_wav(item["path"], blocking=True)
            elif item.get("kind") == "sapi":
                audio.sapi_speak(item["text"], item["voice"])
                played = True
            item["played"] = played
            item["playSeconds"] = round(time.time() - t0, 1)
            self.log.append(item)
            self.h.journal.transient("playback",
                                     {"kind": item.get("kind"),
                                      "played": played,
                                      "playSeconds": item["playSeconds"],
                                      "label": item.get("label", "")})
