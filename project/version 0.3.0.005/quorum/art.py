"""Quorum persona art — LLM-authored portraits (V-A bar).

The owner's bar: persona visual identity reads as AUTHORED imagery of that
specific persona — a generative/LLM art path, not procedural sprites.
Mechanism here: the local LLM authors an SVG portrait from the persona's
name, traits, characterization, and register; the host validates the output
(parses as XML, carries drawable elements) and binds it to the persona.
A deterministic composition is only the declared offline fallback — labeled
`generator: fallback`, never passed off as authored art (C-DeclaredStubs).
"""
from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET

from . import rows

ART_DIR_NAME = "persona-art"

PROMPT = """Author an SVG portrait bust for a personality named "{name}".
Character: {character}
Traits: {traits}
Register: {register} (let the art style reflect it).

Requirements:
- Output ONLY the SVG, no prose, no markdown fences.
- viewBox="0 0 240 280". A recognizable bust portrait: head, shoulders,
  background composition that reflects THIS character.
- Use filled shapes, paths, and a considered palette — authored imagery,
  not a generic placeholder. Give the face distinctive features.
"""

def _extract_svg(text: str) -> str:
    m = re.search(r"<svg[\s\S]*?</svg>", text or "", re.I)
    return m.group(0) if m else ""

def _valid(svg: str) -> bool:
    try:
        root = ET.fromstring(svg)
    except ET.ParseError:
        return False
    tag = root.tag.lower().split("}")[-1]
    if tag != "svg":
        return False
    drawables = {"rect", "circle", "ellipse", "path", "polygon", "line"}
    found = {el.tag.lower().split("}")[-1] for el in root.iter()}
    return bool(drawables & found) and len(svg) > 300

def generate(llm, persona: dict, out_dir: str) -> dict:
    """Author the portrait through the LLM. Returns {path, generator, note}."""
    os.makedirs(out_dir, exist_ok=True)
    name = persona.get("name", "persona")
    character = persona.get("characterization") or "a helpful local companion"
    traits = ", ".join(persona.get("traits") or ["plain"])
    register = persona.get("register", "casual")
    prompt = PROMPT.format(name=name, character=character,
                           traits=traits, register=register)
    svg = ""
    attempts = []
    if llm.available():
        for i in range(2):                      # author, retry once on malform
            r = llm.complete(prompt if i == 0 else
                             prompt + "\nYour last output did not parse as SVG. "
                             "Output ONLY valid <svg>...</svg>.",
                             role="draft", max_tokens=1400)
            attempts.append({"attempt": i + 1, "ok": r.get("ok"),
                             "chars": len(r.get("text", ""))})
            if r.get("ok"):
                svg = _extract_svg(r["text"])
                if _valid(svg):
                    break
                svg = ""
    if svg:
        generator = "llm-authored"
        note = "portrait authored by the local LLM for this persona"
    else:
        svg = _fallback(persona)
        generator = "fallback-declared"
        note = ("LLM art path unavailable/malformed — declared fallback "
                "composition, not authored art")
    path = os.path.join(out_dir, f"{persona['id']}.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return {"path": path, "generator": generator, "note": note,
            "attempts": attempts}

def _fallback(persona: dict) -> str:
    """Deterministic seed composition — the DECLARED fallback, visibly
    labeled in metadata; not presented as authored art."""
    name = persona.get("name", "?")
    seed = sum(ord(c) for c in persona.get("id", name))
    h1, h2 = seed % 360, (seed * 7) % 360
    initials = "".join(w[0] for w in name.split()[:2]).upper() or "?"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 280">'
        f'<rect width="240" height="280" fill="hsl({h1},35%,88%)"/>'
        f'<circle cx="120" cy="105" r="58" fill="hsl({h2},40%,72%)"/>'
        f'<rect x="60" y="170" width="120" height="90" rx="30" '
        f'fill="hsl({h2},35%,55%)"/>'
        f'<text x="120" y="118" font-size="44" text-anchor="middle" '
        f'fill="hsl({h1},40%,30%)">{initials}</text>'
        f'<text x="120" y="262" font-size="11" text-anchor="middle" '
        f'fill="#666">fallback composition — not authored art</text></svg>')
