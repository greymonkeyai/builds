"""hearth personas — distinct persistent participants.
Persistent identity outside semantic rows (privileged class: indices);
roster ordering via dyadic confidence assertions (I-Dyadic: simplest
representable value between neighbors; every move differentiates —
C-PerceivableDyadic); portraits generated + bound automatically
(C-BoundPortrait); voices assigned with judgment, stable, user-directable
(S-voice-assign); imitation mark + admonishment for recognizable figures
(prompt §Personalities, C-EthicsGate).
"""
import hashlib
import os
import struct
import time
import zlib
from . import audio
RECOGNIZABLE = {"simpson": "fictional-ok", "darth vader": "fictional-ok"}
LIVING_MARK = "living-or-recent"
def _pid(name):
    return "p-" + hashlib.sha1(name.lower().encode()).hexdigest()[:10]
def _png(width, height, pixels):
    """Minimal PNG encoder — real generated art files."""
    raw = b""
    for y in range(height):
        raw += b"\x00" + pixels[y * width * 3:(y + 1) * width * 3]
    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + \
            struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))
def render_portrait(path, persona):
    """Procedural portrait — deterministic per persona, unique palette +
    composition. Declared generative path: procedural-render."""
    seed = int(hashlib.sha1(persona["id"].encode()).hexdigest()[:8], 16)
    w = h = 96
    px = bytearray(w * h * 3)
    c1 = [(seed >> s & 0x7F) + 64 for s in (0, 8, 16)]
    c2 = [(seed >> s & 0x7F) + 32 for s in (5, 13, 21)]
    c3 = [(seed >> s & 0xFF) for s in (3, 11, 19)]
    cx = 40 + (seed >> 9) % 16
    cy = 34 + (seed >> 12) % 8
    for y in range(h):
        for x in range(w):
            i = (y * w + x) * 3
            t = y / h
            px[i] = int(c1[0] * (1 - t) + c2[0] * t)
            px[i + 1] = int(c1[1] * (1 - t) + c2[1] * t)
            px[i + 2] = int(c1[2] * (1 - t) + c2[2] * t)
            dx, dy = x - cx, y - cy
            if dx * dx + dy * dy < 15 * 15:  # head
                px[i], px[i + 1], px[i + 2] = c3
                if dx * dx + dy * dy < 5 * 5:
                    px[i], px[i + 1], px[i + 2] = 240, 240, 240
            if dx * dx + (dy - 40) * (dy - 40) < 28 * 28 and dy > 8:
                px[i] = min(255, px[i] + 40)  # shoulders glow
            if (x // 8 + y // 8) % 2 == (seed >> 4) % 2:
                px[i] = px[i] * 9 // 10
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(_png(w, h, bytes(px)))
    return path
SHIPPED = [
    {"name": "Hazel", "register": "warm-domestic",
     "character": "keeps the home's weather, meals, and small comforts in "
                  "mind; speaks in homely images",
     "interests": ["weather", "meals", "home", "garden", "comfort"],
     "domains": ["general-knowledge", "geography", "reference"],
     "gender": "female"},
    {"name": "Marcus", "register": "dry-engineer",
     "character": "precise, skeptical, wants the mechanism before the "
                  "story; short declarative sentences",
     "interests": ["systems", "tools", "machines", "networks"],
     "domains": ["computer-science", "technical-reports", "reference"],
     "gender": "male"},
    {"name": "Plum", "register": "whimsical-storyteller",
     "character": "answers slantwise, loves fables and fictional worlds, "
                  "steers toward tales",
     "interests": ["stories", "fantasy", "star-trek", "games", "jokes"],
     "domains": ["star-trek", "fantasy", "literature", "games"],
     "gender": "female"},
    {"name": "Vera", "register": "direct-archivist",
     "character": "clipped, factual, cites what the ledger holds, "
                  "dislikes speculation",
     "interests": ["records", "lists", "evidence", "history", "orders"],
     "domains": ["reference", "historical-documents", "geography"],
     "gender": "female"},
]
class Personas:
    def __init__(self, host):
        self.h = host
        self.selected = []
        self.portrait_dir = os.path.join(host.data_dir, "portraits")
        os.makedirs(self.portrait_dir, exist_ok=True)
    # ---- lifecycle ----------------------------------------------------
    def ship(self):
        """Mint shipped personas once; identity preserved in indices."""
        if self.h.indices["personas"]:
            return
        for spec in SHIPPED:
            self.mint(spec["name"], spec, claimant="system",
                      basis="system", shipped=True)
        self.selected = list(self.h.indices["personas"].keys())[:1]
    def mint(self, name, spec=None, claimant="user", basis="user-choice",
             shipped=False, register=None, character=None,
             interests=None, domains=None):
        pid = _pid(name + str(len(self.h.indices["personas"]))
                   if name in self.h.indices["personas"] else name)
        spec = spec or {}
        persona = {
            "id": pid, "name": name,
            "register": register or spec.get("register", "plain"),
            "character": character or spec.get("character", ""),
            "interests": interests or spec.get("interests", []),
            "domains": domains or spec.get("domains", []),
            "sources": [], "voice": None, "portrait": None,
            "dyadic": 0.5,          # dyadic default 0.5
            "surfaces": ["chat"],
            "imitation": None,      # set when recognizable figure
            "createdAt": time.time(), "shipped": shipped,
        }
        # Ethics gate: recognizable living/recently-deceased figure →
        # admonish + permanent distinguishing mark
        if self._imitation_of_living(name, spec):
            persona["imitation"] = {
                "of": name, "mark": "imitation",
                "admonished": True,
                "note": "imitation of a point of view — not the "
                        "person's identity or authority"}
            self.h.journal.append(
                "ethics-admonition",
                {"persona": pid, "of": name,
                 "mark": "display carries a permanent imitation mark"},
                claimant="system", basis="system")
        self.h.indices["personas"][pid] = persona
        self.h.save_indices()
        self.h.journal.append(
            "persona-attr", {"persona": pid,
                             "attrs": {k: persona[k] for k in
                                       ("name", "register", "character",
                                        "interests", "domains")}},
            claimant=claimant, basis=basis)
        self.h.journal.append(
            "dyadic-rank", {"persona": pid, "value": 0.5},
            claimant="system", basis="claim")
        self.assign_voice(persona)
        return persona
    def _imitation_of_living(self, name, spec):
        if spec.get("imitatesLiving"):
            return True
        # user-declared imitation target living/recently deceased
        return bool(spec.get("imitationTarget") and
                    spec.get("livingOrRecent"))
    def get(self, pid):
        return self.h.indices["personas"].get(pid)
    def by_name(self, name):
        for p in self.h.indices["personas"].values():
            if p["name"].lower() == name.lower():
                return p
        return None
    def roster(self):
        """Ordered by dyadic confidence, then recency of assignment."""
        persons = list(self.h.indices["personas"].values())
        persons.sort(key=lambda p: (-p.get("dyadic", 0.5),
                                    p["createdAt"]))
        return persons
    def reorder(self, ordered_ids, claimant="user"):
        """Roster reorder: every move produces a dyadic change — the new
        value is the simplest representable value between the persona's
        new neighbors, appended as a fresh assertion."""
        roster = self.roster()
        pos = {pid: i for i, pid in enumerate(ordered_ids)}
        roster.sort(key=lambda p: pos.get(p["id"], len(pos)))
        vals = [p.get("dyadic", 0.5) for p in roster]
        for i, p in enumerate(roster):
            if len(roster) == 1:
                newv = 0.5
            elif i == 0:
                newv = min(1.0, vals[0] + 0.5 * (1 - vals[0]))
            elif i == len(roster) - 1:
                newv = vals[-1] * 0.5
            else:
                lo, hi = vals[i + 1], vals[i - 1]
                newv = round((lo + hi) / 2, 3)
                if newv == vals[i]:
                    newv = round((vals[i] + hi) / 2, 4)
            if newv != p.get("dyadic"):
                p["dyadic"] = newv
                self.h.journal.append(
                    "dyadic-rank", {"persona": p["id"], "value": newv,
                                    "position": i},
                    claimant=claimant, basis="user-choice")
        self.h.save_indices()
        return roster
    def edit(self, pid, field, value, claimant="user"):
        """Editor path — every customizable element editable; edits
        recorded as assertions."""
        p = self.get(pid)
        if not p or field not in ("name", "register", "character",
                                  "interests", "domains", "surfaces",
                                  "voice"):
            return None
        p[field] = value
        self.h.save_indices()
        self.h.journal.append(
            "persona-attr", {"persona": pid, "attrs": {field: value}},
            claimant=claimant, basis="user-choice")
        return p
    # ---- portraits -----------------------------------------------------
    def bind_portrait(self, persona, generative="procedural-render"):
        path = os.path.join(self.portrait_dir, persona["id"] + ".png")
        try:
            render_portrait(path, persona)
            bound = path
            declared = generative
            fallback = False
        except Exception as e:
            # declared fallback: still binds an image; not-authored
            # status legible
            bound = os.path.join(self.h.root, "fixtures",
                                 "portrait-fallback.png")
            declared = "fallback-declared"
            fallback = True
            self.h.journal.append(
                "portrait-fallback", {"persona": persona["id"],
                                      "reason": str(e)},
                claimant="system", basis="system")
        persona["portrait"] = {"path": bound, "generative": declared,
                               "fallback": fallback}
        self.h.save_indices()
        self.h.journal.append(
            "persona-artifact",
            {"persona": persona["id"], "kind": "portrait",
             "path": bound, "generative": declared,
             "fallback": fallback},
            claimant="tool:art.procedural", basis="execution-evidence")
        return persona["portrait"]
    # ---- voices --------------------------------------------------------
    def voice_pool(self):
        return self.h.engines.get("tts", {}).get("voices", [])
    def used_voices(self):
        return {p["voice"]["name"] for p in
                self.h.indices["personas"].values()
                if p.get("voice")}
    def assign_voice(self, persona):
        """Judged assignment: appropriateness to persona traits + variety
        (in-use voices disfavored). Stable once set — changes only on
        user direction."""
        if persona.get("voice"):
            return persona["voice"]  # stable — never changes uninvited
        pool = self.voice_pool()
        if not pool:
            persona["voice"] = None
            self.h.journal.append(
                "voice-assign",
                {"persona": persona["id"], "voice": None,
                 "note": "thin/absent voice pool declared"},
                claimant="system", basis="claim", certainty=0.4)
            return None
        used = self.used_voices()
        pg = (persona.get("gender") or "u")[0].lower()
        gender_match = [v for v in pool
                        if v["gender"].lower().startswith(pg)]
        pref = gender_match or pool
        # variety: prefer unused voices
        unused = [v for v in pref if v["name"] not in used] or pref
        pick = unused[0]
        persona["voice"] = {
            "name": pick["name"], "gender": pick["gender"],
            "reason": "gender-fit over pool; in-use voices disfavored",
            "assignedAt": time.time(), "stable": True}
        self.h.save_indices()
        self.h.journal.append(
            "voice-assign",
            {"persona": persona["id"], "voice": pick["name"],
             "reason": persona["voice"]["reason"],
             "poolSize": len(pool), "usedAtAssign": sorted(used)},
            claimant="system", basis="claim")
        return persona["voice"]
    def voice_spec(self, persona):
        """QR-fittable transferable voice spec — ranked family + traits,
        minimal payload (C-VoiceSpec)."""
        v = persona.get("voice") or {}
        g = (v.get("gender") or "unknown").lower()
        spec = {"f": [{"g": g[0] if g else "u",
                       "fam": "sapi-" + g, "rank": 1}],
                "t": {"rate": 0,
                      "reg": persona.get("register", "plain")[:12]}}
        return spec
    # ---- surface assignment / selector ---------------------------------
    def select(self, ids):
        self.selected = list(ids)
    def selected_personas(self):
        out = [self.get(pid) for pid in self.selected]
        return [p for p in out if p]
    def view(self):
        out = []
        for p in self.roster():
            v = dict(p)
            v["selected"] = p["id"] in self.selected
            v["voiceSpec"] = self.voice_spec(p)
            out.append(v)
        return out
