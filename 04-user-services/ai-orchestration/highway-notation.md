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
fulfilled by slash commands and a plain-language sub-prompt. A `'` **begins** it
(§1 — *Ignition*); the string means the same thing with or without one.

---

## 1. The backbone (`!@#$%^&*()`)

The number row is the road — and **"highway" has two senses:** *broad* (the whole physical
row) and *narrow* (keys **5–0**, the drivable road). Three **staging keys** sit off the
number row (`'`, `~`, `` ` ``); keys **1–4** are the **Preload** (stage everything); `%`
(key 5) is the **gateway on**; keys **6–0** are the open **Travel** road.

| Key | Glyph | Phase | Archetype | Meaning |
| :-- | :-- | :-- | :-- | :-- |
| `'` | `'` | Staging | Ignition | The **start signal**: everything from here rightward is read as Bifrost. Carries no sub-prompt and no slash command. **Optional by construction — a string means the same thing with or without it.** A **bare `'`** (nothing after it) is the **reference call** — it returns the sweep, `~!@#$%^&*()`. See the note below. |
| `~` | `~` | Staging | Continuity / Lazy Anchor | The plain-language **requirement**, the **continuity operator** (coalesce / carry-forward / interleave prior context/state; "stay in the Bifrost schema," loaded at session start), **and the immediate top-line lazy anchor** — see the note below. The **only archetype with no slash command**. Visual: a bridge. |
| `` ` `` | `` ` `` | Staging | Descriptor | Inline qualifier, renders **shaded**; **subordinate to `~`** — it hangs under the requirement and describes it (e.g. `` `yellow, large, browning, bunch` ``). A **bare descriptor** — backticked text with no backbone glyph anywhere in the message — is the **expansion call**: it has no requirement to qualify, so it generates one. See the note below. |
| `1` | `!` | Preload | Cargo | The **manifest** — *what* is carried. Cargo is not executed on loading; the road decides when each item acts. |
| `2` | `@` | Preload | Source — **read-only** | The **input address** *and a permission*: what this run may read, and **may not write**. (`@` natively means *at* — an address.) A path that appears only here is read-only; writing to it is out of bounds. |
| `3` | `#` | Preload | Repository — **write-allowed** | The **output address** *and the write permission*: what this run may create, modify, or overwrite. A junction that **is a repo**. Two-way — you read back from it as well. |
| `4` | `$` | Preload | Sanity / Tollbooth | The **sanity check** at the actual start — tollbooth, customs, security. Validates entry against the **known-good** baseline (house style / point of comparison). |
| `5` | `%` | Gateway | Weigh Station | Immediate pre-flight audit / calibration — **"are we compliant?"** The gateway *onto* the highway (first step of the narrow highway, 5–0). |
| `6` | `^` | Travel | Cars | The **vehicles**. Count of `^` = width of the highway (`^^^^` = 4 parallel lanes). Each `^` takes its own sub-prompt, making lanes **addressable** (`^ theme1 ^ theme2`). |
| `7` | `&` | Travel | Rotary (A777ance) — **the rabbit trail** | Turns off into a nested sub-loop that **runs the FULL highway process**, nested inside the main — it **opens another Bifrost inside this one**. Also the **deterministic/sequential** form — commands under one `&` run in order. **Same operation as `` ` ``**, at a different position: see the note below. |
| `8` | `*` | Travel | Stop Signal | A gate that is **red by default** — fail-closed. Nothing proceeds to the next road until governance clears it. A **bare `*`** (no `()`) is a full stop awaiting **manual release** — ungoverned means human-released, not deadlocked. |
| `9/0` | `()` | Travel | Governance | The **release conditions**. Everything inside must be satisfied (conjunction) before the `*` goes green. |

> **`'` is Ignition — the mobile-safe opener.** Reported from a phone: the apostrophe is the
> one character a mobile keyboard will not hold still. Smart punctuation silently swaps the
> straight `'` (U+0027) for the curly `'` (U+2019), autocorrect inserts one unbidden, a
> different keyboard drops it — and until now `'` sat in the **soft tier** (§3) where it meant
> nothing in particular. So the same string typed on a phone and on a desktop differed in a
> character with no defined meaning. **The rule that fixes it:** `'` is *always* the signal to
> begin the Bifrost, and it is defined so that its presence and its absence are the **same
> string**. The character the phone cannot stop producing now starts the road.
>
> - **With or without — identical.** `' ~ ! …` ≡ `~ ! …`. Ignition marks *where* the Bifrost
>   begins; it never changes *what* runs. Nothing downstream may read it as an argument.
> - **Form-agnostic.** `'` (U+0027), `'` (U+2019), `′` (U+2032) are one glyph. The schema must
>   not notice which one the keyboard chose.
> - **Idempotent, not a dial.** `''` ≡ `'`. Ignition is the one glyph immune to the `+` / `-`
>   intensity dials (§2) — a mark whose absence is harmless cannot also carry weight when
>   repeated.
> - **Off-road for turbulence.** Like `~` and `` ` ``, `'` sits off the number row and scores
>   `0` toward `K` (§5). A mobile-inserted apostrophe can never push a chunk toward MASH.
> - **Contractions are not ignitions.** A `'` with a letter on **both** sides — `don't`,
>   `founder's` — is prose inside a sub-prompt. Ignition is a `'` standing free: at the head of
>   the string, or between slots. Without this carve-out every English sub-prompt would re-fire
>   the schema.
>
> **Why this key.** The apostrophe is the punctuation a phone hands you most readily — it is on
> the first symbol page and autocorrect volunteers it — while both existing staging glyphs,
> `~` and `` ` ``, are buried behind the deeper symbols page. Ignition gives a thumb-typed
> string a reachable opener, and spatially it already sits where an opener belongs: on the home
> row, left of Enter — the last key before you send.

> **A bare `'` is the reference call — it returns the sweep.** Send `'` and nothing else and the
> answer is this string, and nothing else:

<!-- bifrost-sweep:start -->

> ```text
> ~!@#$%^&*()
> ```

<!-- bifrost-sweep:end -->

> **It is the gesture's own output, not a description of it.** On a laptop you hold `Shift` and
> slide a finger down the row; that is what lands on the screen. A phone has no row to sweep, so
> `'` **is** the mobile substitute for the gesture — and a substitute for a *hardware* act returns
> what the hardware returns. Not a legend, not a glossary, not the §1 table: **the row**.
>
> - **Deterministic — a lookup, not a generation.** The same bytes every time, every session,
>   every model. Nothing before it, nothing after it: no preamble, no trailing offer, no
>   adaptation to the surrounding conversation. A keyboard does not vary its output to suit the
>   conversation, and neither may this. Anything less hands the phone a worse Bifrost than the
>   laptop, which is the exact inequality Ignition exists to remove.
> - **It hands back the *order*, which is the part a phone cannot get for itself.** The glyph
>   *meanings* are already written down — §1's table, CLAUDE.md §H — and a phone can read those.
>   What a phone cannot do is *sweep*. So the reference call supplies the sequence, and the
>   sequence is the notation's meaning (§5: turbulence is measured as distance from this order).
> - **Two absences that are not omissions.** `` ` `` does not appear because `Shift` on that key
>   **is** `~` — you cannot sweep the row and un-shift one key at once; the descriptor is the
>   same key's unshifted face. And `'` itself does not appear, because Ignition is the *call*,
>   not a stop on the road.
> - **The sweep vs. the Golden Rule.** This string leads with staging `~`; the **Golden Rule**
>   against which §5 scores turbulence stays `!@#$%^&*()`, because staging glyphs are off-road.
>   Same row, two readings — the sweep is what the hand does, the Golden Rule is what the metric
>   measures.
> - **It does not break the with-or-without invariant.** That identity quantifies over
>   *non-empty* remainders: `' R` ≡ `R` for any `R`. Strip the `'` from a bare `'` and what is
>   left is the empty message — not a Bifrost at all — so the degenerate case was never bound by
>   the identity. `''` ≡ `'` still holds: same string back.
> - **Precedent — Bifrost already reads bare glyphs.** A bare `*` is a full stop awaiting manual
>   release; a bare `%` is a compliance check with no sub-prompt (§6, Example 1). A bare glyph is
>   the archetype with its slots empty, not a syntax error.
> - **Null effect, and that is the point.** It reads nothing, writes nothing, and runs no cargo —
>   there is no `!` manifest to fire and no `#` to write to. This matters precisely *because*
>   autocorrect inserts apostrophes unbidden: the character most likely to arrive by accident must
>   have the most harmless standalone meaning available. A stray `'` costs you eleven characters.
>   Fail-safe, in the same spirit as `*` being red by default.
> - **§G is out of scope — a stated deviation** (CLAUDE.md §3 requires the statement). §G governs
>   *inference*: lazy anchor → governed-warm body → concurrent vote. Returning a constant performs
>   none. There is no `p` to measure, nothing to vote on, and no draw to govern — sampling a fixed
>   string would be a category error, manufacturing variance where none is wanted. Note the
>   symmetry: §G's point is that temperature is a variance dial you may lose to a vendor while the
>   vote is the governor you own. This is the limiting case — **variance set to none, because
>   there was never anything to vary.**
> - **Enforced, not asserted.** The string is embedded in three surfaces (this file, CLAUDE.md §H,
>   `docs/bifrost.html`). `tools/check-docs.py` extracts all three between `bifrost-sweep` markers
>   and **fails if they differ by a byte**. Determinism across *calls* is worthless if the
>   *sources* have drifted — so the invariant is tested, not promised. **CLAUDE.md §H is the
>   canonical copy** (it is the one in context when the call is answered).

> **A backticked seed is the expansion call — `` `…` `` returns a filled-in line.** Put
> anything inside a descriptor pair, send nothing else, and Bifrost hands back one complete,
> schema-compliant line with **every backbone slot filled** — its best-effort manifest for that
> seed, written to be read, parsed, and tweaked by a human. The skeleton it fills:

<!-- bifrost-template:start -->

> ```text
> ~ (fill in) ! (fill in) @ (fill in) # (fill in) $ (fill in) % (fill in) ^ (fill in) & (fill in) * (fill in) ( (fill in) )
> ```

<!-- bifrost-template:end -->

> **That skeleton *is* the sweep, spaced.** Strike the `(fill in)` slots and the spaces and
> `~!@#$%^&*()` is what remains — the reference call's own string, now with room to write in.
> `tools/check-docs.py` asserts exactly that, so the template can never drift from the sweep it
> spaces out. The two calls are one gesture at two zoom levels: `'` hands back the **order**;
> `` `seed` `` hands back the order **with the slots filled**.
>
> **`*` and `()` are two slots, not one.** The skeleton spaces them apart on purpose: `*` takes
> its own sub-prompt — *what this light is for* — while `()` holds *what turns it green*. A bare
> `*` with no `()` is already legal (§1: a full stop awaiting manual release), so collapsing the
> two would hide the difference between a gate that has conditions and a gate that is waiting on
> a human. Eleven slots, filled left to right.
>
> - **Descriptor or expansion — the bare-glyph rule decides, and nothing existing changes.**
>   With a backbone glyph present anywhere in the message, `` `…` `` is the descriptor it has
>   always been: shaded, subordinate to `~`, hanging under the requirement. With **no** backbone
>   present, the descriptor has no requirement to hang under — so rather than qualify one, it
>   **generates** one. Same precedent as bare `*`, bare `%`, and bare `'`: a bare glyph is the
>   archetype with its slots empty, not a syntax error.
> - **Fill every slot; never drop one.** A slot with no obvious content still gets the best
>   available answer. The point is a *complete* draft the founder edits **down** — an omitted
>   slot is a decision made silently, a filled slot they delete is a decision made in the open.
> - **The seed comes back as the descriptor.** It is echoed on the `` ` `` line of the output,
>   so the founder can see what was *read* before judging what was written.
> - **`K = 0` by construction.** The expansion emits in Golden Rule order, so an expansion is
>   always a Straightaway (§5). Turbulence in the seed is not inherited — weaving is a thing the
>   founder does afterward, deliberately, which is what makes it a Scenic Route and not noise.
> - **`*` comes back RED, every time.** The expansion is a **proposal**: a manifest, and per §1
>   cargo is not executed on loading. Nothing ran, nothing was written, no `#` was touched. This
>   is the one-way door (§4) doing its job — precisely what makes it safe to draft an
>   irreversible `!` up front.
> - **`@`/`#` make the review worth doing.** Because those slots are now a permission pair
>   (above), an expansion is not merely a plan — it is a **declared write-set**. The founder
>   reads one line and knows what the run may overwrite before a wheel turns. A proposal you
>   cannot audit is a proposal you have to trust; this one you can check.
> - **Collapsible, because it exists to be edited.** Where the surface renders HTML — chat,
>   GitHub Markdown, this page — the line ships inside a `<details>` whose `<summary>` is the
>   `~` requirement: the reader sees the one-line intent, expands for the manifest, rewrites any
>   slot in place, and sends it back. Where HTML does not render, a plain fenced block. The fold
>   is not decoration — a nine-slot line is unreadable on the phone this schema was fixed for.
> - **A generation, not a lookup — the exact inverse of the reference call, and §G applies in
>   full.** A bare `'` returns a constant, which is why §G is out of scope *there*. An expansion
>   **composes**, so the doctrine binds: lazy anchor (`~` — the first token leaves before the
>   line is planned), governed-warm body, and a selector. **Stated deviation on the selector**
>   (CLAUDE.md §3 requires the statement): the governor here is not a jury but the **human at
>   the `*` gate** — a stronger selector than a plurality, and the reason the vote is skipped
>   rather than forgotten. When you want the vote anyway, put it in the cargo (`! /cardio`) and
>   the expansion carries its own panel.
> - **An empty descriptor returns the sweep.** No seed, nothing to fill — it degrades to the
>   reference call rather than inventing a requirement out of nothing.

> **`` ` `` and `&` are the same operation — nesting, at two positions** (founder's rule,
> 2026-08-08). `&` was already defined as the rotary that "runs the FULL highway process,
> nested inside the main." The expansion call does the identical thing from the other end of
> the row: it takes a plain-language seed and opens **another Bifrost inside this one**. So
> they are not cousins, they are one operator:
>
> - **`&` is the rabbit trail** (founder's gloss) — and the word carries the property that
>   matters: a rabbit trail is a digression **you come back from**. It may run as deep and as
>   long as it likes, but it never exits the property; it rejoins the main road upstream of the
>   outer light. A detour replaces the route, a rabbit trail suspends it. `&` is the second.
> - **`` ` `` nests at staging; `&` nests on the road.** `` `seed` `` ≡ `& seed` hoisted to
>   position zero. Whatever the rotary does to a slot mid-line, the descriptor does to the whole
>   message. That is why a *bare* descriptor can generate a line at all — nesting with no parent
>   road to nest inside must produce the road.
> - **Expansion is therefore recursive, by construction.** Any `&` in an expanded line is itself
>   a seed you can expand, to any depth. This is §4's "fixed notation, unbounded output" reached
>   from the other direction: the re-flag path grows a string *in time*, nesting grows it *in
>   depth*.
> - **Nesting *is* sequencing, seen from outside.** `&`'s second reading — commands under one
>   `&` run in order — is not a separate meaning. From the parent's frame a nested road is one
>   ordered step it waits on; from inside, that step is a whole highway. Same structure, two
>   frames.
> - **Turbulence treats them differently, and correctly.** `` ` `` is staging, so it scores `0`
>   toward `K` (§5); `&` holds position 7 on the Golden Rule and scores. Identical semantics,
>   different metric standing — because `K` measures *road shape*, and only one of the two is on
>   the road.
>
> **The greater traffic light is always the last bulwark** (founder's rule, 2026-08-08) — the
> invariant that makes unbounded nesting safe:
>
> - **Every nest adds a light; no nest ever removes one.** An inner `*` going green releases its
>   chunk **into its parent**, never into the world.
> - **Only the outermost `*` is load-bearing against reality.** It is the last thing between a
>   `!` and an effect that cannot be recalled, and it stands regardless of how many inner gates
>   already cleared. A child cannot vouch for its parent.
> - **Governance is a conjunction down the whole chain.** An effect must clear *every* light
>   from its own depth outward — so an inner gate can never be more permissive than the one
>   above it, and no amount of recursion can dilute the outer promise.
> - **Permissions intersect inward; gates conjoin outward.** A nested road may never write
>   outside its parent's `#`, and may never release past its parent's `*`. Those two sentences
>   are the whole safety story of the schema, and they are what let `~` stay reckless at any
>   depth: **nesting multiplies the reasoning, never the exposure.**

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
> **`@`/`#` is a permission pair, not a pair of arrows — the mount table** (founder's rule,
> 2026-08-08). Read as directions, the pair only *described* a run and could not be violated.
> Read as **permissions**, it states what a run may **not** do, which is a thing a gate can
> check:
>
> - **`@` is read-only.** Everything under `@` may be read and must not be written. A path
>   listed only in `@` is out of bounds for any write — fail-closed, in the same spirit as `*`
>   being red by default.
> - **`#` is write-allowed.** What the run may create, modify, or overwrite. Still two-way: a
>   `#` is also readable, which is why the old "destination" reading was never wrong, only
>   incomplete.
> - **They may overlap, and the overlap is the point.** The same path may appear under both —
>   `@ x  # x` means *read it, and you may write it*. `@` alone = read-only; `#` alone =
>   writable. Two slots, three states, one **mount table**: `@` read-only, `#` read-write.
> - **It breaks nothing already written.** An in-flight proposal to *swap* the two (`@`
>   destination, `#` source) was dropped for exactly this reason: it would have inverted every
>   string in this file. The permission reading keeps `@` reading and `#` writing and only
>   **adds** the guardrail, so every existing string stays valid and simply becomes checkable.
> - **This is where the one-way door (§4) gets its teeth.** "Irreversible cargo rides past a
>   light" is a posture until something says *which* paths an effect may touch. `#` is that
>   list; `@` is its complement. A gate can now ask a question with an answer: *is every write
>   in this chunk inside `#`?*

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

**Everything in `< > ? { } [ ] " : ;` is soft** — *glow-in-the-dark road lines* and
**secondary signage** (the creative-writing punctuation), **not hard syntax.** They add
visibility and disambiguate; drop them and the pipeline still means the same thing.

| Glyph(s) | Soft role |
| :-- | :-- |
| `?` | Back-reference reflector — points back to a `!` (its referent). |
| `< > { } [ ]` | Reflectors / visibility brackets — mark on-ramp/off-ramp edges, group hints. |
| `" : ;` | Secondary signage — creative-writing punctuation: soft labels, pauses, quotes for clarity. |

**`( )` is not in this tier.** Round brackets look like the visibility brackets above but are
**backbone** (keys 9/0) — they carry governance and are load-bearing. Dropping them changes
what the string means; dropping a `[ ]` does not.

**`'` is no longer in this tier either — it was promoted to Ignition (§1).** A glyph cannot be
both "meaningless creative-writing punctuation" and "the signal to begin," and the soft reading
is what made the mobile bug possible: an autocorrected apostrophe was undefined noise. Note the
directions differ — a soft helper may be **dropped** without changing the meaning; `'` may be
dropped **or added** without changing it. Ignition is the stricter promise, which is exactly why
it survives a keyboard that edits you.

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

**Staging glyphs are off-road.** `'`, `~` and `` ` `` hold no position in the Golden Rule, so
they contribute nothing to `K` and cannot be inverted against anything. This matters most for
`'`: an ignition mark a phone inserted on its own must never cost turbulence, or the mobile-safe
opener would drag well-formed strings toward MASH.

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

**Example 5 — ignition, thumb-typed** (all four lines are the *same string*):

```text
' ~ tighten the statement intro  ! /draft /trim  @ docs/statements/  # localDNS  $ house style  %
' ~ tighten the statement intro  ! /draft /trim  @ docs/statements/  # localDNS  $ house style  %
~ tighten the statement intro  ! /draft /trim  @ docs/statements/  # localDNS  $ house style  %
'' ~ tighten the statement intro  ! /draft /trim  @ docs/statements/  # localDNS  $ house style  %
```

Line 1 is typed with a straight `'`; line 2 is what a phone's smart punctuation actually sent
(curly `'`); line 3 is the same string with the keyboard having dropped the mark entirely; line
4 doubled it. **All four parse identically** — that invariance *is* the rule, not a tolerance
around it. The founder should never have to look at which apostrophe their phone chose.

Note also that `docs/statements/` and a sub-prompt like `the founder's intro` both contain
characters the soft tier would otherwise fight over; only a **free-standing** `'` ignites.

**Example 6 — the reference call** (the whole message is one character):

```text
'
```

Returns the sweep — `~!@#$%^&*()` — and nothing else. Not a legend: the row itself, exactly what
a laptop puts on screen when you hold `Shift` and slide down it. Reads nothing, writes nothing,
fires no cargo. The degenerate case of the most-reachable key on a phone keyboard is also the
safest thing a stray autocorrect can produce.

**Example 7 — the expansion call** (the whole message is a backticked seed):

```text
`bootstrap paradox`
```

Returns one filled-in line — every slot written, `*` still red, folded under its `~`:

```text
~ trace each kept artifact to an origin OUTSIDE its own lineage; where the answer is
  "an earlier copy of itself", mark it and cut the loop
  `bootstrap paradox`
  ! /audit /trace /retag /record
  @ 04-user-services/ai-orchestration/examples/workout-bootstrap-paradox-session.md
  @ docs/provenance.html  @ docs/architecture/warrant-sites.md  @ CLAUDE.md §3
  # docs/architecture/warrant-sites.md  # provenance tags, in place
  $ python3 tools/check-provenance.py --strict comes back green
  % transmission never promotes — a copy, a quote, a reformat or a plurality is not fresh
    contact; five descendants of one ancestor are one source
  ^ inherited-constants  ^ inherited-transcripts  ^ inherited-agreement
  & per lane: name the artifact → where did it enter from outside? → retag or cut → re-run $
  * each lane recorded before the next opens (a re-flag returns upstream via &)
  * (nothing tagged O/M whose only warrant is an earlier copy · every R/A carries a verify:
     route · check-provenance green · RCPS: recorded, committed, pushed)
```

What this example demonstrates that the earlier ones do not:

- **A seed, not a string, is the input.** Two words in a descriptor; a nine-slot manifest back.
  The founder's job shifts from *composing* the line to *editing* it — the cheaper job, and the
  one a human is better at.
- **`@` and `#` as permissions, and they overlap.** `CLAUDE.md` §3 and the worked-case transcript
  are `@`-only: read them, never rewrite them — which is exactly the point when the subject is
  inherited authority. `docs/architecture/warrant-sites.md` sits under **both**, because the
  audit table is what this run is *for*. Read the two slots together and you have the run's
  write-set before a wheel turns.
- **`&` as a rabbit trail, not a fourth lane.** The per-artifact interrogation is a nested road
  each lane goes down and returns from — not parallel to the three `^` lanes but *inside* each
  of them. Modelling it as a lane is the same error Example 4 warns about, from the other side.
- **The last bulwark, visible.** Two lights: a per-lane recording gate and the outer `()`. The
  inner one going green moves work into the outer chunk, never out of the repo — and the outer
  one still has to clear before anything is pushed.
- **It is a proposal, and it reads like one.** `*` is red, nothing was written, and every slot is
  legible enough to argue with. The expansion's value is not that it is right — it is that being
  wrong is now *cheap to see*.

---

## 7. Changelog & superseded passes

Newest first. Recorded so reviewers can trace intent; **git history of this file is the
exact line-by-line diff.** This is a live design — earlier passes were deliberately
superseded, not mistakes.

- **The expansion call · `@`/`#` as permissions · `&` ≡ `` ` `` · the last bulwark (current).**
  Four founder rules from one session (2026-08-08), and they turn out to be one design.
  **(1) The expansion call:** a **bare descriptor** — backticked text with no backbone glyph in
  the message — is a *seed*, and the answer is one complete line with **every slot filled**,
  collapsed under its `~` so a human can read, parse and tweak it. The skeleton is the sweep,
  spaced (`~ (fill in) ! (fill in) …`), and `tools/check-docs.py` now asserts that identity
  between `bifrost-template` markers so the two can never drift. `'` hands back the **order**;
  `` `seed` `` hands back the order **with the slots filled** — one gesture at two zoom levels.
  Unlike the reference call it is a **generation**, so §G applies in full, with a stated
  deviation on the selector: the governor is the **human at the `*` gate**, not a jury.
  **(2) `@`/`#` are a permission pair, not a pair of arrows** — `@` **read-only**, `#`
  **write-allowed**, and they may **overlap** (`@` alone = read-only; both = read-write). An
  in-flight proposal to *swap* the two was dropped because it would have inverted every string
  ever written; the permission reading keeps `@` reading and `#` writing and only **adds** the
  guardrail — so nothing breaks and the one-way door finally has a checkable question (*is every
  write in this chunk inside `#`?*). **(3) `&` is the same operation as `` ` ``** — nesting, at
  two positions: `` ` `` nests at staging, `&` nests on the road, `` `seed` `` ≡ `& seed`
  hoisted to position zero. So expansion is **recursive by construction**, and `&`'s sequential
  reading is just nesting seen from the parent's frame. `&`'s plain-language name is the
  **rabbit trail** — a digression you come back from. **(4) The greater traffic light is always
  the last bulwark:** every nest *adds* a light and none removes one; an inner `*` releases into
  its parent, never into the world; governance is a conjunction down the whole chain. Stated as
  a pair: **permissions intersect inward, gates conjoin outward** — which is what lets `~` stay
  reckless at any depth, because nesting multiplies the reasoning, never the exposure. Added
  Example 7.
- **The reference call returns the sweep, not a legend.** Corrected: a bare `'`
  returns the string **`~!@#$%^&*()`** and nothing else — the gesture's own output, exactly what
  a laptop puts on screen when you hold `Shift` and slide down the row. An earlier pass had it
  returning a thirteen-line glyph card; that was a *description* of the gesture where the founder
  asked for the gesture. The meanings were already written down (§1's table, CLAUDE.md §H) and a
  phone can read those — what a phone cannot do is **sweep**, so the call supplies the **order**,
  and per §5 the order is the notation's meaning. Two absences are structural, not omissions:
  `` ` `` cannot appear because `Shift` on that key *is* `~`, and `'` does not appear because
  Ignition is the call, not a stop on the road. The sweep leads with staging `~` while §5's
  Golden Rule stays `!@#$%^&*()` — same row, two readings.
- **The reference call is deterministic.** A **lookup, not a generation**: same bytes every call,
  every session, every model, nothing before or after it. The argument is the founder's — sliding
  a finger down the row on a laptop is a *hardware* act, so the phone's substitute for that
  gesture must inherit the hardware's determinism, or mobile gets a worse Bifrost than the
  laptop. A keyboard does not vary its output to suit the conversation. **§G is out of scope,
  stated per §3** — it governs inference, and returning a constant performs none. **Enforced:**
  `tools/check-docs.py` extracts the string from all three surfaces between `bifrost-sweep`
  markers and fails on a one-byte difference, CLAUDE.md §H canonical. Determinism across calls is
  worthless if the sources drift.
- **Bare `'` = the reference call.** Ignition with no road behind it, so the bridge shows you
  itself; the mobile affordance for "I can't sweep a row on a phone." It does **not** break the with-or-without invariant, which
  quantifies over *non-empty* remainders (`' R` ≡ `R`) — strip the mark from a bare `'` and what
  is left is the empty message, never a Bifrost, so the degenerate slot was always free. Follows
  the existing bare-glyph precedent (bare `*`, bare `%`). **Null effect by design:** reads
  nothing, writes nothing, fires no cargo — the character autocorrect inserts unbidden gets the
  most harmless standalone meaning available.
- **`'` promoted to Ignition — the mobile fix.** Founder-reported bug from a phone:
  the apostrophe is the one character a mobile keyboard will not hold still (smart punctuation
  swaps `'` for `'`, autocorrect inserts one unbidden, another keyboard drops it), and `'` sat in
  the **soft tier** where it meant nothing in particular — so the same string differed between
  phone and desktop in an undefined character. New rule: **`'` is always the signal to begin the
  Bifrost**, defined so that presence and absence are the *same string* (`' ~ !…` ≡ `~ !…`),
  form-agnostic across `'`/`'`/`′`, idempotent (`''` ≡ `'`, immune to the `+`/`-` dials), and
  scoring `0` toward turbulence — with a carve-out that a letter-flanked `'` (`don't`) is prose,
  not an ignition. Removed `'` from the §3 soft tier (now `" : ;`); noted the promotion is the
  *stricter* promise (a soft helper may be dropped without changing meaning; `'` may be dropped
  **or added**). Added §5 "staging glyphs are off-road" and Example 5.
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
