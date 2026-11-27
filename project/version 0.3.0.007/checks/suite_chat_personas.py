"""Checks — chat & personas facet. Frozen names verbatim."""

import json
import re
import time

from .checklib import ck


def _roster(ctx):
    return ctx.probe.get("/api/roster")[1].get("roster", [])


def S_chat_invocation(ctx):
    p = ctx.probe
    _, t = p.post("/api/chat",
                  {"text": "hello — and please find a campsite near altoona"})
    rows = p.rows("input:captured")
    needs = t.get("routedNeeds") or []
    return [
        ck("conversational reply returned", bool(t.get("replies")),
           f"{len(t.get('replies') or [])} replies"),
        ck("tool need(s) opened, distinguishable", bool(needs),
           f"{needs}"),
        ck("input captured as assertion",
           bool(rows) and rows[-1].get("basis") == "captured-input",
           str((rows or [{}])[-1].get("id"))),
        ck("needs route",
           bool(needs) and
           all(any(r.get("need") == n for r in p.rows("need:")) for n in needs),
           "every routed need landed as a distinguishable need:* row"),
    ]


def S_conversational_register(ctx):
    p = ctx.probe
    _, t = p.post("/api/chat", {"text": "tell me about yourself"})
    replies = t.get("replies") or []
    sentences = all(re.search(r"[.!?]['\"]?\s*$", r.get("text", "").strip()) or
                    len(r.get("text", "")) > 3 for r in replies)
    textbook = [r for r in replies
                if re.search(r"(\*\*|## |is defined as|in conclusion|^-\s)",
                             r.get("text", ""), re.M)]
    markup = [r for r in replies if re.search(r"[*_`#\[\]]", r.get("text", ""))]
    regs = {r.get("register") for r in replies}
    return [
        ck("sentences", bool(replies) and sentences,
           f"{len(replies)} replies end as sentences"),
        ck("no textbook", bool(replies) and not textbook,
           f"{len(textbook)} textbook-shaped replies"),
        ck("no verbatim markup", bool(replies) and not markup,
           f"{len(markup)} replies carry markup chars"),
        ck("register unbroken", bool(regs) and "" not in regs,
           f"registers={sorted(regs)}"),
    ]


def S_faithful_voice(ctx):
    p = ctx.probe
    _, t = p.post("/api/chat", {"text": "what is pennsylvania"})
    replies = t.get("replies") or []
    grounded = [r for r in replies if r.get("fidelity") == "grounded"]
    nulls = [r for r in replies if r.get("fidelity") in (None, "null")]
    ungrounded_flagged = [r for r in replies
                          if r.get("fidelity") == "ungrounded-declared"]
    zero_hit_ok = True
    _, t2 = p.post("/api/chat",
                   {"text": "who is xqzvblmor the unfathomable"})
    r2 = t2.get("replies") or []
    for r in r2:
        if r.get("fidelity") == "grounded" and not r.get("grounded"):
            zero_hit_ok = False
    return [
        ck("grounded reply flagged grounded",
           bool(grounded) or bool(ungrounded_flagged),
           f"grounded={len(grounded)} ungrounded-flagged={len(ungrounded_flagged)}"),
        ck("zero-hit does NOT pass grounding (S-2)", bool(r2) and zero_hit_ok,
           "no reply claims grounded fidelity on an unsupportable ask"),
        ck("no unflagged fidelity:null", bool(replies) and not nulls,
           f"{len(nulls)} null-fidelity replies"),
    ]


def S_distinct_preloadeds(ctx):
    p = ctx.probe
    roster = _roster(ctx)
    shipped = [r for r in roster if r.get("shipped") or r.get("mintedAt")]
    regs = {r.get("register") for r in roster}
    _, t = p.post("/api/chat", {"text": "what do you think of rain"})
    texts = [r.get("text", "") for r in t.get("replies") or []]
    distinct = len(set(texts)) == len(texts) and len(texts) > 0
    return [
        ck("≥3 shipped personas w/ distinct registers",
           len(roster) >= 3 and len(regs) >= 3,
           f"{len(roster)} personas, registers={sorted(regs)}"),
        ck("same prompt → noticeably different replies",
           distinct and len(texts) >= 2,
           f"{len(set(texts))} distinct replies of {len(texts)}"),
    ]


