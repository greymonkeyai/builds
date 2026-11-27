"""projects — projects, temporal context, formal lists (module: projects).

Projects are sequences/collections of goals that organize related work
into tool calls — created, advanced, or revised through chat; goals,
needs, tool attempts, progress, results, and historical evidence stay
connected to the assertion ledger. A list request creates a formal
formatted list as an assertion-ledger object — iterable, inspectable,
usable as import to future processes (C-FormalList); the conversational
reply presents the list, it is not the list itself. Temporal sources
(calendar entries, dated mentions) inform project work and persona
responses; entries remain source evidence governed by the same ledger
and authority rules.
"""

import re
import time

MONTHS = {m: i + 1 for i, m in enumerate(
    "january february march april may june july august september october "
    "november december".split())}


class Projects:
    def __init__(self, host):
        self.h = host

    # ---------- projects ----------
    def open(self, title, goals=None):
        pid = f"project-{self.h.ledger.next_index('project'):04d}"
        self.h.ledger.append("project:opened",
                             {"project": pid, "title": title},
                             claimant="system", basis="interpretation")
        for g in goals or []:
            self.add_goal(pid, g)
        return pid

    def add_goal(self, pid, goal):
        return self.h.ledger.append("project:advanced",
                                    {"project": pid, "goal": goal},
                                    claimant="system", basis="derived")

    def advance(self, pid, note, relates=None):
        return self.h.ledger.append("project:advanced",
                                    {"project": pid, "note": note},
                                    relates=relates or [],
                                    claimant="system", basis="derived")

    def close(self, pid, result=None):
        return self.h.ledger.append("project:closed",
                                    {"project": pid, "result": result},
                                    claimant="system", basis="derived")

    # ---------- formal lists ----------
    def create_list(self, title, criteria, need=None, project=None):
        lid = f"list-{self.h.ledger.next_index('list'):04d}"
        self.h.ledger.append("list:created",
                             {"list": lid, "title": title, "criteria": criteria,
                              "need": need, "project": project},
                             claimant="system", basis="derived",
                             relates=[x for x in (need, project) if x])
        return lid

    def add_member(self, lid, member, source=None, confidence=0.7):
        return self.h.ledger.append("list:member",
                                    {"list": lid, "member": member,
                                     "source": source, "confidence": confidence},
                                    claimant="system", basis="source-evidence")

    def add_nonmatch(self, lid, title, why):
        """Results that do not match the requested criteria — headers,
        foreign links, category errors — retained for review and cleanup
        (D4)."""
        return self.h.ledger.append("list:nonmatch",
                                    {"list": lid, "title": title, "why": why},
                                    claimant="system", basis="source-evidence")

    # ---------- the canonical list enactment ----------
    def fulfill_list(self, need_id, request_text):
        """Compose the minimal tool set for a list request: retrieval tool
        → formal list object → need fulfilled. Criteria stay in the need
        rows; non-matches are recorded for review."""
        low = request_text.lower()
        m = re.search(r"(?:all (?:the )?|list (?:of |all )?)?"
                      r"(cities|towns|boroughs|municipalities|places)"
                      r"(?: in | of )?([a-z ]+)?", low)
        member_kind = (m.group(1) if m else "item").rstrip("s")
        place = (m.group(2) if m and m.group(2) else "").strip() or "pennsylvania"
        label = f"{member_kind}s in {place}".strip()
        criteria = {"scope": f"{member_kind}s", "place": place,
                    "member_kind": member_kind, "label": label,
                    "preserved": "criteria carried in the need row; "
                                 "refinement appends related assertions"}

        project = self.open(f"list {label}",
                            goals=[f"retrieve members of {label}",
                                   "preserve criteria", "record non-matches"])
        lid = self.create_list(label, criteria, need=need_id, project=project)

        # compose retrieval: category walk + competing search realization
        comp = self.h.tools.compose(
            f"list-{label}", [
                {"tool": "list.members.wikipedia-category",
                 "args": {"category": f"Category:{label.title().replace(' ', '_')}"
                                       .replace('_In_', '_in_'),
                          "want": member_kind}},
                {"tool": "list.members.search-derived",
                 "args": {"term": f"{member_kind} in {place}", "want": member_kind}},
            ], by="ai")

        out = self.h.tools.invoke(
            "list.members.wikipedia-category",
            {"category": f"Category:{label.title().replace(' ', '_')}",
             "want": member_kind, "source": "source-wikipedia"})
        members = out.get("members") or []
        if not members:  # retry canonical PA category spelling
            out = self.h.tools.invoke(
                "list.members.wikipedia-category",
                {"category": "Category:Cities in Pennsylvania",
                 "want": member_kind, "source": "source-wikipedia"})
            members = out.get("members") or []
        for title in members:
            self.add_member(lid, title, source="source-wikipedia",
                            confidence=0.75)
        for nm in out.get("nonMatches") or []:
            self.add_nonmatch(lid, nm.get("title", "?"), nm.get("why", "non-match"))
        self.advance(project, f"retrieved {len(members)} members; "
                              f"{len(out.get('nonMatches') or [])} non-matches recorded",
                     relates=[lid])
        self.h.needs.fulfill(need_id, result={"list": lid, "memberCount": len(members)},
                             by="list-machinery")
        self.close(project, {"list": lid, "members": len(members)})
        return {"list": lid, "members": members,
                "nonMatches": out.get("nonMatches") or [],
                "composition": comp.get("composition"),
                "memberCount": len(members)}

    # ---------- temporal ----------
    def temporal_classify(self, text):
        """Interpret dated mentions as upcoming/current/historical
        (prompt §Temporal context)."""
        now = time.time()
        out = []
        for m in re.finditer(r"\b(19|20)(\d{2})\b", text):
            yr = int(m.group(0))
            t = time.mktime((yr, 6, 1, 12, 0, 0, 0, 0, -1))
            cls = "current" if abs(t - now) < 200 * 86400 else \
                ("upcoming" if t > now else "historical")
            out.append({"mention": m.group(0), "class": cls})
        for name, num in MONTHS.items():
            if re.search(rf"\b{name}\b", text.lower()):
                out.append({"mention": name, "class": "undated-month"})
        return {"ok": True, "mentions": out,
                "basis": "temporal-classification"}
