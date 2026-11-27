"""Unmet-need floor + tool ontology.
A need is a ledger assertion describing an unfulfilled requirement, governed
by a template (slots, candidate values, tests, satisfaction conditions).
The floor shows only open needs; a met need is marked fulfilled and LEAVES
the open list (C-FloorLifecycle / R-U2).
Tools are persistently identifiable capabilities (tool-as-data): component
id, purpose, input slots, acceptance tests. Needs are met by composing the
minimal existing tool set (tool composition imperative); compositions are
recorded ledger objects, decomposable (S-tool-composition).
"""
import re
from .book import fresh_id, now_iso
from . import sources as src_mod
# ---------------- tools (invokable components) ----------------
# Minimal closed tool set. Needs are met by COMPOSING these — never minting
# bespoke per-need tools where a composition suffices.
TOOLS = {
    "tool.search": {
        "kind": "tool", "purpose": "retrieve candidates from a configured source",
        "inputs": {"query": "required", "source": "optional"},
        "tests": ["result.items nonempty or declared-empty"],
        "explain": "Searches a configured source (mediawiki opensearch / api) "
                   "for a query; returns titled candidates with source."},
    "tool.fetch-page": {
        "kind": "tool", "purpose": "fetch a page extract from a configured source",
        "inputs": {"title": "required", "source": "required"},
        "tests": ["extract present or declared-absent"],
        "explain": "Fetches the plain-text extract for a page title."},
    "tool.list-members": {
        "kind": "tool", "purpose": "enumerate members of a category/set",
        "inputs": {"category": "required", "source": "required",
                   "limit": "optional"},
        "tests": ["members iterable; non-members not included"],
        "explain": "Enumerates category members — specialized set retrieval "
                   "behind defensible list answers."},
    "tool.match-criteria": {
        "kind": "tool", "purpose": "test candidates against list criteria",
        "inputs": {"candidates": "required", "criteria": "required"},
        "tests": ["each candidate judged member | non-match with basis"],
        "explain": "Deterministic match + review: judges each candidate "
                   "against declared criteria; non-matches retained."},
    "tool.compose-text": {
        "kind": "tool", "purpose": "compose text in a persona register",
        "inputs": {"prompt": "required", "register": "optional"},
        "tests": ["conversational sentences; no markup verbatim"],
        "explain": "LLM-composed (or declared-composed) conversational text."},
    "tool.speak": {
        "kind": "tool", "purpose": "render text to speech through the floor",
        "inputs": {"text": "required", "persona": "required"},
        "tests": ["serialized playback; sentence-boundary completion"],
        "explain": "TTS render + serialized floor playback, measured."},
    "tool.render-art": {
        "kind": "tool", "purpose": "author persona-bound art",
        "inputs": {"persona": "required"},
        "tests": ["art bound to persona; authored or declared-fallback"],
        "explain": "LLM-authored SVG portrait; declared fallback binds too."},
    "tool.record": {
        "kind": "tool", "purpose": "record a typed assertion",
        "inputs": {"kind": "required", "claim": "required"},
        "tests": ["row appended with provenance"],
        "explain": "The ledger.append write seam — durable result."},
    "tool.compose-artifact": {
        "kind": "tool", "purpose": "encode a payload as a scannable artifact",
        "inputs": {"payload": "required"},
        "tests": ["decodes literally; CRC verifies"],
        "explain": "Scannable-code encode+decode pair (rastgrid)."},
    "tool.discover": {
        "kind": "tool", "purpose": "map the local network honestly",
        "inputs": {"transports": "optional"},
        "tests": ["everything found recorded incl. non-targets"],
        "explain": "LAN/transport discovery producing a network map."},
}
# A composition is a ledger object naming the minimal component set for a
# need class — decomposable back to components.
COMPOSITIONS = {
    "need:list": ["tool.list-members", "tool.match-criteria", "tool.record"],
    "need:research": ["tool.search", "tool.fetch-page", "tool.record"],
    "need:portrait": ["tool.render-art", "tool.record"],
    "need:scene": ["tool.compose-text", "tool.speak", "tool.render-art",
                   "tool.record"],
    "need:interstitial": ["tool.compose-text", "tool.render-art",
                          "tool.speak", "tool.record"],
    "need:publish": ["tool.compose-artifact", "tool.record"],
}
STOPWORDS = {"list", "of", "all", "the", "in", "a", "an", "and", "or", "for",
             "to", "make", "me", "find", "get", "show", "give", "every",
             "cities", "city", "mountains", "mountain"}
