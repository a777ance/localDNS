# The superqueue

Written 2026-11-12, about 01:55 UTC. One ordered queue for everything: the thirty leans
(`docs/ai-cto/leans-e2e.md`), the open decisions (`docs/ai-cto/blocked.md`), and what was left in
the old queue in `docs/ai-cto/handoff.md`. The order follows `docs/ai-cto/dependency-map.md`.

This file is the queue the Stop hook and the compaction hook read. A session takes the first item
in the loop's lane that is not `DONE` and not `BLOCKED`. Tick an item by adding ` · DONE <commit> ·`
after its bold title. Each line names its lean number in brackets.

## The loop's lane (a session does these alone, in this order)

- **SQ-001 · Extend the Statement gate to the rendered page.** · DONE a93dfe9 · [lean 8] `tools/check-statements.py` covers the composer only. Cover the HTML renderer and the file-reading entry point, or say exactly what cannot be covered. Done: the gate asserts on rendered output, and fails if a figure appears that the input did not carry.
- **SQ-002 · Write the product-ratio rule into the loop tick.** · DONE ee80342 · [lean 5] In `docs/ai-cto/loop-tick.md`: at most one tick in three may work on the loop itself; the session log's last three entries decide. Done: the rule is in the file and the tick's Decide step applies it.
- **SQ-003 · Draft the one-page intent for `main`.** [lean 1] A draft on `leader` for the founder to edit and promote; the loop does not write to `main`. Done: a draft exists and a DEC entry asks for the promotion.
- **SQ-004 · Draft the promotion paragraph.** [lean 16] What goes to `main`, who does it, and that each promotion is tagged. Done: one paragraph in `docs/ai-cto/branches.md`.
- **SQ-005 · Summarise the three old branches that hold unique work.** [lean 18] `Yggdrasil`, `doom-drawer/2026-08-08`, `cloudflare/workers-autoconfig`: what each holds that `leader` does not, in ten lines each. Done: the summaries are in `docs/ai-cto/branches.md`.
- **SQ-006 · Record each session's cost in the session log.** [lean 25] Done: the log's template has a cost line, and the two known figures from 2026-11-12 are entered.
- **SQ-007 · Flag a run of acts with no observation.** [lean 21] In `.claude/hooks/cardinal.py`: three or more act calls in a row with no observe or orient call between them gets a warning. Done: a test case in `tools/check-matrix.py`. This changes a hook: see SQ-104.
- **SQ-008 · Audit the prose-only rules, or name the gate that does. · DONE bd67027 ·** [lean 27, old Q-035] Done: `python3 tools/matrix.py orient.retrofit` lists house style, provenance, and the Jury values.
- **SQ-009 · One probe that picks the others from a stated goal. · DONE 92dcb24 ·** [lean 26] Done: one method takes a goal in plain words and runs the probes that fit it.
- **SQ-010 · Name session branches by cardinal.** [lean 19] Done: one line in `docs/ai-cto/branches.md`, and the setup script names a moved session accordingly.
- **SQ-011 · Proposal: shrink sections G and H of `CLAUDE.md`.** [lean 24, old Q-039] Measure, say which checks must be repointed, and write a DEC entry. Do not move anything.
- **SQ-012 · Proposal: where lane 0 sits in the Bifrost notation.** [old Q-036] A DEC entry only. Do not edit the spec.

## Your lane (only the founder can do these; ordered by what they unblock)

- **SQ-101 · BLOCKED on you · Deploy the volume layer on the t630.** [lean 2] Unblocks the first real Statement. The checklist is `docs/architecture/volume-layer-deploy.md`.
- **SQ-102 · BLOCKED on you · Attach the repository to the scheduled loop (DEC-018).** [lean 4] In the Claude app, on the task "localDNS loop tick". Unblocks the unattended loop.
- **SQ-103 · BLOCKED on you · Say how sub-loops should run (DEC-019).** [lean 23] The lean is: one at a time, inside the session.
- **SQ-104 · BLOCKED on you · Decide whether a hook change needs your eyes before it merges.** [lean 6] Until you say yes, sessions keep merging their own hook changes.
- **SQ-105 · BLOCKED on you · Mint the Uptime Kuma key.** [lean 7] Unblocks two of the four figures on a Statement.
- **SQ-106 · BLOCKED on you · Reconcile live drift into the repo (Track 1).** [lean 9]
- **SQ-107 · BLOCKED on you · Close the urgent exposure item (Track 4).** [lean 10]
- **SQ-108 · BLOCKED on you · Rotate the Windows laptop's VPN key; identify peers .4 to .6.** [lean 11]
- **SQ-109 · BLOCKED on you · Snapshot what exists only on the box (Track 2).** [lean 12]
- **SQ-110 · BLOCKED on you · Seal the real secrets into the vault.** [lean 13]
- **SQ-111 · BLOCKED on you · Set the default branch to `leader`.** [lean 15] GitHub: Settings, General, Default branch.
- **SQ-112 · BLOCKED on you · Delete the six branches marked safe to delete.** [lean 17] The list is in `docs/ai-cto/branches.md`.
- **SQ-113 · BLOCKED on you · Close DEC-005, or send the two facts from the XPS.** [lean 29, old Q-038]
- **SQ-114 · BLOCKED on you · Decide "one rule in, one rule out".** [lean 22]
- **SQ-115 · BLOCKED on you · Run `bash tools/laptop-sync.sh install` on the XPS and send the output of `status`.** [old Q-037]
- **SQ-116 · BLOCKED on you · Write the lanes' instructions for the superfleet, and run a first scenario.** [DEC-020] The plan is `docs/ai-cto/superfleet.md`. S09 (three lanes, one per old branch) is the smallest to try first.

## After your lane moves

- **SQ-201 · BLOCKED on SQ-101 · Produce the first real, measured Statement.** [lean 3] Soft needs: SQ-105 and SQ-001. This is the end of end to end.
- **SQ-202 · BLOCKED on SQ-102 · Fire one proving tick and switch the schedule on.** [lean 4]
- **SQ-203 · BLOCKED on an event · See a live compaction carry the hook's instructions.** [old Q-033]

## Parked, on purpose

- Sorting files between `leader` and `outer` [lean 14, old Q-040]. Nothing depends on it.
- Enforcing OODA order [lean 20]. It contradicts the model.
- Blocking mode [lean 28]. `warn` is enough.
