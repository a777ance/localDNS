# Proxies — the portfolio block (canonical)

**This file is the single source for the proxy section carried by every A777ance repo's
`CLAUDE.md`.** Mediation is portfolio-wide: the agent git proxy and the egress proxy stand
in front of *every* repo in this portfolio, not just `localDNS`. A briefing that says
nothing about them leaves a session to discover the boundaries by hitting them — which is
how a bare `403` became four experiments and a wrong report to the founder.

`tools/sync-briefings.py` renders the block below into each sibling repo between
`proxy-doctrine:start` / `:end` markers. Those rendered blocks are **build output — never
hand-edit them.** Edit this file, re-run the generator, commit the result.

**What stays here and what stays in `localDNS`.** This block carries the *definition*, the
three kinds, and the laws that bind a session in any repo. The full fifteen-row register —
UFW, WireGuard, Pi-hole, Unbound, the vault, the LLM router, ttyd — is stack-specific and
lives in `localDNS/docs/architecture/proxies.md`. Siblings get the part that governs what
they do; they do not get a table describing a box they cannot reach.

<!-- proxy-doctrine:start -->

**A proxy is anything that sits in a path, sees what crosses it, and can refuse or
transform it.** Not just HTTP forward-proxies: a firewall, a resolver, a `PreToolUse` hook,
a secret vault, and a credential-injecting middlebox are all the same shape. Adopted
2026-08-08.

**Why it outranks every other kind of rule.** An invariant in briefing prose has an author
and no site; a static check has a site but sits in the run's *given-set*, so a run that
never invokes it is unbound. A proxy sits in the run's **world** — it cannot be ignored by
not reading it. That makes it the strongest form available, and also a liability worth
writing down: an unregistered proxy is a wiretap and a single point of failure that nobody
recorded.

- **Three kinds, and the difference is not cosmetic.** **Enforced** — an intermediary
  refuses; the caller cannot proceed. **Declared** — written down, and the caller is asked
  to comply; binding only on a run that reads and honours it. **Ambient** — in the path but
  refuses nothing; it routes or transforms, and is still a wiretap. **Never write a declared
  boundary in the language of an enforced one** — it buys the confidence of a control
  without the behaviour of one. Bifrost's `@`/`#` mount table is *declared*: honoured by a
  compliant run and by nothing else. That is fine for a composition schema and fatal if
  taught as a sandbox.
- **Scope by reversibility, not by verb.** The agent git proxy blocks `git push --delete`
  and **permits `git push --force`** — proven 2026-08-08 by a successful forced update. Both
  orphan commits; only one is refused. Never reason "this verb sounds dangerous"; ask **"can
  this destroy something that exists nowhere else?"** and then find every verb that reaches
  that effect.
- **Therefore: never force-push `Yggdrasil` or `main`.** The environment will not stop you.
  Pull `--ff-only`; if a push is rejected as non-fast-forward, `git fetch` and rebase *your*
  commits onto theirs — never rewrite the shared ref. Expect company on `Yggdrasil`.
- **A refusal must be legible, and answerable in advance.** A bare `403` with no reason
  converts a safety control into a debugging expense. If you build an intermediary, make it
  say *what* it refused and *why*, and make its policy readable before the attempt rather
  than only after the failure.
- **Bypassable means convention, not control.** A proxy the caller can route around
  provides no guarantee against a caller who doesn't want one. That is sometimes correct —
  `gate.sh`'s bypass is deliberate — but it must be *known*, and the bypass should say that
  the invariant is unsited while it is on.
- **Fail-closed on the security path, fail-open on the plumbing path.** A failing *check*
  should block; a *broken hook* should not wedge the repo. Choose deliberately and record
  which you chose.
- **Know whether you hold the credential.** This session's `GITHUB_TOKEN` is the literal
  string `proxy-injected` — the real credential is minted per request and never enters the
  environment, so it cannot be exfiltrated, logged, or replayed. Prefer proxy-held authority
  for anything an agent touches over a caller-held scoped token.

**Register an intermediary before relying on it**, answering: what it mediates · who holds
the authority · what it can refuse · whether refusal is legible · bypassable · fail-open or
fail-closed · scoped by verb or by effect. Full register and the worked gap audit:
`localDNS/docs/architecture/proxies.md`.

<!-- proxy-doctrine:end -->
