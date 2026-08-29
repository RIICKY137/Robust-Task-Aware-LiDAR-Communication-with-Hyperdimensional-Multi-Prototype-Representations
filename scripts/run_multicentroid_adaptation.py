#!/usr/bin/env python3
"""Few-shot OOD adaptation for multi-centroid HDC vs single prototype vs linear head.

Shots are balanced per class on `test_ood`. Old-task accuracy is `test_id`.
Prototype methods add/subtract the nearest centroid; the linear head refits
logistic regression on train hypervectors plus the shots (replay).
"""

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
METHODS = [
    ("hdc_k1", {"head": "prototype", "n_centroids": 1}),
    ("hdc_k8", {"head": "prototype", "n_centroids": 8}),
    ("hdc_k16", {"head": "prototype", "n_centroids": 16}),
    ("hdc_linear", {"head": "linear", "n_centroids": 1}),
]


def _acc(labels, pred) -> float:
    return task_metrics(labels, pred)["accuracy"]


def main() -> None:
    batch, splits, _ = load_dataset("sim_indoor_v1")
    train = batch.subset(splits["train"])
    old = batch.subset(splits["test_id"])
    new = batch.subset(splits["test_ood"])

    out = ROOT / "results" / "raw" / "multicentroid_adaptation.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("", encoding="utf-8")

    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        fitted = {}
        for tag, kw in METHODS:
            print(f"fit {tag} seed={seed}")
            method = build_method("pure_hdc", BUDGET, seed=seed, dimension=4096, **kw)
            method.fit(train.ranges, train.labels, train.max_range)
            hv_old = method.encode_matrix(old.ranges)
            hv_new = method.encode_matrix(new.ranges)
            fitted[tag] = {
                "method": method,
                "hv_old": hv_old,
                "hv_new": hv_new,
                "before_old": _acc(old.labels, method.predict_from_hv(hv_old)),
                "before_new": _acc(new.labels, method.predict_from_hv(hv_new)),
                "hv_train": method.encode_matrix(train.ranges) if kw.get("head") == "linear" else None,
            }

        for n in SHOTS:
            x_shot, y_shot = balanced_shots(new.ranges, new.labels, n, rng)
            for tag, kw in METHODS:
                pack = fitted[tag]
                cloned = copy.deepcopy(pack["method"])
                t0 = time.perf_counter()
                if kw.get("head") == "linear":
                    hv_shot = cloned.encode_matrix(x_shot)
                    clf = LogisticRegression(
                        max_iter=600, class_weight="balanced", random_state=seed
                    )
                    clf.fit(
                        np.concatenate([pack["hv_train"], hv_shot]).astype(np.float32),
                        np.concatenate([train.labels, y_shot]),
                    )
                    cloned.clf = clf
                else:
                    adapt_hdc(cloned, x_shot, y_shot, subtract=True)
                adapt_ms = (time.perf_counter() - t0) * 1000
                new_acc = _acc(new.labels, cloned.predict_from_hv(pack["hv_new"]))
                old_acc = _acc(old.labels, cloned.predict_from_hv(pack["hv_old"]))
                row = {
                    "shots_per_class": n,
                    "seed": seed,
                    "method": tag,
                    "hdc_head": kw.get("head"),
                    "n_centroids": kw.get("n_centroids", 1),
                    "before_new_acc": pack["before_new"],
                    "before_old_acc": pack["before_old"],
                    "new_acc": new_acc,
                    "old_acc": old_acc,
                    "forgetting": forgetting(pack["before_old"], old_acc),
                    "delta_new": new_acc - pack["before_new"],
                    "adapt_ms": adapt_ms,
                }
                with out.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(row) + "\n")
                print(
                    f"  {tag} shots={n} OOD {pack['before_new']:.3f}->{new_acc:.3f} "
                    f"ID {old_acc:.3f}  {adapt_ms:.0f} ms"
                )
    print("wrote", out)


if __name__ == "__main__":
    main()
