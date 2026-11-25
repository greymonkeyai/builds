# AGENTS.md — project (harness line of development)

A development-harness project folder per `C:\Harness\harness\workflow.md`. The object
under refinement is `prompt.md`; builds are disposable evidence.

## Layout

- `prompt.md` — prompt snapshot in force (revised only via `C:\Project`'s process)
- `devlog.md` — continuous development log; every cycle fills its entry before stopping
- `direction-*.md` — governing owner directions
- `version 0.3.0.xxx/` — one folder per build
- `.devin/` — harness gates (direction gate, devlog completion gate, JEV prompt)

## Conventions

- Each cycle realizes the **entire application** per the current direction's baseline.
- Builds emit accessible evidence for the direction's named criteria (see `prompt.md`
  §Observable demonstrations, evaluability paragraph).
- The JEV verdict (`.devin/jev-prompt.md` contract) is recorded in the cycle entry in
  `devlog.md` before the session stops. A failed cycle is recorded, not auto-retried.
- **Usage-case discovery (F11):** the scenario suite (`scenarios.md`) is derived
  from the project corpus — prompt §Observable demonstrations, UX reference scenarios,
  prior builds' test conventions. Directions name the suite so every JEV scores it;
  at review, named-but-unenacted scenarios are flagged as evidence gaps. The suite is
  project-side; sync it with the corpus at review points.
- `C:\Project` and `C:\Harness` are read-only corpora — cite by path and identifier
  (E-\*, M-\*, C-\*, D-\*), do not copy content into them or from them wholesale.
