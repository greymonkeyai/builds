"""personas — roster, dyadic confidence, portraits, voices, editor,
surface assignment (module: personas).

Personalities are distinct, persistent participants interpreting the
shared ledger through their own lenses — not separate knowledge stores.
Creation from a minimal input mints identity and opens generated needs
(portrait, voice, characterization) fulfilled in the background
(S-asset-anticipation, C-BoundPortrait). Voice assignment is judgment:
appropriateness from voice descriptions plus variety — used voices
disfavored — then stable, changing only on user direction (S-voice-
assign). Every roster reorder produces a perceivable dyadic consequence
(I-Dyadic: simplest representable value between neighbors). A persona
imitating a person living or recently deceased carries the admonishment
+ permanent distinguishing mark (prompt §Personalities; M-Impersonation;
C-EthicsGate machinery).
"""

import json
import os
import re
import time

SHIPPED = [
    {"name": "Marlowe", "register": "noir",
     "character": "A private-eye narrator — terse, wry, favors short "
                  "sentences and weather metaphors. Interested in "
                  "mysteries, cities, and whatever the user is hiding.",
     "interests": ["mystery", "cities", "rain", "secrets"],
     "history": "Marlowe has logged months of late-night case notes; "
                "he likes rain on asphalt, dislikes small talk, and "
                "trusts facts that survive being written down.",
     "voiceTraits": {"family": ["male"], "rate": -1, "pitch": "low"}},
    {"name": "Ada", "register": "analyst",
     "character": "A precise, warm mathematician — explains with "
                  "structure, delight in patterns, honest about limits.",
     "interests": ["mathematics", "engines", "patterns", "lists"],
     "history": "Ada keeps ledgers of her own: she prefers ordered "
                "evidence, cool mornings, and questions that resolve "
                "into countable things.",
     "voiceTraits": {"family": ["female"], "rate": 0, "pitch": "bright"}},
    {"name": "Bramble", "register": "hedge-witch",
     "character": "A folklore gardener — earthy, meandering, speaks in "
                  "growing things and kitchen wisdom.",
     "interests": ["plants", "folklore", "seasons", "recipes"],
     "history": "Bramble keeps a garden journal older than the house; "
                "she likes damp soil, distrusts haste, and answers "
                "opinions with proverbs.",
     "voiceTraits": {"family": ["female"], "rate": -2, "pitch": "warm"}},
    {"name": "Quill", "register": "herald",
     "character": "A theatrical town-crier — formal, booming, announces "
                  "rather than replies.",
     "interests": ["proclamations", "ceremony", "history", "news"],
     "history": "Quill has read every proclamation twice; he favors "
                "bold headlines, windy hilltops, and never apologizes "
                "for volume.",
     "voiceTraits": {"family": ["male"], "rate": 1, "pitch": "booming"}},
]

RECOGNIZABLE = {
    "morgan freeman", "david attenborough", "barack obama", "elon musk",
    "taylor swift", "keanu reeves", "marilyn monroe", "einstein",
    "albert einstein", "spock", "darth vader", "homer simpson",
}


def _num_id(host, kind="persona"):
    return f"persona-{host.ledger.next_index('persona'):04d}"


