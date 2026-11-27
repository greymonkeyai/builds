"""Quorum boot — two-part execution (C-TwoPartExecution).

Part 1: mount launch partition + journal → first-run seeding → readiness
        gate (pass time recorded — time-to-gate is a named criterion).
Part 2: serve the surface + start the steward + watchdog.

Launch hygiene (S-4): port probed before bind; exclusive bind; a stale
instance owning the port fails the launch honestly; launcher close
terminates the process (parent watchdog).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from quorum import host, gate, server, rows, artifacts, fleet, personas  # noqa


def first_run_seed(h: host.Host):
    """Shipped corpus + named preloads + predicate registry + launch partition
    (materialization ordered by modular schema dependencies)."""
    part = []
    def row(subject, predicate, value, claimant="seed:corpus", certainty=0.65):
        a = rows.make(subject, predicate, value, claimant=claimant,
                      certainty=certainty, basis="seed")
        part.append(a.to_row())
        return a.to_row()

    row("sys", "sys:predicate", sorted({
        "chat:input", "chat:gate", "need:tool-request", "need:list",
        "need:response", "need:request", "eval:fulfillment",
        "tool:exists", "tool:definition", "tool:candidate",
        "tool:endorse", "tool:discredit", "persona:exists",
        "persona:portrait", "persona:set-voice", "persona:imitation-mark",
        "rel:held-confidence", "roster:active", "roster:rank",
        "grant:witnessed", "gate:passed", "steward:pass", "floor:played",
        "source:wikipedia", "source:search", "source:peer",
        "email:received", "exchange:imported", "exchange:exported",
        "workshop:persona", "workshop:entry", "workshop:adopted",
        "workshop:republished", "exchange:claim-review",
        "fleet:discovery", "fleet:invite", "fleet:role", "fleet:member",
        "fleet:install", "fleet:map", "peer:sever",
        "peer:credential-surrender", "seed:courier",
        "settings:theme", "settings:speech", "settings:density",
        "inference:snapshot", "inference:commit", "compare:result",
        "need:focus", "proactive:offer", "email:commentary",
        "ethics:admonishment", "persona:imitation-mark",
    }))
    row("settings", "settings:theme", "light", claimant="principal",
        certainty=1.0)
    row("settings", "settings:density", "comfortable", claimant="principal",
        certainty=1.0)
    row("settings", "settings:speech", "on", claimant="principal",
        certainty=1.0)
    row("config", "config:preloads", list(h.preloads().keys()))
    row("config", "config:voice-families",
        artifacts.VOICE_FAMILIES)

    # shipped personas — distinct enough that the same prompt elicits
    # noticeably different responses (S-distinct-preloadeds)
    shipped = [
        {"name": "Verity", "register": "scholarly",
         "traits": ["precise", "cites sources", "measured"]},
        {"name": "Puck", "register": "playful",
         "traits": ["witty", "irreverent", "quick"]},
        {"name": "Marge", "register": "casual",
         "traits": ["warm", "practical", "homespun"]},
        {"name": "Nix", "register": "terse",
         "traits": ["minimal", "direct", "quiet"]},
    ]
    for s in shipped:
        p = h.personas.mint(s["name"], register=s["register"],
                            traits=s["traits"], claimant="seed:corpus")
        part += [r.to_row() for r in h.book.rows
                 if r.subject == p["id"]]
    if h.personas.order:
        h.personas.select(h.personas.order[0])
    h.seed_launch_partition(part)
    return {"seeded": len(part), "personas": len(shipped)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9790)
    ap.add_argument("--runtime", default=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "runtime"))
    ap.add_argument("--no-watchdog", action="store_true")
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--seed-media", default="")
    args = ap.parse_args()

    # launch log tee — console output is evidence (launch-server.out fresh
    # each boot + timestamped file under evidence/launch/)
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _evdir = os.path.join(_root, "evidence", "launch")
    try:
        os.makedirs(_evdir, exist_ok=True)
        import datetime as _dt
        _ts = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        _logs = [open(os.path.join(_root, "launch-server.out"), "w",
                      encoding="utf-8", buffering=1),
                 open(os.path.join(_evdir, f"launch-{_ts}.log"), "a",
                      encoding="utf-8", buffering=1)]

        class _Tee:
            def __init__(s, orig): s.orig = orig
            def write(s, t):
                s.orig.write(t)
                for f in _logs:
                    try:
                        f.write(t)
                    except Exception:
                        pass
            def flush(s):
                s.orig.flush()
                for f in _logs:
                    try:
                        f.flush()
                    except Exception:
                        pass
        sys.stdout = _Tee(sys.stdout)
        sys.stderr = _Tee(sys.stderr)
    except Exception:
        pass

    report = {"app": "quorum", "version": "0.3.0.005",
              "started": rows.now_ms(), "runtime": args.runtime,
              "port": args.port, "ok": None}

    h = host.Host(args.runtime, args.port)

    # ---- PART 1 — mount + gate ----------------------------------------------
    mounted = h.mount()
    report["mounted"] = mounted
    if not h.book.rows:
        report["first_run"] = first_run_seed(h)
        mounted = h.mount()                     # remount the partition view
        report["mounted_after_seed"] = mounted

    g = gate.Gate(h)
    g.booted_at = report["started"]
    gate_out = g.run()
    report["gate"] = gate_out
    print(f"[quorum] partition={mounted['partition']} "
          f"journal={mounted['journal']} "
          f"gate={'PASS' if gate_out['passed'] else 'FAIL'} "
          f"in {gate_out.get('timeToGateMs')}ms", flush=True)

    # ---- PART 2 — surface + steward ------------------------------------------
    srv = server.serve(h, report, open_browser=not args.no_browser)
    report_path = os.path.join(h.runtime, "last-launch.json")
    if srv is None:
        report["ok"] = False
        os.makedirs(h.runtime, exist_ok=True)
        json.dump(report, open(report_path, "w"), indent=2)
        print(f"[quorum] LAUNCH REFUSED — {report['error']}", flush=True)
        sys.exit(2)

    if args.seed_media:
        h.seed = fleet.Seed(h.book, args.seed_media)
        h.seed.courier({"event": "seed-boot", "port": args.port,
                        "note": "running in place from removable media"})

    h.steward.start()
    report["ok"] = True
    json.dump(report, open(report_path, "w"), indent=2)
    print(f"[quorum] serving http://127.0.0.1:{args.port}/ "
          f"(runtime {args.runtime})", flush=True)

    if not args.no_watchdog:
        def watch():
            while True:
                time.sleep(3)
                if not server.parent_alive():
                    print("[quorum] launcher closed — terminating", flush=True)
                    os._exit(0)
        threading.Thread(target=watch, daemon=True).start()

    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
