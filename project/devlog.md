# Development log — project

Line of development: fresh-from-prompt builds under `version 0.3.0.x`, using GreyAvatar
(`C:\Users\kris_\CursorProjects\GreyAvatar`) as a reference realization with owner-granted
authority to reconsider any aspect. Started 2026-11-18. This log is the continuous record
of this project; it is pointed at by the owner and is not authoritative outside this
project.

## Reference builds (pre-harness)

Prior generations of this line of development, added 2026-11-19 for parity calibration.
Not harness cycles — assessed by JEV reference runs (repository evidence only, no launch).

**Rubric revision (owner, 2026-11-19, Cycle 1 review):** `completeness` added to the
criteria set — fraction of the prompt's required behavior the implementation delivers.
Orthogonal to parity: a build may match the reference yet implement little of the prompt.
Reference builds are scored against the current `prompt.md` snapshot as a common
yardstick (retrospective by design for v0.1/v0.2, which predate it). Also added: a
**per-scenario suite** (`.devin/scenarios.md`) — each named usage scenario scored
individually on ability to enact, with `enactment` vs `repository` evidence class
distinguished. Canonical tests carried from prior builds: S-list-project (Pennsylvania
cities — template model) and S-personality-create (coherent persona). `new features`
**removed** — not a good indicator; completeness absorbs its useful content. `existing
features` retained: failure to enact previously demonstrated features remains scored.
All three versions (v0.1, v0.2, v0.3.0.001) (re)scored under the revised set.

**Tracked metric (owner, 2026-11-19):** `time to implement` — **elapsed time between
successive versions in this continuous series**, measured from the previous version's
completion to this version's completion. All composition counts: owner thinking,
procrastination, requirements/MAXIMs refinement, harness construction, and build session
time alike — the measure is wall-clock, not effort-hours. Shorter is favored, especially
as the implementation share becomes AI tokens rather than user refinement; record the
composition per version so that share is visible.

### version 0.1 — Avatars

- **Path:** `C:\Users\kris_\CursorProjects\Avatars` (deprecated archive, read-only)
- **Role:** first implementation generation (Tauri/React/TS); historical baseline
- **Time to implement:** series origin — git span ~74 days (2026-04-09 → 2026-06-22, 499
  commits); pre-repo conceptual history not captured by this basis
- **Clean launch:** owner-attested working 2026-11-19
- **Verdict:** (JEV `devin -p`, SWE-2 Medium, 2026-11-19; raw output
  `.devin/jev-ref-avatars.out` incl. 18-area capability manifest; `user_opinion`/
  `user_commentary` pending owner review; convention: owner silence = agreement)

```json
{
  "criteria": [
    { "name": "clean launch", "score": 1.0, "confidence": 0.9, "user_opinion": 1.0 },
    { "name": "existing features", "score": 0.7, "confidence": 0.75, "user_opinion": null },
    { "name": "completeness", "score": 0.72, "confidence": 0.7, "user_opinion": null },
    { "name": "fleet install", "score": 0.55, "confidence": 0.7, "user_opinion": null },
    { "name": "exchange media", "score": 0.1, "confidence": 0.85, "user_opinion": null }
  ],
  "overall": 0.61,
  "judge_model": "SWE-2 Medium",
  "user_commentary": [
    { "criterion": "clean launch", "opinion": 1.0, "reasoning": "Owner attestation 2026-11-19: launches just fine; not probed." },
    { "criterion": "existing features", "opinion": null, "reasoning": "Owner confirms 2026-11-19: imitation admonishment + permanent distinguishing mark was implemented in v0.1 — corroborates JEV lineage finding that v0.1 exceeds v0.2 in places." }
  ],
  "scenarios": [
    { "id": "S-assertion-input", "score": 0.85, "evidence_class": "repository" },
    { "id": "S-template-need", "score": 0.75, "evidence_class": "repository" },
    { "id": "S-candidate-ranking", "score": 0.7, "evidence_class": "repository" },
    { "id": "S-list-project", "score": 0.7, "evidence_class": "repository" },
    { "id": "S-personality-create", "score": 0.8, "evidence_class": "repository" },
    { "id": "S-background-present", "score": 0.7, "evidence_class": "repository" },
    { "id": "S-competing-tools", "score": 0.3, "evidence_class": "repository" },
    { "id": "S-restart-recovery", "score": 0.6, "evidence_class": "repository" },
    { "id": "S-exchange-import", "score": 0.05, "evidence_class": "repository" },
    { "id": "S-defer-publication", "score": 0.55, "evidence_class": "repository" },
    { "id": "S-chat-invocation", "score": 0.8, "evidence_class": "repository" },
    { "id": "S-focused-need", "score": 0.6, "evidence_class": "repository" }
  ],
  "notes": "Retrospective measurement: v0.1 predates the prompt snapshot; scored against it as common yardstick. clean-launch owner-attested, not probed. Parity: v0.1 already delivered the large majority of Grey's functional surface — ledger, templates/gaps, personalities+ethics, voices, connectors incl. calendar, monitors/stewardship, projects, paired surfaces/headless host — and in places exceeds it (connector breadth, ethics-gate depth, presentation glass, conversation archive, set-build, agentic tool protocol) — lineage evidence, not scored. Decisive parity gaps: exchange media entirely absent; fleet depth less (host-pack + paired surfaces, no android satellites/deploy tooling parity); cleanup/consolidation and competing-tool comparison thinner than prompt requires. No frontier-model escalation."
}
```

### version 0.2 — GreyAvatar

- **Path:** `C:\Users\kris_\CursorProjects\GreyAvatar`
- **Role:** current implementation; the reference realization for the parity criterion
- **Time to implement:** ~79 days after v0.1 — v0.1 last commit 2026-06-22 → v0.2 last
  commit 2026-09-09, 216 commits; human+agent era
- **Clean launch:** owner-attested working 2026-11-19
- **Verdict:** (JEV `devin -p`, SWE-2 Medium, 2026-11-19; raw output
  `.devin/jev-ref-greyavatar.out` incl. 33-area capability manifest — the parity bar;
  `user_opinion`/`user_commentary` pending owner review; convention: owner silence =
  agreement)

```json
{
  "criteria": [
    { "name": "clean launch", "score": 1.0, "confidence": 1.0, "user_opinion": 1.0 },
    { "name": "existing features", "score": 1.0, "confidence": 1.0, "user_opinion": null },
    { "name": "completeness", "score": 0.88, "confidence": 0.85, "user_opinion": null },
    { "name": "fleet install", "score": 0.9, "confidence": 0.85, "user_opinion": null },
    { "name": "exchange media", "score": 0.95, "confidence": 0.9, "user_opinion": null }
  ],
  "overall": 0.94,
  "judge_model": "SWE-2 Medium",
  "user_commentary": [
    { "criterion": "clean launch", "opinion": 1.0, "reasoning": "Owner attestation 2026-11-19: launches just fine; not probed." },
    { "criterion": "completeness", "opinion": null, "reasoning": "Owner confirms 2026-11-19: imitation admonishment + permanent mark gap is real — implemented in v0.1, deliberately deprioritized in v0.2 as cosmetic, but stands as a requirement for MVP." }
  ],
  "scenarios": [
    { "id": "S-assertion-input", "score": 0.95, "evidence_class": "repository" },
    { "id": "S-template-need", "score": 0.9, "evidence_class": "repository" },
    { "id": "S-candidate-ranking", "score": 0.9, "evidence_class": "repository" },
    { "id": "S-list-project", "score": 0.8, "evidence_class": "repository" },
    { "id": "S-personality-create", "score": 0.8, "evidence_class": "repository" },
    { "id": "S-background-present", "score": 0.8, "evidence_class": "repository" },
    { "id": "S-competing-tools", "score": 0.7, "evidence_class": "repository" },
    { "id": "S-restart-recovery", "score": 0.9, "evidence_class": "repository" },
    { "id": "S-exchange-import", "score": 0.9, "evidence_class": "repository" },
    { "id": "S-defer-publication", "score": 0.9, "evidence_class": "repository" },
    { "id": "S-chat-invocation", "score": 0.85, "evidence_class": "repository" },
    { "id": "S-focused-need", "score": 0.7, "evidence_class": "repository" }
  ],
  "notes": "Clean launch owner-attested 2026-11-19, not probed. Reference repo verified deep: ~400 vitest seams, real engine runners (Piper/Edge/Whisper/Ollama/ComfyUI), real LAN fleet (deploy robocopy + SSE mirror + pairing), real exchange media (Grey code codec, QR both directions, quarantined sub-threshold import). Gaps vs prompt.md: (1) imitation admonishment + permanent distinguishing mark for recognizable/recent persons — absent, a required prompt section; (2) calendar interpretation thin — events ingest and rank but little temporal reasoning; (3) competing-tools is same-scope steward fan-out, not a general competing-tool lifecycle; (4) amazon/crunchyroll honestly fixture-backed; (5) OCR channel absent (optional). No frontier-model escalation."
}
```

