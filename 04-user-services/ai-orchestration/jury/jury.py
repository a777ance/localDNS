#!/usr/bin/env python3
"""
jury.py — adaptive sequential self-consistency for Fireworks / Kimi K3.

The Jury turns ONE tuned sampling config (a "lazy anchor, governed-warm body":
low reasoning effort + temperature/top-p chosen for diverse-but-coherent draws)
into a reliable verdict by empanelling several jurors and voting — but only as
many jurors as the question actually needs.

Two modes:

  deliberate  Answer one prompt. Empanel jurors in small concurrent batches,
              tally their (extracted) answers, and STOP as soon as a Dirichlet
              posterior says the current leader is the true plurality winner
              with >= --confidence probability. Easy prompts settle at the
              --min-n floor; genuinely split ones run to the --max-n cap.

  calibrate   Measure the numbers the stopping rule assumes. Against a labelled
              set, report per-sample accuracy p-hat, single-shot vs. majority
              vote accuracy, the average jury size the adaptive rule spends,
              and the N a fixed vote would need for a target reliability.

Nothing here is Fireworks-specific except FireworksSampler; the endpoint is the
plain OpenAI-compatible chat-completions API. Swap the sampler to point anywhere.

Run against the live model (key from env or ./.env — never hard-code it):
  export FIREWORKS_API_KEY=fw_...
  python3 jury.py deliberate \
      --prompt "A bat and ball cost \$1.10. The bat costs \$1 more. Ball? End with 'ANSWER: <n>'." \
      --temperature 1.1 --top-p 0.9 --top-k 40 --answer-marker ANSWER:

Test the statistics anywhere, no key and no spend (synthetic jurors):
  python3 jury.py deliberate --mock-true 0.05 --mock-p 0.7 --prompt x
  python3 jury.py calibrate  --mock-p 0.7 --mock-questions 200
"""
import argparse
import json
import os
import random
import re
import sys
import urllib.request
import urllib.error
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from math import comb

DEFAULT_BASE_URL = "https://api.fireworks.ai/inference/v1"
DEFAULT_MODEL = "accounts/fireworks/models/kimi-k3"


# --------------------------------------------------------------------------- #
# Answer extraction — voting is meaningless until free-form text is canonical  #
# --------------------------------------------------------------------------- #
def normalize(text):
    """Lowercase, drop surrounding punctuation/space, collapse inner whitespace."""
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip(" \t\n\r.,;:!?\"'`")


def make_extractor(marker=None):
    """Return fn(text)->canonical answer.

    With a marker (e.g. 'ANSWER:') the model is expected to end with
    'ANSWER: <x>'; we take the last such line — the crisp, discrete final
    answer that self-consistency is designed for. Without a marker we fall
    back to the last non-empty line, then to the whole reply. Free-form prose
    won't cluster on exact match — give it a marker, or plug in an embedding
    clusterer here (see README, "Free-form answers").
    """
    def extract(text):
        if marker:
            hits = re.findall(
                re.escape(marker) + r"\s*(.+?)\s*$",
                text, flags=re.IGNORECASE | re.MULTILINE,
            )
            if hits:
                return normalize(hits[-1])
        for line in reversed(text.splitlines()):
            if line.strip():
                return normalize(line)
        return normalize(text)
    return extract


# --------------------------------------------------------------------------- #
# The statistics — Dirichlet posterior stopping rule + fixed-N recommendation  #
# --------------------------------------------------------------------------- #
def leader_confidence(counts, leader, prior=1.0, draws=2000, rng=random):
    """P(leader is the true plurality winner) under a Dirichlet posterior.

    Votes are multinomial; the posterior over answer probabilities is
    Dirichlet(prior + counts). We add one extra 'unseen' pseudo-category with
    `prior` mass so an early unanimous run is not treated as certainty — the
    true modal answer might still be one no juror has voiced yet. We Monte-Carlo
    the posterior (Dirichlet == normalized independent Gammas) and report how
    often `leader` comes out on top.
    """
    labels = list(counts)
    alphas = [counts[l] + prior for l in labels]
    alphas.append(prior)  # 'some answer not yet seen'
    li = labels.index(leader)
    wins = 0
    for _ in range(draws):
        gs = [rng.gammavariate(a, 1.0) for a in alphas]
        if max(range(len(gs)), key=gs.__getitem__) == li:
            wins += 1
    return wins / draws


