#!/usr/bin/env python3
"""Build paragraph BM25 index and optional embedding vectors for RAG chat."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from gh_pipeline.rag_embeddings import DEFAULT_MODEL
from gh_pipeline.rag_hybrid import persist_hybrid_index, HybridParagraphIndex


def main() -> None:
    parser = argparse.ArgumentParser(description="Build RAG paragraph index")
    parser.add_argument("--adapted-book", type=Path, default=Path("adapted_book.json"))
    parser.add_argument("--output", type=Path, default=Path("data/rag/paragraph_index.json"))
    parser.add_argument(
        "--embeddings-output",
        type=Path,
        default=Path("data/rag/paragraph_embeddings.npy"),
    )
    parser.add_argument("--embedding-model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Only build BM25 index (faster, semantic search disabled)",
    )
    args = parser.parse_args()

    if not args.adapted_book.exists():
        raise SystemExit(f"Missing {args.adapted_book}. Run ingest_book.py first.")

    hybrid, bm25_index = HybridParagraphIndex.build_from_adapted_book(
        args.adapted_book,
        model_name=args.embedding_model,
        skip_embeddings=args.skip_embeddings,
    )
    persist_hybrid_index(
        hybrid,
        bm25_index,
        index_path=args.output,
        embeddings_path=args.embeddings_output,
    )

    mode = "hybrid (BM25 + embeddings)" if hybrid.has_embeddings else "bm25 only"
    print(f"Saved {len(bm25_index.paragraphs)} paragraphs -> {args.output}")
    if hybrid.has_embeddings:
        print(f"Saved embeddings -> {args.embeddings_output} [{args.embedding_model}]")
    print(f"Retrieval mode: {mode}")


if __name__ == "__main__":
    main()
