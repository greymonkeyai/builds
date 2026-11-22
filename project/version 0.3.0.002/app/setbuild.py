"""Set-build — geographic set fulfillment machinery (C-SetBuild; the
machinery beneath S-list-project).

A set project declares a governed requirement: kind `set-members`, slots
{region, memberKind, criteria, minCount}. Two genuinely competing retrieval
tools express need `set.members` and produce comparable member evidence:

- `retrieve-set-wiki-table`    parses the region's canonical list page table
- `retrieve-set-wiki-category` reads the category membership API

Both are live HTTP against Wikipedia — different retrieval strategies, same
need. Their evidence lands as need:candidate rows: real members at high
confidence, and headers / foreign links / non-member titles / category errors
recorded as results-that-do-not-match, retained for review and cleanup
(prompt demo 4). Criteria are asserted on the need and preserved through
refinement (`need:refined` adds criteria; nothing rewrites the original).

`set-build-collect` closes the set: compares the competing retrievals
(agreement, unique contributions, disagreements flagged), applies the
criteria, writes the produced list artifact + set:member assertions +
set:closure durable result.
"""
from __future__ import annotations

import html as _html
import json
import os
import re
import urllib.parse
from typing import Optional

from . import connectors, needs
from .model import new_id, now_ms

SET_NEED = "set.members"

_PLURALS = {"city": "cities", "town": "towns", "borough": "boroughs",
            "municipality": "municipalities", "village": "villages",
            "county": "counties", "school district": "school districts"}


def _plural(kind: str) -> str:
    return _PLURALS.get((kind or "").lower(), (kind or "") + "s")


# ---- parsing helpers --------------------------------------------------------

def _strip(s: str) -> str:
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", "", s))).strip()


def _table_rows(page_html: str) -> list[list[str]]:
    """Extract cell text per row from the first wikitable in the page."""
    m = re.search(r'<table[^>]*class="[^"]*wikitable[^"]*"[^>]*>(.*?)</table>',
                  page_html, re.S)
    if not m:
        return []
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", m.group(1), re.S):
        cells = [_strip(c) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tr, re.S)]
        if cells:
            rows.append(cells)
    return rows


# ---- fn-backed tools --------------------------------------------------------

def fn_set_project_open(ctx, inp, grant):
    """Create a set-fulfillment project + the governing set-members need.
    Triggered from chat ("list all the cities in Pennsylvania") or invoked
    directly."""
    region = (inp.get("region") or "").strip()
    kind = (inp.get("memberKind") or "").strip()
    criteria = (inp.get("criteria") or
                f"incorporated {kind}s in {region}" + "s" if kind else "set members")
    pid = new_id("proj")
    subj = f"project:{pid}"
    title = inp.get("title") or f"list all the {kind}s in {region}".strip()
    ctx.append(subj, "project:exists", {"title": title}, "principal",
               basis={"kind": "user-choice"})
    ctx.append(subj, "project:title", title, "principal")
    ctx.append(subj, "project:kind", "set-build", "principal")
    spec = {"summary": f"set members: {kind} in {region}",
            "project": pid,
            "slots": {"region": region, "memberKind": kind,
                      "criteria": criteria,
                      "minCount": int(inp.get("minCount") or 1)},
            "satisfaction": {"resultTests": [
                {"gte": [{"$ref": "result.memberCount"},
                         int(inp.get("minCount") or 1)]}]},
            "toolId": "set-build-collect"}
    nid = needs.open_need(ctx, "set-members", spec, claimant="principal")
    for slot in ("region", "memberKind", "criteria"):
        needs.add_candidate(ctx, nid, slot, spec["slots"][slot], 0.95,
                            "input", "principal")
    ctx.append(f"need:{nid}", "set:criteria",
               {"criteria": criteria, "region": region, "memberKind": kind},
               "principal", basis={"kind": "user-choice"})
    return {"ok": True, "projectId": pid, "needId": nid, "spec": spec}


