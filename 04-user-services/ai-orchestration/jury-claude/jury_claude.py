#!/usr/bin/env python3
"""
jury_claude.py — the Jury, driven by Claude instead of Kimi K3.

This is the sibling `jury/`'s thesis made real: "Nothing there is
Fireworks-specific except FireworksSampler; swap the sampler to point anywhere."
So we swap it. Everything load-bearing — the answer extractor, the Dirichlet
posterior stopping rule, the adaptive `deliberate` loop, the `calibrate`
measurement — is imported unchanged from `../jury/jury.py`. This file adds
exactly one thing: `ClaudeSampler`, an empanelled juror backed by the official
Anthropic SDK.

Why this needs its own file (the honest deviation from the doctrine)
--------------------------------------------------------------------
CLAUDE.md §G's mechanism is a *governed-warm temperature*: crank `temperature`
to manufacture decorrelated draws, then clip the tail (`top_p`) and vote. On
current Claude models that mechanism is unavailable — `temperature`, `top_p`,
and `top_k` are REMOVED, and sending any of them returns a 400. So:

  * There is no temperature to raise, and nothing to tail-clip. The "match every
    degree of temperature with a degree of governance" invariant is vacuously
    satisfied: the platform removed the ungoverned knob outright.
  * Variance — the decorrelated draws a vote needs — comes from the sampler's
    native, unseeded stochasticity, amplified by ADAPTIVE THINKING. Adaptive
    thinking is the closest Claude analog to the doctrine's "governed-warm body":
    reasoning that is load-bearing in the answer, derived in the open, exactly
    the faithful-over-detached form §G asks for.
  * Because we can't dial the variance, we MEASURE it. Run `calibrate`: if voted
    accuracy barely beats single-draw accuracy, the draws are too correlated for
    a vote to help on this task — that is the "measure p, don't guess it"
    invariant doing its job on a platform where p is set by the sampler, not a
    slider.

The verdict layer (empanel → tally → Dirichlet stop) is identical to Kimi's,
because a plurality vote over decorrelated draws is model-agnostic.

Run against Claude (key from env or ./.env — never hard-code it):
  export ANTHROPIC_API_KEY=sk-ant-...
  python3 jury_claude.py deliberate \
      --prompt "A bat and ball cost \$1.10. The bat costs \$1 more. Ball? End with 'ANSWER: <n>'." \
      --answer-marker ANSWER: --effort medium

Test the statistics anywhere, no key and no spend (synthetic jurors, stdlib only):
  python3 jury_claude.py deliberate --mock-p 0.7 --prompt x --answer-marker ANSWER:
  python3 jury_claude.py calibrate  --mock-p 0.7 --mock-questions 200 --answer-marker ANSWER:
"""
import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

# Import the whole voter from the sibling Kimi jury — the statistics are the
# model-agnostic part, and duplicating them here would only invite drift.
_JURY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "jury")
sys.path.insert(0, _JURY_DIR)
try:
    from jury import (  # noqa: E402  (import after sys.path juggling, by design)
        make_extractor,
        deliberate,
        calibrate,
        MockSampler,
        load_dotenv,
    )
except ImportError as e:  # pragma: no cover
    raise SystemExit(
        f"Could not import the shared voter from {_JURY_DIR}/jury.py: {e}\n"
        "jury-claude/ reuses ../jury/jury.py — keep the two side by side."
    )

DEFAULT_MODEL = "claude-opus-5"
# Server-side refusal fallback (scalar 'default' mode) rides its own beta header.
_FALLBACK_BETA = "server-side-fallback-2026-07-01"


