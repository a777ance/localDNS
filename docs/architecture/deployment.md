# Four-device deployment — the buildable cathedral

The concrete instantiation of [`cell-grammar.md`](cell-grammar.md) on real, owned
hardware: **2 Linux thin clients, 1 laptop (any OS), 1 iPhone.** Where the grammar is
abstract, this note is a parts-and-wiring map. Nothing here needs exotic gear — the
membranes are firewall-enforced (logical, not air-gapped), and no box runs a frontier
model (that tier is rented).

One honest framing up front: this is a **cell** (the household) that has **absorbed two
endosymbionts** (the laptop and the iPhone — foreign lineage, any OS, integrated by
contract, not re-imaged). The thin clients are the body; the laptop/phone are organelles
of separate descent.

---

## Topology

```
                 A — external space (internet)
                 │
          [ Netgear R7000 ]  outer perimeter (NAT/WAN)
                 │
   ┌─────────────┴───────────────────────────── E — cytoplasm (LAN + wg0) ──┐
   │                                                                         │
   │   TC#1  ── B/D + F ──  membrane + executor                              │
   │   (current t630)       DNS · VPN · monitoring · egress redaction        │
   │        │                                                                │
   │        │ gated: only TC#1 + wg0 may reach TC#2                          │
   │        ▼                                                                │
   │   TC#2  ── C ──  sealed core / nucleus                                  │
   │   (2nd thin client)    vault (germline) · router/planner · tiny model   │
   │                        never internet-facing                            │
   │                                                                         │
   │   Laptop ── its OWN A–G cell (mitochondrion / endosymbiont) ───────────┐│
   │   (any OS)   loopback membrane · LUKS · heavy inference · your seat    ││
   │        docks via WireGuard  (A_laptop = E_household)                   ││
   │                                                                        ││
   │   iPhone ── endosymbiont ──  G's remote hand + ground wire (pager)     ││
   └────────────────────────────────────────────────────────────────────────┘
                 │
                 G — the human (root of trust/authority; both C's tune to it)
```

---

## Box-by-box (reference)

| Device | Organelle | A–G | Runs | Repo folders |
| ------ | --------- | --- | ---- | ------------ |
| **Thin client #1** (current t630) | Membrane + executor | **B/D + F** | Pi-hole, Unbound, WireGuard, Uptime Kuma, UFW, CAKE; deterministic action-executor; egress redaction (Frigg) | `01`–`09`, `11` |
| **Thin client #2** | Sealed core / nucleus | **C** | Secrets vault (germline), orchestration router/planner (node of trust), tiny always-on model. Reachable only from TC#1 + wg0, never the internet. | `10`, `12` |
| **Laptop** (any OS) | Mitochondrion — its own cell | its own **A–G** | Heavy local inference when present; your workstation/console. Its own loopback membrane. | endosymbiont — not re-imaged |
| **iPhone** | Endosymbiont | **G-touch** | WireGuard peer; chat UI/console/monitoring on the go; **ground wire** (approval/escalation pager). | endosymbiont — not re-imaged |

### Compute ladder (maps to `10-ai-orchestration/config.yaml`)

