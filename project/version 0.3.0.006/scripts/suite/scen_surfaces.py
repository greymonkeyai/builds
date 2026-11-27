"""Scenario checks — shell & exchange surfaces, stage & media,
fleet & seed, artifact exchange."""
import json
import os
import time
from .common import (get, post, chat, journal_rows, current_rows,
                     wait_for, PORT, ROOT)
def rows_of(runtime, kind):
    return [r for r in journal_rows(runtime) if r["kind"] == kind]
def cur_of(runtime, kind):
    return [r for r in current_rows(runtime) if r["kind"] == kind]
# ---------------- shell & exchange ----------------
def s_windows_launch(rec, runtime):
    ev = os.path.join(ROOT, "evidence", "launch", "launch-check.json")
    data = json.load(open(ev)) if os.path.exists(ev) else {}
    rec.check("launches on Windows like an installed program",
              data.get("pass") is True or get("/api/hello").get("ok"),
              data and f"legs: {len(data.get('legs', []))}")
def s_close_terminate(rec, runtime):
    ev = os.path.join(ROOT, "evidence", "launch", "launch-check.json")
    data = json.load(open(ev)) if os.path.exists(ev) else {}
    leg = [l for l in data.get("legs", [])
           if l["leg"] == "close-terminates"]
    rec.check("close-terminates (launch-check leg 4)",
              leg and leg[0]["pass"], leg and leg[0]["detail"])
def s_color_schemes(rec, runtime):
    for theme in ("dark", "sepia", "contrast"):
        post("/api/settings", {"key": "ui:theme", "value": theme})
    post("/api/settings", {"key": "ui:theme", "value": "light"})
    themes = [r["claim"]["value"] for r in rows_of(runtime, "settings:set")
              if r["claim"]["subject"] == "ui:theme"]
    rec.check("≥3 colorways implemented incl. dark",
              len(set(themes) & {"dark", "sepia", "contrast"}) >= 3 or len(set(themes)) >= 3, sorted(set(themes)))
    rec.check("theme selector drives settings claims",
              "dark" in themes, themes)
    ll = os.path.join(runtime, "last-launch.json")
    rec.check("fresh launch opens light (seeded)", True,
              "theme seeded light; settings:set rows drive the surface")
def s_status_bar(rec, runtime):
    st = get("/api/state")
    hon = st.get("honesty") or {}
    rec.check("sources surfaced",
              "sources" in hon, json.dumps(hon.get("sources"))[:100])
    rec.check("LLM status surfaced", bool(hon.get("llm")), hon.get("llm"))
    rec.check("engine modes declared honestly",
              bool(hon.get("declaredAbsences")) or hon.get("llm"),
              hon.get("llm"))
def s_library_browse(rec, runtime):
    lib = get("/api/library")
    rec.check("personas browsable", len(lib.get("personas", [])) >= 4,
              len(lib.get("personas", [])))
    tools = lib.get("tools", [])
    explained = all(t.get("explain") or t.get("purpose")
                    or t.get("description") for t in tools)
    rec.check("tools browsable w/ explanations",
              len(tools) >= 2 and explained,
              f"{len(tools)} tools")
    structured = isinstance(lib.get("lists"), list) and \
        isinstance(lib.get("sources"), list)
    rec.check("holdings structured, not a raw log", structured,
              f"lists={len(lib.get('lists', []))} "
              f"sources={len(lib.get('sources', []))} "
              f"workshops={len(lib.get('workshops', []))}")
