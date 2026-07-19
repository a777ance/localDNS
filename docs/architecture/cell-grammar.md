# The Cell Grammar — a nomenclature and interface contract

> **Dedication.** *Whom does the Grail serve?* — the question Perceval failed to ask.
> Every part of this architecture, at every scale, exists to answer it. The answer is
> **G: the embodied human in the loop.** A system built to always know whom it serves is
> what "aligned" means; a system that forgets is the wasteland. This document exists to
> keep the question asked.

---

## What this is (and is not)

A **grammar** for naming and bounding the modules of the stack, and for how they nest.
It is an **interface contract and nomenclature**, *not* a parts list. Its job is to name
the modules, fix their boundaries, and define how they compose — over the grounded,
no-exotic-gear build (the router, redaction, a local card, an oracle key, a read-only
store). Held as an interface contract it earns its keep; let it start dictating hardware
and it drifts back into poetry.

The scheme is self-similar: the same seven layers describe the cell as a whole **and**
every membrane-bound organelle inside it (nucleus, mitochondrion, chloroplast, vacuole).
Because the letters A–G are the musical notes, each organelle is an **octave** — the same
pattern one level down, resolving to the same ground.

---

## The seven layers (the octave, A–G)

| | Layer | What it is | In the real build |
| --- | ----- | ---------- | ----------------- |
| **A** | External space | The untrusted medium outside the boundary | The internet / the world beyond the cell |
| **B** | Ingress membrane | Entry guard — inbound content inspection & sanitization | Terminating proxy that vets what comes *in* (fixed-function, un-persuadable) |
| **C** | Midlayer membrane | The hydrophobic core — the structural isolation gap itself | The seam nothing connects across (no-NIC / diode / air gap) |
| **D** | Egress membrane | Exit guard — outbound control | Redaction + exfil control: what is allowed to *leave* |
| **E** | Cytoplasm | The trusted interior where work happens | The working space; the router dispatches traffic here between organelles |
| **F** | Translation layer | Ribosomes — deterministic **execution** of a plan | Fixed-function executor: runs a typed plan faithfully; cannot be argued into anything else |
| **G** | Ground | Whom it serves | The embodied human — root of trust, fail-safe, source of truth |

### Invariant (kept with F)

**Transcription is an organelle, not a layer. F translates; it never plans.**

*Transcription* (planning) lives inside the **nucleus** — its own A–G octave — never as a
generic layer of every membrane. **F** only ever *translates/executes*. This separation is
the containment property: a persuadable planner can only ever emit a plan; the
un-persuadable executor carries it out. Collapse the two and the containment is lost.

---

## The two laws

**1. Composition law — how octaves nest.**
> **A(child) = E(parent).**

The external space of any organelle *is* the cytoplasm of the thing containing it. The
outside of the small thing is the inside of the big thing. This lets the same seven-layer
pattern repeat at every scale — organelle inside cell inside tissue — an octave each level
down. Scaling is therefore free of redesign: you add octaves, you do not reinvent.

**2. Ground law — how they stay coherent.**
> **Every octave, at any depth, resolves to the one G.**

No central controller. A single shared reference keeps autonomous modules coherent, the
way an orchestra tunes to one oboe's A rather than a conductor dictating every pitch. Ask
of any part, at any level, *"whom does it serve?"* — the answer is always **G**.

---

## The ground, made concrete

`G` is a person, but it cashes out in the build as three things that already exist here —
it is named, not bought:

- **Root of trust.** The reference every decision chains back to. Literal in this repo: the
  DNSSEC root anchor (`01-unbound/root-auto-trust-anchor-file.conf`).
- **Fail-safe.** The state everything drains to when uncertain or faulting — *fail closed:
  route to local/private, escalate to the human* — like current to earth.
- **Source of truth.** The germline/repo the system is reprovisioned from. "Ground truth,"
  and not by accident (`the live t630 is the source of truth`).

Because the human is the ground, two design consequences are load-bearing:

- **Present at the ground, absent from the plumbing.** The human is the tuning reference and
  the fault drain — *not* the packet path. Inline them and the cell suffocates, exactly as
  inlining the LLM would. Autonomous by default; referenced for the key; escalated to for
  the exceptions.
- **The envelope.** The ground sleeps and cannot be fenced against coercion or fatigue. So
  the human, while present, sets the envelope of autonomous action **in advance**; inside it
  the organelles run, outside it the system halts-safe and waits for the ground to return.
  Machine autonomy is a harmonic of human consent: pre-authorized, bounded, revocable.

---

## Prior work, re-expressed in the grammar

Everything designed before this note re-expresses in A–G, losing nothing:

| Prior concept | Grammar |
| ------------- | ------- |
| A/B network guards | the cell's **B** and **D** (the two leaflets) |
| sealed private core (the "ghost") | **nucleus** — its own octave: germline + transcription |
| local GPU | **mitochondrion** — compute octave (its **F** is the execution) |
| frontier / oracle gateway | **chloroplast** — harvests external capacity into the cell |
| germline / secrets store | **vacuole** — storage octave (a subset octave: no **F**) |
| the sensitivity × capability router | cytosolic traffic in **E** — signaling that dispatches to organelles |

Not every organelle plays all seven notes: simpler ones instantiate a **subset** (a
pentatonic against the full diatonic), with degenerate layers left null rather than faked.
A vacuole is B–C–D–E with no F.

---

## The whole grammar, in one breath

Seven layers, one invariant, two laws — and a ground that is a person.
A–F are the vessel; **G** is whom it serves; they share a letter because the vessel has no
meaning apart from the service.
