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

## Scenario notes

- **S-list-project:** no exact answer exists, but there is a huge variety of bad answers
  (townships or CDPs passed off as cities, tiny subsets, invented names, duplicates,
  criteria reset on refinement). Score the delivered list's defensibility — real
  incorporated municipalities, breadth, preserved criteria — plus non-matches recorded as
  results-that-do-not-match for review, per D4.
- **S-personality-create:** good coverage of many parts working together — identity
  assignment, portrait/voice/characterization needs generated, and the resulting persona
  coherent and distinct. Score coherence of the whole, not the parts' existence.
