#!/usr/bin/env python3
"""Fit first-round methods and dump a tiny smoke accuracy table (no channel)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hdc_lidar.data.io import load_dataset  # noqa: E402
from hdc_lidar.evaluation.metrics import task_metrics  # noqa: E402
from hdc_lidar.methods import build_method  # noqa: E402


def main() -> None:
    batch, splits, _ = load_dataset("sim_indoor_v1")
    train = batch.subset(splits["train"])
    test = batch.subset(splits["test_id"])
    specs = [
        ("quantized", 512, {}),
        ("pca", 512, {}),
        ("binary_hash", 512, {"dimension": 4096}),
        ("pure_hdc", 512, {"dimension": 4096}),
        ("autoencoder", 512, {}),
    ]
    rows = []
    for name, budget, kw in specs:
        print(f"fitting {name} …")
        m = build_method(name, budget, seed=0, **kw)
        m.fit(train.ranges, train.labels, train.max_range)
        rec = m.encode_batch(test.ranges)
        pred = m.predict_from_payloads([r.payload for r in rec], test.n_beams, test.max_range)
        metrics = task_metrics(test.labels, pred)
        rows.append(
            {
                "method": m.name,
                "budget_bytes": budget,
                "actual_bytes": rec[0].total_bytes,
                "accuracy": metrics["accuracy"],
                "macro_f1": metrics["macro_f1"],
                "model_bytes": m.model_bytes(),
                "shared_memory_bytes": m.shared_memory_bytes(),
            }
        )
        print(f"  acc={metrics['accuracy']:.3f} f1={metrics['macro_f1']:.3f} bytes={rec[0].total_bytes:.1f}")
    out = ROOT / "results" / "tables" / "smoke_id.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
