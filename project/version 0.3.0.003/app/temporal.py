"""Calendar temporal reasoning (prompt §Projects and temporal context — F2).

Calendar entries remain source evidence; this module computes the temporal
view the prompt requires to *inform* project work, persona responses, and
background attention:

- upcoming / current / recent interpretation of calendar:event evidence
- project linkage: open projects matched to events by criteria tokens, and
  project deadlines (project:due) compared against the horizon
- steward attention: temporal findings become offers presented through a
  personality (the background-attention channel)
- persona composition: respondents whose lens touches time/calendar are given
  the live temporal context so their replies can cite it
"""
from __future__ import annotations

import re
from typing import Optional

from .model import now_ms

DAY = 86400000


def events(ctx, led=None) -> list[dict]:
    out = []
    for a in (led or ctx.ledger).query(predicate="calendar:event"):
        v = dict(a.value["v"])
        v["assertionId"] = a.id
        out.append(v)
    out.sort(key=lambda e: e.get("startMs", 0))
    return out


def temporal_context(ctx, now: Optional[int] = None,
                     horizon_ms: int = 7 * DAY, led=None) -> dict:
    """Interpret calendar evidence into date-respecting classes: current /
    upcoming (inside horizon) / future (beyond horizon) / recent (ended inside
    horizon) / historical (ended beyond it). A future-dated event is never
    'recent' — the classification respects the date, not the fixture."""
    now = now or now_ms()
    led = led or ctx.ledger
    upcoming, current, recent, future, historical = [], [], [], [], []
    for e in events(ctx, led=led):
        s, en = e.get("startMs", 0), e.get("endMs", 0) or e.get("startMs", 0)
        if s <= now <= (en or s + 3600000):
            current.append(e)
        elif now < s <= now + horizon_ms:
            upcoming.append(e)
        elif s > now + horizon_ms:
            future.append(e)
        elif en and 0 <= now - en <= horizon_ms:
            recent.append(e)
        elif en and now - en > horizon_ms:
            historical.append(e)
    return {"now": now, "horizonMs": horizon_ms,
            "current": current, "upcoming": upcoming, "future": future,
            "recent": recent, "historical": historical,
            "count": {"current": len(current), "upcoming": len(upcoming),
                      "future": len(future), "recent": len(recent),
                      "historical": len(historical)}}


def _tokens(text: str) -> set:
    return set(re.findall(r"[a-z0-9']+", (text or "").lower()))


def linkable(ctx, project: dict, window_ms: int = 30 * DAY) -> list[dict]:
    """Events related to a project's title/goals by token overlap, within a
    bounded window around now."""
    now = now_ms()
    ptoks = _tokens((project.get("title") or "") + " " +
                    " ".join(g.get("text", g) if isinstance(g, dict) else str(g)
                             for g in (project.get("goals") or [])))
    ptoks -= {"a", "the", "to", "of", "in", "for", "and", "project"}
    hits = []
    for e in events(ctx):
        if not ptoks:
            break
        s = e.get("startMs", 0)
        if abs(s - now) > window_ms:
            continue
        etoks = _tokens(e.get("title", ""))
        if ptoks & etoks:
            hits.append({**e, "matched": sorted(ptoks & etoks)})
    return hits


def note_for_persona(ctx, persona: dict, user_text: str,
                     led=None) -> Optional[str]:
    """A persona-level temporal note when the persona's lens touches time or
    the user asks about schedule/upcoming events."""
    text_toks = _tokens(user_text)
    lens_toks = set()
    for k in (persona.get("interests") or []) + (persona.get("traits") or []):
        lens_toks |= _tokens(k)
    resp = (persona.get("lens") or {}).get("responsibilities") or []
    for r in resp:
        lens_toks |= _tokens(r)
    temporal_lens = bool(lens_toks & {"calendar", "time", "schedule", "temporal",
                                      "attention", "deadline", "reminder",
                                      "notifications", "stewardship"})
    temporal_ask = bool(text_toks & {"when", "calendar", "schedule", "upcoming",
                                     "today", "tomorrow", "deadline", "week",
                                     "soon", "date", "remind"})
    if not (temporal_lens or temporal_ask):
        return None
    ctxv = temporal_context(ctx, horizon_ms=3 * DAY, led=led)
    if not (ctxv["current"] or ctxv["upcoming"]):
        return None
    bits = [f"{e['title']} ({_fmt(e.get('startMs'))})" for e in
            (ctxv["current"] + ctxv["upcoming"])[:3]]
    note = "Temporal context from the ledger calendar: " + "; ".join(bits)
    if led is None:  # snapshot reads never write
        ctx.append(f"persona:{persona['id']}", "persona:temporal-note",
                   {"note": note, "events": [e["assertionId"] for e in
                                             (ctxv["current"] + ctxv["upcoming"])[:3]]},
                   "system", basis={"kind": "interpretation"})
    return note


