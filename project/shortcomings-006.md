# Named deficiencies — direction-006
<!-- harness-doc kind=shortcomings status=approved applies-to=cycle-6 mapped-into=scenarios.md,conventions-004.md -->

Compiled 2026-11-25 by the coordinator session from the owner's Cycle-5 review —
response-dynamics findings from live use of the staged `.005` instance
(`C:\builds-installed\quorum`) — plus standing findings carried from prior
directions.

**Posture unchanged:** this line rebuilds fresh from prompt every cycle until the
owner says stop (owner ruling 2026-11-23). These are **named deficiencies of
version 0.3.0.005**: observed bars the next fresh realization is measured
against, and gaps the suite/criteria must be able to catch. They are not
instructions to patch `.005`.

## A. Owner review findings — Cycle 5 (2026-11-25)

Observed fault: the owner addressed a personality **by name** in chat; the named
personality did not respond — the quick selector's single selection picked the
respondent instead.

| # | Deficiency in .005 | Bar for the fresh build |
|---|--------------------|--------------------------|
| R-D1 | **No response-depth setting** — nothing limits or sets how many responses a chat turn gets | Response depth is an accessible setting persisted as a user assertion (`chat:response-depth`, claimant `principal`, default 1 per GreyAvatar D17) — changeable through a settings surface and surviving relaunch |
| R-D2 | **Quick selector is single-select and always constrains** — no way to take it out of play | The selector is an **array of selectable buttons** (multi-select), showing only personalities over the confidence threshold — the previous GreyAvatar form; a dropdown is the wrong form. A default accessible **"chat all"** option means *selector not in play*: "hey chat" semantics — directed at the audience of personalities ranked by confidence, with response depth governing respondent count |
| R-D3 | **Named addressee usurped by the selector** — name-in-message produced no response from the addressee | Name-in-message and quick-selector selections are **equal-top-priority grants that union, not override** — all selected respondents reply. Reply order: directly addressed first, then selector-chosen |
| R-D4 | **No priority-vs-depth ordering** | Priority respondents (named + selector-chosen) always reply, **even beyond** the response-depth value. If priority count < depth, remaining slots fill from the roster in **confidence-rank order** — the roster's ordered state is by confidence regardless of how it is display-sorted |
| R-D5 | **Interest/project relevance ignored** | A persona whose interest or assigned project matches the conversation topic responds even beyond depth. Respondents matching **different keys** may each respond; respondents matching the **same key** respond only if they pass the confidence threshold — those that do not, do not. Matched respondents are given awareness of the related open needs and open projects that match |

Suite implications for direction-006: the respondent-selection contract needs a
named scenario (or amended S-chat-invocation) with checks that can catch
selector-usurpation, absent depth-fill, and interest-miss — enacted through the
owner-facing surfaces, per the S-1 live-controls bar.

### Fleet findings — same review session (live use, staged instance)

Verified against `.005` source: the invite/join/install buttons do call real
endpoints (`/api/fleet/*` → `H.fleet.*`), and `install()` makes an honest
reachability probe of the target admin share — but outcomes surface as raw
`alert(JSON.stringify(...))` and there is no target-side or inviter-side
user-mediated path. Network map produced successfully at
`version 0.3.0.005\runtime\network-map.json`.

| # | Deficiency in .005 | Bar for the fresh build |
|---|--------------------|--------------------------|
| R-F1 | **Discovery runs silently** — no indication the scan was working; results arrived without warning | A discovery run surfaces an in-progress state (per-transport progress where available) and a finished state on the owner-facing surface — the operator can tell scanning is underway before results land |
| R-F2 | **Fleet-action outcomes illegible** — invite/join/install/map results appear as raw JSON alert dialogs; no visible state change reads as "nothing happened" (S-1 violation in form if not mechanism) | Fleet controls produce perceivable UI state changes — member roster, statuses, transitions update on the surface — and report outcomes in user-legible form, not raw JSON |
| R-F3 | **No user-mediated path to install a target** — owner expected a popup on the remote machine or directions on the inviting app for how to add the target; the invite → join → role + credential-surrender → install-push chain dead-ends for a discovered device ("join pending — install requires a reachable peer endpoint") | The invite flow carries the operator through: a perceivable consent/install surface on the target where a peer exists or can be seeded, OR explicit inviter-side directions for completing the add (carry the seed media, open the peer surface, enter an invite key) — with the actual outcome honestly recorded. A discovered installable device that cannot yet join says why and what the operator does next — no dead ends |

### Conversational/list findings — same review session (live chat, staged instance)

Observed: "find a list of all mountains in missouri" and "make a list of all
mountains in japan" produced technically-correct replies (owner: "admirably
so") that opened with persona banter then **read as a page** — markdown
bullets, citation blocks, spoken punctuation; an unfulfilled `opened need`
was recorded but no list object was created; and every long reply was cut
off mid-sentence when spoken. Verified against source: `sapi_speak`
hard-slices text at `[:3000]` mid-token and kills the synth subprocess at
60s.

