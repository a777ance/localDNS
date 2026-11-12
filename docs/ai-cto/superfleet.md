# The superfleet

The founder's name for it: the OODA Haiku Swarm. Decided 2026-11-12 (DEC-020, GO). A fleet of
small-model sessions, planned in advance, for improving how the loop bootstraps: how a session
comes up, finds its rules, and starts work. Ten scenarios, 34 lanes.

## Who does what

- **This repo holds the plan and the checks.** The plan is data: `.claude/superfleet.json`. The
  gate is `tools/check-superfleet.py`. Neither holds instructions for any agent.
- **The founder writes each lane's instructions,** in his work account, from the plan. A session
  in this repo does not write them: the platform stopped that three times on 2026-11-12, and the
  session did not go around it.
- **The founder starts the lanes and reviews what comes back.**

## How a scenario runs

1. **Look first (lane 0).** Run the scenario's look-first command. If it fails, fix that before any lane starts.
2. **The lanes.** Each lane works only inside its own write area. No two lanes in the whole plan
   share one, so every lane can run at the same time as any other.
3. **Each lane lands on its own branch,** named after its scenario and lane, with a pull request into `leader`.
4. **Review.** For each finished branch, run the review command below. It answers the one
   question that must not be judged by eye: did the lane change anything outside its own area?
5. **Integrate.** A lane produces findings or data, never a change to a rule or a hook. Turning a
   finding into a change is separate work, done by one session, in queue order.

The plan, one line per lane:

```bash
cd ~/localDNS
python3 tools/check-superfleet.py --list
```

A finished lane's branch, checked:

```bash
cd ~/localDNS
python3 tools/check-superfleet.py --review S01 L2 origin/leader
```

The second command is shown with `origin/leader` as the branch so that it runs today; it reports
that the branch changed nothing, which is the right answer until a lane has run. Put the lane's
own branch in its place.

## What every lane has to obey

These are the repo's rules, stated here for whoever writes the lanes' instructions:

- Work on its own branch cut from `leader`. Never push to `main`.
- Create or change files only inside its write area. Anything else it notices is a finding, not a fix.
- Never edit `CLAUDE.md`, the hooks, the hook settings, or the tool map. Never change the gate mode.
- Report only what it saw, with the file and the line.
- The reply rules, the letters (O, OO, D, A, L), and the landing line apply inside each lane as they do anywhere in this repo; the hooks enforce them in any checkout.
- A new rule reaches backward (retrofit): a lane that finds old material breaking a rule reports it.

## The ten scenarios

| # | Scenario | What it improves | Lanes | Look first |
| - | -------- | ---------------- | ----- | ---------- |
| S01 | Cold-start read-through | Find every place where the start-of-session documents lose a newcomer. | 4 | `python3 tools/matrix.py orient.probe` |
| S02 | Sample replies for the reply rules | Widen the set of sample replies the Stop hook is tested against. | 4 | `python3 tools/check-stop-hook.py` |
| S03 | Sample commands for the naming hook | Widen the set of shell commands the naming hook is tested against. | 3 | `python3 tools/check-matrix.py` |
| S04 | Retrofit sweep of the prose rules | Apply the rules that live only in prose to what already exists. | 4 | `python3 tools/matrix.py orient.retrofit` |
| S05 | Review of the per-tool probes | Check that each of the 110 probe entries is sensible. | 3 | `python3 tools/check-cardinal.py` |
| S06 | Briefing diet proposals | Propose a shorter form of each large section of CLAUDE.md with nothing lost. | 4 | `python3 tools/check-registers.py` |
| S07 | Work orders for the superqueue | Turn each open item in the loop's lane into a work order a session can pick up cold. | 3 | `python3 tools/matrix.py orient.probe` |
| S08 | Edge inputs for the Statement gate | Widen the inputs the Statement gate is run on. This one is product work. | 3 | `python3 tools/check-statements.py` |
| S09 | Summaries of the old branches | Say what each old branch holds that leader does not. | 3 | `python3 tools/matrix.py observe.probe merge Yggdrasil leader` |
| S10 | Stress test of the rules | Find replies the hooks judge wrongly, in both directions. | 3 | `python3 tools/check-stop-hook.py` |

## Each scenario's lanes

### S01 · Cold-start read-through

