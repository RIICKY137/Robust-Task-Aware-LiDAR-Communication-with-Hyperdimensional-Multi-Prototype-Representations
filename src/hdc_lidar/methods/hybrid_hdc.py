"""Neural + record HDC encoder for 2D LiDAR.

The Stage-5 hybrid only saw 16-sector summaries, which is why it stalled near
pure HDC. This module is the LiDAR hybrid used in follow-up work:

- frontend `scan`: full polar range + circular derivative (doorway/clutter edges)
- mix `record`: bundle that neural code with beam-wise P_i ⊗ L_Q(r_i)
- head `linear`: same logistic head hashing uses, so the hashing gap can be
  attributed to encoding vs classifier
"""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier

from hdc_lidar.hdc_ops import cosine_similarity
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
    return np.concatenate(
        [g.mean(axis=2), g.std(axis=2), g.min(axis=2), g.max(axis=2)],
        axis=1,
    )


def lidar_scan_features(ranges: np.ndarray, max_range: float) -> np.ndarray:
    """Normalized ranges plus circular first difference (2D LiDAR edges)."""
    x = np.atleast_2d(ranges.astype(np.float32)) / float(max_range)
    d = np.empty_like(x)
    d[:, 1:] = x[:, 1:] - x[:, :-1]
    d[:, 0] = x[:, 0] - x[:, -1]
    return np.concatenate([x, d], axis=1)


