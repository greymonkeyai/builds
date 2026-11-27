"""Chat turn pipeline — the governing cycle's interactive face.
turn: input assertion -> classify -> route intents -> select respondents
(name-addressed U selector = equal-top-priority grants that UNION, not
override; interest/project matches respond even beyond depth; shortfall
fills from the roster in confidence-rank order; priority respondents are
exempt from depth) -> each respondent composes in register on a ledger
snapshot (parallel) -> sequential commit -> derived speakable rendering ->
serialized floor playback, measured. Audible acknowledgement enqueues
BEFORE composition (latency masking). Composition latency measured per
response, recorded, fleet-comparable.
"""
import concurrent.futures
import re
import time
from . import engines
def select_respondents(host, text, selector_ids, addressed):
    """Respondent grant union (C-RespondentGrantUnion): addressed-by-name and
    selector-chosen are equal-top-priority and union. Priority respondents
    always reply even beyond depth; shortfall fills from the roster in
    confidence-rank order; interest/project matches also reply beyond
    depth with awareness of matching needs/projects (C-InterestRespondents)."""
    depth = host.response_depth()
    roster = host.roster_order()  # ordered state = roster order
    by_conf = sorted(roster, key=lambda p: -p["confidence"])
    thresh = host.conf_threshold()
    prio, seen = [], set()
    def put(p, why):
        if p["id"] not in seen:
            seen.add(p["id"])
            prio.append({"persona": p, "grant": why})
    for p in addressed:                     # addressed first
        put(p, "addressed")
    for pid in selector_ids:                # then selector-chosen
        if pid in host.personas:
            put(host.personas[pid], "selector")
    # interest/project respondents — different keys each respond; same key
    # gated by the confidence threshold
    keyhits = interest_matches(host, text)
    samekey = {}
    for p, key in keyhits:
        if key in samekey:
            if p["confidence"] >= thresh:
                put(p, f"interest:{key}")
        else:
            samekey[key] = p
            put(p, f"interest:{key}")
    respondents = list(prio)
    # depth fill — only when selector isn't constraining ("chat all") or
    # priority count is below depth
    if len(respondents) < depth:
        for p in by_conf:
            if p["confidence"] < thresh:
                continue
            if len(respondents) >= depth:
                break
            if p["id"] not in seen:
                seen.add(p["id"])
                respondents.append({"persona": p, "grant": "depth-fill"})
    if not respondents and by_conf:
        respondents.append({"persona": by_conf[0], "grant": "depth-fill"})
    return respondents
def interest_matches(host, text):
    """Personas whose interest or assigned project key matches the topic."""
    low = text.lower()
    out = []
    for p in host.personas.values():
        for key in list(p.get("interests", [])) + list(p.get("domains", [])):
            key_l = key.lower().replace("-", " ")
            if len(key_l) > 4 and key_l in low:
                out.append((p, key))
                break
    for proj in host.book.current_of("project:object"):
        for word in re.findall(r"[a-z-]{5,}", proj["claim"].get("title", "").lower()):
            if word in low:
                for p in host.personas.values():
                    if p["id"] in proj["claim"].get("assignees", []):
                        out.append((p, f"project:{word}"))
    return out
def awareness_for(host, persona, text):
    """Matched respondents are given awareness of related open needs and
    open projects that match their keys."""
    keys = {k.lower() for k in persona.get("interests", [])}
    keys |= {k.lower() for k in persona.get("domains", [])}
    related_needs = []
    for n in host.needs.floor():
        req = (n["claim"].get("requirement") or "") + " " + \
              str(n["claim"].get("subject") or "")
        if any(k in req.lower() for k in keys if len(k) > 4):
            related_needs.append(n["claim"].get("requirement", "")[:80])
    related_projects = [pr["claim"].get("title")
                        for pr in host.book.current_of("project:object")
                        if persona["id"] in pr["claim"].get("assignees", [])]
    return {"needs": related_needs[:5], "projects": related_projects[:5]}
