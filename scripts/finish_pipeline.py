#!/usr/bin/env python3
"""Repair incomplete chapters, then resolve + publish + verify."""

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


def wait_for_batch(pid_hint: str = "batch_extract_chapters.py") -> None:
    import subprocess as sp

    while True:
        out = sp.run(["pgrep", "-f", pid_hint], capture_output=True, text=True)
        if out.returncode != 0:
            return
        print("[wait] batch still running...", flush=True)
        time.sleep(60)


def incomplete_chapters(start: int, end: int) -> list[int]:
    rc = run([sys.executable, "scripts/verify_extraction.py", "--start", str(start), "--end", str(end)])
    if rc == 0:
        return []
    import json

    out = subprocess.run(
        [sys.executable, "scripts/verify_extraction.py", "--start", str(start), "--end", str(end), "--json"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if out.returncode not in (0, 1) or not out.stdout.strip():
        raise RuntimeError(f"verify_extraction failed: {out.stderr or out.stdout}")
    data = json.loads(out.stdout)
    return [r["chapter"] for r in data if not r["ok"]]


def main() -> int:
    parser = argparse.ArgumentParser(description="Finish pipeline: repair, resolve, publish, verify")
    parser.add_argument("--start", type=int, default=23)
    parser.add_argument("--end", type=int, default=44)
    parser.add_argument("--wait-batch", action="store_true", help="Wait for running batch_extract to finish first")
    parser.add_argument("--max-repair-rounds", type=int, default=3)
    args = parser.parse_args()

    if args.wait_batch:
        wait_for_batch()

    for round_i in range(1, args.max_repair_rounds + 1):
        bad = incomplete_chapters(args.start, args.end)
        if not bad:
            print("All chapters complete.")
            break
        print(f"Repair round {round_i}: chapters {bad}")
        for ch in bad:
            rc = run([sys.executable, "scripts/extract_chapter.py", "--chapter", str(ch)])
            if rc != 0:
                print(f"[warn] chapter {ch} still has failures after extract")

    bad = incomplete_chapters(args.start, args.end)
    if bad:
        print(f"Still incomplete after repair: {bad}")
        return 1

    if run([sys.executable, "entity_resolution.py"]) != 0:
        return 1
    if run([sys.executable, "scripts/build_geography.py"]) != 0:
        return 1
    if run(["uv", "run", "pytest", "-q"]) != 0:
        return 1
    if run([sys.executable, "scripts/verify_extraction.py", "--start", str(args.start), "--end", str(args.end)]) != 0:
        return 1

    print("\n=== Pipeline verified OK ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