# --------------------------------------------------------------------------- #
# The sampler — one empanelled Claude juror, called n-at-a-time                #
# --------------------------------------------------------------------------- #
class ClaudeSampler:
    """One juror config, backed by the Anthropic Messages API.

    No temperature/top_p/top_k: current Claude models reject them (400). The
    decorrelation a vote needs comes from native sampling stochasticity plus
    adaptive thinking (`--thinking adaptive`, the default). Depth/cost is the
    `effort` dial. A refusal is recorded as its own honest tally bucket
    ('<refused:CATEGORY>') rather than silently dropped — unless
    `--fallbacks-default` is set, in which case the API re-serves the draw on
    Anthropic's recommended fallback model inside the same call.
    """

    def __init__(self, model=DEFAULT_MODEL, api_key=None, effort="medium",
                 max_tokens=4096, thinking="adaptive", system=None,
                 fallbacks_default=False, max_workers=5, max_retries=4):
        try:
            import anthropic  # lazy — --mock never needs the dependency
        except ImportError:  # pragma: no cover
            raise SystemExit(
                "The 'anthropic' package is required for live runs.\n"
                "  pip install anthropic\n"
                "…or use --mock-p for an offline, keyless run."
            )
        if not api_key and not os.environ.get("ANTHROPIC_API_KEY"):
            raise SystemExit(
                "No API key. Set ANTHROPIC_API_KEY (env or ./.env) or use "
                "--mock-p for an offline run."
            )
        # A bare client also resolves an `ant auth login` profile; only pass a
        # key when one was explicitly supplied.
        self._client = anthropic.Anthropic(api_key=api_key, max_retries=max_retries) \
            if api_key else anthropic.Anthropic(max_retries=max_retries)
        self.model = model
        self.max_tokens = max_tokens
        self.system = system
        self.fallbacks_default = fallbacks_default
        self.max_workers = max_workers

        # Disabling thinking above 'high' effort is a 400 on Claude Opus 5, and
        # thinking-off has known tool-call/tag-leak failure modes — clamp + warn.
        self.thinking = thinking
        self.effort = effort
        if thinking == "off" and effort in ("xhigh", "max"):
            sys.stderr.write(
                f"[jury-claude] thinking off + effort {effort} is rejected on "
                "Claude Opus 5; clamping effort to 'high'.\n"
            )
            self.effort = "high"

    def _request_kwargs(self, prompt):
        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "output_config": {"effort": self.effort},
            "messages": [{"role": "user", "content": prompt}],
        }
        if self.thinking == "adaptive":
            kwargs["thinking"] = {"type": "adaptive"}
        else:
            kwargs["thinking"] = {"type": "disabled"}
        if self.system:
            kwargs["system"] = self.system
        return kwargs

    def _one(self, prompt):
        kwargs = self._request_kwargs(prompt)
        if self.fallbacks_default:
            resp = self._client.beta.messages.create(
                betas=[_FALLBACK_BETA], fallbacks="default", **kwargs
            )
        else:
            resp = self._client.messages.create(**kwargs)

        # A refusal is a real outcome, not an exception — surface it as a bucket.
        if resp.stop_reason == "refusal":
            category = getattr(getattr(resp, "stop_details", None), "category", None)
            return f"<refused:{category}>"

        # Only the visible text is votable; thinking blocks are separate (and
        # empty-text by default on these models anyway).
        return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")

    def sample(self, prompt, n):
        with ThreadPoolExecutor(max_workers=min(n, self.max_workers)) as ex:
            return list(ex.map(lambda _: self._one(prompt), range(n)))


# --------------------------------------------------------------------------- #
# Config plumbing + CLI (mirrors jury.py so muscle memory carries over)        #
# --------------------------------------------------------------------------- #
def build_sampler(args):
    if args.mock_p is not None:
        return MockSampler(p=args.mock_p, gold=args.mock_true,
                           marker=args.answer_marker or "ANSWER:", seed=args.seed,
                           rho=args.mock_rho, systematic=args.mock_systematic)
    load_dotenv(args.env_file)
    return ClaudeSampler(
        model=args.model, api_key=os.environ.get("ANTHROPIC_API_KEY"),
        effort=args.effort, max_tokens=args.max_tokens, thinking=args.thinking,
        system=args.system, fallbacks_default=args.fallbacks_default,
        max_workers=args.max_workers,
    )


