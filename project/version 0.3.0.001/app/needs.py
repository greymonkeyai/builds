"""Unfulfilled requirements (needs) — operational ledger assertions.

A need is created with missing, partial, or competing candidates; creation
does not imply execution. A need remains Open until its declared satisfaction
conditions are met, or it is Cancelled or Superseded. Refinement is expressed
through related assertions, never by rewriting the requirement.
"""
from __future__ import annotations

from typing import Optional

from .model import new_id, now_ms


def need_subject(nid: str) -> str:
    return f"need:{nid}"


def open_need(ctx, kind: str, spec: dict, claimant: str = "system",
              relates: Optional[list] = None, certainty: float = 1.0) -> str:
    """Create an unfulfilled requirement. spec: {summary, template?, slots?,
    satisfaction, toolId?, project?, deferred?}."""
    nid = new_id("need")
    ctx.append(need_subject(nid), "need:open",
               {"kind": kind, "status": "open", "spec": spec, "openedAt": now_ms()},
               claimant, certainty=certainty,
               basis={"kind": "interpretation"}, relates=relates or [])
    return nid


def add_candidate(ctx, nid: str, slot: str, value, confidence: float,
                  source: str, claimant: str = "system") -> str:
    a = ctx.append(need_subject(nid), "need:candidate",
                   {"slot": slot, "value": value, "confidence": confidence,
                    "source": source},
                   claimant, certainty=confidence,
                   basis={"kind": "source-evidence", "ref": source})
    return a.id


def refine_need(ctx, nid: str, note: str, claimant: str = "principal",
                extra: Optional[dict] = None) -> str:
    """Refine an existing requirement's criteria via a related assertion."""
    v = {"note": note}
    if extra:
        v.update(extra)
    return ctx.append(need_subject(nid), "need:refined", v, claimant,
                      basis={"kind": "user-choice"}).id


def defer_need(ctx, nid: str, reason: str, missing: list,
               claimant: str = "system") -> str:
    return ctx.append(need_subject(nid), "need:deferred",
                      {"reason": reason, "missing": missing}, claimant,
                      basis={"kind": "execution"}).id


def close_need(ctx, nid: str, outcome: str, detail: dict,
               claimant: str = "system") -> Optional[str]:
    """Close a need: outcome in fulfilled|cancelled|superseded. Supersedes the
    open row; the need leaves the floor."""
    open_row = _open_row(ctx, nid)
    pred = {"fulfilled": "need:fulfilled", "cancelled": "need:cancelled",
            "superseded": "need:superseded"}.get(outcome)
    if not pred:
        raise ValueError(f"bad outcome: {outcome}")
    a = ctx.append(need_subject(nid), pred,
                   {"status": outcome, "detail": detail, "closedAt": now_ms()},
                   claimant, basis={"kind": "durable-result"},
                   supersedes=open_row.id if open_row else None)
    return a.id


def _open_row(ctx, nid: str):
    rows = ctx.ledger.query(subject=need_subject(nid), predicate="need:open")
    return rows[-1] if rows else None


def is_open(ctx, nid: str) -> bool:
    return _open_row(ctx, nid) is not None


def open_needs(ctx, kind: Optional[str] = None) -> list[dict]:
    """All live open needs on the floor."""
    out = []
    for a in ctx.ledger.query(predicate="need:open"):
        nid = a.subjectKey.split(":", 1)[1]
        spec = a.value["v"].get("spec", {})
        k = a.value["v"].get("kind")
        if kind and k != kind:
            continue
        out.append({"id": nid, "kind": k, "spec": spec,
                    "openedAt": a.value["v"].get("openedAt"),
                    "claimant": a.claimant, "assertionId": a.id})
    return out


def candidates(ctx, nid: str) -> dict[str, list[dict]]:
    """Slot -> candidate list (inspectable: value, source, confidence)."""
    out: dict[str, list[dict]] = {}
    for a in ctx.ledger.query(subject=need_subject(nid), predicate="need:candidate"):
        v = a.value["v"]
        eff = ctx.ledger.effective_confidence(a)
        out.setdefault(v["slot"], []).append(
            {"value": v["value"], "confidence": v["confidence"], "source": v["source"],
             "effectiveConfidence": round(eff, 4), "assertionId": a.id, "at": a.at})
    for lst in out.values():
        lst.sort(key=lambda c: (c["effectiveConfidence"], c["at"]), reverse=True)
    return out


def need_state(ctx, nid: str) -> dict:
    subj = need_subject(nid)
    status = "open"
    detail = {}
    for pred, st in (("need:fulfilled", "fulfilled"),
                     ("need:cancelled", "cancelled"),
                     ("need:superseded", "superseded")):
        rows = ctx.ledger.query(subject=subj, predicate=pred)
        if rows:
            status, detail = st, rows[-1].value["v"].get("detail", {})
    open_row = _open_row(ctx, nid)
    spec = open_row.value["v"].get("spec", {}) if open_row else {}
    deferrals = [r.value["v"] for r in
                 ctx.ledger.query(subject=subj, predicate="need:deferred")]
    refinements = [r.value["v"] for r in
                   ctx.ledger.query(subject=subj, predicate="need:refined")]
    return {"id": nid, "status": status, "spec": spec, "detail": detail,
            "candidates": candidates(ctx, nid),
            "deferred": deferrals[-1] if deferrals else None,
            "refinements": refinements}
