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
            head = r.get("hdc_head")
            if pd.notna(head) and str(head) == "linear":
                name = f"{name}+lin"
            n_c = r.get("n_centroids")
            if pd.notna(n_c):
                try:
                    k = int(n_c)
                except (TypeError, ValueError):
                    k = 1
                if k > 1 and str(head) != "linear":
                    name = f"{name}/k{k}"
        if r.get("interleave") is True:
            name = f"{name}+intl"
        kind = r.get("channel_kind")
        if pd.notna(kind) and str(kind) not in {"", "None"}:
            name = f"{name}/{kind}"
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
    plr_intl = load_jsonl(raw / "packet_interleave_sweep.jsonl")
    sensor = load_jsonl(raw / "sensor_shift.jsonl")
    hybrid = load_jsonl(raw / "hybrid_sweep.jsonl")
    hybrid_lidar = load_jsonl(raw / "hybrid_lidar_sweep.jsonl")
    multicentroid = load_jsonl(raw / "multicentroid_sweep.jsonl")
    radio = load_jsonl(raw / "radio_sweep.jsonl")
    adapt_raw = load_jsonl(raw / "adaptation.jsonl")

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

    if not plr_intl.empty:
        plr_intl = plr_intl.copy()
        plr_intl["method_label"] = method_label(plr_intl)
        plot_metric_curves(
            plr_intl,
            x="packet_loss_rate",
            y="accuracy",
            hue="method_label",
            title="Packet loss with and without bit interleaving (32-byte packets)",
            path=fig / "accuracy_packet_interleave.png",
            xlabel="Packet loss rate",
            ylabel="Accuracy",
        )
        plr_intl.to_csv(tables / "packet_interleave_sweep.csv", index=False)

    if not noise.empty or not burst.empty or not plr.empty or not plr_intl.empty:
        _write_stage2(noise, burst, plr, reports / "stage2_noise.md", plr_intl=plr_intl)

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

    if not hybrid_lidar.empty:
        hybrid_lidar = hybrid_lidar.copy()
        hybrid_lidar["method_label"] = method_label(hybrid_lidar)
        plot_metric_curves(
            hybrid_lidar,
            x="ber",
            y="accuracy",
            hue="method_label",
            title="LiDAR hybrid HDC vs hashing (512 bytes)",
            path=fig / "accuracy_hybrid_lidar_ber.png",
            xlabel="BER",
            ylabel="Accuracy",
        )
        hybrid_lidar.to_csv(tables / "hybrid_lidar_sweep.csv", index=False)
        _write_stage5_lidar(hybrid_lidar, reports / "stage5_hybrid_lidar.md")

    if not multicentroid.empty:
        multicentroid = multicentroid.copy()
        multicentroid["method_label"] = method_label(multicentroid)
        id_ = (
            multicentroid[multicentroid["split"] == "test_id"]
            if "split" in multicentroid.columns
            else multicentroid
        )
        plot_metric_curves(
            id_,
            x="ber",
            y="accuracy",
            hue="method_label",
            title="Multi-centroid HDC vs linear head (512 bytes, test_id)",
            path=fig / "accuracy_multicentroid_ber.png",
            xlabel="BER",
            ylabel="Accuracy",
        )
        multicentroid.to_csv(tables / "multicentroid_sweep.csv", index=False)
        _write_multicentroid(multicentroid, reports / "multicentroid.md")

    if not radio.empty:
        radio = radio.copy()
        radio["method_label"] = method_label(radio)
        plot_metric_curves(
            radio,
            x="snr_db",
            y="accuracy",
            hue="method_label",
            title="Accuracy vs Eb/N0 (uncoded radio, 512 bytes)",
            path=fig / "accuracy_radio_snr.png",
            xlabel="Eb/N0 (dB)",
            ylabel="Accuracy",
        )
        radio.to_csv(tables / "radio_sweep.csv", index=False)
        _write_stage8(radio, reports / "stage8_radio.md")

    adapt_path = tables / "adaptation.json"
    if not adapt_raw.empty:
        adapt = adapt_raw
        adapt.to_csv(tables / "adaptation.csv", index=False)
        _write_stage4(adapt, reports / "stage4_adaptation.md")
        _plot_adaptation(adapt, fig / "accuracy_adaptation.png")
    elif adapt_path.exists():
        adapt = pd.read_json(adapt_path)
        _write_stage4(adapt, reports / "stage4_adaptation.md")
    else:
        adapt = pd.DataFrame()
    _write_final(
        bw,
        noise,
        burst,
        plr,
        sensor,
        hybrid,
        adapt,
        reports / "final_report.md",
        radio=radio,
        plr_intl=plr_intl,
        hybrid_lidar=hybrid_lidar,
        multicentroid=multicentroid,
    )
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


