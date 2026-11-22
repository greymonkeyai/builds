"""Per-personality generated art (C-PersonalityArt) + presentation glass
(C-PresentationGlass: asset pipeline, portrait frames, ambient motion).

Every personality's art is *unique to that personality*: the composition is
seeded from the persona's identity (id), name, traits, and interests — never
shared or placeholder media. The generated SVG carries:
- a deterministic motif family derived from the persona's interests
- a palette derived from the persona's name + id
- ambient motion (real SVG animation — drifting elements, not a static image)
- a portrait frame keyed to the persona's display mode / imitation status

The asset pipeline is honest: `persona:art` assertions record the seed,
motif, palette, and artifact path. When a persona's traits change, a re-render
produces a *new* asset supplanting (not silently overwriting) the old.
"""
from __future__ import annotations

import base64
import hashlib
import os
import re
from typing import Optional

MOTIFS = ("orbits", "strata", "prism", "glyphs", "tide", "circuit", "garden", "halo")
FRAMES = ("arc", "square", "notch", "double")


def _seed(persona: dict) -> int:
    h = hashlib.sha256(
        (persona.get("id", "") + "|" + persona.get("name", "") + "|" +
         ",".join(persona.get("traits") or []) + "|" +
         ",".join(persona.get("interests") or [])).encode()).digest()
    return int.from_bytes(h[:8], "big")


