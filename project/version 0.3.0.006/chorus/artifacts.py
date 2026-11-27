"""Artifact exchange — scannable-code interchange (C-ScannableInterchange;
symbology free per owner ruling 2026-11-25), workshop artifacts (C-Workshop-
Artifact, C-InterpretedArtifact, C-ToolWireFidelity, C-ArtifactCapture,
C-ArtifactRepublish, C-PreloadCache).
`rastgrid` is this build's 2D-matrix symbology: payload bytes -> BMP grid
with finder patterns + CRC32; decode reads the grid back. It round-trips
end to end: generate -> carry -> scan/decode -> import.
"""
import json
import os
import struct
import zlib
from .book import fresh_id, now_iso
CELL = 6          # pixels per module
MARGIN = 2        # quiet-zone cells
FINDER = 7        # finder pattern cells
def _grid_size(nbits):
    import math
    n = max(21, int(math.ceil(math.sqrt(nbits))) + 2 * FINDER + 4)
    return n + (n % 2)
def encode_rastgrid(payload: bytes, path):
    """Encode bytes to a BMP scannable matrix. Returns meta."""
    crc = zlib.crc32(payload)
    body = len(payload).to_bytes(4, "big") + payload + crc.to_bytes(4, "big")
    bits = []
    for b in body:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)
    n = _grid_size(len(bits))
    grid = [[0] * n for _ in range(n)]
    def finder(r, c):
        for dr in range(FINDER):
            for dc in range(FINDER):
                on = dr in (0, FINDER - 1) or dc in (0, FINDER - 1) or \
                    (2 <= dr <= 4 and 2 <= dc <= 4)
                grid[r + dr][c + dc] = 1 if on else 0
    finder(0, 0)
    finder(0, n - FINDER)
    finder(n - FINDER, 0)
    grid[n - FINDER][n - FINDER - 1] = 1   # dark module
    # write bits row-major skipping finders + the reserved cell
    def reserved(r, c):
        return (r < FINDER and c < FINDER) or \
               (r < FINDER and c >= n - FINDER) or \
               (r >= n - FINDER and c < FINDER) or \
               (r == n - FINDER and c == n - FINDER - 1)
    bi = 0
    for r in range(n):
        for c in range(n):
            if reserved(r, c):
                continue
            if bi < len(bits):
                grid[r][c] = bits[bi]
            bi += 1
    write_bmp(path, grid, CELL)
    return {"symbology": "rastgrid-1", "modules": n,
            "payloadBytes": len(payload), "crc": crc, "file": path}
