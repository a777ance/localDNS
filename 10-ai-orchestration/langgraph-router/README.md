# Lionheart — the LLM-planned supervisor that musters the Paladins

**Lionheart** is the multi-agent **supervisor** that sits *above* the LiteLLM front door:
it plans a multi-step workflow, musters the capability tiers it needs (the **Paladins** —
reasoning / code / explore / vision / local), carries state across steps, and synthesizes
their reports into one answer. This is the **"optional later" path the
[`../ORCHESTRATION-BLUEPRINT.md`](../ORCHESTRATION-BLUEPRINT.md) named** (§3): reach for
LangGraph only once a flat scripted pipeline isn't enough and you want stateful multi-step
graphs. That's now.

> **The cast** (crusader-era command structure, made literal — Paladins in the *Song of
> Roland* sense, Charlemagne's Twelve Peers, **not** the tabletop class):
> | Name | Is | Does |
> | ---- | -- | ---- |
> | **Lionheart** | the supervisor LLM | plans the campaign, musters Paladins, unites their reports |
> | **the Gatekeeper** | a deterministic guard (no LLM) | rules on privacy *before* Lionheart sees the task |
> | **the Paladins** | the capability tiers | each a champion sworn to one craft (see the roster below) |

---

## Contents

- [Read this first — what it does and does NOT change](#read-this-first)
- [Architecture — the graph](#architecture)
- [The Paladin roster](#the-paladin-roster)
- [The privacy invariant (non-negotiable)](#privacy)
- [Files](#files)
- [Run it](#run-it)
- [Honesty: what's real today vs. not built](#honesty)

---

## Read this first

The blueprint marks one thing **decided, do-not-reopen**: *"no LLM decides the privacy
route."* Lionheart does **not** reopen that. The split:

| Decision | Who makes it | Where |
| -------- | ------------ | ----- |
| **The privacy route** (does this task leave the network?) | **The Gatekeeper — deterministic Python.** `dispatcher.classify()` runs *first*, before any LLM. A `sensitive` task is pinned to a local tier and Lionheart never sees it. | `supervisor.gatekeeper()` |
| **The plan** (which Paladins, in what order, how to combine) | **Lionheart — the LLM.** This is the genuinely new capability over `../dispatcher.py`. | `supervisor.make_muster()` |

So Lionheart plans; it can never overrule the Gatekeeper. Everything still flows through
the **one front door** (`ai.home.lan:4040`) via `dispatcher.call_model()` — same retries,
failover, and "route, don't shard" as the dumb switch. Lionheart is orchestration, not a
second router.

> **Hardware reality check.** The t630 is a **4-core / 16 GB** box — it *cannot* host a
> 27B/32B Lionheart (a common suggestion). `SUPERVISOR_TIER` defaults to `local-smart`
> (qwen2.5:7b, cheap local planning); crown a heavier brain by pointing it at
> `cloud-explore` or the rented-GPU tier. Heavy weights never land on the t630 CPU — that's
> the whole reason this stack exists (see `../README.md`, the DeepSeek-heat note).

---

## Architecture

```
task ─▶ Gatekeeper ──────────────────────────────────────▶ muster ─▶ paladin ─┐
        (deterministic privacy classify;                   (Lionheart  (a tier  │ loop until
         sensitive ⇒ pinned local, muster skipped)          plans)      rides)  │ plan done
                                                                 ▲───────────────┘
                                                                 │
                                                  integrate (Lionheart) ─▶ answer
```

- **Gatekeeper** — `classify()` from the dumb switch. Sets `allow_cloud`; forces a single
  local step for `sensitive`; fails closed to local if external (e.g. GitHub) context is attached.
- **muster** — Lionheart returns a JSON plan; `parse_plan()` validates every tier against an
  allowlist, rewrites any cloud step to local under a privacy lock, and caps the step count
  (runaway protection). Unparseable output degrades to one deterministic step.
- **paladin** — the mustered tier rides: executes the step at the cursor through the front
  door, carrying prior reports forward (the cross-step "memory").
- **integrate** — Lionheart unites the reports into one reply (stays local under a lock).

State is a `RouterState` dataclass; with `LLM_ROUTER_CHECKPOINT` set, a SQLite checkpointer
makes a long campaign **resumable by `thread_id`**.

---

## The Paladin roster

Each capability tier is a champion sworn to one craft. The epithets are flavor for the
trace/logs; the functional name is always the tier string (in `config.yaml`).

| Paladin | Tier | Craft |
| ------- | ---- | ----- |
| **the Scout** | `cloud-explore` | rides wide — research, reconnaissance, hypotheses |
| **the Sage** | `cloud-gpu-reason` | heavy step-by-step reasoning (off on the rented GPU) |
| **the Watchman** | `cloud-vision` | reads the field — screenshots, charts, scans (input only) |
| **the Squire** | `local-smart` | a capable local hand (qwen2.5:7b) |
| **the Page** | `local-fast` | the quickest, lightest local turn |
| **the Friar** | `local-reason` | light reasoning at the keep — runs cool on the t630 |
| **the Armorer** | `cloud-code` | forges the work — code, diffs, diagrams |

---

## Privacy

The boundary is a **line of code, not a hope** (inherited from the blueprint §4.2). The
Gatekeeper holds it:

1. `sensitive` tasks (`bank`, `tax`, `password`, `medical`, …) are pinned to a local tier
   and the muster is skipped — the text never reaches a cloud Lionheart.
2. Under `allow_cloud=False`, `parse_plan()` rewrites any cloud tier Lionheart proposes down
   to a local one. The plan **cannot** smuggle a sensitive step to the cloud.
3. Attaching GitHub context forces local-only by default (private-repo content must not
   leak). Override only for public sources with `GITHUB_CONTEXT_ALLOW_CLOUD=1`.

`python3 supervisor.py --selftest` asserts all three with no network and no `pip install`.

---

## Files

- `supervisor.py` — Lionheart: Gatekeeper → muster → paladin(loop) → integrate.
  Deterministic parts run on stdlib; LangGraph is imported lazily.
- `tools.py` — read-only GitHub grounding (fetch + keyword snippet). No vector store.
- `requirements.txt` — `langgraph` (+ optional SQLite checkpointer). Nothing else.

---

## Run it

> House-style walkthrough: blocks are presented **last-first**; execute by block number,
> **1 → 4**. Steps within a block run in order.

### Block 4 — Ride out (run the campaign)

1. Execute a task: `python3 supervisor.py --run "research X, then write a config diff"`.
2. Ground it on a repo first if useful — in Python: `run(task, context=tools.gather_context("a777ance/localDNS", "unbound DNS split"))`.
3. For a resumable session, set `LLM_ROUTER_CHECKPOINT=~/llm-router/lionheart.sqlite` and pass a stable `thread_id`.

### Block 3 — Point Lionheart at the front door

1. Confirm the tiers exist in `../config.yaml` (`cloud-explore`, `cloud-code`,
   `cloud-vision` were added alongside this; `local-*` already shipped).
2. Set `LLM_ROUTER_URL` + `LITELLM_MASTER_KEY` (same `.env` the switch uses).
3. Optional: `GITHUB_TOKEN` (read-only PAT) for grounding; `SUPERVISOR_TIER` to crown the brain.

### Block 2 — Install deps (only to actually run the graph)

1. `python3 -m venv .venv && . .venv/bin/activate`
2. `pip install -r requirements.txt`

### Block 1 — Prove the safety logic (no deps, no network)

1. `python3 supervisor.py --selftest` — the Gatekeeper, plan validation, step cap, roster.
2. `python3 supervisor.py --dry-run "summarize my bank statement"` — see the route without calling anything.
3. `python3 tools.py --selftest` — grounding snippet logic.

---

## Honesty

Per the repo rule — *never print a capability the code doesn't have*:

- **Real today:** the Gatekeeper, plan validation, the privacy lock, the step cap, the graph
  wiring, and SQLite resume. All testable offline via `--selftest`.
- **Real once you `pip install` + have a live front door:** the actual multi-step campaign.
- **NOT built:** a vector/embedding index over the repos (`tools.py` is fetch + keyword
  only — true RAG is the next step, not a current claim); any image *generation* Paladin
  (the Watchman *reads* images, it does not draw them — see the blueprint's vision note).
