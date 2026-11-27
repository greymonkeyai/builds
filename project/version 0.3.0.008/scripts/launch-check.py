"""launch-check — clean-launch evidence legs (direction-008):
  1. cold launch on a clean data dir reaches readiness gate (seconds)
  2. relaunch recovery — second boot on same data dir preserves state
  3. USB leg — instance launched executing from removable media (H:)
  4. close-terminates — process exits on shutdown signal
  5. launch hygiene — second bind on owned port refused
Writes evidence/launch/launch-check.json
"""
import ctypes
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNTIME = os.path.join(ROOT, "runtime", "launch-check")
LOG = os.path.join(RUNTIME, "launch.log")
EVID = os.path.join(ROOT, "evidence", "launch")
PORT = 9539
def health(port, timeout=3):
    try:
        with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/api/health",
                timeout=timeout) as r:
            return r.status == 200, json.loads(r.read() or b"{}")
    except Exception:
        return False, {}
def boot(data_dir, cwd, port=PORT):
    os.makedirs(data_dir, exist_ok=True)
    out = open(LOG, "a")
    return subprocess.Popen(
        [sys.executable, "-m", "hearth", "--port", str(port),
         "--data", data_dir], cwd=cwd, stdout=out,
        stderr=subprocess.STDOUT)
def wait_alive(port, secs=120):
    t0 = time.time()
    while time.time() - t0 < secs:
        ok, body = health(port, timeout=3)
        if ok:
            return time.time() - t0, body
        time.sleep(1)
    return None, {}
def stop(proc):
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except Exception:
        proc.kill()
def main():
    os.makedirs(RUNTIME, exist_ok=True)
    os.makedirs(EVID, exist_ok=True)
    legs = []
    # leg 1 — cold launch to gate, seconds
    d1 = os.path.join(RUNTIME, "cold")
    if os.path.isdir(d1):
        shutil.rmtree(d1)
    t0 = time.time()
    p1 = boot(d1, ROOT)
    gate_s = None
    gate_body = None
    while time.time() - t0 < 180:
        g = os.path.join(d1, "gate.json")
        if os.path.exists(g):
            gate_s = round(time.time() - t0, 1)
            gate_body = json.load(open(g))
            break
        if p1.poll() is not None:
            break
        time.sleep(0.5)
    alive_s, body = wait_alive(PORT, 90)
    legs.append({"leg": 1, "name": "cold launch → readiness gate",
                 "pass": bool(gate_s) and alive_s is not None,
                 "gateSeconds": gate_s,
                 "aliveSeconds": round(alive_s or -1, 1),
                 "gate": gate_body})
    # leg 2 — relaunch recovery on same data dir
    stop(p1)
    jpath1 = os.path.join(d1, "journal.jsonl")
    j1 = sum(1 for _ in open(jpath1, encoding="utf-8")) \
        if os.path.exists(jpath1) else 0
    p2 = boot(d1, ROOT)
    alive2, _body2 = wait_alive(PORT, 90)
    j2 = sum(1 for _ in open(jpath1, encoding="utf-8")) \
        if os.path.exists(jpath1) else 0
    legs.append({"leg": 2, "name": "relaunch recovery",
                 "pass": alive2 is not None and j2 >= j1 > 0,
                 "journalRowsBefore": j1, "journalRowsAfter": j2})
    # leg 3 — USB executing-from-media (H:)
    usb_ok = False
    usb_health = False
    dtype = ctypes.windll.kernel32.GetDriveTypeW("H:\\")
    seed_root = "H:" + os.sep + "hearth-seed"
    pkg_dst = os.path.join(seed_root, "hearth")
    if dtype == 2 and os.path.isdir(pkg_dst):  # DRIVE_REMOVABLE
        data_h = os.path.join(seed_root, "data-launch-check")
        p3 = boot(data_h, seed_root, port=9545)
        ok, _b = wait_alive(9545, 120)
        usb_health = ok
        jpath = os.path.join(data_h, "journal.jsonl")
        if os.path.exists(jpath):
            for line in open(jpath, encoding="utf-8"):
                if "launch-event" in line:
                    try:
                        usb_ok = json.loads(line)["value"].get(
                            "onRemovable") is True
                    except Exception:
                        pass
        stop(p3)
    legs.append({"leg": 3,
                 "name": "executing from removable media (H:)",
                 "pass": usb_ok and usb_health,
                 "driveType": dtype, "health": usb_health,
                 "onRemovable": usb_ok,
                 "note": "seed staged by S-usb-mint-gen2 / "
                         "S-usb-seed-run"})
    # leg 4 — close-terminates
    stop(p2)
    time.sleep(1)
    still, _ = health(PORT)
    legs.append({"leg": 4, "name": "close-terminates",
                 "pass": p2.returncode is not None and not still,
                 "exitCode": p2.returncode, "portFree": not still})
    # leg 5 — launch hygiene: second bind on owned port refused
    p5 = boot(os.path.join(RUNTIME, "hygiene-a"), ROOT)
    okA, _ = wait_alive(PORT, 90)
    refused = False
    if okA:
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", PORT))
            s.close()
        except OSError:
            refused = True
    legs.append({"leg": 5, "name": "launch hygiene — owned port "
                                   "refused to second owner",
                 "pass": bool(okA and refused),
                 "portOwned": okA, "secondBindRefused": refused})
    stop(p5)
    doc = {"generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "root": ROOT, "port": PORT, "legs": legs,
           "allPass": all(l["pass"] for l in legs)}
    out = os.path.join(EVID, "launch-check.json")
    with open(out, "w") as f:
        json.dump(doc, f, indent=1)
    print(json.dumps({l["leg"]: l["pass"] for l in legs}))
    print("allPass:", doc["allPass"], "->", out)
    return 0 if doc["allPass"] else 1
if __name__ == "__main__":
    sys.exit(main())