- **Tiny, always-on → TC#2** (e.g. `deepseek-r1:1.5b`) — reachable from the iPhone anytime.
- **Bigger, on-demand → laptop** (7B–32B, GPU-dependent) — your real local brain, when present.
- **Frontier → rented** (opex, ~$1–5/mo, **non-sensitive only**, redacted at TC#1's egress). Nothing frontier runs locally — expected.

---

## Endosymbiont governance (laptop + iPhone)

Foreign lineage, absorbed by **contract, not re-imaging** — so the cell can absorb a laptop
running *any* OS. Made safe by three rules:

1. **Double membrane.** The device keeps its own hardening (LUKS, host firewall,
   loopback-bound services) *and* the household gates it. You never trust the guest's
   internals — you contain it between two membranes. Zero-trust BYOD.
2. **Cytoplasm, not nucleus.** Docking over WireGuard puts the device in the household's
   working space (E); it does **not** grant access to the core (C). Reachable ≠ trusted.
   The household core keeps its envelope no matter who is docked.
3. **Dual control, bound to G.** The device retains an **irreducible reflex germline** it
   never delegates — membrane integrity, its own keys, the right to disconnect and leave,
   and its direct line to G — and **imports an envelope** of host-managed policy/config/
   workload for everything above that line. Integration is a dial that deepens with trust
   but never touches the reflex core. If a compromised household core ever sends *"disable
   your encryption / exfiltrate your disk / stop answering to the human,"* it hits the
   germline wall and is refused. Both the device's germline and the host's authority to
   instruct answer to the same **G**.

Independent lineages: a household Lazarus rebuild does not touch the laptop, and re-imaging
the laptop does not touch the household. They die and regrow separately.

---

## Provisioning walkthrough

Blocks run **last-first** per house style; the step numbers are fixed and encode the real
execution order, so follow the numbers (1 → 9), not the page order.

- [Stage 3 — Absorb the endosymbionts: steps 6–9](#stage-3--absorb-the-endosymbionts)
- [Stage 2 — Stand up the sealed core (TC#2): steps 2–5](#stage-2--stand-up-the-sealed-core-tc2)
- [Stage 1 — Keep the membrane body (TC#1): step 1](#stage-1--keep-the-membrane-body-tc1)

### Stage 3 — Absorb the endosymbionts

**Step 6. Laptop — its own membrane.** Full-disk encryption (LUKS); host firewall
default-deny inbound; **every local service bound to `127.0.0.1`, never `0.0.0.0`** (the
local model talks to the laptop over loopback — its sealed internal bus).

**Step 7. Laptop — dock.** WireGuard as the *only* path home (the membrane-fusion pore that
reconnects `A_laptop = E_household`). No other inbound exposure when roaming.

**Step 8. Laptop — governance.** Decide the dial: what the household core may push (policy,
non-sensitive config, workload) vs. the reflex germline it never delegates (keys, membrane,
right to leave, answering to G).

**Step 9. iPhone — ground wire.** Already WireGuard peer `10.8.0.2`. Add push/approval so
fail-closed escalations reach you here — this is how G is reached when the music cannot
resolve on its own.

### Stage 2 — Stand up the sealed core (TC#2)

**Step 2. Provision the second thin client** (any of the household lineage — stateless,
re-imageable from this repo).

**Step 3. Move the core folders onto it:** `10-ai-orchestration/` (router/planner) and
`12-secrets/` (vault/germline).

**Step 4. Unseal the vault** (`12-secrets/unseal.sh`, age key on USB). This is now a hard
prerequisite — Pi-hole on TC#1 reads its password from the vault fail-closed.

**Step 5. Firewall TC#2** to accept connections only from TC#1 and the WireGuard subnet.
**No port-forward, ever.** This is the logical nucleus membrane — one hop behind TC#1,
never internet-facing.

### Stage 1 — Keep the membrane body (TC#1)

**Step 1. Leave the current t630 as-is** — it already *is* the membrane. DNS/VPN/monitoring
(`01`–`09`, `11`) stay where they are; it becomes the executor and egress guard for the
core behind it.

---

## The honest ceiling

- **Frontier is always rented** — nothing local can run it. Sensitive work never leaves
  TC#2 or the laptop; only redacted, non-sensitive work takes the rented lane.
- **The core is logically sealed, not a ghost** — firewall + one hop, not air-gap/diode. The
  right call for a home cathedral; the exotic gear was deliberately dropped.
- **No always-on heavy local** — thin clients are too weak, the laptop is not always on.
  Hence the tiny-always-on / heavy-when-present ladder.
- **Two trust zones is the real win** — separating the trust core (TC#2) from the
  internet-facing box (TC#1) is the biggest gain the hardware allows over a single-box
  stack.
