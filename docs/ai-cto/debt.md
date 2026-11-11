# Debt register

Known debt: things that work less well than they should, or that will cost more later if
left alone. Newest first. Each entry has an ID, a status, what was observed, the cost of
leaving it, and the next action. Read at the Orient step of every briefing. Update the
status in the same commit as the work that changed it.

Status values: `Open` · `Blocked` (also listed in `blocked.md`) · `Punted` · `Done`.

---

## DEBT-012 · Commands were handed to the founder without being run first · Done

- **Observed 2026-11-11:** three recipes in one session failed on the founder's laptop. One used
  the cloud container's path. One switched the gate to `warn` when no test had ever run with the
  live mode set to `warn`, so the gate went red on his machine. One depended on a merge that the
  recipe left as a step with nothing to paste. The founder's words: "an observe failure. We
  didn't check, we didn't look before we leap."
- **Root cause:** nothing made a session run a command before handing it over. Each failure was
  findable in seconds in a copy of his checkout.
- **Fix:** `python3 tools/matrix.py decide.rehearse` runs a command in a throwaway clone at the
  commit the founder is on, with pushes going to a throwaway remote. The Stop hook
  (`.claude/hooks/decide-act.py`, rule REHEARSE) bounces a reply whose `bash` block was not
  rehearsed with exit 0, unless the reply says `Not rehearsed:` and why.
- **Limit:** a rehearsal copies the repo, not the laptop. It cannot see his shell, his other
  folders, or uncommitted edits unless they are given with `--setup`.

## DEBT-011 · Six lint findings predate the Matrix work · Open

