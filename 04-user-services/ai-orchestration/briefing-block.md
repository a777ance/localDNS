# Bifrost — the portfolio briefing block (canonical)

**This file is the single source for the Bifrost section carried by every A777ance repo's
`CLAUDE.md`.** Bifrost is declared active in every repo, so every repo's briefing has to
decode a string the same way — and the only way a dozen hand-maintained copies stay in
agreement is for them to stop being hand-maintained.

`tools/sync-briefings.py` renders the block below into each sibling repo between
`bifrost-briefing:start` / `:end` markers. Those rendered blocks are **build output — never
hand-edit them.** Edit this file, re-run the generator, commit the result.

**Why a generator and not a checklist.** Copies drift silently: git only conflicts when two
sessions touch the *same* file, and these are different files required to *agree*. Two
parallel sessions can each be green, each push cleanly, and leave the portfolio
self-contradictory — which is exactly how nine repos ended up without Ignition after it
landed here. Agreement between copies is not evidence of correctness (the provenance rule:
sources sharing an ancestor are one source), so the invariant is given a site instead of an
author. See `docs/architecture/warrant-sites.md`.

**Scope — two tiers, deliberately.** This block is the *condensed* portfolio form. The
*long* form is `CLAUDE.md` §H in this repo, which carries localDNS-specific material (§G
cross-references, the deploy context) that would be meaningless in `MARKETING`. The two are
not generated from each other, so `sync-briefings.py --check` asserts the one thing that
must never diverge between them: the **backbone glyph→role assignments**.

---

<!-- bifrost-briefing:start -->
**Bifrost** is the A777ance command-composition schema — a keyboard-spatial notation
(`~ ! @ # $ % ^ & * ()` swept left→right, each glyph an *archetype* fulfilled by slash
commands + a plain-language sub-prompt). It is **active from the first token of every
session, in every repo:** adopt the `~` lazy-anchor posture — fire the first token ASAP
(the *model* stays high), let continuity coalesce mid-flight — and read Bifrost notation
per the schema whenever used.

- **Backbone:** `'` ignition (begins the Bifrost) · `~` continuity/lazy-anchor · `` ` ``
  descriptor · `!` cargo (a *manifest* — not executed on loading) · `@` source (read from) ·
  `#` repo/destination (write to) · `$` sanity · `%` compliance · `^` cars/lanes · `&` rotary
  (also the sequential form) · `*` stop signal (red by default) · `()` governance (release
  conditions). Off-row `'`/`~`/`` ` `` stage; keys 1–4 **Preload** form a complete manifest —
  *what · from where · to where · against what*.
- **`'` is always the signal to begin the Bifrost** (founder's rule, 2026-08-07 — fixes a
  mobile bug). Treat `'`, `’` (curly) and `′` as one glyph, and treat **presence and
  absence as the same string**: `' ~ !…` ≡ `~ !…`, `''` ≡ `'`. It marks *where* the Bifrost
  starts, never *what* runs — no sub-prompt, no `/how`, no intensity dial, `0` turbulence. A
  letter-flanked `'` (`don't`, `founder's`) is prose in a sub-prompt, not an ignition; only a
  free-standing `'` ignites. Never ask which apostrophe the phone chose.
- **A bare `'` (the whole message) = the reference call. Return this string and NOTHING else:**

  ```text
  ~!@#$%^&*()
  ```

  It is **the sweep itself** — exactly what sliding a finger down the row on a laptop puts on
  the screen. Not a legend, not a glossary, not a table: the row. So it is a **lookup, not a
  generation** — same bytes every call, every session, every model. No preamble, no trailing
  offer, no adaptation to the conversation. Answer *immediately*; it reads no file and fires no
  cargo. Glyph *meanings* live in the backbone above; the reference call hands back the
  **order**, which is the thing a phone cannot sweep for itself.
- **`*` cuts the road into Dispensations** — bounded, self-governing chunks. Governance has
  three outcomes: satisfied → green · **re-flagged** → return upstream via `&` (this is what
  lets a fixed string produce unbounded output) · unsatisfiable → eject to the shoulder.
- **The one-way door:** `~` rushes the reasoning, `*` gates the *effects* — anything
  irreversible (publish, deploy, send, push) rides past a light, which is exactly what makes
  the lazy start affordable.
- **Cars:** explicit `^` beats inferred. With no `^`, `!`'s command arity instantiates lanes
  1:1; with `^` present, `^` sets the lanes and `!`'s commands are the per-lane pipeline.
- **Guardrails survive a keyboard-mash:** `~` continuity, `$` sanity, `%` compliance — plus
  `*()` **governance**, the only one that repeats at every chunk boundary. `+` / repetition =
  more; `-` inverts into a stress test.

Canonical spec —
markdown: <https://github.com/a777ance/localDNS/blob/main/04-user-services/ai-orchestration/highway-notation.md>
· rendered page: <https://a777ance.github.io/localDNS/bifrost.html>
<!-- bifrost-briefing:end -->