class Needs:
    def __init__(self, host):
        self.host = host
    # ---------- floor ----------
    def open(self, kind, claim, priority=False):
        """Creation does not imply execution; the need is Open until its
        satisfaction conditions are met, or Cancelled/Superseded."""
        claim = dict(claim)
        claim.setdefault("status", "open")
        claim.setdefault("priority", priority)
        claim.setdefault("openedAt", now_iso())
        nid = fresh_id("need")
        claim["needId"] = nid
        row = self.host.book.append(
            kind, claim, claimant=claim.get("claimant", "host"),
            certainty=claim.get("certainty", 0.8), basis="derived")
        row["needId"] = nid
        return row
    def find_open(self, kind=None, subject=None):
        cur = self.host.book.current()
        out = []
        for r in cur:
            if not r["kind"].startswith("need:"):
                continue
            if r["claim"].get("status") not in (None, "open"):
                continue
            if kind and r["kind"] != kind:
                continue
            if subject and r["claim"].get("subject") != subject:
                continue
            out.append(r)
        return out
    def floor(self):
        """Open needs only — the unmet floor."""
        return self.find_open()
    def close(self, row, status, result=None):
        """Fulfilled / cancelled / superseded — a need answered is a need
        closed, marked and removed from the open list."""
        claim = dict(row["claim"])
        claim["status"] = status
        claim["closedAt"] = now_iso()
        if result is not None:
            claim["result"] = result
        return self.host.book.append(
            row["kind"], claim, claimant="host", certainty=row["certainty"],
            basis="execution-evidence", relates=[row["id"]],
            supersedes=row["id"])
    def fulfill(self, row, result=None):
        return self.close(row, "fulfilled", result)
    def focus(self, need_row):
        """Move an unmet need into focus — conversational values fill its
        slots; it remains until its requirement is met."""
        claim = dict(need_row["claim"])
        claim["focused"] = True
        self.host.book.append(need_row["kind"], claim, claimant="principal",
                              certainty=1.0, basis="user-choice",
                              relates=[need_row["id"]],
                              supersedes=need_row["id"])
        self.host.state["focus_need"] = need_row["claim"]["needId"]
        return need_row
    def fill_slot(self, need_row, slot, value, claimant="principal"):
        slots = dict(need_row["claim"].get("slots", {}))
        slots[slot] = {"value": value, "by": claimant, "at": now_iso()}
        claim = dict(need_row["claim"])
        claim["slots"] = slots
        return self.host.book.append(need_row["kind"], claim, claimant=claimant,
                                     certainty=1.0, basis="user-choice",
                                     relates=[need_row["id"]],
                                     supersedes=need_row["id"])
    # ---------- intent classification ----------
    def classify(self, text):
        """Deterministic first pass (C-DeterministicMatchReview): each
        distinguishable intent routes to its fulfillment path (R-U1 /
        C-IntentRouting)."""
        t = text.strip()
        low = t.lower()
        intents = []
        names = {p["name"].lower(): p for p in self.host.personas.values()}
        addressed = [names[n] for n in names
                     if re.search(r"\b" + re.escape(n) + r"\b", low)]
        add = lambda i: intents.append({"intent": i, "addressed": addressed})
        if re.search(r"\b(create|mint|make)\s+(a\s+)?(new\s+)?(persona|personality|avatar|character)\b", low) \
                or re.match(r"^new persona\b", low):
            add("persona-create")
        if re.search(r"\b(list|enumerate)\b", low) \
                and re.search(r"\b(in|of)\s+[A-Za-z]", low):
            add("list-request")
        if re.search(r"\b(i want|i'd like|i would like|get me|buy me|bring me)\b", low) \
                and "list" not in low:
            add("want")
        if re.search(r"\b(what can you do|help\b|capabilit|what are you|who are you|tell me about yourself)\b", low):
            add("capability")
        if re.search(r"\b(publish|postcard)\b", low) or \
                (re.search(r"\b(send|email)\b", low) and re.search(r"\bto\b", low)):
            add("publish")
        if re.search(r"\b(scan|discover|find devices|network map|map the network)\b", low):
            add("discover")
        if re.search(r"\binvite\b|\bjoin\b.*\bnetwork\b", low):
            add("fleet")
        if re.search(r"\b(reset|new topic|change the subject|clear the chat)\b", low):
            add("reset")
        if re.search(r"\b(knock[ -]knock|enact|perform|scene|joke)\b", low):
            add("scene")
        if re.search(r"\b(play|start|listen to)\b", low) and \
                re.search(r"\b(rain|hum|drift|ambient|background|noise|sounds?)\b", low):
            add("channel")
        if re.search(r"\btheme\b|\bdark\b|\blight\b|\bsepia\b|\bcontrast\b", low):
            add("theme")
        if re.search(r"\b(research|look (up|into)|find out about|tell me about|what is|who is|explain)\b", low):
            add("question")
        if not intents:
            add("converse")
        return intents
    # ---------- routing ----------
    def route(self, turn_id, text, intents):
        """Route classified intents to fulfillment paths; returns opened
        needs + routing decisions for evidence."""
        routed = []
        for it in intents:
            kind = it["intent"]
            if kind == "list-request":
                need = self.open_list_need(turn_id, text)
                routed.append({"intent": kind, "need": need["id"],
                               "path": "list-machinery"})
            elif kind == "want":
                need = self.open("need:request", {
                    "subject": f"want:{text[:60]}",
                    "requirement": text, "origin": turn_id,
                    "slots": {}, "claimant": "principal"})
                routed.append({"intent": kind, "need": need["id"],
                               "path": "floor"})
            elif kind == "capability":
                routed.append({"intent": kind, "path": "answered-inline"})
            elif kind == "persona-create":
                routed.append({"intent": kind, "path": "mint-flow"})
            elif kind == "publish":
                routed.append({"intent": kind, "path": "publish-workflow"})
            elif kind == "discover":
                routed.append({"intent": kind, "path": "fleet-discovery"})
            elif kind == "scene":
                routed.append({"intent": kind, "path": "stage"})
            elif kind == "channel":
                routed.append({"intent": kind, "path": "background-channels"})
            elif kind == "reset":
                routed.append({"intent": kind, "path": "conversation-reset"})
            elif kind == "theme":
                routed.append({"intent": kind, "path": "settings"})
            else:
                routed.append({"intent": kind, "path": "conversation"})
        return routed
    def open_list_need(self, turn_id, text):
        """A list request opens template-governed list machinery — a formal
        iterable list object, not prose (C-FormalList)."""
        criteria = extract_list_criteria(text)
        return self.open("need:list", {
            "subject": f"list:{criteria['label']}",
            "requirement": text,
            "criteria": criteria,
            "origin": turn_id,
            "slots": {"scope": criteria["scope"],
                      "memberKind": criteria["member_kind"],
                      "place": criteria["place"],
                      "filled": [], "candidates": []},
            "satisfaction": "formal list object populated with members; "
                            "non-matches recorded for review"})
    def fulfill_list(self, need_row):
        """Compose the minimal tool set for a list need:
        tool.list-members + tool.match-criteria + tool.record
        (S-tool-composition). Produces the formal list object + non-matches."""
        criteria = need_row["claim"]["criteria"]
        scope, place = criteria["scope"], criteria["place"]
        host = self.host
        candidates, retrieval_basis = [], None
        wikipedia = host.sources.get("source-wikipedia")
        used_tool = "tool.list-members"
        for cat in category_candidates(scope, place):
            if wikipedia:
                members = src_mod.mediawiki_category(
                    wikipedia, "Category:" + cat, limit=800)
                candidates += members
            if candidates:
                retrieval_basis = "category:" + cat
                break
        if not candidates and wikipedia:
            used_tool = "tool.search"
            hits = src_mod.mediawiki_search(
                wikipedia, f"{scope} in {place}", limit=8)
            for h in hits[:3]:
                ex = src_mod.mediawiki_extract(wikipedia, h["title"])
                candidates += harvest_bullets(ex)
            retrieval_basis = "page-harvest"
        members, nonmatches = [], []
        seen = set()
        for c in candidates:
            c2 = c.strip()
            if not c2 or c2.lower() in seen:
                continue
            seen.add(c2.lower())
            if is_member(c2, criteria):
                members.append(c2)
            else:
                nonmatches.append(c2)
        comp = host.book.append("tool:composition", {
            "subject": need_row["id"],
            "components": COMPOSITIONS["need:list"],
            "decomposable": True,
            "note": "minimal existing tool set composed; "
                    "AI-creation primacy + direct editing for fine-tuning"},
            claimant="host", basis="execution-evidence")
        lst = self.host.book.append("list:object", {
            "subject": need_row["claim"]["subject"],
            "criteria": criteria,
            "members": members,
            "memberCount": len(members),
            "nonMatches": nonmatches[:200],
            "nonMatchCount": len(nonmatches),
            "iterable": True,
            "retrievalBasis": retrieval_basis,
            "usedTool": used_tool,
            "composition": comp["id"]},
            claimant="host", certainty=0.8, basis="durable-result",
            relates=[need_row["id"]])
        self.close(need_row, "fulfilled",
                   {"listId": lst["id"], "memberCount": len(members)})
        return lst

    def compete(self, need_row):
        """Two competing tools run the same need (S-competing-tools):
        tool.list-members (category enumeration) vs tool.search +
        bullet-harvest (page retrieval). Both legs produce member counts —
        the comparison is recorded as a ledger object."""
        criteria = need_row["claim"].get("criteria") or \
            extract_list_criteria(need_row["claim"].get("requirement", ""))
        scope, place = criteria["scope"], criteria["place"]
        host = self.host
        wikipedia = host.sources.get("source-wikipedia")
        legs = []
        if wikipedia:
            for cat in category_candidates(scope, place)[:2]:
                members = src_mod.mediawiki_category(
                    wikipedia, "Category:" + cat, limit=800)
                legs.append({"tool": "tool.list-members",
                             "via": "category:" + cat,
                             "count": len(members),
                             "members": members[:40]})
                if members:
                    break
            hits = src_mod.mediawiki_search(
                wikipedia, f"{scope} in {place}", limit=6)
            harvested = []
            for h in hits[:3]:
                ex = src_mod.mediawiki_extract(wikipedia, h["title"])
                harvested += harvest_bullets(ex)
            legs.append({"tool": "tool.search+harvest",
                         "via": "page-harvest",
                         "count": len(harvested),
                         "members": harvested[:40]})
        else:
            legs.append({"tool": "tool.list-members", "via": "no-source",
                         "count": 0, "declared": "wikipedia not configured"})
        row = host.book.append("tool:comparison", {
            "subject": need_row["id"],
            "criteria": criteria,
            "legs": legs,
            "winner": max(legs, key=lambda l: l["count"])["tool"]
            if legs else None},
            claimant="host", basis="execution-evidence")
        return row