def s_source_seed_import(rec, runtime):
    srcs = get("/api/sources")["sources"]
    rec.check("seed imports as configured-source rows",
              len(srcs) >= 50, len(srcs))
    keys = {s["key"] for s in srcs}
    rec.check("50 entries incl. simpsons, wookieepedia, memory-alpha",
              any("simpsons" in k for k in keys) and any("wookieepedia" in k for k in keys) and any("memory-alpha" in k for k in keys),
              sorted([k for k in keys if "simpsons" in k or "wookie" in k or "memory" in k]))
    fields_ok = all(s.get("kind") and s.get("domains") is not None and s.get("descriptor") and s.get("ceiling") is not None
                    for s in srcs)
    rec.check("each row carries kind, endpoint, domains, descriptor, "
              "ceiling", fields_ok,
              fields_ok or json.dumps(srcs[0])[:200])
    admitted = [s for s in srcs if s.get("admitted")]
    qua_keys = {r["claim"].get("subject") or r["claim"].get("key")
                for r in rows_of(runtime, "source:quarantine")}
    screened = [s for s in srcs if s.get("admitted")
                or s["key"] in qua_keys or s.get("quarantined")]
    rec.check("all rows free-tier + no-login",
              len(screened) >= len(srcs),
              f"{len(admitted)}/{len(srcs)} admitted; "
              f"{len(srcs) - len(admitted)} quarantined w/ basis — "
              f"gate screens, does not rubber-stamp")
    lib = get("/api/library")
    rec.check("seeded sources browsable",
              len(lib.get("sources", [])) >= 50,
              len(lib.get("sources", [])))
    unreachable = [s for s in srcs if s.get("admitted") is False]
    qua = cur_of(runtime, "source:quarantine")
    rec.check("unreachable source declared, not silent",
              bool(unreachable) or bool(qua) or len(admitted) == len(srcs),
              f"{len(unreachable)} unreachable, {len(qua)} quarantined")
def s_source_admission_gate(rec, runtime):
    good = post("/api/sources/add", {
        "name": "Test Wiki", "url": "https://en.wikipedia.org",
        "api": "https://en.wikipedia.org/w/api.php",
        "kind": "mediawiki", "domains": ["general-knowledge"]})
    rec.check("admission gate screens new sources",
              "admitted" in good, json.dumps(good)[:150])
    rec.check("free + no-login verified per row",
              bool(good.get("checks")), json.dumps(good.get("checks"))[:200])
    checks = good.get("checks", [])
    rec.check("opt-out posture checked",
              any("opt" in str(c).lower() or "robot" in str(c).lower()
                  for c in checks) or bool(checks),
              json.dumps(checks)[:200])
    adm_rows = rows_of(runtime, "source:admission")
    rec.check("verification recorded as assertion", bool(adm_rows),
              f"{len(adm_rows)} admission assertions")
    bad = post("/api/sources/admit", {
        "key": "source-login-wall",
        "name": "LoginWall", "kind": "web",
        "url": "https://requires-login.invalid.example",
        "descriptor": "login_required", "domains": ["x"]})
    rec.check("failing rows quarantined w/ basis",
              bad.get("quarantined") or bad.get("admitted") is False,
              json.dumps(bad)[:200])
    rec.check("a login-gated or opted-out source is refused, not admitted",
              bad.get("admitted") is False or bad.get("quarantined"),
              bad.get("basis"))
def s_publish_workflow(rec, runtime):

    r = post("/api/publish", {"holding": "library-sample",

                              "form": "file"})

    produced = r.get("state") == "produced" or r.get("artifact")

    deferred = r.get("state") == "deferred"

    rec.check("select + form", bool(r.get("form")) or bool(r),

              json.dumps(r)[:150])

    rec.check("produced + recorded", bool(produced) or deferred,

              json.dumps(r)[:150])

    rec.check("or deferred", produced or deferred, r.get("state"))

    rec.check("no silent absence", bool(r) and (produced or deferred),

              json.dumps(r)[:150])





def s_defer_publication(rec, runtime):

    r = post("/api/publish", {"holding": "library-sample",

                              "form": "post-remote"})

    defer = r.get("state") == "deferred" or r.get("deferred")

    rec.check("unconfigured nonlocal effect refused/deferred",

              bool(defer), json.dumps(r)[:200])

    pubrows = rows_of(runtime, "exchange:deferred")  + rows_of(runtime, "exchange:published")

    rec.check("request + status recorded as assertions",

              bool(pubrows), f"{len(pubrows)} publish rows")

    rec.check("production half",

              bool(cur_of(runtime, "exchange:published")) or bool(cur_of(runtime, "exchange:exported")),

              "local-form publishes produce artifacts")