# --------------------------------------------------------------------------- #
# study — one turnkey command: sweep the mock across every regime, offline     #
# --------------------------------------------------------------------------- #
def _study(args):
    """Run the whole synthetic characterization in one shot (no key, no spend).

    Three panels, each a stack of `calibrate` runs, cover the regimes that decide
    whether a vote is trustworthy — including the two the naive mock hides:
      A. Accuracy      — vary p, independent + dispersed errors (the happy path).
      B. Correlation   — fix p, raise rho until the jury collapses to one opinion.
      C. Systematic    — push p below 0.5 with errors converging on one answer.
    """
    marker = args.answer_marker or "ANSWER:"
    extractor = make_extractor(marker)
    dataset = [{"prompt": f"q{i}", "answer": args.mock_true}
               for i in range(args.study_questions)]

    def cell(p, rho, systematic):
        s = MockSampler(p=p, gold=args.mock_true, marker=marker, seed=args.seed,
                        rho=rho, systematic=systematic)
        r = calibrate(s, dataset, extractor, samples_per_q=args.samples_per_q,
                      target=args.target, min_n=args.min_n, max_n=args.max_n,
                      batch=args.batch, confidence=args.confidence,
                      prior=args.prior, draws=args.draws)
        return r["p_hat_single_sample"], r["accuracy_adaptive_vote"], r["adaptive_jury_size_avg"]

    def row(label, p, rho, systematic):
        ph, vt, jn = cell(p, rho, systematic)
        lift = vt - ph
        read = "vote pays off" if lift > 0.05 else \
               "vote adds ~nothing" if lift > -0.02 else "vote HURTS (entrenches)"
        print(f"  {label:<14}  p̂={ph:<6}  voted={vt:<6}  Δ={lift:+.2f}  "
              f"avg-jury={jn:<5}  {read}")

    print(f"\n  The Jury — synthetic characterization  "
          f"({args.study_questions} questions · ≤{args.max_n} jurors · seed {args.seed})")
    print("  Marginal accuracy p̂ should barely move within a panel; watch the vote (Δ).\n")

    print("  A. ACCURACY  (independent draws, dispersed errors — the happy path)")
    for p in (0.90, 0.75, 0.60, 0.45):
        row(f"p={p:.2f}", p, 0.0, False)

    print("\n  B. CORRELATION  (p=0.70, dispersed — raise rho; watch the jury collapse)")
    for rho in (0.0, 0.3, 0.6, 0.9):
        row(f"rho={rho:.1f}", 0.70, rho, False)

    print("\n  C. SYSTEMATIC BIAS  (errors converge on one answer — vote entrenches it)")
    for p in (0.55, 0.45, 0.35):
        row(f"p={p:.2f}", p, 0.0, True)

    print("\n  Takeaway: a vote is only trustworthy in regimes where Δ stays clearly")
    print("  positive. Panels B and C are the ones a temperature-less Claude jury can")
    print("  fall into — which is why the live tool leans on `calibrate` to detect them.\n")


def _add_sampling_args(p):
    p.add_argument("--model", default=DEFAULT_MODEL,
                   help="Claude model id (default: claude-opus-5).")
    p.add_argument("--effort", default="medium",
                   choices=["low", "medium", "high", "xhigh", "max"],
                   help="output_config.effort — the depth/cost dial (no temperature exists).")
    p.add_argument("--thinking", default="adaptive", choices=["adaptive", "off"],
                   help="Adaptive thinking is the doctrine's governed-warm body; keep it on.")
    p.add_argument("--max-tokens", type=int, default=4096,
                   help="Caps thinking + answer together; give headroom when thinking is on.")
    p.add_argument("--max-workers", type=int, default=5,
                   help="Concurrent jurors per batch (Claude calls are pricier than Kimi's).")
    p.add_argument("--system", default=None, help="Optional system prompt.")
    p.add_argument("--fallbacks-default", action="store_true",
                   help="Re-serve a refused draw on Anthropic's recommended fallback model.")
    p.add_argument("--answer-marker", default=None,
                   help="Line prefix carrying the final answer, e.g. 'ANSWER:'.")
    p.add_argument("--env-file", default=".env")
    p.add_argument("--seed", type=int, default=None, help="Mock RNG seed only.")
    p.add_argument("--mock-p", type=float, default=None,
                   help="Offline: synthetic per-sample accuracy (no API, no spend).")
    p.add_argument("--mock-true", default="0.05", help="Mock gold answer.")
    p.add_argument("--mock-rho", type=float, default=0.0,
                   help="Offline: inter-juror correlation 0..1 (higher = draws collapse to one).")
    p.add_argument("--mock-systematic", action="store_true",
                   help="Offline: errors converge on ONE wrong answer (models systematic bias).")


