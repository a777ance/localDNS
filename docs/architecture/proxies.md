# Heimdall — the proxy register and mediation doctrine

<!-- provenance: D · register rows derived from the configs named in §4 (per-row tier in the table); §5-§6 claims from four live experiments against the agent environment · 2026-08-08 · verify: re-run the §6 experiments; re-read each config named in the register -->

Heimdall keeps the Bifrost. He sees every crossing and decides who passes. Bifrost (§H) is
the schema for *composing* a command; this is the register of everything that stands in the
path of one and can refuse it.

**Adopted 2026-08-08**, after a finding that says why the register is needed: the agent
environment blocks `git push --delete` with a bare `403`, and it took four experiments to
establish that no GitHub setting could change it. In the same session, `git push --force`
against the same remote **succeeded** — orphaning commits just as effectively as a delete
would. The control was real, and it guarded the wrong thing.

---

## 1. What counts as a proxy here

Anything that **sits in a path, can see what crosses it, and can refuse or transform it.**
Not just HTTP forward-proxies: a firewall, a resolver, a `PreToolUse` hook, a secret vault,
and a credential-injecting middlebox are all the same shape.

The consequence — the reason this file exists — is that **a proxy is the only kind of
invariant a run cannot ignore by not reading it.** `docs/architecture/warrant-sites.md`
ranks sites: prose < citation < inlined text < fail-closed structure < mechanical check.
Proxy-scoping sits above all of them. A check is in the run's *given-set* and can be
bypassed by a run that never invokes it. A proxy is in the run's **world**.

That power is exactly why each one needs to be written down. An unregistered proxy is an
undocumented single point of failure that also sees all your traffic.

---

## 2. The seven questions

Every row in the register answers these. They are the questions this session had to
discover by experiment, one failure at a time.

1. **Mediates what?** The traffic class it stands in front of.
2. **Who holds the authority?** Caller-held credential, or proxy-held? This sets the blast
   radius of a compromised caller.
3. **What can it refuse?** The refusal surface — destinations, verbs, content, identities.
4. **Is refusal legible?** Does it say *what* it refused and *why*, or just fail?
5. **Bypassable?** Can the caller route around it and still reach the destination?
6. **Fail-open or fail-closed?** What happens when the proxy itself breaks.
7. **Scoped by verb or by effect?** See Law 1 — this is where the leaks are.

---

## 3. Declared, enforced, or neither

The register separates three things this repo has been conflating:

| Kind | Meaning | Worth |
| --- | --- | --- |
| **Enforced** | An intermediary refuses. The caller cannot proceed. | A control. |
| **Declared** | Written down, and the caller is asked to comply. | A convention. Binding only on a run that reads and honours it. |
| **Ambient** | In the path, but refuses nothing — it routes or transforms. | Not a control at all; still a wiretap and a failure point. |

**A declared boundary that reads like an enforced one is the dangerous case**, because it
buys the confidence of a control without the behaviour of one. Three live examples in §5.

---

## 4. The register

`E` enforced · `D` declared · `A` ambient. Tier is the provenance of the row's detail.

| # | Proxy | Kind | Mediates | Authority held by | Can refuse | Legible | Bypassable | Fails | Scope | Tier |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Agent git proxy** (`GITHUB_TOKEN=proxy-injected`) | E | git ref operations | **proxy** — minted per request | ref deletes, tag pushes | **no** — bare 403 | no | closed | **verb** ⚠ | O |
| 2 | **Agent egress proxy** (`$HTTPS_PROXY`, CA re-terminated) | E | all outbound HTTPS | proxy | destination hosts | partial — `/__agentproxy/status` | no | closed | destination | O |
| 3 | **`.claude/hooks/gate.sh`** (`PreToolUse(Bash)`) | E | Bash calls containing `git commit` | local hook | commits failing the five checks | yes — stderr to the model | **yes** — `touch .claude/.gate-off` | **open** on plumbing break, closed on check failure | content | O |
| 4 | **UFW** | E | all inbound | host | ports, source ranges | yes | no | closed | port/source | R |
| 5 | **WireGuard** | E | remote access transport | host + peer keys | non-peers | yes — no handshake | no — only open port | closed | identity | R |
| 6 | **Pi-hole** | E | every LAN/VPN DNS query | host | blocklisted domains | yes | yes — hardcode another resolver | open | destination | O |
| 7 | **Unbound** (`streaming-forward.conf`) | A | DNS resolution | host | — routes, refuses nothing | — | no — Pi-hole's only upstream | `forward-first` → recursive | sensitivity | O |
| 8 | **Cloudflare DoT** (`1.1.1.1@853`) | A | *streaming lookups only* | Cloudflare | could log or lie | no | — | falls back to recursion | destination | O |
| 9 | **sops + age vault** | E | secret material | **age key, off-repo** | anyone without the key | yes — decrypt fails | no | closed | possession | R |
| 10 | **LiteLLM router** (`:4040`) | E | LLM API calls | router master key | unknown models, budget | yes — HTTP errors | **yes** — call Ollama `:11434` direct | failover/cooldown | model/route | R |
| 11 | **ttyd** (`:7681`, `:7682`) | E | a login shell over HTTP | `--credential` + OS `login` | unauthenticated callers | yes — 401 | no | closed | identity (single shared credential ⚠) | O |
| 12 | **NotebookLM bridge** (`bridge.json`) | D | repo Markdown → Google Docs | allowlist file | unlisted files | — | yes | — | allowlist | R |
| 13 | **Generator `--out-dir`** | D | where statements are written | a CLI argument | **nothing** | — | trivially | — | convention | O |
| 14 | **Bifrost `@` / `#`** (§H mount table) | D | what a run may read vs write | **the run's own compliance** | **nothing** | — | trivially | — | convention | O |
| 15 | **"Never force-push"** (CLAUDE.md §3) | D | history rewriting | the run's own compliance | **nothing** — proven, §6 | — | trivially | — | convention ⚠ | O |

