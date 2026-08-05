# Working conventions — carried into Claude Design

The A777ance way of working with Claude does not stop at the repo boundary. Claude Design
is another surface where components get authored, and everything that governs a Claude
Code session governs a Design session too: the briefing, the house style, the honesty
rule, the voice, the public/private invariant, Bifrost, and the git procedure.

This file is that carry-over, written for the Design surface specifically. It is the
**briefing** for design work — the same role `CLAUDE.md` plays for the stack.

**Read order at the start of a design session:** this file → `README.md` (in this folder)
→ the repo `CLAUDE.md` if the work touches anything outside `design-system/`.

---

## 1. The invariant that outranks everything else

**Never put private material into a Claude Design project.**

A Design project is a claude.ai artifact shared with whoever the founder shares it with,
and it is seeded **from this public repo**. So the public/private split in
[CLAUDE.md § Portfolio conventions](../CLAUDE.md#portfolio-conventions-all-a777ance-repos)
applies verbatim, with no softening for "it's just a mockup":

| Never in a Design project | Where it lives instead |
| ------------------------- | ---------------------- |
| Real household names, addresses, account numbers | `customers` (private) |
| A live operator roster or book of homes | `customers` (private) |
| Real QR codes (they encode a real account URL) | generated per household at statement time |
| Pricing, dues, unit economics, guild mechanics | `MARKETING` (private) |
| Keys, passwords, tokens, `.env` values | the sops+age vault |

Every component in `parts/` ships with `Sample …` names and `A77-000`-style placeholder
accounts for this reason. When a component needs to *look* populated, populate it with
obvious placeholders — not with a real month's data "just for the screenshot."

---

## 2. Honesty of the kept document, in design terms

The stack's honesty rule is about numbers on a Statement. Its design-surface form:

- **A component may exist before its data does. A Statement may not.** `How You Compare`
  and `Traffic Allocation` both live in this design system and neither may ship on a
  Statement sold for money — no cohort dataset, no per-category byte accounting. Both
  carry that fact in the card itself, in the component, where a designer reaching for it
  will actually read it.
- **Mark the gap in the component, not in a tracker.** A note in a backlog gets lost the
  moment someone copies the component. A `.stop` block inside the preview travels with it.
- **Placeholder data must look like placeholder data.** `Sample Household`, `A77-000`,
  round numbers. A realistic-looking fake is the one that eventually ships by accident.
- **If a check can't be run, drop the line.** Don't leave a green dot standing in for an
  assumption (see `Service status`).

---

## 3. Voice

Plain-English voice on every customer-facing surface — the Statements read the way a good
tradesperson talks to a homeowner, not how an IT person talks to a server. "Your
living-room TV," not "the endpoint." A grandparent should understand every word.

That rule extends to **component names and card labels**, because those names end up in
the section titles a customer reads. `Handled For You`, `See For Yourself`, `Our Read
This Month` — not `WorkLogModule`, `QRTileGroup`, `AssessmentPanel`. Internal foundations
(`Color`, `Type`, `Layout & rhythm`) may be plain design vocabulary; anything a homeowner
will see is written in their words.

The swap table lives in `DESIGN-Full-Workflow-Integration-end-to-end-/00-brand-identity/the-pitch.md`.

---

## 4. House style on a design surface

The portfolio-wide conventions (adopted 2026-06-05) apply here as written:

- **Time-based content reads newest-first.** Work logs, changelogs, "Handled For You",
  attention lists — most recent, or most urgent, at the top. This is a *component
  behavior*, not just a docs rule: a log component that renders oldest-first is a bug.
- **Alphabetical lists run Z → A.**
- **Walkthroughs: reverse the blocks, keep the steps.** Never renumber.
- **Gill Sans MT everywhere**, via `--font-sans`. Every surface, customer-facing or
  internal — including the design system's own foundation cards.

**Card ordering in the Design System pane.** Groups run `Foundations` → `Statement` →
`Portfolio`: foundations first because everything else is built out of them, then the two
documents in the order a household meets them. Within a group, cards follow the order the
sections appear on the real document — that is the walkthrough rule ("keep the steps")
applied to a page: a designer scanning the pane should be able to read down it and
recognize the Statement.

---

## 5. Bifrost on the design lane

Bifrost is active from the first token of every session, in every repo — and in Claude
Design. The glyphs map onto design work like this:

| Glyph | Archetype | On the design lane |
| :---- | :-------- | :----------------- |
| `~` | Continuity / lazy anchor | Open the component and start editing; let the token rationale coalesce mid-flight. Don't pre-reason a design system from scratch — the Statements already decided most of it. |
| `` ` `` | Descriptor | The qualifier hanging off the requirement — `` `bronze, tighter, one line` ``. |
| `!` | Payloads | The components themselves — the parts being moved. |
| `@` | Signage | The `@dsCard` markers: name, group, subtitle. Literally the signage. |
| `#` | Repository | `localDNS/design-system/` — the source of truth. The Design project is a *mirror*, never the origin. |
| `$` | Sanity / tollbooth | `python3 build.py --check` — does the committed bundle still match its sources? |
| `%` | Weigh station / compliance | The § 1 invariant and the § 2 honesty pass, run **before** any upload. This is the gateway; nothing goes up unweighed. |
| `^` | Instantiators | Component variants — how many states a card shows (severity levels, client vs. operator). |
| `&` | Rotary | A nested full pass on one component (extract → build → review → sync) inside a larger sweep. |
| `*` `()` | Traffic light / intersection | Waiting on the founder's review of a card before it lands. |

The guardrails that survive a keyboard-mash are the same three: **`~` continuity, `$`
sanity, `%` compliance.** On this lane `%` is the one that matters most — it is what
stands between a private roster and a shared design project.

Canonical spec: [`04-user-services/ai-orchestration/highway-notation.md`](../04-user-services/ai-orchestration/highway-notation.md).

---

## 6. The sync protocol

**Direction: repo → Design project.** `design-system/` is the source of truth; the Design
project is a rendered mirror of it. When they disagree, the repo wins — the same way the
live t630 wins against the config repo.

**Incrementally, one component at a time. Never a wholesale replace.** A full-project
overwrite destroys work someone else did in the Design UI and produces a diff nobody can
review. Push the component that changed.

The procedure lives in `/design-sync` (`.claude/commands/design-sync.md`) and reduces to:

1. `python3 design-system/build.py` — regenerate previews and `tokens.json`.
2. `%` — the compliance pass of § 1 and § 2 over anything about to go up.
3. `list_files` on the project, diff structurally against `previews/`.
4. Show the founder the plan: what gets written, what gets deleted.
5. `finalize_plan` → `write_files` (with `localPath`, so file contents never pass through
   the model's context) → done.

**Coming the other way.** If a component was authored in the Design UI first, it is not
real until it exists as a `parts/*.html` fragment in this repo, builds, and is committed.
Pull it down, author the part, rebuild, commit — then the two agree again.

---

## 7. Git

Design changes are ordinary changes and follow the repo's git conventions:

- **Push to `main`, no branches** — the founder's standing instruction (2026-06-05) for
  these repos. *(A change made by an agent working under an enforced feature branch lands
  on that branch and is fast-forwarded to `main` by the founder; the instruction is about
  where work comes to rest, not a licence to ignore the harness.)*
- **Never use the PR "watch" feature** — standing instruction (2026-08-03).
- **Rebuild before committing.** `build.py --check` must be green: a commit where
  `previews/` disagrees with `parts/` publishes a component nobody authored.
- **Run `python3 tools/check-docs.py`** before committing docs — it validates every link
  and repo-path reference in the repo, including the ones in this file.
- **One coherent commit per component**, with the *why* in the message. "Tighten the
  bronze rule under the header" is a design decision and the message is where it gets
  recorded — there is no ADR for type sizes.

---

## 8. Judgment calls

Design has more genuinely-arguable calls than config does. The § G sampling doctrine
applies: **don't consume a single warm draw where a verdict matters.** For a real
either/or — two layouts, two names, whether a component is honest enough to ship — run
`/cardio` (keyless, in-harness) and take the plurality. For a call you'd make in two
seconds, just make it; empanelling a jury on a 1px border is its own kind of waste.
