# Odin — the supervisor that musters the host *(alias: Lionheart)*

**Odin** sits the high seat (Hlidskjalf) and sees all worlds: he plans a multi-step
campaign, musters the **host** he needs, carries state across steps, and integrates their
reports into one answer. He sits *above* the LiteLLM front door — the realized **"optional
later" path the [`../ORCHESTRATION-BLUEPRINT.md`](../ORCHESTRATION-BLUEPRINT.md) named**
(§3): reach for LangGraph only once a flat scripted pipeline isn't enough and you want
stateful multi-step graphs.

## The mythos *is* the architecture

The Norse map onto the privacy boundary so cleanly it's almost cheating:

| Lore | System | Guarded by |
| ---- | ------ | ---------- |
| **Asgard** — the keep | The AI fortress we're building. Local, on the t630, inside the walls. Nothing here leaks. | the Vanguard |
| **Midgard** — the mortal realm | Our **clients / customers** (the households). | the Crossing Guards |
| **Jotunheim** — enemy territory | The **cloud** — where a third party could see the traffic. | (ridden to by the Avant-Garde) |
| **Bifröst** — the rainbow bridge | The **WireGuard VPN** (`wg0`, stage 05): the encrypted crossing into the keep. | **Heimdall** |

**Heimdall** is the **Gatekeeper**: a deterministic guard at the Bifröst who decides who may
cross. *No LLM makes that call.* So "going behind enemy lines" = riding to Jotunheim (the
cloud), and **Heimdall holds the bridge** — exactly the decided invariant *"no LLM decides
the privacy route."*

> **Chronikonomicon:** **Muninn** / the Chronicler keeps the record — the natural bridge to
> that lore. This repo references the hook; it does not invent the canon.

---

## The host — three orders of five, and one bound adversary

Each member is autonomous; the chorus is the point — they guard **each other** and the
human. Two orders supply the **workers Odin musters** (real model tiers in `../config.yaml`);
the **Vanguard** is the deterministic guard around Odin himself (code paths, not tiers).

### the Vanguard — guard Odin / the keep
| Member | Is | Status |
| ------ | -- | ------ |
| **Heimdall** | the Gatekeeper — privacy classify at the Bifröst | built (`gatekeeper()`) |
| **the Warden** | enforces the lock (cloud→local rewrite) **and binds Loki** | built (`parse_plan()`) |
| **the Norn** | the step/loop cap — cuts the thread before it runs away | built (`MAX_STEPS`) |
| **Muninn** (Memory) | the audit log / the record | built (`dispatcher.reflect`) |
| **the Hoard-Warden** | a cloud-spend budget cap (`hoard.py`) — refuses a crossing the treasure can't afford, falls to local | built |

### the Crossing Guards — guard the allies (Midgard, the human)
| Member | Tier / role | Status |
| ------ | ----------- | ------ |
| **the Völva** | `local-reason` — light reasoning at the keep | built tier |
| **the Skald** | `local-smart` — a capable local hand | built tier |
| **the Húskarl** | `local-fast` — the quick household guard | built tier |
| **Huginn** (Thought) | read-only repo grounding (`tools.py`) | built |
| **Frigg** | PII/secret redaction at the cloud crossing (`frigg.py`) — she knows every fate, speaks none | built |

### the Avant-Garde — go behind enemy lines (Jotunheim) — the Valkyries
| Member | Tier | Status |
| ------ | ---- | ------ |
| **Göndul** | `cloud-explore` — wide recon, research | built tier |
| **Hildr** | `cloud-code` — forges code, diffs, diagrams | built tier |
| **Sigrún** | `cloud-vision` — reads the field (images) | built tier |
| **Brynhildr** | `cloud-gpu-reason` — heavy reasoning; rides far to the rented GPU but stays **sworn** (self-hosted over Tailscale, so allowed under a privacy lock) | built tier |
| **Skuld** | `cloud-overflow` — the fallback that is there when needed | built tier |

### Loki — the bound adversary
The irritant in the pearl. **Loki red-teams Odin's plan** to harden it, and when summoned
he **loops**: he critiques → Odin revises → he re-critiques, up to `LOKI_ROUNDS` (default 2)
or until the plan converges (he replies `SOUND`). But he is **bound by the Warden**: every
revision passes back through `parse_plan()`, so no round can widen `allow_cloud` or cross
the Bifröst, and the **Norn** still caps each plan's length. Opt-in (`LOKI=1`); bound (a
silent no-op hop) by default, so a normal run is unchanged and pays for no extra critique.
*In myth Loki is bound until Ragnarök; here, until you summon him — and even then, in chains.*

### The Mead — what Odin brews
At the end, Odin gathers the host's reports and brews them into one draught: the **Mead of
Poetry** (Óðrœrir) — *"our daily bread," the manna*. The brewed answer poured back to the
user **is the product**; `run()` returns it as `mead`. (Whoever drank the mead of myth spoke
as a poet or scholar — the metaphor for turning many raw reports into one wise reply.)

---

## Architecture — the graph

