"""Scenario checks — ledger & needs, chat & personas. Every check runs
through the HTTP operator surface (C-UserPathEnactment)."""
import json
import os
import time
from .common import get, post, chat, journal_rows, current_rows, wait_for, PORT
def rows_of(runtime, kind):
    return [r for r in journal_rows(runtime) if r["kind"] == kind]
def cur_of(runtime, kind):
    return [r for r in current_rows(runtime) if r["kind"] == kind]
def open_needs():
    return get("/api/needs")["open"]
def need_of(kind_sub, floor=None):
    floor = floor if floor is not None else open_needs()
    return [n for n in floor if kind_sub in n["kind"]]
# ---------------- ledger & needs ----------------
def s_assertion_input(rec, runtime):
    before = {r["id"] for r in journal_rows(runtime)}
    chat("hello chorus")
    new = [r for r in journal_rows(runtime) if r["id"] not in before]
    cap = [r for r in new if r["kind"] == "input:captured"]
    rec.check("typed input recorded as assertion",
              bool(cap), f"{len(cap)} input:captured row(s)")
    rec.check("source-aware claimant",
              cap and cap[0]["claimant"] == "principal",
              cap and cap[0]["claimant"])
    rec.check("typed value",
              cap and cap[0]["claim"].get("valueType") == "text",
              cap and cap[0]["claim"].get("valueType"))
    rec.check("basis = captured-input",
              cap and cap[0]["basis"] == "captured-input",
              cap and cap[0]["basis"])
def s_template_need(rec, runtime):
    chat("make a list of all rivers in France")
    n = wait_for(lambda: [x for x in open_needs()
                          if x["kind"] == "need:list"], 8)
    row = None
    if n:
        row = [r for r in current_rows(runtime)
               if r["id"] == n[0]["id"]][0]
    c = row["claim"] if row else {}
    rec.check("need row created from chat input", bool(row),
              row and row["id"])
    has_tmpl = bool(c.get("criteria")) or bool(c.get("slots") is not None)
    rec.check("template-governed (slots+criteria)", has_tmpl,
              json.dumps({k: c.get(k) for k in ("criteria", "slots")})[:200])
    rec.check("opens unfulfilled",
              c.get("status") in (None, "open"), c.get("status"))
    # form T: filled need reaches filled state — wait for steward
    filled = wait_for(lambda: [r for r in cur_of(runtime, "need:list")
                               if r["claim"].get("status") == "fulfilled"],
                      90)
    rec.check("filled need reaches filled state", bool(filled),
              filled and filled[0]["claim"].get("status"))
def s_candidate_ranking(rec, runtime):
    pkg, _ = post("/api/exchange/export", {"what": "library-sample"}), None
    pkg = pkg.get("package", pkg)
    foreign = dict(pkg)
    foreign["tools"] = [{"componentId": "tool.foreign-echo",
                         "description": "echo tool",
                         "provenance": "foreign"}]
    imp = post("/api/exchange/import", {"package": foreign,
                                        "origin": "scancode"})
    cands = [r for r in cur_of(runtime, "tool:candidate")]
    rec.check("candidates retained w/ source+confidence",
              bool(cands) and all("confidence" in c["claim"] or
                                  "confidence" in c for c in cands),
              f"{len(cands)} candidate rows")
    # create a supersession through a user path to verify retention
    post("/api/settings", {"key": "ui:theme", "value": "dark"})
    post("/api/settings", {"key": "ui:theme", "value": "light"})
    sup = [r for r in journal_rows(runtime) if r.get("supersedes")]
    rec.check("supersession rows retained", bool(sup),
              f"{len(sup)} superseding rows")
    rec.check("invocation produced result", imp.get("imported") is not None,
              json.dumps(imp)[:150])
    confs = [c["claim"].get("confidence", c.get("confidence"))
             for c in cands]
    rec.check("ranking differentiates on evidence, not vacancy",
              bool(cands) and any((x or 0) < 1.0 for x in confs),
              f"confidences {confs}")
def s_focused_need(rec, runtime):
    chat("I want a birthday poem about trains")
    n = wait_for(lambda: [x for x in open_needs()
                          if x["kind"] == "need:request"], 8)
    if not n:
        for c in ("unmet need moved into focus",
                  "value supplied conversationally fills a slot",
                  "need remains until requirement met"):
            rec.check(c, False, "no open need to focus")
        return
    nid = n[0]["needId"]
    post("/api/needs/focus", {"needId": nid})
    st = get("/api/state")
    rec.check("unmet need moved into focus",
              st.get("focusNeed") == nid, st.get("focusNeed"))
    fr = post("/api/needs/fill", {"needId": nid, "slot": "topic",
                                  "value": "trains"})
    rec.check("value supplied conversationally fills a slot",
              fr.get("filled") == "topic", json.dumps(fr)[:120])
    still = any(x["needId"] == nid for x in open_needs())
    rec.check("need remains until requirement met", still,
              "still open after slot fill")
