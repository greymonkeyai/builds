"""checklib — phase-0 check harness primitives.

Every check exercises the user path (C-UserPathEnactment): the same
HTTP endpoints the operator surface drives, plus the served page.
A check must be able to fail — on a bare system everything is red.
"""

import base64
import json
import os
import re
import time
import urllib.request
import urllib.error


class Probe:
    """HTTP client for the operator surface — same endpoints the
    browser UI calls."""

    def __init__(self, base):
        self.base = base.rstrip("/")

    def get(self, path, timeout=30):
        try:
            with urllib.request.urlopen(self.base + path, timeout=timeout) as r:
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

    def post(self, path, body=None, timeout=120):
        try:
            req = urllib.request.Request(
                self.base + path, data=json.dumps(body or {}).encode(),
                headers={"Content-Type": "application/json"}, method="POST")
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
        _, h = self.get("/api/health", timeout=3)
        return isinstance(h, dict) and h.get("app") == "vesta" and not h.get("bare")


class Ctx:
    """Check context: probe + driver-provided reboot + cached page."""

    def __init__(self, probe, reboot=None, data_dir=None, root=None):
        self.probe = probe
        self._reboot = reboot
        self._page = None
        self.data_dir = data_dir
        self.root = root or (os.path.dirname(os.path.dirname(data_dir))
                             if data_dir else os.getcwd())
        self.scratch = {}          # cross-check scratch within a scenario

    def reboot(self):
        """Restart the instance on the same data dir — real persistence
        enactment through a boundary."""
        if self._reboot:
            self._reboot()

    def page(self):
        if self._page is None:
            self._page = self.probe.page()[1]
        return self._page


def ck(name, cond, detail=""):
    return {"name": name, "pass": bool(cond), "detail": str(detail)[:400]}


def has_endpoint(ctx, path):
    code, r = ctx.probe.get(path)
    return code == 200 and isinstance(r, dict) and r.get("ok") is not False
