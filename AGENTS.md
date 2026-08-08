# AGENTS.md

Canonical briefing for any AI agent working in this repository.

This file is **agent-agnostic**. It is the repository-level operating contract for Claude, ChatGPT/Codex, local models, Odin, and other automated or human-assisted agents. Do not assume a particular model, vendor, SDK, or agent runtime.

`README.md` is the top-level map. `docs/architecture/network-context.md` contains rationale for non-obvious network decisions. `docs/ai-cto/context.md` contains current operational state and the pre-computed next-action queue. `CLAUDE.md` is retained for Claude Code compatibility; repository-wide rules belong here and should not be made Claude-specific.

---

## 1. Source of truth

- This repository is the public product/configuration snapshot and rollback target.
- The live HP t630 is the operational source of truth. Repository edits do **not** take effect until deliberately deployed.
- When documentation and the live system disagree, verify against the live system rather than inventing a value.
- Never fabricate a live configuration, measurement, deployment result, customer figure, or system state.
- If a fact has not been measured or verified, say so explicitly.

## 2. Public-repository boundary

- Business model, pricing, guild economics, and real customer data belong in separate private repositories.
- Never copy private business/customer data, credentials, or secrets into this repository.
- Keys, passwords, tokens, and other secrets belong in the sops+age vault or ignored `.env` files.
- Commit only `.env.example`, `CHANGE_ME`, templates, or sealed secret material intended for git.

## 3. House style

These conventions apply across A777ance repositories unless a more specific repository rule overrides them:

- Time-based content is newest-first (reverse chronological): logs, changelogs, decision records, known issues, issue trackers, FAQs, metrics, review logs, and "Handled For You" entries.
- Alphabetical lists run Z → A.
- Walkthroughs reverse the major blocks while preserving the numbered execution steps inside each block. Do not renumber existing steps or stages.
- Customer-facing Statements use plain English that a homeowner or grandparent can understand. Internal engineering documentation may use technical terminology.
- The visual typeface convention is Gill Sans MT, with the existing web fallback stack: `Gill Sans MT`, `Gill Sans`, Calibri, `Trebuchet MS`, sans-serif.

## 4. Deployment discipline

- Treat repository configuration as a declarative rollback target, not as proof that the live machine matches it.
- Use `docs/DEPLOY-PROTOCOL.md` for changes that land on the live system: synchronize, inspect the diff, back up, validate, reload, and verify the **effect**.
- Use `docs/DEPLOY-QUEUE.md` for staged deployment work and respect its stage ordering.
- Never claim deployment success without verifying the resulting service behavior.
- For reconstructed configuration, label it as reconstructed and verify it against the live host before trusting it.

## 5. DNS and network invariants

- Pi-hole forwards DNS to the local Unbound instance at `127.0.0.1#5335`; do not add competing public upstreams without an explicit architectural decision.
- Unbound is the DNS decision point. The streaming/low-sensitivity forwarding path uses encrypted DNS-over-TLS; sensitive/default traffic remains recursive with DNSSEC.
- Never place sensitive domains on the Cloudflare forwarding path merely for convenience or speed.
- Preserve the distinction between the host's own resolver and the LAN/VPN DNS service.
- Preserve the existing host-networking requirements for services that must reach host-local DNS or WireGuard interfaces.

## 6. AI-agent operating rules

- Read this file before making repository changes.
- Read `docs/ai-cto/context.md` when the task involves current state, priorities, deployment status, or the AI orchestration system.
- Follow links into deeper documentation when a decision is non-obvious; do not replace documented rationale with guesses.
- Prefer existing repository patterns over introducing a new mechanism.
- Keep changes narrowly scoped and preserve unrelated work.
- Inspect the relevant files before editing them.
- Validate changes with the most relevant available checks.
- Separate facts observed from inference and proposed design.
- When blocked by missing live access, credentials, hardware, or tooling, state the blocker rather than simulating completion.
- Do not expose secrets or copy sensitive runtime values into logs, issues, commits, or documentation.

## 7. AI orchestration

The repository contains an AI gateway and a planned/partially deployed orchestration layer. Treat model providers as interchangeable implementation details unless a document explicitly requires one.

- The gateway is the model front door; do not bypass it casually when working on the orchestration architecture.
- Odin is the supervisor/orchestration layer described in `04-user-services/ai-orchestration/langgraph-router/` and its companion blueprint.
- Deterministic safety/privacy/spend controls are architectural invariants, not optional personality instructions.
- Do not infer that an AI component is deployed merely because its source/configuration exists in git.

## 8. Statements and measurement honesty

- A Statement ships for money only with numbers the appliance actually measured.
- If a measurement layer is scaffolded but not operating, omit unsupported metrics rather than filling them with estimates.
- Never invent comparison benchmarks, GB breakdowns, savings, or other customer-facing figures.
- Preserve the distinction between measured facts, calculated values, and explanatory copy.

## 9. Canonical documentation map

- `AGENTS.md` — agent-agnostic repository operating contract.
- `CLAUDE.md` — Claude Code compatibility briefing; migrate durable repository rules here rather than adding new Claude-only requirements.
- `README.md` — top-level project map and user-facing entry point.
- `docs/ai-cto/context.md` — current AI-CTO operational state and next actions.
- `docs/DEPLOY-QUEUE.md` — staged deployment queue.
- `docs/DEPLOY-PROTOCOL.md` — safe deployment procedure.
- `docs/architecture/network-context.md` — network design rationale.
- `04-user-services/ai-orchestration/ORCHESTRATION-BLUEPRINT.md` — gateway versus supervisor architecture.
- `04-user-services/ai-orchestration/langgraph-router/` — Odin implementation and self-testable orchestration layer.

## 10. Compatibility policy

`CLAUDE.md` may remain for tools that automatically discover that filename. New repository-wide instructions should be written in `AGENTS.md` first. If the two files conflict, `AGENTS.md` is the canonical source for agent-agnostic rules; Claude-specific runtime instructions may remain in `CLAUDE.md`.

When changing an invariant, update the canonical documentation and any compatibility file that would otherwise cause an agent to act on stale instructions.
