"""Vantage boot — two-part execution (C-TwoPartExecution) + launch hygiene.
Part 1 (exactly the readiness gate's scope): runtime dirs + transient
boundary, ledger + launch partition mount, seed packs, component registry,
engine probes — then the Interactive Readiness Gate runs and records its
pass time.
Part 2 (everything after the gate): HTTP surface, SSE window watchdog,
background steward, browser open.
Launch hygiene (standing criterion):
- the port is probed for a live Vantage instance BEFORE binding; a second
  launch prints LAUNCH REFUSED, writes the failure to the launch log and
  last-launch.json, and exits non-zero — never ok:true while a prior
  instance owns the port
- the HTTP socket binds exclusively (allow_reuse_address off; on Windows
  that is SO_EXCLUSIVEADDRUSE) so no silent double-bind is possible
- once a window has connected, closing the last one stops the program —
  no orphaned process (S-close-terminate); --no-watchdog for headless runs
"""
from __future__ import annotations
import argparse
import json
import os
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import host, api, gate as gate_mod  # noqa: E402
def log_line(logf, msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    logf.write(line + "\n")
    logf.flush()
def probe_instance(port: int) -> bool:
    """Is a live Vantage already serving on this port?"""
    try:
        with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/api/honesty", timeout=2) as r:
            d = json.loads(r.read().decode())
            return isinstance(d, dict) and "llm" in d
    except Exception:
        return False
def write_last_launch(runtime, rec):
    with open(os.path.join(runtime, "last-launch.json"), "w",
              encoding="utf-8") as f:
        json.dump(rec, f, indent=2)
def main():
    ap = argparse.ArgumentParser(prog="vantage")
    ap.add_argument("--port", type=int, default=9770)
    ap.add_argument("--runtime", default=None)
    ap.add_argument("--no-serve", action="store_true")
    ap.add_argument("--no-steward", action="store_true")
    ap.add_argument("--no-watchdog", action="store_true")
    ap.add_argument("--open", action="store_true")
    args = ap.parse_args()
    t0 = time.time()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    runtime = args.runtime or os.path.join(root, "runtime")
    os.makedirs(runtime, exist_ok=True)
    os.makedirs(os.path.join(root, "evidence", "launch"), exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    logpath = os.path.join(root, "evidence", "launch",
                           f"launch-{stamp}.log")
    logf = open(logpath, "w", encoding="utf-8")
    server_out = open(os.path.join(root, "launch-server.out"), "w",
                      encoding="utf-8")
    _orig_out = sys.stdout
    class Tee:
        def write(self, s):
            _orig_out.write(s)
            server_out.write(s)
            server_out.flush()
        def flush(self):
            _orig_out.flush()
    sys.stdout = Tee()
    log_line(logf, f"vantage 0.3.0.004 boot — port {args.port}, "
                   f"runtime {runtime}")
    # -- launch hygiene: never claim success while a prior instance owns
    #    the port -------------------------------------------------------
    if not args.no_serve and probe_instance(args.port):
        log_line(logf, "LAUNCH REFUSED — a live Vantage instance already "
                       f"owns port {args.port}")
        write_last_launch(runtime, {
            "ok": False, "reason": "port-owned",
            "detail": f"prior instance owns :{args.port}",
            "at": time.time()})
        logf.close()
        sys.exit(3)
    # ==================== PART 1 (gate scope) ==========================
    ctx = host.Ctx(runtime)
    log_line(logf, f"transient boundary: {ctx.transient} "
                   f"(reset={ctx.transient_reset})")
    log_line(logf, f"launch partition mounted: {ctx.partition_count} rows; "
                   f"journal replay: {ctx.journal_count} rows")
    seed = ctx.seed_packs(os.path.join(root, "seed-packs"))
    log_line(logf, f"seed packs: {seed}")
    # C-LaunchPartition: on first boot the essential slice is materialized
    # in schema-dependency order, then mounted before the gate tests it
    if ctx.partition_count == 0:
        preds = ["persona:profile", "ui:shell-theme",
                 "chat:response-depth", "seed:loaded", "chat:topic"]
        n = ctx.ledger.write_partition(ctx.partition_path, preds)
        ctx.partition_count = ctx.ledger.mount_partition(ctx.partition_path)
        log_line(logf, f"launch partition initialized: {n} rows written, "
                       f"{ctx.partition_count} mounted")
    manifest = ctx.tools.manifest()
    log_line(logf, f"components: {manifest}")
    eng = ctx.engines.honesty()
    log_line(logf, f"engines: llm={eng['llm']['mode']} "
                   f"tts={eng['tts']['mode']}({len(eng['tts']['voices'])}v) "
                   f"stt={eng['stt']['mode']}")
    ctx.gate = gate_mod.Gate(ctx)
    grec = ctx.gate.run(t0)
    log_line(logf, f"readiness gate: {'PASS' if grec['passed'] else 'FAIL'} "
                   f"in {grec['timeToGateMs']}ms — {grec['checks'].keys()}")
    if not grec["passed"]:
        write_last_launch(runtime, {"ok": False, "reason": "gate-failed",
                                    "gate": grec, "at": time.time()})
        logf.close()
        sys.exit(4)
    # ==================== PART 2 (after the gate) ======================
    honesty = eng
    banner = (f"honesty: llm={honesty['llm']['mode']} | "
              f"tts={honesty['tts']['mode']} | declared absences: "
              f"{', '.join(honesty['declaredAbsences'][:3])}…")
    ctx.ledger.say("launch", "launch:honesty",
                   {"banner": banner, "engines": honesty["llm"]["mode"]},
                   claimant="system", certainty=1.0,
                   basis={"kind": "config"})
    log_line(logf, banner)
    if not args.no_steward:
        ctx.steward.start()
        log_line(logf, f"steward running every {ctx.steward.interval}s")
    if args.no_serve:
        write_last_launch(runtime, {
            "ok": True, "served": False, "gate": grec,
            "rows": len(ctx.ledger.rows), "at": time.time()})
        log_line(logf, "--no-serve: boot complete")
        logf.close()
        return
    try:
        srv = api.VantageServer(("127.0.0.1", args.port), api.Handler, ctx,
                                watchdog=not args.no_watchdog)
    except OSError as e:
        log_line(logf, f"LAUNCH REFUSED — bind failed: {e}")
        write_last_launch(runtime, {"ok": False, "reason": "bind-failed",
                                    "error": repr(e), "at": time.time()})
        logf.close()
        sys.exit(3)
    ctx.bus.listeners.append(srv.fanout)
    write_last_launch(runtime, {
        "ok": True, "port": args.port, "gate": grec,
        "rows": len(ctx.ledger.rows), "pid": os.getpid(),
        "url": f"http://127.0.0.1:{args.port}", "at": time.time()})
    log_line(logf, f"serving http://127.0.0.1:{args.port} "
                   f"(watchdog={'on' if not args.no_watchdog else 'off'})")
    log_line(logf, f"launch log: {logpath}")
    if args.open:
        threading.Timer(1.0, lambda: webbrowser.open(
            f"http://127.0.0.1:{args.port}")).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        # checkpoint the launch partition at clean shutdown
        preds = ["persona:profile", "ui:shell-theme", "chat:response-depth",
                 "roster:active", "seed:loaded", "chat:topic"]
        n = ctx.ledger.write_partition(ctx.partition_path, preds)
        ctx.steward.stop()
        log_line(logf, f"shutdown — partition checkpointed ({n} rows)")
        logf.close()
if __name__ == "__main__":
    main()
