# Membrane Node Architecture — the Ghost and its Organelle

> **This serves G.**
> Every layer, node, and decision below exists to serve the embodied human-in-the-loop.
> "Whom does the Grail serve?" is the first test any design choice must pass: does it serve
> **G**, or does it serve the design? A grail that serves no one is the wasteland — a
> cathedral of architecture that never becomes the box on the desk serves G exactly zero.

**Status:** Design. Nothing built. This is the target shape for a future multi-node
rebuild of the AI layer, not a description of the live t630.

**Last updated:** 2026-07-19

Read alongside `context.md` (component status) and `network-context.md` (live-system
rationale). This note records *why* the AI node is shaped like a cell membrane, and the
invariants that keep it real rather than theater.

---

## 0. One-line thesis

The intelligence lives **in the membrane**, not behind a wall. Its security is an
emergent property of the medium — a node with no network interface cannot be
misconfigured into being reachable — not a control anyone has to maintain.

---

## 0.5 The A–G layer schema (the octave)

A reusable role-contract, not a rigid template — every membrane-bound unit (the cell, and
any organelle we later build: mitochondrion, vacuole, chloroplast) *implements* these roles
with its own internal structure, at its own scale. Same pattern, different register — the
octave. **A–F are the recursive machine stack; G is the non-recursive ground beneath all of
them.**

| | Role | Realized by |
|-|------|-------------|
| **A** | extracellular space (the internet) | context — not yours |
| **B** | ingress membrane | internet-facing guard (thin client) |
| **C** | deliberating core — *transcribes* plans | the ghost / local-GPU node |
| **D** | egress membrane | LAN-facing guard (thin client) |
| **E** | cytoplasm (your LAN) | context — the interior |
| **F** | translation — *executes* plans | deterministic typed-action switch on the guards |
| **G** | **the ground — whom it serves** | **the embodied human-in-the-loop** |

- **The octave / recursion:** organelles nest inside E as their own A–F stack, one register
  down. A–F recurse; G does not.
- **C is the tuning fork.** Two distinct references: **G is the tonic** (what the system
  resolves to and serves), **C is the tuning fork** (the live calibration pitch every other
  layer matches). C is tuned *from* G — its policy derives from the source of truth — and
  then A/B/D/F tune to C's current judgment. G = purpose; C = coherence.
- **Protecting C is protecting the reference — but know exactly what stays pure.** C's
  hydrophobic isolation (no-NIC, read-only germline) keeps its *persistent* reference — the
  weights/germline — permanently pure: the water can never *write* to the fork's material.
  It does **not** purify C's *momentary* judgment — each task still ingests pore-sanitized
  world-content and can be transiently detuned (the diffusion risk). The bound is F: a
  detuned fork can push the pitch, but the deterministic executor only plays allowlisted
  notes, so an out-of-score note never sounds. "Protect C at all cost" = the wall
  (hydrophobicity) + the pore (Frigg / typed schema) + the executor (F), not the wall alone.
- **G is the root of trust and source of truth** — the human, and by extension the git
  repo/germline every octave re-derives itself from. The one reference that does not move
  and cannot be re-imaged.
- **G's gate must stay rare and meaningful.** Human-in-the-loop is load-bearing only if the
  human actually decides — germline writes, frontier clearance, physical trust. Consulted on
  everything, the human rubber-stamps, and a rubber-stamp is a soft ground. Keep G's
  approvals few and high-signal.
- Do not merge **C (transcription — writes plans)** with **F (translation — executes them)**.
  That split is the agentic-containment win; collapsing the labels loses it.

---

## 1. The three nodes

Modeled on a phospholipid bilayer. Both faces are water: the internet is the ocean, the
LAN is the cytoplasm. The hydrophobic core touches neither.

