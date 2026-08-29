"""PCA coefficient transmission. Basis is fit on train only."""

from __future__ import annotations

import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from hdc_lidar.methods.base import BaseMethod
from hdc_lidar.types import TransmitRecord
from hdc_lidar.utils.bits import pack_float16, pack_float32, pack_int8, unpack_float16, unpack_float32, unpack_int8


class PCAMethod(BaseMethod):
    name = "pca"

    def __init__(self, budget_bytes: int, seed: int = 0, coeff_dtype: str = "float32"):
        super().__init__(budget_bytes, seed)
        self.coeff_dtype = coeff_dtype
        self.header_bytes = 8
        self.scaler = StandardScaler()
        self.pca = PCA(random_state=seed)
        self.clf = LogisticRegression(max_iter=800, class_weight="balanced", random_state=seed)
        self.n_comp = 1
        self.scale = 1.0
        self.max_range = 10.0

    def _bytes_per_coeff(self) -> int:
        return {"float32": 4, "float16": 2, "int8": 1}[self.coeff_dtype]

    def fit(self, ranges: np.ndarray, labels: np.ndarray, max_range: float) -> None:
        self.max_range = float(max_range)
        x = ranges.astype(np.float32)
        xs = self.scaler.fit_transform(x)
        max_comp = min(xs.shape[0] - 1, xs.shape[1], 256)
        payload = max(self._bytes_per_coeff(), self.budget_bytes - self.header_bytes)
        self.n_comp = max(1, min(max_comp, payload // self._bytes_per_coeff()))
        self.pca.n_components = self.n_comp
        z = self.pca.fit_transform(xs)
        if self.coeff_dtype == "int8":
            self.scale = float(np.max(np.abs(z)) + 1e-6)
        self.clf.fit(z, labels)
        self.fitted = True

    def _pack_z(self, z: np.ndarray) -> bytes:
        header = np.uint16(self.n_comp).tobytes() + np.uint16({"float32": 32, "float16": 16, "int8": 8}[self.coeff_dtype]).tobytes()
        header += pack_float32(np.array([self.scale], dtype=np.float32))
        if self.coeff_dtype == "float32":
            body = pack_float32(z)
        elif self.coeff_dtype == "float16":
            body = pack_float16(z)
        else:
            q = np.clip(np.rint(z / self.scale * 127.0), -127, 127).astype(np.int8)
            body = pack_int8(q)
        return header + body

    def encode_one(self, scan: np.ndarray) -> TransmitRecord:
        xs = self.scaler.transform(scan.reshape(1, -1))
        z = self.pca.transform(xs)[0]
        blob = self._pack_z(z)
        meta = self.header_bytes * 8
        return TransmitRecord(payload=blob, n_payload_bits=len(blob) * 8 - meta, metadata_bits=meta)

    def _unpack_z(self, payload: bytes) -> np.ndarray:
        n_comp = int(np.frombuffer(payload[:2], dtype=np.uint16)[0])
        n_bits = int(np.frombuffer(payload[2:4], dtype=np.uint16)[0])
        scale = float(unpack_float32(payload[4:8], 1)[0] or self.scale)
        if not np.isfinite(scale) or scale <= 0:
            scale = self.scale
        body = payload[8:]
        n_comp = self.n_comp
        if n_bits == 32:
            z = unpack_float32(body, n_comp)
        elif n_bits == 16:
            z = unpack_float16(body, n_comp)
        else:
            q = unpack_int8(body, n_comp)
            z = q.astype(np.float32) * (scale / 127.0)
        if z.size < self.n_comp:
            z = np.pad(z, (0, self.n_comp - z.size))
        return z[: self.n_comp]

    def predict_from_payloads(self, payloads: list[bytes], n_beams: int, max_range: float) -> np.ndarray:
        z = np.stack([self._unpack_z(p) for p in payloads])
        z = np.nan_to_num(z, nan=0.0, posinf=1e3, neginf=-1e3)
        return self.clf.predict(z)

    def model_bytes(self) -> int:
        return self.nbytes_of(self.clf.coef_, self.clf.intercept_)

    def shared_memory_bytes(self) -> int:
        return self.nbytes_of(self.pca.components_, self.pca.mean_, self.scaler.mean_, self.scaler.scale_)
