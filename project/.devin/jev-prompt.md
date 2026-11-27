You are the judge/evaluator (JEV) for a development-harness cycle. Score the build in this
folder against the criteria below. Do not modify any files.

## Criteria

<the direction's named criteria, verbatim>

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
records, run output, artifacts — and cite specific paths and lines.

## Verdict

Output ONLY a JSON object:

```json
{
  "criteria": [
    { "name": "...", "category": "measured", "measure": "<raw value+unit>", "method": "<how measured>", "score": 0, "evidence": ["path:line"], "confidence": 0.0, "user_opinion": null }
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

When the direction names the scenario suite (`scenarios.md`), score each scenario
individually per its scoring conventions — `enactment` evidence where the build runs or its
run artifacts demonstrate it, `repository` evidence where it does not. Omit the `scenarios`
array when the direction does not name the suite.

## Conventions

The corpus convention layer (`C:\Project\MigrateInbound\CONVENTIONS.md`, `C-*` identifiers)
is challengeable but not ignorable. Do not score which direction a build takes on a
convention — score whether a departure was reckoned with on the record: acknowledged,
evaluated, and explained (FEATURES.md, devlog entries, or other build evidence). A
recorded challenge is compliant; a silent departure is a conformance gap — flag it in
`notes`.

`user_opinion` and `user_commentary` are owner-review slots: the judge emits `null` /
`[]`. When the owner reviews, every user opinion offered on an automated score is recorded
in that criterion's `user_opinion` field — a 0-1 figure, or a status such as `"confirmed"`
or `"undisputed"` — and every reasoning the owner offered is recorded in
`user_commentary` as `{ "criterion": "...", "opinion": ..., "reasoning": "..." }`.

Criterion kinds (rubric §Criterion kinds; owner note 2026-11-27): every
criterion carries `"category"` — `"measured"`, `"evaluated"`, or `"user"`
(default `"measured"` when omitted).

- **Measured criteria** report measurements of enumerated evidence — check
  counts, scenario pass ratios, raw timings in seconds (tenths where reasonable,
  per R-M1). They must carry `measure` (the raw value + unit) and `method` (how
  it was taken). The number is the number: the owner may rule a measurement
  failed or absent, but neither side restyles it into a 0-1 opinion. Enumerated
  tests themselves are not altered by review. Time-based criteria are measured
  in seconds, not scored 0-1.
- **Evaluated criteria** are the judgment layer: JEV 0-1 plus `confidence` —
  required, expressing how confident the evaluator is in its own score — and
  owner opinions as vibes-based highlights, not audits. A criterion left
  untouched is **unreviewed**, not agreed: `user_opinion` stays `null` and the
  JEV score reads as provisional. Affirmative commentary without a figure may
  record `"confirmed"` rather than copying the judge's number.
- **User criteria** are scores the user enters at review (satisfaction,
  ranking). The judge emits `"score": null`; the owner's figure lands in
  `user_opinion` and is indicative of user opinion on the topic — neither a
  measurement nor an evaluated judgment.
