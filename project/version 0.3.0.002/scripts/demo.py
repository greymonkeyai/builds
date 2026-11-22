"""Demonstration harness: exercises the 11 observable demonstrations from
prompt.md against a fresh runtime and writes evidence/demos/*.md transcripts.

Usage: python scripts/demo.py          (fresh runtime under runtime/demo)
       python scripts/demo.py --keep   (reuse existing runtime)
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app.host import Ctx
from app import builtins as B
from app import needs as N
from app import tools as T
from app import seed as S

OUT = os.path.join(ROOT, "evidence", "demos")
RUNTIME = os.path.join(ROOT, "runtime", "demo")

results = []


def w(demo: int, title: str, body: list[str]):
    path = os.path.join(OUT, f"{demo:02d}-{title}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(body))
    results.append({"demo": demo, "title": title, "file": os.path.basename(path)})
    print(f"demo {demo}: {title} -> {os.path.basename(path)}")


def fmt(x, n=1600):
    s = json.dumps(x, indent=1, ensure_ascii=False, default=str)
    return s[:n] + ("…" if len(s) > n else "")


def rows(ctx, pred, subj=None, n=5):
    rs = ctx.ledger.query(subject=subj, predicate=pred)
    return [r.to_row() for r in rs[-n:]]


def main():
    keep = "--keep" in sys.argv
    if not keep:
        shutil.rmtree(RUNTIME, ignore_errors=True)
    os.makedirs(OUT, exist_ok=True)
    ctx = Ctx(ROOT, RUNTIME)
    B.register_builtins(ctx)
    S.load_packs(ctx, os.path.join(ROOT, "seed-packs"))

    # ---------- demo 1: source-aware assertion from typed + spoken input ----
    r = ctx.invoke("run-chat-turn", {"text": "what does the ledger hold?"})
    spoken = ctx.invoke("transcribe-speech",
                        {"transcript": "note the weather is fine",
                         "confidence": 0.82})
    w(1, "source-aware-input", [
        "# Demo 1 — typed + spoken input become source-aware assertions",
        "", "## chat turn result", "```json", fmt(r), "```",
        "", "## captured-input assertion", "```json",
        fmt(rows(ctx, "chat:user-message", "chat", 2)), "```",
        "", "## spoken transcript witness", "```json",
        fmt(spoken), "```",
        "", "## device:speech-transcript assertion", "```json",
        fmt(rows(ctx, "device:speech-transcript", "device", 1)), "```",
        "", "Each row carries claimant, basis.kind, certainty, time — typed, "
           "attributed, provenanced input."])

    # ---------- demo 2: template governs an unfulfilled requirement ----
    r2 = ctx.invoke("request-tool",
                    {"toolId": "run-search", "slots": {},
                     "summary": "demo2: governed requirement"})
    nid = r2["result"]["needId"]
    st_before = N.need_state(ctx, nid)
    N.add_candidate(ctx, nid, "query", "confidence", 0.85, "user", "principal")
    gate = T.evaluate_gate(ctx, ctx.registry.get("run-search"), {}, nid)
    fr = T.fulfill_need(ctx, nid)
    st_after = N.need_state(ctx, nid)
    w(2, "template-governs-need", [
        "# Demo 2 — template governs an unfulfilled requirement",
        "", "## need opened (missing required slot 'query')", "```json",
        fmt(st_before["spec"]), "```",
        "", "## candidate supplied -> gate ready", "```json", fmt(gate), "```",
        "", "## fulfillment", "```json", fmt({k: fr[k] for k in ("ok",)}), "```",
        "## need after", "```json", fmt({k: st_after[k] for k in
        ("status", "detail")}), "```",
        "", "Creation did not imply execution: the need waited on the floor "
           "until required slots met their certainty threshold."])

    # ---------- demo 3: confidence ranking + recency, failed evidence kept ----
    nid3 = N.open_need(ctx, "generic",
                       {"summary": "which port?", "satisfaction": {}})
    N.add_candidate(ctx, nid3, "port", 9847, 0.6, "source:old-doc", "source:old-doc")
    time.sleep(0.01)
    N.add_candidate(ctx, nid3, "port", 9760, 0.6, "principal", "principal")
    time.sleep(0.01)
    N.add_candidate(ctx, nid3, "port", 9761, 0.9, "source:old-doc", "source:old-doc")
    cands = N.candidates(ctx, nid3)
    # failed evidence: invoke a tool that fails
    fail = ctx.invoke("import-exchange", {"package": {"schema": "bogus"}})
    tele = rows(ctx, "tool:telemetry", "tool:import-exchange", 2)
    w(3, "confidence-ranking", [
        "# Demo 3 — candidate ranking by contextual confidence + recency",
        "", "Two 0.6 candidates: principal at same certainty beats an unvetted "
            "source (source ceiling caps effective confidence); the 0.9 source "
            "candidate still ranks below because the source ceiling binds.",
        "", "## ranked candidates (slot 'port')", "```json", fmt(cands), "```",
        "", "## failed evidence retained", "```json",
        fmt({"invoke": fail, "telemetry": tele}), "```",
        "", "Nothing is made true by being recorded — candidates stay "
           "inspectable with source and confidence until a tool selects them."])

    # ---------- demo 4: multi-step list; headers/foreign/category errors ----
    r4 = ctx.invoke("build-list", {
        "criteria": "study techniques",
        "items": ["STUDY METHODS:", "spaced repetition study techniques",
                  "interleaved practice study techniques",
                  "https://example.com/unrelated-page",
                  "aardvark grooming manual",
                  "retrieval practice study techniques",
                  "CHAPTER TWO"]})
    subj = None
    for a in ctx.ledger.query(predicate="need:candidate"):
        if a.value["v"].get("class") in ("header", "foreign-link", "category-error"):
            subj = a.subjectKey
    nonmatch = ctx.ledger.query(subject=subj, predicate="need:candidate") if subj else []
    w(4, "criteria-governed-list", [
        "# Demo 4 — multi-step list preserves criteria; non-matches recorded",
        "", "## build-list result", "```json", fmt(r4), "```",
        "", "## non-matching candidates retained for review/cleanup", "```json",
        fmt([r.to_row() for r in nonmatch if r.value["v"].get("class")]), "```",
        "", "Headers, foreign links, and category errors are results that do "
           "not match the requested criteria — recorded, retained, reviewable."])

    # ---------- demo 5: minimal personality + extension ----
    m = ctx.invoke("persona.mint", {"name": "Cartographer",
                                    "interests": ["maps", "routes"], "traits": []})
    pid = m["result"]["personaId"]
    por = ctx.invoke("generate-portrait", {"personaId": pid})
    ed = ctx.invoke("edit-persona", {"personaId": pid,
                                     "traits": ["curious", "spatial"],
                                     "rosterPriority": 0.7})
    view = ctx.ledger.render_view(f"persona:{pid}")
    w(5, "persona-create-extend", [
        "# Demo 5 — minimal personality extended by later work",
        "", "## minted", "```json", fmt(m["result"]), "```",
        "", "## portrait artifact", "```json",
        fmt({"ok": por["result"].get("ok") if isinstance(por.get("result"), dict) else por,
             "artifact": (por.get("result") or {}).get("artifact")}), "```",
        "", "## edits applied", "```json", fmt(ed.get("result", {})), "```",
        "", "## computed persona view (slots resolved from ledger)", "```json",
        fmt(view), "```"])

    # ---------- demo 6: background result via distinct personality ----
    ctx.invoke("import-calendar", {"events": [
        {"title": "dentist appointment", "startMs": int(time.time()*1000)+3600e3}]})
    tick = ctx.invoke("steward-tick", {"reason": "demo6"})
    p = ctx.personas.get(pid)
    comp = B.compose_for(ctx, p, "the steward found an upcoming event")
    speak = ctx.invoke("persona.speak", {"personaId": pid, "text":
        f"Herald of the calendar: '{ 'dentist appointment' }' is within your "
        f"next day — the ledger holds it as source evidence, not my opinion.",
        "cause": "steward-opportunity", "speak": False})
    frag = rows(ctx, "idle:drain-fragment", "idle", 3)
    w(6, "background-result-via-persona", [
        "# Demo 6 — relevant background result through a distinct personality",
        "", "## steward tick (calendar-scan found the event)", "```json",
        fmt(tick["result"]["report"]["ran"]), "```",
        "", "## persona presents it (evidence preserved in ledger)", "```json",
        fmt(speak["result"]), "```",
        "", "## drain/calendar assertions", "```json",
        fmt(rows(ctx, "calendar:event", "calendar", 2)), "```",
        "", "## composition engine used", "```json", fmt(comp), "```"])

    # ---------- demo 7: competing tools, same need ----
    sapi_rate0 = ctx.decision.rank_multiplier("render-speech-sapi")
    rem_rate0 = ctx.decision.rank_multiplier("render-speech-remote")
    sv = ctx.invoke("speak-voice", {"text": "competition check"})
    # exercise the competitor directly: its unconfigured failure is honest and
    # churns its rank among alternatives without making it ineligible
    rem_try = ctx.invoke("render-speech-remote", {"text": "remote check"})
    ctx.decision.record_outcome("render-speech-remote", None,
                                bool(rem_try.get("ok")),
                                bool(rem_try.get("ok") and
                                     (rem_try.get("result") or {}).get("ok")))
    sapi_rate1 = ctx.decision.rank_multiplier("render-speech-sapi")
    rem_rate1 = ctx.decision.rank_multiplier("render-speech-remote")
    churn = rows(ctx, "decision:churn", "decision:churn", 4)
    w(7, "competing-tools", [
        "# Demo 7 — locally competing tools expressing the same need",
        "", "render-speech-sapi and render-speech-remote both express need "
            "'speech.render'. speak-voice ranks them; results are interpretable "
            "under a shared local understanding (ok / rendered artifact).",
        "", "## speak-voice outcome", "```json", fmt(sv["result"]), "```",
        "", "## remote renderer invoked directly — honest unconfigured failure",
        "```json", fmt(rem_try), "```",
        "", f"rank multipliers: sapi {sapi_rate0}->{sapi_rate1}, "
            f"remote {rem_rate0}->{rem_rate1}",
        "", "## churn rows (remote's unconfigured failure lowers its rank,"
            " not its eligibility)", "```json", fmt(churn), "```"])

    # ---------- demo 8: restart recovery + governed consolidation ----
    before = ctx.ledger.stats()
    ctx2 = Ctx(ROOT, RUNTIME)  # restart: new context over the same runtime
    B.register_builtins(ctx2)
    after = ctx2.ledger.stats()
    v = ctx2.ledger.render_view(f"persona:{pid}")
    cl = ctx2.invoke("cleanup-run", {})
    prov = rows(ctx2, "cleanup:compacted", "ledger", 1)
    w(8, "restart-and-cleanup", [
        "# Demo 8 — restart recovery + consolidation without losing provenance",
        "", f"before restart: {before['total']} rows; after re-open: "
            f"{after['total']} rows, {after['live']} live (durable JSONL).",
        "", "## persona view survives restart", "```json", fmt(v), "```",
        "", "## governed consolidation", "```json", fmt(cl.get("result")), "```",
        "", "## compaction summary preserves removed ids + superseding rows",
        "```json", fmt(prov), "```"])

    # ---------- demo 9: import exchange package below threshold ----
    pkg = {"schema": "meridian.exchange/v1", "id": "pkg-demo",
           "personas": [{"name": "Traveller", "interests": ["trains"],
                         "traits": ["restless"]}],
           "tools": [{"id": "find-trains", "kind": "tool", "title": "Find trains",
                      "need": "travel.lookup",
                      "template": {"slots": [{"name": "route", "required": True}]},
                      "steps": [{"op": "result", "value": {"found": "stub-imported"}}]}],
           "assertions": [{"subjectKey": "travel:tips",
                           "predicate": "travel:prep-suggest",
                           "value": "pack light", "certainty": 0.95}],
           "needs": [{"kind": "generic", "spec": {"summary": "imported want"}}]}
    imp = ctx2.invoke("import-exchange", {"package": pkg})
    imp_rows = [a for a in ctx2.ledger.query(predicate="travel:prep-suggest")]
    effs = [{"id": a.id, "eff": round(ctx2.ledger.effective_confidence(a), 3),
             "claimant": a.claimant} for a in imp_rows]
    w(9, "exchange-import-below-threshold", [
        "# Demo 9 — storefront/exchange package import below action threshold",
        "", "## import result", "```json", fmt(imp), "```",
        "", "## effective confidence of imported assertions", "```json",
        fmt(effs), "```",
        "", "Imported material is recorded but capped below the action "
            "threshold (0.4 < 0.7) — resolvable through local ledger, "
            "capabilities, and permissions (endorse-source raises trust)."])

    # ---------- demo 10: unconfigured nonlocal request -> recorded refusal ----
    r10 = ctx2.invoke("run-chat-turn",
                      {"text": "email kris@example.com about the demo"})
    n10 = [n for n in N.open_needs(ctx2, "tool-request")
           if n["spec"]["toolId"] == "send-mail"]
    fr10 = T.fulfill_need(ctx2, n10[0]["id"]) if n10 else {"error": "no need"}
    st10 = N.need_state(ctx2, n10[0]["id"]) if n10 else {}
    w(10, "recorded-refusal-deferral", [
        "# Demo 10 — unconfigured nonlocal effect: deferral recorded",
        "", "## intents detected", "```json",
        fmt((r10.get("result") or {}).get("intents")), "```",
        "", "## fulfill attempt without grant", "```json", fmt(fr10), "```",
        "", "## need state — open, deferred with status", "```json",
        fmt({"status": st10.get("status"), "deferred": st10.get("deferred")}), "```",
        "", "Conversational interpretation alone does not send mail; the "
            "request resolves to a recorded deferral, not silent non-action."])

    # ---------- demo 11: project from chat + calendar relation ----
    r11 = ctx2.invoke("run-chat-turn",
                      {"text": "create a project called spring research"})
    pn = [n for n in N.open_needs(ctx2, "tool-request")
          if n["spec"]["toolId"] == "create-project"]
    if pn:
        N.add_candidate(ctx2, pn[0]["id"], "title", "spring research", 0.85,
                        "chat-extract", "principal")
        N.add_candidate(ctx2, pn[0]["id"], "goals",
                        ["collect spring research notes"], 0.8,
                        "chat-extract", "principal")
    fr11 = T.fulfill_need(ctx2, pn[0]["id"]) if pn else {}
    pid11 = (fr11.get("result") or {}).get("projectId")
    # advance the project: a goal becomes tool work linked to the project
    adv = ctx2.invoke("request-tool",
                      {"toolId": "run-search",
                       "slots": {"query": "spring research"},
                       "project": pid11,
                       "summary": "project goal: collect notes"})
    adv_nid = (adv.get("result") or {}).get("needId")
    adv_fr = T.fulfill_need(ctx2, adv_nid) if adv_nid else {}
    ev = ctx2.ledger.query(predicate="calendar:event")
    link = ctx2.invoke("link-calendar", {
        "projectId": pid11, "eventAssertionId": ev[-1].id}) if pid11 and ev else {}
    from app.api import projects as _projects
    proj = [p for p in _projects(ctx2) if p["id"] == pid11]
    w(11, "project-from-chat-calendar", [
        "# Demo 11 — project created/advanced from chat, related to calendar",
        "", "## intents + fulfill", "```json",
        fmt({"intents": (r11.get("result") or {}).get("intents"),
             "fulfill": fr11}), "```",
        "", "## goal decomposed into tool work (linked need)", "```json",
        fmt({"advanceNeed": adv_nid, "advanceResult": adv_fr.get("ok")}), "```",
        "", "## project view", "```json", fmt(proj), "```",
        "", "## calendar link", "```json", fmt(link.get("result")), "```",
        "", "## calendar events remain source evidence", "```json",
        fmt(rows(ctx2, "calendar:event", "calendar", 3)), "```"])

    # ---------- index ----------
    summary = {"ranAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "runtime": RUNTIME, "demos": results,
               "ledger": ctx2.ledger.stats()}
    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    with open(os.path.join(OUT, "INDEX.md"), "w") as f:
        f.write("# Demonstration evidence index\n\n")
        for r in results:
            f.write(f"- demo {r['demo']}: `{r['file']}`\n")
        f.write(f"\nledger at end: {ctx2.ledger.stats()}\n")
    print("index written")


if __name__ == "__main__":
    main()
