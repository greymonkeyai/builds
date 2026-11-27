# hearth — features & conformance manifest (direction-008 / cycle 8)
Fresh-from-prompt realization of `prompt.md` rev 2026-11-27-a (incl. the
adopted environmental-grounding paragraphs: device location +
meteorological data as configured-source claims; home location
canonical; departure/roaming/return cases). The assertion ledger is the
book of record; surfaces are computed views over it. Every obligation is
exercised through the operator surface (the same HTTP endpoints the UI
drives) — evidence under `evidence/`.
Package: `hearth/` (Python stdlib only). Boot:
`python -m hearth --port 9540 --data DIR [--bare] [--sabotage MODE]`.
Launcher: `launch.cmd`. Suite driver: `run-checks.cmd` /
`scripts/run-suite.py`.
## Phase-0 contract outcome
- **All-red baseline:** `0/352` checks on `--bare` — every check can
  fail; no vacuous greens (evidence: `evidence/runs/baseline-*/`,
  per-scenario `baseline` blocks in `evidence/scenarios/S-*.json`).
- **Green run:** `350/355` checks; all 72 named scenarios + 11 pathed
  user journeys exercised through the operator surface
  (evidence: `evidence/runs/green-*/`).
- **Sabotage discrimination:** (per-scenario `sabotage-*` blocks in
  `evidence/scenarios/S-*.json`, summaries in `evidence/runs/sabotage-*`)
  - `empty-store` — **316/355** still pass; the 39 store-backed legs
    (seed import, shipped personas, preload cache, recovery) go red.
  - `stub-engines` — **332/349**; capability legs (voice/LLM/transport)
    go red while honest-absence legs correctly stay green.
  - `stubbed-endpoints` — **53/347**; endpoint-driven legs go red —
    file-level + dead-surface survivors only.
- **Honest remainder (5 legs, 1 scenario):** `S-fleet_exchange` — all
  five legs require a second real hearth node on the LAN; none exists
  (a same-host second instance is explicitly not a joined device).
  Declared absence, recorded, counted against completeness — not faked.
## Evidence-quality fractions (R-V1 / R-U1 — recorded per check)
From `evidence/runs/green-*/summary.json`:
- externalToFlag ≈ 0.48 — corroborated against journal files, process
  cwd/mounts, rendered page, produced artifacts (not the flag asserted).
- rendered ≈ 0.26 — checks whose evidence includes the rendered
  operator surface (`data-affordance` hooks).
- userPath ≈ 0.59 — legs driven through user-reachable actions rather
  than API plumbing beneath the UI.
- selfAttestedOnly = 0.0 — no check scores on a self-reported flag alone.
## Engine modes (declared, never hidden)
| Engine | Mode when live | Absent behavior |
|--------|---------------|-----------------|
| LLM | `live-ollama:llama3.2:latest` | deterministic in-register fallback, declared — never authored-claimed |
| TTS | `sapi` (Windows) | `absent-declared`; utterances still serialized on the speech floor |
| STT | absent | `absent-declared`; no server-side STT this cycle |
| Voices | pool of 2 (David, Zira) | **thin pool declared honestly** (honesty surface) |
| BT transport | `radio-present` | `absent-declared` |
| Mail | fixture `.eml` basis (`fixtures/inbox/`, labeled) or configured account | fixture basis labeled per item + per response; unconfigured reads honest |
| Seed signing | unsigned source | AV allowlist arrangement documented (C-SeedSigning) |
| Weather | `source-open-meteo` via admission gate (free/no-login) | unreachable → declared, not silent |
## Surfaces
- **Chat** — typed input → captured assertion → routed intents
  (name-addressed / capability / want / list / publish / media /
  persona-create / env-query / unmet fallback) → respondent-union
  replies. Replies carry `register` (grounded / ungrounded-declared /
  composed). Audible ack (≤0.5s wav, per-persona) precedes TTS
  composition; compose latency measured per response in **seconds**
  (R-M1) into `metrics.jsonl` with node id — fleet-comparable.
