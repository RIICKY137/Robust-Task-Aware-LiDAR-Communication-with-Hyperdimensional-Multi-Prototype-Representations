"""Compact MLP autoencoder. Latent is quantized and transmitted."""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

from hdc_lidar.methods.base import BaseMethod
from hdc_lidar.types import TransmitRecord
from hdc_lidar.utils.bits import pack_float32, pack_int8, unpack_float32, unpack_int8


class AutoencoderMethod(BaseMethod):
    """Uses sklearn MLPRegressor as a bottleneck autoencoder (encoder = first layer)."""

    name = "autoencoder"

    def __init__(self, budget_bytes: int, seed: int = 0, latent_bits: int = 8):
        super().__init__(budget_bytes, seed)
        self.header_bytes = 8
        self.latent_bits = int(latent_bits)
        payload = max(1, budget_bytes - self.header_bytes)
        self.latent_dim = max(2, payload if latent_bits == 8 else payload // 2)
        self.scaler = StandardScaler()
        self.ae = MLPRegressor(
            hidden_layer_sizes=(max(16, self.latent_dim * 2), self.latent_dim, max(16, self.latent_dim * 2)),
            activation="relu",
            solver="adam",
            max_iter=120,
            random_state=seed,
            early_stopping=True,
            n_iter_no_change=8,
        )
        self.clf = LogisticRegression(max_iter=800, class_weight="balanced", random_state=seed)
        self.scale = 1.0
        self.max_range = 10.0
        self._enc_w: np.ndarray | None = None
        self._enc_b: np.ndarray | None = None
        self._enc_w2: np.ndarray | None = None
        self._enc_b2: np.ndarray | None = None

    def _encode_latent(self, x_scaled: np.ndarray) -> np.ndarray:
        assert self._enc_w is not None
        h = np.maximum(0.0, x_scaled @ self._enc_w + self._enc_b)
        z = np.maximum(0.0, h @ self._enc_w2 + self._enc_b2)
        return z

    def fit(self, ranges: np.ndarray, labels: np.ndarray, max_range: float) -> None:
        self.max_range = float(max_range)
        x = ranges.astype(np.float32)
        xs = self.scaler.fit_transform(x)
        # keep latent dim feasible vs samples
        self.latent_dim = min(self.latent_dim, max(2, xs.shape[0] // 4), xs.shape[1])
        self.ae.hidden_layer_sizes = (
            max(16, self.latent_dim * 2),
            self.latent_dim,
            max(16, self.latent_dim * 2),
        )
        self.ae.fit(xs, xs)
        w = self.ae.coefs_
        b = self.ae.intercepts_
        self._enc_w, self._enc_b = w[0], b[0]
        self._enc_w2, self._enc_b2 = w[1], b[1]
        z = self._encode_latent(xs)
        self.scale = float(np.max(np.abs(z)) + 1e-6)
        self.clf.fit(z, labels)
        self.fitted = True

    def encode_one(self, scan: np.ndarray) -> TransmitRecord:
        xs = self.scaler.transform(scan.reshape(1, -1))
        z = self._encode_latent(xs)[0]
        header = np.uint16(self.latent_dim).tobytes() + np.uint16(self.latent_bits).tobytes()
        header += pack_float32(np.array([self.scale], dtype=np.float32))
        q = np.clip(np.rint(z / self.scale * 127.0), -127, 127).astype(np.int8)
        blob = header + pack_int8(q)
        return TransmitRecord(payload=blob, n_payload_bits=len(q) * 8, metadata_bits=self.header_bytes * 8)

    def _unpack(self, payload: bytes) -> np.ndarray:
        dim = int(np.frombuffer(payload[:2], dtype=np.uint16)[0])
        scale = float(unpack_float32(payload[4:8], 1)[0] or self.scale)
        dim = max(1, min(dim, self.latent_dim))
        q = unpack_int8(payload[8:], dim)
        z = q.astype(np.float32) * (scale / 127.0)
        if z.size < self.latent_dim:
            z = np.pad(z, (0, self.latent_dim - z.size))
        return z[: self.latent_dim]

    def predict_from_payloads(self, payloads: list[bytes], n_beams: int, max_range: float) -> np.ndarray:
        z = np.stack([self._unpack(p) for p in payloads])
        return self.clf.predict(z)

    def reconstruction_mse(self, ranges: np.ndarray) -> float:
        xs = self.scaler.transform(ranges)
        pred = self.ae.predict(xs)
        recon = self.scaler.inverse_transform(pred)
        return float(np.mean((ranges - recon) ** 2))

    def model_bytes(self) -> int:
        return self.nbytes_of(self.clf.coef_, self.clf.intercept_)

    def shared_memory_bytes(self) -> int:
        parts = [c for c in self.ae.coefs_] + [b for b in self.ae.intercepts_]
        parts += [self.scaler.mean_, self.scaler.scale_]
        return self.nbytes_of(*parts)
