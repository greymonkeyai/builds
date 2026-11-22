"""Tool-logic-as-data: a closed-op interpreter.

Tools are data: { template, steps }. Steps run over a bindings scope seeded
with { input, grant }. There is no eval — only this closed op set:

  set | query | search | view | candidates | append | appendEach | when |
  invoke | engine | emit | repeat | result | fail

Value resolution:
  {"$ref": "input.name"}        scope lookup (dotted path)
  {"$tpl": "Hello {name}"}      string template over scope values
  {"$typed": {...}}             TypedValue literal
  {"$now": true}                epoch ms
  {"$uid": "p"}                 fresh id with prefix
  {"$pipe": [R, "trim", ...]}   transform pipeline
  {"$first": R} {"$last": R} {"$len": R} {"$int": R} {"$get": [R, "k"]}
  {"$join": [R, ", "]} {"$coalesce": [R, ...]} {"$list": [R, ...]}
  {"$map": {"of": R, "as": "x", "tpl": R}}   per-item template
  {"$slugsig": R}               normalized signature for matching

Conditions: truthy/eq/ne/gt/gte/lt/lte/matches/contains/not/and/or.
"""
from __future__ import annotations

import re
import time
from typing import Any

from .model import infer_typed, new_id


class ToolError(Exception):
    def __init__(self, message: str, data: Any = None):
        super().__init__(message)
        self.data = data


TRANSFORMS = {
    "trim": lambda v: str(v).strip(),
    "lower": lambda v: str(v).lower(),
    "upper": lambda v: str(v).upper(),
    "slug": lambda v: re.sub(r"[^a-z0-9]+", "-", str(v).lower()).strip("-"),
    "titlecase": lambda v: str(v).title(),
    "json": lambda v: __import__("json").dumps(v, ensure_ascii=False),
    "int": lambda v: int(float(v)),
    "str": lambda v: str(v),
}


def _slugify(v: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(v).lower()).strip("-")


class Scope:
    def __init__(self, bindings: dict):
        self.b = bindings

    def get(self, path: str) -> Any:
        cur: Any = self.b
        for part in path.split("."):
            if isinstance(cur, dict):
                cur = cur.get(part)
            elif isinstance(cur, list):
                try:
                    cur = cur[int(part)]
                except (ValueError, IndexError):
                    return None
            else:
                return None
        return cur

    def flatten(self) -> dict:
        out = {}
        def walk(prefix, v):
            if isinstance(v, dict):
                for k, vv in v.items():
                    walk(f"{prefix}{k}.", vv)
            out[prefix[:-1] if prefix.endswith(".") else prefix] = v
        for k, v in self.b.items():
            if isinstance(v, (str, int, float, bool)):
                out[k] = v
            else:
                walk(f"{k}.", v)
        return out


