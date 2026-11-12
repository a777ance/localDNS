# Handoff: where the next session starts

Written 2026-11-12, about 00:40 UTC. Everything described here is on `leader` (see `docs/ai-cto/branches.md`: `main` is now intent cold storage). Read this once,
then work the queue. The finished queue from the first lease (Q-001 to Q-030) is archived in
`docs/ai-cto/handoff-2026-11-11.md`; the story of that session is in `docs/ai-cto/session-log.md`.

Start here, in a cloud session (the path is the cloud container's; on the founder's laptop
the repo is `~/localDNS`):

```bash
cd /home/user/localDNS
python3 tools/matrix.py orient.probe && python3 tools/matrix.py decide.open && python3 tools/matrix.py decide.gate
```

Lease: `start: none · expiry: none (no lease is running; the founder is in the loop)`.

---

## 1. What exists, in one screen

| Piece | Where | State |
| ----- | ----- | ----- |
| Labels on every tool call ("the Matrix") | `.claude/hooks/cardinal.py`, `.claude/cardinal-map.json` | Live. Mode `warn`: labels and reminders, nothing blocked. |
| Stopwatch on every tool call | `.claude/hooks/timing.py`, `observe.times` | Live. A call over 10 s is named at once. |
| Reply rules that enforce themselves | `.claude/hooks/decide-act.py`, `tools/check-stop-hook.py` | Seven rules, 23 test replies. |
| Own tooling, called as `cardinal.method` | `tools/matrix.py` (`python3 tools/matrix.py list`) | 22 methods. |
| 1 + N lanes: the probe goes first (INIT-006) | `observe.probe`, `orient.probe`, `decide.probe`, `act.probe` | Built. Hook flags egress or a new lane with no fresh probe. |
| Look before the founder leaps (DEBT-012) | `decide.rehearse` | Built. An unrehearsed command in a reply is bounced. |
| Retrofit: a new rule reaches backward (INIT-007) | `orient.retrofit` | Built for the seven reply rules. |
| Memory across restarts | `docs/ai-cto/checkpoint.md`, `.claude/hooks/resume.py`, `.claude/hooks/precompact.py` | Resume seen live. Compaction text not yet seen live. |
| Laptop keeps itself current | `tools/laptop-sync.sh` | Built and rehearsed; the timer install has not been run on the laptop. |
| Nine gates on every commit | `.claude/hooks/gate.sh`, `python3 tools/matrix.py decide.gate` | All pass. |

## 2. The founder's intent, as it stands

The seven points in the archived handoff still hold. Added since, in his words or close to them:

1. **Look before we leap.** Three recipes failed on his laptop because none had been run first. Never again: rehearse, probe, then act.
2. **1 + N lanes.** The 1 is always the probe. The N is the work in any shape. Every tool call has a quick probe available; each cardinal has its own.
3. **Retrofit.** A new rule applies to what already exists, including rules not yet written.
4. **Announce every scratchpad.** Nothing gets lost in the woodwork.
5. **No multi-turn fixes.** A recipe that needs three tries is a defect in the recipe.
6. **Durability and posterity.** If it is not on `main` and written down, it did not happen.

## 3. Rules of engagement

- **Do without asking:** build, test, and ship to the session's branch; merge a docs or tooling change into `leader` after a passing `observe.probe merge` (the founder's standing rule is "push to `main`", and DEC-010 scopes tiles to what a revert cannot undo).
- **Never without the founder:** the gate mode (the permission system refuses a session that tries; it is his hand or nothing), `enforce`, anything on the live t630, the Bifrost spec, real customer data, spending money.
- **Never at all:** watching a PR. Opening a PR subscribes the session automatically; it unsubscribes on merge. If a PR stays open, unsubscribe by hand.
- **Before any command goes to the founder:** `python3 tools/matrix.py decide.rehearse --at HIS_COMMIT "COMMAND"`. His path is `~/localDNS`.

## 4. Hazards the last session hit

- **The Stop hook bounces a reply** for: no state word; a numbered Decide list with fewer Act lines; a `bash` block not starting with `cd`, or starting with `/home/user/`; a hedge; an incomplete tile; an unrehearsed command with no `Not rehearsed:` line; an unannounced scratchpad file.
- **The commit gate reads the command text.** A shell command that merely quotes the words "git commit" runs the gates first and is blocked while one is red. Keep such text out of unrelated commands.
- **`decide.rehearse` copies the repo, not the laptop.** Give uncommitted state with `--setup`. Read its output; do not trust exit 0 alone (that is how its own stale-remote bug was found).
- **Chaining ships or rehearsals in one shell call breaks the 10-second cap.** One per call.
- **After a merge, restart the session branch from `main`** and push it, or the Stop hook reports an unpushed commit.

## 5. The queue

One item at a time, in order. Each has a done-test.

- **Q-031 · See the hooks in a fresh session on `main`.** Look for a `cardinal:` line with `Matrix route` on the first `Read`. Done: recorded in DEBT-008. This is the proof the merge reached new sessions.
- **Q-032 · See the trimmed setup script run in a fresh cloud container.** Done: nine `ok` lines in the setup log, recorded under DEC-014.
- **Q-033 · See a live Stop-hook bounce and a live compaction.** Done: both recorded in DEBT-008, with the hook text that appeared.
- **Q-034 · A quick probe for every mapped tool (INIT-006).** Add a `probe` field per tool in `.claude/cardinal-map.json` (the dry-run form of the call, or the reason none exists) and make `tools/check-cardinal.py` fail on a tool with neither. Done: gate green.
- **Q-035 · Retrofit audits for the prose-only rules (INIT-007).** House style (newest first, Z to A), provenance, and the Jury doctrine have no audit in `orient.retrofit`. Add one each, or the stated reason none can exist. Done: `orient.retrofit` lists them.
- **Q-036 · 1 + N in the Bifrost notation.** A proposal for the founder only: where lane 0 sits relative to `^`. Do not edit the spec. Done: a tile in `docs/ai-cto/blocked.md`.
- **Q-037 · Confirm the laptop timer.** Once the founder has run `bash tools/laptop-sync.sh install`, ask for the output of `bash tools/laptop-sync.sh status`. Done: recorded in the session log.
- **Q-038 · BLOCKED on DEC-005 · venv peering files.** Needs the two facts from the XPS listed in `docs/ai-cto/roadmap.md`.
- **Q-040 · Sort the files between `leader` and `outer` (DEC-015).** Both start as full copies. Move the non-OODA tree off `leader` and the OODA tree off `outer`, repointing `tools/check-docs.py` and `tools/check-doctrine.py` first so the gates stay green on each. Done: gates pass on both branches, and `docs/ai-cto/branches.md` says so.
- **Q-041 · BLOCKED on DEC-016 · Empty `main`.** The pull request is prepared. Merge it only on the founder's GO.
- **Q-039 · Shrink sections G and H of `CLAUDE.md`.** They are 17,000 of its 60,000 bytes. Each needs its checks repointed first. A proposal with measurements, then a tile.

## 6. Ending a session

1. `python3 tools/matrix.py decide.gate` and `python3 tools/matrix.py orient.retrofit` both pass; the tree is clean.
2. `python3 tools/matrix.py orient.checkpoint`, then update the prose in `docs/ai-cto/checkpoint.md`.
3. Add an entry at the top of `docs/ai-cto/session-log.md`.
4. Tick queue items here with `· DONE <commit>`.
5. Everything is on `leader`, and the session branch matches it. Nothing is pushed to `main`.
