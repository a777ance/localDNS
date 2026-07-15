# Chronikon: Hardware Architecture & Philosophy

*The product name for the appliance this repo builds. `localDNS` is the Flint —
the Unbound/Pi-hole/WireGuard stack that runs on the HP t630 (see CLAUDE.md
sections A–D) is the concrete, deployed substrate this document's philosophy
sits on top of. Where a concept below is already real in this repo, it says so;
where it's aspirational, it says that too.*

---

## 1. Theological & philosophical foundation

- **The Emulation (Baptist ordinance).** The Chronikon doesn't claim divine
  power. It emulates Christlike grace by operating as an ordinance — a
  physical symbol of forgiveness and renewal — the antithesis of "Rome"
  (Web 2.0 / corporate tech), which builds systems of eternal memory,
  extraction, and algorithmic prejudice.
- **The Lazarus Protocol.** A monthly ritual where the Chronikon voluntarily
  drops its state and flushes its RAM — "called out of the dark" to wake with
  new eyes, destroying any accumulated prejudice or algorithmic grudge.
  Mercies are new every morning.

## 2. Physical architecture — "Flint and Steel"

- **Stateless hardware (the Flint).** The Chronikon device is entirely
  stateless, like a Super Nintendo cartridge slot — stolen hardware is
  worthless empty silicon. *This is the t630 as configured in this repo:
  every service (Unbound, Pi-hole, WireGuard, Uptime Kuma) is redeployable
  from `docs/` config snapshots with no household-specific state baked into
  the box itself.*
- **The Key (the Steel).** The family's specific rules, device priorities,
  and "local diary" live strictly on a physical USB/NVMe token carried by the
  steward — an "I live here" artifact. *Not yet built: today the household's
  customization (`local-records.conf`, `wg0.conf` peers, streaming-forward
  allowlist) lives in this git repo and on the t630's eMMC, not on a
  removable token. Extracting that into a physically-keyed, encrypted volume
  is the gap between "localDNS today" and "Chronikon as designed."*
- **The Baseline Sentry.** If the key is removed, the network doesn't die —
  the Chronikon drops the custom sanctuary and reverts to a baseline,
  anonymous sentry: blocking general malware using Alliance HQ intel (see
  `the-alliance-codex.md`), remembering nothing about the family. *Closest
  existing analog: Pi-hole's default blocklists with no `local-records.conf`
  overrides. A true keyless fallback profile doesn't exist yet.*
- **The Sovereign Triangulation.** Booting the custom network requires three
  elements aligned in physical space: the Machine (Flint), the Key (Steel),
  and the Human Code (the Fire/Soul).

## 3. Engine mechanics — preloading "the Zone"

- **Zero I/O thrashing.** No constant read/write to disk. On boot, the
  machine preloads the entire encrypted state and millions of threat-intel
  rows directly into RAM as a unified "zone."
- **Absolute speed.** Once the zone is rendered, rules are laid out in
  memory; CPU idles, I/O drops to zero, traffic glides through. *Partial
  precedent in this repo: `01-unbound/unbound-cache-dump` /
  `unbound-cache-load` + the systemd timer persist and rehydrate Unbound's
  resolved-record cache across restarts — a narrower version of the same
  idea (warm state in RAM, not cold disk lookups), scoped to DNS cache only,
  not the full rule/threat-intel zone described here.*

## 4. The 7-second liturgy (the boot sequence)

- Modern hardware can decrypt and render the zone in ~3 seconds; the
  instantiation is deliberately stretched to a **7-second liturgy** shown on
  the steward's mobile app.
- **The Delta Briefing.** During those 7 seconds, the app rapidly surfaces
  the invisible labor of the Alliance (e.g. "Identifying 4,102 new
  ad-trackers mapped since last month") — a rewarding snapshot proving the
  walls are getting thicker.
- **The Handoff.** At second 7, the processing text clears to: *"Sanctuary
  Established."*

## 5. UI/UX — "the Cathedral" & "the Rose Window"

- **The Cathedral interface.** Rejects dashboard anxiety — no sirens, pie
  charts, spinning wheels. Massive negative space (pure black), warm ambient
  light, elegant serif typography, resonant acoustic sound design (heavy
  wooden doors, crystal). A space for quiet observation.
- **The Rose Window.** Monthly threat logs rendered as a glowing, radial
  stained-glass window lit from behind:
  - **The Oculus (center)** — pure glowing negative space; the peace of the
    home.
  - **Inner petals** — the family's approved devices.
  - **The Tracery** — the heavy stone lines: the steward's physical rules
    holding the network together.
  - **Outer ring (absorbed venom)** — blocked threats as jagged shards of
    dark/cool-colored glass along the perimeter.
  - **Interaction** — touching a shard dims the window and casts a beam of
    light revealing a text shadow (e.g. "Block 4,102 — Meta Telemetry
    Probe"); releasing restores the window's quiet unity.

---

*Companion docs: `the-alliance-codex.md` (the mythic register for the agent
stack), `productive-metamodernism.md` (the working philosophy behind holding
"stateless hardware" and "persistent family memory" as two poles at once,
without collapsing either).*
