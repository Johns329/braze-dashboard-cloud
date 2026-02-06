"""Run the full ETL (extract + parse).

Usage:
  python etl/run_etl.py
  python etl/run_etl.py --env-file .env
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--env-file",
        default=None,
        help="Path to a .env file (passed through to extract step)",
    )
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    extract = os.path.join(base_dir, "etl", "extract_braze.py")
    parse = os.path.join(base_dir, "etl", "parse_liquid.py")

    extract_cmd = [sys.executable, extract]
    if args.env_file:
        extract_cmd.extend(["--env-file", args.env_file])

    print("=== 1) Extracting raw snapshots from Braze ===")
    r1 = subprocess.run(extract_cmd, cwd=base_dir)
    if r1.returncode != 0:
        print("Extraction failed; continuing to parse using existing local files...")

    print("\n=== 2) Parsing snapshots into CSV tables ===")
    r2 = subprocess.run([sys.executable, parse], cwd=base_dir)
    return r2.returncode


if __name__ == "__main__":
    raise SystemExit(main())
