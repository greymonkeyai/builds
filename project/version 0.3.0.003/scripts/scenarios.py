"""Scenario suite enactment (JEV): drives the full .devin/scenarios.md suite
(24 scenarios) against a live server and writes evidence/scenarios/<id>.json
transcripts.

Each scenario runs through the real machinery — HTTP surface, needs, grants,
competitions, connectors, the speech floor — so the transcript is
enactment-class evidence. Rectified this cycle:
- exchange-import leg reads the package path at the correct nesting (H1)
- connectors verification artifact is written (H2)
- autonomous steward evidence captured before any manual wake (H4)
- temporal classification must place far-future events in `future`,
  never `recent` (H5)
- focused-need and chat-invocation legs go deeper (H6/H7)

Usage: python scripts/scenarios.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 9763
BASE = f"http://127.0.0.1:{PORT}"
EVID = os.path.join(ROOT, "evidence", "scenarios")
RUNTIME = os.path.join(ROOT, "runtime", "scenario")


def get(path, timeout=10):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return json.loads(r.read().decode())


def post(path, body=None, timeout=300):
    data = json.dumps(body or {}).encode()
    req = urllib.request.Request(BASE + path, data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def lib(predicate=None, subject=None, limit=100):
    q = []
    if predicate:
        q.append(f"predicate={predicate}")
    if subject:
        q.append(f"subject={subject}")
    q.append(f"limit={limit}")
    return get("/api/library?" + "&".join(q)).get("rows", [])


def run_scenario(sid, fn):
    out = {"id": sid, "ran": False}
    try:
        out.update(fn())
        out["ran"] = True
    except Exception as e:
        out["error"] = repr(e)
    return out


def wait_floor(max_s=90):
    t0 = time.time()
    while time.time() - t0 < max_s:
        s = get("/api/speech-floor")
        if not s["depth"]:
            return s
        time.sleep(0.5)
    return get("/api/speech-floor")


def wait_server(deadline_s=90):
    for _ in range(int(deadline_s * 2)):
        try:
            return get("/api/honesty", timeout=2)
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("server did not come up")


def boot(runtime, port):
    return subprocess.Popen(
        [sys.executable, "-m", "app", "--port", str(port),
         "--runtime", runtime, "--no-watchdog"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def stop(proc):
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except Exception:
            proc.kill()


def main():
    os.makedirs(EVID, exist_ok=True)
    import shutil
    shutil.rmtree(RUNTIME, ignore_errors=True)  # fresh seeding per enactment
    os.makedirs(RUNTIME, exist_ok=True)
    proc = boot(RUNTIME, PORT)
    results = {}
    try:
        honesty = wait_server()
        gate = get("/api/gate")
        state0 = get("/api/state")
        results["_gate"] = {"ran": True, "informational": True,
                            "gate": gate, "honesty": honesty["engines"]}

        # ==============================================================
        # S-assertion-input
        # ==============================================================
        def s_assert():
            post("/api/library/assert", {
                "subject": "scenario-check", "predicate": "product:goal",
                "value": "enactment probe assertion", "certainty": 0.9})
            rows = lib(predicate="product:goal", subject="scenario-check")
            return {"asserted": bool(rows), "rows": len(rows),
                    "claimant": rows[-1]["claimant"] if rows else None}
        results["S-assertion-input"] = run_scenario("S-assertion-input", s_assert)

        # ==============================================================
        # S-personality-create (canonical)
        # ==============================================================
        def s_persona():
            mint = post("/api/personas", {
                "name": "Wendell", "traits": ["precise", "wry"],
                "interests": ["maps", "etymology"],
                "lens": {"register": "wry", "style": "wry"}})
            pid = (mint.get("result") or mint).get("personaId")
            ob = post("/api/tools/persona-onboard/invoke",
                      {"input": {"personaId": pid}})
            wait_floor(60)
            st = get("/api/state")
            me = [p for p in st["roster"] if p["id"] == pid][0]
            rows = lib(subject=f"persona:{pid}", limit=40)
            art = me.get("art") or {}
            return {"personaId": pid,
                    "onboardOk": bool((ob.get("result") or {}).get("ok", ob.get("ok"))),
                    "art": {"bound": bool(art),
                            "artifact": art.get("artifact"),
                            "artifactExists": bool(art.get("artifact")) and
                                os.path.exists(art["artifact"]),
                            "portrait": (art.get("motif"), bool(
                                (art.get("dataUrl") or "")))},
                    "voice": me.get("voice"),
                    "characterized": any(
                        r["predicate"] == "persona:characterization"
                        for r in rows),
                    "predicates": sorted({r["predicate"] for r in rows}),
                    "rosterEntry": {"name": me["name"], "traits": me["traits"],
                                    "color": me["color"]}}
        results["S-personality-create"] = run_scenario(
            "S-personality-create", s_persona)

        post("/api/personas", {"name": "Marlowe",
                               "traits": ["expansive", "kind"],
                               "interests": ["maps", "history"],
                               "lens": {"register": "warm", "style": "warm"}})
        post("/api/config", {"predicate": "chat:response-depth", "value": 2})

        # ==============================================================
        # S-chat-invocation (deepened: conversation + tool needs together,
        # each need distinguishable)
        # ==============================================================
        def s_chat():
            r = post("/api/chat", {"text":
                "set the topic to harbor tides, and tell me what you think "
                "about tidal atlases"})
            floor = wait_floor(90)
            st = get("/api/state")
            chat = [c for c in st["chat"] if c["role"] == "persona"][-3:]
            seq = lib(predicate="decision:respondent", limit=6)
            need_rows = lib(predicate="need:open", limit=20)
            snap_rows = lib(predicate="inference:snapshot", limit=4)
            commit_rows = lib(predicate="inference:commit", limit=8)
            res = r.get("result") or r
            return {"turn": {"ok": res.get("ok"),
                             "needIds": res.get("needIds"),
                             "responseNeedId": res.get("responseNeedId"),
                             "intents": res.get("intents")},
                    "toolNeedsOpened": len(res.get("needIds") or []),
                    "recentPersonaReplies": len(chat),
                    "respondentRows": seq,
                    "inferenceSnapshot": snap_rows[-1]["value"]["v"]
                        if snap_rows else None,
                    "inferenceCommits": [c["value"]["v"] for c in commit_rows],
                    "floorPlayed": len(floor["played"]),
                    "chatTail": chat[-2:] if chat else []}
        results["S-chat-invocation"] = run_scenario("S-chat-invocation", s_chat)

        # ==============================================================
        # S-template-need
        # ==============================================================
        def s_tneed():
            r = post("/api/invoke", {"toolId": "set-topic",
                                     "slots": {"topic": "tidal atlases"},
                                     "summary": "set topic for test"})
            fulfilled = lib(predicate="need:fulfilled", limit=6)
            return {"invoke": r, "topic": get("/api/state").get("topic"),
                    "fulfilledRows": len(fulfilled)}
        results["S-template-need"] = run_scenario("S-template-need", s_tneed)

        # ==============================================================
        # S-candidate-ranking
        # ==============================================================
        def s_crank():
            st = get("/api/state")
            need = next((n for n in st["needs"]
                         if n["kind"] == "generic"), None)
            if not need:
                post("/api/invoke", {"toolId": "create-project",
                                     "slots": {"title": "atlas study",
                                               "goals": ["survey atlases"]}})
                st = get("/api/state")
                need = st["needs"][-1]
            nid = need["id"]
            post(f"/api/needs/{nid}/candidate", {"slot": "format",
                 "value": "hardcover", "confidence": 0.9, "source": "user"})
            post(f"/api/needs/{nid}/candidate", {"slot": "format",
                 "value": "pdf", "confidence": 0.4, "source": "guess"})
            post(f"/api/needs/{nid}/candidate", {"slot": "format",
                 "value": "vhs tape", "confidence": 0.15,
                 "source": "bad-idea"})
            rows = lib(subject=f"need:{nid}", predicate="need:candidate")
            cands = get("/api/candidates?subject=need:" + nid +
                        "&predicate=need:candidate")
            return {"needId": nid,
                    "candidates": [r["value"]["v"] for r in rows],
                    "ranked": cands}
        results["S-candidate-ranking"] = run_scenario(
            "S-candidate-ranking", s_crank)

        # ==============================================================
        # S-competing-tools
        # ==============================================================
        def s_comp():
            r = post("/api/compare",
                     {"need": "speech.render",
                      "input": {"text": "competition check"}})
            rows = lib(predicate="comparison:run")
            return {"competition": r.get("result") or r,
                    "recorded": len(rows)}
        results["S-competing-tools"] = run_scenario(
            "S-competing-tools", s_comp)
        wait_floor(90)

        # ==============================================================
        # S-list-project (canonical PA cities)
        # ==============================================================
        def s_list():
            r = post("/api/invoke", {
                "toolId": "build-list",
                "slots": {"criteria": "all the cities in Pennsylvania"},
                "summary": "canonical PA cities"})
            res = r.get("result") or {}
            closure = lib(predicate="set:closure")
            nonm = [x for x in lib(predicate="need:candidate")
                    if (x["value"]["v"] or {}).get("class")]
            return {"result": r, "memberCount": res.get("memberCount"),
                    "artifact": res.get("artifact"),
                    "artifactExists": bool(res.get("artifact")) and
                        os.path.exists(res["artifact"]),
                    "agreement": res.get("agreement"),
                    "closure": closure[-1]["value"]["v"] if closure else None,
                    "nonMatches": len(nonm),
                    "nonMatchSample": [x["value"]["v"] for x in nonm[:6]]}
        results["S-list-project"] = run_scenario("S-list-project", s_list)

        # ==============================================================
        # S-background-present (H4: autonomous steward evidence first)
        # ==============================================================
        def s_bg():
            # autonomous runs accumulate on the interval (started at launch);
            # record them BEFORE any manual wake so autonomy is visible
            auto_before = lib(predicate="idle:steward-run", limit=10)
            r = post("/api/steward/wake", {})
            runs = lib(predicate="idle:steward-run", limit=10)
            att = lib(predicate="temporal:attention", limit=5)
            return {"wake": r,
                    "autonomousRunsBeforeWake": len(auto_before),
                    "autonomousReasons": [
                        x["value"]["v"].get("reason") for x in auto_before],
                    "stewardRuns": len(runs),
                    "temporalAttention": att}
        results["S-background-present"] = run_scenario(
            "S-background-present", s_bg)

        # calendar feed: one near-future event (in horizon) and one far-future
        # (2030 — must NOT classify as 'recent', H5)
        import datetime as _dt
        fut = _dt.datetime.now() + _dt.timedelta(hours=30)
        ics = "\n".join([
            "BEGIN:VCALENDAR",
            "BEGIN:VEVENT", "SUMMARY:atlas study check-in",
            f"DTSTART:{fut.strftime('%Y%m%dT%H%M%S')}",
            f"DTEND:{(fut + _dt.timedelta(hours=1)).strftime('%Y%m%dT%H%M%S')}",
            "END:VEVENT",
            "BEGIN:VEVENT", "SUMMARY:persona sync (far future fixture)",
            "DTSTART:20300101T150000", "END:VEVENT",
            "BEGIN:VEVENT", "SUMMARY:old survey (long past fixture)",
            "DTSTART:20200101T150000", "DTEND:20200101T160000",
            "END:VEVENT",
            "END:VCALENDAR"])
        post("/api/calendar/import", {"ics": ics, "source": "scenario-ics"})
        post("/api/steward/wake", {})
        tctx = get("/api/temporal")

        # ==============================================================
        # S-defer-publication
        # ==============================================================
        def s_defer():
            r1 = post("/api/invoke", {"toolId": "publish-milestone",
                                      "slots": {"target": "cycle-log",
                                                "content": "scenario evidence"}})
            gid = post("/api/grants", {"scope": "publish.creator"})
            r2 = post("/api/invoke", {"toolId": "publish-milestone",
                                      "slots": {"target": "cycle-log",
                                                "content": "scenario evidence v2"}})
            rows = lib(predicate="need:deferred")
            return {"noGrant": r1, "withGrant": r2,
                    "deferredRows": len(rows),
                    "grantId": gid.get("grantId")}
        results["S-defer-publication"] = run_scenario(
            "S-defer-publication", s_defer)

        # ==============================================================
        # S-focused-need (deepened: focus -> conversational fill -> fulfill)
        # ==============================================================
        def s_focus():
            # open a need missing its required slot -> deferred
            r = post("/api/invoke", {"toolId": "set-response-depth",
                                     "slots": {}})
            nid = r.get("needId")
            if not nid:
                return {"error": "no need opened", "invoke": r}
            st1 = get("/api/state")
            open1 = [n for n in st1["needs"] if n["id"] == nid]
            # move it into focus
            foc = post(f"/api/needs/{nid}/focus", {})
            # conversational slot fill: a chat turn supplies the value
            turn = post("/api/chat", {"text": "3"})
            wait_floor(60)
            st2 = get("/api/state")
            open2 = [n for n in st2["needs"] if n["id"] == nid]
            filled = lib(subject=f"need:{nid}", predicate="need:candidate")
            closed = lib(subject=f"need:{nid}", limit=20)
            t2 = (turn.get("result") or {})
            return {"needId": nid,
                    "deferredBefore": open1[0].get("status") if open1 else None,
                    "focus": foc.get("result") or foc,
                    "turn": {"ok": t2.get("ok"),
                             "focusFill": t2.get("focusFill")},
                    "candidatesAdded": [c["value"]["v"] for c in filled],
                    "statusAfter": open2[0].get("status") if open2 else
                                   "closed-or-absent",
                    "needRows": [(x["predicate"], x["value"]["v"])
                                 for x in closed],
                    "responseDepthNow": st2.get("responseDepth")}
        results["S-focused-need"] = run_scenario("S-focused-need", s_focus)
        # restore depth
        post("/api/config", {"predicate": "chat:response-depth", "value": 2})

        # ==============================================================
        # S-exchange-import (H1: correct path nesting)
        # ==============================================================
        def s_exch():
            ex = post("/api/exchange/export", {"predicate": "product:goal"})
            exres = ex.get("result") or {}
            path = exres.get("path")          # result.path — the .002 bug was
            if not path:                       # ex.get("path") -> package:None
                return {"error": "export produced no path", "export": ex}
            im = post("/api/exchange/import", {"package": path})
            imres = im.get("result") or {}
            rows = lib(predicate="exchange:imported")
            below = all(x["certainty"] <= 0.4 for x in
                        lib(subject="exchange", predicate="exchange:imported")
                        ) if rows else False
            return {"export": {"path": path, "counts": exres.get("counts")},
                    "import": {"ok": imres.get("ok"),
                               "package": imres.get("package"),
                               "counts": imres.get("counts"),
                               "threshold": imres.get("threshold")},
                    "importRows": len(rows),
                    "belowActionThreshold": below}
        results["S-exchange-import"] = run_scenario(
            "S-exchange-import", s_exch)

        # ==============================================================
        # S-personality-roster
        # ==============================================================
        def s_roster():
            st = get("/api/state")
            import urllib.request as _u
            html = _u.urlopen(BASE + "/", timeout=5).read().decode()
            return {"rosterCount": len(st["roster"]),
                    "names": [p["name"] for p in st["roster"]],
                    "withArt": sum(1 for p in st["roster"] if p.get("art")),
                    "persistentPanel": ('id="rail"' in html and
                                        'id="roster"' in html),
                    "registers": [(p["name"], (p.get("lens") or {}).get(
                        "register")) for p in st["roster"]]}
        results["S-personality-roster"] = run_scenario(
            "S-personality-roster", s_roster)

        # ==============================================================
        # S-portrait-bind
        # ==============================================================
        def s_portrait():
            st = get("/api/state")
            arts = {p["name"]: (p.get("art") or {}) for p in st["roster"]}
            svgs = {n: a.get("dataUrl") for n, a in arts.items() if a}
            distinct = len(set(svgs.values())) == len(svgs)
            files_ok = all(
                not a.get("artifact") or os.path.exists(a["artifact"])
                for a in arts.values() if a)
            recs = lib(predicate="persona:art", limit=10)
            return {"personas": len(arts), "bound": len(svgs),
                    "allDistinct": distinct, "artifactsOnDisk": files_ok,
                    "artAssertions": len(recs),
                    "portraitEngines": sorted({
                        (r["value"]["v"] or {}).get("engine", "?")
                        for r in recs}),
                    "samplePortraitParams": (recs[-1]["value"]["v"].get(
                        "portrait") if recs else None)}
        results["S-portrait-bind"] = run_scenario(
            "S-portrait-bind", s_portrait)

        # ==============================================================
        # S-color-schemes
        # ==============================================================
        def s_themes():
            out = {"cycles": []}
            for t in ("dark", "sepia", "slate", "light"):
                post("/api/config",
                     {"predicate": "ui:shell-theme", "value": t})
                st = get("/api/state")
                out["cycles"].append({"set": t, "stateTheme": st["theme"]})
            css = open(os.path.join(ROOT, "app", "ui", "styles.css"),
                       encoding="utf-8").read()
            out["themesInCss"] = [t for t in ("light", "dark", "sepia", "slate")
                                  if f'data-theme="{t}"' in css]
            out["defaultLight"] = ':root, body[data-theme="light"]' in css
            out["finalTheme"] = get("/api/state")["theme"]
            return out
        results["S-color-schemes"] = run_scenario("S-color-schemes", s_themes)

        # ==============================================================
        # S-status-bar
        # ==============================================================
        def s_status():
            st = get("/api/state")
            import urllib.request as _u
            html = _u.urlopen(BASE + "/", timeout=5).read().decode()
            return {"statusbarElement": 'id="statusbar"' in html,
                    "sourcesConfigured": st["connectors"]["configured"],
                    "sourcesAvailable": st["connectors"]["available"],
                    "llmMode": st["honesty"]["engines"]["llm"]["mode"],
                    "llmModel": st["honesty"]["engines"]["llm"].get("model"),
                    "ttsLocal": st["honesty"]["engines"]["tts"]["local"],
                    "gate": st["gate"],
                    "fields": ["version", "gate", "llm", "sources",
                               "speechFloor", "needs"]}
        results["S-status-bar"] = run_scenario("S-status-bar", s_status)

        # ==============================================================
        # S-email-commentary
        # ==============================================================
        def s_email():
            mails = get("/api/emails?limit=10")["emails"]
            if not mails:
                return {"error": "inbox empty — connector did not run"}
            pick = mails[0]
            r = post("/api/context/select",
                     {"kind": "email", "itemId": pick["id"]})
            res = r.get("result") or r
            ctxrows = lib(predicate="chat:context", limit=4)
            return {"emailCount": len(mails),
                    "subjects": [m["subject"] for m in mails],
                    "selected": pick["subject"],
                    "context": res.get("context"),
                    "commentary": res.get("commentary"),
                    "contextRows": [c["value"]["v"].get("label")
                                    for c in ctxrows]}
        results["S-email-commentary"] = run_scenario(
            "S-email-commentary", s_email)

        # ==============================================================
        # S-conversation-reset
        # ==============================================================
        def s_reset():
            before = len(get("/api/state")["chat"])
            r = post("/api/chat/reset", {})
            res = r.get("result") or r
            after = get("/api/state")
            cleared = lib(predicate="chat:cleared", limit=5)
            return {"messagesBefore": before,
                    "reset": res,
                    "messagesAfter": len(after["chat"]),
                    "topicAfter": after["topic"],
                    "contextAfter": after["context"],
                    "clearedRows": [c["value"]["v"] for c in cleared]}
        results["S-conversation-reset"] = run_scenario(
            "S-conversation-reset", s_reset)

        # ==============================================================
        # S-context-display
        # ==============================================================
        def s_ctx():
            st = get("/api/state")
            prof = st["roster"][0]
            r1 = post("/api/context/select",
                      {"kind": "profile", "itemId": prof["id"]})
            st1 = get("/api/state")
            mails = get("/api/emails?limit=2")["emails"]
            r2 = post("/api/context/select",
                      {"kind": "email",
                       "itemId": mails[-1]["id"]}) if mails else {}
            st2 = get("/api/state")
            ctxrows = lib(predicate="chat:context", limit=6)
            return {"profileSelect": (r1.get("result") or r1).get("context"),
                    "contextShownProfile": (st1["context"] or {}).get("label"),
                    "emailSelect": (r2.get("result") or r2).get("context")
                        if r2 else None,
                    "contextShownEmail": (st2["context"] or {}).get("label"),
                    "commentaryPresent": bool(
                        (r2.get("result") or r2).get("commentary"))
                        if r2 else None,
                    "contextRows": [c["value"]["v"].get("label")
                                    for c in ctxrows]}
        results["S-context-display"] = run_scenario(
            "S-context-display", s_ctx)

        # ==============================================================
        # S-personality-editor
        # ==============================================================
        def s_editor():
            st = get("/api/state")
            p = next(x for x in st["roster"] if x["name"] == "Wendell")
            r = post("/api/personas/update", {
                "personaId": p["id"],
                "traits": ["precise", "wry", "patient"],
                "lens": {"register": "scholarly", "style": "scholarly",
                         "responsibilities": ["maps", "citations"]},
                "voice": {"name": "Microsoft Zira Desktop", "rate": -2},
                "color": "#7a3b8c",
                "rosterPriority": 0.7,
                "displayMode": "respondent"})
            res = r.get("result") or r
            st2 = get("/api/state")
            me = [x for x in st2["roster"] if x["id"] == p["id"]][0]
            lensrows = lib(subject=f"persona:{p['id']}",
                           predicate="persona:lens")
            return {"update": res.get("ok"),
                    "applied": {"traits": me["traits"],
                                "register": (me.get("lens") or {}).get(
                                    "register"),
                                "voice": me.get("voice"),
                                "color": me.get("color"),
                                "priority": me.get("rosterPriority")},
                    "lensAssertions": len(lensrows),
                    "editableElements": ["name", "traits", "interests",
                                         "lens", "voice", "color",
                                         "rosterPriority", "displayMode"]}
        results["S-personality-editor"] = run_scenario(
            "S-personality-editor", s_editor)

        # ==============================================================
        # S-speech-serialization
        # ==============================================================
        def s_speech():
            st = get("/api/state")
            ids = [p["id"] for p in st["roster"]][:3]
            before = len(get("/api/speech-floor")["played"])
            # enqueue three speaks back-to-back through persona.speak
            for i, pid in enumerate(ids):
                post("/api/tools/persona.speak/invoke", {"input": {
                    "personaId": pid,
                    "text": f"serialization probe {i+1} of {len(ids)}.",
                    "cause": "serialization-check"}})
            floor = wait_floor(120)
            played = floor["played"][before:]
            return {"enqueued": len(ids),
                    "played": [{"persona": p["personaName"],
                                "ok": p["ok"],
                                "ms": p.get("ms"),
                                "playbackMs": p.get("playbackMs"),
                                "heldUntilPlaybackComplete":
                                    p.get("heldUntilPlaybackComplete")}
                               for p in played],
                    "count": len(played),
                    "queueDepthDuring": floor["depth"]}
        results["S-speech-serialization"] = run_scenario(
            "S-speech-serialization", s_speech)

        # ==============================================================
        # S-distinct-preloadeds
        # ==============================================================
        def s_distinct():
            st = get("/api/state")
            preloaded = [p for p in st["roster"]
                         if p["name"] in ("Curator", "Herald", "Wickett")]
            prompt = "what should we do about the harbor survey results?"
            replies = {}
            for p in preloaded:
                r = post("/api/invoke",
                         {"toolId": "compose-response",
                          "slots": {"personaId": p["id"], "text": prompt}})
                res = r.get("result") or {}
                replies[p["name"]] = {"register": res.get("register"),
                                      "engine": res.get("engine"),
                                      "stub": res.get("stub"),
                                      "text": res.get("text")}
            texts = [v["text"] for v in replies.values()]
            distinct = len(set(texts)) == len(texts)
            sims = []
            for i, a in enumerate(texts):
                for b in texts[i + 1:]:
                    wa, wb = set(a.lower().split()), set(b.lower().split())
                    jac = (len(wa & wb) / len(wa | wb)) if (wa | wb) else 0
                    sims.append(round(jac, 3))
            return {"prompt": prompt, "replies": replies,
                    "allTextuallyDistinct": distinct,
                    "maxJaccard": max(sims) if sims else None}
        results["S-distinct-preloadeds"] = run_scenario(
            "S-distinct-preloadeds", s_distinct)

        # ==============================================================
        # S-windows-launch + S-close-terminate (enacted by
        # scripts/launch-check.py; transcript references that evidence)
        # ==============================================================
        lc_path = os.path.join(ROOT, "evidence", "launch",
                               "launch-check.json")
        results["S-windows-launch"] = run_scenario(
            "S-windows-launch",
            lambda: {"seeEvidence": "evidence/launch/launch-check.json",
                     "launcherExists": os.path.exists(
                         os.path.join(ROOT, "launch.cmd")),
                     "checkFile": json.load(open(lc_path))
                        if os.path.exists(lc_path) else "NOT RUN YET"})
        results["S-close-terminate"] = run_scenario(
            "S-close-terminate",
            lambda: {"seeEvidence": "evidence/launch/launch-check.json",
                     "checkFile": (json.load(open(lc_path)).get(
                         "closeTerminates") if os.path.exists(lc_path)
                         else "NOT RUN YET")})

        # ==============================================================
        # ethics gate (F1 parity) + connectors (F8, verify artifact H2)
        # ==============================================================
        def s_ethics():
            r1 = post("/api/personas", {
                "name": "Barry", "imitates": {"name": "Barack Obama",
                                              "recency": "living"}})
            marked = [p for p in get("/api/state")["roster"]
                      if p.get("name") == "Barry"]
            post("/api/library/assert", {
                "subject": "worldview", "predicate": "maxim:objection",
                "value": {"pattern": "Active Refusal Test",
                          "note": "test objection"}, "certainty": 1.0})
            r2 = post("/api/personas", {
                "name": "RefuseMe",
                "imitates": {"name": "Active Refusal Test",
                             "recency": "living"}})
            gates = lib(predicate="ethics:gate")
            st = get("/api/state")
            return {"imitationMint": r1,
                    "mark": marked[0].get("mark") if marked else None,
                    "admonitions": st["admonitions"],
                    "refusalMint": r2,
                    "gateRows": [g["value"]["v"]["verdict"] for g in gates]}
        results["ethics-gate-F1"] = run_scenario("ethics-gate-F1", s_ethics)

        def s_conn():
            out = {}
            post("/api/connectors/configure",
                 {"connector": "wikipedia", "locator": "Atlas"})
            out["wiki"] = post("/api/connectors/run",
                               {"connector": "wikipedia",
                                "input": {"mode": "summary",
                                          "locator": "Atlas (mythology)"}})
            ics_path = os.path.join(RUNTIME, "scenario.ics")
            with open(ics_path, "w") as f:
                f.write(ics)
            post("/api/connectors/configure",
                 {"connector": "ics-calendar", "locator": ics_path})
            out["ics"] = post("/api/connectors/run",
                              {"connector": "ics-calendar"})
            doc_dir = os.path.join(RUNTIME, "docs")
            os.makedirs(doc_dir, exist_ok=True)
            with open(os.path.join(doc_dir, "note.txt"), "w") as f:
                f.write("scenario connector ingest check\n")
            post("/api/connectors/configure",
                 {"connector": "files", "locator": doc_dir})
            out["files"] = post("/api/connectors/run",
                                {"connector": "files"})
            out["inbox"] = post("/api/connectors/run",
                                {"connector": "inbox-local"})
            out["status"] = get("/api/connectors")
            runs = lib(predicate="connector:run")
            out["runRows"] = len(runs)
            # H2: the verify artifact exists on disk this cycle
            verify = {"connectorRuns": len(runs),
                      "configured": out["status"],
                      "results": {k: v for k, v in out.items()
                                  if k != "status"},
                      "allOk": all((out[k].get("result") or out[k]).get("ok")
                                   for k in ("wiki", "ics", "files", "inbox")
                                   if isinstance(out.get(k), dict)),
                      "verifiedAt": time.time()}
            with open(os.path.join(ROOT, "evidence",
                                   "connectors-F8-verify.json"),
                      "w", encoding="utf-8") as f:
                json.dump(verify, f, indent=2, ensure_ascii=False)
            return out
        results["connectors-F8"] = run_scenario("connectors-F8", s_conn)

        def s_arch():
            post("/api/library/assert", {
                "subject": "chat", "predicate": "chat:topic",
                "value": "new topic for segment boundary", "certainty": 1.0})
            r = post("/api/archive/seal", {"reason": "scenario seal"})
            v = get("/api/archive")
            return {"seal": r, "segments": v.get("segmentCount"),
                    "turns": v.get("turnCount")}
        results["archive-C-ConversationArchive"] = run_scenario(
            "archive-C-ConversationArchive", s_arch)

        # temporal classification check (H5): 2030 -> future, 2020 ->
        # historical, near-future -> upcoming; none may be 'recent'
        results["_temporal"] = {
            "ran": True, "informational": True,
            "context": tctx,
            "check": {
                "farFutureInRecent": any(
                    "persona sync" in (e.get("title") or "")
                    for e in tctx.get("recent", [])),
                "farFutureClass": next(
                    (k for k in ("current", "upcoming", "future", "recent",
                                 "historical")
                     if any("persona sync" in (e.get("title") or "")
                            for e in tctx.get(k, []))), None),
                "longPastClass": next(
                    (k for k in ("current", "upcoming", "future", "recent",
                                 "historical")
                     if any("old survey" in (e.get("title") or "")
                            for e in tctx.get(k, []))), None)}}

        # ==============================================================
        # S-restart-recovery (last — bounces the process)
        # ==============================================================
        def s_restart():
            before = get("/api/state")["honesty"]["ledger"]["total"]
            stop(proc)
            proc2 = boot(RUNTIME, PORT)
            try:
                h = wait_server()
                after = h["ledger"]["total"]
                st = get("/api/state")
                return {"before": before, "after": after,
                        "recovered": after >= before,
                        "partitionMounted": h["ledger"].get(
                            "partitionMounted"),
                        "roster": len(st["roster"]),
                        "personasWithArt": sum(
                            1 for p in st["roster"]
                            if (p.get("art") or {}).get("artifact")),
                        "gate": get("/api/gate")}
            finally:
                stop(proc2)
        results["S-restart-recovery"] = run_scenario(
            "S-restart-recovery", s_restart)

    finally:
        stop(proc)

    summary = {"suite": list(results), "at": time.time(),
               "evidence": EVID, "runtime": RUNTIME}
    with open(os.path.join(EVID, "suite.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    for sid, res in results.items():
        with open(os.path.join(EVID, f"{sid}.json"), "w",
                  encoding="utf-8") as f:
            json.dump(res, f, indent=2, ensure_ascii=False)
    print(json.dumps({k: ("OK" if v.get("ran") else
                          "FAIL:" + str(v.get("error"))[:200])
                      for k, v in results.items()}, indent=2))


if __name__ == "__main__":
    main()
