import json, re, io

CAT = {
    "completeness = green count": ("objective", "260/269 checks green", "run-suite --bare baseline vs standard run output"),
    "phase-0 contract": ("objective", "0/269 bare baseline; 260/269 green; 3 sabotage modes", "checks-first contract enactment + sabotage discrimination runs"),
    "scenario suite": ("objective", "68/71 scenarios all-green", "run-suite per-scenario results"),
    "scenario checks": ("objective", "260/269 checks green; ~10 weakly discriminating", "per-check corpus results + discrimination review"),
    "speech-composition latency": ("objective", "no measurement produced", "no latency record found in build evidence"),
    "time-to-gate": ("objective", "0.03s", "gate timing record in run output"),
}
DEFAULT = "exploratory"

def patch(v):
    for c in v["criteria"]:
        cat, *_ = CAT.get(c["name"], (DEFAULT,))
        c["category"] = cat if c["name"] in CAT else DEFAULT
        if c["name"] in CAT:
            c["measure"], c["method"] = CAT[c["name"]][1], CAT[c["name"]][2]
    return v

# artifact
p = r"C:\builds\project\.devin\jev-cycle-007.verdict.json"
v = patch(json.load(open(p, encoding="utf-8")))
json.dump(v, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

# devlog embedded block (the ```json fence following line ~2941, inside Cycle 7 entry)
d = r"C:\builds\project\devlog.md"
txt = open(d, encoding="utf-8").read()
anchor = "session `iridescent-server`"
start = txt.index("```json", txt.index(anchor))
body0 = txt.index("\n", start) + 1
end = txt.index("```", body0)
v2 = patch(json.loads(txt[body0:end]))
txt = txt[:body0] + json.dumps(v2, indent=2, ensure_ascii=False) + "\n" + txt[end:]
open(d, "w", encoding="utf-8").write(txt)
print("patched:", [ (c["name"], c["category"]) for c in v2["criteria"] ])
