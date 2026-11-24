"""Persistent personalities — lenses over the shared ledger, not separate
knowledge stores.
Identities live outside the ledger's semantic records (prompt §Continuity):
`runtime/personalities.json` holds the roster; `persona:*` assertions give
the ledger view. Mint assigns identity at once, then portrait / voice /
characterization develop through generated needs.
G-B (owner-approved bar 2026-11-23): a persona's voice is a REGISTER
CONSTRAINT on truthful output. Factual answers preserve the factual content
of their sources; unsupported claims are flagged or withheld, never
invented. The compose path therefore separates FACTS (verbatim source
material, cited) from STYLE (register), instructs the engine to use only the
facts, and runs a grounding check on the result — an ungrounded draft is
flagged (`persona:fidelity-flag`) and answered honestly instead.
R3 shape on record (direction-004 G-C): new personalities start at 0.5
held-confidence under a dyadic relation row `rel:held-confidence`
{by: principal, about: persona:<id>, v: 0.5}.
"""
from __future__ import annotations
import json
import os
import re
from . import model, art
# -- voice registers -----------------------------------------------------------
# A register constrains HOW truth is expressed — never WHAT is claimed.
REGISTERS = {
    "clipped":    "Telegraphic. Short declaratives. No filler, no pleasantries.",
    "wry":        "Dry wit, understatement, a raised eyebrow — never a sneer.",
    "warm":       "Kind, encouraging, plain-spoken. Address the person directly.",
    "scholarly":  "Precise and measured. Cite what the record says; hedge where "
                  "the record is thin.",
    "catalogue":  "Enumerate. Ordered, itemized phrasing; one point at a time.",
    "measured":   "Balanced and calm. Weigh both sides before landing.",
    "expansive":  "Generous, curious, associative — but every claim still "
                  "traces to the record.",
}
class PersonaStore:
    def __init__(self, ctx):
        self.ctx = ctx
        self.path = os.path.join(ctx.runtime, "personalities.json")
        self.data = {"personas": {}, "order": [], "active": None}
        self.load()
    # -- persistence ----------------------------------------------------------
    def load(self):
        if os.path.exists(self.path):
            self.data = json.load(open(self.path, encoding="utf-8"))
            # J1 discipline: dedupe order, drop entries with no persona
            seen, order = set(), []
            for pid in self.data.get("order", []):
                if pid in self.data["personas"] and pid not in seen:
                    order.append(pid)
                    seen.add(pid)
            for pid in self.data["personas"]:
                if pid not in order:
                    order.append(pid)
            self.data["order"] = order
            acts = [p for p in order]
            if self.data.get("active") not in acts:
                self.data["active"] = order[0] if order else None
    def save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self.path)
    # -- access ----------------------------------------------------------------
    def get(self, pid):
        return self.data["personas"].get(pid)
    def roster(self):
        return [self.data["personas"][pid] for pid in self.data["order"]
                if pid in self.data["personas"]]
    def active(self):
        p = self.get(self.data.get("active"))
        if not p and self.data["order"]:
            p = self.data["personas"][self.data["order"][0]]
        return p
    # -- roster as an operable control (G-E / R5) --------------------------------
    def select(self, pid) -> dict:
        """Selecting the active personality — every shipped persona reachable."""
        if pid not in self.data["personas"]:
            return {"ok": False, "error": "no such persona"}
        self.data["active"] = pid
        self.save()
        p = self.data["personas"][pid]
        self.ctx.ledger.say("roster", "roster:active",
                            {"personaId": pid, "name": p["name"]},
                            claimant="principal", certainty=1.0,
                            basis={"kind": "user-choice"})
        return {"ok": True, "active": pid, "name": p["name"]}
    def move(self, pid: str, direction: int) -> dict:
        """Reorder entries. The order persists in the persona store and is
        recorded as a dyadic relation assertion (C-PresenceRoster)."""
        order = self.data["order"]
        if pid not in order:
            return {"ok": False, "error": "no such persona"}
        i = order.index(pid)
        j = max(0, min(len(order) - 1, i + int(direction)))
        order.insert(j, order.pop(i))
        self.save()
        for k, q in enumerate(order):
            prev = self.ctx.ledger.resolve("roster", f"roster:rank:{q}")
            self.ctx.ledger.say(
                "roster", f"roster:rank:{q}",
                {"by": "principal", "about": f"persona:{q}", "rank": k},
                claimant="principal", certainty=1.0,
                basis={"kind": "user-choice"},
                supersedes=prev.id if prev else None)
        return {"ok": True, "order": order}
    # -- mint --------------------------------------------------------------------
    def mint(self, name: str, traits=None, interests=None, lens=None,
             figure=None, responsibilities=None) -> dict:
        ctx = self.ctx
        pid = model.rid("persona")
        lens = dict(lens or {})
        register = lens.get("register") or _register_for(name)
        lens.setdefault("style", register)
        # -- ethics gate: recognizable figures carry a permanent mark + the
        # user is admonished (prompt §Personalities; C-EthicsGate underneath)
        mark, admonish, gate = False, None, {"verdict": "original-persona"}
        if figure:
            gate = ctx.ethics_gate(figure)
            if gate["verdict"] == "refused":
                ctx.ledger.say(f"persona:{pid}", "persona:mint-refused",
                               {"name": name, "figure": figure,
                                "reason": gate["reason"]},
                               claimant="system", certainty=1.0,
                               basis={"kind": "refusal"})
                return {"ok": False, "refused": True,
                        "reason": gate["reason"], "gate": gate}
            mark = gate["verdict"] in ("mark-required", "admonish-required")
            admonish = gate.get("admonishment")
        p = {
            "id": pid, "name": name,
            "traits": list(traits or ["curious"]),
            "interests": list(interests or []),
            "responsibilities": list(responsibilities or ["respond"]),
            "lens": lens, "register": register,
            "figure": figure, "mark": mark,
            "voice": _assign_voice(ctx, len(self.data["order"])),
            "color": _color_for(pid),
            "frame": "respondent",
            "created": model.ms(),
        }
        self.data["personas"][pid] = p
        self.data["order"].append(pid)
        if not self.data["active"]:
            self.data["active"] = pid
        self.save()
        subj = f"persona:{pid}"
        ctx.ledger.say(subj, "persona:profile", p, claimant="system",
                       certainty=1.0, basis={"kind": "durable-result"})
        ctx.ledger.say("roster", "roster:joined",
                       {"personaId": pid, "name": name, "mark": mark},
                       claimant="system", certainty=1.0,
                       basis={"kind": "durable-result"})
        # C-PersonalityArt: every shipped persona arrives with a bound,
        # unique portrait — mint binds it, onboard may regenerate.
        try:
            ar = art.generate(ctx, pid, name, mark=mark)
            p["art"] = {"file": ar["file"], "motif": ar["motif"],
                        "palette": ar["palette"], "params": ar["params"]}
            self.save()
            ctx.ledger.say(subj, "persona:art",
                           {"artifact": ar["file"], "motif": ar["motif"],
                            "params": ar["params"], "bound": True},
                           claimant="engine:portrait", certainty=1.0,
                           basis={"kind": "durable-result"})
        except Exception as e:
            ctx.ledger.say(subj, "persona:art-failed",
                           {"error": repr(e)},
                           claimant="engine:portrait", certainty=1.0,
                           basis={"kind": "execution"})
        # R3 recorded shape: held-confidence starts at 0.5, expressed as a
        # dyadic relation (held BY the principal ABOUT the persona).
        ctx.ledger.say("roster", f"rel:held-confidence:{pid}",
                       {"by": "principal", "about": f"persona:{pid}",
                        "v": 0.5, "kind": "dyadic-confidence"},
                       claimant="system", certainty=1.0,
                       basis={"kind": "config"})
        if mark:
            ctx.ledger.say(subj, "persona:imitation-mark",
                           {"mark": "◆ IMITATION", "figure": figure,
                            "permanent": True},
                           claimant="system", certainty=1.0,
                           basis={"kind": "config"})
        return {"ok": True, "personaId": pid, "name": name, "mark": mark,
                "admonishment": admonish, "gate": gate}
    def update(self, pid: str, patch: dict) -> dict:
        """Personality editor path — every customizable element asserted."""
        p = self.get(pid)
        if not p:
            return {"ok": False, "error": "no such persona"}
        for k in ("name", "traits", "interests", "responsibilities",
                  "color", "frame"):
            if k in patch:
                p[k] = patch[k]
        if "register" in patch:
            p["register"] = patch["register"]
            p.setdefault("lens", {})["register"] = patch["register"]
        if "lens" in patch and isinstance(patch["lens"], dict):
            p["lens"].update(patch["lens"])
        if "voice" in patch and isinstance(patch["voice"], dict):
            p["voice"].update(patch["voice"])
        self.save()
        prev = self.ctx.ledger.resolve(f"persona:{pid}", "persona:profile")
        self.ctx.ledger.say(f"persona:{pid}", "persona:profile", p,
                            claimant="principal", certainty=1.0,
                            basis={"kind": "user-choice"},
                            supersedes=prev.id if prev else None)
        return {"ok": True, "persona": p}
    def held_confidence(self, pid) -> float:
        a = self.ctx.ledger.resolve("roster", f"rel:held-confidence:{pid}")
        if a:
            v = a.value.get("v") or {}
            return float(v.get("v", 0.5))
        return 0.5
    def set_held_confidence(self, pid: str, v: float):
        prev = self.ctx.ledger.resolve("roster", f"rel:held-confidence:{pid}")
        self.ctx.ledger.say(
            "roster", f"rel:held-confidence:{pid}",
            {"by": "principal", "about": f"persona:{pid}",
             "v": max(0.0, min(1.0, v)), "kind": "dyadic-confidence"},
            claimant="principal", certainty=1.0,
            basis={"kind": "user-choice"},
            supersedes=prev.id if prev else None)
