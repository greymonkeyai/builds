"""Quorum artifact exchange — workshop bundles on physical media
(C-WorkshopArtifact, C-InterpretedArtifact, C-ToolWireFidelity,
C-ArtifactCapture, C-ArtifactRepublish, C-PreloadCache, C-VoiceSpec,
C-EngineMapping, C-ExchangeLayers).

A WORKSHOP = persona + tool + explanatory text + supplementary materials,
encapsulated in a physical artifact (postcard is the minimal case; the
media class is extensible — the bundle is canonical, transport varies).

The artifact is INTERPRETED, never executed: extracted content is candidate
data under dubious-provenance handling — low source ceiling, adjudicable.

Exchange layers: this build implements a stdlib 2D-barcode symbology
("qmatrix") — a bitmap whose cells carry the literal payload. Encode AND
read are real (C-ExchangeLayers' capability step). Departure on record:
the symbology is build-specific, not standard QR — recorded as a challenge;
the bound essential (literal payload through a 2D image + a real decode
path) is preserved.
"""
from __future__ import annotations

import base64
import json
import os
import struct
import zlib

from . import rows

CELL = 16            # px per data cell
MARGIN = 2           # cells of quiet margin
SYNC = 0xFF          # first payload byte is a sync marker

# ---------------------------------------------------------------------------
# BMP 24bpp writer/reader (stdlib)
def _bmp_write(path: str, w: int, h: int, px: list[list[tuple]]):
    row_pad = (4 - (w * 3) % 4) % 4
    img_size = (w * 3 + row_pad) * h
    with open(path, "wb") as f:
        f.write(b"BM")
        f.write(struct.pack("<IHHI", 54 + img_size, 0, 0, 54))
        f.write(struct.pack("<IiiHHIIiiII", 40, w, h, 1, 24, 0, img_size,
                            2835, 2835, 0, 0))
        pad = b"\x00" * row_pad
        for y in range(h - 1, -1, -1):           # BMP is bottom-up
            for x in range(w):
                r, g, b = px[y][x]
                f.write(bytes((b, g, r)))
            f.write(pad)

def _bmp_read(path: str):
    with open(path, "rb") as f:
        d = f.read()
    if d[:2] != b"BM":
        raise ValueError("not a BMP")
    off = struct.unpack("<I", d[10:14])[0]
    w, h = struct.unpack("<ii", d[18:26])
    bpp = struct.unpack("<H", d[28:30])[0]
    if bpp != 24:
        raise ValueError("expected 24bpp")
    row_pad = (4 - (w * 3) % 4) % 4
    px = []
    for y in range(abs(h) - 1, -1, -1):
        row = []
        base = off + y * (w * 3 + row_pad)
        for x in range(w):
            b, g, r = d[base + x * 3: base + x * 3 + 3]
            row.append((r, g, b))
        px.append(row)
    return w, abs(h), px

# ---------------------------------------------------------------------------
# qmatrix symbology — header row + bit cells
def matrix_encode(payload: bytes, path: str) -> dict:
    data = bytes([SYNC]) + struct.pack(">I", len(payload)) + \
           zlib.compress(payload, 9)
    bits = "".join(f"{b:08b}" for b in data)
    cols = 24
    rows_n = len(bits) // cols + 1 + 1          # +1 sync row
    gw, gh = cols + 2 * MARGIN, rows_n + 2 * MARGIN
    W, H = gw * CELL, gh * CELL
    px = [[(255, 255, 255)] * W for _ in range(H)]

    def cell(cx, cy, on, rgb=(20, 20, 20)):
        for y in range(cy * CELL + 2, (cy + 1) * CELL - 2):
            for x in range(cx * CELL + 2, (cx + 1) * CELL - 2):
                px[y][x] = rgb if on else (250, 250, 250)

    # sync row — alternating pattern the decoder locks onto
    for i in range(cols):
        cell(MARGIN + i, MARGIN, i % 2 == 0)
    for i, bit in enumerate(bits):
        cell(MARGIN + i % cols, MARGIN + 1 + i // cols, bit == "1")
    _bmp_write(path, W, H, px)
    return {"path": path, "bytes": len(payload), "cells": len(bits),
            "symbology": "qmatrix-24"}

def matrix_decode(path: str) -> dict:
    """The read side — a genuine decode: re-samples the bitmap cells and
    reconstructs the literal payload."""
    w, h, px = _bmp_read(path)
    gw, gh = w // CELL, h // CELL
    def cell_on(cx, cy):
        r, g, b = px[cy * CELL + CELL // 2][cx * CELL + CELL // 2]
        return (r + g + b) / 3 < 128
    # lock the sync row
    sy = None
    for y in range(gh):
        pat = [cell_on(x, y) for x in range(MARGIN, MARGIN + 8)]
        if pat == [True, False, True, False, True, False, True, False]:
            sy = y
            break
    if sy is None:
        raise ValueError("sync row not found — not a qmatrix symbol")
    bits = ""
    for y in range(sy + 1, gh):
        for x in range(MARGIN, gw - MARGIN):
            bits += "1" if cell_on(x, y) else "0"
    raw = bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits) - 7, 8))
    if raw[0] != SYNC:
        raise ValueError("bad sync byte")
    n = struct.unpack(">I", raw[1:5])[0]
    payload = zlib.decompress(raw[5:])
    if len(payload) != n:
        raise ValueError("payload length mismatch")
    return {"payload": payload, "bytes": n, "symbology": "qmatrix-24"}