def _write_stage2(
    noise: pd.DataFrame,
    burst: pd.DataFrame,
    plr: pd.DataFrame,
    path: Path,
    plr_intl: pd.DataFrame | None = None,
) -> None:
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
    parts += ["## Packet loss + bit interleaving", ""]
    if plr_intl is None or plr_intl.empty:
        parts.append("_Run `python scripts/run_packet_interleave_sweep.py`._\n")
    else:
        g = (
            plr_intl.groupby(["method", "packet_loss_rate", "interleave"])[["accuracy"]]
            .agg(["mean", "std"])
            .round(4)
            .reset_index()
        )
        parts += [
            _md_table(g),
            "Figure: `results/figures/accuracy_packet_interleave.png`. "
            "Bits are permuted with a shared seed, packets are dropped, then the permutation is inverted. "
            "A lost packet therefore punches scattered holes instead of one contiguous zero block.",
            "",
        ]
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


def _write_stage5_lidar(hybrid: pd.DataFrame, path: Path) -> None:
    g = (
        hybrid.groupby(["method_label", "ber"])[["accuracy", "macro_f1"]]
        .mean()
        .reset_index()
        .round(4)
    )
    path.write_text(
        "\n".join(
            [
                "# LiDAR hybrid HDC — full scan, record bundle, linear vs prototype",
                "",
                "Stage 5 used 16-sector summaries, so the neural-HDC hybrid never saw the same "
                "geometry as binary hashing. This follow-up uses 2D LiDAR features (normalized "
                "range + circular derivative), optionally bundled with record-based `P_i ⊗ L_Q(r_i)`, "
                "and compares HDC prototypes against the same logistic head hashing uses.",
                "",
                _md_table(g),
                "",
                "Figure: `results/figures/accuracy_hybrid_lidar_ber.png`.",
                "",
                "Reading: if the linear head on record-based HDC matches or beats hashing, "
                "the hashing gap was the prototype classifier, not missing geometry in `P⊗L`. "
                "If prototypes stay near 0.73 while the linear head jumps, Outcome B (BER-flat "
                "binary codes) can coexist with a strong task head — the operating region is "
                "then 'HDC payload + trained head', not 'HDC prototypes everywhere'.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_multicentroid(df: pd.DataFrame, path: Path) -> None:
    keys = ["split", "method_label", "ber"] if "split" in df.columns else ["method_label", "ber"]
    g = df.groupby(keys)[["accuracy", "macro_f1"]].mean().reset_index().round(4)
    path.write_text(
        "\n".join(
            [
                "# Multi-centroid HDC",
                "",
                "The transmitted payload is still one bipolar hypervector per scan (`P_i ⊗ L_Q(r_i)` bundled). "
                "What changes is the receiver: k-means on the training hypervectors of each class, "
                "then nearest-centroid cosine. `k=1` is the original class-wide sum. "
                "The linear head is the same logistic classifier used with hashing, trained on the same codes.",
                "",
                _md_table(g),
                "",
                "Figure: `results/figures/accuracy_multicentroid_ber.png` (in-distribution).",
                "",
                "Reading: if raising k lifts in-distribution accuracy toward the linear head while "
                "staying BER-flat, the 0.73 ceiling was unimodal prototypes, not a weak code. "
                "OOD (`test_ood`) is the check that extra centroids did not just memorize the "
                "training building. Few-shot updates still add to the nearest centroid.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _plot_adaptation(adapt: pd.DataFrame, path: Path) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    fig.patch.set_facecolor("#020617")
    ax.set_facecolor("#0b1220")
    mapping = [
        ("hdc_new_acc", "pure HDC (OOD)"),
        ("quant_new_acc", "8-bit + logreg (OOD)"),
        ("hybrid_new_acc", "hybrid-task HDC (OOD)"),
    ]
    for col, label in mapping:
        if col not in adapt.columns:
            continue
        g = adapt.groupby("shots_per_class")[col].agg(["mean", "std"]).reset_index()
        ax.plot(g["shots_per_class"], g["mean"], marker="o", label=label)
        ax.fill_between(
            g["shots_per_class"],
            g["mean"] - g["std"].fillna(0),
            g["mean"] + g["std"].fillna(0),
            alpha=0.15,
        )
    ax.set_title("OOD accuracy vs labeled shots per class", color="#e2e8f0")
    ax.set_xlabel("Shots per class", color="#94a3b8")
    ax.set_ylabel("Accuracy", color="#94a3b8")
    ax.tick_params(colors="#94a3b8")
    ax.legend(facecolor="#0f172a", edgecolor="#1e293b", labelcolor="#e2e8f0")
    for spine in ax.spines.values():
        spine.set_color("#1e293b")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def _write_stage4(adapt: pd.DataFrame, path: Path) -> None:
    keys = ["shots_per_class"]
    cols = [
        c
        for c in [
            "hdc_new_acc",
            "hdc_old_acc",
            "hdc_forgetting",
            "hdc_adapt_ms",
            "quant_new_acc",
            "quant_old_acc",
            "quant_forgetting",
            "quant_adapt_ms",
            "hybrid_new_acc",
            "hybrid_old_acc",
            "hybrid_forgetting",
            "hybrid_adapt_ms",
        ]
        if c in adapt.columns
    ]
    g = adapt.groupby(keys)[cols].agg(["mean", "std"]).round(4).reset_index()
    path.write_text(
        "\n".join(
            [
                "# Stage 4 — few-shot adaptation after environment shift",
                "",
                "Target is `test_ood` (held-out floorplan). Old-task accuracy is `test_id`. "
                "HDC and hybrid-task update class prototypes by adding the encoded shot "
                "(and subtracting the current prediction). The 8-bit baseline refits logistic "
                "regression on train features plus the shots. Times are wall-clock for the update only.",
                "",
                _md_table(g),
                "",
                "Figure: `results/figures/accuracy_adaptation.png`.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_stage8(radio: pd.DataFrame, path: Path) -> None:
    g = (
        radio.groupby(["method", "channel_kind", "snr_db"])[["accuracy", "empirical_ber", "theory_ber"]]
        .mean()
        .reset_index()
        .round(4)
    )
    path.write_text(
        "\n".join(
            [
                "# Stage 8 — uncoded radio vs i.i.d. BER",
                "",
                "Eb/N0 is the physical-layer SNR. BPSK/QPSK use hard decisions so the rest of "
                "the stack still sees a bitstream. `matched_ber` flips bits i.i.d. at the closed-form "
                "uncoded BPSK-AWGN BER for the same Eb/N0. Block Rayleigh (32-symbol coherence) "
                "produces clustered errors; that is the test of whether holographic codes still "
                "look BER-flat when the radio is not a coin-flip.",
                "",
                _md_table(g),
                "",
                "Figure: `results/figures/accuracy_radio_snr.png`.",
                "",
                "On this dataset, holographic HDC stays near its clean accuracy even when "
                "block Rayleigh drives empirical BER above 0.1. Binary hashing degrades slowly. "
                "8-bit PCM and PCA still collapse. BPSK AWGN and `matched_ber` agree, so the "
                "abstract coin-flip did not overstate HDC here — the remaining gap is still "
                "clean-channel accuracy versus hashing, not a hidden radio-structure failure.",
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
    radio: pd.DataFrame | None = None,
    plr_intl: pd.DataFrame | None = None,
    hybrid_lidar: pd.DataFrame | None = None,
    multicentroid: pd.DataFrame | None = None,
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
        "- Stage 4 uses 10 / 50 / 100 shots per class, 3 seeds.",
        "- Stage 8 is uncoded BPSK/QPSK at a grid of Eb/N0, plus matched i.i.d. BER.",
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
        "Packet loss + interleaving: `results/figures/accuracy_packet_interleave.png`.",
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
    if plr_intl is not None and not plr_intl.empty:
        gi = (
            plr_intl.groupby(["method", "packet_loss_rate", "interleave"])["accuracy"]
            .mean()
            .reset_index()
            .round(4)
        )
        lines += ["Packet-loss × interleave means:", "", _md_table(gi)]
    lines += [
        "## RQ3 — shift and adaptation",
        "",
        "Sensor corruptions (pre-encoder) and OOD floorplan: `reports/stage3_shift.md`.",
        "Few-shot prototype / head updates: `reports/stage4_adaptation.md`.",
        "",
    ]
    if not adapt.empty:
        keys = [c for c in ["shots_per_class"] if c in adapt.columns]
        mean_cols = [
            c
            for c in adapt.columns
            if c not in keys and c != "seed" and pd.api.types.is_numeric_dtype(adapt[c])
        ]
        shown = adapt.groupby(keys)[mean_cols].mean().reset_index().round(4) if keys else adapt.round(4)
        lines += [_md_table(shown), ""]
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
    if hybrid_lidar is not None and not hybrid_lidar.empty:
        lines += [
            "## LiDAR hybrid HDC",
            "",
            "See `reports/stage5_hybrid_lidar.md`. Full-scan frontend ± record bundle, prototype vs linear head.",
            "",
        ]
        gl = (
            hybrid_lidar.assign(method_label=method_label(hybrid_lidar))
            .groupby(["method_label", "ber"])["accuracy"]
            .mean()
            .reset_index()
            .round(4)
        )
        lines += [_md_table(gl)]
    if multicentroid is not None and not multicentroid.empty:
        lines += [
            "## Multi-centroid HDC",
            "",
            "See `reports/multicentroid.md`. Same `P⊗L` payload; k prototypes per class vs a linear head.",
            "",
        ]
        gm = (
            multicentroid.assign(method_label=method_label(multicentroid))
            .groupby(["split", "method_label", "ber"])["accuracy"]
            .mean()
            .reset_index()
            .round(4)
        )
        lines += [_md_table(gm)]
    if radio is not None and not radio.empty:
        lines += [
            "## Realistic radio (Stage 8)",
            "",
            "See `reports/stage8_radio.md`. Uncoded BPSK/QPSK hard decisions vs matched i.i.d. BER at the same Eb/N0.",
            "",
        ]
        gr = (
            radio.groupby(["method", "channel_kind", "snr_db"])["accuracy"]
            .mean()
            .reset_index()
            .round(4)
        )
        lines += [_md_table(gr)]
    lines += [
        "## Operating region",
        "",
        "| Regime | Current reading |",
        "|---|---|",
        "| Clean 2D scan | Hashing / AE beat pure HDC |",
        "| Random BER | Pure HDC almost flat; PCM/PCA cliff |",
        "| Burst / packet loss | Binary codes degrade slower than float PCA; interleave hurts PCM |",
        "| Uncoded radio | Pure HDC stays flat under BPSK/QPSK AWGN and block Rayleigh; PCM/PCA still cliff. Matched i.i.d. BER tracks AWGN. |",
        "| Sensor dropout / scale | See Stage 3; not billed as communication noise |",
        "| Few-shot OOD | HDC updates are milliseconds vs seconds for a linear refit |",
        "| Hybrid encoder | Prototype head ~0.73–0.80; linear head on HDC codes can match/beat hashing |",
        "| Multi-centroid | k>1 lifts prototype accuracy while staying BER-flat; see OOD vs linear in the table |",
        "",
        "Configs in `configs/`. Frozen splits in `data/splits/sim_indoor_v1/`.",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
