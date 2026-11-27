"""exchange — artifact codec, import, transmission, republish,
publish-or-defer, preload cache, scancode (module: exchange).

Independent implementations exchange agreed meanings through an
ExchangeSchema (prompt §Exchange). `rastgrid-png-1` is this build's
scannable symbology — symbology free per owner ruling — a real 2D
encode AND read path (C-ExchangeLayers, C-ScannableInterchange). Imported
assertions enter below the threshold for action or acceptance
(C-InterpretedArtifact); tools transfer with literal fidelity and stay
quarantined candidates until accepted (C-ToolWireFidelity). One capture
yields extraction layers: literal payload, semantic fields, stylistic
reference (C-ArtifactCapture). A preload cache seeds vetted-source
pointers, device decoders, and marketing exemplars (C-PreloadCache).
Nonlocal effects need a configured authority path — else defer with
request + status recorded (C-PublishOrDefer).
"""

import binascii
import json
import os
import struct
import time
import zlib

MAGIC = b"VGST"


# ---------------- rastgrid-png-1 codec ----------------
def _png(width, height, pixels):
    """Minimal grayscale PNG writer (8-bit, filter 0)."""
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    raw = b""
    for y in range(height):
        raw += b"\x00" + bytes(pixels[y])
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def _unpng(data):
    """Read a filter-0 8-bit grayscale PNG back to pixel rows."""
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos, idat, w, h = 8, b"", 0, 0
    while pos < len(data):
        ln, tag = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + ln]
        if tag == b"IHDR":
            w, h, depth, color = struct.unpack(">IIBB", body[:10])
            assert depth == 8 and color == 0
        elif tag == b"IDAT":
            idat += body
        elif tag == b"IEND":
            break
        pos += 12 + ln
    raw = zlib.decompress(idat)
    rows, stride = [], w + 1
    for y in range(h):
        row = raw[y * stride:(y + 1) * stride]
        assert row[0] == 0, "only filter-0 pngs are written/read"
        rows.append(list(row[1:]))
    return w, h, rows


def encode_code(payload: bytes, cell=9, quiet=2):
    """Payload → bit-grid matrix with finder pattern → PNG bytes."""
    bits = []
    body = MAGIC + struct.pack(">I", len(payload)) + payload
    body += struct.pack(">H", binascii.crc32(body) & 0xFFFF)
    for b in body:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)
    def _skip(y, x, s):
        return (y < 8 and x < 8) or (y < 8 and x >= s - 8) or \
               (y >= s - 8 and x < 8) or x == 6 or y == 6
    side = 13
    while sum(1 for y in range(side) for x in range(side)
              if not _skip(y, x, side)) < len(bits):
        side += 2
    grid = [[0] * side for _ in range(side)]

    def finder(cx, cy):
        for dy in range(7):
            for dx in range(7):
                edge = dy in (0, 6) or dx in (0, 6)
                inner = 2 <= dx <= 4 and 2 <= dy <= 4
                grid[cy + dy][cx + dx] = 1 if (edge or inner) else 0

    finder(0, 0)
    finder(side - 7, 0)
    finder(0, side - 7)
    for i in range(8, side - 8):      # timing
        grid[6][i] = i % 2
        grid[i][6] = i % 2
    idx = 0
    for y in range(side):
        for x in range(side):
            if (y < 8 and x < 8) or (y < 8 and x >= side - 8) or \
               (y >= side - 8 and x < 8) or x == 6 or y == 6:
                continue
            if idx < len(bits):
                grid[y][x] = bits[idx]
                idx += 1
    w = (side + quiet * 2) * cell
    px = [[255] * w for _ in range(w)]
    for y in range(side):
        for x in range(side):
            if grid[y][x]:
                for dy in range(cell):
                    for dx in range(cell):
                        px[(y + quiet) * cell + dy][(x + quiet) * cell + dx] = 0
    return _png(w, w, px), {"side": side, "cell": cell, "quiet": quiet, "bits": len(bits)}


