#!/usr/bin/env python3
"""The Hoard-Warden — guards the treasure. A deterministic cloud-spend cap, stdlib only.

A Vanguard guard (he guards Asgard / Odin himself). Riding to Jotunheim costs coin: every
call to a third-party cloud tier bills per token. The Hoard-Warden keeps the ledger and,
when the hoard runs dry, refuses the crossing — the work falls back to the keep (a local
tier) instead. Thematically: when the treasure is spent, the Valkyries cannot ride, so the
local garrison takes the field. Mechanically: a budget cap that fails to local, never to a
surprise bill.

Design, on purpose:
  * DETERMINISTIC. A rough but honest pre-flight estimate (chars/4 ≈ tokens) × a per-tier
    price, checked against a cap. No model, no network — same input, same verdict.
  * ESTIMATE, and SAID to be one. Prices are list prices at time of writing; the real bill
    comes from the provider. This guards against runaway spend, it is not an invoice.
  * OFF unless you set a cap. LLM_ROUTER_BUDGET_USD=0 (default) means unlimited — a normal
    run is unchanged. Set a dollar figure to arm the cap.
  * Local tiers and the self-hosted GPU cost nothing here, so they are never counted or
    capped — only third-party cloud crossings are.

The cap ENFORCEMENT (downgrade cloud→local) lives in supervisor.hoard_guard, next to the
tier constants; this file is the pure ledger. `python3 hoard.py --selftest` proves it.
"""

from __future__ import annotations

import os
import sys

# USD per 1,000,000 tokens, (input, output). ESTIMATES — list prices at time of writing;
# verify against current pricing. Keyed by capability tier (see config.yaml). Tiers absent
# here (local-*, cloud-gpu-reason) are treated as free: local CPU, or a flat hourly GPU you
# already pay for, so per-token accounting doesn't apply.
PRICES: dict[str, tuple[float, float]] = {
    "cloud-explore": (5.0, 25.0),    # opus-class
    "cloud-vision": (5.0, 25.0),     # opus-class
    "cloud-overflow": (5.0, 25.0),   # opus-class (the overflow brain)
    "cloud-code": (3.0, 15.0),       # sonnet-class
}

# A crude token estimate good enough for a budget guard: ~4 chars/token.
_CHARS_PER_TOKEN = 4
# What we assume a reply will cost in output tokens when we can't know in advance.
_ASSUMED_OUTPUT_TOKENS = int(os.environ.get("HOARD_OUTPUT_TOKENS", "600"))


def estimate(model: str, messages: list[dict], *, output_tokens: int = _ASSUMED_OUTPUT_TOKENS) -> float:
    """Pre-flight USD estimate for one call. 0.0 for any tier we don't bill (local/GPU)."""
    price = PRICES.get(model)
    if not price:
        return 0.0
    in_tokens = sum(len(m.get("content", "")) for m in messages) / _CHARS_PER_TOKEN
    return in_tokens / 1e6 * price[0] + output_tokens / 1e6 * price[1]


class Hoard:
    """The ledger. `cap_usd <= 0` means unlimited (the guard stands down)."""

    def __init__(self, cap_usd: float = 0.0):
        self.cap_usd = cap_usd
        self.spent = 0.0
        self.charges = 0          # how many cloud calls we billed
        self.downgrades = 0       # how many we refused (sent local instead)

    @classmethod
    def from_env(cls) -> "Hoard":
        try:
            cap = float(os.environ.get("LLM_ROUTER_BUDGET_USD", "0") or 0)
        except ValueError:
            cap = 0.0
        return cls(cap_usd=cap)

    @property
    def armed(self) -> bool:
        return self.cap_usd > 0

    def affordable(self, model: str, messages: list[dict]) -> bool:
        """True if this call fits under the cap (always True when unarmed/free tier)."""
        if not self.armed:
            return True
        return self.spent + estimate(model, messages) <= self.cap_usd

    def charge(self, model: str, messages: list[dict]) -> float:
        """Record the estimated cost of a call we let ride. Returns what was charged."""
        cost = estimate(model, messages)
        self.spent += cost
        self.charges += 1
        return cost

    def refuse(self) -> None:
        """Note that a crossing was refused (the caller will send it local instead)."""
        self.downgrades += 1

    def summary(self) -> dict:
        return {"cap_usd": self.cap_usd, "spent_est_usd": round(self.spent, 4),
                "charges": self.charges, "downgrades": self.downgrades}


def _selftest() -> None:
    msgs = [{"role": "user", "content": "x" * 4000}]   # ~1000 input tokens

    # estimate: free for local/GPU, priced for cloud, ordered opus > sonnet.
    assert estimate("local-fast", msgs) == 0.0
    assert estimate("cloud-gpu-reason", msgs) == 0.0
    assert estimate("cloud-code", msgs) > 0.0
    assert estimate("cloud-explore", msgs) > estimate("cloud-code", msgs)   # opus dearer

    # unarmed hoard: everything affordable, nothing tracked.
    h = Hoard(cap_usd=0)
    assert h.affordable("cloud-explore", msgs) and not h.armed

    # armed hoard: affordable under cap, charges accumulate, then it refuses.
    h = Hoard(cap_usd=0.05)
    assert h.armed and h.affordable("cloud-code", msgs)
    h.charge("cloud-code", msgs)
    assert h.spent > 0 and h.charges == 1
    # drive it over the cap and confirm it refuses the next crossing.
    for _ in range(50):
        if h.affordable("cloud-explore", msgs):
            h.charge("cloud-explore", msgs)
        else:
            break
    assert not h.affordable("cloud-explore", msgs)
    h.refuse()
    assert h.downgrades == 1 and h.spent <= h.cap_usd + estimate("cloud-explore", msgs)

    # a free tier is always affordable even when the hoard is dry.
    assert h.affordable("local-smart", msgs)

    print("selftest: OK — Hoard prices cloud only, charges under cap, refuses when dry, "
          "frees local")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        _selftest()
        sys.exit(0)
    _selftest()
    print("\nset LLM_ROUTER_BUDGET_USD to arm the cap (0 = unlimited)")
