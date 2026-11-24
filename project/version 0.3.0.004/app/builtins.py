"""Builtin components — tools, commands, and the chat-turn chain.
Registration happens once at boot into ctx.tools. Handlers receive
(ctx, slots, need_id) and return a result dict; needs machinery wraps every
invoke in an unmet requirement first.
"""
from __future__ import annotations
import json
import os
import re
import threading
from . import (model, floor, archive, temporal, setbuild, personas as
               personas_mod, compare as compare_mod, dsl)
# ---------------------------------------------------------------------------
# chat-turn helpers
def _facts_for_text(ctx, text: str, limit=3) -> list:
    """Retrieve source facts for a factual prompt: wikipedia search → summary
    extracts. Facts are verbatim source material with their source recorded —
    the persona may use ONLY these (G-B)."""
    q = re.sub(r"[?!.]+$", "", text)
    q = re.sub(r"^(what|who|where|when|which|why|how|is|are|does|did|"
               r"tell me|describe|explain)\s+(is|are|was|were|a|an|the|"
               r"about|me about|me)?\s*", "", q, flags=re.I).strip()
    if len(q) < 3:
        return []
    s = ctx.wiki.search(q, limit=3)
    if not s.get("ok"):
        s = ctx.wiki.search(q, limit=3)  # one retry before declaring absent
    facts = []
    ctx.ledger.say("search", "retrieval:attempt",
                   {"query": q, "for": text[:120], "ok": bool(s.get("ok")),
                    "titles": (s.get("titles") or [])[:3]},
                   claimant="source:wikipedia", certainty=0.9,
                   basis={"kind": "source-evidence"})
    if not s.get("ok"):
        return facts
    for title in s.get("titles", [])[:2]:
        r = ctx.wiki.summary(title)
        if r.get("ok") and r.get("extract"):
            facts.append({"text": r["extract"][:600],
                          "source": f"wikipedia:{r['title']}"})
            ctx.ledger.say("facts", "source:used",
                           {"title": r["title"], "for": text[:120],
                            "excerpt": r["extract"][:240]},
                           claimant="source:wikipedia", certainty=0.85,
                           basis={"kind": "source-evidence"})
        if len(facts) >= limit:
            break
    return facts
def _decision_weights(led):
    a = led.resolve("config", "decision:weights")
    if a:
        v = a.value.get("v")
        if isinstance(v, list) and len(v) == 5:
            return v
    return [0.35, 0.40, 0.25, 1.0, 0.10]  # active, heldConf, overlap, named, rank
def select_respondents(ctx, text: str, depth: int, address: str = None) -> list:
    """Bounded decision model (fixed feature vector, weighted sum). The
    active persona, held-confidence (dyadic rows), lens-interest overlap with
    the topic/text, direct address (C-ChorusOnAddress — a named persona
    answers regardless of rank), and roster position all factor in. Every
    score is a ledger row — routing is inspectable."""
    led = ctx.ledger
    w = _decision_weights(led)
    roster = ctx.personas.roster()
    topic = archive.topic(led).lower()
    scores = []
    for i, p in enumerate(roster):
        named = 1.0 if (address and p["id"] == address) or \
            re.search(rf"\b{re.escape(p['name'])}\b", text, re.I) else 0.0
        overlap = 0.0
        toks = set(re.findall(r"[a-z]{4,}", (topic + " " + text).lower()))
        inter = set(x.lower() for x in p.get("interests", []))
        if toks and inter:
            overlap = len(toks & inter) / len(inter)
        held = ctx.personas.held_confidence(p["id"])
        active = 1.0 if ctx.personas.data.get("active") == p["id"] else 0.0
        rankn = 1.0 - (i / max(1, len(roster) - 1)) if len(roster) > 1 else 1.0
        f = [active, held, min(1.0, overlap), named, rankn]
        score = sum(a * b for a, b in zip(w, f))
        scores.append({"persona": p["id"], "name": p["name"], "score":
                       round(score, 3), "features": [round(x, 3) for x in f]})
        led.say("decision", "decision:score",
                {"persona": p["id"], "features": f, "weights": w,
                 "score": round(score, 4)},
                claimant="model:respondent-selector", certainty=0.9,
                basis={"kind": "interpretation"})
    scores.sort(key=lambda s: s["score"], reverse=True)
    chosen = scores[:max(1, depth)]
    for rank, s in enumerate(chosen):
        led.say("decision", "decision:respondent",
                {"rank": rank, "persona": s["persona"], "name": s["name"],
                 "score": s["score"]},
                claimant="model:respondent-selector", certainty=0.9,
                basis={"kind": "interpretation"})
    return chosen
