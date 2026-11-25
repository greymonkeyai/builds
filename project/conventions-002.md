# Conventions — USB seed distribution (proposal, 2026-11-24)

**Approved 2026-11-25** (owner). Drafted for owner edit/approval ahead of the
fleet-discovery direction. Covers the
removable-media installer lifecycle for the build line's distribution model.
**Binds essentials only** — transport, filesystem, signing method, and protocol
mechanics remain implementation choices unless a convention names them.

## Conventions

| ID | Convention | Source / strength |
|----|-----------|-------------------|
| C-UsbSeed | The installer distribution is a removable **USB drive** carrying a portable Windows executable that **runs in place from the media** — no installation required to start. **Ubiquity of commodity removable media is the maximized factor**: generic drives, standard filesystems, no special hardware or formatting. Required removable-media device for enactment: **USB drive, 4 GB** — lab provides a drive labeled `build` | Owner-stated 2026-11-24 ("choosing USB drive as an executable portable storage medium for our installer"; "ubiquity of removable media is the factor we are trying to maximize"; "required removable media device {USB drive 4 GB}") |
| C-SeedStagePath | Local staging destination is **`C:\builds-installed`** — media→host writes land at a predictable per-machine path | Owner-provided path 2026-11-24 |
| C-SeedLifecycle | The seed lifecycle binds these essentials in order: (1) execute in place from media; (2) stage to local disk **only when update is needed and allowed** — decline leaves the app running from media with no local write; (3) network discovery; (4) **user-mediated invites** — the user picks which discovered devices join; silent auto-join is a departure; (5) role negotiation per joined device; (6) capable target machines install the app. Mechanism and surface for each stage are free | Owner-stated 2026-11-24 lifecycle |
| C-SeedLog | The USB medium carries an **append-only local network log** — the seed doubles as a witness courier, accumulating network history across the machines it visits; the log is machine-readable and serves as evidence for test confirmation | Owner-stated 2026-11-24 ("writes a local network log on the usb"; internal-comms confirmation carried for test scenarios) |
| C-SeedMint | Capable installed nodes can **mint new USB installers** that **carry the founding network's identity as an adoptable offer** — self-propagating seed. The medium **carries but does not enforce**: first run on a new machine may join the carried network or found a new one — the choice is the user's. Mint capability is a negotiated role grant, not universal | Owner-stated 2026-11-24 ("target capable machines install the app with the capability of minting new USB installers"); owner ruling same day: carry-not-enforce ("they carry but do not enforce. meaning, you could start a new network.") |
| C-LocalTransports | Fleet discovery and comms prefer **local-network transports**: BT, NFC, the local WiFi node (SoftAP lineage — `GreySoftAP` used in GreyAvatar testing), and local LAN — among LAN, **wired preferred over wireless**. Mechanism within each transport is free | Owner-stated 2026-11-24 ("testing and preferring local network protocols such as BT NFC and the local wifi node we used before. Local LAN is perfectly fine, with wired preferred over wireless") |
| C-HonestDiscovery | Discovery is **broad and honest**: it records everything found, including non-fleet devices — no silent filtering. Discovery coverage is itself test data ("about the discovery as much as it is about the successful install"), and a **local network map** is a produced artifact maintained **alongside** the member network | Owner-stated 2026-11-24 ("discovery is broad and might hit other devices, this is part of the test and should be noted. a local network map is a good thing to have alongside our network") |
| C-SeedSigning | The seed lifecycle's shape — USB-resident self-staging executable plus LAN install push — is heuristically indistinguishable from worm propagation; Defender/SmartScreen will flag it. Builds **must arrange signing or documented AV allowlisting** on lab/target machines; the method is implementation choice, the constraint is conventional and **success-gating** — a killed first run misreports as "discovery found zero devices" and fails the cycle. Directions naming the fleet suite carry this warning | Owner-ruled 2026-11-25 ("it is a convention, they can be warned. success hinges on success") |

## Derived essentials (flagged for owner ruling)

- **Seed carries network identity — as offer, not mandate.** Resolved by owner ruling
  2026-11-24: identity material lives on the seed so a new machine *can* join the
  carried network, but adoption is user-mediated; founding a new network from the same
  medium is a legitimate choice, not a departure. Side benefit: one stick supports
  deliberate parallel/re-founded networks — regression-safe lab seeding.
- **USB self-refresh on revisit — left unbound (owner direction 2026-11-24).** The
  owner-stated staging check is directional (media→host); the inverse is not bound as
  a convention. Instead the stale-seed condition is folded into `S-usb-log-courier`'s
  precondition so the suite exercises it: whatever the build does on a stale-seed
  revisit (refresh, mint over, ignore) surfaces as evidence at review.

## Known constraint — hostile-heuristic shape

**Bound as `C-SeedSigning` 2026-11-25** — owner ruling: the constraint is a convention;
builds may be warned; cycle success hinges on it. Detail:

A USB-resident executable that self-stages to disk and pushes installs over LAN is
heuristically indistinguishable from worm propagation — Defender/SmartScreen will flag
it. Builds must arrange **signing or documented allowlisting** on lab/target machines.
The *method* (self-signed cert on lab hosts vs AV allowlist entries) is implementation
choice; the *constraint* is conventional. Unaddressed, the first run dies at the seed
and the failure presents confusingly as "discovery found zero devices."