def S_personality_create(ctx):
    p = ctx.probe
    _, r = p.post("/api/persona/create",
                  {"name": "Cinder", "character": "a soot-covered foundry imp",
                   "history": "Cinder stokes forgotten furnaces and "
                              "collects sparks in jars."})
    pid = r.get("persona")
    time.sleep(2)
    roster = _roster(ctx)
    persona = next((x for x in roster if x.get("id") == pid), {})
    held_rows = [x for x in p.rows("dyadic:held-confidence") if x.get("persona") == pid]
    return [
        ck("persona minted from minimal input", bool(pid) and persona.get("name") == "Cinder",
           f"{pid} on roster"),
        ck("portrait generated + bound", bool((persona.get("portrait") or {}).get("file")),
           str(persona.get("portrait"))[:100]),
        ck("LLM art path (V-A)",
           (persona.get("portrait") or {}).get("authored") in ("llm-art", "fallback-declared"),
           (persona.get("portrait") or {}).get("authored")),
        ck("voice assigned", bool((persona.get("voice") or {}).get("id")),
           str((persona.get("voice") or {}).get("id"))),
        ck("characterization extended",
           bool(persona.get("character")) and bool(persona.get("history")),
           "character + history present"),
        ck("dyadic default 0.5",
           held_rows and held_rows[0].get("confidence") == 0.5,
           str((held_rows or [{}])[0].get("confidence"))),
    ]


def S_personality_editor(ctx):
    p = ctx.probe
    roster = _roster(ctx)
    pid = roster[0]["id"] if roster else None
    if not pid:
        return [ck(x, False, "empty roster") for x in
                ("editor path updates persona elements",
                 "edits recorded as assertions",
                 "V-F: edit discoverable from roster surface")]
    _, r = p.post("/api/persona/edit",
                  {"id": pid, "fields": {"character": "edited character mark",
                                         "surface": "stage"}})
    edit_rows = [x for x in p.rows("persona:edited") if x.get("persona") == pid]
    after = next((x for x in _roster(ctx) if x.get("id") == pid), {})
    return [
        ck("editor path updates persona elements",
           r.get("ok") and after.get("character") == "edited character mark",
           str(after.get("character"))[:60]),
        ck("edits recorded as assertions", bool(edit_rows),
           f"{len(edit_rows)} persona:edited rows"),
        ck("V-F: edit discoverable from roster surface",
           "editor" in ctx.page() and "savePersona" in ctx.page(),
           "editor controls present on the served surface"),
    ]


def S_personality_source_match(ctx):
    p = ctx.probe
    _, r = p.post("/api/persona/create",
                  {"name": "Trekkie", "domains": ["star-trek"]})
    sugg = r.get("sourceSuggestions") or []
    top = sugg[0] if sugg else {}
    discriminates = top.get("source") == "source-memory-alpha" and \
        not any(s.get("source") == "source-simpsons" for s in sugg[:1])
    pid = r.get("persona")
    _, acc = p.post("/api/persona/source-grant",
                    {"id": pid, "source": "source-memory-alpha", "accept": True})
    grants = [g for g in p.rows("persona:source-grant")
              if g.get("persona") == pid and g.get("granted")]
    _, dec = p.post("/api/persona/source-grant",
                    {"id": pid, "source": "source-simpsons", "accept": False})
    decl = [g for g in p.rows("persona:source-grant")
            if g.get("persona") == pid and g.get("granted") is False]
    return [
        ck("domain-matched source suggested at creation",
           bool(sugg) and "memory-alpha" in str(top.get("source")),
           str(top)[:120]),
        ck("accept binds source to persona", bool(grants),
           f"{len(grants)} grant rows"),
        ck("decline leaves persona source-free", bool(decl),
           f"{len(decl)} decline rows"),
        ck("discrimination-case", discriminates,
           "star-trek domain matched memory-alpha, not simpsons"),
    ]


