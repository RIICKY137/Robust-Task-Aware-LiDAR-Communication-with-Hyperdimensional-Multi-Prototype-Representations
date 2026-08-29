"""Few-shot prototype / classifier-head adaptation."""

from __future__ import annotations

import copy
from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import SGDClassifier

from hdc_lidar.evaluation.metrics import forgetting, task_metrics
from hdc_lidar.methods.pure_hdc import PureHDCMethod
from hdc_lidar.types import ChannelConfig
from hdc_lidar.utils.bits import pack_bipolar


@dataclass
class AdaptationResult:
    shots: int
    method: str
    new_accuracy: float
    old_accuracy: float
    forgetting: float
    adapt_ms: float
    extras: dict


def balanced_shots(
    ranges: np.ndarray, labels: np.ndarray, n_per_class: int, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    xs = []
    ys = []
    for k in np.unique(labels):
        idx = np.where(labels == k)[0]
        take = idx if len(idx) <= n_per_class else rng.choice(idx, size=n_per_class, replace=False)
        xs.append(ranges[take])
        ys.append(labels[take])
    return np.concatenate(xs), np.concatenate(ys)


def adapt_hdc(
    method: PureHDCMethod,
    ranges_new: np.ndarray,
    labels_new: np.ndarray,
    subtract: bool = True,
) -> PureHDCMethod:
    hv = method.encode_matrix(ranges_new)
    for row, y in zip(hv, labels_new):
        pred = int(method.predict_from_hv(row.reshape(1, -1))[0]) if subtract else None
        method.adapt(row, int(y), subtract_pred=pred)
    return method


def adapt_linear_head(
    x_old: np.ndarray,
    y_old: np.ndarray,
    x_new: np.ndarray,
    y_new: np.ndarray,
    replay: bool = True,
    seed: int = 0,
) -> SGDClassifier:
    clf = SGDClassifier(loss="log_loss", class_weight="balanced", random_state=seed, max_iter=200)
    if replay:
        x = np.concatenate([x_old, x_new])
        y = np.concatenate([y_old, y_new])
    else:
        x, y = x_new, y_new
    clf.fit(x, y)
    return clf


def evaluate_hdc_adaptation(
    base: PureHDCMethod,
    old_ranges: np.ndarray,
    old_labels: np.ndarray,
    new_ranges: np.ndarray,
    new_labels: np.ndarray,
    shots: int,
    rng: np.random.Generator,
) -> AdaptationResult:
    import time

    before_old = task_metrics(old_labels, base.predict_from_hv(base.encode_matrix(old_ranges)))
    x_shot, y_shot = balanced_shots(new_ranges, new_labels, shots, rng)
    cloned = copy.deepcopy(base)
    t0 = time.perf_counter()
    adapt_hdc(cloned, x_shot, y_shot, subtract=True)
    elapsed = (time.perf_counter() - t0) * 1000.0
    after_old = task_metrics(old_labels, cloned.predict_from_hv(cloned.encode_matrix(old_ranges)))
    after_new = task_metrics(new_labels, cloned.predict_from_hv(cloned.encode_matrix(new_ranges)))
    return AdaptationResult(
        shots=shots,
        method="pure_hdc",
        new_accuracy=after_new["accuracy"],
        old_accuracy=after_old["accuracy"],
        forgetting=forgetting(before_old["accuracy"], after_old["accuracy"]),
        adapt_ms=elapsed,
        extras={"before_old": before_old["accuracy"]},
    )
