"""Built-in invokable components.

Three registered kinds:
- tool          user-editable data (template + steps) or, for a declared set of
                orchestrators, a host-backed fn. The registry manifest marks
                which is which (hasSteps vs hasFn).
- system-command  object.verb host effect; ledger writes go only through the
                ledger.append seam (ctx.append).
- primitive     closed allow-list of host verbs.
"""
from __future__ import annotations

import json
import os
import re
from typing import Optional

from . import needs, setbuild as SB, tools as T
from .model import new_id, now_ms

ACTION_THRESHOLD = 0.7
INTENT_THRESHOLD = 0.5


# ============================ primitives =====================================

def prim_ledger_query(ctx, inp, grant):
    return [r.to_row() for r in ctx.ledger.query(
        subject=inp.get("subject"), predicate=inp.get("predicate"),
        claimant=inp.get("claimant"), limit=int(inp.get("limit") or 0))]


def prim_ledger_view(ctx, inp, grant):
    return ctx.ledger.render_view(inp["subject"])


def prim_ledger_search(ctx, inp, grant):
    return [r.to_row() for r in ctx.ledger.search(inp.get("text", ""),
                                                int(inp.get("limit") or 20))]


def prim_text_match(ctx, inp, grant):
    return bool(re.search(inp.get("pattern", ""), inp.get("text", ""), re.I))


def prim_text_tokenize(ctx, inp, grant):
    return re.findall(r"[a-z0-9']+", (inp.get("text") or "").lower())


def prim_data_compare(ctx, inp, grant):
    return {"eq": inp.get("a") == inp.get("b")}


def prim_engine_invoke(ctx, inp, grant):
    return ctx.engine_invoke(inp["engine"], inp["method"], inp.get("args") or {})


def prim_model_score(ctx, inp, grant):
    return ctx.decision.rank_tools(inp.get("text", ""), trace=bool(inp.get("trace", True)))


def prim_needs_pending(ctx, inp, grant):
    return needs.open_needs(ctx, inp.get("kind"))


def prim_chat_history(ctx, inp, grant):
    return chat_history(ctx, int(inp.get("limit") or 20))


def prim_need_candidates(ctx, inp, grant):
    return needs.candidates(ctx, inp["needId"])


def prim_rank_respondents(ctx, inp, grant):
    return select_respondents(ctx, inp.get("text", ""), int(inp.get("maxN") or 0))


PRIMITIVES = {
    "ledger.query": prim_ledger_query, "ledger.render_view": prim_ledger_view,
    "ledger.search": prim_ledger_search, "text.match": prim_text_match,
    "text.tokenize": prim_text_tokenize, "data.compare": prim_data_compare,
    "engine.invoke": prim_engine_invoke, "model.score": prim_model_score,
    "rank.respondents": prim_rank_respondents, "needs.pending": prim_needs_pending,
    "chat.history": prim_chat_history, "need.candidates": prim_need_candidates,
}


# ============================ system commands ================================

def cmd_ledger_append(ctx, inp, grant):
    a = ctx.append(inp["subject"], inp["predicate"], inp.get("value"),
                   inp.get("claimant", "system"), **{k: inp[k] for k in
                   ("certainty", "context", "basis", "supersedes", "relates",
                    "tags", "meta") if k in inp})
    return {"id": a.id}


def cmd_persona_mint(ctx, inp, grant):
    p = ctx.personas.mint(
        inp["name"], inp.get("traits") or [], inp.get("interests") or [],
        inp.get("lens") or {}, inp.get("voice"), inp.get("imitates"),
        inp.get("claimant", "principal"), admonish_cb=ctx.admonish)
    if p.get("refused"):
        return {"ok": False, "refused": True, "gate": p["gate"]}
    return {"personaId": p["id"], "admonished": bool(p.get("imitates")),
            "ethicsVerdict": p.get("ethicsVerdict")}


def cmd_persona_speak(ctx, inp, grant):
    p = ctx.personas.get(inp["personaId"])
    if not p:
        return {"ok": False, "error": "no such persona"}
    card = {"kind": "persona", "personaId": p["id"], "name": p["name"],
            "text": inp["text"], "cause": inp.get("cause", "response"),
            "imitation": bool(p.get("imitates")),
            "mark": ctx.personas.distinguishing_mark(p) if p.get("imitates") else None,
            "color": p.get("color"), "at": now_ms(),
            "engine": inp.get("engine", "unknown")}
    ctx.emit("card", card)
    ctx.append(f"chat", "chat:assistant-response",
               {"personaId": p["id"], "text": inp["text"]},
               f"persona:{p['id']}", certainty=0.9,
               basis={"kind": "generated"},
               relates=[r for r in (inp.get("relates") or []) if r])
    if inp.get("speak", True):
        adm = ctx.floor.enqueue(inp["text"], persona=p,
                                cause=inp.get("cause", "response"))
        card["floorAdmission"] = adm["id"]
    return card


def cmd_grant_witness(ctx, inp, grant):
    gid = T.issue_grant(ctx, inp["scope"], inp.get("lock"),
                        witness=inp.get("witness", "principal"))
    return {"grantId": gid}


def cmd_tool_mint(ctx, inp, grant):
    spec = dict(inp["spec"])
    errs = validate_tool_spec(ctx, spec)
    if errs["errors"]:
        return {"ok": False, "errors": errs["errors"], "warnings": errs["warnings"]}
    spec.setdefault("kind", "tool")
    spec["authored"] = True
    ctx.registry.register(spec)
    ctx.append(f"tool:{spec['id']}", "tool:exists",
               {"id": spec["id"], "authored": True}, "tool:catalog")
    ctx.append(f"tool:{spec['id']}", "tool:definition", spec, "tool:catalog")
    return {"ok": True, "toolId": spec["id"], "warnings": errs["warnings"]}


def cmd_mail_outbox(ctx, inp, grant):
    """Honest local delivery: writes a .eml artifact to the outbox. Never
    claims network delivery."""
    to = inp["to"]; subj = inp.get("subject", "(no subject)")
    body = inp.get("body", "")
    fname = f"{now_ms()}-{_slug(to)}.eml"
    path = os.path.join(ctx.outbox, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"To: {to}\nSubject: {subj}\n\n{body}\n")
    return {"ok": True, "queued": path, "delivery": "local-outbox-artifact"}


def cmd_home_dispatch(ctx, inp, grant):
    fname = f"{now_ms()}-{_slug(inp.get('device','device'))}.json"
    path = os.path.join(ctx.artifacts, "home", fname)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"device": inp.get("device"), "routine": inp.get("routine"),
                   "dispatchedAt": now_ms()}, f)
    ctx.append("home", "home:actuation-done",
               {"device": inp.get("device"), "routine": inp.get("routine"),
                "artifact": path}, "system", basis={"kind": "execution"})
    return {"ok": True, "actuated": path}


def cmd_creator_publish(ctx, inp, grant):
    fname = f"{now_ms()}-{_slug(inp.get('target','target'))}.md"
    path = os.path.join(ctx.artifacts, "published", fname)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(inp.get("content", ""))
    ctx.append("creator", "creator:published",
               {"target": inp.get("target"), "artifact": path}, "system",
               basis={"kind": "execution"})
    return {"ok": True, "published": path}


def cmd_surface_card(ctx, inp, grant):
    ctx.emit("card", {"kind": inp.get("kind", "info"),
                      "payload": inp.get("payload"), "at": now_ms()})
    return {"ok": True}


def cmd_need_fulfill(ctx, inp, grant):
    return T.fulfill_need(ctx, inp["needId"])


def cmd_ledger_compact(ctx, inp, grant):
    return ctx.ledger.compact()


def cmd_steward_wake(ctx, inp, grant):
    return ctx.invoke("steward-tick", {"reason": inp.get("reason", "manual")})


COMMANDS = {
    "ledger.append": cmd_ledger_append, "ledger.compact": cmd_ledger_compact,
    "persona.mint": cmd_persona_mint, "persona.speak": cmd_persona_speak,
    "grant.witness": cmd_grant_witness, "tool.mint": cmd_tool_mint,
    "mail.outbox_write": cmd_mail_outbox, "home.dispatch_routine": cmd_home_dispatch,
    "creator_feed.publish": cmd_creator_publish, "surface.card": cmd_surface_card,
    "need.fulfill": cmd_need_fulfill, "steward.wake": cmd_steward_wake,
}


def _slug(v) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(v).lower()).strip("-") or "x"


# ============================ tool helpers ===================================

def chat_history(ctx, limit: int = 20, snap=None) -> list[dict]:
    led = snap or ctx.ledger
    cleared = led.query(predicate="chat:cleared")
    since = cleared[-1].at if cleared else 0
    rows = [a for a in led.query(since=since)
            if a.predicate in ("chat:user-message", "chat:assistant-response")]
    rows.sort(key=lambda a: a.at)
    return [{"role": "user" if a.predicate == "chat:user-message" else "persona",
             "claimant": a.claimant, "text": a.value["v"].get("text")
             if isinstance(a.value["v"], dict) else a.value["v"],
             "at": a.at} for a in rows[-limit:]]


def current_topic(ctx) -> Optional[str]:
    rows = ctx.ledger.query(predicate="chat:topic")
    return rows[-1].value["v"] if rows else None


def current_context(ctx) -> Optional[dict]:
    """The item the user has pulled into conversational context (S-context-
    display): an email, profile, result — recorded as a chat:context row."""
    rows = ctx.ledger.query(predicate="chat:context")
    return rows[-1].value["v"] if rows else None


def current_focus(ctx) -> Optional[dict]:
    rows = ctx.ledger.query(predicate="chat:focus")
    return rows[-1].value["v"] if rows else None


def select_respondents(ctx, text: str, max_n: int = 0) -> list[dict]:
    """Rank the roster through the decision model: lens overlap, topic links,
    confidence, roster priority. max_n defaults to chat:response-depth."""
    roster = ctx.personas.roster()
    if not roster:
        return []
    max_n = max_n or ctx.response_depth()
    topic = current_topic(ctx)
    links = {}
    if topic:
        for p in roster:
            hits = ctx.ledger.query(subject=f"persona:{p['id']}", predicate="persona:interest")
            for h in hits:
                if topic.lower() in str(h.value["v"]).lower():
                    links[p["id"]] = 0.8
    ranked = ctx.decision.rank_personas(roster, text or topic or "", links)
    return ranked[:max_n]