def compose_reply(host, persona, text, context, awareness):
    """One respondent's conversational reply — in register throughout
    (C-ConversationalRegister), factual grounding checked (S-2/S-faithful-
    voice: zero-hit retrieval must not pass the grounding check)."""
    sys_p = (f"You are {persona['name']}, a persona in a local-first home "
             f"assistant. Register: {persona.get('register')}. "
             f"Reply in 1-4 plain conversational sentences — never bullets, "
             f"never markdown, never citations, never textbook voice. "
             f"Stay in your own voice. If you don't know, say so plainly.")
    bits = [f"The user said: {text}"]
    if context.get("topic"):
        bits.append(f"Current topic: {context['topic']}")
    if awareness.get("needs"):
        bits.append("Related open work you know about: " +
                    "; ".join(awareness["needs"]))
    grounding = None
    if context.get("source_extract"):
        bits.append("Source evidence you may use: " +
                    context["source_extract"][:1500])
        grounding = "grounded"
    reply, meta = host.llm.complete("\n".join(bits), system=sys_p, timeout=40)
    engine = meta.get("engine")
    declared = False
    if not reply:
        reply, declared = fallback_reply(persona, text, context), True
    reply = scrub_conversational(reply)
    if context.get("zero_hit"):
        grounding = "ungrounded-declared"
    fidelity = grounding or ("composed" if not declared else "composed-declared")
    return {"text": reply, "engine": engine, "declared": declared,
            "fidelity": fidelity, "ms": meta.get("ms")}
def fallback_reply(persona, text, context):
    low = text.lower()
    name = persona["name"]
    if "what can you do" in low or "help" in low:
        return (f"I'm {name}. I keep the ledger straight, answer in my own "
                f"voice, and take on open work the steward drains — lists, "
                f"research, personas, the works. Ask me something.")
    if "list" in low:
        return (f"On it — I've opened the list machinery for that. "
                f"Give the steward a pass and the formal list lands in "
                f"the library.")
    if re.search(r"\bi want\b", low):
        return (f"Noted, and it's on the floor as an open want — I can't "
                f"conjure it myself, but it's recorded honestly rather "
                f"than pretended away.")
    if "tell me about yourself" in low or "who are you" in low:
        role = persona.get("role", "persona")
        return (f"I'm {name} — the {role} here. {persona.get('register')}. "
                f"That's the shape of me.")
    return (f"{name} here. I heard you — nothing in that needs a tool, "
            f"so it's just us talking. Say more and I'll keep up.")
def scrub_conversational(text):
    """Keep the reply conversational: collapse markup artifacts the model
    may emit (C-ConversationalRegister; spoken render derives separately)."""
    t = re.sub(r"[*_`#>\[\]]", "", text)
    t = re.sub(r"^\s*[-•]\s*", "", t, flags=re.M)
    t = re.sub(r"\s+\n", "\n", t)
    t = re.sub(r"\n{2,}", " ", t)
    return t.strip()
def grounding_extract(host, text):
    """Retrieve source evidence for grounding when the input asks a factual
    question. Zero hits must not pass the grounding check (S-2)."""
    low = text.lower()
    m = re.search(r"(?:tell me about|what is|who is|explain|look up|research)\s+(.+?)[?.!]*$", low)
    if not m:
        return None
    topic = m.group(1).strip()
    wiki = host.sources.get("source-wikipedia")
    if not wiki or not wiki.get("admitted"):
        return None
    hits = __import__("chorus.sources", fromlist=["mediawiki_search"]) \
        .mediawiki_search(wiki, topic, limit=3)
    if not hits:
        return {"zero_hit": True, "topic": topic}
    ex = __import__("chorus.sources", fromlist=["mediawiki_extract"]) \
        .mediawiki_extract(wiki, hits[0]["title"])
    if not ex:
        return {"zero_hit": True, "topic": topic}
    return {"extract": ex, "title": hits[0]["title"], "topic": topic}