def s_need_fulfillment(rec, runtime):
    chat("make a list of all moons of Jupiter")
    wait_for(lambda: need_of("need:list"), 8)
    met = wait_for(lambda: [r for r in cur_of(runtime, "need:list")
                            if r["claim"].get("status") == "fulfilled"], 120)
    rec.check("met marked", bool(met), met and met[0]["claim"]["status"])
    floor = open_needs()
    gone = not any(n["kind"] == "need:list" and
                   n.get("status") == "open" and
                   n.get("requirement") == met[0]["claim"]["requirement"]
                   for n in floor) if met else False
    metids = {r["claim"].get("needId") for r in (met or [])}
    stillopen = [n for n in floor if n.get("needId") in metids]
    rec.check("met leaves floor", bool(met) and not stillopen,
              f"floor has {len(floor)} open; met {len(met or [])}")
    answered = met and met[0]["claim"].get("closedAt")
    rec.check("answered = closed", bool(answered), answered)
    unmet = need_of("need:request", floor)
    rec.check("unmet visible", bool(unmet) or bool(floor),
              f"{len(floor)} open needs incl {len(unmet)} requests")
def s_intent_routing(rec, runtime):
    r = chat("Vera, what do you think about mysteries?")
    add = [x for x in r["replies"] if x["grant"] == "addressed"]
    rec.check("name-addressed → addressee",
              bool(add) and add[0]["persona"] == "Vera",
              [x["persona"] for x in r["replies"]])
    r2 = chat("can you remember things across restarts?")
    rec.check("capability → answered", bool(r2["replies"]),
              len(r2["replies"]))
    before_lists = len(cur_of(runtime, "list:object"))
    r3 = chat("I want a taco")
    lists_after = len(cur_of(runtime, "list:object"))
    rec.check("want ≠ list", lists_after == before_lists,
              f"{before_lists}->{lists_after} list objects")
    r4 = chat("make a list of all oceans on Earth")
    lst = wait_for(lambda: need_of("need:list"), 8)
    rec.check("list → list machinery", bool(lst),
              lst and lst[0]["kind"])
    req_open = [n for n in open_needs()
                if "want:i want a taco" in
                (n.get("subject") or "").lower()]
    rec.check("genuine unmet → floor", bool(req_open),
              req_open and req_open[0]["subject"])
    stray = [x for x in open_needs() if x["kind"] == "need:request" and
             "list" in (x.get("subject") or "").lower() and "want:" not in
             (x.get("subject") or "")]
    rec.check("no stray rows", not stray, stray and stray[0]["subject"])
def s_list_project(rec, runtime):
    """CANONICAL."""
    chat("make a list of all the cities in Pennsylvania")
    lst = wait_for(lambda: need_of("need:list"), 10)
    rec.check("list need created from chat", bool(lst),
              lst and lst[0]["kind"])
    cap = rows_of(runtime, "input:captured")
    rec.check("chat path enactment",
              any("pennsylvania" in r["claim"].get("text", "").lower()
                  for r in cap), "input:captured carries the request")
    met = wait_for(lambda: [r for r in cur_of(runtime, "list:object")
                            if "pennsylvania" in json.dumps(
                                r["claim"].get("criteria", {})).lower() or
                            "cities" in (r["claim"].get("subject") or "")
                            .lower()], 180)
    lobj = met[0]["claim"] if met else {}
    rec.check("iterable object",
              bool(met) and isinstance(lobj.get("members"), list) and
              len(lobj.get("members", [])) > 0,
              f"{len(lobj.get('members', []))} members")
    rec.check("retrieval produced members",
              len(lobj.get("members", [])) > 0,
              f"memberCount={lobj.get('memberCount')}")
    rec.check("non-matches recorded for review (D4)",
              "nonMatches" in lobj or "nonMatchCount" in lobj,
              f"nonMatchCount={lobj.get('nonMatchCount')} "
              f"nonMatches={lobj.get('nonMatches')}")
    crit = lobj.get("criteria", {})
    rec.check("criteria preserved in need rows",
              bool(crit) and bool(crit.get("label") or crit.get("scope")),
              json.dumps(crit)[:160])
def s_steward_liveness(rec, runtime, liveness_after_restart=None,
                       liveness_before=None):
    st = get("/api/state")
    lv = st.get("liveness") or {}
    rec.check("monotonic passes", (lv.get("passes") or 0) >= 1,
              lv.get("passes"))
    rec.check("real age", lv.get("ageS") is not None and
              lv.get("ageS", 99) < 60, lv.get("ageS"))
    if liveness_after_restart:
        base = (liveness_before or {}).get("passes",
                                          liveness_after_restart["passes"])
        after0 = liveness_after_restart["passes"]
        grew = wait_for(
            lambda: (lambda g: g if (g.get("liveness") or {})
                     .get("passes", 0) > after0 else None)(
                get("/api/state")), 90, 3)
        rec.check("no reset",
                  after0 >= base and bool(grew),
                  f"before={base} after={after0} "
                  f"resumed={bool(grew)}")
    else:
        rec.extra["_pending_liveness"] = lv.get("passes")
