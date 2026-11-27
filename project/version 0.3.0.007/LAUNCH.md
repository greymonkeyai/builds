# vesta — launch

`vesta` is the direction-007 fresh realization of the persona appliance
prompt (rev 2026-11-25-a). Python stdlib only; no dependencies to install.

## Launch

```
launch.cmd
```

Launches like an installed program on Windows: binds
`http://127.0.0.1:9537`, opens the operator surface in the default
browser. The fleet peer protocol binds `0.0.0.0:7872` for exchange.

Launch hygiene (evidence: `evidence/launch/launch-check.json`, 4 legs,
all pass):

1. **probe-before-bind** — the port is probed for a live vesta instance
   before anything binds.
2. **exclusive bind** — exactly one instance owns the port.
3. **no-ok-while-owned** — a second launch while the port is owned prints
   `LAUNCH REFUSED` and exits non-zero; it does not claim success.
4. **close-terminates** — terminating the process frees the port.

## Two-part boot (C-TwoPartExecution)

- **Part 1** — launch partition written + mounted, engines probed, the
  readiness gate runs (input readiness: primitive pipelines + primary
  interactive LLM handle; ledger readiness: partition mounted, valid,
  queryable). Gate result, pass timestamp, and elapsed time →
  `runtime/gate.json` (`timeToGateMs` — a standing scored metric;
  mirrored into `evidence/launch/launch-check.json` as
  `timeToGateSeconds`).
- **Part 2** — everything after the gate: shipped persona mint,
  configured-source seed import + admission gate, sample library,
  steward, surfaces. The surface binds first so launch hygiene holds
  during the cold-boot admission sweep.

## Seed media launch

On removable media (`H:` in the lab — the `build`-labeled USB drive),
run the suite's courier path from the operator surface or:

```
python scripts/run-suite.py --green   # exercises seed-run legs
```

The app detects the medium and runs the courier **in place** — appending
to `seed-log.jsonl` **on the medium** (witness courier, accumulates
across machines and runs). Local staging happens only after explicit
consent on the surface; declining writes nothing locally. The medium
also carries the minted gen-2 seed image and staged install payloads.

## Checks

```
run-checks.cmd
```

Runs the launch-check (4 legs) then the full phase-0 suite through the
operator surface: all-red baseline (`--bare`), green run, and three
sabotage passes (`empty-store`, `stub-engines`, `stubbed-endpoints`).
Evidence lands under `evidence/` — per-scenario records
(`evidence/scenarios/S-*.json`) carry the frozen check names from
`scenarios.md` inline.

## Requirements

- Python 3.10+ (developed on 3.12), Windows.
- Optional: Ollama at `127.0.0.1:11434` for live replies/art
  (`llm=live-ollama:llama3.2:latest` in the banner when live; absence
  declared honestly).
- Optional: SAPI voices for speech (pool of 2 here — thin pool declared).
- Optional: removable `build`-labeled USB drive for the courier path.

## Runtime layout

```
runtime/
  journal.jsonl        # the durable assertion ledger (append-only)
  partition.json       # launch partition — essential slice, ordered
  gate.json            # readiness-gate result + pass timestamp + timeToGateMs
  last-launch.json     # last boot summary (node id, engines, sabotage flag)
  indices.json         # fold indices
  network-map.json     # fleet map artifact (members + non-members)
  preload-cache.json   # vetted-source pointers, decoders, exemplars
  credentials/         # host-local secrets (never enter the ledger)
  personas/            # persona records + bound portraits + ack wavs
  artifacts/           # rastgrid-png-1 encoded payloads + packages
  sample-library/      # stage audio samples
  transient/           # liveness/playback telemetry (transient boundary)
  suite-*/             # per-run suite instances (isolated runtimes)
  launch-check/        # launch-hygiene run's runtime
```