def majority_correct_prob(n, p):
    """P(strict majority of n i.i.d. jurors is correct), each correct w.p. p."""
    need = n // 2 + 1
    return sum(comb(n, k) * p ** k * (1 - p) ** (n - k) for k in range(need, n + 1))


def recommend_fixed_n(p, target=0.90, cap=41):
    """Smallest odd N whose binary-majority vote clears `target`, else None/cap.

    Binary approximation: pessimistic for open-ended tasks where wrong answers
    disperse (there the real N is smaller), honest when p <= 0.5 (voting can't
    help — it amplifies the modal answer, now wrong)."""
    if p <= 0.5:
        return None
    for n in range(1, cap + 1, 2):
        if majority_correct_prob(n, p) >= target:
            return n
    return cap


# --------------------------------------------------------------------------- #
# Samplers                                                                     #
# --------------------------------------------------------------------------- #
class FireworksSampler:
    """One tuned juror config, called n-at-a-time over the OpenAI-compatible API."""

    def __init__(self, model, api_key, base_url=DEFAULT_BASE_URL, temperature=1.1,
                 top_p=0.9, top_k=40, max_tokens=8192, presence_penalty=0,
                 frequency_penalty=0, system=None, timeout=180,
                 max_workers=8, retries=3):
        if not api_key:
            raise SystemExit("No API key. Set FIREWORKS_API_KEY (env or ./.env) "
                             "or use --mock-p for an offline run.")
        self.model, self.api_key, self.base_url = model, api_key, base_url.rstrip("/")
        self.temperature, self.top_p, self.top_k = temperature, top_p, top_k
        self.max_tokens, self.system = max_tokens, system
        # §G pins these at 0 — penalties corrupt code and stack a second
        # randomizer on the temperature. Held here explicitly rather than left to
        # a vendor default, so the invariant has a site in the run and not only
        # in the briefing. tools/check-doctrine.py asserts it.
        self.presence_penalty, self.frequency_penalty = presence_penalty, frequency_penalty
        self.timeout, self.max_workers, self.retries = timeout, max_workers, retries

    def _one(self, prompt):
        messages = []
        if self.system:
            messages.append({"role": "system", "content": self.system})
        messages.append({"role": "user", "content": prompt})
        body = json.dumps({
            "model": self.model, "messages": messages,
            "temperature": self.temperature, "top_p": self.top_p,
            "top_k": self.top_k, "max_tokens": self.max_tokens, "n": 1,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
        }).encode()
        req = urllib.request.Request(
            self.base_url + "/chat/completions", data=body,
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json"},
        )
        last = None
        for attempt in range(self.retries):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    data = json.load(r)
                return data["choices"][0]["message"]["content"]
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
                last = e
                if attempt < self.retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # 1s, 2s, 4s
        raise SystemExit(f"Fireworks call failed after {self.retries} tries: {last}")

    def sample(self, prompt, n):
        with ThreadPoolExecutor(max_workers=min(n, self.max_workers)) as ex:
            return list(ex.map(lambda _: self._one(prompt), range(n)))