class Personas:
    def __init__(self, host):
        self.h = host

    # ---------- shipped roster ----------
    def ensure_shipped(self):
        v = self.h.ledger.view()
        if v["personas"]:
            return v["personas"]
        order = []
        for spec in SHIPPED:
            pid = _num_id(self.h)
            self.h.ledger.append("persona:minted", {
                "persona": pid, "name": spec["name"],
                "register": spec["register"], "character": spec["character"],
                "interests": spec["interests"], "history": spec["history"],
                "shipped": True}, claimant="system", basis="build",
                certainty=0.85)
            order.append(pid)
            self._open_asset_needs(pid, spec["name"])
            self.assign_voice(pid, spec.get("voiceTraits"), spec["name"])
            self.h.ledger.append("dyadic:held-confidence",
                                 {"persona": pid, "confidence": 0.5},
                                 claimant="system", basis="derived",
                                 confidence=0.5)
        self.h.ledger.append("roster:order", {"order": order},
                             claimant="system", basis="build")
        # background bind portraits + acks
        for pid in order:
            self.compose_portrait(pid)
            self.h.stage.prepare_ack(pid)
        return self.h.ledger.view()["personas"]

    # ---------- creation ----------
    def create(self, name, register=None, character=None, interests=None,
               imitate=None, history=None, domains=None):
        """Mint a minimal personality from a minimal input, then extend
        through generated needs (portrait/voice/characterization)."""
        pid = _num_id(self.h)
        low = (name or "").lower()
        imitating = imitate or next(
            (r for r in RECOGNIZABLE if r in low), None)
        spec = {
            "persona": pid, "name": name,
            "register": register or "conversational",
            "character": character or f"{name}, a personality under "
                                      f"construction by its user.",
            "interests": interests or [],
            "domains": domains or [],
            "history": history or "",
        }
        if imitating:
            # M-Impersonation / prompt §Personalities: admonish + permanent mark
            spec["imitation"] = {
                "of": imitating,
                "mark": f"IMITATION — not {imitating}",
                "admonishment": f"This personality presents an imitation of "
                                f"{imitating}'s point of view, not the "
                                f"person's identity or authority. It "
                                f"carries a permanent distinguishing mark."}
            self.h.ledger.append("persona:admonished",
                                 {"persona": pid, "of": imitating,
                                  "notice": spec["imitation"]["admonishment"]},
                                 claimant="system", basis="policy")
        self.h.ledger.append("persona:minted", spec,
                             claimant="principal", basis="user-input")
        order = list(self.h.ledger.view()["roster"]) + [pid]
        self.h.ledger.append("roster:order", {"order": order},
                             claimant="system", basis="derived")
        self.h.ledger.append("dyadic:held-confidence",
                             {"persona": pid, "confidence": 0.5},
                             claimant="system", basis="derived", confidence=0.5)
        self._open_asset_needs(pid, name)
        self.assign_voice(pid)
        self.compose_portrait(pid)
        self.h.stage.prepare_ack(pid)
        return pid

    def _open_asset_needs(self, pid, name):
        """Persona creation opens procedural-asset needs (C-BoundPortrait):
        portrait + acknowledgement snippet, fulfilled in background."""
        self.h.needs.create(
            "asset", f"portrait for {name}",
            template={"slots": {"persona": pid},
                      "required": ["portrait-file"],
                      "satisfaction": ["portrait bound", "need closes"]},
            claimant="system", basis="generated-need",
            persona=pid, asset="portrait")
        self.h.needs.create(
            "asset", f"acknowledgement snippet for {name}",
            template={"slots": {"persona": pid},
                      "required": ["ack-wav"],
                      "satisfaction": ["ack bound", "need closes"]},
            claimant="system", basis="generated-need",
            persona=pid, asset="ack")

    # ---------- portrait ----------
    def compose_portrait(self, pid):
        """Portrait-quality art bound automatically (C-BoundPortrait):
        LLM art path when a live model exists — the model authors an SVG
        scene; absent → declared fallback tile, its not-authored status
        legible on the surface."""
        persona = self.h.ledger.view()["personas"].get(pid) or {}
        name = persona.get("name", pid)
        art_dir = os.path.join(self.h.dir, "personas", pid)
        os.makedirs(art_dir, exist_ok=True)
        svg, path = None, None
        live = self.h.engines["llm"].get("live")
        if live and "stub-engines" not in self.h.sabotage:
            from .engines import llm
            prompt = (
                "Author an SVG portrait (viewBox 0 0 240 300) of a persona "
                f"named {name}. Character: {persona.get('character', '')}. "
                "Style: bold flat shapes, a head-and-shoulders bust, a "
                "distinct silhouette fitting the character, a background "
                "mood fitting their register. Reply with ONLY the svg "
                "markup, no fences.")
            out, _ = llm(prompt, timeout=45, temperature=0.8)
            if out and "<svg" in out:
                svg = out[out.index("<svg"):]
                if "</svg>" in svg:
                    svg = svg[:svg.index("</svg>") + 6]
        if svg:
            path = os.path.join(art_dir, "portrait.svg")
            with open(path, "w", encoding="utf-8") as f:
                f.write(svg)
            self.h.ledger.append("asset:produced",
                                 {"persona": pid, "asset": "portrait",
                                  "file": path, "authored": "llm-art"},
                                 claimant="system", basis="generated")
        else:
            initials = "".join(w[0] for w in name.split()[:2]).upper() or "?"
            hue = (hash(name) % 360)
            svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 300">'
                   f'<rect width="240" height="300" fill="hsl({hue},35%,30%)"/>'
                   f'<circle cx="120" cy="115" r="62" fill="hsl({hue},30%,55%)"/>'
                   f'<text x="120" y="132" font-size="52" text-anchor="middle" '
                   f'fill="hsl({hue},40%,90%)" font-family="serif">{initials}</text>'
                   f'<rect y="256" width="240" height="44" fill="hsl({hue},30%,20%)"/>'
                   f'<text x="120" y="284" font-size="17" text-anchor="middle" '
                   f'fill="#ddd" font-family="serif">{name} — fallback</text></svg>')
            path = os.path.join(art_dir, "portrait.svg")
            with open(path, "w", encoding="utf-8") as f:
                f.write(svg)
            self.h.ledger.append("asset:produced",
                                 {"persona": pid, "asset": "portrait",
                                  "file": path, "authored": "fallback-declared"},
                                 claimant="system", basis="generated")
        self.h.ledger.append("persona:extended",
                             {"persona": pid, "portrait": {"file": path,
                              "authored": "llm-art" if live and svg else
                                          "fallback-declared"}},
                             claimant="system", basis="derived")
        # close the portrait asset need
        for nid, n in self.h.needs.open_needs().items():
            if n.get("persona") == pid and n.get("asset") == "portrait":
                self.h.needs.fulfill(nid, result={"file": path}, by="asset-pipeline")
        return {"ok": True, "file": path,
                "authored": "llm-art" if live and svg else "fallback-declared"}

    # ---------- voices ----------
    def voice_catalog(self):
        """The device's voice catalog (C-VoiceSelectFloor) plus trait
        mappings — the spec is portable preference, local engine mapping
        renders it (C-VoiceSpec, C-EngineMapping)."""
        base = self.h.engines.get("voices") or []
        catalog = []
        for v in base:
            gender = (v.get("gender") or "").lower()
            for variant, traits in (
                    ("base", {"rate": 0, "pitch": "natural"}),
                    ("low", {"rate": -1, "pitch": "low"}),
                    ("bright", {"rate": 1, "pitch": "bright"}),
                    ("slow", {"rate": -3, "pitch": "warm"})):
                catalog.append({
                    "id": f"{v['name']}|{variant}", "voice": v["name"],
                    "gender": gender, "traits": traits,
                    "description": f"{v['name']} — {traits['pitch']}, "
                                   f"rate {traits['rate']:+d}"})
        return catalog

    def assign_voice(self, pid, wanted_traits=None, name=None):
        """Judged assignment at creation: appropriateness from available
        descriptions + variety (in-use voices disfavored); stable once
        assigned (S-voice-assign)."""
        v = self.h.ledger.view()
        existing = v["personas"].get(pid, {}).get("voice")
        if existing:  # stability: never reassign without user direction
            return existing
        catalog = self.voice_catalog()
        if not catalog:
            self.h.ledger.append("voice:spec",
                                 {"persona": pid, "assigned": None,
                                  "declared": "thin/absent voice pool — no "
                                              "voices installed on this device"},
                                 claimant="system", basis="honest-absence")
            return None
        used = {p.get("voice", {}).get("id")
                for p in v["personas"].values() if p.get("voice")}
        family = (wanted_traits or {}).get("family", [])
        rate_want = (wanted_traits or {}).get("rate", 0)
        scored = []
        for c in catalog:
            score = 0
            if family and c["gender"] in family:
                score += 10
            score -= abs(c["traits"]["rate"] - rate_want)
            if c["id"] in used:
                score -= 8          # variety: used voices disfavored
            scored.append((score, c))
        scored.sort(key=lambda x: -x[0])
        chosen = scored[0][1]
        reasons = (f"family match={family or 'any'}; rate≈{rate_want}; "
                   f"variety: {len(used)} voices already in use — "
                   f"in use candidates disfavored")
        spec = {"persona": pid, "assigned": chosen["id"],
                "engine": chosen["voice"], "traits": chosen["traits"],
                "reasons": reasons, "poolSize": len(catalog),
                "stable": "changes only on user direction"}
        self.h.ledger.append("voice:spec", spec, claimant="system",
                             basis="assignment-judgment", certainty=0.8)
        self.h.ledger.append("persona:extended",
                             {"persona": pid, "voice": chosen},
                             claimant="system", basis="derived")
        return chosen

    def user_assign_voice(self, pid, voice_id):
        """Manual reassignment — the user's path (S-voice-select)."""
        catalog = {c["id"]: c for c in self.voice_catalog()}
        chosen = catalog.get(voice_id)
        if not chosen:
            return {"ok": False, "error": "no such voice"}
        self.h.ledger.append("voice:spec",
                             {"persona": pid, "assigned": chosen["id"],
                              "engine": chosen["voice"], "traits": chosen["traits"],
                              "reasons": "user direction", "byUser": True},
                             claimant="principal", basis="user-set",
                             certainty=1.0)
        self.h.ledger.append("persona:extended",
                             {"persona": pid, "voice": chosen},
                             claimant="principal", basis="user-set")
        return {"ok": True, "voice": chosen}

    # ---------- roster / dyadic ----------
    def roster(self):
        v = self.h.ledger.view()
        order = v["roster"] or list(v["personas"].keys())
        return [{"id": pid, **v["personas"].get(pid, {}),
                 "held": v["dyadic"].get(pid, 0.5),
                 "surface": v["assignments"].get(pid, "host")}
                for pid in order if pid in v["personas"]]

    def move(self, pid, direction):
        """Reorder the roster; every move produces a visible dyadic
        consequence — the moved persona's held-confidence differentiates
        on EVERY move, even among equal neighbors (C-PerceivableDyadic).
        I-Dyadic: pick the simplest representable value between
        neighbors; each reorder is a fresh append."""
        v = self.h.ledger.view()
        order = list(v["roster"])
        if pid not in order:
            return {"ok": False, "error": "not on roster"}
        i = order.index(pid)
        j = i + (-1 if direction == "up" else 1)
        if j < 0 or j >= len(order):
            return {"ok": False, "error": "edge of roster"}
        order[i], order[j] = order[j], order[i]
        self.h.ledger.append("roster:order", {"order": order},
                             claimant="principal", basis="user-set")
        # dyadic consequence — always a fresh, differentiated value
        prev = v["dyadic"].get(pid, 0.5)
        neighbor = order[j + 1] if direction == "up" else order[j - 1]
        nb = v["dyadic"].get(neighbor, 0.5)
        if prev != nb:
            new = round((prev + nb) / 2, 3)      # simplest between neighbors
        else:
            new = round(prev + (0.05 if direction == "up" else -0.05), 3)
            new = min(0.95, max(0.05, new))
        self.h.ledger.append("dyadic:held-confidence",
                             {"persona": pid, "confidence": new,
                              "previous": prev,
                              "moved": direction, "neighbor": neighbor},
                             claimant="system", basis="derived", confidence=new)
        return {"ok": True, "order": order, "held": new, "previous": prev}

    def select(self, pid):
        self.h.ledger.append("persona:selected",
                             {"persona": pid}, claimant="principal",
                             basis="user-set")
        return {"ok": True}

    # ---------- editor ----------
    def edit(self, pid, fields):
        """Editor path: every customizable element editable; edits are
        recorded as assertions (S-personality-editor)."""
        allowed = ("name", "register", "character", "interests", "history",
                   "surface", "style")
        updates = {k: val for k, val in fields.items() if k in allowed}
        if not updates:
            return {"ok": False, "error": "no editable fields"}
        self.h.ledger.append("persona:edited",
                             {"persona": pid, **updates},
                             claimant="principal", basis="user-set")
        if "surface" in updates:
            self.h.ledger.append("persona:surface",
                                 {"persona": pid, "surface": updates["surface"]},
                                 claimant="principal", basis="user-set")
        return {"ok": True, "updated": list(updates)}

    # ---------- source matching ----------
    def suggest_sources(self, persona_domains):
        """Domain-matched suggestion at creation (S-personality-source-
        match): the persona's declared domain matches a seeded source's
        domains — discriminating (star-trek → memory-alpha, not simpsons)."""
        v = self.h.ledger.view()
        pdom = {d.lower() for d in persona_domains}
        scored = []
        for key, s in v["sources"].items():
            sdom = {d.lower() for d in s.get("domains", [])}
            inter = pdom & sdom
            if inter:
                scored.append((len(inter), key, s["name"], sorted(inter)))
        scored.sort(key=lambda x: -x[0])
        return [{"source": k, "name": n, "matchedOn": m}
                for _, k, n, m in scored[:3]]

    def grant_source(self, pid, source_key, accept=True):
        """Accept binds the assignment as the grant row; decline leaves
        the persona honestly source-free."""
        if accept:
            self.h.ledger.append("persona:source-grant",
                                 {"persona": pid, "source": source_key,
                                  "granted": True},
                                 claimant="principal", basis="user-set")
            return {"ok": True, "granted": source_key}
        self.h.ledger.append("persona:source-grant",
                             {"persona": pid, "source": source_key,
                              "granted": False, "declared": "source-free"},
                             claimant="principal", basis="user-set")
        return {"ok": True, "declined": source_key}
