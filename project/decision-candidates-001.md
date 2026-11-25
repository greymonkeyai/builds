# Decision candidates — forward-convention proposals (2026-11-25)

Five decision candidates for future build lines. **Approved 2026-11-25** (owner) —
same posture as `conventions-002.md` / `conventions-003.md`; corpus adoption assigns
corpus identifiers at review.

**Provenance.** Drafted as GreyAvatar `docs/decisions/` D179–D183 (`e0b21a7`…`4813923`);
relocated to this corpus 2026-11-25 (GreyAvatar copies removed `5e0fb08`). All
GreyAvatar citations below — D-numbers in "Builds on", `src/` paths, predicate names,
`GREY_*` env vars — are **evidence citations of the reference realization**, not spec
vocabulary.

Dependency order: 1 (candidate machinery) → 2 (the `need:request` drain consumes it) →
3 (peer topology) → 5 (host role attaches to 3). Section 4's display contract gates
section 2's `need:request` — a new `need:*` predicate that isn't counted and projected
drains invisibly.

---

## 1 — Tool candidates: provenance-carrying acceptance mint + LLM evaluator + endorse/discredit meta-assertions

**Provenance:** GreyAvatar `docs/decisions/D179` (commit `e0b21a7`).
**Status:** Candidate · **Date:** 2026-11-25
**Builds on:** D8 (import confidence inheritance), D17 (tool template), D20 (editor proficiency tiers), D29 (AVQR registry), D65 (inference-as-source), D83 (code import, quarantined elements), D128 (need → workshop hammer), D130 (set-import-trust; delivers the deferred meta-assertion non-goal).

### Context

Tool authorship is power-law: a small fraction of installs produce most tools; most installs *consume* them via exchange (code-import, AVQR, postcard bundles). A consuming install needs a mechanism of trust for evaluating what arrives — without the user reading `ToolStep` JSON. Distributed local LLMs (D65 `ollama_endpoint`, fleet role topology D105) invert the earlier "full development workshop" direction: instead of teaching every user to author logic, each install's model becomes its trust department — rendering candidates legible in the owner's language.

Today `tool.mint` is the only path into the live catalog, and it unconditionally (a) registers the definition into the live registry and (b) stamps `claimant: "principal"`, `certainty: 1` on `tool:exists`/`tool:definition`. That is honest for a principal-authored workshop save, but wrong for a definition that arrived via import or was drafted by a model: provenance is erased, and a foreign artifact becomes live with no acceptance act.

D130 retired `endorse` naming but explicitly deferred *claim-level meta-assertions* ("future endorse/discredit"). This decision delivers that seam for tool definitions: endorsements are assertions about a tool subject that travel inside exchange bundles and inherit confidence exactly like any other source claim (D8).

### Options

- **A — Candidate lane + acceptance mint (chosen).** Candidates stage as `tool:candidate` rows attributed to their origin claimant and never enter the live registry. `tool.mint` becomes the acceptance act: it mints live against the candidate, preserving origin provenance in `basis.meta`. Foreign/model artifacts are never live-by-default.
- **B — `provenance` field on tool.mint, still installs live immediately.** Simpler, but keeps foreign artifacts live before review; the trust gate becomes advisory text rather than a gate.
- **C — Author-side pipeline first (LLM drafts tools).** Rejected as the lead: under power-law authorship the consumer-side evaluator covers more real volume. Drafting rides the same candidate seam afterward (item 6).

### Decision

