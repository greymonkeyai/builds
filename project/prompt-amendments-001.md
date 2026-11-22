# Proposed prompt amendments — SUPERSEDED (2026-11-19)

**Owner ruling 2026-11-19: P1–P5 are conventions, not prompt amendments.** Contents
carried into the conventions set (`conventions-sweep-001.md`, owner-reclassified section).
Kept as the record of the proposal.

---

# (original text follows)

# Proposed prompt amendments — drafted for owner edit/approval (2026-11-19)

Proposals only. Adoption runs through `C:\Project`'s revision process; `prompt.md` in this
folder is re-snapshotted after adoption. Each item cites its review finding.

## P1 — Named scenarios must be enacted, not proxied (F5)

Evaluability paragraph, after "The set of named criteria is supplied with each evaluation
direction and may change between runs":

> Where a named usage scenario is supplied, the implementation must *enact* it — execute
> the scenario against real inputs and expose the run's records. Canned, seeded, or
> scripted demonstrations satisfy a named scenario only when the direction explicitly
> accepts them; mechanism-preserving substitutes (a three-item list standing in for a
> large-list requirement) do not.

## P2 — Voice dynamics floor: sequential, non-overlapping respondents (F6)

§Personalities and lenses, after "their conversational dynamics are implementation
choices, provided that the resulting personalities remain distinct and relevant":

> Whatever the conversational dynamics, respondent contributions are presented so that
> each remains individually perceivable — simultaneous overlapping speech that renders
> contributions indistinct fails the requirement.

(Aligns with UX-Scenario-07's sequential-respondents candidate; worded as a floor, not a
prescription of sequence.)

## P3 — Per-personality generated art (F7)

§Personalities and lenses, in the paragraph beginning "Where the installation provides
suitable surfaces":

> A personality's presentation may be extended through generated portrait, voice, and
> characterization work; where generation capability exists, each personality's generated
> art is unique to that personality rather than shared or placeholder media.

(Makes explicit what demonstration #5 currently only implies. Flagged [prompt] pending
owner confirmation that per-personality generated art is a requirement, not a nicety.)

## P4 — User-set supremacy (owner-ruled requirement, 2026-11-19)

§Assertion ledger (or §Governing cycle), new sentence:

> A value set by the user outranks every derived, inferred, or source-supplied value
> regardless of support. The system may derive newer values, but no derived or inferred
> value may silently supersede a user-set one.

Owner rationale: the user can always override the system — required for debugging,
corrective measures, and user primacy (M-Ownership). The dyadic-top + recency mechanics
stay convention (C-CertaintyPrivilege); the guarantee is the requirement.

## P5 — Multiple-source access for personality differentiation (owner-ruled requirement, 2026-11-19)

§Personalities and lenses, strengthening "A personality may be assigned configured
sources and tools":

> The installation must be capable of accessing multiple configured sources so that
> distinct personalities can be informed by different information; the sources assigned
> to each personality are configuration, but the multi-source capability itself is
> required.

Owner rationale: multiple datasources are required for personalities to carry
genuinely different information — the lens mechanism needs more than one diet.

## Not proposed (findings that are adherence, not wording, gaps)

- **F1** imitation admonishment/permanent mark — already required verbatim in
  §Personalities; the gap is delivered behavior → direction material.
- **F2** calendar temporal reasoning — already required in §Projects and temporal
  context → direction material.
- **F3** competing-tool lifecycle — already required in demonstration #7 → direction
  material.
