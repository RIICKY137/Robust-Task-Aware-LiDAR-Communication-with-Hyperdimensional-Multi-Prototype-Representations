#!/usr/bin/env python3
"""Stage 4: 10 / 50 / 100-shot OOD adaptation — HDC prototypes vs linear head vs hybrid."""

from __future__ import annotations

import copy
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
from hdc_lidar.methods import build_method  # noqa: E402

SHOTS = [10, 50, 100]
SEEDS = [0, 1, 2]
BUDGET = 512


def _metrics(labels, pred) -> float:
    return task_metrics(labels, pred)["accuracy"]


def main() -> None:
    batch, splits, _ = load_dataset("sim_indoor_v1")
    train = batch.subset(splits["train"])
    old = batch.subset(splits["test_id"])
    new = batch.subset(splits["test_ood"])

    raw_path = ROOT / "results" / "raw" / "adaptation.jsonl"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text("", encoding="utf-8")
    rows = []

    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        hdc = build_method("pure_hdc", BUDGET, seed=seed, dimension=4096)
        hdc.fit(train.ranges, train.labels, train.max_range)
        quant = build_method("quantized", BUDGET, seed=seed, n_bits=8)
        quant.fit(train.ranges, train.labels, train.max_range)
        hybrid = build_method("hybrid_hdc", BUDGET, seed=seed, dimension=4096, mode="task")
        hybrid.fit(train.ranges, train.labels, train.max_range)

        before_old_hdc = _metrics(old.labels, hdc.predict_from_hv(hdc.encode_matrix(old.ranges)))
        rec_old = quant.encode_batch(old.ranges)
        before_old_q = _metrics(
            old.labels,
            quant.predict_from_payloads([r.payload for r in rec_old], old.n_beams, old.max_range),
        )
        rec_old_h = hybrid.encode_batch(old.ranges)
        before_old_hy = _metrics(
            old.labels,
            hybrid.predict_from_payloads([r.payload for r in rec_old_h], old.n_beams, old.max_range),
        )

        feat_train = quant._features(train.ranges)
        feat_old = quant._features(old.ranges)
        feat_new = quant._features(new.ranges)

        for n in SHOTS:
            x_shot, y_shot = balanced_shots(new.ranges, new.labels, n, rng)

            hdc_t = copy.deepcopy(hdc)
            t0 = time.perf_counter()
            adapt_hdc(hdc_t, x_shot, y_shot, subtract=True)
            hdc_ms = (time.perf_counter() - t0) * 1000
            new_hdc = _metrics(new.labels, hdc_t.predict_from_hv(hdc_t.encode_matrix(new.ranges)))
            old_hdc = _metrics(old.labels, hdc_t.predict_from_hv(hdc_t.encode_matrix(old.ranges)))

            t0 = time.perf_counter()
            clf = LogisticRegression(max_iter=400, class_weight="balanced", random_state=seed)
            clf.fit(np.concatenate([feat_train, quant._features(x_shot)]), np.concatenate([train.labels, y_shot]))
            q_ms = (time.perf_counter() - t0) * 1000
            new_q = _metrics(new.labels, clf.predict(feat_new))
            old_q = _metrics(old.labels, clf.predict(feat_old))

            hy_t = copy.deepcopy(hybrid)
            t0 = time.perf_counter()
            for scan, lab in zip(x_shot, y_shot, strict=True):
                hy_t.adapt(scan, int(lab))
            hy_ms = (time.perf_counter() - t0) * 1000
            rec_new_h = hy_t.encode_batch(new.ranges)
            rec_old_h2 = hy_t.encode_batch(old.ranges)
            new_hy = _metrics(
                new.labels,
                hy_t.predict_from_payloads([r.payload for r in rec_new_h], new.n_beams, new.max_range),
            )
            old_hy = _metrics(
                old.labels,
                hy_t.predict_from_payloads([r.payload for r in rec_old_h2], old.n_beams, old.max_range),
            )

            row = {
                "shots_per_class": n,
                "seed": seed,
                "hdc_new_acc": new_hdc,
                "hdc_old_acc": old_hdc,
                "hdc_forgetting": forgetting(before_old_hdc, old_hdc),
                "hdc_adapt_ms": hdc_ms,
                "quant_new_acc": new_q,
                "quant_old_acc": old_q,
                "quant_forgetting": forgetting(before_old_q, old_q),
                "quant_adapt_ms": q_ms,
                "hybrid_new_acc": new_hy,
                "hybrid_old_acc": old_hy,
                "hybrid_forgetting": forgetting(before_old_hy, old_hy),
                "hybrid_adapt_ms": hy_ms,
            }
            rows.append(row)
            with raw_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")
            print(
                f"seed={seed} shots={n} HDC new={new_hdc:.3f}  "
                f"Q new={new_q:.3f}  hybrid new={new_hy:.3f}"
            )

    out = ROOT / "results" / "tables" / "adaptation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print("wrote", out, "and", raw_path)


if __name__ == "__main__":
    main()