class MockSampler:
    """Synthetic jurors for offline testing: emits the gold answer w.p. `p`,
    otherwise a distractor. Lets the voter and calibration be exercised (and this
    file's math validated) with no key and no spend.

    Two levers model the regimes where a vote should NOT be trusted — the ones a
    naive i.i.d. mock hides (and the exact ones that matter for a temperature-less
    Claude jury, where draw independence can't be dialed, only measured):

      rho (0..1)   Inter-juror correlation. With probability `rho` a juror copies
                   a per-question *consensus* draw instead of drawing on its own.
                   The marginal per-draw accuracy stays ~`p` regardless of rho —
                   only the independence changes — so as rho rises you watch the
                   vote stop helping (voted accuracy falls back toward `p`): the
                   "jury collapses to one" failure, made visible.
      systematic   When a juror is wrong, all errors converge on ONE wrong answer
                   instead of scattering across the pool. Below p=0.5 that wrong
                   answer becomes modal and the vote *entrenches* it — the
                   systematic-bias failure the dispersed default can't show."""

    def __init__(self, p=0.7, gold="0.05", distractors=None, marker="ANSWER:",
                 seed=None, rho=0.0, systematic=False):
        self.p, self.gold, self.marker = p, str(gold), marker
        self.distractors = distractors or ["0.10", "1.00", "0.15", "0.01", "0.50"]
        self.systematic = systematic
        self.rho = max(0.0, min(1.0, rho))
        self.seed = seed
        self.rng = random.Random(seed)
        self._consensus = {}  # per-prompt shared draw, stable across batches

    def _draw_answer(self, rng):
        if rng.random() < self.p:
            return self.gold
        # systematic bias: every error collapses onto ONE wrong answer.
        return self.distractors[0] if self.systematic else rng.choice(self.distractors)

    def _consensus_for(self, prompt):
        """A single shared draw per prompt, stable across batches and independent
        of PYTHONHASHSEED (random.Random seeds deterministically from a str)."""
        if prompt not in self._consensus:
            self._consensus[prompt] = self._draw_answer(random.Random(f"{self.seed}|{prompt}"))
        return self._consensus[prompt]

    def sample(self, prompt, n):
        out = []
        for _ in range(n):
            if self.rng.random() < self.rho:
                ans = self._consensus_for(prompt)   # correlated: copy the panel consensus
            else:
                ans = self._draw_answer(self.rng)   # independent draw
            out.append(f"(reasoning elided)\n{self.marker} {ans}")
        return out


# --------------------------------------------------------------------------- #
# The Jury                                                                     #
# --------------------------------------------------------------------------- #
def deliberate(sampler, prompt, extractor, *, min_n=3, max_n=40, batch=3,
               confidence=0.95, prior=1.0, draws=2000):
    """Empanel jurors in concurrent batches until the verdict is decisive."""
    counts = Counter()
    transcript = []
    conf = 0.0
    while len(transcript) < max_n:
        need = min(batch, max_n - len(transcript))
        for text in sampler.sample(prompt, need):
            ans = extractor(text)
            counts[ans] += 1
            transcript.append({"answer": ans, "text": text})
        if len(transcript) < max(min_n, 1):
            continue
        leader, _ = counts.most_common(1)[0]
        conf = leader_confidence(counts, leader, prior=prior, draws=draws)
        if conf >= confidence:
            break
    leader, lead_count = counts.most_common(1)[0]
    return {
        "answer": leader,
        "confidence": round(conf, 4),
        "jurors": len(transcript),
        "lead": f"{lead_count}/{len(transcript)}",
        "tally": _ranked_tally(counts),
        "stopped": "confident" if conf >= confidence else "hit max-n",
        "transcript": transcript,
    }


def _ranked_tally(counts):
    """Answers by descending votes; ties broken Z->A (house style)."""
    return [
        {"answer": a, "votes": c}
        for a, c in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]), reverse=False)
    ]


def calibrate(sampler, dataset, extractor, *, samples_per_q=20, target=0.90,
              min_n=3, max_n=40, batch=3, confidence=0.95, prior=1.0, draws=2000):
    """Measure p-hat, vote accuracy, and the jury size the adaptive rule spends."""
    single_correct = single_total = 0
    vote_correct = adaptive_correct = 0
    jury_sizes = []
    for item in dataset:
        gold = normalize(str(item["answer"]))
        draws_txt = sampler.sample(item["prompt"], samples_per_q)
        answers = [extractor(t) for t in draws_txt]
        single_correct += sum(a == gold for a in answers)
        single_total += len(answers)
        if Counter(answers).most_common(1)[0][0] == gold:
            vote_correct += 1
        verdict = deliberate(sampler, item["prompt"], extractor, min_n=min_n,
                             max_n=max_n, batch=batch, confidence=confidence,
                             prior=prior, draws=draws)
        jury_sizes.append(verdict["jurors"])
        if verdict["answer"] == gold:
            adaptive_correct += 1
    q = len(dataset)
    p_hat = single_correct / single_total if single_total else 0.0
    fixed_vote_acc = vote_correct / q if q else 0.0
    adaptive_vote_acc = adaptive_correct / q if q else 0.0
    binary_n = recommend_fixed_n(p_hat, target=target, cap=max_n)
    return {
        "questions": q,
        "samples_per_question": samples_per_q,
        "p_hat_single_sample": round(p_hat, 4),
        "accuracy_fixed_vote": round(fixed_vote_acc, 4),
        "accuracy_adaptive_vote": round(adaptive_vote_acc, 4),
        "adaptive_jury_size_avg": round(sum(jury_sizes) / q, 2) if q else 0.0,
        "adaptive_jury_size_max": max(jury_sizes) if jury_sizes else 0,
        # Binary-majority planning figure — pessimistic when wrong answers
        # disperse. The MEASURED accuracy_fixed_vote above is the real signal.
        "recommended_fixed_n_binary": binary_n,
        "recommended_fixed_n_note": (
            "conservative binary bound; measured accuracy_fixed_vote is the truth"
            if binary_n is not None else
            "binary bound undefined (p<=0.5); trust measured accuracy_fixed_vote"),
        "recommendation_target": target,
        "verdict": _verdict(p_hat, fixed_vote_acc),
    }


