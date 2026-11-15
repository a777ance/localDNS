<!-- provenance: D · drafted by the explorer artifact's shot engine (gate passes 1 to 3, shots 20261115T121241-pass1shot, 20261115T121949-pass2shot, 20261115T123355-pass3shot) from each file's header, then checked line by line against the full header, CLAUDE.md §C and a test run by a cloud session · 2026-11-15 -->
# tools/

What each tool here does and how to run it, one line each, taken from the tool's own header. The header is the
authority: if a line here and a header disagree, the header wins and this file is fixed. Z to A, per house style.
Where a tool deploys to or reads the live t630, it says so.

| Tool | What it does | Run |
| --- | --- | --- |
| `t630-drift-audit.sh` | Audits selected repo files against the live t630 without overwriting anything, writing diffs under `.audit/t630-drift/`. | `T630_HOST=USER@192.168.1.118 tools/t630-drift-audit.sh` |
| `sync-briefings.py` | Renders the canonical Bifrost briefing block into every A777ance repo's `CLAUDE.md`. | `python3 tools/sync-briefings.py` (report drift), `--write` (fix it) |
| `racetrack_plan.py` | Plans a hybrid course over a fixed roadmap under a token budget; no model is called. | `python3 tools/racetrack_plan.py --budget 500000 --lanes 8` |
| `racetrack.py` | Scores one racetrack mode folder by checking its citations and counts. | `python3 tools/racetrack.py MODE` (or `--selftest`) |
| `migrate.sh` | The one-time 1.x to 2.0 folder migration, already applied: backs up the repo, moves files to the 2.0 layout, rewrites path references and prunes the legacy folders. It has no header, only a banner, and must run from the repo root. | not to be run again |
| `matrix.py` | The Matrix's own tooling: one entry point, called as `cardinal.method`. | `python3 tools/matrix.py list` |
| `laptop-sync.sh` | Keeps a checkout of `leader` current by fast-forward-only pulls, on a systemd user timer. | `bash tools/laptop-sync.sh run` (or `install`, `status`, `uninstall`) |
| `factory.sh` | The bounded software-factory loop over the racetrack queue; hands off one milestone at a time. | `bash tools/factory.sh`; after an agent: `bash tools/factory.sh --finish ID TOKENS` |
| `deploy-volume-layer.sh` | Deploys and verifies the nftables per-category volume layer on the live t630. | `T630_HOST=USER@192.168.1.118 T630_USER=USER tools/deploy-volume-layer.sh` |
| `check-telepathy.py` | End-to-end test of the telepathy mailbox and its watcher, in a throwaway directory; Linux only. | `python3 tools/check-telepathy.py` |
| `check-superfleet.py` | Gate for the superfleet plan (`.claude/superfleet.json`). | `python3 tools/check-superfleet.py` (or `--list`, `--review S01 L2 BRANCH`) |
| `check-stop-hook.py` | Tests the Stop hook on sample replies, and that every rule it enforces is named in the Briefing style. | `python3 tools/check-stop-hook.py` |
| `check-statements.py` | Gate for the honesty rule on Statements: no category volume shown that was not measured. | `python3 tools/check-statements.py` |
| `check-rsi.py` | Gate for RSI-OODA: the lean queue never drops to 2 open (ongoing-OODA, ∆§), lean ids are unique, every ledger pass has its run file, the name is always RSI-OODA, and every entry in `docs/ai-cto/planned.md` is well formed and newest first. | `python3 tools/check-rsi.py` |
| `check-registers.py` | Gate for the AI-CTO registers (`initiatives.md`, `debt.md`) and the `CLAUDE.md` byte budget. | `python3 tools/check-registers.py` |
| `check-provenance.py` | Validates provenance tags across the repo: the enforcement half of the Provenance Ladder. | `python3 tools/check-provenance.py` (or `--strict`, `--stale-days N`) |
| `check-matrix.py` | End-to-end test of the Matrix in a throwaway sandbox copy. | `python3 tools/check-matrix.py` |
| `check-doctrine.py` | Asserts the mechanically decidable clauses of CLAUDE.md §G against the juror sampler code. | `python3 tools/check-doctrine.py` |
| `check-docs.py` | Validates Markdown links and repo-path references in every doc. | `python3 tools/check-docs.py` |
| `check-decisions.py` | Gate for the decision log (`docs/ai-cto/blocked.md`): status, unique ids, newest first. | `python3 tools/check-decisions.py` |
| `check-cardinal.py` | Gate for the cardinal alias map (`.claude/cardinal-map.json`). | `python3 tools/check-cardinal.py` |
| `check-bridge.py` | Gate for the bridge display: draws every panel at four widths and fails on a crash, an overflow or stray colour codes. | `python3 tools/check-bridge.py` |
| `check-all.sh` | The one entry point for "is this repo healthy": every preflight step and static gate, failing closed. | `bash tools/check-all.sh` (or `--quick`) |
| `bridge.py` | The bridge display: the loop's state as a text dashboard. | `python3 tools/bridge.py` (or `--once`, `--plain`, `--statusline`) |

Folders: `browser/` (the repo in a claude.ai artifact: hook ports, the explorer page, the gate; see its README),
`telepathy/` (mailboxes between Claude sessions).
