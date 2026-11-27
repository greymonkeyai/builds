#!/usr/bin/env python3
"""launch-check.py — 4-leg clean-launch evidence:
  1. no stale instance owns the port (launch hygiene — no success-claim
     while a prior instance owns the port)
  2. fresh launch answers /api/health with part2 complete
  3. readiness gate passed, timestamp recorded (time-to-gate)
  4. close-terminates — the process ends on terminate
Writes evidence/launch/launch-check.json.
"""

import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 9537
BASE = f"http://127.0.0.1:{PORT}"
OUT = os.path.join(ROOT, "evidence", "launch", "launch-check.json")


def healthy():
    try:
        with urllib.request.urlopen(BASE + "/api/health", timeout=2) as r:
            return json.loads(r.read())
    except Exception:
        return None


def main():
    legs = []
    t0 = time.time()

    # leg 1 — port hygiene
    prior = healthy()
    if prior:
        legs.append({"leg": "port-hygiene", "pass": False,
                     "detail": f"prior instance owns :{PORT} — refusing to "
                               f"claim success while port is held"})
        _emit(legs, t0)
        sys.exit(1)
    legs.append({"leg": "port-hygiene", "pass": True,
                 "detail": f":{PORT} free"})

    # leg 2 — fresh launch + health
    data_dir = os.path.join(ROOT, "runtime", "launch-check")
    os.makedirs(data_dir, exist_ok=True)
    log_path = os.path.join(ROOT, "evidence", "launch", "launch.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    proc = subprocess.Popen(
        [sys.executable, "-m", "vesta", "--port", str(PORT)],
        cwd=ROOT, env=dict(os.environ, VESTA_DATA=data_dir),
        stdout=open(log_path, "w"), stderr=subprocess.STDOUT)
    deadline, h = time.time() + 30, None
    while time.time() < deadline:
        h = healthy()
        if h:
            break
        time.sleep(0.4)
    legs.append({"leg": "fresh-launch-health", "pass": bool(h) and
                 h.get("part2") is True,
                 "detail": json.dumps(h)[:300] if h else "no /api/health"})

    # leg 3 — readiness gate timestamp (time-to-gate)
    gate_path = os.path.join(data_dir, "gate.json")
    gate = json.load(open(gate_path)) if os.path.exists(gate_path) else None
    t_gate = gate.get("passedAt") if gate else None
    legs.append({"leg": "readiness-gate-passed", "pass": bool(t_gate),
                 "detail": f"gate passedAt={t_gate} "
                           f"(seconds={gate.get('seconds') if gate else None})",
                 "timeToGateSeconds": gate.get("seconds") if gate else None})

    # leg 4 — close-terminates
    proc.terminate()
    try:
        proc.wait(timeout=8)
        term = proc.returncode is not None
    except Exception:
        proc.kill()
        term = False
    legs.append({"leg": "close-terminates", "pass": term,
                 "detail": f"terminated rc={proc.returncode}"})

    _emit(legs, t0)
    sys.exit(0 if all(l["pass"] for l in legs) else 1)


def _emit(legs, t0):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    doc = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "seconds": round(time.time() - t0, 1),
        "legs": legs,
        "allPass": all(l["pass"] for l in legs),
        "timeToGateSeconds": next(
            (l.get("timeToGateSeconds") for l in legs
             if l.get("timeToGateSeconds") is not None), None),
    }
    with open(OUT, "w") as f:
        json.dump(doc, f, indent=2)
    print(json.dumps(doc, indent=1))


if __name__ == "__main__":
    main()