def _verdict(p_hat, vote_acc):
    """Honest read driven by what was MEASURED, not the binary approximation."""
    lift = vote_acc - p_hat
    if vote_acc < 0.5 or lift <= 0.0:
        return ("Voting does NOT help: the modal answer is not reliably correct "
                "(a systematic bias — more jurors only entrench it). Fix the "
                "sampler/prompt before voting.")
    base = f"Voting lifts accuracy {p_hat:.2f} -> {vote_acc:.2f} (+{lift:.2f}). "
    if p_hat >= 0.8:
        return base + "Sweet spot: small juries (3-7) suffice."
    if p_hat >= 0.65:
        return base + "Workable: expect juries around 9-15."
    if p_hat > 0.5:
        return base + "Weak per-sample margin; jury size climbs fast."
    return base + ("Note p<=0.5 yet voting still works — the dispersed-error "
                   "regime: wrong answers scatter, so the correct one stays modal.")


# --------------------------------------------------------------------------- #
# Config plumbing + CLI                                                        #
# --------------------------------------------------------------------------- #
def load_dotenv(path=".env"):
    """Minimal KEY=VALUE loader — no dependency, does not overwrite real env."""
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def build_sampler(args):
    if args.mock_p is not None:
        return MockSampler(p=args.mock_p, gold=args.mock_true,
                           marker=args.answer_marker or "ANSWER:", seed=args.seed,
                           rho=args.mock_rho, systematic=args.mock_systematic)
    load_dotenv(args.env_file)
    return FireworksSampler(
        model=args.model, api_key=os.environ.get("FIREWORKS_API_KEY"),
        base_url=args.base_url, temperature=args.temperature, top_p=args.top_p,
        top_k=args.top_k, max_tokens=args.max_tokens, system=args.system,
    )


def _add_sampling_args(p):
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--base-url", default=DEFAULT_BASE_URL)
    p.add_argument("--temperature", type=float, default=1.1)
    p.add_argument("--top-p", type=float, default=0.9)
    p.add_argument("--top-k", type=int, default=40)
    p.add_argument("--max-tokens", type=int, default=8192)
    p.add_argument("--system", default=None, help="Optional system prompt.")
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
    p.add_argument("--max-n", type=int, default=40)
    p.add_argument("--batch", type=int, default=3,
                   help="Jurors empanelled concurrently per round.")
    p.add_argument("--confidence", type=float, default=0.95,
                   help="Posterior P(leader is plurality winner) needed to stop.")
    p.add_argument("--prior", type=float, default=1.0, help="Dirichlet prior strength.")
    p.add_argument("--draws", type=int, default=2000, help="Posterior Monte-Carlo draws.")


def main(argv=None):
    ap = argparse.ArgumentParser(description="The Jury — adaptive sequential self-consistency.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    # Gym-schema aliases mirror the Claude backend's, so the same names work here.
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
    c.add_argument("--samples-per-q", type=int, default=20)
    c.add_argument("--target", type=float, default=0.90,
                   help="Target reliability for the fixed-N recommendation.")
    c.add_argument("--mock-questions", type=int, default=0,
                   help="Offline: synthesise this many questions (needs --mock-p).")
    _add_sampling_args(c)
    _add_jury_args(c)

    args = ap.parse_args(argv)
    cmd = {"strength": "deliberate", "form": "calibrate"}.get(args.cmd, args.cmd)
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
