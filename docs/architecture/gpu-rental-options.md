# GPU rental options — cost report for `cloud-gpu-reason`

`provenance: A · web search (Vast.ai/RunPod/Lambda listings) · 2026-08-16 · verify: re-quote
listed provider pricing pages before trusting a number here — marketplace/on-demand rates
move daily`

Cost prediction for the `cloud-gpu-reason` tier in
`04-user-services/ai-orchestration/config.yaml` — the on-demand rented-GPU pod (over
Tailscale) that runs full `deepseek-r1:70b` when a household query needs heavy
chain-of-thought the t630 CPU can't do (CLAUDE.md § 1 "Known issues", § C). This
doc is **asserted/reconstructed** pricing intelligence, not a measured bill — no
pod has been rented yet. Re-quote before committing to a provider; nothing here
should be printed on a customer-facing Statement (§ "Portfolio conventions" —
Statements print only measured numbers).

---

## What we're sizing

`deepseek-r1:70b` via Ollama needs roughly **40–45 GB VRAM** at the Q4 quant
Ollama pulls by default (a 70B model at ~4.5 bits/weight ≈ 40 GB, plus KV-cache
headroom). That rules out a single RTX 4090/3090 (24 GB) — either 2× 4090 or one
48–80 GB card (A100 80GB, A6000, or a dual-4090 pod) is the real floor. Usage
pattern is **bursty and on-demand**: the pod spins up only when local/cloud
tiers overflow to it, then should be torn down — this is a per-second-billed
marketplace workload, not a reserved instance.

## Per-hour rates by card (2026-08-16 snapshot)

