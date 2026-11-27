# Prompt amendments 002 — environmental grounding (weather + location)
<!-- harness-doc kind=amendments status=adopted-upstream since=2026-11-27 applies-to=prompt mapped-into=ProjectPrompt.md -->

Drafted by the coordinator session 2026-11-26 from owner direction:
"we have a lot of 'environmental awareness' specified — add meteorological
data and device location so the app is more temporally grounded and aware."
Owner edits and rules; adoption goes through `C:\Project`'s revision
process — nothing here touches the corpus until then.

## Motivation

- The prompt already specifies calendar/temporal sources (§Projects and
  temporal context), background attention, and recency-grounded confidence —
  but names no meteorological input and no spatial grounding. An
  installation that knows weather but not *where it is* — or time but not
  conditions — is thinly situated.
- Cycle-7 evidence (shortcomings-007 R-I1): the improv-restraint failure was
  a weather question — "what type of weather do you like?" drew refusal.
  Real meteorological data + location gives improv truthful material to
  stand on and gives truthfulness something to protect.

## Proposed amendment text

Extend §Projects and temporal context (or a sibling paragraph — owner
placement):

> The installation grounds itself in place and time. Device location — the
> physical placement of hosts, surfaces, and joined fleet members — is
> recorded in the ledger as attributed assertions, derived from configured
> values, discovered platform or network signals, or user statement;
> uncertainty and staleness are recorded, not smoothed over. Environmental
> data such as meteorological conditions enter through configured sources
> like other outside information: the admission gate applies, and results
> are claims carrying provenance, confidence, and freshness. Personalities
> may draw on location and environmental data as ordinary grounding for
> responses, planning, and background attention — an opinion about weather
> may be backed by observed local conditions where known, and marked by
> register where it is improv.

Fleet consequence (same paragraph or §Fleet-adjacent — owner-narrowed
2026-11-26: not a WAN application): the installation's home location is
canonical. A user may take a device out of the home location and return it —
while away, that device's environmental claims refer to *its* current
location where known (staleness recorded, not hidden); on return they
re-converge on the home site. The interesting cases are departure, roaming
uncertainty, and return — not multi-site federation.

## Rationale-fit notes

- Consistent with §Confidence: location/weather are sourced claims, not
  truth — confidence, provenance, freshness govern their use.
- Consistent with §Background attention: weather change against location is
  natural off-channel work (storm approaching → relevant opportunity).
- Consistent with the source-admission gate (owner ruling 2026-11-25):
  meteorological sources are candidate configured sources, screened like
  any other.

## Open rulings for the owner

1. **Source kind** — does meteorological data arrive as a new configured-
   source kind (e.g. `telemetry`/`environment`) in the seed schema, or as
   ordinary `reference` sources?
2. **Location sensitivity** — device location is personal data; confirm it
   stays ledger-local like other claims (no default reporting anywhere —
   presumably yes given the local-first posture).
3. **Suite additions** — candidate scenarios once adopted: persona answers
   a weather question with source-backed local claims; installation states
   its home location honestly incl. staleness; a device taken off-site
   reports its *current* location's conditions (or declares staleness) and
   re-converges on return.
