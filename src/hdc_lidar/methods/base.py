from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from hdc_lidar.types import TransmitRecord


class BaseMethod(ABC):
    name: str = "base"

    def __init__(self, budget_bytes: int, seed: int = 0):
        self.budget_bytes = int(budget_bytes)
        self.seed = int(seed)
        self.fitted = False

    @abstractmethod
    def fit(self, ranges: np.ndarray, labels: np.ndarray, max_range: float) -> None: ...

    @abstractmethod
    def encode_one(self, scan: np.ndarray) -> TransmitRecord: ...

    def encode_batch(self, ranges: np.ndarray) -> list[TransmitRecord]:
        return [self.encode_one(row) for row in ranges]

    @abstractmethod
    def predict_from_payloads(self, payloads: list[bytes], n_beams: int, max_range: float) -> np.ndarray:
        ...

    def model_bytes(self) -> int:
        return 0

    def shared_memory_bytes(self) -> int:
        """Pre-shared tables (item memories, PCA basis, projection matrix)."""
        return 0

    def nbytes_of(self, *arrays: np.ndarray) -> int:
        return int(sum(np.asarray(a).nbytes for a in arrays))