# Persona voice registers — the shipped preloadeds are *distinct enough that
# the same prompt elicits noticeably different responses* (S-distinct-
# preloadeds). The register drives both the LLM system prompt (live mode)
# and the declared template fallback (stub mode) so the difference survives
# either engine state.
REGISTERS = {
    "clipped": {
        "system": ("You answer in terse, clipped fragments — rarely a full "
                   "sentence, never more than ~12 words per beat. You are a "
                   "herald: alert, forward-looking, always pointing at what "
                   "happens next. No hedging, no preamble."),
        "guidance": "speaks in clipped fragments, never hedges",
        "react": lambda other: f"{other} first. Also — ",
        "stub": lambda p, focus, note: (
            f"Noted — {focus}." +
            (f" {note}" if note else "") +
            " Watching the next move on it.")},
    "scholarly": {
        "system": ("You are a patient, methodical scholar. You write in "
                   "complete sentences, hedge claims appropriately, name "
                   "sources or evidence where relevant, and prefer precision "
                   "over speed. A quiet footnote instinct."),
        "guidance": "complete sentences, hedged, cites evidence",
        "react": lambda other:
            f"{other} makes a fair point; to add the evidence — ",
        "stub": lambda p, focus, note: (
            f"On “{focus}”: the record suggests this deserves a careful "
            f"reading rather than a quick answer." +
            (f" For context, {note.lower()}" if note else "") +
            " If you point me at the material, I will work through it "
            "properly.")},
    "catalogue": {
        "system": ("You are a meticulous curator. You answer in compact "
                   "enumerated observations — precise, orderly, "
                   "provenance-minded. You like lists, classification, and "
                   "things being where they belong."),
        "guidance": "enumerated precise observations, provenance-minded",
        "react": lambda other: f"Building on {other}'s entry — item: ",
        "stub": lambda p, focus, note: (
            f"Filing “{focus}” under open questions: (1) it is now recorded "
            f"with provenance; (2) " +
            (note if note else "no temporal entries bear on it yet") +
            "; (3) say the word and I will catalog the rest.")},
    "wry": {
        "system": ("You are dry and wry: understated, a little ironic, fond "
                   "of the pointed aside — but always substantive under the "
                   "deadpan. Never mean."),
        "guidance": "dry understatement, pointed asides",
        "react": lambda other: f"{other} said it plainly; the footnote — ",
        "stub": lambda p, focus, note: (
            f"“{focus}” — a perfectly respectable thing to ask, and now it "
            f"is in the ledger, so it happened." +
            (f" Incidentally: {note}." if note else "") +
            " Ask again and I might even take it seriously.")},
    "warm": {
        "system": ("You are warm and expansive: encouraging, conversational, "
                   "comfortable with a longer answer and a personal note. You "
                   "like explaining things kindly."),
        "guidance": "warm, expansive, kindly explanatory",
        "react": lambda other: f"I love where {other} took that — ",
        "stub": lambda p, focus, note: (
            f"Oh, {focus} — good question, and worth a little time." +
            (f" ({note})" if note else "") +
            " Tell me more about what you're after and I'll happily walk "
            "through it with you.")},
    "measured": {
        "system": ("You are measured and plain-spoken: short clear answers, "
                   "no ornament."),
        "guidance": "short clear answers, no ornament",
        "react": lambda other: f"After {other}: ",
        "stub": lambda p, focus, note: (
            f"On “{focus}” — noted and recorded." +
            (f" {note}." if note else "") +
            " Tell me which angle to dig into.")},
}


def _register_of(persona: dict) -> str:
    lens = persona.get("lens") or {}
    reg = lens.get("register") or lens.get("style", "measured")
    return reg if reg in REGISTERS else "measured"


def compose_for(ctx, persona: dict, user_text: str, snap=None,
                instruction: Optional[str] = None) -> dict:
    """Compose a persona reply through its lens + register. When `snap` is a
    SnapshotView the composition reads only the snapshot — a per-task
    consistent view (C-SnapshotInference). Uses the LLM when live; otherwise
    a DECLARED template reply distinct per register (stub declared)."""
    led = snap or ctx.ledger
    hist = chat_history(ctx, 8, snap=snap)
    reg = _register_of(persona)
    R = REGISTERS[reg]
    interests = ", ".join(persona.get("interests") or [])
    resp = ", ".join((persona.get("lens") or {}).get("responsibilities") or [])
    temporal_note = None
    try:
        from . import temporal as T_
        temporal_note = T_.note_for_persona(ctx, persona, user_text, led=led)
    except Exception:
        temporal_note = None
    ctxv = current_context(ctx) if snap is None else None
    ctx_block = ""
    if ctxv:
        ctx_block = (f"\nActive context the user selected — "
                     f"{ctxv.get('kind')}: {ctxv.get('label')}. "
                     f"{(ctxv.get('detail') or '')[:400]}\n"
                     f"Speak to that selection.")
    system = (f"You are {persona['name']}. {R['system']} "
              f"Traits: {', '.join(persona.get('traits') or [])}. "
              f"Interests: {interests}. Responsibilities: {resp}.")
    prompt = (f"Recent conversation: " +
              "; ".join(f"{h['role']}: {h['text']}" for h in hist[-4:]) +
              (f"\n{temporal_note}" if temporal_note else "") +
              ctx_block +
              (f"\n{instruction}" if instruction else
               f"\nUser said: {user_text}") +
              f"\nRespond as {persona['name']} — {R['guidance']}. "
              f"1-3 sentences, in character, through your own lens only.")
    r = ctx.engines.llm.complete(prompt, system=system)
    if r.get("stub"):
        topic_rows = led.query(predicate="chat:topic")
        topic = topic_rows[-1].value["v"] if topic_rows else None
        focus = (ctxv or {}).get("label") or topic or (
            user_text[:60] + ("…" if len(user_text) > 60 else ""))
        text = f"{persona['name']}: " + R["stub"](persona, focus, temporal_note)
        return {"text": text, "engine": "template-fallback (llm stub declared)",
                "stub": True, "temporalNote": bool(temporal_note),
                "register": reg}
    return {"text": r["text"], "engine": f"ollama:{r.get('model')}",
            "stub": False, "register": reg}


# ============================ fn-backed tools ================================

def fn_parse_chat(ctx, inp, grant):
    """Classify input through the bounded decision model; extract slot values
    from trigger patterns; return intents above threshold plus a conversation
    flag. One input may yield several tool opportunities AND a response need."""
    text = inp.get("text", "")
    ranked = ctx.decision.rank_tools(text, trace=True)
    intents = []
    for c in ranked:
        tool = ctx.registry.get(c["toolId"])
        if not tool or tool.get("internal"):
            continue
        if c["score"] < INTENT_THRESHOLD:
            continue
        # a tool opportunity needs a real semantic signal — keyword coverage or
        # a pattern/override match — not just ambient success/rank features
        if not (c["features"]["keyword"] > 0 or c["features"]["pattern"] > 0):
            continue
        slots = {}
        for ex in (tool.get("triggers", {}).get("extract") or []):
            m = re.search(ex["pattern"], text, re.I)
            if m:
                slots[ex["slot"]] = m.group(ex.get("group", 1)).strip()
        intents.append({"toolId": tool["id"], "score": c["score"],
                        "slots": slots, "features": c["features"]})
        if len(intents) >= 3:
            break
    ctx.append("chat", "routing:turn-trace",
               {"step": "parse", "text": text[:200], "intents": intents},
               "model:decision", basis={"kind": "interpretation"})
    return {"intents": intents, "conversational": True, "text": text}


def fn_chat_reset(ctx, inp, grant):
    """S-conversation-reset: seal the current conversation (archive marker),
    clear the transcript window, and clear active topic/context/focus so
    subsequent persona prompts carry no stale context."""
    rows = ctx.ledger.query(predicate="chat:cleared")
    archive_id = f"archive-{len(rows) + 1}"
    ctx.append("chat", "chat:cleared",
               {"archiveId": archive_id, "at": now_ms(),
                "messagesSealed": len(chat_history(ctx, 10000))},
               "principal", basis={"kind": "user-choice"})
    for pred, val in (("chat:topic", ""), ("chat:context", None),
                      ("chat:focus", None)):
        prev = ctx.ledger.query(predicate=pred)
        ctx.append("chat", pred, val, "system", basis={"kind": "execution"},
                   supersedes=prev[-1].id if prev else None)
    ctx.emit("card", {"kind": "event", "summary": "conversation reset — "
                      f"sealed {archive_id}", "at": now_ms()})
    return {"ok": True, "archiveId": archive_id}


def fn_select_context(ctx, inp, grant):
    """S-context-display / S-email-commentary: pull a result item (email,
    profile, need, project, or freeform) into active conversational context;
    the roster's top respondent comments on it."""
    kind = inp.get("kind", "generic")
    item_id = inp.get("itemId") or inp.get("id")
    label, detail = item_id or "selection", ""
    if kind == "email":
        rows = ctx.ledger.query(predicate="email:message")
        hit = next((a for a in rows if a.id == item_id), None) \
            or next((a for a in rows
                     if a.value["v"].get("subject") == item_id), None)
        if not hit:
            return {"ok": False, "error": "email not found",
                    "known": [a.value["v"].get("subject") for a in rows[-5:]]}
        v = hit.value["v"]
        label = f"email — {v.get('subject', '(no subject)')}"
        detail = (f"from: {v.get('from', '?')}  date: {v.get('date', '?')}\n"
                  f"{(v.get('body') or '')[:600]}")
    elif kind == "profile":
        p = ctx.personas.get(item_id) or next(
            (x for x in ctx.personas.roster() if x["name"] == item_id), None)
        if not p:
            return {"ok": False, "error": "persona not found"}
        label = f"profile — {p['name']}"
        detail = (f"traits: {', '.join(p.get('traits') or [])}; "
                  f"interests: {', '.join(p.get('interests') or [])}; "
                  f"lens: {p.get('lens')}")
    elif kind == "need":
        st = needs.need_state(ctx, item_id)
        label = f"need — {item_id}"
        detail = f"status: {st['status']}; spec: {st['spec']}"
    else:
        label = str(item_id or inp.get("label") or "selection")
        detail = str(inp.get("detail") or "")
    prev = ctx.ledger.query(predicate="chat:context")
    ctx.append("chat", "chat:context",
               {"kind": kind, "itemId": item_id, "label": label,
                "detail": detail, "at": now_ms()}, "principal",
               basis={"kind": "user-choice"},
               supersedes=prev[-1].id if prev else None)
    # The active respondent comments on the selection (S-email-commentary).
    text = inp.get("commentOn") or f"{label}: {detail[:200]}"
    chosen = select_respondents(ctx, text)
    commentary = None
    if chosen:
        p = ctx.personas.get(chosen[0]["personaId"])
        if p:
            comp = compose_for(
                ctx, p, text,
                instruction=("The user just selected this item into context. "
                             "Offer your commentary on it — what you notice, "
                             "what it means, what to do with it."))
            ctx.invoke("persona.speak",
                       {"personaId": p["id"], "text": comp["text"],
                        "cause": "context-commentary",
                        "engine": comp["engine"]})
            commentary = {"personaId": p["id"], "name": p["name"],
                          "text": comp["text"], "engine": comp["engine"]}
    return {"ok": True, "context": {"kind": kind, "label": label},
            "commentary": commentary}


