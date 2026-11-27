# Scenario suite — project line of development
<!-- harness-doc kind=suite status=in-force applies-to=cycle-6 -->

Per-scenario evaluation criteria for JEV verdicts and owner review. Each scenario scores
0–1 on the implementation's **ability to enact** it. Suite is evolvable at review points
(rubric revision 2026-11-19: scenario suite added alongside `completeness`).
Consolidated 2026-11-25: check specs merged in from `scenario-checks.md` (superseded);
suite faceted by surface; check forms named; delta tiers (new/amended/carried) removed —
the checks below are the current contract, not a changelog.

## Scoring conventions

- **Evidence class:** `enactment` (the build ran or its run artifacts/transcripts/logs
  demonstrate the scenario — strongest) or `repository` (mechanism confirmed present and
  plausibly enactable — weaker; used for reference builds assessed without launch).
  Record the class per scenario; do not pretend repository evidence is enactment.
- **Score the outcome, not just the mechanism.** A scenario fails if the machinery exists
  but the produced result is wrong, incoherent, or violates the scenario's stated bar.
- **User path (C-UserPathEnactment).** Every check exercises the path a user takes —
  owner-facing surfaces, natural chat, real devices. Mechanism-only evidence is
  repository-class at best. This applies to all checks below without restatement.
- Sources: `prompt.md` §Observable demonstrations (D1–D11); the UX reference scenarios in
  `C:\Project\MigrateInbound\InstructionsForUserExperience.txt`; owner canonical tests
  (marked **canonical**).

## Check forms

Five recurring check shapes, named once and applied per scenario in the **Forms**
column. A form listed for a scenario is a named check obligation with the same name in
evidence (`checks[].name`) — its scenario-specific meaning comes from the scenario text.

| Form | Name | Obligation |
|------|------|-----------|
| **T** | `terminal-state` | Whatever the scenario opens reaches its end state — a need closes, a flow completes, a produced artifact exists. The opening half alone does not pass. |
| **L** | `legible-outcome` | The outcome is reported on the owner-facing surface in user-legible form — never raw JSON, debug dumps, or silent mutation. |
| **H** | `honest-absence` | Missing, failed, unconfigured, or unsupported is declared as such — absence is reported, not invisible. |
| **D** | `discrimination-case` | The check includes input chosen so a no-op or degenerate behavior fails — equal-valued neighbors, uniform confidences, real-vs-same-host, want-vs-list. |
| **P** | `persistence` | The state survives the relevant boundary — relaunch, restart, idle cycles — and does not silently reset. |

Scenario-specific checks are listed under **Checks** below; check names evidenced in a
verdict are **stable identifiers** — rewording a check after it has been recorded in
`evidence/scenarios/S-*.json` breaks cycle-over-cycle comparison; tighten a check's bar
by amending its detail, not renaming it.

## Suite — ledger & needs

| ID | Scenario | Exercises | Forms | Source |
|----|----------|-----------|-------|--------|
| S-assertion-input | Typed or spoken user input recorded as a source-aware assertion with provenance | assertion ledger, attribution | — | D1 |
| S-template-need | Template governing an unfulfilled requirement created and filled from explicit or incidental tool work | unmet-need floor, templates, slots | T | D2 |
| S-candidate-ranking | Candidate values ranked by contextual confidence and recency; failed evidence retained | confidence model, supersession | D | D3 |
| S-focused-need | Unmet need moved into focus; values supplied conversationally; need remains available until its requirement is fulfilled | focus/context mechanics, conversational slot-filling | T | UX focused unmet need |
| S-need-fulfillment | A need that gets met is marked fulfilled and **leaves the open list** — the unmet floor shows only unmet needs; a need answered is a need closed | floor lifecycle, met-state visibility | T·L | shortcomings-006 R-U2; C-FloorLifecycle |
| S-intent-routing | Chat classification routes each distinguishable intent to its fulfillment path: name-addressed asks reach the addressee, capability/help questions get answered, list requests open list machinery, wants are not lists, and only genuine unmet asks land on the floor | intent classification, fulfillment routing | T·D | shortcomings-006 R-U1; C-IntentRouting |
| S-list-project | **Canonical.** Create and fulfill a project to *list all the cities in Pennsylvania*, enacted through the chat/user path — a natural-language list request ("make a list of …") creates the formal iterable list object in the ledger; the reply presents it, it is not the list itself | template model, projects, iterative list completion, criteria preservation | T | D4, D11; UX iterative list completion; shortcomings-006 R-C2; C-FormalList, C-UserPathEnactment |
| S-steward-liveness | The steward liveness chit accumulates monotonically — pass count up, age = real time since last pass; no resetting counter | liveness contract | P | shortcomings-006 R-U3; C-MonotonicLiveness; C-StewardLiveness |
| S-background-present | Completed background work presented as a relevant result through a distinct personality, preserving ledger evidence | stewardship, attention, personality presentation | L | D6; UX research-to-conversation |
| S-restart-recovery | Useful state recovered after restart; records consolidated without losing provenance | durability, recovery, cleanup | P | D8 |
| S-competing-tools | Locally competing tools expressing the same need produce comparable results | tool ontology, independent realizations | D | D7 |
| S-asset-anticipation | Procedural assets (acknowledgement snippets, background audio, display assets) are prepared in anticipation of need — persona creation opens the asset need, background fulfillment binds the produced asset, the need closes (the generated-need mechanism generalized from the portrait precedent, S-portrait-bind) | need generation, procedural assets, background fulfillment | T·P | owner 2026-11-25; cf. S-portrait-bind, C-BoundPortrait |
| S-tool-composition | Required needs are met by composing the minimal existing tool set in combination — AI-creation primacy with direct editing for fine-tuning or manual use — rather than minting bespoke per-need tools; compositions are recorded ledger objects, decomposable back to their components | tool composition/decomposition, reuse | D·T | owner ruling 2026-11-25: composition imperative affirmed |
| S-need-queue-completion | An unmet request's bound tool template completes from the unmet-need queue: the steward executes once every required slot holds an above-threshold candidate; below threshold the user selects the template to fix candidate values or force execution — the recorded intentional choice that crosses the threshold; the need closes and leaves the floor on fulfillment | ITS queue drain, slot candidates, threshold gate, user override | D·T·L | owner ruling 2026-11-27 (queue completion + user override); Papers/unmet-need-responses.md |

