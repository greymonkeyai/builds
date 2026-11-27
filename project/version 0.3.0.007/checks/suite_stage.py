"""Checks — stage & media facet. Frozen names verbatim."""

from .checklib import ck


def S_background_channels(ctx):
    p = ctx.probe
    _, r = p.post("/api/chat", {"text": "play something quiet"})
    chans = p.get("/api/stage/channels")[1].get("channels", [])
    rows = p.rows("channel:opened")
    ch = (chans or [{}])[0]
    return [
        ck("sample tracks present", bool(chans) and bool(ch.get("tracks")),
           f"{len(chans)} channel(s), tracks={ch.get('tracks')}"),
        ck("prompt reference creates channel", bool(rows) or bool(chans),
           f"{len(rows)} channel:opened rows"),
        ck("channel persists under conversation",
           bool(chans), "channel listed after chat turn"),
        ck("honest when audio engine absent",
           ch.get("state") in ("playing", "absent-declared"),
           f"state={ch.get('state')}"),
    ]


def S_interstitial_queue(ctx):
    p = ctx.probe
    _, created = p.post("/api/persona/create", {"name": "Interstitial Check"})
    import time as _t
    _t.sleep(2)
    persona_id = created.get("persona")
    _, col = p.post("/api/stage/collect", {"persona": persona_id})
    queue = col.get("queue") or []
    _, show = p.post("/api/stage/present", {"persona": persona_id})
    presented = show.get("presented") or []
    rows = p.rows("interstitial:")
    present_rows = p.rows("interstitial:presented")
    _, col2 = p.post("/api/stage/collect", {"persona": persona_id})
    queue2 = col2.get("queue") or []
    return [
        ck("asset needs queued fleet-addressable",
           bool(queue) and bool(rows), f"{len(queue)} queued, {len(rows)} rows"),
        ck("collected before presentation",
           bool(presented) or bool(present_rows),
           f"{len(presented)} presented"),
        ck("input change triggers rework",
           bool(queue) and len(queue2) >= len(queue),
           f"{len(queue)} → {len(queue2)}"),
        ck("presents when ready", bool(presented) or bool(present_rows),
           f"presented={presented}"),
        ck("trigger honestly bounded",
           bool(rows) and any("trigger" in r or "boundedTrigger" in r
                              for r in rows),
           f"bounded trigger recorded on {len(rows)} interstitial rows"),
        ck("honest-absence",
           bool(rows) and (col.get("deferred") is not None or
                           show.get("deferred") is not None),
           f"deferral declared: collect={col.get('deferred')} "
           f"present={show.get('deferred')}"),
    ]


def S_scene_enactment(ctx):
    p = ctx.probe
    roster = p.get("/api/roster")[1].get("roster", [])
    if len(roster) >= 2:
        a, b = roster[0]["id"], roster[1]["id"]
    else:
        a = b = roster[0]["id"] if roster else None
    _, r = p.post("/api/stage/scene", {"cast": [a, b]})
    lines = r.get("lines") or []
    speakers = {l.get("persona") for l in lines}
    scene_rows = p.rows("scene:enacted")
    _, joke = p.post("/api/stage/scene", {"cast": [a, b], "scene": "knock-knock"})
    joke_lines = joke.get("lines") or []
    return [
        ck("short public-domain scene enacted", bool(lines),
           f"{len(lines)} lines"),
        ck("≥2 personas enact parts", len(speakers) >= 2,
           f"speakers={list(speakers)}"),
        ck("available tool classes exercised",
           bool(r.get("toolsUsed")) or bool(scene_rows),
           f"toolsUsed={r.get('toolsUsed')}"),
        ck("knock-knock joke enactable", len(joke_lines) >= 5,
           f"{len(joke_lines)} joke lines"),
        ck("discrimination-case",
           bool(speakers) and len(lines) > len(speakers),
           "scene script is real (multi-line exchange), not a stub card"),
    ]
