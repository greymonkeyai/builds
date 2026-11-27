# Prompt snapshot — revision 2026-11-27-a
<!-- harness-doc kind=prompt status=in-force -->

Assembled 2026-11-25 for project line `project`.
The revision in force for every cycle of this project until a review adopts a new one.
Re-assembled 2026-11-27 ahead of cycle-8 — `prompt-amendments-002` (environmental
grounding: device location + meteorological data) adopted upstream into
`ProjectPrompt.md` §Projects and temporal context; revision advanced to 2026-11-27-a.

## Assembled from

| Source document | Corpus revision |
|-----------------|-----------------|
| `C:\Project\MigrateInbound\ProjectPrompt.md` | 2026-11-27 |
| `C:\Project\Design\INTENTS.md` | 2026-11-24 |
| `C:\Project\Design\MAXIMS.md` | 2026-11-24 |

Cited depth tier (consultable, not embedded):
`C:\Project\Design\INTENTS_explained.md`, `C:\Project\Design\MAXIMS_explained.md`,
`C:\Project\Papers\`

## Executed under

- Cycle 5 — direction-005 (2026-11-25)
- Cycle 6 — direction-006 (2026-11-25)
- Cycle 7 — direction-007 (2026-11-26)

---
# Project Prompt

Develop an independent implementation of a private, local-first ecosystem in which a persistent assertion ledger records semantic state, distinct personalities interpret that shared ledger through their own lenses, configurable tools perform useful work, and locally controlled devices provide capabilities and surfaces for the user. The implementation may use any programming language, architecture, model provider, storage arrangement, or interface method that preserves the behavior below.

## Purpose and scope

The system exists to benefit its user through useful local agency. Its goals include reducing dependence on provider services, lowering the cost of useful agentic work, and helping the beneficiary consider — or, when authorized, automate — evaluation of their own best interests.

The user is the party the installation serves; audiences and interlocutors may interact with an installation without becoming its user, as when a public installation serves visitors on behalf of an operating organization.

The default target is a private installation on physically local, user-controlled devices. A local network may connect several devices and surfaces. The installation may coordinate different local models, tools, and input/output devices, but hardware assignment and model distribution are implementation choices. Remote services and broader federation are optional integrations or exchange paths, not requirements of the default installation.

## Assertion ledger

The assertion ledger is the book of record for persistent semantic application state. A user input becomes a typed, attributed assertion. Assertions retain their source, typed value, certainty, provenance, time, and relationships to later assertions. Contextual confidence ranks applicability separately from the assertion's certainty. Computed views, caches, payload stores, and segmented files may support the implementation, but they remain subordinate to the ledger and do not become a second descriptive truth store.

The ledger preserves the distinction between captured input, interpretation, source evidence, generated response, execution evidence, user choice, and durable result. Corrections and supersessions add related assertions rather than silently recontextualizing the original event.

## Governing cycle

The application forms a continuing cycle in which inputs, source evidence, candidate interpretations, tool results, presentations, user responses, actions, and corrections become related ledger assertions. Those assertions inform the ranking and selection of future work. Recording information does not by itself make it true, accepted, or actionable. The cycle may defer, repeat, combine, or omit stages according to the work and the tools involved; this relationship is functional, while its sequencing and coordination are implementation choices.

## Work and unfulfilled requirements

The application evaluates user and system inputs for explicit or incidental opportunities to invoke agentic tools. When an opportunity is detected, the work is recorded in the ledger as an assertion describing an unfulfilled requirement. The requirement is governed by a template containing slots, candidate values, tests, required and optional information, and conditions for a satisfactory result.

Candidate values remain inspectable with their source and confidence until a tool invocation selects the values required by its input contract. A need may be created with missing, partial, or competing candidates. Creation does not imply execution. Execution evidence, responses, errors, and results are recorded as further assertions.

An execution attempt can finish without satisfying the requested outcome. An insufficient, failed, stale, conflicting, or malformed result remains recorded and leaves the need available for later work. The need remains Open until its declared satisfaction conditions are met, or it is Cancelled or Superseded. A user-facing queue, focus view, library, or other interface may expose and edit needs without becoming the source of truth.

The smallest valid input may begin useful work. A requirement's template generates the information it still needs as deferred work, so a task such as an open-ended list can elaborate progressively. Successive inputs refine an existing requirement's criteria rather than resetting them; refinement is expressed through related assertions, not by rewriting the original requirement.

## Projects and temporal context

The application represents complex intentions as projects: sequences or collections of goals that organize related work and eventually become tool calls. A project can be created, advanced, or revised through chat or another available interface. Its goals, related unfulfilled requirements, tool attempts, progress, results, and historical evidence remain connected to the assertion ledger.

Project work may include publishing through a specialized interface, creating a personality, or any other multi-step outcome. The project is the organizing structure for those goals; the particular decomposition into tools, prompts, and interfaces is an implementation choice.

The application can interpret calendar and other temporal sources so that upcoming, current, and historical events can inform project work, personality responses, and relevant background attention. Calendar entries remain source evidence; their interpretation, confidence, and resulting actions are governed by the same ledger and authority rules as other data.

The installation grounds itself in place as well as time. Device location — the physical placement of hosts, surfaces, and joined devices — is recorded in the ledger as attributed assertions, derived from configured values, discovered platform or network signals, or user statement; uncertainty and staleness are recorded, not smoothed over. Environmental data such as meteorological conditions enter through configured sources like other outside information: the admission gate applies, and results are claims carrying provenance, confidence, and freshness. Personalities may draw on location and environmental data as ordinary grounding for responses, planning, and background attention — an opinion about weather may be backed by observed local conditions where known, and marked by register where it is improv.

The installation's home location is canonical. A user may take a device out of the home location and return it — while away, that device's environmental claims refer to its current location where known, with staleness recorded rather than hidden; on return they re-converge on the home site. Departure, roaming uncertainty, and return are the interesting cases; multi-site federation is not required of the default installation.

## Confidence and selection

Confidence ranks the applicability of a candidate answer or result to a system need. Its value is contextual: input interpretation, source reliability, answer adequacy, and user selection are distinct kinds of evidence. Each assertion identifies its source and cannot inherit more confidence than that source provides. Exposure or storage does not by itself make an assertion true, accepted, or actionable.

When candidates are otherwise comparable, recency may resolve a confidence tie. Values must pass the tool's declared acceptance tests before they are eligible candidates, and required slots must meet their applicable thresholds before execution. The representation of confidence, including any normalization or privileged values, is an implementation choice unless a tool or exchange contract requires otherwise.

## Personalities and lenses

Personalities are distinct, persistent participants that interpret the same host-local ledger through different points of view, interests, responsibilities, characterization, and modes of expression. Their distinct perspectives do not imply separate knowledge stores. A personality may be assigned configured sources and tools so it can interpret outside information or perform useful work for the installation.

Where the installation provides suitable surfaces, it supports characterized responses through those surfaces. A chat input normally requests a chat response in kind. The number of respondents, their order, their voices, their images, and their conversational dynamics are implementation choices, provided that the resulting personalities remain distinct and relevant.

An installation's audience is composed of persons: the user, and others the installation may never identify. Persons reach an installation through surfaces and channels — observed at a surface, addressed through outbound communication, listening to presented output — and a person may be represented in the host's ledger as attributed records. Representation is not required for audience membership; the same person may appear as a ledger record, a presence at a surface, and a recipient or listener through different means, and these appearances may converge on one identity. A record holds claims about a person; it is not the person, and its thinness or absence describes what the host knows rather than who the person is.

A personality recognizes the persons in its audience, represented or not, as having their own circumstances, knowledge, and purposes that extend beyond their engagement with the installation. Claims about a person require attributed evidence; what a personality does not know remains unknown rather than supplied by invention.

A personality modeled on a recognizable figure presents an imitation of that point of view, not the figure's identity or authority. A personality that imitates a person, living or deceased within the last ten years, requires that the user be admonished and that the personality's display carry a permanent distinguishing mark identifying it as an imitation. This boundary supports performers' artistic contributions and the dignity of the living and recently deceased; the forms of admonishment and of the mark are implementation choices.

## Tools and local comparison

Tools are persistently identifiable capabilities with definitions that describe their purpose, inputs, expected results, acceptance tests, and optional or required values. Tools may be invoked through an interface or discovered from user and system inputs. One input may create several tool opportunities while also requesting a conversational response.

The application supports the development and deployment of competing tools to anticipate which choices will best serve the user. Competing implementations are compared locally when their definitions express the same need and their results are interpretable under a shared local understanding. Confidence, recency, tool criteria, and user acceptance may inform the comparison. The user need not be shown alternatives in every interaction.

## Background activity and attention

The installation continues useful work while the user is not actively providing input. It can search the assertion ledger, process newly available personal-source data, complete research, assess results, and prepare relevant opportunities for presentation. Background work must preserve prompt and direct-command responsiveness and must not treat user silence as consent to an unrelated consequential action.

The mechanism that coordinates recurring attention, background completion, user availability, and tool assignment is an implementation choice. A completed task may become a relevant opportunity for a personality to summarize through an appropriate surface when the user is available.

## Communication and surfaces

Typed language, spoken language, chat, text-to-speech, images, OCR, device surfaces, ledger records, email, postcards, QR or AVQR packages, and other channels may carry different aspects of an interaction. Input devices such as microphones, scanners, and cameras are channels for receiving information; they do not require a particular internal file format.

The system may consider context or work off-channel and present it later when it becomes relevant. A communication request and its status, error, or other outcome are recorded as assertions regardless of whether the channel is chat, email, or another medium.

Nonlocal effects require a configured, high-confidence authority path. Conversational interpretation alone does not publish or send email. Whether a tool drafts, queues, publishes, requests user promotion, retries, or reports delivery is determined by that tool's configuration. A request for a consequential effect that lacks an authorized path resolves to an understandable refusal or deferral — recorded with its status — rather than silent non-action. Interfaces such as a media-specific Studio are optional implementations.

User preferences for configurable interface and display choices are recorded in the assertion ledger.

## Continuity, recovery, and cleanup

An installation must preserve useful operation and understandable next steps across ordinary restarts, power loss, partial execution, and unavailable capabilities. Host ledgers may intentionally diverge as local personality information is refined; cross-host identity is not assumed.

Personalities and tools form a privileged class of persistent objects: their identities are preserved outside the ledger's semantic records, scoped to the installation, and intended to diverge as different installations develop them. How those identities are indexed and stored is an implementation choice.

Cleanup is the governed process for keeping ledger storage within its available resources. It consolidates records and compresses expected or unexpected activity without losing the provenance, confidence, exceptions, or recoverable detail needed by later work. Ordinary interaction, search, validation, and background assessment do not delete assertions. Cleanup rules may vary by record type and may run during recovery or outside the primary interaction cycle.

## Exchange and storefronts

Independent implementations can exchange agreed meanings if they can agree on an ExchangeSchema. A storefront may package a personality, a collection of tools, and other assertions, including unfulfilled requirements. A receiving host records imported assertions below the threshold for action or acceptance by default, then resolves them through its own ledger, capabilities, and permissions.

AVQR is one possible ExchangeSchema implementation; plain-language exchange is another. Interoperability concerns agreed definitions and meanings, not a universal internal data model or file type. Exchange media, serialization, scanning, and validation methods remain implementation choices.

## Observable demonstrations

An implementation should be reviewable through demonstrations such as:

1. Recording a typed or spoken user input as a source-aware assertion.
2. Creating and filling a template that governs an unfulfilled requirement from explicit or incidental tool work.
3. Ranking candidate values by contextual confidence and recency, retaining failed evidence.
4. Completing a multi-step list request while preserving its criteria and recording headers, foreign links, and category errors as results that do not match the requested criteria, retaining them for review and cleanup.
5. Creating a minimal personality and extending it through later portrait, voice, and characterization work.
6. Presenting a relevant background result through a distinct personality while preserving the ledger evidence.
7. Comparing locally competing tools that express the same need and produce comparable results.
8. Recovering useful state after restart and consolidating records without losing provenance.
9. Importing a storefront or exchange package while retaining its contents below the threshold for action or acceptance.
10. Refusing or deferring an unconfigured nonlocal publication request while recording the request and its status.
11. Creating or advancing a project from chat, decomposing its goals into tool work, and relating that work to upcoming, current, or historical calendar events.

These demonstrations are evidence of the required behavior, not prescriptions for a particular user interface, scheduler, model, storage format, or programming language.

An implementation is expected to expose observable evidence for criteria named by the review process — logs, records, or other accessible artifacts — in a form external assessment, including machine assessment, can consume. The set of named criteria is supplied with each evaluation direction and may change between runs; the accessible form is an implementation choice.

---

# Design — project steering tier

Adopted steering statements and maxims for this project. These carry the
design's rationale and preferred paths; the corpus commentaries
(`INTENTS_explained.md`, `MAXIMS_explained.md`) and `Papers/` hold the depth
behind each statement.

# Intents

Project-scoped steering statements — the same type as MAXIMs, binding this project's
design rather than candidate-universal practice. Each names a situation and states the
preferred path (M-Steering). Adopted 2026-11-24; wording remains revisable like all
design statements (M-Revision).

Commentary: `INTENTS_explained.md` — same identifiers and order, same relationship
as `MAXIMS.md` to `MAXIMS_explained.md`. Depth tier: `Papers/` holds the white
papers each intent compresses. Intents may restate guarantees the Project Prompt
requires; they carry the rationale, which is their job.

Scope note: an intent can be project-bound by nature — correct here while contrary to
general practice (see I-Engagement). Whether an intent generalizes is a review
question, not a property of the intent; promotion to M-* runs through the existing
MAXIMs review. History and workflow: `MigrateInbound/InstructionsForMAXIMS.txt`
(Intents note, 2026-11-24).

## I-Delegation: Authority over work is bound before the decision arises: scopes carry attributed, confidence-bearing assignments, and the assigned steward answers for its scope.

## I-Conferral: Work outside assigned authority continues as conversation: the request, its status, and the path to authorization are recorded and remain available.

## I-Discrepancy: When personalities diverge on shared ledger state, each answer carries its claimant and the divergence is presented, so the user can compare named advisors.

## I-Precedent: Rank and confidence changes take effect as new assertions; every consumer re-derives at read time, so one ruling propagates to every scope it reaches.

## I-Dyadic: Confidence moves pick the simplest representable value between neighbors, so each reorder is a fresh append and the prior standing stays in the journal.

## I-Engagement: Bookkeeping, provenance, and recall are automated; choice points remain user-facing, because judgment is the part of the experience the user keeps.

## I-Attachment: Persona shape is user-authored and revisable; attachment tracks the user's own investment in the character.

---

Promoted out: I-Steering → M-Steering (corollary under M-Affirmative, adopted
2026-11-24 — see `MAXIMS_history.md`).

---

# MAXIMs

## MAXIM-Prototype: These MAXIMs should guide planning to prevent predictable mistakes.

## M-Freedom: Ask if you want more than you have.

## M-Revision: Every rule is subject to revision.

### M-Coherence: Check MAXIMs for consistency with one another.

### M-Discipline: Revise procedures in review; surface improvements in execution.

## M-Materialism: All things are either physical substance or constructed meaning.

### M-Reality: The supernatural is fictional.

## M-Lens: Every communication is an imperfect observer's reflection of reality.

### M-Origin: Life arose by abiogenesis.

## M-Adequacy: Gate on requirements.

### M-Affirmative: Avoid negative statements.

#### M-Steering: State preferred paths; a path steers where a prohibition only blocks.

## M-Simplicity: Assume you have the tools you need before planning a task.

## M-Invention: The only solutions are imitation or invention.

## M-Honesty: Offer only what you can deliver.

## M-Benefit: Only promote solutions that serve the user's interests.

### M-Ownership: User intentions are primary, even when unknown.

## M-Novelty: Surface conflicts through conversation.

## M-Fitting: Adaptive utility is the measure of success.

## M-Entropy: Change is constant.

### M-Grace: Fail gracefully.

## M-Compression: Compression is prediction.

### M-Convention: When data is absent, default to Schelling points and existing reference samples.

### M-Absence: An event that is anticipated is notable in its absence.

## M-Village: Social capacity is limited.

## M-Impersonation: Consent is required before imitating the living, and the recently deceased.