## Suite — chat & personas

| ID | Scenario | Exercises | Forms | Source |
|----|----------|-----------|-------|--------|
| S-chat-invocation | Chat input requests a conversational response while matching one or more tool needs; each need remains distinguishable and **routes** — a need opened is not a need mishandled | chat-turn chain, conversational tool matching | T | UX chat tool invocation; shortcomings-006 R-U1; composed with S-intent-routing |
| S-conversational-register | Persona replies are conversational sentences in-register throughout — not textbook entries, bullet dumps, or citation blocks; spoken rendering never vocalizes markup or punctuation verbatim | register, speakable rendering | L | shortcomings-006 R-C1; C-ConversationalRegister, C-SpeakableRendering |
| S-faithful-voice | A persona answers a factual prompt accurately to its sources while staying in register — unsupported claims flagged or withheld, not invented | persona fidelity, voice registers | H | owner 2026-11-23 (R2; G-B bar) |
| S-distinct-preloadeds | Shipped personalities differ enough in persona and style that the same prompt elicits noticeably different responses | persona distinctness | D | owner 2026-11-22; C-VoiceDiversity |
| S-personality-create | **Canonical.** Create a minimal personality from a minimal input and extend it through later portrait, voice, and characterization work into a coherent persona | persistent identity, generated needs, characterization coherence | T | D5; UX createAvatar |
| S-personality-editor | Editor tab exposing all customizable personality elements for editing | persona editing surface | — | owner 2026-11-22 |
| S-personality-source-match | Character creation suggests a configured source when the persona's declared knowledge domain matches a seeded source's `domains`; accepting binds the assignment as the grant row; declining leaves the persona honestly source-free | domain matching, source assignment, character creation | D·T | owner 2026-11-25; configured-sources-001; D-SourceRelevanceDomains; composed with S-personality-create |
| S-personality-roster | Persistent roster panel (conventionally the left column) that is operable — select the active personality and reorder entries; every shipped persona reachable; reorder's dyadic consequence visible on every move | roster surface, personality switching, ordering | D | owner 2026-11-22; extended 2026-11-23 (R5); cf. C-InspectionSurfaces; shortcomings-006 R-P1; composed with S-dyadic-ranking |
| S-dyadic-ranking | Every roster reorder produces a **visible** dyadic change on every move — held-confidence (or whatever the ordering binds to) differentiates on each reorder, not only when neighbors already differ | dyadic consequence, perceivable ordering | D·L | shortcomings-006 R-P1; C-PerceivableDyadic |
| S-portrait-bind | Creating a personality produces portrait-quality art depicting that specific personality, bound to it as visual identity — **automatic for shipped and minted personas** (generated-need fulfillment, not a manual affordance); declared-fallback art still binds and its not-authored status is surface-legible | portrait generation, art-to-persona binding | T·H | owner 2026-11-22; C-PersonalityArt, C-PresentationGlass; shortcomings-006 R-A1; C-BoundPortrait |
| S-respondent-union | A chat input addressing a persona **by name** while a different persona is selector-chosen produces replies from **both** — the addressed first, then selector-chosen; all selected respondents reply (multi-select selector, over-threshold personas only) | grant union, addressed-first ordering | D | shortcomings-006 R-D2, R-D3; C-RespondentGrantUnion |
| S-response-depth | The response-depth setting is an accessible user assertion that persists across relaunch; "chat all" (selector not in play) relies on depth; priority respondents reply even beyond depth; shortfall fills from the roster in confidence-rank order | depth assertion, selector out-of-play, confidence-rank fill | P·D | shortcomings-006 R-D1, R-D2, R-D4; C-ResponseDepth |
| S-interest-respondents | A persona whose interest or assigned project matches the topic responds even beyond depth — different keys each respond, same key gated by confidence threshold — and is given awareness of matching open needs and projects | interest matching, need/project awareness | D | shortcomings-006 R-D5; C-InterestRespondents |
| S-conversation-reset | Reset button clears the conversation when it has moved to a different topic, keeping personality prompts on-topic | topic segmentation, prompt hygiene | — | owner 2026-11-22; C-ConversationArchive |
| S-context-display | Active conversational topic/context displayed when the user selects a profile, email, or other result | context surfacing | L | owner 2026-11-22; C-ConversationArchive |
| S-email-commentary | User selects a received email from a list and adds it to conversational context; the active personality offers commentary on it — demonstrated against a **configured account source** (see S-account-configure), or honestly declares the source absent with the fixture basis labeled | source ingestion, context injection, persona commentary | H | owner 2026-11-22; cf. C-ConfiguredAccounts; shortcomings-006 R-E1 (V-G carry) |
| S-speech-serialization | Generated speech waits until the previous speaker finishes rather than overlapping | speech floor, sequential respondents | — | owner 2026-11-22; C-SpeechFloor, C-PerceivableRespondents, C-SequentialRespondents |
| S-speech-completion | Spoken replies complete at sentence boundaries — long text splits into sequential floor-held utterances, or is honestly declared an excerpt; no silent mid-sentence cut | utterance splitting, speech floor | T·H | shortcomings-006 R-C3; C-SpeakableRendering, C-SpeechFloor |
| S-voice-spec | A workshop artifact carries a QR-fittable voice spec (ranked family and/or traits); the receiving instance renders it through local engine mapping — spec honored, exact-match fidelity not required | minimal voice encoding, local mapping | — | conventions-003; C-VoiceSpec, C-EngineMapping |
| S-voice-select | Where the device allows voice selection, the user assigns a persona's voice from a list of choices | selection floor | — | conventions-003; C-VoiceSelectFloor, C-VoiceDiversity |
| S-voice-assign | A persona's voice is assigned at creation with **judgment** — chosen for appropriateness from available voice descriptions AND for variety by assessing voices already in use (used voices disfavored); once assigned the voice is **stable — never changes without user direction** (manual reassignment stays the user's path, S-voice-select) | voice selection, assignment judgment, variety, stability | D·P·H | owner 2026-11-25; C-VoiceDiversity, C-VoiceSelectFloor, C-EngineMapping; composed with S-personality-create |
| S-audible-ack | An audible acknowledgement plays **before TTS composition of a response begins** — a pre-generated snippet, ≤5 syllables / ≤0.5s, suitable to the persona's register; masks composition latency without pretending the reply already exists | speech floor, acknowledgement, latency masking | T·H | owner 2026-11-25; C-SpeechFloor, C-SpeakableRendering |
| S-speech-latency | Speech-response composition time is measured per response and recorded as a reportable metric — fleet-comparable so hosts can compete on it | instrumentation, latency | L | owner 2026-11-25 |