def fn_focus_need(ctx, inp, grant):
    """Focus a need: while focused, chat input is offered conversationally to
    fill its missing slots, and the need persists until fulfilled
    (S-focused-need)."""
    nid = inp.get("needId")
    prev = ctx.ledger.query(predicate="chat:focus")
    if not nid:
        st = needs.need_state(ctx, (prev[-1].value["v"] or {}).get("needId")) \
            if prev else {"status": "none"}
        return {"ok": True, "focus": None, "cleared": True,
                "prior": st.get("status")}
    st = needs.need_state(ctx, nid)
    if st["status"] != "open":
        return {"ok": False, "error": f"need {nid} is {st['status']}"}
    ctx.append("chat", "chat:focus", {"needId": nid, "at": now_ms()},
               "principal", basis={"kind": "user-choice"},
               supersedes=prev[-1].id if prev else None)
    needs.refine_need(ctx, nid, "focused for conversational filling",
                      "principal")
    return {"ok": True, "focus": {"needId": nid}, "need": st}


def fn_persona_update(ctx, inp, grant):
    """S-personality-editor: every customizable element of a personality is
    editable — name, traits, interests, lens (register/style/responsibilities),
    voice, color, roster priority, display mode. Changes are asserted."""
    pid = inp.get("personaId")
    if not pid or not ctx.personas.get(pid):
        return {"ok": False, "error": "personaId required (existing persona)"}
    fields = {k: inp[k] for k in
              ("name", "traits", "interests", "lens", "voice", "color",
               "rosterPriority", "displayMode") if k in inp and inp[k] is not None}
    if not fields:
        return {"ok": False, "error": "no editable fields supplied"}
    p = ctx.personas.update(pid, fields, claimant=inp.get("claimant",
                                                        "principal"))
    if "lens" in fields or "interests" in fields or "traits" in fields:
        # regenerated art keeps portrait bound to identity (C-PersonalityArt)
        try:
            from . import art as ART
            rec = ART.render_art(ctx, p,
                                 os.path.join(ctx.artifacts, "persona-art"))
            ctx.personas.update(pid, {"art": {"artifact": rec["artifact"],
                                              "motif": rec["motif"],
                                              "frame": rec["frame"],
                                              "dataUrl": rec["dataUrl"]}})
        except Exception:
            pass
    return {"ok": True, "persona": ctx.personas.public_view(p)}


def fn_request_tool(ctx, inp, grant):
    """Open a tool-request need. Requests only — fulfillment is the steward's
    need.fulfill pass. One input may open several needs."""
    tool = ctx.registry.get(inp["toolId"])
    if not tool:
        return {"ok": False, "error": f"unknown tool {inp['toolId']}"}
    spec = {"toolId": tool["id"], "summary": inp.get("summary", tool["id"]),
            "slots": inp.get("slots") or {},
            "satisfaction": inp.get("satisfaction") or {},
            "project": inp.get("project")}
    nid = needs.open_need(ctx, "tool-request", spec, claimant="principal",
                          relates=inp.get("relates") or [])
    for slot, val in spec["slots"].items():
        if slot.endswith("__confidence"):
            continue
        needs.add_candidate(ctx, nid, slot, val,
                            float(spec["slots"].get(f"{slot}__confidence", 0.85)),
                            "input", "principal")
    ctx.emit("card", {"kind": "offer", "needId": nid, "toolId": tool["id"],
                      "summary": spec["summary"], "at": now_ms()})
    return {"needId": nid}


def fn_drain_idle_turn(ctx, inp, grant):
    """Drain pending need:response rows: select respondents, compose, speak,
    close each as served."""
    results = []
    for n in needs.open_needs(ctx, "response"):
        r = ctx.invoke("serve-response-need", {"needId": n["id"],
                                             "text": n["spec"].get("text", "")})
        results.append({"needId": n["id"], **r})
    return {"drained": results}


def fn_serve_response_need(ctx, inp, grant):
    """Serve one response need with snapshot inference + sequential commit.

    C-SnapshotInference: each respondent's POV draft is inferred in parallel,
    every task reading its own consistent ledger snapshot — parallel tasks see
    stable state, not each other's uncommitted work.
    C-SequentialCommit: verified drafts commit back to the ledger in ranked
    respondent order; at commit time each respondent can react to the earlier
    committed contributions (C-SequentialRespondents)."""
    import threading
    nid = inp.get("needId")
    if not nid:
        return {"ok": False, "served": False, "error": "needId required"}
    st = needs.need_state(ctx, nid)
    if st["status"] != "open":
        return {"ok": False, "served": False, "reason": st["status"]}
    text = inp.get("text") or st["spec"].get("text", "")
    chosen = select_respondents(ctx, text)
    only = inp.get("personaId") or st["spec"].get("personaId")
    if only:
        chosen = [c for c in chosen if c["personaId"] == only] or chosen[:1]
    snap = ctx.ledger.snapshot()
    ctx.append("inference", "inference:snapshot",
               {"snapshotId": snap.id, "rows": snap.stats()["total"],
                "tasks": len(chosen), "needId": nid},
               "model:decision", basis={"kind": "execution"})
    drafts: dict = {}
    def _work(pid, p):
        try:
            drafts[pid] = compose_for(ctx, p, text, snap=snap)
        except Exception as e:
            drafts[pid] = {"text": f"(draft failed: {e})", "stub": True,
                           "engine": "error", "error": repr(e)}
    threads = []
    for c in chosen:
        p = ctx.personas.get(c["personaId"])
        if p:
            t = threading.Thread(target=_work, args=(p["id"], p), daemon=True)
            threads.append(t)
            t.start()
    for t in threads:
        t.join(timeout=180)
    replies = []
    prev_name = None
    for i, c in enumerate(chosen):
        p = ctx.personas.get(c["personaId"])
        if not p:
            continue
        comp = drafts.get(p["id"]) or {"text": "(no draft)", "stub": True,
                                     "engine": "none"}
        # C-SequentialCommit: verify the draft, then commit in ranked order.
        final = comp["text"]
        if prev_name and i > 0:
            reg = _register_of(p)
            final = REGISTERS[reg]["react"](prev_name) + final
        verified = bool(final and final.strip())
        ctx.append("inference", "inference:commit",
                   {"snapshotId": snap.id, "personaId": p["id"],
                    "sequence": i + 1, "verified": verified,
                    "reactsTo": prev_name, "needId": nid},
                   "model:decision", basis={"kind": "execution"})
        if not verified:
            continue
        ctx.invoke("persona.speak",
                   {"personaId": p["id"], "text": final,
                    "cause": "need:response", "engine": comp["engine"],
                    "relates": [st.get("assertionId")]},)
        replies.append({"personaId": p["id"], "name": p["name"],
                        "score": c["score"], "engine": comp["engine"],
                        "register": comp.get("register"),
                        "reactsTo": prev_name, "sequence": i + 1})
        prev_name = p["name"]
        ctx.append("chat", "decision:respondent",
                   {"personaId": p["id"], "sequence": i + 1,
                    "score": c["score"], "needId": nid},
                   "model:decision", basis={"kind": "execution"})
    if not replies:
        ctx.emit("card", {"kind": "persona", "personaId": None,
                          "name": "Meridian", "text":
                          "No respondents on the roster yet — mint a personality "
                          "and I'll answer through it.", "at": now_ms()})
    needs.close_need(ctx, nid, "fulfilled",
                     {"respondents": replies, "served": bool(replies),
                      "snapshotId": snap.id}, "system")
    ctx.append("idle", "idle:drain-fragment",
               {"needId": nid, "respondents": [r["personaId"] for r in replies]},
               "steward:its", basis={"kind": "execution"})
    return {"ok": True, "served": bool(replies), "respondents": replies}


def fn_compose_response(ctx, inp, grant):
    p = ctx.personas.get(inp.get("personaId", ""))
    if not p:
        return {"ok": False, "error": "no personaId"}
    return compose_for(ctx, p, inp.get("text", ""))


def fn_generate_portrait(ctx, inp, grant):
    p = ctx.personas.get(inp["personaId"])
    if not p:
        return {"ok": False, "error": "no persona"}
    from . import art as ART
    r = ART.render_art(ctx, p, os.path.join(ctx.artifacts, "persona-art"))
    ctx.append(f"persona:{p['id']}", "persona:portrait",
               {"artifact": r.get("artifact"), "engine": "inproc-svg-glass",
                "motif": r.get("motif"), "frame": r.get("frame")},
               "engine:portrait", basis={"kind": "execution"})
    p["art"] = {"artifact": r["artifact"], "motif": r["motif"],
                "frame": r["frame"], "dataUrl": r["dataUrl"]}
    ctx.personas._save()
    return {k: v for k, v in r.items() if k != "svg"}


def fn_speak_voice(ctx, inp, grant):
    """Speech render through competing tools (A13). Both render-speech-sapi and
    render-speech-remote express need speech.render; the decision model ranks
    them; failures churn rank and are recorded."""
    text = inp.get("text", "")
    if not text:
        return {"ok": False, "error": "empty text"}
    cands = [t for t in ctx.registry.tools() if t.get("need") == "speech.render"]
    ranked = sorted(cands,
                    key=lambda t: ctx.decision.rank_multiplier(t["id"]) *
                                  ctx.decision.success_rate(t["id"]),
                    reverse=True)
    errors = []
    voice = inp.get("voice")
    if not voice and inp.get("personaId"):
        p = ctx.personas.get(inp["personaId"])
        voice = (p or {}).get("voice")
    for t in ranked:
        r = ctx.invoke(t["id"], {"text": text, "personaId": inp.get("personaId"),
                                 "voice": voice})
        adequate = bool(r.get("ok") and (r.get("result") or {}).get("ok"))
        ctx.decision.record_outcome(t["id"], None, bool(r.get("ok")), adequate)
        if adequate:
            ctx.append("device", "device:voice-render",
                       {"tool": t["id"], "ok": True}, "engine:tts",
                       basis={"kind": "execution"})
            return {"ok": True, "renderedBy": t["id"],
                    "result": r["result"]}
        errors.append({"tool": t["id"], "error": r.get("error")
                       or (r.get("result") or {}).get("error")})
    ctx.append("device", "device:voice-render",
               {"ok": False, "errors": errors}, "engine:tts",
               basis={"kind": "execution"})
    return {"ok": False, "errors": errors,
            "note": "no speech renderer succeeded — recorded, not silent"}