Find every place where the start-of-session documents lose a newcomer. Review: A person reads the four findings files and decides which become queue items.

| Lane | Covers | Write area | Done when |
| ---- | ------ | ---------- | --------- |
| L1 | CLAUDE.md, the reply-style section | under `docs/ai-cto/fleet/`, folder S01/L1 | one findings file per item examined, each finding with a file and line |
| L2 | docs/ai-cto/handoff.md and docs/ai-cto/checkpoint.md | under `docs/ai-cto/fleet/`, folder S01/L2 | one findings file per item examined, each finding with a file and line |
| L3 | docs/ai-cto/superqueue.md and docs/ai-cto/dependency-map.md | under `docs/ai-cto/fleet/`, folder S01/L3 | one findings file per item examined, each finding with a file and line |
| L4 | docs/ai-cto/branches.md and docs/ai-cto/loop-tick.md | under `docs/ai-cto/fleet/`, folder S01/L4 | one findings file per item examined, each finding with a file and line |

### S02 · Sample replies for the reply rules

Widen the set of sample replies the Stop hook is tested against. Review: A session loads the data files into tools/check-stop-hook.py; a sample the hook judges differently is a finding.

| Lane | Covers | Write area | Done when |
| ---- | ------ | ---------- | --------- |
| L1 | the state word and landing line rules | under `docs/ai-cto/fleet/`, folder S02/L1 | twenty sample replies with the expected verdict for each, as data |
| L2 | the Decide and Act, next action, and L rules | under `docs/ai-cto/fleet/`, folder S02/L2 | twenty sample replies with the expected verdict for each, as data |
| L3 | the command rules: cd first, rehearsed, no hedges | under `docs/ai-cto/fleet/`, folder S02/L3 | twenty sample replies with the expected verdict for each, as data |
| L4 | the tile and scratchpad rules | under `docs/ai-cto/fleet/`, folder S02/L4 | twenty sample replies with the expected verdict for each, as data |

### S03 · Sample commands for the naming hook

Widen the set of shell commands the naming hook is tested against. Review: A session runs the hook on each command; a mismatch is a finding against the classifier or the sample.

| Lane | Covers | Write area | Done when |
| ---- | ------ | ---------- | --------- |
| L1 | observe: read-only commands, including odd quoting | under `docs/ai-cto/fleet/`, folder S03/L1 | thirty commands with the expected label, as data |
| L2 | orient and decide: probes, gates, rehearsals | under `docs/ai-cto/fleet/`, folder S03/L2 | thirty commands with the expected label, as data |
| L3 | act: writes, ships, pushes, and commands that only quote those words | under `docs/ai-cto/fleet/`, folder S03/L3 | thirty commands with the expected label, as data |

### S04 · Retrofit sweep of the prose rules

Apply the rules that live only in prose to what already exists. Review: Findings only; nothing is changed. A person decides which are real, and a session fixes those.

| Lane | Covers | Write area | Done when |
| ---- | ------ | ---------- | --------- |
| L1 | newest-first ordering in logs and registers | under `docs/ai-cto/fleet/`, folder S04/L1 | one findings file per item examined, each finding with a file and line |
| L2 | Z to A ordering in alphabetical lists | under `docs/ai-cto/fleet/`, folder S04/L2 | one findings file per item examined, each finding with a file and line |
| L3 | plain-English voice in docs/statements/ | under `docs/ai-cto/fleet/`, folder S04/L3 | one findings file per item examined, each finding with a file and line |
| L4 | no secret values and no real customer data anywhere in the tree | under `docs/ai-cto/fleet/`, folder S04/L4 | one findings file per item examined, each finding with a file and line |

### S05 · Review of the per-tool probes

Check that each of the 110 probe entries is sensible. Review: A session corrects the entries a person agrees are wrong.

| Lane | Covers | Write area | Done when |
| ---- | ------ | ---------- | --------- |
| L1 | the observe tools' entries | under `docs/ai-cto/fleet/`, folder S05/L1 | one findings file per item examined, each finding with a file and line |
| L2 | the orient and decide tools' entries | under `docs/ai-cto/fleet/`, folder S05/L2 | one findings file per item examined, each finding with a file and line |
| L3 | the act tools' entries | under `docs/ai-cto/fleet/`, folder S05/L3 | one findings file per item examined, each finding with a file and line |