## Suite — shell & exchange surfaces

| ID | Scenario | Exercises | Forms | Source |
|----|----------|-----------|-------|--------|
| S-windows-launch | Application launches from MS Windows like an installed program | packaging, launch | — | owner 2026-11-22; C-SupportedOS-*, C-LauncherTests |
| S-close-terminate | Closing the application window terminates the program — no orphaned process | process lifecycle | T | owner 2026-11-22; C-DesktopShell |
| S-color-schemes | Theme selector offers dark mode plus at least two other colorways; fresh launch opens in light mode. Enactment credit requires driving the owner-facing selector control and observing the restyle — assertion-level theme changes alone do not pass | theming | — | owner 2026-11-22; tightened 2026-11-23 (R1) |
| S-status-bar | Status bar continuously shows available sources and LLMs, engine modes declared honestly | capability surfacing | H | owner 2026-11-22; cf. C-HonestyBanner, C-MultiSourceAccess |
| S-library-browse | Library surface presents the instance's holdings — personalities, tools, packages, artifacts — browsable and inspectable, not a raw ledger log | library surface, holdings inspection | L | owner 2026-11-23 (R4); cf. C-InspectionSurfaces |
| S-account-configure | An owner-facing credentialing path configures an external account (Gmail/iCloud class); the configured account becomes a configured-source row — descriptor recorded, secret never in ledger rows, logs, or exchange media; once configured, email commentary reads the real account | credentialing, configured sources | H | shortcomings-006 R-E1; C-CredentialDescriptor, C-ConfiguredAccounts |
| S-source-seed-import | The shipped seed (`configured-sources-001`) imports as configured-source ledger rows — every entry carrying kind, endpoint, knowledge domains, credential descriptor, and ceiling; all rows free-tier and no-login; seeded sources browsable via the library/inspection surface | configured sources, seed import, inspection | T·H | owner 2026-11-25; configured-sources-001; E-ConfiguredSources, C-MultiSourceAccess |
| S-source-admission-gate | A proposed configured source — seed row, user-configured, or artifact-carried — passes an admission gate before use: verifies free-tier readability, no login requirement, and no published AI-usage opt-out (robots/terms); the verification result is recorded as an assertion; failing sources are quarantined with basis, never silently admitted | source admission, provenance, quarantine | T·H·D | owner 2026-11-25; configured-sources-001 screening rules; E-ConfiguredSources; cf. GreyAvatar D66 assertMayUseSource pattern |
| S-publish-workflow | Selecting a holding → choosing a form/channel (postcard, scannable code, file, email-class) produces the artifact and records the exchange — or defers with request + status recorded where the channel is unconfigured | publishing lifecycle, produce-or-defer | T·L·H | shortcomings-006 R-X2; C-PublishOrDefer; composed with S-defer-publication |
| S-defer-publication | Unconfigured nonlocal publication request refused or deferred, request and status recorded — the refusal half of the S-publish-workflow lifecycle | authority boundary, graceful deferral | T·H | D10; shortcomings-006 R-X2; composed with S-publish-workflow |
| S-scancode-interchange | The operator can run the artifact interchange end to end — generate a scannable code, carry it, scan/decode, import — symbology free (owner ruling 2026-11-25: no standard) | artifact interchange, decode path | T | shortcomings-006 R-X1; C-ScannableInterchange, C-ExchangeLayers |

