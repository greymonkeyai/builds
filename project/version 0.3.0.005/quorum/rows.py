"""Quorum row model — assertions, typed values, claimants, basis kinds.

The assertion ledger is the book of record for persistent semantic state.
Rows are append-only: a correction or supersession is a NEW row related to
the old one, never a silent rewrite. Each row carries its claimant (source
of the claim), typed value, certainty, contextual applicability, basis kind,
time, and relationships to earlier rows.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any

def now_ms() -> int:
    return int(time.time() * 1000)

def new_id(prefix: str = "r") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"

# ---------------------------------------------------------------------------
# Typed values — every assertion value is tagged
VALUE_KINDS = ("string", "number", "boolean", "enum", "ref", "list", "map")

def tv(kind: str, v: Any) -> dict:
    if kind not in VALUE_KINDS:
        raise ValueError(f"unknown typed-value kind: {kind}")
    return {"kind": kind, "v": v}

def wrap(v: Any) -> dict:
    """Best-effort typed value around a plain python value."""
    if isinstance(v, dict) and v.get("kind") in VALUE_KINDS and "v" in v:
        return v
    if isinstance(v, bool):
        return tv("boolean", v)
    if isinstance(v, (int, float)):
        return tv("number", v)
    if isinstance(v, (list, tuple)):
        return tv("list", list(v))
    if isinstance(v, dict):
        return tv("map", v)
    if v is None:
        return tv("string", "")
    return tv("string", str(v))

# ---------------------------------------------------------------------------
# Claimants — closed vocabulary. An assertion cannot inherit more confidence
# than its claimant provides (ceilings enforced in book.py).
CLAIMANTS = (
    "principal",    # the user, via a surface
    "persona:",     # a persistent personality
    "steward:",     # background steward acting autonomously
    "model:",       # an inference/model lane (LLM gate, evaluator, drafter)
    "source:",      # a configured external source
    "surface:",     # a device/interface surface
    "pipeline:",    # an ingest pipeline
    "engine:",      # an engine seam (llm/tts/art/discovery)
    "tool:",        # a tool execution result
    "peer:",        # a paired sovereign install's claims
    "exchange:",    # imported exchange/artifact material
    "seed:",        # the USB seed corpus / install-time material
    "system",       # the host itself
)

def claimant_ok(c: str) -> bool:
    return any(c == p or (p.endswith(":") and c.startswith(p)) for p in CLAIMANTS)

# ---------------------------------------------------------------------------
# Basis kinds — preserves the distinction between captured input,
# interpretation, source evidence, generated response, execution evidence,
# user choice, durable result, import, refusal.
BASIS_KINDS = (
    "captured-input",
    "interpretation",
    "source-evidence",
    "generated",
    "execution",
    "user-choice",
    "durable-result",
    "import",
    "seed",
    "config",
    "refusal",
    "peer-claim",
)

# ---------------------------------------------------------------------------
@dataclass
class Assertion:
    """One append-only ledger row."""
    id: str
    at: int
    subject: str                  # what the claim is about
    predicate: str                # namespace:predicate
    value: dict                   # typed value
    claimant: str                 # closed vocabulary
    certainty: float              # claimant's own certainty in the claim
    basis: dict = field(default_factory=lambda: {"kind": "captured-input"})
    applicability: float = 1.0    # contextual confidence — ranks relevance,
                                  # separate from certainty
    relates: list = field(default_factory=list)   # ids this row refines/corrects
    supersedes: str = ""          # id this row replaces
    tags: list = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    def to_row(self) -> dict:
        d = asdict(self)
        return d

    @staticmethod
    def from_row(d: dict) -> "Assertion":
        return Assertion(
            id=d["id"], at=d["at"], subject=d["subject"],
            predicate=d["predicate"], value=d["value"],
            claimant=d["claimant"], certainty=float(d["certainty"]),
            basis=d.get("basis") or {"kind": "captured-input"},
            applicability=float(d.get("applicability", 1.0)),
            relates=list(d.get("relates") or []),
            supersedes=d.get("supersedes", ""),
            tags=list(d.get("tags") or []),
            meta=dict(d.get("meta") or {}),
        )

def make(subject: str, predicate: str, value: Any, claimant: str = "principal",
         certainty: float = 1.0, basis: str = "captured-input",
         applicability: float = 1.0, relates=None, supersedes="",
         tags=None, meta=None) -> Assertion:
    if not claimant_ok(claimant):
        raise ValueError(f"claimant outside closed vocabulary: {claimant}")
    return Assertion(
        id=new_id(), at=now_ms(), subject=subject, predicate=predicate,
        value=wrap(value), claimant=claimant, certainty=float(certainty),
        basis={"kind": basis}, applicability=float(applicability),
        relates=list(relates or []), supersedes=supersedes or "",
        tags=list(tags or []), meta=dict(meta or {}),
    )
