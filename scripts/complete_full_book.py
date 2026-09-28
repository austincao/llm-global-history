#!/usr/bin/env python3
"""After post-1500 chapters are done, extract 1–21 and finalize the full book (1–44)."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> int:
    print("+ " + " ".join(cmd), flush=True)
    return subprocess.run(cmd, cwd=PROJECT_ROOT).returncode


def wait_for_process(pattern: str, label: str) -> None:
    while True:
        out = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True)
        if out.returncode != 0:
            print(f"[done] {label} finished", flush=True)
            return
        print(f"[wait] {label} still running...", flush=True)
        time.sleep(60)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Complete full book: wait post-1500 finish → extract ch1-21 → verify 1-44"
    )
    parser.add_argument("--wait-finish", action="store_true", help="Wait for finish_pipeline.py to exit first")
    parser.add_argument("--skip-wait", action="store_true", help="Do not wait (post-1500 already done)")
    parser.add_argument("--pre-start", type=int, default=1, help="Ancient chapters start")
    parser.add_argument("--pre-end", type=int, default=21, help="Ancient chapters end")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.skip_wait:
        if args.wait_finish:
            wait_for_process("finish_pipeline.py", "finish_pipeline (22–44)")
        else:
            wait_for_process("batch_extract_chapters.py", "batch_extract (23–44)")

    print(f"\n=== Phase 2: extract chapters {args.pre_start}–{args.pre_end} (~617 chunks) ===")
    batch_cmd = [
        sys.executable,
        "scripts/batch_extract_chapters.py",
        "--start",
        str(args.pre_start),
        "--end",
        str(args.pre_end),
        "--skip-resolve",
        "--skip-publish",
    ]
    if args.dry_run:
        batch_cmd.append("--dry-run")
    if run(batch_cmd) != 0 and not args.dry_run:
        # batch may exit 1 due to stale progress flags; continue if chapters look complete
        rc = run(
            [
                sys.executable,
                "scripts/verify_extraction.py",
                "--start",
                str(args.pre_start),
                "--end",
                str(args.pre_end),
            ]
        )
        if rc != 0:
            return 1
        print("[warn] batch_extract returned non-zero but all chapters in range are complete")

    if args.dry_run:
        print("[dry-run] would run finish_pipeline 1–44")
        return 0

    print("\n=== Phase 3: repair + merge + geocode + verify (chapters 1–44) ===")
    return run(
        [
            sys.executable,
            "scripts/finish_pipeline.py",
            "--start",
            "1",
            "--end",
            "44",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
