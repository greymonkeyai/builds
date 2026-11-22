"""Install-time seed packs. Packs are JSON data loaded once per installation
(marker row prevents re-seeding). Seed assertions carry claimant seed:*.
"""
from __future__ import annotations

import json
import os


def load_packs(ctx, packs_dir: str) -> dict:
    loaded = []
    if not os.path.isdir(packs_dir):
        return {"loaded": []}
    for fn in sorted(os.listdir(packs_dir)):
        if not fn.endswith(".json"):
            continue
        pack_id = fn[:-5]
        # seeds are idempotent per installation via a marker subject
        existing = [a for a in ctx.ledger.all()
                    if a.subjectKey == f"pack:{pack_id}"]
        if existing:
            continue
        with open(os.path.join(packs_dir, fn), encoding="utf-8") as f:
            pack = json.load(f)
        cl = f"seed:{pack_id}"
        for p in pack.get("personas") or []:
            ctx.personas.mint(p.get("name", "unnamed"), p.get("traits") or [],
                              p.get("interests") or [], p.get("lens") or {},
                              p.get("voice"), p.get("imitates"), cl)
        for a in pack.get("assertions") or []:
            ctx.append(a["subject"], a["predicate"], a.get("value"), cl,
                       certainty=a.get("certainty", 0.9),
                       basis={"kind": "seed", "ref": pack_id})
        for t in pack.get("tools") or []:
            spec = dict(t); spec.setdefault("kind", "tool"); spec["seed"] = True
            ctx.registry.register(spec)
            ctx.append(f"tool:{spec['id']}", "tool:exists",
                       {"id": spec["id"], "seed": True}, cl)
            ctx.append(f"tool:{spec['id']}", "tool:definition", spec, cl)
        ctx.append(f"pack:{pack_id}", "seed:loaded",
                   {"id": pack_id, "personas": len(pack.get("personas") or []),
                    "assertions": len(pack.get("assertions") or []),
                    "tools": len(pack.get("tools") or [])}, cl,
                   basis={"kind": "seed", "ref": pack_id})
        loaded.append(pack_id)
    return {"loaded": loaded}