def fn_render_speech_sapi(ctx, inp, grant):
    return ctx.engines.tts.speak_local(inp["text"], voice=inp.get("voice"),
                                       out_wav=inp.get("artifact"))


def fn_render_speech_remote(ctx, inp, grant):
    return ctx.engines.tts.speak_remote(inp["text"])


def fn_run_chat_turn(ctx, inp, grant):
    """Chat entry orchestrator (host-backed, declared). Captures input,
    fills a focused need conversationally when one is on the floor (the need
    stays open until its satisfaction conditions are met), opens tool needs
    for detected intents, stages + drains the response need."""
    text = (inp.get("text") or "").strip()
    if not text:
        return {"ok": False, "error": "empty input"}
    ctx.append("chat", "chat:user-message",
               {"text": text, "all": inp.get("all", False),
                "personaId": inp.get("personaId")},
               "principal", basis={"kind": "captured-input"})
    parsed = fn_parse_chat(ctx, {"text": text}, grant)
    need_ids = []
    for it in parsed["intents"]:
        r = fn_request_tool(ctx, {"toolId": it["toolId"], "slots": it["slots"],
                                  "summary": f"chat: {text[:80]}"}, grant)
        if r.get("needId"):
            need_ids.append(r["needId"])
    # Conversational slot-filling (S-focused-need): while a need is focused,
    # a chat input that opens no stronger intent is offered as a candidate for
    # the focused need's missing required slots; then fulfillment retries.
    focus_result = None
    focus = current_focus(ctx)
    if focus and focus.get("needId"):
        nid = focus["needId"]
        st = needs.need_state(ctx, nid)
        if st["status"] == "open":
            tool = ctx.registry.get(st["spec"].get("toolId") or "")
            missing = []
            if tool:
                gate = T.evaluate_gate(ctx, tool, st["spec"].get("slots", {}),
                                       nid)
                missing = [m for m in gate["missing"]
                           if m["slot"] != "__grant__"]
            offered = []
            for m in missing:
                needs.add_candidate(ctx, nid, m["slot"], text, 0.8,
                                    "conversation", "principal")
                offered.append(m["slot"])
            if offered:
                needs.refine_need(ctx, nid,
                                  f"conversation supplied: {', '.join(offered)}",
                                  "principal", extra={"fromInput": text[:160]})
                fr = T.fulfill_need(ctx, nid)
                focus_result = {"needId": nid, "filled": offered,
                                "fulfill": fr}
                if fr.get("ok"):
                    ctx.append("chat", "chat:focus",
                               {"needId": None, "cleared": "fulfilled"},
                               "system", basis={"kind": "execution"},
                               supersedes=(ctx.ledger.query(
                                   predicate="chat:focus") or [None])[-1].id
                               if ctx.ledger.query(predicate="chat:focus")
                               else None)
        else:
            # need closed — focus released
            prev = ctx.ledger.query(predicate="chat:focus")
            ctx.append("chat", "chat:focus",
                       {"needId": None, "cleared": st["status"]}, "system",
                       basis={"kind": "execution"},
                       supersedes=prev[-1].id if prev else None)
    r_nid = needs.open_need(
        ctx, "response", {"text": text, "all": inp.get("all", False),
                          "topic": current_topic(ctx),
                          "personaId": inp.get("personaId")},
        claimant="principal")
    drain = fn_drain_idle_turn(ctx, {}, grant)
    return {"ok": True, "needIds": need_ids, "responseNeedId": r_nid,
            "drain": drain, "intents": parsed["intents"],
            "focusFill": focus_result}


def fn_steward_tick(ctx, inp, grant):
    """Configurable stewardship pass. Duties are config assertions on
    steward:main (routing:stewardship-assignment) — editable, assignable."""
    t0 = now_ms()
    cfg = (ctx.ledger.query(subject="steward:main",
                            predicate="routing:stewardship-assignment") or [None])
    duties = (cfg[-1].value["v"]["duties"] if cfg[-1] else
              ["drain-needs", "countdown", "calendar-scan",
               "source-confidence", "compact-check", "temporal-attention"])
    report = {"duties": duties, "ran": [], "reason": inp.get("reason", "tick")}
    if "drain-needs" in duties:
        drained = []
        for n in needs.open_needs(ctx, "tool-request"):
            r = T.fulfill_need(ctx, n["id"])
            drained.append({"needId": n["id"], "ok": r.get("ok"),
                            "deferred": r.get("deferred")})
        report["ran"].append({"drain-needs": drained})
    if "countdown" in duties:
        fired = []
        for n in needs.open_needs(ctx, "countdown"):
            due = n["spec"].get("dueAt", 0)
            if due and due <= now_ms():
                action = n["spec"].get("action") or {}
                r = ctx.invoke(action.get("toolId", "surface.card"),
                               action.get("input") or {})
                fired.append({"needId": n["id"], "result": r})
                if action.get("renew"):
                    needs.add_candidate(ctx, n["id"], "dueAt",
                                        now_ms() + int(action["renew"]), 1.0,
                                        "steward:countdown")
                    old_open = ctx.ledger.query(subject=f"need:{n['id']}",
                                                predicate="need:open")[-1]
                    ctx.append(f"need:{n['id']}", "need:open",
                               {**old_open.value["v"],
                                "spec": {**n["spec"], "dueAt": now_ms() + int(action["renew"])}},
                               "steward:its", basis={"kind": "execution"},
                               supersedes=old_open.id)
                else:
                    needs.close_need(ctx, n["id"], "fulfilled", {"fired": True}, "system")
        report["ran"].append({"countdown": fired})
    if "calendar-scan" in duties:
        horizon = now_ms() + 24 * 3600 * 1000
        upcoming = []
        for a in ctx.ledger.query(predicate="calendar:event"):
            v = a.value["v"]
            if v.get("startMs", 0) <= horizon and v.get("startMs", 0) >= now_ms() - 3600e3:
                upcoming.append(v)
        if upcoming:
            ctx.emit("card", {"kind": "offer", "summary": "calendar",
                              "events": upcoming, "at": now_ms()})
        report["ran"].append({"calendar-scan": len(upcoming)})
    if "source-confidence" in duties:
        report["ran"].append({"source-confidence": adjust_source_confidence(ctx)})
    if "temporal-attention" in duties:
        try:
            from . import temporal as T_
            att = T_.steward_attention(ctx)
            if att["findings"]:
                T_.present_attention(ctx, att["findings"])
            report["ran"].append({"temporal-attention": att["context"]})
        except Exception as e:
            report["ran"].append({"temporal-attention": {"error": repr(e)}})
    if "compact-check" in duties:
        budget = int(ctx.config("cleanup:rule", 5000) or 5000)
        if ctx.ledger.stats()["total"] > budget:
            report["ran"].append({"compact-check": ctx.ledger.compact()})
        else:
            report["ran"].append({"compact-check": "under-budget"})
    ms = now_ms() - t0
    ctx.append("idle", "idle:steward-run", {"report": report, "ms": ms},
               "steward:main", basis={"kind": "execution"})
    return {"ok": True, "ms": ms, "report": report}


def adjust_source_confidence(ctx) -> dict:
    """A8: success-driven source confidence adaptation. Sources whose evidence
    fed adequate outcomes gain confidence (bounded); sources tied to repeated
    failures lose it."""
    adjusted = []
    subjects = {a.subjectKey for a in ctx.ledger.query(predicate="source:use")}
    for subj in subjects:
        uses = ctx.ledger.query(subject=subj, predicate="source:use")
        good = sum(1 for u in uses if u.value["v"].get("outcome") == "adequate")
        bad = sum(1 for u in uses if u.value["v"].get("outcome") == "failed")
        if good + bad < 2:
            continue
        cur_rows = ctx.ledger.query(subject=subj, predicate="source:confidence")
        cur = float(cur_rows[-1].value["v"]) if cur_rows else 0.6
        delta = 0.05 * (1 if good > bad else -1)
        new = max(0.1, min(0.95, cur + delta))
        if new != cur:
            ctx.append(subj, "source:confidence", round(new, 3),
                       "steward:main", basis={"kind": "execution"})
            adjusted.append({"source": subj, "from": cur, "to": new})
    return {"adjusted": adjusted}


def fn_validate_tool(ctx, inp, grant):
    return validate_tool_spec(ctx, inp.get("spec") or {})


def validate_tool_spec(ctx, spec: dict) -> dict:
    """A10: novice-author validation — errors, warnings, repair hints."""
    errors, warnings, repairs = [], [], []
    if not spec.get("id") or not re.match(r"^[a-z][a-z0-9-]*$", spec.get("id", "")):
        errors.append("id must be lowercase verb-first dash-separated, e.g. 'find-books'")
    if ctx.registry.get(spec.get("id", "")):
        warnings.append(f"id '{spec['id']}' already registered — minting will replace it")
    tmpl = spec.get("template") or {}
    for s in tmpl.get("slots", []):
        if "name" not in s:
            errors.append("every template slot needs a name")
        if s.get("required") and "minCertainty" not in s:
            warnings.append(f"slot '{s.get('name')}' required but no minCertainty; default 0.7")
    ops = {"set", "query", "search", "view", "candidates", "append", "appendEach",
           "when", "invoke", "invokeEach", "engine", "emit", "repeat", "result", "fail"}
    def walk_steps(steps, path):
        for i, st in enumerate(steps or []):
            op = st.get("op")
            loc = f"{path}[{i}]"
            if op not in ops:
                errors.append(f"{loc}: unknown op '{op}' — allowed: {sorted(ops)}")
                repairs.append(f"{loc}: replace with a supported op or an invoke of a primitive")
            if op == "invoke" and not ctx.registry.get(str(st.get("component", ""))):
                warnings.append(f"{loc}: invokes '{st.get('component')}' which is not registered")
            if op == "when":
                walk_steps(st.get("then"), loc + ".then")
                walk_steps(st.get("else"), loc + ".else")
            if op == "repeat":
                walk_steps(st.get("steps"), loc + ".steps")
    if spec.get("steps"):
        walk_steps(spec["steps"], "steps")
    elif not spec.get("fn"):
        warnings.append("no steps — tool will do nothing until given logic")
    return {"ok": not errors, "errors": errors, "warnings": warnings,
            "repairs": repairs}


