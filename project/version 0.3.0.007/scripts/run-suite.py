#!/usr/bin/env python3
"""run-suite.py — phase-0 contract driver.

Modes:
  --baseline    boot --bare, run all checks, record all-red evidence
  --green       boot full system, run all checks through user path
  --sabotage    boot with sabotage hooks (empty store / stubbed endpoints),
                record per-check red evidence
  --all         baseline → green → sabotage in sequence

Each run writes evidence/scenarios/S-*.json + a summary under
evidence/runs/<mode>-<ts>/.
"""

import argparse
import importlib
import json
import os
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from checks.checklib import Probe, Ctx  # noqa: E402

PORT = 9537
BASE = f"http://127.0.0.1:{PORT}"

SCENARIO_MODULES = {
    "S-assertion-input":          "checks.suite_ledger_needs",
    "S-template-need":            "checks.suite_ledger_needs",
    "S-candidate-ranking":        "checks.suite_ledger_needs",
    "S-focused-need":             "checks.suite_ledger_needs",
    "S-need-fulfillment":         "checks.suite_ledger_needs",
    "S-intent-routing":           "checks.suite_ledger_needs",
    "S-list-project":             "checks.suite_ledger_needs",
    "S-steward-liveness":         "checks.suite_ledger_needs",
    "S-background-present":       "checks.suite_ledger_needs",
    "S-restart-recovery":         "checks.suite_ledger_needs",
    "S-competing-tools":          "checks.suite_ledger_needs",
    "S-asset-anticipation":       "checks.suite_ledger_needs",
    "S-tool-composition":         "checks.suite_ledger_needs",
    "S-chat-invocation":          "checks.suite_chat_personas",
    "S-conversational-register":  "checks.suite_chat_personas",
    "S-faithful-voice":           "checks.suite_chat_personas",
    "S-distinct-preloadeds":      "checks.suite_chat_personas",
    "S-personality-create":       "checks.suite_chat_personas",
    "S-personality-editor":       "checks.suite_chat_personas",
    "S-personality-source-match": "checks.suite_chat_personas",
    "S-personality-roster":       "checks.suite_chat_personas",
    "S-dyadic-ranking":           "checks.suite_chat_personas",
    "S-portrait-bind":            "checks.suite_chat_personas",
    "S-respondent-union":         "checks.suite_chat_personas",
    "S-response-depth":           "checks.suite_chat_personas",
    "S-interest-respondents":     "checks.suite_chat_personas",
    "S-conversation-reset":       "checks.suite_chat_personas",
    "S-context-display":          "checks.suite_chat_personas",
    "S-email-commentary":         "checks.suite_chat_personas",
    "S-speech-serialization":     "checks.suite_chat_personas",
    "S-speech-completion":        "checks.suite_chat_personas",
    "S-voice-spec":               "checks.suite_chat_personas",
    "S-voice-select":             "checks.suite_chat_personas",
    "S-voice-assign":             "checks.suite_chat_personas",
    "S-audible-ack":              "checks.suite_chat_personas",
    "S-speech-latency":           "checks.suite_chat_personas",
    "S-windows-launch":           "checks.suite_shell_exchange",
    "S-close-terminate":          "checks.suite_shell_exchange",
    "S-color-schemes":            "checks.suite_shell_exchange",
    "S-status-bar":               "checks.suite_shell_exchange",
    "S-library-browse":           "checks.suite_shell_exchange",
    "S-account-configure":        "checks.suite_shell_exchange",
    "S-source-seed-import":       "checks.suite_shell_exchange",
    "S-source-admission-gate":    "checks.suite_shell_exchange",
    "S-publish-workflow":         "checks.suite_shell_exchange",
    "S-defer-publication":        "checks.suite_shell_exchange",
    "S-scancode-interchange":     "checks.suite_shell_exchange",
    "S-background-channels":      "checks.suite_stage",
    "S-interstitial-queue":       "checks.suite_stage",
    "S-scene-enactment":          "checks.suite_stage",
    "S-usb-seed-run":             "checks.suite_fleet",
    "S-usb-stage-consent":        "checks.suite_fleet",
    "S-fleet-invite":             "checks.suite_fleet",
    "S-fleet-install-path":       "checks.suite_fleet",
    "S-fleet-action-legible":     "checks.suite_fleet",
    "S-fleet-exchange":           "checks.suite_fleet",
    "S-role-negotiate":           "checks.suite_fleet",
    "S-usb-mint-gen2":            "checks.suite_fleet",
    "S-usb-log-courier":          "checks.suite_fleet",
    "S-fleet-roster":             "checks.suite_fleet",
    "S-network-map":              "checks.suite_fleet",
    "S-local-transports":         "checks.suite_fleet",
    "S-credential-surrender":     "checks.suite_fleet",
    "S-discovery-progress":       "checks.suite_fleet",
    "S-exchange-import":          "checks.suite_artifact",
    "S-artifact-import":          "checks.suite_artifact",
    "S-tool-transmission":        "checks.suite_artifact",
    "S-artifact-style":           "checks.suite_artifact",
    "S-artifact-republish":       "checks.suite_artifact",
    "S-dubious-source":           "checks.suite_artifact",
    "S-preload-cache":            "checks.suite_artifact",
}


