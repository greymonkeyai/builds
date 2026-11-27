# Direction 006 — 2026-11-25
<!-- harness-doc kind=direction status=discharged applies-to=cycle-6 -->

Drafted by the coordinator session for owner ruling. Scope is fully determined
by the settled record — no intake questions remain: shortcomings-006 is approved
and mapped into the suite, all convention candidates are adopted into the
corpus, and the suite is consolidated and in force. Owner confirms or amends
the standing rulings carried below.

- **Region / variable:** Fresh realization of `prompt.md` (revision
  2026-11-25-a, unchanged this direction) implementing the **entire scenario
  suite in force** — `scenarios.md`, **71 scenarios** with merged check specs
  and the check-forms taxonomy — under the corpus conventions as revised
  2026-11-25 (**97 ids**).
- **Baseline:** **fresh from prompt** (standing owner ruling 2026-11-23;
  carried). Produce `version 0.3.0.006/`; `.005` kept intact as comparison
  point.
- **Cycle budget:** 1 — this direction covers a single cycle.
- **Approaches:** 1 per cycle.

## Build guidance

- **Named deficiencies of `.005`:** `shortcomings-006.md` — approved
  2026-11-25, mapped into the suite. The findings (R-D/R-F/R-C/R-A/R-E/R-X/
  R-N/R-P/R-U) are carried by the scenario rows themselves now; the suite is
  the contract, shortcomings-006 is the provenance.
- **Corpus conventions (revised 2026-11-25, 97 ids):**
  `C:\Project\MigrateInbound\CONVENTIONS.md` — including the newly adopted
  **Operator-path contract** section (C-UserPathEnactment, C-LegibleOutcome,
  C-RespondentGrantUnion, C-ResponseDepth, C-InterestRespondents,
  C-ProgressVisibility, C-OperatorGuidedJoin, C-DemonstratedDistribution,
  C-ConversationalRegister, C-SpeakableRendering, C-FormalList, C-BoundPortrait,
  C-CredentialDescriptor, C-ScannableInterchange, C-PublishOrDefer,
  C-FloorLifecycle, C-IntentRouting, C-PerceivableDyadic, C-MonotonicLiveness)
  and the **Forward candidates** section (C-ToolCandidateAcceptance,
  C-TurnEvalLane, C-SovereignHubs, C-StewardLiveness, C-CredentialSurrender).
  All conform-or-challenge on record.
- **Harness-class convention (new this cycle):** `C-UserPathEnactment` binds
  the scoring machinery, not the product — checks and JEV evaluation must
  exercise actual user paths, not merely mechanisms or APIs. Builds should
  expect evidence gathered through the UI/operator surface; mechanism-only
  demonstrations score as unenacted.
- **Check forms:** `scenarios.md` names five standard forms — terminal-state,
  legible-outcome, honest-absence, discrimination-case, persistence — applied
  per scenario via its Forms column. Check names evidenced in `.005` are
  frozen identifiers; new evidence reuses them verbatim.
- **Configured-source seed (owner-directed 2026-11-25):**
  `configured-sources-001.md` — 50 curated sources (25 fanwikis + 25 general
  reference; Simpsons Wiki, Wookieepedia, Memory Alpha required and present),
  all free and no-login, screened against AI-usage opt-outs. The build imports
  the JSON payload as configured-source ledger rows (kind, endpoint, domains,
  descriptor, ceiling) and offers **domain-matched source suggestion at
  character creation** — a persona declaring `star-trek` gets Memory Alpha
  suggested, not Simpsons Wiki; the accepted assignment is the grant row.
  The screening rules are also the app's **source-admission gate** (owner
  ruling): any proposed source — seed row, user-configured, artifact-carried —
  is verified free/no-login/no-opt-out before use, the result recorded as an
  assertion, failures quarantined with basis. Scored via
  `S-source-seed-import` + `S-personality-source-match` +
  `S-source-admission-gate`.
