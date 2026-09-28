"""Hybrid BM25 + embedding retrieval index."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

from gh_pipeline.rag_embeddings import (
    DEFAULT_MODEL,
    cosine_scores,
    embed_query,
    embedding_text,
    load_embeddings,
    save_embeddings,
    embed_texts,
)
from gh_pipeline.rag_index import ParagraphIndex, ParagraphRecord, SearchHit, load_paragraphs_from_adapted_book


@dataclass
class HybridSearchConfig:
    embedding_weight: float = 0.75
    bm25_weight: float = 0.25


class HybridParagraphIndex:
    """Paragraph retrieval with BM25 fallback and optional embedding rerank."""

    def __init__(
        self,
        bm25_index: ParagraphIndex,
        *,
        embeddings: Optional[np.ndarray] = None,
        embedding_model: Optional[str] = None,
        id_to_row: Optional[dict[str, int]] = None,
        config: Optional[HybridSearchConfig] = None,
    ) -> None:
        self.bm25_index = bm25_index
        self.embeddings = embeddings
        self.embedding_model = embedding_model
        self.id_to_row = id_to_row or {}
        self.config = config or HybridSearchConfig()

    @property
    def paragraphs(self) -> list[ParagraphRecord]:
        return self.bm25_index.paragraphs

    @property
    def has_embeddings(self) -> bool:
        return self.embeddings is not None and self.embeddings.size > 0

    def paragraph_by_id(self, paragraph_id: str) -> Optional[ParagraphRecord]:
        row = self.id_to_row.get(paragraph_id)
        if row is None:
            for para in self.paragraphs:
                if para.id == paragraph_id:
                    return para
            return None
        return self.paragraphs[row]

    def get_chapter_context(
        self,
        chapter_index: int,
        paragraph_index: int,
        *,
        before: int = 2,
        after: int = 2,
    ) -> list[ParagraphRecord]:
        items = [
            p
            for p in self.paragraphs
            if p.chapter_index == chapter_index
            and (paragraph_index - before) <= p.paragraph_index <= (paragraph_index + after)
        ]
        items.sort(key=lambda p: p.paragraph_index)
        return items

    def _filter_doc_ids(
        self,
        chapter_start: Optional[int],
        chapter_end: Optional[int],
    ) -> list[int]:
        doc_ids: list[int] = []
        for doc_id, para in enumerate(self.paragraphs):
            if chapter_start is not None and para.chapter_index < chapter_start:
                continue
            if chapter_end is not None and para.chapter_index > chapter_end:
                continue
            doc_ids.append(doc_id)
        return doc_ids

    @staticmethod
    def _normalize_scores(scores: dict[int, float]) -> dict[int, float]:
        if not scores:
            return {}
        values = list(scores.values())
        lo, hi = min(values), max(values)
        if hi - lo <= 1e-12:
            return {k: 1.0 if v > 0 else 0.0 for k, v in scores.items()}
        return {k: (v - lo) / (hi - lo) for k, v in scores.items()}

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        chapter_start: Optional[int] = None,
        chapter_end: Optional[int] = None,
    ) -> list[SearchHit]:
        if not self.paragraphs:
            return []

        doc_ids = self._filter_doc_ids(chapter_start, chapter_end)
        if not doc_ids:
            return []

        bm25_scores: dict[int, float] = {}
        for hit in self.bm25_index.search(
            query,
            top_k=max(top_k * 4, 20),
            chapter_start=chapter_start,
            chapter_end=chapter_end,
        ):
            row = self.id_to_row.get(hit.paragraph.id)
            if row is None:
                for i, para in enumerate(self.paragraphs):
                    if para.id == hit.paragraph.id:
                        row = i
                        break
            if row is not None:
                bm25_scores[row] = max(bm25_scores.get(row, 0.0), hit.score)

        embed_scores: dict[int, float] = {}
        if self.has_embeddings and self.embedding_model:
            query_vec = embed_query(query, model_name=self.embedding_model)
            for doc_id in doc_ids:
                embed_scores[doc_id] = float(cosine_scores(query_vec, self.embeddings[doc_id : doc_id + 1])[0])

        if not embed_scores:
            hits = self.bm25_index.search(
                query,
                top_k=top_k,
                chapter_start=chapter_start,
                chapter_end=chapter_end,
            )
            return hits

        bm25_norm = self._normalize_scores({k: v for k, v in bm25_scores.items() if k in doc_ids})
        embed_norm = self._normalize_scores({k: v for k, v in embed_scores.items() if k in doc_ids})

        combined: dict[int, float] = {}
        for doc_id in doc_ids:
            combined[doc_id] = (
                self.config.embedding_weight * embed_norm.get(doc_id, 0.0)
                + self.config.bm25_weight * bm25_norm.get(doc_id, 0.0)
            )

        ranked = sorted(combined.items(), key=lambda item: item[1], reverse=True)[:top_k]
        return [
            SearchHit(paragraph=self.paragraphs[doc_id], score=score)
            for doc_id, score in ranked
            if score > 0
        ]

    @classmethod
    def load(
        cls,
        index_path: str | Path,
        embeddings_path: Optional[str | Path] = None,
    ) -> HybridParagraphIndex:
        bm25_index = ParagraphIndex.load(index_path)
        id_to_row = {para.id: i for i, para in enumerate(bm25_index.paragraphs)}

        embeddings = None
        embedding_model = None
        emb_path = Path(embeddings_path or Path(index_path).with_name("paragraph_embeddings.npy"))
        if emb_path.exists():
            embeddings, meta = load_embeddings(emb_path)
            meta_ids = meta.get("paragraph_ids") or []
            if meta_ids != [p.id for p in bm25_index.paragraphs]:
                raise ValueError("Embedding paragraph_ids do not match paragraph_index.json order")
            embedding_model = meta.get("model") or DEFAULT_MODEL

        return cls(
            bm25_index,
            embeddings=embeddings,
            embedding_model=embedding_model,
            id_to_row=id_to_row,
        )

    @classmethod
    def build_from_adapted_book(
        cls,
        adapted_book_path: str | Path,
        *,
        model_name: str = DEFAULT_MODEL,
        skip_embeddings: bool = False,
    ) -> tuple["HybridParagraphIndex", ParagraphIndex]:
        paragraphs = load_paragraphs_from_adapted_book(adapted_book_path)
        bm25_index = ParagraphIndex(paragraphs)
        id_to_row = {para.id: i for i, para in enumerate(paragraphs)}

        embeddings = None
        if not skip_embeddings and paragraphs:
            texts = [embedding_text(p.title_cn, p.text) for p in paragraphs]
            embeddings = embed_texts(texts, model_name=model_name)

        return (
            cls(
                bm25_index,
                embeddings=embeddings,
                embedding_model=model_name if embeddings is not None else None,
                id_to_row=id_to_row,
            ),
            bm25_index,
        )


def persist_hybrid_index(
    hybrid: HybridParagraphIndex,
    bm25_index: ParagraphIndex,
    *,
    index_path: str | Path,
    embeddings_path: str | Path,
) -> None:
    from gh_pipeline.rag_index import save_index

    save_index(bm25_index, index_path)
    if hybrid.has_embeddings and hybrid.embeddings is not None and hybrid.embedding_model:
        save_embeddings(
            embeddings_path,
            paragraph_ids=[p.id for p in bm25_index.paragraphs],
            vectors=hybrid.embeddings,
            model_name=hybrid.embedding_model,
        )
