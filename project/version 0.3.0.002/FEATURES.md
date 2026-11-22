# FEATURES.md — Meridian (version 0.3.0.002) capability manifest

**Direction-002 build.** Rectifies the shortcomings-002 set (F1–F8) on top of
the 0.3.0.001 baseline. New machinery this cycle: `app/ethics.py`,
`app/speechfloor.py`, `app/art.py`, `app/temporal.py`, `app/connectors.py`,
`app/compare.py`, `app/setbuild.py`, `app/archive.py`. Enactment evidence:
`evidence/scenarios/*.json` (real run transcripts) + `runtime/artifacts/`.

Classification: **parity** = functional coverage of a feature GreyAvatar
delivers; **new** = capability beyond the reference (incl. rectified
shortcomings); **absent** = not implemented (declared, not faked).

Reference: `C:\Users\kris_\CursorProjects\GreyAvatar`. This build is a fresh
Python-stdlib implementation — no code ported; architecture re-derived from
`prompt.md`.

## Truth model

| Capability | Class | Where |
|---|---|---|
| Append-only assertion ledger, durable JSONL, restart reload | parity | `app/ledger.py` |
| Typed values (`string/number/boolean/enum/ref/list/map`), closed claimant vocabulary, governed predicate namespaces | parity | `app/model.py`, `app/governance.py` |
| Computed views (`render_view`): supersession + trust resolution at read time; no second store | parity | `ledger.render_view` |
| Source-bounded confidence: effective = min(certainty, context, source ceiling); recency breaks ties | parity | `ledger.effective_confidence` |
| Basis kinds: captured-input / interpretation / source-evidence / generated / execution / user-choice / durable-result / import / refusal | parity | `model.BASIS_KINDS` |
| Candidate slots inspectable with source + confidence until a tool selects | parity | `ledger.candidates_for`, `needs.candidates` |
| Contextual confidence (applicability) carried separately from certainty | parity | `Assertion.context` |

## Components & needs

