"""run-suite — phase-0/1/2 harness driver.

Modes:
  --baseline   launch --bare; every check must fail (all-red recorded)
  --green      launch full app; run the corpus; green count = score
  --sabotage X empty-store|stub-engines|stubbed-endpoints — each check
               must be able to fail; results recorded per scenario

Writes:
  evidence/runs/<mode>-<ts>/summary.json    (green count + src-class
                                             fractions per R-V1/R-U1)
  evidence/scenarios/S-*.json               (checks carried inline per
                                             run mode — frozen names)
"""

import importlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from checks.checklib import Probe, Ctx  # noqa: E402
from checks import suite_ledger_needs, suite_chat_personas, \
    suite_shell, suite_stage, suite_fleet, suite_artifact, \
    suite_paths  # noqa: E402

PORT = int(os.environ.get("HEARTH_PORT", "9537"))
BASE = f"http://127.0.0.1:{PORT}"
RUNTIME = os.path.join(ROOT, "runtime")
EVID = os.path.join(ROOT, "evidence")

SUITES = [
    suite_ledger_needs, suite_chat_personas, suite_shell,
    suite_stage, suite_fleet, suite_artifact, suite_paths,
]


def scenarios():
    out = []
    for mod in SUITES:
        for name in dir(mod):
            if name.startswith(("S_", "P_")) and \
                    callable(getattr(mod, name)):
                out.append((name.replace("_", "-", 1), getattr(mod, name)))
    return out


class Proc:
    def __init__(self, mode, data_dir, port=PORT):
        self.mode = mode
        self.data_dir = data_dir
        self.port = port
        self.proc = None

    def start(self):
        env = dict(os.environ, HEARTH_DATA=self.data_dir)
        cmd = [sys.executable, "-m", "hearth", "--port",
               str(self.port), "--data", self.data_dir]
        if self.mode == "baseline":
            cmd.append("--bare")
        elif self.mode.startswith("sabotage"):
            cmd += ["--sabotage", self.mode.split(":", 1)[-1]]
        self.proc = subprocess.Popen(
            cmd, cwd=ROOT, env=env,
            stdout=open(os.path.join(self.data_dir, "app.log"), "w")
            if os.path.isdir(self.data_dir) else subprocess.DEVNULL,
            stderr=subprocess.STDOUT)
        return self.wait()

    def wait(self, timeout=120):
        t0 = time.time()
        while time.time() - t0 < timeout:
            try:
                code, body = Probe(
                    f"http://127.0.0.1:{self.port}").get(
                    "/api/health", timeout=2)
                if code == 200:
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        return False

    def stop(self):
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except Exception:
                self.proc.kill()

    def reboot(self):
        self.stop()
        return self.start()


def run(mode):
    os.makedirs(EVID, exist_ok=True)
    data_dir = os.path.join(RUNTIME, mode.replace(":", "-"))
    # fresh boot per run — stale journal rows must not contaminate
    # check results; the evidence is the run, not the residue
    for dd in ([data_dir] +
               [os.path.join(RUNTIME, f"peer-{p}")
                for p in (9541, 9542, 9543, 9544)]):
        if os.path.isdir(dd):
            shutil.rmtree(dd, ignore_errors=True)
    os.makedirs(data_dir, exist_ok=True)
    proc = Proc(mode, data_dir)
    if not proc.start():
        print("FAILED to launch")
        proc.stop()
        return 1
    probe = Probe(BASE)
    spawned = []

    def spawn(port):
        dd = os.path.join(RUNTIME, f"peer-{port}")
        os.makedirs(dd, exist_ok=True)
        p2 = Proc("green", dd, port=port)
        ok = p2.start()
        spawned.append(p2)
        return (f"http://127.0.0.1:{port}", dd) if ok else None

    ctx = Ctx(probe, reboot=proc.reboot, data_dir=data_dir,
              root=ROOT, spawn=spawn)

    results = {}
    t0 = time.time()
    for sid, fn in scenarios():
        try:
            checks = fn(ctx) or []
        except Exception as e:
            checks = [{"name": "harness-error", "pass": False,
                       "detail": f"{type(e).__name__}: {e}",
                       "src": ["user-path"]}]
        results[sid] = checks
        gp = sum(1 for c in checks if c["pass"])
        print(f"{sid:32s} {gp}/{len(checks)}", flush=True)

    for p2 in spawned:
        p2.stop()

    total = sum(len(c) for c in results.values())
    passed = sum(1 for c in results.values() for x in c if x["pass"])
    # evidence-quality fractions (R-V1/R-U1)
    all_checks = [x for c in results.values() for x in c]
    ext = sum(1 for x in all_checks
              if any(s.startswith("external:") for s in
                     x.get("src", [])))
    rendered = sum(1 for x in all_checks
                   if "rendered" in x.get("src", []))
    user_path = sum(1 for x in all_checks
                    if "user-path" in x.get("src", []))
    flag = sum(1 for x in all_checks
               if x.get("src") == ["flag"])

    run_dir = os.path.join(
        EVID, "runs",
        f"{mode.replace(':', '-')}-{time.strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(run_dir, exist_ok=True)
    summary = {"mode": mode, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "elapsed": round(time.time() - t0, 1),
               "scenarios": len(results), "checks": total,
               "passed": passed, "green": passed,
               "evidenceClass": {
                   "externalToFlag": ext / total if total else 0,
                   "rendered": rendered / total if total else 0,
                   "userPath": user_path / total if total else 0,
                   "selfAttestedOnly": flag / total if total else 0}}
    json.dump(summary, open(os.path.join(run_dir, "summary.json"),
                            "w"), indent=1)
    json.dump(results, open(os.path.join(run_dir, "checks.json"),
                            "w"), indent=1, default=str)

    # fold into evidence/scenarios/S-*.json (inline run record)
    mode_key = ("baseline" if mode == "baseline" else
                "green" if mode == "green" else
                f"sabotage-{mode.split(':', 1)[-1]}")
    for sid, checks in results.items():
        sfile = os.path.join(EVID, "scenarios", sid + ".json")
        d = json.load(open(sfile)) if os.path.exists(sfile) else {}
        np_ = sum(1 for c in checks if c["pass"])
        d[mode_key] = {"ts": summary["ts"], "checks": checks,
                       "pass": np_, "fail": len(checks) - np_,
                       "allGreen": np_ == len(checks) and
                       len(checks) > 0}
        os.makedirs(os.path.dirname(sfile), exist_ok=True)
        json.dump(d, open(sfile, "w"), indent=1, default=str)

    print(f"\n=== {mode}: {passed}/{total} green "
          f"({summary['elapsed']}s) ===")
    print("evidenceClass:", summary["evidenceClass"])
    proc.stop()
    return 0


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", action="store_true")
    ap.add_argument("--green", action="store_true")
    ap.add_argument("--sabotage", default=None,
                    choices=["empty-store", "stub-engines",
                             "stubbed-endpoints"])
    args = ap.parse_args()
    if args.baseline:
        sys.exit(run("baseline"))
    if args.sabotage:
        sys.exit(run("sabotage:" + args.sabotage))
    sys.exit(run("green"))
