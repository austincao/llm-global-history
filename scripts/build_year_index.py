#!/usr/bin/env python3
"""Build segment + chapter year indexes and publish to visualization."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print("+ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build year indexes end-to-end")
    parser.add_argument("--no-publish", action="store_true")
    parser.add_argument("--validate", action="store_true", help="Run advisory validation (no-op for now)")
    args = parser.parse_args()

    seg_cmd = [sys.executable, "scripts/build_segment_year_index.py"]
    if args.validate:
        seg_cmd.extend(["--validate", "--fail-on-validate"])

    run(seg_cmd)
    run([sys.executable, "scripts/build_chapter_year_index.py"])

    chapter_index = PROJECT_ROOT / "data/chapter_year_index.json"
    viz_year = PROJECT_ROOT / "visualization/public/data/juan_year_index.json"
    viz_year.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(chapter_index, viz_year)
    print(f"Copied {chapter_index} -> {viz_year}")

    if not args.no_publish:
        run([sys.executable, "scripts/publish_visualization_data.py"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