def resolve(v: Any, scope: Scope, ctx) -> Any:
    if isinstance(v, dict):
        keys = [k for k in v if k.startswith("$")]
        if len(keys) == 1:
            k = keys[0]
            if k == "$ref":
                return scope.get(v[k])
            if k == "$tpl":
                flat = scope.flatten()
                def sub(m):
                    return str(flat.get(m.group(1), m.group(0)))
                return re.sub(r"\{([a-zA-Z0-9_.]+)\}", sub, v[k])
            if k == "$typed":
                return dict(v[k])
            if k == "$now":
                return int(time.time() * 1000)
            if k == "$uid":
                return new_id(str(v[k]))
            if k == "$pipe":
                items = v[k]
                cur = resolve(items[0], scope, ctx)
                for t in items[1:]:
                    fn = TRANSFORMS.get(str(t))
                    if not fn:
                        raise ToolError(f"unknown transform: {t}")
                    cur = fn(cur)
                return cur
            if k == "$first":
                arr = resolve(v[k], scope, ctx) or []
                return arr[0] if arr else None
            if k == "$last":
                arr = resolve(v[k], scope, ctx) or []
                return arr[-1] if arr else None
            if k == "$len":
                arr = resolve(v[k], scope, ctx)
                return len(arr) if arr is not None else 0
            if k == "$int":
                return int(float(resolve(v[k], scope, ctx) or 0))
            if k == "$get":
                obj = resolve(v[k][0], scope, ctx)
                return obj.get(v[k][1]) if isinstance(obj, dict) else None
            if k == "$join":
                arr = resolve(v[k][0], scope, ctx) or []
                sep = v[k][1] if len(v[k]) > 1 else ", "
                return sep.join(str(x) for x in arr)
            if k == "$coalesce":
                for item in v[k]:
                    r = resolve(item, scope, ctx)
                    if r not in (None, "", []):
                        return r
                return None
            if k == "$list":
                return [resolve(x, scope, ctx) for x in v[k]]
            if k == "$map":
                spec = v[k]
                arr = resolve(spec["of"], scope, ctx) or []
                name = spec.get("as", "item")
                out = []
                for it in arr:
                    scope.b[name] = it
                    out.append(resolve(spec["tpl"], scope, ctx))
                scope.b.pop(name, None)
                return out
            if k == "$filter":
                spec = v[k]
                arr = resolve(spec["of"], scope, ctx) or []
                name = spec.get("as", "item")
                out = []
                for it in arr:
                    scope.b[name] = it
                    if eval_cond(spec["where"], scope, ctx):
                        out.append(it)
                scope.b.pop(name, None)
                return out
            if k == "$slugsig":
                return _slugify(resolve(v[k], scope, ctx))
        return {kk: resolve(vv, scope, ctx) for kk, vv in v.items()}
    if isinstance(v, list):
        return [resolve(x, scope, ctx) for x in v]
    return v


def eval_cond(cond: Any, scope: Scope, ctx) -> bool:
    if not isinstance(cond, dict):
        return bool(resolve(cond, scope, ctx))
    for k, v in cond.items():
        if k == "truthy":
            return bool(resolve(v, scope, ctx))
        if k == "eq":
            return resolve(v[0], scope, ctx) == resolve(v[1], scope, ctx)
        if k == "ne":
            return resolve(v[0], scope, ctx) != resolve(v[1], scope, ctx)
        if k in ("gt", "gte", "lt", "lte"):
            a, b = resolve(v[0], scope, ctx), resolve(v[1], scope, ctx)
            a, b = float(a or 0), float(b or 0)
            return {"gt": a > b, "gte": a >= b, "lt": a < b, "lte": a <= b}[k]
        if k == "matches":
            s = resolve(v[0], scope, ctx)
            return bool(re.search(str(v[1]), str(s or ""), re.I))
        if k == "contains":
            hay = resolve(v[0], scope, ctx)
            needle = resolve(v[1], scope, ctx)
            if isinstance(hay, (list, tuple, set)):
                return needle in hay
            return str(needle).lower() in str(hay or "").lower()
        if k == "not":
            return not eval_cond(v, scope, ctx)
        if k == "and":
            return all(eval_cond(c, scope, ctx) for c in v)
        if k == "or":
            return any(eval_cond(c, scope, ctx) for c in v)
    return False


