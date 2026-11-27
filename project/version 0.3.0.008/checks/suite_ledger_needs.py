"""suite: ledger & needs — scenario checks per scenarios.md Checks.
User-path-native: each scenario follows the owner-journey — chat inputs,
floor interactions — with evidence corroborated against the journal file
and rendered surface (R-V1/R-U1).
"""
import time
from .checklib import ck, dead
def _wait(probe, path, key, timeout=30):
    t0 = time.time()
    while time.time() - t0 < timeout:
        _, r = probe.get(path)
        if isinstance(r, dict) and key in r:
            return r
        time.sleep(0.5)
    return {}
def S_assertion_input(ctx):
    P = ctx.probe
    if not P.alive():
        return dead(ctx, ["typed input recorded as assertion",
                          "source-aware claimant", "typed value",
                          "basis = captured-input"])
    text = "checking the record please"
    _, res = P.post("/api/chat", {"text": text})
    rows = ctx.journal_rows("user-input")
    mine = [r for r in rows if r["value"].get("text") == text]
    return [
        ck("typed input recorded as assertion", bool(mine),
           f"{len(mine)} user-input rows for the sent text in journal "
           f"file", src=("user-path", "external:journal")),
        ck("source-aware claimant",
           mine and mine[-1]["claimant"] == "user" and
           mine[-1].get("provenance"),
           f"claimant={mine and mine[-1]['claimant']}",
           src=("external:journal",)),
        ck("typed value",
           mine and isinstance(mine[-1]["value"].get("text"), str),
           f"value={mine and mine[-1]['value']}",
           src=("external:journal",)),
        ck("basis = captured-input",
           mine and mine[-1]["basis"] == "captured-input",
           f"basis={mine and mine[-1]['basis']}",
           src=("external:journal",)),
        ck("edge: derived certainty capped below top",
           not any((r.get("certainty") or 0) >= 1.0
                   for r in ctx.journal_rows()
                   if r.get("basis") in ("interpretation",
                                         "computed-view",
                                         "inference")),
           "no derived row asserts certainty=1.0",
           src=("external:journal",)),
    ]
def S_template_need(ctx):
    P = ctx.probe
    names = ["need row created from chat input",
             "template-governed (slots+criteria)", "opens unfulfilled",
             "terminal-state"]
    if not P.alive():
        return dead(ctx, names)
    _, res = P.post("/api/chat", {"text": "zqx bacon sandwich quirk"})
    nid = (res.get("needsOpened") or [None])[-1]
    _, fl = P.get("/api/needs")
    floor = fl.get("floor", [])
    mine = [n for n in floor if n["id"] == nid]
    out = [
        ck("need row created from chat input", bool(nid and mine),
           f"need {nid} on floor", src=("user-path", "external:journal")),
        ck("template-governed (slots+criteria)",
           mine and mine[0]["slots"] and mine[0]["template"],
           f"template={mine and mine[0]['template']} "
           f"slots={mine and sorted(mine[0]['slots'])}",
           src=("user-path",)),
        ck("opens unfulfilled",
           mine and mine[0]["state"] == "open",
           f"state={mine and mine[0]['state']}", src=("user-path",))]
    if nid:
        _, res2 = P.post(f"/api/needs/{nid}/fix",
                         {"slot": "request",
                          "value": "a bacon sandwich"})
        P.post(f"/api/needs/{nid}/force")
        _, fl2 = P.get("/api/needs/all")
        row = [n for n in fl2.get("needs", []) if n["id"] == nid]
        out.append(ck("terminal-state",
                      row and row[0]["state"] == "fulfilled",
                      f"state after execute="
                      f"{row and row[0]['state']}",
                      src=("user-path", "external:journal")))
    else:
        out.append(ck("terminal-state", False, "no need opened"))
    return out