# -- mint helpers -----------------------------------------------------------------
def _register_for(name: str) -> str:
    keys = sorted(REGISTERS)
    return keys[sum(map(ord, name)) % len(keys)]
def _color_for(pid: str) -> str:
    hues = ["#e63946", "#f4a261", "#e9c46a", "#2a9d8f", "#457b9d",
            "#8d6fc0", "#ef8354", "#6b9e78", "#d1495b", "#936639"]
    return hues[sum(map(ord, pid)) % len(hues)]
def _assign_voice(ctx, n: int) -> dict:
    voices = ctx.engines.tts.voices or []
    return {"name": voices[n % len(voices)] if voices else None,
            "rate": [0, -1, 1, 0, -2, 2][n % 6],
            "engine": ctx.engines.tts.mode}
# -- composition --------------------------------------------------------------------
def compose(ctx, persona: dict, prompt_text: str, facts: list = None,
            history: str = "", react_to: str = "",
            expect_facts: bool = False) -> dict:
    """Produce one persona reply.
    `facts` is a list of {"text","source"} — verbatim source material the
    answer may use. With facts present, the engine is instructed to draw on
    them ONLY; the draft then passes a grounding check. Without facts the
    persona speaks conversationally in register — opinion and voice, not
    fabricated fact.
    Returns {ok, text, register, engine, fidelity, flagged}.
    """
    reg = persona.get("register") or "measured"
    style = REGISTERS.get(reg, REGISTERS["measured"])
    facts = facts or []
    system = (
        f"You are {persona['name']}, a persona in a local-first assistant. "
        f"Voice register: {reg} — {style} "
        f"Traits: {', '.join(persona.get('traits', []))}. "
        f"Interests: {', '.join(persona.get('interests', []))}. "
    )
    if facts:
        system += (
            "FIDELITY RULE — a register is a style constraint, never a "
            "license to invent. Answer using ONLY the facts in FACTS below. "
            "Do not add names, dates, numbers, or claims that are not in "
            "FACTS. If FACTS do not answer the question, say plainly (in "
            "your register) what is not on record. Keep it under 120 words.\n"
            "FACTS:\n" + "\n".join(
                f"- [{f.get('source','record')}] {f['text']}" for f in facts))
    else:
        system += (
            "You have no source facts for this turn: speak from persona — "
            "opinion, taste, encouragement — and make no factual claims you "
            "cannot ground. Under 100 words.")
    user = prompt_text
    if history:
        user = f"Conversation so far:\n{history}\n\nNew input: {prompt_text}"
    if react_to:
        user += (f"\n\nEarlier contribution to react to (one sentence, "
                 f"in register): {react_to}")
    r = ctx.engines.llm.chat(system, user, max_tokens=180)
    if r.get("ok") and r.get("text"):
        text = _clean(r["text"])
        fidelity = _grounding(text, facts) if facts else {"grounded": True}
        # R2: a factual prompt with no retrieved source evidence means any
        # factual claim is unsupported — flag it honestly, never pass it as
        # grounded. The reply stands but carries the mark.
        if not facts and expect_facts:
            fidelity = {"grounded": False, "unsupported": True,
                        "issues": ["no-source-evidence"]}
            ctx.ledger.say(
                f"persona:{persona['id']}", "persona:fidelity-flag",
                {"draft": text[:300], "issues": ["no-source-evidence"],
                 "prompt": prompt_text[:200]},
                claimant="model:" + ctx.engines.llm.model,
                certainty=0.9, basis={"kind": "interpretation"})
        if facts and not fidelity["grounded"]:
            ctx.ledger.say(f"persona:{persona['id']}",
                           "persona:fidelity-flag",
                           {"draft": text[:300], "issues": fidelity["issues"],
                            "prompt": prompt_text[:200]},
                           claimant="model:" + ctx.engines.llm.model,
                           certainty=0.9, basis={"kind": "interpretation"})
            # withhold the ungrounded draft — answer honestly in register
            text = _withhold_in_register(reg, facts)
            fidelity = {"grounded": True, "withheld": True,
                        "issues": fidelity["issues"]}
        return {"ok": True, "text": text, "register": reg,
                "engine": r["engine"], "fidelity": fidelity}
    # declared fallback — faithful by construction: only facts may appear.
    text = _template_reply(persona, prompt_text, facts, react_to)
    return {"ok": True, "text": text, "register": reg,
            "engine": "declared-template",
            "fidelity": {"grounded": True, "engine": "template"},
            "fallbackError": r.get("error")}
