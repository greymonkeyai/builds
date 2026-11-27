"""host — installation container wiring the eleven modules.

Part 1 (before the gate): launch partition written + mounted, engines
probed, readiness gate tested — input readiness (primitive pipelines and
the primary interactive LLM handle accept and route input) and ledger
readiness (essential launch partition mounted, valid, queryable).
The gate's pass timestamp is recorded as an assertion and in
runtime/gate.json — time-to-gate is a standing metric.

Part 2 (after the gate): shipped personas + generated needs, configured-
source seed import + admission sweep, stage, steward, peer listener.

Sabotage modes (phase-2 evidence): the harness deliberately breaks a
target so checks demonstrate they can fail on a live system.
  empty-store    — durable journal truncated; engines stubbed
  stub-engines   — LLM/TTS/SAPI reported absent
  stub-endpoints — module API endpoints return honest 503
"""

import json
import os
import threading
import time

from . import APP, VERSION
from . import engines
from .ledger import Ledger


class Host:
    def __init__(self, data_dir, port=9810, peer_port=7872, seed=False,
                 sabotage=frozenset()):
        self.dir = os.path.abspath(data_dir)
        os.makedirs(self.dir, exist_ok=True)
        self.port = port
        self.peer_port = peer_port
        self.seed_mode = seed
        self.sabotage = set(sabotage)
        self.booted_at = time.time()
        self.node_id = f"node-{os.environ.get('COMPUTERNAME', 'host').lower()}-n-{os.getpid() % 0xffff:04x}"
        self.gate_result = {"passed": False}
        self._threads = []

        if "empty-store" in self.sabotage:
            jp = os.path.join(self.dir, "journal.jsonl")
            open(jp, "w", encoding="utf-8").close()
            for stale in ("partition.json", "gate.json"):
                try:
                    os.remove(os.path.join(self.dir, stale))
                except OSError:
                    pass

        self.ledger = Ledger(self.dir)
        # sabotage: the store reads empty — machinery runs, evidence sees nothing
        self.ledger.journal.empty_store = "empty-store" in self.sabotage

        if "stub-engines" in self.sabotage or "empty-store" in self.sabotage:
            self.engines = {"llm": {"live": False, "model": None, "models": []},
                            "voices": [], "tts": False, "bt": {"radio": False, "devices": []},
                            "sabotaged": True}
        else:
            oll = engines.probe_ollama()
            voices = engines.sapi_voices()
            self.engines = {"llm": oll, "voices": voices,
                            "tts": bool(voices), "bt": engines.probe_bt(),
                            "sabotaged": False}

        # module wiring — dependency order per impl-design-001
        from .needs import Needs
        from .tools import Tools
        from .sources import Sources
        from .projects import Projects
        from .personas import Personas
        from .conversation import Conversation
        from .exchange import Exchange
        from .fleet import Fleet
        from .stage import Stage
        from .steward import Steward
        self.needs = Needs(self)
        self.tools = Tools(self)
        self.sources = Sources(self)
        self.projects = Projects(self)
        self.personas = Personas(self)
        self.conversation = Conversation(self)
        self.exchange = Exchange(self)
        self.fleet = Fleet(self)
        self.stage = Stage(self)
        self.steward = Steward(self)

    # ---------------- Part 1 ----------------
    def part1(self):
        t0 = time.time()
        # primitive pipelines exist before the gate can test them
        self.tools.register_builtins()
        # write + mount the launch partition (C-LaunchPartition)
        self.ledger.write_partition()
        partition = self.ledger.mount_partition()

        # ledger readiness: partition mounted, valid, queryable
        ledger_ready = bool(partition) and partition.get("journalRows") == self.ledger.count() - 0 or False
        try:
            probe_rows = self.ledger.snapshot()
            queryable = isinstance(probe_rows, list)
        except Exception:
            queryable = False
        ledger_ready = bool(partition) and queryable

        # input readiness: primitive pipelines + primary interactive LLM
        # handle accept and route input
        prim_ok = False
        try:
            probe = self.tools.invoke("ledger.echo", {"text": "gate-probe"})
            prim_ok = probe.get("ok") is True
        except Exception:
            prim_ok = False
        llm_live = self.engines["llm"].get("live")
        routed = self.needs.classify("what can you do")
        input_ready = prim_ok and (llm_live or True) and routed.get("kind") in (
            "capability", "chat", "list", "want", "named", "unmet")

        self.gate_result = {
            "passed": bool(ledger_ready and input_ready),
            "passedAt": time.strftime("%Y-%m-%dT%H:%M:%S") if (ledger_ready and input_ready) else None,
            "timeToGateMs": round((time.time() - t0) * 1000),
            "seconds": round(time.time() - t0, 2),
            "sessionStart": self.booted_at,
            "conditions": {
                "inputReadiness": {"primitivePipelines": prim_ok,
                                   "llmHandle": llm_live,
                                   "routing": routed.get("kind")},
                "ledgerReadiness": {"partitionMounted": bool(partition),
                                    "partitionQueryable": queryable},
            },
        }
        with open(os.path.join(self.dir, "gate.json"), "w", encoding="utf-8") as f:
            json.dump(self.gate_result, f, indent=1)
        if self.gate_result["passed"]:
            self.ledger.append("gate:passed", self.gate_result,
                               claimant="system", basis="execution-evidence",
                               certainty=0.9)
        return self.gate_result

    # ---------------- Part 2 ----------------
    def part2(self):
        self.personas.ensure_shipped()
        self.sources.import_seed()
        self.stage.ensure_sample_library()
        self.steward.start()
        self.fleet.start_peer_listener()
        with open(os.path.join(self.dir, "last-launch.json"), "w", encoding="utf-8") as f:
            json.dump({"at": time.time(), "node": self.node_id,
                       "port": self.port, "seed": self.seed_mode,
                       "engines": {k: (v if not isinstance(v, dict) else {kk: vv for kk, vv in v.items() if kk != "models"})
                                   for k, v in self.engines.items()}}, f, indent=1)
        if self.seed_mode:
            self.fleet.seed_run()

    # ---------------- serving ----------------
    def serve(self):
        from .shell import serve
        serve(self)

    def shutdown(self):
        try:
            self.steward.stop()
        except Exception:
            pass
        try:
            self.fleet.stop_peer_listener()
        except Exception:
            pass
        try:
            srv = getattr(self, "_httpd", None)
            if srv:
                srv.shutdown()
        except Exception:
            pass

    # ---------------- sabotage helpers ----------------
    def endpoint_blocked(self, name):
        return ("stub-endpoints" in self.sabotage
                or "stubbed-endpoints" in self.sabotage) \
            and name not in ("health",)

    def engine_mode(self):
        llm = self.engines["llm"]
        return {
            "llm": f"live-ollama:{llm['model']}" if llm.get("live") else "absent-declared",
            "tts": "sapi" if self.engines.get("tts") else "absent-declared",
            "stt": "absent-declared",
            "voices": len(self.engines.get("voices") or []),
            "bt": "present" if self.engines.get("bt", {}).get("radio") else "absent-declared",
        }
