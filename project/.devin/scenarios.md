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