| Node | Membrane role | Faces | Network identity | Hardware |
| ---- | ------------- | ----- | ---------------- | -------- |
| **A** | outer head — ingress guard | the internet (ocean) | yes (WAN NIC) | identical thin client |
| **B** | inner head — egress guard | the LAN (cytoplasm) | yes (LAN NIC) | identical thin client |
| **C** | hydrophobic core — the ghost / deliberator | nothing | **none — no NIC** | the one discrete-GPU box |

A and B are the mirror-image heads: cheap, identical, disposable, re-imageable. C is the
odd one out — the only non-identical machine, because it carries the GPU.

## 2. Two planes, and only one is optical

- **Data plane (fast, dumb):** LAN ↔ B ↔ A ↔ internet over normal copper, forwarded and
  filtered by nftables on A and B at line rate. **C is not in this path** and never sees a
  user packet.
- **Control plane (slow, smart, optical):** `A↔C` and `B↔C` only, over one-way optical
  diodes (screen→camera or single fiber). Carries typed schema in, typed plans out —
  KB/s, parseable, rate-limited. This is the *only* thing that touches C.

A and B talk to each other over fast copper because they are already the exposed heads by
design. The only node worth hiding is C.

## 3. Invariants (the load-bearing ones)

1. **C ships with no NIC — optics only. A and B hold all the copper.** Isolation is
   structural, not configured. You cannot fat-finger a firewall rule that exposes a
   machine that has no network interface. This is the invariant everything else hangs off;
   do not regress it. (It self-assembles: wipe C, re-image it, swap the box — it *cannot*
   be anything but the core, because it has no hardware to be a network node with.)
2. **C is hydrophobic to the cytoplasm too.** It distrusts the LAN as much as the internet
   — a compromised internal device reaches C no more easily than the ocean does.
3. **The safety property is "rate-limited and inspectable," not "one channel."** The
   optical diode is safe because it is slow and B can enforce a typed schema on every
   frame. A GPU feed is the opposite — tens of GB/s of opaque bidirectional DMA you can
   only trust, never inspect. "One authenticated channel" is not a safety property; *one
   permission is all exfil ever needs.*
4. **Transcription ≠ translation.** C (the nucleus/deliberator) emits **plans only** —
   typed, allowlisted blueprints. It never acts. Plans are exported through the pore
   (export QC = well-formed schema, not prose) and executed by a **ribosome on A/B: a
   deterministic switch over typed actions, never a second LLM re-reading the plan.** A
   prompt-injected deliberator can still only emit a blueprint that a fixed-function
   executor refuses to misread. Planning and execution are split across a credentialed
   membrane — that is the whole game for agentic containment.
5. **The germline is read-only and downstream-forever.** The blueprint/model store is the
   one non-disposable thing (poison it and every re-imaged membrane inherits the poison).
   The deliberator gets read-only, task-scoped access to the "expressed genes" for this
   task — never the whole genome, no persistence, no write path. Nothing the reasoner
   produces flows upstream into the store without a separate, human-gated path. Enforce the
   write-path's *absence* physically (read-only media / one-way export), same trick as
   C's no-NIC.

## 4. The GPU decision — a local card is the mitochondrion

**Decision: C hosts a single discrete GPU inside the membrane. No external GPU. Permanent.**

Rationale:

- **The workload caps the model size, well below frontier.** C's real jobs — egress
  triage, deny-log reasoning, config authoring/audit, plan transcription — are narrow and
  structured. A well-prompted **32B model fits in 24 GB** and is genuinely sufficient for
  them. So the baseline is a **single 24 GB card** (e.g. one used RTX 3090), with **48 GB
  (2× 24 GB) as optional headroom** if you want to run 70B at 4-bit. That is the right size,
  forever, absent a concrete model requirement this workload does not have. (Corrected down
  from an earlier "48–96 GB" figure — see decision log 2026-07-19: costing it revealed the
  cliff above 24 GB is steep and the workload never asks for it. 96 GB is datacenter-card
  territory and has no place in this build.)
