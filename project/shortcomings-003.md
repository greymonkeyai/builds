# Shortcomings list — direction-003 (ISSUED 2026-11-22)

Compiled 2026-11-22 by the coordinator session; scope confirmed by owner ruling
2026-11-22 ("full set"). Working definition of "the shortcomings" for
direction-003 — carries the findings the Cycle-2 review and live check surfaced,
the owner's 2026-11-22 scenario-suite additions, and the execution-structure
conventions adopted into the corpus the same day. As before: these are functional
gaps to close, not designs to copy; the build may reconsider any prior
realization.

Sources:

- `devlog.md` Cycle-2 verdict `user_commentary` + JEV `notes` flags (1)–(7),
  owner review 2026-11-21/22
- `.devin/scenarios.md` owner additions 2026-11-22 (twelve scenarios below
  S-focused-need)
- `C:\Project\MigrateInbound\CONVENTIONS.md` — execution-structure set adopted
  2026-11-22 (corpus commit `cecb3b2`, set 43 → 49)

## A. Confirmed defects from the Cycle-2 review and live check

| # | Finding | Rectify |
|---|---------|---------|
| G1 | Speech floor gates admission, not playback — `engines.speak_local` fire-and-forget `Popen`; `floor-played` marks render-spawn, not playback end; concurrent SAPI processes still overlap audibly (owner heard it on .002; F6 holds for admission ordering only) | Floor admission must hold until playback completion. S-speech-serialization now names this: generated speech waits until the previous speaker finishes |
| G2 | Persona "art" is a seeded abstract sigil — rounded square + rotating ellipses as a 36px roster tile; nothing face-like or characterization-readable (owner: "portrait" overstates it) | Portrait-quality art depicting the specific personality, bound to it as visual identity — S-portrait-bind now names this; C-PersonalityArt / C-PresentationGlass |
| G3 | Persona engagement — owner: "the personalities had no personality"; user score 0.2 on engagement ("GreyAvatar was a lot more usable") | Shipped personalities distinct enough that the same prompt elicits noticeably different responses — S-distinct-preloadeds names the bar |
| G4 | Launch/process hygiene — stale v0.3.0.001 held :9760; .002 double-bound and reported success anyway (Windows SO_REUSEADDR); requests raced between versions. Owner-scored clean launch 0.5 for version confusion | A launch must not report success while a prior instance owns the port; closing the window terminates the program — S-windows-launch and S-close-terminate now name both legs |

## B. Owner scenario-suite additions 2026-11-22 (the engagement/presentation pass)

Named for enactment this cycle — the suite is named wholesale, so each must be
enacted or carry a recorded challenge (C-ScenarioEnactment):

- **S-personality-roster** — selectable roster as a persistent panel,
  conventionally the left column
- **S-portrait-bind** — (A/G2 above)
- **S-color-schemes** — dark mode plus at least two other colorways; fresh launch
  opens light
- **S-status-bar** — continuously shows available sources and LLMs
- **S-email-commentary** — select a received email into conversational context;
  active personality comments on it
- **S-conversation-reset** — reset clears a moved-on conversation, keeping
  personality prompts on-topic
- **S-context-display** — active topic/context displayed when the user selects a
  profile, email, or other result
- **S-personality-editor** — editor tab exposing all customizable personality
  elements
- **S-windows-launch** — (A/G4 above) launches like an installed program
- **S-close-terminate** — (A/G4 above) close terminates; no orphans
- **S-speech-serialization** — (A/G1 above)
- **S-distinct-preloadeds** — (A/G3 above)

## C. Execution-structure conventions — adopted 2026-11-22

New to the corpus since Cycle 2; named into this direction. Conform, or record the
challenge with evaluation and reasoning — silent departure = defect:

- **C-TwoPartExecution** — build divides into Part 1 (what the readiness gate
  covers) and Part 2 (everything after)
- **C-ReadinessGate** — declared gate: input readiness + ledger readiness;
  records its pass time in accessible evidence (`time-to-gate` is a standing
  scored criterion)
- **C-LaunchPartition** — essential launch slice mounts from a dedicated launch
  file, materialization ordered by modular schema dependencies
- **C-TransientBoundary** — purgeable transient artifacts in a disposable,
  independently resettable boundary
- **C-SnapshotInference** — parallel foreground inference on per-task consistent
  ledger snapshots
- **C-SequentialCommit** — verified inference outputs commit sequentially

## D. Evidence and mechanism flags carried from the JEV Cycle-2 notes

| # | Flag | Rectify |
|---|------|---------|
| H1 | `scripts/scenarios.py` reads `ex.get('path')` at the wrong nesting — S-exchange-import's import leg received `package:None` and scored 0.4 on a driver bug, not a mechanism failure | Fix the driver; re-enact the import leg for real |
| H2 | `connectors-F8-verify.json` claimed in devlog but absent from the build | Evidence claims must exist on disk |
| H3 | `launch-server.out` in .002 is a stale copy referencing .001 paths | Per-version artifacts must be generated by that version |
| H4 | probe `steward.runs=0` again — steward exercised only via manual wake | Steward must run autonomously, or the scenario records the gap |
| H5 | `_temporal.json` classified a 2030-dated fixture event as "recent" | Temporal classification must respect the date, not the fixture |
| H6 | S-focused-need scored 0.35 — focus mechanics and conversational slot-filling not demonstrated; no evidence the need stayed open until fulfilled | Deepen the enactment, not just the machinery |
| H7 | S-chat-invocation: `intents[]`/`needIds[]` empty — the "matches one or more tool needs" half unexercised | Exercise the full scenario on an input that matches a need |

## E. Standing honesty requirements (carried)

No `ok:true`-while-failing, no silent stubs, no env-dependent silent degradation.
Declared absences (fleet install, exchange media at this parity level) are
recorded, not faked — and per owner 2026-11-21/22 they still count against
completeness. A failed cycle is logged, not auto-retried.
