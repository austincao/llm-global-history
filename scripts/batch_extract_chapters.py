#!/usr/bin/env python3
"""Batch LLM extraction for multiple chapters with resume and optional resolve/publish."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHUNK_SIZE = 5
PROGRESS_FILE = "batch_progress.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_adapted_book(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def expected_chunk_count(book: dict, chapter_index: int, chunk_size: int) -> int:
    n = sum(1 for p in book["paragraphs"] if p["chapter_index"] == chapter_index)
    if n == 0:
        return 0
    return (n + chunk_size - 1) // chunk_size


def is_chapter_complete(store_dir: Path, chapter_index: int, expected_chunks: int) -> bool:
    if expected_chunks <= 0:
        return False
    chapter_file = store_dir / f"chapter_{chapter_index}.json"
    if not chapter_file.exists():
        return False
    data = json.loads(chapter_file.read_text(encoding="utf-8"))
    chunks = sum(1 for v in data.values() if isinstance(v, dict))
    return chunks >= expected_chunks


def run_cmd(cmd: list[str], *, dry_run: bool = False) -> int:
    print("+ " + " ".join(cmd), flush=True)
    if dry_run:
        return 0
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode


def load_progress(store_dir: Path) -> dict:
    path = store_dir / PROGRESS_FILE
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_progress(store_dir: Path, state: dict) -> None:
    store_dir.mkdir(parents=True, exist_ok=True)
    (store_dir / PROGRESS_FILE).write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def print_plan(book: dict, chapters: list[int], store_dir: Path) -> None:
    total_chunks = 0
    pending = 0
    for ch in chapters:
        exp = expected_chunk_count(book, ch, CHUNK_SIZE)
        total_chunks += exp
        if is_chapter_complete(store_dir, ch, exp):
            status = "done"
        else:
            status = "pending"
            pending += exp
        title = next(
            (p["title_cn"] for p in book["paragraphs"] if p["chapter_index"] == ch),
            f"chapter {ch}",
        )
        print(f"  Ch{ch:2d}  {exp:3d} chunks  [{status:7s}]  {title[:40]}")
    print(f"Total chunks: {total_chunks} | Pending: {pending}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch extract chapters 23–44 (or custom range)")
    parser.add_argument("--start", type=int, default=23, help="First chapter (inclusive)")
    parser.add_argument("--end", type=int, default=44, help="Last chapter (inclusive)")
    parser.add_argument("--adapted-book", type=Path, default=Path("adapted_book.json"))
    parser.add_argument("--store-dir", type=Path, default=Path("data/store"))
    parser.add_argument("--force", action="store_true", help="Re-extract even if chapter cache looks complete")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first chapter failure")
    parser.add_argument("--dry-run", action="store_true", help="Print plan only, do not call API")
    parser.add_argument("--skip-resolve", action="store_true", help="Skip entity_resolution after extraction")
    parser.add_argument("--skip-publish", action="store_true", help="Skip geocode + visualization publish")
    parser.add_argument("--resolve-only", action="store_true", help="Only run resolve + publish (no extract)")
    args = parser.parse_args()

    if args.start > args.end:
        raise SystemExit("--start must be <= --end")

    if not args.adapted_book.exists():
        raise SystemExit(f"Missing {args.adapted_book}. Run ingest_book.py first.")

    if not args.dry_run and not args.resolve_only and not os.getenv("DEEPSEEK_API_KEY"):
        raise SystemExit("DEEPSEEK_API_KEY not set.")

    book = load_adapted_book(args.adapted_book)
    chapters = list(range(args.start, args.end + 1))

    print(f"Batch extract chapters {args.start}–{args.end}")
    print_plan(book, chapters, args.store_dir)

    state = load_progress(args.store_dir)
    state.update(
        {
            "updated_at": now_iso(),
            "range": [args.start, args.end],
            "completed": state.get("completed", []),
            "failed": state.get("failed", []),
            "skipped": [],
        }
    )
    if "started_at" not in state:
        state["started_at"] = now_iso()

    if not args.resolve_only:
        for chapter in chapters:
            expected = expected_chunk_count(book, chapter, CHUNK_SIZE)
            if expected == 0:
                print(f"[warn] chapter {chapter} has no paragraphs, skipping")
                continue

            if not args.force and is_chapter_complete(args.store_dir, chapter, expected):
                print(f"[skip] chapter {chapter} complete ({len(json.loads((args.store_dir / f'chapter_{chapter}.json').read_text()))}/{expected} chunks)")
                state["skipped"].append(chapter)
                save_progress(args.store_dir, state)
                continue

            if args.dry_run:
                print(f"[dry-run] extract chapter {chapter} ({expected} chunks)")
                continue

            print(f"\n=== Chapter {chapter} ({expected} chunks) ===")
            cmd = [sys.executable, "scripts/extract_chapter.py", "--chapter", str(chapter)]
            if args.force:
                cmd.append("--force")
            rc = run_cmd(cmd)
            if rc != 0:
                entry = {"chapter": chapter, "stage": "extract", "at": now_iso()}
                state["failed"] = [f for f in state.get("failed", []) if f.get("chapter") != chapter]
                state["failed"].append(entry)
                save_progress(args.store_dir, state)
                print(f"[fail] chapter {chapter} extract exit={rc}")
                if args.fail_fast:
                    return rc
                continue

            if chapter not in state["completed"]:
                state["completed"].append(chapter)
            state["failed"] = [f for f in state.get("failed", []) if f.get("chapter") != chapter]
            save_progress(args.store_dir, state)
            print(f"[ok] chapter {chapter}")

    if args.dry_run:
        return 0

    if not args.skip_resolve:
        print("\n=== Entity resolution (all chapters in store) ===")
        rc = run_cmd([sys.executable, "entity_resolution.py"])
        if rc != 0:
            return rc

    if not args.skip_publish:
        print("\n=== Geocode + publish visualization ===")
        rc = run_cmd([sys.executable, "scripts/build_geography.py"])
        if rc != 0:
            return rc

    state["finished_at"] = now_iso()
    save_progress(args.store_dir, state)
    print("\nBatch finished.")
    print(f"  completed: {sorted(state.get('completed', []))}")
    print(f"  skipped:   {sorted(state.get('skipped', []))}")
    if state.get("failed"):
        print(f"  failed:    {state['failed']}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
