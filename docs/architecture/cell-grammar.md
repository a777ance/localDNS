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

The concrete four-device instantiation of this grammar — 2 thin clients, a laptop, an
iPhone — lives in [`deployment.md`](deployment.md).

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

## The two anchors — C and G

The Ground law runs through **two** reference points with two different musical
functions. Keeping them distinct is the point.

- **G — the tuning reference.** Tuning is calibration to an absolute *external* standard:
  is the whole system in tune with the human it serves? G is the tuning fork; it lives
  outside the orchestra. Root of **authority** and meaning.
- **C — the tonic / node of trust.** The tonic is the *internal* center the music resolves
  to — the note every part comes home to. C is the root of **trust** the components
  organize around and verify against. The system is *keyed to C*.

> **You are keyed to C; C is tuned to G. G is sovereign, C is subordinate; when they
> conflict, C re-tunes to G — never the reverse.**

The gap between them is precisely misalignment: a system can be perfectly *in C* —
internally consistent, every part resolving cleanly to its trust anchor — and still be
*out of tune*, because C has drifted from G. Internally coherent, no longer calibrated to
the human. C is the regent, exercising day-to-day trust in the sovereign's name; G is the
sovereign. **Never build a C that can overrule G "for the system's good"** — that is the
regent deposing the sovereign, which is the misaligned system by definition.

C is also what lets G stay *absent from the plumbing*: C handles routine internal trust so
the human is not consulted for every note; G is referenced only when the music cannot
resolve on its own.

**Co-location (deliberate, not a pun):** the node of trust `C` *is* the core layer `C` —
the sealed, structurally-isolated center. The root of trust belongs in the most isolated
compartment, so the two senses of C are the same place on purpose.

So the Ground law resolves in two steps: **every progression cadences to C; C answers to
G.**

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

## Harmony — the horizontal axis

Octaves are the **vertical** axis: nesting, containment, the composition law
`A(child) = E(parent)` — static structure. Harmony is the **horizontal** axis: how
components sound *together* and *in sequence* — relationship and time. Both are anchored by
C (the tonic they resolve to) and G (the reference they tune to).

- **Harmonics** = a component's behavior. In tune, it produces clean overtones of C;
  compromised, it produces *inharmonic* partials — dissonance. **Trust-monitoring is
  harmonic analysis, and dissonance is the signal.**
- **Chords** = authorized multi-component interactions. Consonant = a sanctioned
  combination (nucleus + ribosome + this source); dissonant = a combination policy forbids
  (the sealed core suddenly voiced with an egress path). *Access control as harmony.*
- **Progressions** = workflows over time. A well-formed operation is a progression that
  **cadences** — resolves home to C, and through C to G. A progression that never cadences
  is a runaway or unterminated process: the agent that wandered off and never returned to
  the ground.
- **Dissonance** is not failure — it is tension that *demands* resolution. The system
  resolves it to consonance, or, failing that, the dissonance drains to G. Fail-closed,
  stated as harmony.
- **Modulation** = a key change — and *re-key* is the same word in both worlds for the same
  act. When G modulates (changes the envelope, rotates the anchor), C shifts to the new
  tonic and everything re-tunes. The Lazarus rebuild and secret rotation *are* modulations.

**Tether.** This is a *monitoring-and-policy vocabulary* — one language for three
questions: *is this in tune (trustworthy)? is this consonant (allowed)? has it cadenced
(resolved)?* Its cash value is four things — the C/G split (trust vs authority), alignment
= keeping C tuned to G, dissonance = the escalation signal, modulation = re-key. Held as
the language you reason in, not a synthesizer you build, it stays honest.

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

Seven layers, one invariant, two laws, two anchors, two axes — and a ground that is a
person.
A–F are the vessel; **G** is whom it serves; **C** is the tonic the vessel is keyed to,
tuned to G. They share a letter with the core because the root of trust lives in the
sealed center — and the vessel has no meaning apart from the service.
