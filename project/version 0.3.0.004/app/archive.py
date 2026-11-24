"""Conversation archive (C-ConversationArchive).
Every turn is archived; topic segments are bounded by topic-set and reset
markers. Reset seals the current segment into an `archive:segment`
durable-result row — the transcript survives, the live context clears, so
persona prompts stay on-topic.
"""
from __future__ import annotations
from . import model
def archive_turn(ctx, turn: dict):
    ctx.ledger.say("chat", "archive:turn", turn,
                   claimant="system", certainty=1.0,
                   basis={"kind": "durable-result"},
                   tags=["archive"])
def set_topic(ctx, topic: str):
    prev = ctx.ledger.resolve("chat", "chat:topic")
    ctx.ledger.say("chat", "chat:topic", {"topic": topic},
                   claimant="principal", certainty=1.0,
                   basis={"kind": "user-choice"},
                   supersedes=prev.id if prev else None)
    return {"ok": True, "topic": topic}
def topic(led) -> str:
    a = led.resolve("chat", "chat:topic")
    return (a.value.get("v") or {}).get("topic", "") if a else ""
def context(led):
    a = led.resolve("chat", "chat:context")
    return a.value.get("v") if a else None
def select_context(ctx, kind: str, ref: str, label: str,
                   excerpt: str = "") -> dict:
    """Pull an email/profile/need into conversational context; the top
    respondent comments on the selection."""
    prev = ctx.ledger.resolve("chat", "chat:context")
    ctx.ledger.say("chat", "chat:context",
                   {"kind": kind, "ref": ref, "label": label,
                    "excerpt": excerpt[:600]},
                   claimant="principal", certainty=1.0,
                   basis={"kind": "user-choice"},
                   supersedes=prev.id if prev else None)
    return {"ok": True, "context": {"kind": kind, "ref": ref, "label": label}}
def reset(ctx) -> dict:
    """Seal the conversation: archive the segment, clear topic/context/focus."""
    led = ctx.ledger
    turns = led.query(predicate="archive:turn", limit=500)
    last_reset = led.resolve("chat", "archive:segment")
    since = last_reset.at if last_reset else 0
    seg = [t for t in turns if t.at > since]
    led.say("chat", "archive:segment",
            {"turns": len(seg), "sealedAt": model.ms(),
             "topic": topic(led)},
            claimant="system", certainty=1.0,
            basis={"kind": "durable-result"}, tags=["archive"])
    for pred in ("chat:topic", "chat:context", "chat:focus"):
        a = led.resolve("chat", pred)
        if a:
            led.say("chat", pred, None, claimant="system", certainty=1.0,
                    basis={"kind": "config"}, supersedes=a.id)
    return {"ok": True, "sealedTurns": len(seg)}
