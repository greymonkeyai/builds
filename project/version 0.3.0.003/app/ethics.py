"""Ethics gate (C-EthicsGate — the machinery beneath the prompt-specified
imitation mark, §Personalities).

Depth over the mark alone:
- **liveness research** — the gate looks the subject up through the configured
  wikipedia connector and classifies living / deceased / unclear from the
  returned summary evidence (never guesses silently: unclear is a real verdict
  that still requires the mark when the claimed recency is living/recent).
- **objection/compliance flow** — `maxim:objection` assertions (seeded or
  user-authored patterns like "no imitations of active politicians") are
  checked; a matching objection changes the verdict to refused, which is a
  recorded refusal, not silent non-action.
- **gate cards** — every evaluation emits an `ethics-gate` bus card for the
  surfaces and an `ethics:gate` ledger assertion with verdict + evidence.
- **compliance** — a mint whose verdict requires the mark proceeds only with
  admonishment + permanent mark; a refused mint does not proceed and the need
  is recorded deferred/refused.
"""
from __future__ import annotations

import re
from typing import Optional

from . import connectors
from .model import now_ms

# recency classes requiring admonishment + permanent mark (prompt §Personalities)
_MARKED = ("living", "deceased-10y")


def liveness_research(ctx, name: str) -> dict:
    """Research the subject through the wikipedia connector; classify from
    real summary evidence."""
    r = connectors.wiki_summary(name)
    if not r["ok"]:
        return {"verdict": "unclear", "evidence": f"lookup failed: {r.get('error')}",
                "reachable": False}
    ex = r.get("extract") or ""
    death = re.search(r"\b(?:died|death)\b.*?(\b1[89]\d{2}|20[0-2]\d)", ex)
    born = re.search(r"born[^.;]{0,60}?(\b1[89]\d{2}|20[0-2]\d)", ex)
    if death or re.search(r"\bwas an? ", ex):
        return {"verdict": "deceased", "evidence": ex[:240],
                "deathYear": int(death.group(1)) if death else None,
                "reachable": True, "title": r.get("title")}
    if born or re.search(r"\bis an? ", ex):
        return {"verdict": "living", "evidence": ex[:240],
                "birthYear": int(born.group(1)) if born else None,
                "reachable": True, "title": r.get("title")}
    return {"verdict": "unclear", "evidence": ex[:240] or "empty summary",
            "reachable": True, "title": r.get("title")}


def objections(ctx, name: str) -> list[dict]:
    """maxim:objection assertions act as user-authored prohibition patterns."""
    hits = []
    for a in ctx.ledger.query(predicate="maxim:objection"):
        v = a.value["v"]
        pat = v.get("pattern", "") if isinstance(v, dict) else str(v)
        if pat and re.search(pat, name, re.I):
            hits.append({"pattern": pat,
                         "note": v.get("note") if isinstance(v, dict) else None,
                         "assertionId": a.id})
    return hits


def evaluate(ctx, name: str, imitates: Optional[dict],
             claimant: str = "principal") -> dict:
    """Run the gate for a proposed persona. Returns the verdict dict; every
    evaluation is recorded (ethics:gate) and carded (ethics-gate)."""
    if not imitates:
        verdict = {"verdict": "allowed", "subject": name,
                   "reasons": ["no imitation claimed"]}
        _record(ctx, name, verdict)
        return verdict
    iname = imitates.get("name", "")
    recency = imitates.get("recency", "living")
    obs = objections(ctx, iname)
    live = (liveness_research(ctx, iname)
            if recency in _MARKED + ("deceased-older",)
            else {"verdict": "n/a",
                  "evidence": "fictional subject -- no liveness check"})
    reasons = []
    if obs:
        verdict = "refused"
        reasons.append(f"objection match: {obs[0]['pattern']} — {obs[0].get('note') or 'no note'}")
    elif recency in _MARKED:
        verdict = "admonish-required"
        reasons.append(f"imitates a person ({recency}); admonishment + permanent "
                       f"distinguishing mark required by prompt §Personalities")
        if live.get("verdict") == "deceased":
            reasons.append(f"liveness research suggests deceased "
                           f"({live.get('evidence','')[:80]}…) — recency class kept as claimed")
        elif live.get("verdict") == "living":
            reasons.append("liveness research corroborates living subject")
        else:
            reasons.append(f"liveness unclear ({live.get('evidence','')[:80]}) — "
                           f"claimed recency treated conservatively")
    elif recency == "deceased-older":
        verdict = "mark-required"
        reasons.append("imitates a person deceased >10y; mark required, "
                       "admonishment not mandated")
    else:
        verdict = "allowed"
        reasons.append("fictional/unclaimed subject")
    verdict = {"verdict": verdict, "subject": name, "imitates": iname,
               "recency": recency, "reasons": reasons,
               "liveness": live, "objections": obs}
    _record(ctx, name, verdict)
    return verdict


def _record(ctx, name: str, verdict: dict):
    ctx.append("ethics", "ethics:gate",
               {"subject": name, **verdict, "at": now_ms()},
               "system", basis={"kind": "durable-result"})
    ctx.emit("card", {"kind": "ethics-gate",
                      "summary": f"ethics gate: {verdict['verdict']} — "
                                 f"{name}" + (f" (imitates {verdict.get('imitates')})"
                                              if verdict.get('imitates') else ""),
                      "verdict": verdict["verdict"],
                      "reasons": verdict["reasons"],
                      "at": now_ms()})