| Card | VRAM | On-demand $/hr (typical) | Fits 70B alone? | Source |
| ---- | ---- | ------------------------- | ---------------- | ------ |
| RTX 3090 | 24 GB | $0.12–0.35 | No — needs 2× | [Vast.ai](https://vast.ai/pricing/gpu/RTX-4090) |
| RTX 4090 | 24 GB | $0.29–0.59 (mktplace low ~$0.13) | No — needs 2× | [Vast.ai](https://vast.ai/pricing/gpu/RTX-4090), [SynpixCloud](https://www.synpixcloud.com/blog/vast-ai-vs-runpod-rtx-4090-pricing) |
| A100 80GB (on-demand) | 80 GB | $1.07–1.99 | Yes | [RunPod/Spheron comparison](https://www.spheron.network/blog/gpu-cloud-pricing-comparison-2026/) |
| A100 80GB (marketplace spot) | 80 GB | $0.60–0.67 | Yes | [Spheron](https://www.spheron.network/blog/gpu-cloud-pricing-comparison-2026/), Vast.ai marketplace |
| H100 (RunPod) | 80 GB | $1.99–2.69 | Yes, generous headroom | [Thunder Compute comparison](https://www.thundercompute.com/blog/runpod-pricing-vs-thunder-compute) |
| H100 (Vast.ai marketplace low) | 80 GB | from $1.49 | Yes | [IntuitionLabs](https://intuitionlabs.ai/articles/h100-rental-prices-cloud-comparison) |
| H100 (Lambda Labs, SLA) | 80 GB | $3.29 | Yes | [SynpixCloud](https://www.synpixcloud.com/blog/cloud-gpu-pricing-comparison-2026) |

Practical shortlist for this workload — single 80 GB card, cheapest reasonable
on-demand rate, no SLA needed (a household reasoning overflow tier tolerates a
retry or fallback to `cloud-overflow` per `config.yaml`'s fallback chain):

- **Vast.ai A100 80GB, on-demand marketplace** — **~$1.00–1.10/hr** is the
  realistic sustained rate (spot dips to $0.60–0.67 but can be reclaimed
  mid-session, which is a bad fit for an interactive query).
- **RunPod A100/H100 on-demand (community or secure cloud)** — **~$1.39–2.69/hr**,
  no marketplace-eviction risk, still self-serve (matches "spin up on demand,
  no ops overhead" better than Lambda's reserved/SLA posture).

Lambda Labs is priced out (20–40% premium for an SLA + InfiniBand this
single-node, bursty workload doesn't need).

## Cost scenarios

All scenarios assume **on-demand billing, pod torn down between sessions**
(config.yaml's `TAILSCALE_GPU_HOST` implies "spun up on demand" per
`README.md` — not a 24/7 reservation). Figures are `deepseek-r1:70b` inference
only; storage/idle charges while the pod is stopped are provider-specific and
not modeled here (Vast.ai and RunPod both charge a small idle storage fee per
GB-month if you keep the image between sessions — budget **~$5–10/mo** if so).

| Usage pattern | Sessions/mo | Est. minutes/session | GPU-hours/mo | Vast.ai A100 (~$1.05/hr) | RunPod A100 (~$1.50/hr) | RunPod H100 (~$2.30/hr) |
| ------------- | ----------- | --------------------- | ------------- | -------------------------- | ------------------------ | ------------------------ |
| **Light** — occasional deep-reasoning query, a few times a week | 12 | 10 | 2 | **~$2/mo** | **~$3/mo** | **~$4.60/mo** |
| **Moderate** — daily heavy query, some multi-turn sessions | 30 | 15 | 7.5 | **~$8/mo** | **~$11/mo** | **~$17/mo** |
| **Heavy** — several long reasoning sessions/day, small household using it as a habit | 90 | 20 | 30 | **~$32/mo** | **~$45/mo** | **~$69/mo** |
| **Always-on** (worst case — pod left running instead of torn down) | — | 730 hrs | 730 | **~$766/mo** | **~$1,095/mo** | **~$1,679/mo** |

The always-on row is there to make the point sharply: **this tier only makes
sense if the pod is actually ephemeral.** A reserved/always-on 80GB card is
$700–1,700/mo — nowhere near worth it for a household reasoning overflow path
that has a working `cloud-overflow` fallback already. If usage ever looks like
the "heavy" row sustained for months, a monthly-reserved instance (not covered
here — re-quote at that point) would likely beat marketplace on-demand.

## Recommendation

1. **Vast.ai, on-demand (not interruptible) A100 80GB**, torn down after each
   session — cheapest realistic option (~$1.00–1.10/hr) at light-to-moderate
   usage (**$2–8/mo**), matches the "spin up on demand, fall back to
   `cloud-overflow` when off" design already in `config.yaml`.
2. If marketplace variance (host reliability, teardown discipline) becomes a
   problem, move to **RunPod on-demand A100** — a few tens of cents/hr more,
   still self-serve, more consistent host quality.
3. Automate teardown — a systemd timer or the pod's own idle-shutdown, not
   manual discipline — before this is trusted as a cost figure rather than a
   cost *ceiling*. Nothing above is a measured bill; re-quote provider pricing
   pages at deploy time and replace this table's numbers with **`O`**-tier
   (observed) figures once a real pod has actually run.

## The reasoning/sensitivity dilemma

`config.yaml`'s fallback chain (`local-reason` → `cloud-gpu-reason` →
`cloud-overflow`) reads as a **capability ladder** — climb it when the local
model is too weak. It is easy to mistake that for a **privacy ladder** too,
because `cloud-gpu-reason` sounds like it's still "yours." It isn't: it's
rented hardware, and the host (on a marketplace like Vast.ai, a stranger with
physical/hypervisor access) can see everything that transits the pod — see
the "data exposure" discussion this doc's chat history covers. So climbing the
ladder trades reasoning power for privacy, every step up.

That trade collides with how reasoning depth and sensitivity actually
distribute in practice — **they are not correlated, and if anything run
opposite:**

| | Sensitive | Non-sensitive |
| --- | --- | --- |
| **Low reasoning** | Stays on **local-reason**, even if the answer is worse. Falling through to `cloud-gpu-reason`/`cloud-overflow` here buys no capability and just hands a trivial-effort query to a third party for nothing. | `local-fast` handles it. No third party needed. |
| **High reasoning** | **The unserved quadrant.** Deep personal reasoning — tax situations, medical symptoms, legal disputes, relationship conflicts — is exactly where you want both depth *and* privacy, and today's ladder has no private option at that depth. | The real, narrower use case for `cloud-gpu-reason`/`cloud-overflow`: abstract/technical heavy work with no personal stakes — debugging code, math proofs, general research synthesis. |

**The dilemma, stated plainly:** the queries that most justify paying for
heavy reasoning are disproportionately the sensitive ones, and the ladder's
only heavy-reasoning tiers are both third-party hardware. There is no
configuration of this stack that gets you deep reasoning *and* privacy at the
same time — that combination requires **owned** local compute (a GPU the
household actually controls), which is a hardware purchase, not a routing
change.

**Routing rule adopted from this** (sited in `config.yaml` next to
`router_settings`, not only here — a rule stated only in this doc governs
nothing per CLAUDE.md's "a clause needs a site"): sensitivity is classified
*before* the fallback chain ever runs, and a sensitive query never crosses
onto `cloud-gpu-reason` or `cloud-overflow` regardless of how much reasoning
it needs. The LiteLLM fallback map alone cannot make that call — it has no
concept of sensitivity, only of tier failure — so today the caller (or a
future privacy gate, in the spirit of the Odin/Heimdall design referenced in
`docs/ai-cto/context.md`) has to enforce it manually. **This is an open gap,
not a solved one**: nothing in the current stack stops a sensitive prompt
from silently falling through to a rented GPU when the local model times out
or errors.

## Open item

`config.yaml`'s `TAILSCALE_GPU_HOST` is still a `CHANGE_ME` placeholder — no
provider has been selected or wired up on the live box. This doc informs that
choice; it does not close `docs/REMEDIATION-BOARD.md`'s AI/console-hardening
track. Pin the provider, Tailscale-join the pod, and measure one real session's
`$/hr` and tokens/sec before trusting any number above for a Statement or a
budget commitment.
