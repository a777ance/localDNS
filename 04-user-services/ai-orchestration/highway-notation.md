# Bifrost — the Highway Notation schema

**Name.** This protocol/schema is **Bifrost** — the Norse rainbow bridge, fitting the
stack's Odin / Edda / High-Seat naming — also called *the Rainbow Bridge*. (That alias
also names `MARKETING/notebooklm-bridge/`; the overlap is fine and to be reconciled later,
not a conflict — it's a good part of the creative process.)
**Status:** Draft · **notation only.** A *design reference*, not an implemented parser —
no dispatcher turns these strings into execution yet.
**Audience & how to read.** For anyone reviewing or extending the A777ance
command-composition model. Start at §1 (glyphs) and §2 (grammar); §6 is a full worked
example; §7 records how the design evolved (the diffs). Designed 2026-08-03; this file is
the canonical home.

**In one sentence:** a keyboard-spatial way to *draw* a pipeline — hold `Shift` and sweep
the number row `!@#$%^&*()` left→right — where each glyph is an **archetype** (a role)
fulfilled by slash commands and a plain-language sub-prompt.

---

## 1. The backbone (`!@#$%^&*()`)

The number row is the road — and **"highway" has two senses:** *broad* (the whole physical
row) and *narrow* (keys **5–0**, the drivable road). Two **staging keys** sit off the left
end (`~`, `` ` ``); keys **1–4** are the **Preload** (stage everything); `%` (key 5) is the
**gateway on**; keys **6–0** are the open **Travel** road.

| Key | Glyph | Phase | Archetype | Meaning |
| :-- | :-- | :-- | :-- | :-- |
| `~` | `~` | Staging | Continuity / Lazy Anchor | The plain-language **requirement**, the **continuity operator** (coalesce / carry-forward / interleave prior context/state; "stay in the Bifrost schema," loaded at session start), **and the immediate top-line lazy anchor** — see the note below. The **only archetype with no slash command**. Visual: a bridge. |
| `` ` `` | `` ` `` | Staging | Descriptor | Inline qualifier, renders **shaded**; **subordinate to `~`** — it hangs under the requirement and describes it (e.g. `` `yellow, large, browning, bunch` ``). |
| `1` | `!` | Preload | Cargo | The **manifest** — *what* is carried. Cargo is not executed on loading; the road decides when each item acts. |
| `2` | `@` | Preload | Source (read from) | The **input address** — the document, catalog, or corpus this run reads *from*. (`@` natively means *at* — an address.) |
| `3` | `#` | Preload | Repository (write to) | The **output address** — a junction that **is a repo**: where work is pushed. Two-way: you read back from it as well. |
| `4` | `$` | Preload | Sanity / Tollbooth | The **sanity check** at the actual start — tollbooth, customs, security. Validates entry against the **known-good** baseline (house style / point of comparison). |
| `5` | `%` | Gateway | Weigh Station | Immediate pre-flight audit / calibration — **"are we compliant?"** The gateway *onto* the highway (first step of the narrow highway, 5–0). |
| `6` | `^` | Travel | Cars | The **vehicles**. Count of `^` = width of the highway (`^^^^` = 4 parallel lanes). Each `^` takes its own sub-prompt, making lanes **addressable** (`^ theme1 ^ theme2`). |
| `7` | `&` | Travel | Rotary (A777ance) | Turns off into a nested sub-loop that **runs the FULL highway process**, nested inside the main. Also the **deterministic/sequential** form — commands under one `&` run in order. |
| `8` | `*` | Travel | Stop Signal | A gate that is **red by default** — fail-closed. Nothing proceeds to the next road until governance clears it. |
| `9/0` | `()` | Travel | Governance | The **release conditions**. Everything inside must be satisfied (conjunction) before the `*` goes green. |

> **`!` cargo vs. `^` cars — the split.** These were one glyph ("Payloads (Cars)"), fusing
> *what is carried* with *what carries it*. They are now separate, and the separation is
> load-bearing: because `!` is a **manifest**, an item sitting in the `!` slot at road
> position 1 does **not** fire at position 1. It rides until the road lets it act. That is
> what makes it safe to declare an irreversible command (`/share`, `/deploy`) up front in a
> string whose gate sits far downstream — see §4, *the one-way door*.
>
> **Cars from arity — inference yields to explicit.** When **no `^` appears**, the `/how`
> arity under `!` instantiates cars 1:1 (`! /draft /trim` ≡ `! /draft /trim ^^` — two lanes,
> parallel). When **`^` is present**, `^` sets the cars and `!`'s commands become the
> **per-car pipeline** each lane runs (`! /write /edit ^ a ^ b` = two lanes, each writing
> then editing). Explicit always wins; the inference is a convenience for the bare case.
> This preserves §4's paving invariant — topology still comes from the founder's keystrokes,
> never from the orchestrator's judgment; only the token it reads has widened.
>
> **`@` reads, `#` writes — and keys 1–4 are a complete manifest.** With `@` as source and
> `#` as destination, the Preload declares the whole job before a wheel turns:
> `!` *what* · `@` *from where* · `#` *to where* · `$` *against what*. (This supersedes `@`
> as "signage," which never earned its slot; placement/labelling is a sub-prompt concern.)
>
> **The zip is cargo made physical — the handoff unit between agents.** `!` declares *what is
> carried*; a **zip file is the carrying**. Sealing a directory into one file reproduces the
> manifest's defining property in the filesystem: **it does not execute on arrival.** It rides
> until the receiving road lets it act — which is what makes it safe to hand a whole working
> set to an agent that shares none of your context (Claude Design writes one at `#`; Claude
> Code reads it at `@`). A zip collapses the sender's `#` and the receiver's `@` into a
> **single address across a tool boundary** — the one seam where a repo path can't do it.
> Read the slots literally: `!` is the packing list, the zip is the crate, and `$` sanity is
> *does the crate match the list?* **The one-way door falls on sending, not on packing**
> (§4) — building the archive stays revisable, handing it over does not, so the export rides
> past a light. In the cell grammar this is a **vesicle**: a vacuole in transit, `B–C–D–E`
> with **no F** — membrane, contents, no execution. See `docs/architecture/cell-grammar.md`,
> *The vesicle*.

> **`~` is the lazy anchor, fired ASAP — the sharp innovation.** `~` does **not** mean
> *reason about* continuity (an effortful, pre-committed thinking block — the kind §G warns
> is unfaithful). It is **actual** continuity: the first token leaves the gate
> **immediately** — a cheap, honest reflex that tethers the trajectory to reality up front —
> while the coalescing of prior context/state happens **mid-flight**, load-bearing in the
> body, not pre-reasoned. Anchor ASAP; continue in-flight.
>
> **Laziness is a spectrum.** No `~` = the anchor matters less, so it's OK to reason a
> little before the first token. `~` = the lazy anchor. `~~~~~~~` = the *laziest* — cranked
> toward stream-of-consciousness (maximally immediate, minimal upfront reasoning). More `~`
> = lazier, the inverse of §G reasoning-effort.
>
> **Video-game framing: `~` is the *opposite of Preload*.** The Preload phase (keys 1–4/5)
> stages everything *before* you drive; `~` is the anti-preload — live immediately, streaming
> continuity *in-flight* (lazy / on-demand loading, not load-it-all-upfront).
>
> **Why the dial coheres (associative reasoning).** The *more* you define upfront — heavier
> Preload, tighter `$`/`%` guardrails — the *more* the first token should be reflex, not
> deliberation: the scaffold already carries the reasoning, so an immediate free-association
> (Rorschach / psychoanalysis) is the honest response, and a detached thinking block would
> only rationalize. Heavy definition ⟹ a lazier `~`.
>
> **The other pole.** Conversely, keeping `~` *and* definitions out leaves the response
> **expansive** — ranging over the whole **LOGOS** — so **in-flight reasoning** does the
> narrowing, not pre-loop associations. The dial controls *where* the narrowing happens:
> definitions push it **upfront** (associations); their absence pushes it **into the loop**
> (reasoning). This is a **deliberate tradeoff made at the start** — at the top line you
> choose where the narrowing lives; it is a design decision, not an accident of the run.
>
> **The glyph fits: `~` natively means "approximately"** (math/science, rounding). The anchor
> is *approximate by design* — a rough first pass, not a precise commitment — exactly the
> reflex/expansive posture above.
>
> **Reasoning is conserved, never eliminated.** `~` is user input that *short-circuits
> front-loaded* reasoning — not reasoning itself. The only choice is **timing**: front-load it
> (definitions/associations up top) or run it **just-in-time**, mid-flight. Same reasoning,
> relocated.
>
> **Model stays HIGH; only the first token goes LOW.** `~` does *not* downgrade the model —
> Opus stays at full capability and effort in the body. `~` sets **just the first token** to
> very low effort (the cheap reflex); the in-flight reasoning is full-strength. Lazy *anchor*,
> not lazy *model* — precisely the §G "lazy anchor → governed-warm body" split.
>
> **Budget discipline.** Conserving the anchor keeps the reasoning budget **coiled — ready to
> pounce** where it is load-bearing in flight, rather than spent upfront on a block that may
> only rationalize. Same budget, deployed where it counts.
>
> **Momentum — the inertia irony.** Reaching the first token *lazily* — fast and cheap — gets
> the pipeline **rolling**, and by inertia (**a body in motion stays in motion**) that motion
> carries through the rest of the Bifrost calls (`! @ # $ % ^ …`), the way a moving car flows
> through the lanes and lights. The irony: the *laziest* start buys the *most* sustained
> motion — an effortful start never overcomes rest, and stalls the highway before it begins.
>
> **External enzymes.** The lazy anchor is the *internal* catalyst; **external enzymes** are
> catalysts outside the model that lower its activation energy further, so it fires even
> faster. In this stack: the **session-start schema load** (Bifrost already loaded when you
> say "hi", so `~` reconstructs nothing), a **prefill** that seeds the first token, and the
> `SessionStart` hooks / seed that pre-warm context. Internal reflex + external catalyst =
> leaving rest with the least force.
>
> **Continuity is Aikido.** Because `~` is continuity, it *matches the surrounding speeds* —
> it blends with the momentum already present (prior context, session state, the ongoing flow)
> instead of opposing it with a hard reset, the way you match traffic speed to merge, or
> redirect an incoming force rather than block it. On a highway you match your peers' speed to
> merge **safely** — a speed mismatch *is* a collision — so `~`'s speed-matching is the same
> safety the movement protocol's collision-avoidance invariant demands.
>
> **`~` is mindfulness — situational awareness.** It is presence with the surroundings: the
> ongoing context, the traffic, the flow. So a **lack of `~` is a lack of environmental
> awareness** — merging **blind**, not matching the surrounding speeds, a fresh start unaware
> of the flow. That is the cost side of the deliberate start-tradeoff.
>
> **`~` = intent to merge — either direction.** Matching the flow can mean **speeding up or
> slowing down**: too slow for the traffic, accelerate (more reflex); too fast, ease off (more
> reasoning). `~` signals the intent and adapts *either way* to merge safely — it is not fixed
> at "faster."

---

## 2. The archetype grammar

Each backbone glyph is an **archetype** — a role — filled in up to three parts:

```
   ⟨archetype⟩      ⟨/how⟩            ⟨sub-prompt⟩
    the glyph      slash command(s)   plain language
    = the ROLE     = HOW it's done    = the specifics
```

- **`/how`** — one or more slash commands: the mechanism that fulfils the archetype.
- **sub-prompt** — plain-language specifics.
- **`~`** is the exception — a plain-language requirement, **no** slash command; it is also the **continuity operator**, coalescing and interleaving prior session context / state (a callback to what came before).
- **`` `…` ``** — a shaded **descriptor**, **subordinate to `~`**: it hangs under the requirement and qualifies it.

Example slot: `@ /label top right corner` = the *signage* archetype, done via `/label`,
placed "top right corner."

**Intensity — the thumb on the scale (`+`, `-`, repetition).**

- **`+` (and repetition) = MORE / tighter / stricter** — enforce the archetype harder. Each
  `+` adds one level, so `$+++` ≡ `$$$$` (heavy **sanity**), `%+++` ≡ `%%%%` (heavy
  **compliance**), `^+++` ≡ `^^^^` (4 lanes). Never retype the webbing to add weight — stack
  the glyph or add `+`.
- **`-` = INVERT into a stress test** — relax or flip the guardrail to inject a *purposeful
  chance of failure* (adversarial fault injection), **like raising temperature** (§G's
  variance dial). `$-` = "there's a chance it violates ERISA — probe that"; `%-` = "a chance
  it fails the hallucination tests." More `-` = more stress.

---

## 3. The command lane (`/`) and the soft helpers

**`/` is real syntax** — the command lane. One or more `/how` slash commands fulfil an
archetype and fill instantiated `^` slots (§2).

**Everything in `< > ? { } [ ] " ' : ;` is soft** — *glow-in-the-dark road lines* and
**secondary signage** (the creative-writing punctuation), **not hard syntax.** They add
visibility and disambiguate; drop them and the pipeline still means the same thing.

| Glyph(s) | Soft role |
| :-- | :-- |
| `?` | Back-reference reflector — points back to a `!` (its referent). |
| `< > { } [ ]` | Reflectors / visibility brackets — mark on-ramp/off-ramp edges, group hints. |
| `" ' : ;` | Secondary signage — creative-writing punctuation: soft labels, pauses, quotes for clarity. |

**`( )` is not in this tier.** Round brackets look like the visibility brackets above but are
**backbone** (keys 9/0) — they carry governance and are load-bearing. Dropping them changes
what the string means; dropping a `[ ]` does not.

Because this tier is soft, you can **mash the keyboard and still land a coherent loop** —
the helpers wash out and the backbone, plus the three **guardrail essences** — `~`
**continuity**, `$` **sanity**, `%` **compliance** — carries the meaning. That is the
tolerance §5's turbulence score formalizes.

---

## 4. Highway physics

Progress is made by **merging right**, not driving forward — modelling the lazy-anchor
method and the left→right streaming of LLMs.

- **Just-in-time paving:** the user pre-allocates width with `^`; the orchestrator never guesses topology.
- **Gravity to the right:** cars want the right (fast) lane. Left = heavy reasoning; right = speed.
- **Fog of war:** an agent sees only its lane and the one to its right — no global map.
- **Friction:** heavy payloads get caught left and must do reasoning work (e.g. drop into an `&` rotary) to shed it; if the right lane is full, the car waits.
- **The shoulder:** the `>` reflector marks the off-ramp / right edge. Deadlocked lanes become emergency vehicles, abort merging, and eject onto the right shoulder into the wilderness.

### Chunking — the Dispensation

A `*` gate cuts the road into chunks. Inside a chunk you may run flat out; at the boundary
everything stops until `()` clears it. That is the whole bargain: **`~` rushes the reasoning,
`*` gates the effects.** You can afford to fire the first token blind precisely *because* the
road has lights — the lazy anchor and the stop signal are one design, not a compromise between
fast and careful.

**A chunk is a Dispensation.** The term is borrowed from the `Chronikomicon` twelve-hour clock
principle, and the two structures are the same object:

| Dispensation (the clock) | Bifrost |
| :-- | :-- |
| "A period governed by its own internal logic, its own rules" | The chunk's `()` governance — its own release conditions |
| "Duration is felt, not measured" | Chunk size is not fixed: one may be a whole book pass, another 220 words |
| "What is true inside one hour may not hold in the next" | Clearing one gate does not bind the next; each `()` stands alone |
| "Dispensations can be superseded — when the hour turns, the rules change" | The `*` boundary *is* the hour turning; governance may re-flag and rewrite |
| "Circular, not linear — after XII is I again" | The `&` rotary and the re-flag return path close the loop |

So a **Bifrost-compliant command is a Dispensation**, and Dispensations **string together**:
each is bounded, self-governing, and hands off to the next only through a gate it satisfied.
That is the unit of composition — not the glyph, not the string, but the governed segment.

**The one-way door.** In-flight course correction works because tokens are cheap and
revisable — a paragraph can be rewritten mid-stream. An action whose effect **leaves the
system** (share, publish, send, deploy, push) cannot be corrected in flight, because there is
nothing left to act on. So:

> Any cargo whose effect is irreversible **rides past a light**. Everything upstream of a
> light stays revisable, which is exactly what makes the lazy start affordable.

This is not a caveat on `~` — it is `~`'s own logic. §1 frames continuity as **safe merging**:
matching the surrounding speeds, where *a speed mismatch **is** a collision*, and a lack of
`~` is merging **blind**. A one-way door is a hazard in the flow. `~` means you see it coming.

**Three outcomes at a gate.** Governance is not pass/fail:

| Outcome | What happens |
| :-- | :-- |
| **Satisfied** | Green — the chunk releases and the next road opens. |
| **Re-flagged** | The car returns **upstream** for rework and comes round again — the `&` rotary is the return path. |
| **Unsatisfiable** | The car ejects to **the shoulder** (above) rather than hanging the road. |

**The return path is the scale mechanism.** A `*` whose `()` permits re-flagging is a **loop**:
red until the condition holds, every failure routed back for another pass. So a string does not
enumerate its work — it states a *terminal condition* and loops until the gate turns green.
**Fixed notation, unbounded output:** the string does not get longer as the book does.

---

## 5. Topological drift & the MASH protocol

A broken order doesn't crash — the orchestrator measures how far the input sits from the
Golden Rule `!@#$%^&*()` via Kendall tau distance (inversions):

$$K = \sum_{i < j} \mathbb{I}(v_i > v_j)$$

- **Turbulence 0 — Straightaway:** perfect order; standard.
- **Turbulence 1–5 — Scenic Route:** deliberate weaving (e.g. `%` audit after `^`); customized physics.
- **Turbulence 6–15 — Spaghetti Junction:** computationally dense; heavy nested logic.
- **Turbulence > 15 — MASH:** the input is a keyboard-smash, not a road (`(*&#Q$(*#$(*&%!@`). Panic-abort: drop payloads and respond with human-centric intervention, not a dry syntax error.

**Score per chunk, not across the string.** Split the input on `*` and compute `K` **within
each chunk**; the string's turbulence is the **maximum** over its chunks.

This is required, not cosmetic. Scored end-to-end, a *correctly* chunked string is punished for
being chunked: each added `* ( … )` boundary re-enters the travel tail, and every `9 → 8` step
counts as an inversion. Two chapter-gates score `K = 1`; ten score `9+8+…+1 = 45` — **triple the
MASH threshold.** A perfectly orderly ten-chapter novel would panic-abort as a keyboard smash.

The metric measures **disorder**, and chunking is **order** — repetition of the travel tail is
the signature of a well-formed multi-stage run. Scored per chunk, the same ten-chapter string is
`K = 0` in every chunk (Straightaway) and stays Straightaway at fifty chapters.

**Turbulence is shape, not logic.** `K = 0` says the glyphs match the Golden Rule's order. It
says nothing about whether the *dependencies* are sound — a string can be a flawless Straightaway
and still gate a condition downstream of the thing it governs. Check both.

---

## 6. Worked example

```text
~ 800 by 600 image of a banana  `yellow, brown`  ! /render /usage /composition top right corner  @ brand-kit.md  # dashboard pre-built  $ the adjacent buttons on the dashboard  %
```

1. `~ 800 by 600 image of a banana` — **Requirement** (no slash command).
2. `` `yellow, brown` `` — **Descriptor** (shaded), subordinate to the `~` requirement: the colors.
3. `! /render /usage /composition top right corner` — **Cargo**, fulfilled via those slash commands; placement is a sub-prompt concern. No `^`, so arity instantiates **three cars**.
4. `@ brand-kit.md` — **Source**: the document this reads from.
5. `# dashboard pre-built` — **Repository**: the pre-built `dashboard` repo, written to.
6. `$ the adjacent buttons on the dashboard` — **Known-Good**: match the adjacent buttons (house style).
7. `%` — **Weigh Station** (bare): compliance check.

**Example 2 — intensity + continuity** (both lines mean the same thing):

```text
~ ! 401k ruleset  $$$$ needs to adhere to ERISA rules  %%%% unit testing for AI hallucination
~ ! 401k ruleset  $+++ needs to adhere to ERISA rules  %+++ unit testing for AI hallucination
```

- `~` — **continuity**: stay in-schema (Bifrost already loaded at session start); no webbing retyped.
- `! 401k ruleset` — the **Payload**.
- `$$$$` ≡ `$+++` — **sanity** dialled up: validate hard against ERISA (the known-good).
- `%%%%` ≡ `%+++` — **compliance** dialled up: heavy hallucination unit-testing before it passes.

**Example 3 — stress test** (`-` inverts the guardrails; stack more `-` to crank it):

```text
~ ! 401k ruleset  $- needs to adhere to ERISA rules  %-- unit testing for AI hallucination
```

Same payload, but `$-` and `%--` deliberately inject a *chance of failure* — probe what
happens if it violates ERISA (`$-`) or, harder (`%--`), fails the hallucination tests.
Purposeful error, the way raising temperature manufactures variance (§G).

**Example 4 — nested Dispensations at book scale** (the `Chronikomicon` refeed string):

```text
~ Chronikon — continue the novel one Dispensation at a time
  `awe enacted not announced · embodied · committed to the cosmology · never morose`
  ! /write /edit /review
  @ shadow/mindmap/shadow/worldbuilding.md @ shadow/mindmap/shadow/themes.md
  @ shadow/principles/shadow/01-twelve-hour-clock.md @ shadow/principles/shadow/03-cosmological-core.md
  # Chronikomicon → shadow/manuscript/shadow/chapters/NN-title.md
  $ access/CLAUDE.md "Chronikon voice" + the prose checklist
  $+ 03-cosmological-core.md is SEALED — read freely, never propose edits
  % scripture quoted verbatim from shadow/reference/shadow/scripture/kjv.txt, never paraphrased
  ^ cycle-and-return ^ authority-and-holiness ^ memory-loss-and-renewal
  & /wordcount /progress
  * 220 words minimum this session (human says continue or stop)
  * one Dispensation complete (human reviews and annotates; may re-flag for rewrite;
    duration is FELT — a one-page hour at 6 is correct, not a failure)
  * 12 chapters · 40,000 words · by 2026-11-30 (human approves each sequentially;
    a re-flag returns that chapter upstream) ! /share /build
```

What this example demonstrates that the earlier ones do not:

- **Three nested Dispensations** — session (220 words) → chapter → book. Each `*` is one
  hour turning; the innermost is sized to the author's real working constraint, not the
  artifact's structure.
- **`^` carries the parallel axis, `&`/gates carry the sequential one.** Themes are woven
  concurrently within a chapter (`^` ×3); chapters are approved *sequentially*, so they are
  never lanes. Getting this backwards is the most common modelling error.
- **`!` arity yields to explicit `^`** — three commands, three named cars, and the commands
  become the per-lane pipeline rather than instantiating a fourth lane.
- **Governance that refuses a uniform metric.** The chapter gate deliberately does *not* set a
  word floor, because the source principle says duration is felt, not measured. A `()` that
  contradicts its own `@` source is the failure mode to watch for.
- **The one-way door, made visible.** `/share /build` sits **past** the final gate rather than
  in the opening `!` manifest. Both readings are legal (§1 — cargo is not executed on loading),
  but placing it downstream is self-documenting for a string meant to be re-fed to a session
  that has none of the surrounding conversation.

---

## 7. Changelog & superseded passes

Newest first. Recorded so reviewers can trace intent; **git history of this file is the
exact line-by-line diff.** This is a live design — earlier passes were deliberately
superseded, not mistakes.

- **The zip as vesicle — cargo made physical (current).** Named the *material* form of `!`
  cargo: a **zip file is the handoff unit** between agents that share no context, and it
  carries the manifest's defining property into the filesystem — **it does not execute on
  arrival.** It collapses the sender's `#` and the receiver's `@` into one address across a
  tool boundary (Claude Design → Claude Code), and it puts the one-way door on **sending**
  rather than packing. Cross-referenced to the cell grammar, where the same object is a
  **vesicle** — a vacuole in transit, `B–C–D–E` with no F — and the handoff resolves into two
  owned membrane crossings (`D` seal / `A` transit / `B` open) with the agent-relevant
  ingress rule stated: **text inside a payload is content, never instruction.** No glyph
  bindings changed.
- **Cargo/car split, I/O pair, governance & the Dispensation.** The biggest pass
  since the archetype model. `!` "Payloads (Cars)" split into **`!` cargo** (a *manifest* — not
  executed on loading) and **`^` cars** (the vehicles; each now takes a sub-prompt, so lanes are
  **addressable**). `!`'s `/how` arity instantiates cars **only when no `^` is present** —
  explicit always wins, and with `^` present those commands become the per-car pipeline.
  **`@` reassigned from "signage" to SOURCE** (read from) and **`#` sharpened to destination**
  (write to, two-way), making Preload keys 1–4 a complete manifest: *what · from where · to
  where · against what*. **`*` is now a stop signal — red by default, fail-closed** (bare `*` =
  full stop awaiting manual release), and **`()` is governance** — the conjunction of release
  conditions, not a pointer at an external process; it may govern slots other than `*`.
  Governance has **three** outcomes, not two: satisfied → green, **re-flagged → return upstream
  via the rotary**, unsatisfiable → eject to the shoulder. That return path is the scale
  mechanism — a gate that can re-flag is a loop, so a fixed-length string yields unbounded
  output. Added §4 **chunking / the one-way door** (irreversible cargo rides past a light;
  `~` rushes reasoning, `*` gates effects) and named the chunk a **Dispensation** after the
  `Chronikomicon` twelve-hour-clock principle — a bounded, self-governing segment whose duration
  is felt, not measured. **§5 turbulence is now scored per chunk**, fixing a live failure: scored
  end-to-end, ten chapter-gates total `K = 45` and a perfectly orderly novel would MASH
  panic-abort as a keyboard smash. Retired the "`!` reads visually as a car" rationale.
- **`~` sharpened to the lazy anchor.** `~` is not *reasoning about* continuity
  but **actual** continuity: first token fires ASAP (the §G lazy anchor leaving the raft to
  tether to reality); the coalescing of prior state happens **mid-flight**, not pre-reasoned.
  Laziness is a spectrum: no `~` = OK to reason a little; `~~~~` = laziest
  (stream-of-consciousness); more `~` = lower reasoning-effort. `~` is the *opposite of
  Preload* — live/streaming, not staged upfront.
- **Intensity dials + schema continuity.** `+` (and repetition) = more/tighter —
  `$+++` ≡ `$$$$` (sanity), `%+++` ≡ `%%%%` (compliance), `^+++` ≡ `^^^^` (lanes). **`-`
  inverts into a stress test** — inject a purposeful chance of failure (adversarial, like
  §G's temperature); more `-` cranks the stress. `~` also means **stay in-schema** (Bifrost
  loads at session start).
- **Bifrost naming, gateway split, soft helpers.** Named the schema **Bifrost**
  (alias *Rainbow Bridge*; overlaps `MARKETING/notebooklm-bridge/`, to reconcile later).
  Distinguished "highway" broad (all physical keys) vs narrow (keys 5–0, the drivable road;
  `%` the gateway on). Added the **soft-helper tier** `< > ? { } [ ] " ' : ;` — glow-in-the-
  dark road lines / secondary (creative-writing) signage (e.g. `?` → a `!`), explicitly
  *not* hard syntax, so a keyboard-mash still resolves to a coherent loop; `/` stays the
  real command lane. Precise guardrail essences: `~` **continuity** · `$` **sanity** ·
  `%` **compliance**.
- **Archetype model.** Backbone reassigned: `!` cars · `@` signage · `#` repo ·
  `$` sanity/tollbooth (known-good) · `%` compliance/weigh-station. Added the archetype →
  `/how` → sub-prompt grammar; `~` = requirement/bridge (no slash); `` ` `` = shaded
  descriptor; split **Preload** (1–4) / **Highway** (5–0).
  *Resolved:* `~` is one glyph — the requirement **and** the continuity operator
  (coalesce / carry-forward / interleave prior session context & state); `` ` `` is
  **subordinate to `~`** as its descriptor.
- **Left-edge pass (superseded).** `~` = payloads; `!` = reasoning / lazy anchor;
  `@` = action / turn (reason→act); bare `!` = default anchor. Replaced by the reassignment above.
- **`$` coalesced (superseded).** `$` unified as one verb — *resolve/dereference*
  (shell `$x`, math `$…$`, localDNS). Replaced when `$` became tollbooth/known-good.
- **The Vision Board.** Introduced the QWERTY number-row mapping `!@#$%^&*()`; `^`
  instantiators, `&` rotary, `*` light, `()` intersection; the Kendall-tau turbulence /
  MASH panic-abort.
- **Highway/traffic model.** Road (paved, permanent) vs traffic; `^` = rotary (concentric
  wrapper lanes; cul-de-sac with no exit; child-highway with its own terminus), `=` =
  parallel-lane request (opens right), `%` = Gate, `$` = single terminus; lane discipline,
  semi-permeable boundaries, carry-forward at checkpoints. Spatial intuitions carried
  forward; most glyph bindings later reassigned.
- **First operators (superseded).** `^ & |` as sequence / compound / parallel; `.`-dotted
  nesting. Folded or rejected.
- **Origin.** `.claude/commands/workout.calibrate.md` — the first (and so far only) *paved*
  road that actually exists as a committed command.
