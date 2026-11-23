# AGENTS.md — harness-ui (harness line of development)

A development-harness project folder per `C:\Harness\harness\workflow.md`. The object
under refinement is `prompt.md`; builds are disposable evidence.

## Layout

- `prompt.md` — the display spec in force (revised only at review, via owner-approved
  amendments)
- `devlog.md` — continuous development log; every cycle fills its entry before stopping
- `direction-*.md` — governing owner directions
- `version 0.1.0.xxx/` — one folder per build (emitter, shell, evidence)
- `display/` — deployed shell + emitted `data.js` for this project's own page
- `.devin/` — harness gates, JEV prompt, scenario suite, `state.json`, ACP driver

## Conventions

- Each cycle realizes the **entire application** per the current direction's baseline.
- Builds emit accessible evidence for the direction's named criteria (see `prompt.md`
  §Observable demonstrations).
- The JEV verdict (`.devin/jev-prompt.md` contract) is recorded in the cycle entry in
  `devlog.md` before the session stops. A failed cycle is recorded, not auto-retried.
- The scenario suite (`.devin/scenarios.md`) is derived from the spec corpus; directions
  name it so every JEV scores it; at review, named-but-unenacted scenarios are flagged
  as evidence gaps.
- `C:\Project` and `C:\Harness` are read-only corpora — cite by path and identifier,
  do not copy content into them or from them wholesale.
- This line **dogfoods the harness**: the product it builds is the status display the
  harness itself uses. Once a working build ships, its shell is mirrored to
  `C:\Harness\harness\templates\display/` for future projects.
