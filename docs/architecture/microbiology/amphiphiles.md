# Amphiphiles — what is dual-soluble in a network?

> **The question.** If our system is the fatty, hydrophobic phase bridging a hydrophilic
> internet, how are we to understand the molecules that dissolve in *both* — alpha-lipoic
> acid, CoQ10, ascorbyl palmitate, liposomal glutathione? What is their network analog,
> and what do they tell us to build?

**The short answer.** An amphiphile is a thing that is **legible in both phases at
once** — a polar head the water can address, a nonpolar tail that lives in the fat. Its
defining property is not that it is permitted through the boundary. It is that **it does
not need a door.** It partitions in by solubility alone. So in our stack, the amphiphiles
are every mechanism that crosses or inhabits the t630 *without transiting a rule* — and
that is a category we have never enumerated. This entry enumerates it.

Four patterns follow, one per molecule, plus a fifth the list implies.

---

## 0. First, a correction to the framing

The prompt says "our system is the FATTY hydrophobic system." Nearly right, and the
inaccuracy is productive.

The t630 is not a *body* of fat. It is a **bilayer** — in the cell, two molecules thick,
a phase boundary rather than a compartment. It has almost no volume. Everything with
volume in this picture is water: the internet on one side, the LAN on the other.

This matters because it changes what "living in the membrane" means. There is very little
room in there. A molecule that resides in the bilayer is in a **crowded, two-dimensional,
lateral world** — it cannot go far in the third dimension, but it diffuses sideways very
fast. That is not a limitation; it is the whole trick of pattern 1 below, and it is a
precise description of loopback.

> **Disanalogy, stated up front.** A real bilayer is passive and roughly symmetric; it
> excludes by physics, not by policy, and it has no idea what is crossing it. Our
> membrane is *active, asymmetric, and stateful* — it inspects, logs, decides, and
> distinguishes in from out. Where an argument here depends on the membrane being dumb,
> it is wrong about us. (Leaflet asymmetry recovers part of this — see
> [`permeability-and-gradients.md`](permeability-and-gradients.md).)

---

## 1. CoQ10 — the carrier that never leaves the membrane

**The biology.** Coenzyme Q10 is a quinone head on a 10-unit isoprenoid tail. The tail
anchors it so thoroughly in the hydrophobic core of the inner mitochondrial membrane that
it essentially never surfaces into either water. What it does instead is diffuse
*laterally*, ferrying electrons between respiratory complexes that are fixed in place and
cannot touch each other. It is also regenerative: reduced CoQ10 (ubiquinol) re-reduces
alpha-tocopherol, restoring an antioxidant that has already been spent.

**The mapping.** This is the **link with no address in either water.** Our clearest
instance is the Pi-hole → Unbound hop over `127.0.0.1#5335`. It exists only inside the
membrane. It is not on the LAN, not on the internet, and not reachable from either — and
it is precisely what lets two components that must not be directly exposed still be
coupled. Pi-hole is host-networked *so that* this lateral hop stays on loopback rather
than becoming a routable Docker DNAT path. Uptime Kuma is host-networked for the same
stated reason: to reach Unbound at `127.0.0.1:5335` directly.

The regenerative half maps too. `unbound-cache-dump` /
`unbound-cache-load` are membrane-resident: they spend nothing at the boundary, surface
to no network, and their job is to **restore a component that has been depleted** — the
warm cache after a restart. That is the ubiquinol-recycling-tocopherol move exactly.

> **Claim (checkable).** *Every high-value coupling in this stack should have an address
> in neither water.* An internal link that is reachable from the LAN is a membrane
> carrier that has dissolved out into the cytosol. Audit against the live box:
> `ss -ltnp` on the t630 — anything bound to `0.0.0.0` that only ever talks to another
> local process is a violation, and Unbound on `5335` is the one we already got right.

> **Opportunity.** We have no *stated* invariant for this, only instances. Candidate for
> promotion into `CLAUDE.md`: **loopback-only unless a second host needs it** — with the
> LiteLLM router (`4040`) and Open WebUI (`3000`) as the interesting test cases, since
> both are currently LAN-exposed and it is worth asking whether they need to be.

