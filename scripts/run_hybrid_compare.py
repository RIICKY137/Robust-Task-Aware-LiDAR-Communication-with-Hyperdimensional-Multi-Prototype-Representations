#!/usr/bin/env python3
"""Stage 5: hybrid neural-HDC vs pure HDC and binary hashing (clean + BER)."""

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
SEEDS = [0, 1, 2]
BERS = [0.0, 0.01, 0.05, 0.10]
METHODS = [
    ("binary_hash", {"dimension": 4096}),
    ("pure_hdc", {"dimension": 4096}),
    ("hybrid_hdc", {"dimension": 4096, "mode": "frozen"}),
    ("hybrid_hdc", {"dimension": 4096, "mode": "task"}),
    ("autoencoder", {}),
]
SPLIT = "test_id"


def main() -> None:
    batch, splits, _ = load_dataset("sim_indoor_v1")
    train = batch.subset(splits["train"])
    test = batch.subset(splits[SPLIT])
    out = raw_dir() / "hybrid_sweep.jsonl"
    if out.exists():
        out.unlink()
    for seed in SEEDS:
        for name, kw in METHODS:
            tag = kw.get("mode", name)
            print(f"fit {name}/{tag} seed={seed}")
            method = build_method(name, BUDGET, seed=seed, **kw)
            method.fit(train.ranges, train.labels, train.max_range)
            records = encode_fitted(method, test)
            for ber in BERS:
                channel = ChannelConfig(ber=ber, seed=seed)
                extra = {"hybrid_mode": kw.get("mode")}
                row = score_encoded(method, records, test, channel, seed, BUDGET, extra=extra)
                row.split = SPLIT
                append_jsonl(out, row)
                print(f"  ber={ber} acc={row.accuracy:.3f} bytes={row.actual_bytes:.1f}")
    print("wrote", out)


if __name__ == "__main__":
    main()