### S06 · Briefing diet proposals

Propose a shorter form of each large section of CLAUDE.md with nothing lost. Review: Proposals only. CLAUDE.md is not edited. The founder picks; sections G and H need his yes (lean 24).

| Lane | Covers | Write area | Done when |
| ---- | ------ | ---------- | --------- |
| L1 | section C, deploy paths | under `docs/ai-cto/fleet/`, folder S06/L1 | a proposed text and a list of what moved where |
| L2 | section G, the Jury doctrine | under `docs/ai-cto/fleet/`, folder S06/L2 | a proposed text and a list of what moved where |
| L3 | section H, Bifrost | under `docs/ai-cto/fleet/`, folder S06/L3 | a proposed text and a list of what moved where |
| L4 | sections 1 and 3, known issues and working philosophy | under `docs/ai-cto/fleet/`, folder S06/L4 | a proposed text and a list of what moved where |

### S07 · Work orders for the superqueue

Turn each open item in the loop's lane into a work order a session can pick up cold. Review: A person reads the twelve work orders; a session then works them in queue order.

| Lane | Covers | Write area | Done when |
| ---- | ------ | ---------- | --------- |
| L1 | SQ-001 to SQ-004 | under `docs/ai-cto/fleet/`, folder S07/L1 | one work order per item: files, done-test, risks |
| L2 | SQ-005 to SQ-008 | under `docs/ai-cto/fleet/`, folder S07/L2 | one work order per item: files, done-test, risks |
| L3 | SQ-009 to SQ-012 | under `docs/ai-cto/fleet/`, folder S07/L3 | one work order per item: files, done-test, risks |

### S08 · Edge inputs for the Statement gate

Widen the inputs the Statement gate is run on. This one is product work. Review: A session loads the inputs into tools/check-statements.py; any figure not carried by the input is a product defect.

| Lane | Covers | Write area | Done when |
| ---- | ------ | ---------- | --------- |
| L1 | traffic mixes: ties, one category, very many, very small | under `docs/ai-cto/fleet/`, folder S08/L1 | twenty inputs as data, each with what the output must satisfy |
| L2 | missing and partial measurements | under `docs/ai-cto/fleet/`, folder S08/L2 | twenty inputs as data, each with what the output must satisfy |
| L3 | sidecar settings that could tempt an unmeasured figure onto the page | under `docs/ai-cto/fleet/`, folder S08/L3 | twenty inputs as data, each with what the output must satisfy |

### S09 · Summaries of the old branches

Say what each old branch holds that leader does not. Review: The founder reads the three summaries and decides what to keep (leans 17 and 18).

| Lane | Covers | Write area | Done when |
| ---- | ------ | ---------- | --------- |
| L1 | the branch Yggdrasil | under `docs/ai-cto/fleet/`, folder S09/L1 | a summary of at most thirty lines, with commit ids |
| L2 | the branch doom-drawer/2026-08-08 | under `docs/ai-cto/fleet/`, folder S09/L2 | a summary of at most thirty lines, with commit ids |
| L3 | the branch cloudflare/workers-autoconfig | under `docs/ai-cto/fleet/`, folder S09/L3 | a summary of at most thirty lines, with commit ids |

### S10 · Stress test of the rules

Find replies the hooks judge wrongly, in both directions. Review: A session runs each candidate; every confirmed misjudgment becomes a test case and a fix.

| Lane | Covers | Write area | Done when |
| ---- | ------ | ---------- | --------- |
| L1 | replies that break a rule and may still pass | under `docs/ai-cto/fleet/`, folder S10/L1 | fifteen candidates as data, each naming the rule |
| L2 | replies that keep every rule and may still be bounced | under `docs/ai-cto/fleet/`, folder S10/L2 | fifteen candidates as data, each naming the rule |
| L3 | commands that are labelled wrongly, or flagged for no reason | under `docs/ai-cto/fleet/`, folder S10/L3 | fifteen candidates as data, each naming the flag |

## Limits

- No lane has run. The plan is checked for shape; whether a small model can do each lane well is not known.
- The write areas do not exist yet. Each is created by the lane that owns it.
- S08 is the only scenario that is product work. The other nine improve the loop.
- Cost is not estimated here. Record each lane's cost in `docs/ai-cto/session-log.md` when it has run.
