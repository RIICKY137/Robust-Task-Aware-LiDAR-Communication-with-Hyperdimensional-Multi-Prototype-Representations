from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

import numpy as np

T = TypeVar("T")


def timed_repeats(
    fn: Callable[[], T],
    repeats: int = 20,
    warmup: int = 3,
) -> tuple[T, dict[str, float]]:
    """Run warmup + repeats and return last output plus latency stats in milliseconds."""
    for _ in range(warmup):
        out = fn()
    samples: list[float] = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        out = fn()
        samples.append((time.perf_counter() - t0) * 1000.0)
    arr = np.asarray(samples, dtype=np.float64)
    stats = {
        "median_ms": float(np.median(arr)),
        "p95_ms": float(np.percentile(arr, 95)),
        "mean_ms": float(np.mean(arr)),
        "min_ms": float(np.min(arr)),
        "max_ms": float(np.max(arr)),
    }
    return out, stats
