"""Bit-accurate packing, counting, and channel-facing serialization helpers."""

from __future__ import annotations

import numpy as np


def pack_bipolar(hv: np.ndarray) -> bytes:
    """Pack bipolar {+1,-1} (or binary {0,1}) hypervectors into bytes.

    Accepts shape (D,) or (N, D). Length is padded to a multiple of 8.
    """
    bits = np.asarray(hv > 0, dtype=np.uint8)
    flat = bits.reshape(bits.shape[0], -1) if bits.ndim > 1 else bits.reshape(1, -1)
    packed_rows = [np.packbits(row, bitorder="big") for row in flat]
    if hv.ndim == 1:
        return packed_rows[0].tobytes()
    return b"".join(row.tobytes() for row in packed_rows)


def unpack_bipolar(payload: bytes, dimension: int, n_vectors: int = 1) -> np.ndarray:
    n_bits = dimension * n_vectors
    n_bytes = (n_bits + 7) // 8
    padded = payload[:n_bytes] + bytes(max(0, n_bytes - len(payload)))
    raw = np.frombuffer(padded, dtype=np.uint8)
    bits = np.unpackbits(raw, bitorder="big")[:n_bits]
    bipolar = np.where(bits.astype(np.int8) == 1, 1, -1).astype(np.int8)
    if n_vectors == 1:
        return bipolar
    return bipolar.reshape(n_vectors, dimension)


def pack_uint8(values: np.ndarray) -> bytes:
    return np.asarray(values, dtype=np.uint8).tobytes()


def unpack_uint8(payload: bytes, n: int) -> np.ndarray:
    padded = payload[:n] + bytes(max(0, n - len(payload)))
    return np.frombuffer(padded, dtype=np.uint8, count=n)


def pack_int8(values: np.ndarray) -> bytes:
    return np.asarray(values, dtype=np.int8).tobytes()


def unpack_int8(payload: bytes, n: int) -> np.ndarray:
    padded = payload[:n] + bytes(max(0, n - len(payload)))
    return np.frombuffer(padded, dtype=np.int8, count=n)


def pack_float16(values: np.ndarray) -> bytes:
    return np.asarray(values, dtype=np.float16).tobytes()


def unpack_float16(payload: bytes, n: int) -> np.ndarray:
    need = n * 2
    padded = payload[:need] + bytes(max(0, need - len(payload)))
    return np.frombuffer(padded, dtype=np.float16, count=n).astype(np.float32)


def pack_float32(values: np.ndarray) -> bytes:
    return np.asarray(values, dtype=np.float32).tobytes()


def unpack_float32(payload: bytes, n: int) -> np.ndarray:
    need = n * 4
    padded = payload[:need] + bytes(max(0, need - len(payload)))
    return np.frombuffer(padded, dtype=np.float32, count=n)


def prepend_header(header: bytes, payload: bytes) -> bytes:
    return header + payload


def bit_count(data: bytes) -> int:
    return len(data) * 8


def pad_or_truncate(data: bytes, n_bytes: int) -> bytes:
    if len(data) == n_bytes:
        return data
    if len(data) > n_bytes:
        return data[:n_bytes]
    return data + bytes(n_bytes - len(data))


def interleave_bits(data: bytes, seed: int) -> tuple[bytes, np.ndarray]:
    bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8), bitorder="big")
    order = np.random.default_rng(seed).permutation(bits.size)
    shuffled = bits[order]
    packed_len = (bits.size + 7) // 8
    packed = np.packbits(shuffled, bitorder="big")[:packed_len]
    return packed.tobytes(), order


def deinterleave_bits(data: bytes, order: np.ndarray, n_bits: int) -> bytes:
    bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8), bitorder="big")[:n_bits]
    restored = np.empty_like(bits)
    restored[order] = bits
    packed = np.packbits(restored, bitorder="big")
    n_bytes = (n_bits + 7) // 8
    return packed[:n_bytes].tobytes()


def measured_ber(clean: bytes, noisy: bytes) -> float:
    a = np.unpackbits(np.frombuffer(clean, dtype=np.uint8), bitorder="big")
    b = np.unpackbits(np.frombuffer(noisy, dtype=np.uint8), bitorder="big")
    n = min(a.size, b.size)
    if n == 0:
        return 0.0
    return float(np.mean(a[:n] != b[:n]))
