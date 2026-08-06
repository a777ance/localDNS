# Permeability, gradients, and the two leaflets

> Three things the bilayer does that a firewall diagram does not show: it sorts traffic by
> *solubility* rather than by rule, it exists to hold a **gradient** rather than to block,
> and its two faces are **chemically different** — which turns out to hand us a detection
> rule we do not currently run.

---

## 1. The permeability ladder

**The biology.** A bilayer sorts what crosses it into four bands, with no policy engine
anywhere:

| Band | Examples | How it crosses |
| ---- | -------- | -------------- |
| Charged / ionic | Na⁺, K⁺, H⁺, amino acids | **Effectively never.** Needs a pump; costs energy |
| Large polar | glucose, nucleotides | Needs a dedicated transporter |
| Small polar, uncharged | H₂O, glycerol, urea | Slowly, unaided — fast enough only with a channel |
| Small nonpolar | O₂, CO₂, N₂ | Freely, unaided, unnoticed |

Two details in the middle band are the interesting ones.

**Water gets a dedicated channel because "slowly" was not good enough.** Aquaporins exist
because bulk water crossing by simple diffusion is too slow for a kidney. Volume traffic
earns a purpose-built pipe.

**And aquaporin is exquisitely selective in a specific way: it passes water and blocks
protons.** It has to. Protons hop along hydrogen-bonded water chains far faster than water
itself moves (the Grotthuss mechanism), so a naïve water pipe would be a proton
short-circuit and would drain the cell's pH gradient — the very thing the membrane is
maintained to hold. Aquaporin's architecture breaks the proton wire while letting water
through single-file.

**The mapping.** Our ladder, band for band:

- **Small nonpolar — crosses unremarked.** Cached DNS answers, NTP, ICMP. Carries no
  identity, needs no decision, and we should not pretend we are inspecting it.
- **Small polar — passes anyway, so give it a pipe.** This is exactly what
  `streaming-forward.conf` is: Netflix, YouTube, Spotify, Steam are high-volume and
  low-sensitivity, they were going to cross regardless, so they get a purpose-built
  channel (Cloudflare over DoT) instead of seeping through the general path. **CAKE on
  `enp1s0` is the same instinct at the byte layer.** We built an aquaporin without calling
  it one.
- **Large polar — needs a transporter.** Anything requiring a stateful, named service to
  cross: the LLM router, the statement generator pulling data.
- **Charged — must not cross unaided, and the pump is the expense.** Credentials, keys,
  identity, the contents of the vault.

> **Claim (checkable, and it is the good one).** *Our aquaporin must pass the bulk without
> passing the credential.* The proton-exclusion property is not a nicety — it is the
> reason the channel does not destroy the thing the membrane was built for. Applied to
> `streaming-forward.conf`, that is precisely the invariant `CLAUDE.md` already states:
> **never add sensitive domains to the forward-path.** The biology explains *why* that
> invariant is load-bearing rather than fastidious — a fast channel that also carries the
> sensitive thing does not merely leak a little, it **shorts out the gradient the whole
> membrane exists to hold**, and it does so at the fastest rate in the system, because
> the channel was optimized for throughput.

> **Opportunity.** The invariant is currently enforced by care. Aquaporin enforces it
> *structurally* — the pore's geometry makes proton conduction impossible, not merely
> discouraged. Candidate: a check in `tools/check-docs.py` or a small companion script
> that reads `streaming-forward.conf` and fails on any forward-zone matching a
> sensitivity denylist (banking, health, government, our own `home.lan`). Cheap, and it
> converts a remembered rule into a structural one.

---

## 2. The gradient is the battery

This is the deepest idea in the collection and the one most likely to change what we
build.

**The biology.** A cell does not spend energy on its membrane for the sake of privacy. It
spends it to hold a **disequilibrium**: Na⁺ high outside and low inside, K⁺ the reverse,
protons pumped into the intermembrane space. Maintaining that costs a large fraction of
the cell's entire energy budget — the Na⁺/K⁺-ATPase alone runs continuously.

And then the cell **spends** it:

- **Chemiosmosis.** The proton gradient drives ATP synthase. The battery, discharged into
  work.
- **Symport.** Glucose is dragged *uphill* into the cell by coupling it to Na⁺ flowing
  *downhill*. The gradient pays for a transport it was not built for.
- **Action potentials.** A nerve signal is the controlled, momentary collapse of the
  gradient. Signalling *is* discharge.

The barrier is not the product. **The held difference is the product**, and its value is
that it can be coupled to a second consumer at almost no marginal cost.