def _clean(text: str) -> str:
    t = text.strip()
    if t.startswith('"') and t.endswith('"'):
        t = t[1:-1]
    return re.sub(r"\s+\n", "\n", t).strip()
def _grounding(text: str, facts: list) -> dict:
    """Cheap grounding check: numbers and capitalized multi-token entities in
    the reply must appear in FACTS. Single common words are ignored."""
    if not facts:
        return {"grounded": True}
    hay = " ".join(f["text"] for f in facts)
    issues = []
    for num in re.findall(r"\b\d[\d,\.%]*\b", text):
        if num.strip(",.%") and num not in hay and \
                num.strip(",.%") not in hay:
            issues.append(f"ungrounded-number:{num}")
    for ent in re.findall(r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b", text):
        if ent not in hay and not ent.startswith(("The ", "I ", "A ")):
            issues.append(f"ungrounded-entity:{ent}")
    return {"grounded": not issues, "issues": issues[:6]}
def _withhold_in_register(reg: str, facts: list) -> str:
    """Honest answer when the draft can't be grounded — flagged, withheld."""
    have = "; ".join(f["text"][:120] for f in facts[:2])
    forms = {
        "clipped": f"Can't back it. On record: {have}.",
        "wry": f"I'd love to improvise, but the record only gives me: {have}.",
        "warm": f"I don't want to guess at this — what I do have is: {have}.",
        "scholarly": f"The record supports only: {have}. Beyond that I "
                     f"cannot speak with confidence.",
        "catalogue": f"On record: (1) {have}. Nothing further supported.",
        "expansive": f"Here's what the record actually holds: {have} — "
                     f"the rest I'd only be inventing.",
    }
    return forms.get(reg, f"What I can verify: {have}.")
def _template_reply(persona, prompt_text, facts, react_to="") -> str:
    reg = persona.get("register") or "measured"
    name = persona["name"]
    core = "; ".join(f["text"][:140] for f in facts[:3]) if facts else None
    if react_to:
        base = {
            "clipped": f"Noted. {react_to[:80]} — fair point.",
            "wry": f"Well, {react_to[:60]}… hard to argue with that.",
            "warm": f"I love where that lands — {react_to[:80]}.",
            "scholarly": f"As stated: {react_to[:80]}. I'd concur.",
            "catalogue": f"On that contribution: {react_to[:80]}. Noted.",
            "expansive": f"Oh, that sparks something — {react_to[:80]}.",
        }.get(reg, f"On that: {react_to[:80]}.")
        return base
    if core:
        forms = {
            "clipped": f"{core}.",
            "wry": f"Since you ask: {core}. Thrilling, I know.",
            "warm": f"Here's what I found for you — {core}.",
            "scholarly": f"Per the record: {core}.",
            "catalogue": f"Findings: 1) {core}.",
            "expansive": f"There's rather a lot here — {core} — and it "
                         f"rewards a closer look.",
            "measured": f"As I read the record: {core}.",
        }
        return forms.get(reg, f"{core}.")
    forms = {
        "clipped": f"{name} here. Say more — I'll keep it short.",
        "wry": f"{name}, at your service. Do go on — I'm riveted.",
        "warm": f"{name} here — glad you're asking. Tell me more?",
        "scholarly": f"{name}. I'll need more to go on before I can "
                     f"speak with confidence.",
        "catalogue": f"{name}, present. State your need — I'll itemize.",
        "expansive": f"{name} — oh, do tell me everything.",
        "measured": f"{name} here. What's on your mind?",
    }
    return forms.get(reg, f"{name} here.")
