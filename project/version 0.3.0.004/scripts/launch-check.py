"""Launch-hygiene enactment — real processes, real ports.

Checks:
1. clean launch — boots, gate passes, last-launch.json ok:true
2. launch hygiene — a second launch on the same port REFUSES
   (LAUNCH REFUSED, exit!=0, ok:false) — never ok:true while a prior
   instance owns the port
3. close-terminate — with the watchdog on, closing the last window
   terminates the program

Writes evidence/launch/launch-check.json
"""
import json, os, shutil, subprocess, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "evidence", "launch")
PORT = 9778

def honest(p=PORT, t=3):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{p}/api/honesty",
                                    timeout=t) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None

def wait_up(p=PORT, s=120):
    t0 = time.time()
    while time.time() - t0 < s:
        d = honest(p)
        if d:
            return d
        time.sleep(0.5)
    return None

def main():
    os.makedirs(EVID, exist_ok=True)
    rt = os.path.join(ROOT, "runtime", "launchcheck")
    shutil.rmtree(rt, ignore_errors=True)
    os.makedirs(rt, exist_ok=True)
    out = {"checks": []}

    # 1. clean launch
    p1 = subprocess.Popen([sys.executable, "-m", "app", "--port", str(PORT),
                           "--runtime", rt, "--no-watchdog"],
                          cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True)
    try:
        d = wait_up()
        ll = {}
        llp = os.path.join(rt, "last-launch.json")
        if os.path.exists(llp):
            ll = json.load(open(llp))
        out["checks"].append({"name": "clean launch",
            "pass": bool(d) and ll.get("ok") is True,
            "detail": {"honesty": bool(d), "lastLaunchOk": ll.get("ok"),
                       "gate": ll.get("gate", {}).get("passed"),
                       "timeToGateMs": ll.get("gate", {}).get("timeToGateMs")}})

        # 2. second launch refuses (launch hygiene)
        p2 = subprocess.Popen([sys.executable, "-m", "app", "--port",
                               str(PORT), "--runtime",
                               os.path.join(ROOT, "runtime", "second"),
                               "--no-watchdog"],
                              cwd=ROOT, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True)
        try:
            txt = p2.communicate(timeout=60)[0]
            refused = "LAUNCH REFUSED" in (txt or "")
            out["checks"].append({"name": "second launch refused",
                "pass": refused and p2.returncode != 0,
                "detail": {"exit": p2.returncode,
                           "refusedLine": refused,
                           "out": (txt or "")[-400:]}})
        finally:
            if p2.poll() is None:
                p2.terminate()
    finally:
        p1.terminate()
        try: p1.wait(timeout=15)
        except Exception: p1.kill()

    # 3. close-terminate (watchdog instance)
    rt3 = os.path.join(ROOT, "runtime", "closeterm")
    shutil.rmtree(rt3, ignore_errors=True)
    os.makedirs(rt3, exist_ok=True)
    p3 = subprocess.Popen([sys.executable, "-m", "app", "--port",
                           str(PORT+1), "--runtime", rt3],
                          cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True)
    try:
        if not wait_up(PORT+1):
            out["checks"].append({"name": "close-terminate", "pass": False,
                "detail": "watchdog instance never came up"})
        else:
            conn = urllib.request.urlopen(
                f"http://127.0.0.1:{PORT+1}/api/events", timeout=10)
            conn.read(8); conn.close()
            t0 = time.time(); exited = False
            while time.time() - t0 < 70:
                if p3.poll() is not None:
                    exited = True; break
                time.sleep(1)
            out["checks"].append({"name": "close-terminate",
                "pass": exited,
                "detail": {"exitCode": p3.poll(),
                           "waitedS": int(time.time()-t0)}})
    finally:
        if p3.poll() is None:
            p3.terminate()

    out["pass"] = bool(out["checks"]) and all(c["pass"] for c in out["checks"])
    path = os.path.join(EVID, "launch-check.json")
    json.dump(out, open(path, "w"), indent=2)
    print(json.dumps(out, indent=2)[:1500])
    print("launch-check:", "PASS" if out["pass"] else "FAIL")

if __name__ == "__main__":
    main()
