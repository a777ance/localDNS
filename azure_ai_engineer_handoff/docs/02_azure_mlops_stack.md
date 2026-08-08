<!-- provenance: A · handoff brief supplied by the founder (Gemini-drafted), 2026-08-08 · 2026-08-08 · verify: read the real service list off the employer's Azure subscription before treating any row as the deployed stack -->

# Azure MLOps & Architecture Stack

The company operates on an Azure-native stack. Avoid stitching together disparate
open-source tools; leverage Microsoft's integrated ecosystem.

**Tier: `A` (asserted).** This is the *stated* target stack, not an inventory of
what is running. Confirm each service against the live subscription before
building on it.

## Generative AI & LLMOps (If Applicable)

*   **Retrieval/Memory:** Azure AI Search (acting as the native vector database).
*   **Orchestration:** Azure AI Prompt Flow (for designing, testing, and
    evaluating RAG/LLM chains).
*   **Hub/Deployments:** Azure AI Studio & Azure OpenAI Service.

## Core Infrastructure

1.  **Experiment Tracking & Registry:** Azure Machine Learning Workspace (using
    built-in MLflow capabilities).
2.  **Orchestration & CI/CD:** Azure ML Pipelines (Python SDK v2) integrated with
    Azure DevOps or GitHub Actions.
3.  **Model Serving:** Azure Managed Online Endpoints (for secure, scalable REST
    API endpoints without managing underlying Kubernetes clusters).
4.  **Monitoring:** Azure Monitor, Application Insights, and Azure ML Model Data
    Collector (for detecting data/target drift).

## Sampling posture for any LLM work built here

Anything that configures, prompts, or aggregates a model follows the sampling
doctrine in [`CLAUDE.md` § G](../../CLAUDE.md#g-llm-sampling-doctrine--the-jury) —
lazy anchor → governed-warm body → concurrent vote. Restated inline so it binds
here rather than merely pointing:

*   **Never consume a single warm draw where a verdict matters.** One draw is an
    honest guess; sample several and take a plurality. In Prompt Flow this means
    a multi-variant node plus an aggregation step, not one call.
*   **Match every degree of temperature with a degree of governance** — a
    tail-clip (`top_p`/`top_k`) and a selector (the vote).
*   **Measure `p̂`, don't guess it.** Voting only helps when the correct answer is
    already modal; below that it amplifies a wrong answer. Use a labelled eval
    set (Prompt Flow evaluation runs) before trusting an aggregate.
*   **Never hand jurors the answer menu** — a supplied option set is a shared
    prior that correlates the draws and inflates agreement. Have each draw coin
    its own answer; normalize afterward, in the open.
*   **Unanimity is not a confidence signal.** Agreement is ambiguous between a
    strong panel and a collapsed one. Only a measured `p̂` separates them.
