#!/usr/bin/env python3
"""Stage 2: packet loss on fixed-size packets (zeros for missing packets)."""

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
PACKET_BYTES = 32
SEEDS = [0, 1, 2, 3, 4]
PLRS = [0.0, 0.01, 0.05, 0.10, 0.20, 0.40]
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
    out = raw_dir() / "packet_loss_sweep.jsonl"
    if out.exists():
        out.unlink()
    for seed in SEEDS:
        for name, kw in METHODS:
            print(f"fit {name} seed={seed}")
            method = build_method(name, BUDGET, seed=seed, **kw)
            method.fit(train.ranges, train.labels, train.max_range)
            records = encode_fitted(method, test)
            for plr in PLRS:
                channel = ChannelConfig(packet_bytes=PACKET_BYTES, packet_loss_rate=plr, seed=seed)
                row = score_encoded(method, records, test, channel, seed, BUDGET)
                row.split = SPLIT
                append_jsonl(out, row)
                print(f"  plr={plr} acc={row.accuracy:.3f}")
    print("wrote", out)


if __name__ == "__main__":
    main()
