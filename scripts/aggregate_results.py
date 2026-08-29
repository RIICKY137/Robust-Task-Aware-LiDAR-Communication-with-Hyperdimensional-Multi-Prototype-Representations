#!/usr/bin/env python3
"""Build curves and markdown reports from results/raw JSONL."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hdc_lidar.features.viz import plot_metric_curves  # noqa: E402


def load_jsonl(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    metrics = ["accuracy", "macro_f1", "actual_bytes", "encode_ms_median", "classify_ms_median", "model_bytes"]
    have = [m for m in metrics if m in df.columns]
    return df.groupby(keys)[have].agg(["mean", "std"]).reset_index()


def method_label(df: pd.DataFrame) -> pd.Series:
    def _one(r):
        name = str(r.get("method", ""))
        mode = r.get("hybrid_mode")
        if name == "hybrid_hdc" and pd.notna(mode) and str(mode) not in {"", "None"}:
            name = f"hybrid_hdc:{mode}"
        elif name == "pure_hdc" and pd.notna(r.get("dimension")):
            try:
                name = f"pure_hdc_D{int(r['dimension'])}"
            except (TypeError, ValueError):
                pass
        if r.get("interleave") is True:
            name = f"{name}+intl"
        return name

    return df.apply(_one, axis=1)


def main() -> None:
    raw = ROOT / "results" / "raw"
    fig = ROOT / "results" / "figures"
    tables = ROOT / "results" / "tables"
    reports = ROOT / "reports"
    fig.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)

    bw = load_jsonl(raw / "bandwidth_sweep.jsonl")
    noise = load_jsonl(raw / "noise_sweep.jsonl")
    burst = load_jsonl(raw / "burst_sweep.jsonl")
    plr = load_jsonl(raw / "packet_loss_sweep.jsonl")
    sensor = load_jsonl(raw / "sensor_shift.jsonl")
    hybrid = load_jsonl(raw / "hybrid_sweep.jsonl")

    if not bw.empty:
        bw = bw.copy()
        bw["method_label"] = method_label(bw)
        plot_metric_curves(
            bw,
            x="budget_bytes",
            y="accuracy",
            hue="method_label",
            title="Accuracy vs communication budget (BER = 0)",
            path=fig / "accuracy_bandwidth.png",
            xlabel="Budget (bytes / sample)",
            ylabel="Accuracy",
        )
        plot_metric_curves(
            bw,
            x="budget_bytes",
            y="macro_f1",
            hue="method_label",
            title="Macro-F1 vs communication budget (BER = 0)",
            path=fig / "macrof1_bandwidth.png",
            xlabel="Budget (bytes / sample)",
            ylabel="Macro-F1",
        )
        bw.to_csv(tables / "bandwidth_sweep.csv", index=False)
        _write_stage1(bw, reports / "stage1_bandwidth.md")

    if not noise.empty:
        plot_metric_curves(
            noise,
            x="ber",
            y="accuracy",
            hue="method",
            title="Accuracy vs bit error rate (512 bytes/sample)",
            path=fig / "accuracy_ber.png",
            xlabel="BER",
            ylabel="Accuracy",
        )
        noise.to_csv(tables / "noise_sweep.csv", index=False)

    if not burst.empty:
        burst = burst.copy()
        burst["method_label"] = method_label(burst)
        plot_metric_curves(
            burst,
            x="burst_length",
            y="accuracy",
            hue="method_label",
            title="Accuracy vs burst length (512 bytes/sample)",
            path=fig / "accuracy_burst.png",
            xlabel="Burst length (bits)",
            ylabel="Accuracy",
        )
        burst.to_csv(tables / "burst_sweep.csv", index=False)

    if not plr.empty:
        plot_metric_curves(
            plr,
            x="packet_loss_rate",
            y="accuracy",
            hue="method",
            title="Accuracy vs packet loss rate (32-byte packets)",
            path=fig / "accuracy_packet_loss.png",
            xlabel="Packet loss rate",
            ylabel="Accuracy",
        )
        plr.to_csv(tables / "packet_loss_sweep.csv", index=False)

    if not noise.empty or not burst.empty or not plr.empty:
        _write_stage2(noise, burst, plr, reports / "stage2_noise.md")

    if not sensor.empty:
        sensor = sensor.copy()
        sensor["method_label"] = method_label(sensor)
        sensor.to_csv(tables / "sensor_shift.csv", index=False)
        _write_stage3(sensor, reports / "stage3_shift.md")

    if not hybrid.empty:
        hybrid = hybrid.copy()
        hybrid["method_label"] = method_label(hybrid)
        plot_metric_curves(
            hybrid,
            x="ber",
            y="accuracy",
            hue="method_label",
            title="Hybrid HDC vs hashing / pure HDC (512 bytes)",
            path=fig / "accuracy_hybrid_ber.png",
            xlabel="BER",
            ylabel="Accuracy",
        )
        hybrid.to_csv(tables / "hybrid_sweep.csv", index=False)
        _write_stage5(hybrid, reports / "stage5_hybrid.md")

    adapt_path = tables / "adaptation.json"
    adapt = pd.read_json(adapt_path) if adapt_path.exists() else pd.DataFrame()
    _write_final(bw, noise, burst, plr, sensor, hybrid, adapt, reports / "final_report.md")
    print("reports updated")


def _md_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._\n"
    flat = df.copy()
    if isinstance(flat.columns, pd.MultiIndex):
        flat.columns = ["_".join(str(x) for x in col if x != "") for col in flat.columns]
    cols = [str(c) for c in flat.columns]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for _, row in flat.iterrows():
        lines.append("| " + " | ".join(_fmt(row[c]) for c in flat.columns) + " |")
    return "\n".join(lines) + "\n"


def _fmt(v) -> str:
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)


def _write_stage1(bw: pd.DataFrame, path: Path) -> None:
    g = (
        bw.groupby(["method", "budget_bytes"], dropna=False)[["accuracy", "macro_f1", "actual_bytes"]]
        .mean()
        .reset_index()
        .round(4)
    )
    path.write_text(
        "\n".join(
            [
                "# Stage 1 — bandwidth vs task accuracy",
                "",
                "Clean channel (BER = 0). Means over seeds. HDC item memory is pre-shared and not counted in per-sample bytes.",
                "",
                _md_table(g),
                "",
                "Figures: `results/figures/accuracy_bandwidth.png`, `results/figures/macrof1_bandwidth.png`.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_stage2(noise: pd.DataFrame, burst: pd.DataFrame, plr: pd.DataFrame, path: Path) -> None:
    parts = [
        "# Stage 2 — communication robustness",
        "",
        "Noise is applied to the serialized payload. Receiver uses a pre-agreed layout; dropped packets are filled with zeros.",
        "",
        "## Random bit flips",
        "",
    ]
    if noise.empty:
        parts.append("_Run `python scripts/run_noise_sweep.py`._\n")
    else:
        g = (
            noise.groupby(["method", "ber"])[["accuracy", "macro_f1"]]
            .agg(["mean", "std"])
            .round(4)
            .reset_index()
        )
        parts += [_md_table(g), "Figure: `results/figures/accuracy_ber.png`.", ""]
    parts += ["## Burst errors", ""]
    if burst.empty:
        parts.append("_Run `python scripts/run_burst_sweep.py`._\n")
    else:
        g = (
            burst.groupby(["method", "burst_length", "interleave"])[["accuracy"]]
            .agg(["mean", "std"])
            .round(4)
            .reset_index()
        )
        parts += [
            _md_table(g),
            "Figure: `results/figures/accuracy_burst.png`. Interleaving permutes bits with a shared seed before the burst, then inverts the permutation at the receiver.",
            "",
        ]
    parts += ["## Packet loss", ""]
    if plr.empty:
        parts.append("_Run `python scripts/run_packet_loss_sweep.py`._\n")
    else:
        g = (
            plr.groupby(["method", "packet_loss_rate"])[["accuracy", "macro_f1"]]
            .agg(["mean", "std"])
            .round(4)
            .reset_index()
        )
        parts += [_md_table(g), "Figure: `results/figures/accuracy_packet_loss.png`.", ""]
    path.write_text("\n".join(parts), encoding="utf-8")


def _write_stage3(sensor: pd.DataFrame, path: Path) -> None:
    id_ = sensor[sensor["split"] == "test_id"] if "split" in sensor.columns else sensor
    g = (
        id_.groupby(["method_label", "sensor"])[["accuracy", "macro_f1"]]
        .mean()
        .reset_index()
        .round(4)
    )
    path.write_text(
        "\n".join(
            [
                "# Stage 3 — sensor corruption and environment shift",
                "",
                "These perturbations hit the LiDAR scan **before** encoding. They are not mixed into BER/PLR tables.",
                "",
                "In-distribution test (`test_id`), mean over seeds:",
                "",
                _md_table(g),
                "",
                "OOD (`test_ood`) is the held-out floorplan with the same corruptions. See `results/tables/sensor_shift.csv`.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_stage5(hybrid: pd.DataFrame, path: Path) -> None:
    g = (
        hybrid.groupby(["method_label", "ber"])[["accuracy", "macro_f1"]]
        .mean()
        .reset_index()
        .round(4)
    )
    path.write_text(
        "\n".join(
            [
                "# Stage 5 — hybrid neural-HDC",
                "",
                "`hybrid_hdc:frozen` maps sector statistics through `sign(Rz)` into HDC prototypes. "
                "`hybrid_hdc:task` first trains a small MLP on the place labels, freezes the hidden layer, then uses the same HDC head. "
                "Binary hashing remains the non-HDC binary control.",
                "",
                _md_table(g),
                "",
                "Figure: `results/figures/accuracy_hybrid_ber.png`.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_final(
    bw: pd.DataFrame,
    noise: pd.DataFrame,
    burst: pd.DataFrame,
    plr: pd.DataFrame,
    sensor: pd.DataFrame,
    hybrid: pd.DataFrame,
    adapt: pd.DataFrame,
    path: Path,
) -> None:
    lines = [
        "# Working region of HDC for task-aware LiDAR communication",
        "",
        "This report answers the three questions in the project brief. It does **not** claim HDC wins everywhere.",
        "",
        "## What was measured",
        "",
        "- Task: 5-way place classification on `sim_indoor_v1`.",
        "- Receiver classifies from the transmitted representation; the scan is never reconstructed.",
        "- Methods: 8-bit quantization, PCA, binary hashing, pure HDC, autoencoder, hybrid neural-HDC.",
        "- Stage 2 uses 5 seeds for burst and packet loss; BER used 3 seeds in the first-round matrix.",
        "",
        "## RQ1 — bandwidth",
        "",
        "See `reports/stage1_bandwidth.md`. On this 180-beam scan, 8-bit PCM saturates at ~188 bytes. Pure HDC is not a compression win (Outcome A fails). Binary hashing leads on a clean channel.",
        "",
        "## RQ2 — communication noise",
        "",
        "Random BER: `reports/stage2_noise.md` and `results/figures/accuracy_ber.png`.",
        "Burst + interleaving: `results/figures/accuracy_burst.png`.",
        "Packet loss (32 B packets, zero-fill): `results/figures/accuracy_packet_loss.png`.",
        "",
    ]
    if not noise.empty:
        g = noise.groupby(["method", "ber"])["accuracy"].mean().unstack("ber")
        lines += ["BER means:", "", _md_table(g.reset_index())]
    if not burst.empty:
        gb = (
            burst.groupby(["method", "burst_length", "interleave"])["accuracy"]
            .mean()
            .reset_index()
            .round(4)
        )
        lines += ["Burst means:", "", _md_table(gb)]
    if not plr.empty:
        gp = (
            plr.groupby(["method", "packet_loss_rate"])["accuracy"]
            .mean()
            .reset_index()
            .round(4)
        )
        lines += ["Packet-loss means:", "", _md_table(gp)]
    lines += [
        "## RQ3 — shift and adaptation",
        "",
        "Sensor corruptions (pre-encoder) and OOD floorplan: `reports/stage3_shift.md`.",
        "",
    ]
    if not adapt.empty:
        lines += [_md_table(adapt.round(4)), ""]
    lines += [
        "## Hybrid HDC (Stage 5)",
        "",
        "See `reports/stage5_hybrid.md`. This tests whether a task-trained encoder recovers the geometry that record-based pure HDC drops, while keeping a binary HDC payload.",
        "",
    ]
    if not hybrid.empty:
        gh = (
            hybrid.assign(method_label=method_label(hybrid))
            .groupby(["method_label", "ber"])["accuracy"]
            .mean()
            .reset_index()
            .round(4)
        )
        lines += [_md_table(gh)]
    lines += [
        "## Operating region",
        "",
        "| Regime | Current reading |",
        "|---|---|",
        "| Clean 2D scan | Hashing / AE beat pure HDC |",
        "| Random BER | Pure HDC almost flat; PCM/PCA cliff |",
        "| Burst / packet loss | See Stage 2 tables — binary codes degrade slower than float PCA |",
        "| Sensor dropout / scale | See Stage 3; not billed as communication noise |",
        "| Few-shot OOD | HDC updates are milliseconds vs seconds |",
        "| Hybrid encoder | Stage 5: does task MLP + HDC close the hashing gap? |",
        "",
        "Configs in `configs/`. Frozen splits in `data/splits/sim_indoor_v1/`.",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
