"""run-suite — enact all 71 scenarios through the operator surface and
emit evidence/scenarios/S-*.json + evidence/summary.json.
Phases:
  A. launch-check (4 legs) in its own subprocess
  B. boot chorus instance on :9790 with runtime-suite
  C. fleet discovery (background) + all scenario functions
  D. USB seed enactment on H: (prepare, launch-in-place, consent, gen-2)
  E. second-node peer exchange (same-host — honestly scored, NOT a joined
     device per direction; exercised for protocol evidence)
  F. restart recovery — kill, relaunch on same runtime, verify
"""
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from suite.common import get, post, Rec, wait_for, journal_rows, current_rows  # noqa
from suite import scen_core, scen_surfaces  # noqa
PORT = 9790
PEER_PORT = 9795
RUNTIME = os.path.join(ROOT, "runtime-suite")
EVDIR = os.path.join(ROOT, "evidence")
SCEN_DIR = os.path.join(EVDIR, "scenarios")
MEDIA = "H:\\"
SEED_DIR = os.path.join(MEDIA, "chorus-seed")
def spawn(port, runtime, extra=None, cwd=ROOT, seed=False):
    cmd = [sys.executable, "-m", "chorus", "--port", str(port),
           "--runtime", runtime, "--no-browser"] + (extra or [])
    if seed:
        cmd.append("--seed")
    return subprocess.Popen(
        cmd, cwd=cwd, stdout=open(os.path.join(
            ROOT, "evidence", f"console-{port}.log"), "w"),
        stderr=subprocess.STDOUT, text=True)
def wait_up(port, timeout=90, part2=False):
    def _():
        try:
            h = get("/api/hello", port=port)
            if part2 and not h.get("part2"):
                return None
            return h
        except Exception:
            return None
    return wait_for(_, timeout, 1.0)
def kill(proc):
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=10)
ORDER = [
    # (scenario-id, module.fn, phase)
    ("S-assertion-input", scen_core.s_assertion_input),
    ("S-template-need", scen_core.s_template_need),
    ("S-candidate-ranking", scen_core.s_candidate_ranking),
    ("S-focused-need", scen_core.s_focused_need),
    ("S-intent-routing", scen_core.s_intent_routing),
    ("S-list-project", scen_core.s_list_project),
    ("S-need-fulfillment", scen_core.s_need_fulfillment),
    ("S-background-present", scen_core.s_background_present),
    ("S-competing-tools", scen_core.s_competing_tools),
    ("S-asset-anticipation", scen_core.s_asset_anticipation),
    ("S-tool-composition", scen_core.s_tool_composition),
    ("S-chat-invocation", scen_core.s_chat_invocation),
    ("S-conversational-register", scen_core.s_conversational_register),
    ("S-faithful-voice", scen_core.s_faithful_voice),
    ("S-distinct-preloadeds", scen_core.s_distinct_preloadeds),
    ("S-personality-create", scen_core.s_personality_create),
    ("S-personality-editor", scen_core.s_personality_editor),
    ("S-personality-source-match", scen_core.s_personality_source_match),
    ("S-personality-roster", scen_core.s_personality_roster),
    ("S-dyadic-ranking", scen_core.s_dyadic_ranking),
    ("S-respondent-union", scen_core.s_respondent_union),
    ("S-response-depth", scen_core.s_response_depth),
    ("S-interest-respondents", scen_core.s_interest_respondents),
    ("S-conversation-reset", scen_core.s_conversation_reset),
    ("S-context-display", scen_core.s_context_display),
    ("S-email-commentary", scen_core.s_email_commentary),
    ("S-account-configure", scen_core.s_account_configure),
    ("S-speech-serialization", scen_core.s_speech_serialization),
    ("S-speech-completion", scen_core.s_speech_completion),
    ("S-voice-spec", scen_core.s_voice_spec),
    ("S-voice-select", scen_core.s_voice_select),
    ("S-voice-assign", scen_core.s_voice_assign),
    ("S-audible-ack", scen_core.s_audible_ack),
    ("S-speech-latency", scen_core.s_speech_latency),
    ("S-windows-launch", scen_surfaces.s_windows_launch),
    ("S-close-terminate", scen_surfaces.s_close_terminate),
    ("S-color-schemes", scen_surfaces.s_color_schemes),
    ("S-status-bar", scen_surfaces.s_status_bar),
    ("S-library-browse", scen_surfaces.s_library_browse),
    ("S-source-seed-import", scen_surfaces.s_source_seed_import),
    ("S-source-admission-gate", scen_surfaces.s_source_admission_gate),
    ("S-publish-workflow", scen_surfaces.s_publish_workflow),
    ("S-defer-publication", scen_surfaces.s_defer_publication),
    ("S-scancode-interchange", scen_surfaces.s_scancode_interchange),
    ("S-background-channels", scen_surfaces.s_background_channels),
    ("S-interstitial-queue", scen_surfaces.s_interstitial_queue),
    ("S-scene-enactment", scen_surfaces.s_scene_enactment),
    ("S-fleet-invite", scen_surfaces.s_fleet_invite),
    ("S-fleet-install-path", scen_surfaces.s_fleet_install_path),
    ("S-fleet-action-legible", scen_surfaces.s_fleet_action_legible),
    ("S-fleet-roster", scen_surfaces.s_fleet_roster),
    ("S-network-map", scen_surfaces.s_network_map),
    ("S-local-transports", scen_surfaces.s_local_transports),
    ("S-credential-surrender", scen_surfaces.s_credential_surrender),
    ("S-discovery-progress", scen_surfaces.s_discovery_progress),
    ("S-exchange-import", scen_surfaces.s_exchange_import),
    ("S-artifact-import", scen_surfaces.s_artifact_import),
    ("S-tool-transmission", scen_surfaces.s_tool_transmission),
    ("S-artifact-style", scen_surfaces.s_artifact_style),
    ("S-artifact-republish", scen_surfaces.s_artifact_republish),
    ("S-dubious-source", scen_surfaces.s_dubious_source),
    ("S-preload-cache", scen_surfaces.s_preload_cache),
    ("S-portrait-bind", None),          # composite — runner inline
    ("S-restart-recovery", None),       # post-restart
    ("S-snapshot-inference", None),     # not in suite — skip marker
]
# actual 71 list (order of execution; S-portrait-bind + S-restart-recovery
# handled specially)
REAL_ORDER = [x for x in ORDER if x[0] != "S-snapshot-inference"]
def run_one(sid, fn, runtime, extra=None):
    rec = Rec(sid)
    t0 = time.time()
    try:
        if extra:
            fn(rec, runtime, extra)
        else:
            fn(rec, runtime)
    except Exception as e:
        import traceback
        rec.check("driver-error", False, traceback.format_exc()[-300:])
    rec.extra["seconds"] = round(time.time() - t0, 1)
    out = rec.emit(SCEN_DIR)
    ok = out["pass"]
    failed = [c["name"] for c in out["checks"] if not c["pass"]]
    print(f"  {'PASS' if ok else 'FAIL'} {sid} "
          f"({len(out['checks'])} checks, {out['seconds']}s)"
          + ("" if ok else f"  <- {failed}"))
    return out
