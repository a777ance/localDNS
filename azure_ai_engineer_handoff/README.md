<!-- provenance: A · handoff brief supplied by the founder (Gemini-drafted), 2026-08-08 · 2026-08-08 · verify: confirm the employer's actual stack + roadmap on day 1 — nothing here has been observed against a real Azure tenant -->

# AI Engineer Environment & Context Handoff

## Project Overview

This directory serves as the initial context and workspace for a newly hired AI
Engineer. The goal is to quickly spin up on production engineering, MLOps, and
Azure-native AI deployments.

## Instructions for Claude Code

As an AI assistant operating in this workspace, your goal is to help the user
execute the 90-day roadmap detailed in [`docs/01_90_day_roadmap.md`](docs/01_90_day_roadmap.md)
using the technology stack defined in [`docs/02_azure_mlops_stack.md`](docs/02_azure_mlops_stack.md).

Prioritize clean software engineering, production-ready code, and Azure best
practices over theoretical model tuning. Whenever suggesting architectural
decisions, reference the Azure native stack.

## Layout

| Path | Holds |
| ---- | ----- |
| `tests/` | Test suite — a change is not done until it is covered here |
| `src/` | Application/model code — importable modules, not notebooks |
| `pipelines/` | Azure ML pipeline definitions (Python SDK v2) |
| `docs/` | The handoff briefs: roadmap and stack |
| `.env.example` | Placeholder config — copy to `.env` (git-ignored), never commit real values |

## Provenance

Everything in this directory is **`A` — asserted**: it is intent and plan, drafted
from a handoff brief, not read off a live Azure tenant. Nothing here has been
observed against real infrastructure. Before any of it drives a deploy, promote
it by first contact with the actual subscription, resource group, and workspace —
see [`docs/provenance.html`](../docs/provenance.html) for the ladder and its gates.
