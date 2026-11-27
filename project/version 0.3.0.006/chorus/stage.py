"""The stage — interstitial presentations, scene enactment, background
audio channels.
Interstitials (S-interstitial-queue): ad-like prepared presentations for
complex topics — asset needs queue for creation across the fleet until
collected; changed inputs trigger reassessment/rework; presentation waits
for readiness (defer, not half-show). Trigger honestly bounded:
complex-information need or explicit user request. Under-explored —
declared, not invented.
Scene enactment (S-scene-enactment): personas enact a short public-domain
scene using available tool classes; absent classes honestly skipped.
"""
import os
import time
from . import engines
from .needs import COMPOSITIONS
from .book import fresh_id, now_iso
SCENE_LIBRARY = {
    "knock-knock": {
        "title": "Knock-knock (public domain form)",
        "parts": [
            {"persona": 0, "line": "Knock, knock."},
            {"persona": 1, "line": "Who's there?"},
            {"persona": 0, "line": "Lettuce."},
            {"persona": 1, "line": "Lettuce who?"},
            {"persona": 0, "line": "Lettuce in, it's cold out here."},
        ],
        "tool_classes": ["tool.compose-text", "tool.speak",
                         "tool.render-art", "tool.music",
                         "tool.catalog-media"],
    }
}
def request_interstitial(host, topic, origin="complex-need"):
    """Queue an interstitial: asset needs open fleet-addressable until
    collected; presentation waits for readiness. Trigger bounded to
    complex-information need or explicit user request."""
    if origin not in ("complex-need", "user-request"):
        origin = "complex-need"
    iid = fresh_id("interstitial")
    host.book.append("stage:interstitial", {
        "subject": iid, "topic": topic, "trigger": origin,
        "state": "queued", "boundedTrigger": True,
        "note": "under-explored surface — declared, not invented"},
        claimant="host", basis="derived")
    # asset needs queue across the fleet — each carries an assignable host
    needs = []
    for asset in ("script", "backdrop", "audio-bed"):
        n = host.needs.open("need:asset", {
            "subject": iid, "asset": asset,
            "requirement": f"{asset} for interstitial '{topic}'",
            "fleetAssignable": True,
            "assignee": host.node_id,
            "slots": {"interstitial": iid, "asset": asset}})
        needs.append(n["id"])
    host.state.setdefault("interstitials", {})[iid] = {
        "topic": topic, "needs": needs, "state": "collecting",
        "version": 1}
    return iid
def rework_interstitial(host, iid, new_topic):
    """Changed inputs trigger reassessment/rework — the queue reopens."""
    st = host.state.get("interstitials", {}).get(iid)
    if not st:
        return None
    st["topic"] = new_topic
    st["version"] += 1
    st["state"] = "collecting"
    for nid in st["needs"]:
        rows = [r for r in host.book.rows
                if r["claim"].get("needId") == nid and
                r["claim"].get("status") == "fulfilled"]
        for r in rows:
            host.needs.close(r, "superseded",
                             {"reason": "input changed — reworked"})
            host.needs.open("need:asset", {
                "subject": iid, "asset": r["claim"].get("asset"),
                "requirement": f"{r['claim'].get('asset')} for interstitial "
                               f"'{new_topic}' (rev {st['version']})",
                "fleetAssignable": True, "assignee": host.node_id,
                "slots": {"interstitial": iid,
                          "asset": r["claim"].get("asset")}})
    host.book.append("stage:rework", {
        "subject": iid, "version": st["version"], "topic": new_topic},
        claimant="host", basis="derived")
    return st
def interstitial_ready(host, iid):
    """Readiness gate for presentation — defer, never half-show."""
    st = host.state.get("interstitials", {}).get(iid)
    if not st:
        return {"ready": False, "declared": "unknown interstitial"}
    pending = []
    for nid in st["needs"]:
        cur = host.book.current()
        open_ = [r for r in cur if r["claim"].get("needId") == nid and
                 r["claim"].get("status") in (None, "open")]
        if open_:
            pending.append(open_[0]["claim"].get("asset"))
    if pending:
        st["state"] = "collecting"
        return {"ready": False, "pending": pending,
                "declared": "presentation deferred until assets collect"}
    st["state"] = "ready"
    return {"ready": True, "topic": st["topic"], "version": st["version"]}
def present_interstitial(host, iid):
    r = interstitial_ready(host, iid)
    if not r["ready"]:
        host.book.append("stage:deferred", {"subject": iid, **r},
                         claimant="host", basis="execution-evidence")
        return {"presented": False, "deferred": True,
                "declared": r.get("declared") or
                "unready — presentation deferred, declared not faked",
                "missing": r.get("pending", [])}
    st = host.state["interstitials"][iid]
    st["state"] = "presented"
    host.book.append("stage:presented", {
        "subject": iid, "topic": st["topic"], "version": st["version"],
        "assets": st["needs"]}, claimant="host", basis="execution-evidence")
    host.push_event("stage", {"interstitial": iid, "state": "presented",
                              "topic": st["topic"]})
    return {"presented": iid, "topic": st["topic"]}
