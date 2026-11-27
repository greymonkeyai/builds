"""launch-check — launch hygiene evidence (S-windows-launch / S-close-terminate
legs). Four legs:
  1. probe-before-bind   — port probed for a live instance before binding
  2. exclusive bind      — the instance binds the port exclusively
  3. no-ok-while-owned   — a second launch while owned refuses (no ok:true)
  4. close-terminates    — terminating the process frees the port
"""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "chorus")
PORT = 9791
EV = os.path.join(ROOT, "evidence", "launch")
def hello(port, timeout=3.0):
    try:
        with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/api/hello", timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None
def port_free(port):
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", port))
        s.close()
        return True
    except OSError:
        return False
def wait_up(port, timeout=180):
    t0 = time.time()
    while time.time() - t0 < timeout:
        h = hello(port)
        if h and h.get("ok"):
            return h
        time.sleep(0.5)
    return None
def main():
    os.makedirs(EV, exist_ok=True)
    legs = []
    proc = None
    try:
        # leg 1+2: probe before bind, then exclusive bind
        was_free = port_free(PORT)
        legs.append({"leg": "probe-before-bind",
                     "pass": was_free,
                     "detail": f"port {PORT} free before launch"})
        env = dict(os.environ)
        clog = open(os.path.join(EV, "console-launchcheck.log"), "w")
        proc = subprocess.Popen(
            [sys.executable, "-m", "chorus", "--port", str(PORT),
             "--runtime", os.path.join(ROOT, "runtime-launchcheck"),
             "--no-browser"],
            cwd=ROOT, env=env, stdout=clog, stderr=subprocess.STDOUT)
        h = wait_up(PORT)
        legs.append({"leg": "exclusive-bind",
                     "pass": bool(h) and not port_free(PORT),
                     "detail": f"instance bound port {PORT}: {h}"})
        # leg 3: second launch while owned must refuse
        r2 = subprocess.run(
            [sys.executable, "-m", "chorus", "--port", str(PORT),
             "--runtime", os.path.join(ROOT, "runtime-launchcheck-2"),
             "--no-browser"],
            cwd=ROOT, capture_output=True, text=True, timeout=30)
        refused = r2.returncode == 2 and "LAUNCH REFUSED" in (r2.stdout or "")
        ok_while_owned = '"ok": true' in (r2.stdout or "").lower() and not refused
        legs.append({"leg": "no-ok-while-owned",
                     "pass": refused and not ok_while_owned,
                     "detail": f"second launch rc={r2.returncode}: "
                               f"{(r2.stdout or '').strip()[:160]}"})
        # leg 4: close-terminates
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=10)
        time.sleep(0.5)
        free = port_free(PORT) and hello(PORT) is None
        legs.append({"leg": "close-terminates",
                     "pass": free,
                     "detail": f"port {PORT} free after terminate: {free}"})
    finally:
        if proc and proc.poll() is None:
            proc.kill()
    ok = all(l["pass"] for l in legs)
    out = {"id": "launch-check", "app": "chorus", "port": PORT,
           "legs": legs, "pass": ok,
           "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    with open(os.path.join(EV, "launch-check.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))
    sys.exit(0 if ok else 1)
if __name__ == "__main__":
    main()
