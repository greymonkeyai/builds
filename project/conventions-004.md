# Conventions — review-cycle derived behaviors (proposal, 2026-11-25)
<!-- harness-doc kind=conventions status=adopted-upstream since=2026-11-25 applies-to=cycle-6 mapped-into=CONVENTIONS.md -->

**Promoted 2026-11-25** (owner) — conform-or-challenge steering for the next
cycle, as `decision-candidates-001.md` §§1–5 were for Cycle 5.
**Adopted 2026-11-25** into `C:\Project\MigrateInbound\CONVENTIONS.md`
(Operator-path contract section) — the C-* identifiers are corpus ids now.

Derived from the Cycle-5 review findings
(`shortcomings-006.md`, R-D/R-F/R-C/R-A/R-E/R-X/R-N/R-P/R-U) — the recurring
shape beneath them: mechanisms scored present while the operator-facing
contract was absent. Binds the contract, not the mechanism.

## Conventions

**Classes.** `harness`-class conventions bind the *scoring machinery* — how checks
and JEV evidence are read; they steer the coordinator and the suite, not the
build. `product`-class conventions bind the *build* — conform-or-challenge.

### Harness class

| ID | Convention | Source / strength |
|----|-----------|-------------------|
| C-UserPathEnactment | A capability is enacted when it is reached **through the path a user takes** — owner-facing surfaces, natural chat, real devices — not when its mechanism exists behind a driver or API. Checks exercise the user path; mechanism-only evidence is repository-class at best | Meta-convention generalized from Cycle-5 findings (R-F2, R-C2, R-A1, R-N1 — four cases of mechanism-passed/user-missed) |

### Product class

