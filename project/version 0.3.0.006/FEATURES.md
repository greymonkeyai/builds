# chorus — features & conformance manifest (direction-006 / cycle 6)

Fresh-from-prompt realization. The assertion ledger is the book of record;
surfaces are computed views. Everything listed here is exercised through
the operator surface — evidence under `evidence/`.

## Engine modes (declared, never hidden)

| Engine | Mode when live | Absent behavior |
|--------|---------------|-----------------|
| LLM    | `live-ollama:llama3.2` | deterministic fallback replies, `fallback-declared` art — legible, not authored-claimed |
| TTS    | `sapi` (Windows) | `declared-absent`; utterances still serialized + measured on the floor |
| STT    | absent | declared absence; no server-side STT this cycle |
| Voices | pool of 2 | **thin pool declared honestly** (banner + honesty surface) |
| Mail   | fixture `.eml` basis or configured IMAP account | fixture basis labeled; unconfigured reads honest |
| Seed signing | unsigned source | allowlist arrangement documented in `SIGNING-NOTES.md` (C-SeedSigning) |

## Surfaces

- **Chat** — typed input → assertion → routed intents → persona replies
  (grounded/composed fidelity flagged; never fidelity:null). Audible ack
  (≤5 syllables / ≤0.5s) plays before TTS composition.
- **Roster** — ordered personas; select; dyadic moves ↑/↓ produce a
  perceivable held-confidence consequence every move (even among equal
  values — 0.05 notch).
- **Unmet floor** — open needs only; met needs leave; focus a need, fill a
  slot conversationally, cancel.
- **Library** — personas, tools (with explanations), formal list objects
  (iterable, criteria + non-matches preserved), workshops, sources,
  exchange packages.
- **Fleet** — discovery with in-progress/transport/finished states, map
  artifact covering non-members, invite → install path (never a dead end),
  peer sync, legible outcomes.
- **Stage** — interstitial queue (fleet-addressable asset needs, rework on
  input change, present-when-ready else deferred+declared), scene
  enactment (knock-knock), background audio channels + sample library.
- **Settings** — themes (light/dark/sepia/contrast), response depth,
  account credentialing (secret stays in the local store — never the
  ledger), source admission.

## Convention conformance / challenges

**Conformed (on record):**

- C-TwoPartExecution, C-ReadinessGate (pass timestamp in `runtime/gate.json`),
  C-LaunchPartition, C-TransientBoundary (journal durable; playback/
  liveness telemetry marked transient), C-SnapshotInference,
  C-SequentialCommit (replies commit in respondent order).
- C-UserPathEnactment — all scenario checks exercise the HTTP operator
  surface the UI drives (same endpoints the browser calls).
- C-RespondentGrantUnion, C-ResponseDepth, C-InterestRespondents,
  C-PerceivableDyadic, C-IntentRouting, C-MonotonicLiveness,
  C-ConversationalRegister, C-SpeakableRendering, C-FormalList,
  C-BoundPortrait, C-CredentialDescriptor, C-ScannableInterchange
  (`rastgrid-1` BMP symbology — symbology free per owner ruling),
  C-PublishOrDefer, C-FloorLifecycle, C-ProgressVisibility,
  C-OperatorGuidedJoin, C-HonestDiscovery, C-ToolCandidateAcceptance,
  C-SeedSigning, C-SeedLifecycle, C-SeedMint, C-SovereignHubs,
  C-CredentialSurrender, C-ToolWireFidelity, C-ArtifactCapture,
  C-ArtifactRepublish, C-PreloadCache, C-UserFacingPriority,
  C-DeterministicMatchReview.

**Challenges:** none this cycle — no silent departures.

**Declared absences** (recorded on the honesty surface, count against
completeness): configured live mail account (path exists — app-password/
IMAP), OAuth flow, a second live fleet node on the LAN (operator path
open; peer protocol exercised), Authenticode signing cert (allowlist
documented), server-side STT.

## Scenario evidence

`evidence/scenarios/S-*.json` — 71 scenario records with the frozen check
names from `scenarios.md`; `evidence/summary.json` — pass tally;
`evidence/launch/launch-check.json` — launch-hygiene legs;
`evidence/console-*.log` — boot transcripts.
