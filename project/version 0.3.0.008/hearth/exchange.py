"""hearth exchange — artifacts, workshops, publish-or-defer.
C-ScannableInterchange + C-ExchangeLayers: scannable code the operator
runs end to end (generate, carry, scan/decode, import) — symbology free;
this build uses a PNG bit-grid ("hgrid1"). C-ToolWireFidelity: component
ID, template slots, params transfer literally; imported tools staged as
candidates until accepted (C-ToolCandidateAcceptance). C-Interpreted-
Artifact: extracted content is candidate data under dubious provenance.
C-PublishOrDefer: produce + record, or defer with request+status.
"""
import base64
import json
import os
import struct
import time
import zlib
from .personas import _png
GRID_MAGIC = b"HG1"
def encode_payload(payload: dict) -> bytes:
    raw = json.dumps(payload, ensure_ascii=False,
                     separators=(",", ":")).encode("utf-8")
    comp = zlib.compress(raw, 6)
    body = GRID_MAGIC + struct.pack(">I", len(comp)) + comp
    crc = zlib.crc32(comp) & 0xFFFF
    return body + struct.pack(">H", crc)
def decode_payload(blob: bytes):
    if not blob.startswith(GRID_MAGIC):
        return None
    ln = struct.unpack(">I", blob[3:7])[0]
    comp = blob[7:7 + ln]
    crc = struct.unpack(">H", blob[7 + ln:9 + ln])[0]
    if zlib.crc32(comp) & 0xFFFF != crc:
        return None
    try:
        return json.loads(zlib.decompress(comp).decode("utf-8"))
    except Exception:
        return None
def payload_to_png(path, payload):
    """Scannable artifact: a PNG bit-grid. Header white border, 1 bit per
    cell, checksum row at bottom."""
    blob = encode_payload(payload)
    bits = "".join(f"{b:08b}" for b in blob)
    side = int(len(bits) ** 0.5) + 2
    w = h = side + 4
    px = bytearray(b"\xff" * w * h * 3)
    for i, b in enumerate(bits):
        x = 2 + i % side
        y = 2 + i // side
        if y >= h - 2:
            break
        if b == "1":
            p = (y * w + x) * 3
            px[p] = px[p + 1] = px[p + 2] = 0
    # corner markers
    for (mx, my) in [(1, 1), (w - 2, 1), (1, h - 2)]:
        p = (my * w + mx) * 3
        px[p] = px[p + 1] = px[p + 2] = 0
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(_png(w, h, bytes(px)))
    return path
def png_to_payload(path):
    """Decode the same grid — literal-fidelity seam."""
    data = open(path, "rb").read()
    # parse PNG IHDR + IDAT (minimal reader)
    pos = 8
    idat = b""
    w = h = None
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        tag = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        if tag == b"IHDR":
            w, h = struct.unpack(">II", body[:8])
        elif tag == b"IDAT":
            idat += body
        pos += 12 + ln
    raw = zlib.decompress(idat)
    side = w - 4
    bits = []
    stride = w * 3 + 1
    for y in range(2, h - 2):
        row = raw[y * stride + 1:(y + 1) * stride]
        for x in range(2, 2 + side):
            i = x * 3
            bits.append("1" if row[i] < 128 else "0")
    blob = bytearray()
    for i in range(0, len(bits) - 7, 8):
        blob.append(int("".join(bits[i:i + 8]), 2))
    return decode_payload(bytes(blob))