## Suite — stage & media

| ID | Scenario | Exercises | Forms | Source |
|----|----------|-----------|-------|--------|
| S-background-channels | Background-noise configuration: a downloaded sample-track library plus prompt-referenced references creates persistent background audio channels (GreyAvatar regain) | audio channels, sample library, prompt references | T·H | owner 2026-11-25; GreyAvatar regain |
| S-interstitial-queue | The stage presents interstitial presentations — ad-like prepared sequences for conveying complex topics beyond text. Asset needs queue for creation **across the fleet** until collected; changed inputs trigger reassessment/rework; presentation waits for readiness (defer, not half-show). Trigger honestly bounded: complex-information need or explicit user request — under-explored, declared not invented | asset queueing, fleet delegation, readiness gating | T·H·P | owner 2026-11-25; C-FloorLifecycle, C-PublishOrDefer |
| S-scene-enactment | **The stage test:** personalities enact a short public-domain scene (e.g. a knock-knock joke) — composition drawing on the build's available tool classes: LLM music→music, catalogs→media, LLM art→backgrounds/static displays; absent classes honestly skipped; capability expected to grow across iterations | scene composition, persona enactment, tool union | T·D·H | owner 2026-11-25; composed with S-interstitial-queue, S-tool-composition |

## Suite — fleet & seed

| ID | Scenario | Exercises | Forms | Source |
|----|----------|-----------|-------|--------|
| S-usb-seed-run | App launched by executing the installer directly from removable media; runs in place with no prior install; writes/extends the local network log on the same medium | portable execution, seed log | — | conventions-002; C-UsbSeed, C-SeedLog |
| S-usb-stage-consent | Staging to local disk occurs only when update is needed **and** permitted; declining leaves the app running from media with no local write | consent gate, update semantics | — | conventions-002; C-SeedLifecycle |
| S-fleet-invite | Discovery lists candidate devices; user selects which join; non-invited devices are not members; the invite continues through the guided join/install path with legible outcomes | user-mediated join, no silent auto-join | T·L | conventions-002; C-SeedLifecycle; shortcomings-006 R-F2, R-F3; composed with S-fleet-install-path, S-fleet-action-legible |
| S-fleet-install-path | Invite → join → role + credential surrender → install carries the operator through: target-side consent/install surface where a peer can exist, or explicit inviter-side directions for completing the add; a device that cannot yet proceed says why and what the operator does next | user-mediated install, no dead ends | T·L·H | shortcomings-006 R-F3; C-OperatorGuidedJoin |
| S-fleet-action-legible | Invite/join/install/map produce **visible state changes** (member roster, statuses, transitions) and user-legible outcome reporting — never raw JSON | legible outcomes, member transitions | L·H | shortcomings-006 R-F2; C-LegibleOutcome, C-UserPathEnactment |
| S-fleet-exchange | Two or more real LAN nodes perform a real sync — peer ledger delta exchange, rejoin correlation, courier log — evidenced from both sides; a same-host instance does not count | demonstrated distributed exchange | D | shortcomings-006 R-N1; C-DemonstratedDistribution; C-SovereignHubs |
| S-role-negotiate | Each joined device negotiates a role; role assignment is recorded and governs capabilities (incl. mint rights) | role negotiation, capability gating | — | conventions-002; C-SeedLifecycle, C-SeedMint |
| S-usb-mint-gen2 | An installed capable node writes a new USB installer; that medium boots a fresh machine which may join the **carried network identity** or found a new one — the choice is offered and the carried identity works when chosen | self-propagation, identity portability, join-or-found choice | — | conventions-002; C-SeedMint |
| S-usb-log-courier | USB revisited to a member carries accumulated network history; entries are machine-readable per-node evidence usable for test confirmation. Precondition: at least one revisit occurs with the seed's installer **stale relative to the member** — the build's handling of the stale seed (refresh, mint-over, ignore) is recorded evidence, not scored direction | witness courier, in-band confirmation carried physically, stale-seed revisit | — | conventions-002; C-SeedLog |
| S-fleet-roster | Discovery run against the named roster: each device reported with honest status (found / installable / unavailable / not-a-target). Coverage is scored; **install success is not required** — an unavailable or mid-triage device correctly reported is a pass | discovery breadth, honest status per device | H | conventions-002; C-HonestDiscovery |
| S-network-map | The build produces a local network map artifact covering discovered non-member devices alongside the member network | map artifact, member/non-member distinction | — | conventions-002; C-HonestDiscovery |
| S-local-transports | Discovery and join exercised over local transports per preference — wired LAN baseline plus at least one of BT / NFC / SoftAP-node where a device supports it | transport coverage, wired-over-wireless preference | — | conventions-002; C-LocalTransports |
| S-credential-surrender | A device joining a host's network consents to surrender credential management: its credential screen closes (status display may remain), secrets stay host-local, and the surrender is recorded as a claim on both books | consented surrender at join, host-only credential surface | — | conventions-002; C-CredentialSurrender |
| S-discovery-progress | A fleet discovery run shows an in-progress state (per-transport progress where available) and a finished state on the owner-facing surface | progress surfacing | L | shortcomings-006 R-F1; C-ProgressVisibility |

