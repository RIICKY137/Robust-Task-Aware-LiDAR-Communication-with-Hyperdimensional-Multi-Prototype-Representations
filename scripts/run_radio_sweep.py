#!/usr/bin/env python3
"""Stage 8: uncoded BPSK/QPSK over AWGN or block Rayleigh vs matched i.i.d. BER."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hdc_lidar.channels.radio import theoretical_ber  # noqa: E402
from hdc_lidar.data.io import load_dataset  # noqa: E402
from hdc_lidar.experiment import append_jsonl, encode_fitted, raw_dir, score_encoded  # noqa: E402
from hdc_lidar.methods import build_method  # noqa: E402
from hdc_lidar.types import ChannelConfig  # noqa: E402

BUDGET = 512
SEEDS = [0, 1, 2]
SNRS = [8.0, 6.0, 4.0, 2.0, 0.0, -2.0]
METHODS = [
    ("quantized", {}),
    ("pca", {}),
    ("binary_hash", {"dimension": 4096}),
    ("pure_hdc", {"dimension": 4096}),
]
KINDS = [
    ("bpsk_awgn", {"modulation": "bpsk", "fading": "none"}),
    (
        "bpsk_rayleigh_block",
        {"modulation": "bpsk", "fading": "rayleigh_block", "coherence_symbols": 32},
    ),
    ("qpsk_awgn", {"modulation": "qpsk", "fading": "none"}),
    ("matched_ber", None),
]
SPLIT = "test_id"


def _channel(kind: str, kwargs: dict | None, snr: float, seed: int) -> tuple[ChannelConfig, dict]:
    extra = {"channel_kind": kind, "snr_db": snr}
    if kind == "matched_ber":
        ber = theoretical_ber(snr, "bpsk", "none")
        extra["theory_ber"] = ber
        return ChannelConfig(ber=ber, seed=seed), extra
    cfg = ChannelConfig(snr_db=snr, seed=seed, **kwargs)
    extra["theory_ber"] = theoretical_ber(snr, cfg.modulation, cfg.fading)
    return cfg, extra


def main() -> None:
    batch, splits, _ = load_dataset("sim_indoor_v1")
    train = batch.subset(splits["train"])
    test = batch.subset(splits[SPLIT])
    out = raw_dir() / "radio_sweep.jsonl"
    if out.exists():
        out.unlink()
    for seed in SEEDS:
        for name, kw in METHODS:
            print(f"fit {name} seed={seed}")
            method = build_method(name, BUDGET, seed=seed, **kw)
            method.fit(train.ranges, train.labels, train.max_range)
            records = encode_fitted(method, test)
            for kind, radio_kw in KINDS:
                for snr in SNRS:
                    channel, extra = _channel(kind, radio_kw, snr, seed)
                    row = score_encoded(method, records, test, channel, seed, BUDGET, extra=extra)
                    row.split = SPLIT
                    append_jsonl(out, row)
                    print(
                        f"  {kind} snr={snr:.0f} acc={row.accuracy:.3f} "
                        f"emp_ber={row.extras.get('empirical_ber', float('nan')):.4f}"
                    )
    print("wrote", out)


if __name__ == "__main__":
    main()
