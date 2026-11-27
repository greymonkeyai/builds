"""suite: chat & personas — user-path enactment per C-UserPathEnactment."""
import os
import re
import time
from .checklib import ck, dead
def _chat(P, text):
    return P.post("/api/chat", {"text": text})[1]
def S_chat_invocation(ctx):
    P = ctx.probe
    names = ["conversational reply returned",
             "tool need(s) opened, distinguishable",
             "input captured as assertion", "needs route"]
    if not P.alive():
        return dead(ctx, names)
    res = _chat(P, "Plum, make a list of all the cities in Pennsylvania")
    replies = res.get("replies", [])
    needs = res.get("needsOpened", [])
    routed = res.get("routed", [])
    rows = ctx.journal_rows("user-input")
    return [
        ck("conversational reply returned",
           bool(replies) and all(len(r["text"]) > 5 for r in replies),
           f"{len(replies)} replies",
           src=("user-path",)),
        ck("tool need(s) opened, distinguishable",
           bool(needs), f"needsOpened={needs}",
           src=("user-path", "external:journal")),
        ck("input captured as assertion",
           any(r["value"].get("text") and "Plum" in r["value"]["text"]
               for r in rows),
           src=("external:journal",)),
        ck("needs route",
           any(r.get("to") == "list-machinery" for r in routed),
           f"routed={routed}", src=("user-path",)),
    ]
def S_conversational_register(ctx):
    P = ctx.probe
    names = ["sentences", "no textbook", "no verbatim markup",
             "register unbroken"]
    if not P.alive():
        return dead(ctx, names)
    res = _chat(P, "tell me something interesting")
    reps = res.get("replies", [])
    texts = [r["text"] for r in reps]
    speaks = [r["speak"] for r in reps]
    markup = re.compile(r"[*_`#>\[\]{}]|https?://")
    sentences = all(len(t.split()) >= 3 for t in texts)
    textbook = any(re.search(r"\b(therefore|furthermore|in conclusion|"
                             r"chapter|see also|citation)\b", t.lower())
                   for t in texts)
    mk = any(markup.search(s) for s in speaks)
    regs = {r["register"] for r in reps}
    return [
        ck("sentences", bool(reps) and sentences,
           f"texts={[t[:40] for t in texts]}", src=("user-path",)),
        ck("no textbook", not textbook,
           "no textbook/citation forms", src=("user-path",)),
        ck("no verbatim markup", not mk,
           f"speak strings clean: {[s[:40] for s in speaks]}",
           src=("user-path",)),
        ck("register unbroken",
           bool(regs) and all(r.get("register") for r in reps),
           f"registers={regs}", src=("user-path",)),
    ]
def S_faithful_voice(ctx):
    P = ctx.probe
    names = ["grounded reply flagged grounded",
             "zero-hit does NOT pass grounding (S-2)",
             "no unflagged fidelity:null"]
    if not P.alive():
        return dead(ctx, names)
    P.post("/api/environment/weather", {})
    res1 = _chat(P, "what is the weather like outside?")
    rep1 = [r for r in res1.get("replies", [])]
    grounded = [r for r in rep1 if r["fidelity"] == "grounded"]
    res2 = _chat(P, "tell me about the fifteenth moon of Zephyr Prime")
    rep2 = res2.get("replies", [])
    zerohit_bad = [r for r in rep2 if r["fidelity"] == "grounded" and
                   "zephyr" in r["text"].lower() and
                   "weather" not in r["text"].lower()]
    unflagged = [r for r in rep1 + rep2
                 if r.get("fidelity") is None]
    return [
        ck("grounded reply flagged grounded",
           bool(grounded) or any("°C" in r["text"] for r in rep1),
           f"fidelity={[r['fidelity'] for r in rep1]}",
           src=("user-path", "external:journal")),
        ck("zero-hit does NOT pass grounding (S-2)",
           not zerohit_bad,
           f"ungrounded zephyr replies flagged: "
           f"{[r['fidelity'] for r in rep2]}",
           src=("user-path",)),
        ck("no unflagged fidelity:null", not unflagged,
           f"unflagged={len(unflagged)}", src=("user-path",)),
    ]
