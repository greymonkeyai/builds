# Development log — harness-ui

Line of development: a read-only, file-derived status display over the builds root.
Started 2026-11-23. This log is the continuous record of this project; it is pointed
at by the owner and is not authoritative outside this project.

## Cycle entries

### Cycle 1 — 2026-11-23

- **Direction:** `direction-001.md` — SIGNED by owner 2026-11-23; first
  realization of `prompt.md` — the status display end-to-end: emitter +
  shell + data payloads over the real `C:\builds` corpus.
- **Baseline:** fresh — produces `version 0.1.0.001/`
- **Prompt:** `prompt.md` (snapshot of 2026-11-23)
- **Criteria:** file://-only operation, derivation correctness, view
  completeness, honest absence, scenario suite `.devin/scenarios.md`
  (10 scenarios; S-fleet-index canonical, must enact), user score,
  `time to implement` tracked not scored
- **Time to implement:** session start 2026-11-23 ~18:26 EST; session end
  2026-11-23 ~19:00 EST
- **Result:** `version 0.1.0.001/` — full realization. PowerShell emitter
  (`emitter\harness-emit.ps1`, `-Once` / `-Watch`) + static shell
  (`shell\index.html`, `harness.js`, `styles.css`, hand-rolled SVG, no deps).
  Ran for real against `C:\builds`: emitted `C:\builds\index.html|data.js|harness.js|styles.css`
  and `<project>\display\*` for `harness-ui` + `project`. Fleet index (2 rows,
  all fields), project summary (all `state.json` fields; missing state renders
  as gap), comparison (40 sparse points over 7 verdict series `v0.1`–`C4`;
  scenario matrix 182 cells/98 filled; convention matrix 224 cells incl. 196
  visible gaps), current state (live `C:\Project\MigrateInbound` corpus read:
  26 scenario + 56 convention ids), build detail (verdict JSON verbatim,
  launch pointer only on latest `version 0.3.0.004`, older builds show
  pointer absent). Refresh: 30 s cache-busted script-tag poll under file://,
  refocus re-render only on newer `generated_at` — enacted headless
  (`data-polls="3"`, stamp bumped → re-rendered). Liveness: newest in-scope
  mtime excluding `display/`+`.devin/`+`.git/`+own run log — fixtures pinned
  to 2026-11-01 render `22d`, mtime touch resets to `0s` next scan.
  Writes only emitted artifacts + own run log.
  Evidence: `version 0.1.0.001\evidence\` — `scan-*.log` (real + fixture +
  liveness-reset runs), `payloads\*.js`, `dom-*.html` headless render dumps,
  `render-check.md` (counts vs sources), `scenario-notes.md` (all 10
  scenarios, enactment-class), `stale-refresh-test.py`, `dump-doms.sh`.
  Build manifest: `version 0.1.0.001\build-manifest.md`.
  Fixtures: `version 0.1.0.001\fixtures\` (stalerig, brokenrig, corpus spec).
- **Verdict:**

## Prompt

Embedded in `prompt.md` (snapshot, 2026-11-23).
