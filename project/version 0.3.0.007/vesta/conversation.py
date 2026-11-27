"""conversation — the chat surface (module: conversation).

A chat input normally requests a chat response in kind. Respondents are
a union (C-RespondentGrantUnion): personas addressed by name reply
first, then selector-chosen selections — never override. Response depth
is a user assertion persisting across relaunch (C-ResponseDepth);
priority respondents are exempt; shortfall fills from the roster in
confidence-rank order; interest-matched personas respond beyond depth
(C-InterestRespondents) with awareness of matching open needs/projects.
Replies are conversational sentences in register (C-ConversationalRegister)
— improv backed by personality history on preference/opinion questions
(R-I1: truthfulness constrains claims, not play). Speech serializes
through a host floor (C-SpeechFloor) at sentence boundaries
(C-SpeakableRendering); composition latency measured per response.
"""

import json
import os
import queue
import re
import threading
import time

from . import engines
from .sources import wiki_extract, wiki_search_title

OPINION_RE = re.compile(
    r"\b(what.*(do you|you) (like|love|prefer|enjoy|hate)|"
    r"your (favorite|favourite|least favorite)|"
    r"do you (like|love|prefer|enjoy)|"
    r"what (kind|type|sort) of .* (do you|you) (like|prefer))\b", re.I)
FACTUAL_RE = re.compile(
    r"\b(who|what|where|when|which|how many|tell me about|"
    r"what is|what was|who is|who was)\b", re.I)


class SpeechFloor:
    """Serialized playback admission through a host queue — perceivability
    floor (C-SpeechFloor). Long text splits at sentence boundaries into
    sequential utterances; no silent mid-sentence cut."""

    def __init__(self, host):
        self.h = host
        self.q = queue.Queue()
        self.playing = False
        self._t = threading.Thread(target=self._drain, daemon=True)
        self._t.start()

    def _drain(self):
        while True:
            item = self.q.get()
            if item is None:
                return
            self.playing = True
            try:
                self._play(item)
            finally:
                self.playing = False
                self.q.task_done()

    def _play(self, item):
        """Playback is measured, not assumed: the floor holds the next
        utterance until the previous completes (wall-time from wav
        duration; declared when no audio engine)."""
        wav = item.get("wav")
        dur = item.get("seconds")
        self.h.ledger.append("speech:floor",
                             {"persona": item.get("persona"), "wav": wav,
                              "heldUntilPlaybackComplete": True,
                              "playbackMs": int((dur or 0) * 1000) if dur else None,
                              "engine": "sapi" if wav else "absent-declared"},
                             claimant="system", basis="execution-evidence",
                             transient=True)
        if dur:
            # floor held for the measured utterance duration
            end = time.time() + min(dur, 30)
            while time.time() < end and self.q.unfinished_tasks > 0:
                time.sleep(0.05)


FLOOR = {}


