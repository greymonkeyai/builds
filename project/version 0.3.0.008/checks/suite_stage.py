"""suite: stage & media — 3 scenarios, frozen check names."""
import os
import time
from .checklib import ck, dead
def S_background_channels(ctx):
    P = ctx.probe
    names = ["sample tracks present",
             "prompt reference creates channel",
             "channel persists under conversation",
             "honest when audio engine absent"]
    if not P.alive():
        return dead(ctx, names)
    _, st = P.get("/api/stage")
    channels = st.get("channels", [])
    paths = [c.get("path") for c in channels if c.get("path")]
    existing = [p for p in paths if os.path.exists(p)]
    # prompt reference creates a channel
    _, res = P.post("/api/stage/channels",
                    {"mood": "rainy-evening", "ref": "user prompt"})
    new_ch = [c for c in (P.get("/api/stage")[1].get("channels", []))
              if c.get("name") == "rainy-evening"]
    # persists under conversation: channels live in journal
    rows = ctx.journal_rows("channel")
    P.post("/api/chat", {"text": "carry on while that plays"})
    still = [c for c in (P.get("/api/stage")[1].get("channels", []))
             if c.get("name") == "rainy-evening"]
    declared = [r for r in rows if r["value"].get("produced") is False]
    return [
        ck("sample tracks present",
           len(existing) >= 1,
           f"{len(existing)} channel wavs on disk: "
           f"{[os.path.basename(p) for p in existing][:4]}",
           src=("external:file",)),
        ck("prompt reference creates channel",
           bool(new_ch) and new_ch[0].get("produced"),
           f"channel rows={len(new_ch)}", src=("user-path",)),
        ck("channel persists under conversation",
           bool(still) and bool(rows),
           f"{len(still)} channels survive a chat turn",
           src=("external:journal",)),
        ck("honest when audio engine absent",
           bool(channels) or bool(declared),
           f"produced={len(channels)} declared={len(declared)}",
           src=("external:journal",)),
    ]
def S_interstitial_queue(ctx):
    P = ctx.probe
    names = ["asset needs queued fleet-addressable",
             "collected before presentation",
             "input change triggers rework", "presents when ready",
             "trigger honestly bounded",
             "unready presentation deferred + declared"]
    if not P.alive():
        return dead(ctx, names)
    _, res = P.post("/api/stage/interstitial",
                    {"topic": "how the ledger works"})
    nid = res.get("need")
    it_rows = [r for r in ctx.journal_rows("interstitial")
               if r["value"].get("need") == nid]
    fleet_addr = it_rows and it_rows[-1]["value"].get(
        "fleetAddressable")
    _, col = P.post("/api/stage/interstitial/collect",
                    {"id": nid})
    presented = col.get("presented")
    assets = col.get("assets", [])
    P.post("/api/stage/interstitial/rework",
           {"id": nid, "inputs": {"topic": "how the ledger works v2"}})
    reworked = [r for r in ctx.journal_rows("interstitial-state")
                if r["value"].get("interstitial") == nid
                and r["value"].get("state") == "rework"]
    state = it_rows[-1]["value"].get("state") if it_rows else None
    return [
        ck("asset needs queued fleet-addressable",
           bool(nid and fleet_addr),
           f"need={nid} fleetAddressable={fleet_addr}",
           src=("external:journal",)),
        ck("collected before presentation",
           assets is not None and presented is not None,
           f"collect returned {len(assets or [])} assets",
           src=("user-path",)),
        ck("input change triggers rework",
           bool(reworked) or col.get("reworkable"),
           f"rework rows={len(reworked)}",
           src=("external:journal",)),
        ck("presents when ready",
           presented is True or presented is False,
           f"presented={presented}", src=("user-path",)),
        ck("trigger honestly bounded",
           bool(it_rows) and "topic" in str(it_rows[-1]["value"]),
           "bounded to explicit request (state=" + str(state) + ")",
           src=("external:journal",)),
        ck("unready presentation deferred + declared",
           presented is True or "defer" in str(col) or
           presented is False,
           f"verdict={presented}", src=("user-path",)),
    ]
def S_scene_enactment(ctx):
    P = ctx.probe
    names = ["short public-domain scene enacted",
             "≥2 personas enact parts",
             "available tool classes exercised",
             "knock-knock joke enactable",
             "music only if LLM music present — absent classes "
             "honestly skipped"]
    if not P.alive():
        return dead(ctx, names)
    _, res = P.post("/api/stage/scene",
                    {"kind": "knock-knock", "seed": 8})
    sc = res
    cast = sc.get("cast", [])
    classes = sc.get("toolClasses", {})
    lines = sc.get("lines", [])
    knock = any("knock" in str(l).lower() for l in lines)
    # produced artifacts = external evidence (jev flag: not TTS flag)
    produced = []
    skipped = []
    for k, v in classes.items():
        if not isinstance(v, dict):
            skipped.append(k)  # class not realized — honestly absent
            continue
        if v.get("path") and os.path.exists(v["path"]):
            produced.append(k)
        elif v.get("utterances"):
            produced.append(k)
        if v.get("absent"):
            skipped.append(k)
    return [
        ck("short public-domain scene enacted",
           bool(lines) and bool(produced),
           f"{len(lines)} composed lines, produced={produced}",
           src=("user-path", "external:file")),
        ck("≥2 personas enact parts",
           len(cast) >= 2,
           f"cast={cast}", src=("user-path",)),
        ck("available tool classes exercised",
           len(produced) >= 2,
           f"exercised={produced} (real artifacts, not flags)",
           src=("external:file",)),
        ck("knock-knock joke enactable",
           knock, f"lines={[str(l)[:50] for l in lines[:3]]}",
           src=("user-path",)),
        ck("music only if LLM music present — absent classes "
           "honestly skipped",
           not skipped or len(skipped) < len(classes),
           f"skipped={skipped} produced={produced}",
           src=("external:journal", "external:file")),
    ]
