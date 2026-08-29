#!/usr/bin/env python3
"""Stage 4 (subset): HDC prototype updates on OOD env vs linear-head refit."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hdc_lidar.adaptation import adapt_hdc, balanced_shots  # noqa: E402
from hdc_lidar.data.io import load_dataset  # noqa: E402
from hdc_lidar.evaluation.metrics import forgetting, task_metrics  # noqa: E402
from hdc_lidar.methods.pure_hdc import PureHDCMethod  # noqa: E402
from hdc_lidar.methods.quantization import QuantizedMethod  # noqa: E402


SHOTS = [1, 2, 5, 10, 20]
SEED = 0
BUDGET = 512


def main() -> None:
    batch, splits, _ = load_dataset("sim_indoor_v1")
    train = batch.subset(splits["train"])
    old = batch.subset(splits["test_id"])
    new = batch.subset(splits["test_ood"])
    rng = np.random.default_rng(SEED)

    hdc = PureHDCMethod(BUDGET, seed=SEED, dimension=4096)
    hdc.fit(train.ranges, train.labels, train.max_range)
    quant = QuantizedMethod(BUDGET, seed=SEED, n_bits=8)
    quant.fit(train.ranges, train.labels, train.max_range)

    before_old_hdc = task_metrics(old.labels, hdc.predict_from_hv(hdc.encode_matrix(old.ranges)))["accuracy"]
    rec_old = quant.encode_batch(old.ranges)
    before_old_q = task_metrics(
        old.labels,
        quant.predict_from_payloads([r.payload for r in rec_old], old.n_beams, old.max_range),
    )["accuracy"]

    rows = []
    for n in SHOTS:
        x_shot, y_shot = balanced_shots(new.ranges, new.labels, n, rng)

        import copy

        hdc_t = copy.deepcopy(hdc)
        t0 = time.perf_counter()
        adapt_hdc(hdc_t, x_shot, y_shot, subtract=True)
        hdc_ms = (time.perf_counter() - t0) * 1000
        new_hdc = task_metrics(new.labels, hdc_t.predict_from_hv(hdc_t.encode_matrix(new.ranges)))["accuracy"]
        old_hdc = task_metrics(old.labels, hdc_t.predict_from_hv(hdc_t.encode_matrix(old.ranges)))["accuracy"]

        # linear head: refit 8-bit features on train + shots
        q_shot = QuantizedMethod(BUDGET, seed=SEED, n_bits=8)
        q_shot.index = quant.index
        q_shot.n_keep = quant.n_keep
        q_shot.max_range = quant.max_range
        feat_train = quant._features(train.ranges)
        feat_shot = quant._features(x_shot)
        feat_old = quant._features(old.ranges)
        feat_new = quant._features(new.ranges)
        t0 = time.perf_counter()
        clf = LogisticRegression(max_iter=400, class_weight="balanced", random_state=SEED)
        clf.fit(np.concatenate([feat_train, feat_shot]), np.concatenate([train.labels, y_shot]))
        q_ms = (time.perf_counter() - t0) * 1000
        new_q = task_metrics(new.labels, clf.predict(feat_new))["accuracy"]
        old_q = task_metrics(old.labels, clf.predict(feat_old))["accuracy"]

        rows.append(
            {
                "shots_per_class": n,
                "hdc_new_acc": new_hdc,
                "hdc_old_acc": old_hdc,
                "hdc_forgetting": forgetting(before_old_hdc, old_hdc),
                "hdc_adapt_ms": hdc_ms,
                "quant_new_acc": new_q,
                "quant_old_acc": old_q,
                "quant_forgetting": forgetting(before_old_q, old_q),
                "quant_adapt_ms": q_ms,
            }
        )
        print(f"shots={n} HDC new={new_hdc:.3f} old={old_hdc:.3f}  Q new={new_q:.3f} old={old_q:.3f}")

    out = ROOT / "results" / "tables" / "adaptation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