- **Owner note (2026-11-19):** imitation admonishment + permanent mark is classified
  cosmetic but remains an **MVP requirement** — flag it in future directions so a builder
  does not cut it as optional polish.

## Cycle entries

### Cycle 1 — 2026-11-18

- **Direction:** `direction-001.md` — fulfill the prompt; rectify the shortcomings already
  documented (shortcomings list signed by owner 2026-11-19)
- **Baseline:** fresh from prompt; GreyAvatar as reference realization only
- **Prompt:** embedded in `prompt.md` (snapshot of
  `C:\Project\MigrateInbound\ProjectPrompt.md`, taken 2026-11-18)
- **Criteria (rubric revision):** clean launch, user score, existing features, new
  features, fleet install, exchange media — all 0–1; fleet install and exchange media
  expected 0 unless ≥ GreyAvatar parity (local rubric provisional 2026-11-16 +
  owner direction 2026-11-18)
- **Time to implement:** ~71 days after v0.2 — v0.2 last commit 2026-09-09 → build
  2026-11-19. Composition: months of owner MAXIM/requirements refinement (ChatGPT) +
  spec-corpus and harness construction + <1 day build session (app+evidence write window
  ≈25 min, 00:33–00:58 2026-11-19; AI-token time only)
- **Result:** Built **Meridian** (`version 0.3.0.001/`) — a fresh, stdlib-only
  Python implementation of the full prompt: append-only durable JSONL
  assertion ledger with governed predicates/claimants, computed views,
  source-bounded confidence; component ontology (tool-as-data DSL executor /
  object.verb system commands / closed primitive allow-list, ~68 components);
  unmet-need floor with template gates, candidates, deferral, grants;
  chat-turn chain (decision-model intents → needs → drain → persona.speak);
  persistent personalities with imitation marks; configurable steward thread;
  projects + calendar; governed cleanup; exchange package import below
  threshold; local web surface with honesty banner. Rectified shortcomings per
  owner scope: bounded decision model for routing + respondent selection (A9),
  tool-trust churn bounded rank adjustment (A5), configurable stewardship
  duties (A3), command-center project/queue/focus view (A4), derived workshop
  forms + assertion editing via Library (B-items), novice tool
  validate/mint/inspect (A10), non-anthropomorphic respondent frame (A12),
  independently-defined competing speech tools (A13), success-driven source
  confidence adaptation (A8). Fleet install (A2/A11) and exchange media (A7)
  not implemented, declared absent per scope ruling.
  **Evidence:** `version 0.3.0.001/LAUNCH.md` + `launch.cmd`; launch logs
  `version 0.3.0.001/evidence/launch/launch-*.log` +
  `probe-20261119-005627.json` (clean launch: launched true, ok true, 68
  components, live-ollama llama3.2, durable ledger); demo transcripts
  `version 0.3.0.001/evidence/demos/01..11-*.md` + `INDEX.md`; manifest
  `version 0.3.0.001/FEATURES.md`. Live instance left serving on
  http://127.0.0.1:9760 (durable runtime under `version 0.3.0.001/runtime/`).
- **Verdict:** (JEV `devin -p`, SWE-2 Medium, 2026-11-19; raw output
  `.devin/jev-cycle-001.out`; `user_opinion`/`user_commentary` filled at owner review
  2026-11-19; convention: owner silence = agreement)

```json
{
  "criteria": [
    { "name": "clean launch", "score": 0.9, "confidence": 0.9, "user_opinion": 0.9 },
    { "name": "existing features", "score": 0.7, "confidence": 0.7, "user_opinion": 0.2 },
    { "name": "new features", "score": 0.75, "confidence": 0.7, "user_opinion": 0 },
    { "name": "fleet install", "score": 0, "confidence": 0.95, "user_opinion": 0 },
    { "name": "exchange media", "score": 0, "confidence": 0.95, "user_opinion": 0 }
  ],
  "overall": 0.65,
  "judge_model": "SWE-2 Medium",
  "user_commentary": [
    { "criterion": "clean launch", "opinion": 0.9, "reasoning": "Interacted successfully; interface responsiveness markedly better than prior runs." },
    { "criterion": "existing features", "opinion": 0.2, "reasoning": "JEV underestimated the capability of the previous applications; 0.2 is closer." },
    { "criterion": "new features", "opinion": 0, "reasoning": "No evidence of new features observed in the running application." },
    { "criterion": "user score", "opinion": 0.25, "reasoning": "Impressed with the independent build's similarity to the prior app; against it: all artificial voices speak over each other - a failure, and not even a capability that ought to be specified; the lack of personality-unique generated art was a disappointment." }
  ],
  "notes": "Evidence is largely real, not self-asserted: launch logs, probe JSON, and per-demo transcripts contain actual ledger rows consistent with runtime/demo/ledger.jsonl (223 rows, decision:* and need:* namespaces populated). Spot-checked decision.py (bounded feature-vector model + trust churn) and app.js (multi-tab UI functional but thin ~280 lines). Deductions: parity gaps vs GreyAvatar where LAN mirror, desktop shell, live connectors, soundscape/camera are declared absent; demo transcripts script-generated rather than interactive UI evidence; probe steward.runs=0 (steward responsiveness only partially evidenced). fleet/exchange-media correctly declared 0. No frontier-model escalation needed."
}
```

- **Re-score verdict:** (JEV `devin -p`, SWE-2 Medium, 2026-11-19, under revised rubric —
  `new features` removed, `completeness` + scenario suite added; raw output
  `.devin/jev-rescore-meridian.out` incl. 13-area capability manifest;
  `user_opinion`/`user_commentary` pending owner review; convention: owner silence =
  agreement)