| # | Deficiency in .005 | Bar for the fresh build |
|---|--------------------|--------------------------|
| R-C1 | **Replies read as textbook entries** — markdown bullets, source citations, parentheticals; speech pronounces punctuation and markup verbatim ("(, Fuji-san)"); banter opening then page-read register break | Persona replies are **conversational sentences** in the persona's register throughout. The spoken rendering is derived for speech — markup, citations, and non-speech punctuation are rendered speakably or omitted, never vocalized verbatim |
| R-C2 | **"Make a list" produces prose, not a list** — an `opened need` was recorded but no formal list exists; nothing iterable was created | A list request creates a **formal formatted list as an assertion-ledger object** — iterable, inspectable, and usable as import to future processes (the S-list-project machinery: need → fulfilled entries). The conversational reply presents the list; it is not the list itself |
| R-C3 | **Speech truncates mid-sentence** — `sapi_speak` cuts text at 3000 chars mid-token and kills synthesis at 60s | Spoken replies complete at sentence boundaries — long text is split into sequential floor-held utterances (C-SpeechFloor preserves perceivability), or an excerpt is honestly declared as such. No silent mid-sentence cut |

### Persona-art finding — same review session

Observed: **no portrait art on personalities** in the shipped state — the V-A
bar was supposed to be improved this cycle; what the roster offers instead is
an `art` button. Verified against source and the Cycle-5 JEV: shipped personas
seed with `portrait: ""`; the extend-portrait need opens only for personas
minted through the API — nothing generates art for shipped personas. The art
path itself is real (LLM authors an SVG, declared fallback when unavailable)
and one minted persona's SVG exists in dev runtime — but S-portrait-bind
scored 0.7 with the judge noting shipped personas carry `portrait: ''` and
the enacted artifact lived in wiped `runtime-suite/`.

| # | Deficiency in .005 | Bar for the fresh build |
|---|--------------------|--------------------------|
| R-A1 | **Personas ship with no bound art** — shipped personas carry `portrait: ""`; art exists only behind a manual `art` button (and the mint-time need for API-minted personas). The V-A bar — authored art bound as visual identity — is unmet in the delivered state; the JEV caught it but scored 0.7 anyway | Every persona — shipped and minted — gets authored art generated and **bound automatically** (the generated-need mechanism fulfills it, not a button), displayed wherever the persona is shown. The `art` button may remain as a re-author affordance, never the primary path. Where the LLM art path is unavailable the declared-fallback still binds an image **and** its not-authored status is legible on the surface, not only in metadata |

### Account-credentialing finding — same review session

Verified against source: `configured_accounts = {"email": None,
"calendar": None}` is hardcoded — no settings surface, credential store, or
OAuth/app-password path exists for any external account. The honesty banner
declares "OAuth account connectors" absent and the `.eml` fixture basis is
labeled — the V-G fallback branch was taken honestly — but there is **no
path to configure** a Gmail/iCloud-class account at all (C-ConfiguredAccounts
unmet as capability).

| # | Deficiency in .005 | Bar for the fresh build |
|---|--------------------|--------------------------|
| R-E1 | **No credentialing exists for external accounts** — Gmail/iCloud-class accounts cannot be configured on any surface; `configured_accounts` is hardcoded `None` | An owner-facing account-credentialing path exists for external connectors (Gmail/iCloud class; OAuth or app-password/IMAP is implementation choice): a configured account becomes a configured-source row in the ledger — the descriptor recorded, the secret held per local-credential conventions (secrets never in ledger rows, logs, or courier media). Unconfigured remains an honestly-declared absence; fixture bases remain labeled. Once configured, the email-commentary path reads the real account |

### Publishing/AVQR findings — same review session

Verified against source: artifact exchange ships only the build-specific
`qmatrix-24` BMP codec — encode+decode is real, but the corpus **AVQR**
interchange (GreyAvatar `docs/voice-catalog-and-avqr.md`, `D29` registry,
`CODE_IMPORT_FORMAT`) is absent, honestly declared as "standard QR symbology
(qmatrix build-specific layer)". Export is a bare button writing a hardcoded
`exchange-package.json` behind a text prompt — no publication workflow
exists beyond the refusal path (S-defer-publication).

