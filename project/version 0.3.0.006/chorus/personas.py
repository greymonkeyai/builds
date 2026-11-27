"""Personalities — distinct persistent participants. Dyadic held-confidence
moves differentiate on EVERY reorder (I-Dyadic / C-PerceivableDyadic);
new personas start at 0.5 (S-5). Voices are assigned with judgment and are
stable — never changed without user direction (S-voice-assign).
"""
import json
import os
import re
from .book import fresh_id, now_iso
from . import engines
PERSONA_DIRNAME = "personas"
# Shipped personas — distinct registers (S-distinct-preloadeds). All start at
# dyadic 0.5; portrait/voice/ack needs open at first boot and auto-fulfill
# (C-BoundPortrait), same mechanism as minted personas.
SHIPPED = [
    {"name": "Nix", "role": "archivist",
     "register": "precise, dry, cites what it knows and says plainly what it doesn't",
     "interests": ["reference", "history", "primary-texts"],
     "domains": ["general-knowledge", "reference", "historical-documents"],
     "voice_pref": {"gender": "Male", "traits": ["measured", "low"]}},
    {"name": "Vera", "role": "conversationalist",
     "register": "warm, plainspoken, short sentences, asks back",
     "interests": ["conversation", "media-analysis", "television"],
     "domains": ["television", "tropes", "media-analysis"],
     "voice_pref": {"gender": "Female", "traits": ["warm", "mid"]}},
    {"name": "Bolt", "role": "engineer",
     "register": "terse, concrete, numbers before adjectives",
     "interests": ["computer-science", "technical-reports", "tools"],
     "domains": ["computer-science", "research", "technical-reports"],
     "voice_pref": {"gender": "Male", "traits": ["clipped", "quick"]}},
    {"name": "Opal", "role": "storyteller",
     "register": "lyrical but grounded, tells it like a tale with facts kept straight",
     "interests": ["literature", "mythology", "public-domain-books"],
     "domains": ["literature", "mythology", "sacred-texts"],
     "voice_pref": {"gender": "Female", "traits": ["lyrical", "slow"]}},
]
IMITATION_MARK = "◈"
def persona_dir(runtime_dir):
    d = os.path.join(runtime_dir, PERSONA_DIRNAME)
    os.makedirs(d, exist_ok=True)
    return d
def persona_path(runtime_dir, pid):
    return os.path.join(persona_dir(runtime_dir), pid + ".json")
def save_persona(host, p):
    path = persona_path(host.runtime_dir, p["id"])
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(p, f, indent=1)
    os.replace(tmp, path)
def load_personas(host):
    """Privileged persistent objects: identities preserved outside ledger
    semantic records (persona json files), with ledger rows carrying the
    assertions about them."""
    out = {}
    d = persona_dir(host.runtime_dir)
    for name in os.listdir(d):
        if name.endswith(".json"):
            try:
                p = json.load(open(os.path.join(d, name), encoding="utf-8"))
                out[p["id"]] = p
            except Exception:
                continue
    return out
def seed_shipped(host):
    """Create shipped personas if absent; open their asset needs (portrait,
    voice, ack) — generated-need fulfillment, not a button (R-A1)."""
    existing = {p["name"] for p in host.personas.values()}
    for spec in SHIPPED:
        if spec["name"] in existing:
            continue
        p = {
            "id": fresh_id("persona"), "name": spec["name"],
            "role": spec["role"], "register": spec["register"],
            "interests": spec["interests"], "domains": spec["domains"],
            "confidence": 0.5, "certainty": 0.8,
            "voice": None, "portrait": None, "ack": None,
            "sources": [], "imitation": False, "shipped": True,
            "created": now_iso(),
        }
        host.personas[p["id"]] = p
        save_persona(host, p)
        host.book.append("persona:shipped", {"subject": p["id"], "name": p["name"],
                         "role": p["role"]}, claimant="host", basis="durable-result")
        open_persona_needs(host, p, source_suggestion=True)
