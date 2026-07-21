"""
C brain — local deliberator with frontier-oracle escalation (COMPROMISE PHASE).

Runs on the XPS-as-C stand-in. Two-axis router:
  - sensitivity: sensitive tasks NEVER leave the membrane -> local only, forever.
  - capability:  hard + non-sensitive tasks may consult the rented oracle.

The oracle ADVISES; it never acts. This module returns advice/plans as text.
Execution is a SEPARATE, deterministic step (F) that is not in this file and must
never be another LLM. G (the human) approves anything consequential.

Sealed-C phase: here C dials the oracle directly (the laptop has a NIC; isolation
is logical). In the sealed build C has no NIC — replace ask_oracle() with a
request over the serial pore, and B dials on C's behalf. Nothing else changes.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass

from openai import OpenAI

# ---- clients -----------------------------------------------------------------

# Local brain: Ollama's OpenAI-compatible endpoint. Always available.
local = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
LOCAL_MODEL = os.environ.get("C_LOCAL_MODEL", "qwen2.5:7b-instruct")

# Frontier oracle: a rented, OpenAI-compatible endpoint (vLLM / Ollama / TGI on a
# RunPod or vast pod). OFF unless configured. Never hardcode the key.
ORACLE_BASE = os.environ.get("ORACLE_BASE_URL")
ORACLE_KEY = os.environ.get("ORACLE_API_KEY", "")
ORACLE_MODEL = os.environ.get("ORACLE_MODEL", "")
oracle = OpenAI(base_url=ORACLE_BASE, api_key=ORACLE_KEY) if ORACLE_BASE else None

# ---- Frigg: redaction (STUB — harden before trusting) ------------------------

_PATTERNS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "<EMAIL>"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "<IP>"),
    (re.compile(r"\b[A-Za-z0-9+/]{40,}\b"), "<TOKEN>"),  # long base64-ish blobs
]


def redact(text: str) -> str:
    """Minimal PII/secret stripping. THIS IS A STUB. Real Frigg is more than
    regex — treat everything that crosses to the oracle as world-readable, and
    gate eligibility on the *sensitivity* flag, not on this function being
    complete."""
    for pat, repl in _PATTERNS:
        text = pat.sub(repl, text)
    return text


# ---- the two-axis router -----------------------------------------------------


@dataclass
class Task:
    prompt: str
    sensitive: bool  # G/policy decision: may this data leave the membrane at all?
    hard: bool       # does local C likely need frontier help?


def _chat(client: OpenAI, model: str, prompt: str) -> str:
    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return r.choices[0].message.content


def ask_local(prompt: str) -> str:
    return _chat(local, LOCAL_MODEL, prompt)


def ask_oracle(prompt: str) -> str:
    """Compromise phase: C dials directly. Sealed phase: replace with a serial
    request; B dials. Only ever receives redacted, non-sensitive prompts."""
    if oracle is None:
        raise RuntimeError("ORACLE_BASE_URL not set — the oracle is off by default.")
    return _chat(oracle, ORACLE_MODEL, prompt)


def deliberate(task: Task) -> str:
    """Return ADVICE / a PLAN as text. Never executes. F (deterministic,
    elsewhere) turns an approved plan into allowlisted actions; G approves the
    consequential ones."""
    # sensitive OR easy OR no oracle configured -> stay local, always.
    if task.sensitive or not task.hard or oracle is None:
        return ask_local(task.prompt)

    # hard AND non-sensitive: consult the oracle, then let LOCAL C integrate it.
    advice = ask_oracle(redact(task.prompt))
    integrate = (
        "You are the trusted local reasoner. A frontier consultant returned the "
        "advice below. Judge it, correct it, and produce the final plan yourself. "
        "You may reject the advice entirely.\n\n"
        f"TASK:\n{task.prompt}\n\nCONSULTANT ADVICE:\n{advice}\n"
    )
    return ask_local(integrate)  # local C stays in charge; the oracle only advised.


if __name__ == "__main__":
    # An easy/sensitive task stays local; a hard, non-sensitive one may escalate.
    t = Task(
        prompt="Is newly-registered-domain.tld a likely C2 or a legit CDN?",
        sensitive=False,
        hard=True,
    )
    print(deliberate(t))
