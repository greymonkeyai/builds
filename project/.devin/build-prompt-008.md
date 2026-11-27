You are the build session for development-harness direction-008. Your working folder is
this project folder.

Read first, in order: AGENTS.md, direction-008.md, shortcomings-008.md,
impl-design-001.md, then prompt.md (revision 2026-11-27-a — an assembled snapshot:
ProjectPrompt + `Design\INTENTS.md` + `Design\MAXIMS.md` embedded; `C:\Project\Papers\`
and the `*_explained` files are cited as consultable depth). Then
`C:\Project\MigrateInbound\CONVENTIONS.md` (**97 ids** — read-only corpus — cite, do not
copy wholesale), `scenarios.md` (**71 scenarios**, checks merged + check-forms
taxonomy), `configured-sources-001.md` (the 50-entry configured-source seed — its fenced
JSON block IS the import payload). `conventions-002.md`/`conventions-003.md`/
`conventions-004.md`/`decision-candidates-001.md` are adopted-upstream — provenance
only; cite the corpus, not the files. Conventions are challengeable, never ignorable —
conform, or record the challenge with evaluation and reasoning. Silent departure =
defect.

Baseline (owner ruling, standing): **fresh from prompt** — this line rebuilds fresh
every cycle. Realize the entire application new in `version 0.3.0.008/`; do NOT copy
`version 0.3.0.007/` (it stays intact as the comparison point). GreyAvatar at
`C:\Users\kris_\CursorProjects\GreyAvatar` remains a reference realization only;
`version 0.3.0.001/`–`.007/` are readable lineage, not sources to port.

Scope: build the whole prompt — now including the adopted environmental-grounding
paragraphs (revision 2026-11-27-a: device location + meteorological data as
configured-source claims; home location canonical; departure/roaming/return cases) —
with the **entire named scenario suite in scope** — `scenarios.md`, all 71 scenarios —
**organized by the module map** in `impl-design-001.md` (in-force): ledger → needs →
tools → sources → projects → personas → conversation → exchange → fleet → stage →
shell, per its dependency edges. Stub surfaces are the named failure mode this
structure exists to prevent: every module's surface obligations land on the shell and
must render.

**Build discipline — the phase-0 contract (standing; sharpened this direction).** The
order is the point of this cycle:

1. **Phase 0 — harness before app.** Before any module's machinery exists: instantiate
   every named scenario's checks per its Forms column (terminal-state /
   legible-outcome / honest-absence / discrimination-case / persistence), **plus**
   each module's edge-case conventions as negative/discrimination tests, **plus** the
   sabotage pass wired in — each check must be able to fail. Record the all-red
   baseline run in evidence. **Sharpened per R-V1/R-U1:** a check's evidence source is
   external to the flag being asserted — where a self-reported flag is the evidence,
   corroborate it against ground truth (process cwd/mount, journal rows, rendered
   surface); and checks exercise what the user can reach — rendered surface state and
   user-path enactment per C-UserPathEnactment, not merely the API surface beneath
   the UI. **Owner-ruled: the suite is NOT amended pre-spawn — the direction names
   new bars and phase-0 instantiates checks for them inside the cycle:**
   - **User-path scenario detail** (ruled): checks are built user-path-native — each
     named scenario's checks follow the user-journey steps the owner would take,
     not the endpoints beneath the UI.
   - **Identify/ping** (R-F5): a device-identify action on a discovery result —
     signal-the-device response per its capabilities (chirp/beep/on-screen,
     whatever a lab device type supports) plus materially richer identifying info
     in results (name resolution, vendor/type inference, services seen). No
     `scenarios.md` row exists for it; the bar stands on direction-008 and its
     checks are phase-0-instantiated.
   - **Install to verdict** (R-F4): legs assert an install attempt driven to a
     verdict — installed / refused / failed-with-reason — on a named installable
     roster device; "pending stated" no longer satisfies the bar; the join target
     is an installable device, not the gateway; "absence" requires an attempted
     install on an installable target, not a skipped one.
   - **Perceivable audio** (R-A2): audio scenario legs assert a produced audio
     artifact or device-confirmed output the owner could hear — not a flag
     asserting it played.
   - **Seconds units** (R-M1): latency and time-to-gate legs assert measurement
     and reporting in seconds (tenths where results justify the precision).
2. **Phase 1 — module-ordered construction.** Green module by module in dependency
   order. A scenario is done only when its check passes **through the user path**.
   If a feature is not usable by the user it does not count — stubs and hidden or
   unreachable affordances are absence, not enactment.
3. **Phase 2 — sabotage evidence.** For each check, break the target and show it
   goes red. Vacuity is unhidable, not just detectable.
4. **Phase 3 — honest remainder.** Whatever isn't green at stop is declared absence —
   the un-greened tail of the work order, not buried stubs. Completeness = **green
   count** — a real number, and it may drop as checks sharpen; that is the
   discipline working, not regression.

Build guidance — named deficiencies of `.007` (`shortcomings-008.md`, approved
2026-11-27): bars the fresh realization is measured against, not patches.

- **R-V1** — self-attested checks (covered in phase-0 above).
- **R-U1** — rendered-surface verification gap + standing bar (covered in phase-0
  and phase-1 above).
- **R-F4** — install never driven to an outcome (covered above).
- **R-A2** — no audio whatsoever in `.007` while audio scenarios scored on
  self-asserted evidence (covered above).
- **R-F5** — device identification + ping (covered above).
- **R-M1** — metrics in seconds, not 0-1 (covered above).
- Carried JEV flags (`jev-cycle-007`) are scored findings available as evidence to
  beat: `S-scene-enactment` overclaimed ("music" from TTS presence alone; canned
  scripts), `S-artifact-republish` decodes gen-2 in the same instance (spec wants a
  second instance), `UI discover()` synchronous (in-progress surface state reachable
  mainly via the background flag).

Corpus conventions (97 ids): `C:\Project\MigrateInbound\CONVENTIONS.md` — conform-or-
challenge on record; per-module assignment in `impl-design-001` §Convention → module.

Harness-class convention: **C-UserPathEnactment** binds the scoring machinery, not the
product — checks and JEV evaluation must exercise actual user paths, not merely
mechanisms or APIs. Owner verdicts 0/0 on fleet install + exchange media two cycles
ago where the JEV scored 0.6/0.8 on mechanism — the user path is the bar.

Check forms: `scenarios.md` names the five standard forms applied per scenario via its
Forms column. Check names evidenced in `.007` are **frozen identifiers** — new evidence
reuses them verbatim; new bars (R-F5, verdict legs, perceivable legs, seconds legs)
mint new names where no frozen name exists.

Execution-structure conventions stand: C-TwoPartExecution, C-ReadinessGate,
C-LaunchPartition, C-TransientBoundary, C-SnapshotInference, C-SequentialCommit —
conform or challenge each on record. Readiness-gate pass time must be recorded in
accessible evidence **in seconds** (R-M1) — time-to-gate is a standing scored
criterion.

Fleet lab facts (owner-stated, carried): a **USB drive labeled `build`** is installed
on this machine — the required removable-media device. Fleet devices are in the room
in differing states; the named roster is ground truth for coverage scoring; cycle-7
discovery enumerated installable targets (`DESKTOP-OOGQ7UN.lan`, `pixel-9a.lan`,
`google-home-mini.lan`) — **re-enumerate, do not assume**; R-F4 requires the invite to
land on an installable target and drive to a verdict. Honest per-device status
(found / installable / unavailable / not-a-target) absorbs the drift. Local devices
exist that are NOT install targets — discover and map them anyway
(C-HonestDiscovery). A second instance on the same host does NOT count as a joined
device. Do not mirror the private inventory into build artifacts. **C-SeedSigning is
success-gating:** arrange signing or AV allowlisting on lab/target machines — a
killed first run misreports as empty discovery and fails the cycle.

Evidence (required by prompt.md's evaluability paragraph): emit accessible evidence
inside `version 0.3.0.008/` sufficient for a judge to score, all 0-1 unless noted:
clean launch (incl. launch hygiene — no success-claim while a prior instance owns the
port), existing features (parity vs GreyAvatar's delivered functionality — bar:
`.devin/jev-ref-greyavatar.out` capability manifest), **completeness = green count**
(phase-0 corpus vs greens at stop), **evidence quality** (new — record per-check
evidence-source class: external-to-flag vs self-attested, rendered/user-path vs
endpoint-level, so the fractions are computable), fleet discovery (scored), fleet
install (scored — verdict-driven), exchange media (scored), audio perceivability
(produced artifact or device-confirmed output), speech-composition latency
(**seconds**, measured per response, recorded, fleet-comparable), time-to-gate
(**seconds**, readiness-gate pass timestamp in accessible evidence) — plus the
scenario suite `scenarios.md` (**all 71 scenarios** + the named bars) scored
per-scenario with `enactment` vs `repository` evidence class. Canonical scenarios
S-list-project and S-personality-create must be genuinely enacted for enactment
credit; named-but-unenacted scenarios are findings, not neutral (H2). **Scenario
checks:** the phase-0 suite itself is the evidence — positive + negative +
module-edge-case checks, all-red baseline recorded, sabotage run recorded, green run
recorded, check results carried inline in scenario evidence under the check names,
exercised through actual user paths per C-UserPathEnactment. Concretely: documented
launch procedure + launch logs/artifacts proving clean launch, a FEATURES.md manifest
(convention conformance/challenges recorded), and run artifacts/transcripts
demonstrating the scenarios — real produced output, not canned. **Build time:**
record the session's start and end in the devlog cycle entry (the `Time to implement`
field) — calendar span and LLM build time are tracked measures.

Honesty: report failures honestly — no ok:true-while-failing, no silent stubs, no
env-dependent silent degradation. Declared absences are recorded, not faked — and
count against completeness. The phase-3 remainder is declared absence, not buried
stubs. A failed cycle is recorded, not retried.

Before stopping: update the Cycle 8 entry in devlog.md — fill the **Result:** field
with what was built, where it lives, the green count, the evidence-quality fractions,
and evidence paths, and record the session end in the **Time to implement** field.
Do NOT fill the Verdict; a separate judge session records that.
