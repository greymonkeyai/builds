"""Configured sources — real connectors, honest failures.

Delivered end-to-end: wikipedia (live), ics-calendar (local files), files
(local dir), rss (live), inbox-eml (local .eml dir). OAuth account
connectors (Gmail/Calendar) are a declared absence — never faked.

Every ingest writes `connector:run` evidence; unreachable connectors report
error, they do not fabricate rows (C-DeclaredStubs).
"""
from __future__ import annotations

import email
import email.policy
import hashlib
import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from . import model


UA = {"User-Agent": "Vantage/0.3.0.004 (local-first assistant; stdlib)"}


def _get(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _get_json(url, timeout=20):
    return json.loads(_get(url, timeout).decode("utf-8", "replace"))


def _record(ctx, name, result: dict):
    ctx.ledger.say("connectors", "connector:run",
                   {"connector": name, **result},
                   claimant="source:" + name, certainty=1.0,
                   basis={"kind": "execution"})
    return result


# ---------------------------------------------------------------------------
# wikipedia — backs set retrieval, search fan-out, ethics liveness, facts

class Wikipedia:
    name = "wikipedia"

    def summary(self, title: str) -> dict:
        url = ("https://en.wikipedia.org/api/rest_v1/page/summary/"
               + urllib.parse.quote(title.replace(" ", "_")))
        try:
            d = _get_json(url)
            return {"ok": True, "title": d.get("title"),
                    "extract": d.get("extract", ""),
                    "url": (d.get("content_urls") or {})
                    .get("desktop", {}).get("page")}
        except Exception as e:
            return {"ok": False, "error": repr(e)}

    def search(self, q: str, limit=8) -> dict:
        url = ("https://en.wikipedia.org/w/api.php?action=opensearch&"
               f"search={urllib.parse.quote(q)}&limit={limit}&format=json")
        try:
            d = _get_json(url)
            return {"ok": True, "titles": d[1], "links": d[3]}
        except Exception as e:
            return {"ok": False, "error": repr(e)}

    def category_members(self, cat: str, limit=500) -> dict:
        url = ("https://en.wikipedia.org/w/api.php?action=query&"
               "list=categorymembers&cmtitle=" +
               urllib.parse.quote(cat) +
               f"&cmlimit={limit}&cmtype=page&format=json")
        try:
            d = _get_json(url)
            ms = [m["title"] for m in
                  d.get("query", {}).get("categorymembers", [])]
            return {"ok": True, "members": ms}
        except Exception as e:
            return {"ok": False, "error": repr(e)}

    def wikitext(self, title: str) -> dict:
        url = ("https://en.wikipedia.org/w/index.php?title=" +
               urllib.parse.quote(title.replace(" ", "_")) +
               "&action=raw")
        try:
            return {"ok": True, "text": _get(url, timeout=30)
                    .decode("utf-8", "replace")}
        except Exception as e:
            return {"ok": False, "error": repr(e)}


# ---------------------------------------------------------------------------
# ics calendar files

def import_ics(ctx, ics_text: str, source: str) -> dict:
    events = []
    for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", ics_text,
                            re.S):
        ev = {}
        for line in block.strip().splitlines():
            if ":" not in line:
                continue
            k, v = line.split(":", 1)
            k = k.split(";")[0].strip().upper()
            ev[k] = v.strip()
        if ev.get("SUMMARY"):
            events.append({"summary": ev["SUMMARY"],
                           "start": ev.get("DTSTART", ""),
                           "end": ev.get("DTEND", "")})
    for ev in events:
        ctx.ledger.say("calendar", "calendar:event", ev,
                       claimant="source:" + source, certainty=0.85,
                       basis={"kind": "source-evidence"})
    return _record(ctx, "ics-calendar",
                   {"ok": True, "imported": len(events), "source": source})


# ---------------------------------------------------------------------------
# files directory → source-evidence with sha256 + excerpt

def ingest_files(ctx, directory: str) -> dict:
    if not os.path.isdir(directory):
        return _record(ctx, "files",
                       {"ok": False, "error": f"no dir {directory}"})
    n = 0
    for fn in sorted(os.listdir(directory))[:50]:
        path = os.path.join(directory, fn)
        if not os.path.isfile(path):
            continue
        try:
            data = open(path, "rb").read()
            digest = hashlib.sha256(data).hexdigest()[:16]
            excerpt = data[:400].decode("utf-8", "replace")
            ctx.ledger.say(f"file:{fn}", "file:content",
                           {"path": path, "sha256": digest,
                            "bytes": len(data), "excerpt": excerpt},
                           claimant="source:files", certainty=0.8,
                           basis={"kind": "source-evidence"})
            n += 1
        except Exception:
            pass
    return _record(ctx, "files", {"ok": True, "ingested": n,
                                  "dir": directory})


# ---------------------------------------------------------------------------
# rss feeds

def ingest_rss(ctx, url: str) -> dict:
    try:
        xml = _get(url, timeout=20)
        root = ET.fromstring(xml)
        items = []
        for it in root.iter("item"):
            title = it.findtext("title") or ""
            link = it.findtext("link") or ""
            items.append({"title": title, "link": link})
            ctx.ledger.say("feed", "feed:item",
                           {"title": title, "link": link, "feed": url},
                           claimant="source:rss", certainty=0.7,
                           basis={"kind": "source-evidence"})
        return _record(ctx, "rss", {"ok": True, "items": len(items),
                                    "url": url})
    except Exception as e:
        return _record(ctx, "rss", {"ok": False, "error": repr(e),
                                    "url": url})


# ---------------------------------------------------------------------------
# inbox — real .eml directory ingest (idempotent per file)

def ingest_inbox(ctx, directory: str) -> dict:
    if not os.path.isdir(directory):
        return _record(ctx, "inbox-eml",
                       {"ok": False, "error": f"no dir {directory}"})
    n = 0
    for fn in sorted(os.listdir(directory)):
        if not fn.lower().endswith(".eml"):
            continue
        path = os.path.join(directory, fn)
        try:
            msg = email.message_from_bytes(
                open(path, "rb").read(), policy=email.policy.default)
            subj = msg.get("Subject", "(no subject)")
            sender = msg.get("From", "")
            date = msg.get("Date", "")
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_content()[:1200]
                        break
            else:
                body = msg.get_content()[:1200]
            subj_key = "email:" + hashlib.sha256(
                (path + subj).encode()).hexdigest()[:10]
            already = ctx.ledger.query(subject=subj_key,
                                       predicate="email:message")
            if already:
                continue
            ctx.ledger.say(subj_key, "email:message",
                           {"subject": subj, "from": sender, "date": date,
                            "body": body, "file": fn},
                           claimant="source:inbox-eml", certainty=0.85,
                           basis={"kind": "source-evidence"})
            n += 1
        except Exception as e:
            _record(ctx, "inbox-eml",
                    {"ok": False, "error": f"{fn}: {e!r}"})
    return _record(ctx, "inbox-eml", {"ok": True, "ingested": n,
                                      "dir": directory})


CONNECTORS = {
    "wikipedia": {"title": "Wikipedia (live)", "kind": "live",
                  "note": "summary, search, category, wikitext"},
    "ics-calendar": {"title": "ICS calendar files", "kind": "local"},
    "files": {"title": "Local files directory", "kind": "local"},
    "rss": {"title": "RSS feed", "kind": "live"},
    "inbox-eml": {"title": "Local .eml inbox", "kind": "local"},
    "gmail-oauth": {"title": "Gmail (oauth)", "kind": "declared-absent",
                    "note": "account connectors not configured on this "
                            "installation — declared, not faked"},
}