**The mapping.** What disequilibrium does the t630 hold at real expense? Not bandwidth,
not uptime — those are symmetric. It is an **information gradient**: inside the boundary,
the system knows which device asked for what, when, and how often. Outside it, the ISP
sees an encrypted channel, Cloudflare sees only the low-sensitivity forward-path, and the
recursive queries reach authoritative servers without a name attached to them. That
asymmetry is manufactured, deliberately, and it costs continuous effort — every
architectural decision in `CLAUDE.md` is a pump maintaining it.

Now the chemiosmotic question: **what else can that gradient power?**

We already do this once, and it is worth recognizing it as the same move. The monthly
Statement is chemiosmosis. It couples a second consumer to a gradient we were already
paying to maintain: the measured, inside-only facts about a home's network — facts that
exist *only* because the boundary holds — get discharged into work, namely visible proof
that the quiet was earned. The business does not sell the barrier. It sells the
discharge.

> **Claim (speculative, and the most generative thing here).** *Anything we already pay
> to hold can be coupled to a second consumer at near-zero marginal cost, and we have
> found only one.* The Statement is our ATP synthase. Symport is the pattern we have not
> used: coupling something that would otherwise be uphill to the flow we are already
> maintaining. Candidates worth thinking about — none of them decided:
> - The block-list / query stream already tells us when a household's device starts
>   behaving unusually. That signal is a free rider on a gradient we maintain anyway.
> - Uptime data is held inside the boundary for our own operations; an operator's
>   portfolio is that same gradient discharged toward a different consumer.
> - **The discipline the analogy imposes:** a second consumer is only free if it rides an
>   *existing* gradient. If it requires a new pump, it is not symport — it is a new cost,
>   and should be argued for as one.

> **Disanalogy.** A cell's gradient is a genuine physical store; ours is a metaphor for an
> epistemic asymmetry, and epistemic asymmetries do not obey conservation. Discharging
> information does not deplete it — publishing a fact does not remove it from the inside,
> it adds it to the outside, which is the *opposite* of a battery discharging. So the
> "free second consumer" intuition is real, but the "spending it costs you" intuition is
> **inverted**, and that inversion is exactly where privacy risk lives. Every discharge
> permanently narrows the gradient it drew on. Treat each new consumer as a one-way
> valve, because that is what it is.

---

## 3. The two leaflets are not the same leaflet

**The biology.** A bilayer is not symmetric. The outer and inner leaflets carry different
phospholipids, and the cell spends ATP to keep it that way — flippases and floppases move
specific lipids to specific faces, continuously. The best-known case: phosphatidylserine
is kept almost exclusively on the **inner** leaflet of a healthy cell.

And then: when PS *appears on the outer leaflet*, that is the "eat me" signal.
Macrophages read it and clear the cell. The molecule is not itself toxic. **Its presence
on the wrong face is the entire message.**

**The mapping.** `cell-grammar.md` already names B and D as the two leaflets — ingress and
egress guards, deliberately different. This entry adds the part the grammar does not
have: **asymmetry is maintained at cost, and a violation of it is a first-class alarm.**

That is directly buildable, and it is the concrete detection idea this folder was
prospecting for.

> **Claim (checkable, and not currently implemented).** *An internal-only fact appearing
> on the external face is the highest signal-to-noise alarm available to us, and we run
> none of them.* Specific candidates, all derived from things already in the repo:
> - `local-records.conf` defines LAN-only names — `console`, `term`, `laptop`, `kuma`,
>   `pihole`, `ai`, `chat` under `home.lan`. `CLAUDE.md` already states these "must never
>   be published to a public resolver." **A query for one of them arriving from, or
>   leaving toward, the external face is PS on the outer leaflet.** Nothing benign
>   produces it.
> - `192.168.1.118` or `10.8.0.0/24` appearing in an outbound payload is the same shape.
> - The console and web terminals (8088, 7681, 7682) are explicitly LAN + WireGuard only.
>   Any external-face appearance of those ports is inner-leaflet material on the outside.
>
> The pattern generalizes: **we do not need to detect attacks; we need to detect
> inversions.** Enumerating "facts that live on exactly one face" is a small, finite
> exercise, and each one is a free detector with essentially no false-positive surface.

> **Opportunity.** A `docs/architecture/` note (or an Uptime Kuma monitor) enumerating the
> one-face facts and how each would be observed if it inverted. Start with the `home.lan`
> names, since `local-records.conf` already lists them and the invariant is already
> written down — the detector is the missing half of a rule we have stated but cannot
> currently verify.

> **Disanalogy.** PS exposure is *self-reported* — the dying cell raises its own flag, and
> there is no adversary suppressing it. An intruder in our system has every incentive to
> avoid inverting anything observable. So leaflet asymmetry gives us excellent detection
> of **error and misconfiguration**, and only incidental detection of a careful attacker.
> That is still a very good trade — misconfiguration is what has actually bitten this
> stack, repeatedly — but it should not be sold as intrusion detection.