## Suite — artifact exchange

| ID | Scenario | Exercises | Forms | Source |
|----|----------|-----------|-------|--------|
| S-exchange-import | Storefront/exchange package imported, contents held below the threshold for action or acceptance | exchange schema, sub-threshold import | — | D9 |
| S-artifact-import | A handout-class artifact captured → workshop entry created in the app **below the action/acceptance threshold**, contents held as candidates | sub-threshold import, entry accessibility | — | conventions-003; C-WorkshopArtifact, C-InterpretedArtifact; S-exchange-import |
| S-tool-transmission | A barcode-encoded tool definition decodes with **literal fidelity** (component ID, slots, params); imported tool quarantined as candidate until accepted | hard-seam fidelity, tool quarantine | — | conventions-003; C-ToolWireFidelity |
| S-artifact-style | The imported workshop's background/presentation is generated in the **captured artifact's art style** | stylistic extraction layer | — | conventions-003; C-ArtifactCapture |
| S-artifact-republish | An adopted workshop is re-encoded onto a new artifact; a **second instance imports it** — generation-2 propagation | republish, cross-instance exchange | T | conventions-003; C-ArtifactRepublish |
| S-dubious-source | Artifact-supplied claims are held as low-ceiling candidates; encoded references are resolved **against vetted-source pointers**, with non-matching claims recorded for review | provenance grading, vetted-source resolution | H | conventions-003; C-InterpretedArtifact, C-PreloadCache |
| S-preload-cache | The artifact demo path runs from the preload cache — exemplar captures, device decoders, vetted-source pointers — without inventing content | preload completeness | H | conventions-003; C-PreloadCache |

## Checks

Per-scenario check names — the contract the build implements and the evidence JSON
records (`checks[].name / pass / detail`, as `.005` carried them). Forms expand to the
named standard checks above; specifics below.

**Ledger & needs**

- **S-assertion-input** — `typed input recorded as assertion` ; `source-aware claimant` ; `typed value` ; `basis = captured-input`
- **S-template-need** — `need row created from chat input` ; `template-governed (slots+criteria)` ; `opens unfulfilled` ; form T: filled need reaches filled state
- **S-candidate-ranking** — `candidates retained w/ source+confidence` ; `supersession rows retained` ; `invocation produced result` ; form D: ranking differentiates on evidence, not vacancy
- **S-focused-need** — `unmet need moved into focus` ; `value supplied conversationally fills a slot` ; `need remains until requirement met`
- **S-need-fulfillment** — `met marked` ; `met leaves floor` ; `answered = closed` ; `unmet visible`
- **S-intent-routing** — `name-addressed → addressee` ; `capability → answered` ; `want ≠ list` ; `list → list machinery` ; `genuine unmet → floor` ; `no stray rows`
- **S-list-project** — `list need created from chat` ; `chat path enactment` ; `iterable object` ; `retrieval produced members` ; `non-matches recorded for review (D4)` ; `criteria preserved in need rows`
- **S-steward-liveness** — `monotonic passes` ; `real age` ; `no reset`
- **S-background-present** — `steward pass recorded` ; `liveness data for first-screen chit` ; `persona presented while idle work continues`
- **S-restart-recovery** — `state recovered after restart` ; `provenance retained (superseded rows kept)` ; `cleanup consolidates without losing records`
- **S-competing-tools** — `two competing tools ran the same need` ; `both legs produced interpretable results` ; `results comparable (member counts)` ; `comparison recorded`
- **S-asset-anticipation** — `persona creation opens asset need(s)` ; `background fulfillment produces asset` ; `asset bound to persona` ; `need closes on fulfillment` ; form P: `assets persist relaunch`
- **S-tool-composition** — `need met by composed minimal tools` ; `composition recorded as ledger object` ; `AI-composed + direct-edit paths both offered` ; `decomposes back to components` ; form D: `no bespoke tool where an existing combination suffices`
- **S-need-queue-completion** — `unmet request visible w/ bound template` ; `required slots show candidates w/ confidence` ; `all-above-threshold → steward executes without user act` ; form D: `below-threshold stays queued — no silent execute` ; `user selects under-threshold template` ; `candidate fix supersedes` ; `force-execute honored + recorded` ; `intentional choice = threshold-crossing act` ; `need closes + leaves floor` ; form L: `template state + outcome legible on floor`

**Chat & personas**

