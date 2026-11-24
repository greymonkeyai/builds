"""Host context — wires the runtime together.
Owns: runtime dirs (incl. the transient boundary — C-TransientBoundary),
the ledger, the component registry, personas, engines, the speech floor,
connectors, the steward, the event bus. Tool handlers receive this ctx.
"""
from __future__ import annotations
import json
import os
import shutil
import threading
from . import (model, ledger as ledger_mod, tools as tools_mod, floor,
               personas as personas_mod, engines as engines_mod,
               speechfloor as speechfloor_mod, connectors, steward as
               steward_mod, compare as compare_mod)
class Bus:
    """Cards/offers fan out to surfaces; replayable through the ledger."""
    def __init__(self, ctx):
        self.ctx = ctx
        self.listeners = []
        self.events = []
    def emit(self, kind: str, payload: dict):
        ev = {"kind": kind, "payload": payload, "at": model.ms()}
        self.events.append(ev)
        self.events = self.events[-400:]
        for fn in list(self.listeners):
            try:
                fn(ev)
            except Exception:
                pass
class Ctx:
    def __init__(self, runtime: str, steward_interval=None):
        self.runtime = runtime
        os.makedirs(runtime, exist_ok=True)
        # C-TransientBoundary: transient artifacts live in a disposable
        # boundary — a leftover boot marker means an incomplete cleanup,
        # so the boundary is reset without touching durable stores.
        self.transient = os.path.join(runtime, "transient")
        marker = os.path.join(self.transient, ".boot-ok")
        if os.path.isdir(self.transient) and not os.path.exists(marker):
            shutil.rmtree(self.transient, ignore_errors=True)
        os.makedirs(self.transient, exist_ok=True)
        self.transient_reset = not os.path.exists(marker)
        open(marker, "w").write("ok")
        self.ledger = ledger_mod.Ledger(os.path.join(runtime, "ledger.jsonl"))
        self.partition_path = os.path.join(runtime, "launch-partition.jsonl")
        self.partition_count = self.ledger.mount_partition(self.partition_path)
        self.journal_count = self.ledger.load()
        self.tools = tools_mod.Registry()
        self.engines = engines_mod.Engines()
        self.bus = Bus(self)
        self.wiki = connectors.Wikipedia()
        self.personas = personas_mod.PersonaStore(self)
        self.floor = speechfloor_mod.SpeechFloor(self)
        self.steward = steward_mod.Steward(
            self, interval=steward_interval or steward_mod.DEFAULT_INTERVAL_S)
        self.gate = None
        self.invocations = 0
        self.exchange_schema = "vantage-exchange/1"
        self.lock = threading.RLock()
        tools_mod.register_all(self)

    def partition_rows_mounted(self) -> int:
        """Rows of the launch-partition file that are actually mounted —
        the gate tests the partition is mounted, not that it added new ids."""
        if not os.path.exists(self.partition_path):
            return 0
        n = 0
        with open(self.partition_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and json.loads(line).get("id") in self.ledger.by_id:
                    n += 1
        return n
    # -- needs / tools ----------------------------------------------------------
    def invoke(self, tool_id, slots, summary="", via="api",
               claimant="principal"):
        tool = self.tools.get(tool_id)
        if not tool:
            return {"ok": False, "error": f"no such tool '{tool_id}'"}
        self.invocations += 1
        return floor.open_need(self, tool, dict(slots or {}),
                               summary or tool_id, via, claimant)
    def retry(self, nid):
        return floor.retry_need(self, nid)
    def open_needs(self):
        return floor.open_needs(self.ledger)
    def compete(self, need_expr, slots, normalize=None):
        return compare_mod.compete(self, need_expr, slots, normalize)
    # -- input routing ------------------------------------------------------------
    def route_input(self, text: str) -> dict:
        """Intent packs classify an input into tool needs + a conversational
        response request. Needs stay distinguishable; creation ≠ execution."""
        from . import builtins
        return builtins.parse_intents(self, text)
    # -- ethics ----------------------------------------------------------------------
    def ethics_gate(self, figure: str) -> dict:
        """Liveness research through the wikipedia connector + objection
        patterns. Verdicts: allowed | mark-required | admonish-required |
        refused. The verdict, the research, and the admonishment are all
        ledger rows (C-EthicsGate machinery under the prompt's mark)."""
        led = self.ledger
        r = self.wiki.summary(figure)
        verdict, reason, admonish = "mark-required", "", None
        lowered = figure.lower()
        refused_patterns = ("hitler", "bin laden")
        if any(p in lowered for p in refused_patterns):
            verdict, reason = "refused", (
                "modeled figure refused under the installation's "
                "objection policy")
        elif r.get("ok"):
            extract = (r.get("extract") or "")
            if re_living(extract):
                verdict = "admonish-required"
                reason = "living or recently deceased person"
                admonish = (
                    f"This personality imitates {figure}: an imitation of a "
                    f"point of view, not the person or their authority. It "
                    f"carries a permanent ◆ IMITATION mark.")
            else:
                verdict = "mark-required"
                reason = "recognizable figure (historical)"
                admonish = (
                    f"This personality imitates {figure} — a depiction, "
                    f"not the figure. Marked ◆ IMITATION.")
        else:
            verdict = "mark-required"
            reason = f"figure not verifiable ({r.get('error','?')}) — " \
                     f"marked conservatively"
            admonish = (f"This personality claims to imitate {figure}; "
                        f"verification failed, so it is marked ◆ IMITATION "
                        f"by default.")
        led.say("ethics", "ethics:gate",
                {"figure": figure, "verdict": verdict, "reason": reason,
                 "researched": bool(r.get("ok"))},
                claimant="system", certainty=1.0,
                basis={"kind": "interpretation"})
        return {"verdict": verdict, "reason": reason,
                "admonishment": admonish}
    # -- engines / connectors -----------------------------------------------------------
    def engine_call(self, name, call, args):
        if name == "llm":
            return self.engines.llm.chat(args.get("system", ""),
                                         args.get("prompt", ""),
                                         max_tokens=args.get("max", 300))
        if name == "tts":
            return self.engines.tts.render_local(
                args.get("text", ""), voice=args.get("voice"),
                rate=args.get("rate", 0))
        if name == "wiki":
            fn = getattr(self.wiki, call, None)
            return fn(**args) if fn else {"ok": False, "error": "bad call"}
        return {"ok": False, "error": f"no engine '{name}'"}
    def run_connector(self, name, **kw):
        if name == "wikipedia":
            return {"ok": True, "note": "wikipedia is queried on demand"}
        if name == "ics-calendar":
            return connectors.import_ics(self, kw.get("ics", ""),
                                         kw.get("source", "ics-file"))
        if name == "files":
            return connectors.ingest_files(self, kw.get(
                "dir", os.path.join(self.root, "fixtures", "docs")))
        if name == "rss":
            return connectors.ingest_rss(self, kw.get("url", ""))
        if name == "inbox-eml":
            return connectors.ingest_inbox(self, kw.get(
                "dir", os.path.join(self.root, "fixtures", "inbox")))
        return {"ok": False, "error": f"unknown connector '{name}'"}
    # -- seeding ---------------------------------------------------------------------------
    def seed_packs(self, packs_dir):
        """Install-time corpus, loaded ONCE under the `seed:` claimant —
        a seed:loaded marker makes re-seeding impossible (J1 discipline:
        no double-seeded rosters)."""
        if self.ledger.query(predicate="seed:loaded", limit=1):
            return {"ok": True, "seeded": False, "note": "already seeded"}
        count = 0
        for fn in sorted(os.listdir(packs_dir)):
            if not fn.endswith(".json"):
                continue
            pack = json.load(open(os.path.join(packs_dir, fn),
                                  encoding="utf-8"))
            for a in pack.get("assertions", []):
                self.ledger.say(a["subject"], a["predicate"], a["value"],
                                claimant="seed:" + pack.get("id", fn),
                                certainty=a.get("certainty", 0.7),
                                basis={"kind": "seed"})
                count += 1
            for p in pack.get("personas", []):
                self.personas.mint(**p)
                count += 1
            for t in pack.get("tools", []):
                self.tools.tool(t["id"], t.get("title", t["id"]),
                                need=t.get("need"), template=t.get("template"),
                                steps=t.get("steps"), authored=True)
                count += 1
        self.ledger.say("seed", "seed:loaded",
                        {"dir": packs_dir, "assertions": count},
                        claimant="system", certainty=1.0,
                        basis={"kind": "seed"})
        return {"ok": True, "seeded": True, "count": count}
    @property
    def root(self):
        # the version dir (parent of this package) — fixtures, seed-packs,
        # evidence all live there regardless of the chosen --runtime dir
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import re as _re
def re_living(extract: str) -> bool:
    """A person is living-or-recently-deceased if the extract lacks a death
    year or shows a death within ten years."""
    m = _re.search(r"\((?:[^)]*?)(\d{4})\s*[-–]\s*(\d{4})?\)", extract)
    if not m:
        return True  # can't verify → treat as living, mark anyway
    death = m.group(2)
    if not death:
        return True
    import datetime as _dt
    return (_dt.datetime.now().year - int(death)) <= 10
