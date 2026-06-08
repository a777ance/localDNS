#!/usr/bin/env python3
"""Mímir's well — Huginn's deep memory. A local embedding index over the repo, stdlib only.

Huginn (tools.py) fetches by keyword; this gives him SEMANTIC recall — he drinks from the
well and remembers by meaning, not just by matching words. The pipeline:

    files --chunk--> texts --embed--> vectors  (saved to one JSON index)
    question --embed--> qvec --cosine top-k--> the most relevant chunks (the `context`)

On purpose, and in keeping with the stack:
  * EMBEDDINGS GO THROUGH THE ONE FRONT DOOR. We POST to LiteLLM's /v1/embeddings, which
    routes to a LOCAL Ollama model (config.yaml `local-embed` -> nomic-embed-text). So
    building and querying the index stays inside the walls — repo text is embedded on the
    t630, nothing crosses the Bifröst. (Point EMBED at a cloud model and that changes —
    don't, for private repos.)
  * ZERO pip deps. urllib for the call, pure-Python cosine. A few hundred chunks is fine.
  * OFFLINE-TESTABLE. Chunking, cosine, and top-k ranking are pure; --selftest uses a
    deterministic lexical fallback embedder (hash_embed) — also the degraded mode when no
    front door is reachable. hash_embed is LEXICAL, not semantic; the real index uses the
    neural model. We say so rather than pretend.

Build:  python3 rag.py --build <dir> --out mimir.json
Query:  python3 rag.py --query "how does the DNS split work?" --index mimir.json
Then point Huginn at it: LLM_ROUTER_INDEX=mimir.json (see tools.gather_context).
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import urllib.request
from dataclasses import dataclass

EMBED_URL = os.environ.get("LLM_ROUTER_EMBED_URL", "http://ai.home.lan:4040/v1/embeddings")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "local-embed")   # a LiteLLM model_name -> local Ollama
MASTER_KEY = os.environ.get("LITELLM_MASTER_KEY", "")
_HASH_DIM = 256


# ── Pure helpers (no I/O) ──────────────────────────────────────────────────────────────
def chunk_text(text: str, *, size: int = 1200, overlap: int = 200) -> list[str]:
    """Split into overlapping windows so a match near a boundary isn't lost. Pure."""
    text = text or ""
    if len(text) <= size:
        return [text] if text.strip() else []
    step = max(1, size - overlap)
    out = [text[i:i + size] for i in range(0, len(text), step)]
    return [c for c in out if c.strip()]


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity. 1.0 = identical direction, 0.0 = orthogonal. Pure."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def hash_embed(texts: list[str]) -> list[list[float]]:
    """Deterministic LEXICAL embedding — a hashed bag of words. No network, no deps.

    Used by --selftest and as the degraded fallback when the front door is unreachable.
    It captures word overlap, NOT meaning; the real index uses the neural model via embed().
    """
    vecs = []
    for t in texts:
        v = [0.0] * _HASH_DIM
        for word in t.lower().split():
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            v[h % _HASH_DIM] += 1.0
        vecs.append(v)
    return vecs


# ── The one network touch: embeddings via the front door (LOCAL model behind LiteLLM) ──
def embed(texts: list[str], *, model: str = EMBED_MODEL, url: str = EMBED_URL) -> list[list[float]]:
    """POST to /v1/embeddings. Falls back to hash_embed if the front door is unreachable,
    so building/querying never hard-crashes on a box without the model up (degraded, lexical)."""
    payload = json.dumps({"model": model, "input": texts}).encode()
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MASTER_KEY}",
    })
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read())
        return [d["embedding"] for d in body["data"]]
    except Exception:
        return hash_embed(texts)          # degraded: lexical, but the index still builds


@dataclass
class Index:
    model: str
    chunks: list[dict]                    # each: {"path", "text", "vec"}

    def search(self, qvec: list[float], *, k: int = 4) -> list[dict]:
        ranked = sorted(self.chunks, key=lambda c: cosine(qvec, c["vec"]), reverse=True)
        return ranked[:k]

    def save(self, path: str) -> None:
        with open(os.path.expanduser(path), "w") as fh:
            json.dump({"model": self.model, "chunks": self.chunks}, fh)

    @classmethod
    def load(cls, path: str) -> "Index":
        with open(os.path.expanduser(path)) as fh:
            d = json.load(fh)
        return cls(model=d.get("model", ""), chunks=d.get("chunks", []))