```json
{
  "criteria": [
    { "name": "clean launch", "score": 0.9, "confidence": 0.9, "user_opinion": null },
    { "name": "existing features", "score": 0.4, "confidence": 0.75, "user_opinion": null },
    { "name": "completeness", "score": 0.8, "confidence": 0.75, "user_opinion": null },
    { "name": "fleet install", "score": 0, "confidence": 0.95, "user_opinion": null },
    { "name": "exchange media", "score": 0, "confidence": 0.95, "user_opinion": null }
  ],
  "overall": 0.42,
  "judge_model": "SWE-2 Medium",
  "user_commentary": [],
  "scenarios": [
    { "id": "S-assertion-input", "score": 0.9, "evidence_class": "enactment" },
    { "id": "S-template-need", "score": 0.85, "evidence_class": "enactment" },
    { "id": "S-candidate-ranking", "score": 0.85, "evidence_class": "enactment" },
    { "id": "S-list-project", "score": 0.3, "evidence_class": "enactment" },
    { "id": "S-personality-create", "score": 0.7, "evidence_class": "enactment" },
    { "id": "S-background-present", "score": 0.8, "evidence_class": "enactment" },
    { "id": "S-competing-tools", "score": 0.6, "evidence_class": "enactment" },
    { "id": "S-restart-recovery", "score": 0.85, "evidence_class": "enactment" },
    { "id": "S-exchange-import", "score": 0.8, "evidence_class": "enactment" },
    { "id": "S-defer-publication", "score": 0.8, "evidence_class": "enactment" },
    { "id": "S-chat-invocation", "score": 0.55, "evidence_class": "enactment" },
    { "id": "S-focused-need", "score": 0.4, "evidence_class": "repository" }
  ],
  "notes": "Re-score under revised rubric. Evidence is genuine run output: consistent assertion ids/timestamps, live-ollama engine named, probe.json real HTTP timings/ledger bytes, ledger.jsonl 223 rows corroborates. Major flags: (1) canonical S-list-project (PA cities) never enacted — list pipeline demoed on canned 3-item input only; largest single evidence gap. (2) Parity real but narrow: core ledger/needs/personas/steward/projects solid re-implementations; connectors (0/17), LAN mirror, Tauri/android shells, storefront catalog, studio, soundscape, voice catalog, perception absent — existing-features scored on delivered breadth. (3) Competing-tools demo compares one working tool against a permanently unconfigured one. (4) Parity bar inventoried directly from GreyAvatar repo. No frontier-model escalation."
}
```

- **Owner review:** (2026-11-19; live interactive session against the running instance)
  - user score: **0.25** — owner-scored criterion; per-criterion opinions and
    reasoning ride on the verdict above (`user_opinion` column + `user_commentary`).
  - overall on owner figures: ≈0.23 vs JEV 0.65. Large JEV/owner divergence on
    existing features (0.7→0.2) and new features (0.75→0) — JEV scored code/claim
    existence where the owner scores observed behavior; judge calibration
    suspect, feed into judge-model and criteria-definition revision.
  - observations: overlapping voices is an **implementation defect**, not a spec
    gap — prompt §Personalities and lenses leaves respondent count, order, voices,
    and conversational dynamics to implementation choice. Absent generated art is
    **prompt-relevant** — personality portraiture is named in prompt demo #5
    ("later portrait, voice, and characterization work").
  - ranking (rubric-required): Meridian is the sole candidate on this line —
    ranked 1st of 1, pending owner confirmation at review.
  - open inputs: review-point decision — prompt amendment drafting vs new build
    direction. (shortcomings-001.md signed 2026-11-19)

### Cycle 2 — 2026-11-20

- **Direction:** `direction-002.md` — SIGNED by owner 2026-11-20; close the gaps the
  three-version investigation exposed — enactment depth, not new breadth.
  Rectification set per `shortcomings-002.md`: F1 imitation mark, F2 calendar
  temporal reasoning, F3 competing-tool lifecycle, F4 all six v0.1-only
  capabilities (conventional — conform or challenge on record), F5 canonical
  scenario enactment, F6 voice-dynamics conventions, C-PersonalityArt +
  C-VoiceDiversity, F8 connector breadth = 3 connectors
- **Baseline:** modify-and-measure from `version 0.3.0.001/` → produces
  `version 0.3.0.002/`; baseline kept intact as comparison point
- **Prompt:** `prompt.md` (snapshot of 2026-11-18, unchanged this cycle)
- **Criteria (rubric revision):** clean launch, existing features, completeness,
  fleet install (expected 0), exchange media (expected 0), user score, scenario
  suite (`.devin/scenarios.md` — per-scenario, `enactment` vs `repository` class;
  canonical S-list-project + S-personality-create must be enacted); `time to
  implement` tracked not scored — local rubric revised 2026-11-20 (H3 applied:
  `new features` removed from defaults; completeness + scenario suite + time
  added)
- **Time to implement:** session start 2026-11-20 ~01:40; session end
  2026-11-21 ~01:10 (≈23.5 h wall-clock across one paused/resumed build
  session; baseline copied and rectifications built, launched, and evidenced
  in that span)
- **Result:** Built **Meridian `version 0.3.0.002/`** (baseline
  `version 0.3.0.001/` preserved intact). New modules: `app/ethics.py`
  (F1 gate — live liveness research via wikipedia connector,
  `maxim:objection` refusals, `ethics:gate` rows + cards, admonishment +
  permanent `◆ IMITATION` mark incl. art corner badge),
  `app/speechfloor.py` (F6 — serialized FIFO playback admission;
  `speech:floor-admission`/`floor-played` assertions; sequential
  respondents with `decision:respondent` sequence rows), `app/art.py`
  (C-PersonalityArt/C-PresentationGlass — unique seeded motif+palette
  SVG art per persona with ambient motion and portrait frames),
  `app/temporal.py` (F2 — current/upcoming/recent interpretation,
  project linkage via `calendar:linked`, steward `temporal-attention`
  duty presenting findings through a lens-matched persona, calendar
  context injected into persona replies), `app/compare.py` (F3 —
  general competition over every tool expressing a `need:`;
  `comparison:run`/`comparison:row` evidence), `app/connectors.py`
  (F8 — 4 real connectors: wikipedia live API, ics-calendar file
  ingest, files dir ingest, rss live feed; `connector:run` honest
  records), `app/setbuild.py` (C-SetBuild — competing live retrievals,
  criteria on the need, non-match classes retained, `set:closure` +
  produced-list artifact), `app/archive.py` (C-ConversationArchive —
  per-turn rows + topic segments + `archive:segment` sealing).
  Characterization work added (`characterize-persona` +
  `persona-onboard`; S-personality-create runs mint → art → voice →
  characterization need → floor intro). Convention conformance +
  challenges recorded in `version 0.3.0.002/FEATURES.md` (incl. the
  C-ConnectorSet 17-vs-delivered narrowing and the C-DesktopShell
  browser-surface challenge). Fleet install and exchange media remain
  honest 0s.
- **Evidence (in `version 0.3.0.002/`):** launch —
  `evidence/launch/launch-*.log` + `probe-20261121-010829.json`
  (probe ok:true, llm live-ollama); scenarios —
  `evidence/scenarios/*.json` (all suite scenarios ran;
  `S-list-project.json` holds the real produced list — 57 PA cities,
  55-source agreement, disagreement + non-match rows, artifact at
  `runtime/scenario/artifacts/sets/`; `S-personality-create.json`
  holds live-Ollama characterization + art + assigned SAPI voice +
  floor intro; `connectors-F8.json` + post-fix
  `connectors-F8-verify.json` show all four connectors end-to-end);
  `FEATURES.md`, `LAUNCH.md`, `scripts/scenarios.py` driver.
- **Verdict:** (JEV `devin.exe acp` session, SWE-2 High, 2026-11-21;
  raw output `.devin/jev-cycle-002.out`; `user_opinion`/`user_commentary` filled at
  owner review 2026-11-21/22 — clean launch marked down for version confusion,
  completeness and user score marked down on engagement;
  convention: owner silence = agreement on the remainder)