def run_steps(steps: list, scope: Scope, ctx) -> Any:
    for step in steps:
        op = step.get("op")
        if op == "set":
            scope.b[step["into"]] = resolve(step["value"], scope, ctx)
        elif op == "query":
            rows = ctx.ledger.query(
                subject=resolve(step.get("subject"), scope, ctx),
                predicate=resolve(step.get("predicate"), scope, ctx),
                claimant=resolve(step.get("claimant"), scope, ctx),
                include_superseded=bool(step.get("includeSuperseded")),
                limit=int(resolve(step.get("limit"), scope, ctx) or 0),
                tag=resolve(step.get("tag"), scope, ctx))
            scope.b[step["into"]] = [r.to_row() for r in rows]
        elif op == "search":
            rows = ctx.ledger.search(resolve(step["text"], scope, ctx),
                                     limit=int(resolve(step.get("limit"), scope, ctx) or 20))
            scope.b[step["into"]] = [r.to_row() for r in rows]
        elif op == "view":
            scope.b[step["into"]] = ctx.ledger.render_view(
                resolve(step["subject"], scope, ctx))
        elif op == "candidates":
            scope.b[step["into"]] = ctx.ledger.candidates_for(
                resolve(step["subject"], scope, ctx),
                resolve(step["predicate"], scope, ctx))
        elif op == "append":
            a = ctx.append(
                subject=resolve(step["subject"], scope, ctx),
                predicate=resolve(step["predicate"], scope, ctx),
                value=resolve(step.get("value"), scope, ctx),
                claimant=resolve(step.get("claimant"), scope, ctx) or "system",
                certainty=resolve(step.get("certainty"), scope, ctx) or 1.0,
                context=resolve(step.get("context"), scope, ctx) or 1.0,
                basis=resolve(step.get("basis"), scope, ctx),
                supersedes=resolve(step.get("supersedes"), scope, ctx),
                relates=resolve(step.get("relates"), scope, ctx),
                tags=resolve(step.get("tags"), scope, ctx),
                meta=resolve(step.get("meta"), scope, ctx))
            if step.get("into"):
                scope.b[step["into"]] = a.to_row()
        elif op == "appendEach":
            arr = resolve(step["for"], scope, ctx) or []
            name = step.get("as", "item")
            out = []
            for it in arr:
                scope.b[name] = it
                a = ctx.append(
                    subject=resolve(step["subject"], scope, ctx),
                    predicate=resolve(step["predicate"], scope, ctx),
                    value=resolve(step.get("value"), scope, ctx),
                    claimant=resolve(step.get("claimant"), scope, ctx) or "system",
                    certainty=resolve(step.get("certainty"), scope, ctx) or 1.0,
                    basis=resolve(step.get("basis"), scope, ctx),
                    relates=resolve(step.get("relates"), scope, ctx))
                out.append(a.id)
            scope.b.pop(name, None)
            if step.get("into"):
                scope.b[step["into"]] = out
        elif op == "when":
            branch = step["then"] if eval_cond(step["if"], scope, ctx) else step.get("else", [])
            r = run_steps(branch, scope, ctx)
            if r is not None:
                return r
        elif op == "invoke":
            r = ctx.invoke(resolve(step["component"], scope, ctx),
                           resolve(step.get("input", {}), scope, ctx),
                           grant=scope.b.get("grant"))
            if step.get("into"):
                scope.b[step["into"]] = r
        elif op == "invokeEach":
            arr = resolve(step["for"], scope, ctx) or []
            name = step.get("as", "item")
            results = []
            for it in arr:
                scope.b[name] = it
                r = ctx.invoke(resolve(step["component"], scope, ctx),
                               resolve(step.get("input", {}), scope, ctx),
                               grant=scope.b.get("grant"))
                results.append(r)
            scope.b.pop(name, None)
            if step.get("into"):
                scope.b[step["into"]] = results
        elif op == "engine":
            r = ctx.engine_invoke(resolve(step["engine"], scope, ctx),
                                  resolve(step["method"], scope, ctx),
                                  resolve(step.get("args", {}), scope, ctx))
            if step.get("into"):
                scope.b[step["into"]] = r
        elif op == "emit":
            ctx.emit(resolve(step["kind"], scope, ctx),
                     resolve(step.get("payload"), scope, ctx))
        elif op == "repeat":
            times = int(resolve(step["times"], scope, ctx) or 1)
            for i in range(times):
                scope.b["i"] = i
                r = run_steps(step["steps"], scope, ctx)
                if r is not None:
                    return r
        elif op == "result":
            return resolve(step.get("value"), scope, ctx)
        elif op == "fail":
            raise ToolError(str(resolve(step["error"], scope, ctx)),
                            resolve(step.get("data"), scope, ctx))
        else:
            raise ToolError(f"unknown op: {op}")
    return None
