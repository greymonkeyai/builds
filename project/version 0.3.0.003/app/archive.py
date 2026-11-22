"""Conversation archive (C-ConversationArchive — per-turn archive + topic
segments).

The archive is a computed view over the ledger (not a second store): chat
turns are grouped into segments bounded by topic changes and clear-chat
markers. `archive:segment` summary assertions are emitted at segment
boundaries (end-topic / clear-chat / on demand) so the sealing is itself
ledger evidence.
"""
from __future__ import annotations

from .model import now_ms


def turns(ctx) -> list[dict]:
    """Per-turn archive rows: each user input with its persona responses and
    the needs it opened, in order."""
    rows = []
    pend = None
    for a in ctx.ledger.query():
        if a.predicate == "chat:user-message":
            if pend:
                rows.append(pend)
            pend = {"input": a.value["v"].get("text") if isinstance(a.value["v"], dict)
                    else a.value["v"], "at": a.at, "id": a.id,
                    "claimant": a.claimant, "responses": [], "needs": []}
        elif a.predicate == "chat:assistant-response" and pend is not None:
            v = a.value["v"]
            pend["responses"].append({"personaId": v.get("personaId"),
                                      "text": v.get("text"),
                                      "claimant": a.claimant, "at": a.at})
        elif a.predicate == "need:open" and pend is not None:
            pend["needs"].append({"needId": a.subjectKey.split(":", 1)[1],
                                  "kind": a.value["v"].get("kind"),
                                  "summary": (a.value["v"].get("spec") or {}).get("summary")})
    if pend:
        rows.append(pend)
    return rows


def segments(ctx) -> list[dict]:
    """Topic segments: groups of turns between topic changes and clear-chat
    boundaries."""
    segs = []
    cur = {"index": 1, "topic": None, "turns": [], "startAt": None,
           "boundary": "start"}
    cleared = {a.id: a for a in ctx.ledger.query(predicate="chat:cleared")}
    topic_rows = {a.at: (a.value["v"] if isinstance(a.value["v"], str)
                         else a.value["v"].get("v", a.value["v"]))
                  for a in ctx.ledger.query(predicate="chat:topic")}
    topic_times = sorted(topic_rows)
    t = turns(ctx)
    topic_idx = 0
    clear_times = sorted(a.at for a in cleared.values())
    for turn in t:
        # boundary events before this turn?
        while clear_times and clear_times[0] <= turn["at"]:
            clear_times.pop(0)
            if cur["turns"]:
                cur["endAt"] = turn["at"]
                segs.append(cur)
            cur = {"index": len(segs) + 1, "topic": cur["topic"], "turns": [],
                   "startAt": None, "boundary": "clear-chat"}
        while topic_idx < len(topic_times) and topic_times[topic_idx] <= turn["at"]:
            new_topic = topic_rows[topic_times[topic_idx]] or None
            topic_idx += 1
            if cur["turns"] and new_topic != cur["topic"]:
                cur["endAt"] = turn["at"]
                segs.append(cur)
                cur = {"index": len(segs) + 1, "topic": new_topic, "turns": [],
                       "startAt": None, "boundary": "topic-change"}
            else:
                cur["topic"] = new_topic
        if cur["startAt"] is None:
            cur["startAt"] = turn["at"]
        cur["turns"].append(turn)
    if cur["turns"]:
        cur["endAt"] = cur["turns"][-1]["at"]
        segs.append(cur)
    return segs


def seal(ctx, topic=None, reason: str = "segment boundary",
         claimant: str = "system") -> dict:
    """Write an archive:segment summary row for the segment just closed —
    durable-result evidence, computed from the live turns."""
    segs = segments(ctx)
    last = segs[-1] if segs else {"turns": [], "topic": topic}
    rec = {"topic": topic if topic is not None else last.get("topic"),
           "turns": len(last["turns"]),
           "firstAt": last.get("startAt"), "endAt": last.get("endAt"),
           "reason": reason, "sealedAt": now_ms()}
    ctx.append("archive", "archive:segment", rec, claimant,
               basis={"kind": "durable-result"})
    return rec


def archive_view(ctx) -> dict:
    segs = segments(ctx)
    return {"segments": segs, "turnCount": sum(len(s["turns"]) for s in segs),
            "segmentCount": len(segs)}
