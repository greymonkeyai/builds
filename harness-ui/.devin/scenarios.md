# Scenario suite — harness-ui line of development

DRAFT candidate suite, derived at intake 2026-11-23 from `prompt.md` — awaiting owner
sign-off. Each scenario scores 0–1 on the implementation's **ability to enact** it.

## Scoring conventions

- **Evidence class:** `enactment` (the emitter/shell ran or its artifacts demonstrate
  the scenario) or `repository` (mechanism confirmed present — weaker).
- **Score the outcome, not just the mechanism.** Rendered output must match the
  derived data, not merely exist.
- Test corpus: the real `C:\builds\project` line (4 cycles, verdicts, scenario suite,
  status files) unless the direction names a fixture.

## Suite

| ID | Scenario | Exercises | Source |
|----|----------|-----------|--------|
| S-fleet-index | **Canonical.** `<root>/index.html` lists every machinery-carrying project — line, direction in force, budget spent, last verdict, liveness age — and links to each project page | discovery, summary | prompt §Views |
| S-project-summary | Project page renders all `state.json` fields including pending owner questions | state render | prompt §Views |
| S-criteria-depth | Comparison chart renders per-criterion sparse lines; the depth picker limits to the last N cycles and always includes the latest | chart, selection | owner 2026-11-23 |
| S-convention-matrix | Matrix shows per-id status per cycle; un-assessed ids render as visible gaps, never as pass | matrix, absence-as-finding | prompt §Views; H2 |
| S-current-state | Current-state view shows the live corpus id set; a deliberately stale `state.json` snapshot shows as distinct from it | live-vs-snapshot | owner 2026-11-23 |
| S-build-detail | Clicking a verdict point opens that build's detail: timestamps, verdict JSON, evidence citations | drilldown | prompt §Views |
| S-launch-pointer | The most recent build's detail shows a launcher pointer resolving to an existing artifact; older builds show it absent/stale | pointer, recency | owner 2026-11-23 |
| S-stale-refresh | Refocusing the page reloads `data.js` only when a newer payload exists; visible pages poll on the 30s timer | refresh | owner 2026-11-23 |
| S-liveness-age | An idle project shows a growing liveness age; a file write under a watched path resets it on next scan | derivation | prompt §Architecture |
| S-honest-absence | A project missing `state.json` or verdicts renders gaps, not fabricated values | honesty | prompt §Constraints |
