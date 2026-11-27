# Launch procedure — Quorum (version 0.3.0.005)

Requirements: Windows + Python 3.10+ on PATH (no pip installs, stdlib only).
Optional live engines: Ollama (`llama3.2`, `moondream`) for the interactive
LLM and persona art; Windows SAPI for local speech. Their absence is
declared, never faked.

## One-line launch

```
launch.cmd
```

or, equivalently:

```
cd "version 0.3.0.005"
python -m quorum --port 9790
```

## What a clean launch looks like

1. Console prints `partition=N journal=M gate=PASS in <ms>ms` — the
   launch partition mounts before journal replay (C-LaunchPartition), then
   the readiness gate runs its checks and records its pass time.
2. A machine-readable report goes to `runtime/last-launch.json`
   (`"ok": true`); the gate's pass timestamp + time-to-gate land in
   `runtime/gate.json` and the `gate:passed` assertion.
3. The browser opens `http://127.0.0.1:9790` — honesty banner on top,
   operable roster rail (click selects, arrows reorder with a VISIBLE
   held-confidence change, pencil edits in place), needs rail with the
   steward liveness chit, declared-absences section at the bottom.

## Launch hygiene

- **Probe before bind.** The launcher probes the port for a live Quorum
  instance before binding. A second launch on an owned port prints
  `LAUNCH REFUSED` and exits 2 — no `ok:true` while a stale instance owns
  the port.
- **Exclusive bind.** Once bound, a raw socket cannot steal the port.
- **Close-terminates.** Terminating the process frees the port.
- Enactment: `scripts\launch-check.py` → `evidence\launch\launch-check.json`
  (all four legs, inline pass/fail).

## USB seed (fleet)

`launch-seed.cmd` (copied onto the medium) boots the app executing IN PLACE
from removable media — no install. First consent-gated stage copies to
`C:\builds-installed\quorum`. The medium carries `seed-log.jsonl` (courier
log) and `minted-gen2\` (a fresh installer with the founding network's
identity as an adoptable offer).

## Checks

`run-checks.cmd` runs launch hygiene then the full 44-scenario suite,
writing per-scenario evidence with inline check results to
`evidence\scenarios\`.