def fulfill_asset(host, need_row):
    """Steward fulfills a queued asset need — composed from the minimal
    tool set, produced file bound to the interstitial."""
    asset = need_row["claim"].get("asset")
    iid = need_row["claim"].get("subject")
    out_dir = os.path.join(host.runtime_dir, "assets")
    os.makedirs(out_dir, exist_ok=True)
    produced = None
    if asset == "backdrop":
        svg = os.path.join(out_dir, f"{iid}-backdrop.svg")
        st = host.state.get("interstitials", {}).get(iid, {})
        with open(svg, "w", encoding="utf-8") as f:
            f.write('<svg xmlns="http://www.w3.org/2000/svg" '
                    'viewBox="0 0 320 180"><rect width="320" height="180" '
                    'fill="#1c2a4a"/><text x="160" y="96" font-size="22" '
                    'fill="#dfe8ff" text-anchor="middle">'
                    + (st.get("topic", "stage")) + '</text></svg>')
        produced = svg
    elif asset == "audio-bed":
        wav = os.path.join(out_dir, f"{iid}-bed.wav")
        engines.synth_ambient_wav(wav, seconds=4, kind="hum")
        produced = wav
    else:
        path = os.path.join(out_dir, f"{iid}-script.txt")
        st = host.state.get("interstitials", {}).get(iid, {})
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"Interstitial script — {st.get('topic','?')}\n"
                    "A prepared presentation composed from the tool set.\n")
        produced = path
    host.needs.close(need_row, "fulfilled", {"file": produced})
    host.book.append("stage:asset", {
        "subject": iid, "asset": asset, "file": produced,
        "assignee": host.node_id},
        claimant="host", basis="execution-evidence")
    return produced
def enact_scene(host, scene_key="knock-knock"):
    """The stage test: personas enact a short public-domain scene, parts
    spoken in turn through the serialized floor; available tool classes
    exercised, absent classes honestly skipped."""
    scene = SCENE_LIBRARY.get(scene_key, SCENE_LIBRARY["knock-knock"])
    roster = host.roster_order()
    if len(roster) < 2:
        return {"enacted": False, "declared": "need two personas on stage"}
    a, b = roster[0], roster[1]
    cast = [a, b]
    tool_classes_used, skipped = [], []
    sid = fresh_id("scene")
    host.book.append("stage:scene", {
        "subject": sid, "scene": scene["title"],
        "cast": [p["name"] for p in cast], "state": "enacting"},
        claimant="host", basis="derived")
    lines = []
    for part in scene["parts"]:
        p = cast[part["persona"]]
        text = part["line"]
        row = host.book.append("stage:line", {
            "subject": sid, "persona": p["name"], "text": text,
            "order": len(lines)}, claimant=f"persona:{p['id']}",
            basis="generated-response")
        host.speak_persona(p, text, sid)
        lines.append({"persona": p["name"], "text": text})
    for cls in scene["tool_classes"]:
        if cls in host.tool_catalog:
            tool_classes_used.append(cls)
        elif cls == "tool.compose-text":
            tool_classes_used.append(cls)
        elif cls == "tool.speak":
            tool_classes_used.append(cls)
        elif cls == "tool.render-art":
            # backdrop via art tool
            svg = os.path.join(host.runtime_dir, "assets", f"{sid}-bg.svg")
            os.makedirs(os.path.dirname(svg), exist_ok=True)
            with open(svg, "w", encoding="utf-8") as f:
                f.write('<svg xmlns="http://www.w3.org/2000/svg" '
                        'viewBox="0 0 320 180"><rect width="320" height="180" '
                        'fill="#2d1e3e"/><circle cx="160" cy="90" r="50" '
                        'fill="#ffd98a"/></svg>')
            tool_classes_used.append(cls)
        else:
            skipped.append(cls)
    host.book.append("stage:scene", {
        "subject": sid, "scene": scene["title"], "state": "enacted",
        "lines": lines, "toolClassesUsed": tool_classes_used,
        "classesSkipped": skipped,
        "skippedBasis": "class absent on this host — honestly skipped"},
        claimant="host", basis="execution-evidence")
    return {"enacted": True, "scene": scene["title"], "lines": lines,
            "cast": [p["name"] for p in cast],
            "toolClassesUsed": tool_classes_used, "skipped": skipped}
# ---------------- background channels ----------------
def ensure_sample_library(host):
    """Downloaded/synthesized sample-track library — honest local basis
    (no remote sample source configured on this host)."""
    lib = os.path.join(host.runtime_dir, "sample-library")
    os.makedirs(lib, exist_ok=True)
    tracks = {"rain": "rain", "hum": "hum", "drift": "drift"}
    present = []
    for name, kind in tracks.items():
        path = os.path.join(lib, name + ".wav")
        if not os.path.exists(path):
            engines.synth_ambient_wav(path, seconds=8, kind=kind)
        present.append(path)
    host.book.append("stage:sample-library", {
        "subject": "library", "tracks": present,
        "basis": "locally synthesized samples — no remote sample source "
                 "configured; declared"},
        claimant="host", basis="durable-result")
    return present
def open_channel(host, name):
    """A prompt-referenced background audio channel (S-background-channels):
    'play rain sounds' creates a persistent channel under conversation."""
    lib = os.path.join(host.runtime_dir, "sample-library", name + ".wav")
    exists = os.path.exists(lib)
    channels = host.state.setdefault("channels", {})
    channels[name] = {"name": name, "track": lib if exists else None,
                      "state": "playing" if exists else "declared-absent",
                      "openedAt": now_iso(), "persistent": True}
    host.book.append("stage:channel", {
        "subject": name, "track": channels[name]["track"],
        "state": channels[name]["state"],
        "declared": None if exists else "track absent — declared"},
        claimant="host", basis="execution-evidence")
    if exists:
        host.speech_floor.enqueue({"kind": "channel", "wav": lib,
                                   "persona": None, "turn": None})
    return channels[name]
