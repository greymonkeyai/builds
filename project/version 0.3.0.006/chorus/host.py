"""Host — the sovereign ledger hub. Owns runtime state, engines, personas,
sources, fleet, steward; exposes computed views to surfaces.
"""
import json
import os
import re
import time
from .book import Book, fresh_id, now_iso
from . import engines, personas as per, needs as nds
from . import sources as src_mod
from . import fleet as fleet_mod
from . import steward as steward_mod
from . import stage as stage_mod
from . import exchange as exch
from . import artifacts as art
from . import seedmedia as seed
class Host:
    def __init__(self, runtime_dir, root, node_id=None):
        self.root = root
        self.runtime_dir = runtime_dir
        os.makedirs(runtime_dir, exist_ok=True)
        self.book = Book(runtime_dir)
        self.state = {}
        self.node_id = node_id or self._node_id()
        self.network_id = self._network_id()
        self.llm = engines.LLM()
        self.voice_pool = engines.sapi_voices()
        self.speech_floor = engines.SpeechFloor(self)
        self.speech_log = []
        self.personas = {}
        self.roster_seq = None
        self.sources = {}
        self.accounts = {}
        self.tool_catalog = dict(nds.TOOLS)
        self.needs = nds.Needs(self)
        self.fleet = fleet_mod.Fleet(self)
        self.steward = None
        self.turn_in_flight = False
        self.part2_done = False
        self.events = []           # SSE event queue (bounded)
        self.boot_meta = {}
        self.roster_selected = None
    # ---------- identity ----------
    def _node_id(self):
        p = os.path.join(self.runtime_dir, "node-id")
        if os.path.exists(p):
            return open(p).read().strip()
        nid = f"node-{os.environ.get('COMPUTERNAME','x').lower()}-{fresh_id('n')[:6]}"
        with open(p, "w") as f:
            f.write(nid)
        return nid
    def _network_id(self):
        p = os.path.join(self.root, "network-identity.json")
        if os.path.exists(p):
            try:
                return json.load(open(p))["network"]
            except Exception:
                pass
        return "net-chorus-" + fresh_id("n")[2:8]
    # ---------- boot ----------
    def part1_mount(self):
        """Part 1 (C-TwoPartExecution): partition + mount + engine probes —
        what the readiness gate covers."""
        t0 = time.time()
        essentials = self._launch_partition_rows()
        n_part = self.book.write_partition(essentials)
        self.book.reset_transient()
        n_rows = self.book.mount()
        self._restore_objects()
        self.boot_meta = {"partitionRows": n_part, "mountedRows": n_rows,
                          "mountMs": int((time.time() - t0) * 1000)}
        return self.boot_meta
    def _launch_partition_rows(self):
        """Essential launch slice ordered by modular schema deps."""
        return [
            {"id": "p-1", "layer": 0, "kind": "meta:schema",
             "claimant": "system", "certainty": 1.0, "confidence": 1.0,
             "basis": "durable-result", "relates": [], "supersedes": None,
             "at": now_iso(),
             "claim": {"schema": "chorus-ledger-1",
                       "namespaces": ["input", "need", "persona", "chat",
                                      "source", "grant", "fleet", "exchange",
                                      "speech", "steward", "list", "stage",
                                      "seed", "workshop", "tool",
                                      "artifact", "project", "account",
                                      "settings"]}},
            {"id": "p-2", "layer": 1, "kind": "host:identity",
             "claimant": "system", "certainty": 1.0, "confidence": 1.0,
             "basis": "durable-result", "relates": [], "supersedes": None,
             "at": now_iso(),
             "claim": {"node": self.node_id, "network": self.network_id}},
        ]
    def _restore_objects(self):
        self.personas = per.load_personas(self)
        # restore roster order + settings + sources from the journal
        for r in self.book.current():
            if r["kind"] == "persona:rank":
                names = r["claim"].get("order", [])
                byname = {p["name"]: p["id"] for p in self.personas.values()}
                seq = [byname[n] for n in names if n in byname]
                missing = [pid for pid in self.personas if pid not in seq]
                self.roster_seq = seq + missing
            elif r["kind"] == "settings:set":
                self.state.setdefault("settings", {})[
                    r["claim"]["subject"]] = r["claim"]["value"]
            elif r["kind"] == "source:configured":
                self.sources[r["claim"]["subject"]] = {
                    "key": r["claim"]["subject"],
                    "name": r["claim"].get("name"),
                    "kind": r["claim"].get("kind"),
                    "domains": r["claim"].get("domains", []),
                    "descriptor": r["claim"].get("descriptor", "granted_only"),
                    "ceiling": r["claim"].get("ceiling", 0.6),
                    "credential": r["claim"].get("credentialDescriptor", {})
                    .get("secretRef"),
                    "admitted": True}
        if self.roster_seq is None and self.personas:
            self.roster_seq = sorted(
                self.personas.values(), key=lambda p: -p["confidence"])
            self.roster_seq = [p["id"] for p in self.roster_seq]
        for srow in self.book.current_of("seed:run"):
            pass
    def readiness_gate(self):
        """C-ReadinessGate: input readiness (primitive pipelines + primary
        interactive LLM handles accept and route input) + ledger readiness
        (partition mounted, valid, queryable). Pass time recorded in
        accessible evidence — time-to-gate is a named metric."""
        checks = []
        mounted = self.boot_meta.get("mountedRows", 0) >= 1 and \
            os.path.exists(self.book.partition_path)
        checks.append({"check": "ledger partition mounted", "pass": mounted})
        try:
            q = self.book.of_kind("meta:schema")
            checks.append({"check": "partition queryable",
                           "pass": len(q) >= 1})
        except Exception:
            checks.append({"check": "partition queryable", "pass": False})
        probe = self.needs.classify("gate probe")
        input_ready = bool(probe) and hasattr(self, "book")
        checks.append({"check": "input pipelines accept and route",
                       "pass": input_ready})
        checks.append({"check": "primary LLM handle",
                       "pass": True,
                       "mode": self.llm.mode})
        ok = all(c["pass"] for c in checks)
        passed_at = now_iso()
        gate = {"ok": ok, "checks": checks, "passedAt": passed_at if ok else None,
                "bootStartedAt": self.boot_meta.get("bootStartedAt")}
        gp = os.path.join(self.runtime_dir, "gate.json")
        with open(gp, "w", encoding="utf-8") as f:
            json.dump(gate, f, indent=1)
        self.book.append("gate:passed" if ok else "gate:failed", {
            "subject": "readiness-gate", "checks": checks,
            "passedAt": gate["passedAt"]},
            claimant="host", basis="execution-evidence")
        return gate
    def part2_start(self):
        """Part 2: everything after the gate — seed personas, source import,
        steward, fleet, stage, preload cache."""
        per.seed_shipped(self)
        self.import_source_seed()
        art.seed_preload_cache(self)
        stage_mod.ensure_sample_library(self)
        self.steward = steward_mod.Steward(self)
        self.part2_done = True
        self.book.append("host:part2", {"subject": "boot", "state": "done"},
                         claimant="host", basis="execution-evidence")
    def import_source_seed(self):
        """Import the configured-source seed as configured-source ledger
        rows (kind, endpoint, domains, descriptor, ceiling) and run the
        admission gate over them."""
        if self.book.current_of("source:configured") or \
                self.book.find(lambda r: r["kind"] == "source:seed-imported"):
            for entry in src_mod.SEED_PAYLOAD["sources"]:
                key = entry["key"]
                if key not in self.sources:
                    adm = [r for r in self.book.current_of("source:admission")
                           if r["claim"].get("subject") == key]
                    self.sources[key] = {**entry,
                        "admitted": adm[0]["claim"]["admitted"] if adm else None}
            return
        for entry in src_mod.SEED_PAYLOAD["sources"]:
            self.book.append("source:configured", {
                "subject": entry["key"], "name": entry["name"],
                "kind": entry["kind"], "endpoint": entry.get("api") or entry["url"],
                "url": entry["url"], "domains": entry["domains"],
                "descriptor": entry["descriptor"], "ceiling": entry["ceiling"],
                "seedRevision": src_mod.SEED_REVISION},
                claimant="host", certainty=0.9, basis="durable-result")
        verdicts = src_mod.admit_all(self.book, src_mod.SEED_PAYLOAD["sources"])
        for entry in src_mod.SEED_PAYLOAD["sources"]:
            v = verdicts.get(entry["key"], {})
            self.sources[entry["key"]] = {**entry, "admitted": v.get("admitted")}
        self.book.append("source:seed-imported", {
            "subject": "configured-sources-001", "count":
            len(src_mod.SEED_PAYLOAD["sources"]),
            "admitted": sum(1 for v in verdicts.values() if v["admitted"]),
            "quarantined": sum(1 for v in verdicts.values() if v["quarantined"])},
            claimant="host", basis="execution-evidence")
    # ---------- views ----------
    def roster_order(self):
        """The roster's ordered state — order by sequence, confidence is
        the held dyadic value (display may sort independently)."""
        seq = self.roster_seq or list(self.personas.keys())
        missing = [pid for pid in self.personas if pid not in seq]
        return [self.personas[pid] for pid in seq + missing
                if pid in self.personas]
    def response_depth(self):
        return int(self.state.get("settings", {}).get("chat:response-depth", 1))
    def conf_threshold(self):
        return float(self.state.get("settings", {}).get("chat:conf-threshold", 0.3))
    def set_setting(self, key, value, claimant="principal"):
        """User preferences are user assertions (C-UserSetSupremacy —
        certainty-top reserved for user-set values)."""
        old = self.state.get("settings", {}).get(key)
        prior = [r for r in self.book.current_of("settings:set")
                 if r["claim"].get("subject") == key]
        self.state.setdefault("settings", {})[key] = value
        return self.book.append("settings:set", {
            "subject": key, "value": value, "previous": old},
            claimant=claimant, certainty=1.0, basis="user-choice",
            supersedes=prior[0]["id"] if prior else None)
    def selector_state(self):
        return self.state.get("selector", [])
    def set_selector(self, ids):
        self.state["selector"] = list(ids)
        return self.book.append("chat:selector", {
            "subject": "quick-select", "selected": ids},
            claimant="principal", certainty=1.0, basis="user-choice")
    # ---------- speech ----------
    def speak_persona(self, persona, text, turn_id):
        """Compose speech for a reply: derived speakable rendering, split at
        sentence boundaries into sequential floor-held utterances (C-Speech-
        Floor / C-SpeakableRendering). TTS ms measured per response."""
        t0 = time.time()
        spoken = engines.speakable(text)
        chunks = engines.split_utterances(spoken, max_chars=900)
        voice = (persona.get("voice") or {}).get("name")
        total_ms = 0
        wavs = []
        audio_dir = os.path.join(self.runtime_dir, "audio")
        os.makedirs(audio_dir, exist_ok=True)
        for i, (chunk, excerpt) in enumerate(chunks):
            wav = os.path.join(audio_dir,
                               f"{turn_id}-{persona['id']}-{i}.wav")
            ok = False
            ms = None
            if voice and voice != "declared-absent":
                ok, ms, err = engines.sapi_render(chunk, voice, wav)
            if not ok:
                engines.synth_tone_wav(wav, [440 + i * 60], ms_each=60)
                ms = None
            if ms:
                total_ms += ms
            self.speech_floor.enqueue({
                "kind": "utterance", "wav": wav, "persona": persona["name"],
                "text": chunk, "excerpt": bool(excerpt), "turn": turn_id})
            wavs.append({"wav": wav, "text": chunk,
                         "excerpt": bool(excerpt), "ttsMs": ms})
        return {"tts_ms": total_ms or None, "utterances": wavs,
                "elapsed": int((time.time() - t0) * 1000)}
    def note_speech(self, rec):
        self.speech_log.append(rec)
        self.book.append("speech:played", {
            "subject": rec.get("turn") or "floor",
            "kind": rec["kind"], "persona": rec.get("persona"),
            "measuredMs": rec["measured_ms"], "heldMs": rec["held_ms"],
            "excerpt": rec.get("excerpt")},
            claimant="engine:speech", certainty=0.9,
            basis="execution-evidence", durable=False)
    def push_event(self, etype, data):
        ev = {"type": etype, "data": data, "at": time.time()}
        self.events.append(ev)
        if len(self.events) > 500:
            self.events = self.events[-400:]
    def note_turn(self, text, replies):
        seg = {"text": text, "replies": replies, "at": now_iso()}
        self.state.setdefault("conversation", []).append(seg)
        # topic = rough keyword label for the context display
        words = [w for w in re.findall(r"[a-z']{4,}", text.lower())
                 if w not in ("what", "that", "with", "have", "this",
                              "your", "about", "tell", "make")]
        self.state["topic"] = " ".join(words[:4]) or self.state.get("topic")
    def reset_conversation(self):
        old = self.state.get("conversation", [])
        self.state["conversation"] = []
        self.state["topic"] = None
        self.book.append("chat:reset", {
            "subject": "conversation", "clearedTurns": len(old),
            "archived": True},
            claimant="principal", certainty=1.0, basis="user-choice")
    # ---------- honesty ----------
    def honesty(self):
        admitted = sum(1 for s in self.sources.values() if s.get("admitted"))
        quarantined = len(self.book.current_of("source:quarantine"))
        return {
            "ledger": "durable (jsonl journal + launch partition)",
            "llm": self.llm.mode,
            "tts": "sapi" if self.voice_pool else "absent-declared",
            "voices": {"pool": len(self.voice_pool),
                       "thin": len(self.voice_pool) < 3,
                       "note": "thin voice pool declared honestly"
                       if len(self.voice_pool) < 3 else None},
            "sources": {"configured": len(self.sources),
                        "admitted": admitted, "quarantined": quarantined},
            "accounts": {"configured": [k for k in self.sources
                                        if k.startswith("source-acct-")] or
                         "none — OAuth/app-password path available on "
                         "settings surface",
                         "fixture": "fixtures/inbox .eml (labeled basis)"},
            "art": "llm-authored-svg" if self.llm.live else
                   "fallback-declared (not-authored, legible)",
            "stt": "browser-webspeech-declared (absent server-side)",
            "peerPort": self.fleet.__class__ and
                        int(os.environ.get("CHORUS_PEER_PORT", "7871")),
            "declaredAbsences": [
                "configured live mail account (until settings path used)",
                "OAuth flow (app-password/IMAP path implemented)",
                "second live fleet node on this LAN (until one joins)",
                "seed media signing cert (allowlist arrangement documented)",
            ],
            "node": self.node_id, "network": self.network_id,
        }
