"""Fixed random projection hashing. No HDC binding / bundling / prototypes."""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression

from hdc_lidar.methods.base import BaseMethod
from hdc_lidar.types import TransmitRecord
from hdc_lidar.utils.bits import pack_bipolar, unpack_bipolar


class BinaryHashMethod(BaseMethod):
    name = "binary_hash"

    def __init__(self, budget_bytes: int, seed: int = 0, dimension: int | None = None):
        super().__init__(budget_bytes, seed)
        self.dimension = int(dimension) if dimension is not None else budget_bytes * 8
        self.dimension = min(self.dimension, budget_bytes * 8)
        self.dimension = max(8, self.dimension - (self.dimension % 8))
        self.R: np.ndarray | None = None
        self.clf = LogisticRegression(max_iter=800, class_weight="balanced", random_state=seed)
        self.max_range = 10.0

    def _hash(self, ranges: np.ndarray) -> np.ndarray:
        assert self.R is not None
        x = np.asarray(ranges, dtype=np.float32)
        x = np.where(np.isfinite(x), x, self.max_range) / self.max_range
        if x.ndim == 1:
            bits = np.sign(self.R @ x)
            bits[bits == 0] = 1
            return bits.astype(np.int8)
        bits = np.sign(x @ self.R.T)
        bits[bits == 0] = 1
        return bits.astype(np.int8)

    def fit(self, ranges: np.ndarray, labels: np.ndarray, max_range: float) -> None:
        self.max_range = float(max_range)
        rng = np.random.default_rng(self.seed)
        self.R = rng.normal(0.0, 1.0, size=(self.dimension, ranges.shape[1])).astype(np.float32)
        codes = self._hash(ranges)
        self.clf.fit(codes.astype(np.float32), labels)
        self.fitted = True

    def encode_one(self, scan: np.ndarray) -> TransmitRecord:
        code = self._hash(scan)
        blob = pack_bipolar(code)
        return TransmitRecord(payload=blob, n_payload_bits=self.dimension, metadata_bits=0)

    def predict_from_payloads(self, payloads: list[bytes], n_beams: int, max_range: float) -> np.ndarray:
        codes = np.stack([unpack_bipolar(p, self.dimension, 1) for p in payloads])
        return self.clf.predict(codes.astype(np.float32))

    def model_bytes(self) -> int:
        return self.nbytes_of(self.clf.coef_, self.clf.intercept_)

    def shared_memory_bytes(self) -> int:
        return 0 if self.R is None else int(self.R.nbytes)