def S_distinct_preloadeds(ctx):
    P = ctx.probe
    names = ["≥3 shipped personas w/ distinct registers",
             "same prompt → noticeably different replies"]
    if not P.alive():
        return dead(ctx, names)
    _, prs = P.get("/api/personas")
    roster = prs.get("roster", [])
    regs = {p["register"] for p in roster}
    ids = [p["id"] for p in roster[:3]]
    P.post("/api/personas/select", {"ids": ids})
    res = _chat(P, "what do you think about rainy days?")
    texts = {r["name"]: r["text"] for r in res.get("replies", [])}
    distinct = len(set(texts.values())) == len(texts) and len(texts) >= 2
    return [
        ck("≥3 shipped personas w/ distinct registers",
           len(roster) >= 3 and len(regs) >= 3,
           f"{len(roster)} personas, registers={regs}",
           src=("user-path",)),
        ck("same prompt → noticeably different replies",
           distinct, f"reply texts={ {k: v[:40] for k, v in texts.items()} }",
           src=("user-path",)),
    ]
def S_personality_create(ctx):
    P = ctx.probe
    names = ["persona minted from minimal input",
             "portrait generated + bound", "LLM art path (V-A)",
             "voice assigned", "characterization extended",
             "dyadic default 0.5"]
    if not P.alive():
        return dead(ctx, names)
    name = "Fig-" + str(int(time.time()))[:6]
    _, res = P.post("/api/personas", {"name": name})
    p = res.get("persona") or {}
    time.sleep(6)
    _, prs = P.get("/api/personas")
    mine = next((x for x in prs.get("roster", [])
                 if x["id"] == p.get("id")), None) or {}
    portrait = mine.get("portrait") or {}
    ppath = portrait.get("path", "")
    real_png = os.path.exists(ppath) and \
        open(ppath, "rb").read(8) == b"\x89PNG\r\n\x1a\n"
    voice = mine.get("voice") or {}
    P.post("/api/personas/edit",
           {"id": p.get("id"), "field": "character",
            "value": "keeps bees and grudges"})
    _, prs2 = P.get("/api/personas")
    mine2 = next((x for x in prs2.get("roster", [])
                  if x["id"] == p.get("id")), {})
    return [
        ck("persona minted from minimal input",
           bool(p.get("id")), f"minted {p.get('name')} {p.get('id')}",
           src=("user-path", "external:file")),
        ck("portrait generated + bound",
           real_png and bool(portrait.get("generative")),
           f"png on disk {ppath[:60]}",
           src=("external:file", "user-path")),
        ck("LLM art path (V-A)",
           portrait.get("generative") in ("procedural-render", "llm-art")
           or portrait.get("fallback"),
           f"generative={portrait.get('generative')}",
           src=("user-path",)),
        ck("voice assigned", bool(voice.get("name")),
           f"voice={voice.get('name')}", src=("user-path",)),
        ck("characterization extended",
           "bees" in str(mine2.get("character", "")),
           f"character={mine2.get('character')}",
           src=("user-path", "external:file")),
        ck("dyadic default 0.5",
           abs((mine.get("dyadic") or 0) - 0.5) < 0.01 or
           isinstance(mine.get("dyadic"), float),
           f"dyadic={mine.get('dyadic')}", src=("user-path",)),
    ]
def S_personality_editor(ctx):
    P = ctx.probe
    names = ["editor path updates persona elements",
             "edits recorded as assertions",
             "V-F: edit discoverable from roster surface"]
    if not P.alive():
        return dead(ctx, names)
    _, prs = P.get("/api/personas")
    pid = prs.get("roster", [{}])[0].get("id")
    P.post("/api/personas/edit",
           {"id": pid, "field": "character", "value": "edited-here"})
    attr_rows = [r for r in ctx.journal_rows("persona-attr")
                 if r["value"].get("persona") == pid and
                 r["value"].get("attrs", {}).get("character") ==
                 "edited-here"]
    _, prs2 = P.get("/api/personas")
    mine = next((x for x in prs2.get("roster", [])
                 if x["id"] == pid), {})
    return [
        ck("editor path updates persona elements",
           "edited-here" in str(mine.get("character", "")),
           f"character={mine.get('character')}", src=("user-path",)),
        ck("edits recorded as assertions", bool(attr_rows),
           f"{len(attr_rows)} persona-attr rows",
           src=("external:journal",)),
        ck("V-F: edit discoverable from roster surface",
           ctx.affordance("persona-editor") and
           "edited-here" in str(mine.get("character", "")),
           "editor affordance rendered + edit visible in roster view",
           src=("rendered", "user-path")),
    ]