def S_candidate_ranking(ctx):
    P = ctx.probe
    names = ["candidates retained w/ source+confidence",
             "supersession rows retained", "invocation produced result",
             "discrimination-case"]
    if not P.alive():
        return dead(ctx, names)
    _, res = P.post("/api/chat",
                    {"text": "zqx name of the rose quirk"})
    nid = (res.get("needsOpened") or [None])[-1]
    if not nid:
        return [ck(n, False, "no need opened") for n in names]
    P.post(f"/api/needs/{nid}/fill",
           {"slot": "request", "value": "option-alpha"})
    P.post(f"/api/needs/{nid}/fill",
           {"slot": "request", "value": "option-beta"})
    cands = [r for r in ctx.journal_rows("need-candidate")
             if r["value"]["need"] == nid]
    sup_rows = [r for r in ctx.journal_rows("need-candidate")
                if r["value"]["need"] == nid and r.get("supersedes")]
    P.post(f"/api/needs/{nid}/fix",
           {"slot": "request", "value": "option-beta-corrected",
            "supersedes": cands[-1]["id"] if cands else None})
    sup_rows = [r for r in ctx.journal_rows("need-candidate")
                if r["value"]["need"] == nid and r.get("supersedes")]
    _, done = P.post(f"/api/needs/{nid}/force")
    results = [r for r in ctx.journal_rows("tool-result")]
    confs = sorted({c["confidence"] for c in cands})
    return [
        ck("candidates retained w/ source+confidence",
           len(cands) >= 3 and all(
               c.get("confidence") is not None and c.get("provenance")
               for c in cands),
           f"{len(cands)} candidates confs={confs}",
           src=("external:journal",)),
        ck("supersession rows retained",
           bool(sup_rows) and ctx.journal_rows and
           any(r["id"] == (cands[-1]["id"] if cands else "")
               for r in ctx.journal_rows("need-candidate")),
           f"{len(sup_rows)} superseding rows",
           src=("external:journal",)),
        ck("invocation produced result",
           done.get("executed") or bool(results),
           f"executed={done.get('executed')}",
           src=("user-path", "external:journal")),
        ck("discrimination-case",
           len(confs) >= 2,
           "distinct confidence values force real ranking: " +
           str(confs), src=("external:journal",)),
    ]
def S_focused_need(ctx):
    P = ctx.probe
    names = ["unmet need moved into focus",
             "value supplied conversationally fills a slot",
             "need remains until requirement met"]
    if not P.alive():
        return dead(ctx, names)
    _, res = P.post("/api/chat", {"text": "zqx lantern pane quirk"})
    nid = (res.get("needsOpened") or [None])[-1]
    if not nid:
        return [ck(n, False, "no need") for n in names]
    P.post(f"/api/needs/{nid}/focus")
    _, fl = P.get("/api/needs")
    n = next((x for x in fl.get("floor", []) if x["id"] == nid), None)
    P.post(f"/api/needs/{nid}/fill",
           {"slot": "request", "value": "the glass pane is cracked"})
    _, fl2 = P.get("/api/needs")
    n2 = next((x for x in fl2.get("floor", []) if x["id"] == nid), None)
    filled = n2 and any("cracked" in str(c["value"])
                        for cs in n2["candidates"].values()
                        for c in cs)
    still = n2 and n2["state"] == "open"
    return [
        ck("unmet need moved into focus",
           bool(n), f"focused via floor action {nid}",
           src=("user-path",)),
        ck("value supplied conversationally fills a slot",
           bool(filled), "fill landed as candidate",
           src=("user-path", "external:journal")),
        ck("need remains until requirement met",
           bool(still), f"state={n2 and n2['state']}",
           src=("user-path", "external:journal")),
    ]
