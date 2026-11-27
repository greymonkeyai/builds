"""Quorum temporal interpretation — calendar events as source evidence.

(prompt §Projects and temporal context; F2 carried finding — calendar must
inform projects, persona responses, and background attention, not just
ingest.) Events are bucketed upcoming/current/recent/historical and fed to
project work and persona grounds.
"""
from __future__ import annotations

import re
import time
from datetime import datetime, timezone, timedelta

def _parse_dt(v: str) -> float | None:
    if not v:
        return None
    v = v.strip()
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%dT%H%M%S", "%Y%m%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(v, fmt).replace(tzinfo=timezone.utc).timestamp()
        except ValueError:
            continue
    m = re.match(r"(\d{8}T\d{6})([+-]\d{4})", v)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y%m%dT%H%M%S") \
                .replace(tzinfo=timezone.utc).timestamp()
        except ValueError:
            return None
    return None

def bucket(events: list[dict], now: float | None = None) -> dict:
    now = now or time.time()
    day = 86400
    out = {"current": [], "upcoming": [], "recent": [], "historical": [],
           "far-future": []}
    for e in events:
        start = _parse_dt(e.get("dtstart", "")) or 0
        end = _parse_dt(e.get("dtend", "")) or start
        e2 = dict(e, start_ts=start, end_ts=end)
        if start <= now <= end:
            out["current"].append(e2)
        elif start > now:
            out["upcoming" if start - now < 30 * day else "far-future"].append(e2)
        else:
            out["recent" if now - end < 30 * day else "historical"].append(e2)
    for k in out:
        out[k].sort(key=lambda e: e.get("start_ts", 0))
    return out

def persona_grounds(bucketed: dict, limit: int = 4) -> list[str]:
    """Temporal grounds a persona can cite — upcoming/current first."""
    g = []
    for b in ("current", "upcoming"):
        for e in bucketed.get(b, [])[:limit]:
            g.append(f"calendar:{b} '{e.get('summary','')}' "
                     f"at {e.get('dtstart','')}")
    return g