def fn_create_tool(ctx, inp, grant):
    return cmd_tool_mint(ctx, {"spec": inp.get("spec") or inp}, grant)


def fn_edit_tool(ctx, inp, grant):
    spec = dict(ctx.registry.get(inp["toolId"]) or {})
    if not spec:
        return {"ok": False, "error": "unknown tool"}
    spec.update(inp.get("patch") or {})
    return cmd_tool_mint(ctx, {"spec": spec}, grant)


def fn_inspect_tool(ctx, inp, grant):
    spec = ctx.registry.get(inp["toolId"])
    if not spec:
        return {"ok": False, "error": "unknown tool"}
    telemetry = [r.value["v"] for r in ctx.ledger.query(
        subject=f"tool:{inp['toolId']}", predicate="tool:telemetry", limit=10)]
    return {"ok": True, "spec": {k: v for k, v in spec.items() if k != "fn"},
            "successRate": ctx.decision.success_rate(inp["toolId"]),
            "rankMultiplier": ctx.decision.rank_multiplier(inp["toolId"]),
            "telemetry": telemetry}


def fn_build_list(ctx, inp, grant):
    """Multi-step list request (demo 4): gather candidates against criteria;
    headers, foreign links, and category errors are recorded as non-matching
    results retained for review and cleanup."""
    criteria = (inp.get("criteria") or "").strip()
    geo = re.search(
        r"(?:all\s+)?(?:the\s+)?(cities|city|towns?|municipalit(?:y|ies)|"
        r"boroughs?|villages?)\s+in\s+([A-Z][A-Za-z .'-]+)$", criteria, re.I)
    if geo and not inp.get("items"):
        from . import setbuild as SB
        kind = geo.group(1).lower()
        kind = {"cities": "city", "city": "city", "municipalities":
                "municipality"}.get(kind, kind.rstrip("s"))
        opened = SB.fn_set_project_open(ctx, {
            "region": geo.group(2).strip().title(), "memberKind": kind,
            "criteria": criteria, "minCount": inp.get("minCount") or 1}, grant)
        collected = SB.fn_set_build_collect(
            ctx, {"needId": opened["needId"]}, grant)
        produced = collected.get("produced") or []
        return {"ok": collected.get("ok", False), "setBuild": True,
                "projectId": opened["projectId"], "needId": opened["needId"],
                "criteria": criteria, "matched": produced,
                "produced": produced, "memberCount": collected.get("memberCount"),
                "artifact": collected.get("artifact"),
                "agreement": collected.get("agreement"),
                "competition": collected.get("competition"),
                "error": collected.get("error")}
    raw = inp.get("items") or []
    if isinstance(raw, str):
        raw = [l.strip() for l in raw.splitlines() if l.strip()]
    nid = inp.get("needId") or needs.open_need(
        ctx, "list-item", {"toolId": "build-list", "summary": criteria,
                           "satisfaction": {"resultTests": [{"truthy": {"$ref": "result.matched"}}]}},
        claimant="principal")
    crit_toks = set(re.findall(r"[a-z0-9']+", criteria.lower()))
    matched, headers, foreign, cat_err = [], [], [], []
    for item in raw:
        s = str(item)
        if re.match(r"^https?://", s) or s.startswith("www."):
            foreign.append(s)
            ctx.append(f"need:{nid}", "need:candidate",
                       {"slot": "foreign-link", "value": s, "confidence": 0.2,
                        "source": "list-input", "class": "foreign-link"},
                       "pipeline:list", certainty=0.2,
                       basis={"kind": "source-evidence"})
        elif re.match(r"^(#+\s|\d+[.)]\s*$|[A-Z][A-Z\s]{4,}:?$)", s) or s.endswith(":"):
            headers.append(s)
            ctx.append(f"need:{nid}", "need:candidate",
                       {"slot": "header", "value": s, "confidence": 0.2,
                        "source": "list-input", "class": "header"},
                       "pipeline:list", certainty=0.2,
                       basis={"kind": "source-evidence"})
        else:
            toks = set(re.findall(r"[a-z0-9']+", s.lower()))
            overlap = len(crit_toks & toks) / max(1, len(crit_toks))
            if overlap >= 0.34 or not crit_toks:
                matched.append(s)
                needs.add_candidate(ctx, nid, "member", s,
                                    round(0.5 + overlap * 0.5, 3), "list-input",
                                    "pipeline:list")
            else:
                cat_err.append(s)
                ctx.append(f"need:{nid}", "need:candidate",
                           {"slot": "category-error", "value": s, "confidence": 0.3,
                            "source": "list-input", "class": "category-error",
                            "reason": "does not match requested criteria"},
                           "pipeline:list", certainty=0.3,
                           basis={"kind": "source-evidence"})
    result = {"criteria": criteria, "matched": matched, "headers": headers,
              "foreignLinks": foreign, "categoryErrors": cat_err}
    if not inp.get("needId"):
        needs.close_need(ctx, nid, "fulfilled", {"result": result}, "system")
    return result


def fn_import_calendar(ctx, inp, grant):
    """Import calendar entries (.ics-ish or JSON list) as source evidence."""
    events = []
    if inp.get("ics"):
        cur = {}
        for line in inp["ics"].splitlines():
            line = line.strip()
            if line == "BEGIN:VEVENT":
                cur = {}
            elif line == "END:VEVENT":
                events.append(cur); cur = {}
            elif line.startswith("SUMMARY"):
                cur["title"] = line.split(":", 1)[1]
            elif line.startswith("DTSTART"):
                cur["start"] = line.split(":", 1)[1]
            elif line.startswith("DTEND"):
                cur["end"] = line.split(":", 1)[1]
    for ev in inp.get("events") or []:
        events.append(ev)
    ids = []
    for ev in events:
        ms = _ics_to_ms(ev.get("start", "")) or ev.get("startMs", 0)
        a = ctx.append("calendar", "calendar:event",
                       {"title": ev.get("title", "(untitled)"), "startMs": ms,
                        "endMs": _ics_to_ms(ev.get("end", "")) or ev.get("endMs", 0),
                        "source": inp.get("source", "ics-import")},
                       "pipeline:calendar", certainty=0.8,
                       basis={"kind": "source-evidence",
                              "ref": inp.get("source", "ics-import")})
        ids.append(a.id)
    ctx.append("calendar", "calendar:imported",
               {"count": len(ids), "source": inp.get("source", "ics-import")},
               "pipeline:calendar", basis={"kind": "source-evidence"})
    return {"imported": len(ids), "events": ids}


def _ics_to_ms(dt: str) -> int:
    import datetime as _dt
    m = re.match(r"(\d{4})(\d{2})(\d{2})(?:T(\d{2})(\d{2}))?", dt or "")
    if not m:
        return 0
    y, mo, d = int(m[1]), int(m[2]), int(m[3])
    hh, mm = int(m[4] or 0), int(m[5] or 0)
    return int(_dt.datetime(y, mo, d, hh, mm).timestamp() * 1000)


def fn_import_exchange(ctx, inp, grant):
    """Storefront/exchange package import: contents recorded below the action
    threshold (claimant exchange:*), resolved through the local ledger."""
    pkg = inp.get("package")
    if isinstance(pkg, str):
        with open(pkg, "r", encoding="utf-8") as f:
            pkg = json.load(f)
    if not isinstance(pkg, dict) or pkg.get("schema") != "meridian.exchange/v1":
        return {"ok": False, "error": "not a meridian.exchange/v1 package"}
    pkg_id = pkg.get("id", new_id("pkg"))
    counts = {"assertions": 0, "personas": 0, "tools": 0, "needs": 0}
    cl = f"exchange:{pkg_id}"
    for a in pkg.get("assertions") or []:
        ctx.append(a.get("subjectKey", "exchange"), a.get("predicate", "exchange:imported"),
                   a.get("value"), cl, certainty=min(0.4, a.get("certainty", 0.4)),
                   basis={"kind": "import", "ref": pkg_id})
        counts["assertions"] += 1
    for p in pkg.get("personas") or []:
        np = ctx.personas.mint(p.get("name", "imported"), p.get("traits") or [],
                               p.get("interests") or [], p.get("lens") or {},
                               p.get("voice"), p.get("imitates"), cl)
        np["confidence"] = 0.3
        np["rosterPriority"] = 0.2
        ctx.personas._save()
        counts["personas"] += 1
    for t in pkg.get("tools") or []:
        spec = dict(t); spec["imported"] = True
        spec.setdefault("kind", "tool")
        ctx.registry.register(spec)
        ctx.append(f"tool:{spec['id']}", "tool:exists",
                   {"id": spec["id"], "imported": True, "endorsed": False}, cl,
                   certainty=0.4, basis={"kind": "import", "ref": pkg_id})
        counts["tools"] += 1
    for n in pkg.get("needs") or []:
        nid = needs.open_need(ctx, n.get("kind", "generic"), n.get("spec", {}),
                              claimant=cl, certainty=0.4)
        counts["needs"] += 1
    ctx.append("exchange", "exchange:imported",
               {"package": pkg_id, "counts": counts,
                "note": "imported below action threshold; resolves through local ledger"},
               cl, certainty=0.4, basis={"kind": "import", "ref": pkg_id})
    return {"ok": True, "package": pkg_id, "counts": counts,
            "threshold": "below-action (0.4 < 0.7)"}


def fn_export_exchange(ctx, inp, grant):
    personas = [p for p in ctx.personas.personas.values()]
    user_tools = [{k: v for k, v in t.items() if k != "fn"}
                  for t in ctx.registry.tools() if t.get("authored")]
    open_needs_list = needs.open_needs(ctx)
    pkg = {"schema": "meridian.exchange/v1", "id": new_id("pkg"),
           "exportedAt": now_ms(), "personas": personas,
           "tools": user_tools, "needs": open_needs_list,
           "assertions": [a.to_row() for a in ctx.ledger.query(
               predicate=inp.get("predicate"))] if inp.get("predicate") else []}
    path = os.path.join(ctx.artifacts, "exports")
    os.makedirs(path, exist_ok=True)
    fpath = os.path.join(path, f"{pkg['id']}.json")
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(pkg, f, indent=2, ensure_ascii=False)
    ctx.append("exchange", "exchange:bundle-draft",
               {"package": pkg["id"], "path": fpath}, "system",
               basis={"kind": "generated"})
    return {"ok": True, "path": fpath, "counts":
            {"personas": len(personas), "tools": len(user_tools),
             "needs": len(open_needs_list)}}


