"""Connector framework + the cycle's connector set (F8 — owner scope: 3 real,
runnable connectors end-to-end; recorded challenge to C-ConnectorSet's
17-connector catalog — narrower set delivered on owner ruling, machinery is
general).

A connector is a configured source adapter: it pulls external material and
emits it as `source-evidence` assertions with provenance, and records each run
under `connector:run` — honest failures included (no ok:true-while-failing;
an unreachable remote connector reports `error`, never fabricated items).

Connectors this build:
- `wikipedia`      live HTTP — page fetch, category members, page summary,
                   title search. Backs set-build retrieval, search fan-out,
                   and ethics-gate liveness research.
- `ics-calendar`   local file — ingest a .ics path into calendar:event evidence
                   (the temporal reasoning pipeline's source side).
- `files`          local directory — enumerate + fingerprint + excerpt files
                   into source-evidence (document corpus ingestion).
- `rss`            live HTTP — feed fetch → item entries as source evidence.

Each connector exposes `run(ctx, inp)` returning {ok, items|error, ms}.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Optional

from .model import new_id, now_ms

UA = "Meridian/0.3.0.002 (local-first ledger; research fetch)"


def http_get(url: str, timeout: float = 12.0,
             accept: str = "text/html,application/json,*/*") -> dict:
    """Honest HTTP fetch: returns {ok, body|error, status, url, ms}."""
    t0 = now_ms()
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": UA, "Accept": accept})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", "replace")
            return {"ok": True, "body": body, "status": getattr(r, "status", 200),
                    "url": url, "ms": now_ms() - t0}
    except Exception as e:
        return {"ok": False, "error": repr(e), "url": url, "ms": now_ms() - t0}


# ============================ connector registry ============================

def configured(ctx) -> list[dict]:
    """Configured connectors: connector:configured assertions on
    subject connector:<id>."""
    out = []
    for a in ctx.ledger.query(predicate="connector:configured"):
        v = a.value["v"]
        cid = a.subjectKey.split(":", 1)[1]
        if cid in CONNECTORS:
            out.append({"id": cid, **v, "assertionId": a.id})
    return out


def status(ctx) -> list[dict]:
    """Each configured connector with its last run record (honest status)."""
    out = []
    for c in configured(ctx):
        runs = ctx.ledger.query(subject=f"connector:{c['id']}",
                                predicate="connector:run")
        out.append({**c, "lastRun": runs[-1].value["v"] if runs else None})
    return out


def configure(ctx, cid: str, locator: str, claimant: str = "principal",
              trust: float = 0.8, extra: Optional[dict] = None) -> dict:
    if cid not in CONNECTORS:
        return {"ok": False, "error": f"unknown connector: {cid}",
                "known": sorted(CONNECTORS)}
    v = {"locator": locator, "configuredAt": now_ms(), "trust": trust}
    if extra:
        v.update(extra)
    ctx.append(f"connector:{cid}", "connector:configured", v, claimant,
               basis={"kind": "config"})
    ctx.append(f"source:{cid}", "source:configured",
               {"kind": CONNECTORS[cid]["kind"], "locator": locator},
               claimant, basis={"kind": "config"})
    ctx.append(f"source:{cid}", "source:trust-class", "configured",
               claimant, basis={"kind": "config"})
    ctx.append(f"source:{cid}", "source:confidence", trust,
               claimant, basis={"kind": "config"})
    return {"ok": True, "connector": cid, "locator": locator}


def run(ctx, cid: str, inp: Optional[dict] = None,
        claimant: str = "steward:main") -> dict:
    """Execute a connector ingest end-to-end; record connector:run honestly."""
    spec = CONNECTORS.get(cid)
    if not spec:
        return {"ok": False, "error": f"unknown connector: {cid}"}
    cfg_rows = ctx.ledger.query(subject=f"connector:{cid}",
                                predicate="connector:configured")
    cfg = cfg_rows[-1].value["v"] if cfg_rows else {}
    args = dict(cfg.get("args") or {})
    args.update(inp or {})
    if not args.get("locator"):
        args["locator"] = cfg.get("locator")
    t0 = now_ms()
    try:
        res = spec["run"](ctx, args)
    except Exception as e:
        res = {"ok": False, "error": repr(e)}
    res.setdefault("ms", now_ms() - t0)
    ctx.append(f"connector:{cid}", "connector:run",
               {"ok": bool(res.get("ok")), "items": res.get("items"),
                "error": res.get("error"), "ms": res["ms"],
                "locator": args.get("locator")},
               "pipeline:connector", basis={"kind": "execution"})
    return res


# ============================ wikipedia (live HTTP) ==========================

def _wiki_api(params: dict, timeout: float = 15.0) -> dict:
    qs = urllib.parse.urlencode({**params, "format": "json"})
    r = http_get("https://en.wikipedia.org/w/api.php?" + qs,
                 timeout=timeout, accept="application/json")
    if not r["ok"]:
        return r
    try:
        return {"ok": True, "data": json.loads(r["body"]), "ms": r["ms"],
                "url": r["url"]}
    except Exception as e:
        return {"ok": False, "error": f"bad JSON: {e}", "url": r["url"]}


def wiki_category_members(title: str, limit: int = 400) -> dict:
    r = _wiki_api({"action": "query", "list": "categorymembers",
                   "cmtitle": title if title.startswith("Category:") else
                              "Category:" + title,
                   "cmlimit": limit, "cmtype": "page"})
    if not r["ok"]:
        return r
    members = [m["title"] for m in r["data"].get("query", {}).get("categorymembers", [])]
    return {"ok": True, "titles": members, "url": r["url"], "ms": r["ms"]}


def wiki_page_html(title: str) -> dict:
    return http_get("https://en.wikipedia.org/wiki/" +
                    urllib.parse.quote(title.replace(" ", "_")))


def wiki_summary(title: str) -> dict:
    r = http_get("https://en.wikipedia.org/api/rest_v1/page/summary/" +
                 urllib.parse.quote(title.replace(" ", "_")),
                 accept="application/json")
    if not r["ok"]:
        return r
    try:
        d = json.loads(r["body"])
        return {"ok": True, "title": d.get("title"),
                "extract": d.get("extract", ""), "type": d.get("type"),
                "url": r["url"]}
    except Exception as e:
        return {"ok": False, "error": f"bad summary JSON: {e}"}


def wiki_search(query: str, limit: int = 8) -> dict:
    r = http_get("https://en.wikipedia.org/w/rest.php/v1/search/title?q=" +
                 urllib.parse.quote(query) + f"&limit={limit}",
                 accept="application/json")
    if not r["ok"]:
        return r
    try:
        d = json.loads(r["body"])
        return {"ok": True, "hits": [{"title": p.get("title"),
                                      "excerpt": re.sub(r"<[^>]+>", "",
                                                        p.get("excerpt", ""))}
                                     for p in d.get("pages", [])]}
    except Exception as e:
        return {"ok": False, "error": f"bad search JSON: {e}"}


def _run_wikipedia(ctx, args: dict) -> dict:
    """Ingest a wikipedia source: `search` (title search), `summary` (page
    summary) or `category` (members). Results become source-evidence."""
    mode = args.get("mode", "search")
    q = args.get("query") or args.get("locator") or ""
    if mode == "summary":
        r = wiki_summary(q)
        if not r["ok"]:
            return r
        ctx.append("wikipedia", "connector:item",
                   {"mode": mode, "title": r["title"], "extract": r["extract"][:600]},
                   "source:wikipedia", certainty=0.85,
                   basis={"kind": "source-evidence", "ref": r["url"]})
        return {"ok": True, "items": 1, "title": r["title"]}
    if mode == "category":
        r = wiki_category_members(q)
        if not r["ok"]:
            return r
        for t in r["titles"]:
            ctx.append("wikipedia", "connector:item",
                       {"mode": mode, "title": t, "category": q},
                       "source:wikipedia", certainty=0.8,
                       basis={"kind": "source-evidence", "ref": r["url"]})
        return {"ok": True, "items": len(r["titles"])}
    r = wiki_search(q)
    if not r["ok"]:
        return r
    for h in r["hits"]:
        ctx.append("wikipedia", "connector:item",
                   {"mode": mode, "query": q, **h},
                   "source:wikipedia", certainty=0.75,
                   basis={"kind": "source-evidence", "ref": "wikipedia:" + h["title"]})
    return {"ok": True, "items": len(r["hits"]), "hits": r["hits"]}


# ============================ ics-calendar (local file) ======================

def _run_ics(ctx, args: dict) -> dict:
    path = args.get("locator")
    if not path or not os.path.isfile(path):
        return {"ok": False, "error": f"ics file not found: {path}",
                "locator": path}
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        ics = f.read()
    from .builtins import fn_import_calendar
    r = fn_import_calendar(ctx, {"ics": ics,
                                 "source": f"ics:{os.path.basename(path)}"},
                           None)
    return {"ok": True, "items": r.get("imported", 0), "locator": path}


# ============================ files (local directory) ========================

def _run_files(ctx, args: dict) -> dict:
    d = args.get("locator")
    pattern = args.get("pattern", "*")
    if not d or not os.path.isdir(d):
        return {"ok": False, "error": f"directory not found: {d}", "locator": d}
    import fnmatch
    n = 0
    for name in sorted(os.listdir(d)):
        if not fnmatch.fnmatch(name.lower(), pattern.lower()):
            continue
        fp = os.path.join(d, name)
        if not os.path.isfile(fp):
            continue
        try:
            size = os.path.getsize(fp)
            with open(fp, "rb") as f:
                head = f.read(4096)
            excerpt = head.decode("utf-8", "replace")[:400]
            digest = hashlib.sha256(head).hexdigest()[:16]
        except Exception as e:
            ctx.append("files", "connector:item",
                       {"name": name, "error": repr(e)},
                       "source:files", certainty=0.5,
                       basis={"kind": "source-evidence", "ref": fp})
            continue
        ctx.append("files", "connector:item",
                   {"name": name, "path": fp, "bytes": size,
                    "sha256_4k": digest, "excerpt": excerpt},
                   "source:files", certainty=0.85,
                   basis={"kind": "source-evidence", "ref": fp})
        n += 1
        if n >= int(args.get("max", 25)):
            break
    return {"ok": True, "items": n, "locator": d, "pattern": pattern}


# ============================ rss (live HTTP) ================================

def _run_rss(ctx, args: dict) -> dict:
    url = args.get("locator")
    if not url:
        return {"ok": False, "error": "no feed locator"}
    r = http_get(url, accept="application/rss+xml,application/atom+xml,text/xml,*/*")
    if not r["ok"]:
        return r
    try:
        root = ET.fromstring(r["body"])
    except Exception as e:
        return {"ok": False, "error": f"unparseable feed: {e}", "url": url}
    items = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        date = (it.findtext("pubDate") or it.findtext("date") or "").strip()
        items.append({"title": title, "link": link, "date": date})
    if not items:  # atom
        ns = {"a": "http://www.w3.org/2005/Atom"}
        for it in root.findall("a:entry", ns):
            title = (it.findtext("a:title", "", ns) or "").strip()
            link_el = it.find("a:link", ns)
            items.append({"title": title,
                          "link": link_el.get("href", "") if link_el is not None else "",
                          "date": (it.findtext("a:updated", "", ns) or "").strip()})
    for it in items[: int(args.get("max", 20))]:
        ctx.append("rss", "connector:item",
                   {"feed": url, **it}, "source:rss", certainty=0.75,
                   basis={"kind": "source-evidence", "ref": it.get("link") or url})
    return {"ok": True, "items": len(items), "feed": url,
            "titles": [i["title"] for i in items[:10]]}


CONNECTORS = {
    "wikipedia": {"kind": "remote-api", "title": "Wikipedia (live API/HTML)",
                  "locatorHint": "search query | Category:X | page title",
                  "run": _run_wikipedia},
    "ics-calendar": {"kind": "local-file", "title": "ICS calendar file",
                     "locatorHint": "path to .ics file", "run": _run_ics},
    "files": {"kind": "local-dir", "title": "Local directory ingest",
              "locatorHint": "directory path", "run": _run_files},
    "rss": {"kind": "remote-feed", "title": "RSS/Atom feed",
            "locatorHint": "feed URL", "run": _run_rss},
}
