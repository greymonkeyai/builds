# hearth — launch
`hearth` is the direction-008 fresh realization of the persona appliance
prompt (rev 2026-11-27-a). Python stdlib only; no dependencies to install.
A local Ollama instance (`llama3.2`) improves replies when live; its
absence is declared, never hidden.
## Launch
```
launch.cmd [port] [data-dir]
```
Launches like an installed program on Windows: defaults to
`http://127.0.0.1:9540` with the journal/data partition under
`runtime\default`, then opens the operator surface in the default
browser. The fleet peer protocol binds `0.0.0.0:7872` for exchange.
Launch hygiene (evidence: `evidence/launch/launch-check.json`, 5 legs):
1. **probe-before-bind** — the port is probed for a live hearth before
   anything binds; an owned port is never claimed by a second instance.
2. **exclusive bind** — exactly one instance owns the port.
3. **no-ok-while-owned** — a second launch while the port is owned
   reports the existing owner and exits without claiming success.
4. **close-terminates** — terminating the process frees the port.
5. **cold launch → readiness gate** — the gate's pass timestamp and
   elapsed seconds are recorded.
## Two-part boot (C-TwoPartExecution)
- **Part 1** — launch partition written + mounted, engines probed, the
  readiness gate runs (input readiness + ledger readiness). Gate result,
  pass timestamp, and `timeToGateSeconds` → `runtime/gate.json` and the
  metrics stream (`time-to-gate` — a standing scored metric, seconds
  per R-M1).
- **Part 2** — everything after the gate: shipped persona mint +
  portraits + voice assignment, configured-source seed import +
  admission gate, preload cache, steward, surfaces. The HTTP surface
  binds first so launch hygiene holds during the cold-boot sweep.
## Seed media launch
`mint` (or the fleet surface's seed action) writes `hearth-seed` to the
BUILD removable drive (`H:`) — the full package, runnable in place:
```
H:\hearth-seed> python -m hearth --port 9545 --data data
```
No install step — it executes from the medium, detects itself as
`onRemovable` (drive type + launch dir, corroborated), and appends its
LAN log to `H:\seed-log.jsonl` — the courier record accumulates across
machines and runs. First-run consent stages to
`C:\builds-installed\hearth` only on explicit user consent; decline
leaves everything on the medium (S-usb-stage-consent evidences both
halves). Seed executables are unsigned source — AV allowlisting on
target machines is the owner's arrangement (C-SeedSigning, on record).
## Checks
```
run-checks.cmd green            rem full suite — green count
run-checks.cmd baseline         rem all-red phase-0 record
run-checks.cmd sabotage <mode>  rem empty-store|stub-engines|stubbed-endpoints
run-checks.cmd launch           rem launch-check legs
```
Evidence lands in `evidence/runs/<mode>-<ts>/summary.json` and per-
scenario `evidence/scenarios/S-*.json` (checks inline under frozen
names, per run mode).