def serve_response(ctx, text: str, respondents: list, facts: list,
                   history: str, need_id: str = None,
                   expect_facts: bool = False) -> list:
    """C-SnapshotInference + C-SequentialCommit:
    1. each respondent drafts IN PARALLEL against its own consistent ledger
       snapshot (never each other's uncommitted work)
    2. verified drafts commit back in ranked order
    3. later respondents may append a short reaction reading the committed
       earlier contribution (C-SequentialRespondents) — the reaction commits
       after it, still in order.
    Replies are emitted as persona.speak cards and admitted to the speech
    floor in commit order."""
    led = ctx.ledger
    snap_ids = []
    drafts = {}
    def draft(p):
        snap = led.snapshot()
        sid = model.rid("snap")
        snap_ids.append(sid)
        led.say("inference", "inference:snapshot",
                {"snapshot": sid, "task": p["name"], "rows": len(snap.rows)},
                claimant="model:inference", certainty=1.0,
                basis={"kind": "interpretation"})
        persona = ctx.personas.get(p["persona"])
        history_view = history  # snapshot-consistent (pre-turn reads only)
        drafts[p["persona"]] = personas_mod.compose(
            ctx, persona, text, facts=facts, history=history_view,
            expect_facts=expect_facts)
    threads = [threading.Thread(target=draft, args=(p,)) for p in respondents]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=150)
    replies = []
    committed_texts = []
    for rank, p in enumerate(respondents):
        persona = ctx.personas.get(p["persona"])
        d = drafts.get(p["persona"]) or {
            "ok": True, "text": "…", "register": persona.get("register"),
            "engine": "none"}
        led.say("inference", "inference:commit",
                {"rank": rank, "persona": p["persona"], "name": p["name"],
                 "engine": d.get("engine"),
                 "fidelity": d.get("fidelity")},
                claimant="model:inference", certainty=1.0,
                basis={"kind": "execution"})
        reply = {"persona": p["persona"], "name": persona["name"],
                 "register": d.get("register"), "text": d.get("text"),
                 "engine": d.get("engine"), "rank": rank,
                 "fidelity": d.get("fidelity")}
        led.say(f"persona:{p['persona']}", "persona:reply",
                {"text": d.get("text"), "register": d.get("register"),
                 "prompt": text[:200], "engine": d.get("engine"),
                 "fidelity": d.get("fidelity")},
                claimant="persona:" + persona["name"].lower(),
                certainty=0.9, basis={"kind": "generated"})
        ctx.bus.emit("persona.speak", reply)
        ctx.floor.admit(persona["name"], d.get("text") or "",
                        voice=(persona.get("voice") or {}).get("name"),
                        rate=(persona.get("voice") or {}).get("rate", 0),
                        render=ctx.engines.tts.mode == "sapi")
        committed_texts.append((persona, d.get("text") or ""))
        replies.append(reply)
    # sequential reaction pass — later respondents react to committed work
    for rank in range(1, len(respondents)):
        p = respondents[rank]
        persona = ctx.personas.get(p["persona"])
        earlier = committed_texts[rank - 1]
        d = personas_mod.compose(ctx, persona, text, facts=[],
                                 react_to=f"{earlier[0]['name']}: "
                                          f"{earlier[1][:120]}")
        if d.get("text"):
            led.say("inference", "inference:commit",
                    {"rank": rank, "persona": p["persona"],
                     "kind": "reaction", "reactsTo": earlier[0]["name"]},
                    claimant="model:inference", certainty=1.0,
                    basis={"kind": "execution"})
            reply = {"persona": p["persona"], "name": persona["name"],
                     "register": d.get("register"), "text": d.get("text"),
                     "engine": d.get("engine"), "rank": rank,
                     "reaction": True}
            ctx.bus.emit("persona.speak", reply)
            ctx.floor.admit(persona["name"], d.get("text") or "",
                            voice=(persona.get("voice") or {}).get("name"),
                            rate=(persona.get("voice") or {}).get("rate", 0),
                            render=ctx.engines.tts.mode == "sapi")
            replies.append(reply)
    return replies
# ---------------------------------------------------------------------------
# intent packs — chat input → tool needs + response need
def parse_intents(ctx, text: str) -> dict:
    intents = []
    t = text.strip()
    low = t.lower()
    pats = [
        ("set-topic", r"(?:set|change) (?:the )?topic to (.+)",
         lambda m: {"topic": m.group(1).strip()}),
        ("chat-reset", r"^reset (?:the )?conversation$", lambda m: {}),
        ("build-list", r"list (?:me )?(all (?:the )?.+)",
         lambda m: {"criteria": m.group(1).strip()}),
        ("create-project",
         r"(?:create|start|open) (?:a )?project (?:called |titled |to )?(.+)",
         lambda m: {"title": m.group(1).strip()}),
        ("persona-mint",
         r"(?:create|mint|make) (?:a )?(?:persona|personality|avatar)"
         r"(?: named | called )?(\w[\w\-]*)",
         lambda m: {"name": m.group(1)}),
        ("run-search",
         r"(?:search|look up|find out about|research) (?:for )?(.+)",
         lambda m: {"query": m.group(1).strip()}),
        ("remember", r"remember (?:that )?(.+)",
         lambda m: {"fact": m.group(1).strip()}),
        ("publish-milestone", r"(?:publish|post) (.+)",
         lambda m: {"target": "milestone", "content": m.group(1).strip()}),
        ("send-mail",
         r"(?:send )?(?:an )?email to (.+?)(?: saying |: | that )(.+)",
         lambda m: {"to": m.group(1).strip(), "body": m.group(2).strip()}),
    ]
    for tid, rx, slots_fn in pats:
        m = re.search(rx, low if tid != "persona-mint" else t, re.I)
        if m:
            intents.append({"toolId": tid, "slots": slots_fn(m)})
    if re.search(r"\?\s*$", t) or re.match(
            r"^(what|who|where|when|which|why|how|tell me about|"
            r"describe|explain)\b", low):
        if not any(i["toolId"] == "run-search" for i in intents):
            intents.append({"toolId": "run-search",
                            "slots": {"query": re.sub(r"[?!.]+$", "", t)}})
        intents.append({"kind": "factual"})
    return {"routed": True, "intents": intents}
