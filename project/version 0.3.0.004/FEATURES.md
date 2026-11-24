# FEATURES.md — Vantage 0.3.0.004 capability manifest

Fresh realization from `prompt.md` (build cycle 4, direction-004). Python
3.10+ stdlib only — no dependencies, no package installs. Live engines
declared honestly; every mode below is what the running system reports on
`/api/honesty`.

## Engine modes on this machine (evidence: `runtime/gate.json`, launch logs)

| Engine | Mode |
|---|---|
| LLM | `live-ollama:llama3.2` — real local model |
| TTS | `sapi` — Windows SAPI, 2 voices (David, Zira); serialized speech floor with measured `playbackMs` |
| STT | `browser-webspeech-declared` — browser Web Speech API surface; absent server-side, declared |
| Sources | wikipedia (live HTTP), ics-calendar, files, rss (live), inbox-eml — each connector run recorded |

## Declared absences (counted against completeness — never faked)

- **Fleet install** — deferred by owner ruling 2026-11-23. Absent.
- **Fleet discovery** — deferred by owner ruling 2026-11-23. Absent.
- **Exchange media** — QR/AVQR encode+scan absent at this parity level;
  exchange packages import/export as JSON files only.
- **OAuth account connectors** — gmail et al. not present; local `.eml`
  inbox ingest stands in honestly.

## Feature manifest vs GreyAvatar parity bar (`.devin/jev-ref-greyavatar.out`)

| Area | Status | Where |
|---|---|---|
| Assertion ledger — append-only JSONL, typed values, claimant vocabulary, certainty, basis, supersession | implemented | `app/model.py`, `app/ledger.py` |
| Computed views / resolve / current-vs-superseded | implemented | `app/ledger.py` (`resolve`, `current_view`) |
| Contextual confidence (effective confidence, endorsement raises) | implemented | `app/ledger.py` (`effective_confidence`) |
| Needs floor — need:* lifecycle, templates, slots, candidate values, acceptance gates | implemented | `app/floor.py` |
| Tool registry + DSL steps + user-authored tools | implemented | `app/tools.py`, `app/dsl.py`, `app/builtins.py` |
| Grants/authority — witnessed grant gate, honest deferral, no fabricated effects | implemented | `app/floor.py` (`requirement` grants), `S-defer-publication` |
| Competing tools on the same need + comparison runner | implemented | `retrieve-table` vs `retrieve-category` on `set.members`; `app/compare.py`; `S-competing-tools` |
| Personalities — mint, persistent store, ethics gate + ◆ IMITATION mark, registers | implemented | `app/personas.py`, `app/host.py` (`ethics_gate`) |
| Persona voice fidelity — register constraints on truthful output; ungrounded drafts flagged + withheld; unsupported-without-source flagged | implemented (G-B/R2) | `app/personas.py` (`compose`, `_grounding`) |
| Unique bound portrait art per persona | implemented | `app/art.py` (deterministic seeded SVG), bound at mint |
| Voice configuration per persona (SAPI voices + rates) | implemented | `app/personas.py` (`_assign_voice`, `persona-voice-set`) |
| Active-personality selection + roster reorder (dyadic rank rows) | implemented (G-E/R5) | `app/personas.py` (`select`, `move`), `/api/roster/*`, rail UI |
| Speech floor — serialized playback, measured `playbackMs` | implemented | `app/speechfloor.py`; `S-speech-serialization` |
| Background stewardship — idle duties, temporal attention, persona-presented offers | implemented | `app/steward.py`, `app/temporal.py`; `S-background-present` |
| Temporal interpretation — upcoming/current/recent/far-future buckets | implemented | `app/temporal.py`, `/api/temporal` |
| Connectors — local source ingest + live wikipedia | implemented | `app/connectors.py` |
| Exchange packages — export/import below action threshold | implemented | `app/builtins.py` (`h_export_exchange`, `h_import_exchange`); `S-exchange-import` |
| Launch partition + transient boundary + snapshot inference + sequential commits | implemented | `app/host.py`, `app/ledger.py`, `app/builtins.py` |
| Readiness gate — checks, pass timestamp, time-to-gate in evidence | implemented | `app/gate.py`, `runtime/gate.json`, launch logs |
| Two-part boot + launch hygiene (owned-port refusal, close-terminate) | implemented | `app/__main__.py`, `app/api.py` watchdog; `scripts/launch-check.py` |
| UI — roster rail, Library holdings browser, personality editor, themes, inbox, chat, command, needs, exchange, settings, log, status bar | implemented | `app/ui/` |
| Live owner-facing theme selector (restyles the running surface) | implemented (G-A/R1) | `app/ui/app.js` + `data-theme` styles; `S-color-schemes` |
| Library as holdings browser (personas/tools/artifacts/packages, inspectable) | implemented (G-D/R4) | `/api/holdings`, Library tab; `S-library-browse` |
| Dyadic held-confidence (R3) | draft shape on record (skippable this run) | `rel:held-confidence:*` rows, seeded at 0.5 |
| Imitation mark for recognizable figures | implemented | `ethics_gate` + `persona:imitation-mark` + `◆ IMITATION` |
| Fleet install | **absent — declared** | — |
| Fleet discovery | **absent — declared** | — |
| Exchange media (QR/AVQR) | **absent — declared** | — |
| Studio/document composition, LAN mirror, android satellite, companion app, Tauri shell | absent — not built at this scale | — |
| Gmail/OAuth connectors | absent — declared | — |

