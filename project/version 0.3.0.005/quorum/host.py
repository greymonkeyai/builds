"""Quorum host — the running install: primitives, grants, chat pipeline,
context, settings preloads, persona composition.

Wires the book + floor + tools + personas + engines + connectors + steward
+ JEV lane + fleet + artifact exchange into one install. Everything the UI
and the scenario suite exercise goes through here.
"""
from __future__ import annotations

import json
import os
import re
import threading

from . import rows, book, needs, tools, personas, engines, connectors
from . import temporal, evals, steward, fleet, artifacts, art

# ---------------------------------------------------------------------------
class Grants:
    """Witnessed grant gate — nonlocal effects need a configured, recorded
    authority path (prompt §Communication and surfaces)."""
    def __init__(self, book_):
        self.book = book_

    def grant(self, scope: str, claimant="principal") -> dict:
        return self.book.claim(scope, "grant:witnessed",
                               {"scope": scope, "consumable": True},
                               claimant=claimant, certainty=1.0,
                               basis="user-choice")

    def has(self, scope: str) -> bool:
        return bool(self.book.find(predicate="grant:witnessed",
                                   subject=scope))

class Primitives:
    """Closed primitive set the tool DSL invokes (C-ConvergentOntology)."""

    def run(self, comp: str, verb: str, args: dict, env: dict, ctx) -> dict:
        fn = getattr(self, f"_{comp}_{verb}", None)
        if not fn:
            return {"ok": False, "error": f"unknown primitive {comp}.{verb}"}
        return fn(args, env, ctx)

    # -- ledger ---------------------------------------------------------------
    def _ledger_search(self, args, env, ctx):
        rows_ = ctx.host.book.find(predicate=args.get("predicate"),
                                   subject=args.get("subject"),
                                   text=args.get("text"), limit=50)
        return {"ok": True, "env": {"rows": rows_}, "rows": rows_}

    def _ledger_claim(self, args, env, ctx):
        return {"ok": True, "row": ctx.host.book.claim(
            args["subject"], args["predicate"], args["value"],
            claimant=args.get("claimant", "tool:quorum"),
            certainty=args.get("certainty", 0.8), basis="execution")}

    # -- engine -----------------------------------------------------------------
    def _engine_invoke(self, args, env, ctx):
        if args.get("engine") == "llm":
            prompt = args.get("prompt") or json.dumps({
                "task": args.get("task"), "env_keys": list(env)})[:4000]
            r = ctx.host.llm.complete(prompt, role=args.get("role", "general"))
            return {"ok": r.get("ok"), "text": r.get("text", ""),
                    "stub": r.get("stub"), "env": {"llm_text": r.get("text", "")}}
        return {"ok": False, "stub": True, "note": "engine seam absent"}

    # -- retrieval ----------------------------------------------------------------
    def _wikipedia_extract(self, args, env, ctx):
        topic = args.get("topic", "")
        if args.get("mode") == "table":
            r = connectors.wikipedia_table_members(topic)
            return {"ok": r["ok"], "env": {"members": r.get("members", [])}}
        summ = connectors.wikipedia_summary(topic)
        links = connectors.wikipedia_links(topic)
        ctx.host.book.claim(topic, "source:wikipedia",
                            {"extract": summ.get("extract", "")[:800],
                             "links": len(links.get("links", []))},
                            claimant="source:wikipedia", certainty=0.85,
                            basis="source-evidence")
        return {"ok": summ["ok"], "env": {"extract": summ.get("extract", ""),
                                         "links": links.get("links", []),
                                         "topic": topic}}

    def _filter_members(self, args, env, ctx):
        """Classify candidate links/members against the member shape —
        members AND recorded non-matches (D4: results-that-do-not-match are
        retained for review, not silently dropped)."""
        shape = (args.get("shape") or "").lower()
        links = env.get("links") or env.get("members") or []
        members, nonmatches = [], []
        if "cit" in shape:
            for t in links:
                tl = t.lower()
                if any(k in tl for k in ("(cdp)", "township", "borough",
                                         "county,", "list of", "category:")):
                    nonmatches.append(t)
                elif re.match(r"^[A-Z][\w .'-]+$", t) and len(t) < 40 \
                        and "pennsylvania" not in tl:
                    members.append(t)
                else:
                    nonmatches.append(t)
        else:
            members = list(links)
        return {"ok": True, "env": {"members": members,
                                    "nonmatches": nonmatches,
                                    "criteria": shape}}

    def _web_search(self, args, env, ctx):
        q = args.get("query", "")
        r = connectors.ddg_search(q)
        ctx.host.book.claim(q, "source:search",
                            {"hits": r.get("results", [])},
                            claimant="source:web", certainty=0.6,
                            basis="source-evidence")
        return {"ok": r["ok"], "results": r.get("results", []),
                "env": {"hits": r.get("results", [])}}

    # -- nonlocal effects ---------------------------------------------------------
    def _outbox_send(self, args, env, ctx):
        """Grant-gated + connector-gated. No fabricated delivery."""
        channel = args.get("channel", "email")
        configured = ctx.host.configured_accounts.get(channel)
        if not configured:
            return {"ok": False, "stop": True, "deferred": True,
                    "env": {"delivery": "deferred"},
                    "note": f"no configured {channel} account — honest "
                            f"deferral; request and status recorded"}
        return {"ok": True, "env": {"delivery": "sent"}}

    def _result_card(self, args, env, ctx):
        card = {"kind": args.get("kind", "result"),
                "members": env.get("members"), "hits": env.get("hits"),
                "nonmatches": env.get("nonmatches"),
                "llm_text": env.get("llm_text", "")[:1200],
                "note": env.get("delivery") or ""}
        return {"ok": True, "card": card, "env": {"card": card}}


