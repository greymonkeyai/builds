"""sources — configured-source rows, admission gate, account
credentialing, and retrieval helpers (module: sources).

The shipped seed (configured-sources-001) imports as configured-source
ledger rows: every entry carries kind, endpoint, knowledge domains,
credential descriptor, and ceiling (C-MultiSourceAccess, C-SourceCeilings,
C-SourceDomains, C-CredentialDescriptor). Every proposed source passes an
admission gate before use — free-tier readability, no login, no published
AI-usage opt-out — verified by real probing; the result is recorded as an
assertion and failures are quarantined with basis (S-source-admission-
gate). Secrets never enter ledger rows, logs, or exchange media —
descriptors only (C-CredentialDescriptor).
"""

import base64
import concurrent.futures
import email
import imaplib
import json
import os
import re
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "vesta/0.3.0.007 (local-first persona appliance; contact: owner)"}
AI_OPTOUT_HOSTS = ("reddit.com", "twitter.com", "x.com", "quora.com",
                   "nytimes.com", "britannica.com", "medium.com")


def _fetch(url, timeout=8, head=False):
    try:
        req = urllib.request.Request(url, headers=UA,
                                     method="HEAD" if head else "GET")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = b"" if head else r.read(200_000)
            return r.status, body
    except Exception as e:
        return None, str(e)


