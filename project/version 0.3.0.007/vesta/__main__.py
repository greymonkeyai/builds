"""vesta entry — two-part execution (C-TwoPartExecution).

Part 1: launch partition mounted (C-LaunchPartition), engines probed,
readiness gate tested and its pass timestamp recorded (C-ReadinessGate).
Part 2: everything after the gate — shipped personas, source seed import
+ admission sweep, stage, steward, operator surface.

Launch hygiene: probe-before-bind; exclusive bind; refuse-while-owned
(never claim success while a prior instance owns the port); close
terminates.  --bare boots an empty system (no modules mounted, no gate):
the phase-0 harness runs its all-red baseline against this.
"""

import argparse
import json
import os
import socket
import sys
import time

from . import APP, VERSION


def probe(port, timeout=0.8):
    """Return the owning instance's health dict if the port is live."""
    try:
        s = socket.create_connection(("127.0.0.1", port), timeout)
        req = b"GET /api/health HTTP/1.0\r\nHost: 127.0.0.1\r\n\r\n"
        s.sendall(req)
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
        s.close()
        body = data.split(b"\r\n\r\n", 1)[-1]
        return json.loads(body.decode("utf-8", "replace"))
    except Exception:
        return None


def main(argv=None):
    ap = argparse.ArgumentParser(prog="vesta")
    ap.add_argument("--port", type=int, default=int(os.environ.get("VESTA_PORT", "9810")))
    ap.add_argument("--peer-port", type=int, default=int(os.environ.get("VESTA_PEER_PORT", "7872")))
    ap.add_argument("--data", default=os.environ.get("VESTA_DATA", "runtime"))
    ap.add_argument("--bare", action="store_true", help="empty system — no modules mounted (phase-0 baseline target)")
    ap.add_argument("--sabotage", default="", help="comma list: empty-store, stub-engines, stub-endpoints (phase-2 evidence)")
    ap.add_argument("--seed", action="store_true", help="run in place from removable media (courier log on the medium)")
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args(argv)

    started = time.time()
    owner = probe(args.port)
    if owner and owner.get("app") == APP:
        print(f"LAUNCH REFUSED — a vesta instance ({owner.get('node')}) already owns port {args.port}")
        return 2

    if args.bare:
        from .shell import run_bare
        return run_bare(args.port, args.data)

    os.makedirs(args.data, exist_ok=True)
    os.environ["VESTA_DATA"] = os.path.abspath(args.data)

    from .host import Host
    host = Host(args.data, port=args.port, peer_port=args.peer_port,
                seed=args.seed, sabotage=set(filter(None, args.sabotage.split(","))))

    # Part 1 — partition + engines + readiness gate.
    host.part1()
    gate = host.gate_result
    if not gate.get("passed"):
        print(f"READINESS GATE FAILED: {json.dumps(gate.get('conditions'))}")
        host.shutdown()
        return 3
    print(f"gate passed at {gate['passedAt']} (time-to-gate {gate['timeToGateMs']}ms)")

    # Part 2 — personas, sources, stage, steward, surface.
    host.part2()

    if not args.no_browser:
        try:
            import webbrowser
            webbrowser.open(f"http://127.0.0.1:{args.port}/")
        except Exception:
            pass
    print(f"vesta {VERSION} serving http://127.0.0.1:{args.port}/ node={host.node_id} seed={args.seed}")
    try:
        host.serve()
    except KeyboardInterrupt:
        pass
    finally:
        host.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
