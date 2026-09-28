"""Local embedding generation and storage for paragraph RAG."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import numpy as np

DEFAULT_MODEL = "BAAI/bge-small-zh-v1.5"


def embedding_text(title_cn: str, text: str) -> str:
    title = (title_cn or "").strip()
    body = (text or "").strip()
    if title and body:
        return f"{title}\n{body}"
    return title or body


def embed_texts(texts: list[str], *, model_name: str = DEFAULT_MODEL, batch_size: int = 64) -> np.ndarray:
    from fastembed import TextEmbedding

    model = TextEmbedding(model_name=model_name)
    vectors: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        vectors.extend(list(model.embed(batch)))
    arr = np.asarray(vectors, dtype=np.float32)
    if arr.ndim != 2:
        raise ValueError(f"Expected 2D embedding matrix, got shape {arr.shape}")
    return _l2_normalize_rows(arr)


def _l2_normalize_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms = np.clip(norms, 1e-12, None)
    return matrix / norms


def embed_query(query: str, *, model_name: str = DEFAULT_MODEL) -> np.ndarray:
    from fastembed import TextEmbedding

    model = TextEmbedding(model_name=model_name)
    vec = next(model.embed([query.strip() or " "]))
    arr = np.asarray(vec, dtype=np.float32)
    norm = np.linalg.norm(arr)
    if norm <= 1e-12:
        return arr
    return arr / norm


def save_embeddings(
    path: str | Path,
    *,
    paragraph_ids: list[str],
    vectors: np.ndarray,
    model_name: str,
) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.save(out, vectors.astype(np.float32))
    meta = {
        "version": "v1",
        "model": model_name,
        "dim": int(vectors.shape[1]) if vectors.ndim == 2 else 0,
        "count": len(paragraph_ids),
        "paragraph_ids": paragraph_ids,
    }
    out.with_suffix(".meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_embeddings(path: str | Path) -> tuple[np.ndarray, dict[str, Any]]:
    npy = Path(path)
    meta_path = npy.with_suffix(".meta.json")
    if not npy.exists() or not meta_path.exists():
        raise FileNotFoundError(f"Missing embeddings at {npy}")
    vectors = np.load(npy)
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if vectors.shape[0] != len(meta.get("paragraph_ids", [])):
        raise ValueError("Embedding row count does not match paragraph_ids metadata")
    return vectors.astype(np.float32), meta


def cosine_scores(query_vector: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    if matrix.size == 0:
        return np.asarray([], dtype=np.float32)
    q = query_vector.astype(np.float32)
    return matrix @ q