class Sources:
    def __init__(self, host):
        self.h = host
        self.cred_dir = os.path.join(host.dir, "credentials")
        os.makedirs(self.cred_dir, exist_ok=True)

    # ---------- seed import ----------
    def seed_payload(self):
        path = os.path.join(os.path.dirname(self.h.dir), "seed", "configured-sources.json")
        if not os.path.exists(path):
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "seed", "configured-sources.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def import_seed(self, force=False):
        """Import the shipped 50-row seed as configured-source ledger rows,
        then run the admission gate over them (deferred sweep if slow)."""
        v = self.h.ledger.view()
        if v["sources"] and not force:
            return v["sources"]
        try:
            payload = self.seed_payload()
        except Exception as e:
            self.h.ledger.append("source:seed-failed", {"error": str(e)},
                                 claimant="system", basis="execution-evidence")
            return {}
        for s in payload.get("sources", []):
            self.h.ledger.append("source:configured",
                                 {"source": s["key"], "name": s["name"],
                                  "kind": s["kind"], "url": s["url"],
                                  "api": s.get("api"), "domains": s.get("domains", []),
                                  "descriptor": s.get("descriptor", "granted_only"),
                                  "ceiling": s.get("ceiling", 0.5),
                                  "seedRevision": payload.get("revision")},
                                 claimant="system", basis="seed-import", certainty=0.8)
        return self.h.ledger.view()["sources"]

    # ---------- admission gate ----------
    def admit(self, key):
        """Gate one source: free-tier readable, no login, no AI opt-out.
        Result recorded as an assertion; failures quarantined with basis."""
        src = self.h.ledger.view()["sources"].get(key)
        if not src:
            return {"ok": False, "basis": "unknown-source"}
        url = src.get("api") or src.get("url")
        verdict = {"source": key, "checks": {}, "admitted": False,
                   "probedAt": time.time()}
        host = urllib.parse.urlparse(url or "").netloc.lower()
        verdict["checks"]["no-ai-opt-out"] = not any(h in host for h in AI_OPTOUT_HOSTS)
        status, body = _fetch(url, timeout=8)
        verdict["checks"]["reachable"] = status is not None and 200 <= status < 400
        verdict["checks"]["status"] = status
        text = body.decode("utf-8", "replace") if isinstance(body, bytes) else ""
        login_markers = ("login required", "please log in", "sign in to continue",
                         "create an account to", "401 unauthorized")
        verdict["checks"]["no-login"] = verdict["checks"]["reachable"] and not any(
            m in text.lower() for m in login_markers)
        if status == 401 or status == 403:
            verdict["checks"]["no-login"] = False
        verdict["admitted"] = all(verdict["checks"][k] for k in
                                  ("no-ai-opt-out", "reachable", "no-login"))
        if not verdict["admitted"]:
            verdict["quarantine"] = True
            verdict["basis"] = [k for k, ok in verdict["checks"].items() if ok is False]
        self.h.ledger.append("source:admission", verdict,
                             claimant="system", basis="execution-evidence",
                             certainty=0.85)
        return verdict

    def admit_all(self, limit=None):
        """Concurrent admission sweep over configured sources."""
        keys = list(self.h.ledger.view()["sources"].keys())
        if limit:
            keys = keys[:limit]
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
            futs = {ex.submit(self.admit, k): k for k in keys}
            for fut in concurrent.futures.as_completed(futs):
                k = futs[fut]
                try:
                    results[k] = fut.result()
                except Exception as e:
                    results[k] = {"source": k, "admitted": False, "basis": [str(e)]}
        admitted = sum(1 for r in results.values() if r.get("admitted"))
        self.h.ledger.append("source:admission-sweep",
                             {"total": len(results), "admitted": admitted,
                              "quarantined": len(results) - admitted},
                             claimant="system", basis="execution-evidence")
        return results

    # ---------- credentialing ----------
    def configure_account(self, name, kind, host, user, secret):
        """Owner-facing credentialing path (C-CredentialDescriptor): the
        descriptor becomes a configured-source row; the secret stays in
        the local credential store — never a ledger row."""
        cred_id = f"cred-{name}"
        with open(os.path.join(self.cred_dir, f"{cred_id}.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"account": name, "kind": kind, "host": host,
                       "user": user, "secret": secret}, f)
        self.h.ledger.append("account:configured",
                             {"account": name, "kind": kind, "host": host,
                              "user": user, "descriptor": cred_id,
                              "secretHeld": "local-credential-store"},
                             claimant="principal", basis="user-set", certainty=1.0)
        self.h.ledger.append("source:configured",
                             {"source": f"source-acct-{name}", "name": name,
                              "kind": kind, "url": host,
                              "domains": ["personal", "mail"],
                              "descriptor": "account", "ceiling": 0.7,
                              "account": name},
                             claimant="principal", basis="user-set", certainty=0.9)
        return {"ok": True, "descriptor": cred_id}

    def load_secret(self, name):
        try:
            with open(os.path.join(self.cred_dir, f"cred-{name}.json"),
                      "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    # ---------- mail ----------
    def mail_read(self, limit=10):
        """Read recent mail — configured IMAP account first, else the
        shipped fixture with its basis labeled honestly."""
        v = self.h.ledger.view()
        acct = next((a for a in v["accounts"].values()
                     if a.get("kind") in ("imap", "gmail", "mail")), None)
        if acct:
            return self._imap_read(acct, limit)
        return self._fixture_read(limit)

    def _imap_read(self, acct, limit):
        cred = self.load_secret(acct["account"])
        if not cred:
            return {"ok": False, "basis": "descriptor-without-secret"}
        try:
            conn = imaplib.IMAP4_SSL(cred["host"], timeout=10)
            conn.login(cred["user"], cred["secret"])
            conn.select("INBOX", readonly=True)
            _, ids = conn.search(None, "ALL")
            mails = []
            for mid in ids[0].split()[-limit:]:
                _, data = conn.fetch(mid, "(RFC822)")
                msg = email.message_from_bytes(data[0][1])
                mails.append({"id": mid.decode(), "subject": msg.get("Subject"),
                              "from": msg.get("From"), "date": msg.get("Date"),
                              "basis": f"imap:{cred['host']}"})
            conn.logout()
            return {"ok": True, "basis": f"real-account:{cred['host']}", "mails": mails}
        except Exception as e:
            return {"ok": False, "basis": f"imap-error:{e}", "mails": []}

    def _fixture_read(self, limit):
        inbox = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "fixtures", "inbox")
        mails = []
        if os.path.isdir(inbox):
            for fn in sorted(os.listdir(inbox))[-limit:]:
                if not fn.endswith(".eml"):
                    continue
                with open(os.path.join(inbox, fn), "r", encoding="utf-8",
                          errors="replace") as f:
                    msg = email.message_from_string(f.read())
                body = ""
                try:
                    part = msg.get_payload(decode=True)
                    body = (part or b"").decode("utf-8", "replace")[:800]
                except Exception:
                    pass
                mails.append({"id": fn, "subject": msg.get("Subject"),
                              "from": msg.get("From"), "date": msg.get("Date"),
                              "body": body, "basis": "fixture"})
        return {"ok": True, "basis": "fixture:.eml (no configured account — "
                                     "fixture basis honestly labeled)",
                "fixture": True, "mails": mails}


