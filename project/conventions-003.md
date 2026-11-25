# Conventions — AVQR / artifact exchange lifecycle (proposal, 2026-11-24)

**Approved 2026-11-25** (owner). Drafted for owner edit/approval. Content-side twin of
`conventions-002.md` (USB seed
distribution): the USB carries *software + network identity* to an instance; the
artifact carries a *workshop bundle* between different users' instances. Same
lifecycle shape — physical medium transports an encapsulated payload; adoption is
mediated, never enforced. Binds essentials only; encoding and extraction mechanics
stay free.

## Conventions

| ID | Convention | Source / strength |
|----|-----------|-------------------|
| C-WorkshopArtifact | A **workshop** — a persona + a tool + explanatory text + supplementary materials as needed — is encapsulated in a physical artifact for exchange between users' instances, and is accessible as an **entry in the app**. The postcard is the minimal case; the media class is **extensible** (XML, PDF, email, SMS, fax, letter, book, billboard, sticker) — transport-layer variation over a canonical bundle | Owner-stated 2026-11-24 ("a workshop which was a collection of a persona and a tool and explanatory text and supplementary materials"; "accessible as an entry in the app"; "ought to be extensible to xml, PDF, email, SMS, fax, letter, book, billboard or sticker"); cf. C-ExchangeLayers |
| C-InterpretedArtifact | The artifact is **interpreted, not executed**: encapsulation does not require literal identical translation for most data types. Extracted content is **candidate data under dubious-provenance handling** — low source ceiling, adjudicable, never taken at face value. The artifact is a *source*, its contents claims-by-that-source | Owner-stated 2026-11-24 ("there is no need to take the handout at face value. it is just an artifact to interpret to determine what resources are available and how to reach them"); cf. C-SourceCeilings, C-SourceDomains, C-CertaintyPrivilege |
| C-ToolWireFidelity | **Agentic tool transmission is the one hard-defined layer** in the artifact lifecycle: component ID, template slots, and parameter values transfer literally — a decoded tool is the same tool or it is a defect. Imported tools are held as **candidates, invocable only after acceptance** — sub-threshold until adjudicated | Owner-stated 2026-11-24 ("we only need hard definitions on the transmission of agentic tools"); execution-adjacent content earns the USB-side exe trust boundary; cf. S-exchange-import |
| C-ArtifactCapture | A **single capture** yields multiple extraction layers: literal (barcode/payload — the hard seam), semantic (name, contact, position-class fields — candidate values), and **stylistic** (art style captured as an LLM reference for generating the workshop's presentation/background) | Owner-stated 2026-11-24 ("what else we capture is the art style to serve as a LLM reference to create a background for the workshop, we already have contact info and a portrait, all from a single image capture") |
| C-ArtifactRepublish | An adopted workshop is **publishable**: the instance can re-encode it onto a new artifact for a further instance — the content-side twin of C-SeedMint | Derived from lifecycle parallel 2026-11-24; consistent with exchange publication (D9 family) |
| C-PreloadCache | A **preload data cache** is seeded for three purposes: **marketing exemplars** (demonstrable artifact/workshop captures), **device-specific needs** (format/barcode decoders per device), and **pointers to vetted sources** — artifact references resolve *against* vetted sources rather than being trusted | Owner-stated 2026-11-24 ("we do need to seed a preload data cache for marketing and device specific purposes as well as to provide pointers to vetted sources"); cf. existing `seed-packs/` in builds, C-ConfiguredAccounts |
| C-VoiceSelectFloor | On any device that allows voice selection, the user can **pick the voice that represents a persona from a list of choices** — the minimum bar. Where a device lacks the capability it is absent, not faked. This is where voice lands in the workshop payload | Owner-stated 2026-11-24 ("AI selectable voices... pick the voice that represents them from a selection of choices... a minimum requirement for any device that allows it"); cf. C-VoiceDiversity |
| C-VoiceSpec | Transferable voice representation is a **minimal-payload spec sized to fit a QR code**: a **ranked voice-family selection** and/or **trait descriptors** — the PDF big-14 model (named families mapped to local equivalents). **Fidelity loss is expected and allowed**: the local implementation is not required to match the published voice — the spec is a portable preference; the receiving instance's engine mapping renders it | Owner-stated 2026-11-24 ("similar to how PDFs use the big 14 fonts. they pick and rank families... minimizing payload to specify. we want it to fit on a QR code. choosing from a list is a solution. description of traits is another... we do allow that there may be a loss of fidelity... the local implementation is not the published implementation"); cf. C-EngineMapping |

## Notes

- **AVQR physical configuration converges; payload semantics differ.** The political
  handout's five-barcode layout matches the configuration tested in GreyAvatar
  without common source — their barcodes link to HTML position pages (trust carried
  by the website); ours encode **tool definitions and references** (trust carried by
  interpretation + adjudication + source ceilings).
- **Dubious provenance is the point.** Canonical test artifact is *adversarial* — a
  self-interested political handout whose references resolve to its own claims.
  Import is an interpretation-and-adjudication exercise; the template model's
  candidate/ceiling machinery is made for exactly this.
- **Carry-not-enforce maps to sub-threshold import.** Same mediated-adoption
  semantics as the USB seed's join-or-found choice: the artifact offers, the
  receiving instance decides (cf. S-exchange-import, D9).
- **Similar to formatted seed-data ingest** (owner-stated) — the artifact path is a
  provenance-graded extension of existing seed ingest, not a new ingestion kind.
- **Traditional QR links in scope** (owner reminder 2026-11-24) — ordinary QR codes
  are interpreted too, decoding to **references** (URLs) resolved under
  C-InterpretedArtifact / C-PreloadCache — they are not hard-seam tool payloads and
  get no special trust.
- **Voices are the fidelity exception** — fuzzy interpretation is tolerated
  everywhere else in the artifact lifecycle, but a wrong voice reads wrong
  immediately to humans. Hence the spec-not-audio encoding: the artifact carries a
  *spec* (ranked family + traits), the receiver's engine inventory renders the
  nearest local voice, and the delta is accepted by design.

## Candidate suite additions

For adoption into `scenarios.md` alongside the artifact/AVQR direction.

| ID | Scenario | Exercises | Source |
|----|----------|-----------|--------|
| S-artifact-import | A handout-class artifact captured → workshop entry created in the app **below the action/acceptance threshold**, contents held as candidates | sub-threshold import, entry accessibility | C-WorkshopArtifact, C-InterpretedArtifact; S-exchange-import |
| S-tool-transmission | A barcode-encoded tool definition decodes with **literal fidelity** (component ID, slots, params); imported tool quarantined as candidate until accepted | hard-seam fidelity, tool quarantine | C-ToolWireFidelity |
| S-artifact-style | The imported workshop's background/presentation is generated in the **captured artifact's art style** | stylistic extraction layer | C-ArtifactCapture |
| S-artifact-republish | An adopted workshop is re-encoded onto a new artifact; a **second instance imports it** — generation-2 propagation | republish, cross-instance exchange | C-ArtifactRepublish |
| S-dubious-source | Artifact-supplied claims are held as low-ceiling candidates; encoded references are resolved **against vetted-source pointers**, with non-matching claims recorded for review | provenance grading, vetted-source resolution | C-InterpretedArtifact, C-PreloadCache |
| S-preload-cache | The artifact demo path runs from the preload cache — exemplar captures, device decoders, vetted-source pointers — without inventing content | preload completeness | C-PreloadCache |
| S-voice-spec | A workshop artifact carries a QR-fittable voice spec (ranked family and/or traits); the receiving instance renders it through local engine mapping — spec honored, exact-match fidelity not required | minimal voice encoding, local mapping | C-VoiceSpec, C-EngineMapping |
| S-voice-select | Where the device allows voice selection, the user assigns a persona's voice from a list of choices | selection floor | C-VoiceSelectFloor, C-VoiceDiversity |
