"""Competing tools (prompt §Tools and local comparison).
Every tool expressing the same `need:` is invoked on the same input; results
are normalized to a shared local understanding, ranked, and recorded
(`comparison:run` + `comparison:row`). Adequate outcomes feed tool-trust
churn: a bounded rank multiplier among alternatives — an inadequate tool
stays eligible but sinks; successes recover it.
"""
from __future__ import annotations
from . import model, floor
def trust(led, tool_id: str) -> float:
    a = led.resolve(f"tool:{tool_id}", "tool:trust")
    if a:
        return float((a.value.get("v") or {}).get("trust", 1.0))
    return 1.0
def adjust_trust(ctx, tool_id: str, adequate: bool):
    cur = trust(ctx.ledger, tool_id)
    new = min(1.0, cur + 0.05) if adequate else max(0.1, cur - 0.15)
    if new == cur:
        return
    prev = ctx.ledger.resolve(f"tool:{tool_id}", "tool:trust")
    ctx.ledger.say(f"tool:{tool_id}", "tool:trust",
                   {"trust": round(new, 3), "prior": cur,
                    "why": "adequate" if adequate else "inadequate"},
                   claimant="system", certainty=1.0,
                   basis={"kind": "execution"},
                   supersedes=prev.id if prev else None)
def compete(ctx, need_expr: str, input_slots: dict,
            normalize=None) -> dict:
    """Run all tools expressing `need_expr` on the same input. Both adequate
    results and failures are recorded — the losing side is evidence, not an
    error."""
    led = ctx.ledger
    contestants = ctx.tools.for_need(need_expr)
    run_id = model.rid("cmp")
    rows = []
    for t in contestants:
        r = floor.open_need(ctx, t, dict(input_slots),
                            summary=f"compete:{need_expr}", via="competition")
        res = r.get("result") or {}
        adequate = bool(r.get("ok")) and bool(res.get("ok", True))
        norm = normalize(res) if (normalize and adequate) else res
        rows.append({
            "toolId": t["id"], "ok": r.get("ok"), "adequate": adequate,
            "trust": trust(led, t["id"]),
            "result": _cap(norm)})
        adjust_trust(ctx, t["id"], adequate)
    ranked = sorted(rows, key=lambda x: (x["adequate"], x["trust"]),
                    reverse=True)
    for i, row in enumerate(ranked):
        led.say(f"comparison:{run_id}", "comparison:row",
                {"rank": i, **row}, claimant="system", certainty=1.0,
                basis={"kind": "execution"})
    led.say("comparison", "comparison:run",
            {"id": run_id, "need": need_expr, "tools": [t["id"] for t in
             contestants],
             "adequate": sum(1 for r in rows if r["adequate"]),
             "winner": ranked[0]["toolId"] if ranked else None},
            claimant="system", certainty=1.0,
            basis={"kind": "durable-result"})
    return {"ok": True, "runId": run_id, "need": need_expr, "rows": ranked,
            "adequate": sum(1 for r in rows if r["adequate"])}
def _cap(v, n=300):
    s = repr(v)
    return s[:n] + "…" if len(s) > n else v