def usb_enactment():
    """Phase D — real USB: launch seed in place on H:, consent both ways,
    mint gen-2."""
    print("USB enactment on H: ...")
    # 1. mint the seed payload onto media from the running hub
    mint = post("/api/seed/mint-gen2", {"media": MEDIA}, timeout=180)
    if isinstance(mint, dict) and mint.get("error"):
        print("  mint-gen2 ERROR:", mint.get("trace", mint))
    # wait for the copy
    wait_for(lambda: os.path.exists(os.path.join(
        SEED_DIR, "chorus", "__main__.py")), 60, 1)
    # 2. launch the seed instance IN PLACE from the media (twice — second
    #    run is the stale-seed revisit)
    for port in (9796, 9797):
        proc = subprocess.Popen(
            [sys.executable, "-m", "chorus", "--port", str(port),
             "--runtime", os.path.join(SEED_DIR, "runtime"),
             "--no-browser", "--seed"],
            cwd=SEED_DIR,
            stdout=open(os.path.join(EVDIR, f"console-seed-{port}.log"),
                        "w"), stderr=subprocess.STDOUT)
        up = wait_up(port, timeout=240, part2=True)
        print(f"  seed :{port} up={bool(up)}")
        if up:
            post("/api/seed/consent", {"allowed": False}, port=port)
            time.sleep(0.3)
            post("/api/seed/consent", {"allowed": True}, port=port)
        kill(proc)
        time.sleep(1)
def peer_exchange():
    """Phase E — second chorus instance for peer-protocol exchange evidence.
    Same host: honestly does NOT count as a joined device (direction)."""
    print("peer exchange ...")
    rt2 = os.path.join(ROOT, "runtime-peer")
    proc = spawn(PEER_PORT, rt2, extra=["--node", "node-peer-lab"])
    up = wait_up(PEER_PORT, part2=True, timeout=240)
    if not up:
        return False
    time.sleep(2)
    # real join: invite via main hub, then peer presents key
    inv = post("/api/fleet/invite", {"ip": "127.0.0.1"})
    key = (inv.get("invite") or {}).get("inviteKey")
    try:
        joined = post("/peer/join",
                      {"inviteKey": key, "from": "node-peer-lab",
                       "ip": "127.0.0.1", "role": "surface",
                       "at": time.strftime("%Y-%m-%dT%H:%M:%S")})
        print("  join:", joined)
        sync = post("/api/fleet/sync", {"ip": "127.0.0.1"})
        print("  sync:", str(sync)[:120])
    except Exception as e:
        print("  join failed:", e)
        joined = None
    kill(proc)
    return joined
