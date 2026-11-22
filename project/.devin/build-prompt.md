You are the build session for development-harness direction-001. Your working folder is
this project folder.

Read first, in order: AGENTS.md, direction-001.md, shortcomings-001.md, then prompt.md
(the prompt snapshot in force for this cycle).

Build the ENTIRE application described by prompt.md, fresh, into `version 0.3.0.001/`.
GreyAvatar at `C:\Users\kris_\CursorProjects\GreyAvatar` is a reference realization only —
consult it for working examples, but you have authority to reconsider any of its choices.
Do not port its architecture wholesale.

Scope: rectify the documented shortcomings per shortcomings-001.md, honoring the owner's
scope ruling — fleet install (A2/A11) and exchange media (A7) are NOT rectification
targets; the decision-model concern (A9) IS in scope.

Evidence (required by prompt.md's evaluability paragraph): emit accessible evidence
inside `version 0.3.0.001/` sufficient for a judge to score these criteria, all 0-1:
clean launch, existing features (parity with GreyAvatar's delivered functionality), new
features (beyond reference, including rectified shortcomings), fleet install, exchange
media. Concretely: a documented launch procedure plus launch logs/artifacts proving a
clean launch, and a FEATURES.md manifest enumerating each implemented capability
classified as parity vs new. Fleet install and exchange media are expected to score 0
unless you match GreyAvatar's existing execution there — do not fake them.

Honesty: report failures honestly — no ok:true-while-failing, no silent stubs, no
env-dependent silent degradation. A failed cycle is recorded, not retried.

Before stopping: update the Cycle 1 entry in devlog.md — fill the **Result:** field with
what was built, where it lives, and evidence paths. Do NOT fill the Verdict; a separate
judge session records that.