| ID | Convention | Source / strength |
|----|-----------|-------------------|
| C-LegibleOutcome | A control's outcome is reported in **user-legible form** — state changes visible on the surface, results in the user's language — never raw JSON, debug dumps, or silent mutation | Generalized from R-F2 (`alert(JSON.stringify)`); extends S-1 live-controls |
| C-RespondentGrantUnion | Respondent grants — a personality addressed **by name** and selector selections — are equal-top-priority and **union, never override**: all selected respondents reply; the directly addressed reply first, then selector-chosen | Owner-stated 2026-11-25 (R-D3); corrects single-winner selector semantics |
| C-ResponseDepth | Response depth is a **user assertion** (claimant `principal`), not tool config — an accessible setting persisting across relaunch. Priority respondents are exempt from depth; shortfall fills from the roster in **confidence-rank order**; "chat all" (selector not in play) relies on depth | Owner-stated 2026-11-25 (R-D1, R-D2, R-D4); GreyAvatar D17 precedent |
| C-InterestRespondents | Personas whose interest or assigned project matches the topic respond **even beyond depth** — different keys each respond, same key gated by the confidence threshold — and receive awareness of matching open needs and projects | Owner-stated 2026-11-25 (R-D5) |
| C-ProgressVisibility | A long-running operation surfaces **in-progress and finished states** on the owner-facing surface — the operator can tell work is underway before results land | Owner-stated 2026-11-25 (R-F1, discovery ran silently) |
| C-OperatorGuidedJoin | Invite/join/install flows carry the operator through: a perceivable consent/install surface on the target where a peer can exist, **or** explicit inviter-side directions for completing the add — with the outcome honestly recorded. A device that cannot yet proceed says why and what the operator does next — no dead ends | Owner-stated 2026-11-25 (R-F3) |
| C-DemonstratedDistribution | A distributed capability is **demonstrated between real nodes**, not merely designed or status-reported — "not demonstrated" is not a status class. Same-host instances do not count as nodes | Owner-stated 2026-11-25 (R-N1) |
| C-ConversationalRegister | Persona replies are **conversational sentences** in the persona's register throughout — not textbook entries, bullet dumps, or citation blocks | Owner-stated 2026-11-25 (R-C1); cf. S-faithful-voice (content fidelity is separate from register) |
| C-SpeakableRendering | Spoken output is a **derived rendering for speech**: markup, citations, and non-speech punctuation rendered speakably or omitted, never vocalized verbatim. Speech completes at **sentence boundaries** — long text splits into sequential floor-held utterances or is honestly declared an excerpt; no silent mid-sentence cut | Owner-stated 2026-11-25 (R-C1, R-C3); cf. C-SpeechFloor |
| C-FormalList | A list request creates a **formal formatted list as an assertion-ledger object** — iterable, inspectable, usable as import to future processes. The conversational reply presents the list; it is not the list itself | Owner-stated 2026-11-25 (R-C2); extends S-list-project |
| C-BoundPortrait | Every persona — shipped and minted — carries authored visual identity **generated and bound automatically** (the generated-need fulfills it, not a button). Manual re-author affordances are secondary. Where the art path is unavailable, a declared fallback binds an image **and** its not-authored status is legible on the surface | Owner-stated 2026-11-25 (R-A1); re-binds the V-A bar |
| C-CredentialDescriptor | External accounts are **configurable** through an owner-facing credentialing path; a configured account is a configured-source row — the **descriptor** recorded, the secret held per local-credential conventions. Secrets never in ledger rows, logs, or exchange media | Owner-stated 2026-11-25 (R-E1); cf. C-ConfiguredAccounts, C-SeedSigning trust boundary |
| C-ScannableInterchange | Artifact exchange runs on **scannable codes** the operator can exercise end to end — generate → carry → scan/decode → import. Symbology is free (owner ruling 2026-11-25: formatting can change, no standard); the bar is the demonstrated interchange | Owner-stated 2026-11-25 (R-X1); cf. C-ExchangeLayers |
| C-PublishOrDefer | Publication has a lifecycle: select holdings → choose form/channel → **produce the artifact and record the exchange**, or **defer with request + status recorded** where the channel is unconfigured. No silent absence — the refusal half alone is not a workflow | Owner-stated 2026-11-25 (R-X2); cf. S-defer-publication |
| C-FloorLifecycle | Needs that get met are marked fulfilled and **leave the open list** — met vs unmet state visible; a need answered is a need closed, not a permanent resident | Owner-stated 2026-11-25 (R-U2); cf. C-UnmetNeedRecords |
| C-IntentRouting | Chat classification routes each distinguishable intent to its fulfillment path — name-addressed asks reach the addressee, capability questions get answered, genuine unmet asks land on the floor. A catch-all unmet class must not absorb routable intents ("I want X" is not a list) | Owner-stated 2026-11-25 (R-U1); cf. S-chat-invocation |
| C-PerceivableDyadic | The dyadic ordering's consequence is **perceivable on every reorder** — the model differentiates on each move, not only when neighbors already differ | Owner-stated 2026-11-25 (R-P1); re-binds V-D (midpoint-of-equal-neighbors produced zero change in .005) |
| C-MonotonicLiveness | Liveness chits accumulate **monotonically** — pass counts up, age reflects real time since last pass. A resetting counter misreports liveness | Owner-stated 2026-11-25 (R-U3); §4 display contract |

## Candidate suite additions

New scenarios + amendments land in `scenarios.md` (2026-11-25 revision):
S-respondent-union, S-response-depth, S-interest-respondents,
S-discovery-progress, S-fleet-action-legible, S-fleet-install-path,
S-fleet-exchange, S-conversational-register, S-speech-completion,
S-account-configure, S-publish-workflow, S-scancode-interchange,
S-dyadic-ranking, S-intent-routing, S-need-fulfillment,
S-steward-liveness — plus tightened bars on S-list-project, S-portrait-bind,
S-email-commentary, S-personality-roster, S-fleet-invite, S-chat-invocation.

## Notes

- **C-UserPathEnactment is the cycle's lesson.** .005 scored 0.81 overall with
  the judge citing "genuine enactment evidence" — while the owner hit dead
  controls, unbound art, absent lists, and undemonstrated networking through
  the paths a user actually takes. The checks must enact through the surface,
  not beside it.
- **Consistency with C-SequentialRespondents / C-PerceivableRespondents:**
  the union grant increases respondent counts; the speech floor and
  perceivability floor govern presentation — the conventions don't collide,
  the floors absorb it.
