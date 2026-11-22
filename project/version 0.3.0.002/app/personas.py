"""Personalities: persistent participants interpreting the shared ledger
through their own lenses.

Identity is a privileged class of persistent object: kept outside the
ledger's semantic records (runtime/personalities.json), scoped to the
installation, intended to diverge across installations. The ledger still
records the assertions *about* a persona (traits, voice, portrait, marks) —
the identity file is the index, not a second truth store.

Imitation boundary: a persona imitating a recognizable person living or
deceased within ten years requires the user be admonished and the persona to
carry a permanent distinguishing mark.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Optional

from .model import new_id


class PersonaStore:
    def __init__(self, path: str, ctx):
        self.path = path
        self.ctx = ctx
        self.personas: dict[str, dict] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                for p in json.load(f):
                    self.personas[p["id"]] = p

    def _save(self):
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(list(self.personas.values()), f, indent=2, ensure_ascii=False)

    def get(self, pid: str) -> Optional[dict]:
        return self.personas.get(pid)

    def by_subject(self, subject: str) -> Optional[dict]:
        pid = subject.split(":", 1)[1] if ":" in subject else subject
        return self.personas.get(pid)

    def roster(self) -> list[dict]:
        out = sorted(self.personas.values(),
                     key=lambda p: (-p.get("rosterPriority", 0.5), p["name"]))
        return [self.public_view(p) for p in out]

    def public_view(self, p: dict) -> dict:
        v = dict(p)
        v["imitation"] = bool(p.get("imitates"))
        v["mark"] = self.distinguishing_mark(p) if p.get("imitates") else None
        if "art" not in v:
            rows = self.ctx.ledger.query(subject=f"persona:{p['id']}",
                                         predicate="persona:art")
            if rows:
                v["art"] = rows[-1].value["v"]
        return v

    # ---- mint / edit ----

    def mint(self, name: str, traits: list, interests: list, lens: dict,
             voice: Optional[dict], imitates: Optional[dict],
             claimant: str, admonish_cb=None) -> dict:
        from . import ethics as E
        gate = E.evaluate(self.ctx, name, imitates, claimant)
        if gate["verdict"] == "refused":
            self.ctx.append("persona", "persona:mint-refused",
                            {"name": name, "imitates": imitates,
                             "gate": gate}, "system",
                            basis={"kind": "refusal"})
            if admonish_cb:
                admonish_cb(f"persona '{name}' refused by ethics gate: "
                            + "; ".join(gate["reasons"]))
            return {"refused": True, "gate": gate, "id": None, "name": name}
        pid = new_id("persona")
        color = "#" + hashlib.md5(pid.encode()).hexdigest()[:6]
        if not voice:
            voice = self._assign_voice(pid)
        p = {"id": pid, "name": name, "traits": traits, "interests": interests,
             "lens": lens or {}, "voice": voice,
             "imitates": imitates, "color": color, "rosterPriority": 0.5,
             "confidence": 0.8, "mintedAt": __import__("time").time(),
             "toolPermissions": [], "displayMode": "respondent",
             "ethicsVerdict": gate["verdict"]}
        self.personas[pid] = p
        self._save()
        subj = f"persona:{pid}"
        self.ctx.append(subj, "persona:exists", {"name": name}, claimant,
                        basis={"kind": "user-choice"})
        self.ctx.append(subj, "persona:name", name, claimant)
        for t in traits:
            self.ctx.append(subj, "persona:trait", t, claimant)
        for i in interests:
            self.ctx.append(subj, "persona:interest", i, claimant)
        self.ctx.append(subj, "persona:voice", voice, claimant,
                        basis={"kind": "config"})
        if imitates:
            self.ctx.append(subj, "persona:imitates", imitates["name"], claimant)
            mark = self.distinguishing_mark(p)
            self.ctx.append(subj, "persona:imitation-mark", mark, "system")
            if imitates.get("recency") in ("living", "deceased-10y"):
                self.ctx.append(subj, "persona:admonished",
                                {"message": self.admonition(p)}, "system",
                                basis={"kind": "durable-result"})
                if admonish_cb:
                    admonish_cb(self.admonition(p))
        # C-PersonalityArt: unique generated art, asserted + artifacted
        try:
            from . import art as ART
            rec = ART.render_art(self.ctx, p,
                                 os.path.join(self.ctx.artifacts, "persona-art"))
            p["art"] = {"artifact": rec["artifact"], "motif": rec["motif"],
                        "frame": rec["frame"], "dataUrl": rec["dataUrl"]}
            self._save()
        except Exception as e:
            self.ctx.append(subj, "persona:art",
                            {"error": repr(e)}, "engine:portrait",
                            basis={"kind": "execution"})
        return p

    def _assign_voice(self, pid: str) -> dict:
        """C-VoiceDiversity: a diverse, modifiable default voice per persona.
        Rotates installed SAPI voices and varies rate; the choice is a
        persona:voice assertion the user can change."""
        voices = []
        try:
            voices = self.ctx.engines.tts.voices()
        except Exception:
            voices = []
        idx = len(self.personas) + int(hashlib.md5(pid.encode()).hexdigest()[:2], 16)
        name = voices[idx % len(voices)] if voices else "sapi-default"
        rate = [-2, -1, 0, 1, 2][idx % 5]
        return {"engine": "sapi", "name": name, "rate": rate,
                "assigned": "rotated-default"}

    def update(self, pid: str, fields: dict, claimant: str = "principal") -> Optional[dict]:
        p = self.personas.get(pid)
        if not p:
            return None
        p.update(fields)
        self._save()
        subj = f"persona:{pid}"
        for k, v in fields.items():
            pred = {"name": "persona:name", "traits": "persona:trait",
                    "interests": "persona:interest",
                    "rosterPriority": "persona:roster-priority",
                    "displayMode": "persona:display-mode"}.get(k)
            if pred:
                self.ctx.append(subj, pred, v, claimant,
                                basis={"kind": "user-choice"})
        return p

    # ---- imitation boundary ----

    @staticmethod
    def admonition(p: dict) -> str:
        name = (p.get("imitates") or {}).get("name", "")
        return (f"'{p['name']}' presents an imitation of {name}'s point of view — "
                f"not the person's identity, authority, or endorsement. It carries a "
                f"permanent distinguishing mark wherever it appears.")

    @staticmethod
    def distinguishing_mark(p: dict) -> dict:
        return {"badge": "IMITATION", "prefix": "◆",
                "note": f"imitates {(p.get('imitates') or {}).get('name', '')}",
                "portraitCorner": "diamond"}

    # ---- voice / frame helpers ----

    def frame(self) -> str:
        """Non-anthropomorphic presentation option (A12): 'respondent' (neutral
        lenses) or 'personified'. User choice recorded as an assertion."""
        rows = self.ctx.ledger.query(subject="user-settings",
                                     predicate="user:persona-frame")
        return rows[-1].value["v"] if rows else "respondent"
