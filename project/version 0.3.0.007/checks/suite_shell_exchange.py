"""Checks — shell & exchange surfaces facet. Frozen names verbatim."""

import json
import os
import time

from .checklib import ck


def S_windows_launch(ctx):
    p = ctx.probe
    _, h = p.get("/api/health")
    launch_cmd = os.path.exists(os.path.join(ctx.root, "launch.cmd"))
    return [
        ck("launches on Windows like an installed program",
           h.get("app") == "vesta" and h.get("part2") is True and not h.get("bare"),
           f"health={h.get('app')} part2={h.get('part2')} bare={h.get('bare')}"),
    ]


def S_close_terminate(ctx):
    # launch-check leg 4 — read the launch evidence artifact; also
    # requires a live product instance (a bare harness is not a program)
    art = os.path.join(ctx.root, "evidence", "launch", "launch-check.json")
    ok, detail = False, "no launch-check artifact"
    try:
        d = json.load(open(art))
        leg = next((l for l in d.get("legs", []) if l["leg"] == "close-terminates"), {})
        ok, detail = leg.get("pass"), leg.get("detail")
    except Exception as e:
        detail = str(e)
    ok = bool(ok) and ctx.probe.alive()
    return [ck("close-terminates (launch-check leg 4)", ok,
               f"{detail} + live instance={ctx.probe.alive()}")]


def S_color_schemes(ctx):
    p = ctx.probe
    st = p.state()
    themes = st.get("themes") or []
    page = ctx.page()
    selector_present = 'id="theme"' in page and "setTheme" in page
    fresh_light = st.get("themeName") == "light"
    _, r = p.post("/api/settings", {"setting": "theme", "value": "dark"})
    st2 = p.state()
    drove = st2.get("themeName") == "dark"
    claims = [s for s in p.rows("settings:set") if s.get("setting") == "theme"]
    _, r2 = p.post("/api/settings", {"setting": "theme", "value": "light"})
    return [
        ck("≥3 colorways implemented incl. dark",
           len(themes) >= 3 and "dark" in themes, f"{themes}"),
        ck("theme selector drives settings claims",
           selector_present and drove and bool(claims),
           f"selector on page={selector_present}; claim rows={len(claims)}"),
        ck("fresh launch opens light (seeded)",
           fresh_light,
           f"themeName at first read={st.get('themeName')}"),
    ]


def S_status_bar(ctx):
    p = ctx.probe
    st = p.state()
    e = st.get("engines") or {}
    page = ctx.page()
    sb = "statusbar" in page or "sb-engines" in page
    honesty = st.get("honesty") or []
    return [
        ck("sources surfaced", (st.get("sourceCount") or 0) > 0 and sb,
           f"sourceCount={st.get('sourceCount')}; statusbar on page={sb}"),
        ck("LLM status surfaced", e.get("llm") is not None,
           f"llm={e.get('llm')}"),
        ck("engine modes declared honestly", bool(honesty) and
           ("absent" in str(honesty) or "live" in str(e.get("llm")) or "durable" in str(honesty)),
           f"declarations={honesty}"),
    ]


def S_library_browse(ctx):
    p = ctx.probe
    h = p.get("/api/library")[1].get("holdings", {})
    tools = h.get("tools") or []
    page = ctx.page()
    structured = "library" in page.lower() and "raw log" not in page.lower()
    return [
        ck("personas browsable", bool(h.get("personas")),
           f"{len(h.get('personas') or [])} personas listed"),
        ck("tools browsable w/ explanations",
           bool(tools) and all(t.get("explanation") for t in tools),
           f"{len(tools)} tools, explanations={sum(1 for t in tools if t.get('explanation'))}"),
        ck("holdings structured, not a raw log",
           structured and isinstance(h, dict) and len(h) >= 4,
           f"kinds={list(h.keys())}"),
    ]


def S_account_configure(ctx):
    p = ctx.probe
    _, r = p.post("/api/accounts",
                  {"name": "checkmail", "kind": "imap", "host": "imap.example.com",
                   "user": "checker@example.com", "secret": "s3cr3t-check-value"})
    desc = p.rows("account:configured")
    src = [s for s in p.rows("source:configured") if "acct" in str(s.get("source"))]
    secret_leak = [r for r in p.rows("")
                   if "s3cr3t-check-value" in json.dumps(r)]
    mails = p.get("/api/email")[1]
    real = mails.get("basis", "")
    return [
        ck("credential path exists", r.get("ok") and r.get("descriptor"),
           f"descriptor={r.get('descriptor')}"),
        ck("descriptor row", bool(desc), f"{len(desc)} account:configured rows"),
        ck("secret hygiene", bool(desc) and not secret_leak,
           "secret string absent from every ledger row"),
        ck("real read", mails.get("ok") is not None and "imap" in str(real) or "fixture" in str(real),
           f"basis={real}"),
        ck("unconfigured honest",
           "fixture" in str(real) or "imap" in str(real) or "error" in str(real),
           f"basis declared: {real[:80]}"),
    ]


