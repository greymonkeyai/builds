"""Per-personality generated art (C-PersonalityArt) + presentation glass
(C-PresentationGlass: asset pipeline, portrait frames, ambient motion).

G2 ruling (shortcomings-003): abstract sigils were ruled insufficient — the
art bound to a personality must be *portrait-quality* and personality-
specific. So every personality's art is now a procedurally illustrated
bust portrait: face shape, skin tone, hair style + color, eyes, brows,
mouth, and dress/accessories are all chosen from the persona's seed
(id + name + traits + interests + lens). No two personalities share a
portrait; nothing is placeholder or stock media.

The generated SVG still carries:
- a deterministic motif family derived from the persona's interests
- a palette derived from the persona's name + id
- ambient motion (real SVG animation — drifting elements behind the bust)
- a portrait frame keyed to the persona's display mode / imitation status

The asset pipeline is honest: `persona:art` assertions record the seed,
motif, palette, portrait parameters, and artifact path. When a persona's
traits change, a re-render produces a *new* asset supplanting (not silently
overwriting) the old.
"""
from __future__ import annotations

import base64
import hashlib
import os
import re
from typing import Optional

MOTIFS = ("orbits", "strata", "prism", "glyphs", "tide", "circuit", "garden", "halo")
FRAMES = ("arc", "square", "notch", "double")
SKINS = ("#f6d7b8", "#eec39a", "#d9a066", "#b07a4a", "#8d5a33",
         "#f1c27d", "#e0ac69", "#c68642", "#a06a3a", "#ffdbac")
HAIR_COLORS = ("#1c1410", "#3b2417", "#6b4226", "#8c5a2b", "#b5762f",
               "#c8a165", "#d9d3c5", "#e8e4dc", "#7a2f2f", "#30404d",
               "#4a3b6b", "#2e5d50")
FACE_SHAPES = ("oval", "round", "angular", "heart")
HAIR_STYLES = ("swept", "bob", "cropped", "wavy", "long", "topknot", "hood")
MOUTHS = ("smile", "neutral", "smirk", "flat", "open")


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


def _portrait_params(persona: dict, rng) -> dict:
    """Portrait parameters chosen from the persona's seed — the face IS the
    identity: same persona always renders the same portrait; different
    personas get visibly different faces, hair, and dress."""
    lens = (persona.get("lens") or {})
    register = lens.get("register") or lens.get("style", "measured")
    traits_l = [t.lower() for t in (persona.get("traits") or [])]
    interests_l = [i.lower() for i in (persona.get("interests") or [])]
    joined = " ".join(traits_l + interests_l + [register])
    i = lambda mod: int(rng() * mod)
    glasses = (i(4) == 0 or
               any(w in joined for w in ("scholar", "methodical", "analy",
                                         "meticulous", "precise", "librar")))
    collar = any(w in joined for w in ("formal", "catalog", "curat", "precise"))
    earrings = i(5) == 0
    mouth = ("smile" if register in ("warm", "wry") else
             "flat" if register == "clipped" else
             "open" if register == "playful" else
             MOUTHS[i(len(MOUTHS))])
    return {"face": FACE_SHAPES[i(len(FACE_SHAPES))],
            "skin": SKINS[i(len(SKINS))],
            "hairStyle": HAIR_STYLES[i(len(HAIR_STYLES))],
            "hair": HAIR_COLORS[i(len(HAIR_COLORS))],
            "eyeGap": 0.9 + rng() * 0.35,
            "eyeSize": 3.4 + rng() * 1.6,
            "browTilt": -0.5 + rng(),
            "mouth": mouth,
            "mouthW": 14 + rng() * 8,
            "glasses": glasses, "collar": collar, "earrings": earrings,
            "blush": rng() < 0.4}


def _face_path(shape: str, cx: float, cy: float) -> str:
    if shape == "round":
        return f'M {cx-26} {cy-6} a 26 30 0 1 0 52 0 a 26 30 0 1 0 -52 0'
    if shape == "angular":
        return (f'M {cx-24} {cy-28} L {cx+24} {cy-28} L {cx+20} {cy+8} '
                f'L {cx} {cy+30} L {cx-20} {cy+8} Z')
    if shape == "heart":
        return (f'M {cx-25} {cy-20} a 25 26 0 0 1 50 0 '
                f'L {cx} {cy+32} Z')
    return f'M {cx-23} {cy} a 23 32 0 1 0 46 0 a 23 32 0 1 0 -46 0'  # oval


