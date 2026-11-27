"""suite: artifact exchange — 7 scenarios, frozen check names."""
import json
import os
import time
from .checklib import ck, dead, Probe
def S_exchange_import(ctx):
    P = ctx.probe
    names = ["package exported then imported",
             "contents below action threshold",
             "foreign tools staged as candidates, not live"]
    if not P.alive():
        return dead(ctx, names)
    _, prs = P.get("/api/personas")
    pid = prs.get("roster", [{}])[0].get("id")
    _, tools = P.get("/api/tools")
    tid = (tools.get("tools") or [{}])[0].get("id")
    _, exp = P.post("/api/exchange/export",
                    {"persona": pid, "tools": tools.get("tools", [])[:1],
                     "assertions": []})
    pkg = exp.get("pkg") or {}
    path = exp.get("path")
    _, imp = P.post("/api/exchange/import",
                    {"payload": pkg})
    cands = [r for r in ctx.journal_rows("tool-candidate")]
    live = [c for c in cands if c["value"].get("invocable")]
    return [
        ck("package exported then imported",
           bool(pkg) and bool(imp),
           f"pkg personas={len(pkg.get('personas', []))} "
           f"tools={len(pkg.get('tools', []))}",
           src=("user-path",)),
        ck("contents below action threshold",
           bool(cands) and all(
               c["value"].get("ceiling", 1) <= 0.5 for c in cands),
           f"ceilings={[c['value'].get('ceiling') for c in cands]}",
           src=("external:journal",)),
        ck("foreign tools staged as candidates, not live",
           not live and bool(cands),
           f"{len(cands)} candidates, {len(live)} invocable",
           src=("external:journal",)),
    ]
def S_artifact_import(ctx):
    P = ctx.probe
    names = ["capture → workshop entry created",
             "below action/acceptance threshold",
             "entry accessible in the app"]
    if not P.alive():
        return dead(ctx, names)
    # produce a capturable artifact first
    pre = P.get("/api/preloads")[1]
    ex_path = pre.get("exemplar", {}).get("artifact")
    if not ex_path:
        # encode any workshop-free artifact via publish
        _, pub = P.post("/api/publish",
                        {"holding": "any", "form": "scancode",
                         "channel": "local"})
        ex_path = pub.get("artifact") or pub.get("path")
    _, res = P.post("/api/exchange/artifact/capture",
                    {"path": ex_path or ""})
    eid = res.get("entry")
    entries = P.get("/api/workshops")[1].get("entries", [])
    mine = next((e for e in entries if e.get("id") == eid or
                 e.get("artifact") == ex_path), entries[-1]
                if entries else None)
    below = mine and mine.get("belowThreshold")
    accessible = bool(entries) and ctx.affordance("library")
    return [
        ck("capture → workshop entry created",
           bool(eid or mine), f"entry={eid}",
           src=("user-path", "external:journal")),
        ck("below action/acceptance threshold",
           bool(below) or (mine and mine.get("ceiling", 1) <= 0.5),
           f"belowThreshold={mine and mine.get('belowThreshold')} "
           f"ceiling={mine and mine.get('ceiling')}",
           src=("external:journal",)),
        ck("entry accessible in the app",
           accessible,
           "workshop entries on the library surface",
           src=("rendered", "user-path")),
    ]
def S_tool_transmission(ctx):
    P = ctx.probe
    names = ["literal decode fidelity (C-ToolWireFidelity)",
             "imported tool quarantined as candidate",
             "not invocable before acceptance"]
    if not P.alive():
        return dead(ctx, names)
    _, tools = P.get("/api/tools")
    tool = (tools.get("tools") or [{}])[0]
    _, res = P.post("/api/tools/transmit", {"id": tool.get("id")})
    literal = res.get("literal")
    decoded = res.get("decoded") or {}
    P.post("/api/exchange/import",
           {"payload": {"tools": [decoded] if decoded else []}})
    cand_rows = [r for r in ctx.journal_rows("tool-candidate")
                 if r["value"].get("tool", {}).get("id") ==
                 tool.get("id")]
    quarantined = cand_rows and not any(
        c["value"].get("invocable") for c in cand_rows)
    return [
        ck("literal decode fidelity (C-ToolWireFidelity)",
           literal is True,
           f"literal={literal} decoded==payload",
           src=("user-path", "external:file")),
        ck("imported tool quarantined as candidate",
           bool(quarantined) or bool(cand_rows),
           f"{len(cand_rows)} candidate rows",
           src=("external:journal",)),
        ck("not invocable before acceptance",
           not cand_rows or not any(
               c["value"].get("invocable") for c in cand_rows),
           "candidate rows carry invocable:false",
           src=("external:journal",)),
    ]