# ---------------------------------------------------------------------------
# Workshop bundles + capture layers
VOICE_FAMILIES = ["warm-bass", "bright-tenor", "soft-alto", "crisp-soprano",
                  "neutral-mid", "gravel", "airy", "formal-narrator",
                  "casual-companion", "storybook", "clipped-assistant",
                  "resonant", "light-childlike", "aged-wise"]

def voice_spec(families: list[str], traits: dict) -> dict:
    """C-VoiceSpec — minimal-payload spec sized to fit a QR: ranked
    voice-family selection and/or trait descriptors. Fidelity loss is
    expected — the receiver's engine mapping renders the nearest local
    voice (the PDF big-14 model)."""
    spec = {"families": [f for f in families if f in VOICE_FAMILIES],
            "traits": {k: traits[k] for k in
                       ("rate", "pitch", "gender", "age") if k in traits}}
    spec["_bytes"] = len(json.dumps(spec))
    return spec

def map_voice(spec: dict, local_voices: list[dict]) -> dict:
    """C-EngineMapping — render the spec through the LOCAL voice inventory.
    Portable preference → nearest local engine voice; delta accepted."""
    if not local_voices:
        return {"mapped": None, "note": "no local voices — selection absent, "
                "not faked (C-VoiceSelectFloor)"}
    gender_want = (spec.get("traits") or {}).get("gender", "").lower()
    pick = local_voices[0]
    for v in local_voices:
        if gender_want and gender_want in str(v.get("gender", "")).lower():
            pick = v
            break
    fam = (spec.get("families") or [""])[0]
    if "bass" in fam or "gravel" in fam:
        pick = next((v for v in local_voices
                     if "david" in v["id"].lower() or "mark" in v["id"].lower()),
                    pick)
    return {"mapped": pick["id"], "family": fam,
            "fidelity": "spec honored — nearest local engine voice; "
                        "exact-match fidelity not required (C-VoiceSpec)"}

def bundle_workshop(persona: dict, tool_def: dict, explain_text: str,
                    voice: dict, materials: dict) -> bytes:
    """Canonical workshop bundle — transport-independent payload."""
    return json.dumps({
        "kind": "quorum-workshop", "v": 1,
        "persona": {"name": persona.get("name"), "register": persona.get("register"),
                    "traits": persona.get("traits"),
                    "characterization": persona.get("characterization")},
        "tool": tool_def, "explain": explain_text,
        "voice_spec": voice, "materials": materials,
    }, ensure_ascii=False).encode()

def capture(image_path: str) -> dict:
    """C-ArtifactCapture — a single capture yields multiple extraction layers:
    literal (barcode/payload — the hard seam), semantic (candidate fields),
    stylistic (art style as an LLM reference for workshop presentation)."""
    literal = matrix_decode(image_path)
    bundle = json.loads(literal["payload"].decode())
    # stylistic layer — dominant palette + composition stats from the pixels
    w, h, px = _bmp_read(image_path)
    from collections import Counter
    sample = Counter(px[y][x] for y in range(0, h, 8) for x in range(0, w, 8))
    palette = [{"rgb": list(c), "share": round(n / sum(sample.values()), 3)}
               for c, n in sample.most_common(5)]
    dark = sum(n for c, n in sample.items() if sum(c) / 3 < 128)
    style = {"palette": palette,
             "contrast": round(dark / sum(sample.values()), 3),
             "grid": f"{w}x{h}px",
             "reference": "captured art style — LLM reference for workshop "
                          "background/presentation"}
    semantic = {"name": bundle.get("persona", {}).get("name"),
                "tool_id": (bundle.get("tool") or {}).get("id"),
                "voice_spec": bundle.get("voice_spec"),
                "explain": bundle.get("explain", "")[:300]}
    return {"literal": literal["bytes"], "bundle": bundle,
            "semantic": semantic, "stylistic": style}


