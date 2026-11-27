# Shortcomings list — SIGNED by owner 2026-11-19 (direction-001)
<!-- harness-doc kind=shortcomings status=discharged applies-to=direction-001 mapped-into=direction-001 -->

Compiled 2026-11-18 by the coordinator session. This is the working definition of
"the shortcomings already documented" for direction-001 ("fulfill the prompt; rectify
the shortcomings already documented"). **Scope ruled by the owner 2026-11-18** — see the
Scope section below. The build may reconsider any GreyAvatar realization; these are
functional gaps to close, not designs to copy.

Sources (all readable from the project folder):

- `C:\Project\MigrateInbound\UserConcerns.json` — 13 owner-reported concerns
- `C:\Project\MigrateInbound\DESIGN_CHOICES.md`, `InstructionsForProjectPrompt.txt`,
  `InstructionsForUserExperience.txt` — D-* / noted incomplete realizations
- `C:\Users\kris_\CursorProjects\GreyAvatar\deficits\` — the reference repo's own
  drift tracker (statuses noted; resolved items kept as lessons)

## A. Owner-reported concerns (UserConcerns.json)

| # | Concern | Shortcoming to rectify (observations condensed) |
|---|---------|-------------------------------------------------|
| A1 | Operational data synthesis & working memory | Inadequate synthesis of results worth user attention; unreliable logs/working memory leading to crashes |
| A2 | Local fleet onboarding & coordination | No reliable request-to-join / host-generated installer flow; laborious device enrollment; no capability-discovery/role-placement wizard |
| A3 | Responsiveness of background stewardship | Background work competes with prompt acknowledgement/commands; coded rather than configurable stewardship; separation not robust |
| A4 | Project & task management interfaces | Weak command-to-project grouping; incomplete queue/focus/Library links and command-center view; progress/approval/failure states not user-facing |
| A5 | Competing-tool evaluation & missed-opportunity review | Confidence-based tool ranking after failure not implemented correctly; LLM review of responses/missed opportunities incomplete |
| A6 | Personality presentation & multimodal theater | Uneven interactive theater; incomplete conversational polish, gallery behavior, soundscape; personality lenses not consistently central |
| A7 | Portable exchange & Studio authoring | Incomplete print-to-scan and export/import paths; unfinished scan/QR validation gates; payload-size constraints unhandled |
| A8 | Cleanup policy & confidence adaptation | Governed consolidation conformity unclear; success-driven source confidence adjustment omitted; no dependable compression of history |
| A9 | Decision-model integration for tool selection | Regex-only deterministic matching; no bounded decision model for routing/evaluation (treated as open question, not requirement) |
| A10 | Tool creation for novice authors | Authoring/inspection/validation/repair too hard for first-time programmers; no compact carriers (HTML etc.) |
| A11 | Local installation & network-fracture adaptation | Manual multi-device setup; no OS-specific joiner installers; no defined partition/rejoin behavior |
| A12 | Naming & non-anthropomorphic presentation | "Avatars" naming foregrounds personification; users shouldn't be forced into an anthropomorphic frame |
| A13 | Competing local & online speech tools | Hardcoded local→online speech relationship; should be independently defined competing tools |

Each concern's `planningGuidance` in the JSON states which outcomes matter vs. which
realizations are open — the build should honor that seam (rectify the outcome gap,
choose its own mechanism).

## B. Spec-corpus incompleteness notes

- **D-ToolTrustChurn** — failed-tool ranking adjustment "not implemented correctly" in
  GreyAvatar (DESIGN_CHOICES.md:81; InstructionsForProjectPrompt.txt:43 — "remains an
  import question"). Rectify: insufficient-confidence results lower a tool's rank among
  alternatives without crossing confidence thresholds or making it ineligible.
- **D-IdleTurnAsTool** — idle-turn stewardship as a configurable, assignable tool; the
  coded coordination has "incomplete configurability" (DESIGN_CHOICES.md:45).
- **Project creation prominence** — explicit project-creation call is "an incomplete
  realization of the desired prominence" (InstructionsForProjectPrompt.txt:43).
- **Library-mediated assertion editing** — direct links and editing controls "incomplete
  in the reference implementation" (InstructionsForUserExperience.txt:106,143).
- **Derived workshop UI** — relationship-driven form derivation not fully established
  (tool-specific prefill branches remain) (InstructionsForProjectPrompt.txt:117).

## C. GreyAvatar deficits/ — open items and lessons

| File | Status | Carries forward as |
|------|--------|--------------------|
| `00-built-inventory-and-drift.md` | descriptive | segment inventory for reference |
| `01-ledger-persistence-and-session.md` | mostly resolved | durable-by-default ledger is the standard; cross-turn memory everywhere, not just product paths |
| `02-avatars-interactivity-recovery.md` | open | interactive-feel gap (gallery, routing theater, context panel, workshop suite, soundscape) — overlaps A6 |
| `03-shell-platform-catchup.md` | largely resolved | desktop-app shell as the product path; browser as dev fallback |
| `04` / `src-sequencing-plan.md` | process docs | sequencing rationale only |
| `06` (discrepancy campaign) | CONQUERED (per `07`) | — |
| `07` (liveness frontier) | successor campaign | depth/liveness/presence goals — overlaps A6 |
| `08-success-on-failure-and-env-divergence.md` | audit | **lesson:** no `ok:true`-while-failing, no silent env-dependent degradation — honest result fields everywhere (M-Honesty, M-Grace) |
| `avatars-parity-catalog.md` | open | item-level GUI/feature gap vs. the 0.1.2 reference |
| `no-cross-turn-memory.md` | partial | cross-turn memory on all conversation paths (overlaps A1) |
| `routing-earned-commands-gap.md` | RESOLVED | boundary lesson only |
| `silent-single-voice-turns.md` | RESOLVED | honest stub-fallback must be declared, not silent |
| `interpreter/` | largely landed | tool-logic-as-data + closed primitive allow-list is a proven candidate seam |

## Cycle-1 outcome status — review 2026-11-19

Rectification status per the JEV re-score (`.devin/jev-rescore-meridian.out`), Meridian's
own evidence, and owner review. "Partial" = claimed with thin or contradicted evidence.

| Item | Scope | Cycle-1 status | Evidence |
|------|-------|---------------|----------|
| A1 synthesis/working memory | in | **partial** — ledger solid; stewardship under-evidenced | probe `steward.runs=0`; ledger verified |
| A2/A11 fleet | out (criterion only) | **0** — correctly absent per ruling | verdict |
| A3 stewardship responsiveness | in | **partial** — configurable steward thread claimed | `steward.runs=0` in probe — under-evidenced |
| A4 project/task interfaces | in | **partial/thin** — command-center claimed | app.js ~280 lines; S-focused-need 0.4 repository-only |
| A5 tool ranking + missed-opp review | in | **partial** — bounded rank adjustment real | decision.py spot-checked; competing-tools demo = 1 working vs 1 unconfigured tool |
| A6 personality presentation/multimodal | in | **open** — not rectified | owner: voices overlap (dynamics failure), no generated art; soundscape absent |
| A7 exchange media | out (criterion only) | **0** — correctly absent per ruling | verdict |
| A8 cleanup/confidence adaptation | in | **rectified (evidenced)** | S-restart-recovery 0.85 enactment |
| A9 decision model | in | **rectified** — best-evidenced item | bounded feature-vector model + trust churn verified in decision.py |
| A10 novice tool authoring | in | **partial** | validate/mint/inspect claimed; thin UI |
| A12 non-anthropomorphic frame | in | **rectified** | claimed; undisputed at owner review |
| A13 competing speech tools | in | **partial** — independent tools exist, dynamics broken | overlapping speech makes competing speech moot this cycle |
| B derived workshop UI + Library editing | in | **partial** | generic template rendering; thin |
| C deficit lessons | reference | applied (honesty rules held — JEV found evidence genuine, not self-asserted) | verdict notes |

**Shortcomings this list missed** (surfaced by the three-version review →
`devlog.md` findings): F1 imitation mark (absent v0.2 + v0.3), F2 calendar reasoning,
F3 competing-tool lifecycle (overlaps A5), F6 voice-dynamics floor (now P2),
F5 canonical-scenario enactment. Candidates for a shortcomings-002.

## Scope — owner direction, 2026-11-18

"Fulfill the prompt" already subsumes much of A1–A13 where the prompt states the
requirement. This list functions as emphasis/verification points for the JEV and the
owner's user score — not as extra requirements. Owner ruling for cycle 1:

- **Skipped as rectification targets:** A2/A11 (fleet install), A7 (exchange media).
  They remain **evaluation criteria** — both expected 0 unless the build maintains
  parity with GreyAvatar's existing execution of the feature.
- **In scope:** A9 (decision model) and all other concerns.
