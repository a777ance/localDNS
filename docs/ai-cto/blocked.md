# Blocked items

Items that cannot proceed without an input from the founder or a session that can
reach the blocked system. Newest first. Each entry stays here until its status changes
to `Done` or `Punted`, and it is removed only by the founder.

## 2026-11-11 · Ping-pong peers: lease not running, Stop hook not reachable — BLOCKED

- **Observed:** Peer A (`session_01Wg5h8frVuhW6Af87Z7HzN6`) declined the 3-hour lease and sent nothing. Peer B (`session_01Wg5h8e5zDnRYtHU8MybWw5`) completed its three rounds. Both peers are `config:no-git-repo`, so the Decide-Act Stop hook in this repo is not loaded in them.
- **Why blocked:** a peer only follows its original prompt. A later message that conflicts with it is treated as an injection. The hook can't be wired into a repo-less session.
- **Unblock action:** start a fresh peer pair whose original prompt contains the lease (expiry in UTC), the stop word, and the OODA act step. Confirm the lease was in place before the first ping. Put the decided-items act step in each prompt.

## Decision log (DEC)

A plain-English version of the open decisions, in the order to answer them, is in `docs/ai-cto/roadmap.md`.

Every founder decision, newest first, with its result. Open tiles stay here until the
founder decides.

- **DEC-016 · Empty `main` now · OPEN**
  Asked 2026-11-12. Waiting on GO or NO GO. The founder asked for `main` to be emptied. The change is
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
