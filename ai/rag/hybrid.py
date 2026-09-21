"""Hybrid retrieval: lexical overlap + dense cosine, optional FAISS, simple rerank."""
from __future__ import annotations

from typing import Any

import numpy as np

from ai.rag.embeddings import embed_texts
from ai.rag.retriever import Chunk, _tokenize, load_chunks


def _lexical_score(question: str, text: str) -> float:
    q = _tokenize(question)
    tokens = _tokenize(text)
    if not tokens or not q:
        return 0.0
    return len(q & tokens) / (len(q) ** 0.5 + 1e-6)


def _dense_topk(q: np.ndarray, m: np.ndarray, k: int) -> np.ndarray:
    try:
        import faiss  # type: ignore

        mat = np.ascontiguousarray(m.astype(np.float32))
        qn = np.ascontiguousarray(q.astype(np.float32))
        faiss.normalize_L2(mat)
        faiss.normalize_L2(qn)
        index = faiss.IndexFlatIP(mat.shape[1])
        index.add(mat)
        _, ids = index.search(qn, k)
        return ids[0]
    except Exception:
        qn = q / (np.linalg.norm(q, axis=1, keepdims=True) + 1e-8)
        mn = m / (np.linalg.norm(m, axis=1, keepdims=True) + 1e-8)
        sims = (qn @ mn.T)[0]
        return np.argsort(-sims)[:k]


def retrieve_hybrid(question: str, top_k: int = 3, knowledge_dir=None) -> list[dict[str, Any]]:
    chunks: list[Chunk] = load_chunks(knowledge_dir) if knowledge_dir else load_chunks()
    if not chunks:
        return []
    texts = [c.text for c in chunks]
    mat, backend = embed_texts(texts + [question])
    doc_mat, q_vec = mat[:-1], mat[-1:]
    scored = []
    for i, ch in enumerate(chunks):
        lex = _lexical_score(question, ch.text)
        qn = q_vec[0] / (np.linalg.norm(q_vec[0]) + 1e-8)
        dn = doc_mat[i] / (np.linalg.norm(doc_mat[i]) + 1e-8)
        dense = float(qn @ dn)
        hybrid = 0.45 * lex + 0.55 * max(dense, 0.0)
        scored.append((hybrid, lex, dense, ch))
    scored.sort(key=lambda x: x[0], reverse=True)
    # rerank: prefer chunks that mention query tokens in heading-ish first line
    qtok = _tokenize(question)
    reranked = []
    for hybrid, lex, dense, ch in scored:
        head = _tokenize(ch.text.split("\n", 1)[0])
        bonus = 0.05 * len(qtok & head)
        reranked.append((hybrid + bonus, lex, dense, ch, bonus))
    reranked.sort(key=lambda x: x[0], reverse=True)
    out = []
    for hybrid, lex, dense, ch, bonus in reranked[:top_k]:
        out.append({
            "doc_id": ch.doc_id,
            "title": ch.title,
            "snippet": ch.text[:500],
            "score": round(float(hybrid), 4),
            "lexical_score": round(float(lex), 4),
            "dense_score": round(float(dense), 4),
            "rerank_bonus": round(float(bonus), 4),
            "embedding_backend": backend,
            "citation": f"{ch.title} ({ch.doc_id})",
        })
    return out
