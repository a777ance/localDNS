---
description: Your FORM check (bodybuilding schema) — is the movement actually productive? Measures the Jury's real per-sample accuracy p̂ and whether voting beats a single draw on a labelled set (CLAUDE.md §G — "measure p, don't guess it"). Real Claude API (needs ANTHROPIC_API_KEY) unless run in --mock mode.
argument-hint: (optional) path to a labelled JSONL of {"prompt":…, "answer":…}; defaults to the bundled example set
allowed-tools: Bash(python3:*)
---

Measure — don't guess — the numbers the Jury's stopping rule depends on (§G).
Against a labelled set, report per-sample accuracy `p̂`, single-shot vs. voted
accuracy, and the jury size the adaptive rule spends.

**Dataset:** $ARGUMENTS  *(if empty, use the bundled
`04-user-services/ai-orchestration/jury/datasets/example.jsonl`)*

1. **Pick the dataset.** Use the path in $ARGUMENTS if given; otherwise the
   bundled example set above.

2. **Key check.** If neither `ANTHROPIC_API_KEY` is set nor
   `04-user-services/ai-orchestration/jury-claude/.env` exists, don't run live —
   tell me there's no key, and offer to run a **keyless synthetic** calibration
   instead so I can still see the machinery:

   ```bash
   python3 04-user-services/ai-orchestration/jury-claude/jury_claude.py form \
     --mock-p 0.7 --mock-questions 120 --answer-marker ANSWER: --samples-per-q 12
   ```
   (mention that a keyless run measures a *hypothesized* p, not real Claude — and
   that `--mock-rho` / `--mock-systematic` or `/diet` explore the failure modes.)

3. **Run live** if a key is present:

   ```bash
   python3 04-user-services/ai-orchestration/jury-claude/jury_claude.py form \
     --dataset <DATASET> --answer-marker ANSWER: --samples-per-q 12 --effort medium
   ```

4. **Read `verdict` first**, then the key §G-on-Claude check: if
   `accuracy_adaptive_vote` barely beats `p_hat_single_sample`, the draws are too
   **correlated** for a vote to help on this task — the "measure p, don't guess"
   invariant catching a platform where the sampler, not a temperature slider, sets
   the variance. When that happens the lever is a better prompt or higher
   `--effort`, not a temperature you don't have. Report the numbers and that read.