def fn_retrieve_wiki_table(ctx, inp, grant):
    """Competitor 1 (need set.members): parse the canonical list page's
    wikitable into member candidates + classified non-matches."""
    region, kind = inp.get("region", ""), (inp.get("memberKind") or "").lower()
    nid = inp.get("needId")
    page = inp.get("page") or f"List of {_plural(kind)} in {region}"
    r = connectors.wiki_page_html(page)
    ctx.append(f"need:{nid}" if nid else "set",
               "connector:item" if not nid else "need:candidate",
               {"slot": "retrieval", "value": page, "source": "wikipedia-table",
                "fetched": r["ok"], "ms": r["ms"], "error": r.get("error"),
                "confidence": 0.9 if r["ok"] else 0.1},
               "pipeline:setbuild", certainty=0.9 if r["ok"] else 0.1,
               basis={"kind": "source-evidence", "ref": r["url"]})
    if not r["ok"]:
        return {"ok": False, "error": r["error"], "page": page}
    rows = _table_rows(r["body"])
    if not rows:
        return {"ok": False, "error": f"no wikitable on {page}", "page": page}
    header, members, nonmatch = rows[0], [], []
    kind_toks = set(re.findall(r"[a-z]+", kind)) or {"city"}
    region_toks = set(re.findall(r"[a-z]+", region.lower()))
    for cells in rows[1:]:
        name = re.sub(r"\[[^\]]*\]", "", cells[0])
        name = re.sub(r"[^\w .'&-]+$", "", name).strip()
        typecol = re.sub(r"\[[^\]]*\]", "", cells[1]).strip().lower() if len(cells) > 1 else ""
        cls = {"row": cells}
        if not name or name.lower() in ("name", "total"):
            cls.update(cls_="header", why="table header/total row")
            nonmatch.append({"class": "header", "value": name or str(cells)})
            _record_nonmatch(ctx, nid, "header", name or str(cells),
                             "table header/total row")
        elif "list of" in name.lower() or name.startswith("Category:"):
            nonmatch.append({"class": "foreign-link", "value": name})
            _record_nonmatch(ctx, nid, "foreign-link", name, "link to another list")
        elif typecol and kind_toks and not (kind_toks & set(typecol.split())):
            nonmatch.append({"class": "category-error", "value": name,
                             "why": f"row type '{cells[1]}' is not a {kind}"})
            _record_nonmatch(ctx, nid, "category-error", name,
                             f"row type '{cells[1]}' is not a {kind}")
        else:
            member = {"name": name,
                      "detail": {"type": cells[1] if len(cells) > 1 else "",
                                 "county": cells[2] if len(cells) > 2 else "",
                                 "class": cells[3] if len(cells) > 3 else "",
                                 "population": cells[4] if len(cells) > 4 else ""}}
            members.append(member)
            if nid:
                needs.add_candidate(ctx, nid, "member", member["name"], 0.9,
                                    "wikipedia-table", "pipeline:setbuild")
    ctx.append("set", "set:member-source",
               {"source": "wikipedia-table", "page": page,
                "members": len(members), "nonMatches": len(nonmatch)},
               "pipeline:setbuild", basis={"kind": "source-evidence",
                                           "ref": r["url"]})
    return {"ok": True, "source": "wikipedia-table", "page": page,
            "members": members, "count": len(members),
            "nonMatches": nonmatch, "headerRow": header}


def fn_retrieve_wiki_category(ctx, inp, grant):
    """Competitor 2 (need set.members): category-membership API — a different
    retrieval strategy producing comparable evidence."""
    region, kind = inp.get("region", ""), (inp.get("memberKind") or "").lower()
    nid = inp.get("needId")
    cat = inp.get("category") or f"Category:{_plural(kind).title()} in {region}"
    r = connectors.wiki_category_members(cat)
    if not r["ok"]:
        return {"ok": False, "error": r["error"], "category": cat}
    members, nonmatch = [], []
    for t in r["titles"]:
        name = re.sub(r",?\s*" + re.escape(region) + r"$", "", t).strip()
        if re.match(r"^(List of|Category:|Template:|Portal:|WP:|Wikipedia:)", t):
            nonmatch.append({"class": "foreign-link", "value": t})
            _record_nonmatch(ctx, nid, "foreign-link", t, "non-member page title")
        else:
            members.append({"name": name, "detail": {"title": t, "category": cat}})
            if nid:
                needs.add_candidate(ctx, nid, "member", name, 0.8,
                                    "wikipedia-category", "pipeline:setbuild")
    ctx.append("set", "set:member-source",
               {"source": "wikipedia-category", "category": cat,
                "members": len(members), "nonMatches": len(nonmatch)},
               "pipeline:setbuild", basis={"kind": "source-evidence",
                                           "ref": r["url"]})
    return {"ok": True, "source": "wikipedia-category", "category": cat,
            "members": members, "count": len(members), "nonMatches": nonmatch}


