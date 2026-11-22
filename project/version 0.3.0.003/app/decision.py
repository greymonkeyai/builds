"""Bounded decision model for routing and evaluation (shortcoming A9).

GreyAvatar routed intent with regex-only deterministic matching. Meridian adds
a bounded parametric model: a fixed feature vector per candidate, scored by a
weighted sum whose weights live in the ledger as configurable assertions.
Bounded means: fixed feature count, O(#candidates x #features) per decision,
no unbounded inference, deterministic given the ledger, and fully inspectable
through routing:decision-trace rows.

Tool-trust churn (A5 / D-ToolTrustChurn): an insufficient, failed, stale,
conflicting, or malformed result lowers a tool's rank multiplier among
alternatives — bounded in [0.1, 1.0] — without crossing confidence thresholds
or making the tool ineligible. Successes recover the multiplier gradually.
"""
from __future__ import annotations

import math
import re
import time
from typing import Optional

TOKEN = re.compile(r"[a-z0-9']+")


def _tokens(text: str) -> set[str]:
    return set(TOKEN.findall((text or "").lower()))


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


class DecisionModel:
    TOOL_FEATURES = ["keyword", "pattern", "slot_fill", "success_rate",
                     "rank_mult", "recency", "source_conf"]
    DEFAULT_TOOL_WEIGHTS = {"keyword": 0.28, "pattern": 0.30, "slot_fill": 0.12,
                            "success_rate": 0.10, "rank_mult": 0.14,
                            "recency": 0.03, "source_conf": 0.03}
    PERSONA_FEATURES = ["lens_overlap", "topic_link", "confidence", "priority"]
    DEFAULT_PERSONA_WEIGHTS = {"lens_overlap": 0.40, "topic_link": 0.25,
                               "confidence": 0.20, "priority": 0.15}
    RANK_FLOOR, RANK_CEIL = 0.1, 1.0

    def __init__(self, ctx):
        self.ctx = ctx

    # ---- weights (configurable, ledger-resident) ----

    def weights(self, kind: str = "tool") -> dict:
        rows = self.ctx.ledger.query(subject=f"decision:{kind}",
                                     predicate="decision:weights")
        if rows:
            w = dict(rows[-1].value["v"])
            base = self.DEFAULT_TOOL_WEIGHTS if kind == "tool" else self.DEFAULT_PERSONA_WEIGHTS
            base.update({k: float(v) for k, v in w.items() if k in base})
            return base
        return dict(self.DEFAULT_TOOL_WEIGHTS if kind == "tool"
                    else self.DEFAULT_PERSONA_WEIGHTS)

    def set_weights(self, kind: str, w: dict, claimant: str = "principal"):
        self.ctx.append(f"decision:{kind}", "decision:weights", w, claimant,
                        basis={"kind": "config"})

    # ---- tool scoring ----

    def tool_features(self, tool: dict, text: str, slots_ready: float,
                      source_conf: float) -> dict:
        toks = _tokens(text)
        kw = set()
        for k in (tool.get("triggers", {}).get("keywords") or []):
            kw |= _tokens(k)
        f_keyword = _jaccard(toks, kw) if kw else 0.0
        if kw and kw <= toks:
            f_keyword = max(f_keyword, 0.9)  # full keyword cover
        f_pattern = 0.0
        for p in (tool.get("triggers", {}).get("patterns") or []):
            if re.search(p, text or "", re.I):
                f_pattern = 1.0
                break
        # durable intent overrides authored by the user count as pattern signal
        for a in self.ctx.ledger.query(predicate="routing:intent-override"):
            v = a.value["v"]
            if v.get("toolId") == tool["id"] and re.search(
                    v.get("pattern", r"$^"), text or "", re.I):
                f_pattern = max(f_pattern, float(v.get("confidence", 0.95)))
        f_slot = max(0.0, min(1.0, slots_ready))
        f_success = self.success_rate(tool["id"])
        f_rank = self.rank_multiplier(tool["id"])
        last = self._last_success(tool["id"])
        f_recency = math.exp(-(time.time() * 1000 - last) / 8.64e7) if last else 0.0
        return {"keyword": round(f_keyword, 4), "pattern": f_pattern,
                "slot_fill": round(f_slot, 4), "success_rate": round(f_success, 4),
                "rank_mult": round(f_rank, 4), "recency": round(f_recency, 4),
                "source_conf": round(source_conf, 4)}

    def score_tool(self, tool: dict, text: str, slots_ready: float = 1.0,
                   source_conf: float = 1.0) -> dict:
        feats = self.tool_features(tool, text, slots_ready, source_conf)
        w = self.weights("tool")
        score = sum(feats[f] * w[f] for f in self.TOOL_FEATURES)
        return {"toolId": tool["id"], "score": round(score, 4),
                "features": feats, "weights": w}

    def rank_tools(self, text: str, kind_filter: Optional[str] = None,
                   trace: bool = True) -> list[dict]:
        cands = []
        for t in self.ctx.registry.tools():
            if kind_filter and t.get("lane") != kind_filter:
                continue
            cands.append(self.score_tool(t, text))
        cands.sort(key=lambda c: c["score"], reverse=True)
        if trace:
            self.ctx.append("decision:tool", "decision:score",
                            {"input": text[:200],
                             "ranking": [{"toolId": c["toolId"], "score": c["score"]}
                                         for c in cands[:8]],
                             "top": cands[0] if cands else None},
                            "model:decision", certainty=0.9,
                            basis={"kind": "interpretation"})
        return cands

    # ---- persona (respondent) scoring ----

    def rank_personas(self, personas: list[dict], text: str,
                      topic_links: Optional[dict] = None,
                      trace: bool = True) -> list[dict]:
        toks = _tokens(text)
        w = self.weights("persona")
        out = []
        for p in personas:
            lens = set()
            for k in (p.get("interests") or []) + (p.get("traits") or []):
                lens |= _tokens(k)
            f_lens = _jaccard(toks, lens)
            f_topic = float((topic_links or {}).get(p["id"], 0.0))
            f_conf = float(p.get("confidence", 0.8))
            f_prio = float(p.get("rosterPriority", 0.5))
            feats = {"lens_overlap": round(f_lens, 4), "topic_link": f_topic,
                     "confidence": f_conf, "priority": f_prio}
            score = sum(feats[f] * w[f] for f in self.PERSONA_FEATURES)
            out.append({"personaId": p["id"], "score": round(score, 4),
                        "features": feats})
        out.sort(key=lambda c: c["score"], reverse=True)
        if trace:
            self.ctx.append("decision:persona", "decision:respondent",
                            {"input": text[:200], "ranking": out}, "model:decision",
                            certainty=0.9, basis={"kind": "interpretation"})
        return out

    # ---- outcome feedback / trust churn ----

    def success_rate(self, tool_id: str) -> float:
        rows = self.ctx.ledger.query(subject=f"tool:{tool_id}",
                                     predicate="tool:telemetry", limit=20)
        if not rows:
            return 0.5
        ok = sum(1 for r in rows if r.value["v"].get("status") == "ok")
        return ok / len(rows)

    def _last_success(self, tool_id: str) -> int:
        rows = [r for r in self.ctx.ledger.query(
            subject=f"tool:{tool_id}", predicate="tool:telemetry", limit=40)
            if r.value["v"].get("status") == "ok"]
        return rows[-1].at if rows else 0

    def rank_multiplier(self, tool_id: str) -> float:
        rows = self.ctx.ledger.query(subject=f"tool:{tool_id}",
                                     predicate="tool:rank-adjustment")
        if not rows:
            return 1.0
        return max(self.RANK_FLOOR, min(self.RANK_CEIL,
                                        float(rows[-1].value["v"]["multiplier"])))

    def record_outcome(self, tool_id: str, need_id: Optional[str],
                       ok: bool, adequate: bool):
        """Churn: inadequate/failed results lower rank among alternatives; the
        tool stays eligible (multiplier bounded, never removed)."""
        cur = self.rank_multiplier(tool_id)
        if ok and adequate:
            new = min(self.RANK_CEIL, cur * 1.05)
            if new > cur:
                self.ctx.append(f"tool:{tool_id}", "tool:rank-adjustment",
                                {"multiplier": round(new, 4), "reason": "success-recovery",
                                 "needId": need_id}, "model:decision",
                                basis={"kind": "execution"})
        else:
            new = max(self.RANK_FLOOR, cur * 0.9)
            self.ctx.append(f"tool:{tool_id}", "tool:rank-adjustment",
                            {"multiplier": round(new, 4),
                             "reason": "insufficient-result" if ok else "failure",
                             "needId": need_id}, "model:decision",
                            basis={"kind": "execution"})
            self.ctx.append("decision:churn", "decision:churn",
                            {"toolId": tool_id, "needId": need_id,
                             "from": cur, "to": round(new, 4)},
                            "model:decision", basis={"kind": "execution"})