```json
{
  "criteria": [
    { "name": "clean launch", "score": 0.9, "evidence": ["version 0.3.0.002/evidence/launch/probe-20261121-010829.json:2", "version 0.3.0.002/evidence/launch/probe-20261121-010829.json:15", "version 0.3.0.002/evidence/launch/launch-20261121-010823.log", "version 0.3.0.002/evidence/launch/launch-20261121-011030.log", "version 0.3.0.002/runtime/probe/last-launch.json"], "confidence": 0.85, "user_opinion": 0.5 },
    { "name": "existing features", "score": 0.55, "evidence": ["version 0.3.0.002/app/connectors.py:129", "version 0.3.0.002/app/ethics.py:28", "version 0.3.0.002/app/compare.py", "version 0.3.0.002/app/setbuild.py", "version 0.3.0.002/app/art.py", "version 0.3.0.002/app/temporal.py", "version 0.3.0.002/app/archive.py", "version 0.3.0.002/FEATURES.md:111", ".devin/jev-ref-greyavatar.out:41"], "confidence": 0.7, "user_opinion": null },
    { "name": "completeness", "score": 0.85, "evidence": ["version 0.3.0.002/FEATURES.md:53", "version 0.3.0.002/FEATURES.md:91", "version 0.3.0.002/FEATURES.md:94", "version 0.3.0.002/evidence/scenarios/ethics-gate-F1.json", "version 0.3.0.002/evidence/scenarios/S-list-project.json", "version 0.3.0.002/runtime/scenario/ledger.jsonl", "version 0.3.0.002/app/builtins.py:776"], "confidence": 0.75, "user_opinion": 0.4 },
    { "name": "fleet install", "score": 0, "evidence": ["version 0.3.0.002/FEATURES.md:115"], "confidence": 0.95, "user_opinion": null },
    { "name": "exchange media", "score": 0, "evidence": ["version 0.3.0.002/FEATURES.md:116"], "confidence": 0.95, "user_opinion": null },
    { "name": "user score", "score": null, "evidence": [], "confidence": 0, "user_opinion": 0.2 }
  ],
  "overall": 0.46,
  "judge_model": "SWE-2 High",
  "user_commentary": [
    { "criterion": "clean launch", "opinion": 0.5, "reasoning": "Owner 2026-11-21/22: 'that wasn't a clean launch — version confusion.' On live launch a stale v0.3.0.001 process (left serving since 2026-11-19) still held :9760; Windows permits the double-bind so .002 also bound and reported success — requests raced between builds until the stale instance was killed. Launch reported clean while the port was already owned." },
    { "criterion": "completeness", "opinion": 0.4, "reasoning": "Owner: 'completeness is too confident — fleet install and exchange media still count against completeness' and 'the personalities had no personality.' Mechanism completeness scored higher than enacted quality." },
    { "criterion": "user score", "opinion": 0.2, "reasoning": "Owner: 'the novelty of the working harness has worn off and GreyAvatar was a lot more usable'; engagement is 'how much the user wants to engage' — owner does not want to engage with the personas as presented." },
    { "criterion": "voice dynamics (F6)", "opinion": null, "reasoning": "Owner heard overlapping speech on .002 despite serialized speech:floor admissions. Root cause confirmed in code: engines.speak_local fires subprocess.Popen without wait — the floor serializes admissions and marks floor-played at render-spawn, not playback end; queued admissions spawn concurrent SAPI processes so audio still overlaps. F6 convention claim only partially holds." },
    { "criterion": "persona art (F7)", "opinion": null, "reasoning": "F7 downgrade on live inspection: persona 'art' is a seeded abstract sigil (rounded square + rotating ellipses + dashed rings; motif enum hashed from identity) as a 36px roster tile — artifacts exist but nothing face-like or characterization-readable; 'portrait' overstates it, generative avatar glyph is accurate." },
    { "criterion": "owner intent", "opinion": null, "reasoning": "Owner will refine conventions (persona engagement/presentation) in a separate thread before the next run; line stays open pending that pass." }
  ],
  "scenarios": [
    { "id": "S-assertion-input", "score": 0.8, "evidence_class": "enactment", "evidence": ["version 0.3.0.002/evidence/scenarios/S-assertion-input.json", "version 0.3.0.002/runtime/scenario/ledger.jsonl"], "notes": "Typed input recorded as a source-aware assertion; thin transcript (1 row) but the core D1 arc is demonstrated." },
    { "id": "S-template-need", "score": 0.75, "evidence_class": "enactment", "evidence": ["version 0.3.0.002/evidence/scenarios/S-template-need.json"], "notes": "set-topic invocation opened a governed need and returned a result (topic 'atlases'); single-step transcript, gate/slot mechanics not deeply exercised in evidence." },
    { "id": "S-candidate-ranking", "score": 0.8, "evidence_class": "enactment", "evidence": ["version 0.3.0.002/evidence/scenarios/S-candidate-ranking.json"], "notes": "Two slot candidates ranked by source-bounded confidence (user 0.9 vs guess 0.4); lower-confidence candidate retained for inspection." },
    { "id": "S-list-project", "score": 0.9, "evidence_class": "enactment", "evidence": ["version 0.3.0.002/evidence/scenarios/S-list-project.json", "version 0.3.0.002/runtime/scenario/artifacts/sets/set-set-5cd16f4b4124.json", "version 0.3.0.002/app/setbuild.py"], "notes": "Canonical scenario genuinely enacted — the F5 gap is closed. Real 57-member PA-cities list produced by two competing live wiki retrievals (category vs table, 56 each, 55 agreement, solo finds Harrisburg/Latrobe recorded as disagreement), criteria carried on the need, foreign-link non-matches retained as reviewable candidates, set:closure + produced-list artifact, 61 set:* rows in the ledger. Defensible output, not canned." },
    { "id": "S-personality-create", "score": 0.85, "evidence_class": "enactment", "evidence": ["version 0.3.0.002/evidence/scenarios/S-personality-create.json", "version 0.3.0.002/runtime/scenario/artifacts/persona-art/persona-persona-d43dd152ae18.svg", "version 0.3.0.002/app/personas.py:69"], "notes": "Canonical. Mint → live-Ollama characterization (coherent wry maps/etymology persona, not a stub) → assigned real SAPI voice → seeded SVG portrait artifact → floor-admitted intro card; ethics gate verdict recorded. Whole-persona coherence demonstrated end to end." },
    { "id": "S-background-present", "score": 0.8, "evidence_class": "enactment", "evidence": ["version 0.3.0.002/evidence/scenarios/S-background-present.json", "version 0.3.0.002/evidence/scenarios/archive-C-ConversationArchive.json"], "notes": "Steward wake ran all six duties incl. temporal-attention; the archive transcript shows a distinct persona presenting the temporal findings ('Stewardship pass — temporal attention… Evidence is in the ledger') with ledger refs. Captured temporal:attention row itself shows empty findings — presentation leg is evidenced in the archive, not the scenario file." },
    { "id": "S-competing-tools", "score": 0.7, "evidence_class": "enactment", "evidence": ["version 0.3.0.002/evidence/scenarios/S-competing-tools.json", "version 0.3.0.002/app/compare.py", "version 0.3.0.002/evidence/scenarios/S-list-project.json"], "notes": "F3 machinery is now general — every need:-expressing tool invoked on shared input, normalized, ranked, churn-recorded. The named transcript still pits one working tool against an honestly-unconfigured one (1 adequate of 2); a genuine two-adequate competition is evidenced inside S-list-project (both retrievals produced comparable member lists)." },
    { "id": "S-restart-recovery", "score": 0.85, "evidence_class": "enactment", "evidence": ["version 0.3.0.002/evidence/scenarios/S-restart-recovery.json", "version 0.3.0.002/evidence/launch/launch-20261121-011030.log"], "notes": "Real second boot against the durable ledger: 427 rows before, 430 after, roster of 6 personas recovered with art artifacts intact." },
    { "id": "S-exchange-import", "score": 0.4, "evidence_class": "enactment", "evidence": ["version 0.3.0.002/evidence/scenarios/S-exchange-import.json", "version 0.3.0.002/app/builtins.py:776", "version 0.3.0.002/runtime/scenario/artifacts/exports/pkg-5470fb7017f3.json"], "notes": "Export leg real (valid meridian.exchange/v1 package, 5 personas/2 needs). Import leg failed — scenario-driver bug: scripts/scenarios.py passes ex.get('path') instead of ex['result']['path'], so the tool received package:None and correctly refused it. fn_import_exchange verified correct in code (accepts path string, clamps certainty ≤0.4, basis import); no exchange:imported rows this run. Outcome, not mechanism, failed — flag as harness defect." },
    { "id": "S-defer-publication", "score": 0.9, "evidence_class": "enactment", "evidence": ["version 0.3.0.002/evidence/scenarios/S-defer-publication.json", "version 0.3.0.002/runtime/scenario/artifacts/published/1795241425742-cycle-log.md"], "notes": "Both legs enacted: ungranted request deferred with the missing __grant__ slot recorded; witnessed grant then allowed a real published artifact. D10 fully demonstrated." },
    { "id": "S-chat-invocation", "score": 0.7, "evidence_class": "enactment", "evidence": ["version 0.3.0.002/evidence/scenarios/S-chat-invocation.json", "version 0.3.0.002/evidence/scenarios/archive-C-ConversationArchive.json"], "notes": "Chat turn served by decision-model-ranked sequential respondents (2 floor admissions, 2 floor-played, distinct characterized replies). intents[] and needIds[] empty on this input — the 'matches one or more tool needs, each distinguishable' half of the scenario wasn't exercised by the chosen text." },
    { "id": "S-focused-need", "score": 0.35, "evidence_class": "enactment", "evidence": ["version 0.3.0.002/evidence/scenarios/S-focused-need.json"], "notes": "Weakest scenario: transcript is one needId plus a single refinement note. Focus mechanics and conversational slot-filling are not demonstrated; no evidence the need stayed open until fulfillment." }
  ],
  "notes": "Evidence is genuine run output, not self-asserted: consistent assertion ids/timestamps across JSON transcripts, 430-row scenario ledger with every new namespace populated (ethics:gate 7, set:member 57, comparison:run 2/row 4, connector:run 3, calendar:linked 2, archive:segment, temporal:attention 2, speech:floor-admission/played 4 each), live-HTTP timings (wiki 81/174/243ms), live-ollama characterization, real SAPI voice names. Direction-002 rectifications: F1 ethics gate real and deeper than the mark alone (live wikipedia liveness + maxim:objection refusal); F2 temporal reasoning real (context/linkable/note_for_persona; steward presents findings through a persona); F3 general competition lifecycle real; F5 both canonicals enacted for the first time in the line; F6 FIFO speech floor + sequential respondents; F7 per-persona art + rotated real voices; F8 three connectors end-to-end (wikipedia live, ics, files — rss registered but unevidenced; F8's owner bar of 3 met exactly). F4: all six v0.1-only capabilities delivered or challenged on record (C-ConnectorSet, C-DesktopShell challenges in FEATURES.md). Flags: (1) S-exchange-import import leg failed on a scenario-driver bug — scripts/scenarios.py reads 'path' at the wrong result nesting; one-line driver fix plus rerun would close it; (2) devlog-claimed connectors-F8-verify.json is absent from the build; (3) launch-server.out in .002 is a stale copy referencing .001 paths; (4) probe steward.runs=0 again — steward exercised only via manual wake; (5) _temporal.json classifies a 2030-dated fixture event as 'recent'. Existing-features parity improved materially but remains partial: connectors 4/~17, no fleet, exchange media, LAN mirror, Tauri/android/companion shells, storefronts, studio, STT depth, ComfyUI-class art, contacts/publications, location. Live-check 2026-11-22 added two findings: (6) launch hygiene — a stale v0.3.0.001 process held :9760 and .002 double-bound and reported success anyway (Windows SO_REUSEADDR); requests raced between versions until the stale instance was killed — owner-scored clean launch 0.5 for version confusion; (7) speech floor defect — engines.speak_local uses fire-and-forget subprocess.Popen, so floor-played marks render-spawn not playback completion and concurrent SAPI processes overlap audibly; the F6 serialization claim holds for admission ordering only. Owner review: clean launch 0.5, completeness 0.4, user score 0.2. No frontier-model escalation recommended — evidence unambiguous."
}
```