def run_chat_turn(ctx, text: str, address=None, via="chat") -> dict:
    led = ctx.ledger
    inp = led.say("chat", "chat:input", {"text": text, "via": via},
                  claimant="principal" if via == "chat" else "surface:" + via,
                  certainty=1.0, basis={"kind": "captured-input"})
    # focused need: conversational slot fill (S-focused-need)
    fnid = floor.focused_need(led)
    focus_fill = None
    if fnid and not re.search(r"(?:set the topic|reset conversation)", text,
                              re.I):
        rows = floor.need_rows(led, fnid)
        opener = next((r for r in rows if r.predicate == "need:open"), None)
        spec = (opener.value.get("v") or {}) if opener else {}
        missing = spec.get("missing") or []
        if missing:
            slot = missing[0]
            val = text.strip()
            try:
                val = int(val)
            except ValueError:
                pass
            supply = floor.supply_candidate(ctx, fnid, slot, val,
                                            source="user")
            r = ctx.retry(fnid)
            focus_fill = {"needId": fnid, "slot": slot, "value": val,
                          "test": supply.get("test"),
                          "fulfilled": bool(r.get("ok"))}
    intents = parse_intents(ctx, text)["intents"]
    need_ids, results = [], []
    for it in intents:
        if it.get("kind") == "factual":
            continue
        r = ctx.invoke(it["toolId"], it["slots"],
                       summary=f"chat:{it['toolId']}", via="chat")
        need_ids.append(r.get("needId"))
        results.append({"toolId": it["toolId"], "ok": r.get("ok"),
                        "deferred": r.get("deferred"),
                        "needId": r.get("needId")})
        if r.get("deferred"):
            continue  # needs stay open — the floor records them
    # facts: for factual prompts AND for selected-context commentary
    factual = any(i.get("kind") == "factual" for i in intents)
    facts = _facts_for_text(ctx, text) if factual else []
    ctxsel = archive.context(led)
    if ctxsel and ctxsel.get("excerpt"):
        facts = [{"text": ctxsel["excerpt"],
                  "source": f"context:{ctxsel.get('kind')}:{ctxsel.get('ref')}"}]
    depth = 2
    a = led.resolve("config", "chat:response-depth")
    if a:
        try:
            depth = int(a.value.get("v"))
        except (TypeError, ValueError):
            pass
    resp_need = led.say("chat", "need:response",
                        {"text": text[:200], "depth": depth,
                         "factual": factual},
                        claimant="system", certainty=1.0,
                        basis={"kind": "interpretation"})
    respondents = select_respondents(ctx, text, depth, address)
    history = _history(led)
    replies = serve_response(ctx, text, respondents, facts, history,
                             need_id=resp_need.id, expect_facts=factual)
    led.say("chat", "need:fulfilled",
            {"needId": resp_need.id, "respondents": [r["name"] for r in
             replies]}, claimant="system", certainty=1.0,
            basis={"kind": "durable-result"}, links=[resp_need.id])
    archive.archive_turn(ctx, {"input": text, "intents": intents,
                               "needIds": need_ids,
                               "respondents": [r["name"] for r in replies],
                               "focusFill": focus_fill})
    return {"ok": True, "inputId": inp.id, "intents": intents,
            "needIds": need_ids, "toolResults": results,
            "responseNeedId": resp_need.id, "replies": replies,
            "focusFill": focus_fill}
def _history(led, limit=8):
    rows = led.query(predicate="archive:turn", limit=limit)
    lines = []
    for a in reversed(rows):
        v = a.value.get("v") or {}
        lines.append(f"user: {v.get('input','')[:100]}")
    return "\n".join(lines[-limit:])
# ---------------------------------------------------------------------------
# tool handlers
def h_set_topic(ctx, slots, nid):
    return archive.set_topic(ctx, slots["topic"])
def h_chat_reset(ctx, slots, nid):
    return archive.reset(ctx)
def h_remember(ctx, slots, nid):
    ctx.ledger.say("memory", "memory:fact", {"fact": slots["fact"]},
                   claimant="principal", certainty=0.95,
                   basis={"kind": "user-choice"})
    return {"ok": True, "remembered": slots["fact"]}
def h_create_project(ctx, slots, nid):
    title = slots["title"]
    goals = slots.get("goals") or []
    pid = model.rid("proj")
    ctx.ledger.say(f"project:{pid}", "project:profile",
                   {"title": title, "goals": goals, "status": "open"},
                   claimant="principal", certainty=1.0,
                   basis={"kind": "user-choice"})
    goal_needs = []
    for g in goals:
        pseudo = {"id": "project-goal-work", "kind": "generic",
                  "template": {"slots": [
                      {"name": "deliverable", "required": True},
                      {"name": "format", "required": True,
                       "test": {"kind": "enum",
                                "options": ["report", "summary", "list",
                                            "hardcover", "pdf", "table"]}}]},
                  "handler": h_project_goal}
        r = floor.open_need(ctx, pseudo, {"deliverable": g},
                            summary=f"goal:{g}", via="project")
        goal_needs.append(r.get("needId"))
    ctx.ledger.say(f"project:{pid}", "project:needs",
                   {"needIds": goal_needs, "goals": goals},
                   claimant="system", certainty=1.0,
                   basis={"kind": "interpretation"})
    return {"ok": True, "projectId": pid, "title": title,
            "goalNeeds": goal_needs}
def h_project_goal(ctx, slots, nid):
    ctx.ledger.say("project", "project:deliverable",
                   {"goal": slots.get("deliverable"),
                    "format": slots.get("format"), "needId": nid},
                   claimant="system", certainty=1.0,
                   basis={"kind": "durable-result"})
    return {"ok": True, "delivered": slots.get("deliverable"),
            "format": slots.get("format")}
def h_build_list(ctx, slots, nid):
    criteria = slots["criteria"]
    pid = model.rid("proj")
    ctx.ledger.say(f"project:{pid}", "project:profile",
                   {"title": f"list: {criteria}", "kind": "list-project",
                    "status": "running"},
                   claimant="system", certainty=1.0,
                   basis={"kind": "interpretation"})
    r = setbuild.build(ctx, criteria, need_id=nid)
    status = "done" if r.get("ok") else "failed"
    ctx.ledger.say(f"project:{pid}", "project:status",
                   {"status": status, "memberCount": r.get("memberCount")},
                   claimant="system", certainty=1.0,
                   basis={"kind": "durable-result"})
    r["projectId"] = pid
    return r
def h_retrieve_table(ctx, slots, nid):
    return setbuild.via_table(ctx, slots.get("criteria", ""))
def h_retrieve_category(ctx, slots, nid):
    return setbuild.via_category(ctx, slots.get("criteria", ""))
def h_run_search(ctx, slots, nid):
    q = slots["query"]
    s = ctx.wiki.search(q, limit=5)
    if not s.get("ok"):
        ctx.ledger.say("search", "search:adequacy",
                       {"query": q, "adequate": False,
                        "reason": s.get("error")},
                       claimant="source:wikipedia", certainty=0.9,
                       basis={"kind": "source-evidence"})
        return {"ok": False, "error": s.get("error")}
    hits = []
    for title in s.get("titles", [])[:4]:
        r = ctx.wiki.summary(title)
        if r.get("ok") and r.get("extract"):
            hits.append({"title": r["title"],
                         "extract": r["extract"][:400],
                         "url": r.get("url")})
    ctx.ledger.say("search", "search:adequacy",
                   {"query": q, "adequate": bool(hits), "hits": len(hits)},
                   claimant="source:wikipedia", certainty=0.9,
                   basis={"kind": "source-evidence"})
    for h in hits:
        ctx.ledger.say("search", "search:hit", h,
                       claimant="source:wikipedia", certainty=0.85,
                       basis={"kind": "source-evidence"})
    return {"ok": True, "query": q, "hits": hits}