- **A local card keeps the ghost intact for zero network cost.** Reaching an *external*
  GPU means a fast, opaque, bidirectional link — a network hole — and the ghost is gone the
  moment "connection" is uttered. The card is bought/rented in *ownership* but fully
  *enclosed* in topology: a **mitochondrion** — external compute endosymbiosed and
  permanently sealed inside the cell. The metaphor is the literal origin story, not a
  flourish.
- **It locks with invariant 5.** Even a local card is a DMA-capable device with opaque
  firmware/VBIOS and a large CUDA/driver trust surface living in-host. Trusted-by-enclosure
  ≠ inert. Because the germline's write path is physically absent from that compartment, a
  compromised VBIOS can *read* the crown jewels but structurally *cannot corrupt* them.
  You accept the enclosed firmware/supply-chain risk the way a cell accepts mtDNA.

**"Free" is free on the network-hole axis, not the hardware axis.** A local-GPU ghost
means C is genuinely a discrete-GPU box — not the t630's Carrizo iGPU. The card is the
commitment; the isolation is the freebie.

### If a future model truly won't fit one card

The ghost-preserving path (and *only* that path): a sealed, internet-less, IOMMU-fenced GPU
enclosure over PCIe-fiber, treated as **inside** the membrane — a mitochondrion in an
external shell, never a network peer. This is a second fully-sealed box and a much heavier
build for a marginal gain over a big local card. It earns its keep only if a named model
requirement forces it. It does not, today.

## 5. Accepted residuals (named, not hidden)

- **Physical access is the detergent.** The membrane self-heals against perturbation
  (reboot, re-image, dead node) but lyses under a screwdriver — someone who bolts copper
  onto C, or taps the internal segment. Structural isolation does not survive an attacker
  with hands on the hardware. Accepted for a controlled environment.
- **Integrity, not confidentiality — *if* external compute is ever used.** The nuclear
  envelope stops the reasoner from *acting*; it does nothing about what the reasoner *sees*.
  Rented silicon reads whatever context and weights it is fed unless it runs an attested
  TEE. A local card moots this — the enclosure keeps the context in-cell. This residual only
  reappears if §4's external path is ever taken.
- **Emanations ≠ containment.** Optical I/O carries no RF, but the GPU still radiates EM and
  modulates power draw. If side-channels are in scope, C needs Faraday shielding + power
  filtering; a fiber pass-through crosses a shielded wall without an EM hole. Out of scope
  until it isn't.

## 6. Relationship to the existing Odin layer

This is the enclosure the current `10-ai-orchestration/langgraph-router/` roster would run
*inside*, not a replacement for it:

- **Frigg** (PII redaction) is the pore's **import gate** — redact before anything reaches
  the deliberator.
- **Heimdall** (privacy gate) and the dumb-switch `dispatcher.py` are ribosome-shaped
  already: deterministic, typed. Keep them that way; never let a second LLM become the
  executor.
- **Odin / the orders of five / Loki** are the deliberator — they transcribe plans inside
  the nucleus and export them; they do not translate them into action.

---

## Decision log (newest first)

- **2026-07-19** — VRAM figure corrected down: **24 GB baseline (one used RTX 3090, runs
  32B) / 48 GB optional headroom (2× 3090, runs 70B)**, replacing the earlier "48–96 GB".
  Costing the build (see `membrane-node-bom.md`) showed the workload never needs beyond
  24 GB, and the cost cliff above it is steep — consumer VRAM tops out at 24 GB, so 48 GB
  means two cards. 96 GB is datacenter-only ($10k+) and is struck from the design.
- **2026-07-18** — GPU placement decided: single local discrete card as the mitochondrion;
  no external GPU. External PCIe-fiber enclosure documented as the only ghost-preserving
  path *if* a future model forces it — not needed today.
- **2026-07-18** — No-NIC invariant locked: C has no network interface; isolation is
  hardware-intrinsic. `A↔C`/`B↔C` are inspectable optical diodes; the data plane is A↔B
  copper with C off-path.
