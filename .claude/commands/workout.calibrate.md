---
description: Composed lift — workout(calibrate()). Runs the calibrate/form step FIRST (measure p̂ / the vote's trustworthiness), THEN runs the full /workout jury and reports the verdict BOUNDED by that calibration. The "measured p̂" counterpart to a bare /workout: it never dresses an uncalibrated plurality as a certified one.
argument-hint: <prompt, plain language> [-- path/to/labelled.jsonl]   (dataset optional; without one the calibrate step is keyless/hypothesized and labelled as such)
allowed-tools: Task, Bash(python3:*)
---

**Composed command — the nesting convention.** In this command family a dotted
name is **function composition, innermost first**:
`/workout.calibrate` ≡ `workout(calibrate())` — `calibrate` runs first, its result
feeds `workout`. Deeper nesting reads the same way — `/workout.calibrate.calibrate`
≡ `workout(calibrate(calibrate()))` — but the harness matches commands by
*filename*, so each depth is its own file following this same rule (there is no
auto-recursion). This file is depth-1. (Doubling the inner step,
`calibrate(calibrate())`, means *calibrating the calibration* — the
`--no-variants` vs `--variants` sensitivity check from the jury-claude README; add
that file only if you actually want it.)

**Why this exists.** A bare `/workout` returns a plurality but can't certify it —
per CLAUDE.md §G, "measure `p`, don't guess it." This composed lift does the
measuring first, then attaches the honest bound to the verdict, so the report
states *whether a vote is even trustworthy on this task* instead of leaving the
reader to assume it.

**Prompt:** $ARGUMENTS

---

### 1. Inner step — `calibrate()` runs FIRST (measure the vote's trustworthiness)

Split `$ARGUMENTS` on `--`: text before is the **prompt**, an optional path after
is a **labelled JSONL** (`{"prompt":…, "answer":…}` per line) describing the
prompt's *task type*.

- **Key check.** If neither `ANTHROPIC_API_KEY` is set nor
  `04-user-services/ai-orchestration/jury-claude/.env` exists, do NOT run live —
  say so, and run the **keyless synthetic** calibrate instead. State plainly that a
  keyless run measures a *hypothesized* `p`, not real Claude on this task.

- **Dataset given, key present → measure it for real:**
  ```bash
  python3 04-user-services/ai-orchestration/jury-claude/jury_claude.py calibrate \
    --dataset <DATASET> --answer-marker ANSWER: --samples-per-q 12 --effort medium
  ```

- **No dataset (or no key) → keyless regime read** (hypothesized `p`, no spend):
  ```bash
  python3 04-user-services/ai-orchestration/jury-claude/jury_claude.py calibrate \
    --mock-p 0.7 --mock-questions 120 --answer-marker ANSWER: --samples-per-q 12
  ```
  Mention that `study` / `/diet` (and `--mock-rho` / `--mock-systematic`) map the
  failure modes — correlation collapse and systematic bias — a single number hides.

Read `verdict` first. The load-bearing §G-on-Claude check: **if
`accuracy_adaptive_vote` barely beats `p_hat_single_sample`, the draws are too
correlated for a vote to help here** — the lever is a better prompt or higher
`--effort`, not a temperature Claude doesn't have. Hold this read for step 3.

### 2. Outer step — `workout()` (run the jury on the prompt)

Run the standard `/workout` routine on the **prompt** (see `.claude/commands/workout.md`):
size it (discrete → append `End with 'ANSWER: <x>'.`; open-ended → report the
*lean*), pick the lift automatically (`strength` if a key is present, else the
keyless `cardio` panel of 5 `juror` subagents → +4 to 9 on a 3–2 split), and tally
the plurality.

### 3. Cool-down — report the verdict BOUNDED by the calibration

Give the `/workout` verdict, tally, and confidence read — then **bind it to step 1**:

- Calibration says the vote **pays off** (`accuracy_adaptive_vote` clears
  `p_hat_single_sample`, and `p̂` puts the right answer in the modal position) →
  report the plurality as **calibration-backed**, and say on what basis (measured
  on a labelled set, or hypothesized keyless — never blur the two).
- Calibration says the vote **doesn't help / hurts** (draws too correlated, or
  systematic bias below `p=0.5`) → say so outright: the plurality is **not
  certified**; treat it as illustrative and name the lever (better prompt / higher
  `--effort`). A vote cannot fix systematic bias — flag it rather than dress it.

The whole point of the composition: never present a plurality without its measured
bound. If the calibrate step was keyless, the honest line still holds —
*"trustworthy consensus, but the numeric spread is illustrative, not measured"* —
until it's run against a labelled set.
