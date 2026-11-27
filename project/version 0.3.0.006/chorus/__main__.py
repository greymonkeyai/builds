"""chorus — launch entry. Two-part execution (C-TwoPartExecution):
Part 1 mounts the launch partition + probes engines + runs the readiness
gate; Part 2 is everything after (surfaces, steward, fleet).
Launch hygiene (S-4): port probed before bind; a live instance on the
port refuses the launch; exclusive bind; close-terminates.
"""
import argparse
import json
import os
import sys
import threading
import time
import webbrowser
from .host import Host
from . import server, seedmedia
def main():
    ap = argparse.ArgumentParser(prog="chorus")
    ap.add_argument("--port", type=int, default=9790)
    ap.add_argument("--runtime", default=None,
                    help="runtime dir (default <app>/runtime)")
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--seed", action="store_true",
                    help="force seed-media behavior (run in place from media)")
    ap.add_argument("--node", default=None, help="node id override")
    args = ap.parse_args()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    runtime = args.runtime or os.path.join(root, "runtime")
    os.makedirs(runtime, exist_ok=True)
    t0 = time.time()

    def trace(msg):
        with open(os.path.join(runtime, "boot-trace.log"), "a",
                  encoding="utf-8") as f:
            f.write(f"{time.time()-t0:.2f} {msg}\n")
    trace("argv parsed")
    # --- launch hygiene: probe before bind ---
    existing = server.probe_instance(args.port)
    if existing:
        print(f"LAUNCH REFUSED — a chorus instance ({existing.get('node')}) "
              f"already owns port {args.port}")
        sys.exit(2)
    if server.port_in_use(args.port):
        print(f"LAUNCH REFUSED — port {args.port} is bound by a non-chorus "
              "process")
        sys.exit(2)
    host = Host(runtime, root, node_id=args.node)
    trace("host constructed")
    host.boot_meta["bootStartedAt"] = t0
    host.boot_meta["port"] = args.port
    # --- Part 1: mount + gate ---
    meta = host.part1_mount()
    trace("part1 mounted")
    on_seed = args.seed or seedmedia.is_removable(root)
    if on_seed:
        host.boot_meta["seed"] = True
        seedmedia.boot_seed(host)
    gate = host.readiness_gate()
    gate_ms = int((time.time() - t0) * 1000)
    gate["timeToGateMs"] = gate_ms
    with open(os.path.join(runtime, "gate.json"), "w", encoding="utf-8") as f:
        json.dump(gate, f, indent=1)
    status = "PASS" if gate["ok"] else "FAIL"
    print(f"partition={meta['partitionRows']} journal={meta['mountedRows']} "
          f"gate={status} in {gate_ms}ms llm={host.llm.mode} "
          f"voices={len(host.voice_pool)} seed={bool(on_seed)}")
    # --- Part 2: everything after the gate. Bind the surface first so
    # launch hygiene holds during heavyweight part-2 work (source
    # admission probing on cold boot). ---
    httpd, peerd = server.serve(host, args.port,
                                os.path.join(root, "chorus", "ui"))
    trace("surface bound")
    threading.Thread(target=host.part2_start, daemon=True).start()
    last = {"ok": gate["ok"], "port": args.port, "gate": gate,
            "gateMs": gate_ms, "llm": host.llm.mode,
            "voices": len(host.voice_pool), "node": host.node_id,
            "network": host.network_id, "peerPort":
            int(os.environ.get("CHORUS_PEER_PORT", "7871")),
            "seed": bool(on_seed)}
    with open(os.path.join(runtime, "last-launch.json"), "w",
              encoding="utf-8") as f:
        json.dump(last, f, indent=1)
    print(f"chorus serving on http://127.0.0.1:{args.port} "
          f"(peer :{last['peerPort']}) node={host.node_id}")
    if not args.no_browser:
        try:
            webbrowser.open(f"http://127.0.0.1:{args.port}")
        except Exception:
            pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if host.steward:
            host.steward.stop()
        host.speech_floor.stop()
if __name__ == "__main__":
    main()
