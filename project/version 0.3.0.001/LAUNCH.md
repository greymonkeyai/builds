# Launch procedure — Meridian (version 0.3.0.001)

Requirements: Windows + Python 3.10+ on PATH (no pip installs, stdlib only).

## One-line launch

```
launch.cmd
```

or, equivalently:

```
cd "version 0.3.0.001"
python -m app --port 9760 --open
```

## What a clean launch looks like

1. Console prints the honesty banner: `ledger: durable`, engine modes
   (`llm`, `tts`, `stt`, `portrait`), stub declarations, persona frame, and the
   surface URL.
2. A launch log is written to `evidence/launch/launch-<timestamp>.log` and a
   machine-readable report to `runtime/last-launch.json` with `"ok": true`.
3. The browser opens `http://127.0.0.1:9760` — the honesty banner at the top
   carries the same engine modes and stub declarations (nothing is silent).
4. `launch:report` and `launch:honesty` assertions are appended to the ledger
   (visible in the Library tab).

## Flags

| Flag | Effect |
|------|--------|
| `--port N` | serve on port N (default 9760) |
| `--runtime DIR` | use an alternate runtime dir |
| `--no-steward` | do not start the background steward thread |
| `--no-serve` | boot everything, skip the HTTP surface (used by demo harness) |
| `--open` | open the browser |

## Verification without the browser

```
python scripts\probe.py
```

`probe.py` launches a second instance on port 9761, polls `/api/state` and
`/api/honesty`, proves steward responsiveness while the server answers, writes
`evidence/launch/probe-<timestamp>.json`, and exits — no manual env vars.

## Stopping

Ctrl+C in the console, or close the window. The ledger is durable JSONL —
state survives restart (demonstration 8 in `evidence/demos/`).
