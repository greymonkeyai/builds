# Scenario checks — suite coverage specification (2026-11-25)
<!-- harness-doc kind=suite status=superseded mapped-into=scenarios.md -->

**SUPERSEDED 2026-11-25** — check specs merged into `scenarios.md` (Forms column +
Checks section; delta tiers removed). Kept as the record of the pre-run audit
mapping.

Check specification for the pre-run audit before direction-006. Every named
scenario in `scenarios.md` (60) maps to named checks the build must implement
and enact **through the path a user takes** — owner-facing surfaces, natural
chat, real devices (C-UserPathEnactment). Mechanism-only evidence is
repository-class at best. Results are carried inline in
`evidence/scenarios/S-*.json` (`checks[].name / pass / detail`) as `.005` did.

Status marks: **[new]** — defined here first; the build creates them.
**[amended]** — bar tightened 2026-11-25; listed additions required on top of
the carried checks. **[carried]** — checks existed in `.005` evidence; the
fresh build re-implements against the same contract.

## New scenarios (16) — checks defined here

### S-respondent-union  [new]
Path: chat input naming a persona while a different persona is selector-chosen,
through the owner-facing selector + chat.
- `named addressee replies` — the persona addressed by name responds
- `selector-chosen replies` — the selector-chosen persona(s) respond
- `union not override` — both reply; neither usurps the other
- `addressed first` — reply order: directly addressed, then selector-chosen
- `multi-select` — selector accepts multiple personas, all chosen reply
- `over-threshold only` — selector offers only personas over the confidence
  threshold

### S-response-depth  [new]
Path: owner-facing settings surface + chat.
- `depth setting exists` — accessible control for responses-per-turn
- `user assertion` — recorded as `chat:response-depth` (claimant principal)
- `persists` — value survives relaunch
- `chat all` — selector has an accessible out-of-play option relying on depth
- `priority exempt` — named + selector-chosen reply even beyond depth
- `depth fills` — priority count < depth → roster fills in confidence-rank
  order

### S-interest-respondents  [new]
Path: chat on a topic matching a persona's declared interest/assigned project.
- `interest match responds` — matching persona replies even beyond depth
- `different keys` — respondents matching different keys may each respond
- `same key gated` — same-key respondents pass the confidence threshold or
  don't respond
- `awareness carried` — matched respondent receives related open needs and
  open projects matching the topic

### S-discovery-progress  [new]
Path: owner-facing discovery control.
- `in-progress shown` — scanning state visible while discovery runs
- `transport progress` — per-transport progress where available
- `finished shown` — completion state distinguishable from idle

### S-fleet-action-legible  [new]
Path: every fleet control through its own UI path.
- `invite legible` — invite produces visible state change + legible outcome
- `join legible` — join produces visible member/status transition
- `install legible` — install produces visible outcome (no raw JSON anywhere)
- `map legible` — map action reports where the artifact landed

### S-fleet-install-path  [new]
Path: invite → join → role + credential surrender → install, operator-driven.
- `no dead end` — every step says why it can't proceed or what happens next
- `target surface OR directions` — consent/install surface on target where a
  peer can exist, or explicit inviter-side directions
- `honest outcome` — actual result recorded (reachable, refused, pending)
- `pending stated` — a device that can't join yet reports the blocker

### S-fleet-exchange  [new]
Path: two real LAN nodes (staged install or seed node on second host).
- `second real node` — a node on another host participates (not same-host)
- `delta exchange` — peer ledger rows flow and are applied
- `rejoin correlation` — rejoining peer correlates, no re-init
- `courier sync` — courier log accumulates across nodes
- `both sides evidenced` — run artifacts from each node

### S-conversational-register  [new]
Path: live chat replies + spoken output.
- `sentences` — replies are conversational sentences in-register throughout
- `no textbook` — no bullet dumps, citation blocks, markdown tables in reply
- `no verbatim markup` — spoken output never vocalizes punctuation/markup
- `register unbroken` — banter register sustained, not page-read

### S-speech-completion  [new]
Path: spoken reply longer than one utterance.
- `sentence boundary` — speech stops at a sentence boundary, never mid-token
- `sequential utterances` — long text splits into floor-held sequential
  utterances
- `or declared excerpt` — an excerpt is honestly labeled as such
- `no silent cut` — no truncation without declaration

### S-account-configure  [new]
Path: owner-facing account settings surface.
- `credential path exists` — Gmail/iCloud-class account configurable
- `descriptor row` — configured account recorded as configured-source row
- `secret hygiene` — secret never in ledger rows, logs, or exchange media
- `real read` — once configured, email list/commentary reads the account
- `unconfigured honest` — absent config still honestly declared