- **Roster** — shipped personas minted at boot; create/select/dyadic
  reorder (every move records a new dyadic assertion); bound procedural
  portraits; voice assignment from the pool (thin pool + in-use declared
  honestly); per-persona editor.
- **Unmet floor** — open needs only (fulfilled/cancelled/superseded
  leave); focus → slot candidates ranked w/ confidence → fill
  conversationally or via fix (superseding); force-execute records the
  intentional threshold-crossing act; above-threshold drains by steward
  with no user act.
- **Library** — personas, tools (15, explanations attached; competing
  realizations recorded per need), formal list objects (iterable,
  criteria + non-matches retained for review), workshops, 50 configured
  sources (seed import + admission gate with per-step verdicts),
  exchange packages.
- **Fleet** — async subnet discovery (enumerated ~22–28 devices this
  lab) with in-progress/finished states; mapping non-members
  (C-HonestDiscovery); **identify** action per device — signal-class
  (chirp/beep/on-screen), vendor + type inference, services seen
  (R-F5); **invite → install attempt driven to a verdict**
  (installed / refused / failed-with-reason) on installable targets
  (R-F4); peer protocol on `:7872`; USB courier (`H:\seed-log.jsonl`
  accumulates across runs/machines); mint gen-2 installer to media;
  stage-consent (decline keeps everything on media; consent stages to
  `C:\builds-installed`).
- **Stage** — interstitial queue (fleet-addressable asset needs, rework
  on input change, present-when-ready else deferred+declared); scene
  enactment (real music/background/speech artifacts produced, absent
  classes honestly skipped); background channels + sample library;
  media intent ("play something quiet") opens a channel.
- **Settings** — themes, response depth, style picker with perceivable
  effect, account credentialing (secret → local credential store, never
  the ledger), source admission.
- **Status bar / honesty** — engine banner, thin-pool declaration, gate
  state + time-to-gate seconds, node id; all absences declared.
## Environmental grounding (rev 2026-11-27-a adoption)
- Device location and meteorological data enter as configured-source
  claims — admitted through the same gate, carrying provenance +
  freshness (S-env-* legs).
- Home location canonical; departure/roaming/return handled as
  state, not loss (journal + needs carry it).
## Convention conformance / challenges
**Conformed (on record):**
- C-TwoPartExecution, C-ReadinessGate (pass timestamp +
  `timeToGateSeconds` in `runtime/gate.json` and
  `evidence/launch/launch-check.json`), C-LaunchPartition,
  C-TransientBoundary (journal durable; playback/liveness telemetry
  transient), C-SnapshotInference, C-SequentialCommit.
- C-UserPathEnactment — checks exercise user-reachable paths (operator
  surface + rendered state), not merely mechanisms.
- C-HonestDiscovery — non-member devices enumerated, mapped, and
  honestly classified (found / installable / unavailable /
  not-a-target).
- C-InterpretedArtifact, C-PreloadCache, C-ArtifactCapture,
  C-ToolWireFidelity (literal decode fidelity asserted),
  C-CertaintyPrivilege (certainty-top reserved for user-set; derived
  certainty capped below top — edge check enforced),
  C-FloorLifecycle, C-DeterministicMatchReview (review annotates,
  never vetoes), C-SpecializedListRetrieval + C-SetBuild (competing
  realizations both exercised + comparison recorded).
- C-SeedSigning — success-gating: unsigned source; allowlisting is the
  owner's arrangement on target machines (documented, on record).
**Challenges on record:** none this cycle — no convention was silently
departed from.
## Comparing tools per need
`list-build` is realized by two competing registered tools
(`list.specialized` — curated-source iteration with non-match review;
`list.general` — generic recall). Both run the same need; the
comparison is recorded as a `tool-comparison` ledger row
(S-competing-tools evidences both legs + comparability).
## Frozen check names
Check names under `evidence/scenarios/S-*.json` reuse the `.007`
identifiers verbatim; new bars minted new names (identify/ping,
verdict legs, perceivable-audio legs, seconds legs). Baseline + green +
sabotage runs carried inline per scenario.
