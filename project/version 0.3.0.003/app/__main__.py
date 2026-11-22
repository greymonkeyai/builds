"""Meridian launch entry: python -m app [--port N] [--runtime DIR] [--no-serve]

Boot order (C-TwoPartExecution — Part 1 covers what the gate tests):
  Part 1: ctx mount (launch partition + ledger) -> registry -> seed packs ->
          engine probe -> Interactive Readiness Gate (records pass time).
  Part 2: steward thread -> HTTP surface -> browser -> shutdown hooks.

Launch hygiene (S-windows-launch, S-close-terminate):
  - The port is probed BEFORE binding: if a Meridian instance already owns it,
    the launch refuses — it writes the failure to the launch log and
    last-launch.json and exits non-zero. It never reports success while a
    prior instance owns the port, and the socket binds exclusively.
  - When the UI window is connected over SSE, closing the last window stops
    the program after a short grace period — no orphan processes.
Every boot writes a launch log, a last-launch.json artifact, and
launch-server.out — launch evidence is a product seam, not a test scaffold.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
import urllib.request

from . import builtins as B
from . import gate as GATE
from . import seed as S
from .api import serve, state
from .host import Ctx, VERSION
from .model import now_ms
from .steward import Steward

OUT_LINES: list = []
OUT_PATH = None


def out(m: str):
    """Console + launch-server.out tee — this version's own launch stream
    (per-version artifact, not a copied file)."""
    OUT_LINES.append(m)
    print(m, flush=True)
    if OUT_PATH:
        try:
            with open(OUT_PATH, "a", encoding="utf-8") as f:
                f.write(m + "\n")
        except Exception:
            pass


def banner(honesty: dict, port: int, gate: dict = None) -> str:
    eng = honesty["engines"]
    g = gate or {}
    lines = [
        "=" * 64,
        f"  MERIDIAN {VERSION} - local-first assertion-ledger ecosystem",
        "  personalities are lenses over one shared ledger (respondent frame)",
        "-" * 64,
        f"  ledger: durable  ({honesty['ledger']['path']})",
        f"  rows: {honesty['ledger']['total']}  live: {honesty['ledger']['live']}"
        + (f"  launch partition mounted: {honesty['ledger'].get('partitionMounted', 0)} rows"),
        f"  llm: {eng['llm']['mode']}"
        + (f" ({eng['llm']['model']})" if eng["llm"].get("model") else
           " — template fallback DECLARED"),
        f"  tts: local={eng['tts']['local']}  remote={eng['tts']['remote']}",
        f"  stt: {eng['stt']['mode']}",
        f"  portrait/art: {eng['portrait']['mode']} + generated persona art",
        f"  speech floor: serialized — admission holds until playback ends",
        f"  persona frame: {honesty['personaFrame']}",
        f"  readiness gate: {'PASSED at ' + str(g.get('passedAt')) + ' (time-to-gate ' + str(g.get('msToGate')) + 'ms)' if g.get('passed') else 'NOT PASSED — see gate.json'}",
        f"  surface: http://127.0.0.1:{port}",
        "=" * 64,
    ]
    return "\n".join(lines)


def port_owner(port: int) -> dict:
    """Probe the port before binding. Returns {owned, meridian, detail}."""
    try:
        with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/api/version", timeout=1.5) as r:
            d = json.loads(r.read().decode())
        return {"owned": True, "meridian": d.get("app") == "meridian",
                "detail": d}
    except Exception as e:
        return {"owned": False, "meridian": False, "detail": repr(e)}


def _write_launch_failure(root, runtime, reason: str, detail: dict):
    os.makedirs(os.path.join(root, "evidence", "launch"), exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    log_path = os.path.join(root, "evidence", "launch", f"launch-{ts}.log")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(OUT_LINES) + "\n")
    os.makedirs(runtime, exist_ok=True)
    rep = {"ok": False, "launched": False, "reason": reason, "detail": detail,
           "log": log_path, "version": VERSION}
    with open(os.path.join(runtime, "last-launch.json"), "w") as f:
        json.dump(rep, f, indent=2)
    return rep


def window_watchdog(ctx, srv, grace_s: float = 12.0):
    """S-close-terminate: once at least one UI window has connected (SSE),
    closing the last window terminates the program — no orphans."""
    def watch():
        while srv.sse_total == 0:
            if srv.shutting_down:
                return
            time.sleep(0.5)
        quiet = 0.0
        while True:
            if srv.shutting_down:
                return
            if srv.sse_clients:
                quiet = 0.0
            else:
                quiet += 0.5
                if quiet >= grace_s:
                    ctx.append("launch", "launch:shutdown",
                               {"reason": "last window closed",
                                "graceS": grace_s}, "system",
                               basis={"kind": "execution"})
                    srv.shutdown()
                    return
            time.sleep(0.5)
    threading.Thread(target=watch, daemon=True, name="window-watchdog").start()


def main(argv=None):
    started = now_ms()
    ap = argparse.ArgumentParser(prog="meridian")
    ap.add_argument("--port", type=int, default=9760)
    ap.add_argument("--runtime", default=None,
                    help="runtime dir (default: <build>/runtime)")
    ap.add_argument("--no-serve", action="store_true")
    ap.add_argument("--no-steward", action="store_true")
    ap.add_argument("--no-watchdog", action="store_true",
                    help="never terminate on window close (headless runs)")
    ap.add_argument("--open", action="store_true", help="open browser")
    args = ap.parse_args(argv)

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    runtime = args.runtime or os.path.join(root, "runtime")
    if not os.path.isabs(runtime):
        runtime = os.path.join(root, runtime)

    global OUT_PATH
    OUT_PATH = os.path.join(root, "launch-server.out")
    try:
        open(OUT_PATH, "w", encoding="utf-8").close()  # fresh per launch
    except Exception:
        OUT_PATH = None

    log_lines = [f"meridian {VERSION} boot "
                 f"{time.strftime('%Y-%m-%dT%H:%M:%S')}"]
    def log(m):
        log_lines.append(m)

    # ---- launch hygiene: refuse while a prior instance owns the port ----
    if not args.no_serve:
        owner = port_owner(args.port)
        if owner["owned"]:
            msg = (f"LAUNCH REFUSED: port {args.port} already owned by "
                   f"{'a running Meridian instance' if owner['meridian'] else 'another service'}"
                   f" — {owner['detail']}")
            out(msg)
            out("no second instance bound; this launch reports FAILURE, "
                "not success")
            rep = _write_launch_failure(root, runtime,
                                        "port-owned", owner)
            sys.exit(3)

    ctx = Ctx(root, runtime, started_ms=started)
    if ctx.transient_reset:
        log("transient boundary reset (previous shutdown incomplete)")

    # ================= Part 1: what the readiness gate covers ==============
    B.register_builtins(ctx)
    log(f"registry: {len(ctx.registry.components)} components "
        f"({len(ctx.registry.tools())} tools, "
        f"{len(ctx.registry.commands())} commands, "
        f"{len(ctx.registry.primitives())} primitives)")

    packs = S.load_packs(ctx, os.path.join(root, "seed-packs"))
    log(f"seed packs loaded: {packs['loaded'] or 'none-new'}")

    # Local inbox source: configure + ingest the fixture mailbox once per
    # installation so S-email-commentary has real messages to select.
    from . import connectors as CN
    if not any(c["id"] == "inbox-local" for c in CN.configured(ctx)):
        inbox = os.path.join(root, "fixtures", "inbox")
        if os.path.isdir(inbox):
            CN.configure(ctx, "inbox-local", inbox, claimant="system")
            r = CN.run(ctx, "inbox-local")
            log(f"inbox-local: {r.get('items', 0)} message(s) from "
                f"{os.path.basename(inbox)}")

    eng = ctx.engines.report()
    ctx.append("engine", "engine:mode", eng, "system",
               basis={"kind": "execution"})
    log(f"engines: llm={eng['llm']['mode']} tts-local={eng['tts']['local']} "
        f"tts-remote={eng['tts']['remote']} stt={eng['stt']['mode']}")

    log(f"launch partition: {ctx.ledger.partition_mounted} rows mounted from "
        f"{os.path.basename(ctx.ledger.partition_path or '(none)')}")

    # ---- Interactive Readiness Gate (records its pass time) ----
    ctx.gate = GATE.run_gate(ctx, started)
    log(f"readiness gate: {'PASS' if ctx.gate['passed'] else 'FAIL'} "
        f"(input={ctx.gate['inputReady']} ledger={ctx.gate['ledgerReady']} "
        f"time-to-gate={ctx.gate['msToGate']}ms)")

    honesty = ctx.honesty()
    ctx.append("launch", "launch:honesty", honesty, "system",
               basis={"kind": "execution"})

    # ================= Part 2: everything after the gate ===================
    ui_dir = os.path.join(root, "app", "ui")
    srv = None
    if not args.no_serve:
        try:
            srv = serve(ctx, args.port, ui_dir)
        except OSError as e:
            out(f"LAUNCH FAILED: could not bind :{args.port} — {e}")
            rep = _write_launch_failure(root, runtime, "bind-failed",
                                        {"error": repr(e)})
            sys.exit(4)
    actual_port = srv.server_address[1] if srv else args.port

    steward = None
    if not args.no_steward:
        steward = Steward(ctx)
        steward.start()
        log("steward: started (configurable interval, default 15s; "
            "first tick ~3s)")

    report = {"ok": True, "version": VERSION, "port": actual_port,
              "root": root, "runtime": ctx.runtime, "engines": eng,
              "components": len(ctx.registry.components),
              "ledger": ctx.ledger.stats(),
              "partitionMounted": ctx.ledger.partition_mounted,
              "transientReset": ctx.transient_reset,
              "packs": packs["loaded"],
              "gate": ctx.gate, "steward": bool(steward),
              "bootMs": ctx.boot_at}
    ctx.append("launch", "launch:report", report, "system",
               basis={"kind": "execution"})
    ctx.ledger.write_partition()  # checkpoint after first-boot seeding

    os.makedirs(os.path.join(root, "evidence", "launch"), exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    log_path = os.path.join(root, "evidence", "launch", f"launch-{ts}.log")
    log_lines.append(banner(honesty, actual_port, ctx.gate))
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")
    with open(os.path.join(ctx.runtime, "last-launch.json"), "w") as f:
        json.dump({**report, "log": log_path}, f, indent=2)

    for line in log_lines:
        out(line)

    if not ctx.gate["passed"]:
        out("WARNING: readiness gate did not pass — interaction surface "
            "serves diagnostics only; gate:check assertion recorded")
    if args.open and srv and ctx.gate["passed"]:
        try:
            import webbrowser
            webbrowser.open(f"http://127.0.0.1:{actual_port}")
        except Exception:
            pass
    if srv:
        if not args.no_watchdog:
            window_watchdog(ctx, srv)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            srv.shutting_down = True
            ctx.append("launch", "launch:shutdown",
                       {"reason": "serve loop ended"}, "system",
                       basis={"kind": "execution"})
            if steward:
                steward.stop()
            ctx.close()
    else:
        ctx.close()
    return report


if __name__ == "__main__":
    main()
