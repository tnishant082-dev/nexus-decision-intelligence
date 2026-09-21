"""Embeddings adapter: sentence-transformers if installed, else hashing vectors."""
from __future__ import annotations

import hashlib
from functools import lru_cache

import numpy as np


def _hash_vec(text: str, dim: int = 64) -> np.ndarray:
    vec = np.zeros(dim, dtype=np.float32)
    for tok in text.lower().split():
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        vec[h % dim] += 1.0
    n = np.linalg.norm(vec)
    return vec / n if n else vec


@lru_cache(maxsize=1)
def _st_model():
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore

        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        return None


def embed_texts(texts: list[str]) -> tuple[np.ndarray, str]:
    model = _st_model()
    if model is not None:
        arr = np.asarray(model.encode(texts, show_progress_bar=False), dtype=np.float32)
        return arr, "sentence-transformers/all-MiniLM-L6-v2"
    arr = np.vstack([_hash_vec(t) for t in texts])
    return arr, "hashing_vectorizer_fallback"


def backend_name() -> str:
    return "sentence-transformers" if _st_model() is not None else "hashing_fallback"
