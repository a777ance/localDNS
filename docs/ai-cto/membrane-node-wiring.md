# Membrane Node — Wiring & Build Spec

**Status:** Build spec. Nothing wired yet. Companion to `membrane-node-architecture.md`
(doctrine) and `membrane-node-bom.md` (cost).

**Last updated:** 2026-07-19

Canonical A–G lettering (architecture note §0.5). Assumes the three build defaults:
**all-local compute; USB-NIC point-to-point; no raw internet inward.** Where a different
choice changes the wiring, it's flagged at the end.

---

## Node map

| Letter | Node | Box | Network identity |
| ------ | ---- | --- | ---------------- |
| A | internet (extracellular) | — | context, not a box |
| **B** | ingress head | t630 #1 | WAN + data-plane link |
| **C** | ghost core | discrete-GPU box | **none — no NIC** |
| **D** | egress head | t630 #2 | LAN + data-plane link |
| E | your LAN (cytoplasm) | — | context, not a box |
| F | executor | software on B and D | — |
| G | you | — | root of trust / whom it serves |

## Per-node interfaces (port by port)

**B — ingress head (t630 #1)**
- `enp1s0` (onboard NIC) → WAN (modem / R7000 WAN side)
- USB3 GbE NIC → Cat6 → D's USB3 NIC  *(data plane)*
- USB-serial (FTDI) → C  *(control link: B→C metadata in, C→B verdicts out)*

**D — egress head (t630 #2)**
- `enp1s0` (onboard NIC) → LAN (your switch / R7000 LAN side)
- USB3 GbE NIC → Cat6 → B's USB3 NIC  *(data plane)*
- USB-serial (FTDI) → C  *(control link: D→C requests in, C→D policy out)*

**C — ghost core (discrete-GPU box) — NO NIC**
- USB-serial → B
- USB-serial → D
- Internal only: GPU (RTX 3090 24 GB), 64 GB RAM, NVMe (OS + models), read-only germline
  SSD, 750 W PSU
- Power + cooling. No Ethernet, no Wi-Fi — physically absent or removed after OS install.

## Data plane (fast copper)

```
internet → B:enp1s0 → B:USB-NIC ══Cat6══ D:USB-NIC → D:enp1s0 → LAN
```

nftables on B and D forward + filter at line rate. **C is never in this path.**

## Control plane (portless, one-way, inspectable)

- **v1 — USB-serial diodes (recommended).** `B↔C` and `D↔C` over FTDI serial. Portless,
  dead-simple, honors the no-NIC invariant (a serial tty is not a network interface). Enforce
  a typed schema on every frame; rate-limited by the medium.
- **v2 — optical screen→camera (optional / experimental).** Replace each serial line with a
  small display + webcam pair in a light-tight tube. Same typed schema; the "ghost in the
  dark box." *Not required for a working system* — don't let it block the build.

## Frontier oracle (optional, off by default)

Not in the base wiring. If ever used: C requests a plan through the pore; **B dials** the
rented GPU over its WAN egress (one allowlisted destination), **Frigg-redacted tasks only**.
C never dials. Adds no cabling to C.

## Parts to order

| Item | Qty | ~Cost |
| ---- | --- | ----- |
| t630 heads (B, D) | 2 | owned |
| C box: used tower + RTX 3090 24 GB + 64 GB RAM + NVMe + read-only SSD + 750 W PSU | 1 | ~$1,550 |
| USB3 Gigabit NIC | 2 | ~$40 |
| Cat6 cable (B↔D) | 1 | ~$5 |
| USB-serial (FTDI) cable | 2 | ~$30 |
| Misc cabling / mounts / power | — | ~$30 |
| **Base total (serial control plane)** | | **~$1,700** |
| *(optional)* display + webcam + blackout tube | 4 sets | +~$180 |

## Build sequence

1. **Heads first.** Install Ubuntu on B and D; bring up the data plane
   (WAN → B → D → LAN) with nftables egress default-deny in **log-only** mode. Verify traffic
   flows and the deny-log populates.
2. **Core, isolated.** Build C with its GPU; install the local model stack; **no NIC** (or
   remove it after OS install). Bring up `C↔B` and `C↔D` over USB-serial with the typed
   schema.
3. **Close the loop.** B/D ship deny-logs + metadata to C; C returns typed policy/verdicts; F
   (the deterministic executor on B/D) applies them. Flip egress from log-only to **enforce**
   once the allowlist is seeded (the bounded learning week).
4. **Lock the invariant.** Confirm C has no network path of any kind. That is the no-NIC seal.
5. **(Optional)** Upgrade serial → optical; wire the frontier oracle egress via B.

## If the defaults change

- **Managed switch instead of USB-NIC:** the B↔D data plane becomes a VLAN trunk — drop the
  two USB NICs, add switch config. C unchanged.
- **Raw internet inward:** don't. Letting B forward unterminated flows toward the core
  violates the membrane. Default is no.