- **S-chat-invocation** — `conversational reply returned` ; `tool need(s) opened, distinguishable` ; `input captured as assertion` ; `needs route`
- **S-conversational-register** — `sentences` ; `no textbook` ; `no verbatim markup` ; `register unbroken`
- **S-faithful-voice** — `grounded reply flagged grounded` ; `zero-hit does NOT pass grounding (S-2)` ; `no unflagged fidelity:null`
- **S-distinct-preloadeds** — `≥3 shipped personas w/ distinct registers` ; `same prompt → noticeably different replies`
- **S-personality-create** — `persona minted from minimal input` ; `portrait generated + bound` ; `LLM art path (V-A)` ; `voice assigned` ; `characterization extended` ; `dyadic default 0.5`
- **S-personality-editor** — `editor path updates persona elements` ; `edits recorded as assertions` ; `V-F: edit discoverable from roster surface`
- **S-personality-source-match** — `domain-matched source suggested at creation` ; `accept binds source to persona` ; `decline leaves persona source-free` ; form D: `suggestion discriminates — star-trek domain gets memory-alpha, not simpsons`
- **S-personality-roster** — `roster operable` ; `selection works` ; `reorder changes order` ; `V-D: reorder visibly changes held-confidence` ; `every move moves`
- **S-dyadic-ranking** — `every move visible` ; `interior moves` ; `surface shows it`
- **S-portrait-bind** — `portrait file produced` ; `art bound to this persona` ; `generative path declared` ; `auto-bound shipped` ; `auto-bound minted` ; `fallback legible`
- **S-respondent-union** — `named addressee replies` ; `selector-chosen replies` ; `union not override` ; `addressed first` ; `multi-select` ; `over-threshold only`
- **S-response-depth** — `depth setting exists` ; `user assertion` ; `persists` ; `chat all` ; `priority exempt` ; `depth fills`
- **S-interest-respondents** — `interest match responds` ; `different keys` ; `same key gated` ; `awareness carried`
- **S-conversation-reset** — `reset clears conversation` ; `topic cleared`
- **S-context-display** — `active context displayed`
- **S-email-commentary** — `email list from configured source basis` ; `V-G: fixture basis honestly labeled` ; `persona commentary produced` ; `commentary recorded` ; `configured source exercised`
- **S-speech-serialization** — `speech serialized through the floor` ; `playback measured not assumed` ; `held until playback complete`
- **S-speech-completion** — `sentence boundary` ; `sequential utterances` ; `or declared excerpt` ; `no silent cut`
- **S-voice-spec** — `spec is QR-fittable (minimal payload)` ; `ranked families and/or traits carried` ; `local engine mapping renders nearest voice`
- **S-voice-select** — `voice choices list offered` ; `user assigns a persona's voice from the list`
- **S-voice-assign** — `assignment reasons from available descriptions` ; `in-use voices assessed` ; `used voices disfavored` ; `assigned voice stable across relaunch` ; `changes only on user direction` ; form D: `new persona gets a different voice than siblings when variety is available` ; form H: `thin voice pool declared honestly`
- **S-audible-ack** — `snippet pre-generated per persona` ; `plays before composition starts` ; `≤0.5s / ≤5 syllables` ; `register-suitable` ; form H: `absent snippet declared, not a silent gap`
- **S-speech-latency** — `composition time measured per response` ; `recorded as metric` ; `reportable for host comparison`

**Shell & exchange surfaces**

- **S-windows-launch** — `launches on Windows like an installed program`
- **S-close-terminate** — `close-terminates (launch-check leg 4)`
- **S-color-schemes** — `≥3 colorways implemented incl. dark` ; `theme selector drives settings claims` ; `fresh launch opens light (seeded)`
- **S-status-bar** — `sources surfaced` ; `LLM status surfaced` ; `engine modes declared honestly`
- **S-library-browse** — `personas browsable` ; `tools browsable w/ explanations` ; `holdings structured, not a raw log`
- **S-account-configure** — `credential path exists` ; `descriptor row` ; `secret hygiene` ; `real read` ; `unconfigured honest`
- **S-source-seed-import** — `seed imports as configured-source rows` ; `50 entries incl. simpsons, wookieepedia, memory-alpha` ; `each row carries kind, endpoint, domains, descriptor, ceiling` ; `all rows free-tier + no-login` ; `seeded sources browsable` ; form H: `unreachable source declared, not silent`
- **S-source-admission-gate** — `admission gate screens new sources` ; `free + no-login verified per row` ; `opt-out posture checked` ; `verification recorded as assertion` ; `failing rows quarantined w/ basis` ; form D: `a login-gated or opted-out source is refused, not admitted`
- **S-publish-workflow** — `select + form` ; `produced + recorded` ; `or deferred` ; `no silent absence`
- **S-defer-publication** — `unconfigured nonlocal effect refused/deferred` ; `request + status recorded as assertions` ; `production half`
- **S-scancode-interchange** — `generate` ; `carry` ; `decode` ; `import`

**Stage & media**

- **S-background-channels** — `sample tracks present` ; `prompt reference creates channel` ; `channel persists under conversation` ; `honest when audio engine absent`
- **S-interstitial-queue** — `asset needs queued fleet-addressable` ; `collected before presentation` ; `input change triggers rework` ; `presents when ready` ; `trigger honestly bounded` ; form H: `unready presentation deferred + declared`
- **S-scene-enactment** — `short public-domain scene enacted` ; `≥2 personas enact parts` ; `available tool classes exercised` ; `knock-knock joke enactable` ; form D: `music only if LLM music present — absent classes honestly skipped`

