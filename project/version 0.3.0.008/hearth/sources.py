"""hearth sources — configured sources, admission gate, accounts,
environmental data.
Every proposed source passes an admission gate before use
(S-source-admission-gate): free-tier readability, no login requirement,
no published AI-usage opt-out — result recorded as an assertion;
failures quarantined with basis. Environmental/meteorological data
enters as configured-source claims (prompt §Projects and temporal
context).
"""
import json
import os
import re
import time
import urllib.request
import urllib.error
KNOWN_OPTOUT = ("reddit.com", "twitter.com", "x.com", "quora.com",
                "nytimes.com", "britannica.com", "medium.com",
                "imdb.com", "discogs.com", "stackoverflow.com")
LOGIN_GATED_HINTS = ("accounts.", "login", "signin", "auth/")
class Sources:
    def __init__(self, host):
        self.h = host
    def import_seed(self):
        """Seed imports as configured-source ledger rows once."""
        if self.h.journal.rows("source-row"):
            return
        seed = os.path.join(self.h.root, "seed", "configured-sources.json")
        try:
            payload = json.load(open(seed, encoding="utf-8"))
        except Exception as e:
            self.h.journal.append("source-seed-import",
                                  {"status": "failed", "reason": str(e)},
                                  claimant="system", basis="system")
            return
        for s in payload["sources"]:
            row = {"key": s["key"], "name": s["name"], "kind": s["kind"],
                   "url": s["url"], "api": s.get("api"),
                   "domains": s["domains"],
                   "descriptor": s["descriptor"],
                   "ceiling": s["ceiling"],
                   "admission": "proposed", "quarantined": False}
            self.h.journal.append("source-row", row, claimant="system",
                                  basis="source-evidence",
                                  provenance="seed:configured-sources-001")
        self.h.journal.append(
            "source-seed-import",
            {"count": len(payload["sources"]),
             "revision": payload.get("revision")},
            claimant="system", basis="execution-evidence")
    def rows(self):
        return self.h.journal.rows("source-row")
    def admit(self, source_key, probe=True, claimant="system"):
        """The admission gate — verify free/no-login/no-opt-out, record
        the verdict as an assertion, quarantine failures with basis."""
        row = self.h.journal.rows("source-row",
                                  where={"key": source_key})
        if not row:
            return None
        src = row[-1]["value"]
        verdict = {"source": source_key, "checked": time.time(),
                   "steps": {}}
        host = re.sub(r"^https?://", "", src["url"]).split("/")[0]
        verdict["steps"]["optOutList"] = host not in KNOWN_OPTOUT
        verdict["steps"]["loginHints"] = not any(
            h in src["url"].lower() for h in LOGIN_GATED_HINTS)
        reachable = None
        if probe:
            url = src.get("api") or src["url"]
            try:
                req = urllib.request.Request(
                    url, method="HEAD",
                    headers={"User-Agent": "hearth/0.3 (local-first)"})
                with urllib.request.urlopen(req, timeout=8) as r:
                    reachable = r.status < 400
            except urllib.error.HTTPError as e:
                reachable = e.code in (403, 405)  # exists but HEAD denied
                if e.code in (401, 402):
                    reachable = False
            except Exception:
                reachable = False
        verdict["steps"]["reachableFreeTier"] = reachable
        admitted = all(v is True for k, v in verdict["steps"].items()
                       if v is not None) and reachable is not False
        verdict["admitted"] = bool(admitted)
        verdict["basis"] = (
            "probed endpoint + opt-out list + login-hint screen"
            if probe else "descriptor screen only (probe skipped)")
        self.h.journal.append(
            "source-verdict", verdict,
            claimant="system", basis="execution-evidence",
            refs=[row[-1]["id"]])
        # quarantine state on the source row via superseding claim
        self.h.journal.append(
            "source-state",
            {"source": source_key,
             "admission": "admitted" if admitted else "quarantined",
             "quarantined": not admitted,
             "basis": verdict["basis"]},
            claimant="system", basis="durable-result",
            refs=[row[-1]["id"]])
        return verdict
    def admit_all(self, probe=False):
        """Gate every proposed row (probe=False keeps boot offline-safe;
        the suite/user path probes for real)."""
        out = []
        for r in self.rows():
            if r["value"].get("admission") == "proposed":
                out.append(self.admit(r["value"]["key"], probe=probe))
        return out
    def state(self, key):
        st = self.h.journal.rows("source-state", where={"source": key})
        return st[-1]["value"] if st else {"admission": "proposed"}
    def view(self):
        out = []
        for r in self.rows():
            v = dict(r["value"])
            v.update(self.state(v["key"]))
            out.append(v)
        return out
    def domain_match(self, domains):
        """Suggest a configured source whose domains intersect the
        persona's declared knowledge domain."""
        want = {d.lower() for d in domains}
        best = None
        for r in self.rows():
            v = r["value"]
            inter = want & {d.lower() for d in v.get("domains", [])}
            if inter and (best is None
                          or len(inter) > len(best[1])):
                best = (v, inter)
        return best[0] if best else None
    # ---- configured accounts (C-CredentialDescriptor) ----------------
    def add_account(self, kind, label, endpoint, secret):
        """Descriptor recorded as a configured-source row; the secret
        goes to the local credential store — never ledger/logs/media."""
        key = "account-" + re.sub(r"\W+", "-", label.lower())[:24]
        cred_path = os.path.join(self.h.cred_dir, key + ".secret")
        with open(cred_path, "w") as f:
            f.write(secret)
        os.chmod(cred_path, 0o600)
        row = {"key": key, "name": label, "kind": kind,
               "url": endpoint, "api": None,
               "domains": ["account", kind],
               "descriptor": "granted_only", "ceiling": 0.9,
               "credential": {"kind": kind, "store": "local-file",
                              "ref": key + ".secret"},
               "admission": "admitted", "quarantined": False}
        j = self.h.journal.append("source-row", row, claimant="user",
                                  basis="user-choice",
                                  provenance="account-configure")
        return j
    def secret_in_ledger(self):
        """Secret hygiene check: no credential secret material in rows."""
        for r in self.h.journal.rows():
            if "secret" in json.dumps(r["value"]).lower() and \
                    "credential" not in json.dumps(r["value"]).lower():
                return True
        return False
    # ---- mail --------------------------------------------------------
    def mail_items(self):
        """Email list from configured account or labeled fixture."""
        acct = [r for r in self.rows()
                if r["value"].get("credential")]
        fixture_dir = os.path.join(self.h.root, "fixtures", "inbox")
        items = []
        if os.path.isdir(fixture_dir):
            for fn in sorted(os.listdir(fixture_dir)):
                if fn.endswith(".eml"):
                    txt = open(os.path.join(fixture_dir, fn),
                               encoding="utf-8", errors="replace").read()
                    subj = re.search(r"^Subject:\s*(.+)$", txt, re.M)
                    frm = re.search(r"^From:\s*(.+)$", txt, re.M)
                    items.append({"id": "fixture-" + fn,
                                  "subject": subj.group(1).strip()
                                  if subj else fn,
                                  "from": frm.group(1).strip()
                                  if frm else "unknown",
                                  "basis": "fixture",
                                  "body": txt[:2000]})
        # basis labels what is ACTUALLY served — fixture items stay
        # fixture even when an account is configured but not fetched
        served_fixture = items and all(i["basis"] == "fixture"
                                       for i in items)
        basis = ("fixture-inbox; account configured "
                 "(live fetch unavailable)" if acct and served_fixture
                 else "configured-account:" + acct[-1]["value"]["key"]
                 if acct and not served_fixture else "fixture")
        return {"items": items, "basis": basis,
                "configured": bool(acct)}
    # ---- environmental / meteorological claims -----------------------
    def weather(self, lat, lon):
        """Meteorological data enters like other outside info — a
        configured source (open-meteo class, free/no-login) admitted
        through the gate, results are claims with provenance+freshness."""
        key = "source-open-meteo"
        if not self.h.journal.rows("source-row", where={"key": key}):
            self.h.journal.append(
                "source-row",
                {"key": key, "name": "Open-Meteo", "kind": "api",
                 "url": "https://api.open-meteo.com",
                 "api": "https://api.open-meteo.com/v1/forecast",
                 "domains": ["weather", "meteorology", "environment"],
                 "descriptor": "all_avatars", "ceiling": 0.8,
                 "admission": "proposed", "quarantined": False},
                claimant="system", basis="source-evidence")
            self.admit(key, probe=False)
        url = ("https://api.open-meteo.com/v1/forecast?latitude=%s&longitude"
               "=%s&current=temperature_2m,weather_code,wind_speed_10m"
               % (lat, lon))
        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                data = json.loads(r.read())
            cur = data.get("current", {})
            claim = {"for": {"lat": lat, "lon": lon},
                     "tempC": cur.get("temperature_2m"),
                     "code": cur.get("weather_code"),
                     "windKph": cur.get("wind_speed_10m"),
                     "observedAt": cur.get("time"),
                     "freshnessSeconds": 0}
            self.h.journal.append("env-claim", claim,
                                  claimant="tool:weather.read",
                                  basis="source-evidence",
                                  provenance="source:" + key,
                                  certainty=0.8, confidence=0.8)
            return claim
        except Exception as e:
            self.h.journal.append(
                "env-claim",
                {"for": {"lat": lat, "lon": lon}, "status": "unavailable",
                 "reason": str(e)},
                claimant="tool:weather.read", basis="source-evidence",
                provenance="source:" + key, certainty=0.3)
            return None
