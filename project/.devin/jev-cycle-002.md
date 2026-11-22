You are the judge/evaluator (JEV) for a development-harness cycle. Score the build in this
folder against the criteria below. Do not modify any files.

The build under evaluation is `version 0.3.0.002/` (modify-and-measure from
`version 0.3.0.001/`, which is the preserved baseline — do not score the baseline
folder itself).

## Criteria

From direction-002 (all 0–1 unless noted):

- **clean launch**
- **existing features** — parity vs GreyAvatar's delivered functionality (evidence bar:
  `.devin/jev-ref-greyavatar.out` capability manifest)
- **completeness** — fraction of `prompt.md`-required behavior delivered, weighted
  toward required over optional
- **fleet install** — expected 0 unless parity with GreyAvatar's execution
- **exchange media** — expected 0 unless parity with GreyAvatar's execution
- **user score** — owner-scored at review (emit user_opinion null)
- **scenario suite** — `.devin/scenarios.md`, each scenario individually scored;
  canonical scenarios (S-list-project, S-personality-create) must be enacted for
  `enactment`-class credit
- **time to implement** — tracked, not scored; noted in the devlog entry

## Evidence

The build is required to emit accessible evidence for these criteria. Locate it — logs,
records, run output, artifacts under `version 0.3.0.002/` (see devlog Cycle 2 entry for
the builder's claimed evidence paths) — and cite specific paths and lines.

## Verdict

Output ONLY a JSON object:

```json
{
  "criteria": [
    { "name": "...", "score": 0, "evidence": ["path:line"], "confidence": 0.0, "user_opinion": null }
  ],
  "overall": 0,
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

`user_opinion` and `user_commentary` are owner-review slots: emit `null` / `[]`.
Owner silence is agreement: a criterion that draws no user commentary takes the judge's
score as its `user_opinion`.