class Instance:
    """A booted vesta instance."""

    def __init__(self, args, data_dir, port=PORT):
        self.port = port
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        env = dict(os.environ, VESTA_DATA=data_dir)
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "vesta", "--port", str(port)] + args,
            cwd=ROOT, env=env,
            stdout=open(os.path.join(data_dir, "stdout.log"), "w"),
            stderr=subprocess.STDOUT)
        self.base = f"http://127.0.0.1:{port}"

    def wait_ready(self, timeout=30):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(self.base + "/api/health",
                                            timeout=2) as r:
                    return json.loads(r.read())
            except Exception:
                time.sleep(0.4)
        return None

    def kill(self):
        try:
            self.proc.terminate()
            self.proc.wait(timeout=8)
        except Exception:
            self.proc.kill()


def _check_fn(scenario):
    mod_name = SCENARIO_MODULES[scenario]
    mod = importlib.import_module(mod_name)
    fn_name = scenario.replace("-", "_")
    return getattr(mod, fn_name)


def run_all(ctx, label):
    """Run every scenario's checks against ctx.probe. Returns results dict."""
    results = {}
    for sid in SCENARIO_MODULES:
        try:
            checks = _check_fn(sid)(ctx)
        except Exception as e:
            checks = [{"name": "scenario-executable", "pass": False,
                       "detail": f"{type(e).__name__}: {e}"}]
        results[sid] = {
            "scenario": sid,
            "checks": checks,
            "pass": sum(1 for c in checks if c["pass"]),
            "fail": sum(1 for c in checks if not c["pass"]),
            "allGreen": all(c["pass"] for c in checks),
        }
    return results


def emit(results, mode, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    scen_dir = os.path.join(ROOT, "evidence", "scenarios")
    os.makedirs(scen_dir, exist_ok=True)
    total_pass = total_fail = green_scen = 0
    for sid, res in results.items():
        total_pass += res["pass"]
        total_fail += res["fail"]
        green_scen += 1 if res["allGreen"] else 0
        # evidence/scenarios/S-*.json carries check results inline
        existing = {}
        spath = os.path.join(scen_dir, f"{sid}.json")
        if os.path.exists(spath):
            existing = json.load(open(spath))
        existing[mode] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "checks": res["checks"],
            "pass": res["pass"], "fail": res["fail"],
            "allGreen": res["allGreen"],
        }
        with open(spath, "w") as f:
            json.dump(existing, f, indent=2)
    summary = {
        "mode": mode, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "scenarios": len(results),
        "scenariosAllGreen": green_scen,
        "checksPassed": total_pass, "checksFailed": total_fail,
        "checkTotal": total_pass + total_fail,
        "perScenario": {s: {"pass": r["pass"], "fail": r["fail"],
                            "allGreen": r["allGreen"]}
                        for s, r in results.items()},
    }
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", action="store_true")
    ap.add_argument("--green", action="store_true")
    ap.add_argument("--sabotage", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--sabotage-hook", default="empty-store",
                    help="empty-store | stubbed-endpoints | bare")
    args = ap.parse_args()

    runs_dir = os.path.join(ROOT, "evidence", "runs")
    ts = time.strftime("%Y%m%d-%H%M%S")

    def boot(extra):
        data_dir = os.path.join(ROOT, "runtime", f"suite-{ts}")
        inst = Instance(extra, data_dir)
        health = inst.wait_ready(30)
        if not health:
            print("FATAL: instance did not answer /api/health")
            inst.kill()
            sys.exit(2)
        return inst, data_dir

    def reboot_factory(inst, extra, data_dir):
        def _rb():
            inst.kill()
            time.sleep(1)
            inst.proc = subprocess.Popen(
                [sys.executable, "-m", "vesta", "--port", str(inst.port)] + extra,
                cwd=ROOT, env=dict(os.environ, VESTA_DATA=data_dir),
                stdout=open(os.path.join(data_dir, "stdout.log"), "a"),
                stderr=subprocess.STDOUT)
            inst.wait_ready(30)
        return _rb

    if args.baseline or args.all:
        inst, dd = boot(["--bare"])
        ctx = Ctx(Probe(BASE), reboot_factory(inst, ["--bare"], dd), dd)
        res = run_all(ctx, "baseline")
        s = emit(res, "baseline",
                 os.path.join(runs_dir, f"baseline-{ts}"))
        print(f"[baseline] {s['checksPassed']}/{s['checkTotal']} checks pass "
              f"({s['scenariosAllGreen']}/{s['scenarios']} scenarios all-green)")
        inst.kill()

    if args.green or args.all or not (args.baseline or args.sabotage):
        inst, dd = boot([])
        ctx = Ctx(Probe(BASE), reboot_factory(inst, [], dd), dd)
        res = run_all(ctx, "green")
        s = emit(res, "green",
                 os.path.join(runs_dir, f"green-{ts}"))
        print(f"[green] {s['checksPassed']}/{s['checkTotal']} checks pass "
              f"({s['scenariosAllGreen']}/{s['scenarios']} scenarios all-green)")
        inst.kill()

    if args.sabotage or args.all:
        hook_args = {"empty-store": ["--sabotage", "empty-store"],
                     "stub-engines": ["--sabotage", "stub-engines"],
                     "stubbed-endpoints": ["--sabotage", "stubbed-endpoints"],
                     "bare": ["--bare"]}[args.sabotage_hook]
        inst, dd = boot(hook_args)
        ctx = Ctx(Probe(BASE), reboot_factory(inst, hook_args, dd), dd)
        res = run_all(ctx, "sabotage")
        s = emit(res, f"sabotage-{args.sabotage_hook}",
                 os.path.join(runs_dir, f"sabotage-{args.sabotage_hook}-{ts}"))
        print(f"[sabotage:{args.sabotage_hook}] "
              f"{s['checksPassed']}/{s['checkTotal']} checks pass "
              f"(expected red)")
        inst.kill()


if __name__ == "__main__":
    main()
