#!/usr/bin/env python3
"""Frigg — she knows every fate and speaks none. PII/secret redaction, stdlib only.

A Crossing Guard: Frigg guards the allies (Midgard, the human) by scrubbing personal
data and secrets out of anything that would cross the Bifröst to a third-party cloud.
She is the SECOND line, not the first — Heimdall already pins `sensitive` tasks local;
Frigg catches the stray secret that rides along in an otherwise-benign request bound for
the cloud (an address in a paragraph, an API key pasted into a question).

Design choices, on purpose:
  * DETERMINISTIC regex, no model. Same input -> same redaction. Testable offline.
  * HIGH-PRECISION patterns only. A redactor that mangles ordinary text (or code) is
    worse than none — it silently corrupts prompts. So Frigg redacts only what is
    unmistakably PII/secret; she leaves bare IPs and plain numbers alone by default.
  * She runs ONLY on the cloud crossing (see supervisor.frigg_guard). Local tiers stay
    inside the walls, so their text is never altered — no quality cost where there's no
    leak risk.

`python3 frigg.py --selftest` proves the patterns offline. No pip deps.
"""

from __future__ import annotations

import re
import sys

# Each rule: (label, compiled pattern). Order matters only for overlapping matches;
# these are disjoint enough that it doesn't in practice. Placeholders read ⟨label⟩.
_RULES: list[tuple[str, re.Pattern]] = [
    # Secrets / tokens first — most damaging if leaked.
    ("api-key", re.compile(r"\b(?:sk|pk|rk)-[A-Za-z0-9]{16,}\b")),          # OpenAI/Stripe-style
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),       # ghp_/gho_/...
    ("aws-key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("bearer", re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{16,}\b")),
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----")),
    # Personal data.
    ("email", re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("credit-card", re.compile(r"\b(?:\d[ -]?){13,16}\b")),                 # 13–16 digits, spaced/hyphenated
    ("phone", re.compile(r"\b(?:\+?1[ .\-]?)?\(?\d{3}\)?[ .\-]\d{3}[ .\-]\d{4}\b")),
]


def redact(text: str) -> tuple[str, dict[str, int]]:
    """Return (redacted_text, counts). counts maps label -> hits. Pure, no I/O.

    A no-match input returns unchanged with an empty count — Frigg is invisible when
    there's nothing to guard.
    """
    if not text:
        return text, {}
    counts: dict[str, int] = {}
    out = text
    for label, pat in _RULES:
        out, n = pat.subn(f"⟨{label}⟩", out)
        if n:
            counts[label] = counts.get(label, 0) + n
    return out, counts


def redact_messages(messages: list[dict]) -> tuple[list[dict], dict[str, int]]:
    """Redact the `content` of every chat message; tally what was found across all."""
    total: dict[str, int] = {}
    cleaned = []
    for m in messages:
        c, counts = redact(m.get("content", ""))
        for k, v in counts.items():
            total[k] = total.get(k, 0) + v
        cleaned.append({**m, "content": c})
    return cleaned, total


def _selftest() -> None:
    """High-precision in, low collateral out."""
    # Secrets and PII are caught.
    r, c = redact("mail me at jane.doe@example.com or call 415-555-0188")
    assert "⟨email⟩" in r and "⟨phone⟩" in r and "example.com" not in r
    assert c.get("email") == 1 and c.get("phone") == 1

    r, c = redact("key sk-ABCDEF0123456789XYZ and token ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ012345")
    assert "sk-" not in r and "ghp_" not in r and c.get("api-key") == 1 and c.get("github-token") == 1

    r, c = redact("SSN 123-45-6789 card 4111 1111 1111 1111")
    assert "⟨ssn⟩" in r and "123-45-6789" not in r
    assert "4111" not in r and c.get("credit-card") == 1

    # Ordinary prose and code are LEFT ALONE — no collateral damage.
    plain = "Restart unbound on the t630 at 127.0.0.1 port 5335, then run dig."
    r, c = redact(plain)
    assert r == plain and c == {}          # bare IP/port/words untouched by design

    # Empty / no-op.
    assert redact("") == ("", {})

    # Message helper tallies across messages.
    msgs = [{"role": "user", "content": "a@b.com"}, {"role": "system", "content": "no pii here"}]
    cleaned, total = redact_messages(msgs)
    assert cleaned[0]["content"] == "⟨email⟩" and cleaned[1]["content"] == "no pii here"
    assert total.get("email") == 1

    print("selftest: OK — Frigg redacts secrets + PII, leaves ordinary prose/code untouched")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        _selftest()
        sys.exit(0)
    if len(sys.argv) > 2 and sys.argv[1] == "--redact":
        clean, found = redact(sys.argv[2])
        print(clean)
        print(f"\n[frigg] redacted: {found}", file=sys.stderr)
        sys.exit(0)
    _selftest()
    print("\n--redact \"<text>\" to scrub a string")
