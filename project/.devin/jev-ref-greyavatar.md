You are the judge/evaluator (JEV) for a development-harness reference assessment. Score the
application at `C:\Users\kris_\CursorProjects\GreyAvatar` — "GreyAvatar", version 0.2 of this
line of development and the reference realization for the parity criterion. Do not modify any
files, in any repository. Do NOT launch, build, or run the application — all scoring is
repository evidence only.

## Criteria

All scores 0-1:

- **clean launch** — owner-attested 2026-11-19 ("launches just fine"). Record per attestation;
  note in `notes` that this score is owner-attested, not probed.
- **existing features** — parity coverage of GreyAvatar's delivered functionality. This repo
  IS the reference, so score 1.0 by definition — but your real output is the
  `capability_manifest` below: enumerate each capability area you confirm as actually
  implemented (real backing code, not merely documented or stubbed) with evidence paths.
  Flag capabilities that are documented but hollow or partial.
- **completeness** — fraction of the behavior required by `C:\builds\project\prompt.md`
  (the prompt snapshot in force) that this implementation actually delivers. Assess
  section by section against the prompt; score the delivered fraction, weighted toward
  areas the prompt treats as required rather than optional or integration paths. Cite
  evidence per major covered or absent area. (v0.2 substantially informed this prompt —
  verify delivered behavior anyway; a section the prompt describes is not a section the
  code implements.)
- **fleet install** — does this implementation actually execute multi-device/fleet
  installation? Score on real code/script evidence, not documentation claims.
- **exchange media** — does it actually implement exchange media (QR/AVQR packages,
  storefront import/export)? Score on real code/script evidence, not documentation claims.

(The direction also names **user score** — owner-scored at review; omit it from your verdict.)

## Evidence

Start from `README.md`, `SPEC.md`, `PROGRESS.md`, `AGENTS.md`, the `Launch-*.cmd` inventory
(each launcher is a capability claim — verify), `docs/` (decisions/, acceptance/, design/),
`src/` segment layout, `ui/`, `tests/`. Verify rather than trusting documentation: spot-check
that named capabilities have real backing code. Cite specific paths and lines. Score down for
capabilities that are asserted but hollow.

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
`capability_manifest` is the parity bar for scoring future builds — be exhaustive over major
capability areas (ledger, tools/needs, personalities, voices/speech, images/art, surfaces/UI,
connectors/sources, background work/stewardship, projects, calendar, fleet/install,
exchange/storefront, desktop/device shells).
