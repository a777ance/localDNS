# Blocked items

Items that cannot proceed without an input from the founder or a session that can
reach the blocked system. Newest first. Each entry stays here until its status changes
to `Done` or `Punted`, and it is removed only by the founder.

## 2026-11-11 · Ping-pong peers: lease not running, Stop hook not reachable — BLOCKED

- **Observed:** Peer A (`session_01Wg5h8frVuhW6Af87Z7HzN6`) declined the 3-hour lease and sent nothing. Peer B (`session_01Wg5h8e5zDnRYtHU8MybWw5`) completed its three rounds. Both peers are `config:no-git-repo`, so the Decide-Act Stop hook in this repo is not loaded in them.
- **Why blocked:** a peer only follows its original prompt. A later message that conflicts with it is treated as an injection. The hook can't be wired into a repo-less session.
- **Unblock action:** start a fresh peer pair whose original prompt contains the lease (expiry in UTC), the stop word, and the OODA act step. Confirm the lease was in place before the first ping. Put the decided-items act step in each prompt.

## Decision log (DEC)

- **DEC-022 · Shrink CLAUDE.md sections G and H, and repoint the checks that read them · OPEN**
  Measured 2026-11-12 (SQ-011). §G is 8,631 bytes and §H is 8,496 bytes: 17,127 of CLAUDE.md's
  59,997 bytes, 28.5%. The file is 3 bytes under its 60,000-byte budget, so any growth fails the
  registers check. The checks that read §G or §H, and would need repointing before anything moves:
  `tools/check-doctrine.py` (parses §G's sampler values, `\n## G\.` regex), `tools/check-docs.py`
  (the Bifrost sweep and the §H backbone table, lines near 412 to 426), and the canonical Bifrost
  block in `04-user-services/ai-orchestration/briefing-block.md`, which `tools/sync-briefings.py` renders.
  No section is moved in this entry.
  **Action if GO:** the loop moves the long form of §G and §H to a file under `docs/architecture/`,
  leaves a one-line pointer in CLAUDE.md, and repoints the three checks at the new file in the same commit.
  **Action if NO GO:** CLAUDE.md stays as it is and the budget stays at 60,000 bytes.
  **Decision needed:** **GO** or **NO GO**. Asked 2026-11-12.


- **DEC-021 · Promote the one-page intent draft onto `main` · OPEN**
  **Action if GO:** the founder copies `docs/ai-cto/intent-draft.md` onto `main` after editing it, and tags the promotion.
  **Action if NO GO:** `main` stays empty and the draft stays on `leader`.
  **Decision needed:** **GO** or **NO GO**. Asked 2026-11-12.
A plain-English version of the open decisions, in the order to answer them, is in `docs/ai-cto/roadmap.md`.

Every founder decision, newest first, with its result. Open tiles stay here until the
founder decides.

- **DEC-020 · The superfleet: a small-model swarm with ten scenarios for improving the loop's bootstrap · GO · executed in part.** Founder's GO, 2026-11-12 (a bare "go", taken as answering the newest open tile). Built: the plan as data (`.claude/superfleet.json`, ten scenarios, 34 lanes), the gate and review tool (`tools/check-superfleet.py`), and the page for a person (`docs/ai-cto/superfleet.md`). Not built, and not a session's to build: each lane's own instructions; the founder writes those. Original note: The founder asked for an orchestrated fleet, planned in
  advance, that his work account could review and run. The session understood the request and began
  writing it as data with a gate. The platform's safety system stopped the response while the
  standing instructions for the fleet's unattended lanes were being written. Nothing was written to
  disk. This is the third stop of the same kind in one session (see DEC-019), so the session did
  not retry and will not write those instructions. What a session can still do: describe scenarios
  for a person to plan from, and build the checks a fleet's output would have to pass. Writing the
  lanes' own instructions is left to the founder.
- **DEC-019 · How should sub-OODA loops for L items be run · OPEN**
  Asked 2026-11-12. Waiting on the founder. The L step is built: the Stop hook refuses a stop that
  leaves loop-owned items under L and says to start one sub-loop per item. The first attempt to start
  two sub-loops as parallel subagents was stopped by the platform's safety system, twice in one
  session, and neither subagent started. The session did not retry. Two items were to be handed out:
  goal-adaptive probes (INIT-006), and retrofit audits for the prose-only rules (Q-035). The choice
  is the founder's: run sub-loops one at a time inside the main session, run them as separate
  sessions the founder starts, or drop the automatic hand-out and keep L as a list.
- **DEC-018 · Give the scheduled loop the repository, so its ticks can push · OPEN**
  Asked 2026-11-12. Waiting on GO or NO GO. The proving run of the loop tick (01:15 UTC) did not
  reach the standing session: firing the task started a new session with no repository attached.
  That session cloned the repo by itself and did the work (Q-034, one local commit), but every push
  was refused: "a777ance/localDNS is not in this session's authorized repository set". Nothing
  reached `leader`; the work was lost with the container; it cost about 1.75 dollars. The task is
  **paused** so it cannot repeat that daily. A session cannot attach a repository to a scheduled
  task; the founder does it in the Claude app (the task "localDNS loop tick", its repositories),
  then the task is switched back on.
- **DEC-017 · Run the loop on a schedule, without the founder prompting it · GO · executed.** Founder's GO, 2026-11-12. A scheduled task named "localDNS loop tick" fires once a day at 10:43 UTC into one standing loop session (the second session of 2026-11-12, which has the repository and the GitHub tools). A first design that started a fresh session on each firing was created and deleted within a minute: a fresh session gets no repository and no GitHub tools, so its ticks would have done nothing. To stop the loop: disable or delete the scheduled task in the Claude app. Original note: Today the loop turns only when the founder sends a
  message. The standing prompt for one unattended tick is written (`docs/ai-cto/loop-tick.md`): one
  item, 30 minutes at most, a pull request into `leader`, a session-log entry, then stop. It is the
  founder's decision because every firing starts a session and spends money. Proposed: once a day.
- **DEC-016 · Empty `main` now · GO · executed.** The founder ran the push himself on 2026-11-12, from his laptop, after the block was rehearsed; it worked on the first try. `main` moved `cba76bb..646c709` as a fast-forward and now holds one file, `README.md`. Nothing was lost: the full content is on `leader`, `outer`, `main-before-evacuation`, and in `main`'s history. Original note: The founder asked for `main` to be emptied. The change is
  prepared as a pull request (one commit that removes every file and leaves a short signpost; history
  is kept, so one revert undoes it). It is not merged, because three things break at that moment
  unless moved first: new cloud sessions start on `main` and would load no rules and no hooks until the
  default branch is changed to `leader`; a laptop checkout on `main` loses its working files at its
  next pull; and the public Pages site stops publishing from `main` (the workflow on `leader` now
  publishes from `leader`).
- **DEC-015 · Three branches: emptied `main`, `leader`, `outer` · GO · executed in part.** Founder's
  decision 2026-11-12. `leader`, `outer`, and the safety copy `main-before-evacuation` were created
  from `main` at `cba76bb`. The tooling on `leader` now lands work on `leader`. Emptying `main` is
  DEC-016; sorting files between `leader` and `outer` is Q-040. See `docs/ai-cto/branches.md`.
- **DEC-014 · Trim the cloud environment setup script · GO · executed.** Founder deferred to the loop and approved the environment change 2026-11-11 (leans L-17, L-18). The new script was run once in a live container first; it takes effect on the next fresh container. Original evidence:
  Asked 2026-11-11. Waiting on GO or NO GO. Evidence (read from the Default environment, 2026-11-11):
  the script runs `apt-get install` for `shellcheck`, `wireguard-tools`, `nftables`, and `python3-yaml`
  on every fresh container. No gate, hook, or Matrix method calls `wg` or `nft` (a search of
  `tools/check-*.py`, `.claude/hooks/`, and `tools/matrix.py` finds none); they are only needed on the
  t630. The script's check step runs four of the nine gates by name. Proposal: drop `wireguard-tools`
  and `nftables`, and replace the four named checks with `python3 tools/matrix.py decide.gate`, which
  runs all nine. Keep `shellcheck` and `ruff`. Nothing in the environment has been changed.
- **DEC-013 · Split `CLAUDE.md` into an always-loaded core and on-demand files · GO · executed in part.**
  Founder deferred to the loop 2026-11-11; leans L-06 to L-10. Section F, Further reading, and the reply style were moved or shortened (69,153 to about 59,000 bytes). Sections G and H were left whole. Original evidence:
  Asked 2026-11-11. Waiting on GO or NO GO. Evidence (`wc -c` per top-level section, this branch,
  69,162 bytes in all, loaded into every turn of every session):

  | Section | Bytes | Proposal |
  | ------- | ----- | -------- |
  | C. Deploy paths | 12,908 | keep (the repo → system map) |
  | G. LLM sampling doctrine | 8,632 | move to `docs/`; keep the invariants as a short list |
  | H. Bifrost | 8,497 | move to `docs/`; keep the sweep, the template, and the glyph line |
  | 4. Further reading | 6,971 | move to `docs/`; keep one line per link |
  | 3. Working philosophy | 6,855 | keep the rules; move the worked cases to `docs/` |
  | Reply style: Briefing | 5,896 | keep, cut to one line per rule the Stop hook now enforces |
  | 1. Known issues | 4,429 | keep |
  | B. Network topology | 3,890 | keep |
  | F. nftables volume layer | 2,859 | move to `docs/` (a one-time deploy checklist) |
  | all other sections | 8,225 | keep |

  The four "move" rows and the worked cases come to about 30,000 bytes, a little over 40% of the file.
  Two things stand in the way and are part of the decision: `tools/check-docs.py` requires the Bifrost
  sweep and template to sit in `CLAUDE.md`, and `tools/check-doctrine.py` reads the section G values
  from it. Both checks would be repointed in the same change. This also covers the Phase D step the
  lease did not allow: shortening the reply-style prose now that the hook enforces five of its rules.
  Nothing has been moved.
- **DEC-012 · Move the Matrix from name to warn mode · GO · executed.** The founder ran the change himself and pushed it to `main` as `67da1b6` (2026-11-11). It took three tries: see DEBT-012. `enforce` is still not decided.
  Asked 2026-11-11. Waiting on GO or NO GO. Enforce stays off until warn has run cleanly in a live session.
- **DEC-011 · Merge PR #37 into `main` so the Matrix reaches new sessions · GO · executed.** Founder deferred to the loop 2026-11-11 (leans L-01 to L-05). Merged as `60a53d7`, a merge commit; the tree on `main` is identical to the branch tip `fa94d93`.
  Asked 2026-11-11. Waiting on GO or NO GO.
- **DEC-010 · Scope DEC tiles to decisions only the founder can make · GO · executed.**
  Founder deferred to the loop 2026-11-11; leans L-11 to L-13. The rule is one line in the reply style in `CLAUDE.md`.
  Asked 2026-11-11. Waiting on GO or NO GO.
- **DEC-009 · Spawn 4 cloud peer sessions in 2 pairs · GO · executed.** A pair ran 42 rounds; B pair paused after 1.
- **DEC-008 · Start a fresh peer pair from the revised template · GO · executed.** Carrot C1 and C2 created 2026-11-11.
- **DEC-007 · Merge PR #36 into `main` so the tile, navigation, and decision-log rules reach new sessions · GO · executed.** Merged as `f25bd95`.
- **DEC-006 · Keep pushing to PR #36 while the punted Cloudflare check fails each push · MOOT.** PR #36 merged as `f25bd95` (DEC-007), so there is nothing left to decide. Marked 2026-11-11.
- **DEC-005 · Create venv peering files (`.vscode/settings.json`, bootstrap script) · OPEN**
  Lean L-19: stays open; not created from a guessed path.
  Asked 2026-11-11. Waiting on GO or NO GO. Needs `echo $VIRTUAL_ENV` and `ls ../venv` run on the XPS.
- **DEC-004 · Keep this session subscribed to #36 · MOOT.** PR #36 merged as `f25bd95` (DEC-007), so there is nothing left to decide. Marked 2026-11-11.
- **DEC-003 · Restore the Decide-Act Stop hook · GO · executed.** Hook is on `main` via PR #35.
- **DEC-002 · Stay subscribed to draft PR #36 · GO.** No action needed.
- **DEC-001 · Merge PR #35 into `main` · GO · executed.** Merged as `e275413`.

Format per entry: status · what was observed · why it is blocked · the action that unblocks it.

---

## 2026-11-11 · Cloudflare Workers Builds failure — PUNTED

- **Status:** Punted by the founder. Not part of the current OODA loop project. Revisit only if the founder asks.

- **Observed:** `Workers Builds: cloudflarelocaldns` fails on every head of
  `claude/youthful-hopper-7knhtn` (`c1737f2`, `fea6f36`, `df0bac1`). The same check failed on
  PR #32 before it merged. Check run `130803703679`, build
  `0f0be1b9-eae0-408b-ac27-d6cfe00a2e74`.
- **Why blocked:** the build page is behind Cloudflare login. A fetch returns HTTP 403, so the
  error line cannot be read from this session.
- **Unblock action:**
  1. Open the build page while logged in to the Cloudflare account that owns the
     `cloudflarelocaldns` worker:
     `https://dash.cloudflare.com/284216967bf00220e398d7a519c9f877/workers/services/view/cloudflarelocaldns/production/builds/0f0be1b9-eae0-408b-ac27-d6cfe00a2e74`
  2. Copy the first line containing `error`, `failed`, or `ERR` from the build log.
  3. Paste it into a session on this branch. That session can then write the fix recipe.
  4. If the log shows no error, check the worker's build settings (root directory, build
     command, and the wrangler config path) against this repo's layout.

## 2026-11-11 · Unsubscribe "Gate test v2" from PR #35 — BLOCKED

- **Observed:** the session `session_01Wg5h8dhNvZwnoq6ZeS1T8V` is still subscribed to
  PR #35. Each Cloudflare failure wakes it. It replied that the subscription is the founder's
  decision and that it made no repo changes.
- **Why blocked:** dropping the subscription is the founder's decision. This session can only
  unsubscribe itself.
- **Unblock action:** in the app, open "Gate test v2" and ask it to run
  `unsubscribe_pr_activity` for `a777ance/localDNS#35`. Or tell this session to send the
  request again, after you have decided.