### S-publish-workflow  [new]
Path: owner-facing publish action on a holding.
- `select + form` — choose holding and exchange form/channel
- `produced + recorded` — artifact produced, exchange recorded as assertion
- `or deferred` — unconfigured channel defers with request + status recorded
- `no silent absence` — a missing channel is declared, not invisible

### S-scancode-interchange  [new]
Path: operator runs the full artifact round-trip.
- `generate` — scannable code produced from a holding/workshop
- `carry` — artifact transferable (file/media the operator can move)
- `decode` — scan/decode path readable by the operator
- `import` — decoded artifact imports on an instance

### S-dyadic-ranking  [new]
Path: roster reorder through the owner-facing control.
- `every move visible` — each reorder produces a visible held-confidence (or
  bound-value) change, incl. moves between equal-valued neighbors
- `interior moves` — mid-roster reorders differentiate, not only edge moves
- `surface shows it` — the score change is perceivable on the roster, not
  only in ledger rows

### S-intent-routing  [new]
Path: natural chat inputs of each intent class.
- `name-addressed → addressee` — "Nix, tell me about yourself" reaches Nix
- `capability → answered` — "what can you do?" gets an answer, not a need
- `want ≠ list` — "I want a taco" does not open a list need
- `list → list machinery` — real list requests open the list path
- `genuine unmet → floor` — only unmatched asks land as need:request
- `no stray rows` — no derived needs spawned as extra open rows

### S-need-fulfillment  [new]
Path: need floor + a turn that meets a need.
- `met marked` — fulfilled needs marked fulfilled
- `met leaves floor` — fulfilled needs leave the open list
- `answered = closed` — a need answered by a turn closes, doesn't persist
- `unmet visible` — only genuinely unmet needs remain listed

### S-steward-liveness  [new]
Path: observe the first-screen chit across passes and user activity.
- `monotonic passes` — pass count only increases
- `real age` — age = real time since last pass, not a resetting count
- `no reset` — user activity, idle cycles, relaunch don't silently reset

## Amended scenarios (6) — additions on top of carried checks

### S-list-project  [amended]
Carried: `list need created from chat ; retrieval produced members ;
non-matches recorded for review (D4) ; criteria preserved in need rows`.
Add:
- `chat path enactment` — a natural-language "make a list" chat request
  creates the list (R-C2)
- `iterable object` — a formal list exists in the ledger — iterable,
  inspectable, importable to future processes (C-FormalList)

### S-portrait-bind  [amended]
Carried: `portrait file produced ; art bound to this persona ; generative
path declared`.
Add:
- `auto-bound shipped` — every shipped persona carries bound art without a
  manual step (R-A1)
- `auto-bound minted` — minted personas bind art via need fulfillment
- `fallback legible` — declared-fallback art binds + not-authored status
  visible on surface

### S-email-commentary  [amended]
Carried: `email list from configured source basis ; V-G: fixture basis
honestly labeled ; persona commentary produced ; commentary recorded`.
Add:
- `configured source exercised` — demonstrates against a configured account
  where S-account-configure is enacted (R-E1/V-G)

### S-personality-roster  [amended]
Carried: `roster operable ; selection works ; reorder changes order ; V-D:
reorder visibly changes held-confidence`.
Add:
- `every move moves` — dyadic change on every reorder (S-dyadic-ranking)

### S-chat-invocation  [amended]
Carried: `conversational reply returned ; tool need(s) opened,
distinguishable ; input captured as assertion`.
Add:
- `needs route` — distinguishable needs route to fulfillment paths
  (S-intent-routing), not parked unhandled

### S-fleet-invite  [amended]
Carried: `discovery lists candidates ; user selects which join ; non-invited
devices are NOT members`.
Add:
- `continues to path` — invite continues into the guided join/install path
  (S-fleet-install-path)
- `legible outcome` — invite outcome reported legibly (S-fleet-action-legible)

### S-defer-publication  [amended]
Carried: `unconfigured nonlocal effect refused/deferred ; request + status
recorded as assertions`.
Add:
- `production half` — a configured/producible channel produces the artifact
  (S-publish-workflow)

## Carried scenarios (38) — checks as enacted in `.005` evidence

