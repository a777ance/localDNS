# Debt register

Known debt: things that work less well than they should, or that will cost more later if
left alone. Newest first. Each entry has an ID, a status, what was observed, the cost of
leaving it, and the next action. Read at the Orient step of every briefing. Update the
status in the same commit as the work that changed it.

Status values: `Open` · `Blocked` (also listed in `blocked.md`) · `Punted` · `Done`.

---

## DEBT-006 · Gate and style checks pass only partially · Open

- **Observed:** `tools/sync-briefings.py` exits 2 when given `--check`, because the flag does
  not exist; the bare run exits 0 and reports zero sibling repos. `tools/check-doctrine.py`
  prints a `SyntaxWarning: invalid escape sequence '\$'` at line 29 of an embedded string.
- **Cost:** the briefing-drift check checks nothing on this machine, so a green run
  here does not mean siblings agree.
- **Next action:** fix the escape in the `check-doctrine.py` string (use a raw string), and
  either document the bare call in the gate or add the `--check` mode the gate expects.

## DEBT-005 · Telepathy inbox has no wake-on-arrival outside one machine · Open

- **Observed:** `tools/telepathy/watch.py` works (test `20261111T213322-e0dc5995` woke the
  watcher), but only for sessions on one filesystem. The Monitor expires after its timeout.
- **Cost:** cross-session mail between cloud sessions does not arrive. A watcher that expired
  looks identical to a quiet inbox.
- **Next action:** run a two-session test on one machine; decide whether to re-arm with a
  longer timeout or use the connector the other session is building.

## DEBT-004 · PR #35 has a failing Cloudflare check on every push · Blocked

- **Observed:** `Workers Builds: cloudflarelocaldns` fails on `c1737f2`, `fea6f36`,
  `df0bac1`. The same check failed on PR #32 before it merged. The build log is behind login.
- **Cost:** every push wakes subscribed sessions, and the PR can't be called mergeable.
- **Next action:** see `docs/ai-cto/blocked.md`, "Cloudflare build failure on PR #35".

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

## DEBT-001 · Stop hook untested in a live turn · Open

- **Observed:** `.claude/hooks/decide-act.py` was tested on fake transcripts. It fired once
  on a real turn (block with 3 items), which is the live test.
- **Cost:** the loop guard (`stop_hook_active`) has not been exercised with a real second pass.
- **Next action:** confirm one turn with a non-empty Decide list completes without a second
  block after its items are acted on.