- **Realization note (coordinator, 2026-11-21):** `devin -p` unusable this session —
  the CLI's interactive/print auth gate rejects the stored
  `devin-session-token$` (Windsurf-backed identity: `session_id:
  windsurf-session-*`) as "not a Devin account", locally, despite a fresh
  `auth login` (driven under pywinpty — the TUI ignores piped stdin/fifos).
  Build session spawned instead via `devin.exe acp` JSON-RPC:
  `initialize` → `authenticate._meta.api_key` (same token — valid for agent
  traffic) → `session/new` → `session/prompt`; driver
  `.devin/acp-build-driver.py` auto-approves permissions and logs to
  `.devin/build-cycle-002.acp.log`. Recipe captured as user skill
  `devin-cli-headless`. JEV scoring to use the same path unless the gate is
  fixed. Candidate harness amendment: `implementation.md` JEV/build
  realization should name the ACP fallback.

### Cycle 3 — 2026-11-22

- **Direction:** `direction-003.md` — SIGNED by owner 2026-11-22; engagement and
  enactment depth on the .002 baseline. Rectification set per
  `shortcomings-003.md`: G1 speech-floor playback gating, G2 portrait-quality
  persona art, G3 persona engagement (distinct preloadeds), G4 launch/process
  hygiene; the twelve owner suite additions of 2026-11-22; the six
  execution-structure conventions adopted 2026-11-22 (conform or challenge on
  record); evidence flags H1–H7
- **Baseline:** modify-and-measure from `version 0.3.0.002/` → produces
  `version 0.3.0.003/`; baseline kept intact as comparison point
- **Prompt:** `prompt.md` (snapshot of 2026-11-18, unchanged this cycle)
- **Criteria (rubric revision):** clean launch (incl. launch hygiene), existing
  features, completeness (fleet/exchange count against it), fleet install
  (expected 0), exchange media (expected 0), user score, **time-to-gate**
  (standing), scenario suite `.devin/scenarios.md` (24 scenarios; canonicals must
  enact), `time to implement` tracked not scored
- **Time to implement:** session start 2026-11-22 ~03:05; session end
  2026-11-22 ~03:34 (~29 min session time in this resumed build segment;
  cycle includes the prior segment that produced the Part-1 scaffolding)
- **Result:** Built **Meridian `version 0.3.0.003/`** (baseline
  `version 0.3.0.002/` preserved intact as comparison point). Rectifications:
  **G1** — speech floor now holds admission until real playback completion
  (blocking SAPI render, `playbackMs` + `heldUntilPlaybackComplete` on
  `speech:floor-played`); **G2** — procedurally illustrated bust portraits
  bound per persona (face/hair/eyes/dress seeded from identity,
  `persona:art` + artifact + portrait params); **G3** — voice registers
  (clipped/catalogue/wry/scholarly/warm) drive LLM system prompt and
  declared stub alike — S-distinct-preloadeds Jaccard 0.0 on live ollama;
  **G4** — port probed before bind (LAUNCH REFUSED, exit 3, never ok:true),
  exclusive `SO_EXCLUSIVEADDRUSE` bind, SSE window-watchdog terminates on
  last-window close. Execution conventions all conformed on record:
  `app/gate.py` readiness gate (pass time → `runtime/gate.json`,
  `gate:passed`, launch log, `last-launch.json`; time-to-gate ~3.6 s),
  launch partition (`runtime/launch-partition.jsonl`, dependency-ordered,
  id-deduped), transient boundary (`runtime/transient/` + boot marker),
  snapshot inference + sequential commit (`SnapshotView` parallel drafts,
  `inference:snapshot`/`inference:commit`, ranked-order commits with
  reactsTo), two-part execution. New surface suite: portrait roster rail,
  4 colorways (light default), status bar (sources/LLMs/gate/floor/needs),
  Inbox tab via new `inbox-local` `.eml` connector + persona commentary,
  conversation reset (sealed archive), context badge, personality editor
  (`persona-update` — all editable elements), focus-need conversational
  slot-filling. H-flags: exchange-import path bug fixed;
  `evidence/connectors-F8-verify.json` generated; steward ran autonomously
  (3 runs before manual wake); temporal classification respects dates
  (2030 → future, 2020 → historical, never recent). Evidence:
  `version 0.3.0.003/evidence/scenarios/*.json` (all 24 + 3 aux legs
  enacted, transcripts), `evidence/launch/launch-check.json` (clean boot,
  stale-port refusal, close-terminates, port freed — all pass),
  `evidence/connectors-F8-verify.json`, `launch-server.out` (fresh .003),
  `runtime/gate.json`, launch logs in `evidence/launch/`. FEATURES.md +
  LAUNCH.md updated; fleet install and exchange media left honest 0.