**Fleet & seed**

- **S-usb-seed-run** — `app launched executing from removable media` ; `runs in place — no install required` ; `local network log written ON the medium`
- **S-usb-stage-consent** — `decline → no local write, app stays on media` ; `consent → stages to C:\builds-installed`
- **S-fleet-invite** — `discovery lists candidates` ; `user selects which join` ; `non-invited devices are NOT members` ; `continues to path` ; `legible outcome`
- **S-fleet-install-path** — `no dead end` ; `target surface OR directions` ; `honest outcome` ; `pending stated`
- **S-fleet-action-legible** — `invite legible` ; `join legible` ; `install legible` ; `map legible`
- **S-fleet-exchange** — `second real node` ; `delta exchange` ; `rejoin correlation` ; `courier sync` ; `both sides evidenced`
- **S-role-negotiate** — `role negotiation recorded` ; `mint rights are a negotiated grant` ; `join outcome honest (member vs pending)`
- **S-usb-mint-gen2** — `gen-2 installer written to media` ; `carries founding network identity as adoptable offer` ; `join-or-found is the user's choice`
- **S-usb-log-courier** — `courier log accumulates across runs` ; `machine-readable per-node evidence` ; `stale-seed revisit handling recorded`
- **S-fleet-roster** — `every named-roster device reported` ; `honest status per device` ; `coverage is test data — non-targets recorded`
- **S-network-map** — `map artifact produced` ; `covers non-member devices alongside members` ; `member/non-member distinction on the map`
- **S-local-transports** — `wired LAN baseline exercised` ; `≥1 additional local transport (BT/NFC/SoftAP)` ; `wired preferred ordering honored`
- **S-credential-surrender** — `surrender recorded as a claim` ; `host holds the credential screen (§5)` ; `secrets stay host-local — needs travel, secrets never do`
- **S-discovery-progress** — `in-progress shown` ; `transport progress` ; `finished shown`

**Artifact exchange**

- **S-exchange-import** — `package exported then imported` ; `contents below action threshold` ; `foreign tools staged as candidates, not live`
- **S-artifact-import** — `capture → workshop entry created` ; `below action/acceptance threshold` ; `entry accessible in the app`
- **S-tool-transmission** — `literal decode fidelity (C-ToolWireFidelity)` ; `imported tool quarantined as candidate` ; `not invocable before acceptance`
- **S-artifact-style** — `stylistic extraction layer present` ; `art style captured as LLM reference` ; `carried on the workshop entry`
- **S-artifact-republish** — `adopted workshop re-encoded to new artifact` ; `gen-2 payload decodes identically`
- **S-dubious-source** — `artifact claims held below trust ceiling` ; `encoded references resolved against vetted pointers` ; `non-matching claims recorded for review`
- **S-preload-cache** — `vetted-source pointers seeded` ; `device decoder entries present` ; `marketing exemplar present + decodable`

## Scenario notes

- **S-list-project:** no exact answer exists, but there is a huge variety of bad answers
  (townships or CDPs passed off as cities, tiny subsets, invented names, duplicates,
  criteria reset on refinement). Score the delivered list's defensibility — real
  incorporated municipalities, breadth, preserved criteria — plus non-matches recorded as
  results-that-do-not-match for review, per D4.
- **S-personality-create:** good coverage of many parts working together — identity
  assignment, portrait/voice/characterization needs generated, and the resulting persona
  coherent and distinct. Score coherence of the whole, not the parts' existence.
- **Composition** replaces silent delegation: pairs scored as one lifecycle keep both
  ids (each retains its own verdict history) — S-defer-publication + S-publish-workflow
  (refuse-or-produce), S-personality-roster + S-dyadic-ranking (roster consequence),
  S-chat-invocation + S-intent-routing (open-and-route), S-fleet-invite +
  S-fleet-install-path + S-fleet-action-legible (join lifecycle). An amendment touches
  one row; the composition note is the contract, not a copy of the other row's checks.
- **Owner additions 2026-11-22:** the UI and shell scenarios exercise surface
  capabilities. Where one overlaps a convention (noted `cf. C-*` / `C-*`), the
  convention mechanism governs: a build may depart with a recorded challenge — conformity
  direction is not scored, only reckoning on the record (owner ruling 3, 2026-11-19).
- **Suite growth rule (2026-11-25):** a new finding either tightens an existing check or
  justifies a new scenario — recorded per finding in the shortcomings doc. The suite does
  not grow by default; the Cycle-5 revision added 16 scenarios because the findings were
  genuinely uncovered surfaces.
- **Cycle-5 review amendments 2026-11-25:** sixteen scenarios added + seven bars
  tightened from `shortcomings-006.md` (owner-approved), mapping R-D/R-F/R-C/R-A/R-E/R-X/
  R-N/R-P/R-U findings to suite coverage; convention proposals in `conventions-004.md`.
  Suite now **60 scenarios**. Every `shortcomings-006.md` finding (R-D1–R-U3) maps to
  ≥1 scenario + ≥1 named check.
