# build-manifest — harness-ui `version 0.1.0.001`

Cycle 1 build for direction-001. Read-only, file-derived status display over a
builds root (default `C:\builds`). `file://`-openable, no server, no network, no
runtime dependencies beyond the shell files themselves (no vendored library was
needed — charting is hand-rolled SVG inside `harness.js`).

## What was built

| artifact | path | role |
|---|---|---|
| emitter | `version 0.1.0.001\emitter\harness-emit.ps1` | PowerShell 5.1 scanner/emitter; `-Once` (default) and `-Watch <s>` |
| static shell | `version 0.1.0.001\shell\index.html`, `harness.js`, `styles.css` | renders `window.HARNESS_DATA`; polls `data.js` every 30 s via cache-busted `<script>`; refocus re-renders only on a newer `generated_at` |
| launcher | `version 0.1.0.001\launch.cmd`, `LAUNCH.md` | opens `C:\builds\index.html` |
| fixture fleet | `version 0.1.0.001\fixtures\fleet\{stalerig,brokenrig}`, `fixtures\corpus\spec` | absence / staleness / fallback / launch-pointer test corpus |
| evidence | `version 0.1.0.001\evidence\` | scan logs, DOM dumps, payload copies, render-check, helper scripts |

## What works (verified by evidence/)

- **Discovery**: scans the builds root for folders carrying `.devin/` + `devlog.md`;
  found `harness-ui` + `project` under `C:\builds`, both fixtures under the fixture root.
- **Fleet index** at `<root>/index.html`: line, direction in force, budget spent,
  last verdict, liveness age, last status, link per project (`evidence/dom-fleet.html`).
- **Project summary**: every `state.json` field rendered for `harness-ui`;
  missing `state.json` (real `project`, fixture `brokenrig`) renders an explicit
  gap block, not fabricated values (`dom-harnessui-summary.html`, `dom-proj-summary.html`).
- **Comparison**: sparse per-criterion SVG lines over 7 verdict series points
  (`v0.1, v0.2, C1, C1-rescore, C2, C3, C4`), 40 points; depth picker anchored at
  latest; click → build detail. Scenario matrix 182 cells/98 filled; convention
  matrix 224 cells (196 visible gaps, 24 conformed, 2 reckoned-departure, 2 n/a)
  (`dom-proj-comparison.html`).
- **Current state**: live read of `C:\Project\MigrateInbound\ProjectPrompt.md` +
  `CONVENTIONS.md` — 26 scenario ids, 56 convention ids — kept distinct from
  `state.json` snapshots (`dom-proj-current.html`).
- **Build detail**: timestamps, verbatim verdict JSON, evidence citations
  (honest 0 where none recorded), launch pointer only on the latest build
  (`dom-proj-builddetail.html`, `dom-proj-builddetail-old.html`).
- **Refresh**: 30 s poll via cache-busted script tag (no `fetch()` — it is blocked
  under `file://`); refocus reloads only on a newer `generated_at`. Enacted under
  virtual time: `data-polls="3"`, re-render on bumped stamp (`dom-fx-stale-refresh.html`).
- **Liveness**: seconds since newest in-scope mtime, excluding `display/`,
  `.devin/`, `.git/`, and the emitter's own run log. Fixture mtimes pinned to
  2026-11-01 render `22d`; touching `brokenrig/devlog.md` reset it to `0s` on
  the next scan (`evidence/scan-*.log`).
- **Writes**: only `<root>/index.html|data.js|harness.js|styles.css`,
  `<project>/display/*`, and its own run log. No project source file is modified.
- **Verdict extraction**: fenced ```json blocks under `verdict`/`re-score verdict`
  headings in `devlog.md`; falls back to `.devin/jev-cycle-*.out` when a cycle has
  no devlog block (enacted by `brokenrig` → `0.1 @ C1 — fixture`).

## Declared absences (honest, rendered as gaps)

- `project` has **no `.devin/state.json`** → project-summary fields + fleet
  direction/budget cells render `absent`, not defaults.
- `harness-ui` has **0 parsed verdicts** → fleet "last verdict" shows
  `— no parsed verdict`; its comparison view has no series.
- `project` verdicts carry **no evidence citations** → build detail shows
  `evidence citations (0)`.
- `brokenrig` has no `state.json`, `scenarios.md`, or derivable corpus → all
  rendered as gaps (`dom-fx-brokenrig-*.html`).
- `harness-ui` has **no derivable corpus path** in `prompt.md` → current-state
  shows "none derivable" rather than guessing `C:\Project`.
- v0.1/v0.2 reference verdicts name no build folder → launch pointer shows
  `— no build associated with this verdict`.
- The depth picker's "always include latest" and the click-through to build
  detail are verified in the DOM/code; no scripted multi-click enactment was
  attempted headlessly.
- `fetch()` is never used; no network requests occur anywhere.
