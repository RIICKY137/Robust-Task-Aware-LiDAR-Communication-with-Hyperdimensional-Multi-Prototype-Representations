"""Pure HDC record-based encoding of a 2D LiDAR scan."""

from __future__ import annotations

import numpy as np

from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression

from hdc_lidar import LABELS
from hdc_lidar.hdc_ops import (
    cosine_similarity,
    encode_scans,
    hamming_distance,
    locality_preserving_levels,
    pack_hv,
    random_hv,
    unpack_hv,
)
from hdc_lidar.methods.base import BaseMethod
from hdc_lidar.types import TransmitRecord


class PureHDCMethod(BaseMethod):
    name = "pure_hdc"

    def __init__(
        self,
        budget_bytes: int,
        seed: int = 0,
        dimension: int = 4096,
        n_levels: int = 32,
        level_mode: str = "locality",
        similarity: str = "cosine",
        region_size: int = 1,
        head: str = "prototype",
        n_centroids: int = 1,
        invalid_mode: str = "fill",
    ):
        super().__init__(budget_bytes, seed)
        dim_cap = max(8, budget_bytes * 8)
        self.dimension = min(int(dimension), dim_cap)
        self.dimension -= self.dimension % 8
        self.n_levels = int(n_levels)
        self.level_mode = level_mode
        self.similarity = similarity
        self.region_size = max(1, int(region_size))
        self.head = head
        self.n_centroids = max(1, int(n_centroids))
        mode = str(invalid_mode or "fill")
        if mode not in {"fill", "skip", "drop"}:
            raise ValueError(f"unknown invalid_mode {invalid_mode}")
        self.invalid_mode = mode
        self.clf: LogisticRegression | None = None
        self.position_hv: np.ndarray | None = None
        self.level_hv: np.ndarray | None = None
        self.drop_hv: np.ndarray | None = None
        self.prototypes: np.ndarray | None = None  # analog (C, D), class-wide sum
        self.counts: np.ndarray | None = None
        self.centroids: np.ndarray | None = None  # (C, K, D) when K > 1
        self.centroid_counts: np.ndarray | None = None
        self.max_range = 10.0
        self.n_classes = len(LABELS)

    def _prepare_item_memory(self, n_beams: int) -> None:
        rng = np.random.default_rng(self.seed + 1)
        n_pos = int(np.ceil(n_beams / self.region_size))
        self.position_hv = random_hv(n_pos, self.dimension, rng)
        if self.level_mode == "locality":
            self.level_hv = locality_preserving_levels(self.n_levels, self.dimension, rng)
        else:
            self.level_hv = random_hv(self.n_levels, self.dimension, rng)
        if self.invalid_mode == "drop":
            self.drop_hv = random_hv(1, self.dimension, rng)[0]
        else:
            self.drop_hv = None

    def _maybe_pool(self, ranges: np.ndarray) -> np.ndarray:
        if self.region_size <= 1:
            return ranges
        n, b = ranges.shape
        pad = (-b) % self.region_size
        if pad:
            ranges = np.pad(ranges, ((0, 0), (0, pad)), mode="edge")
        grouped = ranges.reshape(n, -1, self.region_size)
        if self.invalid_mode == "fill":
            return grouped.mean(axis=2)
        with np.errstate(all="ignore"):
            return np.nanmean(grouped, axis=2)

    def encode_matrix(self, ranges: np.ndarray, binarize: bool = True) -> np.ndarray:
        assert self.position_hv is not None and self.level_hv is not None
        pooled = self._maybe_pool(np.atleast_2d(ranges.astype(np.float32)))
        n_pos = self.position_hv.shape[0]
        if pooled.shape[1] != n_pos:
            pooled = pooled[:, :n_pos] if pooled.shape[1] > n_pos else np.pad(
                pooled, ((0, 0), (0, n_pos - pooled.shape[1])), mode="edge"
            )
        return encode_scans(
            pooled,
            self.position_hv,
            self.level_hv,
            self.max_range,
            self.n_levels,
            binarize_out=binarize,
            invalid_mode=self.invalid_mode,
            drop_hv=self.drop_hv,
        )

    def fit(self, ranges: np.ndarray, labels: np.ndarray, max_range: float) -> None:
        self.max_range = float(max_range)
        self._prepare_item_memory(ranges.shape[1])
        hv = self.encode_matrix(ranges)
        self.prototypes = np.zeros((self.n_classes, self.dimension), dtype=np.int32)
        self.counts = np.zeros(self.n_classes, dtype=np.int32)
        for k in range(self.n_classes):
            mask = labels == k
            if not np.any(mask):
                continue
            self.prototypes[k] = hv[mask].astype(np.int32).sum(axis=0)
            self.counts[k] = int(mask.sum())
        if self.head == "prototype" and self.n_centroids > 1:
            self._fit_centroids(hv, labels)
        if self.head == "linear":
            self.clf = LogisticRegression(
                max_iter=600, class_weight="balanced", random_state=self.seed
            )
            self.clf.fit(hv.astype(np.float32), labels)
        self.fitted = True

    def _fit_centroids(self, hv: np.ndarray, labels: np.ndarray) -> None:
        k = self.n_centroids
        self.centroids = np.zeros((self.n_classes, k, self.dimension), dtype=np.int32)
        self.centroid_counts = np.zeros((self.n_classes, k), dtype=np.int32)
        for c in range(self.n_classes):
            x = hv[labels == c]
            if x.shape[0] == 0:
                continue
            k_use = min(k, x.shape[0])
            if k_use == 1:
                self.centroids[c, 0] = x.astype(np.int32).sum(axis=0)
                self.centroid_counts[c, 0] = int(x.shape[0])
                continue
            km = KMeans(
                n_clusters=k_use,
                random_state=self.seed + 17 + c,
                n_init=4,
                max_iter=40,
            )
            assign = km.fit_predict(x.astype(np.float32))
            for j in range(k_use):
                members = x[assign == j]
                if members.shape[0] == 0:
                    continue
                self.centroids[c, j] = members.astype(np.int32).sum(axis=0)
                self.centroid_counts[c, j] = int(members.shape[0])

    def _nearest_centroid(self, hv_row: np.ndarray, class_id: int) -> int:
        assert self.centroids is not None and self.centroid_counts is not None
        valid = self.centroid_counts[class_id] > 0
        if not np.any(valid):
            return 0
        sim = np.asarray(cosine_similarity(hv_row, self.centroids[class_id]), dtype=np.float32)
        sim = np.atleast_1d(sim)
        sim[~valid] = -1e9
        return int(np.argmax(sim))

    def encode_one(self, scan: np.ndarray) -> TransmitRecord:
        hv = self.encode_matrix(scan.reshape(1, -1))[0]
        blob = pack_hv(hv)
        return TransmitRecord(
            payload=blob,
            n_payload_bits=self.dimension,
            metadata_bits=0,
            extras={"hv": hv},
        )

    def encode_batch(self, ranges: np.ndarray) -> list[TransmitRecord]:
        hv = self.encode_matrix(ranges)
        out: list[TransmitRecord] = []
        for row in hv:
            blob = pack_hv(row)
            out.append(
                TransmitRecord(
                    payload=blob,
                    n_payload_bits=self.dimension,
                    metadata_bits=0,
                    extras={"hv": row},
                )
            )
        return out

    def _predict_hv(self, hv: np.ndarray) -> np.ndarray:
        if self.head == "linear":
            assert self.clf is not None
            return self.clf.predict(np.atleast_2d(hv).astype(np.float32)).astype(np.int32)
        x = np.atleast_2d(hv)
        if self.centroids is not None and self.n_centroids > 1:
            return self._predict_centroids(x)
        assert self.prototypes is not None
        proto = self.prototypes.astype(np.float32)
        if self.similarity == "hamming":
            signed = np.sign(proto)
            signed[signed == 0] = 1
            dist = hamming_distance(x.astype(np.int8), signed.astype(np.int8))
            return np.argmin(dist, axis=-1)
        sim = cosine_similarity(x, proto)
        return np.argmax(sim, axis=-1)

    def _predict_centroids(self, hv: np.ndarray) -> np.ndarray:
        assert self.centroids is not None and self.centroid_counts is not None
        n, k = hv.shape[0], self.n_centroids
        flat = self.centroids.reshape(self.n_classes * k, self.dimension)
        valid = self.centroid_counts.reshape(self.n_classes * k) > 0
        if self.similarity == "hamming":
            signed = np.sign(flat).astype(np.int8)
            signed[signed == 0] = 1
            dist = np.asarray(hamming_distance(hv.astype(np.int8), signed), dtype=np.float32)
            dist = np.atleast_2d(dist)
            dist[:, ~valid] = 1e9
            scores = dist.reshape(n, self.n_classes, k)
            return np.argmin(scores.min(axis=2), axis=1)
        sim = np.asarray(cosine_similarity(hv, flat), dtype=np.float32)
        sim = np.atleast_2d(sim)
        sim[:, ~valid] = -1e9
        scores = sim.reshape(n, self.n_classes, k)
        return np.argmax(scores.max(axis=2), axis=1)

    def predict_from_payloads(self, payloads: list[bytes], n_beams: int, max_range: float) -> np.ndarray:
        hv = np.stack([unpack_hv(p, self.dimension) for p in payloads])
        return self._predict_hv(hv).astype(np.int32)

    def predict_from_hv(self, hv: np.ndarray) -> np.ndarray:
        return self._predict_hv(hv).astype(np.int32)

    def adapt(self, hv: np.ndarray, label: int, subtract_pred: int | None = None) -> None:
        """Prototype add / optional subtract. Used for few-shot updates."""
        row = np.asarray(hv).reshape(-1)
        if self.centroids is not None and self.n_centroids > 1:
            j = self._nearest_centroid(row, int(label))
            self.centroids[int(label), j] += row.astype(np.int32)
            self.centroid_counts[int(label), j] += 1
            if subtract_pred is not None and subtract_pred != label:
                j2 = self._nearest_centroid(row, int(subtract_pred))
                self.centroids[int(subtract_pred), j2] -= row.astype(np.int32)
        assert self.prototypes is not None and self.counts is not None
        self.prototypes[label] += row.astype(np.int32)
        self.counts[label] += 1
        if subtract_pred is not None and subtract_pred != label:
            self.prototypes[subtract_pred] -= row.astype(np.int32)

    def model_bytes(self) -> int:
        n = 0
        if self.centroids is not None:
            n += int(self.centroids.nbytes)
            if self.centroid_counts is not None:
                n += int(self.centroid_counts.nbytes)
        elif self.prototypes is not None:
            n += int(self.prototypes.nbytes + (0 if self.counts is None else self.counts.nbytes))
        if self.clf is not None:
            n += self.nbytes_of(self.clf.coef_, self.clf.intercept_)
        return n

    def shared_memory_bytes(self) -> int:
        parts = []
        if self.position_hv is not None:
            parts.append(self.position_hv)
        if self.level_hv is not None:
            parts.append(self.level_hv)
        if self.drop_hv is not None:
            parts.append(self.drop_hv)
        return self.nbytes_of(*parts) if parts else 0
