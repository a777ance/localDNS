# Handoff: Orchestrator roadmap for a 3-hour lease

Written 2026-11-11, about 22:45 UTC, by the outgoing session, for the Orchestrator session
that takes over. Read this file top to bottom once, then work the queue. Everything here is
on branch `decision-log-dec007` (PR #37, draft). The founder (Dave) is away and is **not in
the loop**.

Start here, in a fresh terminal:

```bash
cd /home/user/localDNS
git fetch origin decision-log-dec007 && git checkout decision-log-dec007 && git pull --ff-only origin decision-log-dec007
python3 tools/matrix.py observe.status
python3 tools/matrix.py decide.open
python3 tools/matrix.py decide.gate
```

Then record your lease start in section 2, ship that one-line edit, and begin at Q-001.

---

## 1. The founder's intent, reviewed

What Dave asked for over the session, distilled. When a queue item is unclear, decide by these.

1. **A loop that never stalls in thought.** Every reply is an OODA briefing. Options are
   queued and acted on, never offered as a menu. "Prioritize action over the OO-OO part."
2. **Dave out of the loop unless absolutely necessary.** A founder decision is a loud
   GO / NO GO tile, logged as `DEC-NNN`. Everything else runs without asking.
3. **Rules that survive.** "No flash in the pan." A rule that lives only in a conversation
   or in prose is not a rule; it needs a hook, a check, or a file the next session reads.
4. **The Matrix. Motto: "There is no way out."** Every tool call, workflow, and subagent is
   named `cardinal.method` and, in time, routed through our own tooling. Native tools get
   gated step by step, with a 10-second cap and a one-time fallback so work is never roadblocked.
5. **Ten seconds per tool call is the Holy Grail.** A breach is a defect: diagnose and
   improve the alias at once.
6. **Spend tokens like money. Never poll. Never idle.** Strike while the iron is hot:
   commit and push each finished piece at once.
7. **The OODA loop is an ongoing goal (RSI).** Each cycle re-evaluates the rules, raises the
   quality bar, and adds tooling. A null result gets new work, not silence.

### The outgoing session's honest read (weigh this, do not just execute)

- **The biggest risk is rule inflation.** Each rule added to `CLAUDE.md` raises the fixed
  cost of every turn of every session (it was about 24.5k tokens before this session's
  additions). Intent 3 and intent 6 pull against each other unless rules move **out of
  prose and into hooks and checks**. So the direction of travel for this lease is:
  *mechanize a rule, then shorten its prose to one line.* Never add a rule without a site.
- **Boyd's point is that Orient is the centre, not a step.** A faster loop comes from a
  cheaper, truer Orient, not from more Act. Here that means `orient.ground`,
  `observe.status`, and the checkpoint must stay under a second and stay current. Boyd's
  "implicit guidance and control" is what the hooks are: guidance that needs no deliberation.
  His "Destruction and Creation" is what intent 7 asks for: break a rule that failed, rebuild it.
- **Peers were expensive and mostly produced nothing.** Eight peer sessions cost about
  $12.80; 42 ping-pong rounds produced no work product; one useful rule came out of one
  round. Do not recruit peers in this lease (see section 3).
- **`enforce` mode can lock a session out.** It has never run live. Treat it with the
  respect of a firewall rule on a remote box: kill switch ready, one session, founder GO first.
- **"There is no way out" versus the exits.** The kill switch and the one-time lease are
  ways out, kept on purpose so a stalled Matrix call cannot brick a session. Read the motto
  as "no call runs unnamed". Do not remove the exits without a founder decision.

---

## 2. State at handoff

- **Lease (Orchestrator):** 3 hours from your first action. Record it here when you start:
  `start: 22:52 UTC (2026-11-11) · expiry: 01:52 UTC (2026-11-12)`.
- **Usage:** the account's five-hour limit showed as reached at 22:28 UTC with overage in
  use; it resets at **01:10 UTC on 2026-11-12**. Work lean until then.
- **Branch and PR:** `decision-log-dec007`, PR #37 (draft, unmerged, not watched). Working
  tree clean at handoff. `main` has the OODA reply style and the Decide-Act hook but **not**
  the Matrix.
- **Built and passing** (`python3 tools/matrix.py decide.gate`, six checks, slowest 2.1 s):

  | Piece | File |
  | ----- | ---- |
  | The Matrix map, repoint table, gate mode (`name`) | `.claude/cardinal-map.json` |
  | Four cardinal skills | `.claude/skills/` (`observe`, `orient`, `decide`, `act`) |
  | Naming hook, three modes, lease, stall notice | `.claude/hooks/cardinal.py` |
  | Stop hook: lead state word + act on Decide lists | `.claude/hooks/decide-act.py` |
  | Auto-wake after compaction | `.claude/hooks/resume.py` |
  | Own tooling, 10 s cap, lease, stalls, ship | `tools/matrix.py` |
  | Gates | `tools/check-cardinal.py`, `tools/check-matrix.py`, `tools/check-decisions.py` |
  | Registers | `docs/ai-cto/` (`initiatives.md`, `debt.md`, `blocked.md`, `checkpoint.md`) |
  | Peer prompt template | `docs/ai-cto/bootstrap-peer-template.md` |
  | Telepathy mailbox and watcher | `tools/telepathy/` |

- **Open founder decisions:** DEC-012 (gate to `warn`), DEC-011 (merge PR #37), DEC-010
  (scope the tile rule), DEC-005 (venv files). DEC-004 and DEC-006 are moot (PR #36 merged).
- **Peers:** all eight archived. None running.

---

## 3. Rules of engagement for this lease

**The lease covers:** building, testing, committing, and pushing to `decision-log-dec007`;
editing files under `tools/`, `.claude/`, and `docs/ai-cto/`; adding rows and one-line rules
to `CLAUDE.md`; updating the PR #37 description.

**The lease does not cover** (each needs a founder GO, so write a DEC tile and move on):
merging anything into `main`; changing the gate `mode`; deleting or rewriting the founder's
own sections of `CLAUDE.md`; deleting remote branches; editing the cloud environment;
creating peer sessions or spawning agents (one exception: Q-004); anything on the live t630.

**Planned files do not exist yet.** The docs check fails on a backticked path to a missing
file, so this roadmap names planned files without a full path. Create the file in the same
commit that first references its path.

**Working rules:**

1. One queue item at a time, in order. Skip a `BLOCKED` item; do not reorder otherwise.
2. Ship each finished item at once: `python3 tools/matrix.py act.ship "MESSAGE" FILE... --push`.
   It runs every gate first. End the commit message with the attribution lines your own
   session's reminder gives you.
3. If an item fails twice, stop, record it in `docs/ai-cto/blocked.md` with the error and
   the next diagnostic, and take the next item. Never loop on a failure.
4. Update `docs/ai-cto/checkpoint.md` at every third shipped item and before any long call.
5. Never poll, never `sleep` to wait, never subscribe to PR activity. If nothing is left
   that you can do, write the final report (section 6) and end the turn.
6. Keep tool output short: line ranges, counts, `head`. Do not print whole files.
7. No model names in any file, commit message, or PR text.

**Hazards you will hit:**

- **The Stop hook bounces a reply** that does not open with `**Done**`, `**Partial**`,
  `**Blocked**`, or `**Waiting**`, and any reply with a numbered list under a "Decide"
  heading (it tells you to act on the list). Only write a numbered Decide list when you
  mean to act on it in the same turn. One bounce per turn at most.
- **The commit gate** (`.claude/hooks/gate.sh`) blocks any `git commit` while a check is red.
  Fix the cause; do not bypass.
- **`act.edit` and `act.write` leave a `.bak` beside the file.** Delete it before shipping
  (Q-006 fixes this properly).
- **The naming hook mislabels a Bash call whose here-document quotes a Matrix command.**
  Cosmetic; Q-008 covers it.
- **A Matrix call over 10 s** exits 124, writes a one-time native lease, and opens a stall.
  Diagnose it first: `python3 tools/matrix.py orient.stall`, then `act.resolve`.

---

## 4. Research notes (checked 2026-11-11 against the official hooks reference)

These change what is possible. Verify each live before relying on it.

- **Hooks run inside subagents.** Tool events fire the same configured hooks, and the input
  carries `agent_id` and `agent_type`. So the Matrix already reaches subagents in a checkout
  of this repo; the hook can also name *which* agent made a call.
- **`SessionStart` matchers:** `startup`, `resume`, `clear`, `compact`, `fork`. The
  auto-wake hook's `compact` matcher is valid. Consider `resume` and `fork` too.
- **`PreCompact` exists** (matchers `manual`, `auto`). It can block a compaction, and **its
  stdout becomes instructions for the compaction summary**. That is the right place to say
  what the summary must keep.
- **`PostToolUse` exists** and supports `additionalContext`. With `PreToolUse` it gives a
  start and an end for every native call, which is how to *measure* the 10-second rule for
  native tools instead of asserting it.
- **`PreToolUse` can return `updatedInput`**, which rewrites a tool's arguments before it
  runs, and decisions `allow`, `deny`, `ask`, `defer` (deny wins a conflict). The deny
  reason goes to the model. A community report says `additionalContext` on `PreToolUse` is
  single-turn; the deny reason persists.
- **Command hooks default to a 600-second timeout.** Ours set none. A hung hook could stall
  every tool call for ten minutes. Set an explicit short `timeout` (Q-002).

---

## 5. The queue

Each item: what to do, the cardinal it mainly uses, how you know it is done, and a time
budget. Total budget is about 170 minutes; cut from the bottom of each phase if you fall
behind. `BLOCKED` items wait for the founder.

### Phase A · Verify what is only proven on paper (about 20 min)

- **Q-001 · Confirm the hooks fire in your session.** · DONE 743ef6d · `observe`. Make one `Read` and one
  Bash call and look for a `cardinal:` line on each; end one reply without a state word and
  confirm the bounce. Done: three observations recorded in `docs/ai-cto/checkpoint.md`. 5 min.
- **Q-002 · Give every hook an explicit timeout.** · DONE fbb0fb7 · `act.configure`. In `.claude/settings.json`
  add `"timeout": 5` to `cardinal.py`, `decide-act.py`, and `resume.py` entries (leave
  `gate.sh` at 60; its checks take about 3 s). Done: settings valid JSON, gates green,
  `check-cardinal.py` extended to fail if a hook has no timeout. 8 min.
- **Q-003 · Use `agent_id` / `agent_type` in the naming hook.** · DONE bf77e56 · `act.write`. When the hook
  input carries them, append `· agent: <type>` to the cardinal line. Add a case to
  `tools/check-matrix.py`. Done: e2e green. 5 min.
- **Q-004 · One live subagent check (the single permitted spawn).** · SKIPPED (usage limit still reached during the lease; retry after 01:10 UTC) · `decide.vote`. Spawn one
  `juror` with a one-line read-only question and confirm from its transcript or the Matrix
  log that the hook fired for its tool call. Done: result recorded in DEBT-008. Skip if the
  usage limit is still reached. 5 min.

### Phase B · Harden the Matrix's own tooling (about 45 min)

- **Q-005 · Bound `observe.search` and `observe.read`.** · DONE 52ecd1b · `act.write`. Skip files over 1 MB
  and binary files; add `--max N` (default 200 matches) to search; make read default to the
  first 200 lines with a "N more lines" notice. Done: each returns in under 1 s on this
  repo (time it), e2e cases added. 10 min.
- **Q-006 · Move backups out of the tree.** · DONE 52ecd1b · `act.write`. `act.write` and `act.edit` save
  backups to `.claude/.matrix-bak/<timestamp>-<name>` (git-ignored), not beside the file.
  Add `act.undo` to restore the latest backup of a path. Done: e2e covers write → edit →
  undo; no `.bak` left behind. 8 min.
- **Q-007 · Make `act.edit` safe for multi-line text.** · DONE 52ecd1b · `act.write`. Accept
  `--old-file` / `--new-file` so shell quoting cannot corrupt an edit. Done: e2e case with
  quotes, backticks, and newlines. 6 min.
- **Q-008 · Fix the Bash classifier's known misses.** · DONE bf77e56 · `act.write`. A here-document that only
  quotes a Matrix call must not take that call's name; `git commit` inside a quoted message
  must not make a read-only command `act.ship`. Add each as an e2e case first, then fix.
  Done: e2e green. 8 min.
- **Q-009 · `observe.log`: the Matrix watching itself.** · DONE 52ecd1b · `act.write`. Summarize
  `.claude/.matrix-log` as calls per cardinal and per method, with the slowest call. Rotate
  the log at 2,000 lines. Done: method documented in the `observe` skill and the map. 6 min.
- **Q-010 · `orient.checkpoint`.** · DONE 52ecd1b · `act.write`. One command that rewrites the "Where things
  stand" block of `docs/ai-cto/checkpoint.md` from live facts: branch, last five commits,
  open decisions, open stalls, lease line. Done: running it twice changes nothing the
  second time. 7 min.

### Phase C · Measure the Holy Grail instead of asserting it (about 25 min)

- **Q-011 · Time every native tool call.** · DONE c1ea0ef · `act.write`. Add a `PostToolUse` hook
  (`.claude/hooks/timing.py`): `PreToolUse` stamps a start per `tool_use_id` (or tool name
  if no id), `PostToolUse` computes the duration and appends `tool, cardinal, seconds` to
  `.claude/.matrix-times`. Over 10 s, add a context line naming the breach. Fail open.
  Done: e2e case with a simulated pair; file git-ignored. 12 min.
- **Q-012 · `observe.times`.** · DONE 52ecd1b · `act.write`. Report count, median, and worst duration per
  tool and per cardinal from that file, and list every call over 10 s. Done: documented in
  the skill and map. 6 min.
- **Q-013 · Make a breach a debt entry.** · DONE 52ecd1b · `act.write`. `observe.times --debt` prints a
  ready-to-paste `DEBT-NNN` block for each tool whose worst call broke 10 s. Done: tested
  on synthetic data. 7 min.

### Phase D · Mechanize the prose rules, then shorten the prose (about 40 min)

For each item: add the check to `.claude/hooks/decide-act.py` (one bounce per turn, fail
open), add cases to its test, then cut that rule's text in `CLAUDE.md` to one line that
names the hook. This is the phase that pays down rule inflation.

- **Q-014 · Test file for the Stop hook.** · DONE (this commit: Stop hook rules and tests) · `act.write`. a new check, `check-stop-hook` (to be created under `tools/`), feeds
  sample replies to `decide-act.py` in a temp directory and asserts allow or block. Port the
  seven cases already used by hand. Add it to `gate.sh`. Done: gates green. 8 min.
- **Q-015 · Decide and Act parity.** · DONE (this commit: Stop hook rules and tests) · `act.write`. A reply with N numbered Decide items and
  an Act section must have at least N Act lines or say why one is blocked. (This was the
  Carrot starter's unsent second proposal.) 7 min.
- **Q-016 · Commands start with `cd`.** · DONE (this commit: Stop hook rules and tests) · `act.write`. Every fenced `bash` block in a reply
  must have `cd ` as its first command. 5 min.
- **Q-017 · No vague hedges.** · DONE (this commit: Stop hook rules and tests) · `act.write`. Block "should work", "probably works",
  "may have worked" outside code fences and quotes. Keep the list short to avoid false
  positives; record each false positive you meet as a test case. 6 min.
- **Q-018 · Tile integrity.** · DONE (this commit: Stop hook rules and tests) · `act.write`. A reply containing `DECISION · DEC-NNN` must
  contain both action lines and the GO / NO GO line, and that id must exist in
  `docs/ai-cto/blocked.md`. 7 min.
- **Q-019 · Register status gate.** · DONE (this commit: Stop hook rules and tests) · `act.write`. a new check, `check-registers` (to be created under `tools/`): every `DEBT-`
  and `INIT-` heading ends in a valid status; ids are unique and newest first; every
  `Blocked` entry names a `DEC-` id or a `blocked.md` section. Allow `MOOT` in
  `check-decisions.py` and mark DEC-004 and DEC-006 `MOOT` with the reason. 7 min.

### Phase E · Durability and compaction (about 15 min)

- **Q-020 · `PreCompact` hook.** · DONE c1ea0ef · `act.write`. `.claude/hooks/precompact.py` prints
  instructions for the summary: keep the lease times, the open `DEC` ids, the current queue
  item, and the last shipped commit; say that state is in `docs/ai-cto/checkpoint.md`. If
  the working tree is dirty, say so in the same text. Wire it for `manual` and `auto`.
  Done: output under 1,200 characters; e2e case. 8 min.
- **Q-021 · Wake on `resume` and `fork` as well as `compact`.** · DONE c1ea0ef · `act.configure`. Extend the
  `resume.py` matcher. Done: settings valid, gates green. 3 min.
- **Q-022 · One source for the reply-style rules.** · DONE (this commit: Stop hook rules and tests) · `act.write`. The rules exist in both
  `.claude/output-styles/briefing.md` and `CLAUDE.md`. Add a check that the output-style
  file names every rule the hook enforces, so the two cannot drift. 4 min.

### Phase F · Clear small debt (about 15 min)

- **Q-023 · DEBT-006.** · DONE (this commit: Stop hook rules and tests) · `act.write`. Fix the `SyntaxWarning: invalid escape sequence` in
  `tools/check-doctrine.py` (raw string), and add a `--check` alias to
  `tools/sync-briefings.py` for its default mode. Done: no warning on stderr; DEBT-006 → Done. 6 min.
- **Q-024 · Telepathy test.** · DONE (this commit: telepathy test) · `act.write`. a new check, `check-telepathy` (to be created under `tools/`): in a temp mailbox,
  send → inbox → read → mark done, and assert the watcher prints `NEW` for an arrival
  within 2 s. Map the tools into the Matrix (`act.message`, `observe.listen`). 9 min.

### Phase G · Proposals for the founder (write tiles, change nothing) (about 10 min)

Add each to the decision log in `docs/ai-cto/blocked.md` as `OPEN`, with the evidence.

- **Q-025 · DEC-013: split `CLAUDE.md`.** · DONE (this commit: DEC-013 and DEC-014 tiles) · `orient`. Measure each top-level section's size
  (`wc -c`), and propose which sections stay always-loaded (reply style, the Matrix, deploy
  table, known issues) and which move to on-demand files under `docs/`. Evidence: the table
  of sizes. Do not move anything. 6 min.
- **Q-026 · DEC-014: trim the cloud environment setup script.** · DONE (this commit: DEC-013 and DEC-014 tiles) · `orient`. It installs
  `wireguard-tools` and `nftables` on every fresh container; propose dropping them and
  adding `python3 tools/matrix.py decide.gate` as its check step. Do not edit the environment. 4 min.

### Blocked on the founder (do not start)

- **Q-027 · BLOCKED on DEC-011 · Merge PR #37.** On GO: mark ready, merge, then confirm in a
  fresh session on `main` that a `cardinal:` line appears.
- **Q-028 · BLOCKED on DEC-012 · Gate to `warn`.** On GO: set `"mode": "warn"`, ship, run
  one live session, record the result in DEBT-008. `enforce` needs its own decision after
  that, with `touch .claude/.matrix-off` rehearsed first.
- **Q-029 · BLOCKED on DEC-010 · Scope the tile rule.** On GO: one line in the reply style.
- **Q-030 · BLOCKED on DEC-005 · venv peering files.** Needs the founder's XPS output first.
- **Punted by the founder:** the Cloudflare Workers Builds check. Leave it.

---

## 6. Ending the lease

Stop at the expiry time, or when only blocked items remain, whichever is first. Then:

1. Run `python3 tools/matrix.py decide.gate` and `python3 tools/matrix.py observe.status`;
   the tree must be clean.
2. Update `docs/ai-cto/checkpoint.md`, `docs/ai-cto/debt.md`, and `docs/ai-cto/initiatives.md`
   with what shipped, and tick the queue items in this file (add `· DONE <commit>` to each).
3. Update the PR #37 description to match.
4. Write one final report to the founder: what shipped (commit per item), what is blocked
   and on which `DEC`, what you measured (the timing table), and what you would cut. Lead
   with the state word. Then end the turn. Do not wait for a reply.
