# 10-ai-orchestration — a local-first LLM gateway on the t630

**Optional Step 12.** A LiteLLM router that puts one OpenAI-compatible front door
(`ai.home.lan:4040`) in front of whole-model backends — the local models running on
the t630 by default, with a cloud tier as failover/overflow — plus an **Open WebUI**
browser chat UI (`chat.home.lan:3000`) in front of that. It is the practical,
buildable version of the "let the network pick the best resource and adapt when a
machine drops" idea — **route between whole models, don't shard one model across
machines.**

This is an add-on layered on the finished core stack (README Steps 0–11). Nothing
here touches DNS resolution, the VPN, or QoS; it reuses them.

> **Looking to grow this into a multi-model "route each subtask to the best specialist"
> system?** The engineering design for that — the switchboard-vs-supervisor split, the
> capability-named specialist tiers, and the open hosting decisions — is in
> [`ORCHESTRATION-BLUEPRINT.md`](ORCHESTRATION-BLUEPRINT.md). This README is the
> switchboard it builds on.

```
        you (browser) ──► chat.home.lan:3000  Open WebUI ──┐
                                                           │  OpenAI API
        scripts / SDKs / apps ──► ai.home.lan:4040 ◄───────┘
                                       │  LiteLLM router (this stage, on the t630)
                                       │  picks a backend, retries, fails over
              ┌────────────────────────┼──────────────────────────┐
              ▼                         ▼                          ▼
        local-fast                 local-smart               cloud-overflow
      Ollama qwen2.5:3b          Ollama qwen2.5:7b       anthropic/claude-opus-4-8
        (t630, CPU)                (t630, CPU)             (failover only — $/token)
              └────── whole models, one per backend ──────┘
                    NOT one model split across machines

   plus a reasoning ladder (see "Offload heavy reasoning to a rented GPU"):
     local-reason      deepseek-r1:1.5b on the t630 CPU   (light, runs cool)
     cloud-gpu-reason  full DeepSeek-R1 on a rented GPU    (heavy, spin up on demand)
```

---

## Route, don't shard

The tempting idea is to pool every machine into one big model that auto-uses the best
RAM/GPU/CPU anywhere. With Ethernet between boxes that loses to physics: inference is
sequential and latency-bound — splitting one model's layers across two machines sends
activation state across the LAN for every token, and a gigabit hop is thousands of
times slower than the interconnect inside a single box. The split runs slower than the
best single machine alone, and yanking a node mid-generation fails rather than heals.

So this stage does the version that works: **one router in front of several
independent endpoints, each running a whole model.** You get ~80% of the felt
experience — "uses the best available resource, adapts when a machine goes away" — as
failover between whole endpoints, not migration of a split model. The mental model is
*route between models*, not *fuse machines into one model*.

## How it fits the existing stack

- **DNS names (Unbound).** [`../01-unbound/local-records.conf`](../01-unbound/local-records.conf)
  answers `ai.home.lan` (the API) and `chat.home.lan` (the UI) → `192.168.1.118`
  authoritatively, so every client has one stable address regardless of which backend
  serves the request. This is the right job for the resolver you already run.
- **Firewall (UFW).** [`../04-ufw/setup.sh`](../04-ufw/setup.sh) gates **4040** (API)
  and **3000** (UI) to the LAN and the WireGuard subnet — so VPN peers reach them on
  the tunnel, and the WAN never does.
- **QoS (CAKE).** CAKE shapes the *transport*, not the inference: if a request spills
  to the cloud tier, CAKE keeps that egress from saturating the link and wrecking
  latency for everything else. It does not make the network compute.

These make the network **addressable and well-behaved**, which is exactly what a
multi-endpoint router needs underneath it — they do not turn the network into a
cluster.

## Files

| File | Deploys to | Purpose |
| ---- | ---------- | ------- |
| [`docker-compose.yml`](docker-compose.yml) | `~/llm-router/docker-compose.yml` | `litellm` router (4040) + `open-webui` UI (3000), both host-net |
| [`config.yaml`](config.yaml) | `~/llm-router/config.yaml` | Backends + routing/failover rules |
| [`.env.example`](.env.example) | copy to `~/llm-router/.env` | `LITELLM_MASTER_KEY` + `ANTHROPIC_API_KEY` (git-ignored) |

