# FEATURES.md — Quorum 0.3.0.005 capability manifest

Fresh realization from `prompt.md` (build cycle 5, direction-005). Python
3.10+ stdlib only — no dependencies, no package installs. Nothing deferred
this cycle: the fleet/USB-seed lifecycle and the artifact-exchange suite are
built and scored. Live engines declared honestly; every mode below is what
the running system reports on `/api/honesty`.

## Engine modes on this machine (evidence: `runtime/gate.json`, launch logs)

| Engine | Mode |
|---|---|
| LLM | `live-ollama:llama3.2` — real local model; role-diversified seam (`QUORUM_LLM_MODEL_*`), moondream on the vision lane |
| TTS | `sapi` — Windows SAPI voices; serialized speech floor with measured `playbackMs` |
| STT | `browser-webspeech-declared` — browser Web Speech surface; absent server-side, declared |
| Art | `llm-authored` — persona portraits drafted by the local LLM as authored SVG of THAT persona (V-A); `fallback-declared` when offline |
| Sources | wikipedia (live HTTP), duckduckgo (live HTTP), ics-calendar (fixture file), eml-inbox (fixture directory — labeled, V-G), files |
| Discovery | real subnet ARP/ICMP scan + Bluetooth radio enumeration + named-roster matching |

## Declared absences (counted against completeness — never faked)

- **Configured live mail account** — absent. Email runs on a fixture `.eml`
  directory, and every email surface/commentary records `basis:
  fixture-directory` (V-G honest labeling).
- **OAuth account connectors** — absent, declared on the honesty banner.
- **Physical join of a second machine** — invite/role/surrender mechanics
  are built and enacted; a live peer install answers only if a fleet device
  is actually running one. Unreachable targets record `state: pending`,
  never `member`.
- **Seed media cryptographic signing toolchain** — the seed writes a
  manifest + `SIGNING-NOTES.md` documenting the allowlist arrangement
  (C-SeedSigning); no Authenticode cert on this machine, declared.

## Feature manifest vs GreyAvatar parity bar (`.devin/jev-ref-greyavatar.out`)

| Area | Status | Where |
|---|---|---|
| Assertion ledger — append-only JSONL, typed values, claimant vocabulary, certainty, basis, supersession | implemented | `quorum/rows.py`, `quorum/book.py` |
| Computed views / resolve / current-vs-superseded | implemented | `quorum/book.py` (`resolve`, `view`, `effective_confidence`) |
| Needs floor — need:* lifecycle, templates, slots, candidate values, acceptance gates, focused-need fill | implemented | `quorum/needs.py` |
| Tool registry + DSL steps + user-authored/candidate tools | implemented | `quorum/tools.py` |
| Grants/authority — witnessed grant gate, honest deferral | implemented | `quorum/host.py` (`Grants`), S-defer-publication |
| Competing tools on same need + comparison runner | implemented | `list-members` vs `retrieve-table`; `/api/compare`; S-competing-tools |
| Personalities — mint, ethics gate + imitation mark, registers, persistent store | implemented | `quorum/personas.py` |
| Persona voice fidelity — register constraint on truthful output; zero-hit fails closed; fidelity never null | implemented (S-2 strict) | `quorum/personas.py` (`grounding_of`); S-faithful-voice |
| LLM-authored portrait art bound per persona | implemented (V-A) | `quorum/art.py`; S-portrait-bind |
| Voice config per persona + voice-spec QR-fittable exchange + local mapping | implemented | `quorum/artifacts.py` (`voice_spec`, `map_voice`); S-voice-spec, S-voice-select |
| Roster — select, reorder with VISIBLE held-confidence change (V-D, dyadic 0.5 default, S-5) | implemented | `quorum/personas.py` (`move`); S-personality-roster |
| Speech floor — serialized playback, measured ms, held-until-complete | implemented | `quorum/engines.py` (`SpeechFloor`); S-speech-serialization |
| Steward — idle duties, temporal attention, liveness chit (idlePassAt age vs cadence) | implemented (§4 promoted) | `quorum/steward.py` |
| Temporal interpretation — bucketed calendar | implemented | `quorum/temporal.py`, `/api/calendar` |
| Connectors — local source ingest + live web | implemented | `quorum/connectors.py` |
| Exchange packages — export/import below action threshold, tools staged as candidates | implemented | `/api/exchange/*`; S-exchange-import |
| JEV turn lane — gate→classify→evaluate, counterfactual `need:request` capture | implemented (§2 promoted) | `quorum/evals.py` |
| Launch partition + transient boundary + snapshot inference + sequential commits | implemented | `quorum/book.py`, `quorum/host.py` |
| Readiness gate — checks, pass timestamp, time-to-gate in evidence | implemented | `quorum/gate.py`, `runtime/gate.json` |
| Two-part boot + launch hygiene (probe→exclusive bind→refusal→close-terminate) | implemented (S-4) | `quorum/__main__.py`, `scripts/launch-check.py` |
| UI — roster rail w/ inline edit (V-F), Library, workshop w/ explanations (V-C), needs rail + steward chit, fleet map, credential screen (§5), themes, declared-absences section (V-B), chat, status bar | implemented | `quorum/ui/` |
| Fleet: USB seed run-in-place, stage-consent, discovery scan, user-mediated invite, role negotiation, mint gen-2, courier log, roster, network map, local transports, credential surrender | implemented | `quorum/fleet.py`; S-usb-* + S-fleet-* + S-network-map + S-local-transports + S-credential-surrender |
| Artifact exchange: qmatrix-24 BMP codec, capture layers (literal/semantic/stylistic), workshop below threshold, tool wire fidelity, adopt/republish gen-2, dubious-source resolution against vetted pointers, preload cache | implemented | `quorum/artifacts.py`; S-artifact-*/S-tool-transmission/S-dubious-source/S-preload-cache |
| Machine tones vs user jingles — distinct registers | implemented (V-E) | `quorum/engines.py` (`machine_beep`, `user_jingle`); `/api/tones/*` |
| Gmail/OAuth connectors | absent — declared | — |
| Studio/doc composition, android satellite, companion app, Tauri shell | absent — not built at this scale | — |