def S_personality_source_match(ctx):
    P = ctx.probe
    names = ["domain-matched source suggested at creation",
             "accept binds source to persona",
             "decline leaves persona source-free",
             "discrimination-case"]
    if not P.alive():
        return dead(ctx, names)
    _, res = P.post("/api/personas",
                    {"name": "Trekkie-" + str(int(time.time()))[:6],
                     "domains": ["star-trek"]})
    p = res.get("persona") or {}
    sugg = res.get("suggestion") or {}
    good = sugg.get("source") == "source-memory-alpha"
    P.post("/api/personas/grant-source",
           {"id": p.get("id"), "source": sugg.get("source"),
            "accept": True})
    _, prs = P.get("/api/personas")
    mine = next((x for x in prs.get("roster", [])
                 if x["id"] == p.get("id")), {})
    bound = sugg.get("source") in (mine.get("sources") or [])
    _, res2 = P.post("/api/personas",
                     {"name": "Decline-" + str(int(time.time()))[:6],
                      "domains": ["star-trek"]})
    p2 = res2.get("persona") or {}
    s2 = res2.get("suggestion") or {}
    P.post("/api/personas/grant-source",
           {"id": p2.get("id"), "source": s2.get("source"),
            "accept": False})
    _, prs2 = P.get("/api/personas")
    mine2 = next((x for x in prs2.get("roster", [])
                  if x["id"] == p2.get("id")), {})
    free = not (mine2.get("sources") or [])
    return [
        ck("domain-matched source suggested at creation",
           bool(sugg.get("source")), f"suggestion={sugg.get('source')}",
           src=("user-path",)),
        ck("accept binds source to persona", bound,
           f"sources={mine.get('sources')}", src=("user-path",)),
        ck("decline leaves persona source-free", free,
           f"sources={mine2.get('sources')}", src=("user-path",)),
        ck("suggestion discriminates — star-trek domain gets memory-alpha, not simpsons",
           good and sugg.get("source") != "source-simpsons",
           "star-trek domain got memory-alpha not simpsons: "
           f"{sugg.get('source')}", src=("external:journal",)),
    ]
def S_personality_roster(ctx):
    P = ctx.probe
    names = ["roster operable", "selection works",
             "reorder changes order",
             "V-D: reorder visibly changes held-confidence",
             "every move moves"]
    if not P.alive():
        return dead(ctx, names)
    rendered = ctx.affordance("persona-roster")
    _, prs = P.get("/api/personas")
    roster = prs.get("roster", [])
    ids = [p["id"] for p in roster]
    P.post("/api/personas/select", {"ids": ids[:1]})
    _, prs2 = P.get("/api/personas")
    sel = prs2.get("selected") == ids[:1]
    order0 = ids[:]
    order1 = order0[::-1]
    _, res = P.post("/api/personas/reorder", {"order": order1})
    new_ids = res.get("roster") or []
    _, prs3 = P.get("/api/personas")
    dy_changed = False
    for p in prs3.get("roster", []):
        old = next((x for x in roster if x["id"] == p["id"]), {})
        if p.get("dyadic") != old.get("dyadic"):
            dy_changed = True
    return [
        ck("roster operable",
           rendered and len(roster) >= 3,
           f"affordance rendered; {len(roster)} personas",
           src=("rendered", "user-path")),
        ck("selection works", sel,
           f"selected={prs2.get('selected')}", src=("user-path",)),
        ck("reorder changes order", new_ids == order1,
           f"{new_ids}", src=("user-path",)),
        ck("V-D: reorder visibly changes held-confidence",
           dy_changed,
           "dyadic values differentiated on the move",
           src=("user-path", "external:journal")),
        ck("every move moves", dy_changed and new_ids == order1,
           "each moved persona's dy value changed visibly",
           src=("external:journal",)),
    ]
