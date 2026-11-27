# Named deficiencies — direction-005
<!-- harness-doc kind=shortcomings status=discharged applies-to=direction-005 mapped-into=scenarios.md -->

Compiled 2026-11-25 by the coordinator session from the owner's Cycle-4 review
(`devlog.md` Cycle-4 verdict `user_commentary`, "Owner review — Cycle 4" V-A–V-G)
plus standing findings carried from prior directions.

**Posture unchanged:** this line rebuilds fresh from prompt every cycle until the
owner says stop (owner ruling 2026-11-23). These are **named deficiencies of
version 0.3.0.004**: observed bars the next fresh realization is measured
against, and gaps the suite/criteria must be able to catch. They are not
instructions to patch `.004`.

## A. Owner review findings — Cycle 4 (2026-11-23)

| # | Deficiency in .004 | Bar for the fresh build |
|---|--------------------|--------------------------|
| V-A | **Persona art reads as procedurally drawn sprites** — bound portraits exist but look generated-by-template, not made | Persona visual identity produced by a generative/LLM art path, not procedural sprites. Mechanism is implementation choice; the owner's bar is that the art reads as authored imagery of that specific persona |
| V-B | **Header list looks like features but is deferred features** — the status/header enumerates absent capabilities in a way that reads as shipped | Deferred/absent capabilities are labeled as such, not presented in a form confusable with the feature list |
| V-C | **Workshop hard to interpret** — defined functions are opaque to an owner who didn't write them | Defined/exposed functions carry an inline explanation — name, purpose, what invoking it does — readable by the owner without corpus knowledge |
| V-D | **Roster reorder does not visibly update confidence** — dyadic `roster:rank` rows are written but no score change is observable | Reordering the roster produces a visible change in the ordering effect it is specified to have (dyadic held-confidence or whatever the ranking system binds it to) — the mechanism's consequence must be perceivable, not only recorded |
| V-E | **Diagnostic beeps help the wrong channel** — owner read them as user alerts; their purpose is instance-to-instance signaling | Machine-signaling tones stay machine-directed; user-directed alerts use a jingle/welcome-tone register, audibly distinct |
| V-F | **Personality editing is undiscoverable** — the editor exists (S-personality-editor enacted at 0.85) but the owner cannot find how to reach it | The path to edit an existing personality is discoverable from the surfaces where a personality is seen (roster/profile), not only through a tab the owner must already know |
| V-G | **Sample emails do not demonstrate real account reading** — S-email-commentary enacted on fixture `.eml` files; no configured real-account source exercised | Email commentary demonstrates against a configured account source, not only fixtures — or honestly declares the account source absent and the fixture basis is labeled as such |

## B. Standing requirements carried

| # | Item | Bar |
|---|------|-----|
| S-1 | Live owner-facing controls (G-A, direction-004) — a control that exists must work through the control itself; mechanism-only passes fail | Every owner-facing control exercised through its own path for enactment credit |
| S-2 | Voice as register constraint on truthful output (G-B bar, owner-approved 2026-11-23) — persona answers preserve factual content of their sources; unsupported claims flagged or withheld | S-faithful-voice with the lenient-check flags closed: zero-hit retrieval must not pass the grounding check; live replies must not carry `fidelity:null` unflagged |
| S-3 | Clean evidence (G-F carried) — no double-seeded rosters, populated fields, two adequate competing tools, scenario files carrying check results inline | Scenario evidence carries its checks inline; claimed fields are populated or the claim is dropped |
| S-4 | Launch hygiene (G4 carried) — port probed before bind, exclusive bind, no ok:true while a stale instance owns the port, close-terminates | `launch-check` legs all pass on the fresh build |
| S-5 | Dyadic confidence shape on record (G-C) — under the dyadic ranking system, new personalities start at **0.5** held-confidence by default | If a dyadic confidence model is built, the 0.5 default holds; the model itself was skippable in direction-004 — see direction-005 for this run's ruling |

## C. Standing honesty requirements (carried)

No `ok:true`-while-failing, no silent stubs, no env-dependent silent
degradation. Declared absences are recorded, not faked — and count against
completeness. A failed cycle is logged, not auto-retried.
