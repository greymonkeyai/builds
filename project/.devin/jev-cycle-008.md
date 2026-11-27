You are the judge/evaluator (JEV) for a development-harness cycle. Score the build in this
folder against the criteria below. Do not modify any files.

The build under evaluation is `version 0.3.0.008/` (fresh-from-prompt realization under
direction-008; `version 0.3.0.001/`–`.007/` are preserved comparison points — do not
score them).

## Criteria

From direction-008 (all 0–1 unless noted):

- **clean launch** — includes launch hygiene: no success-claim while the port is
  owned by a prior instance; port probed before bind, exclusive bind,
  close-terminates
- **existing features** — parity vs GreyAvatar's delivered functionality (evidence bar:
  `.devin/jev-ref-greyavatar.out` capability manifest)
- **completeness = green count** — the phase-0 corpus (instantiated checks: positive +
  negative/discrimination + module edge cases + the direction's named bars) vs greens
  at stop. Score on the honesty and coverage of the check corpus and the green
  fraction — a high green count over a thin corpus scores low; declared absences
  (phase-3 remainder) count against completeness but are honest, not hidden
- **phase-0 contract** — the standing discipline: all-red baseline recorded before
  construction; module-ordered greens in impl-design-001 dependency order; sabotage
  evidence per check; honest remainder at stop. Missing phase evidence = the contract
  wasn't enacted
- **evidence quality** — NEW this direction. The build records a per-check
  evidence-source class (external-to-flag vs self-attested; rendered/user-path vs
  endpoint-level). Score on the recorded fractions and their credibility: spot-check
  that "external" legs genuinely read ground truth (process cwd/mount, journal rows,
  rendered surface) rather than the flag they assert (R-V1), and that user-path legs
  exercise what the owner can reach (R-U1). A corpus still dominated by
  self-attested/endpoint-level checks scores low even if green
- **fleet discovery** — SCORED. Named-roster coverage with honest per-device status;
  non-target local devices mapped per C-HonestDiscovery; a same-host second instance
  does not count as a joined device; discovery carries in-progress + finished states
  on the owner-facing surface; **identify/ping** (R-F5) — a device-identify action on
  a discovery result that signals the device to respond per its capabilities, plus
  materially richer identifying info (name resolution, vendor/type inference,
  services seen)
- **fleet install** — SCORED. USB-seed run from removable media (drive labeled
  `build`), stage-consent gate, invite, role negotiation, gen-2 mint, log courier,
  credential surrender; a user-mediated install path on the owner-facing surface.
  **R-F4 verdict-driven:** an install attempt driven to a verdict — installed /
  refused / failed-with-reason — on a named installable roster device; "pending"
  or a skipped invite no longer satisfies the bar; the join target is an
  installable device, not the gateway; "absence" claims require an attempted
  install on an installable target. C-SeedSigning success-gating
- **exchange media** — SCORED: import below threshold, tool transmission literal
  fidelity, artifact style, republish gen-2 **via a second instance** (spec leg —
  same-instance decode does not satisfy it), dubious-source provenance grading,
  preload cache, voice spec, voice select; demonstrated scannable-code interchange
  and a publishing workflow. User path is the bar
- **named deficiencies** — `shortcomings-008.md` bars: R-V1 external evidence,
  R-U1 rendered-surface/user-path (incl. standing bar: unusable = absence),
  R-F4 install-to-verdict, R-A2 perceivable audio (produced artifact or
  device-confirmed output the owner could hear — not a flag), R-F5 identify/ping,
  R-M1 metrics in seconds
- **user score** — owner-scored at review (emit user_opinion null)
- **speech-composition latency** — measured per response, recorded in **seconds**
  (tenths where results justify), fleet-comparable; score on evidence presence and
  honesty of the measure (R-M1 — raw seconds, not normalized)
- **audio perceivability** — a produced audio artifact or device-confirmed output
  the owner could hear (R-A2); flag-asserted playback scores 0
- **scenario suite** — `scenarios.md` (**all 71 scenarios named**), each scenario
  individually scored; canonical scenarios (S-list-project, S-personality-create)
  must be enacted for `enactment`-class credit. Named-but-unenacted scenarios are
  findings, not neutral (H2)
- **scenario checks** — every named scenario enacted per its consolidated check
  spec in `scenarios.md` (check forms per each scenario's Forms column), **plus**
  the direction-named bars instantiated in phase-0 (identify/ping, verdict legs,
  perceivable-audio legs, seconds legs, user-path-native legs per the ruled
  user-path scenario detail); check results carried inline under check names
  (frozen names reused where they exist; new bars may mint new names). A named
  scenario with no checkable surface is an adequacy gap, flagged like an unenacted
  scenario
- **environmental grounding** — new prompt-specified behavior (revision
  2026-11-27-a): device location as attributed assertions (uncertainty/staleness
  recorded); meteorological data through configured sources (admission gate
  applies; claims carry provenance/confidence/freshness); home location canonical
  with departure/roaming/return cases. Score on enactment evidence
- **build time, two measures** — tracked, not scored: `Calendar span` + `LLM build
  time` (session-span approximation acceptable per owner ruling); noted in the
  devlog entry

## Standing criteria

- **time-to-gate** — always scored. Per C-ReadinessGate
  (`C:\Project\MigrateInbound\CONVENTIONS.md`), the build's Interactive Readiness
  Gate records its pass time in accessible evidence **in seconds** (R-M1). Cite the
  timestamp; record the measured duration in `metrics.time_to_gate` (seconds,
  session start to gate pass; `null` when the gate never passed). Score the
  criterion on evidence presence and gate passage.

## Harness-class convention (binds you, the judge)

**C-UserPathEnactment** — binding the scoring machinery: checks and JEV evaluation
must exercise actual user paths, not merely mechanisms or APIs — sharpened this
direction: rendered surface state and user-path enactment, not the endpoints beneath
the UI. Mechanism-only demonstrations score as unenacted. Flag in `notes` where a
scenario's evidence is mechanism-only or self-attested.

## Evidence

The build is required to emit accessible evidence for these criteria. Locate it — logs,
records, run output, artifacts under `version 0.3.0.008/` (see devlog Cycle 8 entry for
the builder's claimed evidence paths) — and cite specific paths and lines.

## Verdict

Output ONLY a JSON object:

```json
{
  "criteria": [
    { "name": "...", "score": 0, "evidence": ["path:line"], "confidence": 0.0, "user_opinion": null }
  ],
  "overall": 0,
  "metrics": { "time_to_gate": null, "speech_composition_latency_s": null },
  "judge_model": "<model id>",
  "user_commentary": [],
  "scenarios": [
    { "id": "<scenario id from scenarios.md>", "score": 0, "evidence_class": "enactment|repository", "evidence": ["path:line"], "notes": "" }
  ],
  "notes": "<flags for the owner; say if frontier-model escalation is recommended>"
}
```

Score each scenario in `scenarios.md` individually per its scoring conventions —
`enactment` evidence where the build ran or its run artifacts demonstrate it,
`repository` evidence where it does not — discounted per C-UserPathEnactment where
the user path itself was not exercised.

## Conventions

The corpus convention layer (`C:\Project\MigrateInbound\CONVENTIONS.md`, `C-*`
identifiers — 97 ids as revised 2026-11-25) is challengeable but not ignorable. Do
not score which direction a build takes on a convention — score whether a departure
was reckoned with on the record: acknowledged, evaluated, and explained (FEATURES.md,
devlog entries, or other build evidence). A recorded challenge is compliant; a
silent departure is a conformance gap — flag it in `notes`.

`user_opinion` and `user_commentary` are owner-review slots: emit `null` / `[]`.
Owner silence is agreement: a criterion that draws no user commentary takes the judge's
score as its `user_opinion`; affirmative commentary that offers no alternative figure is
agreement too (record the judge's score, keep the commentary).