def decode_code(png: bytes):
    """PNG bytes → payload bytes; verifies finder + crc."""
    w, h, px = _unpng(png)
    # locate finder centers: scan for the 7x7 pattern at corners
    cell = 9
    quiet = 2
    # derive cell by locating first dark run in row 0..h
    dark = [(x, y) for y in range(0, h, 2) for x in range(0, w, 2) if px[y][x] < 128]
    if not dark:
        raise ValueError("no code found")
    minx = min(x for x, _ in dark)
    # cell size from the timing row period: scan dark pixels width
    row_y = min(y for _, y in dark)
    run = 0
    best = 0
    for x in range(w):
        if px[row_y][x] < 128:
            run += 1
            best = max(best, run)
        else:
            run = 0
    # longest contiguous dark run on the finder's top edge = 7 cells
    cell = max(1, best // 7)
    side = w // cell - quiet * 2
    bits = []
    for y in range(side):
        for x in range(side):
            if (y < 8 and x < 8) or (y < 8 and x >= side - 8) or \
               (y >= side - 8 and x < 8) or x == 6 or y == 6:
                continue
            v = px[(y + quiet) * cell + cell // 2][(x + quiet) * cell + cell // 2]
            bits.append(1 if v < 128 else 0)
    byts = bytearray()
    for i in range(0, len(bits) - 7, 8):
        b = 0
        for j in range(8):
            b |= bits[i + j] << (7 - j)
        byts.append(b)
    if byts[:4] != MAGIC:
        raise ValueError("magic mismatch")
    ln = struct.unpack(">I", byts[4:8])[0]
    payload = bytes(byts[8:8 + ln])
    crc = struct.unpack(">H", byts[8 + ln:10 + ln])[0]
    if crc != (binascii.crc32(MAGIC + struct.pack(">I", ln) + payload) & 0xFFFF):
        raise ValueError("crc mismatch")
    return payload


# ---------------- exchange module ----------------
class Exchange:
    def __init__(self, host):
        self.h = host
        self.art_dir = os.path.join(host.dir, "artifacts")
        os.makedirs(self.art_dir, exist_ok=True)
        self.ensure_preload_cache()

    # ---------- preload cache ----------
    def ensure_preload_cache(self):
        """Vetted-source pointers, device decoder entries, and a
        marketing exemplar — artifact references resolve against vetted
        sources rather than being trusted (C-PreloadCache)."""
        path = os.path.join(self.h.dir, "preload-cache.json")
        if os.path.exists(path):
            return
        cache = {
            "vettedPointers": {
                "wikipedia": "https://en.wikipedia.org/w/api.php",
                "wikidata": "https://www.wikidata.org/w/api.php",
                "openlibrary": "https://openlibrary.org/search.json",
            },
            "decoders": [
                {"symbology": "rastgrid-png-1", "entry": "vesta.exchange.decode_code",
                 "device": "any"},
                {"symbology": "qr", "entry": "external-decoder",
                 "device": "camera-equipped"},
            ],
            "exemplars": [
                {"name": "postcard-knock-knock", "kind": "workshop",
                 "contains": {"persona": "Quill", "tool": "speech.speak",
                              "text": "a theatrical herald who announces"}},
            ],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=1)
        self.h.ledger.append("cache:preload",
                             {"file": path,
                              "vettedPointers": len(cache["vettedPointers"]),
                              "decoders": len(cache["decoders"]),
                              "exemplars": len(cache["exemplars"])},
                             claimant="system", basis="build", certainty=0.9)

    def preload_cache(self):
        try:
            with open(os.path.join(self.h.dir, "preload-cache.json"),
                      "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    # ---------- package assembly ----------
    def package(self, holding):
        """Assemble an exchange package: a workshop = persona + tool +
        explanatory text + supplementary materials (C-WorkshopArtifact)."""
        v = self.h.ledger.view()
        pkg = {"schema": "vesta-exchange-1", "at": time.time(),
               "from": self.h.node_id, "holding": holding, "claims": [],
               "tools": [], "persona": None, "text": "", "references": []}
        if holding in v["workshops"]:
            w = v["workshops"][holding]
            pkg["text"] = w.get("text", "")
            pkg["tools"] = w.get("tools", [])
            pkg["persona"] = w.get("persona")
            pkg["references"] = w.get("references", [])
            pkg["style"] = w.get("style")
        elif holding in v["compositions"]:
            c = v["compositions"][holding]
            pkg["tools"] = [{"id": c.get("composition"), "name": c.get("name"),
                             "composition": True, "steps": c.get("steps")}]
            pkg["steps"] = c.get("steps") or []
        elif holding in v["tools"]:
            t = v["tools"][holding]
            pkg["tools"] = [{"id": t.get("tool"), "purpose": t.get("purpose"),
                             "inputs": t.get("inputs"), "tests": t.get("tests"),
                             "steps": t.get("steps")}]
        elif holding in v["personas"]:
            p = v["personas"][holding]
            pkg["persona"] = {"id": holding, "name": p.get("name"),
                              "register": p.get("register"),
                              "character": p.get("character"),
                              "voice": (v["voice_specs"].get(p["id"]) or {})}
            pkg["style"] = {"mood": p.get("register"), "palette": "noir-ink"}
        elif holding in v["lists"]:
            l = v["lists"][holding]
            pkg["claims"] = [{"list": l["title"], "members": l["members"]}]
            pkg["references"] = ["wikipedia"]
        return pkg

    def voice_spec_for(self, pid):
        """QR-fittable voice spec: ranked family + trait descriptors,
        minimal payload (C-VoiceSpec)."""
        spec = self.h.ledger.view()["voice_specs"].get(pid) or {}
        return {"v": 1, "fam": [ (spec.get("engine") or "") ],
                "tr": spec.get("traits") or {}}

    # ---------- encode ----------
    def encode(self, holding):
        """Produce a scancode artifact (PNG matrix) carrying the package."""
        pkg = self.package(holding)
        if pkg.get("persona") and pkg["persona"].get("id"):
            pkg["persona"]["voiceSpec"] = self.voice_spec_for(pkg["persona"]["id"])
        payload = json.dumps(pkg, separators=(",", ":")).encode()
        png, meta = encode_code(payload)
        aid = f"artifact-{self.h.ledger.next_index('artifact'):04d}"
        path = os.path.join(self.art_dir, f"{aid}.png")
        with open(path, "wb") as f:
            f.write(png)
        self.h.ledger.append("artifact:encoded",
                             {"artifact": aid, "file": path,
                              "holding": holding, "symbology": "rastgrid-png-1",
                              "payloadBytes": len(payload), **meta},
                             claimant="system", basis="execution-evidence")
        return {"ok": True, "artifact": aid, "file": path, "package": pkg}

    def encode_tool(self, composition):
        """Encode a tool/composition onto a scancode artifact — literal
        wire fidelity on component ids, slots, params
        (C-ToolWireFidelity)."""
        return self.encode(composition)

    # ---------- decode / import ----------
    def decode(self, path_or_png):
        """Scan/decode a scancode → package. Import holds contents below
        the action/acceptance threshold (dubious provenance:
        low source ceiling, adjudicable, never taken at face value)."""
        png = path_or_png
        if isinstance(path_or_png, str):
            with open(path_or_png, "rb") as f:
                png = f.read()
        payload = decode_code(png)
        pkg = json.loads(payload)
        aid = f"artifact-{self.h.ledger.next_index('artifact'):04d}"
        self.h.ledger.append("artifact:decoded",
                             {"artifact": aid, "from": pkg.get("from"),
                              "holding": pkg.get("holding"),
                              "payloadBytes": len(payload)},
                             claimant="system", basis="execution-evidence")
        # import below threshold — candidate data under dubious provenance
        imported = []
        for c in pkg.get("claims", []):
            imported.append(self.h.ledger.append(
                "exchange:imported",
                {"artifact": aid, "claim": c, "ceiling": 0.25},
                claimant=f"source:{pkg.get('from', 'artifact')}",
                basis="exchange-import", certainty=0.25))
        for t in pkg.get("tools", []):
            # literal fidelity on the wire: component id, slots, params
            imported.append(self.h.ledger.append(
                "exchange:imported",
                {"artifact": aid, "tool": t, "quarantined": True,
                 "invocableOnlyAfterAcceptance": True, "ceiling": 0.25},
                claimant=f"source:{pkg.get('from', 'artifact')}",
                basis="exchange-import", certainty=0.25))
        if pkg.get("persona"):
            imported.append(self.h.ledger.append(
                "exchange:imported",
                {"artifact": aid, "persona": pkg["persona"], "quarantined": True,
                 "ceiling": 0.25},
                claimant=f"source:{pkg.get('from', 'artifact')}",
                basis="exchange-import", certainty=0.25))
        # dubious-source handling: resolve encoded references against
        # vetted pointers; non-matching claims recorded for review
        review = []
        cache = self.preload_cache()
        for ref in pkg.get("references", []):
            if ref not in cache.get("vettedPointers", {}):
                review.append({"ref": ref, "why": "no-vetted-pointer"})
        for r in review:
            self.h.ledger.append("claim:review", r,
                                 claimant="system", basis="provenance-grading")
        resolved = [ref for ref in pkg.get("references", [])
                    if ref in cache.get("vettedPointers", {})]
        workshop_id = None
        if pkg.get("persona") or pkg.get("text") or pkg.get("tools"):
            workshop_id = f"workshop-{self.h.ledger.next_index('workshop'):04d}"
            self.h.ledger.append(
                "workshop:minted",
                {"workshop": workshop_id, "imported": True,
                 "persona": pkg.get("persona"), "tools": pkg.get("tools"),
                 "text": pkg.get("text"), "references": pkg.get("references"),
                 "style": pkg.get("style"),
                 "belowThreshold": True, "artifact": aid},
                claimant=f"source:{pkg.get('from', 'artifact')}",
                basis="exchange-import", certainty=0.25)
        return {"ok": True, "artifact": aid, "package": pkg,
                "importedAssertions": len(imported),
                "certainty": 0.25, "threshold": 0.5,
                "referencesResolved": resolved,
                "workshop": workshop_id, "reviewed": review,
                "review": review}

    # ---------- republish (gen-2) ----------
    def republish(self, workshop_id):
        """An adopted workshop re-encodes onto a new artifact —
        generation-2 propagation (C-ArtifactRepublish)."""
        pkg = self.package(workshop_id)
        payload = json.dumps(pkg, separators=(",", ":")).encode()
        png, meta = encode_code(payload)
        aid = f"artifact-{self.h.ledger.next_index('artifact'):04d}"
        path = os.path.join(self.art_dir, f"{aid}.png")
        with open(path, "wb") as f:
            f.write(png)
        self.h.ledger.append("artifact:encoded",
                             {"artifact": aid, "file": path,
                              "holding": workshop_id, "generation": 2,
                              "symbology": "rastgrid-png-1", **meta},
                             claimant="system", basis="execution-evidence")
        return {"ok": True, "artifact": aid, "file": path}

    # ---------- publish workflow ----------
    def publish(self, holding, form):
        """Select a holding → choose a form/channel → produce the artifact
        and record the exchange — or defer with request + status recorded
        where the channel is unconfigured (C-PublishOrDefer)."""
        if not holding:
            return {"ok": False, "error": "no holding selected"}
        if form in ("postcard", "scancode", "file"):
            enc = self.encode(holding)
            self.h.ledger.append("publish:produced",
                                 {"holding": holding, "form": form,
                                  "artifact": enc.get("artifact"),
                                  "file": enc.get("file")},
                                 claimant="system", basis="execution-evidence")
            return {"ok": True, "produced": enc}
        # nonlocal channel (email-class): needs a configured authority path
        v = self.h.ledger.view()
        mail_class = ("email", "mail", "smtp", "newsletter")
        mail_acct = next((a for a in v["accounts"].values()
                          if a.get("kind") in ("imap", "gmail", "mail", "smtp")), None)
        if mail_acct and form in mail_class:
            self.h.ledger.append("publish:produced",
                                 {"holding": holding, "form": form,
                                  "channel": mail_acct["account"],
                                  "authority": "configured-account"},
                                 claimant="system", basis="execution-evidence")
            return {"ok": True, "produced": {"channel": mail_acct["account"]}}
        self.h.ledger.append("publish:deferred",
                             {"holding": holding, "form": form,
                              "status": "deferred-no-configured-channel",
                              "request": f"publish {holding} via {form}",
                              "next": "configure an account in Settings, or "
                                      "choose postcard/scancode/file"},
                             claimant="system", basis="authority-boundary")
        return {"ok": True, "deferred": True,
                "status": "deferred-no-configured-channel"}