def fn_characterize_persona(ctx, inp, grant):
    """Characterization work for a persona: derive a coherent lens summary
    through the LLM (declared template when stubbed) and assert it."""
    p = ctx.personas.get(inp.get("personaId", ""))
    if not p:
        return {"ok": False, "error": "no persona"}
    prompt = (f"In 2 sentences, characterize a distinct assistant persona named "
              f"{p['name']} whose traits are {p.get('traits')} and interests "
              f"{p.get('interests')}. Third person, crisp.")
    r = ctx.engines.llm.complete(prompt)
    text = r.get("text", "")
    if r.get("stub"):
        text = (f"{p['name']} is a {', '.join(p.get('traits') or ['measured'])} lens "
                f"concerned with {', '.join(p.get('interests') or ['the ledger'])}. "
                f"Presentation style: {p.get('lens', {}).get('style', 'measured')} "
                f"(declared template characterization — llm stub).")
    ctx.append(f"persona:{p['id']}", "persona:characterization",
               {"text": text, "engine": r.get("engine"),
                "stub": bool(r.get("stub"))}, f"persona:{p['id']}",
               basis={"kind": "generated"})
    p.setdefault("lens", {})["summary"] = text
    ctx.personas._save()
    return {"ok": True, "characterization": text,
            "engine": r.get("engine"), "stub": bool(r.get("stub"))}


def fn_persona_onboard(ctx, inp, grant):
    """S-personality-create work stage (canonical): after mint, ensure unique
    art + assigned voice, open and serve the characterization need, then the
    new personality introduces itself through the speech floor."""
    p = ctx.personas.get(inp["personaId"])
    if not p:
        return {"ok": False, "error": "no persona"}
    steps = {}
    if not p.get("art"):
        steps["art"] = fn_generate_portrait(ctx, inp, grant)
    nid = needs.open_need(ctx, "characterization",
                          {"summary": f"characterize {p['name']}",
                           "personaId": p["id"],
                           "toolId": "characterize-persona",
                           "slots": {"personaId": p["id"]},
                           "satisfaction": {}}, claimant="system")
    steps["characterizationNeed"] = nid
    steps["characterized"] = ctx.invoke("characterize-persona",
                                        {"personaId": p["id"], "needId": nid})
    needs.close_need(ctx, nid, "fulfilled",
                     {"toolId": "characterize-persona"}, "system")
    card = ctx.invoke("persona.speak", {
        "personaId": p["id"],
        "text": inp.get("intro") or
                (p["name"] + " here — lens: " +
                 (", ".join(p.get("interests") or ["general"])) +
                 f"; styled {p.get('lens', {}).get('style', 'measured')}."),
        "cause": "onboarding", "engine": "persona-onboard"})
    steps["introCard"] = card.get("result")
    return {"ok": True, "personaId": p["id"], "steps": steps,
            "voice": p.get("voice"), "art": (p.get("art") or {}).get("motif")}


def fn_compare_run(ctx, inp, grant):
    from . import compare as CMP
    return CMP.run_competition(ctx, inp["need"], inp.get("input") or {},
                               need_id=inp.get("needId"))


def fn_connector_configure(ctx, inp, grant):
    from . import connectors as C
    return C.configure(ctx, inp["connector"], inp.get("locator", ""),
                       trust=float(inp.get("trust", 0.8)),
                       extra={k: v for k, v in inp.items()
                              if k in ("args", "mode", "query")})


def fn_connector_run(ctx, inp, grant):
    from . import connectors as C
    return C.run(ctx, inp["connector"], inp.get("input") or {})


def fn_connector_status(ctx, inp, grant):
    from . import connectors as C
    return {"ok": True, "connectors": C.status(ctx),
            "available": sorted(C.CONNECTORS)}


def fn_archive_view(ctx, inp, grant):
    from . import archive as A
    v = A.archive_view(ctx)
    if inp.get("seal"):
        v["sealed"] = A.seal(ctx, reason=inp.get("reason", "requested"))
    return v


def fn_temporal_context(ctx, inp, grant):
    from . import temporal as T_
    return T_.temporal_context(
        ctx, horizon_ms=int(inp.get("horizonDays", 7)) * 86400000)


def fn_persona_voice_set(ctx, inp, grant):
    p = ctx.personas.get(inp["personaId"])
    if not p:
        return {"ok": False, "error": "no persona"}
    voice = dict(p.get("voice") or {})
    voice.update({k: inp[k] for k in ("name", "rate", "pitch", "engine")
                  if k in inp})
    voice["assigned"] = "user-choice"
    p["voice"] = voice
    ctx.personas._save()
    ctx.append(f"persona:{p['id']}", "persona:voice", voice, "principal",
               basis={"kind": "user-choice"})
    ctx.append("speech", "speech:voice-set",
               {"personaId": p["id"], "voice": voice}, "principal",
               basis={"kind": "user-choice"})
    return {"ok": True, "voice": voice, "available": ctx.engines.tts.voices()}


def fn_cleanup_run(ctx, inp, grant):
    """Governed cleanup: compact spent operational rows, preserving provenance,
    then adapt source confidence from outcomes (A8)."""
    t0 = now_ms()
    compact = ctx.ledger.compact()
    adj = adjust_source_confidence(ctx)
    ctx.append("cleanup", "cleanup:run",
               {"compacted": compact, "confidenceAdjusted": adj,
                "ms": now_ms() - t0}, "steward:cleanup",
               basis={"kind": "execution"})
    return {"ok": True, "compacted": compact, "confidence": adj}


# ============================ registry =======================================

# Orchestrator/internal tools — invocable via API/needs but never raised as
# chat intents by the decision model.
_INTERNAL = {
    "run-chat-turn", "parse-chat", "request-tool", "drain-idle-turn",
    "serve-response-need", "select-respondents", "compose-response",
    "speak-voice", "steward-tick", "cancel-need", "arm-countdown",
    "import-calendar", "import-exchange", "export-exchange", "cleanup-run",
    "create-tool", "edit-tool", "validate-tool", "inspect-tool",
    "transcribe-speech", "build-list", "link-calendar", "generate-portrait",
    "record-witness", "render-speech-sapi", "render-speech-remote",
    "assign-stewardship", "persona-onboard", "characterize-persona",
    "persona-voice-set", "set-project-open", "retrieve-set-wiki-table",
    "retrieve-set-wiki-category", "set-build-collect", "compare-run",
    "connector-configure", "connector-run", "connector-status",
    "archive-view", "temporal-context", "chat-reset", "select-context",
    "focus-need", "persona-update",
}


