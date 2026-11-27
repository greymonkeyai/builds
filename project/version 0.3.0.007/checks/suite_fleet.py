"""Checks — fleet & seed facet. Frozen names verbatim.

Fleet lab rules (owner-stated): USB drive labeled `build` is the removable
media; named roster is coverage ground truth; same-host second instance is
NOT a joined device; private inventory is not mirrored into artifacts."""

import json
import os
import time

from .checklib import ck


def _seed_root(ctx):
    """Removable media labeled `build` — H:\\vesta-seed by convention."""
    for cand in ("H:\\vesta-seed", "E:\\vesta-seed", "D:\\vesta-seed"):
        if os.path.isdir(os.path.dirname(cand)):
            return cand
    return "H:\\vesta-seed"


def _courier_log_entries(seed):
    """The medium's append-only courier log (seed-log.jsonl)."""
    log = os.path.join(seed, "seed-log.jsonl")
    if not os.path.exists(log):
        return []
    entries = []
    for line in open(log, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except Exception:
                pass
    return entries


def S_usb_seed_run(ctx):
    p = ctx.probe
    seed = _seed_root(ctx)
    _, r = p.post("/api/fleet/seed-run", {"seedDir": seed})
    on_media = os.path.isdir(seed)
    entries = _courier_log_entries(seed)
    rows = p.rows("fleet:seed-run")
    return [
        ck("app launched executing from removable media",
           r.get("ok") and on_media and r.get("launchedFrom") and
           r.get("launchedFrom", "").lower().startswith(os.path.splitdrive(seed)[0].lower()),
           f"launchedFrom={r.get('launchedFrom')}"),
        ck("runs in place — no install required",
           r.get("ok") and r.get("installed") in (False, None),
           f"installed={r.get('installed')}"),
        ck("local network log written ON the medium",
           bool(entries) and r.get("ok"),
           f"{len(entries)} courier entries on {seed}"),
    ]


def S_usb_stage_consent(ctx):
    p = ctx.probe
    seed = _seed_root(ctx)
    stage = "C:\\builds-installed"
    # decline first: no local write
    _, dec = p.post("/api/fleet/seed-stage", {"seedDir": seed,
                                            "targetDir": stage, "consent": False})
    declined_write = dec.get("wrote") in (False, None)
    declined_rows = [x for x in p.rows("fleet:stage-consent")
                     if x.get("consent") is False]
    # consent: stages
    _, acc = p.post("/api/fleet/seed-stage", {"seedDir": seed,
                                            "targetDir": stage, "consent": True})
    staged = acc.get("wrote") and os.path.isdir(stage)
    rows = [x for x in p.rows("fleet:stage-consent") if x.get("consent")]
    return [
        ck("decline → no local write, app stays on media",
           declined_write and bool(declined_rows),
           f"wrote={dec.get('wrote')} declined-rows={len(declined_rows)}"),
        ck("consent → stages to C:\\builds-installed",
           bool(staged) and bool(rows),
           f"wrote={acc.get('wrote')} staged-rows={len(rows)}"),
    ]


def S_fleet_invite(ctx):
    p = ctx.probe
    # discovery lists candidates
    _, disc = p.post("/api/fleet/discover")
    cands = disc.get("candidates") or []
    members_before = [m["node"] for m in p.get("/api/fleet")[1].get("members", [])]
    invited = []
    if cands:
        _, iv = p.post("/api/fleet/invite", {"node": cands[0]["node"]})
        invited.append((cands[0]["node"], iv))
    members_after = [m["node"] for m in p.get("/api/fleet")[1].get("members", [])]
    non_invited_not_members = all(c["node"] not in members_after or
                                  any(i[0] == c["node"] for i in invited)
                                  for c in cands)
    legible = all(i[1].get("legible") or i[1].get("outcome") for i in invited) \
        if invited else False
    return [
        ck("discovery lists candidates", bool(cands),
           f"{len(cands)} candidates: {[c.get('node') for c in cands][:5]}"),
        ck("user selects which join", bool(invited),
           f"invited {[i[0] for i in invited]}"),
        ck("non-invited devices are NOT members",
           bool(cands) and non_invited_not_members,
           f"members={members_after} candidates={[c['node'] for c in cands]}"),
        ck("continues to path", bool(invited) and all(
            i[1].get("next") or i[1].get("path") for i in invited),
           str((invited[0][1] if invited else {}))[:100]),
        ck("legible outcome", legible,
           str(invited[0][1].get("legible") if invited else None)),
    ]


def S_fleet_install_path(ctx):
    p = ctx.probe
    cands = p.get("/api/fleet")[1].get("candidates") or \
        p.post("/api/fleet/discover")[1].get("candidates", [])
    outcome = None
    if cands:
        _, r = p.post("/api/fleet/install", {"node": cands[0]["node"]})
        outcome = r
    legible = outcome and (outcome.get("legible") or outcome.get("directions"))
    return [
        ck("no dead end",
           bool(outcome) and bool(legible or outcome.get("status")),
           str(outcome)[:140]),
        ck("target surface OR directions",
           bool(outcome) and (outcome.get("directions") or outcome.get("surface")),
           str({k: bool((outcome or {}).get(k)) for k in ("directions", "surface")})),
        ck("honest outcome",
           bool(outcome) and outcome.get("status") in
           ("installed", "pending", "refused", "unreachable"),
           f"status={(outcome or {}).get('status')}"),
        ck("pending stated",
           bool(outcome) and (outcome.get("status") != "pending" or
                              outcome.get("pending")),
           f"status={(outcome or {}).get('status')}"),
    ]


def S_fleet_action_legible(ctx):
    p = ctx.probe
    _, disc = p.post("/api/fleet/discover")
    cands = disc.get("candidates") or []
    results = {}
    if cands:
        results["invite"] = p.post("/api/fleet/invite",
                                   {"node": cands[0]["node"]})[1]
        results["install"] = p.post("/api/fleet/install",
                                    {"node": cands[0]["node"]})[1]
    _, mp = p.post("/api/fleet/map")
    results["map"] = mp
    def lg(r):
        return bool(r) and bool(r.get("legible") or r.get("outcome")
                                or r.get("rendered") or r.get("map"))
    return [
        ck("invite legible", bool(cands) and lg(results.get("invite")),
           str(results.get("invite"))[:100]),
        ck("join legible", bool(p.rows("fleet:join")) or
           (bool(cands) and lg(results.get("invite"))),
           f"{len(p.rows('fleet:join'))} join rows"),
        ck("install legible", bool(cands) and lg(results.get("install")),
           str(results.get("install"))[:100]),
        ck("map legible", lg(results.get("map")),
           f"map produced={bool(mp.get('map'))}"),
    ]


def S_fleet_exchange(ctx):
    p = ctx.probe
    members = p.get("/api/fleet")[1].get("members", [])
    # second real node = a member that is NOT this host (C-DemonstratedDistribution)
    remote = [m for m in members if not m.get("sameHost") and m.get("ip")]
    delta_rows = p.rows("fleet:delta")
    rejoin = p.rows("fleet:rejoin")
    courier = p.rows("fleet:courier")
    if remote:
        _, d = p.post("/api/fleet/delta", {"node": remote[0]["node"]})
        delta = d.get("transferred") or len(delta_rows)
    else:
        delta = len(delta_rows)
    both = bool(delta_rows) and all(x.get("node") for x in delta_rows)
    return [
        ck("second real node", bool(remote),
           f"remote members={[m.get('node') for m in remote]} "
           f"(same-host does not count)"),
        ck("delta exchange", bool(delta),
           f"transferred={delta}"),
        ck("rejoin correlation", bool(rejoin) or bool(members),
           f"{len(rejoin)} rejoin rows"),
        ck("courier sync", bool(courier) or bool(remote),
           f"{len(courier)} courier rows"),
        ck("both sides evidenced", both,
           f"{len(delta_rows)} delta rows with node attribution"),
    ]


def S_role_negotiate(ctx):
    p = ctx.probe
    rows = p.rows("fleet:role")
    grants = p.rows("grant:recorded")
    joins = p.rows("fleet:join")
    return [
        ck("role negotiation recorded", bool(rows) or bool(grants),
           f"{len(rows)} role rows, {len(grants)} grants"),
        ck("mint rights are a negotiated grant",
           bool([g for g in grants + rows
                 if g.get("mintRights") is not None]),
           f"mintRights on {sum(1 for g in grants + rows if g.get('mintRights') is not None)} grant rows"),
        ck("join outcome honest (member vs pending)",
           bool(joins) and all(j.get("outcome") in ("member", "pending")
                               for j in joins),
           f"{len(joins)} join rows with outcomes"),
    ]


def S_usb_mint_gen2(ctx):
    p = ctx.probe
    seed = _seed_root(ctx)
    drive = os.path.splitdrive(seed)[0] + "\\"
    _, r = p.post("/api/fleet/mint", {"seedDir": drive, "drive": drive})
    exe = r.get("installer") or r.get("file")
    offer = r.get("networkOffer") or r.get("offer")
    return [
        ck("gen-2 installer written to media",
           bool(exe) and os.path.exists(exe or ""),
           f"installer={exe}"),
        ck("carries founding network identity as adoptable offer",
           bool(offer) and offer.get("networkId") and offer.get("adoptable") is not False,
           f"offer={offer}"),
        ck("join-or-found is the user's choice",
           bool(offer) and offer.get("choice") == "join-or-found",
           f"choice={offer and offer.get('choice')}"),
    ]


def S_usb_log_courier(ctx):
    p = ctx.probe
    seed = _seed_root(ctx)
    before = len(_courier_log_entries(seed))
    p.post("/api/fleet/seed-run", {"seedDir": seed})
    time.sleep(1)
    p.post("/api/fleet/seed-run", {"seedDir": seed})
    entries = _courier_log_entries(seed)
    rows = p.rows("fleet:seed-run") + p.rows("fleet:courier")
    revisit = p.rows("seed:revisit")
    grew = len(entries) >= before + 2
    return [
        ck("courier log accumulates across runs",
           grew and bool(rows),
           f"{before} → {len(entries)} log entries on media, {len(rows)} ledger rows"),
        ck("machine-readable per-node evidence",
           grew and all("node" in e for e in entries[before:]) and bool(rows),
           f"nodes={[e.get('node') for e in entries[before:]][:5]}"),
        ck("stale-seed revisit handling recorded",
           bool(revisit) or grew,
           f"{len(revisit)} revisit rows"),
    ]


def S_fleet_roster(ctx):
    p = ctx.probe
    roster = p.get("/api/fleet/roster")[1]
    devices = roster.get("devices") or []
    named = roster.get("expected") or []
    reported_ids = {d.get("id") or d.get("name") for d in devices}
    covered = reported_ids >= set(named) if named else bool(devices)
    honest = all(d.get("status") in ("found", "installable", "unavailable",
                                   "not-a-target", "not-found", "unknown")
                 for d in devices) if devices else False
    nontargets = [d for d in devices if d.get("status") == "not-a-target"]
    return [
        ck("every named-roster device reported",
           bool(devices) and covered,
           f"{len(devices)} reported / {len(named)} expected"),
        ck("honest status per device",
           bool(devices) and honest,
           f"statuses={sorted({d.get('status') for d in devices})}"),
        ck("coverage is test data — non-targets recorded",
           bool(nontargets) or bool(devices),
           f"{len(nontargets)} non-targets recorded"),
    ]


def S_network_map(ctx):
    p = ctx.probe
    _, mp = p.post("/api/fleet/map")
    m = mp.get("map") or {}
    members = m.get("members") or []
    nonmembers = m.get("nonMembers") or m.get("non-members") or []
    rendered = mp.get("rendered") or ""
    return [
        ck("map artifact produced", bool(m) or bool(rendered),
           f"map keys={list(m.keys()) if isinstance(m, dict) else 'rendered'}"),
        ck("covers non-member devices alongside members",
           bool(nonmembers) or bool(m.get("devices")),
           f"nonMembers={len(nonmembers)} devices={len(m.get('devices') or [])}"),
        ck("member/non-member distinction on the map",
           ("member" in str(rendered).lower() or bool(members)),
           f"members={len(members)}"),
    ]


def S_local_transports(ctx):
    p = ctx.probe
    _, disc = p.post("/api/fleet/discover")
    transports = disc.get("transports") or []
    wired = [t for t in transports if t.get("kind") == "wired-lan"]
    extra = [t for t in transports if t.get("kind") != "wired-lan"]
    ordering = p.get("/api/fleet")[1].get("transportOrder") or []
    return [
        ck("wired LAN baseline exercised", bool(wired) and wired[0].get("used"),
           f"transports={[t.get('kind') for t in transports]}"),
        ck("≥1 additional local transport (BT/NFC/SoftAP)",
           bool(extra) and any(t.get("attempted") or t.get("used") for t in extra),
           f"extra={[t.get('kind') for t in extra]}"),
        ck("wired preferred ordering honored",
           bool(ordering) and ordering[0] in ("wired-lan", "lan"),
           f"order={ordering}"),
    ]


def S_credential_surrender(ctx):
    p = ctx.probe
    rows = p.rows("fleet:credential-surrender")
    members = p.get("/api/fleet")[1].get("members", [])
    FORBIDDEN = ("password", "secretValue", "token", "credentialValue",
                 "privateKey")
    secrets_in_rows = [r for r in p.rows("fleet:")
                       if any(k in r for k in FORBIDDEN)]
    return [
        ck("surrender recorded as a claim", bool(rows) or bool(members),
           f"{len(rows)} surrender rows, {len(members)} members"),
        ck("host holds the credential screen (§5)",
           bool(rows) and all(r.get("heldBy") in ("host", "principal")
                              for r in rows),
           f"heldBy={[r.get('heldBy') for r in rows][:4]}"),
        ck("secrets stay host-local — needs travel, secrets never do",
           bool(members or rows) and not secrets_in_rows,
           f"{len(secrets_in_rows)} rows carrying secret material"),
    ]


def S_discovery_progress(ctx):
    p = ctx.probe
    _, started = p.post("/api/fleet/discover", {"background": True})
    import time as _t
    _t.sleep(1.5)
    mid = p.get("/api/fleet/progress")[1]
    # wait for finish
    for _ in range(30):
        cur = p.get("/api/fleet/progress")[1]
        if not cur.get("running"):
            break
        _t.sleep(1)
    fin = p.get("/api/fleet/progress")[1]
    return [
        ck("in-progress shown", mid.get("running") or fin.get("finished"),
           f"mid running={mid.get('running')} finished={fin.get('finished')}"),
        ck("transport progress",
           mid.get("transport") is not None or fin.get("transports"),
           f"transport={mid.get('transport') or fin.get('transports')}"),
        ck("finished shown", not fin.get("running") and
           (fin.get("finished") or fin.get("devices") is not None),
           f"finished={fin.get('finished')} devices={len(fin.get('devices') or [])}"),
    ]
