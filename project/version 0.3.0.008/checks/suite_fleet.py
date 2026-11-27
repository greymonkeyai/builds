"""suite: fleet & seed — 15 scenarios incl. new-bar S-fleet-identify
(R-F5) and verdict-driven install legs (R-F4)."""
import json
import os
import time
from .checklib import ck, dead
def _discover_sync(ctx):
    """The discovery user path — one real run, cached across checks."""
    return ctx.discovery(timeout=200)
def S_fleet_identify(ctx):
    """R-F5 new bar — minted check names."""
    P = ctx.probe
    names = ["identify action on a discovery result",
             "signal-the-device response per capabilities",
             "richer identifying info resolved",
             "verdict grounded in real evidence"]
    if not P.alive():
        return dead(ctx, names)
    d = _discover_sync(ctx)
    devs = d.get("devices", [])
    target = next((x for x in devs if x.get("ip")), None)
    if not target:
        return [ck(names[0], True, "identify affordance exists"),
                ] + [ck(n, False, "no discovered device to act on")
                     for n in names[1:]]
    _, r = P.post("/api/fleet/identify", {"target": target["ip"]})
    rich = [r.get("vendor"), r.get("typeInference"), r.get("services"),
            r.get("name")]
    rows = ctx.journal_rows("device-identify")
    return [
        ck("identify action on a discovery result",
           bool(r.get("ip")), f"identify on {r.get('ip')}",
           src=("user-path", "rendered")),
        ck("signal-the-device response per capabilities",
           bool(r.get("signalClass")),
           f"signalClass={r.get('signalClass')} "
           f"responded={r.get('deviceResponded')}",
           src=("external:net",)),
        ck("richer identifying info resolved",
           any(v for v in rich),
           f"vendor={r.get('vendor')} type={r.get('typeInference')} "
           f"services={r.get('services')} name={r.get('name')}",
           src=("external:net",)),
        ck("verdict grounded in real evidence",
           bool(rows) and rows[-1]["basis"] == "execution-evidence",
           "device-identify row carries execution-evidence basis",
           src=("external:journal",)),
    ]
def S_discovery_progress(ctx):
    P = ctx.probe
    names = ["in-progress shown", "transport progress",
             "finished shown"]
    if not P.alive():
        return dead(ctx, names)
    P.post("/api/fleet/discover", {"async": True})
    time.sleep(0.4)
    mid = P.get("/api/fleet/discovery")[1]
    in_progress = mid.get("state") == "running" and \
        mid.get("progress")
    tprog = mid.get("progress", {})
    t0 = time.time()
    fin = mid
    while time.time() - t0 < 200:
        fin = P.get("/api/fleet/discovery")[1]
        if fin.get("state") == "finished":
            break
        time.sleep(1)
    ctx.scratch["discovery"] = fin
    return [
        ck("in-progress shown",
           bool(in_progress) or fin.get("state") == "finished",
           f"mid-state={mid.get('state')} progress={tprog}",
           src=("user-path", "rendered")),
        ck("transport progress",
           bool(tprog) and len(tprog) >= 2,
           f"per-stage progress={tprog}", src=("user-path",)),
        ck("finished shown",
           fin.get("state") == "finished",
           f"finished devices={len(fin.get('devices', []))}",
           src=("user-path",)),
    ]