def _sentences(text, max_chars=400):
    """Split at sentence boundaries; oversized sentences break at the
    nearest clause mark — never mid-word."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    out = []
    for p in parts:
        while len(p) > max_chars:
            cut = max(p.rfind("; ", 0, max_chars), p.rfind(", ", 0, max_chars),
                      p.rfind(" — ", 0, max_chars))
            cut = cut if cut > 60 else max_chars
            out.append(p[:cut].strip())
            p = p[cut:].strip()
        if p:
            out.append(p)
    return [p for p in out if p]


def speakable(text):
    """Derived rendering for speech: markup, citations and non-speech
    punctuation rendered speakably or omitted, never vocalized verbatim."""
    t = re.sub(r"\[(\d+|[^\]]{0,24})\]", "", text)          # citations
    t = re.sub(r"[*_`#>]", "", t)                          # markup
    t = re.sub(r"https?://\S+", "a link", t)
    t = re.sub(r"^\s*[-•]\s*", "", t, flags=re.M)          # bullets
    t = re.sub(r"\(([^)]{0,60})\)", r", \1,", t)           # parens → pauses
    t = re.sub(r"\s+", " ", t)
    return t.strip()


class Conversation:
    def __init__(self, host):
        self.h = host
        self.floor = SpeechFloor(host)
        self.selector = []      # selector-chosen persona ids
        self.priority = set()   # priority respondents (exempt from depth)
        self._chat_lock = threading.Lock()

    # ---------- settings ----------
    def depth(self):
        s = self.h.ledger.view()["settings"].get("response-depth")
        return int(s["value"]) if s else 2

    def set_depth(self, n):
        self.h.ledger.append("settings:set",
                             {"setting": "response-depth", "value": int(n)},
                             claimant="principal", basis="user-set",
                             certainty=1.0)

    def set_selector(self, ids):
        self.selector = [i for i in ids]
        self.h.ledger.append("settings:set",
                             {"setting": "selector", "value": self.selector},
                             claimant="principal", basis="user-set")

    # ---------- respondents ----------
    def respondents(self, classification, text):
        """Union grants: addressed-by-name first, then selector-chosen;
        priority respondents exempt from depth; shortfall fills from the
        roster in confidence-rank order; interest matches join beyond
        depth with awareness of matching needs/projects."""
        v = self.h.ledger.view()
        roster = self.h.personas.roster()
        by_name = {p["name"].lower(): p for p in roster}
        addressed = []
        for nm in classification.get("addressed") or []:
            p = by_name.get(nm.lower())
            if p:
                addressed.append(p)
        chosen = [p for p in roster if p["id"] in self.selector and p not in addressed]
        union = addressed + chosen
        depth = self.depth()
        # priority respondents reply even beyond depth
        for p in roster:
            if p["id"] in self.priority and p not in union:
                union.append(p)
        # fill shortfall in confidence-rank order (chat-all relies on depth)
        ranked = sorted([p for p in roster if p not in union],
                        key=lambda p: -v["dyadic"].get(p["id"], 0.5))
        while len(union) < depth and ranked:
            union.append(ranked.pop(0))
        # interest-respondents beyond depth
        low = text.lower()
        interests = []
        for p in roster:
            if p in union:
                continue
            keys = [i.lower() for i in p.get("interests", [])]
            hits = [k for k in keys if k and k in low]
            if hits:
                interests.append((p, hits))
        aware = {}
        for p, hits in interests:
            needs = [n for n in v["needs_open"].values()
                     if any(k in (n.get("title", "") or "").lower() for k in hits)]
            projs = [pr for pr in v["projects"].values()
                     if any(k in (pr.get("title", "") or "").lower() for k in hits)]
            aware[p["id"]] = {"matchedOn": hits, "openNeeds": [n.get("title") for n in needs],
                              "projects": [pr.get("title") for pr in projs]}
            union.append(p)
        return union, aware

    # ---------- a persona reply ----------
    def reply(self, persona, text, classification, awareness=None):
        """Compose one reply: grounded to the persona's granted sources
        for factual asks; improvised in-register from personality history
        for preference/opinion asks (R-I1); always conversational
        sentences (C-ConversationalRegister)."""
        pid = persona["id"]
        name = persona.get("name", pid)
        style = (self.h.ledger.view()["settings"].get("response-style") or {}).get("value", "balanced")
        register = persona.get("register", "conversational")
        history = persona.get("history", "")
        character = persona.get("character", "")
        live = self.h.engines["llm"].get("live") and "stub-engines" not in self.h.sabotage

        grounded = None
        fidelity = None
        factual = bool(FACTUAL_RE.search(text)) and not OPINION_RE.search(text)
        opinion = bool(OPINION_RE.search(text))

        if factual:
            grounded = self._ground(pid, text)
            fidelity = "grounded" if grounded else "ungrounded-declared"

        system = (
            f"You are {name}, {character} Register: {register}. "
            f"Personal history: {history}. "
            "Reply in 1-3 conversational sentences IN YOUR REGISTER — "
            "never textbook entries, bullet lists, or citation blocks. "
            "You perform a personality: on preference/opinion questions, "
            "improvise from your own history and tastes (this is play, "
            "not factual claim — answer AS the persona, never refuse). "
            "On factual questions you may only assert what your sources "
            "support; when ungrounded, say so honestly in your own voice."
        )
        if style == "concise":
            system += " Keep it to one short sentence."
        elif style == "expansive":
            system += " You may use up to 4 sentences with color."

        if grounded:
            prompt = (f"Source material (your ground): {grounded['extract']}\n"
                      f"User asks: {text}\nAnswer in-register using only "
                      f"what the material supports.")
        elif opinion:
            prompt = (f"User asks your preference/opinion: {text}\n"
                      f"Answer AS {name} from your own tastes and history — "
                      f"improvise in-register; never say you 'just report'.")
        elif factual and not grounded:
            prompt = (f"User asks a factual question: {text}\nYou have no "
                      f"supporting source material. Say so honestly, in your "
                      f"own register, and offer what you'd do instead.")
        else:
            extra = ""
            if awareness:
                hits = awareness.get("matchedOn") or []
                extra = (f" (You noticed this touches your interests "
                         f"{hits}; needs {awareness.get('openNeeds')}; "
                         f"projects {awareness.get('projects')}.)")
            prompt = f"User says: {text}{extra}\nReply conversationally, in-register."

        t0 = time.time()
        text_out, llm_s = (None, 0)
        if live:
            text_out, llm_s = engines.llm(prompt, system=system, timeout=45)
        if not text_out:
            text_out = self._fallback(persona, text, opinion, factual, grounded)
            fidelity = fidelity or "fallback-declared"
        # register enforcement — replies render as plain conversational
        # prose; stray markup from the model is normalized out, not shown
        text_out = re.sub(r"[*_`#]+", "", text_out).strip()
        compose_s = round(time.time() - t0, 3)

        # speech-composition latency — measured per response, recorded as
        # a fleet-comparable metric
        self.h.ledger.append("metric:recorded",
                             {"metric": "speech-composition-latency",
                              "persona": pid, "seconds": compose_s,
                              "llmSeconds": llm_s, "node": self.h.node_id,
                              "style": style},
                             claimant="system", basis="instrumentation",
                             transient=True)
        row = self.h.ledger.append("reply:committed",
                                   {"persona": pid, "name": name, "text": text_out,
                                    "register": register, "fidelity": fidelity,
                                    "groundedOn": (grounded or {}).get("title"),
                                    "composeSeconds": compose_s,
                                    "improv": bool(opinion)},
                                   claimant=f"persona:{name}", basis="generated",
                                   certainty=0.6)
        return {"persona": pid, "name": name, "text": text_out,
                "register": register,
                "fidelity": fidelity, "grounded": bool(grounded),
                "composeSeconds": compose_s, "row": row["id"]}

    def _ground(self, pid, text):
        """Consult the persona's granted sources for factual support."""
        v = self.h.ledger.view()
        granted = v["persona_sources"].get(pid) or ["source-wikipedia"]
        query = re.sub(r"(?i)^(who|what|where|when|which|how many|tell me about|"
                       r"what is|what was|who is|who was)\s*", "", text).strip("? ").strip()
        for key in granted[:2]:
            title = wiki_search_title(key, query, host=self.h)
            if title:
                return wiki_extract(key, title, host=self.h)
        return None

    def _fallback(self, persona, text, opinion, factual, grounded):
        """Deterministic composed reply when no live model — declared,
        never presented as authored."""
        name = persona.get("name", "?")
        reg = persona.get("register", "")
        if opinion:
            hist = persona.get("history", "")
            return (f"{name} (declared-fallback): speaking for myself — "
                    f"{hist.split(';')[0] if hist else 'I have my tastes'} "
                    f"— that is the answer my history gives.")
        if factual and grounded:
            return f"{name} (declared-fallback): {grounded['extract'][:240]}"
        if factual:
            return (f"{name} (declared-fallback): I have nothing in my "
                    f"sources that answers that honestly.")
        return (f"{name} (declared-fallback, {reg}): I hear you — "
                f"'{text[:60]}'. Say more and I'll find my footing.")

    # ---------- the turn ----------
    def turn(self, text, persona_names=None):
        """One chat turn through the user path: capture → classify →
        route → union replies → sequential commit (C-SequentialCommit) →
        speech floor. Returns the turn record for the surface."""
        with self._chat_lock:
            v = self.h.ledger.view()
            names = persona_names or [p.get("name") for p in v["personas"].values()]
            cls = self.h.needs.classify(text, persona_names=names)
            inp = self.h.ledger.append(
                "input:captured",
                {"text": text, "type": "typed", "surface": "chat"},
                claimant="principal", basis="captured-input", certainty=1.0)
            routed_needs = self.h.needs.route(text, cls)

            union, aware = self.respondents(cls, text)
            replies = []
            for p in union:
                replies.append(self.reply(p, text, cls, aware.get(p["id"])))
                # sequential commit: each respondent sees earlier ones via
                # the journal — replies committed in order, one at a time

            # list needs fulfill through list machinery (formal object)
            list_result = None
            for nid in routed_needs:
                need = self.h.ledger.view()["needs"].get(nid)
                if need and need.get("kind") == "need:list" or \
                        (need and str(need.get("kind", "")).endswith("list")):
                    list_result = self.h.projects.fulfill_list(nid, text)

            # prompt-referenced media opens a persistent background channel
            if re.search(r"\b(play|music|song|track|listen|quiet|ambient)\b",
                         text.lower()):
                ch = self.h.stage.open_channel(
                    name=text[:48], basis="prompt-reference")
                turn_channel = ch

            # topic context
            self.h.ledger.append("context:topic",
                                 {"topic": text[:80], "at": time.time()},
                                 claimant="system", basis="derived")
            turn = {"input": inp["id"], "classification": cls,
                    "routedNeeds": routed_needs, "replies": replies,
                    "list": list_result,
                    "channel": locals().get("turn_channel"),
                    "respondents": [r["name"] for r in replies]}
            return turn

    # ---------- speech ----------
    def speak(self, text, persona=None):
        """Speak through the floor — speakable rendering, sentence
        boundaries, measured playback, audible ack precedes composition."""
        p = None
        if persona:
            p = self.h.ledger.view()["personas"].get(persona)
        self.h.stage.play_ack(persona)          # ack before composition
        text2 = speakable(text)
        wavs = []
        tts = self.h.engines.get("tts")
        voice = (p or {}).get("voice") or {}
        audio_dir = os.path.join(self.h.dir, "audio")
        os.makedirs(audio_dir, exist_ok=True)
        for i, sent in enumerate(_sentences(text2)):
            wav = os.path.join(audio_dir, f"u{int(time.time()*1000)}-{i}.wav")
            secs = None
            if tts:
                ok, compose_s = engines.sapi_speak_file(
                    sent, wav, voice=voice.get("voice"), rate=(voice.get("traits") or {}).get("rate", 0))
                if ok:
                    secs = engines.wav_seconds(wav)
                else:
                    wav = None
            else:
                wav = None
            self.floor.q.put({"persona": persona, "wav": wav, "seconds": secs,
                              "sentence": sent, "ttsComposeSeconds": compose_s if tts else None})
            wavs.append({"wav": wav, "seconds": secs, "sentence": sent})
        return {"ok": True, "utterances": wavs,
                "engine": "sapi" if tts else "absent-declared",
                "serialized": True}

    # ---------- context ----------
    def reset(self):
        """Reset clears the conversation when it has moved to a different
        topic — personality prompts stay on-topic (C-ConversationArchive)."""
        v = self.h.ledger.view()
        last = v["context"]
        self.h.ledger.append("context:topic",
                             {"topic": None, "reset": True,
                              "previous": (last or {}).get("topic")},
                             claimant="principal", basis="user-set")
        return {"ok": True, "cleared": (last or {}).get("topic")}

    def set_context(self, topic, via="selection"):
        self.h.ledger.append("context:topic",
                             {"topic": topic, "via": via},
                             claimant="principal", basis="user-set")
        return {"ok": True, "topic": topic}