| # | Deficiency in .005 | Bar for the fresh build |
|---|--------------------|--------------------------|
| R-X1 | **AVQR interchange absent** — a bespoke symbology substitutes for the named interchange; a declared absence can't stand in for the format the exchange contract cites | A working scannable-code artifact interchange the operator can exercise end to end — generate → carry → scan/decode → import. **Owner ruling 2026-11-25: the formatting can change — there is no standard.** Symbology is implementation choice (qmatrix-class bespoke is acceptable *if* it round-trips as an exchange the operator can run); the bar is the demonstrated interchange, not Grey-registry byte-fidelity |
| R-X2 | **No publishing workflow** — no way to select holdings → choose exchange form/channel → produce or defer; external channels exist only as the refusal half of S-defer-publication | A publishing workflow on the owner-facing surface: select what to publish (persona, tool, package, workshop) → pick the form/channel (postcard, AVQR, file, email-class) → the artifact is produced and the exchange recorded — or, where a channel is unconfigured, the request is deferred with request + status recorded (S-defer-publication's other half), never silently absent |

### Distributed-networking finding — same review session

Verified against source and the Cycle-5 verdict: the fleet work is invite/
join bookkeeping + an admin-share reachability probe — discovery and the
network map are real, but **no two nodes ever exchanged**. No peer ledger
delta, no rejoin correlation (promoted steering `decision-candidates-001` §3),
no courier-log sync observed by a second live node, no second install on the
LAN. The JEV scored fleet discovery 0.8 / install 0.7 on honest-status
evidence — per-device status was honest, but "not demonstrated" is not a
status class.

| # | Deficiency in .005 | Bar for the fresh build |
|---|--------------------|--------------------------|
| R-N1 | **No distributed networking demonstrated** — one node bookkeeping about devices it never actually talked to | A demonstrated distributed exchange: two or more real nodes on the LAN perform a real sync — peer ledger delta exchange, rejoin correlation, courier log — with run evidence from both sides. The staged install on a second host (or the seed-run node) counts; a same-host instance does not. Where hardware state blocks a device, honest per-device status stands — but the capability itself must be demonstrated somewhere, not merely designed |

### Persona-ranking + needs-floor findings — same review session

Verified against `.005` source:

- `move()` computes new held-confidence as the **midpoint of the new
  neighbors** — with all personas at the uniform 0.5 default, a mid-roster
  reorder yields (0.5+0.5)/2 = **0.5: literally no change**; only a move to
  an end shifts ±0.1. The V-D carry is still unmet.
- "I want a taco" was classified `need:list` (and spawned a stray
  `list:t-*` row as a second open need — another need, not entries);
  "Nix, tell me about yourself" (name-addressed ask — should route to the
  addressee per R-D3) and "hello, what can you do?" (capability question)
  both parked as `need:request` unmet. `need:request` fires whenever the
  lexicon says 'request' with no class match — the catch-all is eating
  routable intents.
- Steward chit: `passes`/`ageS` observed **resetting** in live use; the
  liveness chit misreports.

| # | Deficiency in .005 | Bar for the fresh build |
|---|--------------------|--------------------------|
| R-P1 | **Personality ranking does not move dyadically** — uniform 0.5 values mean interior reorders produce exactly 0.5; the order changes but the ordering's effect doesn't | Every reorder produces a perceivable dyadic consequence on every move — the dyadic model differentiates on each reorder (held-confidence or whatever the ordering binds to), and the movement is visible on the surface, not only when neighbors already differ |
| R-U1 | **Need classification routes intents wrong** — "I want a taco" opened a list need (+ stray `list:t-*` row); name-addressed asks and capability questions park as `need:request` unmet instead of reaching a respondent or answer | The classification step routes each distinguishable intent to its fulfillment path: name-addressed asks reach the addressee (R-D3), capability/help questions get answered, real list requests open list machinery, and only genuinely unmet asks land on the floor — "I want X" is not a list |
| R-U2 | **Needs never get met or leave the list** — "I want a taco" never got a response; the floor accumulates opens without draining to fulfillment | Needs that get met are marked fulfilled and **leave the open list** — met vs unmet state is visible; a need answered is a need closed, not a permanent resident |
| R-U3 | **Steward counter keeps resetting** — the liveness chit's count/age restarts in live use | The liveness chit accumulates monotonically — passes count up and age reflects real time since last pass; a resetting counter misreports liveness (§4 display contract) |

## B. Standing requirements carried

| # | Item | Bar |
|---|------|-----|
| S-1 | Live owner-facing controls — a control that exists must work through the control itself | Every owner-facing control exercised through its own path for enactment credit |
| S-2 | Voice as register constraint on truthful output — persona answers preserve factual content of their sources; unsupported claims flagged or withheld | Zero-hit retrieval must not pass the grounding check; live replies must not carry `fidelity:null` unflagged |
| S-3 | Clean evidence — populated fields, checks inline in scenario evidence | Scenario evidence carries its checks inline; claimed fields are populated or the claim is dropped |
| S-4 | Launch hygiene — port probed before bind, exclusive bind, no ok:true while a stale instance owns the port, close-terminates | `launch-check` legs all pass on the fresh build |
| S-5 | Dyadic confidence shape on record — new personalities start at **0.5** held-confidence by default | If a dyadic confidence model is built, the 0.5 default holds |

## C. Standing honesty requirements (carried)

No `ok:true`-while-failing, no silent stubs, no env-dependent silent
degradation. Declared absences are recorded, not faked — and count against
completeness. A failed cycle is logged, not auto-retried.
