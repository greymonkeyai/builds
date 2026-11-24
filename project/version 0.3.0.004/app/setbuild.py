"""Set fulfillment (C-SetBuild / C-SpecializedListRetrieval).
Geographic set answers are built by specialized retrieval, not general
search. For "all the cities in Pennsylvania" two genuinely competing
strategies express the same `set.members` need:
- retrieve-set-wiki-table — parses the municipalities wikitable and filters
  the class column to City (row-level classification)
- retrieve-set-wiki-category — traverses Category:Cities in Pennsylvania
  (set-membership retrieval)
Both are adequate: results are unioned, agreement/disagreement recorded,
non-matches (headers, foreign links, class errors) retained as reviewable
`need:candidate` rows, and a `set:closure` + list artifact seals the run.
"""
from __future__ import annotations
import json
import os
import re
from . import model
PA_TABLE = "List of municipalities in Pennsylvania"
PA_CATEGORY = "Category:Cities in Pennsylvania"
def _clean_name(title: str) -> str:
    t = re.sub(r",\s*Pennsylvania$", "", title).strip()
    return t
def via_table(ctx, criteria: str) -> dict:
    """Wikitable strategy: fetch the municipalities table wikitext, parse
    rows, keep class == city, classify the rest as non-matches."""
    w = ctx.wiki
    r = w.wikitext(PA_TABLE)
    if not r.get("ok"):
        return {"ok": False, "error": r.get("error"), "strategy": "table"}
    rows = re.findall(
        r"\|\s*\d+\|\|\[\[([^\]|]+)(?:\|[^\]]+)?\]\]([^|]*)\|\|", r["text"])
    members, non = [], []
    for name, klass in rows:
        k = klass.strip().lower().replace("†", "").split("(")[0].strip()
        name = _clean_name(name)
        if k == "city":
            members.append(name)
        elif k in ("borough", "township", "town"):
            non.append({"name": name, "class": "class-error",
                        "detail": f"table class '{k}' is not a city"})
    return {"ok": True, "strategy": "table", "members": members,
            "nonMatches": non, "source": PA_TABLE}
def via_category(ctx, criteria: str) -> dict:
    """Category strategy: traverse the category as a set. Header/list pages
    and foreign links are non-matches, retained for review."""
    w = ctx.wiki
    r = w.category_members(PA_CATEGORY)
    if not r.get("ok"):
        return {"ok": False, "error": r.get("error"),
                "strategy": "category"}
    members, non = [], []
    for title in r.get("members", []):
        if title.lower().startswith("list of"):
            non.append({"name": title, "class": "header",
                        "detail": "list/header page is not a member"})
        elif "sister" in title.lower():
            non.append({"name": title, "class": "foreign-link",
                        "detail": "sister-city relation is not a PA city"})
        elif "(disambiguation)" in title.lower():
            non.append({"name": title, "class": "ambiguous",
                        "detail": "disambiguation page"})
        else:
            members.append(_clean_name(title))
    return {"ok": True, "strategy": "category", "members": members,
            "nonMatches": non, "source": PA_CATEGORY}
def build(ctx, criteria: str, need_id: str = None) -> dict:
    """Full set fulfillment: competing retrievals unioned, criteria preserved,
    non-matches retained for review and cleanup (prompt demo 4)."""
    led = ctx.ledger
    results = [via_table(ctx, criteria), via_category(ctx, criteria)]
    ok_results = [r for r in results if r.get("ok")]
    if not ok_results:
        return {"ok": False, "error": "all retrieval strategies failed",
                "detail": results}
    sets = {r["strategy"]: set(r["members"]) for r in ok_results}
    union = sorted(set().union(*sets.values()))
    agreement = {
        "both": sorted(sets.get("table", set()) & sets.get("category", set())),
        "only-table": sorted(sets.get("table", set())
                             - sets.get("category", set())),
        "only-category": sorted(sets.get("category", set())
                                - sets.get("table", set())),
    }
    subj = f"need:{need_id}" if need_id else "set:run"
    # retain every retrieval as candidate rows; non-matches stay inspectable
    for r in ok_results:
        led.say(subj, "set:retrieval",
                {"strategy": r["strategy"], "count": len(r["members"]),
                 "source": r["source"]},
                claimant="source:wikipedia", certainty=0.85,
                basis={"kind": "source-evidence"})
        for nm in r.get("nonMatches", []):
            led.say(subj, "need:candidate",
                    {"slot": "member", "value": nm["name"], "adequate": False,
                     "class": nm["class"], "detail": nm["detail"],
                     "strategy": r["strategy"]},
                    claimant="source:wikipedia", certainty=0.5,
                    basis={"kind": "source-evidence"})
    # disagreement members are candidates too — inspectable until selected
    for name in agreement["only-table"] + agreement["only-category"]:
        side = "only-table" if name in agreement["only-table"] \
            else "only-category"
        led.say(subj, "need:candidate",
                {"slot": "member", "value": name, "adequate": True,
                 "class": "single-source", "detail":
                 f"returned by {side} strategy only"},
                claimant="source:wikipedia", certainty=0.6,
                basis={"kind": "source-evidence"})
    # artifact: the produced list is a durable file under runtime/artifacts
    outdir = os.path.join(ctx.runtime, "artifacts", "lists")
    os.makedirs(outdir, exist_ok=True)
    fname = f"set-{model.rid('list')}.json"
    path = os.path.join(outdir, fname)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"criteria": criteria, "members": union,
                   "memberCount": len(union), "agreement": agreement,
                   "strategies": [r["strategy"] for r in ok_results]},
                  f, indent=2, ensure_ascii=False)
    led.say(subj, "set:closure",
            {"criteria": criteria, "memberCount": len(union),
             "agreeBoth": len(agreement["both"]),
             "disputed": len(agreement["only-table"])
                        + len(agreement["only-category"]),
             "artifact": path},
            claimant="system", certainty=1.0,
            basis={"kind": "durable-result"})
    return {"ok": True, "members": union, "memberCount": len(union),
            "agreement": agreement, "artifact": path,
            "strategies": [r["strategy"] for r in ok_results],
            "nonMatchCount": sum(len(r.get("nonMatches", []))
                                 for r in ok_results)}
