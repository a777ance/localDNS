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
| `~` | `~` | Staging | Requirement / Bridge | Plain-language **requirement**, and the **continuity operator** — it *coalesces, carries forward, and interleaves* prior session context / state (a callback/bridge to what came before). The **only archetype with no slash command**. Visual: a bridge. |
| `` ` `` | `` ` `` | Staging | Descriptor | Inline qualifier, renders **shaded**; **subordinate to `~`** — it hangs under the requirement and describes it (e.g. `` `yellow, large, browning, bunch` ``). |
| `1` | `!` | Preload | Payloads (Cars) | The cars/payloads themselves. *(The `!` reads visually as a car.)* |
| `2` | `@` | Preload | Signage | The signage / labelling on the road. |
| `3` | `#` | Preload | Repository | A junction that **is a repo** — the repository to work in or against. |
| `4` | `$` | Preload | Sanity / Tollbooth | The **sanity check** at the actual start — tollbooth, customs, security. Validates entry against the **known-good** baseline (house style / point of comparison). |
| `5` | `%` | Gateway | Weigh Station | Immediate pre-flight audit / calibration — **"are we compliant?"** The gateway *onto* the highway (first step of the narrow highway, 5–0). |
| `6` | `^` | Travel | Instantiators | Count of `^` = width of the highway (`^^^^` = 4 parallel lanes). |
| `7` | `&` | Travel | Rotary (A777ance) | Turns off into a nested sub-loop that **runs the FULL highway process**, nested inside the main. |
| `8` | `*` | Travel | Traffic Light | An open-ended gate where highways intersect. |
| `9/0` | `()` | Travel | Intersection | Bounds the external process the `*` light waits for. |

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

---

## 5. Topological drift & the MASH protocol

A broken order doesn't crash — the orchestrator measures how far the input sits from the
Golden Rule `!@#$%^&*()` via Kendall tau distance (inversions):

$$K = \sum_{i < j} \mathbb{I}(v_i > v_j)$$

- **Turbulence 0 — Straightaway:** perfect order; standard.
- **Turbulence 1–5 — Scenic Route:** deliberate weaving (e.g. `%` audit after `^`); customized physics.
- **Turbulence 6–15 — Spaghetti Junction:** computationally dense; heavy nested logic.
- **Turbulence > 15 — MASH:** the input is a keyboard-smash, not a road (`(*&#Q$(*#$(*&%!@`). Panic-abort: drop payloads and respond with human-centric intervention, not a dry syntax error.

---

## 6. Worked example

```text
~ 800 by 600 image of a banana  `yellow, brown`  ! /render /usage /composition  @ top right corner  # dashboard pre-built  $ the adjacent buttons on the dashboard  %
```

1. `~ 800 by 600 image of a banana` — **Requirement** (no slash command).
2. `` `yellow, brown` `` — **Descriptor** (shaded), subordinate to the `~` requirement: the colors.
3. `! /render /usage /composition` — **Payload**, fulfilled via those slash commands.
4. `@ top right corner` — **Signage**: placement.
5. `# dashboard pre-built` — **Repository**: the pre-built `dashboard` repo.
6. `$ the adjacent buttons on the dashboard` — **Known-Good**: match the adjacent buttons (house style).
7. `%` — **Weigh Station** (bare): compliance check.

---

## 7. Changelog & superseded passes

Newest first. Recorded so reviewers can trace intent; **git history of this file is the
exact line-by-line diff.** This is a live design — earlier passes were deliberately
superseded, not mistakes.

- **Bifrost naming, gateway split, soft helpers (current).** Named the schema **Bifrost**
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
