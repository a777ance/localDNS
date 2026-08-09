#!/usr/bin/env python3
"""Assert the mechanically-decidable clauses of CLAUDE.md §G against the code.

§G (the LLM sampling doctrine) states exact juror-sampler values. Those values
are implemented in `04-user-services/ai-orchestration/jury/jury.py`. Nothing
previously connected the two: the doctrine could drift from the implementation,
or the implementation from the doctrine, and both would still read as correct in
isolation. This script closes that by parsing §G for the numbers it states and
the sampler for the numbers it uses, and failing when they disagree.

WHY THIS EXISTS, precisely. A briefing paragraph reaches a reader once. It is not
in the read path of a run that edits `jury.py`, so an invariant living only there
has an author and no site — the run's given-set simply omits it, and nothing in
the run is obliged to check. Restating a clause in a command file gives it a
site for runs that read that file. For a clause that decides mechanically, a
static check is the stronger site: it holds regardless of which file the run
read, and it fails loudly rather than silently.

SCOPE — deliberately narrow. Only clauses with a machine-decidable truth value
are checked here:

  * the juror sampler's default temperature / top_p / top_k / max_tokens
  * presence & frequency penalties pinned to 0 AND actually sent (a value left
    to a vendor default is not pinned — it is inherited, and vendors change
    defaults)
  * the CLI defaults matching the constructor defaults, since the CLI is the
    real entry point

NOT checked here, because they do not decide mechanically: "fire the lazy anchor
first," "never consume a single warm draw where a verdict matters," "measure `p`,
don't guess it." Those are sited in `.claude/commands/*.md` and
`.claude/agents/juror.md`, which ARE in the read path of the runs they govern.
A green run of this script is not a claim that the doctrine is being followed —
only that the numbers still agree.

The Claude-backend jury (`jury-claude/`) is intentionally exempt: current Claude
models reject temperature/top_p/top_k with a 400, a deviation §G's portability
clause anticipates and that variant's README states. There is no number there to
check.

Exits non-zero on any mismatch, so it can gate a commit or CI run.

Usage:
    python3 tools/check-doctrine.py
"""
import ast
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIEFING = os.path.join(ROOT, "CLAUDE.md")
SAMPLER = os.path.join(ROOT, "04-user-services/ai-orchestration/jury/jury.py")
SAMPLER_CLASS = "FireworksSampler"

# Values §G states in prose, and the token that carries each one. Penalties are
# stated as a phrase ("presence/frequency penalties **`0`**") rather than a
# `name value` pair, so they get their own pattern.
STATED = {
    "temperature": r"`temperature\s+([0-9.]+)`",
    "top_p": r"`top_p\s+([0-9.]+)`",
    "top_k": r"`top_k\s+([0-9.]+)`",
    "max_tokens": r"`max_tokens\s+([0-9.]+)`",
}
PENALTY_CLAUSE = r"presence/frequency penalties\D{0,20}`([0-9.]+)`"
PENALTY_KEYS = ("presence_penalty", "frequency_penalty")


def num(text):
    f = float(text)
    return int(f) if f.is_integer() else f


def doctrine_values():
    """Pull the stated sampler values out of CLAUDE.md §G."""
    body = open(BRIEFING, encoding="utf-8").read()
    m = re.search(r"\n## G\..*?(?=\n## )", body, re.S)
    if not m:
        return None, ["CLAUDE.md: could not locate section G"]
    sec, vals, problems = m.group(0), {}, []
    for key, pat in STATED.items():
        hit = re.search(pat, sec)
        if not hit:
            problems.append(f"CLAUDE.md §G: states no value for `{key}`")
        else:
            vals[key] = num(hit.group(1))
    hit = re.search(PENALTY_CLAUSE, sec)
    if not hit:
        problems.append("CLAUDE.md §G: states no presence/frequency penalty value")
    else:
        for k in PENALTY_KEYS:
            vals[k] = num(hit.group(1))
    return vals, problems


