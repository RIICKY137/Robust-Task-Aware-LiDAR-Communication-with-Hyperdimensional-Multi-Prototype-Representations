"""Single-cell experiment: fit, encode, channel, classify, measure."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from hdc_lidar.channels import apply_channel, apply_channel_many
from hdc_lidar.channels.radio import theoretical_ber
from hdc_lidar.evaluation.metrics import task_metrics
from hdc_lidar.methods import build_method
from hdc_lidar.types import ChannelConfig, ExperimentRow, ScanBatch
from hdc_lidar.utils.bits import measured_ber
from hdc_lidar.utils.gitinfo import git_commit, repo_root
from hdc_lidar.utils.timing import timed_repeats


def run_cell(
    method_name: str,
    budget_bytes: int,
    train: ScanBatch,
    test: ScanBatch,
    channel: ChannelConfig,
    seed: int,
    method_kwargs: dict[str, Any] | None = None,
    time_repeats: int = 8,
) -> tuple[ExperimentRow, dict]:
    method = build_method(method_name, budget_bytes, seed=seed, **(method_kwargs or {}))
    method.fit(train.ranges, train.labels, train.max_range)

    probe = test.ranges[: min(32, len(test))]

    def _encode_probe():
        return method.encode_batch(probe)

    _, enc_stats = timed_repeats(_encode_probe, repeats=max(3, time_repeats // 2), warmup=1)
    records = method.encode_batch(test.ranges)
    actual_bits = float(np.mean([r.total_bits for r in records]))
    rng = np.random.default_rng(seed + 99)
    noisy = [apply_channel(r.payload, channel, rng) for r in records]

    def _predict_probe():
        return method.predict_from_payloads(noisy[: min(32, len(noisy))], test.n_beams, test.max_range)

    _, clf_stats = timed_repeats(_predict_probe, repeats=max(3, time_repeats // 2), warmup=1)
    pred = method.predict_from_payloads(noisy, test.n_beams, test.max_range)
    metrics = task_metrics(test.labels, pred)
    row = ExperimentRow(
        dataset="sim_indoor_v1",
        split="custom",
        method=method.name,
        budget_bytes=budget_bytes,
        actual_bytes=actual_bits / 8.0,
        ber=channel.ber,
        burst_length=channel.burst_length,
        packet_loss_rate=channel.packet_loss_rate,
        seed=seed,
        accuracy=metrics["accuracy"],
        macro_f1=metrics["macro_f1"],
        encode_ms_median=enc_stats["median_ms"],
        encode_ms_p95=enc_stats["p95_ms"],
        classify_ms_median=clf_stats["median_ms"],
        classify_ms_p95=clf_stats["p95_ms"],
        model_bytes=method.model_bytes(),
        shared_memory_bytes=method.shared_memory_bytes(),
        git_commit=git_commit(),
        extras={
            "dimension": getattr(method, "dimension", None),
            "n_keep": getattr(method, "n_keep", None),
            "n_comp": getattr(method, "n_comp", None),
            "n_levels": getattr(method, "n_levels", None),
            "interleave": channel.interleave,
            "n_bursts": channel.n_bursts,
            "hybrid_mode": getattr(method, "mode", None),
        },
    )
    return row, {"metrics": metrics, "pred": np.asarray(pred), "method": method}


def encode_fitted(method, test: ScanBatch) -> list:
    return method.encode_batch(test.ranges)


def score_encoded(
    method,
    records: list,
    test: ScanBatch,
    channel: ChannelConfig,
    seed: int,
    budget_bytes: int,
    extra: dict[str, Any] | None = None,
) -> ExperimentRow:
    """Apply a channel to already-encoded payloads. Does not refit."""
    rng = np.random.default_rng(seed + 99)
    noisy = apply_channel_many([r.payload for r in records], channel, rng)
    pred = method.predict_from_payloads(noisy, test.n_beams, test.max_range)
    metrics = task_metrics(test.labels, pred)
    actual_bits = float(np.mean([r.total_bits for r in records]))
    extras = {
        "dimension": getattr(method, "dimension", None),
        "n_keep": getattr(method, "n_keep", None),
        "n_comp": getattr(method, "n_comp", None),
        "interleave": channel.interleave,
        "n_bursts": channel.n_bursts,
        "hybrid_mode": getattr(method, "mode", None),
        "hdc_head": getattr(method, "head", None),
        "n_centroids": getattr(method, "n_centroids", None),
        "frontend": getattr(method, "frontend", None),
        "mix": getattr(method, "mix", None),
        "modulation": channel.modulation,
        "snr_db": channel.snr_db,
        "fading": channel.fading,
        "coherence_symbols": channel.coherence_symbols,
    }
    sample = min(64, len(records))
    if sample:
        extras["empirical_ber"] = float(
            np.mean([measured_ber(records[i].payload, noisy[i]) for i in range(sample)])
        )
    if channel.modulation not in {"", "none"} and channel.snr_db is not None:
        extras["theory_ber"] = theoretical_ber(
            float(channel.snr_db), channel.modulation, channel.fading
        )
    elif channel.ber > 0:
        extras["theory_ber"] = float(channel.ber)
    if extra:
        extras.update(extra)
    return ExperimentRow(
        dataset="sim_indoor_v1",
        split="custom",
        method=method.name,
        budget_bytes=budget_bytes,
        actual_bytes=actual_bits / 8.0,
        ber=channel.ber,
        burst_length=channel.burst_length,
        packet_loss_rate=channel.packet_loss_rate,
        seed=seed,
        accuracy=metrics["accuracy"],
        macro_f1=metrics["macro_f1"],
        encode_ms_median=0.0,
        encode_ms_p95=0.0,
        classify_ms_median=0.0,
        classify_ms_p95=0.0,
        model_bytes=method.model_bytes(),
        shared_memory_bytes=method.shared_memory_bytes(),
        git_commit=git_commit(),
        extras=extras,
    )


def row_to_dict(row: ExperimentRow) -> dict:
    d = dict(row.__dict__)
    extras = d.pop("extras", {})
    d.update({k: v for k, v in extras.items() if v is not None})
    return d


def append_jsonl(path: Path, row: ExperimentRow) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row_to_dict(row)) + "\n")


def raw_dir() -> Path:
    p = repo_root() / "results" / "raw"
    p.mkdir(parents=True, exist_ok=True)
    return p
