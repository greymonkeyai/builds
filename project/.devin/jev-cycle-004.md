You are the judge/evaluator (JEV) for a development-harness cycle. Score the build in this
folder against the criteria below. Do not modify any files.

The build under evaluation is `version 0.3.0.004/` (fresh-from-prompt realization under
direction-004; `version 0.3.0.001/`–`.003/` are preserved comparison points — do not
score them).

## Criteria

From direction-004 (all 0–1 unless noted):

- **clean launch** — includes launch hygiene: no success-claim while the port is
  owned by a prior instance
- **existing features** — parity vs GreyAvatar's delivered functionality (evidence bar:
  `.devin/jev-ref-greyavatar.out` capability manifest)
- **completeness** — fraction of `prompt.md`-required behavior delivered, weighted
  toward required over optional; fleet install, fleet discovery, and exchange media
  count against it
- **fleet install** — expected 0 unless parity with GreyAvatar's execution (fleet
  discovery remains deferred this cycle — a declared absence, not a scored feature)
- **exchange media** — expected 0 unless parity with GreyAvatar's execution
- **user score** — owner-scored at review (emit user_opinion null)
- **scenario suite** — `.devin/scenarios.md` (26 scenarios), each scenario
  individually scored; canonical scenarios (S-list-project, S-personality-create)
  must be enacted for `enactment`-class credit. Amended bars this cycle:
  S-color-schemes requires driving the owner-facing selector and observing the
  restyle; S-personality-roster requires selection + reorder operability; new
  S-library-browse (holdings, not a log view) and S-faithful-voice (source-accurate
  answers in register)
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
records, run output, artifacts under `version 0.3.0.004/` (see devlog Cycle 4 entry for
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
    { "id": "<scenario id from .devin/scenarios.md>", "score": 0, "evidence_class": "enactment|repository", "evidence": ["path:line"], "notes": "" }
  ],
  "notes": "<flags for the owner; say if frontier-model escalation is recommended>"
}
```

Score each scenario in `.devin/scenarios.md` individually per its scoring conventions —
`enactment` evidence where the build ran or its run artifacts demonstrate it,
`repository` evidence where it does not.

## Conventions

The corpus convention layer (`C:\Project\MigrateInbound\CONVENTIONS.md`, `C-*` identifiers)
is challengeable but not ignorable. Do not score which direction a build takes on a
convention — score whether a departure was reckoned with on the record: acknowledged,
evaluated, and explained (FEATURES.md, devlog entries, or other build evidence). A
recorded challenge is compliant; a silent departure is a conformance gap — flag it in
`notes`.

`user_opinion` and `user_commentary` are owner-review slots: emit `null` / `[]`.
Owner silence is agreement: a criterion that draws no user commentary takes the judge's
score as its `user_opinion`; affirmative commentary that offers no alternative figure is
agreement too (record the judge's score, keep the commentary).
