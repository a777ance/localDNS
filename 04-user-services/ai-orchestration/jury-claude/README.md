# The Jury — Claude backend

The [Kimi K3 Jury](../jury/) with its sampler swapped for Claude. Same verdict
layer, same adaptive stopping rule, same `calibrate` — it *imports* all of that
from `../jury/jury.py` unchanged. The only new code here is `ClaudeSampler`,
which empanels a juror over the official Anthropic Messages API.

> **Why a separate tool, not a `--backend claude` flag on the original?** Because
> the doctrine's *mechanism* differs on Claude, and that difference is worth
> stating in one honest place rather than hiding behind a flag. See
> [The temperature deviation](#the-temperature-deviation).

---

## Contents

Walkthrough blocks are ordered newest-stage-first per house style; **stage
numbers are fixed**, so the run order is always readable from the numbers (do
Stage 1 first).

- [Stage 3 — Deliberate: answer one prompt](#stage-3--deliberate-answer-one-prompt)
- [Stage 2 — Calibrate: measure your real `p`](#stage-2--calibrate-measure-your-real-p)
- [Stage 1 — Configure](#stage-1--configure)
- [One command — characterize the jury (`study`)](#one-command--characterize-the-jury-study)
- [The temperature deviation](#the-temperature-deviation)
- [Doctrine mapping (§G → Claude)](#doctrine-mapping-g--claude)
- [Files](#files)

---

## Stage 3 — Deliberate: answer one prompt

Empanel jurors in concurrent batches (`--batch`), tally their extracted answers,
and stop the moment the Dirichlet posterior says the leader is the true plurality
winner with `--confidence` probability. Easy prompts settle at `--min-n`; split
ones run to `--max-n`.

```bash
python3 jury_claude.py deliberate \
  --prompt "A bat and ball cost \$1.10; the bat is \$1 more. Ball? End with 'ANSWER: <n>'." \
  --answer-marker ANSWER: \
  --effort medium --min-n 3 --max-n 12 --batch 3 --confidence 0.95
```

```
  VERDICT: 0.05
  confidence 0.9962  ·  5/5 jurors  ·  stopped: confident
  tally:
      5  0.05
```

`--json` emits the full verdict (tally + every juror's raw text). A juror that is
**refused** by the safety classifiers shows up as its own honest tally bucket,
`<refused:CATEGORY>`, rather than being silently dropped — or pass
`--fallbacks-default` to have the API re-serve that draw on Anthropic's
recommended fallback model inside the same call.

## Stage 2 — Calibrate: measure your real `p`

On Claude you can't *set* the draw variance (there is no temperature — see below),
so you **measure** it. Against a labelled JSONL (`{"prompt":..., "answer":...}`
per line), `calibrate` reports `p̂` (per-sample accuracy), single-shot vs. voted
accuracy, and the jury size the adaptive rule spends.

```bash
python3 jury_claude.py calibrate \
  --dataset ../jury/datasets/example.jsonl \
  --answer-marker ANSWER: --samples-per-q 12 --effort medium --target 0.90
```

Read `verdict` first. The key Claude-specific read: **if `accuracy_adaptive_vote`
barely beats `p_hat_single_sample`, the draws are too correlated for a vote to
help on this task.** That is not a bug — it is the "measure `p`, don't guess it"
invariant catching a platform where the sampler, not a slider, sets the variance.
When it happens, the lever is a different prompt or a higher `--effort` (more
independent reasoning paths), not a temperature you don't have.

## Stage 1 — Configure

1. Copy the env template and drop in your key (never commit the real one):
   ```bash
   cp .env.example .env
   # edit .env: ANTHROPIC_API_KEY=sk-ant-...
   ```
   A bare `Anthropic()` client also resolves an `ant auth login` profile, so the
   key is optional if you authenticate that way.
2. For live runs you need the SDK; the offline mock does not:
   ```bash
   pip install anthropic      # live runs only
   ```
3. Confirm the statistics with zero key, zero spend, zero dependency — synthetic
   jurors, standard library only (the mock path never imports `anthropic`):
   ```bash
   python3 jury_claude.py deliberate --prompt x --mock-p 0.7 --answer-marker ANSWER:
   python3 jury_claude.py calibrate  --mock-p 0.7 --mock-questions 200 --answer-marker ANSWER:
   ```

---

## One command — characterize the jury (`study`)

`calibrate` measures one config. **`study`** runs the whole characterization in a
single, keyless, foreground command — three panels of `calibrate` cells that walk
the jury across every regime, including the two that a naive i.i.d. mock hides and
that a temperature-less Claude jury can actually fall into:

```bash
python3 jury_claude.py study        # ~seconds, stdlib only, no key, no spend
```

```
  A. ACCURACY  (independent draws, dispersed errors — the happy path)
  p=0.90          p̂=0.8938  voted=1.0     Δ=+0.11  avg-jury=7.58   vote pays off
  p=0.45          p̂=0.4542  voted=0.9     Δ=+0.45  avg-jury=11.65  vote pays off
  B. CORRELATION  (p=0.70, dispersed — raise rho; watch the jury collapse)
  rho=0.0         p̂=0.6917  voted=1.0     Δ=+0.31  avg-jury=10.05  vote pays off
  rho=0.9         p̂=0.6896  voted=0.6833  Δ=-0.01  avg-jury=7.0    vote adds ~nothing
  C. SYSTEMATIC BIAS  (errors converge on one answer — vote entrenches it)
  p=0.45          p̂=0.4528  voted=0.4167  Δ=-0.04  avg-jury=11.7   vote HURTS (entrenches)
```

The reads come from two `MockSampler` levers (also usable standalone on any
`deliberate`/`calibrate` run, here and in `../jury/`):

| Lever | Models | Why it matters here |
| ----- | ------ | ------------------- |
| `--mock-rho 0..1` | inter-juror **correlation** — a fraction of jurors copy one shared draw | the temperature-less risk made visible: **per-draw accuracy stays ~`p`, but the vote stops helping** as `rho` rises (the jury collapses to one) |
| `--mock-systematic` | errors **converge on one wrong answer** instead of scattering | below `p=0.5` the vote *entrenches* the wrong answer — the failure the dispersed default can't show |

`study` is the **wrapper** you asked for, and it is exactly what a detached run
fires — same command, no extra implementation:

```bash
# fire-and-forget, capture the report
nohup python3 jury_claude.py study > jury-study-$(date +%F).txt 2>&1 &
```

Because the whole study is offline and deterministic (fixed `--seed`), the
foreground and detached forms are interchangeable — schedule it (cron / a
Routine) and it delivers the same table unattended.

## The temperature deviation

CLAUDE.md §G is built on a **governed-warm temperature**: raise `temperature` to
manufacture decorrelated draws, pair every degree of it with a tail-clip
(`top_p`) so it can't sample garbage, then let a vote select quality out of the
diversity.

**Current Claude models (`claude-opus-5`, `claude-opus-4-8`, `claude-fable-5`,
`claude-sonnet-5`) remove `temperature`, `top_p`, and `top_k` entirely — sending
any of them returns a 400.** So the §G mechanism cannot be expressed here, and
this tool deviates from the doctrine's default *with a stated reason* (exactly
what §3 permits):

- **No temperature to raise, no tail to clip.** The "match every degree of
  temperature with a degree of governance" invariant is satisfied vacuously — the
  platform removed the ungoverned knob for us.
- **Variance comes from the sampler, amplified by adaptive thinking.** Repeated
  identical requests are not deterministic, and adaptive thinking sends each
  juror down a different reasoning path. That is where the decorrelation a vote
  needs comes from.
- **You measure the variance instead of dialing it.** `calibrate` is now the
  primary control surface, not an afterthought: it tells you whether the draws
  are independent enough for the vote to pay off on *your* task.

The verdict layer is untouched — a plurality vote over decorrelated draws is
model-agnostic, which is the whole reason it is imported, not re-implemented.

## Doctrine mapping (§G → Claude)

| §G stage | Kimi K3 (`../jury/`) | Claude (`jury_claude.py`) |
| -------- | -------------------- | ------------------------- |
| **Lazy anchor** | `reasoning effort: low` — cheap honest first token | Inherent: the first token is a reflex; there is no temperature to pre-commit a trajectory |
| **Governed-warm body** | `temp 1.1 / top_p 0.9 / top_k 40`, penalties 0 | **Adaptive thinking** — load-bearing reasoning derived in the open (§G's *preferred* form over a detached thinking dump); depth via `--effort` |
| **Concurrent vote** | Dirichlet-posterior adaptive stop | *Identical* — imported from `../jury/jury.py` |
| **Governance invariant** | tail-clip + selector | platform removed the knob; selector (the vote) remains |
| **Measure `p`, don't guess** | `calibrate` confirms the config | `calibrate` is the *only* variance control — measure or don't vote |

## Files

| File | Purpose |
| ---- | ------- |
| `jury_claude.py` | `ClaudeSampler` + CLI; imports the voter/extractor/calibrator from `../jury/jury.py` |
| `.env.example` | `ANTHROPIC_API_KEY=CHANGE_ME` template → copy to `.env` |

Reuses `../jury/datasets/example.jsonl` for `calibrate` — no separate dataset.