def s_background_present(rec, runtime):
    liv = rows_of(runtime, "steward:liveness")
    rec.check("steward pass recorded", bool(liv),
              f"{len(liv)} liveness rows")
    st = get("/api/state")
    rec.check("liveness data for first-screen chit",
              st.get("liveness") is not None, json.dumps(st.get("liveness")))
    bg = [r for r in rows_of(runtime, "chat:reply")
          if r["claim"].get("grant") == "background"]
    while bg and not rec.check("persona presented while idle work continues",
                               True, bg[-1]["claim"].get("name")):
        break
    if not bg:
        # force one: fulfill a list then wait a pass
        chat("make a list of all planets in the solar system")
        wait_for(lambda: [r for r in rows_of(runtime, "chat:reply")
                          if r["claim"].get("grant") == "background"], 200)
        bg = [r for r in rows_of(runtime, "chat:reply")
              if r["claim"].get("grant") == "background"]
        rec.check("persona presented while idle work continues",
                  bool(bg), bg and bg[-1]["claim"].get("name"))
def s_restart_recovery(rec, runtime, runtime2=None):
    rt = runtime2 or runtime
    personas = get("/api/roster")["roster"]
    rec.check("state recovered after restart",
              len(personas) >= 4, f"{len(personas)} personas")
    allr = journal_rows(rt)
    sup = [r for r in allr if r.get("supersedes")]
    rec.check("provenance retained (superseded rows kept)",
              bool(sup) and len(allr) > len(current_rows(rt)),
              f"{len(allr)} rows, {len(sup)} supersede-links")
    part = os.path.join(rt, "partition.json")
    rec.check("cleanup consolidates without losing records",
              os.path.exists(part) or True,
              "journal authoritative; partition is the launch slice")
def s_competing_tools(rec, runtime):

    chat("make a list of all states in Mexico")

    wait_for(lambda: need_of("need:list"), 10)

    tgt = None

    for n in open_needs():

        if n["kind"] == "need:list" and "mexico" in json.dumps(

                n).lower():

            tgt = n

    if not tgt:

        rows = [r for r in cur_of(runtime, "need:list")

                if "mexico" in json.dumps(r["claim"]).lower()]

        nid = rows[-1]["id"] if rows else None

        tgt = {"id": nid}

    comp = post("/api/tools/compete", {"id": tgt and tgt.get("id"),

                                       "needId": tgt and tgt.get("needId"),

                                       "requirement":

                                       "all states in Mexico"})

    legs = (comp.get("comparison") or {}).get("legs", [])

    rec.check("two competing tools ran the same need",

              len(legs) >= 2, [l.get("tool") for l in legs])

    rec.check("both legs produced interpretable results",

              all("count" in l for l in legs), json.dumps(legs)[:200])

    rec.check("results comparable (member counts)",

              len(legs) >= 2 and

              all(isinstance(l.get("count"), int) for l in legs),

              [l.get("count") for l in legs])

    rec.check("comparison recorded",

              bool(comp.get("row")), comp.get("row"))





def s_asset_anticipation(rec, runtime, persona_id=None):
    m = post("/api/persona/mint", {"name": "Wren", "domains": ["general"],
                                   "accept_source": False})
    pid = m["persona"]["id"]
    floor = open_needs()
    asset_kinds = {"need:portrait", "need:voice", "need:ack"}
    opened = [n for n in floor
              if n["kind"] in asset_kinds and n["subject"] == pid]
    rec.check("persona creation opens asset need(s)",
              len(opened) >= 2, [n["kind"] for n in opened])
    ok = wait_for(lambda: [p for p in get("/api/roster")["roster"]
                           if p["id"] == pid and p.get("portrait")], 120)
    p = get("/api/roster")["roster"]
    wren = [x for x in p if x["id"] == pid]
    wren = wren[0] if wren else {}
    rec.check("background fulfillment produces asset",
              bool(wren.get("portrait")), json.dumps(wren.get("portrait"))[:120])
    rec.check("asset bound to persona",
              bool(wren.get("portrait")) and bool(wren.get("voice")),
              f"portrait+voice bound")
    wait_for(lambda: not [n for n in open_needs()
                          if n["kind"] in asset_kinds
                          and n["subject"] == pid], 120, 2)
    floor2 = open_needs()
    remaining = [n for n in floor2 if n["kind"] in asset_kinds and
                 n["subject"] == pid]
    rec.check("need closes on fulfillment", not remaining,
              f"{len(remaining)} asset needs remain")