class Exchange:
    def __init__(self, host):
        self.h = host
        self.pkg_dir = os.path.join(host.data_dir, "exchange")
        os.makedirs(self.pkg_dir, exist_ok=True)
    # ---- storefront packages ------------------------------------------
    def export_package(self, holding):
        """A storefront packages persona(s) + tools + assertions."""
        pkg = {"schema": "hearth-exchange/1", "created": time.time(),
               "holding": holding,
               "personas": [], "tools": [], "assertions": []}
        if holding.get("persona"):
            p = self.h.indices["personas"].get(holding["persona"])
            if p:
                pkg["personas"].append(
                    {k: p[k] for k in ("name", "register", "character",
                                       "interests", "domains")
                     if k in p})
                pkg["personas"][-1]["voiceSpec"] = \
                    self.h.modules["personas"].voice_spec(p)
        for t in holding.get("tools", []):
            pkg["tools"].append({"id": t["id"], "need": t["need"],
                                 "slots": t["slots"],
                                 "explain": t["explain"]})
        pkg["assertions"] = holding.get("assertions", [])
        path = os.path.join(self.pkg_dir,
                            "pkg-" + str(int(time.time())) + ".json")
        with open(path, "w") as f:
            json.dump(pkg, f, indent=1)
        self.h.journal.append("exchange-package",
                              {"path": path, "schema": pkg["schema"],
                               "contents": {k: len(v) for k, v in
                                            pkg.items() if
                                            isinstance(v, list)}},
                              claimant="user", basis="execution-evidence")
        return {"path": path, "pkg": pkg}
    def import_package(self, path=None, payload=None):
        """Imported contents held BELOW the action/acceptance threshold —
        candidates resolved through this host's own ledger."""
        if payload is None:
            payload = json.load(open(path))
        staged = []
        for t in payload.get("tools", []):
            self.h.journal.append(
                "tool-candidate",
                {"tool": t, "origin": "exchange-package",
                 "accepted": False, "invocable": False,
                 "ceiling": 0.25},
                claimant="import", basis="source-evidence",
                certainty=0.3, confidence=0.25)
            staged.append(t.get("id"))
        for p in payload.get("personas", []):
            self.h.journal.append(
                "import-candidate",
                {"kind": "persona", "value": p, "ceiling": 0.25,
                 "accepted": False},
                claimant="import", basis="source-evidence",
                certainty=0.3, confidence=0.25)
        self.h.journal.append(
            "exchange-import",
            {"path": path, "stagedTools": staged,
             "belowThreshold": True, "confidenceCeiling": 0.25},
            claimant="import", basis="execution-evidence")
        return {"staged": staged, "belowThreshold": True}
    # ---- workshop artifacts --------------------------------------------
    def artifact_capture(self, artifact_path):
        """C-ArtifactCapture: literal + semantic + stylistic layers."""
        payload = png_to_payload(artifact_path) \
            if artifact_path.lower().endswith(".png") else None
        semantic, style = {}, {"mood": "neutral", "palette": "mono"}
        if payload:
            semantic = payload.get("workshop", payload)
            style = payload.get("style", style)
        entry = self.h.journal.append(
            "workshop-entry",
            {"artifact": artifact_path, "belowThreshold": True,
             "literal": bool(payload),
             "semantic": semantic, "style": style,
             "ceiling": 0.25},
            claimant="import", basis="source-evidence",
            certainty=0.3, confidence=0.25)
        return entry["id"]
    def workshop_encode(self, entry_id):
        """Re-encode an adopted workshop onto a new artifact — gen-2
        propagation (C-ArtifactRepublish)."""
        row = self.h.journal.get(entry_id)
        if not row:
            return None
        payload = {"schema": "hearth-exchange/1", "gen": 2,
                   "workshop": row["value"].get("semantic", {}),
                   "style": row["value"].get("style", {}),
                   "origin": row["id"]}
        path = os.path.join(self.pkg_dir, "artifact-gen2.png")
        payload_to_png(path, payload)
        self.h.journal.append("artifact-republish",
                              {"entry": entry_id, "path": path, "gen": 2},
                              claimant="user", basis="execution-evidence",
                              refs=[entry_id])
        return path
    def transmit_tool(self, tool):
        """C-ToolWireFidelity: the hard seam — literal fields."""
        payload = {"schema": "hearth-exchange/1", "kind": "tool",
                   "id": tool["id"], "need": tool["need"],
                   "slots": tool["slots"], "explain": tool["explain"]}
        blob = encode_payload(payload)
        path = os.path.join(self.pkg_dir, "tool-" + tool["id"] + ".bin")
        with open(path, "wb") as f:
            f.write(blob)
        decoded = decode_payload(blob)
        literal = decoded == payload
        self.h.journal.append(
            "tool-transmission",
            {"tool": tool["id"], "path": path,
             "literalFidelity": literal},
            claimant="tool:artifact.codec", basis="execution-evidence")
        return {"path": path, "decoded": decoded, "literal": literal}
    def dubious_resolve(self, claims, vetted_keys):
        """C-InterpretedArtifact + C-PreloadCache: artifact claims are
        low-ceiling candidates; encoded references resolve against
        vetted-source pointers; non-matches recorded for review."""
        resolved, review = [], []
        for c in claims:
            ref = c.get("ref", "")
            hit = any(k in ref for k in vetted_keys)
            self.h.journal.append(
                "claim-resolution" if hit else "review-item",
                {"claim": c, "resolvedAgainst": ref if hit else None,
                 "ceiling": 0.25},
                claimant="import", basis="source-evidence",
                certainty=0.25)
            (resolved if hit else review).append(c)
        return {"resolved": resolved, "review": review}
    # ---- publish / defer -------------------------------------------------
    def publish_request(self, text, input_row=None):
        """Nonlocal effects need a configured high-confidence authority
        path; conversational interpretation alone does not publish."""
        req = self.h.journal.append(
            "publish-request", {"text": text, "state": "received"},
            claimant="user", basis="captured-input",
            refs=[input_row["id"]] if input_row else [])
        # is a channel configured? email-class channel = configured account
        configured = bool(self.h.journal.rows("source-row") and
                          [r for r in self.h.journal.rows("source-row")
                           if r["value"].get("credential")])
        if not configured:
            self.h.journal.append(
                "publish-status",
                {"request": req["id"],
                 "state": "deferred-unconfigured-channel",
                 "note": "no configured authority path; request "
                         "recorded, not silently dropped"},
                claimant="system", basis="execution-evidence",
                refs=[req["id"]])
            return {"state": "deferred-unconfigured-channel",
                    "request": req["id"]}
        self.h.journal.append(
            "publish-status",
            {"request": req["id"], "state": "produced",
             "channel": "configured-account"},
            claimant="system", basis="execution-evidence",
            refs=[req["id"]])
        return {"state": "produced", "request": req["id"]}
    def publish(self, holding, form, channel):
        """Select holdings -> choose form/channel -> produce artifact and
        record, or defer with request+status."""
        if channel == "unconfigured":
            self.h.journal.append(
                "publish-status",
                {"holding": holding, "form": form, "channel": channel,
                 "state": "deferred-unconfigured-channel"},
                claimant="system", basis="execution-evidence")
            return {"state": "deferred-unconfigured-channel"}
        produced = self.export_package({"persona": holding,
                                        "tools": [],
                                        "assertions": []}) \
            if form in ("postcard", "file", "scancode") else None
        out = None
        if form == "scancode" and produced:
            out = payload_to_png(
                os.path.join(self.pkg_dir, "publish.png"),
                produced["pkg"])
        self.h.journal.append(
            "publish-status",
            {"holding": holding, "form": form, "channel": channel,
             "state": "produced", "artifact": out or
                      (produced or {}).get("path")},
            claimant="user", basis="execution-evidence")
        return {"state": "produced",
                "artifact": out or (produced or {}).get("path")}
    # ---- preload cache -----------------------------------------------------
    def seed_preload_cache(self):
        """C-PreloadCache: vetted-source pointers, device decoders,
        marketing exemplar — the demo path never invents content."""
        path = os.path.join(self.h.data_dir, "preload-cache.json")
        if os.path.exists(path):
            return json.load(open(path))
        cache = {
            "vettedPointers": ["source-wikipedia", "source-wikidata",
                               "source-cia-factbook",
                               "source-gutenberg", "source-memory-alpha"],
            "decoders": {"hgrid1": "PNG bit-grid (this build)",
                         "png": "PNG image", "json": "JSON package"},
            "exemplar": {"id": "postcard-knock-knock",
                         "kind": "workshop",
                         "desc": "a public-domain knock-knock scene card",
                         "payload": {"workshop": {"title": "Knock knock",
                                                  "cast": ["any", "any"],
                                                  "beat": "door joke"},
                                     "style": {"mood": "playful",
                                               "palette": "bright"}}},
        }
        ex_path = os.path.join(self.pkg_dir, "exemplar.png")
        payload_to_png(ex_path, cache["exemplar"]["payload"])
        cache["exemplar"]["artifact"] = ex_path
        with open(path, "w") as f:
            json.dump(cache, f, indent=1)
        self.h.journal.append("preload-cache",
                              {"path": path,
                               "pointers": len(cache["vettedPointers"]),
                               "decoders": len(cache["decoders"])},
                              claimant="system", basis="system")
        return cache