def _rng(seed: int):
    state = [seed & 0xFFFFFFFFFFFFFFFF or 1]

    def nxt() -> float:
        state[0] = (state[0] * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
        return (state[0] >> 33) / 0x7FFFFFFF
    return nxt


def _palette(persona: dict) -> list:
    h = hashlib.md5((persona.get("id", "") + persona.get("name", "")).encode()).digest()
    base = h[0] / 255 * 360
    cols = []
    for i in range(4):
        hue = (base + i * (40 + h[1] % 90)) % 360
        sat = 45 + (h[2 + i] % 45)
        lit = 30 + (h[6 + i] % 45)
        cols.append(f"hsl({int(hue)},{sat}%,{lit}%)")
    return cols


def _motif_for(persona: dict, rng) -> str:
    key = " ".join(persona.get("interests") or []) + " " + " ".join(persona.get("traits") or [])
    key = (key or persona.get("name", "")).lower()
    words = re.findall(r"[a-z]+", key)
    vocab = {"orbits": ("star", "sky", "orbit", "space", "plan", "cycle", "calendar", "time"),
             "strata": ("ledger", "record", "history", "layer", "archive", "data", "provenance"),
             "prism": ("light", "glass", "spectrum", "clarity", "analyze", "inspect"),
             "glyphs": ("word", "text", "write", "language", "chat", "story", "essay"),
             "tide": ("water", "flow", "travel", "music", "sound", "voice", "speech"),
             "circuit": ("tool", "compute", "machine", "engine", "system", "build"),
             "garden": ("grow", "plant", "nature", "care", "tend", "garden", "cultivate"),
             "halo": ("watch", "attention", "alert", "forward", "herald", "notify")}
    best, best_n = MOTIFS[int(rng() * len(MOTIFS))], 0
    for m, words_m in vocab.items():
        n = sum(1 for w in words if any(w.startswith(v) or v in w for v in words_m))
        if n > best_n:
            best, best_n = m, n
    return best


def render_art(ctx, persona: dict, out_dir: Optional[str] = None) -> dict:
    """Generate the persona's unique portrait. Returns svg, artifact path,
    and the composition record asserted to the ledger."""
    seed = _seed(persona)
    rng = _rng(seed)
    motif = _motif_for(persona, rng)
    cols = _palette(persona)
    frame = FRAMES[int(rng() * len(FRAMES))]
    W = H = 160
    parts = [f'<rect width="{W}" height="{H}" rx="18" fill="{cols[0]}"/>']
    # ambient motion: two drifting halo layers (real SVG animation)
    dur1 = 6 + rng() * 5
    dur2 = 8 + rng() * 6
    parts.append(
        f'<g opacity="0.35"><ellipse cx="{W/2}" cy="{H/2}" rx="{55+rng()*15:.0f}" '
        f'ry="{40+rng()*15:.0f}" fill="{cols[1]}">'
        f'<animateTransform attributeName="transform" type="rotate" from="0 80 80" '
        f'to="360 80 80" dur="{dur1:.1f}s" repeatCount="indefinite"/></ellipse></g>')
    parts.append(
        f'<g opacity="0.25"><ellipse cx="{W/2}" cy="{H/2}" rx="{30+rng()*12:.0f}" '
        f'ry="{24+rng()*10:.0f}" fill="{cols[2]}">'
        f'<animateTransform attributeName="transform" type="rotate" from="360 80 80" '
        f'to="0 80 80" dur="{dur2:.1f}s" repeatCount="indefinite"/></ellipse></g>')
    # motif layer
    shapes = _motif_shapes(motif, rng, cols, W, H)
    parts.append(shapes)
    # portrait frame (presentation glass): frame style varies per persona
    if frame == "arc":
        parts.append(f'<path d="M14 {H-14} A {W-14} {H-14} 0 0 1 {W-14} 14" fill="none" '
                     f'stroke="{cols[3]}" stroke-width="4"/>')
    elif frame == "square":
        parts.append(f'<rect x="6" y="6" width="{W-12}" height="{H-12}" rx="10" '
                     f'fill="none" stroke="{cols[3]}" stroke-width="3" '
                     f'stroke-dasharray="{8+int(rng()*8)} {4+int(rng()*6)}"/>')
    elif frame == "notch":
        parts.append(f'<rect x="6" y="6" width="{W-12}" height="{H-12}" rx="10" '
                     f'fill="none" stroke="{cols[3]}" stroke-width="2"/>'
                     f'<rect x="2" y="{H/2-14}" width="8" height="28" fill="{cols[3]}"/>')
    else:
        parts.append(f'<rect x="5" y="5" width="{W-10}" height="{H-10}" rx="12" '
                     f'fill="none" stroke="{cols[3]}" stroke-width="2"/>'
                     f'<rect x="11" y="11" width="{W-22}" height="{H-22}" rx="9" '
                     f'fill="none" stroke="{cols[3]}" stroke-width="1" opacity="0.6"/>')
    # permanent imitation mark (prompt §Personalities): corner diamond, always present
    if persona.get("imitates"):
        parts.append('<polygon points="132,8 148,24 132,40 116,24" fill="#ffbf00" '
                     'stroke="#000" stroke-width="1.5"/>'
                     '<text x="132" y="28" font-size="9" text-anchor="middle" '
                     'font-family="monospace" fill="#000">IM</text>')
    # initial monogram
    parts.append(f'<text x="{W/2}" y="{H/2+16}" font-size="46" text-anchor="middle" '
                 f'font-family="Georgia, serif" fill="#fff" opacity="0.92">'
                 f'{persona.get("name", "?")[0].upper()}</text>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">'
           + "".join(parts) + "</svg>")
    artifact = None
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        artifact = os.path.join(out_dir, f"persona-{persona['id']}.svg")
        with open(artifact, "w", encoding="utf-8") as f:
            f.write(svg)
    rec = {"seed": seed, "motif": motif, "palette": cols, "frame": frame,
           "artifact": artifact, "ambient": True,
           "engine": "inproc-svg-glass"}
    if ctx is not None:
        prev = ctx.ledger.query(subject=f"persona:{persona['id']}",
                                predicate="persona:art")
        ctx.append(f"persona:{persona['id']}", "persona:art", rec,
                   "engine:portrait", basis={"kind": "execution"},
                   supersedes=prev[-1].id if prev else None)
    rec["svg"] = svg
    rec["dataUrl"] = "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
    return rec


def _motif_shapes(motif: str, rng, cols: list, W: int, H: int) -> str:
    c = cols[2]
    c2 = cols[3]
    out = []
    cx, cy = W / 2, H / 2
    if motif == "orbits":
        for i in range(2 + int(rng() * 3)):
            rx, ry = 22 + i * (8 + rng() * 6), 14 + i * (6 + rng() * 5)
            rot = rng() * 360
            out.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx:.0f}" ry="{ry:.0f}" '
                       f'fill="none" stroke="{c}" stroke-width="1.4" opacity="0.8" '
                       f'transform="rotate({rot:.0f} {cx} {cy})"/>')
        out.append(f'<circle cx="{cx+18}" cy="{cy-12}" r="4" fill="{c2}"/>')
    elif motif == "strata":
        y = 30
        while y < H - 20:
            h = 5 + rng() * 10
            out.append(f'<path d="M8 {y:.0f} Q {cx} {y-8+rng()*16:.0f} {W-8} {y:.0f} '
                       f'L {W-8} {y+h:.0f} Q {cx} {y+h-8+rng()*16:.0f} 8 {y+h:.0f} Z" '
                       f'fill="{c}" opacity="{0.25+rng()*0.3:.2f}"/>')
            y += h + 4 + rng() * 8
    elif motif == "prism":
        for i in range(3):
            x = 30 + i * 30 + rng() * 10
            out.append(f'<polygon points="{x:.0f},110 {x+22:.0f},110 {x+11:.0f},'
                       f'{52+rng()*20:.0f}" fill="{c}" opacity="{0.3+i*0.18:.2f}"/>')
        out.append(f'<path d="M20 40 L 140 120" stroke="{c2}" stroke-width="1.5" opacity="0.7"/>')
    elif motif == "glyphs":
        chars = "ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛞᛟ"
        for i in range(5):
            x, y = 24 + i * 26, 60 + (i % 2) * 34
            ch = chars[int(rng() * len(chars))]
            out.append(f'<text x="{x}" y="{y}" font-size="{18+rng()*10:.0f}" '
                       f'fill="{c}" opacity="0.85">{ch}</text>')
    elif motif == "tide":
        for i in range(3 + int(rng() * 2)):
            y = 45 + i * 18
            out.append(f'<path d="M6 {y} q 20 {-8-rng()*8:.0f} 40 0 t 40 0 t 40 0 t 40 0" '
                       f'fill="none" stroke="{c}" stroke-width="2.4" opacity="{0.5+rng()*0.3:.2f}"/>')
    elif motif == "circuit":
        nodes = [(20 + rng() * 120, 25 + rng() * 110) for _ in range(5)]
        for i in range(len(nodes) - 1):
            x1, y1 = nodes[i]; x2, y2 = nodes[i + 1]
            out.append(f'<path d="M{x1:.0f} {y1:.0f} L{x1:.0f} {y2:.0f} L{x2:.0f} {y2:.0f}" '
                       f'fill="none" stroke="{c}" stroke-width="1.6" opacity="0.7"/>')
        for x, y in nodes:
            out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="3.4" fill="{c2}"/>')
    elif motif == "garden":
        for i in range(3 + int(rng() * 2)):
            x = 35 + i * 30 + rng() * 8
            out.append(f'<path d="M{x:.0f} 125 v {-30-rng()*25:.0f}" stroke="{c}" '
                       f'stroke-width="2.6" fill="none"/>'
                       f'<ellipse cx="{x:.0f}" cy="{88-rng()*20:.0f}" rx="{6+rng()*5:.0f}" '
                       f'ry="{9+rng()*6:.0f}" fill="{c2}" opacity="0.8"/>')
    else:  # halo
        for i in range(3):
            r = 18 + i * (10 + rng() * 6)
            out.append(f'<circle cx="{cx}" cy="{cy}" r="{r:.0f}" fill="none" '
                       f'stroke="{c}" stroke-width="{2.4-i*0.6:.1f}" '
                       f'opacity="{0.85-i*0.2:.2f}" stroke-dasharray="{r*4:.0f} {r:.0f}"/>')
    return "".join(out)