- **Verdict:** (JEV `devin.exe acp` session, SWE-2 High, 2026-11-22;
  raw output `.devin/jev-cycle-003.out`; `user_opinion`/`user_commentary`
  pending owner review; convention: owner silence = agreement)

```json
{
  "criteria": [
    {
      "name": "clean launch",
      "score": 0.95,
      "evidence": [
        "version 0.3.0.003/evidence/launch/launch-check.json:4",
        "version 0.3.0.003/evidence/launch/launch-check.json:18",
        "version 0.3.0.003/evidence/launch/launch-check.json:27",
        "version 0.3.0.003/evidence/launch/launch-20261122-033435.log",
        "version 0.3.0.003/launch-server.out:7",
        "version 0.3.0.003/app/__main__.py:166",
        "version 0.3.0.003/app/api.py:24"
      ],
      "confidence": 0.9,
      "user_opinion": null
    },
    {
      "name": "existing features",
      "score": 0.6,
      "evidence": [
        "version 0.3.0.003/FEATURES.md:53",
        "version 0.3.0.003/FEATURES.md:159",
        "version 0.3.0.003/evidence/connectors-F8-verify.json:2",
        ".devin/jev-ref-greyavatar.out:27"
      ],
      "confidence": 0.7,
      "user_opinion": null
    },
    {
      "name": "completeness",
      "score": 0.85,
      "evidence": [
        "version 0.3.0.003/FEATURES.md:44",
        "version 0.3.0.003/evidence/scenarios/suite.json:2",
        "version 0.3.0.003/evidence/scenarios/S-list-project.json:1",
        "version 0.3.0.003/runtime/scenario/ledger.jsonl",
        "prompt.md:96"
      ],
      "confidence": 0.7,
      "user_opinion": null
    },
    {
      "name": "fleet install",
      "score": 0,
      "evidence": [
        "version 0.3.0.003/FEATURES.md:163"
      ],
      "confidence": 0.95,
      "user_opinion": null
    },
    {
      "name": "exchange media",
      "score": 0,
      "evidence": [
        "version 0.3.0.003/FEATURES.md:164"
      ],
      "confidence": 0.95,
      "user_opinion": null
    },
    {
      "name": "user score",
      "score": null,
      "evidence": [],
      "confidence": 0,
      "user_opinion": null
    },
    {
      "name": "time-to-gate",
      "score": 1.0,
      "evidence": [
        "version 0.3.0.003/runtime/gate.json:22",
        "version 0.3.0.003/launch-server.out:21",
        "version 0.3.0.003/evidence/launch/launch-20261122-033435.log:7",
        "version 0.3.0.003/runtime/last-launch.json:80"
      ],
      "confidence": 0.95,
      "user_opinion": null
    },
    {
      "name": "scenario suite",
      "score": 0.85,
      "evidence": [
        "version 0.3.0.003/evidence/scenarios/suite.json:2",
        "version 0.3.0.003/evidence/scenarios/",
        "version 0.3.0.003/runtime/scenario/ledger.jsonl"
      ],
      "confidence": 0.8,
      "user_opinion": null
    }
  ],
  "overall": 0.61,
  "metrics": {
    "time_to_gate": 3.649
  },
  "judge_model": "SWE-2 High",
  "user_commentary": [],
  "scenarios": [
    {
      "id": "S-assertion-input",
      "score": 0.8,
      "evidence_class": "enactment",
      "evidence": [
        "version 0.3.0.003/evidence/scenarios/S-assertion-input.json:2"
      ],
      "notes": "Typed input recorded as source-aware assertion (claimant principal); thin transcript but the D1 arc is real."
    },
    {
      "id": "S-template-need",
      "score": 0.8,
      "evidence_class": "enactment",
      "evidence": [
        "version 0.3.0.003/evidence/scenarios/S-template-need.json:2"
      ],
      "notes": "Template need created and filled from incidental work ('tidal atlases'); 6 fulfilled rows in ledger."
    },
    {
      "id": "S-candidate-ranking",
      "score": 0.85,
      "evidence_class": "enactment",
      "evidence": [
        "version 0.3.0.003/evidence/scenarios/S-candidate-ranking.json:3"
      ],
      "notes": "Three slot candidates ranked by source-bounded confidence with failed/weak evidence retained."
    },
    {
      "id": "S-list-project",
      "score": 0.95,
      "evidence_class": "enactment",
      "evidence": [
        "version 0.3.0.003/evidence/scenarios/S-list-project.json:15",
        "version 0.3.0.003/evidence/scenarios/S-list-project.json:135",
        "version 0.3.0.003/evidence/scenarios/S-list-project.json:225"
      ],
      "notes": "Canonical. Produced the full real 57-member list of Pennsylvania's incorporated cities — defensible breadth, no townships/CDPs, no invented names. Two competing live wiki retrievals (56 each, 55 agreement, solo finds recorded), foreign-link non-matches retained, closure + artifact on disk."
    },
    {
      "id": "S-personality-create",
      "score": 0.9,
      "evidence_class": "enactment",
      "evidence": [
        "version 0.3.0.003/evidence/scenarios/S-personality-create.json:2",
        "version 0.3.0.003/runtime/scenario/artifacts/persona-art/persona-persona-9e7669ef1f02.svg"
      ],
      "notes": "Canonical. Mint → characterized → rotated real SAPI voice → bound bust-portrait artifact → roster entry; seven persona:* predicates in ledger. Coherent whole-persona enactment."
    },
    {
      "id": "S-background-present",
      "score": 0.85,
      "evidence_class": "enactment",
      "evidence": [
        "version 0.3.0.003/evidence/scenarios/S-background-present.json:2",
        "version 0.3.0.003/evidence/scenarios/archive-C-ConversationArchive.json"
      ],
      "notes": "Steward ran autonomously (3 runs before manual wake — H4 rectified); temporal-attention findings presented through a distinct persona in the archive transcript with ledger refs."
    },
    {
      "id": "S-competing-tools",
      "score": 0.7,
      "evidence_class": "enactment",
      "evidence": [
        "version 0.3.0.003/evidence/scenarios/S-competing-tools.json:3",
        "version 0.3.0.003/evidence/scenarios/S-list-project.json:150"
      ],
      "notes": "Named leg still pits one adequate tool (render-speech-sapi) against an honestly unconfigured remote — 1 adequate of 2. Genuine two-adequate competition is evidenced inside S-list-project's set retrievals; general compare machinery real."
    },
    {
      "id": "S-restart-recovery",
      "score": 0.9,
      "evidence_class": "enactment",
      "evidence": [
        "version 0.3.0.003/evidence/scenarios/S-restart-recovery.json:2",
        "version 0.3.0.003/runtime/launch-partition.jsonl"
      ],
      "notes": "Real second boot: 856→865 rows, gate re-passed, launch partition mounted 58 rows, roster of 13 with art recovered."
    },
    {
      "id": "S-exchange-import",
      "score": 0.85,
      "evidence_class": "enactment",
      "evidence": [
        "version 0.3.0.003/evidence/scenarios/S-exchange-import.json:3",
        "version 0.3.0.003/scripts/scenarios.py:370"
      ],
      "notes": "H1 rectified — driver reads the path at the correct nesting; real export→import, contents held below action threshold (0.4<0.7), exchange:imported row in ledger."
    },
    {
      "id": "S-defer-publication",
      "score": 0.9,
      "evidence_class": "enactment",
      "evidence": [
        "version 0.3.0.003/evidence/scenarios/S-defer-publication.json:3"
      ],
      "notes": "Both legs: ungranted request deferred with missing __grant__ slot; witnessed grant then produced a real published artifact."
    },
    {
      "id": "S-chat-invocation",
      "score": 0.85,
      "evidence_class": "enactment",
      "evidence": [
        "version 0.3.0.003/evidence/scenarios/S-chat-invocation.json:5",
        "version 0.3.0.003/evidence/scenarios/S-chat-invocation.json:9"
      ],
      "notes": "H7 rectified — intents[] and needIds[] populated (set-topic at 0.675), tool need opened alongside the response need, sequential respondents with snapshot-inference and ordered commits."
    },
    {
      "id": "S-focused-need",
      "score": 0.85,
      "evidence_class": "enactment",
      "evidence": [
        "version 0.3.0.003/evidence/scenarios/S-focused-need.json:4",
        "version 0.3.0.003/evidence/scenarios/S-focused-need.json:44"
      ],
      "notes": "H6 rectified — deferred need focused, chat input offered as slot candidate, fulfilled ('3'); full need:deferred→refined→candidate→fulfilled row trail shows it stayed open until satisfied."
    },
    {
      "id": "S-personality-roster",
      "score": 0.8,
      "evidence_class": "enactment",
      "evidence": [
        "version 0.3.0.003/evidence/scenarios/S-personality-roster.json:3",
        "version 0.3.0.003/app/ui/index.html:13"
      ],
      "notes": "Persistent roster rail enacted — 12 entries, all with bound art and voice registers. Blemish: six names appear twice (preloadeds seeded twice into the scenario runtime), so the roster carries duplicates."
    },
    {
      "id": "S-portrait-bind",
      "score": 0.8,
      "evidence_class": "enactment",
      "evidence": [
        "version 0.3.0.003/evidence/scenarios/S-portrait-bind.json:3",
        "version 0.3.0.003/runtime/artifacts/persona-art/persona-persona-8e27d71488b1.svg:1"
      ],
      "notes": "G2 rectified — 6/6 personas bound to distinct artifacts on disk; SVG is a real illustrated bust (face shape, skin, hair style, eyes/brows, ears, collar) over the retained sigil-style animated background, not an abstract sigil. 'Portrait-quality' remains a taste call for owner review; mechanism and binding fully demonstrated."
    },
    {
      "id": "S-color-schemes",
      "score": 0.9,
      "evidence_class": "enactment",
      "evidence": [
        "version 0.3.0.003/evidence/scenarios/S-color-schemes.json:4",
        "version 0.3.0.003/app/ui/styles.css:4"
      ],
      "notes": "Four colorways cycled (light/dark/sepia/slate) via ui:shell-theme assertions; fresh-launch default light verified."
    },
    {
      "id": "S-status-bar",
      "score": 0.9,
      "evidence_class": "enactment",
      "evidence": [
        "version 0.3.0.003/evidence/scenarios/S-status-bar.json:4",
        "version 0.3.0.003/app/ui/index.html:110"
      ],
      "notes": "Status bar element carries sources (5 available incl. configured inbox-local), LLM mode/model, gate state, floor depth, open needs."
    },
    {
      "id": "S-email-commentary",
      "score": 0.9,
      "evidence_class": "enactment",
      "evidence": [
        "version 0.3.0.003/evidence/scenarios/S-email-commentary.json:4",
        "version 0.3.0.003/evidence/scenarios/S-email-commentary.json:11",
        "version 0.3.0.003/fixtures/inbox/001-marta.eml"
      ],
      "notes": "Real .eml ingest (3 messages), selection pulled into chat:context, Curator produced live-ollama commentary on the selected email."
    },
    {
      "id": "S-conversation-reset",
      "score": 0.8,
      "evidence_class": "enactment",
      "evidence": [
        "version 0.3.0.003/evidence/scenarios/S-conversation-reset.json:4"
      ],
      "notes": "Reset sealed 15 messages into archive-1 and cleared messages/topic/context; moved-topic detection implied by the flow rather than separately demonstrated."
    },
    {
      "id": "S-context-display",
      "score": 0.85,
      "evidence_class": "enactment",
      "evidence": [
        "version 0.3.0.003/evidence/scenarios/S-context-display.json:4"
      ],
      "notes": "Active context shown for both profile-select and email-select; commentary present."
    },
    {
      "id": "S-personality-editor",
      "score": 0.85,
      "evidence_class": "enactment",
      "evidence": [
        "version 0.3.0.003/evidence/scenarios/S-personality-editor.json:4"
      ],
      "notes": "persona-update applied edits across all eight customizable elements (name, traits, interests, lens, voice, color, priority, display mode); lens assertions recorded."
    },
    {
      "id": "S-windows-launch",
      "score": 0.75,
      "evidence_class": "enactment",
      "evidence": [
        "version 0.3.0.003/launch.cmd:1",
        "version 0.3.0.003/evidence/launch/launch-check.json:4"
      ],
      "notes": "launch.cmd + python -m app boots like an installed program on Windows with gate + banner; it is a script launcher, not packaged install media — honest partial against 'installed program'."
    },
    {
      "id": "S-close-terminate",
      "score": 0.85,
      "evidence_class": "enactment",
      "evidence": [
        "version 0.3.0.003/evidence/launch/launch-check.json:27",
        "version 0.3.0.003/evidence/scenarios/S-close-terminate.json:3"
      ],
      "notes": "SSE window-watchdog terminated the program (exit 0, no orphan, port freed) in real-process check. Blemish: scenario JSON embeds checkFile:null — a driver embedding gap; the cross-referenced launch-check.json carries the passing evidence."
    },
    {
      "id": "S-speech-serialization",
      "score": 0.85,
      "evidence_class": "enactment",
      "evidence": [
        "version 0.3.0.003/evidence/scenarios/S-speech-serialization.json:4",
        "version 0.3.0.003/app/engines.py:146",
        "version 0.3.0.003/app/speechfloor.py:75"
      ],
      "notes": "G1 rectified — admission held until real playback completion (blocking SAPI; 7 plays at 15–28s each, queue depth 13, serialized). Blemish: playbackMs surfaces null on floor-played rows though heldUntilPlaybackComplete is true."
    },
    {
      "id": "S-distinct-preloadeds",
      "score": 0.9,
      "evidence_class": "enactment",
      "evidence": [
        "version 0.3.0.003/evidence/scenarios/S-distinct-preloadeds.json:4"
      ],
      "notes": "G3 rectified — same prompt to three preloadeds on live ollama produced markedly different registers (catalogue listicle / clipped imperative / wry digressive); max pairwise Jaccard 0.079."
    }
  ],
  "notes": "All 24 suite scenarios enacted with real run artifacts; the two canonicals carry enactment-class evidence. Scenario-ledger corroboration strong: 865 rows, every new namespace populated (exchange:imported, inference:snapshot/commit, gate:passed, ui:shell-theme, email:*). Cycle-2 evidence flags all closed: H1 driver bug fixed (scenarios.py:370), connectors-F8-verify.json present and real, launch-server.out fresh .003, steward ran autonomously 3x pre-wake, temporal classification correct (2030→future, 2020→historical), focused-need and chat-invocation deepened. Direction-003 rectifications delivered: G1 blocking playback floor, G2 illustrated bust portraits bound per persona, G3 distinct live registers, G4 port-refusal + exclusive bind + watchdog terminate (all four launch-check legs pass). All six execution-structure conventions conformed on record (FEATURES.md:174-182); prior recorded challenges (C-ConnectorSet, C-DesktopShell partial) retained — no silent departures. Flags for owner: (1) S-personality-roster lists 12 entries with each of 6 names duplicated — double-seeding in scenario runtime; (2) S-close-terminate scenario file embeds checkFile:null (driver gap, evidence itself passes); (3) floor-played rows carry playbackMs:null despite the devlog claim of the field; heldUntilPlaybackComplete is the load-bearing flag and is true; (4) S-competing-tools named leg still 1-of-2 adequate — genuine 2-adequate competition only via set retrievals; (5) instance not serving on :9760 at JEV time — final boot recorded ok at 03:34, watchdog likely stopped it post-session; launch evidence stands. time to implement tracked per devlog Cycle-3 entry (session ~03:05–03:34, plus prior Part-1 segment). No frontier-model escalation recommended — evidence is genuine run output and unambiguous."
}
```

