# Owner review Cycle 7 — record owner user_opinion/user_commentary into the
# verdict (artifact + devlog block), per the verdict contract:
# silence = agreement; commentary without a figure = agreement + kept note.
import json, re

scores = {
    "existing features": 0.4,
    "speech-composition latency": 0,
    "user score": 0.35,
}
commentary = [
    "existing features 0.4 (JEV 0.55 generous): NO AUDIO WHATSOEVER in the running build — audio scenarios scored on self-asserted/mechanism evidence, not perceivable output.",
    "speech-composition latency 0: no audio produced, so nothing to measure. Also a units ruling: latency and time-to-gate should be RAW SECONDS (tenths), not normalized 0-1 scores — score on evidence presence, report the number.",
    "fleet discovery challenged: results carry insufficient identifying info to identify devices. Requirement forming: a ping/identify action that signals a device to respond (chirp/beep/on-screen), supporting lab device types; richer identifying info in results.",
    "standing bar sharpened: if a feature is not usable by the user it does not count — stubs and hidden/unreachable features are absence, not enactment. Open scoping questions: formally define interfaces? formally detail user-path use scenarios?",
    "user score 0.35.",
]

def apply(v):
    for c in v["criteria"]:
        if c["name"] in scores:
            c["user_opinion"] = scores[c["name"]]
    existing = v.get("user_commentary") or []
    v["user_commentary"] = existing + commentary
    return v

# artifact
ap = r"C:\builds\project\.devin\jev-cycle-007.verdict.json"
v = json.load(open(ap, encoding="utf-8"))
json.dump(apply(v), open(ap, "w", encoding="utf-8"), indent=2)
print("artifact updated")

# devlog block — replace the cycle-7 fenced verdict (the LAST ```json block)
dp = r"C:\builds\project\devlog.md"
d = open(dp, encoding="utf-8").read()
i = d.rindex("```json")
j = d.index("```", i + 7)
block = d[i + 7:j]
dv = json.loads(block.strip())
dv = apply(dv)
d = d[:i + 7] + "\n" + json.dumps(dv, indent=2) + "\n" + d[j:]
open(dp, "w", encoding="utf-8").write(d)
print("devlog verdict updated")
