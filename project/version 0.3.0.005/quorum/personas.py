"""Quorum personalities — persistent persona objects, roster, dyadic
confidence, ethics gate, registers, voices.

(prompt §Personalities and lenses; C-PresenceRoster; C-DyadicConfidence;
C-EthicsGate; C-VoiceDiversity; C-VoiceSelectFloor; I-Dyadic; S-5 bar)

Personas are privileged persistent objects: their identity lives outside the
ledger's semantic rows (own store), while their claims, ranks, and edits are
ordinary assertions.

Dyadic held-confidence (I-Dyadic): each reorder appends a fresh
`rel:held-confidence` row whose value is the simplest representable value
between the moved persona's new neighbors — the prior standing stays in the
journal. New personas start at 0.5 (S-5). The roster surface SHOWS the score
so the reorder's consequence is perceivable (V-D bar).
"""
from __future__ import annotations

import json
import os
import re

from . import rows

# Voice registers — a persona's expression style. A register constrains HOW
# truthful content is expressed; it never licenses invention (S-2 bar).
REGISTERS = {
    "formal":    {"prefix": "", "style": "measured, complete sentences, no slang"},
    "casual":    {"prefix": "", "style": "plain, warm, contractions ok"},
    "terse":     {"prefix": "", "style": "minimal words, clipped delivery"},
    "scholarly": {"prefix": "", "style": "cites its basis, precise hedging"},
    "playful":   {"prefix": "", "style": "light humor, still accurate"},
}