def main():
    os.makedirs(SCEN_DIR, exist_ok=True)
    t0 = time.time()
    results = {}
    # --- A. launch-check ---
    print("phase A: launch-check")
    lc = subprocess.run([sys.executable,
                         os.path.join(ROOT, "scripts", "launch-check.py")],
                        cwd=ROOT, capture_output=True, text=True,
                        timeout=180)
    print(" ", lc.stdout[-300:] if lc.stdout else lc.stderr[-300:])
    # --- B. boot suite instance ---
    print("phase B: boot")
    # pre-flight: a stale instance on the suite port would own the bind and
    # make our spawned child refuse — kill it via its own surface
    try:
        post("/api/shutdown", {}, port=PORT)
        time.sleep(1.5)
    except Exception:
        pass
    if os.path.exists(RUNTIME):
        shutil.rmtree(RUNTIME)
    proc = spawn(PORT, RUNTIME)
    up = wait_up(PORT, part2=True, timeout=300)
    if not up:
        print("FATAL: app did not come up"); kill(proc); sys.exit(1)
    # verify the answering instance is the one we spawned (its node-id lives
    # in our runtime), not a stale owner
    node_file = os.path.join(RUNTIME, "node-id")
    our_node = open(node_file).read().strip() if os.path.exists(node_file) \
        else None
    if our_node and up.get("node") != our_node:
        print(f"FATAL: port owned by stale instance {up.get('node')} "
              f"(ours={our_node})"); kill(proc); sys.exit(1)
    gate = wait_for(lambda: (lambda g: g if g.get("ok") else None)(
        get("/api/gate")), 60, 1)
    print("  gate:", gate and gate.get("ok"), gate and gate.get("timeToGateMs"))
    # start fleet discovery early (background)
    post("/api/fleet/discover")
    # --- C. scenario sweep ---
    print("phase C: scenario sweep")
    pending = {}
    for sid, fn in REAL_ORDER:
        if fn is None:
            pending[sid] = True
            continue
        results[sid] = run_one(sid, fn, RUNTIME)
    # roster-move result holder
    results["S-portrait-bind"] = portrait_bind(RUNTIME)
    # --- D. USB ---
    usb_enactment()
    for sid, fn in (("S-usb-seed-run", scen_surfaces.s_usb_seed_run),
                    ("S-usb-stage-consent", scen_surfaces.s_usb_stage_consent),
                    ("S-usb-mint-gen2", scen_surfaces.s_usb_mint_gen2),
                    ("S-usb-log-courier", scen_surfaces.s_usb_log_courier)):
        results[sid] = run_one(sid, fn, RUNTIME)
    # --- E. peer exchange ---
    joined = peer_exchange()
    time.sleep(1)
    results["S-fleet-exchange"] = run_one(
        "S-fleet-exchange", scen_surfaces.s_fleet_exchange, RUNTIME,
        extra={"peerJoin": joined, "sameHost": True})
    results["S-role-negotiate"] = run_one(
        "S-role-negotiate", scen_surfaces.s_role_negotiate, RUNTIME)
    # --- F. restart recovery ---
    print("phase F: restart recovery")
    voices_before = {p["id"]: (p.get("voice") or {}).get("name")
                     for p in get("/api/roster")["roster"]}
    passes_before = (get("/api/state").get("liveness") or {}).get("passes", 0)
    personas_before = len(get("/api/roster")["roster"])
    kill(proc)
    time.sleep(1.5)
    proc = spawn(PORT, RUNTIME)
    wait_up(PORT, part2=True, timeout=180)
    gate2 = wait_for(lambda: (lambda g: g if g.get("ok") else None)(
        get("/api/gate")), 90, 1)
    time.sleep(3)
    rec = Rec("S-restart-recovery")
    scen_core.s_restart_recovery(rec, RUNTIME)
    rec.extra["seconds"] = 0
    results["S-restart-recovery"] = rec.emit(SCEN_DIR)
    print("  restart-recovery:", results["S-restart-recovery"]["pass"])
    lv2 = get("/api/state").get("liveness") or {}
    rec2 = Rec("S-steward-liveness")
    scen_core.s_steward_liveness(rec2, RUNTIME,
                                 liveness_after_restart=lv2,
                                 liveness_before={"passes": passes_before})
    results["S-steward-liveness"] = rec2.emit(SCEN_DIR)
    print("  steward-liveness:", results["S-steward-liveness"]["pass"],
          f"{passes_before} -> {lv2.get('passes')}")
    # voice stability across relaunch leg
    rec3 = Rec("S-voice-assign")
    scen_core.s_voice_assign(rec3, RUNTIME)
    voices_after = {p["id"]: (p.get("voice") or {}).get("name")
                    for p in get("/api/roster")["roster"]}
    stable = voices_before == voices_after
    for c in rec3.checks:
        if c["name"] == "assigned voice stable across relaunch":
            c["pass"] = stable
            c["detail"] = f"voices identical post-restart: {stable}"
    rec3.extra["seconds"] = 0
    rec3_out = {"id": "S-voice-assign", "ran": True, "checks": rec3.checks,
                "pass": all(c["pass"] for c in rec3.checks),
                "evidence_class": "enactment"}
    with open(os.path.join(SCEN_DIR, "S-voice-assign.json"), "w",
              encoding="utf-8") as f:
        json.dump(rec3_out, f, indent=1)
    results["S-voice-assign"] = rec3_out
    # depth persists check (settings row is durable)
    st = get("/api/state")
    va = os.path.join(SCEN_DIR, "S-response-depth.json")
    if os.path.exists(va):
        d = json.load(open(va))
        dep_rows = [r for r in journal_rows(RUNTIME)
                    if r["kind"] == "settings:set"
                    and r["claim"].get("subject") == "chat:response-depth"]
        last_set = dep_rows[-1]["claim"].get("value") if dep_rows else None
        for c in d["checks"]:
            if c["name"] == "persists":
                c["pass"] = bool(dep_rows) and \
                    st.get("depth") == last_set
                c["detail"] = (f"depth after restart: {st.get('depth')} "
                               f"== last durable set {last_set} "
                               f"({dep_rows and dep_rows[-1]['id']})")
        d["pass"] = all(c["pass"] for c in d["checks"])
        json.dump(d, open(va, "w"), indent=1)
        results["S-response-depth"] = d
    kill(proc)
    # --- summary ---
    npass = sum(1 for r in results.values() if r and r.get("pass"))
    summary = {"suite": "scenarios.md consolidated 2026-11-25",
               "ran": len(results), "passed": npass,
               "failed": sorted(s for s, r in results.items()
                                if r and not r.get("pass")),
               "seconds": round(time.time() - t0, 1),
               "app": "chorus", "port": PORT}
    with open(os.path.join(EVDIR, "summary.json"), "w",
              encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    print(f"\nsuite complete: {npass}/{len(results)} passed "
          f"in {summary['seconds']}s")
    print("failures:", summary["failed"])
def portrait_bind(runtime):
    """S-portrait-bind — composite across shipped + minted personas."""
    rec = Rec("S-portrait-bind")
    roster = get("/api/roster")["roster"]
    files = [p for p in os.listdir(os.path.join(runtime, "personas"))
             if p.endswith(".svg")] if os.path.isdir(
        os.path.join(runtime, "personas")) else []
    rec.check("portrait file produced", len(files) >= 4,
              f"{len(files)} svg files")
    bound = [p for p in roster if p.get("portrait")]
    rec.check("art bound to this persona",
              len(bound) >= 4, f"{len(bound)}/{len(roster)} bound")
    gen = [p for p in bound if (p["portrait"] or {}).get("basis") or
           (p["portrait"] or {}).get("authored") is not None]
    rec.check("generative path declared", bool(gen),
              gen and json.dumps(gen[0]["portrait"])[:120])
    rec.check("auto-bound shipped",
              all(p.get("portrait") for p in roster if p.get("shipped")),
              f"{len([p for p in roster if p.get('shipped') and p.get('portrait')])} shipped")
    rec.check("auto-bound minted",
              all(p.get("portrait") for p in roster if not p.get("shipped")),
              f"{len([p for p in roster if not p.get('shipped') and p.get('portrait')])} minted")
    fb = [p for p in bound
          if (p["portrait"] or {}).get("authored") is False]
    legible = all("declared" in (p["portrait"] or {}) or
                  "authored" in (p["portrait"] or {}) or
                  "engine" in (p["portrait"] or {}) for p in bound)
    rec.check("fallback legible",
              legible and all(f.get("declared") is True or
                              f.get("authored") is False
                              for f in
                              [x["portrait"] for x in fb]),
              f"{len(fb)} fallback-marked of {len(bound)} bound")
    out = rec.emit(SCEN_DIR)
    print(f"  {'PASS' if out['pass'] else 'FAIL'} S-portrait-bind")
    return out
if __name__ == "__main__":
    main()
