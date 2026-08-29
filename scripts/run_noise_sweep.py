#!/usr/bin/env python3
"""Stage 2: Accuracy–BER at a fixed 512-byte budget (first-round matrix)."""

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
    ("binary_hash", {"dimension": 4096}),
    ("pure_hdc", {"dimension": 4096}),
]
BERS = [0.0, 0.01, 0.05, 0.10]
SEEDS = [0, 1, 2]
BUDGET = 512
SPLIT = "test_id"


def main() -> None:
    batch, splits, _ = load_dataset("sim_indoor_v1")
    train = batch.subset(splits["train"])
    test = batch.subset(splits[SPLIT])
    out = raw_dir() / "noise_sweep.jsonl"
    for seed in SEEDS:
        for ber in BERS:
            for name, kw in METHODS:
                print(f"seed={seed} method={name} ber={ber}")
                row, _ = run_cell(
                    name,
                    BUDGET,
                    train,
                    test,
                    ChannelConfig(ber=ber, seed=seed),
                    seed=seed,
                    method_kwargs=kw,
                    time_repeats=4,
                )
                row.split = SPLIT
                append_jsonl(out, row)
                print(f"  acc={row.accuracy:.3f}")
    print("wrote", out)


if __name__ == "__main__":
    main()