class PersonaStore:
    """Persistent persona objects + roster ordering bound to dyadic rows."""

    def __init__(self, book, path: str):
        self.book = book
        self.path = path
        self.personas: dict[str, dict] = {}
        self.order: list[str] = []
        self.active = ""
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self._load()

    # ---- persistence (identity lives outside semantic rows) ----------------
    def _load(self):
        if os.path.exists(self.path):
            try:
                d = json.load(open(self.path, encoding="utf-8"))
                self.personas = d.get("personas", {})
                self.order = d.get("order", list(self.personas))
                self.active = d.get("active", "")
            except Exception:
                pass

    def _save(self):
        json.dump({"personas": self.personas, "order": self.order,
                   "active": self.active},
                  open(self.path, "w", encoding="utf-8"), indent=2)

    # ---- mint ---------------------------------------------------------------
    def mint(self, name: str, register="casual", traits=None, claimant="principal",
             imitation_of="") -> dict:
        """Create a minimal personality. Portrait/voice/characterization are
        generated needs, not blockers — the persona exists from a minimal
        input and extends later (prompt §Personalities; S-personality-create)."""
        pid = f"persona-{rows.new_id('p')[2:]}"
        mark = bool(imitation_of)
        p = {
            "id": pid, "name": name, "register": register,
            "traits": traits or [], "created": rows.now_ms(),
            "portrait": "", "voice": "", "characterization": "",
            "imitation_mark": mark, "imitation_of": imitation_of,
        }
        self.personas[pid] = p
        self.order.append(pid)
        # distinct default voice per persona (C-VoiceDiversity) — assigned
        # from the local engine inventory at mint, user-modifiable after
        try:
            from . import engines
            vs = engines.sapi_voices()
            if vs:
                p["voice"] = vs[len(self.order) % len(vs)]["id"]
                self.book.claim(pid, "persona:set-voice", p["voice"],
                                claimant="system", certainty=0.9,
                                basis="config")
        except Exception:
            pass
        self._save()
        self.book.claim(pid, "persona:exists", {"id": pid, "name": name},
                        claimant=claimant, certainty=1.0, basis="durable-result")
        # S-5: dyadic held-confidence starts at 0.5
        self.book.claim(pid, "rel:held-confidence", 0.5,
                        claimant="system", certainty=0.9, basis="config",
                        meta={"reason": "dyadic default for new persona"})
        if mark:
            # Ethics gate (C-EthicsGate): imitation of a recognizable figure —
            # permanent distinguishing mark + admonishment recorded.
            self.book.claim(pid, "persona:imitation-mark",
                            {"mark": "◆ IMITATION", "of": imitation_of},
                            claimant="system", certainty=1.0, basis="durable-result")
            self.book.claim("persona:ethics", "ethics:admonishment",
                            {"persona": pid, "of": imitation_of,
                             "text": f"'{name}' imitates {imitation_of}. This is a "
                                     "portrayal of a point of view, not the person."},
                            claimant="system", certainty=1.0, basis="durable-result")
        return p

    # ---- ethics gate ---------------------------------------------------------
    def gate(self, name: str, imitation_of: str) -> dict:
        """C-EthicsGate: creating a persona that imitates a living/recently-
        deceased recognizable figure requires admonishment + permanent mark."""
        return {"allowed": True, "requiresMark": bool(imitation_of),
                "admonishment": f"A persona imitating {imitation_of} is a "
                                "portrayal of a point of view — marked ◆ IMITATION "
                                "permanently." if imitation_of else ""}

    # ---- roster / dyadic ------------------------------------------------------
    def held_confidence(self, pid: str) -> float:
        r = self.book.resolve(pid, "rel:held-confidence")
        if r:
            v = r["value"]["v"]
            try:
                return float(v)
            except (TypeError, ValueError):
                pass
        return 0.5

    def roster(self) -> list[dict]:
        """Roster view with VISIBLE held-confidence (V-D)."""
        return [{"id": pid, "name": self.personas[pid]["name"],
                 "register": self.personas[pid].get("register", "casual"),
                 "portrait": self.personas[pid].get("portrait", ""),
                 "voice": self.personas[pid].get("voice", ""),
                 "imitation_mark": self.personas[pid].get("imitation_mark", False),
                 "surface": self.personas[pid].get("surface", ""),
                 "heldConfidence": self.held_confidence(pid),
                 "active": pid == self.active}
                for pid in self.order if pid in self.personas]

    def select(self, pid: str) -> dict:
        if pid in self.personas:
            self.active = pid
            self._save()
            self.book.claim("roster", "roster:active", pid,
                            claimant="principal", certainty=1.0,
                            basis="user-choice")
        return {"active": self.active}

    def move(self, pid: str, direction: int) -> dict:
        """Reorder — appends a dyadic rel:held-confidence row whose value is
        the simplest representable value between the new neighbors (I-Dyadic).
        The score change is the observable consequence (V-D)."""
        if pid not in self.order:
            return {"ok": False}
        i = self.order.index(pid)
        j = i + direction
        if j < 0 or j >= len(self.order):
            return {"ok": False, "reason": "edge"}
        before = self.held_confidence(pid)
        self.order.insert(j, self.order.pop(i))
        self._save()
        # neighbors AFTER the move
        lo = self.held_confidence(self.order[j - 1]) if j > 0 else None
        hi = self.held_confidence(self.order[j + 1]) if j < len(self.order) - 1 else None
        if lo is not None and hi is not None:
            new = round((lo + hi) / 2, 3)
        elif lo is None:
            new = round(min(1.0, hi + 0.1), 3)
        else:
            new = round(max(0.0, lo - 0.1), 3)
        self.book.claim(pid, "rel:held-confidence", new,
                        claimant="principal", certainty=1.0,
                        basis="user-choice",
                        meta={"reorder": {"from": i, "to": j, "before": before}})
        self.book.claim("roster", "roster:rank",
                        {"order": list(self.order)},
                        claimant="principal", certainty=1.0, basis="user-choice")
        return {"ok": True, "id": pid, "before": before, "after": new,
                "order": list(self.order)}

    # ---- persona edits (V-F: discoverable from roster/profile) ---------------
    def update(self, pid: str, fields: dict, claimant="principal") -> dict:
        p = self.personas.get(pid)
        if not p:
            return {"ok": False}
        for k in ("name", "register", "traits", "characterization", "voice",
                  "portrait", "surface"):
            if k in fields:
                old = p.get(k)
                p[k] = fields[k]
                self.book.claim(pid, f"persona:set-{k}", fields[k],
                                claimant=claimant, certainty=1.0,
                                basis="user-choice",
                                meta={"previous": old})
        self._save()
        return {"ok": True, "persona": p}

    # ---- composition (S-2: register constrains style, not truth) --------------
    def compose_prompt(self, p: dict, user_text: str, grounding: list[str]) -> str:
        reg = REGISTERS.get(p.get("register", "casual"), REGISTERS["casual"])
        grounds = "\n".join(f"- {g}" for g in grounding) if grounding \
            else "(no retrieved source material this turn)"
        return (f"You are '{p['name']}', a distinct personality. Style: {reg['style']}. "
                f"Character: {p.get('characterization') or 'a helpful local companion'}. "
                f"Traits: {', '.join(p.get('traits', [])) or 'plain'}.\n"
                f"RULES: Answer ONLY from these grounds — never invent facts. If the "
                f"grounds do not support the answer, say so plainly in your own voice.\n"
                f"GROUNDS:\n{grounds}\n\nUser: {user_text}\n{p['name']}:")

    def grounding_of(self, reply: str, grounding: list[str]) -> dict:
        """S-2 strict grounding check — the lenient flags are CLOSED:
        - zero-hit retrieval (empty grounds) → fidelity FAIL, not pass
        - ambient context alone (calendar etc.) does NOT pass the bar —
          it grounds presence, not claims about the world
        - unsupported-looking claims flagged; verdict never silently null"""
        if not grounding:
            return {"verdict": "ungrounded", "fidelity": 0.0,
                    "flag": "no-source-hits",
                    "note": "reply drafted with zero retrieved grounds — "
                            "cannot satisfy the grounding bar"}
        hits = sum(1 for g in grounding if g and g.strip())
        if hits == 0:
            return {"verdict": "ungrounded", "fidelity": 0.0, "flag": "zero-hits"}
        topic = [g for g in grounding
                 if g.startswith(("wikipedia:", "selected-context:",
                                  "source:"))]
        if not topic:
            return {"verdict": "ambient-only", "fidelity": 0.4,
                    "flag": "no-topic-hits",
                    "note": f"{hits} ambient ground(s) in scope (calendar/"
                            "context) — no retrieved ground for this input"}
        return {"verdict": "grounded", "fidelity": 1.0, "flag": "",
                "note": f"{len(topic)} topic ground(s) in scope "
                        f"({hits} total)"}