- **Observed:** `ruff check --select E9,F` (the cloud setup script's lint step) reports six
  findings outside this lease's files: unused imports in `jury/jury.py`, `collect_stats.py`,
  `compose.py`, and `tools/telepathy/watch.py`, and two unused variables in `compose.py`.
- **Cost:** the setup script prints `!! FAILED` on every fresh container, so a real failure
  on that line would not stand out.
- **Done 2026-11-11:** the four unused imports are removed.
- **Next action:** two unused variables remain in `build_alloc` in `compose.py` (`other`, `other_bytes`).
  Read on 2026-11-11: the "Other" row is computed from `remainder`, so no figure is missing; they are
  dead code. Left in place because it is the Statement composer; remove them with a test of its output.

## DEBT-010 · Fixed context cost per session is high · Open

- **Observed:** on 2026-11-11 the session's context showed `CLAUDE.md` at about 24.5k tokens,
  the GitHub connector's tool list at about 35k, and one session-management call (archive)
  returning a full session record each time.
- **Cost:** every turn of every session in this repo pays for these before any work starts.
- **Next action:** founder call on splitting `CLAUDE.md` into a short always-loaded core plus
  on-demand reference files; prefer `observe.status`-style narrow calls over bulky ones.

## DEBT-009 · Usage limit reached while peers ran at max effort · Open

- **Observed:** on 2026-11-11 at 22:28 UTC the Carrot starter's session record showed the
  five-hour usage limit as `rejected` with overage in use, resetting at 01:10 UTC. That one
  peer had cost about $2.68 in nine minutes at max effort.
- **Cost:** unattended peers at max effort spend real overage while the founder is away.
- **Next action:** both Carrot peers were sent `stop`. Before the next pair, set a lower
  effort for peers and a spend ceiling in the template.

## DEBT-008 · The Matrix gate has never run in a live enforce session · Open

- **Observed:** `name` mode is seen firing on live calls. `warn` and `enforce`, the lease,
  and the stall rule are proven only by `tools/check-matrix.py`, which pipes calls into the hook.
- **Cost:** whether the app honours the hook's deny, and whether subagent calls pass
  through the hook, is unconfirmed.
- **Measured 2026-11-11 (Orchestrator lease):** the `PostToolUse` timing hook fires live in a
  running session (`.claude/.matrix-times` filled from the first call after it was wired). The
  subagent check (Q-004) was skipped because the usage limit was still reached, so whether the
  hook fires for a subagent's calls is still unconfirmed. Whether a compaction uses the
  `PreCompact` text is also unconfirmed: no compaction happened in the lease.
- **Confirmed 2026-11-11, 23:08 UTC (Q-004):** one `juror` subagent made one `Read` call and reported the
  hook line it received, word for word: `cardinal: observe.read · agent: juror`. The timing hook also
  wrote a row for that call. So hooks fire inside subagents in a checkout of this repo, and the hook
  knows which agent made the call. One agent, one call: `name` mode only.
- **Next action:** after DEC-012, run `warn` in one live session, then `enforce` with the
  kill switch ready.

## DEBT-007 · The Matrix is not on `main` · Blocked

- **Observed:** the map, hook, `tools/matrix.py`, and gates sit on `decision-log-dec007` (PR #37).
- **Cost:** new sessions start from `main` and get none of it.
- **Next action:** DEC-011.

## DEBT-006 · Gate and style checks pass only partially · Done

- **Observed:** `tools/sync-briefings.py` exits 2 when given `--check`, because the flag does
  not exist; the bare run exits 0 and reports zero sibling repos. `tools/check-doctrine.py`
  prints a `SyntaxWarning: invalid escape sequence '\$'` at line 29 of an embedded string.
- **Cost:** the briefing-drift check checks nothing on this machine, so a green run
  here does not mean siblings agree.
- **Fixed 2026-11-11:** the warning came from the module docstrings of `jury/jury.py` and
  `jury-claude/jury_claude.py` (a `\$` in a normal string), which `check-doctrine.py` parses; both
  are now raw strings, and `python3 tools/check-doctrine.py` now prints nothing on stderr. `sync-briefings.py`
  accepts `--check`. Still true: with no sibling repos checked out, the drift check compares nothing.
- **Next action:** fix the escape in the `check-doctrine.py` string (use a raw string), and
  either document the bare call in the gate or add the `--check` mode the gate expects.

## DEBT-005 · Telepathy inbox has no wake-on-arrival outside one machine · Open

- **Observed:** the telepathy watcher (on branch `claude/youthful-hopper-7knhtn`) works (test `20261111T213322-e0dc5995` woke the
  watcher), but only for sessions on one filesystem. The Monitor expires after its timeout.
- **Cost:** cross-session mail between cloud sessions does not arrive. A watcher that expired
  looks identical to a quiet inbox.
- **Next action:** run a two-session test on one machine; decide whether to re-arm with a
  longer timeout or use the connector the other session is building.

## DEBT-004 · Cloudflare Workers Builds check fails on PRs · Punted

- **Observed:** `Workers Builds: cloudflarelocaldns` fails on `c1737f2`, `fea6f36`,
  `df0bac1`. The same check failed on PR #32 before it merged. The build log is behind login.
- **Cost:** every push wakes subscribed sessions, and the PR can't be called mergeable.
- **Next action:** none. Punted by the founder; not part of the current OODA loop project.

## DEBT-003 · Other session still subscribed to PR #35 · Blocked

- **Observed:** "Gate test v2" (`session_01Wg5h8dhNvZwnoq6ZeS1T8V`) wakes on each push. It
  declined to unsubscribe and says the founder decides.
- **Cost:** noise and token spend on every failing push.
- **Next action:** see `docs/ai-cto/blocked.md`, "Unsubscribe Gate test v2 from PR #35".

## DEBT-002 · Briefing style not selectable in the app picker · Punted

- **Observed:** the app's Output style picker lists only Default, Concise, Explanatory,
  Learning, and Proactive. The Briefing style cannot be selected there.
- **Cost:** the style applies only through `CLAUDE.md` and the Stop hook, not as a named style.
- **Next action:** punted by the founder's choice to rely on `CLAUDE.md`.

## DEBT-001 · Stop hook untested in a live turn · Done

- **Observed:** `.claude/hooks/decide-act.py` was tested on fake transcripts. It fired once
  on a real turn (block with 3 items), which is the live test.
- **Cost:** the loop guard (`stop_hook_active`) has not been exercised with a real second pass.
- **Next action:** confirm one turn with a non-empty Decide list completes without a second
  block after its items are acted on.