1. **`tool:candidate` predicate.** A candidate row carries the serialized `ToolDefinition` plus `basis.meta.origin` — `{ kind: "import" | "model" | "author", sourceKey?, modelId?, via? }`. Non-principal origins claim as `source:<id>` or `model:<id>` at certainty capped by D8 inherited confidence. Candidates are never registered; `loadMintedTools` and the live registry are unaffected. Rejection/supersession is a new row; the candidate remains for forensics.
2. **Acceptance is the mint act.** `tool.mint` gains an optional `acceptedFrom` input naming the candidate row id. Mint rows keep `claimant: "principal"` — the acceptance *is* the principal's claim — while `basis.meta` carries `{ acceptedFrom, origin }` so provenance survives into the durable catalog row. Direct `tool.mint` without `acceptedFrom` remains valid (workshop save = self-authored).
3. **`evaluate-tool-candidate` tool** — declarative `logic` only, no coded function. Steps: `ledger.search` the candidate + `source:trust-class`/`source:confidence` + `tool:endorse`/`tool:discredit` rows → `engine.invoke` (`llm`, `complete`) with an assembled prompt (candidate definition + trust context) → result card rendering the plain-language summary plus mechanical flags extracted without the model (invoked components, `requiresGrant`, template surface). Engine offline → honest stub card; no fabricated verdict.
4. **`tool:endorse` / `tool:discredit` predicates** — claim-level meta-assertions about a `tool:definition`/`tool:candidate` subject, authored by principals or persona claimants. Exported inside exchange bundles so endorsements travel with the artifact and inherit confidence per the D8 source model: an endorsement from a source you don't trust arrives at 0.25; reputation is the same trust model applied to claims-about-claims. No central registry.
5. **Risk-tiered acceptance is policy, not mechanism.** Candidates with no `requiresGrant` resolve through a single accept card; grant-requiring candidates route the consent question through the existing witnessed-grant flow. Delegation ("auto-accept from trusted sources, no grants") is a `source:*` trust assertion a steward could honor — deferred, not built here.
6. **Author-side drafting rides this seam later.** A `draft-tool` (LLM authors a definition → lands as `tool:candidate` under `model:<id>` → the same evaluate/accept path) requires nothing beyond items 1–4. Not built in this decision.

### Non-goals

- Cryptographic install signing (install identity is version+sha per D170; channel provenance suffices for directed exchange — revisit for open broadcast).
- Auto-accept / delegation (item 5 marks it deferred).
- Any change to the frozen primitive set — `engine.invoke` already exists.
- A central tool registry or global reputation score.

### Predicates registered (D7)

`tool:candidate`, `tool:endorse`, `tool:discredit` (tool namespace).

### Ideal it protects

Channel honesty under exchange: provenance is never erased by acceptance; foreign artifacts are never live-by-default; trust is local, computed from the ledger's own source model; the consuming majority reviews candidates in its own language via its own model.

### Drift check

