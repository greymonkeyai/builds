# render-check — direction-001 build `version 0.1.0.001`

Headless Chrome (`--headless --dump-dom`) over `file://` URLs — no server, no
network. Each DOM artifact is saved beside this file as `dom-*.html`. Counts
below were extracted from the dumped DOM and compared against the source
artifacts the emitter parsed.

## Fleet index (`file:///C:/builds/index.html` → `dom-fleet.html`)

| field | rendered | source |
|---|---|---|
| project rows | 2 (`harness-ui`, `project`) | 2 dirs with `.devin/`+`devlog.md` |
| direction in force | `direction-001.md (signed)` / `— no state.json` | state.json present / absent |
| budget spent | `1 / 1` / `— absent` | state.json / n/a |
| last verdict | `— no parsed verdict` / `0.61 @ C4 · SWE-2 High` | devlog.md |
| liveness age | `1s` / `0s` (mtime in title attr) | newest in-scope mtime |
| last status | `—` / ACP session-ended line | `last-*-status.txt` (2 files) |
| page link | `harness-ui/display/index.html`, `project/display/index.html` | resolves to emitted pages |

3 `class="absent"` spans render the honest gaps.

## Project summary (`project/display/index.html` → `dom-proj-summary.html`)

`project` has no `.devin/state.json`. Rendered: 1 `gap` block —
".devin/state.json is missing — every state-derived field below is a gap, not a
default" — plus 6 `absent` field markers. No fabricated values.

## Project summary — populated (`harness-ui/display/index.html` → `dom-harnessui-summary.html`)

All state.json fields rendered: `line`, `prompt_ref`, `direction_in_force`,
`clarity`, `baseline`, `budget` (`total`, `spent`), `criteria`, `builds`
(`cycle`, `version`, `status`, `spawned`, `acp_session`),
`pending_owner_questions`, `revisions` (`prompt`, `conventions`, `scenarios`).
1 `absent` marker (a field the state file does not record).

## Comparison (`#comparison` → `dom-proj-comparison.html`)

| element | rendered | source |
|---|---|---|
| SVG points (`<circle>`) | 40 | 7 verdict blocks × criteria scored per cycle (sparse) |
| series labels | `v0.1, v0.2, C1, C1-rescore, C2, C3, C4` | devlog.md verdict headings |
| scenario matrix | `data-cells="182"`, `data-filled="98"` | 26 scenario ids × 7 cycles |
| convention matrix | 224 cells: 196 `cell-gap` + 24 `cell-conformed` + 2 `cell-reckoned` + 2 `cell-na` | 56 corpus ids × 4 builds, FEATURES.md dispositions |

Unchecked ids render as `cell-gap`, never as pass/neutral.

## Current state (`#current` → `dom-proj-current.html`)

| element | rendered | source |
|---|---|---|
| live scenario id set | 26 `S-*` ids, verbatim list | `.devin/scenarios.md` |
| live convention id set | 56 ids | `C:\Project\MigrateInbound\CONVENTIONS.md` |
| corpus prompt ref | `C:\Project\MigrateInbound\ProjectPrompt.md` | derived from project `prompt.md` |
| coverage section | live ids vs last verdict | emitted payload |

## Build detail (`#builddetail/6` → `dom-proj-builddetail.html`)

- headings: `build detail`, `verdict JSON (devlog.md)`, `evidence citations (0)`, `result (devlog excerpt)`
- verdict JSON rendered verbatim (`"overall"`, `"criteria"` keys present)
- launch pointer: `../version 0.3.0.004/launch.cmd` — latest build only
- evidence citations: `(0)` — honest zero; the source verdict records none

## Fixture fleet (`fixtures/fleet/index.html` → `dom-fx-fleet.html`)

| project | rendered | source |
|---|---|---|
| `brokenrig` | `— no state.json`, `— absent` budget, verdict `0.1 @ C1 — fixture` | state.json absent; verdict fell back to `.devin/jev-cycle-001.out` |
| `stalerig` | direction `direction-001.md (fixture)`, verdict `0.4 @ C2` | devlog + state.json |
| liveness | `22d` both rows (data-sec=`1925725`) | mtimes pinned to 2026-11-01 |

## Fixture project views

- `dom-fx-brokenrig-summary.html`: 1 gap + 6 absent (missing state.json, missing scenarios.md)
- `dom-fx-brokenrig-current.html`: 2 gaps + 4 absent (no corpus derivable)
- `dom-fx-stalerig-summary.html`: all state fields populated, 0 absents
- `dom-fx-stalerig-comparison.html`: 4 SVG points (2 cycles × criteria), labels `C1`, `C2`
- `dom-fx-stalerig-current.html`: 3 fixture corpus ids rendered live

## Stale-refresh (`dom-fx-stale-refresh.html`, enactment via `stale-refresh-test.py`)

A background writer bumped `generated_at` in `stalerig/display/data.js` while a
headless page ran under `--virtual-time-budget=90000`. The page's 30-second
poll fetched the cache-busted `data.js?ts=…` (fetch() is not used anywhere),
saw the newer stamp, and re-rendered:

- `data-polls="3"` — poll loop fired
- `data-stamp="2099-01-01T00:00:00Z"` — re-rendered stamp is the newer one

No reload occurs when the stamp is unchanged (same `generated_at` gate on the
refocus handler).
