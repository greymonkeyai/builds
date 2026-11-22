"""Invokable component registry: tools, system commands, primitives.

- Tool: user-editable data (template + steps) run by the closed-op executor.
- System command: object.verb host effect (mint, send, compact, grant...).
- Primitive: irreducible host verb on a closed allow-list.

Grants are consumable, scoped, witnessed, target-locked. A tool whose template
declares a grant cannot execute without a matching witnessed grant; a request
that lacks one resolves to a recorded refusal/deferral, not silent non-action.
"""
from __future__ import annotations

import json
from typing import Any, Optional

from . import dsl, needs
from .model import new_id, now_ms


class Registry:
    def __init__(self):
        self.components: dict[str, dict] = {}

    def register(self, spec: dict) -> dict:
        cid = spec["id"]
        spec.setdefault("kind", "tool")
        spec.setdefault("template", {"slots": []})
        spec.setdefault("steps", [])
        spec.setdefault("triggers", {"keywords": [], "patterns": []})
        spec.setdefault("need", None)
        spec.setdefault("editable", spec["kind"] == "tool")
        self.components[cid] = spec
        return spec

    def get(self, cid: str) -> Optional[dict]:
        return self.components.get(cid)

    def tools(self) -> list[dict]:
        return [s for s in self.components.values() if s["kind"] == "tool"]

    def commands(self) -> list[dict]:
        return [s for s in self.components.values() if s["kind"] == "system-command"]

    def primitives(self) -> list[dict]:
        return [s for s in self.components.values() if s["kind"] == "primitive"]

    def manifest(self) -> list[dict]:
        return [{
            "id": s["id"], "kind": s["kind"], "title": s.get("title", s["id"]),
            "need": s.get("need"), "editable": s.get("editable", False),
            "slots": s.get("template", {}).get("slots", []),
            "grant": s.get("template", {}).get("grant"),
            "triggers": s.get("triggers", {}),
            "hasSteps": bool(s.get("steps")),
            "hasFn": bool(s.get("fn")),
        } for s in sorted(self.components.values(), key=lambda x: x["id"])]


# ---- grants -----------------------------------------------------------------

def grant_subject(gid: str) -> str:
    return f"grant:{gid}"


def issue_grant(ctx, scope: str, lock: Optional[str] = None,
                witness: str = "principal") -> str:
    """Witnessed grant: an explicit user choice, recorded. Consumable."""
    gid = new_id("g")
    ctx.append(grant_subject(gid), "grant:issued",
               {"scope": scope, "lock": lock, "consumed": False},
               witness, basis={"kind": "user-choice"})
    return gid


def live_grant(ctx, scope: str, lock: Optional[str] = None) -> Optional[dict]:
    """Find an unconsumed witnessed grant matching scope and lock."""
    for a in ctx.ledger.query(predicate="grant:issued"):
        v = a.value["v"]
        if v.get("consumed"):
            continue
        if v.get("scope") != scope:
            continue
        if v.get("lock") and lock and v["lock"] != lock:
            continue
        return {"id": a.subjectKey.split(":", 1)[1], "scope": v["scope"],
                "lock": v.get("lock"), "assertionId": a.id}
    return None


def consume_grant(ctx, gid: str) -> None:
    subj = grant_subject(gid)
    rows = ctx.ledger.query(subject=subj, predicate="grant:issued")
    if not rows:
        return
    row = rows[-1]
    v = dict(row.value["v"]); v["consumed"] = True
    ctx.append(subj, "grant:issued", v, "system", supersedes=row.id,
               basis={"kind": "execution"})
    ctx.append(subj, "grant:consumed", {"by": "need.fulfill", "at": now_ms()},
               "system", basis={"kind": "execution"})


# ---- template gate ----------------------------------------------------------

def evaluate_gate(ctx, spec: dict, supplied: dict, nid: Optional[str] = None) -> dict:
    """Entry-path-neutral readiness check. Returns {ready, missing, onOrder,
    grant}. Required slots need a candidate at/above minCertainty (from
    supplied input or need:candidate rows)."""
    tmpl = spec.get("template") or {}
    missing, filled = [], {}
    cands = needs.candidates(ctx, nid) if nid else {}
    for slot in tmpl.get("slots", []):
        name = slot["name"]
        min_c = slot.get("minCertainty", 0.7)
        val = supplied.get(name)
        conf = None
        if val not in (None, ""):
            conf = float(supplied.get(f"{name}__confidence", 1.0))
            if conf >= min_c:
                filled[name] = {"value": val, "confidence": conf, "source": "input"}
                continue
        nc = (cands.get(name) or [])
        if nc and nc[0]["effectiveConfidence"] >= min_c:
            filled[name] = nc[0]
            continue
        if slot.get("required", True):
            missing.append({"slot": name, "minCertainty": min_c,
                            "best": nc[0]["effectiveConfidence"] if nc else None})
    grant_req = tmpl.get("grant")
    grant_state = None
    if grant_req:
        g = live_grant(ctx, grant_req["scope"], supplied.get("lock") or grant_req.get("lock"))
        grant_state = {"required": True, "scope": grant_req["scope"],
                       "lock": grant_req.get("lock"),
                       "witnessed": bool(g), "grantId": g["id"] if g else None}
        if not g:
            missing.append({"slot": "__grant__", "minCertainty": 1.0,
                            "scope": grant_req["scope"]})
    return {"ready": not missing, "missing": missing, "filled": filled,
            "grant": grant_state}