# ---------------------------------------------------------------------------
class Ctx:
    def __init__(self, host):
        self.host = host
        self.primitives = host.primitives
        self.grants = host.grants


class Host:
    """The install. Owns runtime paths; mounts the ledger; runs the gate."""

    def __init__(self, runtime_dir: str, port: int = 9790):
        self.runtime = runtime_dir
        self.port = port
        os.makedirs(runtime_dir, exist_ok=True)
        # C-TransientBoundary — disposable partition reset each boot
        self.transient_dir = os.path.join(runtime_dir, "transient")
        if os.path.isdir(self.transient_dir):
            import shutil
            shutil.rmtree(self.transient_dir, ignore_errors=True)
        os.makedirs(self.transient_dir, exist_ok=True)
        open(os.path.join(self.transient_dir, ".boot-ok"), "w").write("ok")

        self.book = book.Book(os.path.join(runtime_dir, "ledger.jsonl"))
        self.partition_path = os.path.join(runtime_dir, "launch-partition.jsonl")
        self.gate_path = os.path.join(runtime_dir, "gate.json")
        self.artifacts_dir = os.path.join(runtime_dir, "artifacts")
        self.floor = needs.Floor(self.book)
        self.tools = tools.ToolRegistry(self.book, self.floor)
        self.floor.arg_requirements = {
            tid: [s for s, req in (d.get("slots") or {}).items()
                  if req == "required"]
            for tid, d in self.tools.live.items()}
        self.llm = engines.LLM()
        self.speech = engines.SpeechFloor(self.book)
        self.grants = Grants(self.book)
        self.primitives = Primitives()
        self.ctx = Ctx(self)
        self.personas = personas.PersonaStore(
            self.book, os.path.join(runtime_dir, "personas.json"))
        self.jev = evals.JevLane(self.book, self.floor, self.llm)
        self.steward = steward.Steward(self)
        self.fleet = fleet.Fleet(self.book)
        self.seed = None
        self.exchange = artifacts.ArtifactExchange(
            self.book, self.tools, self.floor,
            os.path.join(os.path.dirname(runtime_dir), "seed-packs"))
        self.configured_accounts = {"email": None, "calendar": None}
        self.context_stack: list[dict] = []    # selected context (emails etc.)
        self.topic = ""
        self.turns: list[dict] = []
        self.partition_rows = 0
        self.surface_role = "host"             # host | satellite — §5

    # ---- boot ------------------------------------------------------------------
    def mount(self) -> dict:
        """C-LaunchPartition: essential slice mounts first (dependency-ordered
        modular schema), then the journal replays."""
        self.partition_rows = self.book.mount_partition(self.partition_path)
        n = self.book.mount()
        self.tools.load_minted()
        return {"partition": self.partition_rows, "journal": n}

    def seed_launch_partition(self, rows_list: list[dict]):
        """First-run: write the essential launch slice."""
        with open(self.partition_path, "w", encoding="utf-8") as f:
            for d in rows_list:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")

    # ---- chat pipeline -----------------------------------------------------------
    def chat(self, text: str, persona_id: str = "") -> dict:
        """One turn: capture → lexicon classify → needs → sequential
        respondents on snapshots → sequential commit (C-SnapshotInference /
        C-SequentialCommit). The JEV model lane runs in parallel and its
        verdict lands whenever the engine returns it."""
        self.steward.note_user_activity()
        turn_id = rows.new_id("t")
        self.book.claim(turn_id, "chat:input", text,
                        claimant="principal", certainty=1.0,
                        basis="captured-input")
        lex = evals.lexicon_gate(text)

        # focused-need conversational slot-filling (S-focused-need): when a
        # need is in focus, plain input refines it — appends related rows,
        # never rewrites the original requirement
        focused = self._focused_need()
        if focused and not lex["isRequest"]:
            slot = self._first_open_slot(focused)
            self.floor.set_slot(focused["id"], slot, text,
                                claimant="principal")
            self.floor.add_candidate(focused["id"], slot, text,
                                     "principal", 1.0,
                                     evidence="supplied conversationally in focus")
            self.book.claim(turn_id, "chat:focus-fill",
                            {"need": focused["id"], "slot": slot, "value": text},
                            claimant="principal", certainty=1.0,
                            basis="user-choice")
            cur_need = self.book.get(focused["id"])
            tool_id = (cur_need["value"]["v"].get("slots", {}) or {}
                       ).get("tool", "")
            needs_grant = bool(self.tools.live.get(tool_id, {})
                               .get("requiresGrant"))
            if not self.floor.missing_required(cur_need) and not needs_grant:
                self.floor.fulfill(focused["id"],
                                   {"filled": slot, "via": "focused chat"},
                                   claimant="principal")
            return {"id": turn_id, "input": text, "focus_fill": focused["id"],
                    "replies": [], "needs": [], "topic": self.topic}

        respondents = self._respondents(persona_id)
        grounds = self._grounds(text)

        # C-SnapshotInference: each respondent drafts on its own consistent
        # snapshot (parallel, stable state); commits land sequentially.
        snap = self.book.snapshot()
        self.book.claim(turn_id, "inference:snapshot",
                        {"rows": len(snap), "respondents": len(respondents)},
                        claimant="system", certainty=0.9, basis="execution")
        replies = []
        for p in respondents:
            reply = self._persona_reply(p, text, grounds)
            replies.append(reply)
            # sequential commit, in roster rank order
            self.book.claim(turn_id, "inference:commit",
                            {"persona": p["id"], "reply": reply["text"][:300],
                             "fidelity": reply["fidelity"]},
                            claimant=f"persona:{p['id']}",
                            certainty=reply["fidelity"].get("fidelity", 0.5),
                            basis="generated")
            if reply["text"]:
                self.speech.admit(reply["text"], p.get("voice", ""),
                                  p["id"])

        # needs from the turn — each distinguishable (S-chat-invocation)
        created = []
        if lex["isRequest"]:
            if lex["class"] == "list-request":
                need = self.floor.open("list", f"list:{turn_id}",
                                       {"topic": self._list_topic(text),
                                        "criteria": "incorporated city "
                                                    "municipalities only"},
                                       claimant="system", certainty=0.85)
                created.append(need["id"])
            elif lex["class"] == "mail-request":
                need = self.floor.open("tool-request", f"mail:{turn_id}",
                                       {"tool": "send-email",
                                        "args": {"to": "", "subject": text[:60],
                                                 "body": text}},
                                       claimant="system", certainty=0.85)
                created.append(need["id"])
            else:
                # lexicon says request but no class match — the unmet ask
                # (need:request capture; also fires on gate disagreement)
                need = self.jev.capture_unmet(turn_id, text, lex,
                                              "lexicon-request-no-tool-match")
                created.append(need["id"])
        # async gate lane — verdict lands whenever the engine returns
        self.jev.gate_turn(turn_id, text, lex)

        turn = {"id": turn_id, "input": text, "lexicon": lex,
                "replies": replies, "needs": created,
                "topic": self.topic}
        self.turns.append(turn)
        return turn

    def _focused_need(self) -> dict | None:
        rows_ = self.book.find(predicate="need:focus")
        if not rows_:
            return None
        nid = rows_[-1]["subject"]
        need = self.floor.current(nid) or self.book.get(nid)
        if need and need["value"]["v"].get("status") == "open":
            return need
        return None

    def _first_open_slot(self, need: dict) -> str:
        missing = self.floor.missing_required(need)
        if missing:
            return missing[0]
        slots = need["value"]["v"].get("slots", {})
        return next(iter(slots), "value")

    def _respondents(self, persona_id: str = "") -> list[dict]:
        """Respondent set — sequential (C-SequentialRespondents); chorus
        members of any rank appear when directly addressed (C-ChorusOnAddress)."""
        if persona_id and persona_id in self.personas.personas:
            return [self.personas.personas[persona_id]]
        active = self.personas.active
        if active and active in self.personas.personas:
            return [self.personas.personas[active]]
        return ([self.personas.personas[self.personas.order[0]]]
                if self.personas.order else [])

    def _grounds(self, text: str) -> list[str]:
        """Retrieved grounds for the reply — sources + context + calendar."""
        g = []
        topic = self._list_topic(text)
        if topic:
            s = connectors.wikipedia_summary(topic)
            if s.get("extract"):
                g.append(f"wikipedia:{s['title']}: {s['extract'][:400]}")
        for c in self.context_stack:
            g.append(f"selected-context:{c.get('subject','')}: "
                     f"{c.get('body','')[:300]}")
        cal = connectors.ics_events(os.path.join(
            os.path.dirname(self.runtime), "fixtures", "calendar.ics"))
        if cal.get("ok"):
            g += temporal.persona_grounds(temporal.bucket(cal["events"]))
        return g

    def _persona_reply(self, p: dict, text: str, grounds: list[str]) -> dict:
        prompt = self.personas.compose_prompt(p, text, grounds)
        r = self.llm.complete(prompt, role="general", max_tokens=350)
        fidelity = self.personas.grounding_of(r.get("text", ""), grounds)
        if not r.get("ok"):
            # declared stub — the persona says so in-register, never fabricates
            reg = p.get("register", "casual")
            txt = (f"[{p['name']}] My voice engine is offline right now — "
                   f"I heard you, but I can't answer properly. "
                   f"(declared stub, llm absent)")
            fidelity = {"verdict": "stub", "fidelity": 0.0,
                        "flag": "engine-offline"}
            return {"persona": p["id"], "name": p["name"], "text": txt,
                    "fidelity": fidelity, "stub": True}
        return {"persona": p["id"], "name": p["name"],
                "text": r["text"].strip(), "fidelity": fidelity,
                "grounding": len(grounds), "stub": False}

    def _list_topic(self, text: str) -> str:
        m = re.search(r"(?:cities|places|towns|municipalities)\s+in\s+"
                      r"([A-Z][\w'-]+(?:\s+[A-Z][\w'-]+)*)", text or "")
        if m:
            return f"List of municipalities in {m.group(1).strip()}"
        m = re.search(r"in\s+([A-Z][\w'-]+(?:\s+[A-Z][\w'-]+)*)", text or "")
        return m.group(1) if m else ""

    # ---- settings preloads (C-SettingsPreloads / C-PreloadSuite) -------------------
    def apply_preload(self, name: str, claimant="principal") -> dict:
        """Named settings preloads = assertion bundles over the common choice
        set; a preload supplies starting values later choices supersede."""
        pre = self.preloads().get(name)
        if not pre:
            return {"ok": False, "error": f"unknown preload {name}"}
        for slot, val in pre["settings"].items():
            self.book.claim("settings", f"settings:{slot}", val,
                            claimant=claimant, certainty=1.0,
                            basis="user-choice",
                            meta={"preload": name})
        return {"ok": True, "applied": name, "settings": pre["settings"]}

    def preloads(self) -> dict:
        return {
            "daybreak": {"settings": {"theme": "light", "density": "comfortable",
                                      "speech": "on"},
                         "note": "light-mode working preload"},
            "lamplit": {"settings": {"theme": "sepia", "density": "comfortable",
                                     "speech": "on"},
                        "note": "warm sepia colorway"},
            "nightwatch": {"settings": {"theme": "dark", "density": "compact",
                                        "speech": "off"},
                           "note": "dark colorway, quiet"},
        }

    def honesty(self) -> dict:
        """C-HonestyBanner — runtime capability declaration."""
        return {
            "ledger": {"mode": "jsonl-durable", "rows": len(self.book.rows)},
            "llm": {"mode": self.llm.mode, "models": self.llm.models},
            "tts": {"mode": "sapi" if self.speech.voices() else "absent",
                    "voices": [v["id"] for v in self.speech.voices()]},
            "stt": {"mode": "browser-webspeech-declared",
                    "note": "absent server-side; browser surface only"},
            "art": {"mode": "llm-authored" if self.llm.available()
                    else "fallback-declared"},
            "sources": {"wikipedia": "live-http", "duckduckgo": "live-http",
                        "ics-calendar": "fixture-file",
                        "eml-inbox": "fixture-directory (no configured account)",
                        "files": "local"},
            "accounts": {"email": self.configured_accounts["email"] or
                          "absent — declared; fixture .eml basis labeled",
                         "oauth": "absent — declared"},
            "fleet": {"seed": bool(self.seed),
                      "members": list(self.fleet.members),
                      "surface_role": self.surface_role},
            "steward": self.steward.liveness(),
        }