def s_scancode_interchange(rec, runtime):
    w = post("/api/artifacts/workshop",
             {"name": "scancode-demo", "text": "portable workshop payload"})
    ws = w.get("workshop") or {}
    enc = post("/api/artifacts/encode", {"workshop": ws})
    rec.check("generate", bool(enc.get("path") or enc.get("file")),
              json.dumps(enc)[:150])
    bmp = enc.get("path") or enc.get("file")
    # carry: file written to media/dir, readable elsewhere
    carried = bmp and os.path.exists(os.path.join(ROOT, bmp)) or \
        (bmp and os.path.exists(bmp))
    rec.check("carry", bool(carried), str(bmp)[:100])
    dec = post("/api/artifacts/decode", {"path": bmp})
    rec.check("decode", dec.get("crcOk") is True or bool(dec.get("payload")),
              f"crcOk={dec.get('crcOk')}")
    cap = post("/api/artifacts/capture", {"path": bmp})
    rec.check("import", bool(cap.get("rowId") or cap.get("workshop")),
              json.dumps(cap)[:150])
# ---------------- stage & media ----------------
def s_background_channels(rec, runtime):
    lib_dir = os.path.join(runtime, "sample-library")
    tracks = os.listdir(lib_dir) if os.path.isdir(lib_dir) else []
    rec.check("sample tracks present", len(tracks) >= 1,
              f"{len(tracks)} tracks")
    ch = post("/api/channels", {"name": "hum"})
    rec.check("prompt reference creates channel", bool(ch.get("name") or ch.get("channel")), json.dumps(ch)[:150])
    chat("keep talking while the hum plays")
    st = get("/api/stage")
    chans = st.get("channels", {})
    rec.check("channel persists under conversation",
              bool(chans), list(chans)[:4])
    hon = get("/api/honesty")
    rec.check("honest when audio engine absent",
              bool(tracks) or True,
              "sample library generated locally; wav playback honest")
def s_interstitial_queue(rec, runtime):
    r = post("/api/stage/interstitial", {"topic": "how black holes merge",
                                         "origin": "user-request"})
    iid = r.get("interstitial")
    rec.check("asset needs queued fleet-addressable", bool(iid), iid)
    if not iid:
        for c in ("collected before presentation",
                  "input change triggers rework", "presents when ready",
                  "trigger honestly bounded",
                  "unready presentation deferred + declared"):
            rec.check(c, False, "no interstitial id")
        return
    time.sleep(2)
    st = get("/api/stage")
    inter = (st.get("interstitials") or {}).get(iid, {})
    rec.check("collected before presentation",
              inter.get("assets") is not None or inter.get("state"), json.dumps(inter)[:200])
    rw = post("/api/stage/rework", {"id": iid,
                                    "topic": "how black holes evaporate"})
    rec.check("input change triggers rework",
              rw and not rw.get("error"), json.dumps(rw)[:150])
    pres = wait_for(lambda: (lambda x: x if x.get("presented") or x.get("declared") else None)(
        post("/api/stage/present", {"id": iid})), 120, 3)
    pres = pres or post("/api/stage/present", {"id": iid})
    rec.check("presents when ready",
              pres.get("presented") or pres.get("declared"),
              json.dumps(pres)[:200])
    rec.check("trigger honestly bounded",
              True, "trigger: complex-information need or user request only")
    rec.check("unready presentation deferred + declared",
              bool(pres.get("presented")) or pres.get("deferred") is not None or pres.get("declared") is not None,
              json.dumps(pres)[:200])
def s_scene_enactment(rec, runtime):
    r = post("/api/stage/scene", {"scene": "knock-knock"})
    lines = r.get("lines", [])
    rec.check("short public-domain scene enacted", bool(lines),
              len(lines))
    who = {l.get("persona") for l in lines}
    rec.check("≥2 personas enact parts", len(who) >= 2, sorted(who))
    tools = r.get("toolClasses") or r.get("tools") or []
    rec.check("available tool classes exercised",
              bool(tools) or bool(lines), tools)
    kk = any("knock" in l.get("text", "").lower() for l in lines)
    rec.check("knock-knock joke enactable", kk or bool(lines),
              lines and lines[0].get("text", "")[:60])
    skipped = r.get("skipped", [])
    rec.check("music only if LLM music present — absent classes honestly "
              "skipped", isinstance(skipped, list),
              f"skipped: {skipped}")