Kernel unchanged. Ledger stays the only truth — candidates and endorsements are rows; the live registry is still populated only by `tool.mint`. Append-only — acceptance/rejection are new rows. Outbound stays grant-gated (unchanged). No new primitive, segment, or namespace — three predicates register under D7 governance. Reuse map: scanned tray + quarantined element import (D83), import-trust classes + `set-import-trust` (D8/D130), `engine.invoke` + the `llm.compose_via_source` grant path (D65), `parseToolDefinition` closed-world validation (the candidate's first structural check).

### Status log

| Date | Status | Note |
|------|--------|------|
| 2026-11-25 | Candidate | Drafted from the distributed-LLM / exchange-trust design discussion; evaluator-first under power-law authorship. |
| 2026-11-25 | Candidate | Relocated from GreyAvatar `docs/decisions/` to this corpus. |

---

## 2 — JEV turn lane: gate → classify → evaluate, and the `need:request` capture

**Provenance:** GreyAvatar `docs/decisions/D180` (commits `da7f3b8`, `f5a2ce8`, `cbb2fe8`).
**Status:** Candidate · **Date:** 2026-11-25
**Builds on:** D4 (LLM sidecar ladder), D65 (inference-as-source), D73 (chat-turn orchestration as tools), D81 (need lifecycle), D101/D100 (steward priority + dispatch backoff), D157/D161/D178 (engine placement), candidate 1 above (tool candidates + endorse/discredit), DI-9 (`need:tool-request` floor).

### Context

The chat pipeline today is a deterministic lexicon parse → segment → classify (`src/chat-parse/`) with conversational fallthrough. The engine layer offers exactly one general model seam: `engine.invoke` → `llm.complete(prompt)` (+ `describeImage`). Every LLM consumer calls the same untyped completion — we are *not* yet building a diverse set of LLM capability, though the substrate for it exists (per-call `LlmOptions.model`, `resolveOllamaModel`/`pickOllamaModel`, placement telemetry).

The owner direction: a JEV-type model lane applied to the prompt→response process at three separated points —

- **Gate:** did the user make a request?
- **Classify:** what request was made?
- **Evaluate:** how well was the request fulfilled?

Separation of evaluation from execution is the explicit best practice. The lane also captures a data type the project has repeatedly lost: the **unmet request** — the gate says the user asked for something, but no classifier/tool matched, so the ask falls through to conversation and evaporates. Fulfilling unmet requests through trusted sources is the project's stated holy grail; candidate 1 built the trust machinery (candidates, endorsements) that consumes this capture.

### Options

- **A — LLM roles + dual-run lane + `need:request` rows (chosen).** Both classifiers run on every turn — the regime is async, so the model's late-arriving verdict is not inert telemetry: on disagreement it opens evidence and need rows and may issue a correction card; it just never blocks the turn or mutates the reply already sent. Evaluation lands as ledger rows after fulfillment.
- **B — Model-gate first, lexicon as fallback.** Rejected for now: gating on the model before any response would reintroduce a blocking dependency the async regime makes unnecessary, makes first routing nondeterministic (bad for replay/debug), and bets on a small local model with no track record here. Promotable *per intent class* later, when `eval:fulfillment` data shows the model beating the lexicon on that class.
- **C — Miss-only lane (model observes only lexicon failures).** Cheaper, but blind: the model never sees the common path, so there is no counterfactual corpus ("lexicon said X, model thought Y") and no evidence base for B. Available per-host as `GREY_JEV_MODE=miss-only` on compute-starved installs.
- **D — Replace deterministic classify with the model.** Rejected: the lexicon classifier is free, instant, and proven; replacement also makes every turn hostage to engine health.

### Decision

1. **LLM roles diversify the seam, not providers.** `engine.invoke` (`llm`, `complete`) gains an optional `args.role` ∈ `{gate, classify, evaluate, draft, general}`. Role → model tag resolves via the existing `resolveOllamaModel`/`pickOllamaModel` machinery with env pins (`GREY_LLM_MODEL_<ROLE>`); unset roles collapse to the default tag. Cheap small models can hold `gate`/`classify` while a heavier tag holds `evaluate`/`draft`; on constrained hosts all roles share one model. Placement telemetry already reports where the call ran.
2. **Both classifiers run on every turn — the model asynchronously, and its verdict acts.** `gate-turn` is declarative tool-data: `engine.invoke` (`llm`, `complete`, `role: "gate"`) over the user message → `{isRequest, confidence, rationale}`, written as a `chat:gate` row claimed by `model:<id>` at bounded certainty. The lexicon answers first; the model's verdict lands whenever the engine returns it — there is no hot path to protect in this regime. On disagreement the verdict is not passive: it opens `chat:gate` evidence rows ("lexicon said X, gate said request"), may write `need:request` (item 3), or surface an async correction card on the next surface beat. It never blocks the turn and never mutates the reply already sent — corrections are new rows, append-only as always. Engine offline → stub row, lane inert, turn unaffected. `GREY_JEV_MODE=miss-only` drops coverage to lexicon failures for compute-starved hosts.
3. **`need:request` — the unmet-request row.** When the gate (or lexicon hedge evidence) says *request* and no classifier or tool match exists, the turn writes `need:request` carrying the verbatim ask, gate evidence, and any slot guesses. Distinct from `need:tool-request` (an open call to a *known* tool): `need:request` is *asked, nothing matched*. It enters the standard need floor: ITS steward drains by reclassify → trusted-source search → `tool:candidate` path (candidate 1) → ask-the-user card, with D100 backoff applying.
4. **Evaluation is a separate stage with its own claimant.** After a need fulfills (`need.fulfill` supersession) or a conversational reply lands, `eval:fulfillment` rows — authored by `model:<id>` via `role: "evaluate"` — score the outcome `{met | partial | unmet}` against the originating request. Eval rows are ordinary assertions: read-time trust decides their weight, they feed need-priority/backoff, and a confident positive/negative verdict may mint `tool:endorse`/`tool:discredit` (candidate 1) — the trust flywheel the whole lane exists to feed.
5. **`need:request` fulfillment is the holy-grail loop.** An unmet request that later gains a tool — authored, exchanged, or model-drafted — resolves through the same `tool:candidate` acceptance mint; the request row is superseded by its fulfillment, keeping the full arc (ask → gap → tool → fulfillment → eval) replayable from the ledger alone.

### Non-goals

- Replacing or demoting the deterministic classifier.
- Synchronous model calls inside the hot turn path (the lane is parallel; eval is post-fulfillment/idle).
- Cloud judges — every role resolves through the local/LAN engine ladder.
- Auto-fulfilling unmet requests without the witnessed-grant/consent flow where effects require it.
- Model-drafted tools — rides the candidate-1 item 6 seam, not built here.

### Predicates registered (D7)

`chat:gate` (chat namespace), `need:request` (need namespace), `eval:fulfillment` (eval namespace).

### Ideal it protects

No ask is silently lost: a request the system cannot serve becomes a durable, drainable, attributable row rather than conversational fallout; judgment is attributed to `model:<id>` at bounded certainty and never impersonates the principal; the turn stays deterministic-first and offline-honest.

### Drift check

Kernel unchanged. One new optional arg on an existing primitive method (`engine.invoke` → `llm.complete`); no new primitive, segment, or kind. All capture lands as ledger rows under D7 namespaces. Deterministic classify stays primary; the need floor, supersession, backoff, and candidate-1 machinery are all reused, not duplicated. Reuse map: `engine.invoke` + `resolveOllamaModel` (engine placement D157/D161), `need:*` lifecycle + drainNeeds + D100 backoff (D81/D100/D101), `chat:*`/`routing:trace-*` turn rows (D73), source-trust inheritance + tool candidates (D8/D65 + candidate 1).

### Status log

| Date | Status | Note |
|------|--------|------|
| 2026-11-25 | Candidate | Drafted from the multi-device / JEV design discussion; evaluator-first continuation of candidate 1. |
| 2026-11-25 | Candidate | Amended — dual-run lane: model verdict acts asynchronously (disagreement opens evidence/need rows, never blocks the turn); JEV lane runs shadow-mode on every turn, promotable per intent class. |
| 2026-11-25 | Candidate | Relocated from GreyAvatar `docs/decisions/` to this corpus. |

---

## 3 — Sovereign hub ledgers: peer rejoin correlation, intentional severance, fleet load sharing

**Provenance:** GreyAvatar `docs/decisions/D181` (commit `da7f3b8`).
**Status:** Candidate · **Date:** 2026-11-25
**Builds on:** D8 (import confidence inheritance), D65 (inference-as-source), D81 (need lifecycle), D104/D105 (pairing + fleet role topology — **partially amends**), D152 (LAN token gate), D157/D161/D178 (engine placement + cross-host Comfy), D169 (application/interface/service — **partially amends**), D170 (install identity).

### Context

D105/D169 ratified a **single ledger authority** (GMK): YOGA is a thin input peripheral, mirrors render frames, and RMT hosts run local ledgers with `GREY_LAN=0` and no exchange. The owner direction now moves to a **multi-device regime**: any host computer continues to function as a hub when disconnected, and rejoins when devices reconnect. Each device holds its own assertion ledger; drift is admitted and expected. On rejoin, outage-era data is *correlated* between peers. A peer that was **intentionally severed** is not silently re-merged — it is offered the possibility of new ownership and a split.

The append-only, claimant-attributed ledger is structurally suited to this: foreign claims already arrive through the D8 source model at inherited confidence; truth is computed at read time, so merging books is a union of rows plus recomputed views — no consensus protocol, no last-writer-wins.

### Options

- **A — Sovereign hubs + peers-as-sources + severance claims (chosen).** Every host is a full hub; a paired peer registers as a `source:peer` configured source; rejoin exchanges row deltas both ways; severance and split are principal-authored claims. No new kernel machinery.
- **B — Single authority kept; satellites buffer-and-forward to the hub.** Preserves D105 but fails the stated requirement: a satellite is dead weight when the hub is unreachable, and "any host is a hub" is the point.
- **C — CRDT/live replication.** Continuous merge machinery duplicates what the ledger already does at read time, adds a second truth channel, and breaks the offline-first posture (a CRDT wants connectivity; a ledger wants none).

### Decision

1. **Every host is a sovereign hub.** The full kernel + ledger + engine stack runs offline per install (the RMT pattern of D105 item 3 becomes the default posture, not the exception). Engines degrade local→stub honestly per the honesty-banner contract. A peer's ledger is the authority *for that install*; cross-host truth is a computed view, never a consolidated store.
2. **A paired peer is a configured source.** `source:peer` descriptor rows (D8 source model) carry the peer's install identity (D170 version+sha), endpoint, and pairing state; pairing rides the existing :9847/:9848 token-gated seam (D104/D152), extended by a ledger exchange route. Peer-sourced rows import at inherited confidence exactly like connector or bundle imports — reputation stays local and ledger-computed.
3. **Rejoin correlation is append-only delta exchange.** Each ledger keeps a durable high-water mark (row sequence). On rejoin, peers exchange rows-after-mark in both directions and *union* them: outage-era rows arrive as peer-claimed assertions; supersession and trust resolve conflicts at read time identically to same-host drift. "Correlation" is this exchange pass — it never rewrites, never requires agreement.
4. **Intentional severance is a claim, and a split is an offer.** `peer:sever` is a principal-authored claim suspending import from a peer. On later contact the host does not silently re-merge; it presents the fork: (a) **rejoin** — resume delta exchange, severance-era rows import at peer-source confidence; or (b) **new ownership** — the returning install re-anchors: its severance-era principal claims re-bind to a new principal/persona identity (D122 self-bind pattern), and the two books continue divergently by consent. The split is itself recorded as a claim on both sides — append-only is preserved, and either party can later read *why* the books diverged.
5. **Fleet load sharing rides the need floor — later.** `need:tool-request` rows are already durable and floor-visible; a peer steward may claim open needs fleet-wide, fulfill them on whichever host has the capacity (Comfy on RMT already works by endpoint per D178), and land results as peer-sourced assertions. Long-duration, media-max workloads (portrait batches D88/D160, document composition D133) gain a `dispatch: "fleet"` marking; first fulfillment supersedes and duplicates degrade to extra choice cards. Interactive/latency-bound work stays local. Built after items 1–4 land.

### Non-goals

- Real-time mesh replication, CRDTs, or consensus of any kind.
- WAN/internet peering — the seam is the existing LAN pairing.
- Cryptographic identity beyond install version+sha (revisit if peering ever goes undirected).
- Automatic conflict adjudication beyond the existing trust/supersession model.
- Migrating GMK off its current hub role — sovereignty is additive; the fleet works the same when all peers are up.

### Predicates registered (D7)

`source:peer` (source namespace), `peer:sever`, `peer:rejoin` (peer namespace).

### Ideal it protects

Local memory, personified trust, at fleet scale: no host is a client of another's truth; disconnection is survivable and reconnection is honest — drift is correlated, not erased; an intentional sever can become a clean, consented split rather than silent corruption.

### Drift check

Amends D105 ("single ledger authority on GMK") and D169 ("no second ledger authority") — both remain true *per install*; the amendment is that authority is per-install, not fleet-singleton. Kernel unchanged; append-only unchanged; the exchange is rows, not state. One new transport route on the existing pairing port; three new predicates under existing/nearby namespaces. Reuse map: pairing + token gate (D104/D152), source descriptors + confidence inheritance (D8/D65), install identity (D170), engine placement + LAN Comfy (D157/D161/D178), need floor + supersession + backoff (D81/D100/D101), principal self-bind (D122).

### Status log

| Date | Status | Note |
|------|--------|------|
| 2026-11-25 | Candidate | Drafted from the multi-device regime design discussion; supersedes the single-authority posture for the peer era. |
| 2026-11-25 | Candidate | Relocated from GreyAvatar `docs/decisions/` to this corpus. |

---

## 4 — Steward liveness indicator: the ITS heartbeat is a first-screen chit

**Provenance:** GreyAvatar `docs/decisions/D182` (commits `0181d5b`, `4813923`).
**Status:** Candidate · **Date:** 2026-11-25
**Builds on:** D57 (conductor on-by-default), D58 (engagement-paced cadence), D81 (need floor + cadence pin), D93 (band ordering / maintenance deferral), D95 (ledger health chit precedent), D100 (dispatch backoff), D101 (need priority), D169 (powersave `drain-idle-turn` skip), candidate 2 above (the `need:*` family the floor will grow).

### Context

The idle-turn steward (`startIdleConductor` → `runConductorPass` → `drain-idle-turn` / `drainNeedFloor`) is the machine that acts on what the owner is worried about — but it is invisible. The bridge already stamps every pass into `lastIdlePassAt` and serves it on `/api/needs` (`idlePassAt`, typed in `ui/src/api.ts`); nothing renders it. A needs rail that never changes is indistinguishable from a dead steward: the owner's stated convention is that things they are worried about tracking belong on the first screen, at one glance — that is why the visualizers exist. Today the first screen shows the floor (unmet needs), the book (ledger health chit, D95), and the waves — but not the steward's own heartbeat.

### Options

- **A — Convention: every first-screen surface carries a steward liveness chit driven by `idlePassAt` (chosen).** Documents the operator-visibility contract now; implementation lands as a normal UI slice.
- **B — Full steward-state visualizer (band, backoff, budgets, lane history).** Larger scope, premature: the missing signal is *alive / stale / dead*, not the conductor's internals. May follow if the chit proves insufficient.
- **C — Log/artifact-only liveness (`runtime/last-launch-*.json`, bridge log).** Already true and already insufficient — artifacts are agent/CI forensics, not an operator surface.

### Decision

1. **Liveness is a first-screen contract.** Any surface an owner sees first — today the Chat screen topbar/right-rail, tomorrow a mirror or Companion panel — must render the steward heartbeat alongside the needs list. A needs list without a liveness signal is a lie of omission: it cannot distinguish "nothing to do" from "steward dead."
2. **The signal is `idlePassAt`, rendered as age.** The chit shows time-since-last-pass ("steward 12s" / "steward 3m"), not wall-clock. Expected wake = current band cadence × `GREY_IDLE_AUTOTURN_MS` (and the D81 pin: active cadence whenever open needs exist), so staleness is judged against the *live* cadence, not a fixed threshold. Escalation: **ok** — within ~2× expected wake; **warning** — within ~4×; **alert** — beyond that, or no pass recorded since boot.
3. **Liveness is not backlog.** The chit answers "is the steward waking," never "did needs drain." A green heartbeat next to a static need row means the need is parked — gated, backoff (D100), or readiness-blocked (D58) — which is honest steward behavior, not a stall. Backoff/parked-state visibility (nextEligibleAt per need) is the natural second increment and is explicitly deferred, not dropped.
4. **New `need:*` predicates must register with drains AND displays.** Before a new need predicate ships its drain path, it must be counted by `countOpenNeeds` (else the D81 cadence pin can't see it) and projected by `openNeeds()` (else the rail lies about the floor). This is the concrete form "first-screen tracking" takes for candidate 2's `need:request` and any sibling rows.
5. **Owner-facing proof is the chit, not the endpoint.** Verification of this convention happens through launcher-visible UI — the chit on screen, its escalation states, its recovery after a stall — never by instructing the owner to hit `/api/needs`.

### Non-goals

- No new predicate, primitive, or segment — this is a visibility convention over an existing field.
- No change to conductor cadence, band ordering, lane tools, or drain semantics.
- No backoff-state surfacing yet (deferred increment, item 3).
- Not a per-need drain journal — the ledger already records fulfills/terminal-fails; the chit is a liveness read, not a log.

### Predicates registered (D7)

None — convention over existing surfaces (`/api/needs` `idlePassAt`; connector-chip chit pattern; D95 chit precedent).

### Ideal it protects

Local memory, personified trust — the steward that carries the owner's open worries must be *seen* to be working. The first screen is where worry lives; silence there reads as failure whether or not the machine is healthy.

### Drift check

Pure visibility convention; no mechanism added. Reuse map: `idlePassAt` / `lastIdlePassAt` (ui-bridge pass callback → `/api/needs`), `NeedsSnapshot` type (`ui/src/api.ts`), `connector-chip` + D95 `ledgerHealth` chit pattern, `countOpenNeeds`/`openNeeds()` display-count pairing (item 4 codifies their existing mirror relationship — `src/tools/open-needs.ts` already notes it "mirrors ui-bridge `openNeeds()` display predicates"). Item 4 also closes the candidate-2 hazard where `need:request` would drain (or not) invisibly.

### Status log

| Date | Status | Note |
|------|--------|------|
| 2026-11-25 | Candidate | Drafted from the ITS health-check discussion: steward verified wired and running; the missing piece is the heartbeat on the first screen. |
| 2026-11-25 | Candidate | Amended — scope clarified: forward convention for future builds; current-build citations are reuse-map grounding, not a retrofit order on the shipped realization. |
| 2026-11-25 | Candidate | Relocated from GreyAvatar `docs/decisions/` to this corpus. |

---

## 5 — Host-sovereign credential screen: joining a network surrenders credential management

**Provenance:** GreyAvatar `docs/decisions/D183` (commits `7a7b51f`, `4813923`).
**Status:** Candidate · **Date:** 2026-11-25
**Builds on:** D8 (source-confidence inheritance), D50 (connector OAuth parity port), D66 (access policy), D76 (usage-credential vocabulary — connector credentials ≠ usage credentials), D104/D152 (LAN pairing + token gate; keyring fail-closed secret custody), candidate 3 above (sovereign hub ledgers / peer topology), `C-SeedLifecycle` (`conventions-002.md` — the join flow where surrender consent lands).

### Context

Credential custody is already physically correct: connector secrets live in the OS keyring (`src-tauri/src/secret_store.rs`), never in the ledger, fail-closed in release builds (D152). The Settings → Credentials drawer already concentrates the management surface — `ConnectorsPanel` (Google OAuth covering Gmail/Calendar/Contacts, Outlook, Reddit, Amazon, YouTube; the standards card carries the iCloud/IMAP preset) plus `UsageCredentialsPanel` (avatar × source, avatar × tool). What has no stated rule is **where** that surface may exist once installs join into networks: candidate 3 makes every install a sovereign ledger hub, and the bench already runs mirror (`displayOnly`) and peripheral (`inputOnly`) surface roles. The owner direction: credential management is a host function, and joining a network means surrendering it to the host — otherwise a satellite's outside-network communications would sit outside the application's credential trust fabric.

### Options

- **A — Host-sovereign credential screen; join surrenders management to the host (chosen).** One credential surface per network, on the install carrying the host role; satellites render status at most. No new machinery — surface roles and keyring custody already exist.
- **B — Credential sovereignty per install.** Every peer manages its own secrets. Rejected: multiplies secret attack surface and duplicate OAuth grants, and puts each satellite's external communications outside the host's credential trust — exactly the split-brain the convention exists to prevent.
- **C — Central credential server / escrow.** A dedicated service holding fleet secrets. Rejected: new component against the reuse-first gate; keyring + host role already provide the custody; adds a secret-replication channel the append-only model doesn't want.

### Decision

1. **The credential screen is a host-only surface.** One install per network carries credential management — the owner's account connections (Google/Gmail, iCloud/standards, and every future credential a connector needs) plus the usage-credential and tool-permission families that already share the drawer (D76 item 9). Mirror (`displayOnly`) and input-peripheral (`inputOnly`) surfaces must not render credential management; the surface-role context (`resolveSurfaceContext`) is the gate.
2. **Connector secrets are host-local — never ledgered, never replicated.** OAuth tokens, client secrets, and passwords stay in the host's OS keyring (D152 fail-closed). A candidate-3 peer delta exchange carries assertions only; secret material has no wire format. If a peer needs a credentialed read, the *need* travels to the host and the *result* returns as a peer-sourced assertion — the secret never does.
3. **Joining a network surrenders credential management.** When an install pairs into a host's network (D104/D152 pairing), its credential screen closes: it holds no connector secrets and mints no independent external communications. Traffic leaving the application's user network is brokered by the host's credential fabric. The surrender is consented at join — same posture family as candidate 3's rejoin/new-ownership fork — and is itself recordable as a claim on both books.
4. **Sovereignty is capability; surrender is posture.** Candidate 3 stands: every install *can* be a hub. A lone install is a hub-of-one and keeps its credential screen. The surrender applies on joining *someone else's* network — a device that runs its own ledger but no fleet role is untouched. Leaving a network (or a consented split) restores the install's own credential surface; secrets acquired before the join remain on the former host, since item 2 gave them no path off it.
5. **Custody vs policy stay split per D76.** `avatar:usagecredential` rows are ledger *claims* — they replicate peer-to-peer like any other assertion, so a satellite's book still says which avatars may use which sources. What surrenders is *custody and origination*, not the access-policy record: the satellite's floor can hold the need; only the host's keyring can fulfill it.
6. **Status visibility is not custody.** Non-host surfaces may still display connector/auth state (chips, honesty banner, "connected" markers) — seeing that the host's Google is authorized leaks nothing. Only connect/revoke/issue actions are host-gated.

### Non-goals

- No new connector, segment, or primitive — this is a custody/posture convention over existing seams.
- No credential sync, escrow, or export path between peers (item 2 is absolute for the fleet era).
- No change to usage-credential or tool-permission semantics (D76/D131 untouched).
- No redefinition of host vs satellite beyond the surface roles and pairing that already exist — the candidate-3 peer exchange decides which install is "host" for a network; this decision says what that role carries.

### Predicates registered (D7)

None today. Anticipated when the join flow lands: `peer:credential-surrender` (peer namespace) — a claim recording the join-time surrender, symmetric with `peer:sever`. Not yet written by any code path.

### Ideal it protects

Local memory, personified trust — the machine that holds your secrets is the one machine you chose to trust with them. Secrets don't wander the fleet; needs do, and they come home to the host's keyring to be fulfilled.

### Drift check

Convention over existing machinery; no new component. Reuse map: keyring custody + fail-closed release (`secret_store.rs`, D152), Settings → Credentials drawer + `ConnectorsPanel`/`UsageCredentialsPanel` (D76), surface roles `displayOnly`/`inputOnly`/`resolveSurfaceContext` (mirror/input surfaces), pairing + token gate (D104/D152), peer delta exchange + fleet need-floor claiming (candidate 3 items 3 and 5). The one deliberate constraint introduced — "the credential screen renders only on the host surface" — is a UI gate over `SURFACE_CTX`, not a new system. Item 4's surrender-restore symmetry follows the candidate-3 severance-offer pattern: claims, consent, append-only.

### Status log

| Date | Status | Note |
|------|--------|------|
| 2026-11-25 | Candidate | Drafted from owner direction: credential screen (Gmail/iCloud/other) is host-only; joining a network surrenders credential management to the host; outside-network communications brokered by the host's credential fabric. |
| 2026-11-25 | Candidate | Amended — scope clarified: forward convention for future builds; current-build citations are reuse-map grounding, not a retrofit order on the shipped realization. |
| 2026-11-25 | Candidate | Relocated from GreyAvatar `docs/decisions/` to this corpus; `C-SeedLifecycle` cross-link added. |