Open WebUI keeps its state in `~/llm-router/open-webui-data/` (created at runtime,
git-ignored).

---

## Deploy

Blocks are presented **last-first** per the repo house style; **execute by block
number, 1 → 6.** The numbered steps *within* each block run in order.

### Block 6 — Verify & use

1. The UI: browse to `http://chat.home.lan:3000`, create the first account (it becomes
   the admin), then pick a model (`local-fast`, `local-smart`, `cloud-overflow`) and
   chat. All UI traffic goes through the router.
2. The API — health and catalogue (from any LAN/WG client; substitute your master key):
   ```bash
   curl http://ai.home.lan:4040/health \
     -H "Authorization: Bearer $LITELLM_MASTER_KEY"
   curl http://ai.home.lan:4040/v1/models \
     -H "Authorization: Bearer $LITELLM_MASTER_KEY"
   ```
3. A real completion against the fast local tier:
   ```bash
   curl http://ai.home.lan:4040/v1/chat/completions \
     -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"local-fast","messages":[{"role":"user","content":"say hi in five words"}]}'
   ```
4. Prove failover ("turn a laptop off"): `sudo systemctl stop ollama`, then call
   `local-smart` — the request should fall through to `cloud-overflow` (if a real
   `ANTHROPIC_API_KEY` is set) instead of erroring. `sudo systemctl start ollama` to
   restore.

### Block 5 — Name it (Unbound) · optional

1. Deploy the local records and reload Unbound:
   ```bash
   sudo cp 01-unbound/local-records.conf /etc/unbound/unbound.conf.d/local-records.conf
   sudo systemctl restart unbound
   ```
2. From another LAN/WG client (not the t630 itself — see the note in the conf file):
   ```bash
   dig ai.home.lan +short      # 192.168.1.118
   dig chat.home.lan +short    # 192.168.1.118
   ```
   Without this block, use the IP directly: `http://192.168.1.118:4040` (API) and
   `http://192.168.1.118:3000` (UI).

### Block 4 — Open the firewall (UFW)

1. Re-run the firewall script; it already includes the 4040 + 3000 LAN + WG rules:
   ```bash
   sudo bash 04-ufw/setup.sh
   sudo ufw status verbose | grep -E '4040|3000'   # expect LAN + 10.8.0.0/24, not Anywhere
   ```

### Block 3 — Launch (router + UI)

1. Stage the files and bring both services up (one compose file):
   ```bash
   mkdir -p ~/llm-router && cp 10-ai-orchestration/{docker-compose.yml,config.yaml} ~/llm-router/
   cd ~/llm-router && docker compose up -d
   docker logs -f llm-router        # watch LiteLLM load the config; Ctrl-C when healthy
   ```
2. First visit to `chat.home.lan:3000` creates the Open WebUI admin account — do it
   from a trusted device before exposing the UI to the whole household.

### Block 2 — Configure

1. Copy the env template and fill in real values (never commit `.env`):
   ```bash
   cp 10-ai-orchestration/.env.example ~/llm-router/.env
   nano ~/llm-router/.env           # set LITELLM_MASTER_KEY (start it "sk-…")
                                    # set ANTHROPIC_API_KEY, or leave CHANGE_ME for local-only
   ```
   Open WebUI reuses `LITELLM_MASTER_KEY` as its key to the router (compose
   interpolates it), so there's nothing extra to set for the UI.
2. Edit `config.yaml` so each `model_name` points at a tag you actually pulled in
   Block 1. The shipped defaults are `qwen2.5:3b` (fast) and `qwen2.5:7b` (smart).

### Block 1 — Install Ollama + pull models (on the t630)

