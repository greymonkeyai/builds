"""Procedural persona portraits (C-PersonalityArt / C-PresentationGlass).
Each personality's art is unique to that personality: a deterministic seed
derived from identity drives face geometry, palette, hair style, eyes, brows,
mouth, collar, glasses, and a background motif. The SVG is written as a
durable artifact under runtime/artifacts/persona-art/ and bound to the
persona by a `persona:art` assertion carrying the same parameters — art is
bound to the persona, not just generated near it.
"""
from __future__ import annotations
import hashlib
import os
PALETTES = [
    {"skin": "#f2c9a4", "hair": "#4a3121", "bg1": "#1d3557", "bg2": "#457b9d",
     "accent": "#e63946"},
    {"skin": "#e8b88a", "hair": "#1c1c1c", "bg1": "#2a4d3a", "bg2": "#6b9e78",
     "accent": "#f4a261"},
    {"skin": "#d9a066", "hair": "#5c3a21", "bg1": "#503a6e", "bg2": "#8d6fc0",
     "accent": "#ffd166"},
    {"skin": "#f5d0b0", "hair": "#8a4b2a", "bg1": "#693a3a", "bg2": "#a86b6b",
     "accent": "#a8dadc"},
    {"skin": "#c98f5f", "hair": "#2f2f2f", "bg1": "#1f4e5f", "bg2": "#4f8a9b",
     "accent": "#e9c46a"},
    {"skin": "#ecc39b", "hair": "#6e4b2a", "bg1": "#3c4a2e", "bg2": "#77895c",
     "accent": "#ef8354"},
    {"skin": "#dfb185", "hair": "#7a2e2e", "bg1": "#34435e", "bg2": "#6d7fa3",
     "accent": "#9bf6ff"},
    {"skin": "#f0c8a8", "hair": "#3d2b1f", "bg1": "#4d3b5e", "bg2": "#9370b8",
     "accent": "#ffc6ff"},
]
MOTIFS = ("peaks", "waves", "orbit", "lattice", "sunrise", "grove")
HAIRS = ("crop", "wave", "bob", "bun", "crest", "long", "bald", "part")
EYES = ("round", "almond", "narrow", "bright")
MOUTHS = ("smile", "flat", "smirk", "open")
COLLARS = ("crew", "v", "collar", "scarf")
def _seed(pid: str, name: str) -> int:
    return int(hashlib.sha256(f"{pid}:{name}".encode()).hexdigest()[:12], 16)
def params_for(pid: str, name: str) -> dict:
    s = _seed(pid, name)
    pick = lambda arr, shift=0: arr[(s >> (shift * 4)) % len(arr)]
    return {
        "seed": hex(s), "palette": pick(PALETTES, 0), "motif": pick(MOTIFS, 1),
        "hair": pick(HAIRS, 2), "eyes": pick(EYES, 3),
        "mouth": pick(MOUTHS, 4), "collar": pick(COLLARS, 5),
        "glasses": bool((s >> 24) & 1), "earring": bool((s >> 25) & 1),
        "tilt": ((s >> 26) % 9) - 4, "brow": (s >> 30) % 3,
        "blush": bool((s >> 31) & 1),
    }
def _motif_svg(motif: str, p: dict) -> str:
    pal = p["palette"]
    a = pal["accent"]
    if motif == "peaks":
        return (f'<path d="M0 210 L60 120 L120 200 L180 100 L260 210 Z" '
                f'fill="{a}" opacity="0.25"/>')
    if motif == "waves":
        return (f'<path d="M0 200 Q60 170 130 200 T260 200 L260 260 L0 260 Z" '
                f'fill="{a}" opacity="0.25"/>')
    if motif == "orbit":
        return (f'<circle cx="130" cy="80" r="46" fill="none" stroke="{a}" '
                f'stroke-width="6" opacity="0.3"/>'
                f'<circle cx="130" cy="80" r="10" fill="{a}" opacity="0.5"/>')
    if motif == "lattice":
        return "".join(
            f'<rect x="{20+i*40}" y="{20+(i%3)*30}" width="16" height="16" '
            f'fill="{a}" opacity="0.22" transform="rotate(45 {28+i*40} '
            f'{28+(i%3)*30})"/>' for i in range(6))
    if motif == "sunrise":
        return (f'<circle cx="130" cy="230" r="52" fill="{a}" opacity="0.3"/>'
                f'<rect x="0" y="228" width="260" height="4" fill="{a}" '
                f'opacity="0.4"/>')
    return "".join(
        f'<ellipse cx="{40+i*44}" cy="{40+((i*37)%180)}" rx="10" ry="16" '
        f'fill="{a}" opacity="0.25"/>' for i in range(5))