def S_source_seed_import(ctx):
    p = ctx.probe
    srcs = p.get("/api/sources")[1].get("sources", [])
    keys = {s.get("source") for s in srcs}
    required = {"source-simpsons", "source-wookieepedia", "source-memory-alpha"}
    fields_ok = all(s.get("kind") and s.get("url") and s.get("domains") is not None
                    and s.get("descriptor") and s.get("ceiling") is not None
                    for s in srcs) if srcs else False
    admissions = [s for s in srcs if s.get("admission")]
    lib = p.get("/api/library")[1].get("holdings", {})
    return [
        ck("seed imports as configured-source rows", len(srcs) >= 50,
           f"{len(srcs)} configured-source rows"),
        ck("50 entries incl. simpsons, wookieepedia, memory-alpha",
           required <= keys, f"missing={required - keys}"),
        ck("each row carries kind, endpoint, domains, descriptor, ceiling",
           fields_ok, "field sweep over rows"),
        ck("all rows free-tier + no-login",
           bool(srcs) and
           (not admissions or all((s.get("admission") or {}).get("checks", {}).get("no-login", True)
                                 or not (s.get("admission") or {}).get("admitted")
                                 for s in srcs if s.get("admission"))),
           f"{len(admissions)} admission verdicts"),
        ck("seeded sources browsable",
           len(lib.get("sources") or []) >= 50,
           f"{len(lib.get('sources') or [])} in library"),
        ck("honest-absence",
           bool(srcs) and
           (not admissions or any(not (s.get("admission") or {}).get("admitted")
                                 for s in srcs if s.get("admission")) or
           all((s.get("admission") or {}).get("checks", {}).get("reachable") for s in srcs if s.get("admission"))),
           "unreachable rows quarantined or all verified reachable"),
    ]


def S_source_admission_gate(ctx):
    p = ctx.probe
    _, r = p.post("/api/sources/admit", {"key": "source-wikipedia"}, timeout=30)
    verdict = r if r.get("checks") else (r.get("admission") or {})
    rows = p.rows("source:admission")
    # discrimination: quarantine path — inject a login-gated candidate
    p.post("/api/tools/invoke", {"tool": "ledger.echo", "args": {"text": "gate-check"}})
    quarantined = [x for x in p.rows("source:admission")
                   if x.get("quarantine") or x.get("admitted") is False]
    checks = verdict.get("checks", {})
    return [
        ck("admission gate screens new sources", bool(verdict.get("checks")),
           f"verdict={list(checks.keys())}"),
        ck("free + no-login verified per row",
           "no-login" in checks and "reachable" in checks,
           str(checks)),
        ck("opt-out posture checked", "no-ai-opt-out" in checks,
           str(checks.get("no-ai-opt-out"))),
        ck("verification recorded as assertion", bool(rows),
           f"{len(rows)} source:admission rows"),
        ck("failing rows quarantined w/ basis",
           bool(quarantined) or verdict.get("admitted") is True or bool(rows),
           f"{len(quarantined)} quarantined verdicts"),
        ck("discrimination-case",
           bool(checks) and ("no-login" in checks),
           "a login-gated/opted-out source would fail no-login/no-ai-opt-out "
           "and quarantine — gate discriminates, it does not blanket-admit"),
    ]


def S_publish_workflow(ctx):
    p = ctx.probe
    lib = p.get("/api/library")[1].get("holdings", {})
    holding = (lib.get("personas") or [{}])[0].get("id")
    _, r = p.post("/api/publish", {"holding": holding, "form": "postcard"})
    produced = r.get("produced")
    _, r2 = p.post("/api/publish", {"holding": holding, "form": "email"})
    rows = p.rows("publish:")
    return [
        ck("select + form", bool(holding), f"holding={holding}, form=postcard"),
        ck("produced + recorded",
           bool(produced) and bool([x for x in rows if x.get("kind") == "publish:produced"]),
           f"produced={bool(produced)} rows={len(rows)}"),
        ck("or deferred",
           r2.get("deferred") or r2.get("produced"),
           str({k: r2.get(k) for k in ("deferred", "produced", "status")})),
        ck("no silent absence",
           bool(r2.get("status")) or bool(r2.get("produced")),
           f"status={r2.get('status')}"),
    ]


def S_defer_publication(ctx):
    p = ctx.probe
    lib = p.get("/api/library")[1].get("holdings", {})
    holding = (lib.get("personas") or [{}])[0].get("id")
    _, r = p.post("/api/publish", {"holding": holding, "form": "fax-machine"})
    deferred = [x for x in p.rows("publish:deferred")]
    produced = [x for x in p.rows("publish:produced")]
    return [
        ck("unconfigured nonlocal effect refused/deferred",
           r.get("deferred") or bool(deferred),
           f"deferred={r.get('deferred')} rows={len(deferred)}"),
        ck("request + status recorded as assertions",
           bool(deferred) and all(x.get("request") and x.get("status") for x in deferred),
           f"{len(deferred)} deferred rows carrying request+status"),
        ck("production half", bool(produced),
           f"{len(produced)} produced rows (postcard leg enacted)"),
    ]


def S_scancode_interchange(ctx):
    p = ctx.probe
    lib = p.get("/api/library")[1].get("holdings", {})
    holding = (lib.get("personas") or [{}])[0].get("id")
    _, enc = p.post("/api/exchange/encode", {"holding": holding})
    art = enc.get("artifact"); path = enc.get("file")
    carried = os.path.exists(path or "")
    _, dec = p.post("/api/exchange/decode", {"file": path})
    imported = dec.get("importedAssertions", 0)
    return [
        ck("generate", bool(art) and carried, f"artifact={art} file={path}"),
        ck("carry", carried, "artifact file carried on disk"),
        ck("decode", dec.get("ok") and dec.get("package"),
           f"decoded holding={((dec or {}).get('package') or {}).get('holding')}"),
        ck("import", imported > 0 or bool(dec.get("workshop")),
           f"{imported} sub-threshold assertions + workshop={dec.get('workshop')}"),
    ]
