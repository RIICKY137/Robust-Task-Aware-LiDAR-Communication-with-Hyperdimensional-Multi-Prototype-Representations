#!/usr/bin/env python3
"""k=16 uncoded-radio remake. Does not overwrite radio_sweep.jsonl.

128 B (D=1024) is the operating point; 512 B is the control. Channels:
BPSK-AWGN, BPSK block Rayleigh (32-symbol coherence), and matched i.i.d.
BER at the closed-form BPSK-AWGN rate. QPSK is omitted (Gray-coded QPSK
matches BPSK). Methods: k=16, k=1, linear head, hashing, 8-bit PCM.
"""

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

BUDGETS = [128, 512]
SEEDS = [0, 1, 2]
SPLITS = ["test_id", "test_ood"]
SNRS = [8.0, 4.0, 0.0, -2.0]
METHODS = [
    ("quantized", {}),
    ("binary_hash", {}),
    ("pure_hdc", {"head": "prototype", "n_centroids": 1}),
    ("pure_hdc", {"head": "prototype", "n_centroids": 16}),
    ("pure_hdc", {"head": "linear", "n_centroids": 1}),
]
KINDS = [
    ("bpsk_awgn", {"modulation": "bpsk", "fading": "none"}),
    (
        "bpsk_rayleigh_block",
        {"modulation": "bpsk", "fading": "rayleigh_block", "coherence_symbols": 32},
    ),
    ("matched_ber", None),
]


def _tag(name: str, kw: dict) -> str:
    if name == "quantized":
        return "quantized"
    if name == "binary_hash":
        return "binary_hash"
    if kw.get("head") == "linear":
        return "hdc_linear"
    return f"hdc_k{kw.get('n_centroids', 1)}"


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
    out = raw_dir() / "k16_radio.jsonl"
    if out.exists():
        out.unlink()
    for seed in SEEDS:
        for budget in BUDGETS:
            dim = budget * 8
            for name, kw in METHODS:
                tag = _tag(name, kw)
                fit_kw = dict(kw)
                if name in {"pure_hdc", "binary_hash"}:
                    fit_kw["dimension"] = dim
                print(f"fit {tag} seed={seed} budget={budget} D={fit_kw.get('dimension')}")
                method = build_method(name, budget, seed=seed, **fit_kw)
                method.fit(train.ranges, train.labels, train.max_range)
                base = {
                    "hdc_head": kw.get("head"),
                    "n_centroids": kw.get("n_centroids"),
                    "method_tag": tag,
                    "sweep": "k16_radio",
                }
                for split_name in SPLITS:
                    test = batch.subset(splits[split_name])
                    records = encode_fitted(method, test)
                    for kind, radio_kw in KINDS:
                        for snr in SNRS:
                            channel, extra = _channel(kind, radio_kw, snr, seed)
                            extra.update(base)
                            row = score_encoded(
                                method, records, test, channel, seed, budget, extra=extra
                            )
                            row.split = split_name
                            append_jsonl(out, row)
                            emp = row.extras.get("empirical_ber", float("nan"))
                            print(
                                f"  {split_name} {kind} snr={snr:.0f} "
                                f"acc={row.accuracy:.3f} emp_ber={emp:.4f}"
                            )
    print("wrote", out)


if __name__ == "__main__":
    main()