> **Confirmed, 2026-08-06 — the claim caught a live one on first pass.** Writing this
> entry turned up drift in `streaming-forward.conf`: its header described the Pi-hole →
> Unbound hop as `172.17.0.1#5335`, the **Docker bridge gateway**, when host-networked
> Pi-hole has reached Unbound on `127.0.0.1#5335` since the migration. That is precisely
> the failure this pattern predicts — a carrier documented as living out in the cytosol
> when it in fact lives in the membrane — and it is the same address whose real DNAT path
> once silently broke VPN-peer DNS. Comment corrected. Worth noting *how* it survived:
> `CLAUDE.md`, `network-context.md`, and `server.conf` all had it right, and the stale
> value sat in the one file that is itself the decision point.

---

## 2. Ascorbyl palmitate — the wrapper is not the cargo

**The biology.** Ascorbic acid is aggressively water-soluble and cannot cross a bilayer
on its own. Esterify it to palmitic acid and you get ascorbyl palmitate: a fat-soluble
prodrug that partitions into the membrane, crosses, and is then **cleaved by esterases**
back into plain vitamin C on the far side. The tail is transport, not payload.

**The mapping.** This is **encapsulation**, and WireGuard is the textbook case. LAN
traffic is water-soluble — it cannot survive the internet as itself. Bolt on a lipid tail
(the encrypted UDP/51820 wrapper), and it crosses a phase it could never cross naked. At
`wg0` the tail is cleaved and the original molecule is restored, unchanged. DNS-over-TLS
in `streaming-forward.conf` is the same pattern one layer down: the query is the
ascorbate, the TLS is the palmitate, and Cloudflare's resolver is the esterase.

**But the caveat is the valuable part.** Ascorbyl palmitate has a real failure mode:
the esterified form is *not* the active form. If cleavage does not happen, you have
delivered an inert molecule — and, worse, you have delivered it *successfully* by every
measure you were taking. Absorption looks fine. Nothing works.

> **Claim (retro-predicted, and it hit).** *A wrapper that arrives but is not stripped by
> something that can act on the payload is an unopened box counted as a delivery.* This
> stack has already been bitten by exactly this: VPN peers whose tunnel came up cleanly —
> handshake fine, traffic flowing — while their DNS was **not** actually reaching Pi-hole,
> because Docker DNAT sat in the path for queries sourced from `wg0`. Delivered, inert,
> and green on the dashboard. The fix was to remove the thing that prevented cleavage
> (host-network Pi-hole), not to improve delivery.
>
> The `::/0` IPv6 black hole is the same shape again: handshake succeeds, pages hang.

> **Opportunity — shipped 2026-08-06.** Our verification block checked that mechanisms
> were *up*, never that payloads were *cleaved*. `sudo wg show` proves the tail crossed;
> it proves nothing about the ascorbate. **The cleavage test** is now part of Phase 4 of
> [`docs/DEPLOY-PROTOCOL.md`](../../DEPLOY-PROTOCOL.md) — for every wrapper, name the
> thing that unwraps it and test from the far side — with the far-side `dig` added to
> `CLAUDE.md` § 2. The general form to carry into any new wrapper: *what would this look
> like if it arrived and nothing opened it?* Then check for exactly that.

---

## 3. Liposomal glutathione — admission by resemblance

**The biology.** Glutathione is water-soluble and *stays* water-soluble. The trick is not
to modify the molecule at all — it is to wrap it in a vesicle **made of the same material
as the membrane**. The liposome then either fuses with the membrane, delivering its
contents directly into the interior, or is taken up by endocytosis and remains wrapped in
a membrane-derived compartment. (Which one dominates is genuinely contested in the
literature; both happen, and the distinction is the useful part for us.) Note also *why*
the trick is needed: oral glutathione fails not because the membrane refuses it but
because the **gut destroys it in transit**.

**The mapping — and this is the entry's sharpest finding.** Fusion is **admission by
resemblance**: the boundary accepts the vesicle because it is made of boundary. Nothing
is inspected, because from the membrane's point of view nothing crossed — the two things
merged.

