#!/usr/bin/env python3
"""128 B k=16 remake on Semantic2D (real 2D LiDAR, derived place labels).

Does not overwrite sim_indoor JSONL. Invalid beams stay NaN; HDC uses skip.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hdc_lidar.data.io import load_dataset  # noqa: E402
from hdc_lidar.experiment import append_jsonl, encode_fitted, raw_dir, score_encoded  # noqa: E402
from hdc_lidar.methods import build_method  # noqa: E402
from hdc_lidar.types import ChannelConfig  # noqa: E402
from dataclasses import replace

DATASET = "semantic2d_v1"
BUDGET = 128
DIMENSION = 1024
SEEDS = [0, 1, 2]
SPLITS = ["test_id", "test_ood"]
BERS = [0.0, 0.05, 0.10]
METHODS = [
    ("quantized", {}),
    ("binary_hash", {"dimension": DIMENSION}),
    ("pure_hdc", {"head": "prototype", "n_centroids": 1, "invalid_mode": "skip"}),
    ("pure_hdc", {"head": "prototype", "n_centroids": 16, "invalid_mode": "skip"}),
    ("pure_hdc", {"head": "linear", "n_centroids": 1, "invalid_mode": "skip"}),
]


def _tag(name: str, kw: dict) -> str:
    if name != "pure_hdc":
        return name
    if kw.get("head") == "linear":
        return "hdc_linear"
    return f"hdc_k{kw.get('n_centroids', 1)}"


def _finite_ranges(ranges: np.ndarray, max_range: float) -> np.ndarray:
    return np.where(np.isfinite(ranges), ranges, max_range).astype(np.float32)


def main() -> None:
    batch, splits, meta = load_dataset(DATASET)
    train = batch.subset(splits["train"])
    out = raw_dir() / "k16_semantic2d.jsonl"
    if out.exists():
        out.unlink()
    for seed in SEEDS:
        for name, kw in METHODS:
            tag = _tag(name, kw)
            print(f"fit {tag} seed={seed}")
            method = build_method(name, BUDGET, seed=seed, dimension=DIMENSION, **kw)
            fit_ranges = train.ranges
            if name != "pure_hdc":
                fit_ranges = _finite_ranges(fit_ranges, train.max_range)
            method.fit(fit_ranges, train.labels, train.max_range)
            for split_name in SPLITS:
                test = batch.subset(splits[split_name])
                if name != "pure_hdc":
                    test = replace(test, ranges=_finite_ranges(test.ranges, test.max_range))
                records = encode_fitted(method, test)
                for ber in BERS:
                    channel = ChannelConfig(ber=float(ber), seed=seed)
                    extra = {
                        "hdc_head": kw.get("head"),
                        "n_centroids": kw.get("n_centroids"),
                        "invalid_mode": kw.get("invalid_mode", "fill"),
                        "method_tag": tag,
                        "sweep": "k16_semantic2d",
                        "dataset_name": DATASET,
                        "ood_envs": meta.get("ood_envs"),
                    }
                    row = score_encoded(method, records, test, channel, seed, BUDGET, extra=extra)
                    row.split = split_name
                    row.dataset = DATASET
                    append_jsonl(out, row)
                    print(f"  {split_name} ber={ber} acc={row.accuracy:.3f}")
    print("wrote", out)


if __name__ == "__main__":
    main()