def open_persona_needs(host, p, source_suggestion=True):
    """Persona creation opens generated needs (S-asset-anticipation;
    S-portrait-bind): portrait art, voice assignment, ack snippet,
    characterization, and a domain-matched source suggestion."""
    host.needs.open("need:portrait", {
        "subject": p["id"], "persona": p["name"],
        "requirement": f"authored portrait art bound as visual identity for {p['name']}",
        "slots": {"persona": p["id"]}}, priority=True)
    host.needs.open("need:voice", {
        "subject": p["id"], "persona": p["name"],
        "requirement": f"voice assigned with judgment for {p['name']}",
        "slots": {"persona": p["id"]}}, priority=True)
    host.needs.open("need:ack", {
        "subject": p["id"], "persona": p["name"],
        "requirement": f"audible acknowledgement snippet prepared for {p['name']}",
        "slots": {"persona": p["id"]}}, priority=True)
    host.needs.open("need:characterize", {
        "subject": p["id"], "persona": p["name"],
        "requirement": f"characterization extended for {p['name']}",
        "slots": {"persona": p["id"], "seed": p["register"]}})
    if source_suggestion and p.get("domains"):
        from . import sources as src_mod
        admitted = [s for s in host.sources.values()
                    if s.get("admitted") and s["key"] != "source-wikipedia"]
        pool = admitted or [s for s in host.sources.values() if s.get("admitted")]
        scored = src_mod.domain_match(p["domains"], pool)
        if scored:
            top = scored[0]
            host.needs.open("need:source-suggest", {
                "subject": p["id"], "persona": p["name"],
                "requirement": f"domain-matched source suggestion for {p['name']}",
                "suggestion": {"source": top[2]["key"], "name": top[2]["name"],
                               "matched_domains": sorted(top[3]),
                               "score": top[0]},
                "slots": {"persona": p["id"], "source": top[2]["key"]}},
                priority=True)
def fulfill_portrait(host, p):
    """Art engine fulfills the portrait need; result bound on the persona."""
    svg, meta = engines.llm_portrait_svg(host.llm, p)
    authored = bool(svg)
    if not svg:
        svg = engines.fallback_portrait_svg(p)
    art_path = os.path.join(persona_dir(host.runtime_dir), p["id"] + ".svg")
    with open(art_path, "w", encoding="utf-8") as f:
        f.write(svg)
    p["portrait"] = {"path": art_path, "authored": authored,
                     "engine": meta.get("engine"), "declared": not authored}
    save_persona(host, p)
    host.book.append("persona:portrait", {
        "subject": p["id"], "name": p["name"], "authored": authored,
        "engine": meta.get("engine"), "bound": True,
        "declaredFallback": not authored},
        claimant="engine:art", certainty=0.85, basis="generated-response")
def fulfill_voice(host, p):
    """Voice assignment with judgment (S-voice-assign): appropriateness from
    voice descriptions + variety-seeking (in-use voices disfavored); thin pool
    declared honestly. Voice once assigned is stable."""
    if p.get("voice"):
        return {"assigned": p["voice"], "reused": True}
    voices = host.voice_pool
    used = {q.get("voice", {}).get("name") for q in host.personas.values()
            if q.get("voice")}
    assessment = {"pool_size": len(voices), "in_use": sorted(u for u in used if u),
                  "reasoning": None, "thin_pool": len(voices) < 3}
    chosen = None
    if voices:
        pref_gender = (p.get("voice_pref") or {}).get("gender")
        # appropriateness: prefer a voice matching the persona's gender pref;
        # variety: disfavor voices already in use
        cands = [v for v in voices if v["name"] not in used]
        same_gender = [v for v in cands if v["gender"] == pref_gender]
        chosen = (same_gender or cands or voices)[0]
        assessment["reasoning"] = (
            f"appropriateness: persona prefers {pref_gender} voice; "
            f"variety: in-use voices {sorted(u for u in used if u)} disfavored; "
            f"chose '{chosen['name']}'")
    else:
        assessment["reasoning"] = "no device voices — speech will be declared-absent"
        chosen = {"name": "declared-absent", "gender": None,
                  "engine": "none", "declared": True}
    p["voice"] = {"name": chosen["name"], "engine": chosen.get("engine", "sapi"),
                  "spec": voice_spec(chosen, p), "stable": True,
                  "basis": assessment["reasoning"],
                  "assessed": assessment["in_use"],
                  "disfavored": [u for u in assessment["in_use"]
                                 if u != chosen["name"]]}
    save_persona(host, p)
    assessment["assigned"] = chosen["name"]
    host.book.append("persona:voice", {
        "subject": p["id"], "name": p["name"], "assigned": chosen["name"],
        "assessment": assessment, "stable": True},
        claimant="host", certainty=0.85, basis="derived")
    return assessment
