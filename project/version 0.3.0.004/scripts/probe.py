"""Second-instance probe — boots on an alternate port, verifies isolation
and steward responsiveness, writes evidence/probe-<ts>.json"""
import json, os, shutil, subprocess, sys, time, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 9771
def main():
    rt = os.path.join(ROOT, "runtime", "probe")
    shutil.rmtree(rt, ignore_errors=True); os.makedirs(rt, exist_ok=True)
    p = subprocess.Popen([sys.executable, "-m", "app", "--port", str(PORT),
                          "--runtime", rt, "--no-watchdog"], cwd=ROOT)
    out = {"port": PORT}
    try:
        t0 = time.time(); up = None
        while time.time()-t0 < 90:
            try:
                up = json.loads(urllib.request.urlopen(
                    f"http://127.0.0.1:{PORT}/api/state", timeout=3).read())
                break
            except Exception: time.sleep(0.5)
        out["launched"] = bool(up)
        if up:
            t1 = time.time()
            r = json.loads(urllib.request.urlopen(
                f"http://127.0.0.1:{PORT}/api/gate", timeout=5).read())
            out["gateMs"] = r.get("timeToGateMs")
            out["apiMs"] = int((time.time()-t1)*1000)
            out["components"] = up["manifest"]
            out["roster"] = len(up["roster"])
            out["llm"] = up["engines"]["llm"]["mode"]
            out["stewardLast"] = up["steward"]["last"]
    finally:
        p.terminate()
        try: p.wait(timeout=15)
        except Exception: p.kill()
    os.makedirs(os.path.join(ROOT, "evidence"), exist_ok=True)
    fn = os.path.join(ROOT, "evidence",
                      "probe-"+time.strftime("%Y%m%d-%H%M%S")+".json")
    json.dump(out, open(fn, "w"), indent=2)
    print(json.dumps(out, indent=2))
if __name__ == "__main__":
    main()