We do this four times. Pi-hole, Uptime Kuma, LiteLLM, and Open WebUI all run
`network_mode: host`. Each one is a liposome that has **already fused**. They did not
traverse B or D; they became the membrane's own network stack. Every reason for it is
good and documented — loopback access to Unbound, answering VPN peers over `wg0`, no
Docker DNAT in the path. That is not the point. The point is that we have never counted
them as a category, and they are the category that skipped inspection entirely.

The endocytosis contrast is exactly Docker's default bridge network: the vesicle comes
inside, but stays *wrapped* — its own namespace, its own address, a membrane between it
and the cytosol. Fusion is host networking; endocytosis is bridge networking. Stated that
way, `network_mode: host` reads as what it is — a deliberate, per-container decision to
give up a compartment, which deserves a line of justification each time.

The transit-medium note also earns its keep as a diagnostic split: **"the boundary
refused it" and "the medium digested it" look identical from the sender and have opposite
fixes.** ISP DNS interception, captive portals, and middleboxes are gut enzymes, not
closed doors.

> **Claim (checkable).** *Every `network_mode: host` in this repo is an un-inspected
> admission and should carry a written reason.* Checked at time of writing —
> `grep -rn "network_mode: host" --include=*.yml .` returns exactly four (Pi-hole,
> Uptime Kuma, LiteLLM, Open WebUI), and each compose file carries an inline comment
> justifying it. The claim holds today; it is worth re-running whenever a container is
> added, because the count only ever drifts upward.

> **Opportunity — shipped 2026-08-06.** The **fusion register** now lives in `CLAUDE.md`
> section B: one table naming every component that runs *as* the membrane rather than
> behind it, with its justification. The reasons already existed, scattered across four
> compose files as comments; the register's value is not the reasons but the **count** in
> one place, so that going from four to five is a visible event rather than a diff nobody
> reads. `tools/check-membrane.py` (FUSION) fails if the table and the compose files
> disagree in *either* direction — an unregistered fusion, or a stale entry, since a
> register nobody trusts is worse than none.

---

## 4. Alpha-lipoic acid — the one that works on both sides of the same reaction

**The biology.** ALA is the entry's origin and its oddest member: a genuinely small
molecule, soluble in both phases, that is both a cofactor bound into enzyme complexes and
a free-floating antioxidant, and that operates in aqueous cytosol and lipid membrane
without needing a carrier or a wrapper. It regenerates other antioxidants across the
phase boundary — the water-soluble and fat-soluble pools are not separate to it.

**The mapping.** ALA is the **cross-phase observer**: the mechanism that sees the same
event in both waters and can therefore reconcile them. In our stack the honest instance
is the query log — a DNS lookup is a fact that exists on the LAN side (which device
asked) *and* on the internet side (what was resolved, whether it left the box, whether it
went over DoT), and Pi-hole + Unbound together are the only place both halves are
visible. Nothing else in the stack sees both faces of the same event.

That is also the source of everything downstream: the monthly Statement is only possible
because one component holds both sides of the reaction.

> **Claim (speculative).** *Cross-phase visibility is scarcer than we treat it.* We
> currently have exactly one such observer, for one class of event (DNS). Bytes, sessions,
> and device identity are each visible on only one face. The nftables volume layer
> scaffolded in `docs/statements/tools/collect/` is an attempt to build a second one — and
> reading it this way says something useful about it: its value is not "we get gigabytes,"
> it is "we get a second event class where both faces are visible at once."

---

## 5. The pattern the list implies — detergents and the critical micelle concentration

Nobody asked about this one, and it may be the most operationally important thing in the
folder.

**The biology.** Every amphiphile is, at sufficient concentration, a **solubilizing
agent**. Below its critical micelle concentration (CMC), a detergent inserts into a
bilayer and the membrane holds. Above it, the detergent stops passing *through* the
membrane and starts dissolving it, breaking the bilayer into mixed micelles. The
transition is a threshold, not a slope — the same molecule, at a slightly higher
concentration, goes from passenger to solvent.