def h_persona_mint(ctx, slots, nid):
    return ctx.personas.mint(
        name=slots["name"], traits=slots.get("traits"),
        interests=slots.get("interests"), lens=slots.get("lens"),
        figure=slots.get("figure"),
        responsibilities=slots.get("responsibilities"))
def h_persona_onboard(ctx, slots, nid):
    """Extend a minimal persona: portrait, voice, characterization — each
    opened and served as a real need (prompt demo 5)."""
    pid = slots["personaId"]
    p = ctx.personas.get(pid)
    if not p:
        return {"ok": False, "error": "no such persona"}
    out = {"personaId": pid, "name": p["name"]}
    art_res = ctx.invoke("generate-portrait", {"personaId": pid},
                         summary="onboard:portrait", via="onboard")
    out["portrait"] = art_res.get("result")
    v_res = ctx.invoke("persona-voice-set",
                       {"personaId": pid,
                        "name": (p.get("voice") or {}).get("name"),
                        "rate": (p.get("voice") or {}).get("rate", 0)},
                       summary="onboard:voice", via="onboard")
    out["voice"] = v_res.get("result")
    c_res = ctx.invoke("characterize-persona", {"personaId": pid},
                       summary="onboard:characterization", via="onboard")
    out["characterization"] = c_res.get("result")
    out["ok"] = all(isinstance(x, dict) and x.get("ok") for x in
                    (out["portrait"], out["voice"], out["characterization"]))
    return out
def h_generate_portrait(ctx, slots, nid):
    pid = slots["personaId"]
    p = ctx.personas.get(pid)
    if not p:
        return {"ok": False, "error": "no such persona"}
    from . import art
    r = art.generate(ctx, pid, p["name"], mark=p.get("mark"))
    p["art"] = {"file": r["file"], "motif": r["motif"],
                "palette": r["palette"], "params": r["params"]}
    ctx.personas.save()
    ctx.ledger.say(f"persona:{pid}", "persona:art",
                   {"artifact": r["file"], "motif": r["motif"],
                    "params": r["params"], "bound": True},
                   claimant="engine:portrait", certainty=1.0,
                   basis={"kind": "durable-result"})
    return {"ok": True, "artifact": r["file"], "motif": r["motif"]}
def h_persona_voice_set(ctx, slots, nid):
    pid = slots["personaId"]
    p = ctx.personas.get(pid)
    if not p:
        return {"ok": False, "error": "no such persona"}
    if slots.get("name"):
        p.setdefault("voice", {})["name"] = slots["name"]
    if slots.get("rate") is not None:
        p.setdefault("voice", {})["rate"] = int(slots["rate"])
    ctx.personas.save()
    ctx.ledger.say(f"persona:{pid}", "persona:voice", p["voice"],
                   claimant="principal", certainty=1.0,
                   basis={"kind": "user-choice"})
    return {"ok": True, "voice": p["voice"]}
def h_characterize(ctx, slots, nid):
    pid = slots["personaId"]
    p = ctx.personas.get(pid)
    if not p:
        return {"ok": False, "error": "no such persona"}
    system = (f"Summarize how the persona {p['name']} sees the world: lens, "
              f"responsibilities, characteristic phrasing. Traits: "
              f"{', '.join(p.get('traits', []))}. Register: "
              f"{p.get('register')}. Under 80 words, third person.")
    r = ctx.engines.llm.chat(system, f"Persona: {json.dumps(p)[:600]}",
                             max_tokens=120)
    if r.get("ok") and r.get("text"):
        text = r["text"].strip()
        engine = r["engine"]
    else:
        text = (f"{p['name']} reads the ledger through {p.get('register')} "
                f"lenses: {', '.join(p.get('traits', []))}. Interests: "
                f"{', '.join(p.get('interests', [])) or 'general'}. "
                f"Speaks {p.get('register')}; bound to the record.")
        engine = "declared-template"
    p["characterization"] = text
    ctx.personas.save()
    ctx.ledger.say(f"persona:{pid}", "persona:characterization",
                   {"text": text, "engine": engine},
                   claimant="persona:" + p["name"].lower(), certainty=0.9,
                   basis={"kind": "generated"})
    return {"ok": True, "characterization": text, "engine": engine}
def h_persona_update(ctx, slots, nid):
    return ctx.personas.update(slots["personaId"], slots.get("patch", {}))
def h_speak_voice(ctx, slots, nid):
    name = slots.get("persona") or (ctx.personas.active() or {}).get("name",
                                                                    "system")
    item = ctx.floor.admit(name, slots["text"],
                           voice=slots.get("voice"),
                           rate=slots.get("rate", 0),
                           render=ctx.engines.tts.mode == "sapi")
    res = ctx.floor.wait(item, timeout=180)
    return res or {"ok": False, "error": "floor timeout"}
def h_render_sapi(ctx, slots, nid):
    return ctx.engines.tts.render_local(slots["text"],
                                        voice=slots.get("voice"),
                                        rate=slots.get("rate", 0))
def h_render_remote(ctx, slots, nid):
    return ctx.engines.tts.render_remote(slots["text"],
                                         voice=slots.get("voice"))
