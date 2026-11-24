"""Unmet-need floor (C-UnmetNeedRecords) + witnessed grants.
A detected opportunity is recorded as a `need:*` assertion before any work.
Creation does not imply execution: the template's gate decides. Missing or
inadequate required slots leave the need open; a consequential tool without a
matching witnessed grant defers with a recorded refusal — never silent
non-action and never a fabricated effect.
"""
from __future__ import annotations
import re
from typing import Optional
from . import model
# -- need status (computed from rows; the ledger is the record) ---------------
def need_rows(led, nid):
    return led.query(subject=f"need:{nid}", limit=500)
def need_status(led, nid) -> str:
    """open | deferred | fulfilled | cancelled | superseded — latest wins."""
    status = "open"
    for a in sorted(need_rows(led, nid), key=lambda r: r.at):
        p = a.predicate
        if p in ("need:fulfilled", "need:cancelled", "need:superseded"):
            status = p.split(":")[1]
        elif p == "need:deferred":
            status = "deferred"
        elif p in ("need:candidate", "need:focus", "need:refined",
                   "need:executing", "need:failed"):
            if status in ("open", "deferred"):
                status = "open" if p != "need:deferred" else status
    return status
def open_needs(led) -> list[dict]:
    ids = [a.value.get("v", {}).get("id") or a.subject.split(":", 1)[1]
           for a in led.query(predicate="need:open")]
    out = []
    for nid in dict.fromkeys(ids):
        rows = need_rows(led, nid)
        if not rows:
            continue
        st = need_status(led, nid)
        if st in ("fulfilled", "cancelled", "superseded"):
            continue
        first = next((r for r in rows if r.predicate == "need:open"), rows[0])
        v = first.value.get("v", {})
        out.append({"id": nid, "toolId": v.get("toolId"),
                    "kind": v.get("kind", "tool"),
                    "summary": v.get("summary", ""),
                    "missing": v.get("missing", []),
                    "status": st,
                    "focused": any(r.predicate == "need:focus" and
                                   (r.value.get("v") or {}).get("on")
                                   for r in rows),
                    "at": first.at})
    return sorted(out, key=lambda n: n["at"], reverse=True)
# -- slot acceptance tests (C-AcceptanceChecks) --------------------------------
def test_slot(test: Optional[dict], value) -> tuple[bool, str]:
    if not test:
        return True, "no-test"
    k = test.get("kind")
    if k == "enum":
        ok = value in test.get("options", [])
        return ok, "enum" if ok else f"not-in-{test.get('options')}"
    if k == "pattern":
        ok = bool(re.search(test.get("re", ".*"), str(value)))
        return ok, "pattern" if ok else "pattern-mismatch"
    if k == "type":
        t = test.get("t")
        ok = {"string": str, "number": (int, float),
              "boolean": bool, "list": list, "map": dict}.get(t, str)
        good = isinstance(value, ok) and not isinstance(value, bool) \
            if t == "number" else isinstance(value, ok)
        return good, "type" if good else f"not-{t}"
    if k == "minLen":
        ok = len(str(value)) >= int(test.get("n", 1))
        return ok, "minLen" if ok else "too-short"
    if k == "range":
        try:
            v = float(value)
            ok = test.get("lo", -1e18) <= v <= test.get("hi", 1e18)
            return ok, "range" if ok else "out-of-range"
        except (TypeError, ValueError):
            return False, "not-numeric"
    return True, f"unknown-test:{k}"
# -- grants ---------------------------------------------------------------------
def issue_grant(ctx, scope: str, lock: Optional[dict] = None,
                consumable: bool = True) -> str:
    gid = model.rid("g")
    ctx.ledger.say("grants", "grant:issued",
                   {"id": gid, "scope": scope, "consumable": consumable,
                    "lock": lock or {}, "witness": "principal"},
                   claimant="principal", certainty=1.0,
                   basis={"kind": "user-choice"})
    return gid
def _grant_rows(led):
    return led.query(predicate="grant:issued", limit=500)