1. Install Ollama as a host service (matches how this repo runs Unbound/WireGuard —
   host, not Docker; avoids GPU-passthrough complexity the Carrizo can't use anyway):
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```
2. Pull a small and a mid model:
   ```bash
   ollama pull qwen2.5:3b
   ollama pull qwen2.5:7b           # optional now: deepseek-r1:7b for reasoning
   ```
3. Confirm Ollama is listening on loopback (the router reaches it there):
   ```bash
   curl -s http://127.0.0.1:11434/api/tags | head
   ```
   Leave Ollama bound to `127.0.0.1` — the router is co-located, so it needs no LAN
   exposure. A *second* machine added as a backend runs its own Ollama on its own LAN
   IP; the router points at that (commented example in `config.yaml`).

---

## Offload heavy reasoning to a rented GPU (DeepSeek-R1)

A full DeepSeek-R1 model thinks out loud — it emits a long chain-of-thought before
the answer — so on a CPU it pins every core for minutes per prompt. Run that on a
laptop and the fans scream and the chassis cooks; run it on the t630 and it just
thermal-throttles and crawls. **So don't run the heavy reasoner on local CPU at all.**

This is the "GeForce Now for LLMs" pattern, and the router you already built *is* the
switch for it. The laptop stays a thin browser client (`chat.home.lan:3000`) and does
no inference; the t630 routes each request to the right backend:

```
   quick chat            → local-fast / local-smart   (qwen2.5 on the t630 CPU)
   light "show your work" → local-reason              (deepseek-r1:1.5b, t630 CPU, cool)
   heavy reasoning        → cloud-gpu-reason           (full DeepSeek-R1 on a rented GPU)
   pod is off / unset     → cloud-overflow             (Claude — graceful fallback)
```

The rented GPU is **rented, not always-on**: spin a pod up for a heavy session, stop
it when you're done. While it's stopped, `cloud-gpu-reason` is unreachable and the
router falls those requests over to `cloud-overflow` — so the catalogue never errors,
it just costs a Claude call until the pod is back.

Blocks are presented **last-first** per house style; **execute by block number, 1 → 4.**

### Block 4 — Use it, then stop the pod

1. In Open WebUI (`chat.home.lan:3000`) pick **cloud-gpu-reason** for a hard problem;
   pick **local-reason** for something light. Same front door, no client changes.
2. Confirm the router sees the backend (substitute your master key):
   ```bash
   curl -s http://ai.home.lan:4040/health \
     -H "Authorization: Bearer $LITELLM_MASTER_KEY" | grep -i reason
   ```
3. **Stop the pod when the session ends** — this is where the bill is. Rented GPUs are
   billed by the hour (marketplace/spot is cheapest; on-demand costs more but won't be
   interrupted — check the provider's *current* pricing, it moves). An idle pod still
   bills, so stop or terminate it; the router falls back to `cloud-overflow` meanwhile.

### Block 3 — Point the router at it

1. In `~/llm-router/config.yaml`, set `cloud-gpu-reason`'s `api_base` to the pod's
   **Tailscale IP** (the `100.x.y.z` from Block 2) and its `model:` to the tag you
   actually pulled (`deepseek-r1:32b`, `:70b`, …). Reload:
   ```bash
   cd ~/llm-router && docker compose up -d
   ```
2. There is **no API key** for an Ollama backend — access is gated by the tunnel, not a
   token. That is exactly why Block 2 keeps the pod off the public internet.

### Block 2 — Join it to the tunnel (never expose Ollama publicly)

1. Ollama has no authentication, so it must **never** listen on a public IP. Put the
   pod on a private tunnel instead — install Tailscale on it and join your tailnet:
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh && sudo tailscale up
   tailscale ip -4        # note the 100.x.y.z — this is what config.yaml points at
   ```
2. Bind Ollama to the tunnel (or to all interfaces *only* with the provider's public
   firewall closed): `OLLAMA_HOST=0.0.0.0:11434`. The t630 reaches it over Tailscale;
   the open internet cannot. This mirrors how the rest of this stack gates everything
   to the LAN + WG subnet — the GPU pod just joins that private surface.

### Block 1 — Rent the GPU + pull DeepSeek-R1

1. Rent an hourly GPU pod (Vast.ai is the cheapest marketplace; RunPod is more managed,
   with one-click Ollama templates). One modern data-centre GPU (A100/H100-class) holds
   the larger DeepSeek-R1 distills comfortably.
2. Install Ollama and pull the size you want the heavy tier to be:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama pull deepseek-r1:32b      # or :70b if the pod's VRAM allows
   ```
   Sized this way, the GPU — not your laptop — does the thinking, fast.

> **Privacy note.** Self-hosting on a rented pod keeps prompts off a SaaS provider's
> logs (better than sending the same data to a hosted chat API), but it is *your*
> server to secure — the tunnel in Block 2 is what makes that true. One sharp edge:
> both reasoning tiers list `cloud-overflow` as their final fallback, so when a local
> backend or the pod is unreachable, the prompt **does** go to Anthropic. If a task
> must never leave infra you control, keep the GPU pod up and call `cloud-gpu-reason`
> while it's healthy — don't rely on a tier whose fallback can silently reroute to the
> cloud. (To forbid that outright, drop the `cloud-overflow` entries from those tiers'
> `fallbacks` and they'll fail closed instead.)

---

## A note on speed — measure, don't trust this page

The honesty rule of this repo applies to performance too: this file prints no
tokens-per-second number, because the only honest number is the one you measure on the
box. The t630 is a 4-core AMD Carrizo (AVX2, no usable GPU offload for inference — old
GCN, ROCm unsupported; Vulkan offload is marginal and draws from the same RAM), so
everything runs on the CPU and is **memory-bandwidth bound**, not compute bound. A 3B
model is the one to start interactive; a 7B will run but is better for "submit and
wait" tasks. Time a known prompt and decide from that:

```bash
time curl -s http://127.0.0.1:11434/api/generate \
  -d '{"model":"qwen2.5:7b","prompt":"Write one sentence about DNS.","stream":false}' >/dev/null
```

The thing you actually get regardless of model size is **data control**: with the
cloud tier left unset, every request stays on your network. The cloud tier is there
for the tasks a CPU 7B can't carry — and it's one `model:` line to point elsewhere.

---

## Known limits & open items

*(newest first, per house style)*

- **Heavy DeepSeek-R1 belongs on a rented GPU, not local CPU.** An R1 reasoner pins
  every CPU core for minutes per prompt (the chain-of-thought) — that sustained load
  is what overheats a laptop and throttles the t630. The reasoning ladder splits it:
  `local-reason` (deepseek-r1:1.5b, t630 CPU, cool) for light work, `cloud-gpu-reason`
  (full R1 on a rented GPU over a Tailscale tunnel) for heavy work, spun up on demand.
  See "Offload heavy reasoning to a rented GPU." The laptop stays a thin browser client.
- **Open WebUI: first user is admin; UI is on 3000, not 8080.** Create the admin
  account from a trusted device before opening it to the household. 8080 is already the
  Pi-hole UI on this box, so the chat UI uses 3000. State lives in
  `~/llm-router/open-webui-data/`.
- **Local-only by default is fail-closed, not silent local.** With `ANTHROPIC_API_KEY`
  left as `CHANGE_ME`, a request that falls through to `cloud-overflow` errors rather
  than leaking — intended, but worth knowing when a `local-*` call returns an auth
  error after the local backend went down.
- **No model is sharded.** By design. If you want a model bigger than one box can hold,
  that's a bigger-single-box (or rented-GPU) decision, not a "pool the LAN" one.
- **CPU-bound throughput.** 7B on the Carrizo is usable for async work, sluggish for
  back-and-forth chat. Reach for `local-fast` (3B) when latency matters.
- **No virtual keys / budgets.** LiteLLM runs config-only (no Postgres); per-user keys
  and spend caps would need a database — out of scope for the lean homelab default.
- **Port 4040, not 4000.** LiteLLM defaults to 4000; NoMachine holds 4000 on this box.
  4040 is the router here, gated to LAN + WG by UFW.
