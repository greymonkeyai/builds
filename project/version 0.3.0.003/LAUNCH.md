# Launch procedure — Meridian (version 0.3.0.003)

Requirements: Windows + Python 3.10+ on PATH (no pip installs, stdlib only).

## One-line launch

```
launch.cmd
```

or, equivalently:

```
cd "version 0.3.0.003"
python -m app --port 9760 --open
```

## What a clean launch looks like

1. Console prints the boot log: registry count, seed packs, inbox ingest,
   engine modes, launch partition mount, then **readiness gate: PASS** with
   the recorded time-to-gate, then the honesty banner and the surface URL.
2. The gate's pass time is accessible evidence: `runtime/gate.json`, the
   `gate:passed` assertion, the launch log, and `runtime/last-launch.json`.
3. A launch log is written to `evidence/launch/launch-<timestamp>.log`, a
   machine-readable report to `runtime/last-launch.json` (`"ok": true`), and
   the console stream is teed to **`launch-server.out` — generated fresh by
   this version on every boot** (never a copied artifact).
4. The browser opens `http://127.0.0.1:9760` — the honesty banner at top
   carries the same engine modes and stub declarations; the status bar at
   bottom shows version, gate state, LLMs, configured sources, speech-floor
   depth, and open needs.

## Launch hygiene (G4)

- **No false success on an owned port.** Before binding, the launcher probes
  the port for a live Meridian instance. If one owns it, the launch prints
  `LAUNCH REFUSED`, writes the failure to the launch log +
  `last-launch.json` (`"ok": false`), and exits non-zero. It never reports
  success while a prior instance owns the port.
- **Exclusive bind.** The HTTP socket sets `SO_EXCLUSIVEADDRUSE` (and
  `SO_REUSEADDR` is left off — it would re-enable sharing on Windows), so a
  second process cannot silently double-bind.
- **Closing the window terminates the program.** The UI's event stream
  (SSE) is the window-presence signal: once a window has connected, closing
  the last one stops the server after a short grace period — no orphaned
  process. Headless runs pass `--no-watchdog`.
- `scripts/launch-check.py` enacts all four checks against real processes
  and writes `evidence/launch/launch-check.json`.

## Flags

| Flag | Effect |
|------|--------|
| `--port N` | serve on port N (default 9760) |
| `--runtime DIR` | use an alternate runtime dir |
| `--no-steward` | do not start the background steward thread |
| `--no-serve` | boot everything, skip the HTTP surface (used by demo harness) |
| `--no-watchdog` | never terminate on window close (headless scenario runs) |
| `--open` | open the browser |

## Verification without the browser

```
python scripts\launch-check.py   :: hygiene: boot, refusal, close-terminate
python scripts\probe.py          :: second-instance probe on port 9761
python scripts\scenarios.py      :: full 24-scenario enactment
```

## Stopping

Ctrl+C in the console, or close the browser window (watchdog stops the
program). The ledger is durable JSONL; the launch partition checkpoints at
clean shutdown — state survives restart (S-restart-recovery evidence).