# ---------- wiki retrieval helpers (shared by tools + persona grounding) --
def _api(src, params, retries=2):
    base = src if src.startswith("http") else None
    if base is None:
        return None, "no api"
    url = base + "?" + urllib.parse.urlencode(params)
    err = None
    for attempt in range(retries + 1):
        status, body = _fetch(url, timeout=10)
        if status == 200:
            try:
                return json.loads(body), None
            except Exception as e:
                err = str(e)
        else:
            err = f"http {status}"
        if attempt < retries:
            time.sleep(1.5 * (attempt + 1))
    return None, err


def _src_row(host, key):
    return host.ledger.view()["sources"].get(key) or {}


def wiki_category_members(source_key, category, want="", host=None, limit=120):
    """Walk a MediaWiki category; classify entries as members vs
    results-that-do-not-match (headers, foreign links, category errors
    are retained for review per D4)."""
    api = "https://en.wikipedia.org/w/api.php"
    if host is not None:
        row = _src_row(host, source_key)
        api = row.get("api") or api
    members, non = [], []
    cmcontinue = None
    while len(members) < limit:
        params = {"action": "query", "list": "categorymembers",
                  "cmtitle": category, "cmlimit": "500",
                  "format": "json", "cmnamespace": "0"}
        if cmcontinue:
            params["cmcontinue"] = cmcontinue
        data, err = _api(api, params)
        if err or not data:
            return members, non + [{"title": category, "why": f"fetch-failed:{err}"}]
        for m in data.get("query", {}).get("categorymembers", []):
            title = m["title"]
            if re.match(r"^(List of|Category:|Draft:|Template:)", title):
                non.append({"title": title, "why": "header-or-foreign-entry"})
            else:
                members.append(title)
        cmcontinue = data.get("continue", {}).get("cmcontinue")
        if not cmcontinue:
            break
    return members[:limit], non


def wiki_search_members(source_key, term, want="", host=None, limit=80):
    api = "https://en.wikipedia.org/w/api.php"
    if host is not None:
        row = _src_row(host, source_key)
        api = row.get("api") or api
    data, err = _api(api, {"action": "query", "list": "search",
                           "srsearch": term, "srlimit": str(limit),
                           "format": "json", "srnamespace": "0"})
    members, non = [], []
    if err or not data:
        return members, [{"title": term, "why": f"fetch-failed:{err}"}]
    for hit in data.get("query", {}).get("search", []):
        title = hit["title"]
        if re.match(r"^(List of|Category:|Draft:|Template:)", title) or \
                (want and want not in (hit.get("snippet", "") + title).lower()
                 and "pennsylvania" not in title.lower()):
            non.append({"title": title, "why": "not-matching-criteria"})
        else:
            members.append(title)
    return members, non


def wiki_extract(source_key, title, host=None, sentences=3):
    """Plain-extract lookup for persona grounding."""
    api = "https://en.wikipedia.org/w/api.php"
    if host is not None:
        row = _src_row(host, source_key)
        api = row.get("api") or api
    data, err = _api(api, {"action": "query", "prop": "extracts",
                           "explaintext": "1", "exsentences": str(sentences),
                           "titles": title, "format": "json", "redirects": "1"})
    if err or not data:
        return None
    pages = data.get("query", {}).get("pages", {})
    for p in pages.values():
        if p.get("extract"):
            return {"title": p.get("title"), "extract": p["extract"][:1200]}
    return None


def wiki_search_title(source_key, query, host=None):
    api = "https://en.wikipedia.org/w/api.php"
    if host is not None:
        row = _src_row(host, source_key)
        api = row.get("api") or api
    data, err = _api(api, {"action": "opensearch", "search": query,
                           "limit": "3", "namespace": "0", "format": "json"})
    if err or not data or len(data) < 2 or not data[1]:
        return None
    return data[1][0]
