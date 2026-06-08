# LangGraph supervisor — the LLM-planned, stateful layer

A multi-agent **supervisor** that sits *above* the LiteLLM front door: it plans a
multi-step workflow, recruits capability tiers (reasoning / code / explore / vision /
local) as workers, carries state across steps, and integrates their outputs into one
answer. This is the **"optional later" path the [`../ORCHESTRATION-BLUEPRINT.md`](../ORCHESTRATION-BLUEPRINT.md)
named** (§3): reach for LangGraph only once a flat scripted pipeline isn't enough and you
want stateful multi-step graphs. That's now.

---

## Contents

- [Read this first — what it does and does NOT change](#read-this-first)
- [Architecture — the graph](#architecture)
- [The privacy invariant (non-negotiable)](#privacy)
- [Files](#files)
- [Run it](#run-it)
- [Honesty: what's real today vs. not built](#honesty)

---

## Read this first

The blueprint marks one thing **decided, do-not-reopen**: *"no LLM decides the privacy
route."* This component does **not** reopen that. The split:

| Decision | Who makes it | Where |
| -------- | ------------ | ----- |
| **The privacy route** (does this task leave the network?) | **Deterministic Python.** `dispatcher.classify()` runs *first*, before any LLM. A `sensitive` task is pinned to a local tier and the supervisor never sees it. | `supervisor.gate()` |
| **The plan** (which specialists, in what order, how to combine) | **The LLM supervisor.** This is the genuinely new capability over `../dispatcher.py`. | `supervisor.make_planner()` |

So the LLM plans; it can never overrule the privacy lock. Everything still flows through
the **one front door** (`ai.home.lan:4040`) via `dispatcher.call_model()` — same retries,
failover, and "route, don't shard" as the dumb switch. The supervisor is orchestration,
not a second router.

> **Hardware reality check.** The t630 is a **4-core / 16 GB** box — it *cannot* host a
> 27B/32B planning brain (a common suggestion). `SUPERVISOR_TIER` defaults to
> `local-smart` (qwen2.5:7b, cheap local planning); point it at `cloud-explore` or the
> rented-GPU tier when you want a heavier brain. Heavy weights never land on the t630 CPU
> — that's the whole reason this stack exists (see `../README.md`, the DeepSeek-heat note).

---

## Architecture

```
task ─▶ gate ─────────────────────────────────────────────────▶ plan ─▶ worker ─┐
        (deterministic privacy classify;                         (LLM)    (tier   │ loop until
         sensitive ⇒ pinned local, planner skipped)                       call)   │ plan done
                                                                    ▲──────────────┘
                                                                    │
                                                              integrate (LLM) ─▶ answer
```

- **gate** — `classify()` from the dumb switch. Sets `allow_cloud`; forces a single local
  step for `sensitive`; fails closed to local if external (e.g. GitHub) context is attached.
- **plan** — the supervisor LLM returns a JSON plan; `parse_plan()` validates every tier
  against an allowlist, rewrites any cloud step to local under a privacy lock, and caps the
  step count (runaway protection). Unparseable output degrades to one deterministic step.
- **worker** — executes the step at the cursor through the front door, carrying prior
  results forward (the cross-step "memory").
- **integrate** — synthesizes the partials into one reply (stays local under a lock).

State is a `RouterState` dataclass; with `LLM_ROUTER_CHECKPOINT` set, a SQLite checkpointer
makes a long run **resumable by `thread_id`**.

---

## Privacy

The boundary is a **line of code, not a hope** (inherited from the blueprint §4.2):

1. `sensitive` tasks (`bank`, `tax`, `password`, `medical`, …) are pinned to a local tier
   and the planner is skipped — the text never reaches a cloud supervisor.
2. Under `allow_cloud=False`, `parse_plan()` rewrites any cloud tier the LLM proposes down
   to a local one. The plan **cannot** smuggle a sensitive step to the cloud.
3. Attaching GitHub context forces local-only by default (private-repo content must not
   leak). Override only for public sources with `GITHUB_CONTEXT_ALLOW_CLOUD=1`.

`python3 supervisor.py --selftest` asserts all three with no network and no `pip install`.

---

## Files

- `supervisor.py` — the graph: gate → plan → worker(loop) → integrate. Deterministic parts
  run on stdlib; LangGraph is imported lazily.
- `tools.py` — read-only GitHub grounding (fetch + keyword snippet). No vector store.
- `requirements.txt` — `langgraph` (+ optional SQLite checkpointer). Nothing else.

---

## Run it

> House-style walkthrough: blocks are presented **last-first**; execute by block number,
> **1 → 4**. Steps within a block run in order.

### Block 4 — Run the graph

1. Execute a task: `python3 supervisor.py --run "research X, then write a config diff"`.
2. Ground it on a repo first if useful — in Python: `run(task, context=tools.gather_context("a777ance/localDNS", "unbound DNS split"))`.
3. For a resumable session, set `LLM_ROUTER_CHECKPOINT=~/llm-router/router.sqlite` and pass a stable `thread_id`.

### Block 3 — Point it at the front door

1. Confirm the tiers exist in `../config.yaml` (`cloud-explore`, `cloud-code`,
   `cloud-vision` were added alongside this; `local-*` already shipped).
2. Set `LLM_ROUTER_URL` + `LITELLM_MASTER_KEY` (same `.env` the switch uses).
3. Optional: `GITHUB_TOKEN` (read-only PAT) for grounding; `SUPERVISOR_TIER` to pick the brain.

### Block 2 — Install deps (only to actually run the graph)

1. `python3 -m venv .venv && . .venv/bin/activate`
2. `pip install -r requirements.txt`

### Block 1 — Prove the safety logic (no deps, no network)

1. `python3 supervisor.py --selftest` — privacy gate, plan validation, step cap.
2. `python3 supervisor.py --dry-run "summarize my bank statement"` — see the route without calling anything.
3. `python3 tools.py --selftest` — grounding snippet logic.

---

## Honesty

Per the repo rule — *never print a capability the code doesn't have*:

- **Real today:** the deterministic gate, plan validation, the privacy lock, the step cap,
  the graph wiring, and SQLite resume. All testable offline via `--selftest`.
- **Real once you `pip install` + have a live front door:** the actual multi-step run.
- **NOT built:** a vector/embedding index over the repos (`tools.py` is fetch + keyword
  only — true RAG is the next step, not a current claim); any image *generation* tier
  (`cloud-vision` reads images, it does not draw them — see the blueprint's vision note).
