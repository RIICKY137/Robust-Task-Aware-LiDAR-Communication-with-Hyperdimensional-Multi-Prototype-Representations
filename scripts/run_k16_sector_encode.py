#!/usr/bin/env python3
"""Sector-drop encoder fix: skip / DROP-bind invalid beams vs max-range fill.

Does not overwrite k16_sensor.jsonl. Budget 512 B, D=4096, k=16.
Corruptions that punch holes use NaN for skip/drop and max_range for fill.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hdc_lidar.channels.sensor_corruption import apply_named  # noqa: E402
from hdc_lidar.data.io import load_dataset  # noqa: E402
from hdc_lidar.evaluation.metrics import task_metrics  # noqa: E402
from hdc_lidar.experiment import append_jsonl, raw_dir  # noqa: E402
from hdc_lidar.methods import build_method  # noqa: E402
from hdc_lidar.types import ExperimentRow, ScanBatch  # noqa: E402
from hdc_lidar.utils.gitinfo import git_commit  # noqa: E402

BUDGET = 512
DIMENSION = 4096
SEEDS = [0, 1, 2]
SPLITS = ["test_id", "test_ood"]
VARIANTS = [
    ("binary_hash", {"dimension": DIMENSION}, "max_range", "binary_hash"),
    (
        "pure_hdc",
        {"dimension": DIMENSION, "head": "prototype", "n_centroids": 16, "invalid_mode": "fill"},
        "max_range",
        "hdc_k16/fill",
    ),
    (
        "pure_hdc",
        {"dimension": DIMENSION, "head": "prototype", "n_centroids": 16, "invalid_mode": "skip"},
        "nan",
        "hdc_k16/skip",
    ),
    (
        "pure_hdc",
        {"dimension": DIMENSION, "head": "prototype", "n_centroids": 16, "invalid_mode": "drop"},
        "nan",
        "hdc_k16/drop",
    ),
]
CONDITIONS = [
    ("clean", {}),
    ("beam_drop", {"drop_rate": 0.10}),
    ("beam_drop", {"drop_rate": 0.30}),
    ("sector_drop", {"fraction": 0.15}),
    ("sector_drop", {"fraction": 0.30}),
]


def _label(name: str, params: dict) -> str:
    if not params:
        return name
    inner = ",".join(f"{k}={v}" for k, v in params.items())
    return f"{name}:{inner}"


def main() -> None:
    batch, splits, _ = load_dataset("sim_indoor_v1")
    train = batch.subset(splits["train"])
    out = raw_dir() / "k16_sector_encode.jsonl"
    if out.exists():
        out.unlink()
    for seed in SEEDS:
        for name, kw, invalid, tag in VARIANTS:
            print(f"fit {tag} seed={seed}")
            method = build_method(name, BUDGET, seed=seed, **kw)
            method.fit(train.ranges, train.labels, train.max_range)
            for split in SPLITS:
                test = batch.subset(splits[split])
                for cond, params in CONDITIONS:
                    rng = np.random.default_rng(seed + 17)
                    corrupted = apply_named(
                        cond,
                        test.ranges,
                        rng,
                        test.max_range,
                        invalid=invalid if cond != "clean" else "max_range",
                        **params,
                    )
                    dirty = ScanBatch(
                        ranges=corrupted,
                        labels=test.labels,
                        env_ids=test.env_ids,
                        traj_ids=test.traj_ids,
                        sample_ids=test.sample_ids,
                        poses=test.poses,
                        max_range=test.max_range,
                        n_beams=test.n_beams,
                    )
                    recs = method.encode_batch(dirty.ranges)
                    pred = method.predict_from_payloads(
                        [r.payload for r in recs], dirty.n_beams, dirty.max_range
                    )
                    metrics = task_metrics(dirty.labels, pred)
                    row = ExperimentRow(
                        dataset="sim_indoor_v1",
                        split=split,
                        method=method.name,
                        budget_bytes=BUDGET,
                        actual_bytes=float(recs[0].total_bytes),
                        ber=0.0,
                        burst_length=0,
                        packet_loss_rate=0.0,
                        seed=seed,
                        accuracy=metrics["accuracy"],
                        macro_f1=metrics["macro_f1"],
                        encode_ms_median=0.0,
                        encode_ms_p95=0.0,
                        classify_ms_median=0.0,
                        classify_ms_p95=0.0,
                        model_bytes=method.model_bytes(),
                        shared_memory_bytes=method.shared_memory_bytes(),
                        git_commit=git_commit(),
                        extras={
                            "sensor": _label(cond, params),
                            "dimension": getattr(method, "dimension", None),
                            "hdc_head": kw.get("head"),
                            "n_centroids": kw.get("n_centroids"),
                            "invalid_mode": kw.get("invalid_mode", "fill"),
                            "invalid_storage": invalid,
                            "method_tag": tag,
                            "sweep": "k16_sector_encode",
                        },
                    )
                    append_jsonl(out, row)
                    print(f"  {split} {row.extras['sensor']} acc={row.accuracy:.3f}")
    print("wrote", out)


if __name__ == "__main__":
    main()