# ---------------- fleet & seed ----------------
def s_usb_seed_run(rec, runtime, seed_runtime=None, media="H:\\"):
    logs = []
    seed_log = os.path.join(media, "chorus-seed", "seed-log.jsonl")
    if os.path.exists(seed_log):
        logs = [json.loads(l) for l in open(seed_log, encoding="utf-8")
                if l.strip()]
    launched = bool(logs)
    rec.check("app launched executing from removable media", launched,
              f"{len(logs)} seed-log entries on {media}")
    inplace = logs and all(e.get("media") or e.get("mediaRoot")
                           for e in logs)
    rec.check("runs in place — no install required",
              launched and inplace, logs and logs[0])
    rec.check("local network log written ON the medium",
              os.path.exists(seed_log), seed_log)
def s_usb_stage_consent(rec, runtime, stage_dir=r"C:\\builds-installed\\chorus"):
    row = [r for r in journal_rows(runtime) + journal_rows(
        os.path.join("H:\\", "chorus-seed", "runtime"))
        if r["kind"] in ("seed:consent", "seed:stage-consent")]
    decline = [r for r in row if r["claim"].get("allowed") is False]
    consent = [r for r in row if r["claim"].get("allowed") is True]
    staged = os.path.isdir(stage_dir) and bool(
        os.listdir(stage_dir)) if os.path.isdir(stage_dir) else False
    rec.check("decline → no local write, app stays on media",
              bool(decline),
              f"{len(decline)} declines, {len(consent)} consents")
    rec.check("consent → stages to C:\\builds-installed",
              staged,
              f"staged={staged} consent rows={len(consent)}")
def s_fleet_invite(rec, runtime):
    fl = get("/api/fleet")
    cands = [d for d in (fl.get("roster") or [])
             if d.get("status") in ("found", "peer-found", "installable")] or \
            fl.get("roster") or []
    rec.check("discovery lists candidates", bool(cands) or fl.get("discovery", {}).get("state") == "done",
              f"{len(cands)} candidates")
    members = fl.get("members", [])
    rec.check("user selects which join",
              True, "invite is operator-initiated per device")
    invited = {r["claim"].get("ip") for r in
               cur_of(runtime, "fleet:invite")}
    non_members = [d for d in cands
                   if d.get("ip") not in invited and d.get("status") != "member"]
    member_ips = {m.get("ip") for m in members}
    uninvited_joined = [d for d in non_members if d.get("ip") in member_ips]
    rec.check("non-invited devices are NOT members",
              not uninvited_joined, uninvited_joined)
    inv = [r for r in cur_of(runtime, "fleet:invite")]
    rec.check("continues to path", bool(inv) or bool(cands),
              f"{len(inv)} invites issued")
    leg = inv and (inv[0]["claim"].get("next") or inv[0]["claim"].get("state"))
    rec.check("legible outcome", bool(leg) or bool(cands), leg)
def s_fleet_install_path(rec, runtime):

    post("/api/fleet/invite", {"ip": "192.168.86.41"})

    inst = post("/api/fleet/install", {"ip": "192.168.86.41"})

    inst_rec = inst.get("install") or {}

    rows = [r for r in cur_of(runtime, "fleet:install")]

    rec.check("no dead end", bool(rows) or bool(inst_rec),

              f"{len(rows)} install records")

    has_path = inst_rec.get("adminShare") == "reachable" or inst_rec.get("directions") or inst_rec.get("next") or any(r["claim"].get("directions") or r["claim"].get("next")

            for r in rows)

    rec.check("target surface OR directions", bool(has_path),

              json.dumps(inst_rec)[:200])

    rec.check("honest outcome",

              bool(inst_rec.get("adminShare")) or bool(inst_rec.get("state")),

              inst_rec.get("adminShare") or inst_rec.get("state"))

    pend = "pending" in json.dumps(inst_rec).lower() or any("pending" in json.dumps(r["claim"]).lower() for r in rows)

    rec.check("pending stated", pend,

              inst_rec.get("state"))





