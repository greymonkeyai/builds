"""Competing-tool lifecycle (prompt §Tools and local comparison — F3).

General comparison machinery over genuinely competing tools: every registered
tool that expresses the same `need:` is an eligible competitor. A competition
invokes each runnable competitor on the same input, normalizes the results
under a shared local understanding, records each row and the ranking, and
feeds outcomes back into the trust-churn loop — so a tool that keeps failing
sinks among alternatives without ever becoming ineligible.

"Runnable" is honest: an unconfigured competitor runs and reports its real
status (unconfigured/error); the row records it, the rank drops, the tool
stays eligible. Comparison is between *results*, not registration entries.
"""
from __future__ import annotations

from typing import Optional

from .model import new_id, now_ms


def competitors(ctx, need: str) -> list[dict]:
    return [t for t in ctx.registry.tools() if t.get("need") == need]


def _normalize(res: dict) -> dict:
    """Shared local understanding: every competitor's result is folded to
    {ok, summary, artifact, count, confidence, error}."""
    r = res.get("result") if isinstance(res.get("result"), dict) else {}
    out = {"ok": bool(res.get("ok")) and not (isinstance(r, dict) and r.get("ok") is False),
           "error": res.get("error") or (r or {}).get("error"),
           "ms": res.get("ms")}
    if isinstance(r, dict):
        for k in ("summary", "artifact", "renderedBy", "items", "members",
                  "unconfigured"):
            if k in r:
                out[k] = r[k]
        out["count"] = (len(r["members"]) if isinstance(r.get("members"), list)
                        else r.get("items"))
        out["confidence"] = r.get("confidence", 0.8 if out["ok"] else 0.0)
    else:
        out["summary"] = str(res.get("result"))[:200]
        out["confidence"] = 0.8 if out["ok"] else 0.0
    return out


def run_competition(ctx, need: str, input: dict, claimant: str = "principal",
                    need_id: Optional[str] = None) -> dict:
    """Invoke every tool expressing `need` on the same input; normalize and
    rank the results; record the whole comparison as ledger evidence."""
    cands = competitors(ctx, need)
    comp_id = new_id("cmp")
    rows = []
    members_by_tool = {}
    for t in cands:
        t0 = now_ms()
        res = ctx.invoke(t["id"], input, need_id=need_id)
        norm = _normalize(res)
        _rr = res.get("result") or {}
        if isinstance(_rr, dict) and isinstance(_rr.get("members"), list):
            members_by_tool[t["id"]] = {m["name"]: m for m in _rr["members"]}
        norm["ms"] = res.get("ms", now_ms() - t0)
        ok = bool(res.get("ok"))
        adequate = norm["ok"] and not norm.get("unconfigured")
        ctx.decision.record_outcome(t["id"], need_id, ok, adequate)
        row = {"competition": comp_id, "toolId": t["id"], "need": need,
               "ok": norm["ok"], "adequate": adequate,
               "unconfigured": bool(norm.get("unconfigured")),
               "error": norm.get("error"), "ms": norm["ms"],
               "count": norm.get("count"), "summary": norm.get("summary"),
               "artifact": norm.get("artifact"),
               "confidence": norm.get("confidence"),
               "rankMultiplier": ctx.decision.rank_multiplier(t["id"]),
               "successRate": ctx.decision.success_rate(t["id"])}
        rows.append(row)
        ctx.append(f"comparison:{comp_id}", "comparison:row", row,
                   "system", basis={"kind": "execution"})
    # rank: adequate rows first, then confidence x rank multiplier
    def key(r):
        return (r["adequate"], r["confidence"] * r["rankMultiplier"], -r["ms"] or 0)
    ranked = sorted(rows, key=key, reverse=True)
    for i, r in enumerate(ranked):
        r["rank"] = i + 1
    rec = {"id": comp_id, "need": need, "input": {k: v for k, v in input.items()
           if not k.endswith("__confidence")},
           "competitors": len(rows), "adequate": sum(1 for r in rows if r["adequate"]),
           "ranking": [{"rank": r["rank"], "toolId": r["toolId"], "ok": r["ok"],
                        "adequate": r["adequate"], "count": r.get("count"),
                        "confidence": r["confidence"], "ms": r["ms"],
                        "unconfigured": r["unconfigured"]} for r in ranked]}
    ctx.append(f"comparison:{comp_id}", "comparison:run", rec, "system",
               basis={"kind": "durable-result"})
    return {"ok": True, "competition": rec, "rows": rows,
            "membersByTool": members_by_tool}
