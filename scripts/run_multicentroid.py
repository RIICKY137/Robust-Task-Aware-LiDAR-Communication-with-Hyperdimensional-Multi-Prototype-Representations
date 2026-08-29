#!/usr/bin/env python3
"""Multi-centroid HDC vs single prototype vs linear head (same P⊗L payload)."""

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
SPLITS = ["test_id", "test_ood"]
METHODS = [
    ("binary_hash", {"dimension": 4096}),
    ("pure_hdc", {"dimension": 4096, "head": "prototype", "n_centroids": 1}),
    ("pure_hdc", {"dimension": 4096, "head": "prototype", "n_centroids": 4}),
    ("pure_hdc", {"dimension": 4096, "head": "prototype", "n_centroids": 8}),
    ("pure_hdc", {"dimension": 4096, "head": "prototype", "n_centroids": 16}),
    ("pure_hdc", {"dimension": 4096, "head": "linear", "n_centroids": 1}),
]


def _tag(name: str, kw: dict) -> str:
    if name != "pure_hdc":
        return name
    if kw.get("head") == "linear":
        return "pure_hdc/linear"
    return f"pure_hdc/k{kw.get('n_centroids', 1)}"


def main() -> None:
    batch, splits, _ = load_dataset("sim_indoor_v1")
    train = batch.subset(splits["train"])
    out = raw_dir() / "multicentroid_sweep.jsonl"
    if out.exists():
        out.unlink()
    for seed in SEEDS:
        for name, kw in METHODS:
            tag = _tag(name, kw)
            print(f"fit {tag} seed={seed}")
            method = build_method(name, BUDGET, seed=seed, **kw)
            method.fit(train.ranges, train.labels, train.max_range)
            extra = {
                "hdc_head": kw.get("head"),
                "n_centroids": kw.get("n_centroids", 1),
            }
            for split_name in SPLITS:
                test = batch.subset(splits[split_name])
                records = encode_fitted(method, test)
                for ber in BERS:
                    channel = ChannelConfig(ber=ber, seed=seed)
                    row = score_encoded(method, records, test, channel, seed, BUDGET, extra=extra)
                    row.split = split_name
                    append_jsonl(out, row)
                    print(f"  {split_name} ber={ber} acc={row.accuracy:.3f}")
    print("wrote", out)


if __name__ == "__main__":
    main()
