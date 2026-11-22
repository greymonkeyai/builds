"""Meridian core model: assertions, typed values, predicates, claimants.

The assertion ledger is the book of record. Assertions are append-only;
corrections and supersessions are new rows. Every assertion records source,
typed value, certainty, provenance, time, and relationships.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Optional


def now_ms() -> int:
    return int(time.time() * 1000)


def new_id(prefix: str = "a") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


# --- Typed values -----------------------------------------------------------

TYPED_KINDS = ("string", "number", "boolean", "enum", "ref", "list", "map")


def typed(kind: str, v: Any, options: Optional[list] = None) -> dict:
    if kind not in TYPED_KINDS:
        raise ValueError(f"unknown typed value kind: {kind}")
    tv = {"type": kind, "v": v}
    if options is not None:
        tv["options"] = options
    return tv


def infer_typed(v: Any) -> dict:
    """Best-effort TypedValue for a plain python value."""
    if isinstance(v, dict) and v.get("type") in TYPED_KINDS and "v" in v:
        return v
    if isinstance(v, bool):
        return typed("boolean", v)
    if isinstance(v, (int, float)):
        return typed("number", v)
    if isinstance(v, (list, tuple)):
        return typed("list", list(v))
    if isinstance(v, dict):
        return typed("map", v)
    if v is None:
        return typed("string", "")
    return typed("string", str(v))


# --- Claimants (closed vocabulary) ------------------------------------------

CLAIMANT_PREFIXES = (
    "principal",       # the user, via a surface
    "persona:",        # a persistent personality
    "steward:",        # a background steward tool acting autonomously
    "model:",          # an inference/decision model output
    "source:",         # a configured external source
    "surface:",        # a device/interface surface
    "pipeline:",       # an ingest pipeline (perception, calendar, ...)
    "engine:",         # an engine seam (llm, tts, stt, portrait)
    "seed:",           # install-time corpus
    "tool:",           # a tool execution result
    "exchange:",       # an imported exchange/storefront package
    "system",          # the host itself
)


def valid_claimant(c: str) -> bool:
    return any(c == p or (p.endswith(":") and c.startswith(p)) for p in CLAIMANT_PREFIXES)


# --- Basis kinds ------------------------------------------------------------
# Preserves the distinction between captured input, interpretation, source
# evidence, generated response, execution evidence, user choice, durable
# result, and import.

BASIS_KINDS = (
    "captured-input",     # raw user input as received
    "interpretation",     # an interpretation of captured input
    "source-evidence",    # data from a configured source
    "generated",          # a generated response/draft
    "execution",          # evidence of a tool execution attempt
    "user-choice",        # an explicit witnessed user decision
    "durable-result",     # a settled result of completed work
    "import",             # imported exchange material (below threshold)
    "seed",               # install-time corpus
    "config",             # configuration assertion
    "refusal",            # a recorded refusal/deferral
)


# --- Assertion ---------------------------------------------------------------

@dataclass
class Assertion:
    subjectKey: str
    predicate: str            # "namespace:name"
    value: dict               # TypedValue
    claimant: str
    certainty: float          # 0..1 truth confidence
    context: float = 1.0      # contextual applicability confidence (ranks applicability)
    basis: dict = field(default_factory=lambda: {"kind": "generated"})
    at: int = field(default_factory=now_ms)
    supersedes: Optional[str] = None
    relates: list = field(default_factory=list)   # ids of related assertions
    tags: list = field(default_factory=list)
    id: str = field(default_factory=lambda: new_id())
    meta: dict = field(default_factory=dict)      # non-truth operational metadata

    def to_row(self) -> dict:
        d = asdict(self)
        return d

    @staticmethod
    def from_row(d: dict) -> "Assertion":
        return Assertion(
            id=d["id"], subjectKey=d["subjectKey"], predicate=d["predicate"],
            value=d["value"], claimant=d["claimant"], certainty=d["certainty"],
            context=d.get("context", 1.0), basis=d.get("basis", {"kind": "generated"}),
            at=d["at"], supersedes=d.get("supersedes"),
            relates=d.get("relates", []), tags=d.get("tags", []),
            meta=d.get("meta", {}),
        )


def make_assertion(subject: str, predicate: str, value, claimant: str,
                   certainty: float = 1.0, context: float = 1.0,
                   basis: Optional[dict] = None, supersedes: Optional[str] = None,
                   relates: Optional[list] = None, tags: Optional[list] = None,
                   meta: Optional[dict] = None) -> Assertion:
    if not valid_claimant(claimant):
        raise ValueError(f"invalid claimant: {claimant}")
    tv = infer_typed(value)
    certainty = max(0.0, min(1.0, float(certainty)))
    context = max(0.0, min(1.0, float(context)))
    return Assertion(
        subjectKey=subject, predicate=predicate, value=tv, claimant=claimant,
        certainty=certainty, context=context,
        basis=basis or {"kind": "generated"}, supersedes=supersedes,
        relates=list(relates or []), tags=list(tags or []), meta=dict(meta or {}),
    )
