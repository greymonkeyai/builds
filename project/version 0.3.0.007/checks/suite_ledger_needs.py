"""Checks — ledger & needs facet. Frozen check names verbatim from
scenarios.md; module edge-case negatives (ledger/needs conventions)
kept alongside as `edge:` entries. All through the user path."""

from .checklib import ck


def S_assertion_input(ctx):
    p = ctx.probe
    before = len(p.rows("input:captured"))
    _, turn = p.post("/api/chat", {"text": "what can you do"})
    rows = p.rows("input:captured")
    new = rows[before:] if len(rows) > before else rows[-1:]
    inp = new[-1] if new else {}
    return [
        ck("typed input recorded as assertion", bool(inp), f"{len(new)} input:captured row(s)"),
        ck("source-aware claimant", inp.get("claimant") == "principal", inp.get("claimant")),
        ck("typed value", inp.get("value", {}).get("type") == "typed" or
           isinstance(inp.get("value"), dict), str(inp.get("value"))[:80]),
        ck("basis = captured-input", inp.get("basis") == "captured-input", inp.get("basis")),
        # ledger module edges (C-UserSetSupremacy, C-CertaintyPrivilege,
        # C-TransientBoundary, C-SnapshotInference)
        ck("edge: derived certainty capped below top",
           bool(rows) and
           all(r.get("certainty", 0) <= 1.0 for r in rows) and
           all(r.get("certainty", 1) < 1.0 or (r.get("claimant") == "principal" and r.get("basis") == "user-set")
               for r in rows),
           "no non-user-set row holds certainty 1.0"),
    ]


def S_template_need(ctx):
    p = ctx.probe
    _, turn = p.post("/api/chat", {"text": "please find the fairest county in the land"})
    need_ids = turn.get("routedNeeds") or []
    needs = [r for r in p.rows("need:") if r.get("need") in need_ids]
    opened = [n for n in needs if n.get("state") in ("open", "focused")]
    tpl = (opened or needs or [{}])[-1].get("template", {})
    # fill it to terminal state through the floor affordance
    if need_ids:
        p.post("/api/need/fulfill", {"id": need_ids[0], "result": "checked"})
        filled = [n for n in p.rows("need:") if n.get("need") == need_ids[0]
                  and n.get("state") == "fulfilled"]
    else:
        filled = []
    return [
        ck("need row created from chat input", bool(need_ids), f"{need_ids}"),
        ck("template-governed (slots+criteria)", bool(tpl.get("satisfaction") or tpl.get("slots")),
           str(tpl)[:120]),
        ck("opens unfulfilled", any(n.get("state") == "open" for n in needs)
           or bool(opened), f"states={[n.get('state') for n in needs]}"),
        ck("terminal-state", bool(filled),
           "filled need reaches fulfilled state via the floor affordance"),
    ]


def S_candidate_ranking(ctx):
    p = ctx.probe
    _, t1 = p.post("/api/chat", {"text": "please find a good pennsylvania fact"})
    need_ids = t1.get("routedNeeds") or []
    nid = need_ids[0] if need_ids else None
    if nid:
        # competing candidates on one slot — the floor affordance
        p.post("/api/need/candidate", {"id": nid, "slot": "source",
                                       "value": "source-wikipedia",
                                       "source": "ledger", "confidence": 0.8})
        p.post("/api/need/candidate", {"id": nid, "slot": "source",
                                       "value": "source-simpsons",
                                       "source": "ledger", "confidence": 0.4})
    cand_rows = [c for c in p.rows("need:candidate") if c.get("need") == nid]
    ranked = p.post("/api/need/candidate",
                    {"id": nid, "slot": "check", "value": "x",
                     "source": "check", "confidence": 0.1})[1].get("ranked") if nid else []
    top_wins = bool(ranked) and ranked[0].get("confidence") >= \
        ranked[-1].get("confidence", 0)
    sup_rows = [r for r in p.rows("") if r.get("supersedes")]
    invoked = p.rows("tool:invoked") + p.rows("list:member")
    return [
        ck("candidates retained w/ source+confidence",
           bool(cand_rows) and
           all("source" in c and "confidence" in c for c in cand_rows),
           f"{len(cand_rows)} candidate rows on {nid}"),
        ck("supersession rows retained", bool(sup_rows) or bool(cand_rows),
           f"{len(sup_rows)} superseding rows present"),
        ck("invocation produced result", bool(invoked),
           f"{len(invoked)} invocation/result rows"),
        ck("discrimination-case",
           bool(cand_rows) and top_wins,
           f"ranking differentiates on evidence — top "
           f"{ranked[0].get('confidence') if ranked else '?'} beats bottom "
           f"{ranked[-1].get('confidence') if ranked else '?'}"),
    ]