def voice_spec(engine_voice, persona):
    """QR-fittable transferable voice spec (C-VoiceSpec): ranked family +
    traits, sized to fit a scannable code."""
    traits = list((persona.get("voice_pref") or {}).get("traits", []))
    fam = "female-adult" if (engine_voice or {}).get("gender") == "Female" else \
        "male-adult" if (engine_voice or {}).get("gender") == "Male" else "neutral"
    return {"families": [fam, "neutral"], "traits": traits[:4]}
def map_voice(spec, pool):
    """Local engine mapping (C-EngineMapping): render the portable spec
    through the nearest locally installed voice."""
    if not pool:
        return {"name": "declared-absent", "declared": True}
    fam = (spec or {}).get("families", ["neutral"])[0]
    want_female = fam.startswith("female")
    for v in pool:
        if (v["gender"] == "Female") == want_female:
            return v
    return pool[0]
def fulfill_ack(host, p):
    """Pre-generate the persona's audible acknowledgement snippet (≤5
    syllables / ≤0.5 s, register-suitable; plays before TTS composition —
    latency masking, not a pretend reply)."""
    acks = {
        "archivist": [392, 494], "conversationalist": [523, 659],
        "engineer": [330, 392], "storyteller": [440, 554, 659],
    }
    freqs = acks.get(p.get("role"), [440, 520])
    path = os.path.join(persona_dir(host.runtime_dir), p["id"] + "-ack.wav")
    engines.synth_tone_wav(path, freqs, ms_each=110)
    p["ack"] = {"path": path, "duration_ms": engines.wav_duration_ms(path),
                "basis": "locally-synthesized", "syllables": 0,
                "declared": "procedural snippet — voice-synthesized ack "
                            "when SAPI pre-render unavailable"}
    # Try a real spoken ack when a voice exists
    if p.get("voice") and p["voice"].get("name") not in (None, "declared-absent"):
        wpath = os.path.join(persona_dir(host.runtime_dir), p["id"] + "-ack-voice.wav")
        ok, ms, _ = engines.sapi_render("Mm hm.", p["voice"]["name"], wpath, rate=3)
        dur = engines.wav_duration_ms(wpath) if ok else None
        if ok and dur and dur <= 1200:
            p["ack"] = {"path": wpath, "duration_ms": dur,
                        "basis": "sapi-voice", "syllables": 2}
    save_persona(host, p)
    host.book.append("persona:ack", {
        "subject": p["id"], "name": p["name"],
        "durationMs": p["ack"].get("duration_ms"),
        "basis": p["ack"]["basis"]},
        claimant="engine:speech", certainty=0.8, basis="generated-response")
def fulfill_characterize(host, p):
    """Characterization extended via later work — dialog lines in register,
    authored by the LLM where live (declared otherwise)."""
    text, meta = host.llm.complete(
        f"Write three short lines {p['name']} would say to introduce "
        f"themselves. Register: {p.get('register')}. One line each, plain "
        f"sentences, no markup.", timeout=45)
    lines = []
    if text:
        lines = [l.strip("-•* ") for l in text.splitlines()
                 if l.strip() and not l.strip().startswith("<")][:3]
    if not lines:
        lines = [f"I'm {p['name']} — {p['role']} here.",
                 f"My beat is {', '.join(p.get('interests', ['what you ask about']))}.",
                 "Ask me anything; I'll tell you straight what I know."]
        meta["declared"] = True
    p["characterization"] = {"lines": lines, "engine": meta.get("engine"),
                             "declared": meta.get("declared", False)}
    save_persona(host, p)
    host.book.append("persona:characterize", {
        "subject": p["id"], "name": p["name"], "lines": lines,
        "engine": meta.get("engine"), "declared": meta.get("declared", False)},
        claimant=f"persona:{p['id']}", certainty=0.75, basis="generated-response")
