"""Deterministic local embeddings via feature hashing of words and word bigrams.

Lexical (not semantic) similarity, but real vectors searched with real cosine
distance in pgvector — lets the whole system run offline. Use an API embedding
provider for semantic quality.
"""
import hashlib
import math
import re

from app.services.ai.base import EmbeddingProvider

_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = frozenset(
    "a an the and or of to in on for is are was were be been it this that with as at by from i me my you your "
    "we our they them he she his her its not no do does did have has had will would can could should".split()
)


def _stem(tok: str) -> str:
    for suf in ("ing", "ed", "es", "s"):
        if len(tok) > len(suf) + 2 and tok.endswith(suf):
            return tok[: -len(suf)]
    return tok


class HashEmbeddings(EmbeddingProvider):
    name = "hash"

    def __init__(self, dim: int = 384) -> None:
        self.dim = dim

    def _features(self, text: str) -> list[str]:
        toks = [_stem(t) for t in _TOKEN.findall(text.lower()) if t not in _STOP]
        return toks + [f"{a}_{b}" for a, b in zip(toks, toks[1:])]

    def embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for f in self._features(text):
            h = int.from_bytes(hashlib.blake2b(f.encode(), digest_size=8).digest(), "big")
            vec[h % self.dim] += 1.0 if (h >> 63) & 1 else -1.0
        norm = math.sqrt(sum(v * v for v in vec))
        return [v / norm for v in vec] if norm else vec

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_one(t) for t in texts]