def write_bmp(path, grid, cell):
    n = len(grid)
    px = (n + 2 * MARGIN) * cell
    row_bytes = (px * 3 + 3) // 4 * 4
    img = bytearray()
    for y in range(px):
        row = bytearray()
        gr = n - 1 - (y // cell - MARGIN)
        for x in range(px):
            gc = x // cell - MARGIN
            on = 0 <= gr < n and 0 <= gc < n and grid[gr][gc]
            row += b"\x00\x00\x00" if on else b"\xff\xff\xff"
        row += b"\x00" * (row_bytes - len(row))
        img += row
    hdr = struct.pack("<2sIHHI", b"BM", 54 + len(img), 0, 0, 54)
    dib = struct.pack("<IiiHHIIiiII", 40, px, px, 1, 24, 0, len(img),
                      2835, 2835, 0, 0)
    with open(path, "wb") as f:
        f.write(hdr + dib + img)
def decode_rastgrid(path):
    """Scan/decode a rastgrid BMP back to payload bytes. Literal fidelity —
    a decoded payload is the same payload or a defect (C-ToolWireFidelity's
    seam generalized to packages)."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:2] != b"BM":
        raise ValueError("not a BMP")
    off = struct.unpack("<I", data[10:14])[0]
    px = struct.unpack("<i", data[18:22])[0]
    row_bytes = (px * 3 + 3) // 4 * 4
    img = data[off:]
    # infer module size: the first dark horizontal run ≥ FINDER pixels is
    # the top edge of a finder pattern = FINDER * cell wide
    cell = 1
    for y in range(px):
        row = img[y * row_bytes:y * row_bytes + px * 3]
        run = 0
        best = 0
        for x in range(px):
            if row[x * 3:x * 3 + 3] == b"\x00\x00\x00":
                run += 1
                best = max(best, run)
            else:
                run = 0
        if best >= FINDER:
            cell = max(1, best // FINDER)
            break
    margin = MARGIN
    n = px // cell - 2 * margin
    grid = []
    for gr in range(n):
        rowbits = []
        y = px - 1 - (gr + margin) * cell - cell // 2
        row = img[y * row_bytes:(y + 1) * row_bytes]
        for gc in range(n):
            x = (gc + margin) * cell + cell // 2
            rowbits.append(1 if row[x * 3:x * 3 + 3] == b"\x00\x00\x00" else 0)
        grid.append(rowbits)
    def reserved(r, c):
        return (r < FINDER and c < FINDER) or \
               (r < FINDER and c >= n - FINDER) or \
               (r >= n - FINDER and c < FINDER) or \
               (r == n - FINDER and c == n - FINDER - 1)
    bits = []
    for r in range(n):
        for c in range(n):
            if not reserved(r, c):
                bits.append(grid[r][c])
    body = bytearray()
    for i in range(0, len(bits) - 7, 8):
        b = 0
        for j in range(8):
            b = (b << 1) | bits[i + j]
        body.append(b)
    plen = int.from_bytes(body[:4], "big")
    payload = bytes(body[4:4 + plen])
    crc = int.from_bytes(body[4 + plen:8 + plen], "big")
    ok = zlib.crc32(payload) == crc
    return {"payload": payload, "crcOk": ok, "modules": n,
            "symbology": "rastgrid-1"}
# ---------------- workshops & capture ----------------
def make_workshop(host, name, persona_id=None, tool_ids=None, text="",
                  materials=None, style=None):
    """A workshop: persona + tool + explanatory text + supplementary
    materials — exchangeable, accessible as an app entry."""
    w = {"id": fresh_id("workshop"), "name": name,
         "persona": persona_id, "tools": tool_ids or [],
         "text": text, "materials": materials or [],
         "style": style or {}, "created": now_iso()}
    host.book.append("workshop:created", {
        "subject": w["id"], "name": name, "persona": persona_id,
        "tools": w["tools"]}, claimant="host", basis="durable-result")
    return w
def encode_workshop(host, workshop, out_dir):
    """Workshop -> scannable artifact (postcard-adjacent minimal case)."""
    payload = json.dumps({"workshop": workshop,
                          "network": host.network_id}).encode()
    path = os.path.join(out_dir, f"{workshop['id']}.bmp")
    meta = encode_rastgrid(payload, path)
    host.book.append("artifact:encoded", {
        "subject": workshop["id"], "file": path, "symbology": "rastgrid-1",
        "payloadBytes": meta["payloadBytes"]},
        claimant="host", basis="execution-evidence")
    return meta
def capture_artifact(host, bmp_path):
    """One capture yields multiple extraction layers (C-ArtifactCapture):
    literal (payload — the hard seam), semantic (candidate fields),
    stylistic (art style as an LLM reference)."""
    dec = decode_rastgrid(bmp_path)
    if not dec["crcOk"]:
        raise ValueError("CRC failed — capture refused")
    data = json.loads(dec["payload"].decode())
    literal = data
    semantic = {"name": data.get("workshop", {}).get("name"),
                "fields": list(data.get("workshop", {}).keys())}
    stylistic = {"artStyle": data.get("workshop", {}).get("style") or
                 {"note": "flat-matrix presentation — high contrast, "
                          "bold borders, postcard register"}}
    # Interpreted, not executed: contents are candidate data under
    # dubious-provenance handling (low ceiling, adjudicable)
    row = host.book.append("artifact:captured", {
        "subject": bmp_path, "literal": literal,
        "semantic": semantic, "stylistic": stylistic,
        "provenance": "artifact", "ceiling": 0.35,
        "dubious": True},
        claimant="source:artifact", certainty=0.35, basis="artifact")
    ws = data.get("workshop", {})
    wrow = host.book.append("workshop:imported", {
        "subject": ws.get("id", "workshop-foreign"),
        "name": ws.get("name"), "persona": ws.get("persona"),
        "tools": ws.get("tools", []), "text": ws.get("text"),
        "style": stylistic["artStyle"],
        "belowThreshold": True, "candidate": True,
        "source": bmp_path},
        claimant="source:artifact", certainty=0.35, basis="artifact")
    # foreign tools stage as candidates, invocable only after acceptance
    for tid in ws.get("tools", []):
        host.book.append("tool:candidate", {
            "subject": tid, "origin": bmp_path,
            "status": "candidate", "accepted": False,
            "note": "foreign tool staged — never live-by-default "
                    "(C-ToolCandidateAcceptance)"},
            claimant="source:artifact", certainty=0.35, basis="artifact")
    return {"decode": {"crcOk": dec["crcOk"], "modules": dec["modules"]},
            "capture": row["id"], "workshop": wrow["id"]}
def adopt_workshop(host, workshop_row_id):
    """Adopt an imported workshop (candidate -> adopted), enabling
    republish (C-ArtifactRepublish)."""
    row = host.book.get(workshop_row_id)
    if not row:
        return None
    claim = dict(row["claim"])
    claim["candidate"] = False
    claim["adopted"] = True
    return host.book.append("workshop:imported", claim, claimant="principal",
                            certainty=1.0, basis="user-choice",
                            relates=[row["id"]], supersedes=row["id"])
def republish(host, workshop_row, out_dir):
    """An adopted workshop re-encoded onto a new artifact — generation-2
    propagation."""
    claim = workshop_row["claim"]
    w = {"id": claim.get("subject"), "name": claim.get("name"),
         "persona": claim.get("persona"), "tools": claim.get("tools", []),
         "text": claim.get("text"), "style": claim.get("style"),
         "generation": 2}
    return encode_workshop(host, w, out_dir)
# ---------------- preload cache (C-PreloadCache) ----------------
def seed_preload_cache(host):
    """Vetted-source pointers, device decoders, marketing exemplar —
    seeded, not invented (S-preload-cache)."""
    cache = {
        "vettedSources": [{"key": "source-wikipedia", "pointer":
                           "https://en.wikipedia.org/w/api.php"},
                          {"key": "source-memory-alpha", "pointer":
                           "https://memory-alpha.fandom.com/api.php"}],
        "decoders": [{"device": "camera-bmp", "symbology": "rastgrid-1",
                      "entry": "artifacts.decode_rastgrid"}],
        "exemplars": [{"kind": "postcard", "name": "hello-postcard",
                       "note": "marketing exemplar — decodable rastgrid"}]}
    path = os.path.join(host.runtime_dir, "preload-cache.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=1)
    host.book.append("exchange:preload-cache", {
        "subject": "preload", "vettedSources": len(cache["vettedSources"]),
        "decoders": len(cache["decoders"]),
        "exemplars": len(cache["exemplars"]), "path": path},
        claimant="host", basis="durable-result")
    return cache
