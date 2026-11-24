"""Temporal interpretation — calendar events remain source evidence; their
interpretation is governed by the same ledger and authority rules.
Buckets: past / current / upcoming(horizon) / future(beyond horizon).
A far-future fixture is never 'recent'; a long-past one never 'upcoming'.
The steward's temporal-attention duty turns relevant findings into persona
presentations, preserving the ledger evidence.
"""
from __future__ import annotations
import datetime as dt
HORIZON_H = 96  # upcoming window in hours
def _parse_start(s: str):
    s = (s or "").strip()
    for fmt in ("%Y%m%dT%H%M%S", "%Y%m%dT%H%M%SZ", "%Y%m%d"):
        try:
            return dt.datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None
def classify(led, horizon_h=HORIZON_H):
    now = dt.datetime.now()
    out = {"current": [], "upcoming": [], "past": [], "future": []}
    for a in led.query(predicate="calendar:event", limit=400):
        ev = a.value.get("v") or {}
        start = _parse_start(ev.get("start", ""))
        if not start:
            out["past"].append({**ev, "when": "undated"})
            continue
        delta_h = (start - now).total_seconds() / 3600
        entry = {**ev, "start_dt": start.isoformat(timespec="minutes"),
                 "in_h": round(delta_h, 1), "source": a.claimant}
        if -2 <= delta_h <= 2:
            out["current"].append(entry)
        elif 2 < delta_h <= horizon_h:
            out["upcoming"].append(entry)
        elif delta_h > horizon_h:
            out["future"].append(entry)   # 2030 fixtures land here
        else:
            out["past"].append(entry)
    for k in out:
        out[k].sort(key=lambda e: e["in_h"])
    return out
def attention_scan(ctx):
    """Steward duty: surface a relevant temporal finding as a presentation
    opportunity through a lens-matched persona."""
    buckets = classify(ctx.ledger)
    relevant = buckets["current"] + buckets["upcoming"][:2]
    if not relevant:
        return {"ok": True, "findings": 0}
    led = ctx.ledger
    for ev in relevant:
        key = f"temporal:attention:{ev['summary'][:40]}"
        if led.query(predicate="temporal:attention", text=ev["summary"][:40],
                     limit=1):
            continue
        persona = ctx.personas.active()
        pname = persona["name"] if persona else "system"
        led.say("temporal", "temporal:attention",
                {"summary": ev["summary"], "when": ev.get("start_dt"),
                 "in_h": ev.get("in_h"), "presentAs": "opportunity",
                 "persona": pname},
                claimant="steward:temporal", certainty=0.8,
                basis={"kind": "interpretation"})
        ctx.bus.emit("offer", {
            "kind": "temporal",
            "text": f"{ev['summary']} — {ev.get('start_dt','')}",
            "persona": pname})
    return {"ok": True, "findings": len(relevant)}
