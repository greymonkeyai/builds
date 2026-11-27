# harness-ui — prompt (embedded snapshot, revision 2026-11-23)
<!-- harness-doc kind=prompt status=in-force -->

Build a **read-only status display** over a builds root (default `C:\builds`): a set of
static pages — openable directly from the filesystem (`file://`), no server — that
render the state of every development-harness line under the root.

The display **derives**; it never asks a session to report status. Every datum it shows
comes from artifacts the harness already requires: `devlog.md`, `.devin/` machinery,
build folders. Absence is renderable and honest: missing data is a visible gap, never
fabricated.

## Architecture

- **Static shell + data payload.** Per project: `display/index.html` + JS shell written
  once, and `display/data.js` (`window.HARNESS_DATA = {...}`) rewritten by the emitter
  each scan. The page reloads `data.js` via a cache-busted script tag — `fetch()` is
  blocked under `file://`.
- **Emitter:** a PowerShell script — `-Once` regenerates all payloads and the fleet
  index; `-Watch <seconds>` (default 30) loops. It scans the builds root for folders
  carrying `.devin/` + `devlog.md` and emits `<root>/index.html` + `<root>/data.js`
  plus each project's `display/data.js`.
- **Refresh:** while the page is visible it reloads `data.js` every 30s; on refocus it
  reloads only when the payload's generated-at stamp is newer than what is rendered.
- **Liveness** = seconds since the newest file mtime under the project, excluding
  `display/`, `.devin/` internals, and `.git/`. `devlog.md` appends count as activity.
  No heartbeat contract on builds.

## Views

- **Fleet index** — one summary row per discovered project: line name, direction in
  force, budget spent, last verdict, liveness age; each row links to the project page.
  No cross-project comparison.
- **Project summary** (default view) — the project's `state.json` fields: prompt ref,
  direction in force + clarity status, budget, criteria, baseline, builds with
  timestamps, pending owner questions.
- **Comparison** — a criteria line chart over cycles: one colored line per criterion,
  sparse (no point where a cycle wasn't scored on it); a **depth picker anchored at the
  latest** run ("show last N") — the newest build is nearly always in the comparison
  set; clicking a point opens that build's detail. Below the chart, a
  **conventions/scenarios matrix**: id × cycle cells rendering `conformed` /
  `reckoned-departure` / `silent-departure` / `not-assessed` for conventions and
  score + evidence class for scenarios. An un-checked id renders as a visible gap —
  absence is a finding, not neutral.
- **Current state** — a live read of the convention/scenario id sets and prompt
  revision from their source corpus (e.g. `C:\Project`): what the *next* cycle would
  be judged under, distinct from the per-direction snapshots in `state.json`.
- **Build detail** — timestamps, the verdict JSON, evidence citations, and a **launch
  pointer** to the build's emitted launcher artifact — wired only for the most recent
  run; older builds show it absent or stale.

## Data sources

- Verdicts (criteria, metrics, scenarios, conventions): fenced JSON in `devlog.md`
  cycle entries; `.devin/jev-cycle-*.out` as raw fallback.
- Direction in force, budget, pending questions: `.devin/state.json`.
- Build liveness: newest in-scope mtime; `.devin/last-*-status.txt` shown verbatim.
- Convention/scenario id sets: live read of the source corpus for the current-state
  view; the revision in force per direction comes from `state.json`.
- Launch pointer: the latest build's emitted launcher artifact.

## Constraints

- No network access, no server, no runtime dependencies beyond vendored files —
  opening `file:///.../index.html` from a cold checkout must work. Charts via a
  vendored single-file library (Chart.js or equivalent) or hand-rolled rendering.
- Emitter in PowerShell — fleet-hardware compatible.
- The tool writes only emitted artifacts (`<project>/display/`, `<root>/index.html`,
  `<root>/data.js`, its own run log); it never modifies `devlog.md`, `state.json`,
  or any other project file.
- Honest absence: unknown, unparsed, or missing data renders as a visible gap, never
  a fabricated value.

## Observable demonstrations (evaluability)

Builds emit accessible evidence a judge can cite without opening the UI:

- `evidence/scan-<timestamp>.log` — the emitter's `-Once` run log against the real
  builds root: projects discovered, files parsed, verdicts extracted, exclusions
  applied.
- The emitted `data.js` payloads — inspectable per project and at fleet level.
- The shell files themselves (`index.html`, JS, vendored dependencies).
- `evidence/render-check.*` — a headless or DOM-level check showing each view
  populated from real data (e.g. counts of projects, criteria, conventions rendered
  vs present in sources).
- A build manifest recording what was built, what works, and every declared absence.
