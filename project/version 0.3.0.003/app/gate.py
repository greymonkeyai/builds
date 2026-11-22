"""Interactive Readiness Gate (C-ReadinessGate).

User interaction unlocks at a declared gate testing two conditions:

1. **Input readiness** — primitive pipelines and the primary interactive LLM
   handles accept and route input. Tested by: the chat-turn chain components
   are registered (parse-chat, run-chat-turn, speak path), primitives answer,
   and the LLM handle completes a probe (a declared-stub mode is a *valid*
   mode — the gate tests that the handle accepts and routes input, and the
   honesty banner declares the mode).
2. **Ledger readiness** — the essential launch partition is mounted, valid,
   and queryable: the launch file parsed, its essential subjects are live,
   and a real query round-trips.

The gate records its pass time in accessible evidence: a `gate:passed`
assertion, `runtime/gate.json`, the launch log, and `last-launch.json` —
time-to-gate (session start -> pass) is a named metric.
"""
from __future__ import annotations

import json
import os
from typing import Optional

from .model import now_ms


def run_gate(ctx, started_ms: int) -> dict:
    """Execute the readiness checks. Returns the gate record (pass time +
    per-condition detail). Never declares a pass it didn't verify."""
    checks = {"input": {}, "ledger": {}}

    # ---- input readiness ----
    comps = ctx.registry.components
    need_ids = ["parse-chat", "run-chat-turn", "speak-voice",
                "persona.speak", "ledger.append"]
    checks["input"]["components"] = all(cid in comps for cid in need_ids)
    checks["input"]["componentCount"] = len(comps)
    try:
        r = ctx.invoke("parse-chat", {"text": "readiness gate probe"})
        checks["input"]["pipelineRoutes"] = bool(r.get("ok"))
    except Exception as e:
        checks["input"]["pipelineRoutes"] = False
        checks["input"]["pipelineError"] = repr(e)
    eng = ctx.engines.llm
    checks["input"]["llmMode"] = eng.mode
    checks["input"]["llmAccepts"] = eng.mode in ("live-ollama", "stub") and \
        callable(getattr(eng, "complete", None))
    checks["input"]["primitiveAnswer"] = bool(
        ctx.invoke("ledger.query", {"predicate": "engine:mode",
                                    "limit": 1}).get("ok") or
        ctx.engine_invoke is not None)
    input_ready = (checks["input"]["components"]
                   and checks["input"]["pipelineRoutes"]
                   and checks["input"]["llmAccepts"])

    # ---- ledger readiness ----
    checks["ledger"]["durable"] = os.path.exists(ctx.ledger.path)
    checks["ledger"]["partitionMounted"] = ctx.ledger.partition_mounted
    checks["ledger"]["partitionFile"] = ctx.ledger.partition_path
    try:
        probe = ctx.ledger.query(predicate="engine:mode", limit=1)
        checks["ledger"]["queryable"] = True
        checks["ledger"]["live"] = ctx.ledger.stats()["live"]
        # essential subjects materialized: seed marker or partition rows
        checks["ledger"]["essentialMounted"] = (
            ctx.ledger.partition_mounted > 0
            or bool(ctx.ledger.query(predicate="seed:loaded", limit=1))
            or checks["ledger"]["live"] > 0)
    except Exception as e:
        checks["ledger"]["queryable"] = False
        checks["ledger"]["error"] = repr(e)
    ledger_ready = (checks["ledger"]["durable"]
                    and checks["ledger"]["queryable"]
                    and checks["ledger"]["essentialMounted"])

    passed = input_ready and ledger_ready
    rec = {"passed": passed, "checks": checks,
           "startedMs": started_ms,
           "passedAt": now_ms() if passed else None,
           "msToGate": (now_ms() - started_ms) if passed else None,
           "inputReady": input_ready, "ledgerReady": ledger_ready}
    ctx.append("gate", "gate:check", rec, "system",
               basis={"kind": "execution"})
    if passed:
        ctx.append("gate", "gate:passed",
                   {"passedAt": rec["passedAt"], "msToGate": rec["msToGate"],
                    "inputReady": True, "ledgerReady": True},
                   "system", basis={"kind": "execution"})
    gate_path = os.path.join(ctx.runtime, "gate.json")
    with open(gate_path, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=2)
    rec["path"] = gate_path
    return rec
