# Blocked items

Items that cannot proceed without an input from the founder or a session that can
reach the blocked system. Newest first. Each entry stays here until its status changes
to `Done` or `Punted`, and it is removed only by the founder.

## Decision log (DEC)

Every founder decision, newest first, with its result. Open tiles stay here until the
founder decides.

- **DEC-007 · Merge PR #36 into `main` so the tile, navigation, and decision-log rules reach new sessions · GO · executed.** Merged as `f25bd95`.
- **DEC-006 · Keep pushing to PR #36 while the punted Cloudflare check fails each push · OPEN**
  Asked 2026-11-11. Waiting on GO or NO GO.
- **DEC-005 · Create venv peering files (`.vscode/settings.json`, bootstrap script) · OPEN**
  Asked 2026-11-11. Waiting on GO or NO GO. Needs `echo $VIRTUAL_ENV` and `ls ../venv` run on the XPS.
- **DEC-004 · Keep this session subscribed to #36 · OPEN**
  Asked 2026-11-11. Waiting on GO or NO GO.
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
