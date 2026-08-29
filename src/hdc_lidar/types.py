from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np

from hdc_lidar import LABELS

MethodName = Literal[
    "raw_float32",
    "quantized",
    "pca",
    "autoencoder",
    "binary_hash",
    "pure_hdc",
    "hybrid_hdc",
]
SplitName = Literal["train", "test_id", "test_ood"]


@dataclass
class ScanBatch:
    """Fixed-length 2D LiDAR scans plus split-safe metadata."""

    ranges: np.ndarray  # (N, B) float32, meters
    labels: np.ndarray  # (N,) int32
    env_ids: np.ndarray  # (N,) object/str
    traj_ids: np.ndarray
    sample_ids: np.ndarray
    poses: np.ndarray  # (N, 3) x, y, yaw
    max_range: float
    n_beams: int
    angle_min: float = 0.0
    angle_max: float = 2 * np.pi

    def __len__(self) -> int:
        return int(self.ranges.shape[0])

    def subset(self, idx: np.ndarray) -> "ScanBatch":
        return ScanBatch(
            ranges=self.ranges[idx],
            labels=self.labels[idx],
            env_ids=self.env_ids[idx],
            traj_ids=self.traj_ids[idx],
            sample_ids=self.sample_ids[idx],
            poses=self.poses[idx],
            max_range=self.max_range,
            n_beams=self.n_beams,
            angle_min=self.angle_min,
            angle_max=self.angle_max,
        )


@dataclass
class TransmitRecord:
    """What actually goes over the simulated channel."""

    payload: bytes
    n_payload_bits: int
    metadata_bits: int
    extras: dict[str, Any] = field(default_factory=dict)

    @property
    def total_bits(self) -> int:
        return int(self.n_payload_bits + self.metadata_bits)

    @property
    def total_bytes(self) -> float:
        return self.total_bits / 8.0


@dataclass
class ChannelConfig:
    ber: float = 0.0
    burst_length: int = 0
    n_bursts: int = 0
    burst_mode: Literal["flip", "erase"] = "flip"
    packet_bytes: int = 32
    packet_loss_rate: float = 0.0
    interleave: bool = False
    seed: int = 0
    # Stage 8 radio. When modulation is set and snr_db is finite, radio
    # replaces the abstract BER coin-flip (do not stack both).
    modulation: Literal["none", "bpsk", "qpsk"] = "none"
    snr_db: float | None = None
    fading: Literal["none", "rayleigh_iid", "rayleigh_block"] = "none"
    coherence_symbols: int = 32


@dataclass
class ExperimentRow:
    dataset: str
    split: str
    method: str
    budget_bytes: int
    actual_bytes: float
    ber: float
    burst_length: int
    packet_loss_rate: int | float
    seed: int
    accuracy: float
    macro_f1: float
    encode_ms_median: float
    encode_ms_p95: float
    classify_ms_median: float
    classify_ms_p95: float
    model_bytes: int
    shared_memory_bytes: int
    git_commit: str
    extras: dict[str, Any] = field(default_factory=dict)


def class_names() -> tuple[str, ...]:
    return LABELS
