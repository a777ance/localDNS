# The Yggdrasil Bestiary — the creatures of the tree, and what each one is

<!-- provenance: A · design/lore mapping onto the branch-policy mechanics; the founder's cosmology · 2026-08-11 · verify: CLAUDE.md §3 (the ladder); tools/check-promotion.py (the eagle); tools/check-branch-cap.py (the deer); tools/ratatoskr.py (the squirrel) -->

> Companion to `cell-grammar.md`. That file names the modules of a *cell*; this one names
> the creatures of the *tree* — the branch-promotion ladder (`CLAUDE.md` §3) told as the
> ecosystem that actually lives on Yggdrasil. Held as a **reasoning language**, not a
> menagerie to build, it earns its keep. Where a creature names machinery that already
> exists, this file says so and points at the site; where it names a role, it fixes the
> role's bounds.

---

## The tree and the well

**Yggdrasil** is the world-tree — the standing working branch that spans every interacting
system (the t630 stack, the router, the bridges, the CRM). **Mímir's well
(Mímisbrunnr)** lies beneath its root: **`main`**, the vetted knowledge, the source of
truth the machine can *read*. The tree **drinks from the well** — the seed flows well→tree
at `SessionStart` — and the well is fed back only at the gate, one deliberate cherry-pick
at a time (tree→well).

**Three "sources of truth," layered — not in conflict:**

| Source | What it is truth *of* | In lore |
| ------ | --------------------- | ------- |
| The **founder** | authority and intent — out of scope for the machine, unsamplable | **Mímir**, keeper of the well; the spring above it |
| **`main`** | the repo's vetted knowledge | **the well** Odin drinks from |
| The **t630** | deployed *reality* (`CLAUDE.md` §0) | **Valhalla** — where a change is real, not merely written |

A future session must not "fix" one of these against another: they answer different
questions (*who decides* · *what is vetted* · *what is running*).

---

## Odin — learns the runes, brews the mead

**Odin** is the orchestration / high-seat layer. Two acts of the myth are load-bearing:

- **He wins the runes** by hanging nine nights on the windy tree, wounded "myself to
  myself" — knowledge is *taken from the tree at a cost*, not handed over. Odin *reads*
  every branch to learn; he does not get the runes for free, and neither does the layer
  that reads this repo to act in it.
- **He brews / wins the Mead of Poetry** (Óðrœrir) — the valuable generative *output*, the
  thing that grants its drinker the gift. The mead is the **product** (the Statements, the
  deliverables). Odin is the only one who reaches the well, and the only one who decides
  what the mead is worth pouring.

Everything below serves Odin at the tree; none of it *is* Odin. The animals carry, guard,
and prune — they do not decide.

---

## The four creatures — two already built, one new, one named

| Creature (lore-accurate) | Role on the tree | Site |
| ------------------------ | ---------------- | ---- |
| **Ratatoskr**, the squirrel who runs up and down carrying messages he did not write | the **agentic cherry-pick courier** — carries *chosen* commits one rung up the ladder | **NEW:** `tools/ratatoskr.py` + `.claude/agents/ratatoskr.md` |
| **The eagle** at the crown, who chases the squirrel off | the **top gate** — refuses a courier (or anyone) at the well; only Odin drinks | **ALREADY BUILT:** `tools/check-promotion.py` / the `promotion-guard` check |
| **The four harts** (Dáinn, Dvalinn, Duneyrr, Duraþrór) nibbling the leaves | **branch pruning** — leaves (feature branches) are nibbled back so the tree never overgrows | **ALREADY BUILT:** `tools/check-branch-cap.py` + doombox retirement |
| **Níðhöggr**, gnawing the roots below | **decay** — stale branches gnawing from beneath; what the doom drawer holds so nothing is lost to the gnawing | The doom boxes (`doombox/1-messy`) |

The satisfying part: the **eagle** and the **harts** are not new inventions — they are the
locks this repo already grew. The bestiary is mostly a *name* for sited machinery. Only
**Ratatoskr** adds a creature.

---

## Ratatoskr — a courier, never a judge

The squirrel is the one animal that *moves things*, so he is the one that needs the
tightest bounds. In the myth he carries words between the eagle and the serpent — **words
he did not author.** That is the whole discipline:

- **He carries the selection; he never makes it.** Odin chooses which commits are cream;
  Ratatoskr cherry-picks exactly those onto the next rung (feature → doom box → Yggdrasil),
  preserving authorship. A squirrel that decided *what* to promote would be the misaligned
  system — the judge wearing the courier's coat.
- **The eagle bounds his climb.** He may reach Yggdrasil; he may **never** carry into the
  well (`main`). `ratatoskr.py` refuses `--to main` in code, and the eagle
  (`promotion-guard`) refuses it again at the PR gate — the bound is sited twice, not left
  to the squirrel's manners.
- **He carries named commits, not whole branches.** Carrying a branch's entire lead is the
  full-branch merge the ladder forbids.
- **He does not resolve conflicts.** A conflict is a Norn's judgment call
  (`norns.md`); the courier aborts cleanly and reports.
- **He stacks; the founder pushes.** Carrying is local. The deliberate push — and the
  founder-approved PR into the well — stay human.

So Ratatoskr makes the ladder *fast* without making it *reckless*: the tedious mechanical
carry is automated, while every act of judgment (what is cream, what reaches the well,
how a conflict resolves) stays with Odin and the Norns. **Nesting the courier multiplies
the movement, never the authority.**

---

## The tether

This is a *vocabulary for the promotion ladder*, one language for three questions: *who
carries (Ratatoskr)? who is refused at the well (the eagle)? what keeps the tree from
overgrowing (the harts)?* Its cash value is that two of the three already have sites, the
third (the squirrel) now has one, and all of them cash out to the same rule the branch
policy already states: **the cream rises by selection, the well is Odin's, and nothing
promotes itself.** Held as the language you reason in — not a zoo you are obliged to
stock — it stays honest.
