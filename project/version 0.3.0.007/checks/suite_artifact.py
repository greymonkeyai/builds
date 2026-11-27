"""Checks — artifact exchange facet. Frozen names verbatim."""

import json
import os
import time

from .checklib import ck


def _encode_persona(ctx):
    p = ctx.probe
    lib = p.get("/api/library")[1].get("holdings", {})
    holding = (lib.get("personas") or [{}])[0].get("id")
    return p.post("/api/exchange/encode", {"holding": holding})[1]


def S_exchange_import(ctx):
    p = ctx.probe
    # encode a tool/composition holding → foreign tools arrive staged
    _, enc = p.post("/api/exchange/encode-tool",
                    {"composition": _first_composition(p)})
    path = enc.get("file")
    _, dec = p.post("/api/exchange/decode", {"file": path})
    pkg = dec.get("package") or {}
    n = dec.get("importedAssertions", 0)
    cand_rows = [r for r in p.rows("exchange:imported")
                 if r.get("quarantined")]
    return [
        ck("package exported then imported",
           bool(path) and os.path.exists(path or "") and bool(pkg),
           f"file={path} importedAssertions={n}"),
        ck("contents below action threshold",
           (dec.get("certainty") or 1) < (dec.get("threshold") or 0.5),
           f"certainty={dec.get('certainty')} threshold={dec.get('threshold')}"),
        ck("foreign tools staged as candidates, not live",
           bool(cand_rows) and all(r.get("certainty", 1) <= 0.25
                                   for r in cand_rows),
           f"{len(cand_rows)} quarantined import rows at ≤0.25"),
    ]


def _first_composition(p):
    comps = p.get("/api/library")[1].get("holdings", {}).get("compositions", [])
    return comps[0]["id"] if comps else None


def S_artifact_import(ctx):
    p = ctx.probe
    enc = _encode_persona(ctx)
    _, dec = p.post("/api/exchange/decode", {"file": enc.get("file")})
    ws = dec.get("workshop")
    entry_rows = p.rows("workshop:minted")
    holdings = p.get("/api/library")[1].get("holdings", {})
    return [
        ck("capture → workshop entry created",
           bool(ws) or bool(entry_rows),
           f"workshop={ws} rows={len(entry_rows)}"),
        ck("below action/acceptance threshold",
           (dec.get("certainty") or 1) < (dec.get("threshold") or 0.5),
           f"{dec.get('certainty')} < {dec.get('threshold')}"),
        ck("entry accessible in the app",
           bool(entry_rows) or bool(holdings.get("workshops")),
           f"{len(entry_rows)} workshop rows, "
           f"{len(holdings.get('workshops') or [])} in library"),
    ]


def S_tool_transmission(ctx):
    p = ctx.probe
    _, comp = p.post("/api/tools/compose",
                     {"name": "transmit-check",
                      "steps": [{"tool": "ledger.echo", "args": {"text": "wire"}}],
                      "by": "manual"})
    cid = comp.get("composition")
    _, enc = p.post("/api/exchange/encode-tool", {"composition": cid})
    _, dec = p.post("/api/exchange/decode", {"file": enc.get("file")})
    pkg = dec.get("package") or {}
    re_steps = (pkg.get("steps")
                or ((pkg.get("tools") or [{}])[0].get("steps") or []))
    fidelity = bool(re_steps) and re_steps[0].get("tool") == "ledger.echo"
    cand = [r for r in p.rows("exchange:imported")
            if r.get("tool") and r.get("quarantined")]
    _, iv = p.post("/api/tools/invoke",
                   {"tool": "transmit-check", "args": {"text": "x"}})
    not_invocable = not iv.get("ok")
    return [
        ck("literal decode fidelity (C-ToolWireFidelity)",
           fidelity, f"re-steps={re_steps}"),
        ck("imported tool quarantined as candidate", bool(cand),
           f"{len(cand)} candidate tool entries"),
        ck("not invocable before acceptance",
           bool(cand) and not_invocable,
           f"invoke ok={iv.get('ok')} err={iv.get('error')}"),
    ]


def S_artifact_style(ctx):
    p = ctx.probe
    enc = _encode_persona(ctx)
    _, dec = p.post("/api/exchange/decode", {"file": enc.get("file")})
    pkg = dec.get("package") or {}
    style = pkg.get("style")
    ws_rows = [w for w in p.rows("workshop:minted") if w.get("style")]
    return [
        ck("stylistic extraction layer present",
           style is not None, f"style={style}"),
        ck("art style captured as LLM reference",
           bool(style) and (style.get("reference") or style.get("mood")
                            or style.get("palette")),
           str(style)[:120]),
        ck("carried on the workshop entry",
           bool(ws_rows) or bool(style),
           f"{len(ws_rows)} workshop rows carrying style"),
    ]


def S_artifact_republish(ctx):
    p = ctx.probe
    enc = _encode_persona(ctx)
    _, dec = p.post("/api/exchange/decode", {"file": enc.get("file")})
    ws = dec.get("workshop")
    _, enc2 = p.post("/api/exchange/republish", {"workshop": ws})
    _, dec2 = p.post("/api/exchange/decode", {"file": enc2.get("file")})
    pkg1 = dec.get("package") or {}
    pkg2 = dec2.get("package") or {}
    same_persona = (pkg1.get("persona") or {}).get("name") == \
        (pkg2.get("persona") or {}).get("name") and pkg2.get("persona")
    return [
        ck("adopted workshop re-encoded to new artifact",
           bool(enc2.get("file")) and os.path.exists(enc2.get("file") or ""),
           f"gen-2 file={enc2.get('file')} holding={pkg2.get('holding')}"),
        ck("gen-2 payload decodes identically",
           pkg2.get("holding") == ws and same_persona,
           f"gen2 holding={pkg2.get('holding')} persona={bool(same_persona)}"),
    ]


def S_dubious_source(ctx):
    p = ctx.probe
    enc = _encode_persona(ctx)
    _, dec = p.post("/api/exchange/decode", {"file": enc.get("file")})
    imported = p.rows("exchange:imported")
    below = all(r.get("certainty", 1) <= 0.25 for r in imported) if imported else False
    review = p.rows("claim:review")
    vetted = p.rows("cache:preload") or p.rows("exchange:vetted")
    return [
        ck("artifact claims held below trust ceiling",
           bool(imported) and below,
           f"{len(imported)} imported rows ≤0.25 certainty"),
        ck("encoded references resolved against vetted pointers",
           bool(vetted) or dec.get("referencesResolved") is not None,
           f"{len(vetted)} vetted-pointer rows; resolved={dec.get('referencesResolved')}"),
        ck("non-matching claims recorded for review",
           bool(review) or dec.get("reviewed") is not None,
           f"{len(review)} claim:review rows"),
    ]


def S_preload_cache(ctx):
    p = ctx.probe
    preloads = p.get("/api/preloads")[1].get("preloads", [])
    kinds = {x.get("kind") for x in preloads}
    has_source = "vetted-source" in kinds
    has_decoder = "decoder" in kinds
    exemplar = [x for x in preloads if x.get("kind") == "exemplar"]
    return [
        ck("vetted-source pointers seeded", has_source,
           f"kinds={sorted(kinds)}"),
        ck("device decoder entries present", has_decoder,
           f"{len(preloads)} preloads"),
        ck("marketing exemplar present + decodable",
           bool(exemplar),
           f"{len(exemplar)} exemplars: {[e.get('name') for e in exemplar]}"),
    ]
