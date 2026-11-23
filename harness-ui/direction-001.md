# Direction 001 — SIGNED 2026-11-23

Drafted by the coordinator session 2026-11-23 at line birth. First cycle on a new line.
Signed by owner 2026-11-23 (with line name, judge model, and scenario suite).

- **Region / variable:** first realization of `prompt.md` — the status display
  end-to-end: emitter + shell + data payloads over the real `C:\builds` corpus.
- **Baseline:** **fresh** — first build on this line. Produce `version 0.1.0.001/`.
- **Cycle budget:** 1
- **Approaches:** 1
- **Criteria to log:**
  - file://-only operation — every view works from a cold checkout, no server
  - derivation correctness — displayed data matches sources (verdicts in devlog,
    `state.json`, mtimes); test corpus: the real `C:\builds\project` line
  - view completeness — fleet index + project summary + comparison + current state +
    build detail per `prompt.md`
  - honest absence — missing/unparsed data renders as visible gaps
  - scenario suite — `.devin/scenarios.md` (once owner-signed)
  - user score — owner-scored at review
  - time to implement — tracked, not scored
- **Review at:** end of this cycle — owner scores, ranks across the line's candidates