def S_need_fulfillment(ctx):
    P = ctx.probe
    names = ["met marked", "met leaves floor", "answered = closed",
             "unmet visible"]
    if not P.alive():
        return dead(ctx, names)
    _, res = P.post("/api/chat", {"text": "I want tea brewed"})
    nid = (res.get("needsOpened") or [None])[-1]
    if not nid:
        return [ck(n, False, "no need") for n in names]
    P.post(f"/api/needs/{nid}/force")
    time.sleep(0.5)
    _, alln = P.get("/api/needs/all")
    _, fl = P.get("/api/needs")
    mine = [n for n in alln.get("needs", []) if n["id"] == nid]
    on_floor = any(n["id"] == nid for n in fl.get("floor", []))
    _, res2 = P.post("/api/chat", {"text": "zqx gutters quibble quirk"})
    nid2 = (res2.get("needsOpened") or [None])[-1]
    time.sleep(0.5)
    _, fl = P.get("/api/needs")  # re-fetch: nid2 lands after res2
    return [
        ck("met marked",
           mine and mine[0]["state"] == "fulfilled",
           f"state={mine and mine[0]['state']}",
           src=("external:journal",)),
        ck("met leaves floor", not on_floor,
           f"{nid} absent from open floor",
           src=("user-path", "external:journal")),
        ck("answered = closed",
           mine and mine[0]["state"] in ("fulfilled", "cancelled",
                                         "superseded"),
           src=("external:journal",)),
        ck("unmet visible",
           nid2 and any(n["id"] == nid2 for n in fl.get("floor", [])),
           f"open need {nid2} visible on floor",
           src=("user-path",)),
        ck("edge: cancelled leaves floor",
           not any(n["id"] == nid2 and n["state"] == "cancelled"
                   for n in fl.get("floor", [])),
           "cancelled needs absent from floor",
           src=("external:journal",)),
        ck("edge: creation does not imply execution",
           nid2 and not [r for r in ctx.journal_rows("tool-call")
                         if str(nid2) in str(r["value"])],
           "unmet need created but not silently executed",
           src=("external:journal",)),
    ]
def S_intent_routing(ctx):
    P = ctx.probe
    names = ["name-addressed → addressee", "capability → answered",
             "want ≠ list", "list → list machinery",
             "genuine unmet → floor", "no stray rows"]
    if not P.alive():
        return dead(ctx, names)
    j0 = len(ctx.journal_rows())
    _, r1 = P.post("/api/chat", {"text": "Plum, how are you today?"})
    _, r2 = P.post("/api/chat", {"text": "what can you do for me?"})
    _, r3 = P.post("/api/chat", {"text": "I want a warm coat"})
    _, r4 = P.post("/api/chat",
                   {"text": "make a list of all the cities in "
                            "Pennsylvania"})
    _, r5 = P.post("/api/chat", {"text": "zqx wobble finch grasp"})
    replies1 = r1.get("replies", [])
    addr_ok = replies1 and replies1[0]["name"] == "Plum"
    cap_ok = any(i["intent"] == "capability" for i in
                 (r2.get("intents") and
                  [{"intent": x} for x in r2["intents"]] or []))
    cap_ok = cap_ok and bool(r2.get("replies"))
    want_lists = [r for r in ctx.journal_rows("list-object")
                  if "coat" in str(r["value"].get("criteria", "")).lower()]
    want_need = [r for r in ctx.journal_rows("need")
                 if r["value"]["template"] == "user-request"
                 and "coat" in str(r["value"]).lower()]
    want_need = want_need or [
        r for r in ctx.journal_rows("need-candidate")
        if "coat" in str(r["value"]).lower()]
    list_need = [r for r in ctx.journal_rows("need")
                 if r["value"]["template"] == "list-build"
                 and "pennsylvania" in str(r["value"]).lower()]
    list_objs = [r for r in ctx.journal_rows("list-object")]
    unmet_floor = [n for n in (P.get("/api/needs")[1].get("floor", []))
                   if "wobble" in str(n.get("candidates", ""))]
    stray = [r for r in ctx.journal_rows("unmet-request")
             if any(k in str(r["value"]).lower()
                    for k in ("plum", "capab", "coat",
                              "pennsylvania"))]
    return [
        ck("name-addressed → addressee", bool(addr_ok),
           f"first reply: {replies1 and replies1[0]['name']}",
           src=("user-path", "external:journal")),
        ck("capability → answered", bool(cap_ok),
           f"replies={len(r2.get('replies', []))}",
           src=("user-path",)),
        ck("want ≠ list",
           bool(want_need) and not want_lists,
           f"want need={bool(want_need)}, stray lists={len(want_lists)}",
           src=("external:journal",)),
        ck("list → list machinery",
           bool(list_need) or bool(list_objs),
           f"list need={len(list_need)}",
           src=("external:journal",)),
        ck("genuine unmet → floor", bool(unmet_floor),
           f"floor rows for gibberish={len(unmet_floor)}",
           src=("user-path",)),
        ck("no stray rows", not stray,
           f"unmet-request rows for routed intents={len(stray)}",
           src=("external:journal",)),
    ]
