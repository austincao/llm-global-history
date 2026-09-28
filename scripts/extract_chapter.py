#!/usr/bin/env python3
"""Extract entities/events/relations from one chapter via DeepSeek LLM."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_deepseek import ChatDeepSeek
from tqdm import tqdm

from gh_pipeline.llm_json import extract_json_from_response, sanitize_extraction_payload
from knowledge_store import ChunkExtraction, KnowledgeStore
from model.extraction import EntityRelationExtraction

from gh_pipeline.time_parsing import parse_chapter_title_years

CHUNK_SIZE = 5
CONTEXT_SIZE = 3
MAX_WORKERS = 4


def chapter_time_label(meta: dict, chapter_year_path: Path) -> str:
    title = meta.get("title_cn", "")
    title_range = parse_chapter_title_years(title)
    if title_range:
        if title_range.start_year < 0:
            start = f"公元前{abs(title_range.start_year)}"
        else:
            start = str(title_range.start_year)
        if title_range.end_year < 0:
            end = f"公元前{abs(title_range.end_year)}"
        else:
            end = str(title_range.end_year)
        return f"{start}—{end}年"

    if chapter_year_path.exists():
        idx = str(meta["chapter_index"])
        data = json.loads(chapter_year_path.read_text(encoding="utf-8"))
        start = data.get("chapter_start_year", {}).get(idx)
        end = data.get("chapter_end_year", {}).get(idx)
        if start is not None and end is not None:
            return f"{start}—{end}年"
    return ""
CONTEXT_SIZE = 3
MAX_WORKERS = 4


def load_chapter_paragraphs(adapted_path: Path, chapter_index: int) -> tuple[dict, list[str]]:
    data = json.loads(adapted_path.read_text(encoding="utf-8"))
    paragraphs = [p for p in data["paragraphs"] if p["chapter_index"] == chapter_index]
    if not paragraphs:
        raise SystemExit(f"Chapter {chapter_index} not found in {adapted_path}")
    meta = {
        "chapter_index": chapter_index,
        "title_cn": paragraphs[0]["title_cn"],
        "part_index": paragraphs[0]["part_index"],
        "part_title_cn": paragraphs[0]["part_title_cn"],
        "era": paragraphs[0]["era"],
    }
    sentences = [p["text"] for p in paragraphs]
    return meta, sentences


def build_chunks(sentences: list[str], chunk_size: int) -> list[tuple[int, int]]:
    return [(start, min(start + chunk_size, len(sentences))) for start in range(0, len(sentences), chunk_size)]


def process_chunk(
    *,
    chapter_meta: dict,
    sentences: list[str],
    chunk_start: int,
    chunk_end: int,
    segment_index: int,
    segment_start_time: str,
    sys_prompt: str,
    chat_model: ChatDeepSeek,
    store: KnowledgeStore,
) -> tuple[bool, str]:
    chapter_index = chapter_meta["chapter_index"]
    if store.has_chunk(chapter_index, segment_index, chunk_start):
        return True, f"skip existing chunk {chunk_start}"

    chunk_sentences = sentences[chunk_start:chunk_end]
    context_start = max(0, chunk_start - CONTEXT_SIZE)
    context_sentences = sentences[context_start:chunk_start]

    indexed_target = [f"[{chunk_start + i}]{s}" for i, s in enumerate(chunk_sentences)]
    indexed_context = [f"[{context_start + i}]{s}" for i, s in enumerate(context_sentences)]

    input_data = {
        "chapter_index": chapter_index,
        "chapter_title": chapter_meta["title_cn"],
        "era": chapter_meta["era"],
        "segment_index": segment_index,
        "segment_start_time": segment_start_time,
        "context_sentences": indexed_context,
        "target_sentences": indexed_target,
        "note": f"Paragraphs {chunk_start}..{chunk_end - 1} of {len(sentences)} in chapter {chapter_index}.",
    }

    conversation = [
        SystemMessage(sys_prompt),
        HumanMessage(json.dumps(input_data, ensure_ascii=False, indent=2)),
    ]

    for attempt in range(3):
        try:
            response = chat_model.invoke(conversation)
            er_data = sanitize_extraction_payload(extract_json_from_response(response.content))
            llm_extraction = EntityRelationExtraction(**er_data)

            for entity in llm_extraction.entities:
                entity.chapter_index = chapter_index
                entity.segment_index = segment_index
            for location in llm_extraction.locations:
                location.chapter_index = chapter_index
                location.segment_index = segment_index
            for event in llm_extraction.events:
                event.chapter_index = chapter_index
                event.segment_index = segment_index
            for relation in llm_extraction.relations:
                relation.chapter_index = chapter_index
                relation.segment_index = segment_index

            usage = response.response_metadata.get("token_usage", {})
            store.save_chunk(
                ChunkExtraction(
                    chapter_index=chapter_index,
                    segment_index=segment_index,
                    chunk_start_index=chunk_start,
                    chunk_end_index=chunk_end,
                    chapter_title=chapter_meta["title_cn"],
                    segment_start_time=segment_start_time,
                    source_sentences=chunk_sentences,
                    entities=llm_extraction.entities,
                    locations=llm_extraction.locations,
                    events=llm_extraction.events,
                    relations=llm_extraction.relations,
                    model_name=getattr(chat_model, "model_name", ""),
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0),
                )
            )
            return True, f"saved chunk {chunk_start}"
        except Exception as exc:
            if attempt == 2:
                return False, f"chunk {chunk_start} failed: {exc}"
            time.sleep(2)
    return False, "unreachable"


def main() -> int:
    parser = argparse.ArgumentParser(description="LLM extract one chapter from adapted_book.json")
    parser.add_argument("--chapter", type=int, default=22)
    parser.add_argument("--adapted-book", type=Path, default=Path("adapted_book.json"))
    parser.add_argument("--store-dir", type=Path, default=Path("data/store"))
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE)
    parser.add_argument("--max-workers", type=int, default=MAX_WORKERS)
    parser.add_argument("--limit-chunks", type=int, default=0, help="0 = all chunks")
    parser.add_argument("--force", action="store_true", help="Re-process even if cached")
    args = parser.parse_args()

    if not os.getenv("DEEPSEEK_API_KEY"):
        raise SystemExit("DEEPSEEK_API_KEY not set. Export from .env before running.")

    sys_prompt = (PROJECT_ROOT / "prompts/sys_entity_relation_extraction.md").read_text(encoding="utf-8")
    chapter_meta, sentences = load_chapter_paragraphs(args.adapted_book, args.chapter)
    chapter_year_path = PROJECT_ROOT / "data/chapter_year_index.json"
    segment_start_time = chapter_time_label(chapter_meta, chapter_year_path) or "未知年代"
    chunks = build_chunks(sentences, args.chunk_size)
    if args.limit_chunks:
        chunks = chunks[: args.limit_chunks]

    store = KnowledgeStore(str(args.store_dir))
    if args.force:
        chapter_file = args.store_dir / f"chapter_{args.chapter}.json"
        if chapter_file.exists():
            chapter_file.unlink()
        store = KnowledgeStore(str(args.store_dir))

    chat_model = ChatDeepSeek(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        temperature=0.1,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        disable_streaming=True,
    )

    print(f"Chapter {args.chapter}: {chapter_meta['title_cn']}")
    print(f"Paragraphs: {len(sentences)} | Chunks: {len(chunks)} (size={args.chunk_size})")

    failures = 0
    with ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        futures = {
            pool.submit(
                process_chunk,
                chapter_meta=chapter_meta,
                sentences=sentences,
                chunk_start=start,
                chunk_end=end,
                segment_index=1,
                sys_prompt=sys_prompt,
                chat_model=chat_model,
                store=store,
                segment_start_time=segment_start_time,
            ): start
            for start, end in chunks
        }
        for future in tqdm(as_completed(futures), total=len(futures), desc=f"Ch{args.chapter}"):
            ok, msg = future.result()
            if not ok:
                failures += 1
                print(msg)

    print(store.summary())
    if failures:
        raise SystemExit(f"{failures} chunks failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