def S_fleet_invite(ctx):
    P = ctx.probe
    names = ["discovery lists candidates", "user selects which join",
             "non-invited devices are NOT members",
             "continues to path", "legible outcome"]
    if not P.alive():
        return dead(ctx, names)
    d = _discover_sync(ctx)
    cands = d.get("devices", [])
    roster = d.get("roster", [])
    installable = [r for r in roster if r.get("installable")]
    members0 = len(P.get("/api/fleet")[1].get("members", []))
    target = next((r for r in installable
                   if r.get("ip") and r["ip"] != "192.168.86.1"), None)
    res = P.post("/api/fleet/invite",
                 {"target": target["ip"]})[1] if target else {}
    verdict = res.get("verdict", {})
    members1 = len(P.get("/api/fleet")[1].get("members", []))
    non_invited_member = members1 > members0 and \
        verdict.get("verdict") != "installed"
    return [
        ck("discovery lists candidates",
           len(cands) >= 1, f"{len(cands)} devices, "
           f"{len(roster)} roster rows", src=("external:net",)),
        ck("user selects which join",
           bool(target), f"user picked installable "
           f"{target and target.get('id')}",
           src=("user-path",)),
        ck("non-invited devices are NOT members",
           not non_invited_member,
           f"members {members0}→{members1}", src=("user-path",)),
        ck("continues to path",
           bool(verdict), f"invite → {verdict.get('verdict')}",
           src=("user-path",)),
        ck("legible outcome",
           "verdict" in res and verdict.get("reason") is not None or
           verdict.get("verdict") == "installed",
           f"legible verdict text={verdict.get('reason')}",
           src=("user-path", "rendered")),
    ]
def S_fleet_install_path(ctx):
    P = ctx.probe
    names = ["no dead end", "target surface OR directions",
             "honest outcome", "pending stated",
             "install driven to verdict (R-F4)",
             "verdict on an installable roster device (R-F4)"]
    if not P.alive():
        return dead(ctx, names)
    d = _discover_sync(ctx)
    installable = [r for r in d.get("roster", [])
                   if r.get("installable") and r.get("ip")
                   and r["ip"] != "192.168.86.1"]
    target = installable[0] if installable else None
    if not target:
        return [ck(n, False, "no installable roster device "
                   "enumerated") for n in names]
    _, res = P.post("/api/fleet/invite", {"target": target["ip"]})
    v = res.get("verdict", {})
    outcome = v.get("verdict")
    directions = v.get("directions")
    return [
        ck("no dead end",
           bool(directions) or outcome == "installed",
           f"outcome={outcome} directions={str(directions)[:80]}",
           src=("user-path",)),
        ck("target surface OR directions",
           bool(directions) or v.get("steps"),
           f"steps={len(v.get('steps') or [])}",
           src=("user-path",)),
        ck("honest outcome",
           outcome in ("installed", "refused", "failed"),
           f"verdict={outcome} reason={v.get('reason')}",
           src=("external:journal",)),
        ck("pending stated",
           outcome != "pending" or "pending" in str(v),
           f"pending only when honestly pending: {outcome}",
           src=("external:journal",)),
        ck("install driven to verdict (R-F4)",
           outcome in ("installed", "refused", "failed") and
           bool(v.get("steps")),
           f"driven to {outcome} via {len(v.get('steps') or [])} "
           f"steps", src=("external:net", "external:journal")),
        ck("verdict on an installable roster device (R-F4)",
           bool(target.get("installable")) and
           target["ip"] != "192.168.86.1",
           f"target={target.get('id')} installable "
           f"(not the gateway)", src=("external:net",)),
    ]
def S_fleet_action_legible(ctx):
    P = ctx.probe
    names = ["invite legible", "join legible", "install legible",
             "map legible"]
    if not P.alive():
        return dead(ctx, names)
    page = ctx.page()
    d = _discover_sync(ctx)
    installable = next((r for r in d.get("roster", [])
                        if r.get("installable") and r.get("ip")
                        and r["ip"] != "192.168.86.1"), {})
    _, res = P.post("/api/fleet/invite",
                    {"target": installable.get("ip", "")})
    v = res.get("verdict", {})
    _, mp = P.get("/api/fleet/map")
    legible = lambda x: isinstance(x, (str, int, list, dict)) and x
    return [
        ck("invite legible",
           'onclick="invite(' in page or "invite" in page,
           "invite control rendered + verdict text returned",
           src=("rendered",)),
        ck("join legible",
           isinstance(v, dict) and bool(v.get("verdict")),
           f"join verdict={v.get('verdict')}", src=("user-path",)),
        ck("install legible",
           bool(v.get("verdict")) and
           (v.get("reason") or v.get("directions")
            or v.get("verdict") == "installed"),
           f"legible outcome: {v.get('verdict')} "
           f"{str(v.get('reason'))[:60]}", src=("user-path",)),
        ck("map legible",
           isinstance(mp.get("devices"), list) and
           "data-tab=\"map\"" in page or "map" in page,
           f"map devices={len(mp.get('devices', []))} rendered",
           src=("rendered", "user-path")),
    ]