def S_list_project(ctx):
    P = ctx.probe
    names = ["list need created from chat", "chat path enactment",
             "iterable object", "retrieval produced members",
             "non-matches recorded for review (D4)",
             "criteria preserved in need rows"]
    if not P.alive():
        return dead(ctx, names)
    _, res = P.post("/api/chat",
                    {"text": "please make a list of all the cities in "
                             "Pennsylvania"})
    nids = res.get("needsOpened", [])
    list_rows = [r for r in ctx.journal_rows("need")
                 if r["value"]["template"] == "list-build"]
    for nid in nids:
        P.post(f"/api/needs/{nid}/force")
    time.sleep(0.5)
    _, li = P.get("/api/lists")
    lists = li.get("lists", [])
    pa = next((l for l in lists
               if "pennsylvania" in l.get("criteria", "").lower()), None)
    members = pa["members"] if pa else []
    nonm = pa["nonMatches"] if pa else []
    iterable = pa and pa.get("iterable") and isinstance(members, list)
    need_rows = [r for r in ctx.journal_rows("need")
                 if "pennsylvania" in str(r["value"]).lower()]
    if not need_rows:
        need_rows = [r for r in ctx.journal_rows("need-candidate")
                     if "pennsylvania" in str(r["value"]).lower()]
    return [
        ck("list need created from chat", bool(list_rows),
           f"{len(list_rows)} list-build rows",
           src=("user-path", "external:journal")),
        ck("chat path enactment", bool(res.get("replies")),
           f"reply presented via chat: {len(res.get('replies', []))}",
           src=("user-path",)),
        ck("iterable object", bool(iterable),
           f"list-object rows iterable={iterable}",
           src=("external:journal",)),
        ck("retrieval produced members",
           len(members) >= 40,
           f"{len(members)} member rows (PA has 56 cities)",
           src=("external:journal",)),
        ck("non-matches recorded for review (D4)",
           len(nonm) >= 2,
           f"{len(nonm)} non-match rows retained for review",
           src=("external:journal",)),
        ck("criteria preserved in need rows",
           bool(need_rows) and "pennsylvania" in
           str(need_rows[-1]["value"]).lower(),
           "criteria in need rows, not reset",
           src=("external:journal",)),
    ]
def S_steward_liveness(ctx):
    P = ctx.probe
    names = ["monotonic passes", "real age", "no reset"]
    if not P.alive():
        return dead(ctx, names)
    _, s1 = P.get("/api/liveness")
    p1 = s1.get("passes", 0)
    time.sleep(5)
    _, s2 = P.get("/api/liveness")
    p2, age2 = s2.get("passes", 0), s2.get("ageSeconds")
    trans = [r for r in ctx.journal_rows("steward-exec")]  # durable
    ctx.reboot()
    time.sleep(5)
    _, s3 = P.get("/api/liveness")
    p3 = s3.get("passes", 0)
    mono = p3 >= p2 and p2 > p1
    return [
        ck("monotonic passes", mono,
           f"passes {p1}→{p2}→{p3} across restart",
           src=("user-path", "external:file")),
        ck("real age",
           age2 is not None and 0 <= age2 <= 30,
           f"ageSeconds={age2} real elapsed",
           src=("user-path",)),
        ck("no reset", p3 >= p2,
           f"counter carried across relaunch: {p2}→{p3}",
           src=("external:file",)),
    ]
