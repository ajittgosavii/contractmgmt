"""Retrieval across the whole contract repository.

Contract Copilot answers questions about one document. This module is what lets
you ask a question of *every* contract at once ("which agreements have uncapped
liability?").

Two scorers, deliberately:
  * BM25 — lexical, deterministic, needs no API key, and is very good when the
    user types the words the contract actually uses.
  * Embeddings — semantic, catches "uncapped liability" in a clause that says
    "liability shall not be limited". Requires an OpenAI key.

They are combined by reciprocal-rank fusion, which needs no score calibration
between two scales that are not comparable. Embeddings are optional throughout:
with no key, or if the API call fails, search degrades to pure BM25 rather than
failing.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

EMBED_MODEL = "text-embedding-3-small"
_TOKEN_RE = re.compile(r"[a-z0-9']+")


@dataclass(frozen=True)
class Chunk:
    contract_id: str
    contract_name: str
    index: int
    text: str


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(str(text).lower())


def chunk_text(text: str, target_words: int = 140, overlap: int = 30) -> list[str]:
    """Split into overlapping word windows. Overlap keeps a clause that straddles
    a boundary retrievable from either side."""
    words = str(text or "").split()
    if not words:
        return []
    if len(words) <= target_words:
        return [" ".join(words)]

    step = max(1, target_words - overlap)
    chunks = []
    for start in range(0, len(words), step):
        window = words[start:start + target_words]
        if not window:
            break
        chunks.append(" ".join(window))
        if start + target_words >= len(words):
            break
    return chunks


def chunk_contracts(contracts) -> list[Chunk]:
    """Build chunks from a contracts DataFrame (needs id, filename, full_text)."""
    out: list[Chunk] = []
    if contracts is None or len(contracts) == 0:
        return out
    for _, row in contracts.iterrows():
        text = row.get("full_text") or ""
        for i, piece in enumerate(chunk_text(text)):
            out.append(Chunk(str(row["id"]), str(row["filename"]), i, piece))
    return out


# ---------------------------------------------------------------------------
# BM25
# ---------------------------------------------------------------------------
class BM25:
    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = [tokenize(d) for d in docs]
        self.n = len(self.docs)
        self.lengths = [len(d) for d in self.docs]
        self.avg_len = (sum(self.lengths) / self.n) if self.n else 0.0
        self.freqs = [Counter(d) for d in self.docs]

        df = Counter()
        for doc in self.docs:
            df.update(set(doc))
        # +1 inside the log keeps the idf non-negative for terms in most documents.
        self.idf = {
            term: math.log(1 + (self.n - count + 0.5) / (count + 0.5))
            for term, count in df.items()
        }

    def scores(self, query: str) -> list[float]:
        terms = tokenize(query)
        out = [0.0] * self.n
        if not self.n or not self.avg_len:
            return out
        for i, freq in enumerate(self.freqs):
            length = self.lengths[i]
            total = 0.0
            for term in terms:
                tf = freq.get(term, 0)
                if not tf:
                    continue
                denom = tf + self.k1 * (1 - self.b + self.b * length / self.avg_len)
                total += self.idf.get(term, 0.0) * tf * (self.k1 + 1) / denom
            out[i] = total
        return out


# ---------------------------------------------------------------------------
# Embeddings (optional)
# ---------------------------------------------------------------------------
def embed_texts(texts: list[str], api_key: str, batch_size: int = 96) -> list[list[float]] | None:
    """Embed texts, or return None if embeddings are unavailable for any reason."""
    if not api_key or not texts:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        vectors: list[list[float]] = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start:start + batch_size]
            resp = client.embeddings.create(model=EMBED_MODEL, input=batch)
            vectors.extend(item.embedding for item in resp.data)
        return vectors
    except Exception:
        return None


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if not na or not nb:
        return 0.0
    return dot / (na * nb)


# ---------------------------------------------------------------------------
# Hybrid search
# ---------------------------------------------------------------------------
def _rank_positions(scores: list[float]) -> dict[int, int]:
    """Map document index -> 0-based rank (best first). Zero scores never rank."""
    ordered = sorted((i for i, s in enumerate(scores) if s > 0),
                     key=lambda i: scores[i], reverse=True)
    return {doc: rank for rank, doc in enumerate(ordered)}


def reciprocal_rank_fusion(rankings: list[dict[int, int]], size: int, k: int = 60) -> list[float]:
    """Fuse rank lists without needing the underlying scores to be comparable."""
    fused = [0.0] * size
    for ranking in rankings:
        for doc, rank in ranking.items():
            fused[doc] += 1.0 / (k + rank + 1)
    return fused


class RepositoryIndex:
    """Searchable index over every contract's chunks."""

    def __init__(self, chunks: list[Chunk], embeddings: list[list[float]] | None = None):
        self.chunks = chunks
        self.embeddings = embeddings if embeddings and len(embeddings) == len(chunks) else None
        self.bm25 = BM25([c.text for c in chunks])

    @property
    def semantic(self) -> bool:
        return self.embeddings is not None

    def search(self, query: str, top_k: int = 8, api_key: str = "",
               per_contract_cap: int = 3) -> list[tuple[Chunk, float]]:
        if not self.chunks or not query.strip():
            return []

        rankings = [_rank_positions(self.bm25.scores(query))]

        if self.semantic:
            query_vec = embed_texts([query], api_key)
            if query_vec:
                sims = [cosine(query_vec[0], vec) for vec in self.embeddings]
                rankings.append(_rank_positions(sims))

        fused = reciprocal_rank_fusion(rankings, len(self.chunks))
        order = sorted((i for i, s in enumerate(fused) if s > 0),
                       key=lambda i: fused[i], reverse=True)

        # Keep one contract from monopolising the context window.
        seen: Counter = Counter()
        results: list[tuple[Chunk, float]] = []
        for i in order:
            chunk = self.chunks[i]
            if seen[chunk.contract_id] >= per_contract_cap:
                continue
            seen[chunk.contract_id] += 1
            results.append((chunk, fused[i]))
            if len(results) >= top_k:
                break
        return results


def build_index(contracts, api_key: str = "", use_embeddings: bool = True) -> RepositoryIndex:
    chunks = chunk_contracts(contracts)
    vectors = None
    if use_embeddings and api_key and chunks:
        vectors = embed_texts([c.text for c in chunks], api_key)
    return RepositoryIndex(chunks, vectors)