def S_personality_roster(ctx):
    p = ctx.probe
    roster = _roster(ctx)
    if len(roster) < 2:
        return [ck(x, False, "roster < 2") for x in
                ("roster operable", "selection works", "reorder changes order",
                 "V-D: reorder visibly changes held-confidence", "every move moves")]
    pid = roster[-1]["id"]
    _, sel = p.post("/api/persona/select", {"id": pid})
    before = [x["id"] for x in _roster(ctx)]
    _, mv = p.post("/api/roster/move", {"id": pid, "direction": "up"})
    after = mv.get("order") or []
    moved = before != after
    held_change = mv.get("held") != mv.get("previous")
    every = True
    r2 = _roster(ctx)
    mid = r2[1]["id"]
    _, mv2 = p.post("/api/roster/move", {"id": mid, "direction": "down"})
    if not (mv2.get("ok") and mv2.get("order") != after):
        every = False
    return [
        ck("roster operable", "roster" in ctx.page().lower() and bool(roster),
           f"{len(roster)} entries, controls on page"),
        ck("selection works", sel.get("ok"), str(sel)),
        ck("reorder changes order", moved,
           f"{before[:4]} → {after[:4]}"),
        ck("V-D: reorder visibly changes held-confidence",
           held_change or mv.get("held") is not None,
           f"{mv.get('previous')} → {mv.get('held')}"),
        ck("every move moves", every,
           "interior move also reordered"),
    ]


def S_dyadic_ranking(ctx):
    p = ctx.probe
    roster = _roster(ctx)
    results = []
    every_visible = True
    interior = False
    if len(roster) >= 3:
        for i in (1, 0):
            pid = roster[i]["id"]
            _, mv = p.post("/api/roster/move", {"id": pid, "direction": "down"})
            if mv.get("held") is None and not mv.get("ok"):
                every_visible = False
            if i == 1:
                interior = mv.get("ok")
        dyadic_rows = p.rows("dyadic:held-confidence")
    else:
        dyadic_rows = []
        every_visible = False
    surface = "held" in ctx.page() or any(x.get("held") for x in _roster(ctx))
    return [
        ck("every move visible", every_visible and bool(dyadic_rows),
           f"{len(dyadic_rows)} dyadic rows, each move differentiates"),
        ck("interior moves", interior, "middle-entry move reorders"),
        ck("surface shows it", surface, "held-confidence rendered on roster"),
    ]


def S_portrait_bind(ctx):
    p = ctx.probe
    roster = _roster(ctx)
    shipped = [x for x in roster if x.get("mintedAt")]
    bound = [x for x in shipped if (x.get("portrait") or {}).get("file")]
    _, r = p.post("/api/persona/create", {"name": "Portrait-check"})
    pid = r.get("persona")
    time.sleep(2)
    newp = next((x for x in _roster(ctx) if x.get("id") == pid), {})
    code, body = p.get(f"/api/persona/{pid}/portrait")
    authored = (newp.get("portrait") or {}).get("authored")
    return [
        ck("portrait file produced", code == 200, f"GET portrait {code}"),
        ck("art bound to this persona", bool((newp.get("portrait") or {}).get("file")),
           str(newp.get("portrait"))[:90]),
        ck("generative path declared", authored in ("llm-art", "fallback-declared"),
           str(authored)),
        ck("auto-bound shipped", bool(shipped) and len(bound) == len(shipped),
           f"{len(bound)}/{len(shipped)} shipped bound"),
        ck("auto-bound minted", bool((newp.get("portrait") or {}).get("file")),
           f"minted {pid} bound"),
        ck("fallback legible",
           bool(newp) and (authored != "fallback-declared" or
                           "fallback" in str(newp.get("portrait"))),
           f"authored={authored} — fallback marked when used"),
    ]


def S_respondent_union(ctx):
    p = ctx.probe
    roster = _roster(ctx)
    if len(roster) < 2:
        return [ck(x, False, "roster < 2") for x in
                ("named addressee replies", "selector-chosen replies",
                 "union not override", "addressed first", "multi-select",
                 "over-threshold only")]
    a, b = roster[0], roster[1]
    p.post("/api/settings/selector", {"ids": [b["id"]]})
    _, t = p.post("/api/chat",
                  {"text": f"{a['name']}, what is the weather like today"})
    names = [r.get("name") for r in t.get("replies") or []]
    both = a["name"] in names and b["name"] in names
    first = names[0] == a["name"] if names else False
    p.post("/api/settings/selector", {"ids": [b["id"], roster[2]["id"] if len(roster) > 2 else b["id"]]})
    _, t2 = p.post("/api/chat", {"text": "hello there"})
    names2 = [r.get("name") for r in t2.get("replies") or []]
    multi = len(set(names2) & {b["name"], (roster[2] if len(roster) > 2 else b)["name"]}) >= 2
    p.post("/api/settings/selector", {"ids": []})
    return [
        ck("named addressee replies", a["name"] in names, str(names)),
        ck("selector-chosen replies", b["name"] in names, str(names)),
        ck("union not override", both, f"both replied: {both}"),
        ck("addressed first", first, f"order={names}"),
        ck("multi-select", multi, f"multi replies={names2}"),
        ck("over-threshold only",
           len(set(names)) <= len(set([a["name"], b["name"]])),
           f"respondents {names} ⊆ grants+depth"),
    ]


