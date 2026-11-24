"""Component registry — the invokable ontology (C-ConvergentOntology).
Three component kinds:
- **tool** — tool-as-data: id, title, need expression, template (slots,
  tests, grant, minCertainty), then a python handler or DSL steps
- **command** — `object.verb` system commands on host objects
- **primitive** — closed allow-list of low-level capabilities
Invocation always goes through the need floor: an invoke is an unmet
requirement first, an execution only when its gate passes.
"""
from __future__ import annotations
from . import floor
PRIMITIVES = (
    "prim.now", "prim.uuid", "prim.sha256", "prim.read-text",
    "prim.write-artifact", "prim.list-dir", "prim.json-parse",
    "prim.http-get",
)
class Registry:
    def __init__(self):
        self.tools: dict[str, dict] = {}
        self.commands: dict[str, callable] = {}
        self.primitives = set(PRIMITIVES)
    # -- registration --------------------------------------------------------
    def tool(self, id, title, need=None, template=None, handler=None,
             steps=None, tags=None, consequential=False, authored=False):
        self.tools[id] = {
            "id": id, "title": title, "kind": "tool", "need": need,
            "template": template or {"slots": []}, "handler": handler,
            "steps": steps, "tags": tags or [],
            "consequential": consequential, "authored": authored}
        return self.tools[id]
    def command(self, name, handler):
        self.commands[name] = handler
    # -- access ---------------------------------------------------------------
    def get(self, tool_id):
        return self.tools.get(tool_id)
    def for_need(self, need_expr):
        """All tools expressing the same need — the competing set."""
        return [t for t in self.tools.values() if t.get("need") == need_expr]
    def manifest(self):
        return {
            "tools": len(self.tools),
            "commands": len(self.commands),
            "primitives": len(self.primitives),
            "components": len(self.tools) + len(self.commands)
                          + len(self.primitives),
            "byNeed": sorted({t["need"] for t in self.tools.values()
                              if t.get("need")}),
        }
def register_all(ctx):
    from . import builtins
    builtins.register(ctx)
