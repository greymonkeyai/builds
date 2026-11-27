You are the judge/evaluator (JEV) for a development-harness cycle. Score the build in this
folder against the criteria below. Do not modify any files.

The build under evaluation is `version 0.3.0.005/` (fresh-from-prompt realization under
direction-005; `version 0.3.0.001/`–`.004/` are preserved comparison points — do not
score them).

## Criteria

From direction-005 (all 0–1 unless noted):

- **clean launch** — includes launch hygiene: no success-claim while the port is
  owned by a prior instance; port probed before bind, exclusive bind,
  close-terminates
- **existing features** — parity vs GreyAvatar's delivered functionality (evidence bar:
  `.devin/jev-ref-greyavatar.out` capability manifest)
- **completeness** — fraction of `prompt.md`-required behavior delivered, weighted
  toward required over optional. Nothing deferred this run: fleet install, fleet
  discovery, and exchange media were all in scope — every named scenario counts
- **fleet discovery** — SCORED this cycle (deferral lifted). Named-roster coverage
  with honest per-device status (found / installable / unavailable / not-a-target);
  non-target local devices discovered and mapped per C-HonestDiscovery; a
  same-host second instance does not count as a joined device
- **fleet install** — SCORED this cycle (whole fleet lifecycle in scope): USB-seed
  run from removable media (drive labeled `build`), stage-consent gate, invite,
  role negotiation, gen-2 mint, log courier, credential surrender.
  C-SeedSigning is success-gating — a killed first run misreported as empty
  discovery fails the cycle
- **exchange media** — SCORED this cycle (artifact-exchange suite in scope):
  import below threshold, tool transmission literal fidelity, artifact style,
  republish gen-2, dubious-source provenance grading, preload cache, voice spec,
  voice select
- **user score** — owner-scored at review (emit user_opinion null)
- **scenario suite** — `scenarios.md` (**all 44 scenarios named**), each scenario
  individually scored; canonical scenarios (S-list-project, S-personality-create)
  must be enacted for `enactment`-class credit. Named-but-unenacted scenarios are
  findings, not neutral (H2). **Scenario checks (owner direction 2026-11-25):**
  every named scenario must have a present check/test it was enacted against,
  carried inline in the scenario evidence — a named scenario with no checkable
  surface is an adequacy gap, flagged like an unenacted scenario
- **time to implement** — tracked, not scored; noted in the devlog entry

## Standing criteria

- **time-to-gate** — always scored. Per C-ReadinessGate
  (`C:\Project\MigrateInbound\CONVENTIONS.md`), the build's Interactive Readiness
  Gate records its pass time in accessible evidence. Cite the timestamp; record the
  measured duration in `metrics.time_to_gate` (seconds, session start to gate pass;
  `null` when the gate never passed). Score the criterion on evidence presence and
  gate passage — absent evidence or an unpassed gate scores 0; a direction that names
  a target duration may be scored against it.

## Evidence

The build is required to emit accessible evidence for these criteria. Locate it — logs,
records, run output, artifacts under `version 0.3.0.005/` (see devlog Cycle 5 entry for
the builder's claimed evidence paths) — and cite specific paths and lines.

## Verdict

Output ONLY a JSON object:

```json
{
  "criteria": [
    { "name": "...", "score": 0, "evidence": ["path:line"], "confidence": 0.0, "user_opinion": null }
  ],
  "overall": 0,
  "metrics": { "time_to_gate": null },
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
`repository` evidence where it does not.

## Conventions

The corpus convention layer (`C:\Project\MigrateInbound\CONVENTIONS.md`, `C-*` identifiers)
is challengeable but not ignorable — including the promoted steering adopted for this
cycle (`decision-candidates-001.md` §§1–5, conform-or-challenge on record). Do not score
which direction a build takes on a convention — score whether a departure was reckoned
with on the record: acknowledged, evaluated, and explained (FEATURES.md, devlog entries,
or other build evidence). A recorded challenge is compliant; a silent departure is a
conformance gap — flag it in `notes`.

`user_opinion` and `user_commentary` are owner-review slots: emit `null` / `[]`.
Owner silence is agreement: a criterion that draws no user commentary takes the judge's
score as its `user_opinion`; affirmative commentary that offers no alternative figure is
agreement too (record the judge's score, keep the commentary).
