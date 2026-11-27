#!/usr/bin/env python
"""launch-check — S-4 launch hygiene enactment for Quorum 0.3.0.005.

Four legs, all must pass:
1. clean bind on a free port (probe → exclusive bind → ok:true)
2. second launch while the port is owned → honest refusal (ok:false, no
   success-claim while a prior instance owns the port)
3. exclusive bind — a raw socket CANNOT steal the bound port
4. close-terminates — terminating the process frees the port
"""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EVID = os.path.join(ROOT, "evidence", "launch")
os.makedirs(EVID, exist_ok=True)
PORT = 9794
RUNTIME = os.path.join(ROOT, "runtime-check")


def get(path, timeout=3):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}",
                                timeout=timeout) as r:
        return json.loads(r.read())


def boot(port=PORT, runtime=RUNTIME):
    return subprocess.Popen(
        [sys.executable, "-m", "quorum", "--port", str(port),
         "--runtime", runtime, "--no-watchdog", "--no-browser"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def wait_up(port=PORT, deadline=60):
    t0 = time.time()
    while time.time() - t0 < deadline:
        try:
            return get("/api/honesty")
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("instance did not come up")


def main():
    results = {"legs": [], "port": PORT}
    def leg(name, ok, detail=""):
        results["legs"].append({"leg": name, "pass": bool(ok),
                                "detail": detail})
        print(f"  [{ 'PASS' if ok else 'FAIL'}] {name}: {detail}")

    # leg 1 — clean bind
    p1 = boot()
    try:
        h = wait_up()
        gate = get("/api/gate")
        rep = json.load(open(os.path.join(RUNTIME, "last-launch.json")))
        leg("clean-bind", h.get("app") == "quorum-0.3.0.005" and rep.get("ok"),
            f"gate {gate.get('passed')} ttg {gate.get('timeToGateMs')}ms")

        # leg 2 — stale-owner refusal
        p2 = boot()
        time.sleep(4)
        code = p2.poll()
        rep2 = json.load(open(os.path.join(RUNTIME, "last-launch.json"))) \
            if os.path.exists(os.path.join(RUNTIME, "last-launch.json")) else {}
        refused = code == 2 or (rep2.get("ok") is False)
        leg("stale-owner-refusal", refused and p1.poll() is None,
            f"second instance exit={code}; first still alive={p1.poll() is None}")
        if p2.poll() is None:
            p2.terminate()

        # leg 3 — exclusive bind
        stolen = False
        try:
            s = socket.socket()
            s.bind(("127.0.0.1", PORT))
            stolen = True
            s.close()
        except OSError:
            pass
        leg("exclusive-bind", not stolen,
            "raw socket could not steal the bound port" if not stolen
            else "port was stealable")

        # leg 4 — close-terminates
        p1.terminate()
        try:
            p1.wait(timeout=10)
        except Exception:
            p1.kill()
        time.sleep(1)
        free = False
        try:
            socket.create_connection(("127.0.0.1", PORT), timeout=1).close()
        except Exception:
            free = True
        leg("close-terminates", free and p1.poll() is not None,
            f"process ended={p1.poll() is not None}; port free={free}")
    finally:
        if p1.poll() is None:
            p1.terminate()

    results["pass"] = all(l["pass"] for l in results["legs"])
    out = os.path.join(EVID, "launch-check.json")
    json.dump(results, open(out, "w"), indent=2)
    print("launch-check:", "PASS" if results["pass"] else "FAIL",
          "->", out)
    return 0 if results["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