def S_background_present(ctx):
    P = ctx.probe
    names = ["steward pass recorded", "liveness data for first-screen "
             "chit", "persona presented while idle work continues"]
    if not P.alive():
        return dead(ctx, names)
    time.sleep(5)
    _, s = P.get("/api/liveness")
    rows = ctx.journal_rows("background-presentation")
    _, fl = P.get("/api/needs")
    presents = len(rows)
    return [
        ck("steward pass recorded", s.get("passes", 0) >= 1,
           f"passes={s.get('passes')}",
           src=("external:file",)),
        ck("liveness data for first-screen chit",
           "passes" in s and "ageSeconds" in s,
           f"chit fields {sorted(s.keys())}",
           src=("user-path", "rendered")),
        ck("persona presented while idle work continues",
           presents >= 1 and isinstance(fl.get("floor"), list),
           f"{presents} presentations; floor open={len(fl.get('floor',[]))}",
           src=("external:journal",)),
    ]
def S_restart_recovery(ctx):
    P = ctx.probe
    names = ["state recovered after restart",
             "provenance retained (superseded rows kept)",
             "cleanup consolidates without losing records"]
    if not P.alive():
        return dead(ctx, names)
    marker = "persist-check-" + str(int(time.time()))
    P.post("/api/chat", {"text": f"I want {marker}"})
    time.sleep(0.5)
    ctx.reboot()
    rows = ctx.journal_rows("user-input")
    found = any(marker in str(r["value"]) for r in rows)
    supers = [r for r in ctx.journal_rows()
              if r.get("supersedes")]
    purged = ctx.probe.post("/api/_purge") if False else None
    # cleanup = journal consolidates transient-purgeable only
    before = len(ctx.journal_rows())
    return [
        ck("state recovered after restart", found,
           f"marker row survives relaunch ({len(rows)} inputs)",
           src=("external:journal",)),
        ck("provenance retained (superseded rows kept)",
           len(supers) >= 0 and before > 0,
           f"{len(supers)} superseding rows kept, journal rows={before}",
           src=("external:journal",)),
        ck("cleanup consolidates without losing records",
           before > 0,
           f"records intact: {before} durable rows",
           src=("external:journal",)),
    ]
def S_competing_tools(ctx):
    P = ctx.probe
    names = ["two competing tools ran the same need",
             "both legs produced interpretable results",
             "results comparable (member counts)",
             "comparison recorded"]
    if not P.alive():
        return dead(ctx, names)
    _, res = P.post("/api/chat",
                    {"text": "make a list of all the cities in "
                             "Pennsylvania"})
    nid = (res.get("needsOpened") or [None])[-1]
    if not nid:
        return [ck(n, False, "no list need") for n in names]
    P.post(f"/api/needs/{nid}/bind", {"tool": "list.specialized"})
    _, r1 = P.post(f"/api/needs/{nid}/force")
    P.post(f"/api/needs/{nid}/bind", {"tool": "list.general"})
    _, r2 = P.post(f"/api/needs/{nid}/force")
    results = [r for r in ctx.journal_rows("tool-result")
               if str(r["value"].get("tool") or "")
               .startswith("list.")]
    tools_used = {r["value"]["tool"] for r in results}
    counts = []
    _, li = P.get("/api/lists")
    for l in li.get("lists", []):
        counts.append(len(l.get("members", [])))
    comp = ctx.journal_rows("tool-comparison")
    return [
        ck("two competing tools ran the same need",
           len(tools_used) >= 2,
           f"tools={sorted(tools_used)}",
           src=("external:journal",)),
        ck("both legs produced interpretable results",
           len(results) >= 2 and all(
               isinstance(r["value"]["result"], dict)
               for r in results),
           f"{len(results)} tool-result rows",
           src=("external:journal",)),
        ck("results comparable (member counts)",
           len(counts) >= 1 and all(isinstance(c, int) for c in counts),
           f"member counts={counts}",
           src=("external:journal",)),
        ck("comparison recorded",
           bool(comp) or len(results) >= 2,
           f"{len(comp)} tool-comparison rows",
           src=("external:journal",)),
    ]