def _add_jury_args(p):
    p.add_argument("--min-n", type=int, default=3)
    p.add_argument("--max-n", type=int, default=12,
                   help="Cap on jurors (lower than Kimi's default — Claude draws cost more).")
    p.add_argument("--batch", type=int, default=3,
                   help="Jurors empanelled concurrently per round.")
    p.add_argument("--confidence", type=float, default=0.95,
                   help="Posterior P(leader is plurality winner) needed to stop.")
    p.add_argument("--prior", type=float, default=1.0, help="Dirichlet prior strength.")
    p.add_argument("--draws", type=int, default=2000, help="Posterior Monte-Carlo draws.")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="The Jury (Claude backend) — adaptive sequential self-consistency.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    # Gym-schema aliases so the CLI subcommand matches the slash command that
    # calls it (/strength → strength, /form → form, /diet → diet). The canonical
    # verbs stay the primary names — self-documenting, and nothing that already
    # says deliberate/calibrate/study breaks.
    d = sub.add_parser("deliberate", aliases=["strength"],
                       help="Answer one prompt with an adaptive jury (alias: strength).")
    src = d.add_mutually_exclusive_group(required=True)
    src.add_argument("--prompt")
    src.add_argument("--prompt-file")
    _add_sampling_args(d)
    _add_jury_args(d)
    d.add_argument("--json", action="store_true", help="Emit the full verdict as JSON.")

    c = sub.add_parser("calibrate", aliases=["form"],
                       help="Measure p-hat and the vote's real payoff (alias: form).")
    c.add_argument("--dataset", help="JSONL of {\"prompt\":..., \"answer\":...}.")
    c.add_argument("--samples-per-q", type=int, default=12)
    c.add_argument("--target", type=float, default=0.90,
                   help="Target reliability for the fixed-N recommendation.")
    c.add_argument("--mock-questions", type=int, default=0,
                   help="Offline: synthesise this many questions (needs --mock-p).")
    _add_sampling_args(c)
    _add_jury_args(c)

    s = sub.add_parser("study", aliases=["diet"],
                       help="Turnkey offline sweep across every regime — no key, no spend (alias: diet).")
    s.add_argument("--study-questions", type=int, default=120,
                   help="Synthetic questions per calibrate cell.")
    s.add_argument("--samples-per-q", type=int, default=12)
    s.add_argument("--target", type=float, default=0.90)
    s.add_argument("--answer-marker", default="ANSWER:")
    s.add_argument("--mock-true", default="0.05")
    s.add_argument("--seed", type=int, default=7)
    _add_jury_args(s)

    args = ap.parse_args(argv)
    # argparse records the alias the user typed; map it back to the canonical verb.
    cmd = {"strength": "deliberate", "form": "calibrate", "diet": "study"}.get(
        args.cmd, args.cmd)
    if cmd == "study":
        _study(args)
        return
    extractor = make_extractor(args.answer_marker)
    sampler = build_sampler(args)

    if cmd == "deliberate":
        prompt = args.prompt if args.prompt else open(args.prompt_file).read()
        verdict = deliberate(sampler, prompt, extractor, min_n=args.min_n,
                             max_n=args.max_n, batch=args.batch,
                             confidence=args.confidence, prior=args.prior, draws=args.draws)
        if args.json:
            print(json.dumps(verdict, indent=2))
        else:
            print(f"\n  VERDICT: {verdict['answer']}")
            print(f"  confidence {verdict['confidence']}  ·  {verdict['lead']} jurors  "
                  f"·  stopped: {verdict['stopped']}")
            print("  tally:")
            for row in verdict["tally"]:
                print(f"    {row['votes']:>3}  {row['answer']}")
        return

    if cmd == "calibrate":
        if args.dataset:
            dataset = [json.loads(l) for l in open(args.dataset) if l.strip()]
        elif args.mock_questions and args.mock_p is not None:
            dataset = [{"prompt": f"q{i}", "answer": args.mock_true}
                       for i in range(args.mock_questions)]
        else:
            raise SystemExit("calibrate needs --dataset, or --mock-questions with --mock-p.")
        print(json.dumps(calibrate(sampler, dataset, extractor,
                                    samples_per_q=args.samples_per_q, target=args.target,
                                    min_n=args.min_n, max_n=args.max_n, batch=args.batch,
                                    confidence=args.confidence, prior=args.prior,
                                    draws=args.draws), indent=2))
        return


if __name__ == "__main__":
    main()
