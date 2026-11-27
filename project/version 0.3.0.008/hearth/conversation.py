"""hearth conversation — chat surface + speech floor.
Turn chain: capture (assertion) -> deterministic classify first pass
-> async model lane (C-TurnEvalLane: gate->classify->evaluate; the
late verdict opens rows, never blocks) -> intent routing (name-address /
capability / list->machinery / want!=list / unmet->floor) -> respondent
union (addressed-first + selected + priority + interest-matched + depth
fill, confidence-rank) -> replies (in-register, fidelity-marked) ->
speech: audible ack BEFORE TTS composition, serialized floor playback,
sentence-boundary utterances, latency measured in seconds.
"""
import os
import re
import threading
import time
from . import audio
MARKUP = re.compile(r"[*_`#>\[\](){}]|https?://\S+|\S+@\S+")
class Conversation:
    def __init__(self, host):
        self.h = host
        self.turns = []
        self.topic = "general"
        self.context = []      # persona / email / result selections
        self.priority = set()  # priority respondent ids (exempt depth)
        self.conf_threshold = 0.5
    # ---- settings ------------------------------------------------------
    def depth(self):
        rows = self.h.journal.rows("settings-claim",
                                   where={"setting": "response-depth"})
        return int(rows[-1]["value"]["value"]) if rows else 2
    def set_depth(self, n, claimant="user"):
        """Response depth is a user assertion — accessible, persistent."""
        self.h.journal.append("settings-claim",
                              {"setting": "response-depth", "value": int(n)},
                              claimant=claimant, basis="user-choice")
        return int(n)
    # ---- classification / routing --------------------------------------
    def classify(self, text):
        """Deterministic first pass — each distinguishable intent routes
        to its fulfillment path."""
        t = text.strip()
        low = t.lower()
        intents = []
        addressed = None
        personas = self.h.modules["personas"]
        for p in self.h.indices["personas"].values():
            if re.search(r"\b" + re.escape(p["name"].lower()) + r"\b", low):
                addressed = p["id"]
                intents.append({"intent": "name-address",
                                "persona": p["id"], "name": p["name"]})
                break
        if re.search(r"\b(make|create|build|list)\b.*\blist\b|"
                     r"\blist (all|the|every)\b", low):
            intents.append({"intent": "list-request", "text": t})
        if re.search(r"\bwhat (can|are) (you|your)\b|\bhelp\b|"
                     r"\bcapabilit", low):
            intents.append({"intent": "capability"})
        if re.search(r"\bi want\b|\bi'd like\b|\bwish\b", low) and \
                not any(i["intent"] == "list-request" for i in intents):
            intents.append({"intent": "want", "text": t})
        if re.search(r"\b(email|send|post|publish|mail)\b", low) and \
                re.search(r"\b(to|out)\b", low):
            intents.append({"intent": "publish-request", "text": t})
        if re.search(r"\b(play|music|background|ambient|quiet)\b", low):
            intents.append({"intent": "media", "text": t})
        if re.search(r"(create|make|mint) (a |an )?(new )?"
                     r"(personality|persona|character)", low):
            intents.append({"intent": "persona-create", "text": t})
        if re.search(r"\bweather\b|\btemperature\b|\brain\b|\bsnow\b",
                     low):
            intents.append({"intent": "env-query", "text": t})
        if not intents:
            intents.append({"intent": "unmet", "text": t})
        return addressed, intents
    def _model_lane(self, text, input_row, intents):
        """C-TurnEvalLane: async model verdict beside the deterministic
        pass — late verdict opens evidence/need rows, never blocks."""
        def work():
            verdict = self.h.ollama(
                "Classify this user request in one word: question, "
                "command, list-request, want, or chat.\n" + text)
            if verdict:
                self.h.journal.append(
                    "turn-eval",
                    {"input": input_row["id"], "verdict": verdict[:80],
                     "lane": "model", "late": True},
                    claimant="system", basis="interpretation",
                    refs=[input_row["id"]])
                if "list" in verdict.lower() and                         all(i["intent"] == "unmet" for i in intents)                         and not any(
                        r["value"].get("request") == text
                        for r in self.h.journal.rows("unmet-request")):
                    self.h.journal.append(
                        "unmet-request",
                        {"request": text, "lane": "model",
                         "state": "open", "boundTemplate": "list-build"},
                        claimant="system", basis="interpretation")
        threading.Thread(target=work, daemon=True).start()
    # ---- the turn --------------------------------------------------------
    def turn(self, text, user="user"):
        h = self.h
        needs_m = h.modules["needs"]
        pers = h.modules["personas"]
        t0 = time.time()
        input_row = h.journal.append(
            "user-input", {"text": text, "surface": "chat"},
            claimant=user, basis="captured-input")
        addressed, intents = self.classify(text)
        self._model_lane(text, input_row, intents)
        results = {"intents": [], "needsOpened": [], "replies": [],
                   "routed": [], "speech": {}}
        for it in intents:
            results["intents"].append(it["intent"])
            if it["intent"] == "list-request":
                r = self._open_list(text, input_row)
                results["needsOpened"].append(r)
                results["routed"].append({"intent": "list-request",
                                          "to": "list-machinery"})
            elif it["intent"] == "want":
                n = needs_m.open("user-request",
                                 claimant="user",
                                 provenance=input_row["id"],
                                 slots={"request": {"value": text,
                                                    "confidence": 0.7,
                                                    "source": "user"}})
                results["needsOpened"].append(n["id"])
                results["routed"].append({"intent": "want",
                                          "to": "floor-user-request"})
            elif it["intent"] == "unmet":
                h.journal.append(
                    "unmet-request",
                    {"request": text, "state": "open",
                     "lane": "deterministic"},
                    claimant="system", basis="interpretation",
                    refs=[input_row["id"]])
                n = needs_m.open("user-request",
                                 claimant="system",
                                 provenance=input_row["id"],
                                 slots={"request": {"value": text,
                                                    "confidence": 0.55,
                                                    "source": "system"}})
                results["needsOpened"].append(n["id"])
                results["routed"].append({"intent": "unmet",
                                          "to": "floor"})
            elif it["intent"] == "publish-request":
                r = h.modules["exchange"].publish_request(text, input_row)
                results["routed"].append({"intent": "publish-request",
                                          "to": "publish-workflow",
                                          "result": r})
            elif it["intent"] == "media":
                r = h.modules["stage"].media_intent(text)
                results["routed"].append({"intent": "media",
                                          "to": "stage-channels",
                                          "result": r})
            elif it["intent"] == "persona-create":
                r = self._create_persona_from_text(text)
                results["routed"].append({"intent": "persona-create",
                                          "to": "persona-mint",
                                          "result": r})
            elif it["intent"] == "env-query":
                r = h.modules["projects"].environment()
                results["routed"].append({"intent": "env-query",
                                          "to": "env-claims",
                                          "result": bool(r.get("weather"))})
            elif it["intent"] == "capability":
                results["routed"].append({"intent": "capability",
                                          "to": "answered"})
            elif it["intent"] == "name-address":
                results["routed"].append({"intent": "name-address",
                                          "to": it["persona"]})
        respondents = self._respondents(addressed, text)
        replies = []
        for p in respondents:
            replies.append(self._reply(p, text, intents))
        results["replies"] = replies
        results["turnSeconds"] = round(time.time() - t0, 1)
        self.turns.append({"input": text, "ts": time.time(),
                           "replies": replies})
        self._update_topic(text)
        return results
    def _open_list(self, text, input_row):
        needs_m = self.h.modules["needs"]
        m = re.search(r"list (?:all )?(?:the )?(.+?)(?:\?|\.|$)",
                      text, re.I)
        criteria = m.group(1).strip() if m else text
        n = needs_m.open("list-build", claimant="user",
                         provenance=input_row["id"],
                         slots={"criteria": {"value": criteria,
                                             "confidence": 0.9,
                                             "source": "user"}})
        needs_m.bind_tool(n["id"], "list.specialized")
        proj = self.h.modules["projects"].create(
            "list: " + criteria[:40], criteria,
            claimant="system")
        self.h.modules["projects"].advance(
            proj["id"], "list request routed to list-build",
            need_ref=n["id"])
        return n["id"]
    def _create_persona_from_text(self, text):
        m = re.search(r"(?:named|called) ([\w'-]+)", text, re.I)
        name = m.group(1) if m else "New Persona"
        p = self.h.modules["personas"].mint(name, claimant="user")
        self.h.modules["needs"].open(
            "portrait-asset",
            slots={"persona": {"value": p["id"], "confidence": 0.9,
                               "source": "system"}},
            claimant="system")
        self.h.modules["needs"].open(
            "ack-asset",
            slots={"persona": {"value": p["id"], "confidence": 0.9,
                               "source": "system"}},
            claimant="system")
        return p["id"]
    # ---- respondents -----------------------------------------------------
    def _respondents(self, addressed, text):
        pers = self.h.modules["personas"]
        roster = pers.roster()
        selected = pers.selected_personas()
        union = []
        if addressed:
            p = pers.get(addressed)
            if p:  # addressed-first (C-RespondentGrantUnion)
                union.append(p)
        for p in selected:
            if p not in union and p.get("dyadic", 0.5) >= \
                    self.conf_threshold:
                union.append(p)
        # interest-matched respond beyond depth (C-InterestRespondents)
        low = text.lower()
        interested = [p for p in roster if p not in union and any(
            k in low for k in p.get("interests", []))]
        for p in interested:
            if p.get("dyadic", 0.5) >= self.conf_threshold or \
                    len({k for k in p.get("interests", [])
                        if k in low}) > 0:
                union.append(p)
        # priority respondents exempt from depth
        for pid in self.priority:
            p = pers.get(pid)
            if p and p not in union:
                union.insert(0, p)
        # depth: "chat all" relies on depth; shortfall fills in
        # confidence-rank order
        depth = self.depth()
        fill = [p for p in roster if p not in union
                and p.get("dyadic", 0.5) >= self.conf_threshold]
        while len(union) < max(depth, 1) and fill:
            union.append(fill.pop(0))
        return union
    # ---- reply composition ------------------------------------------------
    def _reply(self, persona, text, intents):
        h = self.h
        register = persona["register"]
        name = persona["name"]
        low = text.lower()
        grounded = False
        body = None
        # grounding: env claims, granted sources, ledger context
        env = h.modules["projects"].environment()
        if any(k in low for k in ("weather", "temperature", "rain",
                                  "snow", "outside")) and \
                env.get("weather") and env["weather"].get("tempC") is not None:
            w = env["weather"]
            body = (f"{name} here — it's reading about "
                    f"{w['tempC']}°C out, wind near {w.get('windKph')} "
                    f"kilometers an hour, if the instruments can be "
                    f"trusted.")
            grounded = True
        if body is None:
            body = h.ollama(
                f"In {register} register, answer as {name} "
                f"({persona.get('character','')}). Stay conversational. "
                f"User said: {text}")
        if body:
            fidelity = "grounded" if grounded else "composed"
        else:
            body = self._fallback(persona, text, intents)
            fidelity = ("grounded" if grounded
                        else "ungrounded-declared")
        # speakable rendering: strip markup/citations for speech
        speak = re.sub(r"[*_`#>\[\]{}]", "", body).strip()
        speak = re.sub(r"https?://\S+", "a link", speak)
        reply = {"persona": persona["id"], "name": name,
                 "register": register, "text": body, "speak": speak,
                 "fidelity": fidelity, "chars": len(body)}
        self.h.journal.append(
            "reply", {"persona": persona["id"], "text": body,
                      "register": register, "fidelity": fidelity,
                      "addressed": True},
            claimant="persona:" + persona["id"],
            basis="generated-response")
        self._speech(persona, reply)
        return reply
    def _fallback(self, persona, text, intents):
        """Deterministic in-register fallback — declared, never
        authored-claimed; distinct per persona register."""
        name = persona["name"]
        reg = persona["register"]
        kinds = {i["intent"] for i in intents}
        if "capability" in kinds:
            core = "I can chat, track needs, work the floor, watch the " \
                   "local network, and pass artifacts between instances."
        elif "env-query" in kinds:
            env = self.h.modules["projects"].environment()
            w = env.get("weather")
            if w and w.get("tempC") is not None:
                core = f"The instruments say {w['tempC']} degrees."
            else:
                core = "I haven't a reliable reading to offer."
        elif "list-request" in kinds:
            core = "I've opened the list machinery on the floor."
        elif "persona-create" in kinds:
            core = "A new presence is being shaped."
        else:
            core = "I'm here; say more and I'll see to it."
        flavor = {
            "warm-domestic": f"Well now — {core[0].lower()+core[1:]} "
                             f"— {name}",
            "dry-engineer": f"{core} — {name}.",
            "whimsical-storyteller":
                f"Ah, a thread to pull! {core} — {name}, spinning on.",
            "direct-archivist": f"{core} — {name}, on record.",
        }.get(reg, f"{core} — {name}")
        return flavor
    # ---- speech -------------------------------------------------------------
    def _speech(self, persona, reply):
        """Ack before composition; measured compose seconds; serialized
        floor playback; sentence-boundary utterances or declared excerpt."""
        h = self.h
        tts = h.engines.get("tts", {})
        voices = tts.get("voices", [])
        voice = (persona.get("voice") or {}).get("name")
        turn_speech = {"ack": None, "composeSeconds": None,
                       "wavs": [], "declared": None}
        # audible ack — pre-generated snippet plays BEFORE composition
        ack_path = os.path.join(h.audio_dir, "ack-" + persona["id"] + ".wav")
        if not os.path.exists(ack_path):
            try:
                audio.synth_ack(ack_path,
                                persona_seed=hash(persona["id"]) % 97)
                h.journal.append("ack-snippet",
                                 {"persona": persona["id"],
                                  "path": ack_path, "seconds": 0.28,
                                  "register": persona["register"]},
                                 claimant="tool:audio.synth",
                                 basis="execution-evidence")
            except Exception:
                h.journal.append("ack-snippet",
                                 {"persona": persona["id"], "path": None,
                                  "declared": "no ack snippet available"},
                                 claimant="system", basis="system")
        if os.path.exists(ack_path):
            info = audio.wav_info(ack_path)
            turn_speech["ack"] = info
            if not any(r["value"].get("persona") == persona["id"] and
                       r["value"].get("path")
                       for r in h.journal.rows("ack-snippet")):
                h.journal.append("ack-snippet",
                                 {"persona": persona["id"],
                                  "path": ack_path,
                                  "seconds": (info or {}).get("seconds"),
                                  "register": persona["register"]},
                                 claimant="tool:audio.synth",
                                 basis="execution-evidence")
            h.speech_floor.enqueue({"kind": "wav", "path": ack_path,
                                    "label": "ack:" + persona["id"]})
        if not voices or not voice:
            turn_speech["declared"] = ("tts-absent-declared" if not voices
                                       else "voice-unassigned-declared")
            return turn_speech
        # compose — measured seconds, sentence-boundary utterances
        sents = re.split(r"(?<=[.!?])\s+", reply["speak"])
        sents = [s for s in sents if s.strip()]
        truncated = False
        if len(reply["speak"]) > 300:
            truncated = True
            keep, acc = [], 0
            for s in sents:
                if acc + len(s) > 300:
                    break
                keep.append(s)
                acc += len(s)
            sents = keep
        t0 = time.time()
        for i, s in enumerate(sents):
            path = os.path.join(
                h.audio_dir,
                f"sp-{persona['id']}-{int(t0*1000)}-{i}.wav")
            info = audio.sapi_speak_to_wav(s, voice, path)
            if info:
                turn_speech["wavs"].append(info)
                h.speech_floor.enqueue({"kind": "wav", "path": path,
                                        "label": "tts:" + persona["id"]})
        compose = round(time.time() - t0, 1)
        turn_speech["composeSeconds"] = compose
        if truncated:
            turn_speech["declared"] = "excerpt-declared"
        if not turn_speech["wavs"]:
            # nothing was composed — a 0.0s metric row would be a false
            # measurement; the speech-event records the declared absence
            turn_speech["declared"] = "no-utterance-declared"
        else:
            # fleet-comparable metric — seconds
            h.metric("speech-compose", compose, persona=persona["id"],
                     chars=reply["chars"], node=h.node["id"],
                     utterances=len(turn_speech["wavs"]))
        h.journal.append("speech-event",
                         {"persona": persona["id"],
                          "composeSeconds": compose,
                          "utterances": len(turn_speech["wavs"]),
                          "ackPlayedBefore": True,
                          "excerpt": truncated,
                          "declared": turn_speech["declared"]},
                         claimant="tool:tts.sapi",
                         basis="execution-evidence")
        reply["speech"] = turn_speech
        return turn_speech
    # ---- topic / context / reset -----------------------------------------
    def _update_topic(self, text):
        words = {w for w in re.findall(r"[a-z]{4,}", text.lower())}
        for t in self.turns[-5:]:
            tw = {w for w in re.findall(r"[a-z]{4,}", t["input"].lower())}
            if words & tw:
                return
        if len(self.turns) > 1:
            self.topic = (text[:40] or "general")
            self.h.journal.append("conversation-segment",
                                  {"topic": self.topic},
                                  claimant="system", basis="claim")
    def reset(self, claimant="user"):
        n = len(self.turns)
        self.turns = []
        self.context = []
        self.topic = "general"
        self.h.journal.append("conversation-reset",
                              {"cleared": n, "topic": "general"},
                              claimant=claimant, basis="user-choice")
        return n
    def add_context(self, kind, ref, label=None):
        item = {"kind": kind, "ref": ref,
                "label": label or ref, "ts": time.time()}
        self.context.append(item)
        self.h.journal.append("context-focus", item, claimant="user",
                              basis="user-choice")
        return item