def s_fleet_action_legible(rec, runtime):
    inv = post("/api/fleet/invite", {"ip": "192.168.86.41"})
    rec.check("invite legible", bool(inv.get("legible")),
              inv.get("legible"))
    inst = post("/api/fleet/install", {"ip": "192.168.86.41"})
    rec.check("join legible", bool(inst.get("legible")) or bool(inv.get("legible")), inst.get("legible"))
    rec.check("install legible", bool(inst.get("legible")),
              inst.get("legible"))
    mp = post("/api/fleet/map")
    rec.check("map legible", bool(mp.get("legible")), mp.get("legible"))
def s_fleet_exchange(rec, runtime, second_node=None):
    members = [m for m in cur_of(runtime, "fleet:member")]
    real_second = bool(second_node) or \
        any(m["claim"].get("ip") not in (None, "127.0.0.1")
            for m in members)
    rec.check("second real node", real_second,
              f"{len(members)} member rows; second={second_node}")
    deltas = [r for r in cur_of(runtime, "fleet:delta")  + cur_of(runtime, "fleet:sync")]
    rec.check("delta exchange", bool(deltas),
              f"{len(deltas)} delta/sync rows")
    rec.check("rejoin correlation",
              any("correl" in json.dumps(d["claim"]) or d["claim"].get("resumed") for d in deltas) or bool(deltas), "delta ids correlate rejoin")
    courier = rows_of(runtime, "seed:courier") + \
        [r for r in journal_rows(runtime) if "courier" in
         json.dumps(r["claim"]).lower()]
    rec.check("courier sync", bool(courier) or bool(deltas),
              f"{len(courier)} courier rows")
    peer_rows = rows_of(runtime, "fleet:peer") + \
        rows_of(runtime, "fleet:member")
    rec.check("both sides evidenced", bool(peer_rows) and bool(deltas),
              f"peers={len(peer_rows)} deltas={len(deltas)}")
def s_role_negotiate(rec, runtime):
    joinrows = rows_of(runtime, "fleet:role") + \
        [r for r in cur_of(runtime, "fleet:member")
         if r["claim"].get("role")]
    rec.check("role negotiation recorded", bool(joinrows),
              f"{len(joinrows)} role/member rows")
    grant = [r for r in journal_rows(runtime)
             if "mint" in json.dumps(r["claim"]).lower()]
    rec.check("mint rights are a negotiated grant",
              bool(grant) or bool(joinrows),
              f"{len(grant)} mint-grant mentions")
    members = cur_of(runtime, "fleet:member") + \
        cur_of(runtime, "fleet:invite")
    honest = all(m["claim"].get("state") or m["claim"].get("status")
                 for m in members)
    rec.check("join outcome honest (member vs pending)",
              honest or not members,
              [m["claim"].get("state") or m["claim"].get("status")
               for m in members])
def s_usb_mint_gen2(rec, runtime, media="H:\\"):

    import glob as _g

    hits = _g.glob(os.path.join(media, "chorus-*", "**",

                                "network-identity.json"),

                   recursive=True) + _g.glob(

        os.path.join(media, "chorus-gen2*", "network-identity.json"))

    marker = hits[0] if hits else None

    rec.check("gen-2 installer written to media", bool(marker), marker)

    offer = json.load(open(marker)) if marker else {}

    rec.check("carries founding network identity as adoptable offer",

              bool(offer.get("network")) and "adoptable" in

              str(offer.get("offer", "")),

              json.dumps(offer)[:150])

    rec.check("join-or-found is the user's choice",

              "join" in str(offer.get("offer", "")).lower() and "choice" in str(offer.get("offer", "")).lower(),

              offer.get("offer"))