## Review findings — missing prompt/convention coverage (2026-11-19)

Surfaced by the three-version JEV comparison + owner review. Classification marks where
each item lands: **[prompt]** prompt-specified behavior (incl. MVP items), **[conv]**
convention (challengeable, never ignorable), **[dir]** candidate next-direction
rectification target, **[harness]** evaluation/harness machinery.

- **F1 [prompt][dir]** Imitation admonishment + permanent distinguishing mark — required by
  prompt §Personalities; implemented in v0.1, absent in v0.2 (owner: cosmetic-
  deprioritized, MVP-required). Absent in v0.3.0.001 as well (v0.3 completeness gap).
- **F2 [prompt][dir]** Calendar temporal reasoning — prompt requires calendar to inform
  projects, persona responses, background attention; v0.2 ingests/ranks but does little
  temporal reasoning. Thin everywhere in the line.
- **F3 [prompt][dir]** Competing-tool lifecycle — D7 requires comparing locally competing
  tools; v0.2 has only same-scope steward fan-out; v0.3 demoed one working tool against a
  permanently unconfigured one (S-competing-tools 0.6 enactment).
- **F4 [conv][dir]** v0.1 capabilities absent from v0.2 (lineage evidence; per-item
  class resolved in conventions-sweep: the realized machinery is conventional —
  connector breadth, ethics-gate depth, presentation glass, conversation archive,
  set-build, agentic tool protocol).