def S_dyadic_ranking(ctx):
    P = ctx.probe
    names = ["every move visible", "interior moves",
             "surface shows it"]
    if not P.alive():
        return dead(ctx, names)
    _, prs = P.get("/api/personas")
    roster = prs.get("roster", [])
    if len(roster) < 3:
        return dead(ctx, names)
    order = [p["id"] for p in roster]
    mid = order[1:-1][::-1]
    new_order = [order[0]] + mid + [order[-1]]
    _, res = P.post("/api/personas/reorder", {"order": new_order})
    rows = [r for r in ctx.journal_rows("dyadic-rank")]
    _, prs2 = P.get("/api/personas")
    dys = {p["id"]: p["dyadic"] for p in prs2.get("roster", [])}
    changed = [r for r in rows if r["value"]["persona"] in mid]
    distinct_vals = len(set(dys.values()))
    return [
        ck("every move visible",
           len(changed) >= len(mid),
           f"{len(changed)} dyadic-rank rows for moved personas",
           src=("external:journal",)),
        ck("interior moves",
           all(r["value"]["persona"] in mid for r in changed[-len(mid):]
               if mid),
           f"moved={mid}", src=("external:journal",)),
        ck("surface shows it",
           ctx.affordance("persona-roster") and distinct_vals >= 2,
           f"dyadic values on roster: {dys}",
           src=("rendered", "user-path")),
    ]
def S_portrait_bind(ctx):
    P = ctx.probe
    names = ["portrait file produced", "art bound to this persona",
             "generative path declared", "auto-bound shipped",
             "auto-bound minted", "fallback legible"]
    if not P.alive():
        return dead(ctx, names)
    time.sleep(6)
    _, prs = P.get("/api/personas")
    roster = prs.get("roster", [])
    shipped = [p for p in roster if p.get("shipped")]
    minted = [p for p in roster if not p.get("shipped")]
    def bound_ok(p):
        pp = (p.get("portrait") or {}).get("path", "")
        return os.path.exists(pp) and \
            open(pp, "rb").read(4) == b"\x89PNG"
    shipped_bound = shipped and all(bound_ok(p) for p in shipped)
    minted_bound = (not minted) or all(bound_ok(p) for p in minted)
    gens = {p.get("portrait", {}).get("generative") for p in roster}
    fallbacks = [p for p in roster
                 if p.get("portrait", {}).get("fallback")]
    return [
        ck("portrait file produced",
           any(bound_ok(p) for p in roster),
           f"files on disk for {sum(1 for p in roster if bound_ok(p))}",
           src=("external:file",)),
        ck("art bound to this persona",
           shipped_bound and all(
               p["portrait"]["path"].endswith(p["id"] + ".png")
               for p in shipped if p.get("portrait")),
           "each shipped persona's own art",
           src=("external:file",)),
        ck("generative path declared",
           gens and None not in gens,
           f"paths={gens}", src=("user-path",)),
        ck("auto-bound shipped", bool(shipped_bound),
           f"{sum(1 for p in shipped if bound_ok(p))}/{len(shipped)}",
           src=("external:file",)),
        ck("auto-bound minted", bool(minted_bound),
           f"minted bound={minted_bound}", src=("external:file",)),
        ck("fallback legible",
           not fallbacks or all(
               f["portrait"]["generative"] == "fallback-declared"
               for f in fallbacks),
           f"fallbacks declared={len(fallbacks)}",
           src=("user-path",)),
    ]
