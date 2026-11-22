You are the judge/evaluator (JEV) for a development-harness re-score. Score the build in
`version 0.3.0.001/` — "Meridian", version 0.3.0.001 of this line of development — under the
revised criteria (rubric revision 2026-11-19: `new features` removed, `completeness` and the
scenario suite added). Do not modify any files, in any repository. Do NOT launch or run the
application — score from the emitted artifacts and repository evidence.

## Criteria

All scores 0-1:

- **clean launch** — score from the emitted launch evidence (`LAUNCH.md`, `launch.cmd`,
  `evidence/launch/`, `runtime/last-launch.json`). Verify the artifacts are real output.
- **existing features** — parity coverage of GreyAvatar's delivered functionality; failure
  to enact previously demonstrated features counts against this score. The parity bar is the
  reference at `C:\Users\kris_\CursorProjects\GreyAvatar` — a capability manifest may exist
  at `C:\builds\project\.devin\jev-ref-greyavatar.out`; use it if present, otherwise
  inventory GreyAvatar's delivered capability yourself from repository evidence.
- **completeness** — fraction of the behavior required by `C:\builds\project\prompt.md`
  (the prompt snapshot in force) that this build actually delivers. Assess section by
  section; score the delivered fraction, weighted toward areas the prompt treats as required
  rather than optional or integration paths. Cite evidence per major covered or absent area.
- **fleet install** — expected 0 unless the build executes multi-device/fleet installation at
  parity with GreyAvatar's execution. Real evidence only, not documentation claims.
- **exchange media** — expected 0 unless the build implements exchange media (QR/AVQR
  packages, storefront import/export) at parity with GreyAvatar's execution.

(The direction also names **user score** — owner-scored at review; omit it from your verdict.)

## Evidence

The build was required to emit accessible evidence. Start from `version 0.3.0.001/FEATURES.md`,
`LAUNCH.md`, `launch.cmd`, `evidence/launch/`, `evidence/demos/` (11 transcripts + INDEX.md),
`app/` source. Verify rather than trusting the manifest: spot-check that cited artifacts exist
and that claimed capabilities have backing code or transcripts. Cite specific paths and lines.
Score down for evidence that is missing, hollow, or self-asserted without artifacts.

## Scenarios

Score each scenario in `C:\builds\project\.devin\scenarios.md` individually. The build's demo
transcripts (`evidence/demos/`) and launch artifacts are `enactment`-class evidence where they
demonstrate the scenario's outcome; mechanism-only backing is `repository` class. Where a
scenario's outcome quality cannot be judged from the artifacts, cap the score accordingly and
say so in that scenario's `notes`.

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
    { "id": "<scenario id>", "score": 0, "evidence_class": "enactment|repository", "evidence": ["path:line"], "notes": "" }
  ],
  "capability_manifest": [
    { "area": "<capability area>", "status": "implemented|partial|documented-only|absent", "evidence": ["path:line"] }
  ],
  "notes": "<flags for the owner; say if frontier-model escalation is recommended>"
}
```

`user_opinion` and `user_commentary` are owner-review slots: emit `null` / `[]`.
`capability_manifest` covers what this build actually delivered — be exhaustive over major
capability areas (ledger, tools/needs, personalities, voices/speech, images/art, surfaces/UI,
connectors/sources, background work/stewardship, projects, calendar, fleet/install,
exchange/storefront, desktop/device shells).
