---
description: Your CARDIO (bodybuilding schema) — quick, keyless conditioning. Empanels a concurrent in-harness jury on a question and returns a plurality verdict (CLAUDE.md §G). For the heavy loaded lift on measurable/repeatable tasks, use /strength (jury-claude) for statistically-governed stopping.
argument-hint: <a question with an extractable, discrete answer — end it with the answer type you want>
allowed-tools: Task, Bash(python3:*)
---

Run the stack's sampling doctrine (CLAUDE.md §G) **inside this harness**: don't
consume a single warm draw where a verdict matters — empanel a jury, then let a
plurality vote outvote the idiosyncratic draws.

**Question to deliberate:** $ARGUMENTS

## First: is this the right tool?

- **One-off judgment call** (a design decision, "which of these is the bug", a
  factual call you need *now*) → empanel the in-harness jury below.
- **Measurable or repeatable task** (you have or can build a labelled set, or
  you'll ask this shape of question often) → don't hand-roll it here. Use
  `04-user-services/ai-orchestration/jury-claude/` instead, and **`calibrate`
  first** so the jury size is measured, not guessed:
  ```bash
  python3 04-user-services/ai-orchestration/jury-claude/jury_claude.py form \
    --dataset <your.jsonl> --answer-marker ANSWER: --samples-per-q 12
  ```
  Its Dirichlet stopping rule and honest verdict beat the fixed fan-out below.
  Come back here only for the un-repeatable calls.

## Empanel the jury (concurrent vote)

1. **Empanel 5 jurors at once, each with a different framing.** In a **single
   message**, spawn 5 concurrent `juror` subagents (Task tool,
   `subagent_type: "juror"`), each handed the **same question** ($ARGUMENTS) but a
   **different answer-preserving framing directive**, so the draws decorrelate *by
   construction* rather than by luck — the temperature-less analog of §G's
   governed-warm body (identical prompts to a locked-decoding model collapse into
   one reasoning path). Juror 1 gets no directive (plain); jurors 2–5 get one each:
   - *skeptic* — work one step at a time; before accepting each step, ask how it could be wrong.
   - *restate* — restate the question and list what's given vs. asked; derive from those facts only.
   - *cross-check* — solve, then reach the answer a second way (estimate / work backwards) and reconcile.
   - *avoid-the-trap* — name the most tempting wrong approach first, then deliberately avoid it.

   The framing changes the *approach*, never the question or the answer. Ask each
   to end with a canonical `ANSWER:` line.

2. **Tally.** Collect each juror's `ANSWER:` line, normalize (lowercase, strip
   surrounding punctuation/whitespace), and count. The **plurality** is the
   working verdict.

3. **Adaptive top-up (bounded).** Judge the agreement:
   - **Decisive** (≥ 4 of 5 agree) → stop; report the verdict.
   - **Split** (a 3–2, or a 2–2–1 with no majority) → empanel **4 more** jurors in
     one message (keep varying their framings — add *first-principles* and reuse
     the list — so the extra jurors stay decorrelated too), re-tally over all 9,
     and stop. Do **not** go past 9 — a jury that won't converge by 9 is telling
     you the question is genuinely contested or under-specified, which is itself
     the finding.

4. **Report**, briefly:
   - the **verdict** (the plurality answer),
   - the **tally** (each distinct answer and its vote count), and
   - a one-line **confidence read**: unanimous / strong majority / split — and if
     split, say so plainly rather than dressing a coin-flip as a verdict.

Never present a single juror's draw as the answer, and never average by vibes —
the vote is the governor (§G). If the jurors mostly agree *and are mostly wrong*,
that's systematic model bias the vote can't fix; flag it if you suspect it.
