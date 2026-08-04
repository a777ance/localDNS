# Bifrost — parse + score

Stages 1 and 2 of the Bifrost dispatcher. Canonical spec:
[`../highway-notation.md`](../highway-notation.md).

```
PARSE   a glyph string  ->  an ordered list of Segments
SCORE   those segments  ->  a Kendall tau turbulence score + band
ROUTE   deliberately not here — see "Why route is missing" below
```

Standard library only. `parse()` and `score()` are pure functions with no
side effects, so the whole thing is offline-testable and safe to import.

---

## Use

```bash
python3 bifrost.py "~ resize the banner \`800x600\` ! /render @ top right # dashboard \$ house style %"
python3 bifrost.py --json "…"          # machine-readable
python3 test_bifrost.py                # 36 tests, stdlib unittest
```

Exit code is `2` when the score lands in MASH (a panic-abort), `0` otherwise.

```python
from bifrost import parse, score

p = parse("! /render the banana @ top right")
score(p).band        # 'Straightaway'
p.backbone[0].commands   # ['/render']
```

---

## The two normalizations

These are the whole design. Both exist so the score measures **topological
order and nothing else**.

**Staging glyphs are excluded from the count.** `~` and `` ` `` sit off the
number row and carry no Golden Rule rank, so they cannot be out of order
with respect to it. Counting them would score a perfectly legal lazy anchor
as turbulence — and `~~~~~~~`, the *laziest* anchor, would score worst of
all. It scores 0, as it must.

**Intensity collapses before the count.** `$$$$` and `$+++` are one node
carrying `intensity=4`, not four nodes. Without this, an emphatic but
perfectly ordered string accumulates inversions purely from repetition and
can cross into MASH — a panic-abort triggered by the user pressing *harder*
on a guardrail, which is exactly backwards. `test_emphatic_ordered_string_stays_straightaway`
is the regression test for it.

Adjacency is what distinguishes emphasis from recurrence: `$$$$` is one
emphatic tollbooth, but `$ … % … $` is two separate visits and lexes as two
nodes. Only adjacent runs collapse.

`-` (stress) is recorded per-segment and likewise never moves the score.

`n` is a dozen glyphs at most, so the naive `O(n²)` double loop is correct
and instant. Kendall tau does not need to be clever here.

---

## Glyph collision, and a spec gap

The one real lexing hazard is a glyph appearing inside prose: a `#` in a
branch name, a `$` in a shell snippet. A descriptor span shields them —
everything between backticks is consumed whole as one `Descriptor` segment
and never scanned for glyphs:

```
~ deploy `use $HOME and #main`  ! /run     ->  ~  `  !     (3 segments, 1 ranked)
```

**A descriptor span is the only masking the notation supports.** There is no
general escape for a literal glyph in ordinary sub-prompt text. This module
does not invent one — an unbalanced backtick is treated as a bare glyph and
the text after it lexes as notation
(`test_unbalanced_backtick_falls_through` pins that behavior).

If the spec later grows an escape, it belongs in `../highway-notation.md`
first and here second. Inventing syntax in the implementation is how a spec
and its parser start disagreeing.

---

## Why route is missing

Routing dispatches to real slash commands and repos, and a supervisor
already does that on the live t630 — the LangGraph `langgraph-router/`
noted as missing in `CLAUDE.md` §C. Writing a second router from the spec
would mean inventing it from documentation rather than reading it off the
machine, putting a plausible fiction in a repo whose entire value is being a
faithful rollback target.

Parse and score are safe to build now precisely because they are pure: they
have no opinion about what a `#` *does*, only that it is a Repository
archetype sitting at rank 3. Route lands when it can be snapshotted.

---

## What this proves

The spec is self-consistent enough to execute. The §6 worked example parses
to exactly the seven documented segments and scores `Straightaway`; the §5
keyboard-smash scores 65 and panics. Those are tests, not claims —
`TestWorkedExample` and `TestMashProtocol`.