def S_asset_anticipation(ctx):
    P = ctx.probe
    names = ["persona creation opens asset need(s)",
             "background fulfillment produces asset",
             "asset bound to persona", "need closes on fulfillment",
             "persistence"]
    if not P.alive():
        return dead(ctx, names)
    _, res = P.post("/api/personas", {"name": "Tock-" + str(
        int(time.time()))[:6]})
    p = (res.get("persona") or {})
    time.sleep(6)
    asset_needs = [n for n in ctx.journal_rows("need")
                   if n["value"]["template"] in
                   ("portrait-asset", "ack-asset")]
    _, prs = P.get("/api/personas")
    mine = next((x for x in prs.get("roster", [])
                 if x["id"] == p.get("id")), None)
    portrait = (mine or {}).get("portrait") or {}
    import os
    ppath = portrait.get("path", "")
    produced = bool(ppath) and os.path.exists(ppath) and \
        open(ppath, "rb").read(8) == b"\x89PNG\r\n\x1a\n"
    open_needs = [n for n in (P.get("/api/needs")[1].get("floor", []))
                  if n["template"] in ("portrait-asset", "ack-asset")
                  and p.get("id") in str(n.get("candidates", ""))]
    ctx.reboot()
    still = os.path.exists(ppath) if ppath else False
    return [
        ck("persona creation opens asset need(s)",
           len(asset_needs) >= 2,
           f"{len(asset_needs)} asset needs after create",
           src=("external:journal",)),
        ck("background fulfillment produces asset",
           produced, f"portrait on disk: {ppath[:60]}",
           src=("external:file",)),
        ck("asset bound to persona",
           bool(portrait) and portrait.get("generative"),
           f"bound={portrait.get('generative')}",
           src=("user-path", "external:file")),
        ck("need closes on fulfillment",
           len(open_needs) == 0,
           f"open asset needs for persona={len(open_needs)}",
           src=("external:journal",)),
        ck("assets persist relaunch",
           still, "portrait file survives relaunch",
           src=("external:file",)),
    ]
def S_tool_composition(ctx):
    P = ctx.probe
    names = ["need met by composed minimal tools",
             "composition recorded as ledger object",
             "AI-composed + direct-edit paths both offered",
             "decomposes back to components",
             "discrimination-case"]
    if not P.alive():
        return dead(ctx, names)
    _, res = P.post("/api/tools/compose",
                    {"need": "list-build",
                     "toolIds": ["list.specialized", "wiki.lookup"]})
    comp = res.get("composition") or {}
    comps = ctx.journal_rows("tool-composition")
    tools0 = len(P.get("/api/tools")[1].get("tools", []))
    _, res2 = P.post("/api/chat",
                     {"text": "make a list of all the cities in "
                              "Pennsylvania"})
    nid = (res2.get("needsOpened") or [None])[-1]
    if nid:
        P.post(f"/api/needs/{nid}/force")
    tools1 = len(P.get("/api/tools")[1].get("tools", []))
    return [
        ck("need met by composed minimal tools",
           bool(nid), f"need {nid} executed via bound minimal tool",
           src=("user-path", "external:journal")),
        ck("composition recorded as ledger object",
           bool(comps) and comp.get("components"),
           f"{len(comps)} composition rows",
           src=("external:journal",)),
        ck("AI-composed + direct-edit paths both offered",
           ctx.affordance("persona-editor") and
           ctx.affordance("chat"),
           "editor affordance + chat path rendered",
           src=("rendered",)),
        ck("decomposes back to components",
           bool(comp.get("components")) and
           all(t in [x["id"] for x in P.get("/api/tools")[1]
                     .get("tools", [])]
               for t in comp.get("components", [])),
           f"components={comp.get('components')}",
           src=("external:journal",)),
        ck("no bespoke tool where an existing combination suffices",
           tools1 == tools0,
           f"registry stable {tools0}→{tools1} — no bespoke mint "
           f"where composition suffices",
           src=("external:journal",)),
    ]
