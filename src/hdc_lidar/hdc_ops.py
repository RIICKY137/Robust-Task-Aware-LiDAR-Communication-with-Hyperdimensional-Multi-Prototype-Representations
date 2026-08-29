"""Hyperdimensional computing primitives used by Pure HDC and Hybrid HDC."""

from __future__ import annotations

import numpy as np

from hdc_lidar.utils.bits import pack_bipolar, unpack_bipolar


def random_hv(n: int, dimension: int, rng: np.random.Generator) -> np.ndarray:
    bits = rng.integers(0, 2, size=(n, dimension), dtype=np.int8)
    return np.where(bits == 1, 1, -1).astype(np.int8)


def bind(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Elementwise binding for bipolar hypervectors (XOR in {0,1})."""
    return (np.asarray(a) * np.asarray(b)).astype(np.int8)


def permute(hv: np.ndarray, shift: int = 1) -> np.ndarray:
    return np.roll(hv, shift, axis=-1)


def bundle(vectors: np.ndarray, binarize: bool = True) -> np.ndarray:
    """Bundle along axis 0. `vectors` shape (N, D)."""
    acc = np.sum(vectors.astype(np.int32), axis=0)
    if not binarize:
        return acc
    return np.sign(acc).astype(np.int8)


def binarize(acc: np.ndarray) -> np.ndarray:
    signed = np.sign(acc)
    signed[signed == 0] = 1
    return signed.astype(np.int8)


def hamming_distance(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a_b = np.asarray(a)
    b_b = np.asarray(b)
    if a_b.ndim == 1 and b_b.ndim == 1:
        return np.count_nonzero(a_b != b_b)
    if a_b.ndim == 1:
        return np.count_nonzero(a_b[None, :] != b_b, axis=1)
    if b_b.ndim == 1:
        return np.count_nonzero(a_b != b_b[None, :], axis=1)
    return np.count_nonzero(a_b[:, None, :] != b_b[None, :, :], axis=2)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a_f = np.asarray(a, dtype=np.float32)
    b_f = np.asarray(b, dtype=np.float32)
    if a_f.ndim == 1:
        a_f = a_f[None, :]
        squeeze_a = True
    else:
        squeeze_a = False
    if b_f.ndim == 1:
        b_f = b_f[None, :]
        squeeze_b = True
    else:
        squeeze_b = False
    a_n = a_f / (np.linalg.norm(a_f, axis=1, keepdims=True) + 1e-8)
    b_n = b_f / (np.linalg.norm(b_f, axis=1, keepdims=True) + 1e-8)
    sim = a_n @ b_n.T
    if squeeze_a and squeeze_b:
        return sim[0, 0]
    if squeeze_a:
        return sim[0]
    if squeeze_b:
        return sim[:, 0]
    return sim


def locality_preserving_levels(
    n_levels: int, dimension: int, rng: np.random.Generator, flips_per_step: int | None = None
) -> np.ndarray:
    """Nearby quantization levels share more bits (thermometer-like in HD space)."""
    if flips_per_step is None:
        flips_per_step = max(1, dimension // max(n_levels, 1))
    levels = np.empty((n_levels, dimension), dtype=np.int8)
    levels[0] = random_hv(1, dimension, rng)[0]
    for i in range(1, n_levels):
        nxt = levels[i - 1].copy()
        idx = rng.choice(dimension, size=min(flips_per_step, dimension), replace=False)
        nxt[idx] *= -1
        levels[i] = nxt
    return levels


def encode_scans(
    ranges: np.ndarray,
    position_hv: np.ndarray,
    level_hv: np.ndarray,
    max_range: float,
    n_levels: int,
) -> np.ndarray:
    """Vectorized record-based encoding: H = sign(sum_i P_i ⊗ L_{Q(r_i)}).

    ranges: (N, B), position_hv: (B, D), level_hv: (L, D)
    """
    n_samples, n_beams = ranges.shape
    dimension = position_hv.shape[1]
    q = quantize_ranges(ranges, max_range, n_levels)
    acc = np.zeros((n_samples, dimension), dtype=np.int32)
    for beam in range(n_beams):
        acc += position_hv[beam] * level_hv[q[:, beam]]
    return binarize(acc)


def quantize_ranges(ranges: np.ndarray, max_range: float, n_levels: int) -> np.ndarray:
    clipped = np.clip(ranges, 0.0, max_range)
    q = np.floor(clipped / max_range * n_levels).astype(np.int32)
    return np.clip(q, 0, n_levels - 1)


def pack_hv(hv: np.ndarray) -> bytes:
    return pack_bipolar(hv)


def unpack_hv(payload: bytes, dimension: int) -> np.ndarray:
    return unpack_bipolar(payload, dimension, n_vectors=1)
