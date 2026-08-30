#!/usr/bin/env python3
"""k=16 communication-noise remake. Does not overwrite noise_sweep.jsonl.

Main grid: BER 0 / 0.01 / 0.05 / 0.10 at 128 B (D=1024) and 512 B (D=4096).
At 128 B only, also score a compact burst and packet-loss grid on the same
encoded payloads. Methods: k=16, k=1, linear head, hashing, 8-bit PCM.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hdc_lidar.data.io import load_dataset  # noqa: E402
from hdc_lidar.experiment import append_jsonl, encode_fitted, raw_dir, score_encoded  # noqa: E402
from hdc_lidar.methods import build_method  # noqa: E402
from hdc_lidar.types import ChannelConfig  # noqa: E402

BUDGETS = [128, 512]
SEEDS = [0, 1, 2]
SPLITS = ["test_id", "test_ood"]
BERS = [0.0, 0.01, 0.05, 0.10]
BURSTS_128 = [128, 512]
PLRS_128 = [0.05, 0.10, 0.20]
PACKET_BYTES = 32
METHODS = [
    ("quantized", {}),
    ("binary_hash", {}),
    ("pure_hdc", {"head": "prototype", "n_centroids": 1}),
    ("pure_hdc", {"head": "prototype", "n_centroids": 16}),
    ("pure_hdc", {"head": "linear", "n_centroids": 1}),
]


def _tag(name: str, kw: dict) -> str:
    if name == "quantized":
        return "quantized"
    if name == "binary_hash":
        return "binary_hash"
    if kw.get("head") == "linear":
        return "hdc_linear"
    return f"hdc_k{kw.get('n_centroids', 1)}"


def _score(method, records, test, channel, seed, budget, extra, split_name, out) -> None:
    row = score_encoded(method, records, test, channel, seed, budget, extra=extra)
    row.split = split_name
    append_jsonl(out, row)
    print(
        f"  {split_name} ber={channel.ber} burst={channel.burst_length} "
        f"plr={channel.packet_loss_rate} acc={row.accuracy:.3f}"
    )


def main() -> None:
    batch, splits, _ = load_dataset("sim_indoor_v1")
    train = batch.subset(splits["train"])
    out = raw_dir() / "k16_noise.jsonl"
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
                extra = {
                    "hdc_head": kw.get("head"),
                    "n_centroids": kw.get("n_centroids"),
                    "method_tag": tag,
                    "sweep": "k16_noise",
                }
                for split_name in SPLITS:
                    test = batch.subset(splits[split_name])
                    records = encode_fitted(method, test)
                    for ber in BERS:
                        channel = ChannelConfig(ber=ber, seed=seed)
                        _score(
                            method,
                            records,
                            test,
                            channel,
                            seed,
                            budget,
                            {**extra, "noise_kind": "ber"},
                            split_name,
                            out,
                        )
                    if budget != 128:
                        continue
                    for length in BURSTS_128:
                        channel = ChannelConfig(
                            burst_length=length, n_bursts=1, seed=seed
                        )
                        _score(
                            method,
                            records,
                            test,
                            channel,
                            seed,
                            budget,
                            {**extra, "noise_kind": "burst"},
                            split_name,
                            out,
                        )
                    for plr in PLRS_128:
                        channel = ChannelConfig(
                            packet_bytes=PACKET_BYTES,
                            packet_loss_rate=plr,
                            seed=seed,
                        )
                        _score(
                            method,
                            records,
                            test,
                            channel,
                            seed,
                            budget,
                            {**extra, "noise_kind": "plr"},
                            split_name,
                            out,
                        )
    print("wrote", out)


if __name__ == "__main__":
    main()