class HybridHDCMethod(BaseMethod):
    """Task-aware LiDAR hybrid.

    `mode`: frozen (no MLP) or task (MLP trained on place labels).
    `frontend`: sector stats (Stage 5) or full-scan LiDAR features.
    `mix`: none, or bundle with record-based HDC of the raw beams.
    `head`: HDC prototypes or a linear classifier on the bipolar code.
    """

    name = "hybrid_hdc"

    def __init__(
        self,
        budget_bytes: int,
        seed: int = 0,
        dimension: int = 4096,
        mode: str = "task",
        frontend: str = "sector",
        head: str = "prototype",
        mix: str = "none",
        hidden: int = 64,
    ):
        super().__init__(budget_bytes, seed)
        self.dimension = min(int(dimension), budget_bytes * 8)
        self.dimension -= self.dimension % 8
        self.mode = mode
        self.frontend = frontend
        self.head = head
        self.mix = mix
        self.hidden = hidden
        self.mlp: MLPClassifier | None = None
        self.clf: LogisticRegression | None = None
        self.R: np.ndarray | None = None
        self.hdc = PureHDCMethod(budget_bytes, seed=seed, dimension=self.dimension)
        self.max_range = 10.0
        self._feat_mean: np.ndarray | None = None
        self._feat_std: np.ndarray | None = None

    def tag(self) -> str:
        return f"{self.mode}/{self.frontend}/{self.head}/{self.mix}"

    def _raw_features(self, ranges: np.ndarray) -> np.ndarray:
        if self.frontend == "scan":
            return lidar_scan_features(ranges, self.max_range)
        return sector_features(ranges)

    def _features(self, ranges: np.ndarray) -> np.ndarray:
        feat = self._raw_features(ranges)
        if self.mode == "task" and self.mlp is not None:
            w0, b0 = self.mlp.coefs_[0], self.mlp.intercepts_[0]
            return np.maximum(0.0, feat @ w0 + b0)
        return feat

    def _neural_pre(self, feat: np.ndarray) -> np.ndarray:
        assert self.R is not None and self._feat_mean is not None and self._feat_std is not None
        z = (feat - self._feat_mean) / self._feat_std
        return z @ self.R.T

    def _to_hv(self, feat: np.ndarray) -> np.ndarray:
        pre = self._neural_pre(feat)
        hv = np.sign(pre)
        hv[hv == 0] = 1
        return hv.astype(np.int8)

    def _mix_record(self, ranges: np.ndarray, neural_hv: np.ndarray, feat: np.ndarray) -> np.ndarray:
        if self.mix != "record":
            return neural_hv
        # Bundle analog record accumulator with the neural projection, then one sign.
        # Majority of two already-bipolar codes is a no-op (ties reproduce one parent).
        rec = self.hdc.encode_matrix(ranges, binarize=False).astype(np.float32)
        neu = self._neural_pre(feat)
        rec = rec / (rec.std(axis=1, keepdims=True) + 1e-6)
        neu = neu / (neu.std(axis=1, keepdims=True) + 1e-6)
        hv = np.sign(rec + neu)
        hv[hv == 0] = 1
        return hv.astype(np.int8)

    def _codes(self, ranges: np.ndarray) -> np.ndarray:
        x = np.atleast_2d(ranges.astype(np.float32))
        feat = self._features(x)
        neural = self._to_hv(feat)
        return self._mix_record(x, neural, feat)

    def _fit_prototypes(self, hv: np.ndarray, labels: np.ndarray) -> None:
        self.hdc.dimension = self.dimension
        self.hdc.max_range = self.max_range
        self.hdc.prototypes = np.zeros((self.hdc.n_classes, self.dimension), dtype=np.int32)
        self.hdc.counts = np.zeros(self.hdc.n_classes, dtype=np.int32)
        for k in range(self.hdc.n_classes):
            mask = labels == k
            if np.any(mask):
                self.hdc.prototypes[k] = hv[mask].astype(np.int32).sum(axis=0)
                self.hdc.counts[k] = int(mask.sum())

    def fit(self, ranges: np.ndarray, labels: np.ndarray, max_range: float) -> None:
        self.max_range = float(max_range)
        if self.mix == "record":
            self.hdc.dimension = self.dimension
            self.hdc.max_range = self.max_range
            self.hdc._prepare_item_memory(ranges.shape[1])
        feat = self._raw_features(ranges)
        if self.mode == "task":
            self.mlp = MLPClassifier(
                hidden_layer_sizes=(self.hidden,),
                max_iter=300,
                random_state=self.seed,
                early_stopping=True,
            )
            self.mlp.fit(feat, labels)
        feat_h = self._features(ranges)
        self._feat_mean = feat_h.mean(axis=0)
        self._feat_std = feat_h.std(axis=0) + 1e-6
        rng = np.random.default_rng(self.seed + 3)
        self.R = rng.normal(0.0, 1.0, size=(self.dimension, feat_h.shape[1])).astype(np.float32)
        hv = self._codes(ranges)
        self._fit_prototypes(hv, labels)
        if self.head == "linear":
            self.clf = LogisticRegression(
                max_iter=600, class_weight="balanced", random_state=self.seed
            )
            self.clf.fit(hv.astype(np.float32), labels)
        self.fitted = True

    def encode_batch(self, ranges: np.ndarray) -> list[TransmitRecord]:
        hv = self._codes(ranges)
        out: list[TransmitRecord] = []
        for row in hv:
            blob = pack_bipolar(row)
            out.append(TransmitRecord(payload=blob, n_payload_bits=self.dimension, metadata_bits=0))
        return out

    def encode_one(self, scan: np.ndarray) -> TransmitRecord:
        return self.encode_batch(scan.reshape(1, -1))[0]

    def predict_from_payloads(self, payloads: list[bytes], n_beams: int, max_range: float) -> np.ndarray:
        hv = np.stack([unpack_bipolar(p, self.dimension, 1) for p in payloads])
        if self.head == "linear":
            assert self.clf is not None
            return self.clf.predict(hv.astype(np.float32)).astype(np.int32)
        proto = self.hdc.prototypes.astype(np.float32)
        sim = cosine_similarity(hv, proto)
        return np.argmax(sim, axis=-1).astype(np.int32)

    def adapt(self, scan: np.ndarray, label: int) -> None:
        hv = self._codes(scan.reshape(1, -1))[0]
        pred = int(self.predict_from_payloads([pack_bipolar(hv)], scan.size, self.max_range)[0])
        self.hdc.adapt(hv, label, subtract_pred=pred)

    def model_bytes(self) -> int:
        n = self.hdc.model_bytes()
        if self.clf is not None:
            n += self.nbytes_of(self.clf.coef_, self.clf.intercept_)
        return n

    def shared_memory_bytes(self) -> int:
        n = 0 if self.R is None else int(self.R.nbytes)
        if self.mlp is not None:
            n += self.nbytes_of(*self.mlp.coefs_, *self.mlp.intercepts_)
        if self.mix == "record":
            n += self.hdc.shared_memory_bytes()
        return n
