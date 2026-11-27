# Proposed harness amendments — APPROVED and APPLIED 2026-11-20
<!-- harness-doc kind=amendments status=adopted-upstream -->

Applied to `C:\Harness`: H1/H2/H4 → `harness/workflow.md`, H3 → `harness/rubric.md`,
scenario-suite item → `harness/templates/intake.md`.

Proposals for `C:\Harness\harness\` documents — drafted here because `C:\Harness` is
read-only from this project folder; adoption is the owner's call. Each cites its review
finding.

## H1 — `workflow.md`, intake/setup: usage-case discovery (F11)

> At project intake, derive a candidate **scenario suite** from the project corpus —
> the prompt's observable demonstrations, user-experience reference scenarios, and prior
> builds' test conventions — and propose it for owner sign-off. The suite lives
> project-side; the harness imports and syncs it at review points, it does not own it.

## H2 — `workflow.md`, cycle gate / review: unenacted-scenario flag (F11)

> At each review, named suite scenarios with no enactment evidence are flagged as
> evidence gaps. An anticipated scenario is notable in its absence; a cycle that never
> enacts a named scenario is a finding, not neutral.

## H3 — `rubric.md`, default criteria: add completeness + scenario suite + time (rubric revisions 2026-11-19)

> Default machine/owner criteria gain: **completeness** (fraction of prompt-required
> behavior delivered, weighted toward required over optional), the **scenario suite**
> (per-scenario 0–1 on ability to enact, `enactment` vs `repository` evidence class
> distinguished), and **time to implement** (tracked, not scored — elapsed wall-clock
> between successive versions in the line, all composition recorded). `new features` is
> removed from the default set; `existing features` (failure to enact previously
> demonstrated features) is retained.

## H4 — `workflow.md`, development log: cycle-close capture (F10)

> The cycle entry records session start and end at close (for `time to implement`), the
> rubric revision that judged it (already required), and the named criteria — including
> which suite scenarios were named.
