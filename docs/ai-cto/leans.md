# Leans on the six open decisions

Written 2026-11-11, about 23:20 UTC. The founder asked for 20 leans across the six open
decisions and said he would defer to the OODA loop. A lean is a stated position with its
reason and the check that would show it wrong. Each decision's status is in the decision
log in `docs/ai-cto/blocked.md`.

## DEC-011 · Merge PR #37 into `main` → lean GO

- **L-01 · Merge.** Nine gates pass in the cloud container and on the founder's XPS. Wrong if: a gate fails on `main` after the merge.
- **L-02 · The merge cannot block work.** No hook denies a tool call in `name` mode, and every hook fails open with a timeout. Exit: `touch .claude/.matrix-off`.
- **L-03 · Use a merge commit, not a squash.** The queue and the registers cite commit ids; a squash would orphan every one of them.
- **L-04 · The failing Cloudflare check does not hold the merge.** It is punted (DEBT-004) and is unrelated to this diff.
- **L-05 · The one real behaviour change is the Stop hook.** Every session on `main` will be bounced, once per turn at most, for a reply that breaks one of five rules. Wrong if: a false bounce shows up; then add the reply as a case in `tools/check-stop-hook.py` and fix the rule.

## DEC-013 · Split `CLAUDE.md` → lean GO, in part

- **L-06 · Move what no session needs on every turn.** Section F (a one-time deploy checklist) and the long notes under "Further reading" go to `docs/architecture/`, word for word. Measured: 69,153 to about 59,000 bytes.
- **L-07 · Cut the reply-style rules to one line each.** Five are now enforced by the Stop hook; the long form is kept in `docs/ai-cto/reply-style-full.md`.
- **L-08 · Section H (Bifrost) stays whole.** Its heading is the founder's rule: it "loads every session". Three checks anchor its strings in `CLAUDE.md`.
- **L-09 · Section G (the Jury doctrine) stays whole for now.** `tools/check-doctrine.py` reads its values from `CLAUDE.md`, and its clause table is the map of where each rule is sited. Shortening it is a separate change with its own check.
- **L-10 · Nothing is deleted, only moved.** Wrong if: a moved passage cannot be found in the three new files; `tools/check-docs.py` checks every link and path in them.

## DEC-010 · Scope tiles to what only the founder can decide → lean GO

- **L-11 · Fewer tiles.** A tile for every small choice is how the founder ended up with six open at once.
- **L-12 · The test is reversibility.** Tile only: an action a revert cannot undo, anything outward-facing or that spends money, the live t630, real customer data, and the founder's own rules.
- **L-13 · Everything else is decided, acted on, and recorded.** The record is the commit and the register entry, so the founder can still overrule it afterwards.

## DEC-012 · Move the gate from `name` to `warn` → lean GO, founder's hand

- **L-14 · Turn on `warn`.** It adds one line of context to five native tools and denies nothing.
- **L-15 · The session must not flip its own gate.** The attempt on 2026-11-11 was refused by the permission system as self-modification, and that refusal is right: a session changing the mode of the hook that governs it is the one change that should pass a human hand. The founder runs the one-line change, or permits it by name.
- **L-16 · `enforce` stays off, and is not decided here.** It can lock a session out and has never run live. It keeps its own decision, after `warn` has run in more than one session.

## DEC-014 · Trim the cloud setup script → lean GO

- **L-17 · Drop `wireguard-tools` and `nftables`.** No gate, hook, or Matrix method calls `wg` or `nft`; they matter only on the t630.
- **L-18 · Run all nine gates at start, through `decide.gate`.** Keep `shellcheck`, `ruff`, and `python3-yaml`. The environment asks the founder to approve the exact script, so this one still passes his eyes.

## DEC-005 · venv peering files for the XPS → stays OPEN

- **L-19 · Do not create them yet.** They would encode a path on the founder's laptop that no session has seen. Writing a guessed path into config is the same fault as the `cd /home/user/localDNS` rule. Needs the two-line output asked for in `docs/ai-cto/roadmap.md`.

## Across all six

- **L-20 · Defer does not reach the t630 or `enforce`.** The founder deferred on these six items. Nothing here deploys to the live box, and nothing here turns on blocking.