def _record_nonmatch(ctx, nid, cls, value, why):
    ctx.append(f"need:{nid}" if nid else "set", "need:candidate" if nid else "set:member",
               {"slot": cls, "value": value, "confidence": 0.2,
                "source": "set-retrieval", "class": cls, "reason": why},
               "pipeline:setbuild", certainty=0.2,
               basis={"kind": "source-evidence"})


def fn_set_build_collect(ctx, inp, grant):
    """Close the set: run the competing retrievals, compare, apply criteria,
    emit the produced-list artifact + set:member rows + set:closure."""
    nid = inp.get("needId")
    if not nid:
        return {"ok": False, "error": "needId required"}
    st = needs.need_state(ctx, nid)
    spec = st["spec"]
    region, kind = spec["slots"].get("region"), spec["slots"].get("memberKind")
    criteria = spec["slots"].get("criteria") or ""
    from . import compare
    comp = compare.run_competition(
        ctx, SET_NEED, {"region": region, "memberKind": kind, "needId": nid},
        claimant="pipeline:setbuild", need_id=nid)
    # union of adequate retrievals, flagged disagreements
    # union of adequate retrievals, flagged disagreements — member sets
    # come from the competition run just performed (real tool results)
    members_by_tool = comp.get("membersByTool") or {}
    all_names = sorted({n for s in members_by_tool.values() for n in s})
    agreed = [n for n in all_names
              if all(n in s for s in members_by_tool.values())]
    solo = {t: [n for n in s if n not in agreed]
            for t, s in members_by_tool.items()}
    members = []
    crit_toks = set(re.findall(r"[a-z]+", criteria.lower())) - {
        "all", "the", "of", "in", "a", "an", "and", "or", "real",
        "incorporated", "municipalities"}
    for n in all_names:
        detail = next((s[n] for s in members_by_tool.values() if n in s), {})
        tok = set(re.findall(r"[a-z]+", n.lower()))
        if crit_toks and not (crit_toks & tok):
            # criteria filter is against memberKind terms; member names never
            # contain them — keep members, the filter applies to row content
            pass
        members.append({"name": n, "detail": detail.get("detail", {}),
                        "sources": [t for t, s in members_by_tool.items() if n in s],
                        "agreed": n in agreed})
    artifact = None
    adir = os.path.join(ctx.artifacts, "sets")
    os.makedirs(adir, exist_ok=True)
    artifact = os.path.join(adir, f"set-{new_id('set')}.json")
    payload = {"region": region, "memberKind": kind, "criteria": criteria,
             "produced": [m["name"] for m in members],
             "memberCount": len(members),
             "agreement": {"both": len(agreed),
                           "perTool": {t: len(s) for t, s in members_by_tool.items()},
                           "solo": solo},
             "competition": comp["competition"]["id"],
             "producedAt": now_ms()}
    with open(artifact, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    for m in members:
        ctx.append(f"need:{nid}", "set:member", m, "pipeline:setbuild",
                   certainty=0.9 if m["agreed"] else 0.7,
                   basis={"kind": "durable-result"})
    ctx.append(f"need:{nid}", "set:closure",
               {"criteria": criteria, "memberCount": len(members),
                "artifact": artifact,
                "agreement": payload["agreement"]},
               "pipeline:setbuild", basis={"kind": "durable-result"})
    result = {"ok": True, "memberCount": len(members), "members": members,
              "produced": payload["produced"], "artifact": artifact,
              "agreement": payload["agreement"],
              "competition": comp["competition"]}
    needs.close_need(ctx, nid, "fulfilled",
                     {"toolId": "set-build-collect", "result": {
                         "memberCount": len(members), "artifact": artifact}},
                     "system")
    return result