def grant_available(led, scope: str) -> Optional[str]:
    consumed = {a.value.get("v", {}).get("id")
                for a in led.query(predicate="grant:consumed", limit=500)}
    for a in _grant_rows(led):
        v = a.value.get("v", {})
        if v.get("scope") == scope and v.get("id") not in consumed:
            return v.get("id")
    return None
def consume_grant(ctx, gid: str):
    ctx.ledger.say("grants", "grant:consumed", {"id": gid},
                   claimant="system", certainty=1.0,
                   basis={"kind": "execution"})
# -- the gate ---------------------------------------------------------------------
def open_need(ctx, tool: dict, slots: dict, summary: str, via: str,
              claimant: str = "principal") -> dict:
    """Record the unmet requirement, evaluate the template gate, and either
    execute or leave the need open. Returns a result dict."""
    led = ctx.ledger
    nid = model.rid("n")
    tpl = tool.get("template") or {}
    req = [s for s in tpl.get("slots", []) if s.get("required")]
    missing, failed = [], []
    for s in tpl.get("slots", []):
        name = s["name"]
        if name in slots:
            ok, why = test_slot(s.get("test"), slots[name])
            led.say(f"need:{nid}", "need:candidate",
                    {"slot": name, "value": slots[name], "test": why,
                     "adequate": ok},
                    claimant=claimant, certainty=0.9 if ok else 0.4,
                    basis={"kind": "user-choice" if via != "steward"
                           else "generated"})
            if not ok:
                failed.append({"slot": name, "why": why})
        elif s.get("required"):
            missing.append(name)
    led.say(f"need:{nid}", "need:open",
            {"id": nid, "toolId": tool["id"], "kind": tool.get("kind", "tool"),
             "summary": summary, "via": via, "missing": missing,
             "failed": failed}, claimant="system", certainty=1.0,
            basis={"kind": "interpretation"})
    # authority boundary: consequential tools need a witnessed grant
    scope = tpl.get("grant")
    gid = None
    if scope:
        gid = grant_available(led, scope)
        if not gid:
            led.say(f"need:{nid}", "need:deferred",
                    {"reason": "awaiting-authority", "scope": scope,
                     "status": "refused-pending-grant"},
                    claimant="system", certainty=1.0,
                    basis={"kind": "refusal"})
            return {"ok": False, "needId": nid, "status": "deferred",
                    "reason": f"requires witnessed grant '{scope}'",
                    "deferred": True}
    if missing or failed:
        led.say(f"need:{nid}", "need:deferred",
                {"reason": "inadequate-slots", "missing": missing,
                 "failed": failed},
                claimant="system", certainty=1.0,
                basis={"kind": "interpretation"})
        return {"ok": False, "needId": nid, "status": "open",
                "missing": missing, "failed": failed, "deferred": True}
    if gid:
        consume_grant(ctx, gid)
    return execute_need(ctx, tool, nid, slots, summary, via)
def execute_need(ctx, tool: dict, nid: str, slots: dict, summary: str,
                 via: str) -> dict:
    led = ctx.ledger
    led.say(f"need:{nid}", "need:executing", {"via": via},
            claimant="system", certainty=1.0, basis={"kind": "execution"})
    try:
        if tool.get("handler"):
            result = tool["handler"](ctx, slots, nid)
        else:
            from . import dsl
            result = dsl.run_steps(ctx, tool.get("steps", []),
                                   {"slots": slots, "needId": nid})
        ok = not (isinstance(result, dict) and result.get("ok") is False)
    except Exception as e:  # execution can finish without satisfying
        result = {"ok": False, "error": repr(e)}
        ok = False
    led.say(f"need:{nid}", "need:executed",
            {"ok": ok, "result": _truncate(result)},
            claimant="tool:" + tool["id"], certainty=1.0,
            basis={"kind": "execution"})
    if ok:
        led.say(f"need:{nid}", "need:fulfilled", {"result": _truncate(result)},
                claimant="system", certainty=1.0,
                basis={"kind": "durable-result"})
    else:
        led.say(f"need:{nid}", "need:failed", {"result": _truncate(result)},
                claimant="system", certainty=1.0,
                basis={"kind": "execution"})
        # a failed result leaves the need available for later work
    return {"ok": ok, "needId": nid, "result": result}