def h_import_exchange(ctx, slots, nid):
    path = slots.get("package")
    if isinstance(path, dict):
        pkg = path
    else:
        if not path or not os.path.exists(path):
            return {"ok": False, "error": "no such package"}
        pkg = json.load(open(path, encoding="utf-8"))
    if pkg.get("schema") != ctx.exchange_schema:
        return {"ok": False, "error":
                f"schema mismatch ({pkg.get('schema')})"}
    counts = {"personas": 0, "tools": 0, "assertions": 0, "needs": 0}
    src = "exchange:" + pkg.get("id", "pkg")
    existing = {p["name"].lower() for p in ctx.personas.roster()}
    for p in pkg.get("personas", []):
        # a persona already on this roster is a duplicate of the
        # package's copy — skip the mint, record the skip (J1: no
        # double-seeded rosters even via self-import)
        if (p.get("name") or "").lower() in existing:
            ctx.ledger.say("exchange", "exchange:imported",
                           {"kind": "persona", "name": p.get("name"),
                            "package": pkg.get("id"),
                            "skipped": "already-on-roster"},
                           claimant=src, certainty=0.4,
                           basis={"kind": "import"})
            continue
        r = ctx.personas.mint(**p)
        existing.add((p.get("name") or "").lower())
        ctx.ledger.say("exchange", "exchange:imported",
                       {"kind": "persona", "id": r.get("personaId"),
                        "package": pkg.get("id")},
                       claimant=src, certainty=0.4,
                       basis={"kind": "import"})
        counts["personas"] += 1
    for t in pkg.get("tools", []):
        ctx.tools.tool(t["id"], t.get("title", t["id"]), need=t.get("need"),
                       template=t.get("template"), steps=t.get("steps"),
                       authored=True)
        ctx.ledger.say("exchange", "exchange:imported",
                       {"kind": "tool", "id": t["id"],
                        "package": pkg.get("id")},
                       claimant=src, certainty=0.4, basis={"kind": "import"})
        counts["tools"] += 1
    for a in pkg.get("assertions", []):
        ctx.ledger.say(a["subject"], a["predicate"], a["value"],
                       claimant=src, certainty=0.4, basis={"kind": "import"})
        counts["assertions"] += 1
    for n in pkg.get("needs", []):
        ctx.ledger.say("exchange", "exchange:imported",
                       {"kind": "need", "summary": n.get("summary"),
                        "package": pkg.get("id"), "held": "below-threshold"},
                       claimant=src, certainty=0.4, basis={"kind": "import"})
        counts["needs"] += 1
    ctx.ledger.say("exchange", "exchange:package",
                   {"id": pkg.get("id"), "schema": pkg.get("schema"),
                    "counts": counts, "threshold": 0.4,
                    "status": "held-below-action-threshold"},
                   claimant="system", certainty=1.0,
                   basis={"kind": "durable-result"})
    return {"ok": True, "package": pkg.get("id"), "counts": counts,
            "threshold": 0.4}
def h_export_exchange(ctx, slots, nid):
    pred = slots.get("predicate")
    pkg = {"schema": ctx.exchange_schema, "id": model.rid("pkg"),
           "personas": [], "tools": [], "assertions": [], "needs": []}
    for p in ctx.personas.roster()[:6]:
        pkg["personas"].append({"name": p["name"], "traits": p["traits"],
                                "interests": p["interests"],
                                "lens": p["lens"]})
    for t in ctx.tools.tools.values():
        if t.get("authored"):
            pkg["tools"].append({"id": t["id"], "title": t["title"],
                                 "need": t["need"],
                                 "template": t["template"],
                                 "steps": t.get("steps")})
    for a in ctx.ledger.query(predicate=pred, limit=40) if pred else []:
        pkg["assertions"].append({"subject": a.subject,
                                  "predicate": a.predicate,
                                  "value": a.value.get("v")})
    for n in ctx.open_needs()[:10]:
        pkg["needs"].append({"summary": n["summary"],
                             "toolId": n["toolId"]})
    outdir = os.path.join(ctx.runtime, "artifacts", "exports")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, pkg["id"] + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pkg, f, indent=2, ensure_ascii=False)
    ctx.ledger.say("exchange", "exchange:exported",
                   {"id": pkg["id"], "path": path,
                    "counts": {k: len(v) for k, v in pkg.items()
                               if isinstance(v, list)}},
                   claimant="system", certainty=1.0,
                   basis={"kind": "durable-result"})
    return {"ok": True, "path": path,
            "counts": {k: len(v) for k, v in pkg.items()
                       if isinstance(v, list)}}
def h_publish(ctx, slots, nid):
    """Grant-gated consequential tool. With a witnessed grant it writes a
    real local artifact — it never claims a network effect it can't produce."""
    outdir = os.path.join(ctx.runtime, "outbox")
    os.makedirs(outdir, exist_ok=True)
    fname = f"milestone-{model.rid('pub')}.md"
    path = os.path.join(outdir, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {slots.get('target','milestone')}\n\n"
                f"{slots.get('content','')}\n\n"
                f"— published to local outbox by Vantage\n")
    ctx.ledger.say("publish", "publish:artifact",
                   {"target": slots.get("target"), "artifact": path,
                    "channel": "local-outbox",
                    "note": "no configured remote channel — artifact, not "
                            "transmission"},
                   claimant="tool:publish-milestone", certainty=1.0,
                   basis={"kind": "execution"})
    return {"ok": True, "artifact": path, "channel": "local-outbox",
            "delivered": False,
            "note": "wrote local artifact; no remote channel configured"}
def h_send_mail(ctx, slots, nid):
    outdir = os.path.join(ctx.runtime, "outbox")
    os.makedirs(outdir, exist_ok=True)
    fname = f"mail-{model.rid('eml')}.eml"
    path = os.path.join(outdir, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"To: {slots.get('to')}\nSubject: Vantage message\n\n"
                f"{slots.get('body')}\n")
    ctx.ledger.say("mail", "mail:queued",
                   {"to": slots.get("to"), "artifact": path,
                    "status": "queued-local-outbox",
                    "delivered": False},
                   claimant="tool:send-mail", certainty=1.0,
                   basis={"kind": "execution"})
    return {"ok": True, "artifact": path, "delivered": False,
            "status": "queued-local-outbox"}
def h_home_routine(ctx, slots, nid):
    outdir = os.path.join(ctx.runtime, "outbox")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f"routine-{model.rid('act')}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"routine": slots.get("routine"),
                   "actuation": "artifact-only"}, f, indent=2)
    return {"ok": True, "artifact": path, "actuated": False,
            "note": "home device channel not configured — artifact only"}
