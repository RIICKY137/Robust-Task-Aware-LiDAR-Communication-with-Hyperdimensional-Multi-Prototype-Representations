#!/usr/bin/env python3
"""Remake Stage 1 with k=16 HDC. Does not overwrite bandwidth_sweep.jsonl.

Budgets 128 / 512 / 2048 bytes. Dimension fills the budget (D = 8 × bytes),
so 128 B → D=1024, 512 B → D=4096, 2048 B → D=16384. Payload is still one
hypervector per scan; k=16 only changes the receiver.
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

BUDGETS = [128, 512, 2048]
SEEDS = [0, 1, 2]
SPLITS = ["test_id", "test_ood"]
METHODS = [
    ("quantized", {}),
    ("binary_hash", {}),
    ("pure_hdc", {"head": "prototype", "n_centroids": 1}),
    ("pure_hdc", {"head": "prototype", "n_centroids": 16}),
    ("pure_hdc", {"head": "linear", "n_centroids": 1}),
]


def _tag(name: str, kw: dict) -> str:
    if name == "quantized":
        return "quantized"
    if name == "binary_hash":
        return "binary_hash"
    if kw.get("head") == "linear":
        return "hdc_linear"
    return f"hdc_k{kw.get('n_centroids', 1)}"


def main() -> None:
    batch, splits, _ = load_dataset("sim_indoor_v1")
    train = batch.subset(splits["train"])
    out = raw_dir() / "k16_bandwidth.jsonl"
    if out.exists():
        out.unlink()
    channel = ChannelConfig(ber=0.0)
    for seed in SEEDS:
        for budget in BUDGETS:
            dim = budget * 8
            for name, kw in METHODS:
                tag = _tag(name, kw)
                fit_kw = dict(kw)
                if name in {"pure_hdc", "binary_hash"}:
                    fit_kw["dimension"] = dim
                print(f"fit {tag} seed={seed} budget={budget} D={fit_kw.get('dimension')}")
                method = build_method(name, budget, seed=seed, **fit_kw)
                method.fit(train.ranges, train.labels, train.max_range)
                extra = {
                    "hdc_head": kw.get("head"),
                    "n_centroids": kw.get("n_centroids"),
                    "method_tag": tag,
                    "sweep": "k16_bandwidth",
                }
                for split_name in SPLITS:
                    test = batch.subset(splits[split_name])
                    records = encode_fitted(method, test)
                    row = score_encoded(method, records, test, channel, seed, budget, extra=extra)
                    row.split = split_name
                    append_jsonl(out, row)
                    print(f"  {split_name} acc={row.accuracy:.3f} bytes={row.actual_bytes:.1f}")
    print("wrote", out)


if __name__ == "__main__":
    main()
