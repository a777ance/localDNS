---
description: Your DIET (bodybuilding schema) — plan what works before you train. Runs the Jury's offline synthetic study and reads the result: which regimes a self-consistency vote can and can't be trusted in. No API key, no spend, runs in seconds.
argument-hint: (optional) extra flags, e.g. --study-questions 200 --seed 7 --max-n 12
allowed-tools: Bash(python3:*)
---

Run the Claude Jury's **synthetic characterization** (CLAUDE.md §G) — a keyless,
offline, deterministic sweep that shows the regimes where a self-consistency vote
does and does not pay off. This spends nothing and needs no API key.

1. Run it (pass through any extra flags in $ARGUMENTS):

   ```bash
   python3 04-user-services/ai-orchestration/jury-claude/jury_claude.py study $ARGUMENTS
   ```

2. Read the table back to me — briefly, not verbatim. For each of the three panels
   say what it shows:
   - **A. Accuracy** — does the vote lift accuracy as per-draw `p` climbs? (should)
   - **B. Correlation** — as `rho` rises, does the jury **collapse** (Δ → 0) while
     `p̂` barely moves? This is the temperature-less-Claude risk made visible.
   - **C. Systematic bias** — below `p=0.5` with errors converging, does the vote
     **hurt** (Δ negative — it entrenches the wrong answer)?

3. One-line takeaway: a vote is only trustworthy where **Δ stays clearly
   positive**. Point out that Panels B and C are exactly why the live tool leans on
   `calibrate` to detect them, rather than assuming the draws are independent.

Do not present this as a measurement of real Claude behavior — it characterizes a
*hypothesized* `p`/`rho`. Measuring the real numbers needs `/form` with a key.
