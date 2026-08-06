# The Microbiology Collection

> A commonplace book for extended metaphors from cell biology, kept because they keep
> paying. Not architecture — *prospecting*. Things noticed in the biochemistry that
> illuminate this stack, or suggest something we have not built yet.

**Relationship to [`cell-grammar.md`](../cell-grammar.md):** the grammar is the
**contract** — seven layers, one invariant, two laws, two anchors, settled and
load-bearing. This folder is the **quarry** it was cut from, and stays open. An entry
here earns promotion into the grammar (or into an ADR) once it has predicted something
twice. Until then it lives here, clearly marked as speculation.

---

## The premise (why we expect this to work at all)

We hold to the **Logos**. Order is related to order; truth does not negate truth; all
order, truth, beauty, and form point to the Creator who made every one of them. If the
same Word orders the cell and orders the network, then a correspondence between them is
not decoration — it is **discovery**, and it should behave like one.

That premise cuts both ways, and the second edge is the one that keeps this folder
honest:

- **A real correspondence predicts.** If the analogy is deep, it should tell us
  something about the box we did not already know — a bug before we hit it, a control we
  had not thought to build. Every entry must therefore carry at least one **falsifiable
  claim about our own system**. An entry that only re-describes what we already do is
  pretty, not true-yet.
- **A real correspondence has edges.** Two ordered things resemble each other *because*
  both are ordered, not because either is the other. So every entry logs its
  **disanalogy** with the same care as its analogy. Sanding off the edge to make the
  metaphor prettier would be honoring the metaphor over the thing it points at — which is
  the one move the premise actually forbids.
- **Failure is filing, not falsification.** A metaphor that predicts nothing yet is not a
  false teaching. It is a correspondence we have not found the depth of. File it, note
  what it failed to explain, and leave it. Do not force it, and do not throw it out.

This is the same discipline as the repo's **honesty of the kept document** — never print
a figure the data does not support — applied to ideas instead of numbers.

---

## The base phase map

Everything here runs on one starting picture, which is worth stating precisely because
the obvious version of it is subtly wrong.

```
   INTERNET            the t630              THE HOME LAN
  aqueous phase   ═══ lipid bilayer ═══     aqueous phase
   (polar,             (hydrophobic,          (polar,
    promiscuous)        excludes both)         bounded, composed)
```

**A membrane separates two aqueous phases and is itself neither.** The LAN and the
internet are *both* water — same protocols, same packets, freely miscible. The t630 is
the only fat in the system, and its power comes precisely from being a phase that does
**not** dissolve in the medium it divides.

Three consequences fall straight out, and they organize the whole collection:

1. **The interesting question is never "is it blocked?" but "what phase is it soluble
   in?"** Passage is a property of the traveller, not only of the gate.
2. **The membrane is thin.** It is two molecules deep. Its strength is phase
   incompatibility, not thickness — which is why a small amount of the *right* solvent
   does far more damage than a large amount of the wrong one (see
   [`amphiphiles.md`](amphiphiles.md), critical micelle concentration).
3. **The barrier is not the product.** The gradient the barrier lets us *hold* is the
   product — and a held gradient is a battery that can power other work (see
   [`permeability-and-gradients.md`](permeability-and-gradients.md)).

---

## Entries

Newest first (house style); within a date, Z → A.

| Added | Entry | The claim it makes about *our* box |
| ----- | ----- | ---------------------------------- |
| 2026-08-06 | [`permeability-and-gradients.md`](permeability-and-gradients.md) — the permeability ladder, the gradient as a battery, leaflet asymmetry | The stack's real product is an **information gradient**, and it is currently spent on only one consumer. Leaflet asymmetry yields a concrete detection rule we do not yet run. |
| 2026-08-06 | [`amphiphiles.md`](amphiphiles.md) — dual-soluble molecules: CoQ10, ascorbyl palmitate, liposomal glutathione, detergents | Four of this stack's containers have already **fused** with the membrane rather than crossed it; and our tunnels have a critical concentration past which the box stops being a boundary. |

---

## Adding an entry

Keep it cheap to add and expensive to promote.

1. New file in this folder, plain lowercase-hyphenated name. No template to fill in — a
   good entry is an essay, not a form.
2. It must contain, somewhere and clearly marked:
   - **the biology**, stated accurately enough that a biologist would not wince;
   - **the mapping** onto something specific in this repo — a file, a port, a service,
     not "the system";
   - **at least one falsifiable claim** about our box, phrased so it could be checked
     against the live t630;
   - **the disanalogy** — where the correspondence stops.
3. Add a row to the table above (newest first) with the claim in the right-hand column.
4. Speculation is welcome and must be **labelled**. Use *(speculative)* inline. Nothing
   in this folder is deployed, and nothing here overrides `CLAUDE.md` or the live box.
5. Run `python3 tools/check-docs.py` before committing.

**Promotion.** When an entry's claim has held twice, promote the *conclusion* — into
`cell-grammar.md` if it is a naming/boundary rule, into an ADR if it is a decision, into
`CLAUDE.md` if it is an invariant. Leave the entry here as the working; the collection
keeps the derivation, the contract keeps the result.