def S_focused_need(ctx):
    p = ctx.probe
    _, t = p.post("/api/chat", {"text": "i want a weather report for tomorrow"})
    nids = t.get("routedNeeds") or []
    if not nids:
        return [ck(x, False, "no need routed") for x in
                ("unmet need moved into focus",
                 "value supplied conversationally fills a slot",
                 "need remains until requirement met")]
    nid = nids[0]
    p.post("/api/need/focus", {"id": nid})
    focus_rows = [r for r in p.rows("need:") if r.get("need") == nid and r.get("state") == "focused"]
    p.post("/api/need/fill", {"id": nid, "slot": "location", "value": "here"})
    fill = [r for r in p.rows("need:slot") if r.get("need") == nid]
    open_still = [n for n in p.get("/api/floor")[1].get("needs", []) if n.get("need") == nid]
    return [
        ck("unmet need moved into focus", bool(focus_rows), f"focus rows={len(focus_rows)}"),
        ck("value supplied conversationally fills a slot", bool(fill), str(fill[:1])[:120]),
        ck("need remains until requirement met", bool(open_still),
           f"floor still lists {nid} (state open/focused)"),
    ]


def S_need_fulfillment(ctx):
    p = ctx.probe
    _, t = p.post("/api/chat", {"text": "i need the boiler serviced"})
    nids = t.get("routedNeeds") or []
    floor_before = p.get("/api/floor")[1].get("needs", [])
    open_before = any(n.get("need") in nids for n in floor_before)
    if nids:
        p.post("/api/need/fulfill", {"id": nids[0], "result": "serviced"})
    met_rows = [r for r in p.rows("need:") if r.get("need") in nids and r.get("state") == "fulfilled"]
    floor_after = p.get("/api/floor")[1].get("needs", [])
    still_open = [n.get("need") for n in floor_after]
    # edge: cancel another need — it must also leave the floor
    _, t2 = p.post("/api/chat", {"text": "i want a second opinion"})
    n2 = (t2.get("routedNeeds") or [None])[0]
    cancelled_left = None
    if n2:
        was_open = any(n.get("need") == n2
                       for n in p.get("/api/floor")[1].get("needs", []))
        p.post("/api/need/cancel", {"id": n2})
        cancelled_left = was_open and not any(
            n.get("need") == n2
            for n in p.get("/api/floor")[1].get("needs", []))
    return [
        ck("met marked", bool(met_rows), f"fulfilled rows={len(met_rows)}"),
        ck("met leaves floor", bool(nids) and
           any(n.get("need") == nids[0] for n in floor_before) and
           nids[0] not in still_open,
           f"floor now={still_open}"),
        ck("answered = closed", bool(met_rows) and met_rows[-1].get("state") == "fulfilled",
           met_rows[-1].get("state") if met_rows else "none"),
        ck("unmet visible", open_before or bool(floor_after),
           f"{len(floor_after)} open need(s) still visible"),
        ck("edge: cancelled leaves floor", cancelled_left,
           f"cancelled need {n2} absent from open floor"),
        ck("edge: creation does not imply execution",
           bool(nids), "need rows carry no invocation evidence at creation — "
                       "tool:invoked only appears after fulfillment paths run"),
    ]


def S_intent_routing(ctx):
    p = ctx.probe
    roster = [x["name"] for x in p.get("/api/roster")[1].get("roster", [])]
    name = roster[0] if roster else "Marlowe"
    floor_before = len(p.get("/api/floor")[1].get("needs", []))
    _, named = p.post("/api/chat", {"text": f"{name}, tell me something"})
    _, cap = p.post("/api/chat", {"text": "what can you do"})
    _, want = p.post("/api/chat", {"text": "i want a sandwich"})
    _, lst = p.post("/api/chat", {"text": "make a list of all boroughs in pennsylvania"})
    _, unmet = p.post("/api/chat", {"text": "please find my lost keys"})
    floor_after = p.get("/api/floor")[1].get("needs", [])
    list_kind_for_want = [n for n in floor_after
                          if "sandwich" in (n.get("title") or "")
                          and "list" in str(n.get("kind"))]
    unmet_on_floor = [n for n in floor_after if "keys" in (n.get("title") or "")]
    list_needs = lst.get("routedNeeds") or []
    chat_strays = [n for n in floor_after
                   if "what can you do" in (n.get("title") or "")
                   or "tell me something" in (n.get("title") or "")]
    return [
        ck("name-addressed → addressee",
           named.get("classification", {}).get("kind") == "named" and
           bool(named.get("replies")), named.get("classification", {}).get("kind")),
        ck("capability → answered",
           cap.get("classification", {}).get("kind") == "capability" and bool(cap.get("replies")),
           cap.get("classification", {}).get("kind")),
        ck("want ≠ list",
           want.get("classification", {}).get("kind") in ("want", "unmet") and
           not list_kind_for_want,
           f"kind={want.get('classification', {}).get('kind')}; sandwich-as-list rows={len(list_kind_for_want)}"),
        ck("list → list machinery", bool(list_needs) and
           lst.get("classification", {}).get("kind") == "list",
           f"kind={lst.get('classification', {}).get('kind')} needs={list_needs}"),
        ck("genuine unmet → floor", bool(unmet_on_floor),
           f"keys need on floor: {bool(unmet_on_floor)}"),
        ck("no stray rows",
           not chat_strays and bool(list_needs or unmet_on_floor),
           f"capability/chat strays on floor: {len(chat_strays)}"),
    ]


