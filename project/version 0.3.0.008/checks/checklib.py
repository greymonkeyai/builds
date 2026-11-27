"""checklib — phase-0 harness primitives (fresh realization, cycle 8).
R-V1: a check's evidence source is external to the flag asserted —
journal rows read from the file, wav artifacts parsed on disk, process
command lines, real ping RTTs. Where a flag is the evidence it is
corroborated, not trusted.
R-U1: checks exercise what the user can reach — rendered page content
(data-affordance attributes the page carries) plus the user-path
endpoints the page's JS calls.
Every check records its evidence-source classes in `src`:
  rendered    — inspects the served page's rendered affordances
  user-path   — drives the operator-surface endpoints the page calls
  external:journal  — journal.jsonl read from disk
  external:file     — artifact files (wav/png/gate.json/map/seed-log)
  external:proc     — process-level evidence (cmdline/port owner)
  external:net      — real network evidence (ping/arp/scan)
  flag        — self-attested only (minimized; corroborate when used)
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error
class Probe:
    """HTTP client for the operator surface — the same endpoints the
    operator page's JS calls."""
    def __init__(self, base):
        self.base = base.rstrip("/")
    def get(self, path, timeout=30):
        try:
            with urllib.request.urlopen(self.base + path,
                                        timeout=timeout) as r:
                body = r.read()
                try:
                    return r.status, json.loads(body)
                except Exception:
                    return r.status, body
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.loads(e.read())
            except Exception:
                return e.code, {}
        except Exception as e:
            return None, {"error": str(e)}
    def post(self, path, body=None, timeout=180):
        try:
            req = urllib.request.Request(
                self.base + path, data=json.dumps(body or {}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as r:
                try:
                    return r.status, json.loads(r.read())
                except Exception:
                    return r.status, {}
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.loads(e.read())
            except Exception:
                return e.code, {}
        except Exception as e:
            return None, {"error": str(e)}
    def page(self):
        code, body = self.get("/")
        if isinstance(body, bytes):
            return code, body.decode("utf-8", "replace")
        return code, ""
    def rows(self, kind="", limit=5000):
        _, r = self.get(f"/api/ledger?kind={kind}&limit={limit}")
        return r.get("rows", []) if isinstance(r, dict) else []
    def state(self):
        _, s = self.get("/api/state")
        return s if isinstance(s, dict) else {}
    def alive(self):
        _, hh = self.get("/api/health", timeout=3)
        return isinstance(hh, dict) and hh.get("app") == "hearth" \
            and not hh.get("bare")
class Ctx:
    def __init__(self, probe, reboot=None, data_dir=None, root=None,
                 spawn=None):
        self.probe = probe
        self._reboot = reboot
        self._page = None
        self.data_dir = data_dir
        self.root = root or (os.path.dirname(os.path.dirname(data_dir))
                             if data_dir else os.getcwd())
        self.scratch = {}
        self._spawn = spawn
    def reboot(self):
        if self._reboot:
            self._page = None
            self._reboot()
    def spawn(self, port=9541):
        """Boot a second real instance on another port + data dir —
        same host (not a fleet member, but a distinct instance for
        exchange-generation checks)."""
        if self._spawn:
            return self._spawn(port)
        return None
    def page(self):
        if self._page is None:
            self._page = self.probe.page()[1]
        return self._page
    # ---- external ground truth --------------------------------------
    def journal_rows(self, kind=None):
        """Journal read from the FILE — external to the app's flags."""
        path = os.path.join(self.data_dir or "", "journal.jsonl")
        out = []
        if os.path.exists(path):
            for line in open(path, encoding="utf-8"):
                line = line.strip()
                if line:
                    try:
                        r = json.loads(line)
                        if not kind or r["kind"] == kind:
                            out.append(r)
                    except Exception:
                        pass
        return out
    def affordance(self, name):
        """Rendered surface: the page carries this affordance."""
        return f'data-affordance="{name}"' in self.page() or \
            f'data-action="{name}"' in self.page() or \
            f'id="{name}"' in self.page()
    def discovery(self, timeout=200, force=False):
        """One real discovery run per suite session — device
        enrichment (resolve+ping+ports) takes minutes; reuse the
        finished result across fleet checks."""
        cached = self.scratch.get("discovery")
        if cached and not force:
            return cached
        self.probe.post("/api/fleet/discover", {"async": True})
        t0 = time.time()
        while time.time() - t0 < timeout:
            _, d = self.probe.get("/api/fleet/discovery")
            if isinstance(d, dict) and d.get("state") == "finished":
                self.scratch["discovery"] = d
                return d
            time.sleep(1)
        d = self.probe.get("/api/fleet/discovery")[1]
        self.scratch["discovery"] = d if isinstance(d, dict) else {}
        return self.scratch["discovery"]

    def wav_info(self, path):
        import wave
        try:
            with wave.open(path, "rb") as w:
                frames = w.getnframes()
                return {"frames": frames,
                        "seconds": round(frames / w.getframerate(), 3)}
        except Exception:
            return None
def ck(name, cond, detail="", src=("user-path",)):
    return {"name": name, "pass": bool(cond),
            "detail": str(detail)[:400], "src": list(src)}
def dead(ctx, names):
    """Everything fails while the surface is absent."""
    return [ck(n, False, "operator surface absent",
               src=("user-path",)) for n in names]