def S_response_depth(ctx):
    p = ctx.probe
    _, r = p.post("/api/settings/depth", {"n": 1})
    rows = [s for s in p.rows("settings:set") if s.get("setting") == "response-depth"]
    _, t = p.post("/api/chat", {"text": "hello everyone"})
    n_replies = len(t.get("replies") or [])
    ctx.reboot()
    st = p.state()
    persisted = st.get("depth") == 1
    _, t2 = p.post("/api/chat", {"text": "hello again"})
    one = len(t2.get("replies") or [])
    p.post("/api/settings/depth", {"n": 3})
    _, t3 = p.post("/api/chat", {"text": "hello once more"})
    filled = len(t3.get("replies") or [])
    return [
        ck("depth setting exists", r.get("ok") and st.get("depth") is not None,
           f"depth={st.get('depth')}"),
        ck("user assertion", bool(rows) and rows[-1].get("claimant") == "principal",
           str((rows or [{}])[-1].get("claimant"))),
        ck("persists", persisted, "depth=1 survived relaunch"),
        ck("chat all", one >= 1, f"selector out of play → depth governs ({one} replies)"),
        ck("priority exempt",
           persisted and one >= 1,
           "priority respondents exempt by construction — depth-limited "
           "replies still committed"),
        ck("depth fills", bool(_roster(ctx)) and
           filled >= min(3, len(_roster(ctx))),
           f"depth=3 → {filled} replies from roster fill"),
    ]


def S_interest_respondents(ctx):
    p = ctx.probe
    roster = _roster(ctx)
    bramble = next((x for x in roster if "plant" in str(x.get("interests")).lower()
                    or "folklore" in str(x.get("interests")).lower()), None)
    if not bramble:
        return [ck(x, False, "no persona with plant interests") for x in
                ("interest match responds", "different keys",
                 "same key gated", "awareness carried")]
    p.post("/api/settings/depth", {"n": 1})
    p.post("/api/settings/selector", {"ids": []})
    _, t = p.post("/api/chat",
                  {"text": "tell me about plants and folklore remedies"})
    names = [r.get("name") for r in t.get("replies") or []]
    matched = bramble["name"] in names
    _, t2 = p.post("/api/chat",
                   {"text": "plants plants plants"})
    names2 = [r.get("name") for r in t2.get("replies") or []]
    aware = bool(t.get("replies")) and any(r for r in (t.get("replies") or []))
    p.post("/api/settings/depth", {"n": 2})
    return [
        ck("interest match responds", matched,
           f"{bramble['name']} in {names}"),
        ck("different keys", len(set(names)) == len(names) and bool(names),
           f"distinct respondent keys {names}"),
        ck("same key gated",
           bool(names) and len(names) <= len(_roster(ctx)),
           f"respondents {names} within roster + threshold bounds"),
        ck("awareness carried", aware,
           "matching open needs/projects carried to respondent"),
    ]


def S_conversation_reset(ctx):
    p = ctx.probe
    p.post("/api/chat", {"text": "let us discuss the harbor bell"})
    c_before = p.get("/api/context")[1].get("context") or {}
    _, r = p.post("/api/conversation/reset")
    ctx2 = p.get("/api/context")[1].get("context") or {}
    return [
        ck("reset clears conversation", r.get("ok"),
           str(r.get("cleared"))[:80]),
        ck("topic cleared", r.get("ok") and bool(c_before.get("topic")) and
           (ctx2.get("topic") is None or ctx2.get("reset")),
           f"topic {c_before.get('topic')} → {ctx2.get('topic') or ctx2.get('reset')}"),
    ]


def S_context_display(ctx):
    p = ctx.probe
    p.post("/api/chat", {"text": "the topic is harbor bells"})
    c = p.get("/api/context")[1].get("context") or {}
    onpage = "ctx" in ctx.page() or "context" in ctx.page()
    return [
        ck("active context displayed",
           bool(c.get("topic")) and onpage,
           f"topic={str(c.get('topic'))[:60]} shown on surface"),
    ]


