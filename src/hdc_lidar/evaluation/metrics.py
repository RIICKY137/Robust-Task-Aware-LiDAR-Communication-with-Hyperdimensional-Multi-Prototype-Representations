from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)

from hdc_lidar import LABELS


def task_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    acc = float(accuracy_score(y_true, y_pred))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    prec, rec, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=list(range(len(LABELS))), zero_division=0
    )
    per_class = {
        LABELS[i]: {
            "precision": float(prec[i]),
            "recall": float(rec[i]),
            "f1": float(f1[i]),
            "support": int(support[i]),
        }
        for i in range(len(LABELS))
    }
    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(LABELS)))).tolist()
    return {
        "accuracy": acc,
        "macro_f1": macro_f1,
        "per_class": per_class,
        "confusion_matrix": cm,
        "report": classification_report(
            y_true, y_pred, target_names=list(LABELS), zero_division=0
        ),
    }


def forgetting(acc_old_before: float, acc_old_after: float) -> float:
    return float(acc_old_before - acc_old_after)
