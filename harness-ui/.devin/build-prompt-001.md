You are the build session for development-harness direction-001 on the
harness-ui line. Your working folder is this project folder.

Read first, in order: AGENTS.md, direction-001.md, then prompt.md (the spec
snapshot in force for this cycle). The signed scenario suite is
`.devin/scenarios.md` (10 scenarios).

Baseline: **fresh** — first build on this line. Produce `version 0.1.0.001/`
containing the emitter, the static shell with vendored dependencies, emitted
artifacts, and evidence.

Scope: realize the entire prompt — a read-only status display over the builds
root (default `C:\builds`), file://-openable, no server, no network, no
runtime deps beyond vendored files.

- **Emitter** in PowerShell: `-Once` regenerates all payloads and the fleet
  index; `-Watch <seconds>` (default 30) loops. Scans the builds root for
  folders carrying `.devin/` + `devlog.md`; emits `<root>/index.html` +
  `<root>/data.js` plus each project's `display/data.js`
  (`window.HARNESS_DATA = {...}`).
- **Static shell**: `display/index.html` + JS; `data.js` reload via
  cache-busted script tag (fetch() is blocked under file://); charts via a
  vendored single-file library or hand-rolled rendering.
- **Views** per prompt.md: fleet index (row per project: line, direction in
  force, budget spent, last verdict, liveness age, link to project page);
  project summary (all state.json fields incl. pending owner questions);
  comparison (sparse per-criterion line chart, depth picker anchored at the
  latest run, click a point → build detail; conventions/scenarios matrix
  rendering conformed / reckoned-departure / silent-departure /
  not-assessed, un-checked ids as visible gaps); current state (live corpus
  read of convention/scenario id sets + prompt revision, distinct from
  state.json snapshots); build detail (timestamps, verdict JSON, evidence
  citations, launch pointer wired only for the most recent run).
- **Refresh/liveness** per prompt.md §Architecture: visible pages poll
  data.js every 30s; refocus reloads only on a newer generated-at stamp;
  liveness = seconds since newest in-scope mtime (excluding display/,
  .devin/ internals, .git/).
- **Honest absence** everywhere: missing/unparsed data renders as a visible
  gap, never fabricated.
- **Writes only emitted artifacts** (`<project>/display/`, `<root>/index.html`,
  `<root>/data.js`, own run log) — never modifies `devlog.md`, `state.json`,
  or any other project file.
- **Run the emitter for real** against `C:\builds`: the real `project` line
  (4 cycles, verdicts, scenario suite, status files) is the test corpus.
  Emitted artifacts landing under `C:\builds\` root and
  `C:\builds\project\display\` are emitted artifacts and are expected.

Evidence (required by prompt.md §Observable demonstrations), inside
`version 0.1.0.001/`:

- `evidence/scan-<timestamp>.log` — the emitter's real `-Once` run log:
  projects discovered, files parsed, verdicts extracted, exclusions applied.
- The emitted `data.js` payloads — per project and at fleet level.
- The shell files themselves (index.html, JS, vendored dependencies).
- `evidence/render-check.*` — a headless or DOM-level check showing each
  view populated from real data (counts rendered vs present in sources).
- A build manifest recording what was built, what works, and every declared
  absence.

Scenario suite `.devin/scenarios.md` (10 scenarios): enact as many as
possible with `enactment`-class evidence; collect per-scenario evidence for
the judge. **S-fleet-index is canonical** and must be genuinely enacted —
the real fleet index over `C:\builds`, all fields, links resolving.

Scored criteria (all 0-1, from direction-001): file://-only operation,
derivation correctness, view completeness, honest absence, scenario suite.
`user score` at owner review; `time to implement` tracked, not scored.

Honesty: report failures honestly — no ok:true-while-failing, no silent
stubs, no fabricated data, no env-dependent silent degradation. A failed
cycle is recorded, not retried.

Before stopping: update the Cycle 1 entry in devlog.md — fill the
**Result:** field with what was built, where it lives, and evidence paths,
and record the session end in the **Time to implement** field. Do NOT fill
the Verdict; a separate judge session records that.