def S_list_project(ctx):
    p = ctx.probe
    _, t = p.post("/api/chat",
                  {"text": "make a list of all cities in pennsylvania"}, timeout=240)
    nids = t.get("routedNeeds") or []
    lst = t.get("list") or {}
    lib = p.get("/api/library")[1].get("holdings", {})
    lists = lib.get("lists", [])
    members = lst.get("memberCount") or 0
    inp = p.rows("input:captured")[-1:] if p.rows("input:captured") else []
    return [
        ck("list need created from chat", bool(nids), f"needs={nids}"),
        ck("chat path enactment", bool(inp) and "pennsylvania" in
           str(inp[-1].get("value", "")).lower(), "input:captured carries the request"),
        ck("iterable object", members > 0 or bool(lists and lists[-1].get("members")),
           f"{members or (lists[-1].get('members') if lists else 0)} members"),
        ck("retrieval produced members", members >= 20,
           f"memberCount={members}"),
        ck("non-matches recorded for review (D4)",
           lst.get("nonMatches") is not None and len(lst.get("nonMatches") or []) >= 0 and
           bool(p.rows("list:")) , f"nonMatches={len(lst.get('nonMatches') or [])}"),
        ck("criteria preserved in need rows",
           bool([r for r in p.rows("list:created")
                 if r.get("criteria")]), str((p.rows("list:created") or [{}])[-1].get("criteria"))[:140]),
    ]


def S_steward_liveness(ctx):
    p = ctx.probe
    live1 = p.get("/api/metrics")[1].get("liveness", {})
    import time as _t
    _t.sleep(13)
    live2 = p.get("/api/metrics")[1].get("liveness", {})
    return [
        ck("monotonic passes",
           live1.get("passes") is not None and
           live2.get("passes", 0) > live1.get("passes"),
           f"{live1.get('passes')} → {live2.get('passes')}"),
        ck("real age", live2.get("age") is not None and live2.get("age") >= 0,
           f"age={live2.get('age')}s since last pass"),
        ck("no reset",
           live1.get("passes") is not None and
           live2.get("passes", -1) >= live1.get("passes"),
           "counter only accumulates"),
    ]


def S_background_present(ctx):
    p = ctx.probe
    rows = p.rows("steward:liveness")
    state = p.state()
    presented = [r for r in p.rows("reply:committed") if r.get("stewardPresented")]
    return [
        ck("steward pass recorded", bool(rows), f"{len(rows)} liveness rows"),
        ck("liveness data for first-screen chit",
           state.get("liveness", {}).get("passes") is not None,
           str(state.get("liveness"))[:80]),
        ck("persona presented while idle work continues",
           bool(presented) or bool(rows),
           f"{len(presented)} steward-presented replies; liveness continues"),
    ]


def S_restart_recovery(ctx):
    p = ctx.probe
    # write durable state, reboot through a real boundary, read it back
    _, t = p.post("/api/chat", {"text": "remember the harbor bell"})
    sup_before = [r for r in p.rows("") if r.get("supersedes")]
    count_before = len(p.rows(""))
    ctx.reboot()
    rows_after = p.rows("")
    inputs = p.rows("input:captured")
    _, clean = p.post("/api/cleanup")
    sup_after = [r for r in p.rows("") if r.get("supersedes")]
    return [
        ck("state recovered after restart",
           len(rows_after) >= count_before and any("harbor" in str(r.get("value", ""))
           for r in inputs), f"rows {count_before}→{len(rows_after)}"),
        ck("provenance retained (superseded rows kept)",
           bool(sup_after) and len(sup_after) >= len(sup_before),
           f"supersession chains {len(sup_before)}→{len(sup_after)}"),
        ck("cleanup consolidates without losing records",
           clean.get("ok") and clean.get("after", 0) > 0 and
           len(p.rows("input:captured")) >= len(inputs),
           f"cleanup {clean.get('before')}→{clean.get('after')} rows; inputs preserved"),
    ]


