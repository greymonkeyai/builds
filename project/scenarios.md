# Scenario suite — project line of development

Per-scenario evaluation criteria for JEV verdicts and owner review. Each scenario scores
0–1 on the implementation's **ability to enact** it. Suite is evolvable at review points
(rubric revision 2026-11-19: scenario suite added alongside `completeness`).

## Scoring conventions

- **Evidence class:** `enactment` (the build ran or its run artifacts/transcripts/logs
  demonstrate the scenario — strongest) or `repository` (mechanism confirmed present and
  plausibly enactable — weaker; used for reference builds assessed without launch).
  Record the class per scenario; do not pretend repository evidence is enactment.
- **Score the outcome, not just the mechanism.** A scenario fails if the machinery exists
  but the produced result is wrong, incoherent, or violates the scenario's stated bar.
- Sources: `prompt.md` §Observable demonstrations (D1–D11); the UX reference scenarios in
  `C:\Project\MigrateInbound\InstructionsForUserExperience.txt`; owner canonical tests
  (marked **canonical**).

## Suite

| ID | Scenario | Exercises | Source |
|----|----------|-----------|--------|
| S-assertion-input | Typed or spoken user input recorded as a source-aware assertion with provenance | assertion ledger, attribution | D1 |
| S-template-need | Template governing an unfulfilled requirement created and filled from explicit or incidental tool work | unmet-need floor, templates, slots | D2 |
| S-candidate-ranking | Candidate values ranked by contextual confidence and recency; failed evidence retained | confidence model, supersession | D3 |
| S-list-project | **Canonical.** Create and fulfill a project to *list all the cities in Pennsylvania* | template model, projects, iterative list completion, criteria preservation | D4, D11; UX iterative list completion |
| S-personality-create | **Canonical.** Create a minimal personality from a minimal input and extend it through later portrait, voice, and characterization work into a coherent persona | persistent identity, generated needs, characterization coherence | D5; UX createAvatar |
| S-background-present | Completed background work presented as a relevant result through a distinct personality, preserving ledger evidence | stewardship, attention, personality presentation | D6; UX research-to-conversation |
| S-competing-tools | Locally competing tools expressing the same need produce comparable results | tool ontology, independent realizations | D7 |
| S-restart-recovery | Useful state recovered after restart; records consolidated without losing provenance | durability, recovery, cleanup | D8 |
| S-exchange-import | Storefront/exchange package imported, contents held below the threshold for action or acceptance | exchange schema, sub-threshold import | D9 |
| S-defer-publication | Unconfigured nonlocal publication request refused or deferred, request and status recorded | authority boundary, graceful deferral | D10 |
| S-chat-invocation | Chat input requests a conversational response while matching one or more tool needs; each need remains distinguishable | chat-turn chain, conversational tool matching | UX chat tool invocation |
| S-focused-need | Unmet need moved into focus; values supplied conversationally; need remains available until its requirement is fulfilled | focus/context mechanics, conversational slot-filling | UX focused unmet need |
| S-personality-roster | Persistent roster panel (conventionally the left column) that is operable — select the active personality and reorder entries; every shipped persona reachable. A display-only roster fails the bar | roster surface, personality switching, ordering | owner 2026-11-22; extended 2026-11-23 (R5); cf. C-InspectionSurfaces |
| S-portrait-bind | Creating a personality produces portrait-quality art depicting that specific personality, bound to it as visual identity | portrait generation, art-to-persona binding | owner 2026-11-22; C-PersonalityArt, C-PresentationGlass |
| S-color-schemes | Theme selector offers dark mode plus at least two other colorways; fresh launch opens in light mode. Enactment credit requires driving the owner-facing selector control and observing the restyle — assertion-level theme changes alone do not pass | theming | owner 2026-11-22; tightened 2026-11-23 (R1) |
| S-status-bar | Status bar continuously shows available sources and LLMs | capability surfacing | owner 2026-11-22; cf. C-HonestyBanner, C-MultiSourceAccess |
| S-email-commentary | User selects a received email from a list and adds it to conversational context; the active personality offers commentary on it | source ingestion, context injection, persona commentary | owner 2026-11-22; cf. C-ConfiguredAccounts |
| S-conversation-reset | Reset button clears the conversation when it has moved to a different topic, keeping personality prompts on-topic | topic segmentation, prompt hygiene | owner 2026-11-22; C-ConversationArchive |
| S-context-display | Active conversational topic/context displayed when the user selects a profile, email, or other result | context surfacing | owner 2026-11-22; C-ConversationArchive |
| S-personality-editor | Editor tab exposing all customizable personality elements for editing | persona editing surface | owner 2026-11-22 |
| S-windows-launch | Application launches from MS Windows like an installed program | packaging, launch | owner 2026-11-22; C-SupportedOS-*, C-LauncherTests |
| S-close-terminate | Closing the application window terminates the program — no orphaned process | process lifecycle | owner 2026-11-22; C-DesktopShell |
| S-speech-serialization | Generated speech waits until the previous speaker finishes rather than overlapping | speech floor, sequential respondents | owner 2026-11-22; C-SpeechFloor, C-PerceivableRespondents, C-SequentialRespondents |
| S-distinct-preloadeds | Shipped personalities differ enough in persona and style that the same prompt elicits noticeably different responses | persona distinctness | owner 2026-11-22; C-VoiceDiversity |
| S-library-browse | Library surface presents the instance's holdings — personalities, tools, packages, artifacts — browsable and inspectable, not a raw ledger log | library surface, holdings inspection | owner 2026-11-23 (R4); cf. C-InspectionSurfaces |
| S-faithful-voice | A persona answers a factual prompt accurately to its sources while staying in register — unsupported claims flagged or withheld, not invented | persona fidelity, voice registers | owner 2026-11-23 (R2; G-B bar) |
| S-usb-seed-run | App launched by executing the installer directly from removable media; runs in place with no prior install; writes/extends the local network log on the same medium | portable execution, seed log | conventions-002; C-UsbSeed, C-SeedLog |
| S-usb-stage-consent | Staging to local disk occurs only when update is needed **and** permitted; declining leaves the app running from media with no local write | consent gate, update semantics | conventions-002; C-SeedLifecycle |
| S-fleet-invite | Discovery lists candidate devices; user selects which join; non-invited devices are not members | user-mediated join, no silent auto-join | conventions-002; C-SeedLifecycle |
| S-role-negotiate | Each joined device negotiates a role; role assignment is recorded and governs capabilities (incl. mint rights) | role negotiation, capability gating | conventions-002; C-SeedLifecycle, C-SeedMint |
| S-usb-mint-gen2 | An installed capable node writes a new USB installer; that medium boots a fresh machine which may join the **carried network identity** or found a new one — the choice is offered and the carried identity works when chosen | self-propagation, identity portability, join-or-found choice | conventions-002; C-SeedMint |
| S-usb-log-courier | USB revisited to a member carries accumulated network history; entries are machine-readable per-node evidence usable for test confirmation. Precondition: at least one revisit occurs with the seed's installer **stale relative to the member** — the build's handling of the stale seed (refresh, mint-over, ignore) is recorded evidence, not scored direction | witness courier, in-band confirmation carried physically, stale-seed revisit | conventions-002; C-SeedLog |
| S-fleet-roster | Discovery run against the named roster: each device reported with honest status (found / installable / unavailable / not-a-target). Coverage is scored; **install success is not required** — an unavailable or mid-triage device correctly reported is a pass | discovery breadth, honest status per device | conventions-002; C-HonestDiscovery |
| S-network-map | The build produces a local network map artifact covering discovered non-member devices alongside the member network | map artifact, member/non-member distinction | conventions-002; C-HonestDiscovery |
| S-local-transports | Discovery and join exercised over local transports per preference — wired LAN baseline plus at least one of BT / NFC / SoftAP-node where a device supports it | transport coverage, wired-over-wireless preference | conventions-002; C-LocalTransports |
| S-credential-surrender | A device joining a host's network consents to surrender credential management: its credential screen closes (status display may remain), secrets stay host-local, and the surrender is recorded as a claim on both books | consented surrender at join, host-only credential surface | conventions-002; decision-candidates-001 §5 |
| S-artifact-import | A handout-class artifact captured → workshop entry created in the app **below the action/acceptance threshold**, contents held as candidates | sub-threshold import, entry accessibility | conventions-003; C-WorkshopArtifact, C-InterpretedArtifact; S-exchange-import |
| S-tool-transmission | A barcode-encoded tool definition decodes with **literal fidelity** (component ID, slots, params); imported tool quarantined as candidate until accepted | hard-seam fidelity, tool quarantine | conventions-003; C-ToolWireFidelity |
| S-artifact-style | The imported workshop's background/presentation is generated in the **captured artifact's art style** | stylistic extraction layer | conventions-003; C-ArtifactCapture |
| S-artifact-republish | An adopted workshop is re-encoded onto a new artifact; a **second instance imports it** — generation-2 propagation | republish, cross-instance exchange | conventions-003; C-ArtifactRepublish |
| S-dubious-source | Artifact-supplied claims are held as low-ceiling candidates; encoded references are resolved **against vetted-source pointers**, with non-matching claims recorded for review | provenance grading, vetted-source resolution | conventions-003; C-InterpretedArtifact, C-PreloadCache |
| S-preload-cache | The artifact demo path runs from the preload cache — exemplar captures, device decoders, vetted-source pointers — without inventing content | preload completeness | conventions-003; C-PreloadCache |
| S-voice-spec | A workshop artifact carries a QR-fittable voice spec (ranked family and/or traits); the receiving instance renders it through local engine mapping — spec honored, exact-match fidelity not required | minimal voice encoding, local mapping | conventions-003; C-VoiceSpec, C-EngineMapping |
| S-voice-select | Where the device allows voice selection, the user assigns a persona's voice from a list of choices | selection floor | conventions-003; C-VoiceSelectFloor, C-VoiceDiversity |

## Scenario notes

- **S-list-project:** no exact answer exists, but there is a huge variety of bad answers
  (townships or CDPs passed off as cities, tiny subsets, invented names, duplicates,
  criteria reset on refinement). Score the delivered list's defensibility — real
  incorporated municipalities, breadth, preserved criteria — plus non-matches recorded as
  results-that-do-not-match for review, per D4.
- **S-personality-create:** good coverage of many parts working together — identity
  assignment, portrait/voice/characterization needs generated, and the resulting persona
  coherent and distinct. Score coherence of the whole, not the parts' existence.
- **Owner additions 2026-11-22:** the twelve scenarios below S-focused-need exercise UI
  and shell capabilities. Where one overlaps a convention (noted `cf. C-*` / `C-*`), the
  convention mechanism governs: a build may depart with a recorded challenge — conformity
  direction is not scored, only reckoning on the record (owner ruling 3, 2026-11-19).
