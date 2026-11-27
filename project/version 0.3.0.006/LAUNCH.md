# chorus — launch

`chorus` is the direction-006 fresh realization of the persona appliance
prompt (rev 2026-11-25-a). Python stdlib only; no dependencies to install.

## Launch

```
launch.cmd
```

Launches like an installed program on Windows: binds `http://127.0.0.1:9790`,
opens the operator surface in the default browser. The peer protocol binds
`0.0.0.0:7871` for fleet exchange.

Launch hygiene (evidence: `evidence/launch/launch-check.json`, 4 legs):

1. **probe-before-bind** — the port is probed for a live chorus instance
   before anything binds.
2. **exclusive bind** — exactly one instance owns the port.
3. **no-ok-while-owned** — a second launch while the port is owned prints
   `LAUNCH REFUSED` and exits non-zero; it does not claim success.
4. **close-terminates** — terminating the process frees the port.

## Two-part boot (C-TwoPartExecution)

- **Part 1** — launch partition written + mounted, engines probed, the
  readiness gate runs (input readiness: primitive pipelines + primary
  interactive LLM handle accept/route input; ledger readiness: partition
  mounted, valid, queryable). Gate result + pass timestamp →
  `runtime/gate.json` (time-to-gate is a scored metric —
  `gate.timeToGateMs`).
- **Part 2** — everything after the gate: shipped personas, configured-
  source seed import + admission gate, sample library, steward, surfaces.
  The surface binds first so launch hygiene holds during the cold-boot
  admission sweep.

## Seed media launch

`launch-seed.cmd` on removable media (`H:` in the lab): the app detects the
removable drive and runs **in place** — no install required — appending to
`seed-log.jsonl` **on the medium** (witness courier). Local staging to
`C:\builds-installed\chorus` happens only after explicit consent on the
surface (`POST /api/seed/consent`); declining writes nothing locally.

## Checks

```
run-checks.cmd
```

Runs the launch-check (4 legs) then the full 71-scenario suite through the
operator surface; evidence under `evidence/`.

## Requirements

- Python 3.10+ (developed on 3.12), Windows.
- Optional: Ollama at `127.0.0.1:11434` for live replies/art (declared
  honestly when absent — `llm=live-ollama:<model>` in the banner).
- Optional: SAPI voices for speech (thin pool declared honestly).

## Runtime layout

```
runtime/
  journal.jsonl      # the durable assertion ledger (append-only)
  partition.json     # launch partition — essential slice, ordered
  gate.json          # readiness-gate result + pass timestamp
  last-launch.json   # last boot summary
  personas/          # persona records + bound art + ack wavs
  audio/             # speech-floor wavs
  artifacts/         # encoded rastgrid BMPs + packages
  network-map.json   # fleet map artifact
  preload-cache.json # vetted-source pointers, decoders, exemplars
```
