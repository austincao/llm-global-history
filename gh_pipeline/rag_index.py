"""BM25 paragraph retrieval over adapted_book.json for RAG chat."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

TOKEN_RE = re.compile(r"[\u4e00-\u9fff]|[a-zA-Z]{2,}|\d+")


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text or "")]


@dataclass(frozen=True)
class ParagraphRecord:
    id: str
    chapter_index: int
    paragraph_index: int
    part_index: int
    part_title_cn: str
    era: str
    title_cn: str
    text: str
    segment_start_time_raw: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "chapter_index": self.chapter_index,
            "paragraph_index": self.paragraph_index,
            "part_index": self.part_index,
            "part_title_cn": self.part_title_cn,
            "era": self.era,
            "title_cn": self.title_cn,
            "text": self.text,
            "segment_start_time_raw": self.segment_start_time_raw,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ParagraphRecord:
        return cls(
            id=str(data["id"]),
            chapter_index=int(data["chapter_index"]),
            paragraph_index=int(data["paragraph_index"]),
            part_index=int(data.get("part_index", 0)),
            part_title_cn=str(data.get("part_title_cn", "")),
            era=str(data.get("era", "")),
            title_cn=str(data.get("title_cn", "")),
            text=str(data.get("text", "")),
            segment_start_time_raw=data.get("segment_start_time_raw"),
        )


@dataclass
class SearchHit:
    paragraph: ParagraphRecord
    score: float

    def to_citation(self) -> dict[str, Any]:
        p = self.paragraph
        return {
            "id": p.id,
            "chapter_index": p.chapter_index,
            "paragraph_index": p.paragraph_index,
            "part_title_cn": p.part_title_cn,
            "title_cn": p.title_cn,
            "era": p.era,
            "segment_start_time_raw": p.segment_start_time_raw,
            "text": p.text,
            "score": round(self.score, 4),
        }


class ParagraphIndex:
    """In-memory BM25 index over book paragraphs."""

    def __init__(
        self,
        paragraphs: list[ParagraphRecord],
        *,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self.paragraphs = paragraphs
        self.k1 = k1
        self.b = b
        self._tokenized: list[list[str]] = []
        self._doc_lengths: list[int] = []
        self._avg_dl = 0.0
        self._df: dict[str, int] = {}
        self._postings: dict[str, list[tuple[int, int]]] = {}
        self._build()

    def _build(self) -> None:
        for para in self.paragraphs:
            tokens = tokenize(para.text)
            self._tokenized.append(tokens)
            self._doc_lengths.append(len(tokens))

        n = len(self.paragraphs)
        self._avg_dl = (sum(self._doc_lengths) / n) if n else 0.0

        for doc_id, tokens in enumerate(self._tokenized):
            counts: dict[str, int] = {}
            for tok in tokens:
                counts[tok] = counts.get(tok, 0) + 1
            for tok, tf in counts.items():
                self._df[tok] = self._df.get(tok, 0) + 1
                self._postings.setdefault(tok, []).append((doc_id, tf))

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

        q_tokens = tokenize(query)
        if not q_tokens:
            return []

        n = len(self.paragraphs)
        scores = [0.0] * n

        for tok in q_tokens:
            df = self._df.get(tok, 0)
            if df == 0:
                continue
            idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
            for doc_id, tf in self._postings.get(tok, []):
                dl = self._doc_lengths[doc_id]
                denom = tf + self.k1 * (1 - self.b + self.b * dl / (self._avg_dl or 1))
                scores[doc_id] += idf * (tf * (self.k1 + 1)) / denom

        hits: list[SearchHit] = []
        for doc_id, score in enumerate(scores):
            if score <= 0:
                continue
            para = self.paragraphs[doc_id]
            if chapter_start is not None and para.chapter_index < chapter_start:
                continue
            if chapter_end is not None and para.chapter_index > chapter_end:
                continue
            hits.append(SearchHit(paragraph=para, score=score))

        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:top_k]

    def to_json(self) -> dict[str, Any]:
        return {
            "version": "v1",
            "algorithm": "bm25",
            "paragraph_count": len(self.paragraphs),
            "paragraphs": [p.to_dict() for p in self.paragraphs],
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> ParagraphIndex:
        paragraphs = [ParagraphRecord.from_dict(p) for p in data.get("paragraphs", [])]
        return cls(paragraphs)

    @classmethod
    def load(cls, path: str | Path) -> ParagraphIndex:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_json(payload)


def load_paragraphs_from_adapted_book(path: str | Path) -> list[ParagraphRecord]:
    book = json.loads(Path(path).read_text(encoding="utf-8"))
    paragraphs: list[ParagraphRecord] = []
    for item in book.get("paragraphs", []):
        chapter_index = int(item["chapter_index"])
        paragraph_index = int(item["paragraph_index"])
        paragraphs.append(
            ParagraphRecord(
                id=f"{chapter_index}-{paragraph_index}",
                chapter_index=chapter_index,
                paragraph_index=paragraph_index,
                part_index=int(item.get("part_index", 0)),
                part_title_cn=str(item.get("part_title_cn", "")),
                era=str(item.get("era", "")),
                title_cn=str(item.get("title_cn", "")),
                text=str(item.get("text", "")),
                segment_start_time_raw=item.get("segment_start_time_raw"),
            )
        )
    return paragraphs


def build_index_from_adapted_book(path: str | Path) -> ParagraphIndex:
    return ParagraphIndex(load_paragraphs_from_adapted_book(path))


def save_index(index: ParagraphIndex, path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(index.to_json(), ensure_ascii=False, indent=2), encoding="utf-8")