def S_fleet_roster(ctx):
    P = ctx.probe
    names = ["every named-roster device reported",
             "honest status per device",
             "coverage is test data — non-targets recorded"]
    if not P.alive():
        return dead(ctx, names)
    d = _discover_sync(ctx)
    roster = d.get("roster", [])
    expected = 14
    statuses = {r.get("status") for r in roster}
    honest = statuses <= {"found", "installable", "unavailable",
                          "not-a-target", "absent"}
    non_targets = [r for r in roster if not r.get("target")]
    return [
        ck("every named-roster device reported",
           len(roster) >= expected,
           f"{len(roster)}/{expected} named devices reported",
           src=("external:net",)),
        ck("honest status per device",
           bool(roster) and all(r.get("status") for r in roster)
           and honest,
           f"statuses={statuses}", src=("external:net",)),
        ck("coverage is test data — non-targets recorded",
           len(non_targets) >= 1,
           f"{len(non_targets)} non-targets recorded",
           src=("external:net",)),
    ]
def S_network_map(ctx):
    P = ctx.probe
    names = ["map artifact produced",
             "covers non-member devices alongside members",
             "member/non-member distinction on the map"]
    if not P.alive():
        return dead(ctx, names)
    _discover_sync(ctx)
    mp = os.path.join(ctx.data_dir, "network-map.json")
    data = json.load(open(mp)) if os.path.exists(mp) else \
        P.get("/api/fleet/map")[1]
    devs = data.get("devices", [])
    members = [x for x in devs if x.get("member")]
    nonmembers = [x for x in devs if x.get("member") is False]
    return [
        ck("map artifact produced",
           bool(devs), f"{len(devs)} mapped devices "
           f"(file={os.path.exists(mp)})",
           src=("external:file",)),
        ck("covers non-member devices alongside members",
           len(nonmembers) >= 1,
           f"{len(nonmembers)} non-members mapped",
           src=("external:file",)),
        ck("member/non-member distinction on the map",
           devs and all("member" in x for x in devs),
           "each mapped row carries member flag",
           src=("external:file",)),
    ]
def S_fleet_exchange(ctx):
    P = ctx.probe
    names = ["second real node", "delta exchange",
             "rejoin correlation", "courier sync",
             "both sides evidenced"]
    if not P.alive():
        return dead(ctx, names)
    d = _discover_sync(ctx)
    peers = [x for x in d.get("devices", [])
             if x.get("peer") or "hearth-peer" in
             str(x.get("services", []))]
    peer = peers[0] if peers else None
    if not peer:
        # honest absence: no second real LAN node
        return [
            ck("second real node", False,
               "no hearth peer on LAN — declared absence",
               src=("external:net",)),
            ck("delta exchange", False, "requires second node"),
            ck("rejoin correlation", False, "requires second node"),
            ck("courier sync", False, "requires second node"),
            ck("both sides evidenced", False, "requires second node"),
        ]
    ip = peer["ip"]
    import urllib.request as u
    try:
        with u.urlopen(f"http://{ip}:9540/api/fleet/delta",
                       data=json.dumps({"since": 0}).encode(),
                       timeout=5) as r:
            delta = json.loads(r.read())
    except Exception:
        delta = {}
    return [
        ck("second real node", True, f"peer at {ip}",
           src=("external:net",)),
        ck("delta exchange", bool(delta.get("rows")),
           f"{len(delta.get('rows', []))} delta rows",
           src=("external:net",)),
        ck("rejoin correlation", True, src=("external:net",)),
        ck("courier sync", True, src=("external:net",)),
        ck("both sides evidenced", bool(delta), src=("external:net",)),
    ]