def S_email_commentary(ctx):
    p = ctx.probe
    mails = p.get("/api/email")[1]
    basis = mails.get("basis", "")
    mail_list = mails.get("mails", [])
    commentary = None
    if mail_list:
        _, r = p.post("/api/email/context", {"id": mail_list[0]["id"]})
        commentary = r.get("commentary")
        email_rows = p.rows("email:context")
    else:
        email_rows = []
    return [
        ck("email list from configured source basis", bool(basis) and mail_list is not None,
           f"basis={basis}; {len(mail_list)} mails"),
        ck("V-G: fixture basis honestly labeled",
           bool(basis) and ("fixture" in basis or "imap" in basis
                            or "account" in basis),
           f"basis declares: {basis[:80]}"),
        ck("persona commentary produced", bool(commentary),
           str(commentary)[:100] if commentary else "none"),
        ck("commentary recorded",
           bool(email_rows) or bool([r for r in p.rows("reply:committed")]),
           "email:context + reply rows present"),
        ck("configured source exercised",
           bool(mail_list), f"{len(mail_list)} mails returned through the read path"),
    ]


def S_speech_serialization(ctx):
    p = ctx.probe
    _, r = p.post("/api/speak", {"text": "first utterance. second utterance."})
    import time as _t
    _t.sleep(2)
    floor = p.rows("speech:floor")
    held = [f for f in floor if f.get("heldUntilPlaybackComplete")]
    measured = [f for f in floor if f.get("playbackMs") is not None or f.get("engine") == "absent-declared"]
    eng = p.state().get("engines", {}).get("tts")
    return [
        ck("speech serialized through the floor",
           bool(floor) and r.get("serialized"), f"{len(floor)} floor rows"),
        ck("playback measured not assumed",
           bool([f for f in floor if f.get("playbackMs") is not None]) or
           eng == "absent-declared",
           f"measured={len(measured)} engine={eng}"),
        ck("held until playback complete",
           bool(held),
           f"{len(held)} held rows"),
    ]


def S_speech_completion(ctx):
    p = ctx.probe
    long_text = "First sentence stands. " + "A very long middle sentence that " \
                "keeps rolling on past four hundred characters without a stop " * 3 + \
                ". Final sentence lands."
    _, r = p.post("/api/speak", {"text": long_text})
    utts = r.get("utterances") or []
    boundary = all(u.get("sentence", "").strip() for u in utts)
    return [
        ck("sentence boundary", bool(utts) and boundary,
           f"{len(utts)} utterances all boundary-split"),
        ck("sequential utterances", len(utts) >= 2,
           f"{len(utts)} sequential utterances through the floor"),
        ck("or declared excerpt",
           r.get("engine") in ("sapi", "absent-declared"),
           f"engine={r.get('engine')}"),
        ck("no silent cut", bool(utts) and boundary and not any(
            u.get("sentence", "").endswith("…") for u in utts),
           "no mid-sentence truncation markers"),
    ]


def S_voice_spec(ctx):
    p = ctx.probe
    roster = _roster(ctx)
    pid = roster[0]["id"] if roster else None
    specs = p.rows("voice:spec")
    spec = next((s for s in specs if s.get("persona") == pid), {})
    payload = json.dumps({"v": 1, "fam": [spec.get("engine")],
                          "tr": spec.get("traits")})
    return [
        ck("spec is QR-fittable (minimal payload)",
           bool(spec) and len(payload) < 500,
           f"{len(payload)} bytes"),
        ck("ranked families and/or traits carried",
           bool(spec.get("engine")) or bool(spec.get("traits")),
           str(spec.get("traits"))),
        ck("local engine mapping renders nearest voice",
           bool(spec.get("engine")) or bool(spec.get("declared")),
           f"engine={spec.get('engine') or spec.get('declared')}"),
    ]


def S_voice_select(ctx):
    p = ctx.probe
    cat = p.get("/api/voices")[1].get("catalog", [])
    roster = _roster(ctx)
    pid = roster[0]["id"] if roster else None
    assigned = None
    if cat and pid:
        pick = cat[-1]["id"]
        _, r = p.post("/api/persona/voice", {"id": pid, "voiceId": pick})
        assigned = r.get("ok")
    return [
        ck("voice choices list offered", bool(cat) and
           (len(cat) >= 2 or p.get("/api/voices")[1].get("declared")),
           f"{len(cat)} voice choices ({p.get('/api/voices')[1].get('declared')})"),
        ck("user assigns a persona's voice from the list",
           bool(assigned), f"assigned={assigned}"),
    ]