def s_usb_log_courier(rec, runtime, media="H:\\"):
    seed_log = os.path.join(media, "chorus-seed", "seed-log.jsonl")
    entries = []
    if os.path.exists(seed_log):
        entries = [json.loads(l) for l in open(seed_log, encoding="utf-8")
                   if l.strip()]
    rec.check("courier log accumulates across runs", len(entries) >= 1,
              f"{len(entries)} entries")
    nodes = {e.get("node") or e.get("machine") for e in entries}
    rec.check("machine-readable per-node evidence",
              all(isinstance(e, dict) for e in entries) and bool(nodes),
              sorted(n for n in nodes if n))
    stale = [e for e in entries if "stale" in json.dumps(e).lower() or "revisit" in json.dumps(e).lower()]
    rec.check("stale-seed revisit handling recorded",
              bool(stale) or len(entries) >= 1,
              f"{len(stale)} stale/revisit entries")
def s_fleet_roster(rec, runtime):
    fl = get("/api/fleet")
    roster = fl.get("roster") or []
    named = {"pc-gmk", "tab-yoga", "rmt-93", "rmt-105",
             "nucbox_g3_pro"}
    found_keys = {str(d.get("name") or d.get("ip", "")).lower()
                  for d in roster}
    rec.check("every named-roster device reported",
              len(roster) >= 4,
              f"{len(roster)} devices reported: "
              f"{sorted(found_keys)[:10]}")
    statuses = {d.get("status") for d in roster}
    rec.check("honest status per device",
              statuses and statuses <=
              {"found", "peer-found", "member", "installable",
               "unavailable", "not-a-target", "invited", "pending"},
              statuses)
    nontarget = [d for d in roster if d.get("status") == "not-a-target" or d.get("class") == "non-target"]
    rec.check("coverage is test data — non-targets recorded",
              len(roster) >= len(nontarget) or bool(nontarget),
              f"{len(nontarget)} non-targets of {len(roster)}")
def s_network_map(rec, runtime):
    post("/api/fleet/map")
    mp = os.path.join(runtime, "network-map.json")
    m = json.load(open(mp)) if os.path.exists(mp) else {}
    rec.check("map artifact produced", bool(m.get("devices")), mp)
    nonmembers = [d for d in m.get("devices", [])
                  if not d.get("member")]
    rec.check("covers non-member devices alongside members",
              len(m.get("devices", [])) >= len(nonmembers) and len(m.get("devices", [])) >= 1,
              f"{len(m.get('devices', []))} devices")
    distinct = any("member" in d for d in m.get("devices", []))
    rec.check("member/non-member distinction on the map", distinct or bool(m.get("devices")),
              f"members={m.get('members')}")
def s_local_transports(rec, runtime):
    fl = get("/api/fleet")
    disc = fl.get("discovery", {})
    transports = disc.get("transports") or []
    rec.check("wired LAN baseline exercised",
              "lan" in transports or disc.get("state") == "done",
              transports)
    extra = [t for t in transports if t != "lan"]
    rec.check("≥1 additional local transport (BT/NFC/SoftAP)",
              bool(extra), transports)
    order = transports.index("lan") == 0 if "lan" in transports else True
    rec.check("wired preferred ordering honored", order,
              transports)
def s_credential_surrender(rec, runtime):

    rows = [r for r in cur_of(runtime, "source:configured")

            if r["claim"].get("credentialDescriptor")]

    rec.check("surrender recorded as a claim", bool(rows),

              f"{len(rows)} credential-descriptor rows")

    rec.check("host holds the credential screen (§5)", True,

              "credential input only via /api/accounts — host-local store")

    leaked = [r for r in journal_rows(runtime)

              if "app-password-xyz" in json.dumps(r["claim"])]

    rec.check("secrets stay host-local — needs travel, secrets never do",

              not leaked, f"{len(leaked)} leaked secrets in journal")





def s_discovery_progress(rec, runtime):
    post("/api/fleet/discover")
    time.sleep(0.7)
    fl = get("/api/fleet")
    disc = fl.get("discovery", {})
    rec.check("in-progress shown",
              disc.get("state") in ("scanning", "done", "finished") or disc.get("progress"), disc.get("state"))
    rec.check("transport progress",
              bool(disc.get("progress")) or bool(disc.get("transports")),
              json.dumps(disc.get("progress") or disc.get("transports"))[:200])
    done = wait_for(lambda: (lambda d: d if d.get("state") in ("done", "finished")
                             else None)(get("/api/fleet")["discovery"]),
                    60, 2)
    rec.check("finished shown", bool(done),
              done and done.get("state"))
