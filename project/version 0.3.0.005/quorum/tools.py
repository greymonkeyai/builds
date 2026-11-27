"""Quorum tools — registry, declarative step DSL, candidates, mint, endorse.

(prompt §Tools; C-ConvergentOntology; C-AcceptanceChecks; decision-candidates
§1 — tool:candidate provenance lane + acceptance mint + endorse/discredit)

Tools are persistently identifiable capabilities: a definition with purpose,
inputs, expected results, acceptance tests, and required/optional values.
Definitions are DATA (tool-as-data DSL): `logic` is an ordered list of
`component.verb` steps over a closed primitive set.

Every definition carries an inline explanation readable without corpus
knowledge (V-C bar): `explain` = what the tool is for + what invoking does.

Candidate lane (decision-candidates §1):
- foreign/model definitions land as `tool:candidate` rows — NEVER live
- `tool.mint` is the acceptance act: minting against a candidate preserves
  provenance in basis.meta; direct mint = self-authored
- `tool:endorse` / `tool:discredit` are meta-assertions about a tool subject
  that travel in exchange bundles and inherit source confidence
"""
from __future__ import annotations

import json
import re
import urllib.request

from . import rows

# ---------------------------------------------------------------------------
# The tool definitions — tool-as-data. `explain` is the V-C contract.
BUILTIN_TOOLS = {
    "list-members": {
        "id": "list-members",
        "name": "List members of a set",
        "purpose": "Fill a list need (topic+criteria) with defensible members.",
        "explain": "Specialized set retrieval: pulls the topic's roster page "
                   "from a configured source, classifies each entry against the "
                   "stated criteria (member shape), records non-matches for "
                   "review, and appends members to the list need. Invoking it "
                   "with {topic, criteria} performs one retrieval pass.",
        "slots": {"topic": "required", "criteria": "required",
                  "source": "optional"},
        "requiresGrant": False,
        "logic": [
            {"step": "wikipedia.extract", "args": {"topic": "$topic"}},
            {"step": "filter.members", "args": {"shape": "$criteria"}},
            {"step": "result.card", "args": {"kind": "list"}},
        ],
    },
    "retrieve-table": {
        "id": "retrieve-table",
        "name": "Table-based set retrieval",
        "purpose": "Competing approach to set fulfillment: parse list tables.",
        "explain": "Competing tool for set.members: reads an HTML table on the "
                   "topic's roster page and takes the member column. Different "
                   "evidence than link-classification — the local comparison "
                   "runner (compare) scores both on the same need.",
        "slots": {"topic": "required", "criteria": "required"},
        "requiresGrant": False,
        "logic": [
            {"step": "wikipedia.extract", "args": {"topic": "$topic", "mode": "table"}},
            {"step": "filter.members", "args": {"shape": "$criteria"}},
            {"step": "result.card", "args": {"kind": "list"}},
        ],
    },
    "search-web": {
        "id": "search-web",
        "name": "General web search",
        "purpose": "Broad retrieval when no specialized list source exists.",
        "explain": "Queries the general web-search source for the topic and "
                   "returns ranked result titles/snippets as candidates. "
                   "Competes with specialized retrieval; usually lower "
                   "confidence for set enumeration.",
        "slots": {"topic": "required"},
        "requiresGrant": False,
        "logic": [
            {"step": "web.search", "args": {"query": "$topic"}},
            {"step": "result.card", "args": {"kind": "candidates"}},
        ],
    },
    "evaluate-tool-candidate": {
        "id": "evaluate-tool-candidate",
        "name": "Evaluate an imported/model tool candidate",
        "purpose": "Render a foreign tool definition legible before acceptance.",
        "explain": "Reads the tool:candidate row plus trust context "
                   "(source trust class, endorse/discredit rows), asks the "
                   "local LLM for a plain-language summary, and emits a result "
                   "card with mechanical flags extracted without the model "
                   "(components used, requiresGrant, slot surface). Engine "
                   "offline → honest stub card, no fabricated verdict.",
        "slots": {"candidate": "required"},
        "requiresGrant": False,
        "logic": [
            {"step": "ledger.search", "args": {"predicate": "tool:candidate"}},
            {"step": "ledger.search", "args": {"predicate": "tool:endorse"}},
            {"step": "ledger.search", "args": {"predicate": "tool:discredit"}},
            {"step": "engine.invoke",
             "args": {"engine": "llm", "method": "complete",
                      "role": "classify", "task": "evaluate-candidate"}},
            {"step": "result.card", "args": {"kind": "evaluation"}},
        ],
    },
    "send-email": {
        "id": "send-email",
        "name": "Send an email through a configured account",
        "purpose": "Deliver a drafted message via the configured mail account.",
        "explain": "Grant-gated nonlocal effect: requires a witnessed "
                   "send-mail grant AND a configured account connector. With "
                   "no configured account it honestly defers (status recorded) "
                   "rather than fabricating delivery.",
        "slots": {"to": "required", "subject": "required", "body": "required"},
        "requiresGrant": True,
        "logic": [
            {"step": "outbox.send", "args": {"channel": "email"}},
            {"step": "result.card", "args": {"kind": "receipt"}},
        ],
    },
    "publish-external": {
        "id": "publish-external",
        "name": "Publish to an external channel",
        "purpose": "Post content to a nonlocal publication surface.",
        "explain": "Grant-gated nonlocal effect: needs a witnessed publish "
                   "grant plus a configured publish connector. Unconfigured → "
                   "honest deferral recorded with its status.",
        "slots": {"body": "required"},
        "requiresGrant": True,
        "logic": [
            {"step": "outbox.send", "args": {"channel": "publish"}},
            {"step": "result.card", "args": {"kind": "receipt"}},
        ],
    },
    "drain-request": {
        "id": "drain-request",
        "name": "Drain an unmet request",
        "purpose": "Attempt to serve a need:request no classifier matched.",
        "explain": "Steward path for captured asks: reclassify → trusted-"
                   "source search → tool:candidate path → ask-the-user card. "
                   "Records which leg produced the resolution.",
        "slots": {"ask": "required"},
        "requiresGrant": False,
        "logic": [
            {"step": "engine.invoke",
             "args": {"engine": "llm", "method": "complete",
                      "role": "classify", "task": "reclassify-request"}},
            {"step": "web.search", "args": {"query": "$ask"}},
            {"step": "result.card", "args": {"kind": "drain"}},
        ],
    },
}

