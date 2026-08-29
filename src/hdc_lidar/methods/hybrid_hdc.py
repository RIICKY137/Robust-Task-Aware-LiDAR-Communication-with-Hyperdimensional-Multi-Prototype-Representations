"""Neural encoder followed by binary HDC / random projection."""

from __future__ import annotations

import numpy as np
from sklearn.neural_network import MLPClassifier

from hdc_lidar.hdc_ops import cosine_similarity, random_hv
from hdc_lidar.methods.base import BaseMethod
from hdc_lidar.methods.pure_hdc import PureHDCMethod
from hdc_lidar.types import TransmitRecord
from hdc_lidar.utils.bits import pack_bipolar, unpack_bipolar


def sector_features(ranges: np.ndarray, n_sectors: int = 16) -> np.ndarray:
    x = np.atleast_2d(ranges.astype(np.float32))
    n, b = x.shape
    pad = (-b) % n_sectors
    if pad:
        x = np.pad(x, ((0, 0), (0, pad)), mode="edge")
    g = x.reshape(n, n_sectors, -1)
    feats = np.concatenate(
        [g.mean(axis=2), g.std(axis=2), g.min(axis=2), g.max(axis=2)],
        axis=1,
    )
    return feats


class HybridHDCMethod(BaseMethod):
    """Two training modes:

    - frozen: handcrafted sector stats, then sign(Rz) + HDC prototypes
    - task: MLP trained with task loss, freeze hidden features, then sign(Rz)
    """

    name = "hybrid_hdc"

    def __init__(
        self,
        budget_bytes: int,
        seed: int = 0,
        dimension: int = 4096,
        mode: str = "task",
        hidden: int = 32,
    ):
        super().__init__(budget_bytes, seed)
        self.dimension = min(int(dimension), budget_bytes * 8)
        self.dimension -= self.dimension % 8
        self.mode = mode
        self.hidden = hidden
        self.mlp: MLPClassifier | None = None
        self.R: np.ndarray | None = None
        self.hdc = PureHDCMethod(budget_bytes, seed=seed, dimension=self.dimension)
        self.max_range = 10.0
        self._feat_mean: np.ndarray | None = None
        self._feat_std: np.ndarray | None = None

    def _features(self, ranges: np.ndarray) -> np.ndarray:
        feat = sector_features(ranges)
        if self.mode == "task" and self.mlp is not None:
            # hidden activations of the trained MLP
            w0, b0 = self.mlp.coefs_[0], self.mlp.intercepts_[0]
            h = np.maximum(0.0, feat @ w0 + b0)
            return h
        return feat

    def _to_hv(self, feat: np.ndarray) -> np.ndarray:
        assert self.R is not None and self._feat_mean is not None and self._feat_std is not None
        z = (feat - self._feat_mean) / self._feat_std
        hv = np.sign(z @ self.R.T)
        hv[hv == 0] = 1
        return hv.astype(np.int8)

    def fit(self, ranges: np.ndarray, labels: np.ndarray, max_range: float) -> None:
        self.max_range = float(max_range)
        feat = sector_features(ranges)
        if self.mode == "task":
            self.mlp = MLPClassifier(
                hidden_layer_sizes=(self.hidden,),
                max_iter=250,
                random_state=self.seed,
                early_stopping=True,
            )
            self.mlp.fit(feat, labels)
            feat_h = self._features(ranges)
        else:
            feat_h = feat
        self._feat_mean = feat_h.mean(axis=0)
        self._feat_std = feat_h.std(axis=0) + 1e-6
        rng = np.random.default_rng(self.seed + 3)
        self.R = rng.normal(0.0, 1.0, size=(self.dimension, feat_h.shape[1])).astype(np.float32)
        hv = self._to_hv(feat_h)
        # reuse HDC prototype machinery
        self.hdc.dimension = self.dimension
        self.hdc.max_range = self.max_range
        self.hdc.prototypes = np.zeros((self.hdc.n_classes, self.dimension), dtype=np.int32)
        self.hdc.counts = np.zeros(self.hdc.n_classes, dtype=np.int32)
        for k in range(self.hdc.n_classes):
            mask = labels == k
            if np.any(mask):
                self.hdc.prototypes[k] = hv[mask].astype(np.int32).sum(axis=0)
                self.hdc.counts[k] = int(mask.sum())
        self.fitted = True

    def encode_one(self, scan: np.ndarray) -> TransmitRecord:
        feat = self._features(scan.reshape(1, -1))
        hv = self._to_hv(feat)[0]
        blob = pack_bipolar(hv)
        return TransmitRecord(payload=blob, n_payload_bits=self.dimension, metadata_bits=0)

    def predict_from_payloads(self, payloads: list[bytes], n_beams: int, max_range: float) -> np.ndarray:
        hv = np.stack([unpack_bipolar(p, self.dimension, 1) for p in payloads])
        proto = self.hdc.prototypes.astype(np.float32)
        sim = cosine_similarity(hv, proto)
        return np.argmax(sim, axis=-1).astype(np.int32)

    def adapt(self, scan: np.ndarray, label: int) -> None:
        feat = self._features(scan.reshape(1, -1))
        hv = self._to_hv(feat)[0]
        pred = int(self.predict_from_payloads([pack_bipolar(hv)], scan.size, self.max_range)[0])
        self.hdc.adapt(hv, label, subtract_pred=pred)

    def model_bytes(self) -> int:
        return self.hdc.model_bytes()

    def shared_memory_bytes(self) -> int:
        n = 0 if self.R is None else int(self.R.nbytes)
        if self.mlp is not None:
            n += self.nbytes_of(*self.mlp.coefs_, *self.mlp.intercepts_)
        return n
