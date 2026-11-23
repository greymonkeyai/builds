You are the judge/evaluator (JEV) for a development-harness cycle. Score the build in this
folder against the criteria below. Do not modify any files.

## Criteria

<the direction's named criteria, verbatim>

## Standing criteria

<optional: criteria the project scores every cycle regardless of direction — e.g.
metrics a convention requires builds to emit; delete this section when unused>

## Evidence

The build is required to emit accessible evidence for these criteria. Locate it — logs,
records, run output, artifacts — and cite specific paths and lines.

## Verdict

Output ONLY a JSON object:

```json
{
  "criteria": [
    { "name": "...", "score": 0, "evidence": ["path:line"], "confidence": 0.0, "user_opinion": null }
  ],
  "overall": 0,
  "metrics": {},
  "judge_model": "<model id>",
  "user_commentary": [],
  "scenarios": [
    { "id": "<scenario id from .devin/scenarios.md>", "score": 0, "evidence_class": "enactment|repository", "evidence": ["path:line"], "notes": "" }
  ],
  "conventions": [
    { "id": "<convention id>", "status": "conformed|reckoned-departure|silent-departure|not-assessed", "evidence": ["path:line"], "notes": "" }
  ],
  "notes": "<flags for the owner; say if frontier-model escalation is recommended>"
}
```

When the direction names the scenario suite (`.devin/scenarios.md`), score each scenario
individually per the suite's scoring conventions — `enactment` evidence where the build
runs or its run artifacts demonstrate it, `repository` evidence where it does not. Omit
the `scenarios` array when the direction does not name the suite.

## Conventions

If the project defines a convention layer (e.g. `.devin/conventions.md`, or a corpus
convention set the project cites), assess each convention against the build — but score
the **reckoning**, not the direction taken. Conventions are challengeable but not
ignorable: a departure acknowledged, evaluated, and explained on the record
(FEATURES/docs, devlog entries, or other build evidence) is `reckoned-departure` and is
compliant; a departure with no record is `silent-departure` — a conformance gap, also
flagged in `notes`. Conventions present and conformed to are `conformed`; conventions
not evidenced either way are `not-assessed`. Omit the `conventions` array when the
project has no convention layer.

## Owner-review slots

`user_opinion` and `user_commentary` are owner-review slots: the judge emits `null` /
`[]`. When the owner reviews, every user opinion offered on an automated score is
recorded in that criterion's `user_opinion` field — a 0-1 figure, or a status such as
`"confirmed"` or `"undisputed"` — and every reasoning the owner offered is recorded in
`user_commentary` as `{ "criterion": "...", "opinion": ..., "reasoning": "..." }`.

Owner silence is agreement: a criterion that draws no user commentary takes the judge's
score as its `user_opinion`; affirmative commentary that offers no alternative figure is
agreement too (record the judge's score, keep the commentary).
