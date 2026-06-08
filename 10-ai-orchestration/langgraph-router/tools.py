#!/usr/bin/env python3
"""Huginn (Thought) — read-only GitHub grounding for Odin, stdlib only.

Huginn is one of Odin's two ravens; he flies out and brings back word. Odin plans better
when he can see the relevant repo, so Huginn pulls a few files from GitHub over the REST
API and stitches them into a `context` string the graph threads through every node. He is
deliberately small: fetch + naive keyword pick, no vector store. (A real embedding index —
Chroma/FAISS over the repos — is the obvious next step; it is NOT built here. Don't claim
RAG we don't have.) His brother Muninn (Memory) keeps the record — the audit log.

PRIVACY, READ THIS: fetched content can come from a PRIVATE repo (DESIGN, MARKETING).
Heimdall (supervisor.gatekeeper()) therefore fails CLOSED — any attached context forces
local-only routing unless GITHUB_CONTEXT_ALLOW_CLOUD=1. So word Huginn carries from a
private repo does not quietly cross the Bifröst to a cloud model. Token is read from
GITHUB_TOKEN (a fine-grained, read-only PAT in ~/llm-router/.env, git-ignored) — never
inline it, never log it.

No pip deps. `python3 tools.py --selftest` checks the URL/snippet logic offline.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

GITHUB_API = os.environ.get("GITHUB_API", "https://api.github.com")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")     # read-only fine-grained PAT; never log
MAX_CONTEXT_CHARS = int(os.environ.get("GITHUB_CONTEXT_MAX_CHARS", "8000"))


def _api_get(path: str) -> dict | list:
    """GET an api.github.com path and parse JSON. Auth only if a token is present."""
    req = urllib.request.Request(f"{GITHUB_API}{path}")
    req.add_header("Accept", "application/vnd.github+json")
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def fetch_file(repo: str, path: str, *, ref: str = "") -> str:
    """Return the decoded text of one file, or "" if unavailable.

    `repo` is "owner/name". Uses the raw-content Accept header so we get bytes, not a
    base64 JSON envelope. Network/permission errors degrade to "" — grounding is a
    nice-to-have, never a hard dependency that can sink a run.
    """
    url = f"{GITHUB_API}/repos/{repo}/contents/{path}"
    if ref:
        url += f"?ref={ref}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github.raw+json")
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", "replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return ""


def search_code(repo: str, query: str, *, limit: int = 5) -> list[str]:
    """Return file paths in `repo` matching `query` via GitHub code search. [] on error."""
    q = urllib.request.quote(f"{query} repo:{repo}")
    try:
        data = _api_get(f"/search/code?q={q}&per_page={limit}")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return []
    items = data.get("items", []) if isinstance(data, dict) else []
    return [it.get("path", "") for it in items if it.get("path")]


def snippet(text: str, query: str, *, window: int = 1500) -> str:
    """Center a window on the first query-term hit, so context stays under budget.

    Keeps the most relevant slice instead of a blind head() — the planner sees the part
    that matters. Falls back to the head when nothing matches.
    """
    if not text:
        return ""
    low = text.lower()
    pos = -1
    for term in query.lower().split():
        pos = low.find(term)
        if pos != -1:
            break
    if pos == -1:
        return text[:window]
    start = max(0, pos - window // 2)
    return text[start : start + window]


def gather_context(repo: str, query: str, *, paths: list[str] | None = None) -> str:
    """Build a grounding blob for the supervisor: a few relevant files, trimmed to budget.

    Give explicit `paths` to skip search (cheap, deterministic), or let code search find
    candidates. Output is capped at MAX_CONTEXT_CHARS. Returning this into the graph
    forces local-only routing by default (see module docstring + supervisor.gate).
    """
    chosen = list(paths or [])
    if not chosen:
        chosen = search_code(repo, query, limit=3)
    blocks: list[str] = []
    used = 0
    for p in chosen:
        body = snippet(fetch_file(repo, p), query)
        if not body:
            continue
        block = f"=== {repo}/{p} ===\n{body}"
        if used + len(block) > MAX_CONTEXT_CHARS:
            break
        blocks.append(block)
        used += len(block)
    return "\n\n".join(blocks)


def _selftest() -> None:
    """Offline checks: snippet centering + budget, no network touched."""
    assert snippet("", "x") == ""
    big = "A" * 100 + "NEEDLE" + "B" * 100
    s = snippet(big, "needle", window=40)
    assert "NEEDLE" in s and len(s) <= 40
    assert snippet("no match here", "zzz", window=5) == "no ma"   # head fallback
    print("selftest: OK — snippet centers on the hit, respects the window, no network used")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        _selftest()
        sys.exit(0)
    if len(sys.argv) > 3 and sys.argv[1] == "--gather":
        # python3 tools.py --gather <owner/repo> "<query>"   (needs GITHUB_TOKEN for private)
        print(gather_context(sys.argv[2], sys.argv[3]))
        sys.exit(0)
    _selftest()
    print("\n--gather <owner/repo> \"<query>\" to pull live context (set GITHUB_TOKEN first)")