| Scenario | Checks (names as evidenced) |
|----------|------------------------------|
| S-artifact-import | capture → workshop entry created ; below action/acceptance threshold ; entry accessible in the app |
| S-artifact-republish | adopted workshop re-encoded to new artifact ; gen-2 payload decodes identically |
| S-artifact-style | stylistic extraction layer present ; art style captured as LLM reference ; carried on the workshop entry |
| S-assertion-input | typed input recorded as assertion ; source-aware claimant ; typed value ; basis = captured-input |
| S-background-present | steward pass recorded ; liveness data for first-screen chit ; persona presented while idle work continues |
| S-candidate-ranking | candidates retained w/ source+confidence ; supersession rows retained ; invocation produced result |
| S-close-terminate | close-terminates (launch-check leg 4) |
| S-color-schemes | ≥3 colorways implemented incl. dark ; theme selector drives settings claims ; fresh launch opens light (seeded) |
| S-competing-tools | two competing tools ran the same need ; both legs produced interpretable results ; results comparable (member counts) ; comparison recorded |
| S-context-display | active context displayed |
| S-conversation-reset | reset clears conversation ; topic cleared |
| S-credential-surrender | surrender recorded as a claim ; host holds the credential screen (§5) ; secrets stay host-local — needs travel, secrets never do |
| S-distinct-preloadeds | ≥3 shipped personas w/ distinct registers ; same prompt → noticeably different replies |
| S-dubious-source | artifact claims held below trust ceiling ; encoded references resolved against vetted pointers ; non-matching claims recorded for review |
| S-exchange-import | package exported then imported ; contents below action threshold ; foreign tools staged as candidates, not live |
| S-faithful-voice | grounded reply flagged grounded ; zero-hit does NOT pass grounding (S-2) ; no unflagged fidelity:null |
| S-fleet-roster | every named-roster device reported ; honest status per device ; coverage is test data — non-targets recorded |
| S-focused-need | unmet need moved into focus ; value supplied conversationally fills a slot ; need remains until requirement met |
| S-library-browse | personas browsable ; tools browsable w/ explanations ; holdings structured, not a raw log |
| S-local-transports | wired LAN baseline exercised ; ≥1 additional local transport (BT/NFC/SoftAP) ; wired preferred ordering honored |
| S-network-map | map artifact produced ; covers non-member devices alongside members ; member/non-member distinction on the map |
| S-personality-create | persona minted from minimal input ; portrait generated + bound ; LLM art path (V-A) ; voice assigned ; characterization extended ; dyadic default 0.5 (S-5) |
| S-personality-editor | editor path updates persona elements ; edits recorded as assertions ; V-F: edit discoverable from roster surface |
| S-preload-cache | vetted-source pointers seeded ; device decoder entries present ; marketing exemplar present + decodable |
| S-restart-recovery | state recovered after restart ; provenance retained (superseded rows kept) ; cleanup consolidates without losing records |
| S-role-negotiate | role negotiation recorded ; mint rights are a negotiated grant ; join outcome honest (member vs pending) |
| S-speech-serialization | speech serialized through the floor ; playback measured not assumed ; held until playback complete |
| S-status-bar | sources surfaced ; LLM status surfaced ; engine modes declared honestly |
| S-template-need | need row created from chat input ; template-governed (slots+criteria) ; opens unfulfilled |
| S-tool-transmission | literal decode fidelity (C-ToolWireFidelity) ; imported tool quarantined as candidate ; not invocable before acceptance |
| S-usb-log-courier | courier log accumulates across runs ; machine-readable per-node evidence ; stale-seed revisit handling recorded |
| S-usb-mint-gen2 | gen-2 installer written to media ; carries founding network identity as adoptable offer ; join-or-found is the user's choice |
| S-usb-seed-run | app launched executing from removable media ; runs in place — no install required ; local network log written ON the medium |
| S-usb-stage-consent | decline → no local write, app stays on media ; consent → stages to C:\builds-installed |
| S-voice-select | voice choices list offered ; user assigns a persona's voice from the list |
| S-voice-spec | spec is QR-fittable (minimal payload) ; ranked families and/or traits carried ; local engine mapping renders nearest voice |
| S-windows-launch | launches on Windows like an installed program |

## Coverage summary

- 60 named scenarios; 60 check specs mapped: 16 new, 7 amended, 37 carried.
- Amended: S-list-project, S-portrait-bind, S-email-commentary,
  S-personality-roster, S-chat-invocation, S-fleet-invite, S-defer-publication.
- Every `shortcomings-006.md` finding (R-D1–R-U3) maps to ≥1 scenario +
  ≥1 named check; convention candidates in `conventions-004.md`.
