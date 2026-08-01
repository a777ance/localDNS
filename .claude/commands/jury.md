---
description: Empanel the statistical Claude Jury on a question and return a Dirichlet-stopped plurality verdict (CLAUDE.md §G). Uses the real Claude API (needs ANTHROPIC_API_KEY, so it spends). For a keyless in-harness vote, use /deliberate instead.
argument-hint: <a question with an extractable, discrete answer — say the answer type>
allowed-tools: Bash(python3:*)
---

Answer this question with the statistical Jury tool — sample decorrelated draws,
extract each `ANSWER:`, and stop the moment the Dirichlet posterior says the
leader is the true plurality winner (§G). **This calls the real Claude API and
costs tokens.**

**Question:** $ARGUMENTS

1. **Check for a key first.** If neither `ANTHROPIC_API_KEY` is set nor
   `04-user-services/ai-orchestration/jury-claude/.env` exists, stop and tell me:
   there's no key, so this would fail — offer `/deliberate` instead (the keyless
   in-harness jury), and don't run anything.

   ```bash
   test -n "$ANTHROPIC_API_KEY" || test -f 04-user-services/ai-orchestration/jury-claude/.env && echo "key present" || echo "no key"
   ```

2. **Run the jury** only if a key is present. Ensure the prompt ends with a
   canonical answer instruction (append `End with 'ANSWER: <x>'.` if the question
   doesn't already pin the final-answer form):

   ```bash
   python3 04-user-services/ai-orchestration/jury-claude/jury_claude.py deliberate \
     --prompt "$ARGUMENTS  End with 'ANSWER: <x>'." \
     --answer-marker ANSWER: --effort medium --min-n 3 --max-n 12 --batch 3
   ```

3. **Report** the verdict, the tally, the confidence, and whether it stopped
   *confident* or *hit max-n*. If it hit max-n or the tally is split, say so
   plainly — a jury that won't converge is telling you the question is genuinely
   contested, and that is the finding. Never dress a split as a clean verdict.

Notes: bump `--effort high`/`--max-n` for harder questions (more cost). If the
jurors mostly agree *and* are mostly wrong, that's systematic model bias the vote
can't fix — flag it if you suspect it (and see `/study` for what that looks like).
