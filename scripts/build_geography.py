#!/usr/bin/env python3
"""Geocode locations, merge into KB, and publish visualization data."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print("+ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Geocode + merge + publish for visualization")
    parser.add_argument("--offline", action="store_true", help="Only use known_coordinates hints")
    parser.add_argument("--force-geocode", action="store_true")
    args = parser.parse_args()

    geo_cmd = [sys.executable, "scripts/geocode_locations.py"]
    if args.offline:
        geo_cmd.append("--offline")
    if args.force_geocode:
        geo_cmd.append("--force")

    run(geo_cmd)
    run([sys.executable, "scripts/merge_geocoding_into_unified_kb.py"])
    run([sys.executable, "scripts/publish_visualization_data.py"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