**The mapping.** Our amphiphiles are our tunnels and our shells: things that cross the
boundary by their own nature rather than by permission. One WireGuard peer is a channel.
Six peers — **three of them currently unidentified on the live box, with no recent
handshake** — is a boundary with enough lipid-soluble passages that it is worth asking
whether it is still a phase. That known issue has been open for a while and reads as
housekeeping. Under this frame it reads as *approaching CMC*, which is a different
priority.

The web terminals are the high-potency case: `ttyd` on 7681 and 7682 is a login shell over
HTTP, gated only by `--credential`. That is a very powerful amphiphile, and its CMC is
low — one is a tool, and the count should never casually rise.

> **Claim (checkable, and the most actionable in the folder).** *There is a critical
> concentration of amphiphiles past which the t630 stops functioning as a phase boundary,
> and it is a threshold rather than a gradual degradation.* Operationally: **count the
> amphiphiles and keep the number small and every one of them named.** Concretely —
> `sudo wg show` should list only peers we can name; every unnamed peer counts toward CMC
> and buys nothing.

> **Opportunity — shipped 2026-08-06.** "Identify or remove peers 10.8.0.4–.6" has moved
> out of Known-Issues-as-chore and into `tools/check-membrane.py` (CMC) as a *count*: the
> check is not "are these three still there," it is "is the amphiphile count still the
> number we intend, and can we name every one of them." A declared budget of 4 live peers
> sits in the script as a constant, so raising it is a deliberate act that shows up in a
> diff rather than a device someone added on a Tuesday. `CLAUDE.md` § 2 now says the same
> thing at `sudo wg show`.
>
> Note what the repo snapshot actually holds: **one** live `[Peer]` (the iPhone). The
> other five are commented placeholders, because real keys never live in git. So the CMC
> check passes here and cannot see the live box — the three unidentified peers exist on
> the t630. The repo-side check is the ratchet; the box-side count still needs an SSH
> session, and that is the honest limit of this control.

---

## Summary — the five patterns

| Pattern | Molecule | What crosses | Our instance | The risk it names |
| ------- | -------- | ------------ | ------------ | ----------------- |
| **Solvent** | detergent above CMC | the membrane itself dissolves | unnamed WG peers; extra `ttyd` shells | boundary stops being a phase — at a threshold |
| **Cross-phase observer** | alpha-lipoic acid | nothing — it sees both sides | Pi-hole + Unbound on one query | scarcity: we have exactly one |
| **Fusion** | liposome | the vesicle merges, uninspected | 4 × `network_mode: host` | admission by resemblance, never counted |
| **Wrapper** | ascorbyl palmitate | payload in a cleavable tail | WireGuard; DoT | delivered-but-inert, green on the dashboard |
| **Lateral carrier** | CoQ10 | nothing — it ferries within | `127.0.0.1#5335`; cache dump/load | dissolving a private link out into the LAN |

Read the table bottom-up and it is a story about **doors we did not build**: a carrier
that needs no door, a wrapper that makes its own, a vesicle that merges instead of
entering, an observer that stands in the doorway, and a solvent that removes the wall the
door was in.

---

## Disanalogies (the edges, kept on purpose)

- **Our membrane is active; a bilayer is not.** Physics excludes ions with no opinion
  about them. We inspect, decide, and log. Any argument above that leans on passivity is
  wrong about us.
- **A bilayer self-assembles and self-heals.** Puncture one and it closes, because the
  hydrophobic effect drives it. Our membrane does not self-heal — a hole stays open until
  a human closes it. This is the single biggest edge, and it is why the "just below CMC"
  intuition is *more* dangerous for us than for a cell: we get no restoring force.
- **Concentration is not really the variable.** Real CMC is a bulk thermodynamic
  threshold; our "count of tunnels" is a countable integer with no phase transition in any
  physical sense. The threshold intuition is a heuristic borrowed for its shape, not a
  measurement. Do not put a number on it and pretend it was derived.
- **Cells have no adversary that reads the textbook.** Diffusion does not adapt.
  Anything here framed as "an attacker would have to" is doing work the biology does not
  support.