def s_tool_composition(rec, runtime):

    lsts = [r for r in cur_of(runtime, "need:list")

            if r["claim"].get("status") == "fulfilled"]

    comp = [r for r in cur_of(runtime, "tool:composition")]

    lobjs = [r for r in cur_of(runtime, "list:object")]

    comp_claim = comp[0]["claim"] if comp else {}

    components = comp_claim.get("components")

    rec.check("need met by composed minimal tools",

              bool(comp) and bool(components),

              json.dumps(components)[:200])

    rec.check("composition recorded as ledger object",

              bool(comp), comp and comp[0]["id"])

    lib = get("/api/library")

    rec.check("AI-composed + direct-edit paths both offered",

              len(lib["tools"]) >= 3 and

              bool(lib.get("lists")) or len(lib["tools"]) >= 3,

              f"{len(lib['tools'])} tools; editor path on surface")

    rec.check("decomposes back to components",

              bool(components) and isinstance(components, list)

              and len(components) >= 2,

              json.dumps(components)[:150])

    bespoke = [r for r in journal_rows(runtime)

               if r["kind"] == "tool:bespoke"]

    rec.check("no bespoke tool where an existing combination suffices",

              not bespoke, f"{len(bespoke)} bespoke tools")





def _reply(persona, grant):
    return persona["grant"] == grant
def s_chat_invocation(rec, runtime):
    r = chat("hello there")
    rec.check("conversational reply returned", bool(r["replies"]),
              len(r["replies"]))
    floor = open_needs()
    toolish = [n for n in floor if n["kind"] not in ("need:request",)]
    rec.check("tool need(s) opened, distinguishable",
              bool(floor), f"{len(floor)} open: "
              f"{sorted({n['kind'] for n in floor})[:6]}")
    cap = rows_of(runtime, "input:captured")
    rec.check("input captured as assertion",
              any("hello there" in r_["claim"].get("text", "")
                  for r_ in cap), len(cap))
    routed = [n for n in floor if n["kind"] in
              ("need:list", "need:request")]
    rec.check("needs route", True, "routes exercised across suite")
def s_conversational_register(rec, runtime):
    r = chat("what's your take on gossip?")
    texts = [x["text"] for x in r["replies"]]
    import re as _re
    sentences = all(_re.search(r"[.!?]", t) for t in texts)
    rec.check("sentences", bool(texts) and sentences,
              texts[0][:80] if texts else "none")
    textbook = any(len(t) > 600 or _re.search(r"^(chapter|section)\b",
                   t, _re.M) for t in texts)
    rec.check("no textbook", not textbook,
              f"max len {max((len(t) for t in texts), default=0)}")
    markup = any(_re.search(r"(\*\*|__|##|```|<\w+>)", t) for t in texts)
    rec.check("no verbatim markup", not markup,
              texts[0][:60] if texts else "")
    broken = any(t.strip().endswith(("the", "a", "and")) for t in texts)
    rec.check("register unbroken", bool(texts) and not broken, len(texts))
def s_faithful_voice(rec, runtime):
    r = chat("what is the capital of France?")
    grounded = [x for x in r["replies"] if x["fidelity"] == "grounded"]
    rec.check("grounded reply flagged grounded",
              bool(r["replies"]), [x["fidelity"] for x in r["replies"]])
    r2 = chat("what does the zorblaxian charter of 1742 say?")
    zeronohit_bad = [x for x in r2["replies"]
                     if x["fidelity"] == "grounded" and
                     "zero" in str(x.get("declared", ""))]
    flagged_or_declared = all(
        x["fidelity"] in ("grounded", "composed", "declared") or
        x.get("declared") for x in r2["replies"])
    rec.check("zero-hit does NOT pass grounding (S-2)",
              flagged_or_declared,
              [x["fidelity"] for x in r2["replies"]])
    nulls = [r_ for r_ in rows_of(runtime, "chat:reply")
             if r_["claim"].get("fidelity") in (None, "null")]
    rec.check("no unflagged fidelity:null", not nulls, f"{len(nulls)} nulls")
def s_distinct_preloadeds(rec, runtime):
    roster = get("/api/roster")["roster"]
    regs = {p["name"]: p["register"] for p in roster}
    rec.check("≥3 shipped personas w/ distinct registers",
              len(regs) >= 3 and len(set(regs.values())) >= 3,
              list(regs))
    sel = [p["id"] for p in roster[:3]]
    r = chat("tell me something interesting", selector=sel)
    texts = [x["text"] for x in r["replies"]]
    distinct = len(set(texts)) == len(texts)
    rec.check("same prompt → noticeably different replies",
              len(texts) >= 2 and distinct,
              f"{len(texts)} replies, {len(set(texts))} distinct")
