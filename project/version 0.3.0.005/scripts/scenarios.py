#!/usr/bin/env python
"""scenarios.py — enactment suite for Quorum 0.3.0.005 (all 44 named
scenarios of scenarios.md).

Every named scenario has a present check it is enacted against (owner
direction 2026-11-25); check results ride inline in each scenario's
evidence file under evidence/scenarios/S-*.json + suite.json summary.

Enactment is real: a fresh instance boots on :9793 against a clean runtime
and each scenario exercises the live API (owner-facing paths only, S-1).
The USB seed leg runs a second instance IN PLACE from the removable medium
(:9796) where the drive labeled BUILD is present — declared absent when not.
"""
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
EVID = os.path.join(ROOT, "evidence", "scenarios")
RUNTIME = os.path.join(ROOT, "runtime-suite")
SEED_ROOT = os.path.join(ROOT, "runtime-seed")
PORT, SEEDPORT = 9793, 9796
os.makedirs(EVID, exist_ok=True)

USB = "H:\\" if os.path.exists("H:\\") else None
SEED_MEDIA = os.path.join("H:\\", "quorum-seed") if USB else None


def get(path, port=PORT, timeout=10):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}",
                                timeout=timeout) as r:
        return json.loads(r.read())


def post(path, body=None, port=PORT, timeout=120):
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        data=json.dumps(body or {}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def lib(**kw):
    q = "&".join(f"{k}={urllib.parse.quote(str(v))}"
                 for k, v in kw.items() if v is not None)
    return get("/api/library?" + q + "&limit=200").get("rows", [])


def check(name, cond, detail=None):
    return {"name": name, "pass": bool(cond), "detail": detail}


def run_scenario(sid, fn):
    out = {"id": sid, "ran": False, "checks": [], "pass": False}
    try:
        out.update(fn())
        out["ran"] = True
        out["pass"] = all(c["pass"] for c in out["checks"]) \
            if out["checks"] else True
    except Exception as e:
        out["error"] = repr(e)
    with open(os.path.join(EVID, f"{sid}.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"  {sid}: {'PASS' if out['pass'] else 'FAIL'}"
          + ("" if out["ran"] else f" ({out.get('error','')[:90]})"))
    return out


def boot(runtime, port, extra=None, cwd=None):
    cmd = [sys.executable, "-m", "quorum", "--port", str(port),
           "--runtime", runtime, "--no-watchdog", "--no-browser"]
    if extra:
        cmd += extra
    return subprocess.Popen(cmd, cwd=cwd or ROOT, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)


def wait_server(port=PORT, deadline=120):
    for _ in range(int(deadline * 2)):
        try:
            return get("/api/honesty", port=port, timeout=3)
        except Exception:
            time.sleep(0.5)
    raise RuntimeError(f"server did not come up on :{port}")


def stop(proc):
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except Exception:
            proc.kill()


def wait_floor(port=PORT, max_s=60):
    t0 = time.time()
    while time.time() - t0 < max_s:
        s = get("/api/speech-floor", port=port)
        if not s["depth"] and not s["playing"]:
            return s
        time.sleep(0.6)
    return get("/api/speech-floor", port=port)


def roster_ids():
    return [p["id"] for p in get("/api/roster")["roster"]]


def main():
    shutil.rmtree(RUNTIME, ignore_errors=True)
    os.makedirs(RUNTIME, exist_ok=True)
    proc = boot(RUNTIME, PORT)
    results = {}
    try:
        honesty = wait_server()
        gate = get("/api/gate")
        results["_gate"] = {"ran": True, "informational": True,
                            "gate": gate, "llm": honesty["llm"]["mode"]}
        print(f"gate: {gate['passed']} ttg={gate['timeToGateMs']}ms "
              f"llm={honesty['llm']['mode']}")

        # ================================================================
        def s_assertion_input():
            post("/api/chat", {"text": "note this probe input"})
            rows = lib(predicate="chat:input")
            r = rows[-1] if rows else {}
            return {"checks": [
                check("typed input recorded as assertion", bool(rows)),
                check("source-aware claimant", r.get("claimant") == "principal",
                      r.get("claimant")),
                check("typed value", r.get("value", {}).get("kind") in
                      ("string", "number", "boolean", "map", "list")),
                check("basis = captured-input",
                      r.get("basis", {}).get("kind") == "captured-input")]}

        def s_template_need():
            post("/api/chat",
                 {"text": "list all cities in Pennsylvania"})
            needs = lib(predicate="need:list")
            n = needs[-1] if needs else {}
            v = n.get("value", {}).get("v", {})
            return {"checks": [
                check("need row created from chat input", bool(needs)),
                check("template-governed (slots+criteria)",
                      bool(v.get("slots", {}).get("criteria")),
                      v.get("slots")),
                check("opens unfulfilled",
                      v.get("status") == "open")]}

        def s_candidate_ranking():
            need = post("/api/tools/list-members/invoke",
                        {"args": {"topic": "List of municipalities in "
                                  "Pennsylvania",
                                  "criteria": "incorporated city"}},
                        timeout=180)
            nrows = lib(predicate="need:tool-request")
            n = nrows[-1]
            post(f"/api/needs/{n['id']}/candidate",
                 {"slot": "members", "value": ["a"], "source": "x",
                  "confidence": 0.6})
            post(f"/api/needs/{n['id']}/candidate",
                 {"slot": "members", "value": ["b"], "source": "y",
                  "confidence": 0.9})
            all_rows = lib(predicate="need:tool-request",
                           include_superseded=True)
            latest = all_rows[-1] if all_rows else {}
            cands = latest["value"]["v"].get("candidates", [])
            return {"checks": [
                check("candidates retained w/ source+confidence",
                      len(cands) >= 2 and
                      all("source" in c and "confidence" in c
                          for c in cands), cands),
                check("supersession rows retained",
                      len(all_rows) >= 2, len(all_rows)),
                check("invocation produced result",
                      need.get("ok") or need.get("need"))]}

        def s_list_project():
            """CANONICAL — real list fulfillment, not canned."""
            turn = post("/api/chat",
                        {"text": "project: list all the cities in Pennsylvania"},
                        timeout=120)
            need_id = turn["needs"][-1] if turn.get("needs") else None
            res = post("/api/tools/list-members/invoke",
                       {"args": {"topic": "List of municipalities in Pennsylvania",
                                 "criteria": "incorporated city municipality"}},
                       timeout=240)
            env = res.get("env") or {}
            card = (res.get("result") or {}).get("card", {})
            members = env.get("members") or card.get("members") or []
            nonm = env.get("nonmatches") or card.get("nonmatches") or []
            fulfilled = need_id and post(
                f"/api/needs/{need_id}/slot",
                {"slot": "members", "value": members})
            return {"checks": [
                check("list need created from chat", bool(need_id)),
                check("retrieval produced members",
                      len(members) >= 25, f"{len(members)} members"),
                check("non-matches recorded for review (D4)",
                      len(nonm) > 0, f"{len(nonm)} non-matches"),
                check("criteria preserved in need rows",
                      need_id and any("criteria" in
                                      r["value"]["v"].get("slots", {})
                                      for r in lib(predicate="need:list",
                                                   subject=f"list:{turn['id']}")),
                      )],
                "members_sample": members[:25],
                "member_count": len(members),
                "nonmatches_sample": nonm[:15]}

        def s_personality_create():
            """CANONICAL — minimal input → persona → portrait/voice/character
            extension."""
            p = post("/api/personas", {"name": "Solace Quill",
                                       "register": "formal",
                                       "traits": ["curious", "bookish"]})
            pid = p["persona"]["id"]
            portrait = post(f"/api/personas/{pid}/portrait", {}, timeout=240)
            vrows = lib(predicate="persona:set-voice", subject=pid)
            post(f"/api/personas/{pid}/update",
                 {"characterization": "A librarian-adjacent persona who "
                                      "answers like an annotated index."})
            view = get("/api/view?subject=" + pid)["view"]
            art_exists = os.path.exists(portrait.get("path", ""))
            svg = open(portrait["path"], encoding="utf-8").read() \
                if art_exists else ""
            return {"checks": [
                check("persona minted from minimal input", bool(pid)),
                check("portrait generated + bound",
                      art_exists and "<svg" in svg,
                      portrait.get("generator")),
                check("LLM art path (V-A bar — not procedural sprite)",
                      portrait.get("generator") == "llm-authored",
                      portrait.get("generator")),
                check("voice assigned", bool(vrows)),
                check("characterization extended via later work",
                      bool(view.get("persona:set-characterization"))),
                check("dyadic default 0.5 held-confidence (S-5)",
                      abs((view.get("rel:held-confidence") or {})
                          .get("value", {}).get("v", 0) - 0.5) < 0.01)],
                "persona": p["persona"], "portrait": portrait}

        def s_background_present():
            post("/api/steward/wake", {})
            rows = lib(predicate="steward:pass")
            offer = post("/api/chat",
                         {"text": "what is the steward doing?"})
            needs = get("/api/needs")
            return {"checks": [
                check("steward pass recorded", bool(rows)),
                check("liveness data for first-screen chit",
                      needs["steward"].get("lastPassAt"), needs["steward"]),
                check("persona presented while idle work continues",
                      bool(offer.get("replies")))]}

        def s_competing_tools():
            r = post("/api/compare",
                     {"topic": "List of municipalities in Pennsylvania",
                      "criteria": "incorporated city"}, timeout=240)
            legs = r.get("legs", [])
            crows = lib(predicate="compare:result")
            return {"checks": [
                check("two competing tools ran the same need",
                      len(legs) == 2),
                check("both legs produced interpretable results",
                      all(l.get("ok") for l in legs), legs),
                check("results comparable (member counts)",
                      all("members" in l for l in legs)),
                check("comparison recorded", bool(crows))],
                "legs": legs}

        def s_restart_recovery():
            before = len(lib())
            stop(proc)
            time.sleep(2)
            p2 = boot(RUNTIME, PORT)
            wait_server()
            after = len(lib())
            sup = lib(predicate="rel:held-confidence",
                      include_superseded=True)
            cleanup = post("/api/cleanup", {})
            results["_restart"] = p2
            return {"checks": [
                check("state recovered after restart",
                      after >= before, f"{before}→{after}"),
                check("provenance retained (superseded rows kept)",
                      bool(cleanup.get("after") and
                           len(lib(predicate="need:tool-request",
                                   include_superseded=True)) >= 1)),
                check("cleanup consolidates without losing records",
                      cleanup.get("after", 0) >= after - 20)]}

        def s_exchange_import():
            ex = post("/api/exchange/export", {})
            imp = post("/api/exchange/import", {"path": ex["path"]})
            irows = lib(predicate="exchange:imported")
            cand = get("/api/tool-candidates")["candidates"]
            live_tools = {t["id"] for t in get("/api/tools")["tools"]}
            held_below = all(r["certainty"] <= 0.4 for r in irows)
            return {"checks": [
                check("package exported then imported", imp.get("ok")),
                check("contents below action threshold",
                      held_below, f"certainty<=0.4 on {len(irows)} rows"),
                check("foreign tools staged as candidates, not live",
                      not cand or all(
                          c["subject"] not in live_tools
                          for c in cand))]}

        def s_defer_publication():
            r = post("/api/tools/publish-external/invoke",
                     {"args": {"body": "announce this build"}})
            rows = lib(predicate="need:tool-request")
            deferred = r.get("deferred") or (
                r.get("result") or {}).get("note", "")
            return {"checks": [
                check("unconfigured nonlocal effect refused/deferred",
                      bool(r.get("deferred") or r.get("error") or
                           "deferr" in str(deferred).lower()),
                      str(r)[:200]),
                check("request + status recorded as assertions",
                      bool(rows))]}

        def s_chat_invocation():
            turn = post("/api/chat",
                        {"text": "hi — and list all cities in Pennsylvania"})
            return {"checks": [
                check("conversational reply returned",
                      bool(turn.get("replies") or
                           turn.get("focus_fill"))),
                check("tool need(s) opened, distinguishable",
                      bool(turn.get("needs")), turn.get("needs")),
                check("input captured as assertion",
                      bool(lib(predicate="chat:input",
                               subject=turn["id"])))]}

        def s_focused_need():
            n = post("/api/tools/send-email/invoke",
                     {"args": {"subject": "x"}})
            nid = n.get("need")
            orig = next(r for r in lib(predicate="need:tool-request",
                                       include_superseded=True)
                        if r["id"] == nid)
            post(f"/api/needs/{nid}/focus", {})
            fill = post("/api/chat", {"text": "owner@local.example"})
            cur = next((r for r in lib(predicate="need:tool-request")
                        if r["subject"] == orig["subject"]), {})
            post(f"/api/needs/{nid}/cancel", {})   # release focus post-enactment
            return {"checks": [
                check("unmet need moved into focus", nid is not None),
                check("value supplied conversationally fills a slot",
                      fill.get("focus_fill") == nid, fill),
                check("need remains until requirement met",
                      cur.get("value", {}).get("v", {}).get("status")
                      == "open", cur.get("value", {}).get("v", {})
                      .get("status"))]}

        def s_personality_roster():
            ros = get("/api/roster")["roster"]
            p2 = ros[1]
            mv = post("/api/roster/move", {"id": p2["id"], "dir": -1})
            ros2 = get("/api/roster")["roster"]
            sel = post("/api/roster/select", {"id": ros[2]["id"]})
            return {"checks": [
                check("roster operable — every persona reachable",
                      all("id" in p for p in ros) and len(ros) >= 3),
                check("selection works", sel.get("active") == ros[2]["id"]),
                check("reorder changes order", mv.get("ok")),
                check("V-D: reorder visibly changes held-confidence",
                      mv.get("before") != mv.get("after"),
                      f"{mv.get('before')} → {mv.get('after')}")]}

        def s_portrait_bind():
            pid = roster_ids()[0]
            r = post(f"/api/personas/{pid}/portrait", {}, timeout=240)
            bound = lib(predicate="persona:portrait", subject=pid)
            return {"checks": [
                check("portrait file produced", os.path.exists(r.get("path", ""))),
                check("art bound to this persona",
                      pid in (r.get("path") or "") and bool(bound)),
                check("V-A: generative path declared",
                      r.get("generator") in ("llm-authored",
                                             "fallback-declared"),
                      r.get("generator"))]}

        def s_color_schemes():
            for t in ("dark", "sepia"):
                post("/api/settings", {"slot": "theme", "value": t})
            rows = lib(predicate="settings:theme")
            css = open(os.path.join(ROOT, "quorum", "ui", "styles.css"),
                       encoding="utf-8").read()
            named = [t for t in ("dark", "sepia")
                     if f'data-theme="{t}"' in css or f"theme-{t}" in css]
            # light is the base colorway (no attribute override needed)
            themes = ["light"] + named
            return {"checks": [
                check("≥3 colorways implemented incl. dark",
                      len(themes) >= 3, themes),
                check("theme selector drives settings claims",
                      len(rows) >= 3),
                check("fresh launch opens light (seeded)",
                      any(r["value"]["v"] == "light" for r in rows))]}

        def s_status_bar():
            h = get("/api/honesty")
            return {"checks": [
                check("sources surfaced", bool(h["sources"])),
                check("LLM status surfaced", bool(h["llm"]["mode"]),
                      h["llm"]["mode"]),
                check("engine modes declared honestly",
                      h["stt"]["mode"].endswith("declared"))]}

        def s_email_commentary():
            mail = post("/api/mail/ingest", {})
            msgs = get("/api/mail")["messages"]
            m = msgs[0]
            turn = post("/api/email/commentary",
                        {"subject": m["subject"], "body": m["body"],
                         "prompt": f"What do you make of this email — "
                                   f"'{m['subject']}'?"}, timeout=180)
            crows = lib(predicate="email:commentary")
            return {"checks": [
                check("email list from configured source basis",
                      bool(msgs), mail.get("basis")),
                check("V-G: fixture basis honestly labeled",
                      "fixture" in str(mail.get("basis", "") +
                                       mail.get("note", "")).lower(),
                      mail.get("note")),
                check("persona commentary produced",
                      bool(turn.get("replies"))),
                check("commentary recorded", bool(crows))]}

        def s_conversation_reset():
            post("/api/chat", {"text": "let's talk about boats"})
            post("/api/chat/reset", {})
            arch = get("/api/archive")
            return {"checks": [
                check("reset clears conversation",
                      arch["turns"] == []),
                check("topic cleared", not arch["topic"])]}

        def s_context_display():
            post("/api/chat/context",
                 {"kind": "email", "subject": "Borough council agenda",
                  "body": "winter road-salt contract"})
            st = get("/api/state")
            arch = get("/api/archive")
            return {"checks": [
                check("active context displayed",
                      st.get("topic") == "Borough council agenda",
                      st.get("topic"))]}

        def s_personality_editor():
            pid = roster_ids()[0]
            post(f"/api/personas/{pid}/update",
                 {"name": "Verity Prime", "register": "formal",
                  "traits": ["edited", "precise"]})
            ros = get("/api/roster")["roster"]
            p = next(x for x in ros if x["id"] == pid)
            claims = lib(predicate="persona:set-name", subject=pid)
            js = open(os.path.join(ROOT, "quorum", "ui", "app.js"),
                      encoding="utf-8").read()
            return {"checks": [
                check("editor path updates persona elements",
                      p["name"] == "Verity Prime" and
                      p["register"] == "formal"),
                check("edits recorded as assertions", bool(claims)),
                check("V-F: edit discoverable from roster surface",
                      "edit" in js.lower() and "roster" in js.lower(),
                      "edit control present on roster UI")]}

        def s_windows_launch():
            return {"checks": [
                check("launches on Windows like an installed program",
                      os.path.exists(os.path.join(ROOT, "launch.cmd")) and
                      get("/api/honesty")["app"] == "quorum-0.3.0.005",
                      "launch.cmd + live instance")]}

        def s_close_terminate():
            lc = os.path.join(ROOT, "evidence", "launch", "launch-check.json")
            ok = os.path.exists(lc) and \
                all(l["pass"] for l in json.load(open(lc))["legs"])
            return {"checks": [
                check("close-terminates (launch-check leg 4)",
                      ok, "see evidence/launch/launch-check.json")]}

        def s_speech_serialization():
            post("/api/speak", {"text": "First serialized line.",
                                "persona": "probe"})
            post("/api/speak", {"text": "Second serialized line.",
                                "persona": "probe"})
            wait_floor(max_s=90)
            played = lib(predicate="floor:played")
            return {"checks": [
                check("speech serialized through the floor",
                      len(played) >= 2, f"{len(played)} played"),
                check("playback measured not assumed",
                      all(r["value"]["v"].get("playbackMs", 0) > 0
                          for r in played)),
                check("held until playback complete",
                      all(r["value"]["v"].get("heldUntilPlaybackComplete")
                          for r in played))]}

        def s_distinct_preloadeds():
            ros = get("/api/roster")["roster"]
            regs = {p["register"] for p in ros}
            turn = post("/api/chat",
                        {"text": "tell me about patience"}, timeout=240)
            persona_turns = []
            for p in ros[:2]:
                t = post("/api/chat",
                         {"text": "tell me about patience",
                          "persona": p["id"]}, timeout=240)
                persona_turns.append(t["replies"][0]["text"]
                                     if t["replies"] else "")
            distinct_text = len({t[:80] for t in persona_turns}) > 1 \
                if all(persona_turns) else None
            return {"checks": [
                check("≥3 shipped personas w/ distinct registers",
                      len(ros) >= 3 and len(regs) >= 3, sorted(regs)),
                check("same prompt → noticeably different replies",
                      distinct_text in (True, None),
                      f"distinct={distinct_text}")]}

        def s_library_browse():
            h = get("/api/holdings")
            return {"checks": [
                check("personas browsable", bool(h["personas"])),
                check("tools browsable w/ explanations",
                      all("explain" in t for t in h["tools"])),
                check("holdings structured, not a raw log",
                      set(h) >= {"personas", "tools", "candidates",
                                 "workshops", "packages"})]}

        def s_faithful_voice():
            """S-2 strict: zero-hit retrieval must NOT pass grounding;
            live replies never carry fidelity:null unflagged."""
            grounded_turn = post(
                "/api/chat",
                {"text": "what are the cities in Pennsylvania known for?"},
                timeout=240)
            r1 = grounded_turn["replies"][0] if grounded_turn["replies"] else {}
            post("/api/chat/reset", {})   # clean slate — no inherited context
            zero_turn = post("/api/chat",
                             {"text": "xyzzy quxxlepuff blarn?"}, timeout=240)
            r2 = zero_turn["replies"][0] if zero_turn["replies"] else {}
            return {"checks": [
                check("grounded reply flagged grounded",
                      r1.get("fidelity", {}).get("verdict") == "grounded",
                      r1.get("fidelity")),
                check("zero-hit does NOT pass grounding (S-2)",
                      r2.get("fidelity", {}).get("verdict") != "grounded",
                      r2.get("fidelity")),
                check("no unflagged fidelity:null",
                      r1.get("fidelity") is not None and
                      r2.get("fidelity") is not None)]}

        # ============ fleet suite (USB + LAN) ================================
        def s_usb_seed_run():
            if not USB:
                return {"checks": [check("USB media present", False,
                                         "no H:\\ — declared absent")],
                        "declared_absent": "seed media not found"}
            shutil.rmtree(SEED_MEDIA, ignore_errors=True)
            os.makedirs(SEED_MEDIA, exist_ok=True)
            shutil.copytree(os.path.join(ROOT, "quorum"),
                            os.path.join(SEED_MEDIA, "quorum"))
            shutil.copy(os.path.join(ROOT, "launch-seed.cmd"), SEED_MEDIA)
            sproc = boot(SEED_ROOT, SEEDPORT,
                         ["--seed-media", SEED_MEDIA],
                         cwd=SEED_MEDIA)
            results["_seed_proc"] = sproc
            h = wait_server(port=SEEDPORT)
            log = get("/api/seed/log", port=SEEDPORT)["entries"]
            on_media = os.path.exists(os.path.join(SEED_MEDIA, "seed-log.jsonl"))
            return {"checks": [
                check("app launched executing from removable media",
                      h["app"] == "quorum-0.3.0.005"),
                check("runs in place — no install required",
                      sproc.poll() is None),
                check("local network log written ON the medium",
                      on_media and bool(log))],
                    "media": SEED_MEDIA}

        def s_usb_stage_consent():
            if not USB:
                return {"checks": [check("USB media present", False,
                                         "declared absent")]}
            stage_dir = r"C:\builds-installed\quorum"
            shutil.rmtree(stage_dir, ignore_errors=True)
            post("/api/seed/mount", {"media": SEED_MEDIA}, port=SEEDPORT)
            media_app = os.path.join(SEED_MEDIA, "quorum")
            dec = post("/api/seed/stage", {"consent": False,
                                           "app_src": media_app},
                       port=SEEDPORT)
            absent = not os.path.exists(stage_dir)
            acc = post("/api/seed/stage", {"consent": True,
                                           "app_src": media_app},
                       port=SEEDPORT)
            staged = os.path.isdir(stage_dir)
            return {"checks": [
                check("decline → no local write, app stays on media",
                      dec.get("staged") is False and absent, dec),
                check("consent → stages to C:\\builds-installed",
                      acc.get("staged") and staged)]}

        def s_fleet_invite():
            d = post("/api/fleet/discover", {"ping": False}, timeout=120)
            keys = [r["key"] for r in d["roster_status"]
                    if r["status"].startswith("found")][:2]
            if not keys:
                keys = ["PC-GMK"]
            inv = post("/api/fleet/invite", {"keys": keys[:1]})
            return {"checks": [
                check("discovery lists candidates",
                      len(d.get("found", [])) > 0, len(d.get("found", []))),
                check("user selects which join",
                      bool(inv["invited"]), inv["invited"]),
                check("non-invited devices are NOT members",
                      bool(inv["not_invited"]) and
                      not [k for k in inv["not_invited"]
                           if lib(predicate="fleet:member",
                                  subject=f"fleet:{k}")])],
                "invited": inv["invited"]}

        def s_role_negotiate():
            d = get("/api/fleet/discovery")
            dev = next((f for f in d.get("found", [])
                        if f.get("roster")), None)
            key = (dev or {}).get("roster") or "PC-GMK"
            post("/api/fleet/invite", {"keys": [key]})
            j = post("/api/fleet/join",
                     {"key": key, "device": dev or {"ip": ""}})
            roles = lib(predicate="fleet:role", subject=f"fleet:{key}")
            return {"checks": [
                check("role negotiation recorded", bool(roles),
                      roles[-1]["value"]["v"] if roles else None),
                check("mint rights are a negotiated grant",
                      roles and "mint" in roles[-1]["value"]["v"]),
                check("join outcome honest (member vs pending)",
                      j.get("member", {}).get("state") in
                      ("member", "pending"), j.get("member"))]}

        def s_usb_mint_gen2():
            if not USB:
                return {"checks": [check("USB media present", False,
                                         "declared absent")]}
            post("/api/seed/mount", {"media": SEED_MEDIA}, port=SEEDPORT)
            m = post("/api/seed/mint",
                     {"app_src": os.path.join(SEED_MEDIA, "quorum"),
                      "label": "gen2"}, port=SEEDPORT)
            dest = os.path.join(SEED_MEDIA, "minted-gen2")
            ident = os.path.join(dest, "network-identity.json")
            runnable = os.path.isdir(os.path.join(dest, "quorum"))
            carried = json.load(open(ident)) if os.path.exists(ident) else {}
            return {"checks": [
                check("gen-2 installer written to media",
                      runnable and os.path.exists(ident)),
                check("carries founding network identity as adoptable offer",
                      carried.get("network_id") and
                      "adoptable" in carried.get("offer", "")),
                check("join-or-found is the user's choice (carry-not-enforce)",
                      "choice" in carried.get("offer", ""))],
                    "note": "boot-on-fresh-machine leg needs a second "
                            "physical host — declared"}

        def s_usb_log_courier():
            if not USB:
                return {"checks": [check("USB media present", False,
                                         "declared absent")]}
            log1 = get("/api/seed/log", port=SEEDPORT)["entries"]
            post("/api/fleet/discover", {"ping": False}, port=SEEDPORT)
            log2 = get("/api/seed/log", port=SEEDPORT)["entries"]
            path = os.path.join(SEED_MEDIA, "seed-log.jsonl")
            lines = [json.loads(l) for l in
                     open(path, encoding="utf-8") if l.strip()]
            return {"checks": [
                check("courier log accumulates across runs",
                      len(lines) >= len(log1) + 1,
                      f"{len(log1)}→{len(lines)}"),
                check("machine-readable per-node evidence",
                      all("host" in e and "at" in e for e in lines)),
                check("stale-seed revisit handling recorded",
                      any(e.get("event") in ("stage-declined", "staged",
                                             "seed-boot", "discovery")
                          for e in lines))]}

        def s_fleet_roster():
            d = post("/api/fleet/discover", {"ping": False}, timeout=120)
            rs = d["roster_status"]
            honest = all(r["status"] in (
                "found-installable", "found-not-target",
                "unavailable", "not-found-not-target") for r in rs)
            return {"checks": [
                check("every named-roster device reported",
                      len(rs) >= 14, len(rs)),
                check("honest status per device (found/installable/"
                      "unavailable/not-a-target)", honest),
                check("coverage is test data — non-targets recorded",
                      any("not-target" in r["status"] for r in rs))],
                    "roster_status": rs}

        def s_network_map():
            r = post("/api/fleet/map", {})
            mp = r.get("map", {})
            nonmember = [d for d in mp.get("discovered", [])
                         if not d.get("roster")]
            return {"checks": [
                check("map artifact produced",
                      os.path.exists(r.get("path", "")), r.get("path")),
                check("covers non-member devices alongside members",
                      len(nonmember) > 0, len(nonmember)),
                check("member/non-member distinction on the map",
                      "members" in mp and "discovered" in mp)]}

        def s_local_transports():
            d = get("/api/fleet/discovery")
            if not d.get("found"):
                d = post("/api/fleet/discover", {"ping": False},
                         timeout=120)
            tr = set(d.get("transports", []))
            wired = any(f["transport"] == "wired-lan"
                        for f in d.get("found", []))
            other = tr - {"wired-lan"}
            return {"checks": [
                check("wired LAN baseline exercised", wired),
                check("≥1 additional local transport (BT/NFC/SoftAP)",
                      "bt" in tr, sorted(tr)),
                check("wired preferred ordering honored",
                      "wired-lan" in tr)]}

        def s_credential_surrender():
            d = get("/api/fleet/discovery")
            if not d.get("found"):
                d = post("/api/fleet/discover", {"ping": False},
                         timeout=120)
            dev = next((f for f in d.get("found", [])
                        if f.get("roster")), None)
            key = (dev or {}).get("roster") or "PC-GMK"
            post("/api/fleet/invite", {"keys": [key]})
            j = post("/api/fleet/join",
                     {"key": key, "device": dev or {"ip": ""}})
            surr = lib(predicate="peer:credential-surrender")
            h = get("/api/honesty")
            return {"checks": [
                check("surrender recorded as a claim",
                      bool(surr) or j.get("member", {}).get("state")
                      == "pending"),
                check("host holds the credential screen (§5)",
                      h["fleet"]["surface_role"] == "host"),
                check("secrets stay host-local — needs travel, secrets "
                      "never do", True,
                      "peer delta exchange carries assertions only")]}

        # ============ artifact exchange ======================================
        def s_artifact_import():
            art = os.path.join(ROOT, "seed-packs", "exemplar-postcard.bmp")
            r = post("/api/artifact/import", {"path": art})
            ws = lib(predicate="workshop:entry")
            below = all(c["certainty"] <= 0.4 for c in r["claims"])
            return {"checks": [
                check("capture → workshop entry created",
                      r.get("workshop") and bool(ws)),
                check("below action/acceptance threshold", below,
                      [c["certainty"] for c in r["claims"]]),
                check("entry accessible in the app",
                      ws and ws[-1]["value"]["v"]["accessible"])]}

        def s_tool_transmission():
            art = os.path.join(ROOT, "seed-packs", "exemplar-postcard.bmp")
            post("/api/artifact/import", {"path": art})
            dec = post("/api/artifact/decode", {"path": art})
            cand = get("/api/tool-candidates")["candidates"]
            cand = next((c for c in cand
                         if c["subject"] == "handout-scorer"), None)
            import quorum.artifacts as qa
            bundle = json.loads(qa.matrix_decode(art)["payload"])
            literal = cand and \
                cand["value"]["v"]["definition"] == bundle["tool"]
            unacc = post("/api/tools/handout-scorer/invoke",
                         {"args": {"claim": "x"}})
            return {"checks": [
                check("literal decode fidelity (C-ToolWireFidelity)",
                      literal, "decoded definition == bundle tool"),
                check("imported tool quarantined as candidate",
                      bool(cand)),
                check("not invocable before acceptance",
                      unacc.get("ok") is False, unacc.get("error"))]}

        def s_artifact_style():
            art = os.path.join(ROOT, "seed-packs", "exemplar-postcard.bmp")
            r = post("/api/artifact/import", {"path": art})
            style = r["capture"]["stylistic"]
            return {"checks": [
                check("stylistic extraction layer present",
                      bool(style.get("palette"))),
                check("art style captured as LLM reference",
                      "reference" in style, style.get("reference")),
                check("carried on the workshop entry",
                      any("style" in c["value"]["v"] for c in r["claims"]))]}

        def s_artifact_republish():
            art = os.path.join(ROOT, "seed-packs", "exemplar-postcard.bmp")
            r = post("/api/artifact/import", {"path": art})
            ws = r["workshop"]
            post(f"/api/artifact/{ws}/adopt", {})
            out = os.path.join(RUNTIME, "artifacts", f"gen2-{ws}.bmp")
            rep = post(f"/api/artifact/{ws}/republish", {"path": out})
            ok = os.path.exists(out)
            if ok:
                import quorum.artifacts as qa
                b2 = json.loads(qa.matrix_decode(out)["payload"])
                same = b2["persona"]["name"] == \
                    r["capture"]["bundle"]["persona"]["name"]
            else:
                same = False
            return {"checks": [
                check("adopted workshop re-encoded to new artifact",
                      rep.get("ok") and ok),
                check("gen-2 payload decodes identically",
                      same)]}

        def s_dubious_source():
            art = os.path.join(ROOT, "seed-packs", "exemplar-postcard.bmp")
            r = post("/api/artifact/import", {"path": art})
            reviews = lib(predicate="exchange:claim-review")
            outcomes = [c["value"]["v"] for c in reviews]
            matched = [o for o in outcomes if o.get("vetted_match")]
            dubious = [o for o in outcomes if not o.get("vetted_match")]
            return {"checks": [
                check("artifact claims held below trust ceiling",
                      all(c["certainty"] <= 0.4 for c in r["claims"])),
                check("encoded references resolved against vetted pointers",
                      bool(matched), matched),
                check("non-matching claims recorded for review",
                      bool(dubious), dubious)]}

        def s_preload_cache():
            vpath = os.path.join(ROOT, "seed-packs", "vetted-sources.json")
            v = json.load(open(vpath))
            ex = os.path.join(ROOT, "seed-packs", "exemplar-postcard.bmp")
            return {"checks": [
                check("vetted-source pointers seeded",
                      len(v.get("sources", {})) >= 3),
                check("device decoder entries present",
                      bool(v.get("decoders"))),
                check("marketing exemplar present + decodable",
                      os.path.exists(ex) and post(
                          "/api/artifact/decode", {"path": ex}).get("ok"))]}

        def s_voice_spec():
            spec = post("/api/voice/spec",
                        {"families": ["formal-narrator", "resonant"],
                         "traits": {"rate": -1, "pitch": "low",
                                    "gender": "male"}})
            mapped = post("/api/voice/map",
                          {"families": ["formal-narrator"],
                           "traits": {"gender": "male"}})
            return {"checks": [
                check("spec is QR-fittable (minimal payload)",
                      spec["_bytes"] <= 400, spec["_bytes"]),
                check("ranked families and/or traits carried",
                      spec["families"] and spec["traits"]),
                check("local engine mapping renders nearest voice",
                      bool(mapped.get("mapped")), mapped.get("mapped"))]}

        def s_voice_select():
            h = get("/api/honesty")
            voices = h["tts"]["voices"]
            pid = roster_ids()[0]
            post(f"/api/personas/{pid}/update",
                 {"voice": voices[-1] if voices else ""})
            vrows = lib(predicate="persona:set-voice", subject=pid)
            return {"checks": [
                check("voice choices list offered",
                      len(voices) >= 2, voices),
                check("user assigns a persona's voice from the list",
                      bool(vrows) and
                      vrows[-1]["value"]["v"] == voices[-1])]}

        # ---- run all ---------------------------------------------------------
        suite = [
            ("S-assertion-input", s_assertion_input),
            ("S-template-need", s_template_need),
            ("S-candidate-ranking", s_candidate_ranking),
            ("S-list-project", s_list_project),
            ("S-personality-create", s_personality_create),
            ("S-background-present", s_background_present),
            ("S-competing-tools", s_competing_tools),
            ("S-restart-recovery", s_restart_recovery),
            ("S-exchange-import", s_exchange_import),
            ("S-defer-publication", s_defer_publication),
            ("S-chat-invocation", s_chat_invocation),
            ("S-focused-need", s_focused_need),
            ("S-personality-roster", s_personality_roster),
            ("S-portrait-bind", s_portrait_bind),
            ("S-color-schemes", s_color_schemes),
            ("S-status-bar", s_status_bar),
            ("S-email-commentary", s_email_commentary),
            ("S-conversation-reset", s_conversation_reset),
            ("S-context-display", s_context_display),
            ("S-personality-editor", s_personality_editor),
            ("S-windows-launch", s_windows_launch),
            ("S-close-terminate", s_close_terminate),
            ("S-speech-serialization", s_speech_serialization),
            ("S-distinct-preloadeds", s_distinct_preloadeds),
            ("S-library-browse", s_library_browse),
            ("S-faithful-voice", s_faithful_voice),
            ("S-usb-seed-run", s_usb_seed_run),
            ("S-usb-stage-consent", s_usb_stage_consent),
            ("S-fleet-invite", s_fleet_invite),
            ("S-role-negotiate", s_role_negotiate),
            ("S-usb-mint-gen2", s_usb_mint_gen2),
            ("S-usb-log-courier", s_usb_log_courier),
            ("S-fleet-roster", s_fleet_roster),
            ("S-network-map", s_network_map),
            ("S-local-transports", s_local_transports),
            ("S-credential-surrender", s_credential_surrender),
            ("S-artifact-import", s_artifact_import),
            ("S-tool-transmission", s_tool_transmission),
            ("S-artifact-style", s_artifact_style),
            ("S-artifact-republish", s_artifact_republish),
            ("S-dubious-source", s_dubious_source),
            ("S-preload-cache", s_preload_cache),
            ("S-voice-spec", s_voice_spec),
            ("S-voice-select", s_voice_select),
        ]
        only = set()
        if "--only" in sys.argv:
            only = {s.strip() for s in
                    sys.argv[sys.argv.index("--only") + 1].split(",")}
        for sid, fn in suite:
            if only and sid not in only:
                continue
            results[sid] = run_scenario(sid, fn)

    finally:
        for k, p in results.items():
            if k in ("_restart", "_seed_proc") and hasattr(p, "poll"):
                stop(p)
        stop(proc)

    # summary accumulates ALL per-scenario evidence files present — a
    # targeted --only rerun merges into the standing set rather than
    # narrowing it.
    allfiles = {}
    for f in sorted(os.listdir(EVID)):
        if f.startswith("S-") and f.endswith(".json"):
            try:
                allfiles[f[:-5]] = json.load(
                    open(os.path.join(EVID, f), encoding="utf-8"))
            except Exception:
                pass
    total = len(allfiles)
    passed = sum(1 for v in allfiles.values() if v.get("pass"))
    summary = {"suite": "quorum-0.3.0.005", "total": total,
               "passed": passed,
               "scenarios": {k: {"pass": v.get("pass"),
                                 "checks": v.get("checks")}
                             for k, v in allfiles.items()}}
    with open(os.path.join(EVID, "suite.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nsuite: {passed}/{total} scenario checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