## Convention conformance (C-\* from `C:\Project\MigrateInbound\CONVENTIONS.md`)

| Convention | Disposition |
|---|---|
| C-TwoPartExecution | conform — Part 1 boot→gate, Part 2 surface+steward (`app/__main__.py`) |
| C-ReadinessGate | conform — gate checks components, input pipeline, llm handle, ledger durable+queryable, launch partition; pass time recorded (`runtime/gate.json`, launch log, `gate:passed` assertion, `last-launch.json`) |
| C-LaunchPartition | conform — essential slice written in dependency order to `launch-partition.jsonl`, mounted before journal replay; gate tests mounted rows |
| C-TransientBoundary | conform — `runtime/transient/` reset per boot with `.boot-ok` marker |
| C-SnapshotInference | conform — respondents draft on `ledger.snapshot()`; `inference:snapshot` rows |
| C-SequentialCommit | conform — drafts commit in rank order; `inference:commit` rows |
| C-PersonalityArt | conform — art bound per persona, params recorded |
| C-EthicsGate | conform — recognizable figures: liveness research → mark + admonishment; refused patterns recorded |
| C-PresenceRoster | conform — roster order + active as dyadic ledger rows |
| C-ChorusOnAddress | conform — named persona answers regardless of rank |

Challenges: none filed this cycle.

## Evidence map

| Item | Path |
|---|---|
| Launch procedure | `LAUNCH.md` |
| Launch logs | `evidence/launch/launch-*.log`, `launch-server.out` |
| Machine-readable launch report | `runtime/last-launch.json` |
| Gate + time-to-gate | `runtime/gate.json`, launch log line `readiness gate: PASS in Nms` |
| Launch hygiene enactment | `evidence/launch/launch-check.json` (`scripts/launch-check.py`) |
| Second-instance probe | `evidence/probe-*.json` (`scripts/probe.py`) |
| 26 scenario files w/ inline checks | `evidence/scenarios/S-*.json`, `evidence/scenarios/suite.json` |
| Ledger book of record | `runtime/ledger.jsonl` |
| Launch partition | `runtime/launch-partition.jsonl` |
| Persona store + portraits | `runtime/personas.json`, `runtime/artifacts/persona-art/` |
| Exchange packages | `runtime/artifacts/exchange/` |
