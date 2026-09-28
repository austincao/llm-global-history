#!/usr/bin/env python3
"""FastAPI RAG chat server for Global History visualization."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_deepseek import ChatDeepSeek
from pydantic import BaseModel, Field

from gh_pipeline.rag_entities import find_entities_in_citations
from gh_pipeline.rag_hybrid import HybridParagraphIndex

DEFAULT_INDEX = PROJECT_ROOT / "data/rag/paragraph_index.json"
DEFAULT_EMBEDDINGS = PROJECT_ROOT / "data/rag/paragraph_embeddings.npy"
DEFAULT_KB = PROJECT_ROOT / "data/unified_knowledge.json"

app = FastAPI(title="Global History RAG Chat", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_index: Optional[HybridParagraphIndex] = None
_index_path = DEFAULT_INDEX
_embeddings_path = DEFAULT_EMBEDDINGS
_kb_path = DEFAULT_KB


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    chapter_start: Optional[int] = Field(default=None, ge=1, le=44)
    chapter_end: Optional[int] = Field(default=None, ge=1, le=44)
    top_k: int = Field(default=5, ge=1, le=12)


class ChatResponse(BaseModel):
    answer: str
    citations: list[dict[str, Any]]
    entities: list[dict[str, Any]]
    mode: str
    retrieval: str


def get_index() -> HybridParagraphIndex:
    global _index
    if _index is None:
        if not _index_path.exists():
            raise HTTPException(
                status_code=503,
                detail=f"RAG index missing at {_index_path}. Run: uv run python scripts/build_rag_index.py",
            )
        _index = HybridParagraphIndex.load(_index_path, _embeddings_path)
    return _index


def retrieval_mode(index: HybridParagraphIndex) -> str:
    return "hybrid" if index.has_embeddings else "bm25"


def synthesize_with_llm(question: str, citations: list[dict[str, Any]]) -> str:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY not set")

    context_blocks = []
    for i, c in enumerate(citations, start=1):
        context_blocks.append(
            f"[{i}] 第{c['chapter_index']}章《{c['title_cn']}》第{c['paragraph_index']}段\n{c['text']}"
        )
    context = "\n\n".join(context_blocks)

    system = SystemMessage(
        content=(
            "你是《全球通史》阅读助手。仅根据提供的原文段落回答问题。"
            "回答使用中文，结构清晰。必须引用段落编号（如 [1][2]）。"
            "若原文不足以回答，请明确说明「原文未直接论述」。不要编造。"
        )
    )
    human = HumanMessage(content=f"问题：{question}\n\n原文段落：\n{context}")
    model = ChatDeepSeek(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        api_key=api_key,
        temperature=0.2,
    )
    response = model.invoke([system, human])
    return str(response.content).strip()


def retrieval_only_answer(question: str, citations: list[dict[str, Any]]) -> str:
    if not citations:
        return "未在当前章节范围内检索到相关段落。请尝试扩大章节范围或换种问法。"
    lines = [f"关于「{question}」，检索到以下原文段落（未调用 LLM 合成）：", ""]
    for i, c in enumerate(citations, start=1):
        lines.append(
            f"[{i}] 第{c['chapter_index']}章《{c['title_cn']}》第{c['paragraph_index']}段\n{c['text']}"
        )
        lines.append("")
    lines.append("提示：设置 DEEPSEEK_API_KEY 后可获得归纳式回答。")
    return "\n".join(lines)


@app.get("/health")
def health() -> dict[str, Any]:
    index_exists = _index_path.exists()
    embeddings_exists = _embeddings_path.exists()
    loaded = _index
    return {
        "ok": True,
        "index_loaded": loaded is not None,
        "index_path": str(_index_path),
        "index_exists": index_exists,
        "embeddings_exists": embeddings_exists,
        "retrieval": retrieval_mode(loaded) if loaded else ("hybrid" if embeddings_exists else "bm25"),
        "llm_available": bool(os.getenv("DEEPSEEK_API_KEY")),
    }


@app.get("/paragraphs/context")
def paragraph_context(
    chapter_index: int = Query(ge=1, le=44),
    paragraph_index: int = Query(ge=1),
    before: int = Query(default=2, ge=0, le=10),
    after: int = Query(default=2, ge=0, le=10),
) -> dict[str, Any]:
    index = get_index()
    items = index.get_chapter_context(chapter_index, paragraph_index, before=before, after=after)
    if not items:
        raise HTTPException(status_code=404, detail="Paragraph not found")
    return {
        "chapter_index": chapter_index,
        "focus_paragraph_index": paragraph_index,
        "paragraphs": [p.to_dict() for p in items],
    }


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    index = get_index()
    hits = index.search(
        req.question,
        top_k=req.top_k,
        chapter_start=req.chapter_start,
        chapter_end=req.chapter_end,
    )
    citations = [h.to_citation() for h in hits]
    entities = find_entities_in_citations(citations, _kb_path if _kb_path.exists() else None)

    retrieval = retrieval_mode(index)
    mode = "retrieval_only"
    try:
        if citations and os.getenv("DEEPSEEK_API_KEY"):
            answer = synthesize_with_llm(req.question, citations)
            mode = "llm"
        else:
            answer = retrieval_only_answer(req.question, citations)
    except Exception as exc:
        answer = retrieval_only_answer(req.question, citations)
        if citations:
            answer = f"{answer}\n\n（LLM 合成失败：{exc}）"

    return ChatResponse(
        answer=answer,
        citations=citations,
        entities=entities,
        mode=mode,
        retrieval=retrieval,
    )


def main() -> None:
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="Run RAG chat API server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--embeddings", type=Path, default=DEFAULT_EMBEDDINGS)
    parser.add_argument("--kb", type=Path, default=DEFAULT_KB)
    args = parser.parse_args()

    global _index_path, _embeddings_path, _kb_path
    _index_path = args.index
    _embeddings_path = args.embeddings
    _kb_path = args.kb

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
