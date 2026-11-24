"""Tool-logic-as-data interpreter (C-ConvergentOntology).
User-authored tools are step lists over a closed op set — no eval. Steps read
and write an env ({slots, results, vars}); value references use "$path"
against env and "{path}" interpolation inside strings.
"""
from __future__ import annotations
import json
import re
OPS = ("set", "query", "assert", "each", "if", "invoke", "engine",
       "emit", "result", "fail", "first", "concat")
def _lookup(env, path):
    cur = env
    for part in str(path).split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, (list, tuple)) and part.isdigit():
            cur = cur[int(part)]
        else:
            return None
    return cur
def resolve(v, env):
    if isinstance(v, str):
        if v.startswith("$"):
            return _lookup(env, v[1:])
        def sub(m):
            got = _lookup(env, m.group(1))
            return "" if got is None else str(got)
        return re.sub(r"\{([\w.\[\]]+)\}", sub, v)
    if isinstance(v, list):
        return [resolve(x, env) for x in v]
    if isinstance(v, dict):
        return {k: resolve(x, env) for k, x in v.items()}
    return v
def run_steps(ctx, steps, env=None) -> dict:
    env = dict(env or {})
    env.setdefault("vars", {})
    env.setdefault("results", [])
    for i, st in enumerate(steps or []):
        op = st.get("op")
        if op not in OPS:
            return {"ok": False, "error": f"unknown op '{op}' at step {i}"}
        try:
            out = _step(ctx, op, st, env, i)
            if isinstance(out, dict) and out.get("__return"):
                return out["value"]
        except Exception as e:
            return {"ok": False, "error": f"step {i} ({op}): {e!r}"}
    return {"ok": True, "results": env.get("results"),
            "vars": env.get("vars")}
def _step(ctx, op, st, env, i):
    led = ctx.ledger
    if op == "set":
        env["vars"][st["k"]] = resolve(st.get("value"), env)
        env["results"] = env["vars"][st["k"]]
    elif op == "query":
        rows = led.query(subject=resolve(st.get("subject"), env),
                         predicate=resolve(st.get("predicate"), env),
                         limit=int(st.get("limit", 50)),
                         current=bool(st.get("current", True)))
        env["results"] = [r.row() for r in rows]
    elif op == "first":
        rows = env.get("results") or []
        env["vars"][st.get("k", "first")] = rows[0] if rows else None
    elif op == "assert":
        led.say(resolve(st.get("subject"), env),
                resolve(st.get("predicate"), env),
                resolve(st.get("value"), env),
                claimant=st.get("claimant", "tool:dsl"),
                certainty=float(st.get("certainty", 0.9)),
                basis={"kind": st.get("basis", "execution")})
    elif op == "each":
        items = resolve(st.get("over"), env) or []
        acc = []
        for it in items:
            env["it"] = it
            r = run_steps(ctx, st.get("steps", []), env)
            acc.append(r)
            if isinstance(r, dict) and r.get("ok") is False:
                env["results"] = acc
                return r
        env["results"] = acc
    elif op == "if":
        cond = resolve(st.get("cond"), env)
        branch = st.get("then", []) if cond else st.get("else", [])
        r = run_steps(ctx, branch, env)
        if isinstance(r, dict) and r.get("ok") is False:
            return r
    elif op == "invoke":
        tid = resolve(st.get("tool"), env)
        slots = resolve(st.get("slots", {}), env)
        r = ctx.invoke(tid, slots, via="tool", summary=f"dsl invoke {tid}")
        env["results"] = r
        if isinstance(r, dict) and r.get("ok") is False and not r.get("deferred"):
            return r
    elif op == "engine":
        name = resolve(st.get("name"), env)
        call = resolve(st.get("call"), env)
        args = resolve(st.get("args", {}), env)
        env["results"] = ctx.engine_call(name, call, args)
    elif op == "emit":
        ctx.bus.emit(resolve(st.get("kind", "card"), env),
                     resolve(st.get("payload", {}), env))
    elif op == "concat":
        parts = resolve(st.get("parts", []), env) or []
        env["vars"][st.get("k", "text")] = str(st.get("sep", "")).join(
            str(p) for p in parts)
    elif op == "result":
        return {"__return": True, "value": resolve(st.get("value"), env)}
    elif op == "fail":
        return {"__return": True,
                "value": {"ok": False,
                          "error": resolve(st.get("reason", "failed"), env)}}
    return None
def validate_spec(spec: dict) -> dict:
    """Novice tool authoring: errors, warnings, repair hints."""
    errors, warnings, hints = [], [], []
    if not isinstance(spec, dict):
        return {"ok": False, "errors": ["spec must be a JSON object"]}
    tid = spec.get("id")
    if not tid or not re.match(r"^[a-z0-9][a-z0-9\-]*$", str(tid)):
        errors.append("id must be lowercase-kebab (a-z0-9-)")
        hints.append("try id like 'my-tool'")
    if not spec.get("title"):
        warnings.append("no title — the library shows the id instead")
    tpl = spec.get("template") or {}
    if not isinstance(tpl.get("slots", []), list):
        errors.append("template.slots must be a list")
    for s in tpl.get("slots", []):
        if "name" not in s:
            errors.append("a slot is missing 'name'")
    steps = spec.get("steps")
    if not steps and not spec.get("need"):
        warnings.append("no steps and no need — the tool can only open needs")
    for j, st in enumerate(steps or []):
        if st.get("op") not in OPS:
            errors.append(f"step {j}: unknown op '{st.get('op')}'")
            hints.append(f"valid ops: {', '.join(OPS)}")
    if spec.get("template", {}).get("grant") and not spec.get("consequential", True):
        warnings.append("grant-gated tools are consequential — kept the gate")
    return {"ok": not errors, "errors": errors, "warnings": warnings,
            "hints": hints}