def h_set_depth(ctx, slots, nid):
    prev = ctx.ledger.resolve("config", "chat:response-depth")
    ctx.ledger.say("config", "chat:response-depth",
                   int(slots["depth"]), claimant="principal",
                   certainty=1.0, basis={"kind": "user-choice"},
                   supersedes=prev.id if prev else None)
    return {"ok": True, "depth": int(slots["depth"])}
def h_focus_need(ctx, slots, nid):
    return floor.focus_need(ctx, slots["needId"], slots.get("on", True))
def h_select_context(ctx, slots, nid):
    r = archive.select_context(ctx, slots["kind"], slots["ref"],
                               slots["label"], slots.get("excerpt", ""))
    # the top respondent comments on the selection
    persona = ctx.personas.active()
    if persona and slots.get("excerpt"):
        d = personas_mod.compose(
            ctx, persona, f"Comment on this selected {slots['kind']}: "
                          f"{slots['label']}",
            facts=[{"text": slots["excerpt"],
                    "source": f"selected:{slots['kind']}"}])
        r["commentary"] = {"persona": persona["name"], "text": d["text"],
                           "register": d.get("register")}
        ctx.bus.emit("persona.speak", {"persona": persona["id"],
                                      "name": persona["name"],
                                      "text": d["text"],
                                      "contextCommentary": True})
    return r
def h_validate_tool(ctx, slots, nid):
    spec = slots.get("spec")
    if isinstance(spec, str):
        spec = json.loads(spec)
    return dsl.validate_spec(spec)
def h_create_tool(ctx, slots, nid):
    spec = slots.get("spec")
    if isinstance(spec, str):
        spec = json.loads(spec)
    v = dsl.validate_spec(spec)
    if not v["ok"]:
        return {"ok": False, "validation": v}
    ctx.tools.tool(spec["id"], spec.get("title", spec["id"]),
                   need=spec.get("need"), template=spec.get("template"),
                   steps=spec.get("steps"), authored=True)
    path = os.path.join(ctx.runtime, "authored-tools.json")
    authored = []
    if os.path.exists(path):
        authored = json.load(open(path, encoding="utf-8"))
    authored = [t for t in authored if t["id"] != spec["id"]]
    authored.append(spec)
    json.dump(authored, open(path, "w", encoding="utf-8"), indent=2)
    return {"ok": True, "toolId": spec["id"], "validation": v}
def h_inspect_tool(ctx, slots, nid):
    t = ctx.tools.get(slots["toolId"])
    if not t:
        return {"ok": False, "error": "no such tool"}
    runs = [a.value.get("v") for a in ctx.ledger.query(
        predicate="need:executed", limit=200)
        if True][:20]
    return {"ok": True, "tool": {"id": t["id"], "title": t["title"],
                                 "need": t["need"], "template": t["template"],
                                 "authored": t.get("authored"),
                                 "steps": bool(t.get("steps"))},
            "trust": compare_mod.trust(ctx.ledger, t["id"])}
def h_steward_tick(ctx, slots, nid):
    return ctx.steward.tick(reason="tool")
def h_assign_stewardship(ctx, slots, nid):
    duty = slots["duty"]
    on = bool(slots.get("on", True))
    prev = ctx.ledger.resolve("steward", f"steward:duty:{duty}")
    ctx.ledger.say("steward", f"steward:duty:{duty}",
                   {"duty": duty, "on": on},
                   claimant="principal", certainty=1.0,
                   basis={"kind": "user-choice"},
                   supersedes=prev.id if prev else None)
    return {"ok": True, "duty": duty, "on": on}
def h_import_calendar(ctx, slots, nid):
    from . import connectors
    return connectors.import_ics(ctx, slots.get("ics", ""),
                                 slots.get("source", "ics-manual"))
def h_link_calendar(ctx, slots, nid):
    buckets = temporal.classify(ctx.ledger)
    proj = slots.get("projectId")
    linked = []
    toks = set(re.findall(r"[a-z]{4,}", (slots.get("title") or "").lower()))
    for b in ("current", "upcoming"):
        for ev in buckets[b]:
            etoks = set(re.findall(r"[a-z]{4,}", ev["summary"].lower()))
            if toks & etoks:
                linked.append(ev["summary"])
                ctx.ledger.say(f"project:{proj}", "calendar:linked",
                               {"event": ev["summary"], "when":
                                ev.get("start_dt")},
                               claimant="model:temporal", certainty=0.8,
                               basis={"kind": "interpretation"})
    return {"ok": True, "linked": linked}
def h_endorse_source(ctx, slots, nid):
    src = slots["source"]
    ctx.ledger.say("sources", "source:endorsement",
                   {"source": src, "raise": 0.1},
                   claimant="principal", certainty=1.0,
                   basis={"kind": "user-choice"})
    prev = ctx.ledger.resolve("sources", f"source:ceiling:{src}")
    ctx.ledger.say("sources", "source:ceiling",
                   {"claimant": src, "ceiling":
                    min(1.0, 0.7 + 0.15)},
                   claimant="principal", certainty=1.0,
                   basis={"kind": "user-choice"})
    return {"ok": True, "endorsed": src}
def h_cleanup(ctx, slots, nid):
    return ctx.ledger.compact(
        ["decision:score", "inference:snapshot", "speech:admitted",
         "idle:steward-run", "archive:turn"], keep=3)
def h_apply_preload(ctx, slots, nid):
    """C-SettingsPreloads: a named preload is a bundle of assertions over the
    common presentation/config choice set; it supplies starting values that
    later choices supersede."""
    name = slots["name"]
    pack = PRELOADS.get(name)
    if not pack:
        return {"ok": False, "error": f"unknown preload '{name}'",
                "available": sorted(PRELOADS)}
    applied = []
    for pred, val in pack["settings"].items():
        prev = ctx.ledger.resolve("config", pred)
        ctx.ledger.say("config", pred, val, claimant="principal",
                       certainty=1.0, basis={"kind": "user-choice"},
                       supersedes=prev.id if prev else None,
                       tags=["preload:" + name])
        applied.append(pred)
    ctx.ledger.say("config", "preload:applied",
                   {"name": name, "settings": applied},
                   claimant="principal", certainty=1.0,
                   basis={"kind": "user-choice"})
    return {"ok": True, "preload": name, "applied": applied}