def extract_list_criteria(text):
    low = text.lower()
    m = re.search(r"list\s+(?:of\s+)?(?:all\s+)?(?:the\s+)?(.+?)\s+in\s+(.+)$", low)
    if not m:
        m = re.search(r"(?:all\s+)?(.+?)\s+in\s+(.+?)(?:\?|\.|$)", low)
    scope = (m.group(1).strip() if m else "items")
    place = (m.group(2).strip(" ?.") if m else "the world")
    scope = re.sub(r"^(all|the|every)\s+", "", scope).strip() or "items"
    member_kind = "city" if ("cities" in scope or "city" in scope) else \
        "mountain" if ("mountain" in scope or "peak" in scope) else \
        re.sub(r"s$", "", scope)
    return {"scope": scope, "place": place, "member_kind": member_kind,
            "label": f"{scope} in {place}",
            "preserved": "criteria carried in the need row; refinement "
                         "supersedes by assertion, never rewrites"}
def category_candidates(scope, place):
    p = place.title()
    if "city" in scope or "cities" in scope:
        return [f"Cities in {p}", f"Populated places in {p}",
                f"Municipalities in {p}"]
    if "mountain" in scope or "peak" in scope:
        return [f"Mountains of {p}", f"Mountains of {p} (state)",
                f"Landforms of {p}"]
    return [f"{scope.title()} in {p}", scope.title()]
def harvest_bullets(extract):
    out = []
    for line in extract.splitlines():
        line = line.strip()
        if 3 < len(line) < 60 and "," in line:
            out.append(line.split("(")[0].strip())
    return out
BAD_MEMBER = re.compile(
    r"\b(list|category|template|wikipedia|file|portal|disambiguation|"
    r"township|county|school|district|borough of|neighborhood|river|"
    r"creek|mountain|ridge|valley|forest|lake|park|trail|road|street|"
    r"station|airport|cemetery|church|unincorporated community|"
    r"census-designated|post office|u\.s\. state|metropolitan|micropolitan)\b",
    re.I)
def is_member(title, criteria):
    """Deterministic member test; non-matches retained for review (D4).
    Category members for a place-scoped set are already place-filtered by
    retrieval ("Category:Cities in Pennsylvania"); remaining entries are
    member titles, sometimes suffixed ", Pennsylvania" for disambiguation."""
    t = title.strip()
    if BAD_MEMBER.search(t):
        return False
    if ":" in t:
        return False
    base = t.split(",")[0].strip()
    if len(base) < 2 or base.lower() in STOPWORDS:
        return False
    return True