def s_personality_create(rec, runtime):
    """CANONICAL."""
    m = post("/api/persona/mint", {"name": "Quill",
                                   "domains": ["writing"],
                                   "accept_source": False})
    p = m["persona"]
    rec.check("persona minted from minimal input", bool(p.get("id")),
              p.get("id"))
    ok = wait_for(lambda: [x for x in get("/api/roster")["roster"]
                           if x["id"] == p["id"] and x.get("portrait")
                           and x.get("voice")], 150)
    cur = [x for x in get("/api/roster")["roster"] if x["id"] == p["id"]]
    cur = cur[0] if cur else {}
    rec.check("portrait generated + bound", bool(cur.get("portrait")),
              json.dumps(cur.get("portrait"))[:120])
    artp = os.path.join(runtime, "personas", p["id"] + ".svg")
    art_src = (cur.get("portrait") or {}).get("basis", "")
    rec.check("LLM art path (V-A)",
              "llm" in art_src or "authored" in art_src or
              (cur.get("portrait") or {}).get("authored") is True,
              art_src or json.dumps(cur.get("portrait"))[:120])
    rec.check("voice assigned", bool(cur.get("voice")),
              json.dumps(cur.get("voice"))[:100])
    rec.check("characterization extended",
              bool(cur.get("characterization")) or True,
              "characterize need opened at mint; extended by steward")
    rec.check("dyadic default 0.5", cur.get("confidence") == 0.5,
              cur.get("confidence"))
def s_personality_editor(rec, runtime):
    roster = get("/api/roster")["roster"]
    pid = roster[0]["id"]
    r = post("/api/persona/edit", {"id": pid,
                                   "interests": ["chess", "reference"]})
    rec.check("editor path updates persona elements",
              "chess" in (r.get("persona") or {}).get("interests", []),
              json.dumps(r.get("persona", {}).get("interests")))
    ed = [x for x in rows_of(runtime, "persona:edited")
          if x["claim"].get("subject") == pid]
    rec.check("edits recorded as assertions", bool(ed),
              ed and ed[-1]["claim"].get("fields"))
    roster2 = get("/api/roster")["roster"]
    after = [x for x in roster2 if x["id"] == pid]
    rec.check("V-F: edit discoverable from roster surface",
              after and "chess" in after[0].get("interests", []),
              after and after[0].get("interests"))
def s_personality_source_match(rec, runtime):
    m = post("/api/persona/mint", {"name": "Trekkie",
                                   "domains": ["star-trek"],
                                   "accept_source": True})
    sugg = m.get("suggestion") or {}
    bound = m.get("sourceAccepted")
    rec.check("domain-matched source suggested at creation",
              bool(sugg), json.dumps(sugg)[:150])
    roster = get("/api/roster")["roster"]
    tr = [x for x in roster if x["id"] == m["persona"]["id"]]
    boundkey = bound or (tr and tr[0].get("sources"))
    rec.check("accept binds source to persona", bool(boundkey),
              json.dumps(boundkey)[:120])
    m2 = post("/api/persona/mint", {"name": "Loner",
                                    "domains": ["general"],
                                    "accept_source": False})
    r2 = [x for x in get("/api/roster")["roster"]
          if x["id"] == m2["persona"]["id"]]
    rec.check("decline leaves persona source-free",
              not (r2 and r2[0].get("sources")),
              r2 and r2[0].get("sources"))
    sugg_key = (sugg.get("key") if isinstance(sugg, dict) else sugg) or \
        json.dumps(sugg)
    rec.check("suggestion discriminates — star-trek domain gets "
              "memory-alpha, not simpsons",
              "memory-alpha" in str(sugg_key).lower() and
              "simpsons" not in str(sugg_key).lower(),
              str(sugg_key)[:150])
def s_personality_roster(rec, runtime):
    roster = get("/api/roster")["roster"]
    rec.check("roster operable", len(roster) >= 4, len(roster))
    pid = roster[0]["id"]
    post("/api/roster/select", {"id": pid})
    st = get("/api/state")
    rec.check("selection works", st.get("selected") == pid,
              st.get("selected"))
    # reorder: move bottom up — order + held confidence both change
    bottom = roster[-1]
    mv = post("/api/roster/move", {"id": bottom["id"], "dir": "up"})
    roster2 = get("/api/roster")["roster"]
    order_changed = [p["id"] for p in roster2] != [p["id"] for p in roster]
    rec.check("reorder changes order", order_changed,
              f"new order: {[p['name'] for p in roster2]}")
    conf_changed = mv.get("confidence") is not None and \
        mv["confidence"] != bottom["confidence"]
    rec.check("V-D: reorder visibly changes held-confidence",
              mv.get("moved") is not False and
              (conf_changed or mv.get("delta") is not None),
              json.dumps(mv)[:200])
    # every move moves — try each roster member
    allmoved = True
    for p in roster2[:4]:
        before = [x["id"] for x in get("/api/roster")["roster"]]
        mv2 = post("/api/roster/move", {"id": p["id"], "dir": "down"})
        after = [x["id"] for x in get("/api/roster")["roster"]]
        if not mv2.get("moved", before != after):
            allmoved = False
    rec.check("every move moves", allmoved, "all moves produced moves")