def h_set_theme(ctx, slots, nid):
    theme = slots["theme"]
    prev = ctx.ledger.resolve("config", "ui:shell-theme")
    ctx.ledger.say("config", "ui:shell-theme", theme,
                   claimant="principal", certainty=1.0,
                   basis={"kind": "user-choice"},
                   supersedes=prev.id if prev else None)
    return {"ok": True, "theme": theme}
def h_transcribe(ctx, slots, nid):
    """Browser Web Speech transcript → witness → chat turn (mic channel)."""
    text = slots["text"]
    ctx.ledger.say("device", "device:speech-transcript",
                   {"text": text, "channel": "browser-webspeech"},
                   claimant="surface:mic", certainty=0.9,
                   basis={"kind": "captured-input"})
    return run_chat_turn(ctx, text, via="mic")
def h_note_for_persona(ctx, slots, nid):
    pid = slots["personaId"]
    p = ctx.personas.get(pid)
    if not p:
        return {"ok": False, "error": "no such persona"}
    note = slots["note"]
    ctx.ledger.say(f"persona:{pid}", "persona:note",
                   {"note": note}, claimant="principal", certainty=0.9,
                   basis={"kind": "user-choice"})
    p.setdefault("notes", []).append(note)
    ctx.personas.save()
    return {"ok": True, "noted": note}
def h_compare_run(ctx, slots, nid):
    return ctx.compete(slots["need"], slots.get("input", {}))