# ---- invoke / fulfill -------------------------------------------------------

def invoke(ctx, cid: str, input: Optional[dict] = None,
           grant: Optional[dict] = None, need_id: Optional[str] = None) -> dict:
    """Invoke a component by id. Honors the gate for templated tools when a
    need context is given; direct invokes assume operator authority and run."""
    spec = ctx.registry.get(cid)
    if not spec:
        return {"ok": False, "error": f"unknown component: {cid}"}
    input = dict(input or {})
    scope = dsl.Scope({"input": input, "grant": grant, "need": need_id})
    t0 = now_ms()
    try:
        if spec.get("fn") is not None:
            out = spec["fn"](ctx, input, grant)
        else:
            out = dsl.run_steps(spec.get("steps", []), scope, ctx)
        dur = now_ms() - t0
        _telemetry(ctx, cid, "ok", dur, need_id)
        return {"ok": True, "result": out, "ms": dur}
    except dsl.ToolError as e:
        _telemetry(ctx, cid, "failed", now_ms() - t0, need_id, str(e))
        return {"ok": False, "error": str(e), "data": e.data}
    except Exception as e:  # honest failure, recorded
        _telemetry(ctx, cid, "error", now_ms() - t0, need_id, repr(e))
        return {"ok": False, "error": repr(e)}


def fulfill_need(ctx, nid: str) -> dict:
    """need.fulfill path: unpack gate, invoke, close or defer the need.
    Records execution evidence either way. Failed/insufficient results leave
    the need Open and lower the tool's rank among alternatives (trust churn)
    without making it ineligible."""
    st = needs.need_state(ctx, nid)
    if st["status"] != "open":
        return {"ok": False, "error": f"need {nid} is {st['status']}"}
    spec = st["spec"]
    cid = spec.get("toolId")
    if not cid:
        return {"ok": False, "error": "need has no toolId"}
    tool = ctx.registry.get(cid)
    if not tool:
        needs.defer_need(ctx, nid, "tool not registered", [cid], "system")
        return {"ok": False, "error": f"tool not registered: {cid}"}
    gate = evaluate_gate(ctx, tool, spec.get("slots", {}), nid)
    if not gate["ready"]:
        needs.defer_need(ctx, nid, "requirements on order",
                         gate["missing"], "steward:its")
        if gate["grant"] and not gate["grant"]["witnessed"]:
            ctx.append(need := f"need:{nid}", "need:deferred",
                       {"reason": "grant-required",
                        "scope": gate["grant"]["scope"]}, "steward:its",
                       basis={"kind": "refusal"})
        return {"ok": False, "deferred": True, "missing": gate["missing"]}
    input_vals = {k: v["value"] for k, v in gate["filled"].items()}
    input_vals.update({k: v for k, v in spec.get("slots", {}).items()
                       if not k.endswith("__confidence") and k not in input_vals})
    grant = None
    if gate["grant"] and gate["grant"]["witnessed"]:
        grant = {"id": gate["grant"]["grantId"], "scope": gate["grant"]["scope"]}
    ctx.append(f"need:{nid}", "need:fulfilled",   # in-flight marker superseded at close
               {"status": "dispatching", "toolId": cid}, "steward:its",
               basis={"kind": "execution"})
    res = invoke(ctx, cid, input_vals, grant=grant, need_id=nid)
    if grant:
        consume_grant(ctx, grant["id"])
    adequate = res.get("ok") and _adequate(ctx, spec, res)
    ctx.decision.record_outcome(cid, nid, bool(res.get("ok")), adequate)
    if adequate:
        needs.close_need(ctx, nid, "fulfilled",
                         {"toolId": cid, "result": res.get("result"),
                          "ms": res.get("ms")}, "system")
        return {"ok": True, "result": res.get("result")}
    needs.defer_need(ctx, nid,
                     "insufficient result — need remains open for later work",
                     spec.get("satisfaction", {}), "system")
    return {"ok": False, "insufficient": True, "error": res.get("error")}


def _adequate(ctx, spec: dict, res: dict) -> bool:
    """Satisfaction conditions: a tool result is adequate only if it matches
    the need's declared conditions (result.ok plus optional value tests)."""
    sat = spec.get("satisfaction") or {}
    if not res.get("ok"):
        return False
    r = res.get("result")
    if isinstance(r, dict) and r.get("ok") is False:
        return False
    tests = sat.get("resultTests") or []
    scope = dsl.Scope({"result": r or {}})
    for t in tests:
        if not dsl.eval_cond(t, scope, ctx):
            return False
    return True


def _telemetry(ctx, cid: str, status: str, ms: int,
               need_id: Optional[str], error: Optional[str] = None):
    ctx.append(f"tool:{cid}", "tool:telemetry",
               {"status": status, "ms": ms, "needId": need_id, "error": error},
               "tool:registry", basis={"kind": "execution"})
