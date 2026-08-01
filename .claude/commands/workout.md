---
description: Your full WORKOUT (bodybuilding schema) — hand it any normal prompt and it runs the whole Jury routine end to end (CLAUDE.md §G): warm up, pick the right lift, report a verdict. Not picky about input — it decides the path (keyless /cardio vs live /strength) for you.
argument-hint: <any question or judgment call, in plain language — no special format>
allowed-tools: Task, Bash(python3:*)
---

Run the full Jury routine (CLAUDE.md §G) on whatever the user handed you. **Be
forgiving about the input** — a math problem, a factual call, a design decision,
or open-ended prose are all fair game. Do NOT make the user reformat anything, and
do NOT ask clarifying questions unless the prompt is truly unintelligible.

**Prompt:** $ARGUMENTS

### 1. Warm-up — size the session (keyless, instant)

Read the prompt and decide its shape:

- **Discrete answer** (a number, a name, a label, yes/no, "which of these") →
  votable. Make sure the question ends with a canonical `End with 'ANSWER: <x>'.`
  instruction (append it if it's missing) so draws tally by exact match.
- **Open-ended prose** (explain, design, weigh trade-offs) → self-consistency
  voting is weaker (answers won't cluster on exact match). Still empanel a panel
  for the judgment, but report the result as *where the panel leans*, not a hard
  verdict — and say so.

### 2. Pick the lift — automatic, don't ask

Detect a key:

```bash
test -n "$ANTHROPIC_API_KEY" || test -f 04-user-services/ai-orchestration/jury-claude/.env && echo strength || echo cardio
```

- **`strength`** (key present) — the statistical jury, real API:
  ```bash
  python3 04-user-services/ai-orchestration/jury-claude/jury_claude.py strength \
    --prompt "$ARGUMENTS  End with 'ANSWER: <x>'." \
    --answer-marker ANSWER: --effort medium --min-n 3 --max-n 12 --batch 3
  ```
  Drop the appended `End with…` if the prompt is open-ended; bump `--effort high`
  / `--max-n` when the question is clearly hard.
- **`cardio`** (no key) — the keyless in-harness jury: empanel **5** concurrent
  `juror` subagents (Task tool, `subagent_type: "juror"`) on the prompt in a
  **single message**, **each with a different answer-preserving framing** (plain /
  skeptic / restate / cross-check / avoid-the-trap — same list as `/cardio`) so the
  draws decorrelate by construction. Collect their `ANSWER:` lines, normalize, and
  take the plurality. On a 3–2 / no-majority split, empanel **4 more** (to 9,
  varying framings) once, then stop.

### 3. Cool-down — report honestly

Give the **verdict**, the **tally**, and a one-line confidence read (unanimous /
strong majority / split). If it hit max-n or split, say so plainly — a jury that
won't converge means the question is genuinely contested, and that *is* the
finding; never dress a split as a clean verdict. If the panel agrees strongly but
you suspect it's confidently wrong, flag possible **systematic bias** — a vote
can't fix that (see `/diet` for what that looks like).

> `/workout` is the **per-prompt** routine. The deeper homework — `/diet` (when a
> vote can be trusted) and `/form` (measure real `p̂` on a labelled set) — you do
> **once per task type**, not per prompt. Only mention them if the user wants to
> characterize a whole class of questions before trusting votes.