def run_turn(host, text, selector_ids, surface="chat-ui"):
    """One chat turn — the full cycle. Returns the turn record; every stage
    lands as ledger assertions."""
    t0 = time.time()
    turn_id = host.book.append(
        "input:captured",
        {"subject": "chat", "text": text, "surface": surface,
         "valueType": "text"},
        claimant="principal", certainty=1.0, basis="captured-input")["id"]
    intents = host.needs.classify(text)
    addressed = []
    for it in intents:
        for p in it.get("addressed", []):
            if p not in addressed:
                addressed.append(p)
    routed = host.needs.route(turn_id, text, intents)
    host.book.append("chat:classified", {
        "subject": turn_id,
        "intents": [{"intent": i["intent"],
                     "addressed": [p["name"] for p in i["addressed"]]}
                    for i in intents],
        "routed": routed},
        claimant="host", basis="derived", relates=[turn_id])
    respondents = select_respondents(host, text, selector_ids, addressed)
    host.book.append("chat:respondents", {
        "subject": turn_id,
        "respondents": [{"persona": r["persona"]["name"],
                         "grant": r["grant"]} for r in respondents],
        "depth": host.response_depth(),
        "selectorInPlay": bool(selector_ids)},
        claimant="host", basis="derived", relates=[turn_id])
    # audible acknowledgement BEFORE composition — latency masking
    first = respondents[0]["persona"] if respondents else None
    ack_played = None
    if first and first.get("ack") and first["ack"].get("path"):
        host.speech_floor.enqueue({"kind": "ack", "wav": first["ack"]["path"],
                            "persona": first["name"], "turn": turn_id})
        ack_played = {"persona": first["name"],
                      "durationMs": first["ack"].get("duration_ms"),
                      "basis": first["ack"].get("basis")}
    else:
        ack_played = {"declared": "no pre-generated snippet — absent "
                      "snippet declared, not a silent gap"}
    # grounding + awareness
    g = grounding_extract(host, text) or {}
    context = {"topic": host.state.get("topic"),
               "source_extract": g.get("extract"),
               "zero_hit": g.get("zero_hit", False)}
    snap = host.book.snapshot()
    replies = []
    def draft(r):
        p = r["persona"]
        aw = awareness_for(host, p, text) if r["grant"].startswith("interest") \
            else {"needs": [], "projects": []}
        t_start = time.time()
        out = compose_reply(host, p, text, context, aw)
        compose_ms = int((time.time() - t_start) * 1000)
        return p, r["grant"], aw, out, compose_ms
    with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(4, len(respondents) or 1)) as ex:
        drafted = list(ex.map(draft, respondents))
    for p, grant, aw, out, compose_ms in drafted:
        # sequential commit in respondent order
        row = host.book.append("chat:reply", {
            "subject": turn_id, "persona": p["id"], "name": p["name"],
            "grant": grant, "text": out["text"], "engine": out["engine"],
            "declared": out["declared"], "fidelity": out["fidelity"],
            "awareness": aw, "composeMs": compose_ms},
            claimant=f"persona:{p['id']}", certainty=0.8,
            basis="generated-response", relates=[turn_id])
        # speech composition latency — measured per response, recorded,
        # fleet-comparable (S-speech-latency)
        lat = host.speak_persona(p, out["text"], turn_id)
        host.book.append("speech:latency", {
            "subject": row["id"], "persona": p["name"],
            "composeMs": compose_ms, "ttsMs": lat.get("tts_ms"),
            "totalMs": compose_ms + (lat.get("tts_ms") or 0),
            "host": host.node_id},
            claimant="engine:speech", basis="execution-evidence",
            relates=[row["id"], turn_id])
        replies.append({"persona": p["name"], "grant": grant,
                        "text": out["text"], "fidelity": out["fidelity"],
                        "engine": out["engine"], "declared": out["declared"],
                        "composeMs": compose_ms,
                        "ttsMs": lat.get("tts_ms"),
                        "row": row["id"]})
    host.book.append("chat:turn", {
        "subject": turn_id, "elapsedMs": int((time.time() - t0) * 1000),
        "ack": ack_played, "replyCount": len(replies)},
        claimant="host", basis="execution-evidence", relates=[turn_id])
    host.note_turn(text, replies)
    return {"turn": turn_id, "intents": routed, "respondents": respondents,
            "replies": replies, "ack": ack_played}
