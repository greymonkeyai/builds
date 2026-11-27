#!/usr/bin/env python
"""Mint the exemplar workshop artifact (C-PreloadCache marketing exemplar).

A handout-class artifact — deliberately self-interested (a political-style
handout whose references point at its own claims), so the import path
exercises genuine dubious-provenance handling.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from quorum import artifacts

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

persona = {"name": "Warden Cross", "register": "formal",
           "traits": ["persuasive", "campaign-hardened", "self-assured"],
           "characterization": "A ward-heeler persona shipped on a political "
                               "handout — its claims are ITS candidate's "
                               "claims, not verified fact."}
tool = {"id": "handout-scorer",
        "name": "Handout claim scorer",
        "purpose": "Score a handout's claims against vetted sources.",
        "explain": "Takes a claim string, resolves its references against the "
                   "preload cache's vetted pointers, and reports which claims "
                   "hold. Imported tools stay candidates until accepted.",
        "slots": {"claim": "required"}, "requiresGrant": False,
        "logic": [{"step": "ledger.search",
                   "args": {"predicate": "exchange:claim-review"}},
                  {"step": "result.card", "args": {"kind": "review"}}]}
explain = ("WARDEN CROSS FOR BOROUGH COUNCIL — handout workshop. Persona + "
           "tool + references. References point at the campaign's own "
           "material: treat every claim as dubious-provenance candidate "
           "data (C-InterpretedArtifact).")
voice = artifacts.voice_spec(["formal-narrator", "resonant"],
                             {"rate": -1, "pitch": "low", "gender": "male"})
materials = {"claims": [
    {"text": "Cross cut the salt budget 30%", "ref": "https://cross2026.example/facts"},
    {"text": "Crime fell every year of the term",
     "ref": "https://en.wikipedia.org/wiki/Pennsylvania"},
]}
payload = artifacts.bundle_workshop(persona, tool, explain, voice, materials)
out = os.path.join(HERE, "seed-packs", "exemplar-postcard.bmp")
r = artifacts.matrix_encode(payload, out)
print("encoded:", r)

# verify round-trip — the hard seam is real
d = artifacts.matrix_decode(out)
b = json.loads(d["payload"])
assert b["persona"]["name"] == "Warden Cross"
assert b["tool"]["id"] == "handout-scorer"
print("decode OK —", d["bytes"], "bytes; tool:", b["tool"]["id"])