| Capability | Class | Where |
|---|---|---|
| Component ontology: tool (data) / system-command (`object.verb`) / primitive (closed allow-list) | parity | `app/tools.py`, `app/builtins.py` |
| Tool-logic-as-data: closed-op interpreter (`set/query/search/view/candidates/append/appendEach/when/invoke/invokeEach/engine/emit/repeat/result/fail`), no eval | parity | `app/dsl.py` |
| Single write seam `ledger.append`; other stores via system commands | parity | `ctx.append`, `COMMANDS` |
| Unmet needs (`need:*`): open floor, gate eval, defer/cancel/supersede/fulfill, `need.fulfill` command | parity | `app/needs.py`, `tools.fulfill_need` |
| Templates: required/optional slots, `minCertainty`, grant requirement | parity | `spec.template`, `tools.evaluate_gate` |
| Consumable, scoped, witnessed, lockable grants; ungranted consequential request = recorded deferral | parity | `tools.issue_grant`…, demo 10 |
| Deferred work: missing slots leave need open with `need:deferred`; refinement via related assertions | parity | `needs.defer_need`, `needs.refine_need` |
| **Competing-tool lifecycle (F3): general `compare-run` machinery — every tool expressing a `need:` is invoked on the same input, results normalized to a shared understanding, ranked; each `comparison:row`/`comparison:run` recorded; outcomes feed trust churn** | **new (F3)** | `app/compare.py` |
| Genuinely competing retrieval tools: `retrieve-set-wiki-table` vs `retrieve-set-wiki-category` (both `set.members`, different live strategies, comparable members) + `render-speech-sapi` vs `render-speech-remote` (`speech.render`) | **new (F3)** | `app/setbuild.py`, speech tools |
| **Bounded decision model for routing/evaluation — fixed feature vector, weighted sum, weights as ledger config, `decision:score`/`decision:respondent` traces, O(#tools×7) per decision** | **new (A9)** | `app/decision.py` |
| **Tool-trust churn: inadequate/failed results lower a bounded rank multiplier [0.1–1.0] among alternatives without making the tool ineligible; successes recover it** | **new (A5 / D-ToolTrustChurn)** | `decision.record_outcome`, demo 7 |
| **Novice tool authoring: `validate-tool` (errors + warnings + repair hints), `create-tool`/`edit-tool`/`inspect-tool` with telemetry view** | **new (A10)** | `fn_validate_tool`, Workshops tab |
| 68 registered components at launch (30+ tools, 12 commands, 12 primitives) | parity-scale | registry manifest, probe |

## Personalities

| Capability | Class | Where |
|---|---|---|
| Persistent persona identities outside the ledger (`runtime/personalities.json`); `persona:*` assertions as ledger view | parity | `app/personas.py` |
| Mint/edit persona; **unique generated art per persona** — motif family from interests, palette from identity, ambient SVG motion, portrait frame, artifact + `persona:art` assertion (C-PersonalityArt / C-PresentationGlass) | **new (F7)** | `app/art.py`, `fn_generate_portrait` |
| **Ethics gate (F1): every mint passes liveness research through the wikipedia connector + maxim:objection patterns; verdicts allowed / mark-required / admonish-required / refused; gate cards + `ethics:gate` rows; refusals recorded (`persona:mint-refused`, basis refusal)** | **new (F1)** | `app/ethics.py`, `personas.mint` |
| Imitation boundary: user admonished at mint; permanent `◆ IMITATION` mark on display + ledger rows + art corner badge | parity | `personas.mint`, `art.render_art` |
| **Characterization work: `characterize-persona` (LLM/declared-template lens summary → `persona:characterization`) opened as a real need and served during `persona-onboard`** | **new (F5)** | `fn_characterize_persona`, `fn_persona_onboard` |
| **Diverse modifiable voices (C-VoiceDiversity): mint assigns a rotated SAPI voice + rate as a `persona:voice` assertion; `persona-voice-set` modifies; SAPI voice enumeration is real** | **new (F7)** | `personas._assign_voice`, `TTSEngine.voices`, `fn_persona_voice_set` |
| **Respondent selection through the decision model (lens overlap, topic links, confidence, priority; `chat:response-depth` caps count) — not coded rotation** | **new (A6)** | `select_respondents`, `decision.rank_personas` |
| **Non-anthropomorphic presentation: personas are "lenses/respondents"; `user:persona-frame` selects `respondent`/`personified` display; no avatar vocabulary required** | **new (A12)** | `personas.frame`, Settings |
| Distinct characterized replies per persona via lens (LLM when live; template fallback declared) | parity | `compose_for` |

## Turn chain & surfaces

| Capability | Class | Where |
|---|---|---|
| Chat turn: captured-input assertion → decision-model intents → `need:tool-request` per intent + `need:response` → drain → compose → `persona.speak` card | parity | `fn_run_chat_turn` |
| One input can open several tool opportunities AND a conversation response | parity | `fn_parse_chat` |
| Cards feed (persona / offer / witness kinds) routed via bus, replayable | parity | `host.Bus`, UI feed |
| Chat lane: clear-chat boundary marker (append-only), set/close topic, all-chat flag | parity | chat lane tools |
| Cross-turn memory: history since last clear-chat read into compose prompts — on all conversation paths | parity+ (their open deficit) | `chat_history` |
| Web UI: chat, roster, command center, library, workshops, exchange, settings, log; honesty banner | parity-level | `app/ui/` |
| **Command center: projects + open-need queue + focus/calendar + grant requests on one surface; explicit create-project affordance** | **new (A4)** | Command tab |
| **Library: assertion browser/search + computed-view inspector + append-only assertion editing (supersession supported)** | **new (B: library-mediated editing)** | Library tab, `/api/library/*` |
| **Workshops: one generic renderer derives forms from `tool.template` (relationship-driven form derivation); proficiency tier disclosure** | **new (B / A10)** | `openWorkshop`, `set-editor-proficiency` |
| Mic: browser Web Speech → `device:speech-transcript` witness → turn; absent API declared, not faked | parity | UI mic, `transcribe-speech` |
| TTS: `speak-voice` ranks renderers; local SAPI synthesis with per-persona voice/rate | parity | `fn_speak_voice` |
| **Speech floor (F6/C-SpeechFloor): serialized FIFO playback admission — one render at a time; every admission + playback is a ledger assertion (`speech:floor-admission`, `speech:floor-played`)** | **new (F6)** | `app/speechfloor.py`, `cmd_persona_speak` |
| **Sequential respondents (F6): ranked roster order = speaking order; each reply card + floor admission carries its sequence; `decision:respondent` rows record it** | **new (F6)** | `fn_serve_response_need` |
| **Speech as independently-defined competing tools (local `render-speech-sapi` vs remote `render-speech-remote`, both need `speech.render`, ranked by outcomes; remote honestly unconfigured)** | **new (A13)** | speech tools |
| Soundscape / camera / gallery theater | **absent** | declared |

## Stewardship, projects, sources

| Capability | Class | Where |
|---|---|---|
| Background steward: daemon thread running `steward-tick` tool; drains needs, countdown needs, calendar scan, source-confidence, compact-check; each run recorded (`idle:steward-run`, ms) | parity | `app/steward.py`, `fn_steward_tick` |
| **Stewardship configurable as ledger data: duties + interval via `assign-stewardship` (`routing:stewardship-assignment`), per-duty toggles** | **new (A3 / D-IdleTurnAsTool)** | `assign-stewardship`, Settings |
| Responsiveness: steward never holds request path; probe measures API answer while tick runs | parity | `steward.py`, probe |
| Projects: `project:*` subjects, goals as assertions, goals → linked needs, progress visible; create via chat | parity | `_create_project`, Command tab |
| **Goal→need decomposition + project-linked queue/progress states user-facing** | **new (A4/B)** | `/api/projects`, demo 11 |
| Calendar: ICS/JSON import → `calendar:event` source-evidence; project linking | parity | `fn_import_calendar`, `link-calendar` |
| **Temporal reasoning (F2): `temporal_context` interprets events into current/upcoming/recent; project linking by goal-token overlap (`calendar:linked`); steward `temporal-attention` duty presents findings through a lens-matched persona; `note_for_persona` injects live calendar context into replies** | **new (F2)** | `app/temporal.py`, steward duty, `compose_for` |
| `run-search` + adequacy gate (`search:run`, `search:adequacy`, `source:use` witnesses) | parity | `_run_search` |
| `endorse-source` / `set-import-trust` raising inherited confidence | parity | `endorse-source` |
| **Connector framework + 4 real connectors (F8): `wikipedia` (live API/HTML: summary, search, category members — backs set retrieval, search fan-out, ethics liveness), `ics-calendar` (local file → calendar:event), `files` (local dir → source-evidence with sha256 + excerpt), `rss` (live feed → items). Configured via `connector:configured`; every ingest writes `connector:run` — unreachable connectors report `error`, never fabricate** | **new (F8)** | `app/connectors.py` |
| **Set-build (C-SetBuild, S-list-project): geographic set fulfillment — `set-project-open` creates project + `set-members` need with criteria slots; competing retrievals unioned with agreement/disagreement recorded; non-matches (headers, foreign links, category errors) retained as reviewable `need:candidate` rows; `set:closure` + produced-list JSON artifact** | **new (F4/F5)** | `app/setbuild.py`, `fn_build_list` geo path |
| **Conversation archive (C-ConversationArchive): computed per-turn rows + topic segments bounded by topic-change/clear-chat; `archive:segment` durable-result sealing** | **new (F4)** | `app/archive.py`, `/api/archive` |
| **Success-driven source-confidence adaptation in steward/cleanup (bounded ±0.05 after ≥2 outcomes)** | **new (A8)** | `adjust_source_confidence` |
| Governed cleanup: `ledger.compact` consolidates spent operational rows; `cleanup:compacted` summary preserves removed ids + superseding row (provenance) | parity | `ledger.compact`, `fn_cleanup_run`, demo 8 |

## Exchange & effects

| Capability | Class | Where |
|---|---|---|
| `meridian.exchange/v1` package import: personas/tools/needs/assertions recorded **below action threshold** (`claimant exchange:*`, ceiling 0.4) pending local resolution | parity | `fn_import_exchange`, demo 9 |
| Package export (personas + authored tools + open needs) to file artifact | parity-level | `fn_export_exchange` |
| Grant-gated consequential effects: `send-mail` (honest local `.eml` outbox), `dispatch-home-routine` (actuation artifact), `publish-milestone` (file artifact) — no silent sends | parity-level | vessel tools |
| Seed packs (2) loaded once with `seed:*` claimant | parity | `seed-packs/` |
| Honesty banner: engine modes + stub declarations on console + UI + `launch:honesty` assertion | parity | `banner`, `#honesty` |
| Launch evidence: launch log per boot + `last-launch.json` + probe artifact | parity | `evidence/launch/` |

## Absent (declared, expected score 0)

| Criterion feature | Status |
|---|---|
| **Fleet install** (A2/A11): multi-device joiner installers, LAN pairing/mirror, capability-discovery wizard | not implemented — no fleet code; expected 0 |
| **Exchange media** (A7): print-to-scan, QR/AVQR encode/scan/validation | not implemented — file-based package import only; expected 0 |
| LAN viewer/mirror transport, Tauri/native desktop shell | not implemented (browser surface only) |
| OAuth/account connectors (Gmail, YouTube, etc.) | not implemented — declared; the 4 delivered connectors are real and end-to-end |
| Perception/webcam pipeline, soundscape | not implemented |

## Convention conformance / recorded challenges (direction-002)

Conventions are challengeable, never ignorable. Recorded challenges for the
v0.1-only set (F4) and related conventions:

| Convention | Conform / challenge | Record |
|---|---|---|
| C-JsonlLedger, C-LocalIndices, C-DyadicConfidence, C-CertaintyPrivilege, C-UnmetNeedRecords, C-AcceptanceChecks, C-MultiSourceAccess, C-CompetingSources, C-SpecializedListRetrieval, C-ConfiguredAccounts, C-ConvergentOntology | conform | carried from baseline; unchanged semantics |
| C-EthicsGate | **conform+** | gate now does liveness research via the live wikipedia connector + maxim:objection refusals + cards; imitation mark is a floor, not the whole gate |
| C-PresentationGlass | conform | persona art asset pipeline: seeded composition, portrait frames, ambient SVG motion, artifacts + `persona:art` rows, re-render supersedes |
| C-ConversationArchive | conform | `archive-view` computed segments + per-turn rows + `archive:segment` sealing |
| C-SetBuild | conform | `setbuild.py` — competing retrievals, criteria on the need, non-match classes retained, closure + artifact |
| C-AgenticProtocol | conform | need→gate→invoke→outcome/churn protocol is the tool lifecycle; `compare-run` generalizes competition over it |
| C-ConnectorSet | **challenge (recorded)** | convention describes a 17-connector catalog; owner direction-002 scopes this cycle to 3 real runnable connectors — 4 delivered (wikipedia, ics-calendar, files, rss), all end-to-end. Evaluation: machinery is general (`CONNECTORS` registry + configured-source assertions); breadth beyond the delivered set is connector-authoring, not new machinery |
| C-PerceivableRespondents, C-SequentialRespondents, C-SpeechFloor | conform | floor serializes playback; sequence indices on cards + `decision:respondent` rows |
| C-PersonalityArt, C-VoiceDiversity | conform | `art.py` unique art; rotated real SAPI voices + `persona:voice` modifiable assertions |
| C-ScenarioEnactment, C-CanonicalScenarios | conform | `evidence/scenarios/*.json` are live-run transcripts, not source inspection |
| C-DeclaredStubs, C-HonestyBanner | conform | banner + `launch:honesty` rows; remote TTS/OAuth connectors declared unconfigured |
| C-DesktopShell / C-FullScreen / ranked-OS | **challenge (recorded)** | browser surface retained from baseline — no dedicated shell this cycle; owner direction did not scope a shell and GreyAvatar parity is measured against delivered functionality, not platform form factor |

## Honesty notes

- `llm` engine: `live-ollama` when reachable (model picked from `/api/tags`,
  preferring text models), otherwise `stub` — the fallback reply text itself
  declares `[declared stub]`; the banner always shows the mode.
- `render-speech-remote` is registered and competes, but honestly reports
  `unconfigured` until a source grant exists — it never substitutes silently.
- `mail.outbox_write` writes `.eml` artifacts to `runtime/outbox/` — it claims
  local queueing, never network delivery.
- Host-backed `fn` tools are marked `hasFn` in the component manifest (a
  declared divergence from the reference's all-data posture for
  orchestrators); user-authored tools are data-only and validated.
