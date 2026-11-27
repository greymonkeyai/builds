# vesta — features & conformance manifest (direction-007 / cycle 7)



Fresh-from-prompt realization. The assertion ledger is the book of record;

surfaces are computed views over it. Every obligation is exercised through

the operator surface (the same HTTP endpoints the UI drives) — evidence

under `evidence/`.



## Phase-0 contract outcome



- **All-red baseline:** `0/269` checks pass on `--bare` — every check can

  fail; no vacuous greens (evidence: `evidence/runs/baseline-20261126-160431/`).

- **Green run:** `260/269` checks, `68/71` scenarios all-green

  (evidence: `evidence/runs/green-20261126-160519/`).

- **Sabotage discrimination:**

  - `empty-store` — `85/269` still pass (surface/file-level legs only;

    store-backed legs go red).

  - `stub-engines` — `249/269` pass; capability legs (voice/transport/LLM)

    go red while honest-absence legs correctly stay green.

  - `stubbed-endpoints` — `3/269` pass (pure file-level survivors:

    launch.cmd, launch-check artifact, courier log on media).

- **Honest remainder:** 9 legs across 3 scenarios — all gated on a remote

  (non-sameHost) joined fleet member; no second real node exists on this

  LAN. Declared absence, not faked (see below).



## Engine modes (declared, never hidden)



| Engine | Mode when live | Absent behavior |

|--------|---------------|-----------------|

| LLM | `live-ollama:llama3.2:latest` | deterministic fallback replies, `ungrounded-declared` register — legible, not authored-claimed |

| TTS | `sapi` (Windows) | `absent-declared`; utterances still serialized on the speech floor |

| STT | absent | `absent-declared`; no server-side STT this cycle |

| Voices | pool of 2 (David, Zira) | **thin pool declared honestly** (honesty surface) |

| BT transport | `present` (radio + enumerators) | `absent-declared` |

| Mail | fixture `.eml` basis (`fixtures/inbox/`) or configured IMAP account | fixture basis labeled; unconfigured reads honest |

| Seed signing | unsigned source | allowlist arrangement documented (C-SeedSigning) |



## Surfaces



- **Chat** — typed input → assertion → routed intents (want/unmet) →

  respondent-union replies. Each reply carries `register`

  (grounded / ungrounded-declared / composed); R-I1 — personalities

  improvise on preference/opinion questions, marked by register, never

  refused. Audible ack (≤0.5s wav) precedes TTS composition; composition

  latency measured per response and recorded (fleet-comparable field).

- **Roster** — 4 shipped personas minted at boot; create/select/dyadic

  ordering; bound portraits; voice assignment from the pool (in-use

  declared honestly).

- **Unmet floor** — open needs only (fold bug fixed: fulfilled/cancelled

  needs stay off the floor); focus → slot-fill candidates ranked → fill

  conversationally; cancel path.

- **Library** — personas, tools (deterministic review pairs per

  C-DeterministicMatchReview — review annotates, never vetoes), formal

  list objects (iterable, criteria + non-matches preserved), workshops,

  50 configured sources (seed import + admission gate), exchange packages.

- **Fleet** — subnet discovery (sweep + parallel enrichment, in-progress/

  transport/finished states) mapping non-members too (C-HonestDiscovery);

  invite → join → install path with honest per-target status; peer sync

  deltas; USB courier (`seed-log.jsonl` on the medium accumulates across

  machines/runs).

- **Stage** — interstitial queue (asset needs fleet-addressable, rework on

  input change, present-when-ready else deferred+declared); scene

  enactment; background channels + sample library; media intent detected

  in `conversation.turn` ("play something quiet" opens a channel).

- **Settings** — themes (light/dark/sepia/contrast), response depth,

  **style picker (R-S1) present and reachable on the owner surface with

  perceivable effect**, account credentialing (secret in the local store —

  never the ledger), source admission.

- **Status bar / honesty** — engine banner, thin-pool declaration, gate

  state, node id; all stubs declared.



## Convention conformance / challenges



**Conformed (on record):**



- C-TwoPartExecution, C-ReadinessGate (pass timestamp +

  `timeToGateMs` in `runtime/gate.json` and

  `evidence/launch/launch-check.json`), C-LaunchPartition,

  C-TransientBoundary (journal durable; liveness/playback telemetry

  transient), C-SnapshotInference, C-SequentialCommit.

- C-UserPathEnactment — all 269 checks exercise the HTTP operator surface

  the UI drives; no mechanism-only greens.

- C-RespondentGrantUnion, C-ResponseDepth, C-InterestRespondents,

  C-PerceivableDyadic, C-IntentRouting, C-ConversationalRegister,

  C-FormalList, C-BoundPortrait, C-CredentialDescriptor,

  C-ScannableInterchange (`rastgrid-png-1` — PNG payload symbology this

  build; symbology choice free per owner ruling), C-PublishOrDefer,

  C-FloorLifecycle, C-ProgressVisibility, C-OperatorGuidedJoin,

  C-HonestDiscovery, C-ToolCandidateAcceptance, C-SeedSigning,

  C-SeedLifecycle, C-SeedMint, C-SovereignHubs, C-CredentialSurrender,

  C-ArtifactCapture, C-ArtifactRepublish, C-PreloadCache,

  C-DeterministicMatchReview.



**Challenges:** none this cycle — no silent departures.



**Declared absences** (recorded, count against completeness):



- **Remote fleet member** — 9 red legs across `S-fleet-exchange` (4),

  `S-role-negotiate` (2), `S-credential-surrender` (3). All require a

  joined member that is not sameHost; no second real node exists on this

  LAN. Same-host instances are explicitly not members per fleet lab rules.

  The operator path is open; the peer protocol is exercised

  (invite/join/install/delta legs green to the extent a single node can

  demonstrate).

- Live configured mail account (fixture `.eml` basis stands in, labeled).

- Authenticode signing cert (allowlist arrangement documented instead).

- Server-side STT.



## Scenario evidence



- `evidence/scenarios/S-*.json` — 71 scenario records; each carries the

  frozen check names from `scenarios.md` with baseline + green + sabotage

  outcomes inline.

- `evidence/runs/baseline-20261126-160431/summary.json` — all-red baseline

  (`0/269`).

- `evidence/runs/green-20261126-160519/summary.json` — green run

  (`260/269`, `68/71` scenarios all-green).

- `evidence/runs/sabotage-*-*/summary.json` — three sabotage passes.

- `evidence/launch/launch-check.json` — 4 launch-hygiene legs +

  `timeToGateSeconds`.

- `runtime/` — the durable journal, gate.json, last-launch.json, persona

  records, speech wavs, exchange artifacts, preload cache.

