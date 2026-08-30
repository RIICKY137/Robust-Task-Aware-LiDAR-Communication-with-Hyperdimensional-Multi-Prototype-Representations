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
    per_sample: bool = False,
) -> np.ndarray:
    out = ranges.copy()
    n_beams = out.shape[-1]
    width = max(1, int(round(fraction * n_beams)))
    if per_sample and out.ndim == 2:
        starts = rng.integers(0, n_beams, size=out.shape[0])
        for i, start in enumerate(starts):
            idx = (np.arange(width) + int(start)) % n_beams
            out[i, idx] = fill
        return out
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


def apply_named(
    name: str,
    ranges: np.ndarray,
    rng: np.random.Generator,
    max_range: float,
    invalid: str = "max_range",
    **params,
) -> np.ndarray:
    """Dispatch a Stage-3 sensor corruption. `name` is the condition id.

    `invalid` is how missing beams are stored: `max_range` (legacy fill, looks
    like open space) or `nan` (encoder can skip / DROP-bind them).
    """
    x = np.asarray(ranges, dtype=np.float32)
    fill = np.float32(np.nan) if invalid == "nan" else float(max_range)
    if name in {"clean", "none"}:
        return x.copy()
    if name == "beam_drop":
        return beam_dropout(x, float(params.get("drop_rate", 0.1)), rng, fill)
    if name == "sector_drop":
        return sector_dropout(
            x, float(params.get("fraction", 0.15)), rng, fill, per_sample=True
        )
    if name == "range_bias":
        return range_offset(x, bias=float(params.get("bias", 0.25)), scale=1.0, max_range=max_range)
    if name == "range_scale":
        return range_offset(x, bias=0.0, scale=float(params.get("scale", 1.15)), max_range=max_range)
    if name == "gauss":
        return gaussian_range_noise(x, float(params.get("sigma", 0.05)), rng, max_range=max_range)
    if name == "clip":
        return max_range_clip(x, float(params.get("clip_to", 6.0)))
    raise ValueError(f"Unknown sensor corruption {name}")