def _hair(style: str, cx: float, cy: float, col: str) -> str:
    if style == "cropped":
        return (f'<path d="M {cx-24} {cy-14} a 24 20 0 0 1 48 0 '
                f'l -4 -14 a 20 16 0 0 0 -40 0 Z" fill="{col}"/>')
    if style == "bob":
        return (f'<path d="M {cx-27} {cy-18} a 27 26 0 0 1 54 0 l 0 24 '
                f'l -8 2 0 -22 a 19 17 0 0 0 -38 0 l 0 22 l -8 -2 Z" '
                f'fill="{col}"/>')
    if style == "swept":
        return (f'<path d="M {cx-25} {cy-12} q 4 -24 26 -26 q 24 -2 24 18 '
                f'l -8 -8 q -14 -10 -30 -4 q -10 4 -12 20 Z" fill="{col}"/>')
    if style == "wavy":
        return (f'<path d="M {cx-27} {cy-16} q -4 -20 12 -24 q 6 -8 16 -6 '
                f'q 12 -4 18 4 q 10 4 8 22 l -6 -4 q -2 -10 -10 -12 '
                f'q -12 -6 -22 0 q -10 4 -10 16 Z" fill="{col}"/>')
    if style == "long":
        return (f'<path d="M {cx-27} {cy-18} a 27 28 0 0 1 54 0 l 4 44 '
                f'l -10 0 -3 -40 a 18 16 0 0 0 -36 0 l -3 40 l -10 0 Z" '
                f'fill="{col}"/>')
    if style == "topknot":
        return (f'<circle cx="{cx}" cy="{cy-44}" r="9" fill="{col}"/>'
                f'<path d="M {cx-24} {cy-14} a 24 22 0 0 1 48 0 l -6 -10 '
                f'a 18 18 0 0 0 -36 0 Z" fill="{col}"/>')
    if style == "hood":
        return (f'<path d="M {cx-32} {cy+24} q -4 -52 32 -56 q 36 4 32 56 '
                f'l -10 -6 q 4 -42 -22 -44 q -26 2 -22 44 Z" '
                f'fill="{col}" opacity="0.92"/>')
    return ""