def _hair_svg(style: str, p: dict, cx=130, cy=108, rx=62, ry=66) -> str:
    h = p["palette"]["hair"]
    if style == "bald":
        return f'<path d="M{cx-rx} {cy} A{rx} {ry} 0 0 1 {cx+rx} {cy} L{cx+rx} {cy-16} A{rx} {ry} 0 0 0 {cx-rx} {cy-16} Z" fill="{h}" opacity="0.35"/>'
    if style == "crop":
        return f'<path d="M{cx-rx-4} {cy-10} Q{cx} {cy-ry-34} {cx+rx+4} {cy-10} L{cx+rx} {cy-40} Q{cx} {cy-ry-8} {cx-rx} {cy-40} Z" fill="{h}"/>'
    if style == "wave":
        return (f'<path d="M{cx-rx-6} {cy+8} Q{cx-rx} {cy-ry-36} {cx} {cy-ry-30} '
                f'Q{cx+rx} {cy-ry-36} {cx+rx+6} {cy+8} '
                f'Q{cx+rx-10} {cy-40} {cx} {cy-46} Q{cx-rx+10} {cy-40} '
                f'{cx-rx-6} {cy+8} Z" fill="{h}"/>')
    if style == "bob":
        return (f'<path d="M{cx-rx-8} {cy+44} L{cx-rx-8} {cy-6} '
                f'Q{cx} {cy-ry-40} {cx+rx+8} {cy-6} L{cx+rx+8} {cy+44} '
                f'L{cx+rx-6} {cy+40} L{cx+rx-6} {cy-30} '
                f'Q{cx} {cy-ry-10} {cx-rx+6} {cy-30} L{cx-rx+6} {cy+40} Z" fill="{h}"/>')
    if style == "bun":
        return (f'<circle cx="{cx}" cy="{cy-ry-14}" r="20" fill="{h}"/>'
                f'<path d="M{cx-rx-4} {cy-4} Q{cx} {cy-ry-32} {cx+rx+4} {cy-4} '
                f'L{cx+rx} {cy-34} Q{cx} {cy-ry-4} {cx-rx} {cy-34} Z" fill="{h}"/>')
    if style == "crest":
        return (f'<path d="M{cx-20} {cy-ry+8} Q{cx} {cy-ry-48} {cx+20} {cy-ry+8} '
                f'Q{cx} {cy-ry-16} {cx-20} {cy-ry+8} Z" fill="{h}"/>'
                f'<path d="M{cx-rx-2} {cy-8} Q{cx} {cy-ry-20} {cx+rx+2} {cy-8} '
                f'L{cx+rx} {cy-34} Q{cx} {cy-ry+2} {cx-rx} {cy-34} Z" fill="{h}"/>')
    if style == "long":
        return (f'<path d="M{cx-rx-10} {cy+92} L{cx-rx-10} {cy-4} '
                f'Q{cx} {cy-ry-38} {cx+rx+10} {cy-4} L{cx+rx+10} {cy+92} '
                f'L{cx+rx-4} {cy+86} L{cx+rx-4} {cy-28} '
                f'Q{cx} {cy-ry-6} {cx-rx+4} {cy-28} L{cx-rx+4} {cy+86} Z" fill="{h}"/>')
    return (f'<path d="M{cx-rx-4} {cy-6} Q{cx-10} {cy-ry-34} {cx+rx+4} {cy-6} '
            f'L{cx+rx-6} {cy-36} Q{cx-6} {cy-ry-6} {cx-rx-6} {cy-34} Z" fill="{h}"/>')
def _eyes_svg(kind: str, p: dict, cx=130, cy=116) -> str:
    dark = "#22242a"
    lx, rx = cx - 24, cx + 24
    if kind == "round":
        return (f'<circle cx="{lx}" cy="{cy}" r="7" fill="{dark}"/>'
                f'<circle cx="{rx}" cy="{cy}" r="7" fill="{dark}"/>')
    if kind == "almond":
        return (f'<ellipse cx="{lx}" cy="{cy}" rx="9" ry="5" fill="{dark}"/>'
                f'<ellipse cx="{rx}" cy="{cy}" rx="9" ry="5" fill="{dark}"/>')
    if kind == "narrow":
        return (f'<rect x="{lx-9}" y="{cy-2}" width="18" height="4" rx="2" fill="{dark}"/>'
                f'<rect x="{rx-9}" y="{cy-2}" width="18" height="4" rx="2" fill="{dark}"/>')
    return (f'<circle cx="{lx}" cy="{cy}" r="6" fill="{dark}"/>'
            f'<circle cx="{rx}" cy="{cy}" r="6" fill="{dark}"/>'
            f'<circle cx="{lx+2}" cy="{cy-2}" r="2" fill="#fff"/>'
            f'<circle cx="{rx+2}" cy="{cy-2}" r="2" fill="#fff"/>')
