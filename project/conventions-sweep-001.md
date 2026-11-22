# Convention reclassification sweep — 2026-11-19

Per owner ruling 3 in `conventions-001.md`: every D-* record and every review finding
classified across the three-layer model — **prompt** (specified behavior — "requirement"
is not a defined corpus term; the prompt needs none), **convention** (challengeable,
never ignorable — recorded departure required), **implementation choice** (free), or
**harness** (evaluation machinery). Recommendations pending owner adoption.

## D-* records

| Record | Proposed class | Explanation |
|--------|---------------|-------------|
| D-ProductNaming | implementation choice | The record itself says independent implementations choose names; A12 concern is owner-visible but doesn't make naming conventional |
| D-PersistentLocalIndices | **C-LocalIndices** | Stable local indices for persistent objects is a proven, converged pattern (avatarID/toolID); labels and encoding free — prompt already specifies the durable-identity behavior |
| D-DyadicNormalization | **C-DyadicConfidence** | Shared normalization gives independent builds comparable confidence semantics and threshold discipline; math details challengeable |
| D-CertaintyPrivilege | split | **User-set supremacy: C-UserSetSupremacy** — briefly ruled prompt-level then reclassified convention per owner rulings 2026-11-19. Dyadic-top + recency mechanics: **C-CertaintyPrivilege** |
| D-ResponseDepth | implementation choice | Record itself marks conversational dynamics implementation work; user-facing depth control is one realization among others |
| D-LedgerStorage | **C-JsonlLedger** (seeded) | Independently converged in GreyAvatar and Meridian — strongest convention evidence |
| D-TemplatesAndWorkshops | **C-TemplateDerivedUI** | Form/execution-check derivation from templates converged in both builds (Meridian: derived workshop forms) |
| D-HostAndSurfaces | **C-HostAuthority** | Authoritative host + satellite surfaces is a proven topology; transport/topology free unless an exchange agreement pins it |
| D-SpeechScheduling | **C-SpeechFloor** | Serialized playback admission — the convention that would have prevented v0.3's overlapping-voices failure. The floor itself is C-PerceivableRespondents (P2 reclassified convention); the queue/FIFO manner is this convention |
| D-IdleTurnAsTool | **C-StewardAsTool** | Stewardship as a configurable, assignable tool — converged (Meridian: configurable steward thread) |
| D-BackgroundThrottling | **C-UserFacingPriority** | The *policy direction* (background yields to user-facing) is conventional; scheduler mechanism is free; the responsiveness outcome is already prompt-required |
| D-EngineMapping | **C-EngineMapping** | Portable preferences vs device mapping separation is a proven seam (AVQR voice guide); engine selection free |
| D-ExchangeEncoding | **C-ExchangeLayers** + contract note | **Owner correction 2026-11-19: this is layered, not single** — multiple encoding layers and channels (2D-barcode encode *and* read is itself a big step; AVQR, codebooks, envelopes, printed budgets, postcard batch are separate layers). An adopted schema pins provisionally within its layer (evolving over time; revocable through the schema's own process); departure always available by not claiming the schema — you can't claim the contract while breaking it |
| D-InterfaceOrganization | **C-InspectionSurfaces** | Library/Studio/Storefronts organization is a proven UX pattern; labels/layout free |
| D-FixedPolicies | **C-ExplicitPolicies** | The pattern of explicit thresholds/budgets/retry limits is conventional; each value separately reviewable |
| D-UnmetNeedRecords | **C-UnmetNeedRecords** | Converged in both builds (Meridian: unmet-need floor); record-shape details replaceable |
| D-ResponseAcceptanceEncoding | **C-AcceptanceChecks** | Executable adequacy checks + candidate retention + confidence-lowering is the proven seam; regex encoding free |
| D-ToolMatchingByRegex | split | Regex itself: implementation choice (record says so). The deterministic-match *plus* LLM-review pairing: **C-DeterministicMatchReview** convention candidate |
| D-ToolTrustChurn | prompt-side | The rank-adjustment behavior is shortcoming A5 — prompt material, not convention (record itself: implemented incorrectly = defect). Mechanics free |
| D-SourceConfidenceCeilings | **C-SourceCeilings** | Per-source confidence ceilings are a proven realization. Mixed-results review — mechanism corrected per owner 2026-11-19: **records are immutable; values are never changed, newer entries are derived and used, creating the audit trail** (already prompt-required semantics: corrections add assertions). The review loop's own classification stays flagged for the prompt pass |
| D-SourceRelevanceDomains | **C-SourceDomains** | Domain-described sources is a proven realization; vocabulary/matching free |
| D-StructuredSpecialtySearch | split per owner 2026-11-19 | Multi-source access capability → **C-MultiSourceAccess** (P5 reclassified convention). **Conventions:** **C-CompetingSources** (Wikipedia and Google as separate competitors); **C-SpecializedListRetrieval** (evaluating specialized over general search for list completion — the machinery behind S-list-project's defensible answers); **C-ConfiguredAccounts** (gmail, calendar, profiles access); **C-ContactTags** (ledger tags for contacts) |
| D-DevelopmentHarness | outside sweep | Governing process realization — lives in the harness layer, not the product spec layers |

## F-entry classification

| Finding | Class | Explanation |
|---------|-------|-------------|
| F1 imitation mark | prompt | Prompt-specified verbatim §Personalities + owner MVP ruling; apparatus below it → C-EthicsGate |
| F2 calendar reasoning | prompt | Already prompt-specified (§Projects and temporal context); adherence gap → direction |
| F3 competing tools | prompt | Already prompt-specified (demo #7); adherence gap → direction |
| F4 connector breadth | **C-ConnectorSet** | The conventional source catalog (17 connectors); narrower is a recorded challenge — breadth level is conventional, sources-as-a-capability is required |
| F4 ethics-gate depth | **C-EthicsGate** | Liveness research, objection/compliance flow, gate cards — the realized machinery delivering F1's prompt-specified behavior |
| F4 presentation glass | **C-PresentationGlass** | Asset pipeline + portrait frames + ambient motion; the conventional machinery beneath P3's generated-art proposal |
| F4 conversation archive | **C-ConversationArchive** | Per-turn archive + topic segments; proven realization of ledger-retained history |
| F4 set-build | **C-SetBuild** | The conventional machinery under S-list-project — geographic set fulfillment |
| F4 agentic tool protocol | **C-AgenticProtocol** | Tools-invoking-tools protocol; proven realization of the prompt's agentic-tool specification |
| F5 scenario enactment | convention | P1 reclassified convention 2026-11-19 → C-ScenarioEnactment; the canonical test set itself → C-CanonicalScenarios |
| F6 voice dynamics | convention | Floor → C-PerceivableRespondents (P2 reclassified); manner → C-SequentialRespondents + C-SpeechFloor |
| F7 generated art + voices | convention | P3 reclassified convention 2026-11-19 → C-PersonalityArt + C-VoiceDiversity (owner-expanded); machinery → C-PresentationGlass |
| F8 connectors | = F4 C-ConnectorSet | Same item, restated in parity terms |
| F9 criteria anchoring | harness | Evaluation convention, not product layer |
| F10 time capture | harness | ditto |
| F11 usage-case discovery | harness | ditto — encoded in AGENTS.md + proposed H1/H2 |

## Owner-declared conventions (2026-11-19)

| ID | Convention | Explanation |
|----|-----------|-------------|
| **C-DesktopShell** | The installation must be **capable** of running as its own application with a separate GUI — capability, not the only allowed method. Browser display is a legitimate channel, expected-best for satellite devices | Owner-declared (refined same day); expected to be the **first challenged** convention. GreyAvatar: Tauri desktop shell; Avatars: Tauri app. Meridian v0.3.0.001 departed silently — browser-*only*, no dedicated-shell capability ("desktop/device shells: absent") — under the rule that's an unrecorded departure; the layer catches it retroactively. What fails is the missing capability, not browser use itself |
| **C-FullScreen** | Ability to display full-screen | Owner-declared, held **for portability's sake** — a surface-capability convention: realizable across installation surfaces |
| **C-SupportedOS-\*** | **Ranked** supported-target list for fleet implementation — each is its own convention, and the ranking itself is conventional (priority order) | Owner-enumerated 2026-11-19: **1. Windows 11 · 2. Android satellite devices · 3. Bluetooth support for Echo devices · 4. Windows 10 · 5. TAB-YOGA satellite · 6. Linux · 7. Raspberry Pi** |

## Owner-reclassified additions (2026-11-19)

Owner ruling: **P1–P5 are conventions, not prompt amendments** — and test criteria can
themselves be conventions. `prompt-amendments-001.md` superseded.

| ID | Convention | Explanation |
|----|-----------|-------------|
| **C-ScenarioEnactment** (was P1) | Named usage scenarios are enacted on real inputs; canned/seeded substitutes don't satisfy without a recorded challenge | Test criteria as conventions: a build may challenge (canned demos) but must acknowledge, evaluate, explain |
| **C-PerceivableRespondents** (was P2) | Respondent contributions remain individually perceivable; overlapping speech that renders them indistinct is a departure requiring a recorded challenge | The voice-dynamics floor as convention — floor by default, challengeable |
| **C-PersonalityArt** (was P3) | Where generation capability exists, each personality's generated art is unique to that personality — not shared or placeholder media | Owner-expanded same day to include voices |
| **C-VoiceDiversity** | Personalities' voices are diverse and modifiable | Owner-declared alongside C-PersonalityArt |
| **C-UserSetSupremacy** (was P4) | User-set values outrank derived/inferred/source values regardless of support; nothing silently supersedes a user-set value | Convention per owner's final ruling — challengeable-with-record; owner confirms platform context may obviate need or method |
| **C-MultiSourceAccess** (was P5) | Capability to access multiple configured sources so distinct personalities carry different information | Convention per owner's final ruling — same obviation clause applies |

## Convention count after sweep

Seeds (7) + D-derived (17) + F4 machinery (6) + structured-retrieval
decomposition (4: CompetingSources, SpecializedListRetrieval, ConfiguredAccounts,
ContactTags) + owner-declared (3: DesktopShell, FullScreen, SupportedOS family) +
reclassified prompt-amendments (6: ScenarioEnactment, PerceivableRespondents,
PersonalityArt, VoiceDiversity, UserSetSupremacy, MultiSourceAccess) =
**43 conventions — ADOPTED 2026-11-19** (owner approval; earlier count of 41 was an
arithmetic slip — 17 D-derived, not 15). User-set supremacy and multi-source access
were briefly ruled prompt-level, then reclassified conventions per owner rulings
2026-11-19.