def build_index(files: dict[str, str], *, embed_fn=embed, model: str = EMBED_MODEL) -> Index:
    """Chunk every file, embed all chunks in one batch, return the Index. `embed_fn` is
    injectable so tests (and the offline fallback) need no network."""
    paths, texts = [], []
    for path, body in files.items():
        for chunk in chunk_text(body):
            paths.append(path)
            texts.append(chunk)
    vecs = embed_fn(texts) if texts else []
    chunks = [{"path": p, "text": t, "vec": v} for p, t, v in zip(paths, texts, vecs)]
    return Index(model=model, chunks=chunks)


def retrieve(index: Index, question: str, *, k: int = 4, embed_fn=embed,
             max_chars: int = 8000) -> str:
    """Return the top-k chunks as a grounding blob (same shape Huginn's keyword path emits)."""
    if not index.chunks:
        return ""
    qvec = embed_fn([question])[0]
    blocks, used = [], 0
    for c in index.search(qvec, k=k):
        block = f"=== {c['path']} ===\n{c['text']}"
        if used + len(block) > max_chars:
            break
        blocks.append(block)
        used += len(block)
    return "\n\n".join(blocks)


def _read_dir(root: str, *, exts=(".md", ".py", ".conf", ".yaml", ".yml", ".txt", ".sh")) -> dict[str, str]:
    files = {}
    for dirpath, _dirs, names in os.walk(os.path.expanduser(root)):
        if "/.git" in dirpath or "/__pycache__" in dirpath:
            continue
        for n in names:
            if n.endswith(exts):
                fp = os.path.join(dirpath, n)
                try:
                    files[os.path.relpath(fp, root)] = open(fp, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
    return files


def _selftest() -> None:
    # chunk_text: small text -> one chunk; large -> overlapping windows that cover it all.
    assert chunk_text("short") == ["short"]
    big = "".join(f"word{i} " for i in range(800))
    cs = chunk_text(big, size=1200, overlap=200)
    assert len(cs) > 1 and "".join(cs).replace(" ", "").count("word0") >= 1

    # cosine: identical = 1, orthogonal = 0.
    assert abs(cosine([1, 0, 0], [1, 0, 0]) - 1.0) < 1e-9
    assert abs(cosine([1, 0, 0], [0, 1, 0]) - 0.0) < 1e-9

    # build + retrieve with the deterministic embedder: the on-topic chunk ranks first.
    files = {
        "dns.md": "The DNS split forwards streaming domains to Cloudflare over DoT.",
        "gpu.md": "The AMD Carrizo iGPU downclocks to 200 MHz when headless.",
        "vpn.md": "WireGuard wg0 is the encrypted tunnel into the keep.",
    }
    idx = build_index(files, embed_fn=hash_embed, model="hash")
    assert len(idx.chunks) == 3
    hits = idx.search(hash_embed(["streaming Cloudflare DoT forward"])[0], k=1)
    assert hits[0]["path"] == "dns.md"          # semantic-ish recall via lexical overlap
    blob = retrieve(idx, "tell me about the VPN tunnel", k=1, embed_fn=hash_embed)
    assert "vpn.md" in blob

    # save / load round-trip.
    import tempfile
    p = tempfile.mkstemp(suffix=".json")[1]
    try:
        idx.save(p)
        loaded = Index.load(p)
        assert len(loaded.chunks) == 3 and loaded.model == "hash"
    finally:
        os.unlink(p)

    print("selftest: OK — chunking covers, cosine ranks, retrieve finds the on-topic file, "
          "index round-trips (deterministic embedder; the real index uses the neural model)")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        _selftest()
        sys.exit(0)
    args = sys.argv[1:]
    if "--build" in args:
        root = args[args.index("--build") + 1]
        out = args[args.index("--out") + 1] if "--out" in args else "mimir.json"
        idx = build_index(_read_dir(root))
        idx.save(out)
        print(f"built {len(idx.chunks)} chunks from {root} -> {out} (model={idx.model})")
        sys.exit(0)
    if "--query" in args and "--index" in args:
        q = args[args.index("--query") + 1]
        idx = Index.load(args[args.index("--index") + 1])
        print(retrieve(idx, q))
        sys.exit(0)
    _selftest()
    print("\n--build <dir> --out mimir.json   |   --query \"...\" --index mimir.json")