```
                              ┌─ loki ─┐ (critique→revise, ≤ LOKI_ROUNDS or converged)
                              ▼        │
task ─▶ Heimdall ─▶ muster ─▶ loki ────┘─▶ agent ─┐
        (privacy     (Odin     (bound      (a member│ loop until
         classify)    plans)    critic)     rides)  │ plan done
                                               ▲─────┘
                                               │
                                integrate (Odin) ─▶ the Mead (answer)
   (every cloud-bound call passes through Frigg [redaction] + the Hoard-Warden [spend cap])
```

- **Heimdall** — `classify()` from the dumb switch. Sets `allow_cloud`; forces a single
  local step for `sensitive`; fails closed to local if external (Huginn) context is attached.
- **muster** — Odin returns a JSON plan; the **Warden** (`parse_plan`) validates tiers,
  rewrites cloud→local under a lock, and the **Norn** caps the length.
- **loki** — if summoned, loops: critiques → Odin revises → re-critiques, each revision
  re-bound by the Warden, until convergence or `LOKI_ROUNDS`.
- **agent** — the mustered member rides through the one front door, carrying prior reports
  forward (the cross-step memory). **Frigg** scrubs every cloud-bound call.
- **integrate** — Odin brews the reports into one draught — **the Mead** (`run()` returns it
  as `mead`); stays local under a lock.

State is a `RouterState` dataclass; with `LLM_ROUTER_CHECKPOINT` set, a SQLite checkpointer
(Muninn's hoard) makes a long campaign **resumable by `thread_id`**.

---

## Privacy — Heimdall holds the Bifröst

The boundary is a **line of code, not a hope** (blueprint §4.2):

1. `sensitive` tasks (`bank`, `tax`, `password`, `medical`, …) are pinned local and Odin is
   skipped — the text never reaches a cloud supervisor.
2. Under `allow_cloud=False`, the Warden rewrites any cloud tier (Odin's **or Loki's**) down
   to local. No plan — not even the adversary's — can smuggle a step across the bridge.
3. Huginn's grounding forces local-only by default (private-repo content must not leak).
   Override only for public sources with `GITHUB_CONTEXT_ALLOW_CLOUD=1`.

`python3 supervisor.py --selftest` asserts all of the above — including that **Loki is
bound** — with no network and no `pip install`.

---

## Run it

> House-style walkthrough: blocks are presented **last-first**; execute by block number,
> **1 → 4**. Steps within a block run in order.

### Block 4 — Ride out (run the campaign)

1. Execute a task: `python3 supervisor.py --run "research X, then write a config diff"`.
2. Summon Loki to harden the plan: `LOKI=1 python3 supervisor.py --run "..."`.
3. Ground on a repo (Huginn): `run(task, context=tools.gather_context("a777ance/localDNS", "unbound DNS split"))`; resume a long run with `LLM_ROUTER_CHECKPOINT` + a stable `thread_id`.

### Block 3 — Point Odin at the front door

1. Confirm the tiers exist in `../config.yaml` (`cloud-explore`, `cloud-code`,
   `cloud-vision` were added alongside this; `local-*` already shipped).
2. Set `LLM_ROUTER_URL` + `LITELLM_MASTER_KEY` (same `.env` the switch uses).
3. Optional knobs: `GITHUB_TOKEN` (Huginn) · `SUPERVISOR_TIER` (crown Odin's brain) ·
   `LOKI=1` + `LOKI_ROUNDS` (summon the looping critic) · `FRIGG=0` (disable redaction; on by
   default) · `LLM_ROUTER_BUDGET_USD` (arm the Hoard-Warden; 0 = unlimited).

### Block 2 — Install deps (only to actually run the graph)

1. `python3 -m venv .venv && . .venv/bin/activate`
2. `pip install -r requirements.txt`

### Block 1 — Prove the safety logic (no deps, no network)

1. `python3 supervisor.py --selftest` — Heimdall, the Warden, Loki's binding + loop control, Frigg's crossing-guard, the Hoard-Warden's spend cap, the Norn, the roster.
2. `python3 supervisor.py --dry-run "summarize my bank statement"` — see the route without calling anything.
3. `python3 tools.py --selftest` (Huginn) · `python3 frigg.py --selftest` (redaction) · `python3 hoard.py --selftest` (spend cap).

---

## Honesty

Per the repo rule — *never print a capability the code doesn't have*:

- **Real today:** Heimdall, the Warden, the Norn, Muninn (the log), **Frigg (redaction)**,
  **the Hoard-Warden (spend cap)**, **Loki's binding + bounded loop**, the graph wiring,
  SQLite resume, and the 8 worker tiers (Crossing Guards + Avant-Garde). All testable offline
  via `--selftest`. Every roster seat is now real code or a live tier — no roadmap stubs left.
- **Real once you `pip install` + have a live front door:** the actual multi-step campaign,
  including Loki's critique→revise rounds (each round is two model calls).
- **NOT built:** a vector/embedding index over the repos (Huginn is fetch + keyword only —
  true RAG is the next step); any image *generation* (Sigrún *reads* images, she does not
  draw them — see the blueprint's vision note).
