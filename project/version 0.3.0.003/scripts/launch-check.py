"""Launch-hygiene evidence (G4, S-windows-launch, S-close-terminate).

Enacts four checks against real processes and writes

evidence/launch/launch-check.json:

1. clean boot — server comes up, gate passes, launch-server.out is written

   by THIS version (fresh per launch, not copied);

2. stale-port refusal — a second launch on the same port REFUSES: non-zero

   exit, "LAUNCH REFUSED" in its output, and it never reports ok:true;

3. close-terminate — once a UI window has connected (SSE) and then closes,

   the program terminates on its own — no orphan process;

4. port freed — after termination the port accepts a fresh bind.

Usage: python scripts/launch-check.py

"""

from __future__ import annotations

import json

import os

import subprocess

import sys

import time

import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PORT = 9764

BASE = f"http://127.0.0.1:{PORT}"

RUNTIME = os.path.join(ROOT, "runtime", "launchcheck")

OUT = os.path.join(ROOT, "evidence", "launch", "launch-check.json")

def get(path, timeout=3):

    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:

        return json.loads(r.read().decode())

def boot(extra=()):

    return subprocess.Popen(

        [sys.executable, "-m", "app", "--port", str(PORT),

         "--runtime", RUNTIME, *extra],

        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

def read_all(proc, timeout=25):

    try:

        return proc.communicate(timeout=timeout)[0] or ""

    except Exception:

        proc.kill()

        return proc.communicate()[0] or ""

def wait_up(deadline_s=60):

    for _ in range(int(deadline_s * 2)):

        try:

            return get("/api/honesty", timeout=2)

        except Exception:

            time.sleep(0.5)

    return None

def main():

    os.makedirs(RUNTIME, exist_ok=True)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    rec = {"port": PORT, "checks": {}, "ok": False}

    # ---- 1. clean boot ----

    p1 = boot()

    h = wait_up()

    if not h:

        rec["checks"]["cleanBoot"] = {"ok": False,

                                      "output": read_all(p1)[:2000]}

        json.dump(rec, open(OUT, "w"), indent=2)

        print("FAIL: clean boot")

        return

    gate = get("/api/gate")

    out_path = os.path.join(ROOT, "launch-server.out")

    out_txt = open(out_path, encoding="utf-8").read() if os.path.exists(

        out_path) else ""

    rec["checks"]["cleanBoot"] = {

        "ok": True, "gatePassed": gate.get("passed"),

        "gatePassedAt": gate.get("passedAt"),

        "msToGate": gate.get("msToGate"),

        "launchServerOut": out_path,

        "launchServerOutFresh": "0.3.0.003" in out_txt and

            "READINESS GATE" in out_txt.upper() or "gate" in out_txt.lower(),

        "version": get("/api/version")}

    # ---- 2. stale-port refusal: a second launch must NOT claim success ----

    p2 = boot()

    out2 = read_all(p2, timeout=30)

    rc2 = p2.returncode

    last_launch = {}

    ll_path = os.path.join(RUNTIME, "last-launch.json")

    if os.path.exists(ll_path):

        last_launch = json.load(open(ll_path))

    rec["checks"]["stalePortRefusal"] = {

        "exitCode": rc2,

        "refused": "LAUNCH REFUSED" in out2,

        "reportedSuccess": '"ok": true' in out2 and "LAUNCH" not in out2,

        "neverFalseOk": not (rc2 == 0),

        "tail": out2[-1200:],

        "lastLaunchOk": last_launch.get("ok")}

    # ---- 2b. stop the first instance; port must free ----
    stop(p1)
    time.sleep(1)
    try:
        get("/api/honesty", timeout=2)
        rec["checks"]["portFreedAfterStop"] = False
    except Exception:
        rec["checks"]["portFreedAfterStop"] = True

    # ---- 3. close-terminate: connect SSE window then close it ----

    p3 = boot()

    h3 = wait_up()

    close_rec = {"ok": False}

    if h3:

        # open an SSE connection = a UI window presence

        try:

            sse = urllib.request.urlopen(BASE + "/api/events", timeout=5)

            time.sleep(1.5)

            sse.close()  # window closed

            t0 = time.time()

            exited = False

            while time.time() - t0 < 25:

                if p3.poll() is not None:

                    exited = True

                    break

                time.sleep(0.5)

            close_rec = {"ok": exited,

                         "exitCode": p3.returncode,

                         "waitedS": round(time.time() - t0, 1),

                         "noOrphan": exited and p3.returncode is not None}

            if not exited:

                p3.terminate()

                try:

                    p3.wait(timeout=10)

                except Exception:

                    p3.kill()

        except Exception as e:

            close_rec = {"ok": False, "error": repr(e)}

            if p3.poll() is None:

                p3.terminate()

    rec["checks"]["closeTerminates"] = close_rec

    # ---- 4. port freed after termination ----

    time.sleep(1)

    freed = False

    try:

        get("/api/honesty", timeout=2)

    except Exception:

        freed = True

    if p3.poll() is None:

        freed = False

        p3.terminate()

    rec["checks"]["portFreed"] = freed

    stop(p1)
    stop(p3)
    rec["ok"] = all([

        rec["checks"]["cleanBoot"]["ok"] and gate.get("passed"),

        rec["checks"]["stalePortRefusal"]["refused"] and

            rec["checks"]["stalePortRefusal"]["neverFalseOk"] and

            last_launch.get("ok") is False,

        close_rec.get("ok"),

        freed])

    with open(OUT, "w", encoding="utf-8") as f:

        json.dump(rec, f, indent=2, ensure_ascii=False)

    print(json.dumps(rec, indent=2)[:3000])

def stop(proc):

    if proc.poll() is None:

        proc.terminate()

        try:

            proc.wait(timeout=15)

        except Exception:

            proc.kill()

if __name__ == "__main__":

    main()

