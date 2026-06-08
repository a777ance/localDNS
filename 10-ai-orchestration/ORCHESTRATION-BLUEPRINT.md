# Multi-model orchestration — engineering blueprint

**Status:** design, not built. **Audience:** an engineer implementing it. **Substrate:**
the stage-10 router (`10-ai-orchestration/`) already running on the t630.

This is the buildable version of the "let one brain route each subtask to the best
specialist, and keep the heavy compute off the laptop" idea. It exists because running
a full DeepSeek-R1 on a laptop pins every core for minutes per prompt and overheats the
machine (see `README.md` → "Offload heavy reasoning to a rented GPU"). The fix is not a
bigger laptop — it's to make the laptop a **thin client** and route work to the right
backend.

Read the existing `README.md` first; it documents the switchboard this builds on.

---

## 0. The one distinction that drives the whole design

There are **two layers**, and conflating them is the most common mistake. The robotics
analogy makes the split clean:

| Layer | Robotics analogue | What it does | Status |
| ----- | ----------------- | ------------ | ------ |
| **Switchboard / HAL** | ROS transport, hardware abstraction | Given an *already-chosen* backend, route the call, retry, load-balance, fail over | **Exists** — LiteLLM, stage 10 |
| **Dispatcher / router** | Behavior tree (hand-coded) | Classify the request by explicit rules, pick the backend, sequence a fixed pipeline if needed, integrate | **To build — plain scripted Python, no LLM** |

**LiteLLM does not decompose or capability-route.** It dispatches by an explicit
`model_name` the caller already picked, plus load-balancing and fallback. The "sandwich"
(input → classify → route to specialists → integrate → output) needs a thin dispatch
layer **above** LiteLLM — but that layer is **deterministic scripted Python, not an
LLM.** This is deliberate: a rule-based switch is debuggable, free, and keeps all
nondeterminism out of the control plane (no AI making the routing call). Today a human
does this by picking a model in Open WebUI; the build replaces the human with a **rule
table, not another model**. The routing decision is `if/elif` (or a dict dispatch), not
inference.

