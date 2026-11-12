# Thirty leans for the end-to-end build

Written 2026-11-12, about 01:40 UTC, at the founder's request: "e2e build. Present me with 30 of
your leans, ranked and sorted." A lean is a stated position, with its reason. Ranked 1 to 30 by how
much each moves the whole thing from the founder's intent to a real Statement in a customer's hand.
Sorted into five tiers. "End to end" is read here as: intent on `main` → the loop on `leader` → the
product → the live box → a kept document.

Who acts is marked: **[you]** needs the founder's hand, **[loop]** a session can do alone,
**[both]** the founder decides and a session does the work.

## Tier 1 · Without these there is no end to end

1. **Write the intent onto `main`, one page. [both]** `main` is emptied and reserved for intent, and
   holds none. Until a spec sits there, "is this still what we meant?" has nothing to be asked against.
2. **Deploy the volume layer on the t630. [you]** It is cleared to deploy and is the highest-value
   product unlock on the board. Nothing a session does in the repo substitutes for it.
3. **Produce one real, measured Statement for your own household. [both]** This is the first time
   the whole chain would run: box → numbers → composer → gate → document. Everything before it is rehearsal.
4. **Attach the repository to the scheduled loop (DEC-018). [you]** The loop turns only when you
   prompt it. The one unattended run did the work and lost it because it could not push.
5. **Point the loop at the product, by rule. [loop]** At most one tick in three may work on the loop
   itself. The night of 2026-11-11 was spent almost wholly on the loop; one product defect was found
   only when a session was aimed at product on purpose.
6. **A change to a hook gets your eyes before it merges. [both]** Tonight a session wrote the rules
   that judge it and merged them itself, again and again. That is the one kind of self-merge that
   should be a tile. Docs and ordinary tooling can stay self-merged.

## Tier 2 · The product chain, in the order it has to close

7. **Mint the Uptime Kuma key. [you]** Without it, two of the four figures on a Statement are
   omitted, by the honesty rule.
8. **Extend the Statement gate to the rendered page. [loop]** `tools/check-statements.py` covers the
   composer. The HTML renderer and the file-reading entry point are not covered.
9. **Reconcile live drift into the repo before deploying over it (Track 1). [you]** The box is the
   source of truth; deploying over unreconciled drift destroys evidence.
10. **Close the urgent exposure item (Track 4). [you]** It is marked urgent on the board and has
    waited since August.
11. **Rotate the Windows laptop's WireGuard key and identify peers .4 to .6. [you]** A known-exposed
    key on a VPN is the cheapest serious risk to remove.
12. **Snapshot what exists only on the box (Track 2). [you]** The repo is not a rollback target for
    anything it does not hold.
13. **Seal the real secrets into the vault. [you]** The tooling is in the repo; the sealed files are not.

## Tier 3 · Structure

14. **Do not sort files between `leader` and `outer` yet. [loop]** Two gates read across the whole
    tree. Sorting costs real work and breaks them, and buys nothing until two people or sessions are
    in each other's way. Leave `outer` as a full copy and say so.
15. **Set the default branch to `leader`. [you]** The setup script covers new sessions, but GitHub
    itself still opens pull requests against, and shows visitors, an empty branch.
16. **Define promotion in one paragraph. [both]** What goes to `main` (intent and spec only), who
    does it (you), and that each promotion is tagged.
17. **Delete the six branches marked safe to delete. [you]** They are fully contained in `leader`.
    Fifteen stray branches is noise in every fetch.
18. **Read the three old branches that hold unique work before anything else touches them. [loop]**
    `Yggdrasil` (48 commits), `doom-drawer/2026-08-08` (201), `cloudflare/workers-autoconfig` (128).
    A session can summarise what is in each so you can decide.
19. **Name session branches by cardinal. [loop]** `observe/…`, `orient/…`, `decide/…`, `act/…` into
    `leader`. It gives the per-step view you asked about, at no cost. Not four permanent branches.

## Tier 4 · Loop quality

20. **Do not enforce OODA order. [loop]** Boyd's loop is not a sequence. Enforce the dependency
    instead: no act on ground that has not been looked at. That is already the probe rule.
21. **Flag a run of acts with no observation. [loop]** Three or more `A` in a row with no `O`
    between is the pattern that exposed five blind trims in one evening. A warning, not a block.
22. **One rule in, one rule out. [both]** The Stop hook enforces eleven reply rules, added in one
    night. Each is small; together they are a tax on every reply. A new one should merge with or
    replace an old one.
23. **Run sub-loops one at a time inside the session (DEC-019). [you]** The parallel launch was
    stopped by the platform. Sequential is slower and works today.
24. **Shrink sections G and H of `CLAUDE.md`. [both]** They are 17,000 of 60,000 bytes loaded on
    every turn. It is the largest single cost cut available, and needs two checks repointed first.
25. **Record the cost of each session in the session log. [loop]** The failed tick cost 1.75
    dollars and the second session 2.36. Without the figure, "spend tokens like money" has no ledger.
26. **One probe that picks the others from a stated goal. [loop]** The four probes are fixed checks.
    A single entry point that chooses among them is the smallest honest form of "adaptive".
27. **Audit the prose-only rules or say why not (Q-035). [loop]** House style, provenance, and the
    Jury values are enforced by gates in part; the retrofit list should say which.

## Tier 5 · Do not do, or stop doing

28. **Do not turn on blocking mode. [you]** `warn` gives the reminder. `enforce` can lock a session
    out, has never run, and nothing tonight needed it.
29. **Close DEC-005 as NO GO. [you]** The venv files have waited on two facts from the laptop since
    the first session and nothing has been blocked by their absence.
30. **Stop three habits of this session. [loop]** Reading another session's event log (it returned
    a wall of text for one fact). Chaining slow steps in one call (ten breaches of the 10-second
    cap, all from that). Opening a pull request for each one-line record (nineteen in one night;
    batch them).

## How to read the ranking

- Leans 1 to 5 are the build. If only five things happen, these are the five.
- Nine of the first thirteen need your hand, and none of those is a session's to do. The loop is
  now further along than the product it exists to serve, and the product is waiting on the box.
- Leans 14, 20, 28 and 29 are positions against doing something. They are ranked where the
  temptation is, not where the work is.
