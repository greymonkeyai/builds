"""Scenario suite enactment (JEV): drives the full .devin/scenarios.md suite
against a live server and writes evidence/scenarios/<id>.json transcripts.

Each scenario runs through the real machinery — HTTP surface, needs, grants,
competitions, connectors — so the transcript is enactment-class evidence.

Usage: python scripts/scenarios.py [--keep]
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


def post(path, body=None, timeout=120):
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


def wait_floor(max_s=60):
    t0 = time.time()
    while time.time() - t0 < max_s:
        s = get("/api/speech-floor")
        if not s["depth"]:
            return s
        time.sleep(0.5)
    return get("/api/speech-floor")


def main():
    os.makedirs(EVID, exist_ok=True)
    os.makedirs(RUNTIME, exist_ok=True)
    proc = subprocess.Popen(
        [sys.executable, "-m", "app", "--port", str(PORT),
         "--runtime", RUNTIME],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    results = {}
    try:
        for _ in range(90):
            try:
                get("/api/honesty", timeout=2)
                break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError("server did not come up")

        # ---------- S-assertion-input ----------
        def s_assert():
            post("/api/library/assert", {
                "subject": "scenario-check", "predicate": "product:goal",
                "value": "enactment probe assertion", "certainty": 0.9})
            rows = lib(predicate="product:goal", subject="scenario-check")
            return {"asserted": bool(rows), "rows": len(rows)}
        results["S-assertion-input"] = run_scenario("S-assertion-input", s_assert)

        # ---------- S-personality-create (canonical, minimal input) ----------
        def s_persona():
            mint = post("/api/personas", {
                "name": "Wendell", "traits": ["precise", "wry"],
                "interests": ["maps", "etymology"],
                "lens": {"style": "wry"}})
            pid = (mint.get("result") or mint).get("personaId")
            ob = post("/api/tools/persona-onboard/invoke",
                      {"input": {"personaId": pid}})
            st = get("/api/state")
            me = [p for p in st["roster"] if p["id"] == pid][0]
            rows = lib(subject=f"persona:{pid}", limit=30)
            return {"personaId": pid, "onboard": ob,
                    "art": bool(me.get("art")), "voice": me.get("voice"),
                    "characterized": any(
                        r["predicate"] == "persona:characterization"
                        for r in rows),
                    "roster": me}
        results["S-personality-create"] = run_scenario(
            "S-personality-create", s_persona)

        # second persona for sequential respondents
        post("/api/personas", {"name": "Marlowe",
                               "traits": ["expansive"],
                               "interests": ["maps", "history"],
                               "lens": {"style": "warm"}})
        post("/api/config", {"predicate": "chat:response-depth", "value": 2})

        # ---------- S-chat-invocation + sequential respondents ----------
        def s_chat():
            r = post("/api/chat", {"text":
                                   "what is the difference between a map and "
                                   "an atlas"})
            floor = wait_floor(90)
            st = get("/api/state")
            chat = [c for c in st["chat"] if c["role"] == "persona"][-3:]
            seq = lib(predicate="decision:respondent", limit=5)
            return {"turn": r, "recentPersonaReplies": len(chat),
                    "respondentRows": seq, "floorPlayed": len(floor["played"]),
                    "chatTail": chat[-2:] if chat else []}
        results["S-chat-invocation"] = run_scenario("S-chat-invocation", s_chat)

        # ---------- S-template-need ----------
        def s_tneed():
            r = post("/api/invoke", {"toolId": "set-topic",
                                     "slots": {"topic": "atlases"},
                                     "summary": "set topic for test"})
            return {"invoke": r, "topic": get("/api/state").get("topic")}
        results["S-template-need"] = run_scenario("S-template-need", s_tneed)

        # ---------- S-candidate-ranking ----------
        def s_crank():
            st = get("/api/state")
            need = next((n for n in st["needs"]
                         if n["kind"] == "generic"), None)
            if not need:
                # create a project goal need to rank candidates on
                r = post("/api/invoke", {"toolId": "create-project",
                                         "slots": {"title": "atlas study",
                                                   "goals": ["survey atlases"]}})
                st = get("/api/state")
                need = st["needs"][-1]
            nid = need["id"]
            post(f"/api/needs/{nid}/candidate", {"slot": "format",
                 "value": "hardcover", "confidence": 0.9, "source": "user"})
            post(f"/api/needs/{nid}/candidate", {"slot": "format",
                 "value": "pdf", "confidence": 0.4, "source": "guess"})
            st2 = get("/api/state")
            rows = lib(subject=f"need:{nid}", predicate="need:candidate")
            return {"needId": nid, "candidates": [
                r["value"]["v"] for r in rows]}
        results["S-candidate-ranking"] = run_scenario(
            "S-candidate-ranking", s_crank)

        # ---------- S-competing-tools (general machinery) ----------
        def s_comp():
            r = post("/api/compare",
                     {"need": "speech.render",
                      "input": {"text": "competition check"}})
            rows = lib(predicate="comparison:run")
            return {"competition": r, "recorded": len(rows)}
        results["S-competing-tools"] = run_scenario(
            "S-competing-tools", s_comp)
        wait_floor(90)

        # ---------- S-list-project (canonical PA cities — live retrieval) ----
        def s_list():
            r = post("/api/invoke", {
                "toolId": "build-list",
                "slots": {"criteria": "all the cities in Pennsylvania"},
                "summary": "canonical PA cities"})
            rows = lib(predicate="comparison:row")
            closure = lib(predicate="set:closure")
            nonm = [x for x in lib(predicate="need:candidate")
                    if x["value"]["v"].get("class")]
            return {"result": r,
                    "memberCount": (r.get("result") or {}).get("memberCount"),
                    "artifact": (r.get("result") or {}).get("artifact"),
                    "agreement": (r.get("result") or {}).get("agreement"),
                    "competitionRows": len(rows),
                    "closure": closure[-1]["value"]["v"] if closure else None,
                    "nonMatches": len(nonm),
                    "nonMatchSample": [x["value"]["v"] for x in nonm[:5]]}
        results["S-list-project"] = run_scenario("S-list-project", s_list)

        # ---------- S-background-present ----------
        def s_bg():
            r = post("/api/steward/wake", {})
            runs = lib(predicate="idle:steward-run", limit=5)
            att = lib(predicate="temporal:attention", limit=5)
            return {"wake": r, "stewardRuns": len(runs),
                    "temporalAttention": att}
        results["S-background-present"] = run_scenario(
            "S-background-present", s_bg)

        # ---------- calendar feed for F2 evidence ----------
        ics = "\n".join([
            "BEGIN:VCALENDAR",
            "BEGIN:VEVENT", "SUMMARY:atlas study check-in",
            "DTSTART:20990101T1500", "DTEND:20990101T1600", "END:VEVENT",
            "BEGIN:VEVENT", "SUMMARY:persona sync",
            "DTSTART:20300101T1500", "END:VEVENT",
            "END:VCALENDAR"])
        # use a near-future event so it lands in the horizon
        import datetime as _dt
        fut = _dt.datetime.now() + _dt.timedelta(hours=30)
        ics = ics.replace("20990101T1500",
                          fut.strftime("%Y%m%dT%H%M")).replace(
            "20990101T1600", (fut + _dt.timedelta(hours=1)).strftime("%Y%m%dT%H%M"))
        post("/api/calendar/import", {"ics": ics, "source": "scenario-ics"})
        post("/api/steward/wake", {})
        tctx = get("/api/temporal")

        # ---------- S-defer-publication (grant gate) ----------
        def s_defer():
            r1 = post("/api/invoke", {"toolId": "publish-milestone",
                                      "slots": {"target": "cycle-log",
                                                "content": "scenario evidence"}})
            gid = post("/api/grants", {"scope": "publish.creator"})
            # re-invoke with grant recorded — the need was deferred; open anew
            r2 = post("/api/invoke", {"toolId": "publish-milestone",
                                      "slots": {"target": "cycle-log",
                                                "content": "scenario evidence v2"}})
            rows = lib(predicate="need:deferred")
            return {"noGrant": r1, "withGrant": r2,
                    "deferredRows": len(rows),
                    "grantId": gid.get("grantId")}
        results["S-defer-publication"] = run_scenario(
            "S-defer-publication", s_defer)

        # ---------- S-focused-need (refinement preserves criteria) ----------
        def s_focus():
            st = get("/api/state")
            need = st["needs"][-1] if st["needs"] else None
            if not need:
                return {"skipped": "no open need"}
            nid = need["id"]
            post("/api/library/assert", {
                "subject": f"need:{nid}", "predicate": "need:refined",
                "value": {"note": "focus: pennsylvania municipalities only"},
                "certainty": 1.0})
            rows = lib(subject=f"need:{nid}", predicate="need:refined")
            return {"needId": nid, "refinements": [
                r["value"]["v"] for r in rows]}
        results["S-focused-need"] = run_scenario("S-focused-need", s_focus)

        # ---------- S-exchange-import ----------
        def s_exch():
            ex = post("/api/exchange/export", {"predicate": "product:goal"})
            im = post("/api/exchange/import", {"package": ex.get("path")})
            rows = lib(predicate="exchange:imported")
            return {"export": ex, "import": im, "importRows": len(rows)}
        results["S-exchange-import"] = run_scenario(
            "S-exchange-import", s_exch)

        # ---------- ethics gate (F1) ----------
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
                "imitates": {"name": "Active Refusal Test", "recency": "living"}})
            gates = lib(predicate="ethics:gate")
            st = get("/api/state")
            return {"imitationMint": r1,
                    "mark": marked[0].get("mark") if marked else None,
                    "admonitions": st["admonitions"],
                    "refusalMint": r2,
                    "gateRows": [g["value"]["v"]["verdict"] for g in gates]}
        results["ethics-gate-F1"] = run_scenario("ethics-gate-F1", s_ethics)

        # ---------- connectors (F8) ----------
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
            out["status"] = get("/api/connectors")
            runs = lib(predicate="connector:run")
            out["runRows"] = len(runs)
            return out
        results["connectors-F8"] = run_scenario("connectors-F8", s_conn)

        # ---------- archive ----------
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

        results["_temporal"] = {"context": tctx}

        # ---------- S-restart-recovery ----------
        def s_restart():
            before = get("/api/state")["honesty"]["ledger"]["total"]
            proc.terminate()
            try:
                proc.wait(timeout=15)
            except Exception:
                proc.kill()
            proc2 = subprocess.Popen(
                [sys.executable, "-m", "app", "--port", str(PORT),
                 "--runtime", RUNTIME], cwd=ROOT,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            try:
                for _ in range(90):
                    try:
                        h = get("/api/honesty", timeout=2)
                        break
                    except Exception:
                        time.sleep(0.5)
                after = h["ledger"]["total"]
                st = get("/api/state")
                return {"before": before, "after": after,
                        "recovered": after >= before,
                        "roster": len(st["roster"]),
                        "personasWithArt": sum(
                            1 for p in st["roster"]
                            if (p.get("art") or {}).get("artifact"))}
            finally:
                proc2.terminate()
                try:
                    proc2.wait(timeout=15)
                except Exception:
                    proc2.kill()
        results["S-restart-recovery"] = run_scenario(
            "S-restart-recovery", s_restart)

    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=15)
            except Exception:
                proc.kill()

    summary = {"suite": list(results), "at": time.time(),
               "evidence": EVID, "runtime": RUNTIME}
    with open(os.path.join(EVID, "suite.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    for sid, res in results.items():
        with open(os.path.join(EVID, f"{sid}.json"), "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2, ensure_ascii=False)
    print(json.dumps({k: ("OK" if v.get("ran") else "FAIL:" + str(v.get("error")))
                      for k, v in results.items()}, indent=2))


if __name__ == "__main__":
    main()
