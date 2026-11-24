# Launch procedure — Vantage (version 0.3.0.004)

Requirements: Windows + Python 3.10+ on PATH (no pip installs, stdlib only).
Optional live engines: Ollama (llama3.2) for the interactive LLM; Windows
SAPI for local speech. Their absence is declared, never faked.

## One-line launch

```
launch.cmd
```

or, equivalently:

```
cd "version 0.3.0.004"
python -m app --port 9770 --open
```

## What a clean launch looks like

1. Console prints the boot log: transient boundary, launch partition mount,
   journal replay, seed packs (once — `seed:loaded` guards re-seeding),
   component manifest, engine modes, then **readiness gate: PASS** with the
   recorded time-to-gate, the honesty banner, and the surface URL.
2. The gate's pass time is accessible evidence: `runtime/gate.json`, the
   `gate:passed` assertion, the launch log under `evidence/launch/`, and
   `runtime/last-launch.json`.
3. A machine-readable launch report goes to `runtime/last-launch.json`
   (`"ok": true`) and the console stream is teed to `launch-server.out`,
   generated fresh on every boot.
4. The browser opens `http://127.0.0.1:9770` — honesty banner on top,
   operable roster rail on the left (click selects the active personality,
   ▲▼ reorders), status bar at the bottom with version, gate, LLMs,
   sources, speech floor, and open needs.

## Launch hygiene

- **No false success on an owned port.** The launcher probes the port for a
  live Vantage instance before binding. A second launch prints
  `LAUNCH REFUSED`, records the failure in the launch log and
  `last-launch.json` (`"ok": false`), and exits 3.
- **Exclusive bind.** `allow_reuse_address = False` (on Windows the socket
  is bound exclusively) — no silent double-bind.
- **Closing the window terminates the program.** The UI's SSE stream is the
  window-presence signal: once a window has connected, closing the last one
  stops the server after a short grace period — no orphaned process.
  Headless runs pass `--no-watchdog`.
- `scripts/launch-check.py` enacts all of this against real processes and
  writes `evidence/launch/launch-check.json`.

## Flags

| Flag | Effect |
|------|--------|
| `--port N` | serve on port N (default 9770) |
| `--runtime DIR` | use an alternate runtime dir |
| `--no-steward` | do not start the background steward thread |
| `--no-serve` | boot through the gate, skip the HTTP surface |
| `--no-watchdog` | never terminate on window close (headless runs) |
| `--open` | open the browser |

## Verification without the browser

```
python scripts\launch-check.py   :: hygiene: boot, refusal, close-terminate
python scripts\probe.py          :: second-instance probe on port 9771
python scripts\scenarios.py      :: full 26-scenario enactment
```

## Stopping

Ctrl+C in the console, or close the browser window (the watchdog stops the
program). The ledger is durable JSONL; the launch partition checkpoints at
clean shutdown — state survives restart.