def retry_need(ctx, nid: str) -> dict:
    """Re-evaluate an open need's gate against its accumulated candidates."""
    led = ctx.ledger
    rows = need_rows(led, nid)
    opener = next((r for r in rows if r.predicate == "need:open"), None)
    if not opener:
        return {"ok": False, "error": "no such need"}
    spec = opener.value.get("v", {})
    tool = ctx.tools.get(spec.get("toolId"))
    if not tool:
        return {"ok": False, "error": "tool missing"}
    tpl = tool.get("template") or {}
    slots = {}
    missing, failed = [], []
    for s in tpl.get("slots", []):
        cands = led.candidates(f"need:{nid}", "need:candidate")
        mine = [c for c in cands
                if (c["value"] or {}).get("slot") == s["name"]
                and (c["value"] or {}).get("adequate", True)]
        if mine:
            slots[s["name"]] = mine[0]["value"].get("value")
        elif s.get("required"):
            missing.append(s["name"])
    scope = tpl.get("grant")
    if scope and not grant_available(led, scope):
        return {"ok": False, "needId": nid, "deferred": True,
                "reason": f"requires witnessed grant '{scope}'"}
    if missing:
        return {"ok": False, "needId": nid, "missing": missing,
                "failed": failed, "deferred": True}
    if scope:
        consume_grant(ctx, grant_available(led, scope))
    return execute_need(ctx, tool, nid, slots, spec.get("summary", ""), "retry")
def supply_candidate(ctx, nid: str, slot: str, value, source: str,
                     confidence: float = 0.9) -> dict:
    """Refinement: successive inputs add related assertions — the requirement
    is never reset, its criteria are preserved."""
    led = ctx.ledger
    tool = _tool_of(led, nid)
    spec = _slot_spec(tool, slot)
    ok, why = test_slot((spec or {}).get("test"), value)
    a = led.say(f"need:{nid}", "need:candidate",
                {"slot": slot, "value": value, "test": why, "adequate": ok,
                 "via": source},
                claimant="principal" if source == "user" else f"model:{source}",
                certainty=confidence,
                basis={"kind": "user-choice" if source == "user"
                       else "interpretation"})
    led.say(f"need:{nid}", "need:refined", {"slot": slot, "by": source},
            claimant="system", certainty=1.0,
            basis={"kind": "interpretation"}, links=[a.id])
    return {"ok": ok, "test": why, "id": a.id}
def focus_need(ctx, nid: str, on: bool = True) -> dict:
    ctx.ledger.say(f"need:{nid}", "need:focus", {"on": on},
                   claimant="principal", certainty=1.0,
                   basis={"kind": "user-choice"})
    if on:
        ctx.ledger.say("chat", "chat:focus", {"needId": nid},
                       claimant="system", certainty=1.0,
                       basis={"kind": "config"})
    return {"ok": True, "needId": nid, "focused": on}
def focused_need(led) -> Optional[str]:
    a = led.resolve("chat", "chat:focus")
    if a:
        v = a.value.get("v") or {}
        nid = v.get("needId")
        if nid and need_status(led, nid) not in ("fulfilled", "cancelled"):
            return nid
    return None
def cancel_need(ctx, nid: str):
    ctx.ledger.say(f"need:{nid}", "need:cancelled", {},
                   claimant="principal", certainty=1.0,
                   basis={"kind": "user-choice"})
    return {"ok": True}
def _tool_of(led, nid):
    rows = need_rows(led, nid)
    opener = next((r for r in rows if r.predicate == "need:open"), None)
    return None  # resolved by caller through ctx
def _slot_spec(tool, name):
    if not tool:
        return None
    for s in (tool.get("template") or {}).get("slots", []):
        if s["name"] == name:
            return s
    return None
def _truncate(result, limit=4000):
    s = repr(result)
    if len(s) > limit:
        return {"truncated": s[:limit]}
    return result
