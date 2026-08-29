#!/usr/bin/env python3
"""Stage 1: Accuracy–Bandwidth at BER = 0 (first-round matrix)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hdc_lidar.data.io import load_dataset  # noqa: E402
from hdc_lidar.experiment import append_jsonl, raw_dir, run_cell  # noqa: E402
from hdc_lidar.types import ChannelConfig  # noqa: E402

METHODS = [
    ("quantized", {}),
    ("pca", {}),
    ("binary_hash", {}),
    ("pure_hdc", {"dimension": 1024}),
    ("pure_hdc", {"dimension": 4096}),
    ("pure_hdc", {"dimension": 8192}),
]
BUDGETS = [128, 512, 2048]
SEEDS = [0, 1, 2]
SPLIT = "test_id"


def main() -> None:
    batch, splits, _ = load_dataset("sim_indoor_v1")
    train = batch.subset(splits["train"])
    test = batch.subset(splits[SPLIT])
    out = raw_dir() / "bandwidth_sweep.jsonl"
    channel = ChannelConfig(ber=0.0)
    for seed in SEEDS:
        for budget in BUDGETS:
            for name, kw in METHODS:
                dim = kw.get("dimension")
                if dim is not None and dim > budget * 8:
                    continue
                print(f"seed={seed} method={name} budget={budget} dim={dim}")
                row, _ = run_cell(
                    name,
                    budget,
                    train,
                    test,
                    channel,
                    seed=seed,
                    method_kwargs=kw,
                    time_repeats=4,
                )
                row.split = SPLIT
                append_jsonl(out, row)
                print(f"  acc={row.accuracy:.3f} bytes={row.actual_bytes:.1f}")
    print("wrote", out)


if __name__ == "__main__":
    main()
