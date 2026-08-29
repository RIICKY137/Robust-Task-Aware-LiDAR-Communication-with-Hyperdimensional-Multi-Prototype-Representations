#!/usr/bin/env python3
"""LiDAR hybrid HDC: full-scan frontend ± record bundle, prototype vs linear head.

Does not overwrite Stage-5 `hybrid_sweep.jsonl`. The question is whether a
2D-LiDAR hybrid (range + edge features, bundled with P⊗L records) closes the
gap to binary hashing, and whether that gap is the encoder or the classifier.
"""

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
    ("pure_hdc", {"dimension": 4096, "head": "prototype"}),
    ("pure_hdc", {"dimension": 4096, "head": "linear"}),
    (
        "hybrid_hdc",
        {"dimension": 4096, "mode": "task", "frontend": "sector", "head": "prototype", "mix": "none"},
    ),
    (
        "hybrid_hdc",
        {"dimension": 4096, "mode": "task", "frontend": "scan", "head": "prototype", "mix": "none"},
    ),
    (
        "hybrid_hdc",
        {"dimension": 4096, "mode": "task", "frontend": "scan", "head": "linear", "mix": "none"},
    ),
    (
        "hybrid_hdc",
        {"dimension": 4096, "mode": "task", "frontend": "scan", "head": "prototype", "mix": "record"},
    ),
    (
        "hybrid_hdc",
        {"dimension": 4096, "mode": "task", "frontend": "scan", "head": "linear", "mix": "record"},
    ),
]
SPLIT = "test_id"


def _tag(name: str, kw: dict) -> str:
    if name == "pure_hdc":
        return f"pure_hdc/{kw.get('head', 'prototype')}"
    if name == "hybrid_hdc":
        return f"{kw.get('mode')}/{kw.get('frontend')}/{kw.get('head')}/{kw.get('mix')}"
    return name


def main() -> None:
    batch, splits, _ = load_dataset("sim_indoor_v1")
    train = batch.subset(splits["train"])
    test = batch.subset(splits[SPLIT])
    out = raw_dir() / "hybrid_lidar_sweep.jsonl"
    if out.exists():
        out.unlink()
    for seed in SEEDS:
        for name, kw in METHODS:
            tag = _tag(name, kw)
            print(f"fit {tag} seed={seed}")
            method = build_method(name, BUDGET, seed=seed, **kw)
            method.fit(train.ranges, train.labels, train.max_range)
            records = encode_fitted(method, test)
            extra = {
                "hybrid_mode": tag if name == "hybrid_hdc" else None,
                "hdc_head": kw.get("head"),
                "frontend": kw.get("frontend"),
                "mix": kw.get("mix"),
            }
            for ber in BERS:
                channel = ChannelConfig(ber=ber, seed=seed)
                row = score_encoded(method, records, test, channel, seed, BUDGET, extra=extra)
                row.split = SPLIT
                append_jsonl(out, row)
                print(f"  ber={ber} acc={row.accuracy:.3f}")
    print("wrote", out)


if __name__ == "__main__":
    main()