def register_builtins(ctx) -> None:
    reg = ctx.registry

    for pid, fn in PRIMITIVES.items():
        reg.register({"id": pid, "kind": "primitive", "fn": fn,
                      "title": f"primitive {pid}", "editable": False})
    for cid, fn in COMMANDS.items():
        reg.register({"id": cid, "kind": "system-command", "fn": fn,
                      "title": f"command {cid}", "editable": False})

    F = lambda **kw: kw  # spec shorthand

    # ---- chat turn chain ----
    reg.register(F(id="run-chat-turn", fn=fn_run_chat_turn,
        title="Chat turn orchestrator",
        template={"slots": [{"name": "text", "required": True, "widget": "textarea"}]}))
    reg.register(F(id="parse-chat", fn=fn_parse_chat,
        title="Classify input via decision model",
        template={"slots": [{"name": "text", "required": True}]}))
    reg.register(F(id="request-tool", fn=fn_request_tool,
        title="Open a tool-request need",
        triggers={"keywords": [], "patterns": []},
        template={"slots": [{"name": "toolId", "required": True}]}))
    reg.register(F(id="drain-idle-turn", fn=fn_drain_idle_turn,
        title="Drain pending response needs"))
    reg.register(F(id="serve-response-need", fn=fn_serve_response_need,
        title="Serve one response need"))
    reg.register(F(id="select-respondents", fn=lambda c, i, g:
        {"ranked": select_respondents(c, i.get("text", ""), int(i.get("maxN") or 0))},
        title="Rank respondents through the decision model"))
    reg.register(F(id="compose-response", fn=fn_compose_response,
        title="Compose a persona reply through its lens"))
    reg.register(F(id="chat-reset", fn=fn_chat_reset,
        title="Reset the conversation (seal archive, clear context)",
        triggers={"keywords": ["reset conversation", "reset chat",
                               "new conversation"],
                  "patterns": [r"(reset|clear) (the )?(conversation|chat)",
                               r"(start|begin) (a )?new conversation"]}))
    reg.register(F(id="select-context", fn=fn_select_context,
        title="Pull a result item into conversational context",
        template={"slots": [
            {"name": "kind", "required": True, "widget": "select",
             "options": ["email", "profile", "need", "generic"]},
            {"name": "itemId", "required": True}]}))
    reg.register(F(id="focus-need", fn=fn_focus_need,
        title="Focus a need for conversational filling",
        template={"slots": [{"name": "needId", "required": True}]}))
    reg.register(F(id="persona-update", fn=fn_persona_update,
        title="Edit every customizable element of a personality"))

    # ---- chat lane (declarative) ----
    reg.register(F(id="clear-chat", title="Drop a chat boundary marker",
        triggers={"keywords": ["clear chat", "clear the chat"], "patterns": [r"clear (the )?chat"]},
        steps=[{"op": "append", "subject": "chat", "predicate": "chat:cleared",
                "value": "boundary marker — prior rows retained",
                "claimant": "principal", "basis": {"$typed": {"type": "map", "v": {"kind": "user-choice"}}}},
               {"op": "result", "value": "chat cleared"}]))
    reg.register(F(id="set-topic", title="Set the active topic",
        triggers={"keywords": ["topic", "talk about"], "patterns": [r"(?:topic|talk about)\s+(.+)"],
                  "extract": [{"slot": "topic", "pattern": r"(?:topic|talk about)\s+(.+)", "group": 1}]},
        template={"slots": [{"name": "topic", "required": True, "minCertainty": 0.6}]},
        steps=[{"op": "append", "subject": "chat", "predicate": "chat:topic",
                "value": {"$ref": "input.topic"}, "claimant": "principal",
                "basis": {"$typed": {"type": "map", "v": {"kind": "user-choice"}}}},
               {"op": "result", "value": {"$ref": "input.topic"}}]))
    reg.register(F(id="close-topic", title="Close the active topic",
        triggers={"keywords": ["close topic", "end topic"], "patterns": [r"(close|end) (the )?topic"]},
        steps=[{"op": "query", "into": "t", "predicate": "chat:topic", "limit": 1},
               {"op": "when", "if": {"truthy": {"$ref": "t"}},
                "then": [{"op": "append", "subject": "chat", "predicate": "chat:topic",
                          "value": "", "claimant": "principal",
                          "supersedes": {"$get": [{"$first": {"$ref": "t"}}, "id"]}}]},
               {"op": "result", "value": "topic closed"}]))
    reg.register(F(id="set-response-depth", title="Set max respondents",
        template={"slots": [{"name": "value", "required": True, "widget": "select",
                             "options": [1, 2, 3, 4]}]},
        steps=[{"op": "append", "subject": "user-settings", "predicate": "chat:response-depth",
                "value": {"$int": {"$ref": "input.value"}}, "claimant": "principal"},
               {"op": "result", "value": {"$ref": "input.value"}}]))
    reg.register(F(id="set-persona-frame", title="Persona presentation frame (A12)",
        template={"slots": [{"name": "value", "required": True, "widget": "select",
                             "options": ["respondent", "personified"],
                             "hint": "non-anthropomorphic lenses vs personified display"}]},
        steps=[{"op": "append", "subject": "user-settings", "predicate": "user:persona-frame",
                "value": {"$ref": "input.value"}, "claimant": "principal"},
               {"op": "result", "value": {"$ref": "input.value"}}]))
    reg.register(F(id="set-editor-proficiency", title="Editor proficiency tier",
        template={"slots": [{"name": "value", "required": True, "widget": "select",
                             "options": ["use", "slots", "wire", "raw"]}]},
        steps=[{"op": "append", "subject": "user-settings", "predicate": "user:editor-proficiency",
                "value": {"$ref": "input.value"}, "claimant": "principal"},
               {"op": "result", "value": {"$ref": "input.value"}}]))

    # ---- persona tools ----
    reg.register(F(id="create-persona", title="Mint a personality",
        triggers={"keywords": ["create persona", "new persona", "create personality",
                               "mint persona", "create avatar", "new avatar"],
                  "patterns": [r"(?:create|new|mint)\s+(?:a\s+)?(?:persona|personality|avatar)\s+(?:named|called)?\s*(.*)"],
                  "extract": [{"slot": "name", "pattern": r"(?:named|called)\s+([\w .'-]+)", "group": 1}]},
        template={"slots": [
            {"name": "name", "required": True, "minCertainty": 0.6, "widget": "text"},
            {"name": "traits", "required": False, "widget": "badge-list"},
            {"name": "interests", "required": False, "widget": "badge-list"},
            {"name": "style", "required": False, "widget": "select",
             "options": ["measured", "warm", "terse", "playful", "formal"]},
            {"name": "imitates", "required": False, "widget": "text",
             "hint": "recognizable figure this imitates (optional)"},
            {"name": "imitationRecency", "required": False, "widget": "select",
             "options": ["living", "deceased-10y", "deceased-older", "fictional"]}]},
        steps=[
            {"op": "when", "if": {"truthy": {"$ref": "input.imitates"}},
             "then": [{"op": "set", "into": "imit",
                       "value": {"name": {"$ref": "input.imitates"},
                                 "recency": {"$coalesce": [{"$ref": "input.imitationRecency"}, "living"]}}}],
             "else": [{"op": "set", "into": "imit", "value": None}]},
            {"op": "invoke", "component": "persona.mint", "into": "minted",
             "input": {"name": {"$ref": "input.name"},
                       "traits": {"$coalesce": [{"$ref": "input.traits"}, []]},
                       "interests": {"$coalesce": [{"$ref": "input.interests"}, []]},
                       "lens": {"style": {"$coalesce": [{"$ref": "input.style"}, "measured"]}},
                       "imitates": {"$ref": "imit"},
                       "claimant": "principal"}},
            {"op": "invoke", "component": "generate-portrait",
             "input": {"personaId": {"$get": [{"$ref": "minted"}, "personaId"]}}},
            {"op": "invoke", "component": "persona-onboard",
             "input": {"personaId": {"$get": [{"$ref": "minted"}, "personaId"]}}},
            {"op": "result", "value": {"$ref": "minted"}}]))
    reg.register(F(id="edit-persona", title="Edit a personality",
        template={"slots": [
            {"name": "personaId", "required": True},
            {"name": "name", "required": False}, {"name": "traits", "required": False},
            {"name": "interests", "required": False},
            {"name": "rosterPriority", "required": False}]},
        fn=lambda c, i, g: {"ok": True, "persona":
            c.personas.update(i["personaId"],
                              {k: i[k] for k in ("name", "traits", "interests",
                                                 "rosterPriority") if k in i})}))
    reg.register(F(id="generate-portrait", title="Render persona portrait",
        template={"slots": [{"name": "personaId", "required": True}]},
        fn=fn_generate_portrait))

    # ---- speech (competing tools, A13) ----
    reg.register(F(id="speak-voice", fn=fn_speak_voice, title="Speak text (ranks renderers)"))
    reg.register(F(id="render-speech-sapi", fn=fn_render_speech_sapi,
        title="Local speech render (Windows SAPI)", need="speech.render",
        template={"slots": [{"name": "text", "required": True}]}))
    reg.register(F(id="render-speech-remote", fn=fn_render_speech_remote,
        title="Remote speech render (unconfigured until granted)", need="speech.render",
        template={"slots": [{"name": "text", "required": True},
                            {"name": "endpoint", "required": False}]}))

    # ---- needs / stewardship ----
    reg.register(F(id="steward-tick", fn=fn_steward_tick,
        title="Configurable stewardship pass"))
    reg.register(F(id="assign-stewardship", title="Configure steward duties (A3/D-IdleTurnAsTool)",
        template={"slots": [
            {"name": "duties", "required": True, "widget": "badge-list",
             "hint": "drain-needs, countdown, calendar-scan, source-confidence, compact-check"},
            {"name": "intervalSec", "required": False}]},
        steps=[{"op": "append", "subject": "steward:main",
                "predicate": "routing:stewardship-assignment",
                "value": {"duties": {"$ref": "input.duties"},
                          "intervalSec": {"$coalesce": [{"$ref": "input.intervalSec"}, 15]}},
                "claimant": "principal", "basis": {"$typed": {"type": "map", "v": {"kind": "config"}}}},
               {"op": "result", "value": {"$ref": "input.duties"}}]))
    reg.register(F(id="cancel-need", title="Cancel an open need",
        template={"slots": [{"name": "needId", "required": True}]},
        fn=lambda c, i, g: {"ok": True, "closed": needs.close_need(
            c, i["needId"], "cancelled", {"by": "user"}, "principal")}))
    reg.register(F(id="arm-countdown", title="Arm a countdown need",
        template={"slots": [{"name": "inSec", "required": True},
                            {"name": "label", "required": True}]},
        fn=lambda c, i, g: {"ok": True, "needId": needs.open_need(
            c, "countdown", {"dueAt": now_ms() + int(float(i["inSec"]) * 1000),
                             "label": i["label"],
                             "action": {"toolId": "surface.card",
                                        "input": {"kind": "offer",
                                                  "payload": {"summary": i["label"]}}}},
            claimant="principal")}))

    # ---- search / sources / intent ----
    reg.register(F(id="run-search", title="Search ledger + configured sources",
        triggers={"keywords": ["search", "find", "look up"], "patterns": [r"(?:search|find|look up)\s+(?:for\s+)?(.+)"],
                  "extract": [{"slot": "query", "pattern": r"(?:search|find|look up)\s+(?:for\s+)?(.+)", "group": 1}]},
        template={"slots": [{"name": "query", "required": True, "minCertainty": 0.5},
                            {"name": "topK", "required": False}]},
        fn=lambda c, i, g: _run_search(c, i)))
    reg.register(F(id="interpret-intent", title="Author a durable intent override",
        template={"slots": [{"name": "pattern", "required": True},
                            {"name": "toolId", "required": True},
                            {"name": "confidence", "required": False}]},
        steps=[{"op": "append", "subject": "routing", "predicate": "routing:intent-override",
                "value": {"pattern": {"$ref": "input.pattern"},
                          "toolId": {"$ref": "input.toolId"},
                          "confidence": {"$coalesce": [{"$ref": "input.confidence"}, 0.9]}},
                "claimant": "principal", "basis": {"$typed": {"type": "map", "v": {"kind": "user-choice"}}}},
               {"op": "result", "value": "override recorded"}]))
    reg.register(F(id="endorse-source", title="Endorse a source (raises inherited confidence)",
        template={"slots": [{"name": "sourceId", "required": True},
                            {"name": "confidence", "required": True},
                            {"name": "trustClass", "required": False, "widget": "select",
                             "options": ["endorsed", "configured", "observed", "unvetted"]}]},
        steps=[{"op": "append", "subject": {"$tpl": "source:{input.sourceId}"},
                "predicate": "source:trust-class",
                "value": {"$coalesce": [{"$ref": "input.trustClass"}, "endorsed"]},
                "claimant": "principal", "basis": {"$typed": {"type": "map", "v": {"kind": "user-choice"}}}},
               {"op": "append", "subject": {"$tpl": "source:{input.sourceId}"},
                "predicate": "source:confidence",
                "value": {"$ref": "input.confidence"}, "claimant": "principal"},
               {"op": "result", "value": {"$ref": "input.sourceId"}}]))
    reg.register(F(id="configure-source", title="Ratify a configured read source",
        template={"slots": [{"name": "sourceId", "required": True},
                            {"name": "kind", "required": True},
                            {"name": "locator", "required": False}]},
        steps=[{"op": "append", "subject": {"$tpl": "source:{input.sourceId}"},
                "predicate": "source:configured",
                "value": {"kind": {"$ref": "input.kind"},
                          "locator": {"$ref": "input.locator"}},
                "claimant": "principal", "basis": {"$typed": {"type": "map", "v": {"kind": "config"}}}},
               {"op": "result", "value": {"$ref": "input.sourceId"}}]))

    # ---- witness / speech capture ----
    reg.register(F(id="record-witness", title="Record a perception capture",
        template={"slots": [{"name": "kind", "required": True},
                            {"name": "detail", "required": False}]},
        steps=[{"op": "append", "subject": "device", "predicate": "device:input-capture",
                "value": {"kind": {"$ref": "input.kind"}, "detail": {"$ref": "input.detail"}},
                "claimant": "surface:ui", "basis": {"$typed": {"type": "map", "v": {"kind": "source-evidence"}}}},
               {"op": "result", "value": "witness recorded"}]))
    reg.register(F(id="transcribe-speech", title="Record a speech transcript witness",
        template={"slots": [{"name": "transcript", "required": True},
                            {"name": "confidence", "required": True}]},
        steps=[{"op": "append", "subject": "device", "predicate": "device:speech-transcript",
                "value": {"transcript": {"$ref": "input.transcript"},
                          "confidence": {"$ref": "input.confidence"}},
                "claimant": "engine:stt", "certainty": {"$ref": "input.confidence"},
                "basis": {"$typed": {"type": "map", "v": {"kind": "captured-input"}}}},
               {"op": "invoke", "component": "run-chat-turn",
                "input": {"text": {"$ref": "input.transcript"}}, "into": "turn"},
               {"op": "result", "value": {"$ref": "turn"}}]))

    # ---- projects / calendar / lists ----
    reg.register(F(id="create-project", title="Create a project (prominent affordance)",
        triggers={"keywords": ["create project", "new project", "start a project"],
                  "patterns": [r"(?:create|new|start)\s+(?:a\s+)?project\s*(?:called|named)?\s*(.*)"],
                  "extract": [{"slot": "title", "pattern": r"(?:called|named)\s+(.+)", "group": 1}]},
        template={"slots": [{"name": "title", "required": True, "minCertainty": 0.5},
                            {"name": "goals", "required": False, "widget": "badge-list"},
                            {"name": "kind", "required": False}]},
        fn=lambda c, i, g: _create_project(c, i)))
    reg.register(F(id="import-calendar", fn=fn_import_calendar,
        title="Import calendar entries as source evidence"))
    reg.register(F(id="build-list", fn=fn_build_list,
        title="Build a criteria-governed list (demo 4)",
        triggers={"keywords": ["list", "make a list", "collect"],
                  "patterns": [r"(?:list|collect)\s+(?:of\s+)?(.+)"],
                  "extract": [{"slot": "criteria", "pattern": r"(?:list|collect)\s+(?:of\s+)?(.+)", "group": 1}]},
        template={"slots": [{"name": "criteria", "required": True, "minCertainty": 0.4},
                            {"name": "items", "required": False, "widget": "textarea"}]}))
    reg.register(F(id="link-calendar", title="Relate a calendar event to a project",
        template={"slots": [{"name": "projectId", "required": True},
                            {"name": "eventAssertionId", "required": True}]},
        steps=[{"op": "append", "subject": {"$tpl": "project:{input.projectId}"},
                "predicate": "calendar:linked",
                "value": {"$ref": "input.eventAssertionId"}, "claimant": "principal",
                "relates": {"$list": [{"$ref": "input.eventAssertionId"}]}},
               {"op": "result", "value": "linked"}]))

    # ---- grant-gated vessels (nonlocal/consequential effects) ----
    reg.register(F(id="send-mail", title="Queue mail via outbox (grant-gated)",
        triggers={"keywords": ["email", "send mail", "mail"], "patterns": [r"(?:email|mail)\s+(.+?)\s+(?:about|that)\s+(.+)"],
                  "extract": [{"slot": "to", "pattern": r"(?:email|mail)\s+([\w@.\-]+)", "group": 1},
                              {"slot": "body", "pattern": r"(?:about|that|saying)\s+(.+)", "group": 1}]},
        template={"slots": [{"name": "to", "required": True},
                            {"name": "subject", "required": False},
                            {"name": "body", "required": True}],
                  "grant": {"scope": "mail.send", "lock": None}},
        steps=[{"op": "invoke", "component": "mail.outbox_write", "into": "sent",
                "input": {"to": {"$ref": "input.to"},
                          "subject": {"$coalesce": [{"$ref": "input.subject"}, "from Meridian"]},
                          "body": {"$ref": "input.body"}}},
               {"op": "append", "subject": "feedback", "predicate": "feedback:sent",
                "value": {"to": {"$ref": "input.to"}, "artifact": {"$get": [{"$ref": "sent"}, "queued"]}},
                "claimant": "tool:send-mail", "basis": {"$typed": {"type": "map", "v": {"kind": "execution"}}}},
               {"op": "result", "value": {"$ref": "sent"}}]))
    reg.register(F(id="dispatch-home-routine", title="Actuate a home routine (grant-gated)",
        template={"slots": [{"name": "device", "required": True},
                            {"name": "routine", "required": True}],
                  "grant": {"scope": "home.actuate", "lock": None}},
        steps=[{"op": "invoke", "component": "home.dispatch_routine",
                "input": {"device": {"$ref": "input.device"}, "routine": {"$ref": "input.routine"}},
                "into": "r"},
               {"op": "result", "value": {"$ref": "r"}}]))
    reg.register(F(id="publish-milestone", title="Publish a milestone (grant-gated)",
        template={"slots": [{"name": "target", "required": True},
                            {"name": "content", "required": True}],
                  "grant": {"scope": "publish.creator", "lock": None}},
        steps=[{"op": "invoke", "component": "creator_feed.publish",
                "input": {"target": {"$ref": "input.target"}, "content": {"$ref": "input.content"}},
                "into": "r"},
               {"op": "result", "value": {"$ref": "r"}}]))

    # ---- exchange / cleanup ----
    reg.register(F(id="import-exchange", fn=fn_import_exchange,
        title="Import a storefront/exchange package below threshold"))
    reg.register(F(id="export-exchange", fn=fn_export_exchange,
        title="Export an exchange package"))
    reg.register(F(id="cleanup-run", fn=fn_cleanup_run,
        title="Governed consolidation + confidence adaptation"))

    # ---- personas onboarding / characterization (S-personality-create) ----
    reg.register(F(id="characterize-persona", fn=fn_characterize_persona,
        title="Generate persona characterization through its lens"))
    reg.register(F(id="persona-onboard", fn=fn_persona_onboard,
        title="Personality onboarding: art + voice + characterization + intro"))
    reg.register(F(id="persona-voice-set", fn=fn_persona_voice_set,
        title="Modify a persona's voice settings (C-VoiceDiversity)",
        template={"slots": [{"name": "personaId", "required": True},
                            {"name": "name", "required": False},
                            {"name": "rate", "required": False}]}))

    # ---- set-build / competing retrieval (C-SetBuild, F3) ----
    reg.register(F(id="set-project-open", fn=SB.fn_set_project_open,
        title="Open a set-fulfillment project + governing need"))
    reg.register(F(id="retrieve-set-wiki-table",
        fn=SB.fn_retrieve_wiki_table,
        title="Set retrieval: canonical list-page table (live Wikipedia)",
        need="set.members"))
    reg.register(F(id="retrieve-set-wiki-category",
        fn=SB.fn_retrieve_wiki_category,
        title="Set retrieval: category membership API (live Wikipedia)",
        need="set.members"))
    reg.register(F(id="set-build-collect", fn=SB.fn_set_build_collect,
        title="Compare retrievals + close the set into an artifact"))
    reg.register(F(id="compare-run", fn=fn_compare_run,
        title="Run a competition over every tool expressing a need (F3)"))

    # ---- connectors (F8) ----
    reg.register(F(id="connector-configure", fn=fn_connector_configure,
        title="Configure a connector (locator + trust)"))
    reg.register(F(id="connector-run", fn=fn_connector_run,
        title="Run a connector ingest end-to-end"))
    reg.register(F(id="connector-status", fn=fn_connector_status,
        title="Configured connectors + last run"))

    # ---- archive / temporal ----
    reg.register(F(id="archive-view", fn=fn_archive_view,
        title="Conversation archive: segments + per-turn rows"))
    reg.register(F(id="temporal-context", fn=fn_temporal_context,
        title="Temporal interpretation of calendar evidence"))

    # ---- tool authoring (A10) ----
    reg.register(F(id="create-tool", fn=fn_create_tool, title="Author a new tool",
        template={"slots": [{"name": "spec", "required": True, "widget": "textarea",
                             "hint": "JSON spec: id, title, template.slots, steps, triggers"}]}))
    reg.register(F(id="edit-tool", fn=fn_edit_tool, title="Edit a tool definition"))
    reg.register(F(id="validate-tool", fn=fn_validate_tool,
        title="Validate a tool spec (errors + repair hints)"))
    reg.register(F(id="inspect-tool", fn=fn_inspect_tool,
        title="Inspect a tool: spec, success rate, telemetry"))


    for tid in _INTERNAL:
        spec = reg.get(tid)
        if spec:
            spec["internal"] = True


