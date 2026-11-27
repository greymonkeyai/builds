# Conventions — a new spec-corpus category (proposal, 2026-11-19)
<!-- harness-doc kind=conventions status=adopted-upstream -->

Drafted for owner edit/approval. Adoption runs through `C:\Project`'s revision process —
proposed home: `C:\Project\MigrateInbound\CONVENTIONS.md` + `InstructionsForConventions.txt`,
following the existing publication pattern.

## The layer

Between the **prompt** (specified behavior — platform-agnostic, binding by being the
prompt) and **implementation details** (free choices) sits a third specificity tier:
**conventions**. ("Requirement" is not a defined corpus term — the prompt needs no
category name for what it specifies.)

A convention is a commitment at intermediate specificity. **It can be challenged, but it
cannot be ignored.** Departures are permitted only as recorded challenges with stated
reasons; silent non-conformance is a defect — a finding, not a choice. This is the
enforceable form of M-Convention: conventions are the Schelling points that let
independent implementations converge when the prompt doesn't determine an answer.

## Force and mechanics

- **Default-binding.** An implementation follows a convention unless it records a
  challenge. "Didn't look" is non-conformance, not a choice.
- **Challengeable.** A challenge states: the convention, the departure, and the reason.
  Recorded challenges are build evidence and surface at review — the owner's
  adjudication promotes (into the prompt), retains, or retires (back to implementation
  choice) the convention.
- **Not ignorable.** An unrecorded departure counts against the build as a conformance
  gap — the criterion it costs depends on the convention (parity for realization
  conventions, completeness for behavior-shaping ones).

## What belongs here (and what doesn't)

- **Conventions:** named usage scenarios and how they're enacted; proven realizations
  that independent implementations converged on; inherited test/operator conventions;
  realizations the corpus keeps as reference (selected D-\* items reclassified).
- **Not conventions:** prompt-specified behavior and free implementation choices.
  Owner rulings land wherever the owner places them — the imitation mark stays
  prompt-specified; P1–P5 were ruled conventions 2026-11-19.
- **Test criteria can be conventions** (owner ruling 2026-11-19): evaluation
  criteria and named test scenarios may themselves be conventional — a build may
  challenge a criterion or test but must acknowledge, evaluate, and explain the
  departure.
- **Platform context can obviate** (owner ruling 2026-11-19): a platform-specific
  implementation may obviate a convention's *need* or its *method of enactment*
  (e.g., the platform enforces user-set supremacy or unifies sources elsewhere).
  That is a legitimate recorded challenge — the convention stands as the default;
  the platform rationale is the explanation.

## Seed conventions — evidence from the three-version investigation

| ID | Convention | Source / strength |
|----|-----------|-------------------|
| C-CanonicalScenarios | The line's discriminating tests are enacted per version: S-list-project (PA cities), S-personality-create, and the named suite — real inputs, not canned | Prior builds' test canon; now `scenarios.md`. Strong — two generations of test convention |
| C-ConvergentOntology | Invokable components realized as tool-as-data DSL executor / object.verb system commands / closed primitive allow-list | GreyAvatar + Meridian **independently converged** — the strongest convention evidence there is |
| C-JsonlLedger | Append-only durable JSONL assertion journal as the ledger realization | Converged: both implementations |
| C-HonestyBanner | Runtime surfaces declare capability honestly (ledger durability, engine/stub status) | Converged: both implementations |
| C-SequentialRespondents | Multiple respondents present in sequence, each able to react to earlier contributions | GreyAvatar realization + UX-Scenario-07 candidate; the perceivability floor is itself a convention (C-PerceivableRespondents, owner-ruled 2026-11-19) — sequential presentation is the conventional manner beneath it |
| C-LauncherTests | Bench/owner tests run via launcher shortcuts with env baked in; owner-facing test steps use operator surfaces only | GreyAvatar `grey-test-launchers`, `user-facing-test-instructions` conventions |
| C-DeclaredStubs | Failed or stubbed capability is declared honestly — no ok:true-while-failing, no silent degradation | GreyAvatar deficits lesson (`08-success-on-failure`, `silent-single-voice-turns`); arguably prompt-adjacent via M-Honesty — owner call |

## Owner rulings (2026-11-19)

1. **Identifier scheme: C-\* adopted** — matches the corpus pattern (E-\*, M-\*, D-\*).
2. **Challenge authority: free departure with recorded challenge.** The harness (and
   its builds) may ignore a convention provided the departure is **acknowledged,
   evaluated, and explained** — the record is the duty; review adjudicates afterward.
   Silent departure remains a defect.
3. **Reclassification sweep: proceed** — each F-entry and relevant record classified
   with explanation (`conventions-sweep-001.md`).
4. **Convention-conformance: NOT assessed.** Conformity is not a criterion — we do not
   care which direction a build goes on a convention, only that the choice was
   acknowledged, evaluated, and explained. No criterion hook; conformance is not an
   evidence input either.