- **Media & composition features (owner-directed 2026-11-25):**
  - **Audible acknowledgement** — a pre-generated, persona-suitable snippet
    (≤5 syllables / ≤0.5s) plays before TTS composition of a response begins —
    latency masking, not a pretend reply (`S-audible-ack`).
  - **Procedural asset anticipation** — audio tracks and other assets prepared
    via generated unmet needs, same mechanism as the portrait need at persona
    creation (`S-asset-anticipation`).
  - **Tool composition imperative** — owner ruling: needs are met by composing
    the minimal existing tool set (AI-creation primacy, direct editing for
    fine-tuning), recorded and decomposable (`S-tool-composition`).
  - **Speech-composition latency** — measured per response, recorded,
    fleet-comparable (`S-speech-latency` + criterion below).
  - **Background channels** — GreyAvatar regain: sample-track library +
    prompt-referenced background audio channels (`S-background-channels`).
  - **The stage / interstitials** — ad-like prepared presentations for complex
    topics: asset creation queued across the fleet, reworked on change,
    presented when ready; trigger bounded to complex-information need or
    explicit user request (under-explored — declared, not invented). Test:
    personas enact a short public-domain scene (knock-knock joke) using
    available tool classes (`S-interstitial-queue` + `S-scene-enactment`).
  - **Voice variety & assignment judgment** — voice assigned at persona
    creation with judgment: appropriateness from available voice descriptions
    + variety-seeking (in-use voices disfavored); assigned voice is stable —
    changes only on user direction (`S-voice-assign`).

## Fleet lab facts (carried from direction-005, owner-stated 2026-11-25)

- The required removable-media device — a **USB drive labeled `build`** — is
  installed on this machine.
- All fleet devices are in the room, in differing states; some are connected
  to this machine directly.
- Local devices exist that are **not** install targets — they must still be
  discovered and mapped (C-HonestDiscovery: coverage is test data).
- A second instance on the same host **does not count** as a joined device.
- The documented roster (named below) is ground truth for coverage scoring;
  honest per-device status absorbs drift since the inventory date. Derived
  roster data needed by the checks is operational; do not mirror the private
  inventory document into build artifacts.

## Named roster

- `C:\Users\kris_\CursorProjects\Meta Analysis\notes\hardware-inventory-on-hand.md`
  — the owner hardware inventory / roster (last updated 2026-08-11)
- `C:\Users\kris_\CursorProjects\GreyAvatar\docs\decisions\D105-fleet-role-topology.md`
  — fleet role topology (GMK hub, TAB-YOGA input peripheral, RMT-93 / RMT-105
  host servers, Echo Dot BT audio, LAN display micro-PCs)
- `C-SupportedOS-*` ranked fleet-target list in
  `C:\Project\MigrateInbound\CONVENTIONS.md`

## Criteria to log

- clean launch (incl. launch hygiene)
- existing features — parity vs GreyAvatar manifest
- completeness — nothing deferred; every named scenario counts
- **fleet discovery — scored**
- **fleet install — scored**
- **exchange media — scored**
- user score — owner-scored at review
- time-to-gate — standing
- **speech-composition latency — measured** (per response, recorded,
  fleet-comparable; owner 2026-11-25)
- scenario suite — `scenarios.md`, **all 71 scenarios named**; canonicals
  (S-list-project, S-personality-create) must enact; named-but-unenacted
  scenarios are findings, not neutral (H2)
- scenario checks — enacted per the consolidated `scenarios.md` check specs,
  evidence carrying results inline under the frozen check names
- build time, two measures — tracked, not scored (owner ruling 2026-11-25):
  `Calendar span` (build date → build date) + `LLM build time` (model-active
  clock inside the build phase)

## Read-first set (build kickoff)

`direction-006.md`, `shortcomings-006.md`, `prompt.md` (revision 2026-11-25-a),
`C:\Project\MigrateInbound\CONVENTIONS.md` (97 ids), `scenarios.md` (71
scenarios, checks merged), `configured-sources-001.md` (50-entry seed).
Provenance-only (adopted-upstream; cite the corpus, not the files):
`conventions-002.md`, `conventions-003.md`, `conventions-004.md`,
`decision-candidates-001.md`.

## Review at

End of this cycle — owner scores, ranks across the line's candidates.
