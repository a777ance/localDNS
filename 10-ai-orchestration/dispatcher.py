#!/usr/bin/env python3
"""Deterministic dispatcher for the multi-model stack — the "dumb switch".

Reference implementation for ORCHESTRATION-BLUEPRINT.md. This is the layer ABOVE
LiteLLM: it picks WHICH backend handles a task, then calls the one OpenAI-compatible
front door (ai.home.lan:4040). LiteLLM handles the provider, retries, and failover.

Design rules (from the blueprint — do not "improve" these away):
  * NO LLM in the routing decision. Routing is a rule table + token match. Same input
    -> same route, every time. Zero token/CPU cost to decide.
  * Route to CAPABILITY model-names (cloud-explore / cloud-code / ...), never to vendor
    endpoints. Swapping a backend is a config.yaml edit, never a code edit here.
  * The privacy boundary is a line of code, not a hope: a task classified `sensitive`
    routes to a LOCAL tier and is sent with allow_cloud=False. See SENSITIVE below and
    the note in route().

classify() is pure (no I/O) so it is trivially unit-testable. call_model() is the only
thing that touches the network. Runs on python3 stdlib alone — no pip install needed.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone

# ── One front door. The dispatcher never talks to a provider directly. ──
FRONT_DOOR = os.environ.get("LLM_ROUTER_URL", "http://ai.home.lan:4040/v1/chat/completions")
MASTER_KEY = os.environ.get("LITELLM_MASTER_KEY", "")  # never hard-code; never log
LOG_PATH = os.environ.get("LLM_ROUTER_LOG", "")        # set a path to enable the reflection log

# ── Capability tiers (model_names served by LiteLLM). These must exist in
#    10-ai-orchestration/config.yaml. local-* exist today; cloud-explore / cloud-code /
#    cloud-vision are the Phase-2 additions from the blueprint. ──
LOCAL_FAST = "local-fast"          # qwen2.5:3b on the t630 — snappy, cool
LOCAL_REASON = "local-reason"      # deepseek-r1:1.5b on the t630 — light reasoning, LOCAL ONLY
GPU_REASON = "cloud-gpu-reason"    # full DeepSeek-R1 on the rented GPU (self-hosted)
CLOUD_EXPLORE = "cloud-explore"    # wide-angle / research  (e.g. Opus 4.8)
CLOUD_CODE = "cloud-code"          # code / schematics / diffs / structured build (e.g. Sonnet 4.6)
CLOUD_VISION = "cloud-vision"      # READING an image (understanding) — NOT image generation


@dataclass(frozen=True)
class Rule:
    name: str
    keywords: frozenset[str]
    model: str
    allow_cloud: bool = True       # False => privacy-locked: never leaves self-hosted infra


@dataclass
class Route:
    model: str
    rule: str
    allow_cloud: bool


# ── The rule table. ORDER MATTERS: first match wins. Edit freely; it's just data. ──
# Privacy-sensitive sits FIRST so it can never be out-voted by a later keyword.
SENSITIVE = frozenset(
    "bank banking tax taxes ssn salary password passwd secret medical health "
    "diagnosis legal lawsuit invoice payroll personal private confidential".split()
)

RULES: list[Rule] = [
    Rule("sensitive", SENSITIVE, LOCAL_REASON, allow_cloud=False),
    # Diagram/chart GENERATION is a code job (emit Mermaid/SVG/matplotlib), not vision.
    Rule("code", frozenset("code build implement refactor diff schematic "
                           "function bug compile diagram chart mermaid svg".split()), CLOUD_CODE),
    # Vision = UNDERSTANDING an existing image (screenshot, photo, scan).
    Rule("vision", frozenset("screenshot image photo picture scan ocr "
                            "describe look".split()), CLOUD_VISION),
    Rule("explore", frozenset("research explore brainstorm ideate idea creative "
                            "hypothesis investigate compare survey wide".split()), CLOUD_EXPLORE),
    Rule("heavy_reason", frozenset("prove derive analyze reason "
                                "step-by-step deep".split()), GPU_REASON),
]
DEFAULT = Rule("default", frozenset(), LOCAL_FAST)   # quick local turn; nothing matched


_TOKEN = re.compile(r"[a-z0-9][a-z0-9\-]*")


def classify(task: str) -> Route:
    """Pure, deterministic. Token-match (not substring) so 'code' != 'decoded'."""
    tokens = set(_TOKEN.findall(task.lower()))
    for rule in RULES:
        if rule.keywords & tokens:
            return Route(model=rule.model, rule=rule.name, allow_cloud=rule.allow_cloud)
    return Route(model=DEFAULT.model, rule=DEFAULT.name, allow_cloud=DEFAULT.allow_cloud)


def call_model(model: str, messages: list[dict], *, allow_cloud: bool = True) -> str:
    """The only network I/O. POSTs to the single front door; LiteLLM does the rest.

    Privacy enforcement lives at the config layer: a privacy-locked tier (e.g.
    `local-reason`) MUST be configured in config.yaml with a LOCAL-ONLY fallback chain
    (no `cloud-overflow`). allow_cloud is carried so the caller/UI can assert it and so
    a future LiteLLM tag-based guard can read it; we refuse to even attempt cloud here.
    """
    if not allow_cloud and model.startswith("cloud-") and model != GPU_REASON:
        raise PermissionError(
            f"refusing to send a privacy-locked task to cloud tier {model!r}"
        )
    payload = json.dumps({"model": model, "messages": messages}).encode()
    req = urllib.request.Request(
        FRONT_DOOR,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {MASTER_KEY}",
        },
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        body = json.loads(resp.read())
    return body["choices"][0]["message"]["content"]


def _log(record: dict) -> None:
    """Reflection log — one JSONL line per route. Off unless LLM_ROUTER_LOG is set.

    Redacts the MATERIAL, keeps the INSIGHT. A privacy-locked task (allow_cloud=False)
    never persists its text or result in the clear — but the routing metadata
    (timestamp / model / rule) and the caller-supplied `note` ARE kept, so the log
    stays reviewable without leaking the sensitive content. (`note` is the caller's
    line to keep non-sensitive — it's the one-line takeaway, not the source text.)
    A log that leaked the sensitive text would defeat the boundary the dispatcher
    exists to hold; a log you can never read back teaches nothing. reflect() reads
    these lines back.
    """
    if not LOG_PATH:
        return
    entry = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), **record}
    if not entry.get("allow_cloud", True):
        entry["task"] = "<redacted: privacy-locked>"
        entry.pop("result", None)
    with open(os.path.expanduser(LOG_PATH), "a") as fh:
        fh.write(json.dumps(entry) + "\n")


def reflect(path: str = "", *, limit: int = 10) -> dict:
    """Read the reflection log back — the half that makes it a log, not a drain.

    Pure read, no network. Tallies routes by rule / model / privacy and surfaces the
    most recent `note`s (the kept takeaways, which survive redaction). Notes are
    newest-first, per house style. Falls back to LLM_ROUTER_LOG when no path is given.
    """
    path = os.path.expanduser(path or LOG_PATH)
    if not path or not os.path.exists(path):
        return {"entries": 0, "hint": "no log yet — set LLM_ROUTER_LOG and run some tasks"}
    by_rule: dict[str, int] = {}
    by_model: dict[str, int] = {}
    notes: list[dict] = []
    total = locked = 0
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue          # a torn half-line shouldn't blind the whole mirror
            total += 1
            by_rule[e.get("rule", "?")] = by_rule.get(e.get("rule", "?"), 0) + 1
            by_model[e.get("model", "?")] = by_model.get(e.get("model", "?"), 0) + 1
            if not e.get("allow_cloud", True):
                locked += 1
            if e.get("note"):
                notes.append({"ts": e.get("ts"), "rule": e.get("rule"), "note": e["note"]})
    return {
        "entries": total,
        "privacy_locked": locked,
        "by_rule": dict(sorted(by_rule.items(), key=lambda kv: -kv[1])),
        "by_model": dict(sorted(by_model.items(), key=lambda kv: -kv[1])),
        "recent_notes": notes[-limit:][::-1],          # newest-first
    }


def dispatch(task: str, *, dry_run: bool = False, note: str = "") -> dict:
    """Classify -> route -> (optionally) call. Returns a small audit record.

    `note` is an optional one-line takeaway from the caller; it is kept in the log
    even when the task itself is redacted, so a privacy-locked route still leaves
    something reviewable behind. Keep it non-sensitive.
    """
    route = classify(task)
    record = {"task": task[:80], "model": route.model, "rule": route.rule,
              "allow_cloud": route.allow_cloud}
    if note:
        record["note"] = note
    if dry_run:
        record["status"] = "routed (dry-run, not called)"
    else:
        record["result"] = call_model(
            route.model, [{"role": "user", "content": task}], allow_cloud=route.allow_cloud
        )
        record["status"] = "called"
    _log(record)
    return record


# ── A FIXED, scripted pipeline. No LLM decides the steps — the sequence is the spec. ──
def research_then_build(topic: str, *, dry_run: bool = False) -> dict:
    """Two-step sandwich: explore wide, then hand the findings to the code tier."""
    findings = dispatch(f"research and survey approaches to: {topic}", dry_run=dry_run)
    spec = findings.get("result", f"[dry-run findings for {topic}]")
    build = dispatch(f"implement, given these findings: {spec}", dry_run=dry_run)
    return {"step1_explore": findings, "step2_code": build}


def _selftest() -> None:
    """Inline smoke test — proves the routing is deterministic and privacy-safe."""
    assert classify("refactor this function").rule == "code"
    assert classify("decoded the payload").rule != "code"          # token match, not substring
    assert classify("brainstorm wide-angle ideas").rule == "explore"
    assert classify("describe this screenshot").rule == "vision"
    s = classify("review my bank tax statement")
    assert s.rule == "sensitive" and s.model == LOCAL_REASON and s.allow_cloud is False
    assert classify("hi there").rule == "default"

    # reflection: material redacted, insight + metadata kept, and readable back
    import tempfile
    global LOG_PATH
    _saved, fd_path = LOG_PATH, tempfile.mkstemp(suffix=".jsonl")[1]
    LOG_PATH = fd_path
    try:
        dispatch("review my bank password 1234", dry_run=True, note="kept the takeaway")
        dispatch("brainstorm wide ideas", dry_run=True, note="explore takeaway")
        raw = open(fd_path).read()
        assert "bank" not in raw and "password" not in raw and "1234" not in raw  # material gone
        assert "kept the takeaway" in raw                                          # insight stays
        r = reflect(fd_path)
        assert r["entries"] == 2 and r["privacy_locked"] == 1
        assert r["recent_notes"][0]["note"] == "explore takeaway"                  # newest-first
    finally:
        os.unlink(fd_path)
        LOG_PATH = _saved
    print("selftest: OK — routing deterministic, privacy lock holds, log is readable")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--reflect":
        print(json.dumps(reflect(), indent=2))     # read the log back: python3 dispatcher.py --reflect
        sys.exit(0)
    _selftest()
    print(f"\nfront door: {FRONT_DOOR}\n")
    samples = [
        "Generate a creative solution set for taming local AI compute heat",
        "Refactor the dispatcher and show a diff",
        "Summarize my bank tax statement",          # must stay local
        "Describe what's in this screenshot",
        "hello",
    ]
    for t in samples:
        print(json.dumps(dispatch(t, dry_run=True)))
    # Real call: `python3 dispatcher.py --run "your task" ["one-line takeaway"]` (needs tiers + key)
    if len(sys.argv) > 2 and sys.argv[1] == "--run":
        _note = sys.argv[3] if len(sys.argv) > 3 else ""
        print(json.dumps(dispatch(sys.argv[2], note=_note), indent=2))