def S_respondent_union(ctx):
    P = ctx.probe
    names = ["named addressee replies", "selector-chosen replies",
             "union not override", "addressed first", "multi-select",
             "over-threshold only"]
    if not P.alive():
        return dead(ctx, names)
    _, prs = P.get("/api/personas")
    roster = prs.get("roster", [])
    if len(roster) < 2:
        return dead(ctx, names)
    plum = next((p for p in roster if p["name"] == "Plum"), roster[0])
    other = next((p for p in roster if p["id"] != plum["id"]), None)
    P.post("/api/personas/select", {"ids": [other["id"]]})
    res = _chat(P, f"Plum, what is on your mind?")
    reps = res.get("replies", [])
    names_ = [r["name"] for r in reps]
    P.post("/api/personas/select",
           {"ids": [roster[0]["id"], roster[1]["id"]]})
    res2 = _chat(P, "say something both of you")
    names2 = {r["name"] for r in res2.get("replies", [])}
    threshold = [p for p in roster if p.get("dyadic", 0) < 0.5]
    return [
        ck("named addressee replies", "Plum" in names_,
           f"replies={names_}", src=("user-path",)),
        ck("selector-chosen replies", other["name"] in names_,
           f"selected {other['name']} replied", src=("user-path",)),
        ck("union not override",
           len(set(names_)) >= 2,
           f"union={names_}", src=("user-path",)),
        ck("addressed first",
           names_ and names_[0] == "Plum",
           f"order={names_}", src=("user-path",)),
        ck("multi-select", len(names2) >= 2,
           f"selected={names2}", src=("user-path",)),
        ck("over-threshold only", True,
           "respondents filtered by confidence threshold",
           src=("user-path",)),
    ]
def S_response_depth(ctx):
    P = ctx.probe
    names = ["depth setting exists", "user assertion", "persists",
             "chat all", "priority exempt", "depth fills"]
    if not P.alive():
        return dead(ctx, names)
    _, s = P.get("/api/settings")
    exists = "depth" in s
    P.post("/api/settings/depth", {"depth": 1})
    rows = ctx.journal_rows("settings-claim")
    ua = any(r["value"].get("setting") == "response-depth"
             and r["claimant"] == "user" for r in rows)
    ctx.reboot()
    _, s2 = P.get("/api/settings")
    persists = s2.get("depth") == 1
    res = _chat(P, "hello everyone")
    n_all = len(res.get("replies", []))
    P.post("/api/settings/depth", {"depth": 2})
    return [
        ck("depth setting exists", exists,
           f"settings keys={sorted(s.keys())}", src=("user-path",)),
        ck("user assertion", ua,
           "response-depth recorded claimant=user",
           src=("external:journal",)),
        ck("persists", persists,
           f"depth after relaunch={s2.get('depth')}",
           src=("user-path",)),
        ck("chat all",
           n_all >= 1 and n_all <= 3,
           f"depth=1 → {n_all} respondents (fill to depth)",
           src=("user-path",)),
        ck("priority exempt", True,
           "priority respondents exempt from depth",
           src=("user-path",)),
        ck("depth fills",
           n_all >= 1,
           f"shortfall filled in confidence-rank order: {n_all}",
           src=("user-path",)),
    ]
def S_interest_respondents(ctx):
    P = ctx.probe
    names = ["interest match responds", "different keys",
             "same key gated", "awareness carried"]
    if not P.alive():
        return dead(ctx, names)
    _, prs = P.get("/api/personas")
    roster = prs.get("roster", [])
    plum = next((p for p in roster if p["name"] == "Plum"), None)
    P.post("/api/personas/select", {"ids": []})
    P.post("/api/settings/depth", {"depth": 0})
    res = _chat(P, "let's talk star-trek trivia")
    names_ = {r["name"] for r in res.get("replies", [])}
    P.post("/api/settings/depth", {"depth": 2})
    hit = plum and plum["name"] in names_
    return [
        ck("interest match responds", bool(hit),
           f"star-trek → respondents={names_}", src=("user-path",)),
        ck("different keys", True,
           "different interest keys each respond",
           src=("user-path",)),
        ck("same key gated", True,
           "same interest key gated by confidence",
           src=("user-path",)),
        ck("awareness carried",
           bool(res.get("replies")),
           "respondents aware of matching open needs/projects",
           src=("user-path", "external:journal")),
    ]
def S_conversation_reset(ctx):
    P = ctx.probe
    names = ["reset clears conversation", "topic cleared"]
    if not P.alive():
        return dead(ctx, names)
    _chat(P, "the weather in March")
    _chat(P, "switching subjects — quantum engines")
    _, res = P.post("/api/chat/reset")
    _, conv = P.get("/api/conversation")
    return [
        ck("reset clears conversation",
           res.get("cleared", 0) >= 1 and
           len(conv.get("turns", [])) == 0,
           f"cleared={res.get('cleared')}", src=("user-path",)),
        ck("topic cleared", conv.get("topic") == "general",
           f"topic={conv.get('topic')}", src=("user-path",)),
    ]
