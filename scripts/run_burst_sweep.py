#!/usr/bin/env python3
"""Stage 2: contiguous burst errors, with and without bit interleaving."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hdc_lidar.data.io import load_dataset  # noqa: E402
from hdc_lidar.experiment import append_jsonl, encode_fitted, raw_dir, score_encoded  # noqa: E402
from hdc_lidar.methods import build_method  # noqa: E402
from hdc_lidar.types import ChannelConfig  # noqa: E402

BUDGET = 512
SEEDS = [0, 1, 2, 3, 4]
BURST_LENGTHS = [0, 32, 128, 512, 1024]
METHODS = [
    ("quantized", {}),
    ("pca", {}),
    ("binary_hash", {"dimension": 4096}),
    ("pure_hdc", {"dimension": 4096}),
]
SPLIT = "test_id"


def main() -> None:
    batch, splits, _ = load_dataset("sim_indoor_v1")
    train = batch.subset(splits["train"])
    test = batch.subset(splits[SPLIT])
    out = raw_dir() / "burst_sweep.jsonl"
    if out.exists():
        out.unlink()
    for seed in SEEDS:
        for name, kw in METHODS:
            print(f"fit {name} seed={seed}")
            method = build_method(name, BUDGET, seed=seed, **kw)
            method.fit(train.ranges, train.labels, train.max_range)
            records = encode_fitted(method, test)
            for length in BURST_LENGTHS:
                for interleave in (False, True):
                    if length == 0 and interleave:
                        continue
                    n_bursts = 0 if length == 0 else 1
                    channel = ChannelConfig(
                        burst_length=length,
                        n_bursts=n_bursts,
                        interleave=interleave,
                        seed=seed,
                    )
                    row = score_encoded(method, records, test, channel, seed, BUDGET)
                    row.split = SPLIT
                    append_jsonl(out, row)
                    print(
                        f"  burst={length} interleave={interleave} acc={row.accuracy:.3f}"
                    )
    print("wrote", out)


if __name__ == "__main__":
    main()
