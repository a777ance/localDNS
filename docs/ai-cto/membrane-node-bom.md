# Membrane Node — Bill of Materials & Cost

**Status:** Planning. Nothing purchased. Companion to `membrane-node-architecture.md`.

**Last updated:** 2026-07-19

Prices are US used-market, July 2026, and volatile — verify before buying. The two
membrane heads (A, B) are existing HP t630s and cost nothing; **the GPU is 55–70% of the
whole build**, so the real decision is which card, not which box.

---

## Inventory

| # | Component | Node | Own / Buy | Cost |
| - | --------- | ---- | --------- | ---- |
| 1 | HP t630 — ingress head | A | **owned** | $0 |
| 2 | HP t630 — egress head | B | **owned** | $0 |
| 3 | USB3 GbE NIC ×2 (each head needs a 2nd interface: WAN+link / link+LAN) | A, B | buy | ~$40 |
| 4 | Optical diode links — 4× (small display + webcam) pairs + blackout tubing | A↔C, B↔C | buy (DIY) | ~$180 |
| 5 | C host — used tower, 64 GB RAM, 2 TB NVMe, 750 W PSU | C | buy | ~$450–550 |
| 6 | Read-only germline SSD (separate device, mounted read-only) | C | buy | ~$30 |
| 7 | **GPU (the mitochondrion)** | C | buy | see tiers |
| 8 | Managed switch (only if you want VLAN segmentation) | — | optional | $0–40 |
| 9 | Cabling / mounts / misc | — | buy | ~$40 |

## GPU tiers (the real fork)

| VRAM | Card(s) | Runs | GPU cost | **Build total** |
| ---- | ------- | ---- | -------- | --------------- |
| **24 GB** (baseline) | 1× used RTX 3090 | 32B @ 4-bit | ~$1,050 | **~$1,800** |
| 48 GB (headroom) | 2× used RTX 3090 | 70B @ 4-bit | ~$2,100 | **~$3,000** |
| 48 GB (single, clean) | 1× RTX A6000 | 70B @ 4-bit | ~$3,500 (verify) | ~$4,300 |

96 GB single-card is datacenter territory ($10k+) — struck from the design; the workload
never asks for it.

## Recommendation

**Go 24 GB — ~$1,800 all-in.** C's workload (egress triage, deny-log reasoning, config
audit, plan transcription) is narrow; a single 32B model in one used RTX 3090 covers it.
48 GB is headroom for 70B, not a requirement — buy it only if you want the ceiling. This
supersedes the earlier "48–96 GB" figure (see `membrane-node-architecture.md` §4 and its
decision log).

## Caveats that swing the number

- **The optical diodes (line 4) are the experimental part** — ~$180 of screens and webcams,
  and genuinely fiddly. The two heads + GPU box are the *real* system and work even if the
  A↔C / B↔C links start as something simpler and evolve into the full screen-camera mesh.
  Do not let the ghost's plumbing block the brain.
- **Lines 3 and 8 depend on the open networking question** — with a managed switch the data
  plane is VLANs and you skip the USB NICs; without one it's two USB NICs and a direct A↔B
  cable. A ±$40 swing, not a redesign.
- **"Free" heads, not free build** — A and B are $0, but C is a genuine discrete-GPU tower,
  not a t630. The card is the commitment; the isolation is the freebie.

## Open questions before this becomes a wiring diagram

1. All-local compute confirmed? (The GPU decision implies yes — kills any offload line.)
2. Managed switch on hand, or USB-NIC point-to-point between the nodes?
3. Does any raw-internet flow reach inward past A, or does A terminate everything so only
   structured data crosses the diode?
