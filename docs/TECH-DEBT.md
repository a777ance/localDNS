# Technical debt register

Every known shortcut, gap, or wrong claim goes here the moment it is found. Entries
are **newest first**. The register is loud by design: `tools/check-debt.py` fails
on any entry missing a field, and on any open entry past its `due` date.

Fields per entry: `id`, `opened`, `owner`, `status` (`open` | `closed`), `due`
(YYYY-MM-DD), `what`, `why it is debt`, `fix`.

---

### DEBT-008
- **opened:** 2026-11-11
- **owner:** founder
- **status:** open
- **due:** 2026-11-18
- **what:** `CLAUDE.md` §C describes `tools/sync-briefings.py` as taking `--check`. The script rejects that flag (argparse: unrecognized arguments). Bare invocation reports drift.
- **why it is debt:** the documented command fails when run as written.
- **fix:** correct the §C row to the bare invocation, or add a real `--check` flag.

### DEBT-007
- **opened:** 2026-11-11
- **owner:** founder
- **status:** closed
- **due:** 2026-11-18
- **what:** the repo-level precedence header in `CLAUDE.md` exists only as a local, uncommitted edit.
- **why it is debt:** the file on the branch does not carry the rule the session is supposed to follow.
- **fix:** commit and push the 6-line header to `claude/elegant-sagan-ul1tc6`, then confirm the remote copy.
- **closed:** the header is on the branch. `CLAUDE.md` at ea709d5 begins with the precedence blockquote, and no later commit on this branch touches `CLAUDE.md`. Verified by reading the remote file, not by a local diff.

### DEBT-006
- **opened:** 2026-11-11
- **owner:** founder
- **status:** open
- **due:** 2026-11-18
- **what:** the Default cloud environment's network is `unrestricted`. The agreed setting is `limited` with no extra hosts.
- **why it is debt:** broader network reach than the proposal that was reviewed.
- **fix:** switch network back to limited, with package managers on and no hosts.

### DEBT-005
- **opened:** 2026-11-11
- **owner:** founder
- **status:** open
- **due:** 2026-11-18
- **what:** the Bash rule is now narrowed to destructive commands (`block-destructive-bash` in `.claude/tool-aliases.json`) and `alias.sh` is registered as a PreToolUse hook in `.claude/settings.json`. Enforcement is not yet verified: no live run has shown the hook firing, and the executable bit on `alias.sh` cannot be confirmed through the GitHub API.
- **why it is debt:** a rule that has never fired is still a silent gap.
- **fix:** from a session with a shell, run `chmod +x .claude/hooks/alias.sh`, then confirm `rm -rf /tmp/x` is blocked and `git status` is allowed. Close this entry once both are seen.

### DEBT-004
- **opened:** 2026-11-11
- **owner:** founder
- **status:** open
- **due:** 2026-11-18
- **what:** `unbound-checkconf` is not in the cloud setup script, so the six Unbound drop-ins are not validated before a change is proposed.
- **why it is debt:** the main offline validation for the DNS layer is missing.
- **fix:** extract the binary without starting the packaged service, then run it against `01-core-network/unbound/`.

### DEBT-003
- **opened:** 2026-11-11
- **owner:** founder
- **status:** open
- **due:** 2026-11-18
- **what:** the agent cannot run `git status` in this session, because Bash is banned, so untracked-file reports from the stop hook cannot be checked locally.
- **why it is debt:** the stop hook can fire on state the agent cannot see.
- **fix:** either allow a read-only `git status`, or have the stop hook print the file list it is reacting to.

### DEBT-002
- **opened:** 2026-11-11
- **owner:** founder
- **status:** open
- **due:** 2026-11-18
- **what:** `04-user-services/ai-orchestration/jury-claude/` was not verified on disk in this session. Its path is taken from CLAUDE.md.
- **why it is debt:** a documented path has not been confirmed against the working tree.
- **fix:** list the directory and confirm the files named in the §C table exist.

### DEBT-001
- **opened:** 2026-11-11
- **owner:** founder
- **status:** open
- **due:** 2026-11-18
- **what:** the PR-activity subscription was created without a request, and the session was unsubscribed by hand from PR #34.
- **why it is debt:** a subscription the agent did not ask for is a process gap; the cause is not yet known.
- **fix:** find what created the subscription, and make the repo rule ("never watch") enforced rather than remembered.