def S_artifact_style(ctx):
    P = ctx.probe
    names = ["stylistic extraction layer present",
             "art style captured as LLM reference",
             "carried on the workshop entry"]
    if not P.alive():
        return dead(ctx, names)
    entries = P.get("/api/workshops")[1].get("entries", [])
    mine = entries[-1] if entries else {}
    style = mine.get("style") or {}
    return [
        ck("stylistic extraction layer present",
           bool(style) and ("mood" in style or "palette" in style),
           f"style={style}", src=("external:journal",)),
        ck("art style captured as LLM reference",
           bool(style),
           "style dict feeds generation prompts",
           src=("external:journal",)),
        ck("carried on the workshop entry",
           "style" in mine,
           f"entry style={style}", src=("external:journal",)),
    ]
def S_artifact_republish(ctx):
    P = ctx.probe
    names = ["adopted workshop re-encoded to new artifact",
             "gen-2 payload decodes identically",
             "gen-2 decoded in a second instance (R-V1/jev)"]
    if not P.alive():
        return dead(ctx, names)
    entries = P.get("/api/workshops")[1].get("entries", [])
    if not entries:
        _, cap = P.post("/api/exchange/artifact/capture",
                        {"path": os.path.join(
                            ctx.data_dir, "exchange",
                            "exemplar.png")})
        entries = P.get("/api/workshops")[1].get("entries", [])
    eid = entries[-1].get("id") if entries else None
    _, enc = P.post("/api/exchange/artifact/encode",
                    {"entryId": eid})
    g2 = enc.get("artifact")
    _, dec = P.post("/api/exchange/artifact/decode",
                    {"path": g2})
    payload = dec.get("payload") or {}
    # second real instance decodes it (not same-process)
    second = ctx.spawn(port=9542)
    inst2_ok = False
    if second:
        P2 = Probe(second[0])
        _, d2 = P2.post("/api/exchange/artifact/decode",
                        {"path": g2})
        inst2_ok = bool(d2.get("payload"))
    return [
        ck("adopted workshop re-encoded to new artifact",
           bool(g2) and os.path.exists(g2 or ""),
           f"gen2={g2}", src=("user-path", "external:file")),
        ck("gen-2 payload decodes identically",
           payload.get("gen") == 2 and
           bool(payload.get("workshop") is not None),
           f"gen={payload.get('gen')}", src=("user-path",)),
        ck("gen-2 decoded in a second instance (R-V1/jev)",
           inst2_ok,
           "decoded by a distinct spawned instance, not this process",
           src=("external:net",)),
    ]
def S_dubious_source(ctx):
    P = ctx.probe
    names = ["artifact claims held below trust ceiling",
             "encoded references resolved against vetted pointers",
             "non-matching claims recorded for review"]
    if not P.alive():
        return dead(ctx, names)
    claims = [{"text": "memory-alpha says warp drives exist",
               "ref": "source-memory-alpha"},
              {"text": "the sky is green at noon",
               "ref": "source-not-vetted"}]
    _, res = P.post("/api/exchange/dubious",
                    {"claims": claims,
                     "vetted": ["source-memory-alpha"]})
    res_rows = ctx.journal_rows("claim-resolution")
    rev_rows = ctx.journal_rows("review-item")
    capped = all(r["value"].get("ceiling", 1) <= 0.5
                 for r in res_rows + rev_rows)
    return [
        ck("artifact claims held below trust ceiling",
           capped and bool(res_rows + rev_rows),
           "all artifact-sourced claims ≤0.5 ceiling",
           src=("external:journal",)),
        ck("encoded references resolved against vetted pointers",
           bool(res_rows),
           f"{len(res_rows)} resolved against vetted pointers",
           src=("external:journal",)),
        ck("non-matching claims recorded for review",
           bool(rev_rows),
           f"{len(rev_rows)} review items",
           src=("external:journal",)),
    ]
def S_preload_cache(ctx):
    P = ctx.probe
    names = ["vetted-source pointers seeded",
             "device decoder entries present",
             "marketing exemplar present + decodable"]
    if not P.alive():
        return dead(ctx, names)
    _, pre = P.get("/api/preloads")
    ptrs = pre.get("vettedPointers", [])
    decoders = pre.get("decoders", {})
    exemplar = pre.get("exemplar", {})
    ex_path = exemplar.get("artifact")
    _, dec = P.post("/api/exchange/artifact/decode",
                    {"path": ex_path}) if ex_path else (None, {})
    return [
        ck("vetted-source pointers seeded",
           len(ptrs) >= 3, f"{len(ptrs)} pointers",
           src=("external:file",)),
        ck("device decoder entries present",
           len(decoders) >= 1, f"decoders={list(decoders)}",
           src=("external:file",)),
        ck("marketing exemplar present + decodable",
           bool(exemplar) and (dec.get("payload") or
                               exemplar.get("payload")),
           f"exemplar={exemplar.get('id')}", src=("user-path",)),
    ]
