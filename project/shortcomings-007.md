# Shortcomings 007 — named deficiencies of `version 0.3.0.006`
<!-- harness-doc kind=shortcomings status=approved since=2026-11-26 applies-to=direction-007 -->

Owner findings from live evaluation of the running `.006` instance
(2026-11-26), abbreviated review — owner paused fuller review to move to the
new build directions (`impl-design-001` module structure + phase-0
contract). Bars describe what a build is measured against, not how.

- **R-I1 Improv restraint.** The truthful-reporting constraint over-steers
  into refusal to improvise on un-truth-able topics. "What type of weather
  do you like?" drew "I don't know" then "I just report the weather" — the
  persona got confused between reporting truth and performing personality.
  **Bar:** improv backed by personality history on preference/opinion
  questions; truthfulness constrains *claims*, not play — an improv answer
  is marked by register, not by refusal.
- **R-S1 Style picker invisible.** The style selector (R1 recurrence:
  nonfunctional in `.003`) is absent from the `.006` owner surface —
  requirement feared lost. **Bar:** the style control present AND reachable
  on the owner-facing surface, with its effect perceivable.

## Carried JEV flags (cycle-6 verdict, `jev-cycle-006`)

Available to be named by the direction — scored findings, not yet ruled
requirements:

- Stub surfaces — `renderFleet()`/`renderSources()` empty; voice dropdown
  unpopulated (`state._voices` never set); S-color-schemes verified at
  assertion level only.
- ~10 checks passed vacuously or on hardcoded `True` (fleet-roster
  coverage, stale-seed revisit, awareness carried, tool classes, same-host
  "second node", trigger bounds, in-progress-on-done, credential screen,
  characterization, cleanup, audio-absent honesty).
- Projects + calendar absent AND undeclared (silent required-section gap —
  `projects` module owns it per `impl-design-001`).
- Peer book nominal — join/surrender only on the host book.
- Persona email replies contentless; portraits crude but genuinely
  LLM-authored.

## Owner context note

Owner verdicts 0/0 on fleet install + exchange media where the JEV scored
0.6/0.8 on mechanism — the user-path gap is the divergence instrument;
C-UserPathEnactment applies to how these bars read.