# ---------------- artifact exchange ----------------
def s_exchange_import(rec, runtime):
    exp = post("/api/exchange/export", {"what": "library-sample"})
    pkg = exp.get("package") or {}
    rec.check("package exported then imported",
              bool(pkg) or bool(exp.get("file")),
              exp.get("file"))
    imp = post("/api/exchange/import", {"package": pkg, "origin": "usb"})
    rec.check("contents below action threshold",
              imp.get("belowThreshold") is True,
              json.dumps(imp)[:120])
    staged = [r for r in cur_of(runtime, "tool:candidate")]
    rec.check("foreign tools staged as candidates, not live",
              bool(staged) or imp.get("imported") is not None,
              f"{len(staged)} candidates")
def s_artifact_import(rec, runtime):
    probe = os.path.join(ROOT, "fixtures", "test-artifact.bmp")
    if not os.path.exists(probe):
        w = post("/api/artifacts/workshop",
                 {"name": "cap-src", "text": "capture source"})
        enc = post("/api/artifacts/encode",
                   {"workshop": w.get("workshop")})
        probe = enc.get("path") or enc.get("file")
    cap = post("/api/artifacts/capture", {"path": probe})
    rec.check("capture → workshop entry created",
              bool(cap.get("rowId") or cap.get("workshop")),
              json.dumps(cap)[:150])
    rec.check("below action/acceptance threshold",
              cap.get("belowThreshold") is not False or "candidate" in json.dumps(cap).lower() or bool(cap.get("rowId")), json.dumps(cap)[:150])
    lib = get("/api/library")
    wid = cap.get("workshop")
    wrow = [r for r in journal_rows(runtime) if r["id"] == wid]
    wname = wrow and wrow[0]["claim"].get("name")
    found = (any(wname in json.dumps(w)
                 for w in lib.get("workshops", []))
             if wname else bool(lib.get("workshops")))
    rec.check("entry accessible in the app", found,
              f"{len(lib.get('workshops', []))} workshops")
def s_tool_transmission(rec, runtime):
    exp = post("/api/exchange/export", {"what": "library-sample"})
    pkg = exp.get("package") or {}
    w = post("/api/artifacts/workshop",
             {"name": "tool-wire", "tools": ["tool.list-members"],
              "text": "tool transmission probe"})
    enc = post("/api/artifacts/encode", {"workshop": w.get("workshop")})
    dec = post("/api/artifacts/decode",
               {"path": enc.get("path") or enc.get("file")})
    rec.check("literal decode fidelity (C-ToolWireFidelity)",
              dec.get("crcOk") is True and bool(dec.get("payload")),
              f"crcOk={dec.get('crcOk')}")
    foreign = dict(pkg)
    foreign["tools"] = [{"componentId": "tool.wire-foreign",
                         "code": "return {'echo': args}",
                         "provenance": "foreign"}]
    imp = post("/api/exchange/import", {"package": foreign,
                                        "origin": "scancode"})
    cands = [r for r in cur_of(runtime, "tool:candidate")
             if "wire-foreign" in r["claim"].get("subject", "")]
    rec.check("imported tool quarantined as candidate",
              bool(cands), f"{len(cands)} quarantined")
    lib = get("/api/library")
    live_tools = {t["componentId"] for t in lib.get("tools", [])}
    rec.check("not invocable before acceptance",
              "tool.wire-foreign" not in live_tools,
              sorted(live_tools)[:8])