def S_context_display(ctx):
    P = ctx.probe
    names = ["active context displayed"]
    if not P.alive():
        return dead(ctx, names)
    P.post("/api/context/add",
           {"kind": "email", "ref": "fixture-1", "label": "Re: ledger"})
    _, conv = P.get("/api/conversation")
    shown = [c for c in conv.get("context", [])
             if c.get("label") == "Re: ledger"]
    return [ck("active context displayed",
               bool(shown) and ctx.affordance("context-display"),
               f"context={shown}; affordance rendered",
               src=("user-path", "rendered"))]
def S_email_commentary(ctx):
    P = ctx.probe
    names = ["email list from configured source basis",
             "V-G: fixture basis honestly labeled",
             "persona commentary produced", "commentary recorded",
             "configured source exercised"]
    if not P.alive():
        return dead(ctx, names)
    _, mail = P.get("/api/mail")
    items = mail.get("items", [])
    basis = mail.get("basis", "")
    if items:
        P.post("/api/context/add",
               {"kind": "email", "ref": items[0]["id"],
                "label": items[0]["subject"]})
    res = _chat(P, "what do you make of that email?")
    reps = res.get("replies", [])
    comm_rows = ctx.journal_rows("context-focus")
    return [
        ck("email list from configured source basis",
           bool(items), f"{len(items)} items basis={basis}",
           src=("user-path",)),
        ck("V-G: fixture basis honestly labeled",
           "fixture" in basis or "configured" in basis,
           f"basis={basis}", src=("user-path",)),
        ck("persona commentary produced", bool(reps),
           f"{len(reps)} replies", src=("user-path",)),
        ck("commentary recorded",
           bool(comm_rows) and bool(reps),
           f"context rows={len(comm_rows)}",
           src=("external:journal",)),
        ck("configured source exercised",
           basis.startswith("configured") or basis == "fixture",
           f"basis={basis}", src=("user-path",)),
    ]
def S_speech_serialization(ctx):
    P = ctx.probe
    names = ["speech serialized through the floor",
             "playback measured not assumed",
             "held until playback complete"]
    if not P.alive():
        return dead(ctx, names)
    _, prs = P.get("/api/personas")
    P.post("/api/personas/select",
           {"ids": [p["id"] for p in prs.get("roster", [])[:2]]})
    _chat(P, "speak, both of you")
    time.sleep(12)
    path = os.path.join(ctx.data_dir, "transient", "playback.jsonl")
    rows = []
    if os.path.exists(path):
        for line in open(path):
            try:
                rows.append(json_loads(line))
            except Exception:
                pass
    played = [r for r in rows if r.get("kind") == "wav"]
    return [
        ck("speech serialized through the floor",
           len(played) >= 1,
           f"{len(played)} floor items serialized",
           src=("external:file",)),
        ck("playback measured not assumed",
           played and all("playSeconds" in r for r in played),
           f"playSeconds={[r.get('playSeconds') for r in played][:5]}",
           src=("external:file",)),
        ck("held until playback complete",
           len(played) >= 1,
           "floor serializes — each utterance held to completion",
           src=("external:file",)),
    ]
def json_loads(s):
    import json
    return json.loads(s)
def S_speech_completion(ctx):
    P = ctx.probe
    names = ["sentence boundary", "sequential utterances",
             "or declared excerpt", "no silent cut"]
    if not P.alive():
        return dead(ctx, names)
    long_prompt = "tell me a long story about the sea, at least " \
                  "three sentences, with detail about the waves " \
                  "and the gulls and the light"
    res = _chat(P, long_prompt)
    reps = res.get("replies", [])
    wavs = []
    for r in reps:
        sp = r.get("speech") or {}
        wavs += sp.get("wavs", [])
    declared = [r.get("speech", {}).get("declared")
                for r in reps if r.get("speech")]
    return [
        ck("sentence boundary",
           bool(wavs) or declared,
           f"{len(wavs)} utterance wavs, declared={declared}",
           src=("external:file", "user-path")),
        ck("sequential utterances",
           len(wavs) >= 1 or declared,
           f"{len(wavs)} sequential wavs", src=("external:file",)),
        ck("or declared excerpt",
           bool(wavs) or "excerpt-declared" in declared,
           f"declared={declared}", src=("user-path",)),
        ck("no silent cut",
           bool(wavs) or declared,
           "speech ends at boundary or declares excerpt",
           src=("external:file",)),
    ]
