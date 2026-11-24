"""Vantage core model — assertions, typed values, claimants, basis kinds.
The assertion ledger is the book of record. Rows are append-only: corrections
and supersessions are new rows that relate to earlier ones, never silent
rewrites. Every row carries its source (claimant), typed value, certainty,
contextual applicability, basis kind, time, and relationships.
"""
from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Optional
def ms() -> int:
    return int(time.time() * 1000)
def rid(prefix: str = "a") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"
# ---------------------------------------------------------------------------
# Typed values
VALUE_TYPES = ("string", "number", "boolean", "enum", "ref", "list", "map")
def tv(kind: str, v: Any) -> dict:
    if kind not in VALUE_TYPES:
        raise ValueError(f"unknown value type: {kind}")
    return {"type": kind, "v": v}
def coerce(v: Any) -> dict:
    """Best-effort TypedValue around a plain value."""
    if isinstance(v, dict) and v.get("type") in VALUE_TYPES and "v" in v:
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
# than its source provides; ceilings are enforced in ledger.confidence.
CLAIMANTS = (
    "principal",    # the user, via a surface
    "persona:",     # a persistent personality
    "steward:",     # background duty acting autonomously
    "model:",       # inference / decision model output
    "source:",      # a configured external source
    "surface:",     # a device/interface surface
    "pipeline:",    # ingest pipeline
    "engine:",      # an engine seam (llm, tts, stt, portrait)
    "tool:",        # tool execution result
    "exchange:",    # imported exchange material
    "seed:",        # install-time corpus
    "system",       # the host itself
)
def claimant_ok(c: str) -> bool:
    return any(c == p or (p.endswith(":") and c.startswith(p))
               for p in CLAIMANTS)
# ---------------------------------------------------------------------------
# Basis kinds — the ledger preserves the distinction between captured input,
# interpretation, source evidence, generated response, execution evidence,
# user choice, durable result, import, refusal.
BASIS = (
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
)
# ---------------------------------------------------------------------------
# Assertion
@dataclass
class Assertion:
    id: str
    at: int
    subject: str                # subject key, e.g. "persona:abc" / "need:xyz"
    predicate: str              # "namespace:name"
    value: dict                 # TypedValue
    claimant: str
    certainty: float            # 0..1 — truth confidence of this row
    applicability: float        # 0..1 — contextual confidence (ranks relevance)
    basis: dict                 # {"kind": <BASIS>, ...}
    supersedes: Optional[str] = None
    links: list = field(default_factory=list)   # related assertion ids
    tags: list = field(default_factory=list)
    meta: dict = field(default_factory=dict)    # operational, non-truth data
    def row(self) -> dict:
        return asdict(self)
    @staticmethod
    def from_row(d: dict) -> "Assertion":
        return Assertion(
            id=d["id"], at=d["at"], subject=d["subject"],
            predicate=d["predicate"], value=d["value"], claimant=d["claimant"],
            certainty=d.get("certainty", 1.0),
            applicability=d.get("applicability", 1.0),
            basis=d.get("basis", {"kind": "generated"}),
            supersedes=d.get("supersedes"), links=d.get("links", []),
            tags=d.get("tags", []), meta=d.get("meta", {}),
        )
def assert_that(subject: str, predicate: str, value: Any, claimant: str,
                certainty: float = 1.0, applicability: float = 1.0,
                basis: Optional[dict] = None, supersedes: Optional[str] = None,
                links: Optional[list] = None, tags: Optional[list] = None,
                meta: Optional[dict] = None) -> Assertion:
    if not claimant_ok(claimant):
        raise ValueError(f"claimant outside closed vocabulary: {claimant}")
    b = basis or {"kind": "generated"}
    if b.get("kind") not in BASIS:
        raise ValueError(f"basis outside closed vocabulary: {b.get('kind')}")
    return Assertion(
        id=rid(), at=ms(), subject=subject, predicate=predicate,
        value=coerce(value), claimant=claimant,
        certainty=max(0.0, min(1.0, float(certainty))),
        applicability=max(0.0, min(1.0, float(applicability))),
        basis=b, supersedes=supersedes, links=list(links or []),
        tags=list(tags or []), meta=dict(meta or {}),
    )
