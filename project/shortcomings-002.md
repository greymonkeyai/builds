# Shortcomings list — direction-002 (2026-11-20)

Compiled 2026-11-20 by the coordinator session. Working definition of "the
shortcomings" for direction-002 — carries the findings the Cycle-1 review surfaced
that shortcomings-001 missed, plus the direction's convention targets. As with
shortcomings-001: these are functional gaps to close, not designs to copy; the build
may reconsider any prior realization.

Sources:

- `devlog.md` `## Review findings` (F1–F11), Cycle-1 JEV re-score
  (`.devin/jev-rescore-meridian.out`), owner review 2026-11-19
- `conventions-sweep-001.md` — per-item classification (all F4 items: conventional)
- `C:\Project\MigrateInbound\CONVENTIONS.md` + `InstructionsForConventions.txt` —
  adopted convention set (C-*) the build conforms to or challenges on record

## A. Missed findings carried from the Cycle-1 review

| # | Finding | Rectify |
|---|---------|---------|
| F1 | Imitation admonishment + permanent distinguishing mark — prompt §Personalities; implemented in v0.1, absent in v0.2 and v0.3.0.001 | Implement: a personality imitating a real person carries the admonishment and the mark. Owner: cosmetic, but **MVP-required** — do not cut as optional polish |
| F2 | Calendar temporal reasoning — ingested but not informing projects, persona responses, or background attention | Calendar must actually inform project scheduling, persona responses, and stewardship timing — not just ingest/rank |
| F3 | Competing-tool lifecycle — D7 requires comparing locally competing tools; v0.3 demoed one working tool against a permanently unconfigured one | General comparison machinery over genuinely competing tools — multiple runnable tools for the same need, comparable results |
| F5 | Canonical scenario enactment — S-list-project (PA cities) was never enacted (canned 3-item demo); S-personality-create enacted only in part | Genuinely enact both canonical scenarios end-to-end. Per C-ScenarioEnactment: enact or record the challenge; an anticipated scenario absent is a finding |
| F6 | Voice dynamics — overlapping artificial speech in v0.3 was an unrecorded departure from the floor | Conform to, or challenge on record: C-PerceivableRespondents (floor) + C-SequentialRespondents / C-SpeechFloor (manner) |

## B. Convention targets named by direction-002

From the adopted convention set (`C:\Project\MigrateInbound\CONVENTIONS.md`).
Conventions are challengeable, never ignorable: conform, or record the challenge
with evaluation and reasoning — a silent departure is a defect.

- **F4 — all six v0.1-only capabilities** (owner ruling 2026-11-20: all in scope;
  per-item classes resolved conventional by `conventions-sweep-001.md`):
  connector breadth, ethics-gate depth, presentation glass, conversation archive,
  set-build, agentic tool protocol
- **F7 — personality presentation:** C-PersonalityArt (per-personality generated
  art — named in prompt demo #5) + C-VoiceDiversity (diverse, modifiable voices)
- **F8 — connector breadth:** owner scope 2026-11-20 — **3 connectors** this cycle.
  Real, runnable connector machinery end-to-end on three connectors, not a
  17-connector catalog shell

## C. Standing honesty requirements (carried)

From the Cycle-1 deficit lessons and the direction gate: no `ok:true`-while-failing,
no silent stubs, no env-dependent silent degradation. Declared absences (e.g. fleet
install, exchange media at this parity level) are recorded, not faked. A failed
cycle is logged, not auto-retried.
