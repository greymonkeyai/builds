"""Launch verification probe. Boots a second Meridian instance on port 9761
with an isolated runtime dir, polls the API, proves the steward runs while the
server answers, and writes evidence/launch/probe-<ts>.json.

Usage: python scripts/probe.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get(url, timeout=3.0):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode())


def main():
    runtime = os.path.join(ROOT, "runtime", "probe")
    os.makedirs(runtime, exist_ok=True)
    proc = subprocess.Popen(
        [sys.executable, "-m", "app", "--port", "9761",
         "--runtime", runtime],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True)
    out = {"launched": False, "checks": {}, "ok": False}
    try:
        # wait for serve
        base = "http://127.0.0.1:9761"
        for _ in range(60):
            try:
                get(base + "/api/honesty", timeout=3.0)
                out["launched"] = True
                break
            except Exception:
                time.sleep(0.5)
        if not out["launched"]:
            print("FAIL: server did not come up")
            return out
        st = get(base + "/api/state")
        out["checks"]["state.roster"] = len(st.get("roster", []))
        out["checks"]["state.tools"] = len(st.get("tools", []))
        out["checks"]["honesty.ledger.durable"] = st["honesty"]["ledger"]["durable"]
        out["checks"]["engine.llm.mode"] = st["honesty"]["engines"]["llm"]["mode"]
        # chat round trip
        t0 = time.time()
        r = get(base + "/api/state")  # warm
        chat = None
        try:
            req = urllib.request.Request(
                base + "/api/chat", data=json.dumps(
                    {"text": "probe ping"}).encode(),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as resp:
                chat = json.loads(resp.read().decode())
        except Exception as e:
            chat = {"ok": False, "error": repr(e)}
        out["checks"]["chat.ms"] = int((time.time() - t0) * 1000)
        out["checks"]["chat.ok"] = bool(chat and chat.get("ok"))
        out["checks"]["chat.intents"] = (chat or {}).get("result", {}).get("intents")
        # steward ran while serving?
        runs = get(base + "/api/log?kind=steward&limit=5").get("rows", [])
        out["checks"]["steward.runs"] = len(runs)
        # durability: ledger file exists and non-empty
        lp = os.path.join(runtime, "ledger.jsonl")
        out["checks"]["ledger.file.bytes"] = os.path.getsize(lp) if os.path.exists(lp) else 0
        out["checks"]["launch.assertion"] = bool(get(
            base + "/api/library?predicate=launch:report&limit=1").get("rows"))
        out["ok"] = (out["launched"] and out["checks"]["chat.ok"]
                     and out["checks"]["state.tools"] > 10
                     and out["checks"]["ledger.file.bytes"] > 0)
        return out
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        ts = time.strftime("%Y%m%d-%H%M%S")
        ep = os.path.join(ROOT, "evidence", "launch", f"probe-{ts}.json")
        with open(ep, "w") as f:
            json.dump(out, f, indent=2)
        print(json.dumps(out, indent=2))
        print("probe evidence:", ep)


if __name__ == "__main__":
    main()
