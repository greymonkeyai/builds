# Implementation design 001 — module structure for iteration
<!-- harness-doc kind=impl-design status=in-force since=2026-11-26 applies-to=cycle-7 -->

Drafted by the coordinator session per owner direction 2026-11-26:
*move towards a modular design so components can be iterated in the future —
isolate changes, hasten build time; a structuring of requirements is
necessary.* Owner rulings on scope and mechanics recorded below; the
convention→module mapping is coordinator-completed, owner-review pending.

**Class (owner nomenclature 2026-11-26):** an *implementation design doc* —
the working tier beneath the corpus's higher-order design docs
(`C:\Project\Design\`, M-\*/I-\*/Papers). Lower rigor bar by intent: the line
revises it continuously as the implementation teaches, unlike corpus docs
that move through their own revision process. It organizes requirements for
construction; it is not a normative design authority.

## Owner rulings 2026-11-26

- **Scope:** whole-app attempts continue — organized by this module map.
  Unclassified requirements get a section to await classification.
- **Convention mapping:** coordinator assigns all 97 ids with placement
  rationale; owner reviews.
- **Completeness = green count.** Under the phase-0 contract, completeness
  is the count of checks gone green — not a fraction judged after the fact.
- **Negative tests live with the positive tests** in `scenarios.md` Checks;
  the check corpus is verified for completeness (positive + negative + edge
  cases) **before a build starts**.

## Purpose

A **module** is the iteration unit: a named component that owns (a) its
requirement sources, (b) the scenario ids that define "enacted" for it,
(c) the conventions — including edge cases — that constrain it, (d) its
surface obligations, and (e) its dependency edges. Consequences:

- A direction may scope **by module** and carries that module's entire
  obligation set with it — no requirement orphaned when a component is
  iterated.
- A build greens **module by module**; the stop-time remainder is a list of
  un-greened modules/scenarios — honest absence shaped like the work order,
  not buried stubs.
- Check corpora attach to modules: instantiating module M's tests means its
  scenario checks **plus its edge-case conventions as negative/discrimination
  tests** — instantiated *before* M's machinery exists (tests precede the
  machinery needed to pass them; negative and edge cases are instantiated at
  the same phase; pass/fail is adequate only if edge cases are handled).
- Edge cases enter through the standing **convention-drafting response**:
  findings → conventions (challengeable, never ignorable); this doc aligns
  each edge-case convention to the module(s) it constrains, so the case
  travels with the module when the module is iterated.

The suite's six surface facets (`scenarios.md`) stay — they describe *where
behavior is observed*. Modules describe *what implements it*. Both are
needed: facets for scoring coverage, modules for construction order and
iteration scope.

## Modules

| Module | Owns (in one line) | Scenarios | Surface obligations | Depends on |
|--------|--------------------|-----------|---------------------|------------|
| **ledger** | Assertion book — typed attributed input, provenance, supersession, computed views subordinate, durability | S-assertion-input, S-candidate-ranking, S-restart-recovery | none directly; backs all surfaces | — |
| **needs** | Unmet-requirement floor — templates, slots, candidates, focus, fulfillment lifecycle, intent routing, generated needs | S-template-need, S-focused-need, S-need-fulfillment, S-intent-routing, S-asset-anticipation, S-steward-liveness | floor view legible; met needs leave the open list | ledger, tools |
| **projects** | Projects, temporal context, formal lists as ledger objects | S-list-project (+ prompt §Projects/§Temporal — absent and silent in `.006`; declare or build) | list/project inspectable objects | ledger, needs |
| **personas** | Roster, dyadic confidence & reorder, portraits, voices, editor, selector, surface assignment | S-personality-create, S-personality-editor, S-personality-roster, S-dyadic-ranking, S-portrait-bind, S-voice-spec, S-voice-select, S-voice-assign, S-distinct-preloadeds, S-personality-source-match | roster/editor/selector operable; reorder consequence perceivable | ledger, needs, sources |
| **conversation** | Chat surface — respondent union, depth, register, grounding/fidelity, speech floor, latency | S-chat-invocation, S-conversational-register, S-faithful-voice, S-respondent-union, S-response-depth, S-interest-respondents, S-conversation-reset, S-context-display, S-email-commentary, S-speech-serialization, S-speech-completion, S-speech-latency | every reply path user-reachable through chat | personas, needs, sources, tools |
| **tools** | Tool registry/ontology, DSL, competing realizations, workshop, composition, execution policies | S-competing-tools, S-tool-composition, S-background-present | workshop functions carry inline explanation | ledger, needs |
| **sources** | Configured-source rows, admission gate, domain-matched suggestion, account credentialing | S-source-seed-import, S-source-admission-gate, S-email-commentary (account side) | seed rows browsable; gate verdicts legible | ledger, shell |
| **fleet** | Discovery, invite/join/install, peer protocol, seed media, roster/map, transports, surrender, host/satellite topology | S-usb-seed-run, S-usb-stage-consent, S-fleet-invite, S-fleet-install-path, S-fleet-action-legible, S-fleet-exchange, S-role-negotiate, S-usb-mint-gen2, S-usb-log-courier, S-fleet-roster, S-network-map, S-local-transports, S-credential-surrender, S-discovery-progress | **owner-facing fleet surface must render** (.006: renderFleet empty) | ledger, shell, tools |
| **exchange** | Artifact codec, import, transmission, style, republish, publish-or-defer, preload cache, scancode | S-exchange-import, S-artifact-import, S-tool-transmission, S-artifact-style, S-artifact-republish, S-dubious-source, S-preload-cache, S-publish-workflow, S-defer-publication, S-scancode-interchange | publish workflow + legible interchange | ledger, shell |
| **stage** | Interstitials, scene enactment, background channels, audible ack, presence stage | S-interstitial-queue, S-scene-enactment, S-background-channels, S-audible-ack | stage surface presents when ready | personas, tools, fleet |
| **shell** | Launch, readiness gate, launch hygiene, host runtime, operator surface, library, status bar, theme, presentation, honesty declarations, progress/legible outcomes | S-windows-launch, S-close-terminate, S-color-schemes, S-status-bar, S-library-browse, S-account-configure | the operator surface itself — every other module's surface obligations land here | all (it hosts them) |
| **unclassified** | Requirements not yet assigned — awaiting classification into a module (or a new module) | — | — | — |

Harness-class bindings (bind the scoring machinery, not a module):
C-UserPathEnactment, C-ScenarioEnactment, C-CanonicalScenarios.

## Convention → module assignment (complete — owner review)

**ledger** — C-JsonlLedger, C-LocalIndices, C-CertaintyPrivilege,
C-UserSetSupremacy, C-TransientBoundary, C-SnapshotInference,
C-SequentialCommit, C-ContactTags

**needs** — C-UnmetNeedRecords, C-AcceptanceChecks, C-DeterministicMatchReview,
C-FloorLifecycle, C-IntentRouting, C-MonotonicLiveness, C-StewardLiveness,
C-TurnEvalLane, C-TemplateDerivedUI

**projects** — C-SetBuild, C-FormalList, C-SpecializedListRetrieval

**personas** — C-DyadicConfidence, C-PerceivableDyadic, C-PersonalityArt,
C-BoundPortrait, C-VoiceDiversity, C-VoiceSelectFloor, C-VoiceSpec,
C-EngineMapping, C-SurfaceAssignment, C-PresenceRoster, C-EthicsGate

**conversation** — C-ConversationArchive, C-PerceivableRespondents,
C-SequentialRespondents, C-SpeechFloor, C-RespondentGrantUnion,
C-ResponseDepth, C-InterestRespondents, C-ConversationalRegister,
C-SpeakableRendering, C-QuickSelect, C-ChorusOnAddress

**tools** — C-ConvergentOntology, C-AgenticProtocol, C-StewardAsTool,
C-UserFacingPriority, C-ExplicitPolicies, C-ToolCandidateAcceptance

**sources** — C-MultiSourceAccess, C-CompetingSources, C-ConfiguredAccounts,
C-SourceCeilings, C-SourceDomains, C-ConnectorSet, C-CredentialDescriptor

**fleet** — C-UsbSeed, C-SeedStagePath, C-SeedLifecycle, C-SeedLog, C-SeedMint,
C-LocalTransports, C-HonestDiscovery, C-SeedSigning, C-SupportedOS-\*,
C-OperatorGuidedJoin, C-DemonstratedDistribution, C-SovereignHubs,
C-CredentialSurrender, C-HostAuthority

**exchange** — C-ExchangeLayers, C-WorkshopArtifact, C-InterpretedArtifact,
C-ToolWireFidelity, C-ArtifactCapture, C-ArtifactRepublish, C-PreloadCache,
C-ScannableInterchange, C-PublishOrDefer

**stage** — C-PresenceStage

**shell** — C-DesktopShell, C-FullScreen, C-InspectionSurfaces,
C-PresentationGlass, C-HonestyBanner, C-DeclaredStubs, C-LauncherTests,
C-DeclaredPresentation, C-SettingsPreloads, C-PreloadSuite,
C-TwoPartExecution, C-ReadinessGate, C-LaunchPartition, C-LegibleOutcome,
C-ProgressVisibility

**harness (binds machinery, not a module)** — C-UserPathEnactment,
C-ScenarioEnactment, C-CanonicalScenarios

**unclassified** — none yet; the section awaits requirements that arrive
unassigned.

## Placement rationale (the non-obvious calls)

- **C-LaunchPartition → shell, not ledger.** It describes launch machinery —
  what mounts the ledger's essential partition. The partition itself is
  ledger's; the obligation lands on launch.
- **C-HostAuthority → fleet.** Authoritative-host + satellite-surface is a
  device/surface *topology*; the shell hosts it but the convention governs
  how surfaces distribute across the fleet.
- **C-PreloadSuite → shell (product-class despite its corpus section).** It
  sits under Evaluation & test but constrains what a build *ships* — ≥3
  named settings preloads enacted — so it binds the build, module shell.
- **C-DyadicConfidence → personas** (dyadic = user↔persona relationship);
  its shared confidence semantics reach needs' candidate ranking — noted as
  a cross-module dependency, not a second home.
- **C-TemplateDerivedUI → needs.** The template is the need's own; the
  derived form is a shell obligation carried via needs → shell dependency.
- **C-CredentialDescriptor → sources.** A configured account *is* a
  configured-source row; the secret-handling half is convention-level.
- **C-SetBuild / C-SpecializedListRetrieval → projects.** Both are the
  machinery beneath S-list-project — set fulfillment and specialized
  retrieval for defensible list answers.
- **C-TurnEvalLane → needs.** The gate→classify→evaluate lane *is* the
  intent-routing machinery; its drainable unmet-request row is floor work.
- **Shell takes the cross-cutting surface contracts** — C-LegibleOutcome,
  C-ProgressVisibility, C-DeclaredStubs, C-HonestyBanner apply to every
  module's controls but are obligations *of the surface layer*; modules
  inherit them through their shell dependency rather than duplicating the
  convention.
- **C-ContactTags → ledger** (tags are ledger rows); **C-ConnectorSet →
  sources** (the connector catalog is source configuration);
  **C-UserFacingPriority / C-ExplicitPolicies → tools** (work-execution
  policy); **C-EthicsGate → personas** (machinery beneath the
  prompt-specified imitation mark, a personalities-section requirement).

## Phase-0 contract (ruled 2026-11-26)

For each module a cycle touches, **before its machinery exists**:

1. Instantiate every owned scenario's named checks per its Forms column —
   including the discrimination inputs the scenario text implies.
2. Instantiate the module's edge-case conventions as negative tests, kept
   **alongside the positive checks** in `scenarios.md` Checks.
3. Verify corpus completeness — every named scenario's checks present,
   positive + negative + edge — **before the build spawns** (coordinator
   gate, runbook §2).
4. Record the all-red baseline run.

Construction greens module by module in dependency order. Completeness =
**green count**; the un-greened remainder is declared absence.

## Open — none outstanding

The four decisions above are ruled. Next open item belongs to direction-007:
confirm this doc `approved → in-force` at intake.
