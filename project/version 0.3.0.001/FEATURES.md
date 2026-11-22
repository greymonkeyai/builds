# FEATURES.md — Meridian (version 0.3.0.001) capability manifest

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
| Competing tools for the same need (`need:` expression) compared locally | parity | demo 7 |
| **Bounded decision model for routing/evaluation — fixed feature vector, weighted sum, weights as ledger config, `decision:score`/`decision:respondent` traces, O(#tools×7) per decision** | **new (A9)** | `app/decision.py` |
| **Tool-trust churn: inadequate/failed results lower a bounded rank multiplier [0.1–1.0] among alternatives without making the tool ineligible; successes recover it** | **new (A5 / D-ToolTrustChurn)** | `decision.record_outcome`, demo 7 |
| **Novice tool authoring: `validate-tool` (errors + warnings + repair hints), `create-tool`/`edit-tool`/`inspect-tool` with telemetry view** | **new (A10)** | `fn_validate_tool`, Workshops tab |
| 68 registered components at launch (30+ tools, 12 commands, 12 primitives) | parity-scale | registry manifest, probe |

## Personalities

| Capability | Class | Where |
|---|---|---|
| Persistent persona identities outside the ledger (`runtime/personalities.json`); `persona:*` assertions as ledger view | parity | `app/personas.py` |
| Mint/edit persona, deterministic geometric SVG portrait + artifact | parity | `persona.mint`, `PortraitEngine` |
| Imitation boundary: user admonished at mint; permanent `◆ IMITATION` mark on display + ledger rows | parity | `personas.mint`, demo-adjacent |
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
| TTS: `speak-voice` ranks renderers; local SAPI synthesis | parity-level | `fn_speak_voice` |
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
| Calendar: ICS/JSON import → `calendar:event` source-evidence; steward scans upcoming; project linking | parity-level | `fn_import_calendar`, `link-calendar` |
| `run-search` + adequacy gate (`search:run`, `search:adequacy`, `source:use` witnesses) | parity | `_run_search` |
| `endorse-source` / `set-import-trust` raising inherited confidence | parity | `endorse-source` |
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
| Live network connectors (Gmail/Calendar OAuth, YouTube, etc.) | not implemented (local artifacts + ICS import) |
| Perception/webcam pipeline, soundscape | not implemented |

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