class ArtifactExchange:
    """Import/adopt/republish — mediated, never enforced (carry-not-enforce
    maps to sub-threshold import)."""

    def __init__(self, book, tools, floor, preload_dir: str):
        self.book = book
        self.tools = tools
        self.floor = floor
        self.preload_dir = preload_dir

    def import_artifact(self, image_path: str) -> dict:
        """C-WorkshopArtifact + C-InterpretedArtifact: the workshop lands as
        an app entry BELOW the action/acceptance threshold; contents are
        candidates under dubious-provenance handling."""
        cap = capture(image_path)
        bundle = cap["bundle"]
        ws_id = f"ws-{rows.new_id('w')[2:]}"
        claims = []
        # persona → candidate claims (not live)
        pname = bundle.get("persona", {}).get("name", "unnamed")
        claims.append(self.book.claim(
            ws_id, "workshop:persona",
            {"name": pname, "spec": bundle.get("persona"), "live": False},
            claimant="exchange:artifact", certainty=0.4, basis="import",
            meta={"origin": {"kind": "import", "sourceKey": image_path}}))
        # tool → tool:candidate — hard seam: the decoded definition is the
        # SAME tool or it is a defect (C-ToolWireFidelity); invocable only
        # after acceptance mint.
        tool = bundle.get("tool")
        if tool and tool.get("id"):
            self.tools.stage_candidate(
                tool, {"kind": "import", "sourceKey": image_path,
                       "via": "qmatrix-artifact"})
        claims.append(self.book.claim(
            ws_id, "workshop:entry",
            {"title": pname, "accessible": True,
             "threshold": "below-action — adjudicate to adopt",
             "voice_spec": bundle.get("voice_spec"),
             "style": cap["stylistic"]},
            claimant="exchange:artifact", certainty=0.4, basis="import"))
        review = self.resolve_claims(
            ws_id, (bundle.get("materials") or {}).get("claims", []))
        return {"workshop": ws_id, "claims": claims, "capture": cap,
                "claim_review": review.get("outcomes", [])}

    def adopt(self, ws_id: str, claimant="principal") -> dict:
        """Adoption is the mediated act — the artifact offered, the instance
        decides. Adopting mints the persona live + offers tool acceptance."""
        ws = self.book.resolve(ws_id, "workshop:entry")
        if not ws:
            return {"ok": False}
        self.book.claim(ws_id, "workshop:adopted",
                        {"by": claimant, "at": rows.now_ms()},
                        claimant=claimant, certainty=1.0, basis="user-choice")
        return {"ok": True, "adopted": ws_id}

    def republish(self, ws_id: str, out_path: str) -> dict:
        """C-ArtifactRepublish — an adopted workshop re-encodes onto a new
        artifact for a further instance (gen-2 propagation)."""
        ws = self.book.resolve(ws_id, "workshop:persona")
        entry = self.book.resolve(ws_id, "workshop:entry")
        if not ws:
            return {"ok": False}
        spec = ws["value"]["v"].get("spec") or {}
        cand = next((c for c in self.tools.candidates()
                     if c["subject"] == ws_id), None)
        os.makedirs(os.path.dirname(os.path.abspath(out_path)),
                    exist_ok=True)
        tool_def = (cand["value"]["v"]["definition"] if cand else
                    {"id": "note-reader", "name": "Note reader",
                     "purpose": "reads notes", "explain": "Reads a note aloud.",
                     "slots": {}, "logic": []})
        payload = bundle_workshop(
            spec, tool_def,
            (entry["value"]["v"].get("title", "") if entry else ""),
            (entry["value"]["v"].get("voice_spec") or
             voice_spec(["neutral-mid"], {})), {})
        enc = matrix_encode(payload, out_path)
        self.book.claim(ws_id, "workshop:republished",
                        {"path": out_path, "gen": 2},
                        claimant="system", certainty=0.9, basis="execution")
        return {"ok": True, "artifact": out_path, "encoding": enc}

    # ---- dubious source (C-InterpretedArtifact + C-PreloadCache) --------------
    def vetted_sources(self) -> dict:
        """Preload cache pointers — artifact references resolve AGAINST
        vetted sources, never trusted at face value."""
        path = os.path.join(self.preload_dir, "vetted-sources.json")
        if os.path.exists(path):
            return json.load(open(path, encoding="utf-8"))
        return {"sources": {}}

    def resolve_claims(self, ws_id: str, claims: list[dict]) -> dict:
        """Artifact-supplied claims held as low-ceiling candidates; encoded
        references resolved against vetted-source pointers; non-matching
        claims recorded for review (S-dubious-source)."""
        vetted = self.vetted_sources().get("sources", {})
        outcomes = []
        for c in claims:
            ref = c.get("ref", "")
            match = next((k for k in vetted if ref.startswith(k)), None)
            outcome = {"claim": c.get("text", ""), "ref": ref,
                       "vetted_match": match,
                       "status": "resolves-against-vetted" if match else
                                 "non-matching — recorded for review"}
            outcomes.append(outcome)
            self.book.claim(
                ws_id, "exchange:claim-review", outcome,
                claimant="pipeline:artifact", certainty=0.4, basis="import",
                meta={"vetted": bool(match)})
        return {"ws": ws_id, "outcomes": outcomes}