---

## 5. The laws

**Law 1 — Scope by reversibility, not by verb.** The agent git proxy blocks `delete` and
permits `--force`. Both orphan commits; only one is refused. The right boundary is never
"this verb sounds dangerous" but **"can this operation destroy something that exists
nowhere else?"** Delete, force-push, and a backwards reset-push belong on the same side of
that line. Enumerate effects, then find every verb that produces them.

**Law 2 — A refusal must be legible.** A bare `403` cost this session four experiments to
distinguish egress policy from a GitHub ruleset from proxy policy — and produced a *wrong
report to the founder* in the meantime ("refused by the environment", as though it were a
permission he could grant). A proxy that refuses without saying what and why converts a
safety control into a debugging expense. Compare row 3, which is enforced *and* legible:
it prints which check failed and how to proceed.

**Law 3 — Publish a capability manifest.** Nothing advertised that deletes were blocked;
it was discoverable only by failing. Any proxy in this register should be answerable
*before* the attempt, not only after it.

**Law 4 — Bypassable means convention, not control.** Rows 3, 6, 10 can be routed around.
That is not automatically wrong — `gate.sh`'s bypass is deliberate and its message says the
invariant is unsited while the bypass exists — but it must be *known*, because a bypassable
proxy provides no guarantee against a run that doesn't want one.

**Law 5 — Fail-closed on the security path, fail-open on the plumbing path.** `gate.sh`
gets this right on purpose: a failing *check* blocks the commit; a broken *hook* lets it
through, because a gate that wedges the repo when its own plumbing breaks is a worse
failure than the one it guards. State which of the two you chose, per proxy.

**Law 6 — Every proxy is a wiretap and a single point of failure.** It sees everything
crossing it. This is precisely why row 7 exists in the shape it does: sensitive lookups
resolve recursively and **structurally cannot** reach row 8. The design answer to "a proxy
sees my traffic" is not to trust the proxy — it is to keep the sensitive class out of its
path entirely.

**Law 7 — Know whether you hold the credential.** Row 1's token is *not in the
environment*; `proxy-injected` is a placeholder. It cannot be exfiltrated from a place it
never occupies, logged, or replayed after the session. A caller-held scoped token can be
all three. Prefer proxy-held authority for anything an agent touches.

---

## 6. Gap audit — 2026-08-08

Reproduce any of these; each is one command.

- **⚠ Row 15 — "never force-push" is enforced by nothing.** Proven: a forced,
  non-fast-forward update to `tmp/delete-probe` in `Marketing-Strategy-1` succeeded
  (`+ f750e15...b5b085c (forced update)`). A session could force-push `Yggdrasil`
  tomorrow, orphan founder-authored work, and be following its own briefing faithfully.
  **This is the highest-value unsited invariant in the portfolio.** Remedy: a
  `PreToolUse(Bash)` matcher refusing force-pushes to `Yggdrasil`/`main` — Law 1 applied to
  Law 4.
- **⚠ Row 1 is verb-scoped** (Law 1) **and illegible** (Law 2). Not fixable from inside a
  session; recorded so no future session re-derives it. See
  `evidence/403-deletion-block.md` in the session handoff, or reproduce via §2's questions.
- **⚠ Row 11 — one shared credential** gates a login shell. Already in Known issues; listed
  here because the register is the place the whole class becomes visible at once.
- **Row 14 — `@`/`#` is declared, not enforced.** The mount table is honoured by a
  compliant run and by nothing else. This is *acceptable* — it is a composition schema, not
  a sandbox — but §3's distinction must be stated wherever it is taught, or it will be read
  as a guarantee. The one-way door that actually holds is row 1 plus the human at `*`.
- **Row 13 — `--out-dir`** keeps generated statements out of the public repo by *argument*.
  The real control against publishing customer data is that the data lives in a separate
  private repo, not that a flag was passed.

---

## 7. Adding a proxy

1. Answer §2's seven questions and add the row **before** relying on it.
2. Say **enforced, declared, or ambient** (§3). If declared, do not write it in language
   that implies refusal.
3. Apply Law 1: enumerate the *effects* to prevent, then every verb that reaches them.
4. Make refusal legible (Law 2) and answerable in advance (Law 3).
5. Choose fail-open or fail-closed deliberately, and record why (Law 5).
6. If it is enforced and mechanically decidable, it also belongs in
   `warrant-sites.md`'s ladder — a proxy is the top rung, not a substitute for the rest.
