You are the judge/evaluator (JEV) for a development-harness reference assessment. Score the
application at `C:\Users\kris_\CursorProjects\Avatars` — "Avatars", version 0.1 of this line
of development (a deprecated archive). Do not modify any files, in any repository. Do NOT
launch, build, or run the application — all scoring is repository evidence only.

## Criteria

All scores 0-1:

- **clean launch** — owner-attested 2026-11-19 ("launches just fine"). Record per attestation;
  note in `notes` that this score is owner-attested, not probed.
- **existing features** — parity coverage of GreyAvatar's delivered functionality. The parity
  bar is the reference implementation at `C:\Users\kris_\CursorProjects\GreyAvatar`:
  inventory what GreyAvatar actually implements from its repository evidence, then assess
  what fraction of that delivered capability Avatars v0.1 already had. (A capability manifest
  may also exist at `C:\builds\project\.devin\jev-ref-greyavatar.out` — use it if present,
  otherwise inventory GreyAvatar yourself.)
- **completeness** — fraction of the behavior required by `C:\builds\project\prompt.md`
  (the prompt snapshot in force) that this implementation actually delivers. Assess
  section by section against the prompt; score the delivered fraction, weighted toward
  areas the prompt treats as required rather than optional or integration paths. Cite
  evidence per major covered or absent area. (v0.1 predates this prompt snapshot — score
  against it anyway as a common yardstick, and flag the retrospective nature of the
  measurement in `notes`.)
- **fleet install** — does v0.1 execute multi-device/fleet installation at parity with
  GreyAvatar's execution? Score on real code/script evidence.
- **exchange media** — does v0.1 implement exchange media (QR/AVQR packages, storefront
  import/export) at parity with GreyAvatar's execution? Score on real code/script evidence.

(The direction also names **user score** — owner-scored at review; omit it from your verdict.
Capability present in v0.1 but absent from GreyAvatar is not a scored criterion; flag notable
instances in `notes` as lineage evidence.)

## Evidence

Start from `README.md`, `SPEC.md`, `TECHSPEC.md`, `PROGRESS.md`, `AGENTS.md` (its skills index
enumerates the subsystems), `docs/`, `src/` (especially `src/services/`, `src/app/`),
`src-tauri/`, `package.json`, launcher scripts. Verify rather than trusting documentation:
spot-check that named capabilities have real backing code. Cite specific paths and lines.
Score down for capabilities that are asserted but hollow.

## Scenarios

Score each scenario in `C:\builds\project\.devin\scenarios.md` individually. This assessment
is repository-evidence only (no launch): score **ability to enact** — the mechanism is
present and plausibly enactable — with `evidence_class: "repository"`. Where a scenario's
outcome quality cannot be judged without running, cap the score accordingly and say so in
that scenario's `notes`.

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
    { "id": "<scenario id>", "score": 0, "evidence_class": "repository", "evidence": ["path:line"], "notes": "" }
  ],
  "capability_manifest": [
    { "area": "<capability area>", "status": "implemented|partial|documented-only|absent", "evidence": ["path:line"] }
  ],
  "notes": "<flags for the owner; say if frontier-model escalation is recommended>"
}
```

`user_opinion` and `user_commentary` are owner-review slots: emit `null` / `[]`.
`capability_manifest` covers what v0.1 actually delivered — be exhaustive over major
capability areas (ledger, tools/needs, personalities, voices/speech, images/art, surfaces/UI,
connectors/sources, background work/stewardship, projects, calendar, fleet/install,
exchange/storefront, desktop/device shells).