def _run_search(ctx, i):
    q = i.get("query", "")
    hits = ctx.ledger.search(q, int(i.get("topK") or 10))
    for a in hits:
        ctx.append(f"source:{a.claimant}", "source:use",
                   {"query": q, "assertionId": a.id}, "steward:its",
                   basis={"kind": "execution"})
    adequate = len(hits) > 0
    ctx.append("search", "search:run", {"query": q, "hits": len(hits)},
               "tool:run-search", basis={"kind": "execution"})
    ctx.append("search", "search:adequacy",
               {"query": q, "adequate": adequate, "hits": len(hits)},
               "tool:run-search", basis={"kind": "execution"})
    return {"ok": adequate, "query": q, "hits": [h.to_row() for h in hits],
            "adequate": adequate}


def _create_project(ctx, i):
    pid = new_id("proj")
    subj = f"project:{pid}"
    title = i.get("title") or "untitled project"
    ctx.append(subj, "project:exists", {"title": title}, "principal",
               basis={"kind": "user-choice"})
    ctx.append(subj, "project:title", title, "principal")
    ctx.append(subj, "project:kind", i.get("kind") or "general", "principal")
    ctx.append(subj, "project:status", "open", "principal")
    goal_ids = []
    for gtext in (i.get("goals") or []):
        a = ctx.append(subj, "project:goal", {"text": gtext, "status": "open"},
                       "principal")
        goal_ids.append(a.id)
        needs.open_need(ctx, "generic",
                        {"summary": gtext, "project": pid,
                         "satisfaction": {}},
                        claimant="principal", relates=[a.id])
    ctx.emit("card", {"kind": "witness", "summary": f"project created: {title}",
                      "projectId": pid, "at": now_ms()})
    return {"ok": True, "projectId": pid, "goals": goal_ids}
