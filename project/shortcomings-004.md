# Named deficiencies — direction-004 (SIGNED 2026-11-23)

Compiled 2026-11-23 by the coordinator session from the owner's Cycle-3 review
(`devlog.md` Cycle-3 verdict `user_commentary`, "Owner review — Cycle 3" R1–R5)
plus the JEV Cycle-3 notes flags.

**Reframed per owner ruling 2026-11-23:** this line rebuilds fresh from prompt
every cycle until the owner says stop — no modify-and-measure rectification.
These are therefore **named deficiencies of version 0.3.0.003**: observed bars
the next fresh realization is measured against, and gaps the suite/criteria
must be able to catch. They are not instructions to patch `.003`.

## A. Owner review findings — Cycle 3 (2026-11-23)

| # | Deficiency in .003 | Bar for the fresh build |
|---|--------------------|--------------------------|
| R1 | **Style selector nonfunctional** — the requested control exists but does nothing. S-color-schemes scored 0.9 on assertion-level enactment (`ui:shell-theme` assertions + stylesheet), which the owner's live check exposes as a mechanism-not-affordance pass | The theme control must actually restyle the running surface. Suite amendment proposed: tighten S-color-schemes so enactment credit requires exercising the owner-facing selector, not only the assertion path |
| R2 | **Persona speech favors personality over accuracy; hallucinates** — voice registers carry into the system prompt and swamp fidelity; the persona produces confident invention | Persona voice is a register constraint on truthful output, not a license to invent. Candidate bars: persona answers must preserve factual content of their sources; unsupported claims flagged or withheld rather than fabricated |
| R3 | **Default profiles carry a problematic (non-dyadic) confidence value** — a free-floating scalar where confidence is a relation | Confidence modeled dyadically — held *by* a party *about* a claimant/claim — not a bare number on the profile. Shape to be confirmed with owner (open item in direction-004) |
| R4 | **Library surface just contains a log** — the Library tab presents a raw event log rather than the library | Library presents library content — the personalities, tools, packages, and artifacts the instance holds — browsable and inspectable, not a tail of the ledger. Candidate suite scenario proposed (S-library-browse) |
| R5 | **No way to select or reorder personalities** — roster panel displays but offers no selection or ordering; some personas locked out of use | Roster must allow selecting the active personality and reordering entries; every shipped persona reachable. Extends S-personality-roster's bar, or a new scenario S-personality-select |

## B. JEV Cycle-3 flags carried

| # | Flag | Bar for the fresh build |
|---|------|--------------------------|
| J1 | Roster double-seeding — 12 entries, each of the 6 preloaded names duplicated (scenario-runtime seeding bug surfaced into evidence) | No double-seeding; roster shows each persona once |
| J2 | `playbackMs: null` on floor-played rows though `heldUntilPlaybackComplete` is true — the claimed field is not populated | Populate `playbackMs` or drop the field claim; evidence fields must carry real values |
| J3 | S-competing-tools still 1-of-2 adequate — genuine 2-adequate competition only via set retrievals (F3 continues to hold) | Two adequate competing tools on the same need, enacted |
| J4 | `checkFile: null` embedded in S-close-terminate's scenario JSON — driver embedding gap (cross-referenced evidence passes) | Driver fixed so scenario files carry their check results inline |

## C. Candidate suite amendments — ADOPTED 2026-11-23

Applied to `.devin/scenarios.md` at direction-004 sign-off:

- **Tightened S-color-schemes** — enactment requires driving the actual selector
  control and observing the restyle (R1). Applied.
- **Extended S-personality-roster** — selection of active personality and
  reorder added to the scenario bar; display-only rosters fail (R5, J1).
  Coordinator recommendation (extend vs new id) taken under silence=agreement.
- **New S-library-browse** — Library surface browsable/inspectable content,
  not a log view (R4). Applied.
- **New S-faithful-voice** — factual prompt answered accurately to sources, in
  register (R2); distinctness bar (S-distinct-preloadeds) and fidelity bar must
  both hold. Applied. Owner approved the G-B fidelity bar 2026-11-23.
- **R3 confidence shape** — skippable this run (owner ruling 2026-11-23):
  dyadic-confidence modeling is draft guidance, not a required bar. Shape on
  record: under the dyadic ranking system, new personalities start at **0.5**
  held-confidence by default.

## D. Standing honesty requirements (carried)

No `ok:true`-while-failing, no silent stubs, no env-dependent silent
degradation. Declared absences (fleet install, exchange media at this parity
level) are recorded, not faked — and still count against completeness.
A failed cycle is logged, not auto-retried.