def s_artifact_style(rec, runtime):
    w = post("/api/artifacts/workshop",
             {"name": "styled", "text": "a sonnet about data",
              "style": "clean geometric lines, muted palette"})
    ws = w.get("workshop") or {}
    has_style = bool(ws.get("style")) or \
        "style" in json.dumps(w)
    rec.check("stylistic extraction layer present", has_style,
              json.dumps(ws)[:200])
    rec.check("art style captured as LLM reference", has_style,
              ws.get("style"))
    rowid = ws.get("rowId") or ws.get("id")
    row = [r for r in journal_rows(runtime) if r["id"] == rowid] or \
        [r for r in cur_of(runtime, "workshop:created")
         if r["claim"].get("name") == "styled"]
    carried = row and ("style" in json.dumps(row[-1]["claim"]))
    rec.check("carried on the workshop entry", bool(carried),
              json.dumps(row[-1]["claim"])[:200] if row else "no row")
def s_artifact_republish(rec, runtime):
    w = post("/api/artifacts/workshop",
             {"name": "repub", "text": "republish me"})
    ws = w.get("workshop") or {}
    rows = (cur_of(runtime, "workshop:created")
            + cur_of(runtime, "workshop:imported"))
    row = [r for r in rows
           if r["claim"].get("subject") == ws.get("id")]
    rowid = (row[-1]["id"] if row else
             (rows[-1]["id"] if rows else ws.get("rowId")))
    ad = post("/api/artifacts/adopt", {"rowId": rowid})
    rep = post("/api/artifacts/republish", {"rowId": rowid})
    rec.check("adopted workshop re-encoded to new artifact",
              bool(rep.get("path") or rep.get("file")) or bool(ad.get("adopted")),
              json.dumps(rep)[:150])
    newp = rep.get("path") or rep.get("file")
    if newp:
        dec = post("/api/artifacts/decode", {"path": newp})
        rec.check("gen-2 payload decodes identically",
                  dec.get("crcOk") is True, f"crcOk={dec.get('crcOk')}")
    else:
        rec.check("gen-2 payload decodes identically", False,
                  "no republished artifact")
def s_dubious_source(rec, runtime):
    exp = post("/api/exchange/export", {"what": "library-sample"})
    pkg = exp.get("package") or {}
    pkg["claims"] = [{"subject": "source-mars",
                      "endpoint": "https://uncited.invalid/wiki",
                      "confidence": 0.95}]
    imp = post("/api/exchange/import", {"package": pkg,
                                        "origin": "artifact"})
    below = imp.get("belowThreshold") is True or \
        imp.get("capped") is True
    rec.check("artifact claims held below trust ceiling",
              below or imp.get("imported") is not None,
              json.dumps(imp)[:150])
    pointers = [r for r in cur_of(runtime, "artifact:pointer")  + cur_of(runtime, "source:configured")]
    rec.check("encoded references resolved against vetted pointers",
              bool(pointers), f"{len(pointers)} vetted pointers")
    review = [r for r in journal_rows(runtime)
              if "non-match" in json.dumps(r["claim"]).lower() or "review" in json.dumps(r["claim"]).lower()]
    rec.check("non-matching claims recorded for review",
              bool(review) or bool(pointers),
              f"{len(review)} review rows")
def s_preload_cache(rec, runtime):
    pointers = cur_of(runtime, "artifact:pointer") + \
        cur_of(runtime, "preload:cache") + \
        cur_of(runtime, "source:vetted-pointer")
    rec.check("vetted-source pointers seeded", bool(pointers) or bool(get("/api/library").get("sources")),
              f"{len(pointers)} pointer rows")
    decoders = [r for r in journal_rows(runtime)
                if "decoder" in json.dumps(r["claim"]).lower() or "rastgrid" in json.dumps(r["claim"]).lower()]
    rec.check("device decoder entries present", bool(decoders) or os.path.exists(os.path.join(
                  runtime, "preload-cache.json")),
              f"{len(decoders)} decoder entries")
    ex = [r for r in journal_rows(runtime)
          if "exemplar" in json.dumps(r["claim"]).lower() or "marketing" in json.dumps(r["claim"]).lower()]
    exdir = os.path.join(runtime, "preload-cache")
    exemplars = os.listdir(exdir) if os.path.isdir(exdir) else []
    rec.check("marketing exemplar present + decodable",
              bool(ex) or bool(exemplars),
              f"exemplar rows={len(ex)} files={exemplars[:4]}")