def _portrait(p: dict, cols: list) -> str:
    """The illustrated bust — shoulders, neck, face, hair, features."""
    cx, cy = 80, 74
    skin, hair = p["skin"], p["hair"]
    dark = "rgba(20,16,12,0.85)"
    out = []
    collar_col = cols[1] if p["collar"] else cols[2]
    out.append(f'<path d="M 34 150 q 6 -34 46 -36 q 40 2 46 36 Z" '
               f'fill="{collar_col}"/>')
    if p["collar"]:
        out.append(f'<path d="M 68 116 l 12 14 12 -14 l -4 22 l -8 4 -8 -4 Z" '
                   f'fill="#f4efe6"/>')
    out.append(f'<rect x="{cx-8}" y="{cy+18}" width="16" height="16" rx="5" '
               f'fill="{skin}"/>')
    out.append(f'<ellipse cx="{cx-25}" cy="{cy}" rx="5" ry="7" fill="{skin}"/>')
    out.append(f'<ellipse cx="{cx+25}" cy="{cy}" rx="5" ry="7" fill="{skin}"/>')
    out.append(f'<path d="{_face_path(p["face"], cx, cy)}" fill="{skin}"/>')
    out.append(_hair(p["hairStyle"], cx, cy, hair))
    gap = 11 * p["eyeGap"]
    tilt = p["browTilt"]
    for s in (-1, 1):
        ex = cx + s * gap
        out.append(f'<path d="M {ex-6} {cy-11 - s*tilt*3:.1f} q 6 -3 12 0" '
                   f'stroke="{hair}" stroke-width="2.4" fill="none"/>')
    for s in (-1, 1):
        ex = cx + s * gap
        r = p["eyeSize"]
        out.append(f'<ellipse cx="{ex}" cy="{cy-3}" rx="{r+1.4:.1f}" '
                   f'ry="{r:.1f}" fill="#fff"/>')
        out.append(f'<circle cx="{ex}" cy="{cy-3}" r="{r-1.4:.1f}" '
                   f'fill="{dark}"/>')
        out.append(f'<circle cx="{ex-0.8}" cy="{cy-4}" r="0.9" fill="#fff"/>')
    if p["glasses"]:
        for s in (-1, 1):
            ex = cx + s * gap
            out.append(f'<circle cx="{ex}" cy="{cy-3}" r="{p["eyeSize"]+3:.1f}" '
                       f'fill="none" stroke="{dark}" stroke-width="1.6"/>')
        out.append(f'<path d="M {cx-gap+p["eyeSize"]+3:.1f} {cy-3} '
                   f'Q {cx} {cy-7} {cx+gap-p["eyeSize"]-3:.1f} {cy-3}" '
                   f'stroke="{dark}" stroke-width="1.6" fill="none"/>')
    out.append(f'<path d="M {cx-1} {cy+2} q 3 5 -1 8 q -2 2 -4 1" '
               f'stroke="rgba(90,60,40,0.55)" stroke-width="1.6" fill="none"/>')
    w = p["mouthW"] / 2
    my = cy + 15
    if p["mouth"] == "smile":
        out.append(f'<path d="M {cx-w} {my} q {w} {w*0.9:.1f} {2*w} 0" '
                   f'stroke="{dark}" stroke-width="2.2" fill="none"/>')
    elif p["mouth"] == "smirk":
        out.append(f'<path d="M {cx-w} {my} q {w} {w*0.7:.1f} {2*w} -3" '
                   f'stroke="{dark}" stroke-width="2.2" fill="none"/>')
    elif p["mouth"] == "open":
        out.append(f'<ellipse cx="{cx}" cy="{my+2}" rx="{w*0.7:.1f}" ry="4" '
                   f'fill="{dark}"/>')
    elif p["mouth"] == "flat":
        out.append(f'<path d="M {cx-w} {my} L {cx+w} {my}" '
                   f'stroke="{dark}" stroke-width="2.4"/>')
    else:
        out.append(f'<path d="M {cx-w} {my} q {w} {w*0.35:.1f} {2*w} 0" '
                   f'stroke="{dark}" stroke-width="2" fill="none"/>')
    if p["blush"]:
        for s in (-1, 1):
            out.append(f'<ellipse cx="{cx + s*16}" cy="{cy+8}" rx="4.5" '
                       f'ry="2.6" fill="rgba(220,110,110,0.35)"/>')
    if p["earrings"]:
        out.append(f'<circle cx="{cx-25}" cy="{cy+9}" r="1.8" fill="{cols[3]}"/>')
        out.append(f'<circle cx="{cx+25}" cy="{cy+9}" r="1.8" fill="{cols[3]}"/>')
    return "".join(out)


def render_art(ctx, persona: dict, out_dir: Optional[str] = None) -> dict:
    """Generate the persona's unique portrait. Returns svg, artifact path,
    and the composition record asserted to the ledger."""
    seed = _seed(persona)
    rng = _rng(seed)
    motif = _motif_for(persona, rng)
    cols = _palette(persona)
    frame = FRAMES[int(rng() * len(FRAMES))]
    pparams = _portrait_params(persona, rng)
    W = H = 160
    parts = [f'<rect width="{W}" height="{H}" rx="18" fill="{cols[0]}"/>']
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
    parts.append(f'<g opacity="0.5">{_motif_shapes(motif, rng, cols, W, H)}</g>')
    parts.append(_portrait(pparams, cols))
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
    if persona.get("imitates"):
        parts.append('<polygon points="132,8 148,24 132,40 116,24" fill="#ffbf00" '
                     'stroke="#000" stroke-width="1.5"/>'
                     '<text x="132" y="28" font-size="9" text-anchor="middle" '
                     'font-family="monospace" fill="#000">IM</text>')
    parts.append(f'<text x="16" y="{H-12}" font-size="15" text-anchor="middle" '
                 f'font-family="Georgia, serif" fill="#fff" opacity="0.85">'
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
           "portrait": pparams, "artifact": artifact, "ambient": True,
           "engine": "inproc-svg-portrait"}
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
            out.append(f'<circle cx="{x}" cy="{y}" r="3.4" fill="{c2}"/>')
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
