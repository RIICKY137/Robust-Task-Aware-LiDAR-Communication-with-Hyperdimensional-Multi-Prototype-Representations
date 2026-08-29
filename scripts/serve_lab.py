#!/usr/bin/env python3
"""Launch the Streamlit lab on a non-default port."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "src" / "hdc_lidar" / "lab.py"


def main() -> None:
    port = sys.argv[1] if len(sys.argv) > 1 else "43187"
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(LAB),
        "--server.port",
        port,
        "--server.address",
        "0.0.0.0",
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
    ]
    raise SystemExit(subprocess.call(cmd, cwd=ROOT))


if __name__ == "__main__":
    main()