def _fmt(ms: int) -> str:
    import datetime as dt
    if not ms:
        return "?"
    return dt.datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d %H:%M")


def steward_attention(ctx) -> dict:
    """Background-attention duty: interpret the calendar into findings and
    present the relevant ones through a distinct personality (prompt §Background
    activity and attention; demo 6 channel)."""
    ctxv = temporal_context(ctx, horizon_ms=72 * 3600 * 1000)
    findings = []
    # (a) upcoming/current events the user should hear about
    for e in (ctxv["current"] + ctxv["upcoming"])[:5]:
        findings.append({"kind": "calendar", "event": e})
    # (b) projects with deadlines inside the horizon, or linked events coming due
    for pa in ctx.ledger.query(predicate="project:exists"):
        pid = pa.subjectKey.split(":", 1)[1]
        subj = pa.subjectKey
        due_rows = ctx.ledger.query(subject=subj, predicate="project:due")
        due = due_rows[-1].value["v"] if due_rows else None
        if due and now_ms() <= due <= now_ms() + 72 * 3600 * 1000:
            findings.append({"kind": "project-due", "projectId": pid,
                             "title": pa.value["v"].get("title"), "dueMs": due})
        proj = {"title": pa.value["v"].get("title"), "goals":
                [r.value["v"] for r in ctx.ledger.query(subject=subj,
                                                      predicate="project:goal")]}
        for hit in linkable(ctx, proj, window_ms=14 * DAY):
            already = [r for r in ctx.ledger.query(subject=subj,
                                                   predicate="calendar:linked")
                       if r.value["v"] == hit["assertionId"]]
            if not already:
                ctx.append(subj, "calendar:linked", hit["assertionId"],
                           "steward:main", certainty=0.8,
                           basis={"kind": "interpretation"},
                           relates=[hit["assertionId"]])
                findings.append({"kind": "project-event-link",
                                 "projectId": pid, "title": proj["title"],
                                 "event": hit})
    ctx.append("temporal", "temporal:attention",
               {"findings": findings, "contextCount": ctxv["count"]},
               "steward:main", basis={"kind": "execution"})
    return {"findings": findings, "context": ctxv["count"]}


def present_attention(ctx, findings: list) -> Optional[dict]:
    """Offer the steward's temporal findings to a persona whose lens fits —
    completed background work surfaced as a relevant result (demo 6)."""
    if not findings:
        return None
    roster = ctx.personas.roster()
    if not roster:
        return None
    # pick the persona whose interests/responsibilities overlap time/attention
    best, best_n = None, -1
    for p in roster:
        toks = set()
        for k in (p.get("interests") or []) + (p.get("traits") or []):
            toks |= _tokens(k)
        for r in (p.get("lens") or {}).get("responsibilities") or []:
            toks |= _tokens(r)
        n = len(toks & {"calendar", "time", "attention", "stewardship",
                        "temporal", "opportunities", "notifications", "schedule"})
        if n > best_n:
            best, best_n = p, n
    p = best or roster[0]
    lines = []
    for f in findings[:4]:
        if f["kind"] == "calendar":
            lines.append(f"event: {f['event'].get('title')} at {_fmt(f['event'].get('startMs'))}")
        elif f["kind"] == "project-due":
            lines.append(f"project '{f['title']}' is due at {_fmt(f['dueMs'])}")
        else:
            lines.append(f"project '{f['title']}' relates to event "
                         f"'{f['event'].get('title')}' at {_fmt(f['event'].get('startMs'))}")
    text = ("Stewardship pass — temporal attention: " + "; ".join(lines) +
            ". Evidence is in the ledger (calendar:event, project:due, calendar:linked).")
    card = ctx.invoke("persona.speak",
                      {"personaId": p["id"], "text": text,
                       "cause": "stewardship-temporal", "engine": "temporal"})
    return {"persona": p["name"], "text": text, "card": card.get("result")}