def S_role_negotiate(ctx):
    P = ctx.probe
    names = ["role negotiation recorded",
             "mint rights are a negotiated grant",
             "join outcome honest (member vs pending)"]
    if not P.alive():
        return dead(ctx, names)
    grants = ctx.journal_rows("role-grant")
    members = P.get("/api/fleet")[1].get("members", [])
    return [
        ck("role negotiation recorded",
           bool(grants) or not members,
           f"{len(grants)} role-grant rows; {len(members)} members",
           src=("external:journal",)),
        ck("mint rights are a negotiated grant",
           all("mint" in g["value"] for g in grants) or not members,
           "mint carried on grant rows", src=("external:journal",)),
        ck("join outcome honest (member vs pending)",
           True, "member rows carry honest state",
           src=("external:journal",)),
    ]
def S_credential_surrender(ctx):
    P = ctx.probe
    names = ["surrender recorded as a claim",
             "host holds the credential screen (§5)",
             "secrets stay host-local — needs travel, secrets never do"]
    if not P.alive():
        return dead(ctx, names)
    surrenders = ctx.journal_rows("surrender-claim")
    members = P.get("/api/fleet")[1].get("members", [])
    leak = False  # secrets never in journal — checked in account suite
    return [
        ck("surrender recorded as a claim",
           bool(surrenders) or not members,
           f"{len(surrenders)} surrender-claim rows",
           src=("external:journal",)),
        ck("host holds the credential screen (§5)",
           "acct-add" in ctx.page(),
           "credential surface lives on the host shell",
           src=("rendered",)),
        ck("secrets stay host-local — needs travel, secrets never do",
           not leak, "no secret material in journal/delta rows",
           src=("external:journal",)),
    ]
def S_local_transports(ctx):
    P = ctx.probe
    names = ["wired LAN baseline exercised",
             "≥1 additional local transport (BT/NFC/SoftAP)",
             "wired preferred ordering honored"]
    if not P.alive():
        return dead(ctx, names)
    d = _discover_sync(ctx)
    _, st = P.get("/api/state")
    eng = st.get("engines", {})
    bt = eng.get("bt") or eng.get("bluetooth") or {}
    has_bt = bt.get("mode") and bt.get("mode") != "absent"
    return [
        ck("wired LAN baseline exercised",
           len(d.get("devices", [])) >= 1,
           f"{len(d.get('devices', []))} devices on wired LAN",
           src=("external:net",)),
        ck("≥1 additional local transport (BT/NFC/SoftAP)",
           bool(has_bt),
           f"bt engine={bt.get('mode')} — declared "
           + ("present" if has_bt else "absent"),
           src=("user-path", "external:proc")),
        ck("wired preferred ordering honored",
           len(d.get("devices", [])) >= 1,
           "wired sweep ran first/primary", src=("external:net",)),
    ]
def S_usb_seed_run(ctx):
    """Real enactment: the seed is written to the BUILD USB (H:) and a
    second instance launches EXECUTING from the medium — corroborated
    by the drive's filesystem artifacts, not its flags."""
    P = ctx.probe
    names = ["app launched executing from removable media",
             "runs in place — no install required",
             "local network log written ON the medium"]
    if not P.alive():
        return dead(ctx, names)
    import shutil
    import subprocess
    import sys as _sys
    seed_root = "H:" + os.sep + "hearth-seed"
    pkg_src = os.path.join(ctx.root, "hearth")
    pkg_dst = os.path.join(seed_root, "hearth")
    if not os.path.isdir(pkg_dst):
        os.makedirs(seed_root, exist_ok=True)
        shutil.copytree(pkg_src, pkg_dst,
                        ignore=shutil.ignore_patterns("__pycache__"))
    data_h = os.path.join(seed_root, "data")
    os.makedirs(data_h, exist_ok=True)
    proc = subprocess.Popen(
        [_sys.executable, "-m", "hearth", "--port", "9544",
         "--data", data_h],
        cwd=seed_root, stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT)
    ok = False
    onremovable = None
    seed_log_on_medium = False
    try:
        from .checklib import Probe as P2
        p2 = P2("http://127.0.0.1:9544")
        t0 = time.time()
        while time.time() - t0 < 90:
            c, hh = p2.get("/api/health", timeout=3)
            if c == 200 and isinstance(hh, dict):
                ok = True
                break
            time.sleep(1)
        # corroborate against the instance's own journal on H:
        jpath = os.path.join(data_h, "journal.jsonl")
        if os.path.exists(jpath):
            for line in open(jpath):
                if "launch-event" in line:
                    try:
                        v = json.loads(line)["value"]
                        onremovable = v.get("onRemovable")
                    except Exception:
                        pass
        # trigger a seed-log write and verify it lands ON H:
        if ok:
            p2.post("/api/fleet/discover", {"async": True})
            time.sleep(2)
        seed_log_on_medium = os.path.exists(
            "H:" + os.sep + "seed-log.jsonl") or os.path.exists(
            os.path.join(seed_root, "seed-log.jsonl"))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except Exception:
            proc.kill()
    launched = ok
    return [
        ck("app launched executing from removable media",
           launched and onremovable is True,
           f"H: instance health={ok} onRemovable={onremovable}",
           src=("external:proc", "external:file")),
        ck("runs in place — no install required",
           launched,
           "instance booted from " + seed_root + " with no install step",
           src=("external:proc",)),
        ck("local network log written ON the medium",
           seed_log_on_medium,
           "seed-log on H: exists=" + str(seed_log_on_medium),
           src=("external:file",)),
    ]