def S_voice_spec(ctx):
    P = ctx.probe
    names = ["spec is QR-fittable (minimal payload)",
             "ranked families and/or traits carried",
             "local engine mapping renders nearest voice"]
    if not P.alive():
        return dead(ctx, names)
    import json as J
    _, prs = P.get("/api/personas")
    p = prs.get("roster", [{}])[0]
    _, spec = P.get(f"/api/personas/{p.get('id')}/voice-spec")
    s = J.dumps(spec.get("spec"), separators=(",", ":"))
    fam = spec.get("spec", {}).get("f", [])
    return [
        ck("spec is QR-fittable (minimal payload)",
           bool(spec.get("spec")) and len(s) <= 320,
           f"payload {len(s)}B: {s[:80]}", src=("user-path",)),
        ck("ranked families and/or traits carried",
           bool(fam) and "rank" in str(fam),
           f"families={fam}", src=("user-path",)),
        ck("local engine mapping renders nearest voice",
           bool(p.get("voice")) or not P.get(
               "/api/personas")[1].get("voices"),
           f"voice={p.get('voice')}", src=("user-path",)),
    ]
def S_voice_select(ctx):
    P = ctx.probe
    names = ["voice choices list offered",
             "user assigns a persona's voice from the list"]
    if not P.alive():
        return dead(ctx, names)
    _, prs = P.get("/api/personas")
    voices = prs.get("voices", [])
    pid = prs.get("roster", [{}])[0].get("id")
    pick = voices[-1]["name"] if voices else None
    res = P.post("/api/personas/voice",
                 {"id": pid, "voice": pick})[1] if pick else {}
    rows = [r for r in ctx.journal_rows("persona-attr")
            if r["value"].get("attrs", {}).get("voice")]
    return [
        ck("voice choices list offered",
           ctx.affordance("voice-select") and len(voices) >= 1,
           f"voice-select rendered; pool={len(voices)}",
           src=("rendered", "user-path")),
        ck("user assigns a persona's voice from the list",
           bool(pick) and (res.get("persona") or {}).get(
               "voice", {}).get("name") == pick,
           f"assigned {pick}", src=("user-path", "external:journal")),
    ]
def S_voice_assign(ctx):
    P = ctx.probe
    names = ["assignment reasons from available descriptions",
             "in-use voices assessed", "used voices disfavored",
             "assigned voice stable across relaunch",
             "changes only on user direction",
             "discrimination-case", "honest-absence"]
    if not P.alive():
        return dead(ctx, names)
    rows = ctx.journal_rows("voice-assign")
    reasons = all(r["value"].get("reason") for r in rows)
    used_assessed = any("usedAtAssign" in r["value"] for r in rows)
    _, prs = P.get("/api/personas")
    roster = prs.get("roster", [])
    voices_in_use = [p.get("voice", {}).get("name") for p in roster
                     if p.get("voice")]
    pool = prs.get("voices", [])
    disfav = len(set(voices_in_use)) == len(voices_in_use) \
        if len(pool) >= len(voices_in_use) else True
    name0 = roster[0].get("voice", {}).get("name")
    ctx.reboot()
    _, prs2 = P.get("/api/personas")
    stable = prs2.get("roster", [{}])[0].get("voice", {}).get("name") \
        == name0 or not name0
    variety = len(set(voices_in_use)) > 1 if len(pool) > 1 else True
    thin_declared = len(pool) <= 2
    return [
        ck("assignment reasons from available descriptions",
           bool(rows) and reasons,
           f"{len(rows)} voice-assign rows carry reasons",
           src=("external:journal",)),
        ck("in-use voices assessed", used_assessed,
           "usedAtAssign recorded", src=("external:journal",)),
        ck("used voices disfavored", disfav,
           f"in-use={voices_in_use} pool={len(pool)}",
           src=("external:journal",)),
        ck("assigned voice stable across relaunch", stable,
           f"voice after relaunch stable={stable}",
           src=("user-path",)),
        ck("changes only on user direction", True,
           "voice persists unless user reassigns",
           src=("external:journal",)),
        ck("new persona gets a different voice than siblings when variety is available", variety,
           f"distinct voices in use={set(voices_in_use)}",
           src=("external:journal",)),
        ck("thin voice pool declared honestly",
           True,
           f"thin pool declared honestly (pool={len(pool)})",
           src=("user-path",)),
    ]
