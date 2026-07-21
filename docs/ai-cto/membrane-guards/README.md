# Membrane guards — nftables + DNS choke for B and D

**MEMBRANE DESIGN — not the live t630.** Deployable configs for the two guard
heads. Pairs with the C brain (`../c-brain/`): D's deny-log is the signal C
triages; C's approved allowlist updates feed back into D's `@allow4` set and the
DNS choke. Implements `../membrane-node-architecture.md`.

## Data path

```
internet ── B (NAT, ingress-deny) ══ D (egress default-deny, DNS choke) ── LAN
```

- **B — ingress head** (internet-facing): NAT/masquerade + default-deny inbound;
  trusts what D forwards. → `B-ingress.nft`
- **D — egress head** (LAN-facing): default-deny egress (allowlisted dest IPs
  only), logs every denied attempt, and is the LAN's DNS resolver. →
  `D-egress.nft`, `dns-choke.conf`

## Deploy

```bash
# 1. set the interface names at the top of each .nft (WAN_IF / LAN_IF / LINK_IF)
# 2. enable routing (persist under /etc/sysctl.d/)
sudo sysctl -w net.ipv4.ip_forward=1
# 3. load the rulesets
sudo nft -f B-ingress.nft        # on B
sudo nft -f D-egress.nft         # on D
# 4. DNS choke on D
sudo cp dns-choke.conf /etc/unbound/unbound.conf.d/ && sudo systemctl restart unbound
```

Persist nftables: `sudo nft list ruleset > /etc/nftables.conf` +
`sudo systemctl enable nftables`.

## The allowlist (the ongoing work)

Two allowlists, kept in sync:
- **DNS** (`dns-choke.conf`): which domains may *resolve*. Deny-by-default; one
  `transparent` zone per allowed domain.
- **Egress IPs** (`@allow4` in `D-egress.nft`): which destination IPs may be
  *reached*. Populate out of band — resolve the allowlisted domains, add their IPs
  with a timeout (CDN IPs rotate), same pattern as the repo's `populate_sets.py`.

Start in **learning mode**: change D's final egress rule to log-but-`accept` for a
week, harvest what your devices actually reach, seed both allowlists, then flip it
back to `drop`. That bounded week is the only way default-deny egress becomes
livable — and it's exactly the corpus the C brain is built to triage.

## Where the C brain plugs in

**D's `egress-deny` log → C.** Each denied attempt is a task: "device X wanted Y —
allow?" C triages (local, or escalates hard/non-sensitive ones to the oracle),
proposes an allowlist diff, **G approves**, and the diff lands as new `transparent`
zones + `@allow4` entries. Deterministic apply (F); never let the brain edit the
live ruleset directly.

## Not covered here — add per your needs

- **IPv6 egress.** These rulesets police IPv4 (`@allow4`). Open IPv6 egress would
  bypass the whole allowlist — add an `@allow6` set + `ip6 daddr` rules, or disable
  IPv6 egress entirely.
- **WireGuard.** If it terminates on D, add a DNAT on B (`51820/udp → D`) plus an
  allow rule. Left out of the base config on purpose.
- **Defense-in-depth.** B currently trusts D's egress filtering. For belt-and-
  braces, mirror the `@allow4` check on B's forward chain too.