def _const(node):
    """Literal value of an AST node, or None if it is not a plain literal."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _const(node.operand)
        return None if inner is None else -inner
    return None


def sampler_facts():
    """Constructor defaults, CLI defaults, and the keys actually sent."""
    tree = ast.parse(open(SAMPLER, encoding="utf-8").read())

    ctor, sent, cli = {}, {}, {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == SAMPLER_CLASS:
            for fn in node.body:
                if isinstance(fn, ast.FunctionDef) and fn.name == "__init__":
                    args = fn.args.args[-len(fn.args.defaults):] if fn.args.defaults else []
                    for a, d in zip(args, fn.args.defaults):
                        v = _const(d)
                        if v is not None:
                            ctor[a.arg] = v
        # The request payload: json.dumps({...}) inside the sampler.
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "dumps" and node.args \
                and isinstance(node.args[0], ast.Dict):
            for k, v in zip(node.args[0].keys, node.args[0].values):
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    sent[k.value] = v
        # argparse: p.add_argument("--temperature", type=float, default=1.1)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "add_argument" and node.args \
                and isinstance(node.args[0], ast.Constant) \
                and str(node.args[0].value).startswith("--"):
            flag = str(node.args[0].value)[2:].replace("-", "_")
            for kw in node.keywords:
                if kw.arg == "default":
                    v = _const(kw.value)
                    if v is not None:
                        cli[flag] = v
    return ctor, sent, cli


def docstring_flags():
    """Pull `--flag value` pairs out of jury.py's own module docstring.

    Found by tripping the wire, 2026-08-08: the constructor, CLI and payload were
    all guarded, but the *usage example* in the docstring was not — so `--top-p`
    could be edited to 0.75 there and every check stayed green. A reader who
    copy-pastes the documented invocation is running the sampler the docs
    describe, not the one §G specifies, and the copy-paste is the likelier entry
    point than the default. The doc is an entry point, so it is a site.
    """
    try:
        doc = ast.get_docstring(ast.parse(open(SAMPLER, encoding="utf-8").read())) or ""
    except Exception:
        return {}
    found = {}
    for flag, val in re.findall(r"--([a-z][a-z-]*)\s+(-?[0-9.]+)\b", doc):
        v = num(val)
        if v is not None:
            found[flag.replace("-", "_")] = v
    return found


def check():
    problems = []
    stated, prob = doctrine_values()
    problems += prob
    if stated is None:
        return problems
    if not os.path.exists(SAMPLER):
        return problems + [f"{SAMPLER}: missing"]

    ctor, sent, cli = sampler_facts()
    doc = docstring_flags()

    for key, want in sorted(stated.items()):
        got = ctor.get(key)
        if got is None:
            problems.append(
                f"jury.py {SAMPLER_CLASS}.__init__: no default for `{key}` "
                f"(§G states {want})")
        elif got != want:
            problems.append(
                f"jury.py {SAMPLER_CLASS}.__init__ `{key}` = {got}, "
                f"but CLAUDE.md §G states {want}")
        # A value the request never carries cannot govern the draw.
        if key not in sent:
            problems.append(
                f"jury.py: `{key}` is never sent in the request payload — "
                f"§G's value would be inherited from the vendor default, not pinned")
        # CLI is the real entry point; a divergent flag default silently wins.
        if key in cli and cli[key] != want:
            problems.append(
                f"jury.py CLI `--{key.replace('_', '-')}` default = {cli[key]}, "
                f"but CLAUDE.md §G states {want}")
        # The docstring's usage example is what a reader copy-pastes; a drifted
        # value there overrides every default that agrees.
        if key in doc and doc[key] != want:
            problems.append(
                f"jury.py docstring usage example `--{key.replace('_', '-')} "
                f"{doc[key]}`, but CLAUDE.md §G states {want} — a reader "
                f"copy-pasting the documented invocation would not be running §G")

    for key in PENALTY_KEYS:
        if stated.get(key) not in (0, 0.0):
            problems.append(
                f"CLAUDE.md §G: `{key}` is stated as {stated.get(key)}, expected 0 "
                f"(penalties stack a second randomizer on the temperature)")
    return problems


def main():
    problems = check()
    if problems:
        print("FAIL CLAUDE.md §G — sampling doctrine vs. implementation")
        for p in problems:
            print(f"  - {p}")
        print("\nDoctrine check FAILED")
        sys.exit(1)
    print("ok   CLAUDE.md §G sampler values match jury.py "
          "(defaults, CLI, the sent payload, and the docstring's usage example)")
    print("\nNote: only the mechanically-decidable clauses are checked. The "
          "posture clauses\n(lazy anchor, vote-as-governor, measure `p`) are "
          "sited in .claude/commands/ and\n.claude/agents/juror.md — a green "
          "run here is not a claim that they were followed.")


if __name__ == "__main__":
    main()
