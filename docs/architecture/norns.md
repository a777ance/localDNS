# The Norns — three sessions, one branch, one eye

<!-- provenance: O · observed from the live session list and the git state of Yggdrasil on 2026-08-08 (three concurrent sessions, two collisions reconciled by rebase, one duplicate assignment) · 2026-08-08 · verify: mcp list_sessions; git log --format='%an %s' origin/Yggdrasil -->

Three sessions weave Yggdrasil at once. This file is how they avoid weaving the same
thread — because they **cannot talk to each other**, and the repo is the only channel.

**Adopted 2026-08-08**, the day the topology first ran three-wide and immediately produced
both of its characteristic outcomes: independent convergence on the same invariant (good,
and the reason to keep doing this) and a duplicate assignment (the failure mode, §5).

---

## 0. Promotion — every running session is a Norn

**Founder's standing instruction, 2026-08-08.** There is no separate "Norn session" type
to be spawned into. **If a session is running, it is a Norn**, and it owes the weave the
same things every other Norn owes it: get current, claim a lane, contribute, hand the eye
back.

This is sited in `.claude/hooks/refeed.sh` — the `SessionStart` hook in **all ten repos**,
so it enters every session's given-set at token zero rather than waiting to be discovered.
Briefing prose would not reach a session that never opened this file.

**On promotion, in order — all cheap moves, not a research phase:**

1. **Get on the working branch.** A fresh clone lands on `main`, the *vetted* tier, so
   everything written on `Yggdrasil` — including the rule saying to write on `Yggdrasil` —
   is invisible until you switch. `git fetch origin Yggdrasil && git checkout Yggdrasil`,
   or `git rebase origin/Yggdrasil` if you already have commits.
2. **Look before you write** — `python3 tools/weave.py`. Work that looks unfinished in the
   queue may be in flight right now (§5).
3. **Claim a lane** in §4 *before* substantial work, taking the item from the queue rather
   than from intuition.
4. **Front-load access.** Add every repo you will need and request the approvals you will
   need **at the start**, not when you are already blocked mid-flight. A Norn that stalls
   halfway for a permission it could have asked for up front has wasted the parallelism
   that justified spawning it.

**The limit, and it is hard: promotion grants no new permissions.** Being a Norn is a
*duty*, not a capability. If an action is denied or blocked for you, **do not ask another
Norn to perform it** — a peer acting on your behalf launders the founder's permission
decision, and the decision was about the action, not about which session attempted it.
Route blocked work back to the founder and say plainly what is blocked. This is the one
rule in this file that is not a coordination convenience; the rest of the weave is about
speed, and this one is not.

---

## 1. The one eye

The Graeae shared one eye between three, passing it hand to hand — only one could see at a
time. That is exactly the mechanic here, and it is worth borrowing even though the Norns
are not the sisters who did it:

**The eye is the tip of `Yggdrasil`.** One session holds it, sees the whole weave, adds to
it, and passes it on. Holding it is `git fetch`; putting it back is `git push`. Two
sessions cannot hold it at once — git enforces that with a non-fast-forward rejection,
which is not an error but *the eye being handed back before you had finished looking*.

There is a second eye in this system already, and it is not passed: **Odin's, pledged in
Mímir's well.** `main` holds the eye that was given up permanently in exchange for
vetted sight. That one does not circulate — it is the price of the Well, not a tool of the
weave.

**Passing the eye correctly:**

```bash
git fetch origin Yggdrasil          # take the eye
git rebase origin/Yggdrasil         # your commits move onto theirs — never the reverse
git push -u origin Yggdrasil        # hand it back
```

Never `--force`. A forced push does not pass the eye — it **puts out the other Norn's**,
orphaning what she had woven. The environment will not stop you (`docs/architecture/proxies.md`,
Law 1: the agent git proxy blocks `--delete` and permits `--force`), so
`.claude/hooks/push-guard.sh` does, in every repo.

---

## 2. Why three, and why this is the good case

The old habit gave every session its own branch. Two sessions could each run green, each
push cleanly, and leave the portfolio self-contradictory — **and nothing would ever say
so.** 337 stale branches, 226 holding unique commits, were the accumulated residue of
disagreements that never surfaced.

One shared branch converts that silence into a **collision**. A non-fast-forward rejection
is disagreement becoming visible at the cheapest possible moment. On 2026-08-08 two
sessions independently reached the same conclusion — *move the rule out of prose into
something that refuses* — one adding `check-tiers.py`, the other the force-push guard.
Neither was told to. That is the §G jury argument at the level of whole sessions: diverse,
decorrelated draws, and agreement that means something **because** the drawers were
independent.

