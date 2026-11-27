"""Suite helpers — everything goes through the HTTP operator surface
(C-UserPathEnactment: checks exercise real user paths)."""
import json
import os
import subprocess
import sys
import time
import urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PORT = 9790
def req(path, body=None, port=PORT, timeout=30):
    url = f"http://127.0.0.1:{port}{path}"
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    last = None
    for _ in range(3):
        try:
            r = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(r, timeout=timeout) as resp:
                raw = resp.read()
            if raw:
                return json.loads(raw.decode())
            last = "empty body"
        except Exception as e:
            last = repr(e)
        time.sleep(2)
    raise RuntimeError(f"{path}: {last}")
def get(path, port=PORT):
    return req(path, None, port)
def post(path, body=None, port=PORT, timeout=30):
    return req(path, body or {}, port, timeout=timeout)
def chat(text, selector=None, port=PORT):
    return post("/api/chat", {"text": text, "selector": selector or []}, port)
class Rec:
    """per-scenario evidence recorder."""
    def __init__(self, sid):
        self.sid = sid
        self.checks = []
        self.extra = {}
    def check(self, name, ok, detail=""):
        self.checks.append({"name": name, "pass": bool(ok), "detail": str(detail)[:400]})
        return ok
    def emit(self, ev_dir, klass="enactment"):
        out = {"id": self.sid, "ran": True, "checks": self.checks,
               "pass": all(c["pass"] for c in self.checks),
               "evidence_class": klass, **self.extra}
        os.makedirs(ev_dir, exist_ok=True)
        with open(os.path.join(ev_dir, self.sid + ".json"), "w",
                  encoding="utf-8") as f:
            json.dump(out, f, indent=1)
        return out
def journal_rows(runtime):
    rows = []
    p = os.path.join(runtime, "journal.jsonl")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows
def current_rows(runtime):
    cur = {}
    for r in journal_rows(runtime):
        cur[r["id"]] = r
        if r.get("supersedes") and r["supersedes"] in cur:
            del cur[r["supersedes"]]
    return list(cur.values())
def wait_for(pred, timeout=20, step=0.5):
    t0 = time.time()
    while time.time() - t0 < timeout:
        v = pred()
        if v:
            return v
        time.sleep(step)
    return None
