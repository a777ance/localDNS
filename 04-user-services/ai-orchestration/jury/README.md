# The Jury — adaptive sequential self-consistency

One tuned sampling config, empanelled as many times as the question *needs*, then
voted to a statistically decisive verdict. Built for Fireworks / Kimi K3 but the
endpoint is the plain OpenAI-compatible chat API — repoint `FireworksSampler` at
anything.

The design follows the sampling philosophy worked out for this stack: a **lazy
anchor** (low reasoning effort — cheap, honest first pass) with a **governed-warm
body** (`temperature 1.1`, `top_p 0.9`, `top_k 40` — diverse but coherent draws).
A single draw at that setting is a good, honest guess. The Jury is the layer that
turns a stack of those guesses into a *reliable* answer — and, crucially, spends
only as many draws as the question actually demands.

> **What it's for.** Tasks with an extractable, discrete final answer (math,
> classification, a factual value). That is exactly where self-consistency earns
> its keep. Free-form prose needs a marker or a clusterer — see
> [Free-form answers](#free-form-answers).

---

## Contents

Walkthrough blocks are ordered newest-stage-first per house style; **stage numbers
are fixed**, so the intended run order is always readable from the numbers (do
Stage 1 first).

- [Stage 3 — Deliberate: answer one prompt](#stage-3--deliberate-answer-one-prompt)
- [Stage 2 — Calibrate: measure your real `p`](#stage-2--calibrate-measure-your-real-p)
- [Stage 1 — Configure](#stage-1--configure)
- [How the stopping rule works](#how-the-stopping-rule-works)
- [Free-form answers](#free-form-answers)
- [Design decisions](#design-decisions)
- [Files](#files)

---

## Stage 3 — Deliberate: answer one prompt

Empanel jurors in concurrent batches (`--batch`), tally their extracted answers,
and stop the moment a Dirichlet posterior says the leader is the true plurality
winner with `--confidence` probability. Easy prompts settle at `--min-n`; split
ones run to `--max-n`.

```bash
python3 jury.py deliberate \
  --prompt "A bat and ball cost \$1.10; the bat is \$1 more. Ball? End with 'ANSWER: <n>'." \
  --answer-marker ANSWER: \
  --temperature 1.1 --top-p 0.9 --top-k 40 \
  --min-n 3 --max-n 40 --batch 3 --confidence 0.95
```

```
  VERDICT: 0.05
  confidence 0.9955  ·  6/6 jurors  ·  stopped: confident
  tally:
      6  0.05
```

Add `--json` for the full verdict (tally + every juror's raw text) to pipe onward.

## Stage 2 — Calibrate: measure your real `p`

Don't guess the jury size — measure the per-sample accuracy it depends on. Against
a labelled JSONL (`{"prompt":..., "answer":...}` per line), `calibrate` reports
`p̂`, single-shot vs. voted accuracy, the average jury the adaptive rule spends,
and a conservative fixed-N figure.

```bash
python3 jury.py calibrate \
  --dataset datasets/example.jsonl \
  --answer-marker ANSWER: --samples-per-q 21 --target 0.90
```

Read `verdict` first — it is driven by what was **measured**, not by a textbook
threshold, so it correctly separates the two sub-`0.5` regimes (dispersed error →
voting still works; systematic bias → voting entrenches the wrong answer).

## Stage 1 — Configure

1. Copy the env template and drop in your key (never commit the real one):
   ```bash
   cp .env.example .env
   # edit .env: FIREWORKS_API_KEY=fw_...
   ```
2. Confirm the statistics with zero key and zero spend — synthetic jurors:
   ```bash
   python3 jury.py deliberate --prompt x --mock-p 0.7 --answer-marker ANSWER:
   python3 jury.py calibrate  --mock-p 0.7 --mock-questions 200 --answer-marker ANSWER:
   ```
   `--mock-p` sets a synthetic per-sample accuracy so the voter and calibration
   can be exercised offline. Everything runs on the Python 3 standard library — no
   `pip install`.

---

## How the stopping rule works

Votes are multinomial. After each round we hold a **Dirichlet(prior + counts)**
posterior over the answer probabilities, plus one extra *unseen* pseudo-category
(mass = `--prior`) so an early unanimous run isn't mistaken for certainty — the
true modal answer might still be one no juror has voiced. We Monte-Carlo that
posterior (`--draws`) and stop when `P(leader is the argmax) ≥ --confidence`,
bounded by `--min-n` and `--max-n`.

**Two guarantees worth knowing:**

- **Break-even.** Voting helps only when the correct answer is already *modal*.
  Above break-even accuracy climbs toward a ceiling with more jurors; below it,
  voting **amplifies** whatever is most common. For open-ended answers break-even
  sits *below* 0.5 because wrong answers disperse — which is why `calibrate`
  reports **measured** vote accuracy as the source of truth and flags the binary
  fixed-N figure as merely a conservative bound.
- **Independence.** The math assumes decorrelated jurors. Too-cold sampling makes
  draws near-identical, collapsing the effective jury to one. The governed-warm
  config is what buys the independence that makes N votes worth ~N — and because
  jurors still share the model's biases, the vote asymptotes at the model's
  *systematic* accuracy, never at 1.0.

Fixed-N planning figures (binary approximation, target 0.90):

| Per-sample `p` | Jurors for ~90% | Note |
| -------------- | --------------- | ---- |
| 0.9 | 3 | trivial |
| 0.8 | 3–5 | sweet spot |
| 0.7 | 9–11 | workable |
| 0.6 | ~40+ | weak — improve the sampler first |
| ≤ 0.5 | — | don't vote (unless errors disperse; measure it) |

The adaptive rule beats any fixed N by spending the small counts on easy prompts
and saving the large ones for genuinely split prompts.

## Free-form answers

Exact-match voting needs a canonical answer. Two ways to get one:

1. **Marker (recommended).** Instruct the model to end with `ANSWER: <x>` and pass
   `--answer-marker ANSWER:`. Best for discrete final answers.
2. **Clusterer.** For prose, replace `make_extractor` with an embedding-based
   clusterer so semantically equal answers share a bucket. Not shipped — the
   default falls back to the normalized last line, which only clusters when
   phrasing is near-identical.

## Design decisions

- **2026-08-01 — Verdict follows the measurement, not the threshold.** Early
  calibrate output said "don't vote" whenever `p ≤ 0.5`, contradicting its own
  measured vote accuracy on dispersed-error tasks. `_verdict` now reads the
  measured lift, so it distinguishes dispersed error (vote works) from systematic
  bias (vote fails) — the binary `recommended_fixed_n_binary` is kept only as a
  labelled conservative bound.
- **2026-08-01 — Dirichlet posterior over a fixed lead margin.** A Monte-Carlo
  posterior handles the multi-way open-ended case directly and yields an
  interpretable stop signal (`P(leader is plurality winner)`), where a simple
  "leader is k votes ahead" rule does not.
- **2026-08-01 — Standard library only.** Matches the `collect/` tools' ethos so
  the Jury runs on the t630 with no environment to build.

## Files

| File | Purpose |
| ---- | ------- |
| `jury.py` | Sampler, extractor, Dirichlet voter, adaptive loop, calibrator, CLI |
| `datasets/example.jsonl` | Five marked-answer reasoning prompts for `calibrate` |
| `.env.example` | `FIREWORKS_API_KEY=CHANGE_ME` template → copy to `.env` |

## References

- CLAUDE.md [§G — LLM sampling doctrine](../../../CLAUDE.md#g-llm-sampling-doctrine--the-jury) — the doctrine this tool implements.
- [Self-Consistency Improves Chain-of-Thought Reasoning in Language Models](https://arxiv.org/abs/2203.11171) — Wang et al., 2022. The method this tool operationalizes: sample diverse reasoning paths, return the plurality answer.
- [The Claude-backend Jury](../jury-claude/) — same voter, swapped sampler, for a temperature-less platform.
