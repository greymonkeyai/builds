# Direction 004 — SIGNED 2026-11-23
<!-- harness-doc kind=direction status=discharged applies-to=cycle-4 -->

Drafted by the coordinator session from the owner's Cycle-3 review
(`devlog.md` 2026-11-23: existing features 0.4, completeness 0.5, user score
0.5; findings R1–R5) and the JEV Cycle-3 flags (J1–J4). Signed by owner
2026-11-23 with the rulings recorded below.

**Owner rulings 2026-11-23:** no modify-and-measure — this line rebuilds
**fresh from prompt every cycle until the owner says stop.** Findings from
Cycle 3 are not patches to `.003`; they inform how the next build is built
better — the guidance below and the suite that scores it. **Fleet discovery
remains deferred** (owner ruling 2026-11-23): fleet onboarding/
capability-discovery stays a declared absence alongside fleet install.

- **Region / variable:** Fresh realization of `prompt.md`, built better
  than `.003`. Build guidance for the next realization (from
  `shortcomings-004.md`):
  - **G-A** Build live owner-facing controls, not mechanism-only
    affordances — a control that exists must work through the control
    itself. (Cycle-3 lesson: the style selector scored 0.9 on
    assertion-level evidence while the UI control did nothing.)
  - **G-B** Build persona voices as register constraints on truthful
    output — characterization must never trade away factual accuracy.
    **Bar approved by owner 2026-11-23:** persona answers preserve the
    factual content of their sources; unsupported claims flagged or
    withheld, not invented.
  - **G-C** Build confidence as a relation — held *by* a party *about* a
    claimant/claim — not a bare scalar. **SKIPPABLE this run** (owner
    ruling 2026-11-23): remains draft guidance; the build may or may not
    realize a dyadic confidence model this cycle — not a required bar.
    Shape on record for whenever it is built: under the dyadic ranking
    system, new personalities start at **0.5** held-confidence by
    default.
  - **G-D** Build the Library as a library — browsable, inspectable
    holdings (personas, tools, packages, artifacts), not a log view.
  - **G-E** Build the roster as an operable control — select the active
    personality, reorder entries; every shipped persona reachable.
  - **G-F** Build clean evidence — no double-seeded rosters, populated
    fields (`playbackMs` or no claim), two adequate competing tools,
    scenario files carrying their check results inline.
  - **Suite amendments (adopted 2026-11-23):** tightened S-color-schemes,
    extended S-personality-roster (selection + reorder legs; coordinator
    recommendation taken under silence=agreement), new S-library-browse,
    new S-faithful-voice — per `shortcomings-004.md` §C. The suite is the
    enforcement surface for G-A through G-E; amended suite = 26 scenarios.
- **Baseline:** **fresh from prompt** (owner ruling 2026-11-23). Produce
  `version 0.3.0.004/` as a new realization; `.003` kept intact as
  comparison point.
- **Cycle budget:** 1 — this direction signs a single cycle (owner
  "next single harness run", 2026-11-23). Repeated fresh builds each get
  their own direction unless the owner rules a standing direction.
- **Approaches:** 1 per cycle
- **Criteria to log:**
  - clean launch (incl. launch hygiene)
  - existing features — parity vs GreyAvatar manifest
  - completeness — fleet install, fleet discovery, and exchange media
    count against it
  - fleet install — expected 0 (discovery deferred with it, 2026-11-23)
  - exchange media — expected 0
  - user score — owner-scored at review
  - time-to-gate — standing
  - scenario suite — `.devin/scenarios.md` as amended (26 scenarios);
    canonicals must enact
  - time to implement — tracked, not scored
- **Review at:** end of this cycle — owner scores, ranks across the
  line's candidates
