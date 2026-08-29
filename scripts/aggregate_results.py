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


def main() -> None:
    raw = ROOT / "results" / "raw"
    fig = ROOT / "results" / "figures"
    tables = ROOT / "results" / "tables"
    reports = ROOT / "reports"
    fig.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)

    bw = load_jsonl(raw / "bandwidth_sweep.jsonl")
    noise = load_jsonl(raw / "noise_sweep.jsonl")

    if not bw.empty:
        # collapse HDC dims into method label
        bw = bw.copy()
        if "dimension" in bw.columns:
            bw["method_label"] = bw.apply(
                lambda r: f"{r['method']}" + (f"_D{int(r['dimension'])}" if pd.notna(r["dimension"]) else ""),
                axis=1,
            )
        else:
            bw["method_label"] = bw["method"]
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
        _write_stage2(noise, reports / "stage2_noise.md")

    adapt_path = tables / "adaptation.json"
    if adapt_path.exists():
        adapt = pd.read_json(adapt_path)
        _write_final(bw, noise, adapt, reports / "final_report.md")
    else:
        _write_final(bw, noise, pd.DataFrame(), reports / "final_report.md")
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


def _write_stage2(noise: pd.DataFrame, path: Path) -> None:
    g = (
        noise.groupby(["method", "ber"])[["accuracy", "macro_f1"]]
        .agg(["mean", "std"])
        .round(4)
        .reset_index()
    )
    path.write_text(
        "\n".join(
            [
                "# Stage 2 — bit-error robustness",
                "",
                "Fixed 512 bytes/sample budget. Bit flips applied to the serialized payload, not to the classifier output.",
                "",
                _md_table(g),
                "",
                "Figure: `results/figures/accuracy_ber.png`.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_final(bw: pd.DataFrame, noise: pd.DataFrame, adapt: pd.DataFrame, path: Path) -> None:
    lines = [
        "# Working region of HDC for task-aware LiDAR communication",
        "",
        "This report answers the three questions in the project brief. It does **not** claim HDC wins everywhere.",
        "",
        "## What was measured",
        "",
        "- Task: 5-way place classification (corridor / room / doorway / open / cluttered) on `sim_indoor_v1`.",
        "- Receiver classifies from the transmitted representation; the scan is never reconstructed for the metric.",
        "- First-round methods: 8-bit quantization, PCA, binary hashing, pure HDC. Autoencoder and hybrid HDC are implemented for later stages.",
        "- Splits: trajectory hold-out (`test_id`) and a different floorplan (`test_ood`).",
        "",
        "## RQ1 — bandwidth",
        "",
        "On a 180-beam 2D scan, full 8-bit PCM is only **188 bytes** including header. Raising the budget above that does not add beams, so quantization saturates. HDC at D=8K is **1024 bytes**, already larger than the raw 8-bit scan — this is the brief's Risk 2.",
        "",
        "Clean-channel ID accuracy (means over 3 seeds): binary hashing is strongest (~0.86 at 128 B, ~0.92 at 512 B). Pure HDC sits with 8-bit PCM and PCA around **0.73–0.75** and barely moves with D. So HDC is **not** a bandwidth winner here (Outcome A fails). The hashing vs HDC gap is Risk 3: much of the clean-channel gain is **binarization + a trained linear head**, not position-level binding.",
        "",
        "See `reports/stage1_bandwidth.md` and `results/figures/accuracy_bandwidth.png`.",
        "",
        "## RQ2 — noise (clearest HDC advantage)",
        "",
        "At a 512-byte cap, flipping bits in the **payload** (not the labels):",
        "",
    ]
    if not noise.empty:
        g = noise.groupby(["method", "ber"])["accuracy"].mean().unstack("ber")
        lines.append(_md_table(g.reset_index()))
        lines += [
            "Pure HDC is almost flat from BER 0 to 0.10 (**~0.731 → ~0.729**). "
            "8-bit PCM drops **0.75 → 0.29**. PCA float32 bits collapse **0.75 → 0.17**. "
            "Binary hashing degrades slowly (**0.92 → 0.84**) but still faster than HDC.",
            "",
            "This is **Outcome B**: at matched budget, HDC shows repeatable graceful degradation versus at least two reasonable baselines, across seeds. Binary hashing shares the binary codebook robustness; HDC's extra structure did not win clean accuracy, but Hamming/cosine to analog prototypes is the most noise-stable classifier in this matrix.",
            "",
        ]
    lines += [
        "Figure: `results/figures/accuracy_ber.png`.",
        "",
        "## RQ3 — few-shot adaptation",
        "",
    ]
    if adapt.empty:
        lines.append("Run `python scripts/run_shift_adaptation.py` to fill this section.")
    else:
        lines.append(_md_table(adapt.round(4)))
        lines += [
            "",
            "HDC prototype add/subtract on OOD shots runs in **milliseconds** vs **~12 s** to refit the 8-bit logistic head on train+shots. "
            "OOD accuracy gains are modest for both; the linear head still ends slightly higher. Forgetting stays < 1 pp for HDC and ~1–2 pp for the refit. "
            "This is a **cost** win (Outcome C on update time), not an accuracy win.",
            "",
        ]
    lines += [
        "## Mapped operating region (Outcome D)",
        "",
        "| Regime | What happens |",
        "|---|---|",
        "| Clean channel, 2D 180-beam scan | Binary hashing (or AE) beats pure HDC. HDC ≈ 8-bit PCM. |",
        "| Budget ≫ 188 bytes | Extra bytes do not help 8-bit PCM; HDC larger than the scan is not a compression win. |",
        "| BER 1–10% on the payload | **HDC holds accuracy**; PCM and PCA cliff. Hashing holds most but not all. |",
        "| Few OOD labels | HDC updates are 100–1000× faster; accuracy recovery is small on this shift. |",
        "| Next levers | Region pooling, temporal n-grams, hybrid encoder (Stage 5), real labeled LiDAR. |",
        "",
        "## Reproducibility",
        "",
        "Configs in `configs/`. Frozen splits in `data/splits/sim_indoor_v1/`. Every JSONL row stores method, budget, BER, seed, and git commit.",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