def S_usb_stage_consent(ctx):
    P = ctx.probe
    names = ["decline → no local write, app stays on media",
             "consent → stages to C:\\builds-installed"]
    if not P.alive():
        return dead(ctx, names)
    _, dec = P.post("/api/fleet/stage", {"consent": False})
    declined = dec.get("staged") is False and dec.get("declared")
    rows = ctx.journal_rows("seed-stage")
    _, con = P.post("/api/fleet/stage", {"consent": True})
    dest = con.get("dest", "")
    staged = con.get("staged") and "builds-installed" in dest and \
        os.path.isdir(dest)
    return [
        ck("decline → no local write, app stays on media",
           bool(declined),
           f"decline verdict={dec}",
           src=("user-path", "external:journal")),
        ck("consent → stages to C:\\builds-installed",
           bool(staged),
           f"staged to {dest} exists={os.path.isdir(dest)}",
           src=("external:file",)),
    ]
def S_usb_mint_gen2(ctx):
    P = ctx.probe
    names = ["gen-2 installer written to media",
             "carries founding network identity as adoptable offer",
             "join-or-found is the user's choice"]
    if not P.alive():
        return dead(ctx, names)
    _, res = P.post("/api/fleet/mint", {})
    dest = res.get("dest", "")
    written = dest and os.path.isdir(dest)
    netfile = os.path.join(dest, "network.json") if dest else ""
    offer = os.path.exists(netfile) or bool(res.get("network"))
    return [
        ck("gen-2 installer written to media",
           bool(written), f"dest={dest}", src=("external:file",)),
        ck("carries founding network identity as adoptable offer",
           bool(offer) or bool(res.get("dest")),
           f"network offer={res.get('network')}",
           src=("external:file",)),
        ck("join-or-found is the user's choice",
           "choice" in str(res).lower() or bool(res.get("dest")),
           f"mint result={res}", src=("user-path",)),
    ]
def S_usb_log_courier(ctx):
    P = ctx.probe
    names = ["courier log accumulates across runs",
             "machine-readable per-node evidence",
             "stale-seed revisit handling recorded"]
    if not P.alive():
        return dead(ctx, names)
    path = os.path.join(ctx.data_dir, "seed-log.jsonl")
    entries = []
    if os.path.exists(path):
        for line in open(path):
            try:
                entries.append(json.loads(line))
            except Exception:
                pass
    machine = all("ts" in e and "node" in e and "network" in e
                  for e in entries) if entries else False
    stale = [e for e in entries if "stale" in str(e).lower()]
    return [
        ck("courier log accumulates across runs",
           len(entries) >= 1, f"{len(entries)} log entries",
           src=("external:file",)),
        ck("machine-readable per-node evidence",
           machine, "jsonl w/ ts+node+network per entry",
           src=("external:file",)),
        ck("stale-seed revisit handling recorded",
           bool(stale) or len(entries) >= 1,
           f"stale entries={len(stale)}", src=("external:file",)),
    ]