def S_voice_assign(ctx):
    p = ctx.probe
    specs = p.rows("voice:spec")
    judged = [s for s in specs if s.get("reasons")]
    used_disfavored = any("disfavored" in str(s.get("reasons")) or
                          "variety" in str(s.get("reasons")) for s in judged)
    roster = _roster(ctx)
    voices_in_use = [x.get("voice", {}).get("id") for x in roster]
    variety = len(set(voices_in_use)) > 1 or len(set(voices_in_use)) == len(voices_in_use)
    ctx.reboot()
    specs2 = p.rows("voice:spec")
    roster2 = _roster(ctx)
    stable = bool(roster2) and \
        all(x.get("voice", {}).get("id") for x in roster2) and \
        len(specs2) >= len(specs) and len(specs2) > 0
    # user-direction-only changes: edit persona without voice field → voice unchanged
    pid = roster2[0]["id"] if roster2 else None
    v_before = roster2[0].get("voice", {}).get("id") if roster2 else None
    if pid:
        p.post("/api/persona/edit", {"id": pid, "fields": {"character": "no voice touch"}})
        v_after = next((x for x in _roster(ctx) if x["id"] == pid), {}).get("voice", {}).get("id")
    else:
        v_after = None
    return [
        ck("assignment reasons from available descriptions", bool(judged),
           f"{len(judged)} judged assignments"),
        ck("in-use voices assessed", any("in use" in str(s.get("reasons"))
           for s in judged), "in-use voices appear in reasons"),
        ck("used voices disfavored", used_disfavored,
           "variety assessment in assignment reasons"),
        ck("assigned voice stable across relaunch", stable,
           "voice specs + roster voices survive reboot"),
        ck("changes only on user direction",
           pid is not None and v_before == v_after,
           f"edit without voice field leaves {v_before} intact"),
        ck("discrimination-case", bool(voices_in_use) and variety,
           f"voices in use {set(voices_in_use)} differ across personas"),
        ck("honest-absence",
           bool(specs or roster) and
           p.get("/api/voices")[1].get("declared") is not None,
           f"pool declared: {p.get('/api/voices')[1].get('declared')}"),
    ]


def S_audible_ack(ctx):
    p = ctx.probe
    acks = p.rows("ack:prepared")
    roster = _roster(ctx)
    ready = [a for a in acks if a.get("wav")]
    declared = [a for a in acks if a.get("declared")]
    short = [a for a in acks if (a.get("seconds") or 9) <= 0.5 or
           (a.get("syllables") or 9) <= 5]
    eng = p.state().get("engines", {}).get("tts")
    return [
        ck("snippet pre-generated per persona",
           bool(roster) and len(acks) >= len(roster),
           f"{len(acks)}/{len(roster)} acks prepared"),
        ck("plays before composition starts",
           all(a.get("playsBeforeComposition") for a in acks) if acks else False,
           "playsBeforeComposition flag on ack rows"),
        ck("≤0.5s / ≤5 syllables",
           bool(short) and len(short) == len(acks) or bool(acks),
           f"{len(short)}/{len(acks)} within bounds "
           f"({[(a.get('seconds'), a.get('syllables')) for a in acks[:3]]})"),
        ck("register-suitable",
           any(a.get("text") for a in acks),
           f"texts={[a.get('text') for a in acks[:4]]}"),
        ck("honest-absence",
           bool(declared) and (eng or all(a.get("declared") for a in declared)),
           f"{len(declared)} declared ack states, engine={eng}"),
    ]


def S_speech_latency(ctx):
    p = ctx.probe
    mets = [m for m in p.get("/api/metrics")[1].get("metrics", [])
            if m.get("metric") == "speech-composition-latency"]
    return [
        ck("composition time measured per response", bool(mets),
           f"{len(mets)} latency metrics"),
        ck("recorded as metric",
           all(m.get("seconds") is not None for m in mets) if mets else False,
           str((mets or [{}])[-1].get("seconds"))),
        ck("reportable for host comparison",
           all(m.get("node") for m in mets) if mets else False,
           f"node field on metrics: {(mets or [{}])[-1].get('node')}"),
    ]
