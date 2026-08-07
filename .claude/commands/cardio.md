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

   **Never supply the candidate answers.** Handing the panel an option set makes
   the draws matchable the cheap way — and a shared option set is a *shared prior*
   that correlates them by construction, inflating agreement (§G). Matchability is
   step 2's job, not the question's. If the question genuinely has a closed answer
   set (yes/no, "which of these three files", a multiple-choice item), the set is
   part of the question — use it, and **say in the report that you did**. If it
   does not, ask each juror to **coin its own** answer or label. Never reuse a
   previous run's option set to make tallies "comparable": that is the same
   correlation with a second run's authority behind it.

2. **Tally.** Collect each juror's `ANSWER:` line, normalize (lowercase, strip
   surrounding punctuation/whitespace), and count. The **plurality** is the
   working verdict. Normalizing free-form answers is a **judgment call you make
   after seeing them** — so print the raw strings alongside the merged tally and
   show which you merged. Post-hoc normalization you disclose is the honest way to
   get exact-match voting; a pre-supplied menu is not.

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
   - the **tally** (each distinct answer and its vote count, raw before merged),
   - a one-line **agreement read**: unanimous / strong majority / split — and if
     split, say so plainly rather than dressing a coin-flip as a verdict, and
   - a one-line **bound** — mandatory, see below.

**Agreement is not confidence, and unanimity is not the top of the scale.** A
near-unanimous tally is exactly what a **collapsed** jury produces: `/diet` shows
that as draws correlate (`rho` → 0.9) the vote's lift decays to **Δ=+0.00** while
`p̂` sits unmoved. Correlated jurors agree *because* they're correlated. This run is
keyless, so `p̂` is **unmeasured** and you cannot tell a strong panel from a
collapsed one — say that, in one line, every time:

> Unanimity here is unpriced: with no measured `p̂` I can't separate a strong panel
> from a collapsed one. Measuring it needs `/form` on a labelled set with a key.

Report what the run **does not** certify as plainly as what it does — a keyless
plurality certifies that the elicitation converged, not that the answer is right.
Never present a single juror's draw as the answer, and never average by vibes —
the vote is the governor (§G). If the jurors mostly agree *and are mostly wrong*,
that's systematic model bias the vote can't fix; assume it is *possible* rather
than waiting to suspect it (`/diet` panel C shows the vote actively entrenching a
wrong answer below `p=0.5`).
