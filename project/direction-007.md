# Direction 007 — 2026-11-26
<!-- harness-doc kind=direction status=discharged since=2026-11-26 applies-to=cycle-7 -->

Drafted by the coordinator session for owner ruling. Scope is determined by
the rulings of 2026-11-26: `impl-design-001` (approved — goes `in-force` at
this direction's adoption), the phase-0 contract, and the modular-iteration
intent. Owner confirms or amends.

- **Region / variable:** Fresh realization of `prompt.md` (revision
  2026-11-25-a, unchanged) implementing the entire scenario suite in force —
  `scenarios.md`, **71 scenarios** — **organized by the module map**
  (`impl-design-001`, 11 modules + unclassified). Construction greens module
  by module in dependency order.
- **Baseline:** **fresh from prompt** (standing owner ruling; carried).
  Produce `version 0.3.0.007/`; `.006` kept intact as comparison point.
- **Cycle budget:** 1.
- **Approaches:** 1.

## Build discipline — the phase-0 contract (ruled 2026-11-26)

This is the first cycle under the new sequence; the order is the point:

1. **Phase 0 — harness before app.** Before any module's machinery exists:
   instantiate every named scenario's checks per its Forms column, **plus**
   the module's edge-case conventions as negative/discrimination tests
   (negative tests live with the positive ones in `scenarios.md` Checks),
   **plus** the sabotage pass wired in (each check must be able to fail —
   a check that passes on an empty system fails the phase). Record the
   all-red baseline run in evidence.
2. **Phase 1 — module-ordered construction.** Green module by module in
   dependency order (ledger → needs → … → shell hosts surfaces). A scenario
   is done only when its check passes **through the user path**
   (C-UserPathEnactment as construction constraint, not just scoring).
3. **Phase 2 — sabotage evidence.** For each check, break the target
   (empty store, stubbed endpoint) and show it goes red. Vacuity is
   unhidable, not just detectable.
4. **Phase 3 — honest remainder.** Whatever isn't green at stop is declared
   absence — the un-greened tail of the work order, not buried stubs.
   Completeness = **green count**.

## Build guidance

- **Named deficiencies of `.006`:** `shortcomings-007.md` (draft — owner
  ruling pending) — **R-I1 improv restraint** (truthful-reporting
  constraint suppressing improv on un-truth-able topics; improv is backed
  by personality history, marked by register not refusal) and **R-S1 style
  picker** absent from the owner surface (R1 recurrence).
- **Module structure:** `impl-design-001` — 11 modules with owned scenarios,
  edge-case conventions, surface obligations, dependencies. Stub surfaces
  are the named failure mode this structure exists to prevent: every
  module's surface obligations land on the shell and must render.
- **Expectation (owner-stated):** a real green count, not "71/71 enacted" —
  the headline completeness number will drop while becoming true. That is
  the discipline working, not a regression.
- **Corpus conventions** (97 ids): `C:\Project\MigrateInbound\CONVENTIONS.md`
  — conform-or-challenge on record; per-module assignment in
  `impl-design-001`.
- **Execution-structure conventions stand:** C-TwoPartExecution,
  C-ReadinessGate, C-LaunchPartition, C-TransientBoundary,
  C-SnapshotInference, C-SequentialCommit — conform or challenge on record;
  readiness-gate pass time recorded in accessible evidence.
- **Fleet lab facts** (carried): USB drive labeled `build` installed;
  named roster is coverage ground truth; honest per-device status;
  non-target devices mapped (C-HonestDiscovery); same-host second instance
  ≠ joined device; C-SeedSigning success-gating; do not mirror the private
  inventory into build artifacts.

## Criteria to log

- clean launch (incl. launch hygiene)
- existing features — parity vs GreyAvatar manifest
- **completeness = green count** (ruled 2026-11-26) — phase-0 corpus vs
  greens at stop
- fleet discovery — scored · fleet install — scored · exchange media —
  scored (**owner scored 0/0 last cycle on user-path grounds; the user path
  is the bar**)
- user score — owner-scored at review
- time-to-gate — standing
- speech-composition latency — measured, fleet-comparable
- scenario suite — `scenarios.md`, 71 named; canonicals must enact;
  named-but-unenacted = findings (H2)
- scenario checks — phase-0 instantiated, positive + negative + edge cases;
  sabotage evidence per check; frozen check names
- build time, two measures — tracked, not scored: `Calendar span` +
  `LLM build time`

## Read-first set (build kickoff)

`direction-007.md`, `shortcomings-007.md`, `impl-design-001.md`, `prompt.md`
(revision 2026-11-25-a), `C:\Project\MigrateInbound\CONVENTIONS.md` (97 ids),
`scenarios.md` (71 scenarios, checks + check forms), `configured-sources-001.md`.

## Review at

End of this cycle — owner scores, ranks across the line's candidates.

## Open rulings before spawn

- `shortcomings-007` approval (draft — carrying R-I1, R-S1, JEV flags as
  candidates to name).
- `impl-design-001` flips `approved → in-force` in the same edit as this
  direction's adoption.
