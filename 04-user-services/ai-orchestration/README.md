# AI orchestration — the LLM router (route, not shard)

<!-- provenance: R · rebuilt from CLAUDE.md + docs/architecture/network-context.md "Step 12. LLM router" · 2026-08-07 · verify: docs/DEPLOY-QUEUE.md Stage 12 — pin model IDs and the Tailscale host on the box -->

> **Front door reconstructed from documentation, not yet verified against the live
> box.** `docker-compose.yml`, `config.yaml`, and `.env.example` are rebuilt from
> CLAUDE.md and `docs/architecture/network-context.md` "Step 12". Pin the model IDs
> and the Tailscale GPU address, then confirm on the t630 before trusting this as a
> rollback target.
>
> **Still NOT snapshotted — deliberately not fabricated here:** the
> `langgraph-router/` "Odin" supervisor (LangGraph multi-agent graph, `odin` CLI,
> `dispatcher.py`, the juror/critic roster). It is described as design-and-self-
> tested in `docs/ai-cto/context.md`, but its code is a whole subsystem — inventing
> it from the lore prose would be fiction dressed as a rollback target. Snapshot it
> from the live box (or wherever it was authored) rather than from memory. The
> `jury/` and `jury-claude/` voters that DO live here are the sampling-doctrine
> tools (CLAUDE.md §G), not the Odin router.

One OpenAI-compatible endpoint for the whole household, routing to whole-model
backends. LiteLLM is the router; Open WebUI is the browser front-end.

## What runs

| Piece | Container | Port | Name |
| ----- | --------- | ---- | ---- |
| LiteLLM router | `litellm` | 4040 | `ai.home.lan:4040` |
| Open WebUI (chat) | `open-webui` | 3000 | `chat.home.lan:3000` |

Both `network_mode: host` (reach a co-located Ollama at `127.0.0.1:11434`
directly, and let UFW gate the ports). **4040, not 4000** — NoMachine owns 4000.
**3000, not 8080** — 8080 is the Pi-hole UI. Names come from
`01-core-network/unbound/local-records.conf`.

## Route, not shard

Pooling machines into one auto-balancing model loses to physics over Ethernet:
inference is sequential and latency-bound, and splitting a model's layers pushes
activation state across the LAN for every token (a gigabit hop is thousands of
times slower than the interconnect inside one box). So one router in front of
several **whole**-model endpoints — health-checked failover, not migration — is the
design. See `docs/architecture/network-context.md` "Step 12" for the full argument.

## The reasoning ladder

`config.yaml` encodes it as a fallbacks map: light work stays local
(`local-fast`, `local-reason` = deepseek-r1:1.5b, cool on the t630 CPU), heavy
reasoning climbs to a rented GPU pod over Tailscale (`cloud-gpu-reason` = full R1),
then spills to the Anthropic cloud tier (`cloud-overflow` / `cloud-explore` /
`cloud-code` / `cloud-vision`) when the pod is off. **Never run deepseek-r1:7b+ on
the t630 CPU** — its long chain-of-thought pins every core for minutes.

## Deploy

```bash
mkdir -p ~/llm-router && cd ~/llm-router
cp /path/to/repo/04-user-services/ai-orchestration/{docker-compose.yml,config.yaml} .
cp /path/to/repo/04-user-services/ai-orchestration/.env.example .env
editor .env            # set LITELLM_MASTER_KEY; set ANTHROPIC_API_KEY only for overflow
editor config.yaml     # pin model IDs + the Tailscale GPU host
docker compose up -d
sudo bash /path/to/repo/01-core-network/ufw/setup.sh   # gate 4040 + 3000 to LAN + WG
```

Verify: `curl -s http://127.0.0.1:4040/v1/models -H "Authorization: Bearer $LITELLM_MASTER_KEY"`
lists the tiers; `chat.home.lan:3000` loads the UI (first account = admin, create
it from a trusted device).

## Honesty on performance

The t630 is CPU-only for local models (Carrizo iGPU: old GCN, ROCm unsupported).
Throughput is memory-bandwidth bound — no tokens/sec figure is recorded here on
purpose; measure it on the box (`time` a request). Start interactive on a 3B; treat
7B as submit-and-wait. The durable win at any size is data control: with the cloud
key unset, every request stays on your network and overflow calls fail closed.