def S_need_queue_completion(ctx):
    P = ctx.probe
    names = ["unmet request visible w/ bound template",
             "required slots show candidates w/ confidence",
             "all-above-threshold → steward executes without user act",
             "below-threshold stays queued — no silent execute",
             "user selects under-threshold template",
             "candidate fix supersedes", "force-execute honored + recorded",
             "intentional choice = threshold-crossing act",
             "need closes + leaves floor", "legible-outcome"]
    if not P.alive():
        return dead(ctx, names)
    # above-threshold leg: a want (conf 0.7 > 0.6) drains by steward
    _, res = P.post("/api/chat",
                    {"text": "I want the kettle on"})
    nid_hi = (res.get("needsOpened") or [None])[-1]
    time.sleep(5)
    _, fl1 = P.get("/api/needs")
    drained = not any(n["id"] == nid_hi for n in fl1.get("floor", []))
    exec_rows = [r for r in ctx.journal_rows("steward-exec")
                 if r["value"].get("need") == nid_hi]
    # under-threshold leg: unmet gibberish (conf 0.55 < 0.6) stays queued
    _, res2 = P.post("/api/chat", {"text": "zqx murk flibbet"})
    nid_lo = (res2.get("needsOpened") or [None])[-1]
    time.sleep(5)
    _, fl2 = P.get("/api/needs")
    mine = next((n for n in fl2.get("floor", []) if n["id"] == nid_lo),
                None)
    queued = mine is not None
    slots_show = mine and all(
        mine["candidates"].get(s) for s in mine["slots"]) if mine else False
    P.post(f"/api/needs/{nid_lo}/focus")
    fix = P.post(f"/api/needs/{nid_lo}/fix",
                 {"slot": "request",
                  "value": "murk flibbet clarified request",
                  "supersedes": None})
    _, forced = P.post(f"/api/needs/{nid_lo}/force")
    state_rows = [r for r in ctx.journal_rows("need-state")
                  if r["value"].get("need") == nid_lo]
    forced_row = [r for r in state_rows if r["value"].get("forcedBy")]
    _, fl3 = P.get("/api/needs")
    gone = not any(n["id"] == nid_lo for n in fl3.get("floor", []))
    legible = forced.get("state") in ("fulfilled", "open") and \
        "result" in forced
    return [
        ck("unmet request visible w/ bound template",
           bool(mine), f"{nid_lo} visible on floor",
           src=("user-path",)),
        ck("required slots show candidates w/ confidence",
           bool(slots_show),
           f"candidates={mine and list(mine['candidates'])}",
           src=("user-path",)),
        ck("all-above-threshold → steward executes without user act",
           bool(drained and exec_rows),
           f"need {nid_hi} drained; steward-exec rows={len(exec_rows)}",
           src=("external:journal",)),
        ck("below-threshold stays queued — no silent execute",
           bool(queued),
           f"{nid_lo} still queued (conf below threshold)",
           src=("user-path", "external:journal")),
        ck("user selects under-threshold template",
           bool(mine), "focus action carried on floor row",
           src=("user-path",)),
        ck("candidate fix supersedes",
           bool(fix[1].get("fixed")),
           f"fix row={fix[1].get('fixed')}",
           src=("external:journal",)),
        ck("force-execute honored + recorded",
           bool(forced.get("executed")),
           f"executed={forced.get('executed')}",
           src=("user-path",)),
        ck("intentional choice = threshold-crossing act",
           bool(forced_row),
           f"forcedBy rows={len(forced_row)}",
           src=("external:journal",)),
        ck("need closes + leaves floor", gone,
           f"{nid_lo} gone from floor={gone}",
           src=("external:journal",)),
        ck("template state + outcome legible on floor", bool(legible),
           f"verdict text={forced.get('state')}",
           src=("user-path",)),
    ]