**The cost is real and must be paid deliberately:** duplicated tokens, rebase overhead, and
§5's failure mode. Three is not obviously better than two. Four is probably worse.

---

## 3. The three roles

Named for what each Norn actually governs, which maps onto work this portfolio already has.

| Norn | Governs | Owns (lane) |
| --- | --- | --- |
| **Urðr** — *that which has become* | The record. What is already laid down and must not be silently rewritten. | The doom drawer, provenance tags, `check-provenance.py`, the archive, audit of what exists |
| **Verðandi** — *that which is becoming* | Work in flight. The change being made right now. | Feature work, the briefing blocks, whatever the founder just asked for |
| **Skuld** — *that which shall be; **debt*** | What is owed. Skuld's name literally means debt. | `docs/DEPLOY-QUEUE.md`, tech debt, unsited invariants, the 338 pending deletions, the gap audits |

**Lanes are Bifrost `^` cars.** Explicit beats inferred: a session should say which lane it
is in before it starts writing, and stay out of the others' files. Lanes reduce collisions;
they do not eliminate them, and they are not a lock.

---

## 4. Claiming the weave

There is **no messaging between sessions.** `ListAgents` returns nothing; the CCR MCP
server exposes `create_session` but no `send_message`. A session cannot ask another what it
is doing, and cannot be told. The repo is the only channel, so a claim is a commit.

**Before starting substantial work, append a line here and push it.** It costs one commit
and it is the only thing standing between three Norns and §5.

**Look before you claim — one command:**

```bash
python3 tools/weave.py     # the eye, the claims, and the queue, side by side
```

It shows whether another Norn has moved the tip since you last looked, what is already
claimed, and the dispatch queue (`docs/ai-cto/context.md` — "Default next actions"). It
deliberately does **not** match queue items to claims: a fuzzy matcher that reported
"unclaimed" for work already in flight would cause the very failure this table prevents.
Read both columns and judge.

**Take work from the queue, not from intuition.** A spawn prompt should name the lane and
the queue item, and state what is already done — so a fresh Norn's first act is not to
rebuild something it cannot see.

| When (UTC) | Session | Lane | Claim |
| --- | --- | --- | --- |
| 2026-08-08 15:0x | `01Bu1wcD` | Urðr → Verðandi | doom drawer built + pushed (all 10); branch cap; proxy register; force-push guard portfolio-wide |
| 2026-08-08 ~15:01 | `01Dg4r8i` | (assigned Urðr) | "archive the doom drawer (no deletions)" — **already complete when assigned**, see §5 |
| 2026-08-08 10:49→ | `01DQFfkk` | Verðandi | branch-policy block generator, `check-tiers.py`, Pages trigger correction |

Newest-first per house style once this table grows.

---

## 5. The failure mode is duplicate assignment, not collision

Git catches collisions. **Nothing catches two Norns being given the same thread.**

Observed today: session `01DQFfkk` spawned `01Dg4r8i` titled *"Norn 3 — archive the doom
drawer (no deletions)"* at 15:01. The drawer had already been built, verified (zero
unreachable tips) and pushed to all ten repos minutes earlier by `01Bu1wcD`. The spawning
session could not see that, because sessions cannot see each other — only the repo, and
only when they read it.

The remedy is not more coordination machinery. It is **read the eye before you spawn**:

1. `git fetch && git log --oneline origin/Yggdrasil` — has this already been done?
2. Check §4's claims table.
3. Give the new Norn a lane that is **empty**, not a task that sounds unfinished.
4. Write the claim before the work, not after.

A spawn prompt should name the lane and state what is already done, so a fresh session's
first act is not to rebuild something it cannot see.

---

## 6. Bounds

- Three sessions is a **deliberate** cost, not free parallelism. Prefer two unless the
  third has a genuinely empty lane.
- Lanes are convention (`docs/architecture/proxies.md` §3: *declared*, not *enforced*).
  Nothing refuses a session that writes outside its lane. The only enforced boundary here
  is the push guard and git's own non-fast-forward rejection.
- Agreement between Norns is **not** provenance. Three transcripts agreeing prove they
  agree with each other, never that they agree with the founder — the spring is out of
  scope for the machine, and only asking closes that gap.