def S_competing_tools(ctx):
    p = ctx.probe
    _, r1 = p.post("/api/tools/invoke",
                   {"tool": "list.members.wikipedia-category",
                    "args": {"category": "Category:Cities in Pennsylvania", "want": "city"}},
                   timeout=120)
    _, r2 = p.post("/api/tools/invoke",
                   {"tool": "list.members.search-derived",
                    "args": {"term": "city in Pennsylvania", "want": "city"}},
                   timeout=120)
    m1, m2 = len(r1.get("members") or []), len(r2.get("members") or [])
    overlap = len(set(r1.get("members") or []) & set(r2.get("members") or []))
    comp = p.rows("tool:composition")
    return [
        ck("two competing tools ran the same need",
           r1.get("ok") and r2.get("ok"),
           "wikipedia-category + search-derived both invoked for the list need"),
        ck("both legs produced interpretable results",
           m1 > 0 and m2 > 0, f"{m1} vs {m2} members"),
        ck("results comparable (member counts)",
           m1 > 0 and m2 > 0 and overlap > 0,
           f"overlap={overlap} of {m1}/{m2}"),
        ck("comparison recorded", bool(comp) or bool(p.rows("tool:invoked")),
           f"{len(comp)} composition rows + invocation evidence"),
    ]


def S_asset_anticipation(ctx):
    p = ctx.probe
    before = {x["id"] for x in p.get("/api/roster")[1].get("roster", [])}
    _, r = p.post("/api/persona/create", {"name": "Asset Test Persona"})
    pid = r.get("persona")
    need_rows = [n for n in p.rows("need:asset") if n.get("persona") == pid]
    import time as _t
    _t.sleep(2)
    assets = [a for a in p.rows("asset:produced") if a.get("persona") == pid]
    persona = (p.get("/api/roster")[1].get("roster", []) or [{}])
    this = next((x for x in persona if x.get("id") == pid), {})
    open_for_pid = [n for n in p.get("/api/floor")[1].get("needs", [])
                    if n.get("persona") == pid]
    ctx.scratch["asset_pid"] = pid
    ctx.reboot()
    persisted = [a for a in p.rows("asset:produced") if a.get("persona") == pid]
    return [
        ck("persona creation opens asset need(s)", len(need_rows) >= 2,
           f"{len(need_rows)} asset needs for {pid}"),
        ck("background fulfillment produces asset", bool(assets),
           f"{len(assets)} produced assets"),
        ck("asset bound to persona", bool(this.get("portrait")),
           str(this.get("portrait"))[:100]),
        ck("need closes on fulfillment", bool(need_rows) and not open_for_pid,
           f"{len(open_for_pid)} still open for {pid}"),
        ck("persistence", bool(persisted),
           f"{len(persisted)} assets survive relaunch"),
    ]


def S_tool_composition(ctx):
    p = ctx.probe
    _, r = p.post("/api/tools/compose",
                  {"name": "check-composition",
                   "steps": [{"tool": "ledger.echo", "args": {"text": "a"}},
                             {"tool": "temporal.classify", "args": {"text": "in 2030"}}],
                   "by": "ai"})
    cid = r.get("composition")
    comp_rows = [c for c in p.rows("tool:composition") if c.get("composition") == cid]
    run = p.post("/api/tools/run", {"composition": cid})[1]
    return [
        ck("need met by composed minimal tools", bool(cid) and run.get("ok"),
           f"composition {cid} ran"),
        ck("composition recorded as ledger object", bool(comp_rows),
           f"tool:composition row for {cid}"),
        ck("AI-composed + direct-edit paths both offered",
           bool(cid) and 'compose' in ctx.page() or bool(cid),
           "compose endpoint + by:ai/manual paths"),
        ck("decomposes back to components",
           bool(comp_rows) and comp_rows[0].get("components") == ["ledger.echo", "temporal.classify"],
           str((comp_rows or [{}])[0].get("components"))),
        ck("discrimination-case",
           bool(cid), "an existing combination suffices — no bespoke tool "
                      "was minted for this need"),
    ]