# -- named settings preloads (C-PreloadSuite — ≥3, era-named) -----------------
PRELOADS = {
    "athenaeum": {"settings": {"ui:shell-theme": "sepia",
                               "chat:response-depth": 3,
                               "user:persona-frame": "personified"}},
    "workshop":  {"settings": {"ui:shell-theme": "light",
                               "chat:response-depth": 1,
                               "user:persona-frame": "respondent"}},
    "evening":   {"settings": {"ui:shell-theme": "dark",
                               "chat:response-depth": 2,
                               "user:persona-frame": "respondent"}},
}
# ---------------------------------------------------------------------------
# registration
def register(ctx):
    R = ctx.tools
    R.tool("set-topic", "Set conversation topic",
           need="chat.topic",
           template={"slots": [{"name": "topic", "required": True,
                                "test": {"kind": "minLen", "n": 2}}]},
           handler=h_set_topic)
    R.tool("chat-reset", "Seal + reset the conversation",
           handler=h_chat_reset)
    R.tool("remember", "Record a fact as a user assertion",
           need="memory.note",
           template={"slots": [{"name": "fact", "required": True,
                                "test": {"kind": "minLen", "n": 3}}]},
           handler=h_remember)
    R.tool("create-project", "Create a project with goals",
           need="project.create",
           template={"slots": [{"name": "title", "required": True},
                               {"name": "goals", "required": False}]},
           handler=h_create_project)
    R.tool("build-list", "Build a criteria-governed list (set fulfillment)",
           need="set.build",
           template={"slots": [{"name": "criteria", "required": True,
                                "test": {"kind": "minLen", "n": 5}}]},
           handler=h_build_list)
    R.tool("retrieve-set-wiki-table", "Set members via PA wikitable class",
           need="set.members", handler=h_retrieve_table)
    R.tool("retrieve-set-wiki-category", "Set members via PA category",
           need="set.members", handler=h_retrieve_category)
    R.tool("run-search", "Search configured sources",
           need="search.run",
           template={"slots": [{"name": "query", "required": True,
                                "test": {"kind": "minLen", "n": 3}}]},
           handler=h_run_search)
    R.tool("persona-mint", "Mint a personality (minimal input ok)",
           need="persona.mint",
           template={"slots": [{"name": "name", "required": True,
                                "test": {"kind": "minLen", "n": 2}},
                               {"name": "traits"}, {"name": "interests"},
                               {"name": "lens"}, {"name": "figure"},
                               {"name": "responsibilities"}]},
           handler=h_persona_mint)
    R.tool("persona-onboard", "Portrait + voice + characterization needs",
           need="persona.onboard",
           template={"slots": [{"name": "personaId", "required": True}]},
           handler=h_persona_onboard)
    R.tool("generate-portrait", "Generate + bind persona portrait",
           need="persona.portrait",
           template={"slots": [{"name": "personaId", "required": True}]},
           handler=h_generate_portrait)
    R.tool("persona-voice-set", "Assign/modify persona voice",
           need="persona.voice",
           template={"slots": [{"name": "personaId", "required": True},
                               {"name": "name"}, {"name": "rate"}]},
           handler=h_persona_voice_set)
    R.tool("characterize-persona", "Write persona characterization",
           need="persona.characterize",
           template={"slots": [{"name": "personaId", "required": True}]},
           handler=h_characterize)
    R.tool("persona-update", "Edit persona elements",
           need="persona.update",
           template={"slots": [{"name": "personaId", "required": True},
                               {"name": "patch", "required": True}]},
           handler=h_persona_update)
    R.tool("speak-voice", "Speak text through the speech floor",
           need="speech.speak",
           template={"slots": [{"name": "text", "required": True},
                               {"name": "persona"}, {"name": "voice"},
                               {"name": "rate"}]},
           handler=h_speak_voice)
    R.tool("render-speech-sapi", "Local SAPI speech renderer",
           need="speech.render",
           template={"slots": [{"name": "text", "required": True},
                               {"name": "voice"}, {"name": "rate"}]},
           handler=h_render_sapi)
    R.tool("render-speech-remote", "Remote speech service (declared absent)",
           need="speech.render",
           template={"slots": [{"name": "text", "required": True},
                               {"name": "voice"}]},
           handler=h_render_remote)
    R.tool("import-exchange", "Import an exchange package below threshold",
           need="exchange.import",
           template={"slots": [{"name": "package", "required": True}]},
           handler=h_import_exchange)
    R.tool("export-exchange", "Export a storefront package",
           need="exchange.export",
           template={"slots": [{"name": "predicate"}]},
           handler=h_export_exchange)
    R.tool("publish-milestone", "Publish a milestone (grant-gated)",
           need="publish.artifact", consequential=True,
           template={"slots": [{"name": "target", "required": True},
                               {"name": "content", "required": True}],
                     "grant": "publish.creator"},
           handler=h_publish)
    R.tool("send-mail", "Send mail (grant-gated; honest local outbox)",
           need="mail.send", consequential=True,
           template={"slots": [{"name": "to", "required": True},
                               {"name": "body", "required": True}],
                     "grant": "mail.send"},
           handler=h_send_mail)
    R.tool("dispatch-home-routine", "Actuate home routine (grant-gated)",
           need="home.actuate", consequential=True,
           template={"slots": [{"name": "routine", "required": True}],
                     "grant": "home.actuate"},
           handler=h_home_routine)
    R.tool("set-response-depth", "Respondents per turn (1-4)",
           need="config.depth",
           template={"slots": [{"name": "depth", "required": True,
                                "test": {"kind": "range",
                                         "lo": 1, "hi": 4}}]},
           handler=h_set_depth)
    R.tool("focus-need", "Move a need into focus",
           need="need.focus",
           template={"slots": [{"name": "needId", "required": True},
                               {"name": "on"}]},
           handler=h_focus_need)
    R.tool("select-context", "Pull an item into conversational context",
           need="context.select",
           template={"slots": [{"name": "kind", "required": True},
                               {"name": "ref", "required": True},
                               {"name": "label", "required": True},
                               {"name": "excerpt"}]},
           handler=h_select_context)
    R.tool("validate-tool", "Validate a tool spec (errors+hints)",
           need="tool.validate",
           template={"slots": [{"name": "spec", "required": True}]},
           handler=h_validate_tool)
    R.tool("create-tool", "Mint an authored tool from a spec",
           need="tool.create",
           template={"slots": [{"name": "spec", "required": True}]},
           handler=h_create_tool)
    R.tool("inspect-tool", "Tool detail + trust telemetry",
           need="tool.inspect",
           template={"slots": [{"name": "toolId", "required": True}]},
           handler=h_inspect_tool)
    R.tool("steward-tick", "Run one stewardship pass",
           need="steward.tick", handler=h_steward_tick)
    R.tool("assign-stewardship", "Configure a steward duty",
           need="steward.assign",
           template={"slots": [{"name": "duty", "required": True},
                               {"name": "on"}]},
           handler=h_assign_stewardship)
    R.tool("import-calendar", "Import ICS calendar source evidence",
           need="calendar.import",
           template={"slots": [{"name": "ics", "required": True},
                               {"name": "source"}]},
           handler=h_import_calendar)
    R.tool("link-calendar", "Relate project to calendar events",
           need="calendar.link",
           template={"slots": [{"name": "projectId", "required": True},
                               {"name": "title"}]},
           handler=h_link_calendar)
    R.tool("endorse-source", "Raise a source's inherited confidence",
           need="source.endorse",
           template={"slots": [{"name": "source", "required": True}]},
           handler=h_endorse_source)
    R.tool("cleanup-run", "Governed ledger consolidation",
           need="ledger.cleanup", handler=h_cleanup)
    R.tool("apply-preload", "Apply a named settings preload",
           need="config.preload",
           template={"slots": [{"name": "name", "required": True,
                                "test": {"kind": "enum",
                                         "options": sorted(PRELOADS)}}]},
           handler=h_apply_preload)
    R.tool("set-theme", "Set the shell colorway",
           need="ui.theme",
           template={"slots": [{"name": "theme", "required": True,
                                "test": {"kind": "enum",
                                         "options": ["light", "dark",
                                                    "sepia", "slate"]}}]},
           handler=h_set_theme)
    R.tool("transcribe-speech", "Browser speech transcript → turn",
           need="speech.transcribe",
           template={"slots": [{"name": "text", "required": True}]},
           handler=h_transcribe)
    R.tool("note-for-persona", "Add a note to a persona",
           need="persona.note",
           template={"slots": [{"name": "personaId", "required": True},
                               {"name": "note", "required": True}]},
           handler=h_note_for_persona)
    R.tool("compare-run", "Run competing tools on the same input",
           need="comparison.run",
           template={"slots": [{"name": "need", "required": True},
                               {"name": "input"}]},
           handler=h_compare_run)
    # -- system commands (object.verb) ----------------------------------------
    C = ctx.tools.command
    C("ledger.query", lambda ctx, a: [
        r.row() for r in ctx.ledger.query(**a)])
    C("ledger.assert", lambda ctx, a: ctx.ledger.say(
        a["subject"], a["predicate"], a["value"],
        claimant=a.get("claimant", "principal"),
        certainty=a.get("certainty", 0.9),
        basis={"kind": a.get("basis", "user-choice")}).row())
    C("roster.select", lambda ctx, a: ctx.personas.select(a["personaId"]))
    C("roster.move", lambda ctx, a: ctx.personas.move(
        a["personaId"], a.get("direction", 0)))
    C("roster.list", lambda ctx, a: [p["id"] for p in ctx.personas.roster()])
    C("need.focus", lambda ctx, a: floor.focus_need(
        ctx, a["needId"], a.get("on", True)))
    C("need.cancel", lambda ctx, a: floor.cancel_need(ctx, a["needId"]))
    C("grant.issue", lambda ctx, a: {"grantId": floor.issue_grant(
        ctx, a["scope"], a.get("lock"), a.get("consumable", True))})
    C("theme.set", lambda ctx, a: h_set_theme(ctx, a, None))
    C("preload.apply", lambda ctx, a: h_apply_preload(ctx, a, None))
    C("steward.wake", lambda ctx, a: ctx.steward.tick(reason="command"))
    C("chat.topic", lambda ctx, a: archive.set_topic(ctx, a["topic"]))