## Convention conformance (C-* from `C:\Project\MigrateInbound\CONVENTIONS.md`)

Execution structure (scored standing):
| Convention | Disposition |
|---|---|
| C-TwoPartExecution | conform — Part 1 mount+gate, Part 2 surface+steward (`__main__.py`) |
| C-ReadinessGate | conform — gate checks ledger/partition/LLM/speech/fleet; pass time in `gate.json` + `last-launch.json` |
| C-LaunchPartition | conform — partition written in dependency order, mounted before journal replay |
| C-TransientBoundary | conform — `runtime/transient/` reset per boot |
| C-SnapshotInference | conform — respondents draft on `book.snapshot()` (`inference:snapshot` rows) |
| C-SequentialCommit | conform — commits land in rank order (`inference:commit` rows) |

Fleet/seed (new this cycle):
| C-UsbSeed | conform — app runs in place from `H:\quorum-seed`, no install required |
| C-SeedStagePath | conform — stage target `C:\builds-installed\quorum` |
| C-SeedLifecycle | conform — seed boot→log→stage-consent→discovery→invite→role→map order |
| C-SeedLog | conform — `seed-log.jsonl` on the medium, accumulates across machines |
| C-SeedMint | conform — gen-2 installer carries founding network identity as an ADOPTABLE offer (join-or-found is the user's choice) |
| C-LocalTransports | conform — wired-lan baseline + bluetooth enumeration; wired preferred |
| C-HonestDiscovery | conform — broad+honest: non-fleet devices found and mapped, never joined |
| C-SeedSigning | conform — `SIGNING-NOTES.md` + manifest on the minted seed; no cert on this machine, arrangement documented rather than faked |
| C-HostAuthority | conform — host mints/installs; satellites get surfaces, never host powers |
| C-AgenticProtocol | conform — peer contact = structured machine exchange, not human chat |
| C-SupportedOS | conform — ranked target list honored in `fleet.py` ROSTER |

Artifact exchange (new this cycle):
| C-WorkshopArtifact | conform — workshop lands below action threshold, adjudicate-to-adopt |
| C-InterpretedArtifact | conform — capture = literal + semantic + stylistic layers |
| C-ToolWireFidelity | conform — literal decode must round-trip the SAME tool definition (checked in S-tool-transmission) |
| C-ArtifactCapture | conform — single capture yields multiple extraction layers |
| C-ArtifactRepublish | conform — adopted workshop re-encodes to gen-2 artifact |
| C-PreloadCache | conform — `seed-packs/vetted-sources.json` pointers + decoder entries + exemplar |
| C-VoiceSpec | conform — QR-fittable minimal voice spec (≤400 bytes) |
| C-VoiceSelectFloor | conform — selection from locally installed voice list |
| C-EngineMapping | conform — spec→installed-voice nearest mapping (`map_voice`) |

Promoted steering (decision-candidates-001 §§1–5, owner 2026-11-25):
| § | Disposition |
|---|---|
| §1 tool candidates + acceptance mint | conform — imported/minted tools stage as `tool:candidate`, invocable only after acceptance mint |
| §2 JEV turn lane | conform — gate→classify→evaluate; counterfactual disagreement mints `need:request` (unmet-need record) |
| §3 sovereign hub ledgers + peer rejoin/severance | conform — `peer:joined`/`peer:severed`/`peer:rejoin-offer` rows + delta exchange |
| §4 steward liveness chit | conform — `idlePassAt` age escalated ok/warning/alert vs cadence |
| §5 host-sovereign credential screen | conform — `surface_role` gate; satellites never host the screen |

Core vocabulary (standing):
| C-JsonlLedger | conform | C-SourceCeilings | conform | C-UserSetSupremacy | conform |
| C-CertaintyPrivilege | conform | C-ExchangeLayers | conform | C-ConvergentOntology | conform |
| C-UnmetNeedRecords | conform | C-DeterministicMatchReview | conform | C-SpecializedListRetrieval | conform |
| C-CompetingSources | conform | C-ConfiguredAccounts | conform (fixtures labeled) | C-ConnectorSet | conform |
| C-SourceDomains | conform | C-MultiSourceAccess | conform | C-LocalIndices | conform |
| C-EthicsGate | conform | C-PersonalityArt | conform (LLM-authored) | C-VoiceDiversity | conform |
| C-PresenceRoster | conform | C-PresenceStage | conform | C-ChorusOnAddress | conform |
| C-SequentialRespondents | conform | C-PerceivableRespondents | conform | C-DyadicConfidence | conform (0.5 default, I-Dyadic between-neighbors) |
| C-SpeechFloor | conform | C-StewardAsTool | conform | C-TemplateDerivedUI | conform |
| C-DeclaredPresentation | conform | C-DeclaredStubs | conform | C-HonestyBanner | conform |
| C-InspectionSurfaces | conform | C-SettingsPreloads | conform | C-PreloadSuite | conform |
| C-ConversationArchive | conform | C-QuickSelect | conform | C-SurfaceAssignment | conform |
| C-ExplicitPolicies | conform | C-ScenarioEnactment | conform | C-CanonicalScenarios | conform |
| C-LauncherTests | conform | C-DesktopShell | conform | C-FullScreen | conform |
| C-UserFacingPriority | conform | C-SetBuild | conform | C-AcceptanceChecks | conform |
| C-ContactTags | conform | | | | |

Challenges filed: none this cycle. DDG is retained as the independent
second general source alongside wikipedia (C-CompetingSources).

## Evidence map

| Item | Path |
|---|---|
| Launch procedure | `LAUNCH.md` |
| Launch logs | `evidence/launch/`, `launch-server.out` |
| Machine-readable launch report | `runtime/last-launch.json` |
| Gate + time-to-gate | `runtime/gate.json`, `gate:passed` assertion, launch log |
| Launch hygiene enactment | `evidence/launch/launch-check.json` |
| Second-instance probe | `evidence/probe-*.json` (`scripts/probe.py`) |
| 44 scenario files w/ inline checks | `evidence/scenarios/S-*.json`, `evidence/scenarios/suite.json` |
| Ledger book of record | `runtime/ledger.jsonl` |
| Network map artifact | `runtime/network-map.json` |
| Seed courier log (on media) | `H:\quorum-seed\seed-log.jsonl` |
| Minted gen-2 installer (on media) | `H:\quorum-seed\minted-gen2\` |
| Persona portraits | `runtime/artifacts/persona-art/` |
| Workshop artifacts | `runtime/artifacts/`, `seed-packs/` |