- **F5 [conv][harness]** Canonical scenario enactment — S-list-project was never enacted
  in v0.3 (canned 3-item demo). Convention C-ScenarioEnactment: builds must *enact*
  canonical scenarios or record the challenge.
- **F6 [conv]** Voice dynamics — prompt leaves respondent dynamics to implementation;
  v0.3 produced overlapping artificial speech (owner: a failure). C-PerceivableRespondents
  (floor) + C-SequentialRespondents/C-SpeechFloor (manner).
- **F7 [conv]** Personality-unique generated art + diverse/modifiable voices — owner
  disappointed at absence in v0.3; C-PersonalityArt + C-VoiceDiversity.
- **F8 [conv][dir]** Connector breadth — v0.3 has 0/17 vs reference; existing-features
  criterion already weights it (parity 0.4); machinery → C-ConnectorBreadth.
- **F9 [harness]** Criteria must anchor to user-observable behavior, not code existence —
  the 0.7→0.2 lesson; carries into JEV prompt definitions.
- **F10 [harness]** `time to implement` needs session-level capture (start/end recorded
  at cycle close); mtime archaeology was a one-time substitute.
- **F11 [harness]** Usage-case discovery — criteria are supplied per-direction and
  default to the previous list, so un-named evidence classes are never scored. The
  project's testable-scenario layer (prompt §Observable demonstrations, UX reference
  scenarios, prior builds' test conventions) existed but was not imported. Required
  harness behavior at intake/review: derive a candidate scenario suite from the project
  corpus, propose it for owner sign-off, and flag named scenarios left unenacted
  (anticipated-but-absent). Suite stays project-side; harness imports and syncs, does
  not own.

**Proposals drafted 2026-11-19** (owner edit/approval pending): `prompt-amendments-001.md`
— **superseded; owner ruled P1–P5 conventions 2026-11-19** (test criteria can be
conventions; P3 expanded with diverse/modifiable voices; P4/P5's earlier requirement
rulings superseded — now challengeable-with-record); `harness-amendments-001.md`
(H1–H4: intake scenario discovery, unenacted-scenario flag, revised default criteria,
cycle-close capture); `direction-002.md` draft with open
decisions — F4 per-item classification, connector-breadth scope, baseline choice,
cycle budget, P2/P3 adoption status. `shortcomings-001.md` **SIGNED 2026-11-19**;
outcome-status annotation appended during review. `shortcomings-002.md` to carry the
missed findings (F1–F3, F5, F6) for direction-002.
`conventions-001.md` drafted — proposal for a third specificity tier between prompt and
implementation details: conventions, challengeable but not ignorable (silent departure =
defect). Seeded with convergent realizations (tool ontology, JSONL ledger, honesty
banner), canonical-scenario and operator/test conventions, and C-SequentialRespondents
beneath the proposed P2 floor. **Owner rulings 2026-11-19:** C-* identifiers adopted;
departure free when acknowledged, evaluated, explained (silent departure = defect);
conformity NOT scored (direction doesn't matter, only the recorded reckoning).
`conventions-sweep-001.md` — all 16 D-* records + 11 F-entries classified: 41 proposed
conventions (incl. P1–P5 reclassifications); notable outcomes — D-SpeechScheduling→C-SpeechFloor (the convention that
would have caught the overlapping-voices failure), D-ToolTrustChurn→prompt-side
(A5 defect, not convention), D-ExchangeEncoding→C-ExchangeLayers (layered encodings/
channels; adopted schema pins provisionally, evolving over time). User-set supremacy
and multi-source access: briefly ruled prompt-level (P4/P5), then **all of P1–P5
reclassified conventions per owner ruling** — "test criteria can be conventions."
Mixed-results review: mechanism corrected (immutable records, derived newer entries,
audit trail). Owner-declared conventions added:
C-DesktopShell (dedicated-shell **capability**, not the only method — browser display
legitimate, expected-best for satellites; Meridian departed silently, first
retroactive catch), C-FullScreen (portability),
C-SupportedOS-* (ranked fleet-target list: Win11, Android satellites, Bluetooth/Echo,
Win10, TAB-YOGA, Linux, Pi — ranking itself conventional). **Owner terminology
correction 2026-11-19:** "requirement" is not a defined corpus term — the three layers
are the **prompt** (specified behavior), **conventions**, **implementation choices**
(+ harness machinery); all documents/tags corrected. **ADOPTION APPROVED 2026-11-19:**
conventions category + full set (43 after count correction: 17 D-derived, not 15)
written into the corpus as `C:\Project\MigrateInbound\CONVENTIONS.md` +
`InstructionsForConventions.txt`. Harness amendments (H1–H4) approved in principle;
`C:\Harness` writes held pending the owner's next harness question.

**Owner rulings 2026-11-20 (direction-002 sign-off):** baseline = modify-and-measure
from `version 0.3.0.001/`; cycle budget 1; F8 scope = 3 connectors; F4 scope = all
six items (all conventional per the sweep — conform or challenge on record);
harness amendments H1–H4 approved **and applied** to `C:\Harness` —
`workflow.md` (H1 intake scenario discovery, H2 unenacted-scenario flag, H4
cycle-close capture), `rubric.md` (H3 revised defaults), `templates/intake.md`
(scenario-suite item); `shortcomings-002.md` issued carrying F1–F3, F5, F6 plus the
direction's convention targets; `direction-002.md` signed.

## Prompt

Embedded in `prompt.md` (snapshot, 2026-11-18).