def _mouth_svg(kind: str, p: dict, cx=130, cy=156) -> str:
    dark = "#7c3b3b"
    if kind == "smile":
        return f'<path d="M{cx-16} {cy} Q{cx} {cy+16} {cx+16} {cy}" stroke="{dark}" stroke-width="4" fill="none" stroke-linecap="round"/>'
    if kind == "flat":
        return f'<line x1="{cx-14}" y1="{cy+4}" x2="{cx+14}" y2="{cy+4}" stroke="{dark}" stroke-width="4" stroke-linecap="round"/>'
    if kind == "smirk":
        return f'<path d="M{cx-14} {cy+6} Q{cx+4} {cy+12} {cx+16} {cy-2}" stroke="{dark}" stroke-width="4" fill="none" stroke-linecap="round"/>'
    return f'<ellipse cx="{cx}" cy="{cy+6}" rx="9" ry="7" fill="{dark}"/>'
def render_svg(p: dict, mark: bool = False) -> str:
    pal = p["palette"]
    tilt = p["tilt"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 260" '
        f'role="img">',
        f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{pal["bg1"]}"/>'
        f'<stop offset="1" stop-color="{pal["bg2"]}"/></linearGradient></defs>',
        f'<rect width="260" height="260" rx="18" fill="url(#bg)"/>',
        _motif_svg(p["motif"], p),
        f'<g transform="rotate({tilt} 130 130)">',
        f'<path d="M60 260 Q70 196 130 192 Q190 196 200 260 Z" fill="{pal["accent"]}"/>',  # shoulders
        f'<rect x="112" y="150" width="36" height="52" rx="14" fill="{pal["skin"]}"/>',  # neck
        f'<ellipse cx="130" cy="112" rx="62" ry="66" fill="{pal["skin"]}"/>',  # face
        _hair_svg(p["hair"], p),
        _eyes_svg(p["eyes"], p),
        f'<path d="M104 {104 - p["brow"]*2} q10 -6 22 -2" stroke="{pal["hair"]}" stroke-width="5" fill="none" stroke-linecap="round"/>'
        f'<path d="M134 {102 - p["brow"]*2} q12 -4 22 2" stroke="{pal["hair"]}" stroke-width="5" fill="none" stroke-linecap="round"/>',
        f'<path d="M126 118 q8 14 4 22 q-4 4 -10 2" stroke="#b98a62" stroke-width="4" fill="none" stroke-linecap="round"/>',  # nose
        _mouth_svg(p["mouth"], p),
    ]
    if p["blush"]:
        parts.append(f'<ellipse cx="98" cy="140" rx="9" ry="5" fill="#e8a0a0" opacity="0.5"/>'
                     f'<ellipse cx="162" cy="140" rx="9" ry="5" fill="#e8a0a0" opacity="0.5"/>')
    if p["glasses"]:
        parts.append(
            f'<g stroke="#22242a" stroke-width="4" fill="none">'
            f'<circle cx="106" cy="116" r="14"/><circle cx="154" cy="116" r="14"/>'
            f'<line x1="120" y1="116" x2="140" y2="116"/></g>')
    if p["earring"]:
        parts.append(f'<circle cx="68" cy="128" r="4" fill="{pal["accent"]}"/>')
    # collar
    parts.append(
        f'<path d="M104 202 L130 218 L156 202 L156 214 L130 230 L104 214 Z" '
        f'fill="{pal["bg1"]}" opacity="0.85"/>')
    parts.append('</g>')
    # ambient motion — a slow glint (C-PresentationGlass ambient motion)
    parts.append(
        f'<circle cx="0" cy="0" r="90" fill="#ffffff" opacity="0.06">'
        f'<animate attributeName="cx" from="-60" to="320" dur="9s" '
        f'repeatCount="indefinite"/></circle>')
    if mark:
        parts.append(
            f'<g><rect x="176" y="10" width="76" height="24" rx="6" '
            f'fill="#000" opacity="0.75"/>'
            f'<text x="214" y="27" font-size="13" text-anchor="middle" '
            f'fill="#ffd166" font-family="monospace">&#9670; IMITATION</text></g>')
    parts.append('</svg>')
    return "".join(parts)
def generate(ctx, pid: str, name: str, mark: bool = False) -> dict:
    p = params_for(pid, name)
    svg = render_svg(p, mark=mark)
    d = os.path.join(ctx.runtime, "artifacts", "persona-art")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"persona-{pid}.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return {"file": path, "svg": svg, "params": p, "motif": p["motif"],
            "palette": p["palette"]["bg1"]}