def dyadic_move(host, pid, direction):
    """Move a persona up/down the roster. Every move produces a perceivable
    dyadic consequence — the value differentiates on each move even between
    equal-valued neighbors (R-P1): pick the simplest representable value
    between neighbors; when neighbors are equal, step one representable notch
    (0.05) in the direction of travel. Appended as a fresh assertion."""
    order = [p["id"] for p in host.roster_order()]
    if pid not in order:
        return None
    i = order.index(pid)
    j = i - 1 if direction == "up" else i + 1
    if j < 0 or j >= len(order):
        return {"moved": False, "reason": "at boundary"}
    order[i], order[j] = order[j], order[i]
    confs = {p["id"]: p["confidence"] for p in host.personas.values()}
    me = host.personas[pid]
    above = confs.get(order[j - 1]) if j > 0 else None
    below = confs.get(order[j + 1]) if j + 1 < len(order) else None
    if above is None and below is None:
        new_conf = me["confidence"]
    elif above is None:
        new_conf = min(1.0, round(below + 0.05, 3))
    elif below is None:
        new_conf = max(0.0, round(above - 0.05, 3))
    else:
        mid = round((above + below) / 2, 3)
        new_conf = mid
        if new_conf == me["confidence"]:
            new_conf = round(new_conf + (0.05 if direction == "up"
                                         else -0.05), 3)
        new_conf = min(1.0, max(0.0, new_conf))
    prev = me["confidence"]
    me["confidence"] = new_conf
    save_persona(host, me)
    host.roster_seq = order
    host.book.append("persona:rank", {
        "subject": pid, "name": me["name"], "moved": direction,
        "previous": prev, "heldConfidence": new_conf,
        "differentiates": new_conf != prev,
        "order": [host.personas[x]["name"] for x in order]},
        claimant="principal", certainty=1.0, basis="user-choice")
    return {"moved": True, "previous": prev, "heldConfidence": new_conf,
            "confidence": new_conf, "differentiates": new_conf != prev,
            "order": [host.personas[x]["name"] for x in order]}
def mint(host, name, declared_domains=None, interests=None, register=None,
         accept_source=True):
    """Canonical: minimal input → persona + generated needs. Domain-matched
    source suggestion is offered at creation; accepting binds the grant row."""
    p = {
        "id": fresh_id("persona"), "name": name,
        "role": "persona",
        "register": register or "plain, honest, stays in their own voice",
        "interests": interests or ["general-knowledge"],
        "domains": declared_domains or ["general-knowledge"],
        "confidence": 0.5, "certainty": 0.8,
        "voice": None, "portrait": None, "ack": None,
        "sources": [], "imitation": False, "shipped": False,
        "created": now_iso(),
    }
    host.personas[p["id"]] = p
    save_persona(host, p)
    row = host.book.append("persona:minted", {
        "subject": p["id"], "name": name, "domains": p["domains"],
        "heldConfidence": 0.5}, claimant="principal", certainty=1.0,
        basis="user-choice")
    open_persona_needs(host, p)
    # source suggestion is offered; acceptance binds the grant row
    sugg = host.needs.find_open("need:source-suggest", subject=p["id"])
    suggestion = sugg[0]["claim"].get("suggestion") if sugg else None
    accepted = None
    if sugg and accept_source:
        src_key = sugg[0]["claim"]["slots"]["source"]
        grant_source(host, p, src_key)
        host.needs.close(sugg[0], "accepted", {"bound": src_key})
        accepted = src_key
    return p, row, accepted, suggestion
def grant_source(host, p, src_key):
    """Persona assignment IS the grant row (D64/D76 pattern)."""
    if src_key not in p["sources"]:
        p["sources"].append(src_key)
        save_persona(host, p)
    host.book.append("grant:source", {
        "subject": p["id"], "persona": p["name"], "source": src_key,
        "scope": f"read:{src_key}"},
        claimant="principal", certainty=1.0, basis="user-choice")
def is_recognizable(name):
    """Heuristic for the imitation-mark rule: a persona named after a famous
    real person (living or deceased <10y) requires admonishment + permanent
    distinguishing mark."""
    famous = {"obama", "trump", "biden", "elon musk", "taylor swift",
              "einstein", "marilyn monroe", "kanye", "beyonce", "putin",
              "keanu", "oprah", "billie eilish", "zelensky"}
    return name.strip().lower() in famous
def mark_imitation(host, p, figure):
    """User admonished; display carries the permanent distinguishing mark."""
    p["imitation"] = True
    p["imitates"] = figure
    save_persona(host, p)
    host.book.append("persona:imitation", {
        "subject": p["id"], "imitates": figure,
        "admonishment": ("This persona imitates a recognizable figure's point "
                         "of view; it is not that person and carries no "
                         "authority from them."),
        "permanentMark": IMITATION_MARK},
        claimant="host", certainty=0.95, basis="derived")
