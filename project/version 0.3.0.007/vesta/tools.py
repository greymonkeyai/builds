"""tools — invokable capability registry (module: tools).

Tools are persistently identifiable capabilities: definitions describe
purpose, inputs, expected results, acceptance tests, optional/required
values (C-AcceptanceChecks, C-TemplateDerivedUI). The invokable surface
is an object.verb command set over a closed primitive allow-list
(C-ConvergentOntology). Competing realizations of the same need are
compared locally — confidence, recency, criteria, user acceptance inform
the comparison (prompt §Tools). Needs are met by composing the minimal
existing tool set — AI-creation primacy with direct editing — rather
than minting bespoke per-need tools; compositions are recorded ledger
objects decomposable to components (owner ruling: composition
imperative). Workshop functions carry inline explanation.
"""

import time


class Tools:
    def __init__(self, host):
        self.h = host
        self.registry = {}

    # ---------- registry ----------
    def define(self, tool_id, purpose, handler, inputs=None, tests=None,
               explanation="", optional=None, competing=None):
        self.registry[tool_id] = {
            "id": tool_id, "purpose": purpose, "handler": handler,
            "inputs": inputs or {}, "tests": tests or [],
            "optional": optional or [], "explanation": explanation,
            "competing": competing or [],
        }

    def register_builtins(self):
        """Shipped tool set — minimal, composable."""
        self.define("ledger.echo", "Echo text through the ledger pipeline",
                    lambda a: {"ok": True, "text": a.get("text")},
                    explanation="Gate probe: proves primitive pipelines accept and route input.")
        self.define("list.members.wikipedia-category",
                    "Enumerate list members via a wiki category walk",
                    self._list_via_category,
                    explanation="Retrieves category members from the assigned wiki source; "
                                "records non-matching entries as results-that-do-not-match for review.")
        self.define("list.members.search-derived",
                    "Enumerate list members via search + title filtering",
                    self._list_via_search,
                    competing=["list.members.wikipedia-category"],
                    explanation="Competing realization: derives members from wiki search titles "
                                "instead of a category walk — comparable results.")
        self.define("mail.read", "Read recent mail from a configured account or fixture",
                    self._mail_read,
                    explanation="Reads the configured account source; when unconfigured, "
                                "reads the shipped fixture and labels the basis honestly.")
        self.define("temporal.classify", "Classify temporal mentions as upcoming/current/historical",
                    self._temporal,
                    explanation="Interprets calendar/date references against 'now' so events "
                                "can inform project work and persona responses.")
        self.define("speech.speak", "Speak text on the host audio surface",
                    self._speak,
                    explanation="Serializes playback through the speech floor; measured "
                                "utterance durations, never assumed.")
        self.define("art.svg", "Compose a personality portrait as vector art",
                    self._art,
                    explanation="LLM art path: the model authors an SVG scene for this "
                                "persona; a declared fallback binds a marked tile instead.")
        self.define("exchange.publish", "Publish a holding through a form/channel",
                    self._publish,
                    explanation="Produces the artifact and records the exchange — or defers "
                                "with request + status recorded where the channel is unconfigured.")
        self.define("seed.mint", "Write a new USB installer from an installed capable node",
                    self._mint,
                    explanation="Capable nodes mint installers carrying the founding network's "
                                "identity as an adoptable offer (C-SeedMint).")
        for tid, t in self.registry.items():
            self.h.ledger.append("tool:registered",
                                 {"tool": tid, "purpose": t["purpose"],
                                  "explanation": t["explanation"],
                                  "inputs": t["inputs"], "tests": t["tests"],
                                  "competing": t["competing"]},
                                 claimant="system", basis="build", certainty=0.85)

    # ---------- invocation ----------
    def invoke(self, tool_id, args):
        t = self.registry.get(tool_id)
        if not t:
            return {"ok": False, "error": f"unknown tool {tool_id}"}
        # acceptance gate: required inputs
        missing = [k for k, req in (t["inputs"] or {}).items()
                   if req and args.get(k) is None]
        if missing:
            self.h.ledger.append("tool:invocation-refused",
                                 {"tool": tool_id, "missing": missing},
                                 claimant="system", basis="execution-evidence")
            return {"ok": False, "missing": missing}
        try:
            out = t["handler"](args) or {"ok": True}
        except Exception as e:
            out = {"ok": False, "error": str(e)}
        self.h.ledger.append("tool:invoked",
                             {"tool": tool_id, "args": {k: str(v)[:120] for k, v in args.items()},
                              "ok": out.get("ok")},
                             claimant="system", basis="execution-evidence")
        return out

    # ---------- composition (the composition imperative) ----------
    def compose(self, name, steps, by="ai"):
        """A composition is a recorded ledger object listing component
        tool steps — decomposable back to its components."""
        cid = f"comp-{self.h.ledger.next_index('tool'):04d}"
        bad = [s for s in steps if s.get("tool") not in self.registry]
        if bad:
            return {"ok": False, "error": "unknown components", "bad": bad}
        self.h.ledger.append("tool:composition",
                             {"composition": cid, "name": name,
                              "steps": steps, "by": by,
                              "components": [s["tool"] for s in steps]},
                             claimant="principal" if by == "manual" else "system",
                             basis="user-set" if by == "manual" else "derived")
        return {"ok": True, "composition": cid}

    def run_composition(self, cid, args):
        comp = self.h.ledger.view()["compositions"].get(cid)
        if not comp:
            return {"ok": False, "error": "no such composition"}
        results = []
        ctx = dict(args)
        for step in comp["steps"]:
            out = self.invoke(step["tool"], {**args, **step.get("args", {}), **ctx})
            results.append({"tool": step["tool"], "out": out})
            if isinstance(out, dict) and out.get("ctx"):
                ctx.update(out["ctx"])
            if isinstance(out, dict) and out.get("ok") is False:
                break
        return {"ok": True, "composition": cid, "results": results}

    # ---------- builtin handlers ----------
    def _list_via_category(self, args):
        from .sources import wiki_category_members
        src = args.get("source", "source-wikipedia")
        cat = args.get("category", "Category:Cities in Pennsylvania")
        members, nonmatches = wiki_category_members(src, cat,
                                                  want=args.get("want", "city"))
        return {"ok": True, "members": members, "nonMatches": nonmatches,
                "source": src, "category": cat}

    def _list_via_search(self, args):
        from .sources import wiki_search_members
        src = args.get("source", "source-wikipedia")
        term = args.get("term", "city in Pennsylvania")
        members, nonmatches = wiki_search_members(src, term,
                                                want=args.get("want", "city"),
                                                limit=int(args.get("limit", 80)))
        return {"ok": True, "members": members, "nonMatches": nonmatches,
                "source": src, "term": term}

    def _mail_read(self, args):
        return self.h.sources.mail_read()

    def _temporal(self, args):
        return self.h.projects.temporal_classify(args.get("text", ""))

    def _speak(self, args):
        return self.h.conversation.speak(args.get("text", ""),
                                         persona=args.get("persona"))

    def _art(self, args):
        return self.h.personas.compose_portrait(args.get("persona"))

    def _publish(self, args):
        return self.h.exchange.publish(args.get("holding"), args.get("form"))

    def _mint(self, args):
        return self.h.fleet.mint_seed(args.get("drive"))
