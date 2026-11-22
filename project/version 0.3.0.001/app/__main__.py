"""Meridian launch entry: python -m app [--port N] [--runtime DIR] [--no-serve]

Boot order: ledger -> personas -> registry -> seed packs -> engine probe ->
launch report/honesty assertions -> steward thread -> HTTP surface.
Every boot writes a launch log and a last-launch.json artifact — launch
evidence is a product seam, not a test scaffold.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

from . import builtins as B
from . import seed as S
from .api import serve, state
from .host import Ctx
from .steward import Steward


def banner(honesty: dict, port: int) -> str:
    eng = honesty["engines"]
    lines = [
        "=" * 64,
        "  MERIDIAN - local-first assertion-ledger ecosystem",
        "  personalities are lenses over one shared ledger (respondent frame)",
        "-" * 64,
        f"  ledger: durable  ({honesty['ledger']['path']})",
        f"  rows: {honesty['ledger']['total']}  live: {honesty['ledger']['live']}",
        f"  llm: {eng['llm']['mode']}"
        + (f" ({eng['llm']['model']})" if eng["llm"].get("model") else
           " — template fallback DECLARED"),
        f"  tts: local={eng['tts']['local']}  remote={eng['tts']['remote']}",
        f"  stt: {eng['stt']['mode']}",
        f"  portrait: {eng['portrait']['mode']}",
        f"  persona frame: {honesty['personaFrame']}",
        f"  surface: http://127.0.0.1:{port}",
        "=" * 64,
    ]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="meridian")
    ap.add_argument("--port", type=int, default=9760)
    ap.add_argument("--runtime", default=None,
                    help="runtime dir (default: <build>/runtime)")
    ap.add_argument("--no-serve", action="store_true")
    ap.add_argument("--no-steward", action="store_true")
    ap.add_argument("--open", action="store_true", help="open browser")
    args = ap.parse_args(argv)

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    runtime = args.runtime or os.path.join(root, "runtime")
    if not os.path.isabs(runtime):
        runtime = os.path.join(root, runtime)
    ctx = Ctx(root, runtime)

    log_lines = [f"meridian boot {time.strftime('%Y-%m-%dT%H:%M:%S')}"]
    def log(m):
        log_lines.append(m)

    B.register_builtins(ctx)
    log(f"registry: {len(ctx.registry.components)} components "
        f"({len(ctx.registry.tools())} tools, "
        f"{len(ctx.registry.commands())} commands, "
        f"{len(ctx.registry.primitives())} primitives)")

    packs = S.load_packs(ctx, os.path.join(root, "seed-packs"))
    log(f"seed packs loaded: {packs['loaded'] or 'none-new'}")

    eng = ctx.engines.report()
    ctx.append("engine", "engine:mode", eng, "system",
               basis={"kind": "execution"})
    log(f"engines: llm={eng['llm']['mode']} tts-local={eng['tts']['local']} "
        f"tts-remote={eng['tts']['remote']} stt={eng['stt']['mode']}")

    honesty = ctx.honesty()
    ctx.append("launch", "launch:honesty", honesty, "system",
               basis={"kind": "execution"})

    ui_dir = os.path.join(root, "app", "ui")
    srv = None if args.no_serve else serve(ctx, args.port, ui_dir)
    actual_port = srv.server_address[1] if srv else args.port

    steward = None
    if not args.no_steward:
        steward = Steward(ctx)
        steward.start()
        log("steward: started (configurable interval, default 15s)")

    report = {"ok": True, "port": actual_port, "root": root,
              "runtime": ctx.runtime, "engines": eng,
              "components": len(ctx.registry.components),
              "ledger": ctx.ledger.stats(), "packs": packs["loaded"],
              "steward": bool(steward), "bootMs": ctx.boot_at}
    ctx.append("launch", "launch:report", report, "system",
               basis={"kind": "execution"})

    os.makedirs(os.path.join(root, "evidence", "launch"), exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    log_path = os.path.join(root, "evidence", "launch", f"launch-{ts}.log")
    log_lines.append(banner(honesty, actual_port))
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")
    with open(os.path.join(ctx.runtime, "last-launch.json"), "w") as f:
        json.dump({**report, "log": log_path}, f, indent=2)

    print(banner(honesty, actual_port), flush=True)
    print(f"launch log: {log_path}", flush=True)

    if args.open and srv:
        try:
            import webbrowser
            webbrowser.open(f"http://127.0.0.1:{actual_port}")
        except Exception:
            pass
    if srv:
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            if steward:
                steward.stop()
    return report


if __name__ == "__main__":
    main()