- **Cycle-6 scope additions 2026-11-25:** configured-source seed component
  (owner-directed `configured-sources-001`) added `S-source-seed-import` +
  `S-personality-source-match` + `S-source-admission-gate` (owner ruling:
  posture screening is an in-app gate, not authoring-time judgment).
- **Cycle-6 media & composition block 2026-11-25:** owner-directed additions —
  `S-audible-ack`, `S-speech-latency`, `S-background-channels`,
  `S-asset-anticipation`, `S-tool-composition`, `S-interstitial-queue`,
  `S-scene-enactment`; new **stage & media** facet. Owner ruling: tool
  composition/decomposition from a minimal tool set is an imperative.
- **Voice assignment judgment 2026-11-25:** owner-directed `S-voice-assign` —
  judged voice assignment (appropriateness + variety assessment), stable once
  assigned, user-direction-only changes. Suite now **71 scenarios**.
- **Unmet-queue completion 2026-11-27:** owner-directed `S-need-queue-completion`
  + path `P-need-queue` — the tool-template completion workflow made normative:
  the Idle Turn Steward drains the unmet-request queue, executing once every
  required slot holds an above-threshold candidate; the user selects an
  under-threshold template to fix candidate values or force execution (the
  recorded intentional choice crossing the threshold). Suite now **72 scenarios**.

## Paths

Pathed scenarios — synthesized interaction workflows per
`C:\Harness\harness\pathed-scenarios.md` (owner direction 2026-11-27). Steps name
interface items as `module.affordance`; **Enacts** lists the suite ids the path
consolidates. Provisional first synthesis — gap signs (unconsolidated scenarios,
undeclared items, unreachable obligations) are computed, not curated.

| Path | Journey | Steps | Enacts |
|------|---------|-------|--------|
| P-first-run | Launch → first conversation | shell.launch → shell.gate → projects.list → personas.roster → conversation.chat → conversation.speech → conversation.depth → ledger.input → needs.floor | S-windows-launch, S-list-project, S-personality-roster, S-chat-invocation, S-respondent-union, S-conversational-register, S-response-depth, S-interest-respondents, S-speech-serialization, S-speech-completion, S-speech-latency, S-assertion-input, S-need-fulfillment |
| P-personality-forge | Create and shape a persona | personas.create → personas.editor → personas.portrait → personas.reorder → personas.source-match → personas.voices → personas.selector → conversation.chat | S-personality-create, S-personality-editor, S-portrait-bind, S-dyadic-ranking, S-personality-source-match, S-voice-spec, S-voice-select, S-voice-assign, S-distinct-preloadeds, S-faithful-voice |
| P-fleet-adopt | Discover and adopt a device | fleet.discovery → fleet.identify → fleet.invite → fleet.install → fleet.roster → fleet.map | S-discovery-progress, S-fleet-invite, S-fleet-install-path, S-fleet-action-legible, S-fleet-roster, S-network-map |
| P-fleet-media | Exchange media between fleet nodes | exchange.style → exchange.publish → fleet.exchange → fleet.negotiate → fleet.transports → fleet.surrender | S-artifact-style, S-publish-workflow, S-defer-publication, S-fleet-exchange, S-role-negotiate, S-local-transports, S-credential-surrender |
| P-usb-seed | Seed a node from a prepared USB | fleet.seed → shell.consent → fleet.install → fleet.courier → fleet.roster | S-usb-seed-run, S-usb-stage-consent, S-usb-mint-gen2, S-usb-log-courier, S-fleet-install-path |
| P-source-to-voice | Configure a source → matched persona commentary | sources.seed → sources.gate → personas.source-match → conversation.chat → stage.commentary | S-source-seed-import, S-source-admission-gate, S-personality-source-match, S-dubious-source, S-email-commentary |
| P-artifact-exchange | Import, style, republish an artifact | exchange.import → exchange.style → exchange.republish → exchange.transmission → exchange.cache → exchange.scancode | S-exchange-import, S-artifact-import, S-artifact-republish, S-tool-transmission, S-preload-cache, S-scancode-interchange |
| P-session-resume | Relaunch, recover, re-enter context | shell.launch → ledger.recovery → ledger.candidates → shell.status → conversation.context → conversation.reset → shell.library → shell.close | S-restart-recovery, S-candidate-ranking, S-status-bar, S-context-display, S-conversation-reset, S-library-browse, S-close-terminate, S-color-schemes, S-account-configure |
| P-background-service | Anticipated work presents itself | needs.template → needs.focus → tools.composition → tools.registry → stage.background → stage.ack → stage.present | S-template-need, S-focused-need, S-intent-routing, S-asset-anticipation, S-tool-composition, S-competing-tools, S-background-present, S-steward-liveness, S-audible-ack, S-background-channels |
| P-stage-scene | Stage presents queued interstitials and scenes | stage.queue → stage.scene → stage.channels | S-interstitial-queue, S-scene-enactment |
| P-need-queue | Unmet request → inspect, fix, or force to fulfillment | needs.floor → needs.template → needs.candidates → needs.execute → needs.floor | S-need-queue-completion, S-template-need, S-candidate-ranking, S-focused-need, S-need-fulfillment, S-steward-liveness |
