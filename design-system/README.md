# A777ance design system

The look, extracted from the shipped Statements and made reusable — and the bridge that
carries it into **Claude Design** (claude.ai/design) without losing any of the rules that
govern the rest of this portfolio.

Two things live here:

1. **The system itself** — tokens, base layer, and every Statement component as a
   self-contained preview.
2. **[`CONVENTIONS.md`](CONVENTIONS.md)** — how the A777ance way of working (house style,
   honesty rule, voice, public/private invariant, Bifrost, git) applies on a design
   surface. **Read that first** when starting design work.

---

## Where it came from

Nothing here was designed from scratch. Every token and every component was **extracted
from documents that already ship**:

- `docs/statements/client/*.html` — the Network Activity Statement (three archetypes)
- `docs/statements/operator/alliance-member-portfolio.html` — the Alliance Member Portfolio

That direction matters. The Statements are the product; this is a description of them,
kept honest by being derived rather than invented. When the two disagree, **the shipped
Statement wins** and this system gets corrected — the same rule as the live t630 versus
the config repo.

**Known drift (2026-08-05):** the generated Statements are self-contained by design — the
generator inlines their CSS per household — so they do **not** yet consume `tokens.css`.
Today the tokens are a faithful copy, not a shared dependency, and a change made here does
not reach a customer's document. Reconciling that (teaching
`docs/statements/tools/generate_client.py` to inline `design-system/tokens/` instead of
its own copy) is the next real step and is not done.

---

## Layout

```
design-system/
├── CONVENTIONS.md          ← the working rules, carried onto the design surface
├── README.md               ← you are here
├── build.py                ← composes parts + tokens → self-contained previews
├── tokens/
│   ├── tokens.css          ← THE source of truth for the look (hand-authored)
│   ├── base.css            ← shared page chrome (hand-authored)
│   └── tokens.json         ← GENERATED mirror of tokens.css — do not edit
├── parts/                  ← hand-authored fragments: @dsCard + <style> + markup
│   ├── foundations/        ← color · type · layout & rhythm
│   ├── statement/          ← the client Network Activity Statement, section by section
│   └── portfolio/          ← the operator Alliance Member Portfolio
└── previews/               ← GENERATED, committed, uploaded — do not edit
```

**Edit `parts/` and `tokens/*.css`. Never edit `previews/` or `tokens.json`** — they are
build output and the next `build.py` run will overwrite them.

---

## Build

```bash
python3 design-system/build.py            # regenerate previews/ + tokens.json
python3 design-system/build.py --check    # verify committed output matches sources (CI)
```

Standard library only, like every other tool in this repo.

The build exists to keep **one source of truth**. The palette is written once, in
`tokens/tokens.css`; previews get an inlined copy at build time because a Claude Design
card has to render standalone with no external requests. Nobody hand-maintains the second
copy, and `--check` fails the moment the two drift.

`build.py` also names **orphans** — a preview whose part was deleted or renamed. An orphan
still uploads and still shows a card, so it gets called out rather than left lying there.

---

## Sync to Claude Design

Run **`/design-sync`** (`.claude/commands/design-sync.md`). It builds, runs the compliance
pass, diffs against the remote project, shows you the plan, and pushes only what changed.

The `DesignSync` tool needs a design-system authorization that **`/design-login` can only
grant from an interactive terminal** — a Claude Code *web* session cannot get it. From the
web, either run the sync from a terminal session, or use Claude Design's "Send to Claude
Code Web" to seed the project into the workspace and work from there.

Two rules the command enforces, both from [`CONVENTIONS.md`](CONVENTIONS.md):

- **Incremental, one component at a time — never a wholesale replace.** A full overwrite
  destroys work done in the Design UI and produces a diff nobody can review.
- **The compliance gate runs before anything uploads.** No real names, no real accounts,
  no real QR codes, no pricing, no secrets.

---

## What's in the system

| Group | Cards |
| ----- | ----- |
| **Foundations** | Color · Type · Layout & rhythm |
| **Statement** (client) | Statement header · Account summary · Handled For You · Traffic allocation · Household profile · How You Compare · Our read this month · Connect in the Alliance · See for yourself · Service status & privacy · Statement footer |
| **Portfolio** (operator) | KPI band · Needs your attention · Work log · Homes roster |

Two of these **must not ship on a Statement sold for money**, and say so inside the card:

- **How You Compare** — no real cohort dataset exists; every peer percentage is invented.
- **Traffic allocation** — the per-category byte accounting is scaffolded on the appliance
  ([CLAUDE.md § F](../CLAUDE.md#f-nftables-volume-layer--deploy-checklist)) but not stood up.

They live here so the *form* is settled and reviewable. They earn a place on a real
document the month the data behind them is real.

---

## Adding a component

1. Author `parts/<group>/<name>.html`:
   ```html
   <!-- @dsCard group="Statement" name="Plain English name" subtitle="what it shows" viewport="740x360" -->
   <style> /* component-only CSS — shared chrome belongs in tokens/base.css */ </style>
   <div class="page"> … </div>
   ```
   The `@dsCard` comment **must be the first line** — the Design System pane builds its
   card index from it.
2. Use tokens (`var(--navy)`), not hex values. A literal hex in a part is a token that
   went missing.
3. Name it the way a homeowner would (`CONVENTIONS.md` § 3).
4. Populate it with obvious placeholders — `Sample Household`, `A77-000` (§ 1).
5. `python3 design-system/build.py`, then `/design-sync`.

---

## Further reading

- **[`CONVENTIONS.md`](CONVENTIONS.md)** — the working rules on the design surface
- **[`../CLAUDE.md`](../CLAUDE.md)** — the stack briefing; § I covers this bridge
- **[`../docs/statements/README.md`](../docs/statements/README.md)** — the Statement gallery and generator
- **[`../04-user-services/ai-orchestration/highway-notation.md`](../04-user-services/ai-orchestration/highway-notation.md)** — Bifrost, including the design lane
