"""Sensor-side corruptions, reported separately from communication errors."""

from __future__ import annotations

import numpy as np


def beam_dropout(ranges: np.ndarray, drop_rate: float, rng: np.random.Generator, fill: float) -> np.ndarray:
    out = ranges.copy()
    mask = rng.random(out.shape) < drop_rate
    out[mask] = fill
    return out


def sector_dropout(
    ranges: np.ndarray,
    fraction: float,
    rng: np.random.Generator,
    fill: float,
) -> np.ndarray:
    out = ranges.copy()
    n_beams = out.shape[-1]
    width = max(1, int(round(fraction * n_beams)))
    start = int(rng.integers(0, n_beams))
    idx = (np.arange(width) + start) % n_beams
    out[..., idx] = fill
    return out


def range_offset(ranges: np.ndarray, bias: float, scale: float = 1.0, max_range: float | None = None) -> np.ndarray:
    out = ranges * scale + bias
    out = np.clip(out, 0.0, None)
    if max_range is not None:
        out = np.minimum(out, max_range)
    return out


def gaussian_range_noise(
    ranges: np.ndarray, sigma: float, rng: np.random.Generator, max_range: float | None = None
) -> np.ndarray:
    out = ranges + rng.normal(0.0, sigma, size=ranges.shape)
    out = np.clip(out, 0.0, None)
    if max_range is not None:
        out = np.minimum(out, max_range)
    return out


def max_range_clip(ranges: np.ndarray, max_range: float) -> np.ndarray:
    return np.minimum(ranges, max_range)
