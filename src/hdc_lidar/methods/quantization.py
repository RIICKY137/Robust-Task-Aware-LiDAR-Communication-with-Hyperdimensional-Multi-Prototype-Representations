"""Raw float and uniform quantization baselines."""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from hdc_lidar.methods.base import BaseMethod
from hdc_lidar.types import TransmitRecord
from hdc_lidar.utils.bits import pack_float32, pack_uint8, unpack_float32, unpack_uint8


def _subsample_index(n_beams: int, n_keep: int) -> np.ndarray:
    if n_keep >= n_beams:
        return np.arange(n_beams)
    return np.linspace(0, n_beams - 1, n_keep).round().astype(np.int32)


def quantize_uint(values: np.ndarray, n_bits: int, max_range: float) -> np.ndarray:
    levels = (1 << n_bits) - 1
    q = np.rint(np.clip(values, 0.0, max_range) / max_range * levels)
    return np.clip(q, 0, levels).astype(np.uint16)


def dequantize_uint(q: np.ndarray, n_bits: int, max_range: float) -> np.ndarray:
    levels = (1 << n_bits) - 1
    return q.astype(np.float32) * (max_range / levels)


class QuantizedMethod(BaseMethod):
    """Uniform range quantization. Default first-round setting is 8-bit."""

    name = "quantized"

    def __init__(self, budget_bytes: int, seed: int = 0, n_bits: int = 8, raw_float32: bool = False):
        super().__init__(budget_bytes, seed)
        self.n_bits = int(n_bits)
        self.raw_float32 = bool(raw_float32)
        if raw_float32:
            self.name = "raw_float32"
            self.n_bits = 32
        self.clf = LogisticRegression(
            max_iter=800,
            class_weight="balanced",
            random_state=seed,
        )
        self.scaler = StandardScaler()
        self.index: np.ndarray | None = None
        self.n_keep = 0
        self.max_range = 10.0
        self.header_bytes = 8  # max_range f32 + n_keep u16 + n_bits u8 + pad

    def _layout(self, n_beams: int) -> None:
        if self.raw_float32:
            payload_bytes = max(4, self.budget_bytes - self.header_bytes)
            self.n_keep = min(n_beams, payload_bytes // 4)
        else:
            payload_bits = max(8, (self.budget_bytes - self.header_bytes) * 8)
            self.n_keep = min(n_beams, payload_bits // self.n_bits)
        self.n_keep = max(1, self.n_keep)
        self.index = _subsample_index(n_beams, self.n_keep)

    def _features(self, ranges: np.ndarray) -> np.ndarray:
        assert self.index is not None
        return ranges[:, self.index].astype(np.float32)

    def fit(self, ranges: np.ndarray, labels: np.ndarray, max_range: float) -> None:
        self.max_range = float(max_range)
        self._layout(ranges.shape[1])
        feats = self.scaler.fit_transform(self._features(ranges))
        self.clf.fit(feats, labels)
        self.fitted = True

    def _pack(self, scan: np.ndarray) -> bytes:
        assert self.index is not None
        subsampled = scan[self.index]
        header = pack_float32(np.array([self.max_range], dtype=np.float32))
        header += np.uint16(self.n_keep).tobytes()
        header += np.uint8(self.n_bits).tobytes()
        header += b"\x00"  # pad to 8
        if self.raw_float32:
            payload = pack_float32(subsampled)
        elif self.n_bits == 16:
            levels = 65535
            q = np.clip(np.rint(subsampled / self.max_range * levels), 0, levels).astype(np.uint16)
            payload = q.tobytes()
        elif self.n_bits == 8:
            q = quantize_uint(subsampled, 8, self.max_range).astype(np.uint8)
            payload = pack_uint8(q)
        else:  # 4-bit packed
            q = quantize_uint(subsampled, 4, self.max_range).astype(np.uint8)
            if q.size % 2 == 1:
                q = np.concatenate([q, q[-1:]])
            packed = q[0::2] << 4 | q[1::2]
            payload = pack_uint8(packed)
        return header + payload

    def encode_one(self, scan: np.ndarray) -> TransmitRecord:
        blob = self._pack(scan)
        meta = self.header_bytes * 8
        return TransmitRecord(payload=blob, n_payload_bits=len(blob) * 8 - meta, metadata_bits=meta)

    def _unpack(self, payload: bytes) -> np.ndarray:
        if len(payload) < 8:
            payload = payload + bytes(8 - len(payload))
        max_range = float(unpack_float32(payload[:4], 1)[0] or self.max_range)
        if not np.isfinite(max_range) or max_range <= 0:
            max_range = self.max_range
        n_bits = int(payload[6]) if payload[6] in (4, 8, 16, 32) else self.n_bits
        body = payload[8:]
        width = self.n_keep
        if n_bits == 32:
            vals = unpack_float32(body, width)
        elif n_bits == 16:
            need = width * 2
            padded = body[:need] + bytes(max(0, need - len(body)))
            q = np.frombuffer(padded, dtype=np.uint16, count=width)
            vals = q.astype(np.float32) * (max_range / 65535.0)
        elif n_bits == 8:
            q = unpack_uint8(body, width)
            vals = dequantize_uint(q, 8, max_range)
        else:
            packed = unpack_uint8(body, (width + 1) // 2)
            hi = packed >> 4
            lo = packed & 0x0F
            q = np.empty(packed.size * 2, dtype=np.uint8)
            q[0::2] = hi
            q[1::2] = lo
            vals = dequantize_uint(q[:width], 4, max_range)
        out = vals.astype(np.float32)
        if out.size < width:
            out = np.pad(out, (0, width - out.size))
        return out[:width]

    def predict_from_payloads(self, payloads: list[bytes], n_beams: int, max_range: float) -> np.ndarray:
        feats = np.stack([self._unpack(p) for p in payloads])
        # channel noise may change n_keep; pad/crop to training width
        width = self.n_keep
        if feats.shape[1] < width:
            feats = np.pad(feats, ((0, 0), (0, width - feats.shape[1])))
        elif feats.shape[1] > width:
            feats = feats[:, :width]
        feats = np.nan_to_num(feats, nan=0.0, posinf=self.max_range, neginf=0.0)
        return self.clf.predict(self.scaler.transform(feats))

    def model_bytes(self) -> int:
        return self.nbytes_of(self.clf.coef_, self.clf.intercept_)
