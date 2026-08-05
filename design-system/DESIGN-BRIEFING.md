# A777ance — briefing for Claude Design

**You are working on the A777ance design system inside Claude Design.** This file is your
briefing: it carries everything decided in the repo so you can work without guessing. Read
it top to bottom, then execute [§ 10](#10-do-this-now).

It is written to be self-sufficient — every token value and every rule is inline, so it
works whether or not you can see the repository.

**Canonical source:** `localDNS/design-system/DESIGN-BRIEFING.md`. If this document and the
repo disagree, the repo wins. If the repo and a **shipped Statement** disagree, the
Statement wins.

---

## 0. What this is

A777ance runs managed home networks for households — DNS filtering, encrypted DNS, VPN,
monitoring. The product a customer actually holds is a **monthly Statement**: a one-page
document proving the quiet was earned. The business is "pest control, not lawn care" — the
work is invisible, so the document has to make it visible.

Two documents, and everything in this design system comes out of them:

| Document | Who | What it does |
| --- | --- | --- |
| **Network Activity Statement** | The homeowner | The monthly value receipt — the "sticker on the door" |
| **Alliance Member Portfolio** | The operator | One view across a whole book of homes |

**Extracted, not invented.** Every token and component here was pulled out of documents that
already ship. That direction is the point: this system is a *description* of the Statements,
kept honest by being derived. Do not "improve" a value because it looks off-scale — find out
what ships first.

---

## 1. The invariant that outranks everything

**Never put private material into this design project.** A Design project is shared; treat
anything you add as published.

| Never | Where it actually lives |
| --- | --- |
| Real household or operator names, addresses, account numbers | a private repo |
| A live roster or book of homes | a private repo |
| Real QR codes — they encode a real account URL | generated per household at statement time |
| Pricing, member dues, unit economics | a private repo |
| Keys, passwords, tokens | a secrets vault |

Placeholders are `Sample Household`, `Sample Operator`, `A77-000`, `ALY-0000`. When a
component needs to look populated, populate it with obvious placeholders — never with a real
month's data "just for the screenshot." **A realistic-looking fake is the one that ships by
accident.**

---

## 2. Honesty of the kept document

People keep these documents. Never print a number the data doesn't support.

- **A component may exist before its data does. A Statement may not.** Two components in
  this system must not appear on a Statement sold for money (see [§ 6](#6-the-components)).
- **Mark the gap inside the component**, not in a tracker. A note in a backlog is lost the
  moment someone copies the component; a warning block inside the card travels with it.
- **If a check can't be run, drop the line.** Never leave a green status dot standing in for
  an assumption.

---

## 3. Voice

Write the way a good tradesperson talks to a homeowner, not how an IT person talks to a
server. **"Your living-room TV," not "the endpoint."** A grandparent should understand every
customer-facing word.

This governs **component names**, because those names become the section titles a customer
reads: `Handled For You`, `See For Yourself`, `Our Read This Month` — never `WorkLogModule`,
`QRTileGroup`, `AssessmentPanel`. Internal foundation cards (`Color`, `Type`,
`Layout & rhythm`) may use plain design vocabulary.

Name the person who did the work, in bronze. "Your appliance was updated" is a system
talking; "patched on your t630 by Jose" is a tradesperson.

---

## 4. House style

Portfolio-wide conventions. They bind components, not just documents.

- **Time-based content reads newest-first.** Work logs, changelogs, "Handled For You",
  attention lists — most recent, or most urgent, at the top. **This is a component
  behavior: a log that renders oldest-first is a bug, not a preference.**
- **Alphabetical lists run Z → A.**
- **Walkthroughs reverse the blocks but keep the steps in order, and never renumber.**
- **Gill Sans MT everywhere**, on every surface. Stack:
  `'Gill Sans MT', 'Gill Sans', Calibri, 'Trebuchet MS', sans-serif`.
  **Do not introduce a second typeface.** Hierarchy comes from size, weight, case, and
  letterspacing — the way the Statements already do it.

**Card order in the Design System pane:** `Foundations` → `Statement` → `Portfolio`.
Foundations first because everything is built from them, then the two documents in the order
a household meets them. Within a group, cards follow the order the sections appear on the
real document.

---

## 5. The tokens

The complete set. Take values from here; never sample one off a screenshot.

### Brand
Navy carries authority; bronze carries the human hand.

| Token | Hex | Use |
| --- | --- | --- |
| `--navy` | `#13314f` | Primary — headers, section titles, figures |
| `--navy-deep` | `#0e2640` | Gradient floor; text reversed out of bronze |
| `--navy-mid` | `#1c4a73` | Gradient ceiling — monogram, avatar, badge |
| `--bronze` | `#a9803f` | The accent that means *a person did this* |
| `--bronze-soft` | `#c6a463` | Bronze on navy, where the darker tone goes muddy |

**Spend bronze sparingly.** It marks the operator's name, the rule under the header, the edge
of a called-out block. Decorate with it and it stops meaning anything.

### Surface

| Token | Hex | Use |
| --- | --- | --- |
| `--paper` | `#fbfaf7` | The document. Warm — **never** pure white |
| `--canvas` | `#e9ecf0` | The desk the document lies on |
| `--white` | `#ffffff` | QR frames only |
| `--rule` | `#e6e2d6` | Warm hairline, on paper |
| `--rule-2` | `#eceef1` | Cool hairline, between table rows |

### Ink

| Token | Hex | Use |
| --- | --- | --- |
| `--ink` | `#1f2733` | Default text |
| `--ink-body` | `#3a4553` | Running prose |
| `--ink-sub` | `#5a6573` | Supporting detail under a heading |
| `--muted` | `#8a93a0` | Notes, captions, table headers |
| `--slate` | `#9aa7b4` | Furthest-back text |
| `--on-navy` | `#8fb0cc` | Text on the navy header and footer |
| `--on-navy-dim` | `#7e9fbb` | Account-field keys on navy |
| `--on-navy-link` | `#b8d0e6` | Links in the navy footer |

### Status
Severity order, worst first.

| Token | Hex | Use |
| --- | --- | --- |
| `--alert` | `#b4542a` | High severity — act now |
| `--neg` | `#a0524a` | Worse than the comparison baseline |
| `--amber` | `#c08a2e` | Medium — needs attention |
| `--watch` | `#2d6aa8` | Informational — worth a look, no action |
| `--pos` | `#3f7a4d` | Healthy; better than baseline |
| `--neutral-bar` | `#a8adb4` | Different, but neither good nor bad |

Washes: `--alert-wash #fbf2ec` · `--amber-wash #fbf6ea` · `--watch-wash #eef4fa` ·
`--pos-wash #eef4ef` (edge `#d7e6da`, ink `#2f5d3c`, sub-ink `#4a6a52`).

**Never carry state by color alone.** Every status is also spelled out in words — "Needs
attention", "High", "Healthy (17)". These documents get printed, photocopied, and read by
people who don't see red and green apart.

### Category ramp
Sequential, navy → bronze → stone, largest share first: `--cat-1 #13314f` · `--cat-2 #2d5a82`
· `--cat-3 #4d82a8` · `--cat-4 #7aa6c4` · `--cat-5 #a9803f` · `--cat-6 #c6a463` ·
`--cat-7 #ddd6c6`.

Traffic categories are ranked by volume, so the ramp reads as the ranking. **Don't use it for
unordered categories** — it will invent an order that isn't there.

### Component washes
`--chip-bg #eef2f0` · `--suggest-bg #f5f7f9` · `--privacy-bg #f2efe7` (ink `#5a5446`) ·
`--attn-bg #faf7f1` · alliance card gradient `#fbfaf7` → `#f3f1ea`.

### Type scale
Largest → smallest. Half-steps are deliberate — this is a dense one-page document and
11.5px vs 12px is a decision.

`--fs-display 28` · `--fs-figure 23` · `--fs-name 22` · `--fs-brand 21` · `--fs-mono 19` ·
`--fs-period 17` · `--fs-lg 15` · `--fs-md 13.5` · `--fs-base 13` · `--fs-body 12.5` ·
`--fs-sm 12` · `--fs-xs 11.5` · `--fs-2xs 11` · `--fs-3xs 10.5` · `--fs-4xs 10` ·
`--fs-5xs 9.5` · `--fs-6xs 9` (px).

Line height: `--lh-prose 1.6`, `--lh-tight 1.5`.
Letterspacing: `--ls-brand .16em` · `--ls-eyebrow .2em` · `--ls-label .18em` ·
`--ls-caps .16em` · `--ls-table .12em` · `--ls-loose .1em`.

**Tabular figures on every number in a column** (`font-feature-settings: "tnum"`). On a
document people compare month to month, a wandering column reads as sloppiness in the work.

### Space & line
`--page-w 740px` (client) · `--page-w-wide 760px` (operator) · `--gutter 44px` ·
`--gutter-sm 20px` (under 600px) · `--sp-section 26px` · `--sp-head 18px` · `--sp-row 13px` ·
`--sp-tight 9px`.

`--hairline 1px` · `--header-rule 3px` (the bronze rule under the header) ·
`--accent-edge 3px` · radii `4 / 8 / 10 / 20px` ·
`--shadow-page 0 6px 40px rgba(0,0,0,.13)`.

---

## 6. The components

Fifteen cards in three groups.

**Foundations** — Color · Type · Layout & rhythm

**Statement** (client, 740px) — Statement header · Account summary · Handled For You ·
Traffic allocation · Household profile · How You Compare · Our read this month · Connect in
the Alliance · See for yourself · Service status & privacy · Statement footer

**Portfolio** (operator, 760px) — KPI band · Needs your attention · Work log · Homes roster

### The two that must not ship

Both carry a warning block **inside the card**. If you edit either one, the warning stays.

- **How You Compare** — there is no real cohort dataset, so every "vs. the average home"
  percentage is invented. The *form* is settled and worth reviewing: diverging axis,
  better-is-green regardless of direction, a plain-English gloss under any metric a homeowner
  wouldn't recognize.
- **Traffic allocation** — the per-category byte accounting is scaffolded on the appliance
  but not switched on, so there is no measured number behind the slices.

Each earns a place on a real Statement the month its data becomes real. Not before.

### Rules worth knowing per component

- **Account summary** — green means *better*, not *bigger*. Queries down 2.1% and threats up
  3.2% are both positive. Decide which direction is good per row before coloring it.
- **Handled For You** — newest first, name the person in bronze, say what it meant to the
  household ("before anyone felt a lag"), not what was done to the machine.
- **Our read this month** — "Nothing to change" must be a real option. A month where a
  suggestion is invented to fill the space is the month the section stops being read.
- **Connect in the Alliance** — the opt-in sentence is part of the component, not a
  footnote. Ship them together or not at all.
- **See for yourself** — a QR tile without its lock line is a broken promise.
- **Service status** — every line is a claim the appliance actually verifies.
- **Needs your attention** — every row answers "is the client affected?" and names an owner.
- **Work log** — the scope column ("20 / 20") is the argument; order by reach, not effort.
- **Homes roster** — the counted legend is what makes the dot column honest in grayscale.

---

## 7. Bifrost — the design lane

Bifrost is the A777ance command notation: hold `Shift`, sweep the number row, each glyph an
archetype. It is active in every session, on every surface, including this one.

| Glyph | Archetype | Here |
| --- | --- | --- |
| `~` | Continuity / lazy anchor | Open the component and start; let rationale coalesce mid-flight. The Statements already decided most of it — re-deriving from scratch is the opposite of `~` |
| `` ` `` | Descriptor | The qualifier — `` `bronze, tighter, one line` `` |
| `!` | Payloads | The components themselves |
| `@` | Signage | The `@dsCard` markers — group, name, subtitle |
| `#` | Repository | `localDNS/design-system/` — the origin. **This project is the mirror** |
| `$` | Sanity | `build.py --check` — does the bundle still match its sources? |
| `%` | Compliance | The pre-upload gate: [§ 1](#1-the-invariant-that-outranks-everything) and [§ 2](#2-honesty-of-the-kept-document). **The load-bearing guardrail on this lane** |
| `^` | Instantiators | Component variants — how many states one card shows |
| `&` | Rotary | A nested full pass on one component |
| `*` `()` | Traffic light | Waiting on review before something lands |

Guardrails that survive a keyboard-mash: **`~` continuity, `$` sanity, `%` compliance.**

---

## 8. Where the source of truth lives

```
localDNS/design-system/
├── CONVENTIONS.md      the working rules (this briefing condenses them)
├── build.py            parts + tokens → self-contained previews
├── tokens/
│   ├── tokens.css      THE source of truth for the look
│   ├── base.css        shared page chrome
│   └── tokens.json     generated — do not edit
├── parts/              hand-authored fragments (edit these)
└── previews/           generated + committed (never hand-edit)
```

**Direction: repo → project.** The repo is the source; this project is a rendered mirror.

**Work done here is not real until it returns to the repo.** A component authored in Design
becomes real when it exists as a `parts/*.html` fragment, builds, and is committed. So: when
you change something here, **state plainly what changed and in which component**, so it can
be carried back. Don't assume the round trip is automatic.

**Incremental, one component at a time — never a wholesale replace.** A full overwrite
destroys work done in the UI and produces a diff nobody can review.

---

## 9. Known limits

- **The generator does not consume `tokens.css` yet.** Statements inline their own CSS per
  household, so the tokens are a faithful copy, not a shared dependency — changing a token
  here does not reach a customer's document. Two edits, and the Statement is the one that
  counts.
- **Component previews are flattened HTML**, composed by a build step, not a live component
  library. Each is self-contained with its CSS inlined, because a card has to render
  standalone.

---

## 10. Do this now

A real sequence — each step depends on the one before it.

1. **Take inventory.** List what this project already contains. If it's empty, say so.
2. **Load the system.** Import `localDNS/design-system/` — the `previews/` directory holds
   fifteen self-contained cards, each with an `@dsCard` marker on its first line giving its
   group and name. Take `tokens/tokens.css` as the palette.
3. **Check the grouping** reads `Foundations` → `Statement` → `Portfolio`, and that cards
   within a group follow the order the sections appear on the real document
   ([§ 4](#4-house-style)).
4. **Run the compliance pass** ([§ 1](#1-the-invariant-that-outranks-everything)) over
   everything now in the project. Flag anything carrying a real name, a real account number,
   a real QR code, a price, or a credential. Do not quietly fix it — **name it**, because its
   presence means something upstream leaked.
5. **Verify the two restricted components** still carry their warning blocks. If either lost
   it, that is a defect worth reporting before anything else.
6. **Check house style as component behavior.** Any log or list rendering oldest-first, or
   any alphabetical list running A → Z, is a bug.
7. **Report back**: what's in the project, what the compliance pass found, and anything where
   this briefing and what you see disagree.

Then wait. Don't restyle, rename, or "modernize" anything on your own initiative — this
system is derived from documents that already ship, and drift here becomes drift on a
customer's Statement.

---

## 11. Definition of done

Any change you make is finished when all of these hold:

- Every color and size came from [§ 5](#5-the-tokens) — no invented values, none sampled off
  a screenshot
- One typeface: Gill Sans MT, with the documented fallback stack
- Names read the way a homeowner talks ([§ 3](#3-voice))
- Time-based content renders newest-first; alphabetical runs Z → A
- No real name, account, QR code, price, or credential anywhere in it
- Any unmeasured-data component still carries its warning block
- Status is carried by words as well as color
- Numbers in columns use tabular figures
- You have said plainly what changed and in which component, so it can go back to the repo
