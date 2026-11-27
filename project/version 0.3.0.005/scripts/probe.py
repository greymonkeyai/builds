#!/usr/bin/env python
"""probe — second-instance probe for Quorum. Reports who owns the port and
whether the running instance answers, without claiming anything."""
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EVID = os.path.join(ROOT, "evidence")
os.makedirs(EVID, exist_ok=True)

port = int(sys.argv[1]) if len(sys.argv) > 1 else 9790
out = {"port": port, "answers": False, "app": None, "honest": None}
try:
    with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/honesty", timeout=3) as r:
        d = json.loads(r.read())
    out["answers"] = True
    out["app"] = d.get("app")
    out["ledger_rows"] = d.get("ledger", {}).get("rows")
    out["llm"] = d.get("llm", {}).get("mode")
    out["steward"] = d.get("steward")
except Exception as e:
    out["error"] = str(e)
import time
name = f"probe-{time.strftime('%Y%m%d-%H%M%S')}.json"
json.dump(out, open(os.path.join(EVID, name), "w"), indent=2)
print(json.dumps(out, indent=2))