## Fleet test roster (spec data — not a convention)

Intended test devices, drawn from `Meta Analysis/notes/hardware-inventory-on-hand.md`
and the GreyAvatar farm tests (wave 3, 2026-08). Devices are back in the room, plugged
in, and **in various states** — the roster lists intended targets; availability,
state, and user-attendance vary and **are themselves test data**, not test failures.
Roster keys on **names** — lab IPs are DHCP and have drifted between records (e.g.
RMT-93 recorded `.33` and `.41` in different months).

| Device | Bench name | Transport(s) | Expected role in test |
|--------|-----------|--------------|-----------------------|
| PC-DEV | this machine | Wired LAN | Likely seed/observer host |
| PC-RMATA-01 | `RMT-93` | Wired Ethernet | Fleet target — stable node (durable ledger home; installable — owner-confirmed 2026-11-24) |
| PC-RMATA-02 | `RMT-105` | Wired Ethernet | Fleet target — designated resettable/seed node |
| PC-GMK | `NUCBOX_G3_PRO` | Wired + WiFi + BT 5.2 (+dongle) | Fleet target; host-capable; SoftAP lineage |
| TAB-YOGA | — | WiFi | Surface-class (ARM) — discoverable; install may be N/A — the natural "found but not installable" case |
| Echo Dot(s) | — | BT / WiFi | Appliance-class — discoverable, not installable |
| Android phones ×2 | — | WiFi | Surface-class (Grey Mouth lineage — LAN or SoftAP pair) |
| Android / Fire tablets | — | WiFi | Surface/kiosk-class |
| PC-TERRY | Terryza T6 | Wired/WiFi | "Various states" datapoint — disk-repair/triage state |
| STICK-WIN | — | Wired/WiFi | Unknown state — triage discovery result |
| TAB-SURF | — | WiFi | Loaner (not project-owned) — availability and consent care required |
| RPI-01/02 | — | Wired/WiFi | Side devices — discoverable, not install targets |
| SPK-SONOS-01 | — | LAN | Appliance-class — discoverable, not installable |
| Expected non-fleet finds | — | various | Smart TVs, Xbox, Fire Sticks, smart plugs/bulbs, household phones — recorded on the map, never members |

## Candidate suite additions

For adoption into `.devin/scenarios.md` when a direction names the fleet suite.

| ID | Scenario | Exercises | Source |
|----|----------|-----------|--------|
| S-usb-seed-run | App launched by executing the installer directly from removable media; runs in place with no prior install; writes/extends the local network log on the same medium | portable execution, seed log | C-UsbSeed, C-SeedLog |
| S-usb-stage-consent | Staging to local disk occurs only when update is needed **and** permitted; declining leaves the app running from media with no local write | consent gate, update semantics | C-SeedLifecycle |
| S-fleet-invite | Discovery lists candidate devices; user selects which join; non-invited devices are not members | user-mediated join, no silent auto-join | C-SeedLifecycle |
| S-role-negotiate | Each joined device negotiates a role; role assignment is recorded and governs capabilities (incl. mint rights) | role negotiation, capability gating | C-SeedLifecycle, C-SeedMint |
| S-usb-mint-gen2 | An installed capable node writes a new USB installer; that medium boots a fresh machine which may join the **carried network identity** or found a new one — the choice is offered and the carried identity works when chosen | self-propagation, identity portability, join-or-found choice | C-SeedMint |
| S-usb-log-courier | USB revisited to a member carries accumulated network history; entries are machine-readable per-node evidence usable for test confirmation. Precondition: at least one revisit occurs with the seed's installer **stale relative to the member** — the build's handling of the stale seed (refresh, mint-over, ignore) is recorded evidence, not scored direction | witness courier, in-band confirmation carried physically, stale-seed revisit | C-SeedLog |
| S-fleet-roster | Discovery run against the named roster: each device reported with honest status (found / installable / unavailable / not-a-target). Coverage is scored; **install success is not required** — an unavailable or mid-triage device correctly reported is a pass | discovery breadth, honest status per device | C-HonestDiscovery; roster above |
| S-network-map | The build produces a local network map artifact covering discovered non-member devices alongside the member network | map artifact, member/non-member distinction | C-HonestDiscovery |
| S-local-transports | Discovery and join exercised over local transports per preference — wired LAN baseline plus at least one of BT / NFC / SoftAP-node where a device supports it | transport coverage, wired-over-wireless preference | C-LocalTransports |
| S-credential-surrender | A device joining a host's network consents to surrender credential management: its credential screen closes (status display may remain), secrets stay host-local, and the surrender is recorded as a claim on both books | consented surrender at join, host-only credential surface | `decision-candidates-001.md` §5 (host-sovereign credential screen); C-SeedLifecycle stage 4–5 |

Cross-link: the `C-SeedLifecycle` join flow (invite → role negotiation) is where the
host-sovereign credential surrender in `decision-candidates-001.md` §5 lands — the
consent point is the join act itself. `S-credential-surrender` above closes the suite
gap: no other candidate row exercises credential posture at join.
