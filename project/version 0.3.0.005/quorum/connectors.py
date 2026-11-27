"""Quorum connectors — configured sources (C-MultiSourceAccess,
C-CompetingSources, C-SourceCeilings, C-ConfiguredAccounts).

Each connector run is recorded as a ledger assertion; per-source ceilings
bound inherited confidence. Absent connectors are DECLARED, never faked:
no configured mail account exists on this install — the .eml inbox source
is labeled fixture-basis in every surface and evidence file (V-G bar).

Competing-source pair (C-CompetingSources — recorded challenge): the corpus
pair is Wikipedia + Google; this build substitutes Wikipedia + DuckDuckGo
(HTML endpoint, no API key) as the two independent general sources. The
challenge is recorded in FEATURES.md; the convention's intent — two
independent competing general sources — is preserved.
"""
from __future__ import annotations

import email
import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from . import rows

UA = {"User-Agent": "Quorum/0.3.0.005 (local-first install)"}

def http_get(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Wikipedia — live general+specialized source
def wikipedia_summary(topic: str) -> dict:
    try:
        t = urllib.parse.quote(topic.replace(" ", "_"))
        d = json.loads(http_get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{t}", 15))
        return {"ok": True, "title": d.get("title", topic),
                "extract": d.get("extract", "")}
    except Exception as e:
        return {"ok": False, "error": str(e), "extract": ""}

def wikipedia_links(topic: str) -> dict:
    """Link roster of a page — the specialized-list substrate."""
    try:
        t = urllib.parse.quote(topic.replace(" ", "_"))
        d = json.loads(http_get(
            f"https://en.wikipedia.org/w/api.php?action=parse&page={t}"
            f"&prop=links&format=json&formatversion=2", 20))
        links = [l["title"] for l in d.get("parse", {}).get("links", [])
                 if l.get("ns") == 0]
        return {"ok": True, "links": links}
    except Exception as e:
        return {"ok": False, "error": str(e), "links": []}

def wikipedia_table_members(topic: str, member_col_hint="") -> dict:
    """Competing path: parse the HTML table's first text column."""
    try:
        t = urllib.parse.quote(topic.replace(" ", "_"))
        html = http_get(f"https://en.wikipedia.org/wiki/{t}", 20)
        cells = re.findall(r"<td[^>]*>\s*<a[^>]*>([^<]{2,60})</a>", html)
        seen, out = set(), []
        for c in cells:
            c = c.strip()
            if c and c not in seen and not c.startswith("["):
                seen.add(c)
                out.append(c)
        return {"ok": True, "members": out}
    except Exception as e:
        return {"ok": False, "error": str(e), "members": []}

# ---------------------------------------------------------------------------
# DuckDuckGo — the second independent general source (challenge on record)
def ddg_search(query: str, limit: int = 8) -> dict:
    try:
        q = urllib.parse.quote(query)
        html = http_get(f"https://html.duckduckgo.com/html/?q={q}", 15)
        titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', html)
        titles = [re.sub(r"<[^>]+>", "", t).strip() for t in titles][:limit]
        return {"ok": True, "results": titles}
    except Exception as e:
        return {"ok": False, "error": str(e), "results": []}

# ---------------------------------------------------------------------------
# RSS
def rss_titles(feed_url: str, limit: int = 10) -> dict:
    try:
        root = ET.fromstring(http_get(feed_url, 15))
        titles = [i.findtext("title", "") for i in root.iter("item")][:limit]
        if not titles:
            titles = [e.findtext("{http://www.w3.org/2005/Atom}title", "")
                      for e in root.iter("{http://www.w3.org/2005/Atom}entry")][:limit]
        return {"ok": True, "titles": [t for t in titles if t]}
    except Exception as e:
        return {"ok": False, "error": str(e), "titles": []}

# ---------------------------------------------------------------------------
# .eml inbox — fixture-basis declared source (V-G)
def eml_inbox(inbox_dir: str) -> dict:
    """Read a configured DIRECTORY of .eml files. Labeled fixture-basis:
    no live account connector is configured on this install."""
    out = []
    if not os.path.isdir(inbox_dir):
        return {"ok": False, "basis": "fixture", "error": "inbox dir absent",
                "messages": []}
    for fn in sorted(os.listdir(inbox_dir)):
        if not fn.lower().endswith(".eml"):
            continue
        try:
            with open(os.path.join(inbox_dir, fn), "rb") as f:
                m = email.message_from_bytes(f.read())
            body = ""
            if m.is_multipart():
                for part in m.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(
                            "utf-8", errors="replace")
                        break
            else:
                body = m.get_payload(decode=True).decode("utf-8", errors="replace")
            out.append({"file": fn, "from": str(m.get("From", "")),
                        "to": str(m.get("To", "")),
                        "date": str(m.get("Date", "")),
                        "subject": str(m.get("Subject", "")),
                        "body": body[:4000]})
        except Exception as e:
            out.append({"file": fn, "error": str(e)})
    return {"ok": True, "basis": "fixture-directory",
            "note": "FIXTURE BASIS — no configured live mail account on this "
                    "install; .eml directory stands in (declared, V-G)",
            "messages": out}

# ---------------------------------------------------------------------------
# ICS calendar
def ics_events(ics_path_or_url: str) -> dict:
    try:
        text = http_get(ics_path_or_url, 15) if ics_path_or_url.startswith("http") \
            else open(ics_path_or_url, encoding="utf-8").read()
    except Exception as e:
        return {"ok": False, "error": str(e), "events": []}
    events, cur = [], {}
    for line in text.splitlines():
        line = line.strip()
        if line == "BEGIN:VEVENT":
            cur = {}
        elif line == "END:VEVENT":
            events.append(cur)
        elif ":" in line:
            k, v = line.split(":", 1)
            k = k.split(";")[0]
            if k in ("SUMMARY", "DTSTART", "DTEND", "LOCATION", "DESCRIPTION"):
                cur[k.lower()] = v
    return {"ok": True, "events": events}

# Files / misc
def file_source(path: str) -> dict:
    try:
        return {"ok": True, "text": open(path, encoding="utf-8",
                                         errors="replace").read()[:8000]}
    except Exception as e:
        return {"ok": False, "error": str(e), "text": ""}
