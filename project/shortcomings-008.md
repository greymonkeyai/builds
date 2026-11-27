# Shortcomings 008 — named deficiencies of `version 0.3.0.007`
<!-- harness-doc kind=shortcomings status=approved since=2026-11-27 applies-to=direction-008 -->

Owner findings at the Cycle 7 review point (2026-11-26), challenging the
JEV/result framing. Bars describe what a build is measured against, not how.

- **R-V1 Self-attested checks.** ~10 checks trust the app's own flags about
  itself (`launchedFrom`/`inPlace` while the suite instance ran from
  `C:\builds`, not the medium; `playsBeforeComposition` trusted without
  corroboration) or pass vacuously (or-fallbacks, `is-not-None` on empty
  payloads, speculative discrimination). The phase-0 sabotage pass proves a
  check *can* fail; it does not prove a check measures the right thing —
  self-attestation survives it. **Bar:** a check's evidence source is
  external to the flag being asserted — where a self-reported flag is the
  evidence, it is corroborated against ground truth (process cwd/mount,
  journal rows, rendered surface), not read at face value.
- **R-U1 Rendered-surface verification gap.** Only 8/269 checks inspect
  rendered page content; the rest exercise the endpoints the UI drives —
  mechanism-adjacent, the same divergence class as the cycle-6 0/0-vs-0.6/0.8
  owner ruling. **Bar:** checks exercise what the user can reach — rendered
  surface state and user-path enactment per C-UserPathEnactment, not merely
  the API surface beneath the UI.
- **R-F4 Install never driven to an outcome.** The fleet legs were framed as
  environment-capped ("one-node lab") — an error. Discovery found 36
  candidates including installable targets (`DESKTOP-OOGQ7UN.lan`,
  `pixel-9a.lan`, `google-home-mini.lan`); roster 14/14. The suite invited
  `192.168.86.1` — the **gateway** — got "runs no vesta peer", surfaced
  directions (that leg passed), and install stayed `pending`; no install was
  ever enacted, so no remote member existed and the 9 exchange/role/surrender
  legs stayed red. **Bar:** an install attempt driven to a verdict on a named
  installable roster device (installed / refused / failed-with-reason);
  "absence" claims require an attempted install on an installable target,
  not a skipped one; the selected join target is an installable device, not
  the gateway. Cycle-6 attempted `.41` and failed honestly — cycle-7
  regressed.

## Owner review findings (2026-11-27)

- **R-A2 No audio whatsoever.** The running `.007` produces no audio — yet
  audible-ack, background-channels, voice-select and speech-latency scored
  on self-asserted and mechanism evidence (R-V1/R-U1 in the wild). **Bar:**
  audio scenarios require *perceivable* evidence — a produced audio
  artifact or device-confirmed output the owner could hear, not a flag
  asserting it played. (Owner: existing features 0.4, speech-composition
  latency 0.)
- **R-F5 Device identification + ping.** Fleet discovery results carry
  insufficient identifying info to tell devices apart. **Bar:** an
  identify/ping action on a discovery result that signals the device to
  respond per its capabilities — chirp/beep, on-screen display, whatever a
  lab device type supports — plus materially richer identifying info in
  results (name resolution, vendor/type inference, services seen).
- **R-M1 Metrics are raw seconds, not 0-1.** Owner ruling: speech-
  composition latency and time-to-gate are measured and reported in
  **seconds** (tenths where results justify the precision) — scored on
  evidence presence and honesty, not normalized. Suite + JEV criteria to
  carry the unit.
- **R-U1 sharpened (standing bar).** If a feature is not usable by the
  user it does not count — stubs and hidden/unreachable affordances are
  absence, not enactment.

## Open — for direction-008 scoping

- Formally **define interfaces** (surface/affordance contract per module,
  deepening impl-design-001's surface obligations)?
- Formally **detail user-path use scenarios** (user-journey steps per
  scenario, making checks user-path-native rather than endpoint-native)?
- Coordinator recommendation recorded 2026-11-27: user-path scenario
  detail is the stronger lever — it feeds directly into checkable
  artifacts; interface formality as named affordances, not pixel-level
  design.

## Carried JEV flags (cycle-7 verdict, `jev-cycle-007`)

Available to be named by a direction — scored findings, not yet ruled
requirements:

- `S-scene-enactment` overclaimed: "music" tool-class asserted from TTS
  presence alone; scripts canned, not composed.
- `S-artifact-republish` decodes gen-2 in the same instance, not a second
  instance per spec.
- `UI discover()` runs synchronous discovery; in-progress surface state
  reachable mainly via the background flag.
- No convention challenges recorded; C-SeedSigning departure (unsigned
  source, allowlist arrangement) declared on the record in FEATURES.md —
  reckoned, not silent.
- Owner context: user scored fleet install + exchange media 0/0 last cycle
  against JEV mechanism scores — the user path is the binding instrument.