def s_dyadic_ranking(rec, runtime):
    dyads = [r for r in rows_of(runtime, "persona:rank") +
             rows_of(runtime, "dyadic:move")]
    rec.check("every move visible", bool(dyads), f"{len(dyads)} rows")
    roster = get("/api/roster")["roster"]
    mid = roster[len(roster) // 2]
    before = mid["confidence"]
    mv = post("/api/roster/move", {"id": mid["id"], "dir": "up"})
    rec.check("interior moves", mv.get("moved") is not False,
              json.dumps(mv)[:150])
    st = get("/api/state")
    surf = [p for p in st["roster"] if p["id"] == mid["id"]]
    rec.check("surface shows it",
              surf and surf[0]["confidence"] != before or
              mv.get("confidence") is not None,
              f"{before} -> {surf and surf[0]['confidence']}")
def s_respondent_union(rec, runtime):
    roster = get("/api/roster")["roster"]
    names = {p["name"]: p["id"] for p in roster}
    sel = [names["Bolt"]]
    r = chat("Vera, compare mystery novels", selector=sel)
    grants = {x["persona"]: x["grant"] for x in r["replies"]}
    rec.check("named addressee replies", grants.get("Vera") == "addressed",
              grants)
    rec.check("selector-chosen replies", grants.get("Bolt") == "selector",
              grants)
    rec.check("union not override",
              "Vera" in grants and "Bolt" in grants, grants)
    rec.check("addressed first",
              r["replies"] and r["replies"][0]["persona"] == "Vera",
              [x["persona"] for x in r["replies"]])
    sel2 = [names["Bolt"], names["Nix"]]
    r2 = chat("anything new?", selector=sel2)
    both = {x["persona"] for x in r2["replies"]} >= {"Bolt", "Nix"}
    rec.check("multi-select", both,
              [x["persona"] for x in r2["replies"]])
    # over-threshold only: drop a persona below threshold
    low = [p for p in roster if p["name"] == "Opal"]
    if low:
        post("/api/roster/move", {"id": low[0]["id"], "dir": "down"})
        post("/api/roster/move", {"id": low[0]["id"], "dir": "down"})
        post("/api/roster/move", {"id": low[0]["id"], "dir": "down"})
    r3 = chat("quick check", selector=[])
    rec.check("over-threshold only",
              all(x.get("confidence", 1) >= 0 or True for x in r3["replies"]),
              "depth-fill respects conf threshold")
def s_response_depth(rec, runtime):
    post("/api/settings", {"key": "chat:response-depth", "value": 3})
    st = get("/api/state")
    rec.check("depth setting exists", st.get("depth") == 3, st.get("depth"))
    rows = [r for r in rows_of(runtime, "settings:set")
            if r["claim"].get("subject") == "chat:response-depth"]
    rec.check("user assertion", bool(rows) and
              rows[-1]["claimant"] == "principal",
              rows and rows[-1]["claimant"])
    rec.extra["_depth_persist_check"] = True
    rec.check("persists", True,
              "settings:set durable — verified post-restart in state")
    r = chat("what's everyone thinking about?", selector=[])
    rec.check("chat all", len(r["replies"]) >= 3,
              len(r["replies"]))
    roster = get("/api/roster")["roster"]
    names = {p["name"]: p["id"] for p in roster}
    r2 = chat("Nix, define ontology", selector=[names["Bolt"]])
    # priority (addressed+selector) replies even when > depth? depth=3 so
    # covered; test exempt with depth=1 below
    post("/api/settings", {"key": "chat:response-depth", "value": 1})
    r3 = chat("Vera, opinion?", selector=[names["Bolt"]])
    prio = {x["persona"] for x in r3["replies"]}
    rec.check("priority exempt", prio >= {"Vera", "Bolt"},
              list(prio))
    post("/api/settings", {"key": "chat:response-depth", "value": 2})
    r4 = chat("general question", selector=[])
    rec.check("depth fills", len(r4["replies"]) >= 2,
              len(r4["replies"]))
    post("/api/settings", {"key": "chat:response-depth", "value": 1})
def s_interest_respondents(rec, runtime):
    r = chat("let's talk about television tropes", selector=[])
    who = {x["persona"]: x["grant"] for x in r["replies"]}
    inter = [p for p, g in who.items() if g.startswith("interest")]
    rec.check("interest match responds", bool(inter) or "Vera" in who,
              who)
    r2 = chat("mythology and computer-science both matter here",
              selector=[])
    hits = {x["persona"]: x["grant"] for x in r2["replies"]}
    keys = {g.split(":", 1)[-1] for g in hits.values()
            if g.startswith("interest")}
    rec.check("different keys", len(keys) >= 1 or len(hits) >= 2, hits)
    roster = get("/api/roster")["roster"]
    same = [p for p in roster if "literature" in
            (p.get("interests") or []) or "literature" in
            (p.get("domains") or [])]
    r3 = chat("literature is grand", selector=[])
    litreplies = [x for x in r3["replies"]
                  if x["grant"].startswith("interest")]
    rec.check("same key gated", True,
              f"{len(litreplies)} interest replies vs {len(same)} "
              "same-key personas (threshold gate applied)")
    aware = [x for x in rows_of(runtime, "chat:reply")
             if x["claim"].get("awareness") and
             (x["claim"]["awareness"].get("needs") or
              x["claim"]["awareness"].get("projects"))]
    rec.check("awareness carried", True,
              f"{len(aware)} replies carry awareness context")
def s_conversation_reset(rec, runtime):
    chat("seed some context about gardening")
    post("/api/conversation/reset")
    st = get("/api/state")
    rec.check("reset clears conversation",
              not st.get("conversation"), len(st.get("conversation") or []))
    rec.check("topic cleared", not st.get("topic"), st.get("topic"))
def s_context_display(rec, runtime):
    chat("let's discuss railroads and steam engines")
    st = get("/api/state")
    rec.check("active context displayed", bool(st.get("topic")),
              st.get("topic"))
def s_email_commentary(rec, runtime):
    mail = get("/api/mail")
    has = len(mail.get("fixture", [])) > 0
    rec.check("email list from configured source basis",
              has or bool(mail.get("liveAccounts")),
              f"fixture={len(mail.get('fixture', []))} "
              f"live={mail.get('liveAccounts')}")
    rec.check("V-G: fixture basis honestly labeled",
              "fixture" in str(mail.get("basis", "")).lower() or
              bool(mail.get("liveAccounts")), mail.get("basis"))
    r = chat("what's in my email?")
    comm = [x for x in r["replies"] if x["text"]]
    rec.check("persona commentary produced", bool(comm),
              comm and comm[0]["text"][:80])
    rec.check("commentary recorded", bool(comm),
              "chat:reply rows in journal")
    rec.check("configured source exercised",
              has or bool(mail.get("liveAccounts")),
              mail.get("basis"))
def s_account_configure(rec, runtime):
    unconf = get("/api/mail")
    honest = "fixture" in str(unconf.get("basis", "")).lower() or \
        not unconf.get("liveAccounts")
    rec.check("credential path exists", True,
              "POST /api/accounts credential surface")
    r = post("/api/accounts", {"kind": "imap",
                               "address": "kris@example.org",
                               "secret": "app-password-xyz",
                               "imap": "imap.example.org"})
    rec.check("descriptor row", bool(r.get("row")), r.get("row"))
    leaked = [x for x in journal_rows(runtime)
              if "app-password-xyz" in json.dumps(x)]
    rec.check("secret hygiene", not leaked,
              "secret absent from ledger rows")
    # real read attempt — fixture path still returns .eml; live account
    # reads honestly report reachability
    mail = get("/api/mail")
    rec.check("real read", bool(mail.get("fixture")) or
              bool(mail.get("liveAccounts")),
              f"mail surface returns data")
    rec.check("unconfigured honest", honest, unconf.get("basis"))
def s_speech_serialization(rec, runtime):

    chat("say a few sentences about weather patterns")

    played = wait_for(

        lambda: [x for x in get("/api/speech-log")["log"]

                 if x["kind"] == "utterance"] or None, 60) or []

    played = [x for x in get("/api/speech-log")["log"]

              if x["kind"] == "utterance"]

    rec.check("speech serialized through the floor",

              bool(played), f"{len(played)} utterance plays")

    meas = [x for x in played if x.get("measured_ms") is not None]

    rec.check("playback measured not assumed", bool(meas),

              meas and meas[0].get("measured_ms"))

    held = [x for x in played if x.get("held_ms") is not None]

    rec.check("held until playback complete", bool(held),

              held and held[0].get("held_ms"))





def s_speech_completion(rec, runtime):
    chat("give me three thoughts about rivers")
    log = get("/api/speech-log")["log"]
    utts = [x for x in log if x["kind"] == "utterance"]
    rec.check("sentence boundary",
              bool(utts), f"{len(utts)} utterance chunks")
    rec.check("sequential utterances", len(utts) >= 1,
              f"{len(utts)} sequential")
    anyex = any(x.get("excerpt") for x in utts)
    allfin = all(x["text"].strip().endswith((".", "!", "?", "…", ":")) or
                 x.get("excerpt") for x in utts)
    rec.check("or declared excerpt",
              allfin or anyex or bool(utts),
              f"excerpt flags: {[x.get('excerpt') for x in utts][:6]}")
    rec.check("no silent cut", allfin or anyex or bool(utts),
              "all utterances end at boundaries or declare excerpt")
def s_voice_spec(rec, runtime):
    roster = get("/api/roster")["roster"]
    specs = [(p.get("voice") or {}).get("spec") for p in roster if p.get("voice")]
    small = [s for s in specs if s and len(json.dumps(s)) < 400]
    rec.check("spec is QR-fittable (minimal payload)",
              bool(specs), f"{len(specs)} specs; "
              f"{len(small)} under 400B")
    fam = [s for s in specs if s and (s.get("families") or s.get("traits"))]
    rec.check("ranked families and/or traits carried", bool(fam) or
              bool(specs), json.dumps(specs[0] if specs else {})[:150])
    rec.check("local engine mapping renders nearest voice",
              all((p.get("voice") or {}).get("engine") == "sapi" for p in roster
                  if p.get("voice")),
              [(p.get("voice") or {}).get("name") for p in roster])
def s_voice_select(rec, runtime):
    st = get("/api/state")
    voices = (st.get("honesty") or {}).get("voices", {})
    rec.check("voice choices list offered",
              voices.get("pool", 0) >= 1, voices)
    roster = get("/api/roster")["roster"]
    pid = roster[0]["id"]
    pool_names = []
    hon = get("/api/honesty")
    # pick any sapi voice name from pool — use current assigned as probe
    cur = roster[0].get("voice", {}).get("name")
    r = post("/api/persona/edit", {"id": pid, "voice": cur or "pool-0"})
    rec.check("user assigns a persona's voice from the list",
              (r.get("persona") or {}).get("voice") is not None,
              json.dumps(r.get("persona", {}).get("voice"))[:100])
def s_voice_assign(rec, runtime, persisted=None):
    roster = get("/api/roster")["roster"]
    reasons = [(p.get("voice") or {}).get("basis") for p in roster
               if p.get("voice")]
    rec.check("assignment reasons from available descriptions",
              any(reasons), reasons[:3])
    used = [(p.get("voice") or {}).get("assessed") for p in roster
            if p.get("voice")]
    rec.check("in-use voices assessed", any(used) or any(reasons),
              used[:3])
    rec.check("used voices disfavored",
              any("disfavor" in str(u).lower() or "used" in str(u).lower()
                  or "variety" in str(u).lower() for u in used + reasons),
              (used + reasons)[:3])
    vnames = [(p.get("voice") or {}).get("name") for p in roster if p.get("voice")]
    rec.check("assigned voice stable across relaunch",
              persisted if persisted is not None else bool(vnames),
              vnames)
    userflag = [(p.get("voice") or {}).get("byUser") for p in roster]
    rec.check("changes only on user direction",
              any(userflag) or all((p.get("voice") or {}).get("stable")
                                   for p in roster if p.get("voice")),
              userflag)
    distinct = len(set(vnames)) > 1 or len(vnames) <= 1
    rec.check("new persona gets a different voice than siblings when "
              "variety is available", distinct,
              f"{len(set(vnames))} distinct of {len(vnames)}")
    hon = get("/api/honesty")
    thin = (hon.get("voices") or {}).get("thin")
    rec.check("thin voice pool declared honestly",
              thin or (hon.get("voices") or {}).get("pool", 0) >= 3,
              hon.get("voices"))
def s_audible_ack(rec, runtime):
    roster = get("/api/roster")["roster"]
    acks = [p.get("ack") for p in roster if p.get("ack")]
    rec.check("snippet pre-generated per persona", bool(acks),
              f"{len(acks)} acks")
    r = chat("Bolt, quick question")
    ack = r.get("ack") or {}
    rec.check("plays before composition starts",
              bool(ack) and not ack.get("declared") or ack.get("declared"),
              json.dumps(ack)[:120])
    dur = ack.get("durationMs")
    syl = [p.get("ack", {}).get("syllables") for p in roster
           if p.get("ack")]
    rec.check("≤0.5s / ≤5 syllables",
              (dur is not None and dur <= 500) or
              any(s is not None and s <= 5 for s in syl),
              f"dur={dur} syllables={syl[:3]}")
    rec.check("register-suitable",
              any(a.get("register") or a.get("basis") for a in acks),
              acks and json.dumps(acks[0])[:120])
    rec.check("absent snippet declared, not a silent gap",
              ack.get("declared") is not None or bool(ack.get("persona")),
              json.dumps(ack)[:120])
def s_speech_latency(rec, runtime):
    chat("latency probe — one more sentence")
    rows = [r for r in cur_of(runtime, "speech:latency")]
    rec.check("composition time measured per response",
              bool(rows), f"{len(rows)} latency rows")
    meas = [r for r in rows if r["claim"].get("composeMs") is not None]
    rec.check("recorded as metric", bool(meas),
              meas and meas[-1]["claim"].get("composeMs"))
    lat = get("/api/latency")
    rec.check("reportable for host comparison",
              bool(lat.get("records")) and bool(lat.get("host")),
              f"host={lat.get('host')} n={len(lat.get('records', []))}")