> **Terminology correction for anyone briefing on this:** **MCP = Model Context
> Protocol** (Anthropic's open standard for connecting models to tools/data) — *not*
> "Multi-Connector Protocol." It is a tool-connection standard, not the router itself.
> The router here is plain OpenAI-compatible HTTP (LiteLLM); MCP is one possible way the
> *dispatcher* attaches tools, not a synonym for the routing layer.

---

## 1. Control flow — the "sandwich"

```
   the laptop is a THIN CLIENT — browser only, zero local inference, zero heat
        │
        ▼
   ai.home.lan:4040  ── OpenAI-compatible front door (LiteLLM, on the t630) ──┐
        │                                                                     │
        ▼                                                                     │
   ┌─────────────────────────────────────────────────────────────────────┐   │
   │ DISPATCHER (to build) — deterministic Python, NO LLM in this box     │   │
   │   1. classify by explicit rules (task type / keyword / path)         │   │
   │   2. dispatch to a specialist (or run a fixed, scripted pipeline)     │   │
   │   3. integrate partial results into one answer                       │   │
   └───────────────┬───────────────┬───────────────┬─────────────────────┘   │
                   ▼               ▼               ▼                          │
              cloud-explore    cloud-code      cloud-vision   …      ◄─────────┘
              (wide-angle)     (build/code)    (understand     routed as whole
                                               images)         models, never sharded
```

**Invariant — "route, don't shard"** (inherited from `README.md`): never split one model
across machines. Each specialist is a whole model behind one endpoint; the dispatcher
routes *between* them. This is buildable and heals on node loss; sharding does not.

---

## 2. Specialist catalog (capability-based, provider-pluggable)

Tiers are named by **capability**, not by vendor, so a backend can be swapped without
touching callers. Candidate backends are listed; the **hosting decision is open** (§4).

> **The dispatcher is not a tier.** It's the scripted Python that *chooses* a tier (§3) —
> no model sits in the routing decision. Don't burn an LLM (local or cloud) on "which
> backend"; that's a rule table.

| Tier | Role (your words) | Candidate backend(s) | Notes |
| ---- | ----------------- | -------------------- | ----- |
| `cloud-explore` | Wide-angle exploration, research, hypothesis | `claude-opus-4-8` (1M ctx, ~$5/$25) **or** self-hosted full DeepSeek-R1 | Deepest reasoning + largest context for divergent search. |
| `cloud-code` | Precise execution, code synthesis, structured impl, diffs vs GitHub | `claude-sonnet-4-6` (1M, ~$3/$15), escalate to `claude-opus-4-8` | Sonnet 4.6 is the speed/intelligence sweet spot for code; Opus for the hardest. |
| `cloud-vision` | Visual **understanding** — read a screenshot / chart / schematic | `claude-opus-4-8` (high-res image *input*; Opus 4.7+ supports up to 2576px long edge) | Vision **input** only — see the correction below. |
| `cloud-gpu-reason` | Heavy self-hosted reasoning | full DeepSeek-R1 on a rented GPU over Tailscale | **Already wired** in `config.yaml`. |
| `local-fast` / `local-smart` | Snappy local chat | `qwen2.5:3b` / `:7b` on the t630 | Already in `config.yaml`; keep for laptop-free quick turns. |

> **Vision correction (important for the engineer).** "Vision models for generating
> diagrams/charts" bundles two *different* capabilities:
> - **Image understanding** (read a chart/screenshot and reason about it) → a
>   vision-capable model, e.g. `cloud-vision` above. This is vision **input**.
> - **Diagram/chart generation** → there is no "vision model" for this. Text models
>   (Claude, DeepSeek) emit **Mermaid / SVG / a matplotlib script**, which a renderer
>   turns into the picture. Route diagram *generation* to `cloud-code`, not a vision
>   tier. True raster image generation (a diffusion model) is a *separate service* and
>   is out of scope unless explicitly added — don't promise it from this stack.

Current Claude model IDs (verify against the API's `/v1/models` at build time):
`claude-opus-4-8`, `claude-sonnet-4-6`, `claude-haiku-4-5`.

---

## 3. What exists today vs. what to build

**Exists (the substrate):**
- LiteLLM front door at `ai.home.lan:4040`, OpenAI-compatible, host-net on the t630.
- Open WebUI at `chat.home.lan:3000` (manual model picker = today's "human supervisor").
- Whole-model backends + fallback map in `config.yaml` (`local-*`, `cloud-overflow`,
  `cloud-gpu-reason`).
- UFW gating 4040/3000 to LAN + WireGuard; Unbound names; CAKE shaping egress.

**To build (the dispatcher):** a deterministic Python script in front of LiteLLM that
classifies → dispatches → integrates. It calls the *same* OpenAI-compatible front door,
so it inherits routing, retries, and failover for free. It is **plain code, not an
agent**:
- **Core (v1):** stdlib + an OpenAI-compatible client (`openai` / `httpx`) pointed at
  `ai.home.lan:4040`. A dict / `if-elif` table maps task-type → `model_name`. Multi-step
  jobs are an **explicit, fixed sequence of calls**, not an LLM deciding the steps.
- **Optional later — now built:** LangGraph / LlamaIndex *only* if you outgrow a flat
  script and want stateful multi-step graphs. This is realized in
  [`langgraph-router/`](langgraph-router/): an LLM **supervisor** that plans a multi-step
  workflow, recruits capability tiers as workers, keeps state (SQLite resume), and
  integrates the results. Crucially it does **not** reopen the decided invariant below —
  the privacy *route* is still chosen by deterministic `classify()` before any LLM runs;
  the LLM only plans the *workflow*. Reach for it when a fixed scripted pipeline isn't
  enough; the flat `dispatcher.py` remains the default for simple, single-shot routing.
- **Not for v1:** an LLM-driven agent loop (Agent SDK / Managed Agents). That
  re-introduces the nondeterminism and token cost a scripted switch exists to avoid.

A runnable starting point is committed alongside this doc:
[`dispatcher.py`](dispatcher.py) — pure `classify()` rule table (token-matched, not
substring), a single-front-door `call_model()`, the privacy lock (`sensitive` →
local-only, `allow_cloud=False`), a fixed two-step `research_then_build()` pipeline, an
opt-in reflection log (`LLM_ROUTER_LOG=path` → JSONL, one line per route; privacy-locked
tasks are redacted so the audit trail never leaks what the lock protected), and an inline
`_selftest()`. Zero pip deps; `python3 dispatcher.py` dry-runs the routing.

---

## 4. Decisions

**Decided — do not re-open:**

- **The dispatcher is deterministic scripted Python. No LLM in the routing decision.**
  A rule table (task-type / keyword / path → `model_name`) and fixed call sequences for
  multi-step jobs. Chosen for determinism (same input → same route), zero token cost on
  routing, and debuggability. No agent loop, no LLM classifier, no Agent SDK for v1.
  *Scope note:* the `langgraph-router/` supervisor (above) layers an LLM **planner** on
  top for stateful multi-step jobs, but the **privacy route stays deterministic** —
  `classify()` pins a sensitive task local before the planner runs, so this decision
  holds for the part it was made about (the privacy boundary), not the workflow plan.

**Still open — for the engineer to resolve:**

1. **Where the heavy specialists run** — decision matrix:

   | Option | Pros | Cons |
   | ------ | ---- | ---- |
   | **Cloud Claude** (explore=Opus 4.8, code=Sonnet 4.6) | Highest ceiling; nothing to operate | Per-token cost; prompts leave the network |
   | **Self-hosted on rented GPU** (DeepSeek-R1 etc.) | Data stays on infra you control; flat hourly | Lower ceiling than frontier Claude; you operate the pod |
   | **Hybrid** | Self-hosted reasoning + cloud code/overflow | Two paths to keep healthy |

   The repo already leans hybrid (local + rented-GPU + `cloud-overflow`). Pick per tier;
   each tier is one `model:` line in `config.yaml`.

2. **Privacy boundary** — `cloud-overflow` and any `cloud-*` Claude tier send the prompt
   to a third party. If a class of task must stay self-hosted, the rule table must route
   it only to local / rented-GPU tiers and **must not** carry a cloud fallback. This is a
   line in the Python switch, not a hope.

3. **Tool attachment** — if the dispatcher needs tools (web, GitHub diffs, file ops), the
   script calls them directly as Python functions; reach for MCP only if you want a
   standard tool interface. Credentials in `.env` — never in prompts or committed.

---

## 5. Build phases

Phases are presented **last-first** per the repo house style; **execute by phase number,
1 → 4.** Each phase is shippable on its own.

### Phase 4 — Dispatch + integrate (the sandwich closes)

1. Wrap the rule table in the Python dispatcher in front of `ai.home.lan:4040`.
2. Implement classify → dispatch → integrate; specialists are `model_name`s from §2.
   Multi-step jobs are an explicit, fixed sequence of calls — not an LLM choosing steps.
3. Enforce the privacy routing rule (§4) and any budget caps.

### Phase 3 — Routing rules

1. Write the deterministic rule table (task-type / keyword / path → `model_name`) in
   plain Python. No LLM in this decision.
2. Expose it as one logical entry point (e.g. an `auto` endpoint, or a CLI / function)
   that internally dispatches to a tier.

### Phase 2 — Specialist catalog

1. Add the §2 tiers to `config.yaml` as whole-model backends (capability-named).
2. Wire fallbacks so each tier degrades sensibly (mirror the existing reasoning-ladder
   fallbacks; respect the privacy rule — sensitive tiers fail closed, not to cloud).
3. Resolve §4.1 (hosting) enough to fill each tier's `model:` + `api_base:`.

### Phase 1 — Thin-client baseline (mostly done)

1. Confirm the laptop runs **no local inference** — browser → `chat.home.lan:3000` only.
2. Confirm the rented-GPU `cloud-gpu-reason` path works end to end (README Block 4).
3. This alone solves the original heat/compute problem; everything above is capability,
   not thermal relief.

---

## 6. Interfaces & contracts

- **One front door.** Everything (UI, scripts, the dispatcher itself) speaks the
  OpenAI-compatible API at `ai.home.lan:4040`. Specialists are `model` names; swapping a
  backend never changes a caller.
- **Whole models only.** Each backend serves a complete model (`README.md` →
  "Route, don't shard").
- **Rented GPU reachability.** Tunnel only (Tailscale `100.x.y.z`), never a public IP —
  Ollama has no auth (`README.md` → Block 2).
- **Secrets.** `LITELLM_MASTER_KEY`, `ANTHROPIC_API_KEY` in `~/llm-router/.env`
  (git-ignored). Never inline keys; never put them in prompts (they persist in history).
- **Network posture.** UFW gates 4040/3000 to LAN + WG; the dispatcher, if it runs on
  the t630, sits behind the same gate.

---

## 7. References

- `10-ai-orchestration/README.md` — the switchboard + rented-GPU offload (the substrate).
- `10-ai-orchestration/config.yaml` — current backends + fallback map.
- `CLAUDE.md` → Known issues — the DeepSeek heat entry that started this.
- Robotics framing this mirrors: offboard heavy compute (planning/SLAM) while keeping
  real-time control on-device — here, keep coordination cheap/local, offload heavy
  inference to cloud or a rented GPU.
