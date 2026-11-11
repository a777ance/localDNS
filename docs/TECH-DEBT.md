# Technical debt register

Every known shortcut, gap, or wrong claim goes here the moment it is found. Entries
are **newest first**. The register is loud by design: `tools/check-debt.py` fails
on any entry missing a field, and on any open entry past its `due` date.

Fields per entry: `id`, `opened`, `owner`, `status` (`open` | `closed`), `due`
(YYYY-MM-DD), `what`, `why it is debt`, `fix`.

---

### DEBT-011
- **opened:** 2026-11-11
- **owner:** founder
- **status:** open
- **due:** 2026-11-18
- **what:** `.claude/hooks/alias.sh` is registered as a `PreToolUse` hook for every tool (`.claude/settings.json`, matcher `*`) but is mode `-rw-r--r--`, not executable. In the alias-gate test, native `Read` and `Grep` were not denied as the gate's contract says.
- **why it is debt:** the alias gate is registered and documented as enforcing, and it is not observed to enforce. A hook that silently does nothing looks like protection.
- **fix:** read `alias.sh` and the harness's behaviour on a non-executable or failing hook; `chmod +x` (as done for `gate.sh`, `lint.sh`, `refeed.sh`) only once the contract is confirmed; then re-run the six-point alias test and record the result here.

### DEBT-010
- **opened:** 2026-11-11
- **owner:** founder
- **status:** open
- **due:** 2026-12-11
- **what:** `ruff.toml` selects `E F W B UP I` (E501 ignored). Rules not selected: `SIM115` (open without a context manager, 18 sites), `PLR2004` (magic numbers), `RUF`/`PL`, `DTZ` (naive datetimes), `BLE001` (blind except), `EXE001` (shebang not executable), `C408`/`ISC`.
- **why it is debt:** the selected set was chosen to make the gate passable, not from a measured judgment that the unselected rules do not matter. `SIM115` and `DTZ` are plausible defects in the statement pipeline, which must not silently mis-date figures.
- **fix:** widen one family at a time: measure the finding count with `ruff check --select <family> --statistics`, fix or record each, add the family to `ruff.toml` in the same commit. Start with `DTZ` and `SIM115` on `docs/statements/tools/collect/`.

### DEBT-009
- **opened:** 2026-11-11
- **owner:** founder
- **status:** closed
- **due:** 2026-11-18
- **what:** no lint config in the repo, and no lint step in the process. `ruff` ran on built-in defaults (113 findings, and the set differs between releases); nothing gated lint at commit or while editing, so findings accumulated unread.
- **why it is debt:** a rule that is not run is not a rule. Lint debt grows silently between sessions, and each new session inherits it without seeing it.
- **fix:** check in `ruff.toml` as the single rule source; fix the findings it reports; run ruff and `tools/check-debt.py` at commit time through `tools/verify.sh` (which `gate.sh` runs); add an edit-time hook (`lint.sh`, PostToolUse on Edit/Write/MultiEdit) that reports findings on the file just written. The repo-owned `ruff.toml` and `verify.sh` landed in parallel on this branch (12c6d43); this entry's work was merged onto them.
- **closed:** `ruff check .` reports "All checks passed!" on the tree. `check-doctrine.py` exits 0 after the edits. The edit hook was tested with a bad file (exit 2, findings shown), a clean file and a non-Python file (exit 0). The commit gate was tested with a temporary file carrying a real finding: it blocked with exit 2 and the ruff output, and the file was removed. Verified by running the checks, not by reading the diff.

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
