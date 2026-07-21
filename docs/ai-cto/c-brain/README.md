# C brain — starter (compromise phase, on the XPS)

Stand up the local deliberator (**C**) on the Dell XPS 13 9340 (Core Ultra 7 155H,
Arc iGPU, 32 GB, Ubuntu 24.04) and wire the frontier-oracle escalation. This is the
**compromise / validation** phase: C runs on the laptop with *logical* (not
structural) isolation, so you can prove the whole loop before buying the sealed
GPU box. Implements the design in `../membrane-node-architecture.md`.

## 1. Local brain — start on CPU (guaranteed), it's enough to validate

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:7b-instruct              # strong structured output, fits easily in 32 GB
ollama run qwen2.5:7b-instruct "reply OK"    # sanity check
```

**Qwen2.5-7B-Instruct** is the recommended local model: excellent at JSON/structured
output and instruction-following — exactly C's job (triage, config drafting, plan
transcription). CPU on the 155H is usable for async work. Do **not** run a reasoning
model (deepseek-r1) locally — its long chain-of-thought is slow on CPU/iGPU (your own
known-issue); escalate hard reasoning to the oracle instead.

## 2. (Optional) Arc iGPU acceleration — only after the loop works

Validate on CPU first; then optimize. Two real paths, most-reliable first:

**Vulkan (simplest, fewest moving parts):**
```bash
sudo apt install -y mesa-vulkan-drivers vulkan-tools libvulkan-dev
vulkaninfo | grep deviceName                 # should list Intel Arc / Xe
```
Build llama.cpp with `-DGGML_VULKAN=ON` and run with `-ngl 99` to offload layers to
the iGPU.

**Intel ipex-llm (best Arc perf, Intel-official, version-sensitive):** follow Intel's
current "Run Ollama on Intel GPU" ipex-llm quickstart — it ships a SYCL/Level-Zero
Ollama build. It moves fast, so use their live docs rather than a command pinned here.
The fallback is always CPU Ollama from step 1.

Expect single-to-low-double-digit tokens/sec for a 7B on the iGPU — plenty for a brain
that scores decisions in the background, not a chatbot you wait on.

## 3. The router + oracle escalation

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install openai
# Oracle is OFF by default. Set these only when you rent a pod (OpenAI-compatible:
# vLLM / Ollama / TGI on RunPod or vast). NEVER commit real keys.
export ORACLE_BASE_URL="https://<your-pod-host>:8000/v1"
export ORACLE_API_KEY="..."
export ORACLE_MODEL="<model-served-by-the-pod>"
python router.py
```

`router.py` is the **two-axis gate**: *sensitive* tasks never leave (local only,
forever); *hard + non-sensitive* tasks may consult the rented oracle, which **advises
only** — local C integrates the advice, stays in charge, and can reject it. The module
returns a plan as text; it never executes. Execution (**F**) is a separate,
deterministic step, and **G** (you) approves anything consequential.

## Sealed-C phase (later)

When C becomes the dedicated no-NIC GPU box, C no longer dials. Replace the direct call
in `ask_oracle()` with a request over the serial pore — **B** dials the oracle on C's
behalf. Everything else in `router.py` is unchanged. That is the only edit between the
compromise brain and the sealed ghost.

## Cost reminder

Local: one-time hardware. Oracle: ~$1–5/mo bursty (per-second billing, cold starts) or
~$300+/mo if a pod is kept warm. Off by default — you pay only when C escalates.