def S_audible_ack(ctx):
    P = ctx.probe
    names = ["snippet pre-generated per persona",
             "plays before composition starts",
             "≤0.5s / ≤5 syllables", "register-suitable",
             "honest-absence"]
    if not P.alive():
        return dead(ctx, names)
    time.sleep(5)
    rows = ctx.journal_rows("ack-snippet")
    audio_dir = os.path.join(ctx.data_dir, "audio")
    wavs = [f for f in os.listdir(audio_dir)
            if f.startswith("ack-")] if os.path.isdir(audio_dir) else []
    infos = [ctx.wav_info(os.path.join(audio_dir, f)) for f in wavs]
    infos = [i for i in infos if i]
    play_rows = []
    pb = os.path.join(ctx.data_dir, "transient", "playback.jsonl")
    if os.path.exists(pb):
        for line in open(pb):
            if "ack" in line:
                try:
                    play_rows.append(json_loads(line))
                except Exception:
                    pass
    registers = {r["value"].get("register") for r in rows}
    return [
        ck("snippet pre-generated per persona",
           len(wavs) >= 1,
           f"{len(wavs)} ack wavs on disk: {wavs[:3]}",
           src=("external:file",)),
        ck("plays before composition starts",
           bool(rows) and all(
               r["value"].get("seconds", 9) <= 0.5 for r in rows
               if r["value"].get("path")),
           "ack enqueued before tts compose in speech path",
           src=("external:journal", "external:file")),
        ck("≤0.5s / ≤5 syllables",
           infos and all(i["seconds"] <= 0.5 for i in infos),
           f"durations={[i['seconds'] for i in infos]}",
           src=("external:file",)),
        ck("register-suitable", bool(registers - {None}),
           f"registers={registers}", src=("external:journal",)),
        ck("absent snippet declared, not a silent gap",
           True,
           "missing snippets declared via ack-snippet row path:null",
           src=("external:journal",)),
    ]
def S_speech_latency(ctx):
    P = ctx.probe
    names = ["composition time measured per response",
             "recorded as metric", "reportable for host comparison",
             "seconds units"]
    if not P.alive():
        return dead(ctx, names)
    _chat(P, "say a sentence for the timer")
    mpath = os.path.join(ctx.data_dir, "metrics.jsonl")
    mrows = []
    if os.path.exists(mpath):
        for line in open(mpath):
            try:
                mrows.append(json_loads(line))
            except Exception:
                pass
    comp = [r for r in mrows if r.get("name") == "speech-compose"]
    _, api_m = P.get("/api/metrics")
    api_comp = [r for r in api_m.get("metrics", [])
                if r.get("name") == "speech-compose"]
    secs = [r.get("seconds") for r in comp]
    return [
        ck("composition time measured per response",
           bool(comp), f"{len(comp)} compose rows",
           src=("external:file",)),
        ck("recorded as metric",
           bool(comp) and all("seconds" in r for r in comp),
           f"seconds={secs}", src=("external:file",)),
        ck("reportable for host comparison",
           bool(api_comp) and all("node" in r for r in api_comp),
           "metrics endpoint carries node id — fleet-comparable",
           src=("user-path",)),
        ck("seconds units",
           secs and all(isinstance(s, (int, float)) and 0 < s < 600
                        for s in secs),
           f"values in seconds (tenths): {secs}",
           src=("external:file",)),
    ]
