# scenario-notes — `.devin/scenarios.md` (10 scenarios) vs `version 0.1.0.001`



Per-scenario evidence for the judge. `enactment` = the emitter/shell ran and the

artifact demonstrates the scenario; `repository` = mechanism confirmed present.



| ID | Class | Evidence |

|----|-------|----------|

| S-fleet-index | **enactment** | `evidence/dom-fleet.html` — real index over `C:\builds`: 2 rows, all six fields rendered or honestly absent, links `harness-ui/display/index.html` + `project/display/index.html` resolve to emitted pages. Payload: `evidence/payloads/fleet-data.js`. |

| S-project-summary | **enactment** | `dom-harnessui-summary.html` — every `state.json` field rendered incl. `pending_owner_questions`, `revisions`, nested `budget`/`builds`. `dom-proj-summary.html` — missing `state.json` renders an explicit gap block + per-field `absent`. |

| S-criteria-depth | **enactment** | `dom-proj-comparison.html` — 40 `<circle>` points across 7 sparse series (`v0.1`–`C4`), per-criterion lines, no point where a cycle wasn't scored. Depth picker and latest-anchored selection present in DOM; click → `#builddetail/<i>` (see `dom-proj-builddetail.html`). |

| S-convention-matrix | **enactment** | `dom-proj-comparison.html` — 224 cells over 56 corpus ids × 4 builds: 24 `cell-conformed`, 2 `cell-reckoned`, 2 `cell-na`, 196 `cell-gap` visible absences. Scenario matrix: `data-cells="182" data-filled="98"`. |

| S-current-state | **enactment** | `dom-proj-current.html` — live read: 26 `S-*` ids from `.devin/scenarios.md`, 56 ids from `C:\Project\MigrateInbound\CONVENTIONS.md`, prompt ref `C:\Project\MigrateInbound\ProjectPrompt.md`. Snapshot-vs-live distinction: `project` state.json is *missing*, so only the live set exists (no snapshot to confuse it with); `harness-ui` shows both. Fixture `stalerig` shows a live 3-id corpus read. |

| S-build-detail | **enactment** | `dom-proj-builddetail.html` — timestamps, verbatim verdict JSON (`overall`, `criteria`), `evidence citations (0)` honestly empty, devlog excerpt. Deep link `#builddetail/6` resolves the selected series point. |

| S-launch-pointer | **enactment** | Latest build: `../version 0.3.0.004/launch.cmd` rendered as a resolving link (`dom-proj-builddetail.html`). Older/unassociated verdict (`#builddetail/0`): `— no build associated with this verdict` (`dom-proj-builddetail-old.html`). |

| S-stale-refresh | **enactment** | `stale-refresh-test.py` + `dom-fx-stale-refresh.html`: headless page under `--virtual-time-budget=90000`; a writer bumped `generated_at` in `data.js`; the 30 s cache-busted script-tag poll (no `fetch()`) fired 3 times (`data-polls="3"`) and re-rendered with the newer stamp. Refocus handler reloads only on a newer stamp (same gate). |

| S-liveness-age | **enactment** | Fixture mtimes pinned 2026-11-01 → fleet DOM renders `22d` (`dom-fx-fleet.html`, `data-sec="1925725"`). Then `os.utime` on `brokenrig/devlog.md` → next `-Once` reports `age 0s` while `stalerig` stays `1925918s` (`evidence/scan-20261123-185837.log`). Exclusions (`display/`, `.devin/`, `.git/`, the run log itself) verified in code + real run logs. |

| S-honest-absence | **enactment** | `project` (real): missing `state.json` → gap block + 6 absent fields (`dom-proj-summary.html`); `brokenrig` (fixture): missing state + scenario suite + corpus → `dom-fx-brokenrig-summary.html`, `dom-fx-brokenrig-current.html` all gaps. `harness-ui` zero verdicts → `— no parsed verdict` (`dom-fleet.html`). Nothing fabricated anywhere in the suite. |



## Run logs



- `evidence/scan-20261123-185724.log` — real `-Once` over `C:\builds` (final emitter)

- `evidence/scan-20261123-185730.log` — fixture `-Once` over `fixtures/fleet`

- `evidence/scan-20261123-185837.log` — fixture re-scan after `devlog.md` mtime touch (liveness reset)



## Payload copies



`evidence/payloads/` — `fleet-data.js`, `project-data.js`, `harness-ui-data.js`,

`fx-fleet-data.js`, `fx-stalerig-data.js`, `fx-brokenrig-data.js`.