# ---------------------------------------------------------------------------
class ToolRegistry:
    """Live catalog + candidate lane. The live registry is populated ONLY by
    the acceptance mint — candidates never self-register."""

    def __init__(self, book, floor):
        self.book = book
        self.floor = floor
        self.live: dict[str, dict] = {}      # id -> definition (live)
        for tid, d in BUILTIN_TOOLS.items():
            self.live[tid] = dict(d)

    # ---- mint --------------------------------------------------------------
    def mint(self, definition: dict, claimant="principal",
             accepted_from: str = "") -> dict:
        """The acceptance act (decision-candidates §1 item 2).
        accepted_from names the tool:candidate row being accepted; provenance
        survives into basis.meta. Direct mint = self-authored (workshop save)."""
        tid = definition["id"]
        self.live[tid] = definition
        if self.floor.arg_requirements is not None:
            self.floor.arg_requirements[tid] = [
                s for s, req in (definition.get("slots") or {}).items()
                if req == "required"]
        meta = {"origin": {"kind": "author"}}
        if accepted_from:
            cand = self.book.get(accepted_from)
            origin = {}
            if cand:
                origin = cand.get("meta", {}).get("origin", {})
            meta = {"acceptedFrom": accepted_from, "origin": origin}
        self.book.claim(tid, "tool:exists", {"id": tid, "name": definition.get("name", tid)},
                        claimant=claimant, certainty=1.0, basis="durable-result",
                        meta=meta)
        self.book.claim(tid, "tool:definition", definition,
                        claimant=claimant, certainty=1.0, basis="durable-result",
                        meta=meta)
        return {"minted": tid, "acceptedFrom": accepted_from or None}

    def stage_candidate(self, definition: dict, origin: dict) -> dict:
        """Foreign/model definitions stage as candidates, never live
        (decision-candidates §1 item 1)."""
        cert = {"import": 0.4, "model": 0.5, "author": 0.9}.get(
            origin.get("kind", "import"), 0.4)
        claimant = {"import": f"source:{origin.get('sourceKey', 'exchange')}",
                    "model": f"model:{origin.get('modelId', 'llm')}",
                    "author": "principal"}.get(origin.get("kind", "import"),
                                               "source:exchange")
        return self.book.claim(
            definition["id"], "tool:candidate",
            {"definition": definition, "status": "staged"},
            claimant=claimant, certainty=cert, basis="import",
            meta={"origin": origin})

    def candidates(self) -> list[dict]:
        return [r for r in self.book.find(predicate="tool:candidate")
                if r["value"]["v"].get("status") == "staged"]

    def endorse(self, tool_id: str, positive: bool, claimant="principal",
                note="") -> dict:
        """tool:endorse / tool:discredit — claim-level meta-assertions that
        travel inside exchange bundles and inherit source confidence."""
        return self.book.claim(
            tool_id, "tool:endorse" if positive else "tool:discredit",
            {"note": note}, claimant=claimant,
            certainty=1.0 if claimant == "principal" else 0.6,
            basis="user-choice" if claimant == "principal" else "interpretation")

    # ---- definition loading ------------------------------------------------
    def load_minted(self):
        for r in self.book.find(predicate="tool:definition"):
            d = r["value"]["v"]
            if isinstance(d, dict) and d.get("id"):
                self.live[d["id"]] = d

    # ---- execution -----------------------------------------------------------
    def invoke(self, tool_id: str, args: dict, ctx) -> dict:
        """Run a definition's declarative logic. ctx carries engines, ledger,
        floor, grants — the primitive implementations live in host.py."""
        dfn = self.live.get(tool_id)
        if not dfn:
            return {"ok": False, "error": f"unknown tool: {tool_id}"}
        if dfn.get("requiresGrant") and not ctx.grants.has(tool_id):
            return {"ok": False, "error": "grant-required",
                "deferred": True,
                "status": "no witnessed grant — request recorded, not executed"}
        env = dict(args)
        last = None
        trace = []
        for spec in dfn.get("logic", []):
            comp, _, verb = spec["step"].partition(".")
            call_args = {k: self._sub(v, env) for k, v in spec.get("args", {}).items()}
            last = ctx.primitives.run(comp, verb, call_args, env, ctx)
            trace.append({"step": spec["step"], "ok": bool(last and last.get("ok", True))})
            if last and last.get("env"):
                env.update(last["env"])
            if last and last.get("stop"):
                break
        return {"ok": True, "tool": tool_id, "trace": trace,
                "result": last, "env": {k: v for k, v in env.items()
                                        if not k.startswith("_")}}

    def _sub(self, v, env):
        if isinstance(v, str) and v.startswith("$"):
            return env.get(v[1:], v)
        return v

    def describe(self, tool_id: str) -> dict:
        d = self.live.get(tool_id)
        if not d:
            return {}
        return {"id": d["id"], "name": d["name"], "purpose": d["purpose"],
                "explain": d["explain"], "slots": d["slots"],
                "requiresGrant": d.get("requiresGrant", False)}
