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
    mc_adapt = load_jsonl(raw / "multicentroid_adaptation.jsonl")
    k16_bw = load_jsonl(raw / "k16_bandwidth.jsonl")
    k16_sensor = load_jsonl(raw / "k16_sensor.jsonl")
    k16_noise = load_jsonl(raw / "k16_noise.jsonl")
    k16_radio = load_jsonl(raw / "k16_radio.jsonl")
    k16_sector_encode = load_jsonl(raw / "k16_sector_encode.jsonl")
    k16_adapt_128 = load_jsonl(raw / "k16_adaptation_128b.jsonl")
    k16_semantic2d = load_jsonl(raw / "k16_semantic2d.jsonl")
    k16_lidardataframes = load_jsonl(raw / "k16_lidardataframes.jsonl")
    k16_ldf_sensor = load_jsonl(raw / "k16_lidardataframes_sensor.jsonl")

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
    if not mc_adapt.empty:
        mc_adapt.to_csv(tables / "multicentroid_adaptation.csv", index=False)
        _write_mc_adapt(mc_adapt, reports / "stage4_multicentroid_adapt.md")
        _plot_mc_adapt(mc_adapt, fig / "accuracy_multicentroid_adaptation.png")

    if not k16_bw.empty:
        k16_bw = k16_bw.copy()
        k16_bw["method_label"] = k16_bw["method_tag"] if "method_tag" in k16_bw.columns else method_label(k16_bw)
        id_bw = k16_bw[k16_bw["split"] == "test_id"] if "split" in k16_bw.columns else k16_bw
        plot_metric_curves(
            id_bw,
            x="budget_bytes",
            y="accuracy",
            hue="method_label",
            title="k=16 HDC vs hashing / PCM (clean channel, test_id)",
            path=fig / "accuracy_k16_bandwidth.png",
            xlabel="Budget (bytes / sample)",
            ylabel="Accuracy",
        )
        ood_bw = k16_bw[k16_bw["split"] == "test_ood"] if "split" in k16_bw.columns else pd.DataFrame()
        if not ood_bw.empty:
            plot_metric_curves(
                ood_bw,
                x="budget_bytes",
                y="accuracy",
                hue="method_label",
                title="k=16 HDC vs hashing / PCM (clean channel, test_ood)",
                path=fig / "accuracy_k16_bandwidth_ood.png",
                xlabel="Budget (bytes / sample)",
                ylabel="Accuracy",
            )
        k16_bw.to_csv(tables / "k16_bandwidth.csv", index=False)
        _write_k16_bandwidth(k16_bw, reports / "stage1_k16_bandwidth.md")

    if not k16_sensor.empty:
        k16_sensor = k16_sensor.copy()
        k16_sensor["method_label"] = (
            k16_sensor["method_tag"] if "method_tag" in k16_sensor.columns else method_label(k16_sensor)
        )
        k16_sensor.to_csv(tables / "k16_sensor.csv", index=False)
        _plot_k16_dropout(k16_sensor, fig)
        _write_k16_sensor(k16_sensor, reports / "stage3_k16_sensor.md")

    if not k16_noise.empty:
        k16_noise = k16_noise.copy()
        k16_noise["method_label"] = (
            k16_noise["method_tag"] if "method_tag" in k16_noise.columns else method_label(k16_noise)
        )
        k16_noise.to_csv(tables / "k16_noise.csv", index=False)
        _plot_k16_noise(k16_noise, fig)
        _write_k16_noise(k16_noise, reports / "stage2_k16_noise.md")

    if not k16_radio.empty:
        k16_radio = k16_radio.copy()
        k16_radio["method_label"] = (
            k16_radio["method_tag"] if "method_tag" in k16_radio.columns else method_label(k16_radio)
        )
        k16_radio.to_csv(tables / "k16_radio.csv", index=False)
        _plot_k16_radio(k16_radio, fig)
        _write_k16_radio(k16_radio, reports / "stage8_k16_radio.md")

    if not k16_sector_encode.empty:
        k16_sector_encode = k16_sector_encode.copy()
        k16_sector_encode["method_label"] = (
            k16_sector_encode["method_tag"]
            if "method_tag" in k16_sector_encode.columns
            else method_label(k16_sector_encode)
        )
        k16_sector_encode.to_csv(tables / "k16_sector_encode.csv", index=False)
        _plot_k16_sector_encode(k16_sector_encode, fig)
        _write_k16_sector_encode(k16_sector_encode, reports / "stage3_k16_sector_encode.md")
    if not k16_adapt_128.empty:
        k16_adapt_128.to_csv(tables / "k16_adaptation_128b.csv", index=False)
        _plot_k16_adapt_128(k16_adapt_128, fig / "accuracy_k16_adaptation_128b.png")
        _write_k16_adapt_128(k16_adapt_128, reports / "stage4_k16_adaptation_128b.md")
    if not k16_semantic2d.empty:
        k16_semantic2d = k16_semantic2d.copy()
        k16_semantic2d["method_label"] = (
            k16_semantic2d["method_tag"]
            if "method_tag" in k16_semantic2d.columns
            else method_label(k16_semantic2d)
        )
        k16_semantic2d.to_csv(tables / "k16_semantic2d.csv", index=False)
        _plot_k16_semantic2d(k16_semantic2d, fig)
        _write_k16_semantic2d(k16_semantic2d, reports / "stage0_semantic2d.md")
    if not k16_lidardataframes.empty:
        k16_lidardataframes = k16_lidardataframes.copy()
        k16_lidardataframes["method_label"] = (
            k16_lidardataframes["method_tag"]
            if "method_tag" in k16_lidardataframes.columns
            else method_label(k16_lidardataframes)
        )
        k16_lidardataframes.to_csv(tables / "k16_lidardataframes.csv", index=False)
        _plot_k16_lidardataframes(k16_lidardataframes, fig)
        _write_k16_lidardataframes(k16_lidardataframes, reports / "stage0_lidardataframes.md")
    if not k16_ldf_sensor.empty:
        k16_ldf_sensor = k16_ldf_sensor.copy()
        k16_ldf_sensor["method_label"] = (
            k16_ldf_sensor["method_tag"]
            if "method_tag" in k16_ldf_sensor.columns
            else method_label(k16_ldf_sensor)
        )
        k16_ldf_sensor.to_csv(tables / "k16_lidardataframes_sensor.csv", index=False)
        _plot_k16_lidardataframes_sensor(k16_ldf_sensor, fig)
        _write_k16_lidardataframes_sensor(
            k16_ldf_sensor, reports / "stage3_k16_lidardataframes_sensor.md"
        )

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
        mc_adapt=mc_adapt,
        k16_bw=k16_bw,
        k16_sensor=k16_sensor,
        k16_noise=k16_noise,
        k16_radio=k16_radio,
        k16_sector_encode=k16_sector_encode,
        k16_adapt_128=k16_adapt_128,
        k16_semantic2d=k16_semantic2d,
        k16_lidardataframes=k16_lidardataframes,
        k16_ldf_sensor=k16_ldf_sensor,
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


def _plot_mc_adapt(adapt: pd.DataFrame, path: Path) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    fig.patch.set_facecolor("#020617")
    ax.set_facecolor("#0b1220")
    for method, sub in adapt.groupby("method"):
        g = sub.groupby("shots_per_class")["new_acc"].agg(["mean", "std"]).reset_index()
        ax.plot(g["shots_per_class"], g["mean"], marker="o", label=str(method))
        ax.fill_between(
            g["shots_per_class"],
            g["mean"] - g["std"].fillna(0),
            g["mean"] + g["std"].fillna(0),
            alpha=0.15,
        )
    ax.set_title("OOD accuracy after few-shot centroid / head update", color="#e2e8f0")
    ax.set_xlabel("Shots per class", color="#94a3b8")
    ax.set_ylabel("OOD accuracy", color="#94a3b8")
    ax.tick_params(colors="#94a3b8")
    ax.legend(facecolor="#0f172a", edgecolor="#1e293b", labelcolor="#e2e8f0")
    for spine in ax.spines.values():
        spine.set_color("#1e293b")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def _write_mc_adapt(adapt: pd.DataFrame, path: Path) -> None:
    cols = [
        c
        for c in [
            "before_new_acc",
            "new_acc",
            "delta_new",
            "before_old_acc",
            "old_acc",
            "forgetting",
            "adapt_ms",
        ]
        if c in adapt.columns
    ]
    g = adapt.groupby(["method", "shots_per_class"])[cols].agg(["mean", "std"]).round(4).reset_index()
    path.write_text(
        "\n".join(
            [
                "# Few-shot OOD adaptation — multi-centroid vs linear head",
                "",
                "Target is `test_ood`. Old-task accuracy is `test_id`. "
                "`hdc_k1` / `hdc_k8` / `hdc_k16` add (and subtract the current prediction from) "
                "the nearest class centroid. `hdc_linear` refits logistic regression on train "
                "hypervectors plus the labeled shots. Times are wall-clock for the update only.",
                "",
                _md_table(g),
                "",
                "Figure: `results/figures/accuracy_multicentroid_adaptation.png`.",
                "",
            ]
        ),
        encoding="utf-8",
    )


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


def _sensor_rate(label: str, kind: str) -> float | None:
    s = str(label)
    if s == "clean":
        return 0.0
    if kind == "beam" and s.startswith("beam_drop:"):
        return float(s.split("=", 1)[1])
    if kind == "sector" and s.startswith("sector_drop:"):
        return float(s.split("=", 1)[1])
    return None


def _plot_k16_dropout(df: pd.DataFrame, fig: Path) -> None:
    id_ = df[df["split"] == "test_id"] if "split" in df.columns else df
    for kind, title, fname in (
        ("beam", "Beam dropout vs accuracy (512 B, test_id, BER = 0)", "accuracy_k16_beam_drop.png"),
        ("sector", "Sector dropout vs accuracy (512 B, test_id, BER = 0)", "accuracy_k16_sector_drop.png"),
    ):
        rows = []
        for _, r in id_.iterrows():
            rate = _sensor_rate(r.get("sensor", ""), kind)
            if rate is None:
                continue
            rows.append({**r.to_dict(), "drop_rate": rate})
        if not rows:
            continue
        sub = pd.DataFrame(rows)
        plot_metric_curves(
            sub,
            x="drop_rate",
            y="accuracy",
            hue="method_label",
            title=title,
            path=fig / fname,
            xlabel="Dropped fraction of beams",
            ylabel="Accuracy",
        )


def _write_k16_bandwidth(df: pd.DataFrame, path: Path) -> None:
    g = (
        df.groupby(["split", "method_label", "budget_bytes"], dropna=False)[["accuracy", "macro_f1", "actual_bytes"]]
        .mean()
        .reset_index()
        .round(4)
    )
    path.write_text(
        "\n".join(
            [
                "# Stage 1 remake — k=16 HDC vs bandwidth",
                "",
                "Clean channel (BER = 0). Dimension fills the budget (`D = 8 × bytes`): "
                "128 B → 1024, 512 B → 4096, 2048 B → 16384. The payload is still **one** "
                "hypervector per scan; `k` is the number of centroids at the receiver. "
                "First-round `bandwidth_sweep.jsonl` is left unchanged.",
                "",
                "Means over seeds:",
                "",
                _md_table(g),
                "",
                "Figures: `results/figures/accuracy_k16_bandwidth.png`, "
                "`results/figures/accuracy_k16_bandwidth_ood.png`.",
                "",
                "## Reading",
                "",
                "- **k=1 is still not a compressor.** Accuracy stays ~0.73 in-distribution at every budget.",
                "- **k=16 saturates early.** At 128 B (`D=1024`) it is already ~0.95 in-distribution, "
                "matching hashing at 2048 B, and ~0.84 OOD (hashing stays ~0.58–0.63).",
                "- Extra bytes help the **linear** head in-distribution (0.95 → 0.98) more than k=16. "
                "k=16 stays ahead of linear on OOD at every budget.",
                "- 8-bit PCM saturates at 188 B and does not use the extra budget.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_k16_sensor(df: pd.DataFrame, path: Path) -> None:
    id_ = df[df["split"] == "test_id"] if "split" in df.columns else df
    ood = df[df["split"] == "test_ood"] if "split" in df.columns else pd.DataFrame()
    g_id = (
        id_.groupby(["method_label", "sensor"])[["accuracy", "macro_f1"]]
        .mean()
        .reset_index()
        .round(4)
    )
    parts = [
        "# Stage 3 remake — k=16 HDC under sensor dropout",
        "",
        "Corruptions hit the LiDAR scan **before** encoding. Budget 512 bytes, `D=4096`, BER = 0. "
        "Compared with k=1 prototypes, a linear head, hashing, and 8-bit PCM. "
        "First-round `sensor_shift.jsonl` is left unchanged.",
        "",
        "In-distribution (`test_id`), mean over seeds:",
        "",
        _md_table(g_id),
        "",
        "Figures: `results/figures/accuracy_k16_beam_drop.png`, "
        "`results/figures/accuracy_k16_sector_drop.png`.",
        "",
    ]
    if not ood.empty:
        g_ood = (
            ood.groupby(["method_label", "sensor"])[["accuracy", "macro_f1"]]
            .mean()
            .reset_index()
            .round(4)
        )
        parts += ["OOD (`test_ood`), mean over seeds:", "", _md_table(g_ood), ""]
    parts += [
        "## Reading",
        "",
        "- **Scattered beam dropout is the k=16 operating region.** At 10% random beam drop, "
        "in-distribution k=16 stays near clean (~0.94) while hashing falls to ~0.50 and the linear "
        "head to ~0.75. At 30% it is still ~0.80 vs ~0.23 hashing / ~0.53 linear.",
        "- **Contiguous sector drop is a failure region.** 15% sector drop: k=16 ~0.79 vs linear ~0.59 "
        "vs hashing ~0.39. At 30% (~54 adjacent beams) k=16 collapses to ~0.39, no better than k=1.",
        "- Mild range noise / bias barely moves k=16. Range clip to 6 m hurts the linear head more "
        "than nearest-centroid (~0.54 vs ~0.88 in-distribution).",
        "",
    ]
    path.write_text("\n".join(parts), encoding="utf-8")


def _k16_ber_rows(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "noise_kind" in out.columns:
        return out[out["noise_kind"].astype(str) == "ber"]
    for col, default in (("burst_length", 0), ("packet_loss_rate", 0.0)):
        if col not in out.columns:
            out[col] = default
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(default)
    return out[(out["burst_length"] == 0) & (out["packet_loss_rate"] == 0)]


def _plot_k16_noise(df: pd.DataFrame, fig: Path) -> None:
    ber = _k16_ber_rows(df)
    for split, suffix, split_title in (
        ("test_id", "", "test_id"),
        ("test_ood", "_ood", "test_ood"),
    ):
        sub_split = ber[ber["split"] == split] if "split" in ber.columns else ber
        for budget in (128, 512):
            sub = sub_split[sub_split["budget_bytes"] == budget] if "budget_bytes" in sub_split.columns else sub_split
            if sub.empty:
                continue
            plot_metric_curves(
                sub,
                x="ber",
                y="accuracy",
                hue="method_label",
                title=f"k=16 HDC vs BER ({budget} B, {split_title})",
                path=fig / f"accuracy_k16_ber_{budget}{suffix}.png",
                xlabel="BER",
                ylabel="Accuracy",
            )
    burst = df.copy()
    if "noise_kind" in burst.columns:
        burst_rows = burst[burst["noise_kind"].astype(str) == "burst"]
    else:
        burst_rows = pd.DataFrame()
    if not burst_rows.empty:
        clean_128 = ber[(ber["budget_bytes"] == 128) & (ber["ber"] == 0)].copy()
        if not clean_128.empty:
            clean_128 = clean_128.copy()
            clean_128["burst_length"] = 0
            burst_rows = pd.concat([clean_128, burst_rows], ignore_index=True)
        id_ = burst_rows[burst_rows["split"] == "test_id"] if "split" in burst_rows.columns else burst_rows
        plot_metric_curves(
            id_,
            x="burst_length",
            y="accuracy",
            hue="method_label",
            title="k=16 HDC vs burst length (128 B, test_id)",
            path=fig / "accuracy_k16_burst_128.png",
            xlabel="Burst length (bits)",
            ylabel="Accuracy",
        )
    if "noise_kind" in df.columns:
        plr_rows = df[df["noise_kind"].astype(str) == "plr"]
        if not plr_rows.empty:
            clean_128 = ber[(ber["budget_bytes"] == 128) & (ber["ber"] == 0)].copy()
            if not clean_128.empty:
                clean_128 = clean_128.copy()
                clean_128["packet_loss_rate"] = 0.0
                plr_rows = pd.concat([clean_128, plr_rows], ignore_index=True)
            id_ = plr_rows[plr_rows["split"] == "test_id"] if "split" in plr_rows.columns else plr_rows
            plot_metric_curves(
                id_,
                x="packet_loss_rate",
                y="accuracy",
                hue="method_label",
                title="k=16 HDC vs packet loss (128 B, 32-byte packets, test_id)",
                path=fig / "accuracy_k16_plr_128.png",
                xlabel="Packet loss rate",
                ylabel="Accuracy",
            )


def _write_k16_noise(df: pd.DataFrame, path: Path) -> None:
    ber = _k16_ber_rows(df)
    g_ber = (
        ber.groupby(["split", "method_label", "budget_bytes", "ber"], dropna=False)[["accuracy", "macro_f1"]]
        .mean()
        .reset_index()
        .round(4)
    )
    parts = [
        "# Stage 2 remake — k=16 HDC under bitstream noise",
        "",
        "Dimension fills the budget: 128 B → `D=1024`, 512 B → `D=4096`. "
        "The payload is still **one** hypervector per scan. "
        "First-round `noise_sweep.jsonl` / `burst_sweep.jsonl` / `packet_loss_sweep.jsonl` are unchanged.",
        "",
        "BER means over seeds:",
        "",
        _md_table(g_ber),
        "",
        "Figures: `results/figures/accuracy_k16_ber_128.png`, "
        "`results/figures/accuracy_k16_ber_512.png`, "
        "`results/figures/accuracy_k16_ber_128_ood.png`, "
        "`results/figures/accuracy_k16_ber_512_ood.png`.",
        "",
    ]
    burst = df[df["noise_kind"].astype(str) == "burst"] if "noise_kind" in df.columns else pd.DataFrame()
    if not burst.empty:
        g_b = (
            burst.groupby(["split", "method_label", "burst_length"])[["accuracy"]]
            .mean()
            .reset_index()
            .round(4)
        )
        parts += [
            "Burst (128 B only, one contiguous flip block, no interleave):",
            "",
            _md_table(g_b),
            "",
            "Figure: `results/figures/accuracy_k16_burst_128.png`.",
            "",
        ]
    plr = df[df["noise_kind"].astype(str) == "plr"] if "noise_kind" in df.columns else pd.DataFrame()
    if not plr.empty:
        g_p = (
            plr.groupby(["split", "method_label", "packet_loss_rate"])[["accuracy"]]
            .mean()
            .reset_index()
            .round(4)
        )
        parts += [
            "Packet loss (128 B only, 32-byte packets, zero-fill):",
            "",
            _md_table(g_p),
            "",
            "Figure: `results/figures/accuracy_k16_plr_128.png`.",
            "",
        ]
    parts += [
        "## Reading",
        "",
        "- **k=16 stays BER-flat at 128 B.** In-distribution accuracy is ~0.95 from BER 0 to 0.10, "
        "matching the 512 B curve. k=1 is also flat, but stuck at ~0.73.",
        "- **The linear head is not holographic at 128 B.** It drops ~0.95 → ~0.86 in-distribution "
        "at BER 0.10. At 512 B the same head was almost flat. Hashing at 128 B falls ~0.86 → ~0.68; "
        "8-bit PCM cliffs ~0.74 → ~0.31.",
        "- **Scattered packet loss (32 B packets) is still in the k=16 region.** At PLR 0.20, "
        "k=16 stays ~0.95; linear and hashing drop.",
        "- **A 512-bit burst on a 1024-bit code is a failure region for everyone.** Half the "
        "hypervector is flipped as one block; accuracy collapses to chance-level. A 128-bit burst "
        "does not move k=16.",
        "",
    ]
    path.write_text("\n".join(parts), encoding="utf-8")


def _plot_k16_radio(df: pd.DataFrame, fig: Path) -> None:
    id_ = df[df["split"] == "test_id"] if "split" in df.columns else df
    sub128 = id_[id_["budget_bytes"] == 128] if "budget_bytes" in id_.columns else id_
    for kind, title, fname in (
        ("bpsk_awgn", "k=16 vs BPSK-AWGN (128 B, test_id)", "accuracy_k16_radio_128_awgn.png"),
        (
            "bpsk_rayleigh_block",
            "k=16 vs BPSK block Rayleigh (128 B, test_id)",
            "accuracy_k16_radio_128_rayleigh.png",
        ),
        ("matched_ber", "k=16 vs matched i.i.d. BER (128 B, test_id)", "accuracy_k16_radio_128_matched.png"),
    ):
        sub = sub128[sub128["channel_kind"].astype(str) == kind] if "channel_kind" in sub128.columns else sub128
        if sub.empty:
            continue
        plot_metric_curves(
            sub,
            x="snr_db",
            y="accuracy",
            hue="method_label",
            title=title,
            path=fig / fname,
            xlabel="Eb/N0 (dB)",
            ylabel="Accuracy",
        )
    k16 = sub128[sub128["method_label"].astype(str) == "hdc_k16"]
    if not k16.empty and "channel_kind" in k16.columns:
        plot_metric_curves(
            k16,
            x="snr_db",
            y="accuracy",
            hue="channel_kind",
            title="k=16: radio structure vs matched BER (128 B, test_id)",
            path=fig / "accuracy_k16_radio_128_kinds.png",
            xlabel="Eb/N0 (dB)",
            ylabel="Accuracy",
        )


def _write_k16_radio(df: pd.DataFrame, path: Path) -> None:
    cols = [c for c in ["accuracy", "empirical_ber", "theory_ber"] if c in df.columns]
    g = (
        df.groupby(["split", "method_label", "budget_bytes", "channel_kind", "snr_db"], dropna=False)[cols]
        .mean()
        .reset_index()
        .round(4)
    )
    path.write_text(
        "\n".join(
            [
                "# Stage 8 remake — k=16 HDC on uncoded radio",
                "",
                "Eb/N0 is the physical-layer SNR. BPSK uses hard decisions. "
                "`matched_ber` flips bits i.i.d. at the closed-form uncoded BPSK-AWGN BER. "
                "Block Rayleigh (32-symbol coherence) clusters errors. "
                "128 B → `D=1024`; 512 B is the control. First-round `radio_sweep.jsonl` is unchanged.",
                "",
                "Means over seeds:",
                "",
                _md_table(g),
                "",
                "Figures: `results/figures/accuracy_k16_radio_128_awgn.png`, "
                "`results/figures/accuracy_k16_radio_128_rayleigh.png`, "
                "`results/figures/accuracy_k16_radio_128_matched.png`, "
                "`results/figures/accuracy_k16_radio_128_kinds.png`.",
                "",
                "## Reading",
                "",
                "- **i.i.d. BER did not overstate k=16 at 128 B.** BPSK-AWGN and `matched_ber` overlay. "
                "Block Rayleigh at Eb/N0 = −2 dB has empirical BER ~0.19 (worse than the BER=0.10 coin-flip) "
                "and k=16 stays ~0.95 in-distribution.",
                "- **The linear head is the one radio structure hurts.** At 128 B, Rayleigh −2 dB drops it "
                "below matched BER (clustered errors, not just the mean BER). Hashing degrades; PCM cliffs.",
                "- 32-symbol coherence on a 1024-bit code is ~32-bit clusters, closer to the 128-bit burst "
                "k=16 already survived than to the 512-bit half-code wipe.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _plot_k16_sector_encode(df: pd.DataFrame, fig: Path) -> None:
    id_ = df[df["split"] == "test_id"] if "split" in df.columns else df
    for kind, title, fname in (
        ("sector", "Sector dropout: skip / DROP vs max-range fill (512 B, test_id)", "accuracy_k16_sector_encode.png"),
        ("beam", "Random beam dropout after encoder fix (512 B, test_id)", "accuracy_k16_sector_encode_beam.png"),
    ):
        rows = []
        for _, r in id_.iterrows():
            rate = _sensor_rate(r.get("sensor", ""), kind)
            if rate is None:
                continue
            rows.append({**r.to_dict(), "drop_rate": rate})
        if not rows:
            continue
        plot_metric_curves(
            pd.DataFrame(rows),
            x="drop_rate",
            y="accuracy",
            hue="method_label",
            title=title,
            path=fig / fname,
            xlabel="Dropped fraction of beams",
            ylabel="Accuracy",
        )


def _write_k16_sector_encode(df: pd.DataFrame, path: Path) -> None:
    g = (
        df.groupby(["split", "method_label", "sensor"])[["accuracy", "macro_f1"]]
        .mean()
        .reset_index()
        .round(4)
    )
    path.write_text(
        "\n".join(
            [
                "# Sector-drop encoder fix — skip / DROP vs max-range fill",
                "",
                "k=16 at 512 B (`D=4096`). `fill` writes missing beams as max-range (a fake opening). "
                "`skip` omits non-finite beams from the bundle. `drop` binds a dedicated DROP item. "
                "First-round `k16_sensor.jsonl` is unchanged.",
                "",
                "Means over seeds:",
                "",
                _md_table(g),
                "",
                "Figures: `results/figures/accuracy_k16_sector_encode.png`, "
                "`results/figures/accuracy_k16_sector_encode_beam.png`.",
                "",
                "## Reading",
                "",
                "The question is whether telling the encoder that a hole is invalid "
                "(instead of open space) recovers sector-drop accuracy without hurting "
                "random beam dropout or the clean channel.",
                "",
                "- **Clean is unchanged.** Hashing is 0.922 ID / 0.623 OOD. k=16 fill, skip, and "
                "DROP are identical at 0.960 ID / 0.850 OOD — there are no non-finite beams, so "
                "the three encoders write the same HV.",
                "- **30% sector drop was the encoder, not the classifier.** ID: fill 0.387 "
                "(same as the first-round remake), skip 0.902, DROP 0.899, hashing 0.274. "
                "OOD: fill 0.437, skip 0.702, DROP 0.753.",
                "- **Random beam drop does not regress; skip/DROP improve it.** ID 30% beam drop: "
                "fill 0.803, skip 0.950, DROP 0.949. Fill still writes scattered holes as "
                "max-range, so those random gaps were a milder version of the same fake opening.",
                "- **DROP vs skip.** On this grid they are close on ID. DROP is a bit ahead on "
                "OOD holes (a bound DROP item stays in the bundle; skip shortens it). Neither "
                "is a universal win over the other. Hashing has no DROP item and stays the "
                "max-range-fill control.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _plot_k16_adapt_128(adapt: pd.DataFrame, path: Path) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    fig.patch.set_facecolor("#020617")
    ax.set_facecolor("#0b1220")
    for method, sub in adapt.groupby("method"):
        g = sub.groupby("shots_per_class")["new_acc"].agg(["mean", "std"]).reset_index()
        start = float(sub["before_new_acc"].mean())
        xs = [0, *g["shots_per_class"].tolist()]
        ys = [start, *g["mean"].tolist()]
        ax.plot(xs, ys, marker="o", label=str(method))
        ax.fill_between(
            g["shots_per_class"],
            g["mean"] - g["std"].fillna(0),
            g["mean"] + g["std"].fillna(0),
            alpha=0.15,
        )
    ax.set_title("OOD few-shot at 128 B (k=1 / k=16 / linear)", color="#e2e8f0")
    ax.set_xlabel("Shots per class", color="#94a3b8")
    ax.set_ylabel("OOD accuracy", color="#94a3b8")
    ax.tick_params(colors="#94a3b8")
    ax.legend(facecolor="#0f172a", edgecolor="#1e293b", labelcolor="#e2e8f0")
    for spine in ax.spines.values():
        spine.set_color("#1e293b")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def _write_k16_adapt_128(adapt: pd.DataFrame, path: Path) -> None:
    cols = [
        c
        for c in [
            "before_new_acc",
            "new_acc",
            "delta_new",
            "before_old_acc",
            "old_acc",
            "forgetting",
            "adapt_ms",
        ]
        if c in adapt.columns
    ]
    g = adapt.groupby(["method", "shots_per_class"])[cols].agg(["mean", "std"]).round(4).reset_index()
    path.write_text(
        "\n".join(
            [
                "# Few-shot OOD remake at 128 B",
                "",
                "Same protocol as `reports/stage4_multicentroid_adapt.md`, at the 128 B operating "
                "point (`D=1024`). `hdc_k1` / `hdc_k16` add (and subtract the current prediction "
                "from) the nearest class centroid. `hdc_linear` refits logistic regression on train "
                "hypervectors plus the labeled shots. First-round `adaptation.jsonl` and "
                "`multicentroid_adaptation.jsonl` are unchanged.",
                "",
                "Means over seeds:",
                "",
                _md_table(g),
                "",
                "Figure: `results/figures/accuracy_k16_adaptation_128b.png`.",
                "",
                "## Reading",
                "",
                "The question is Outcome C at 128 B: does a cheap centroid update still close the "
                "OOD gap relative to refitting a linear head, and does shrinking D from 4096 to "
                "1024 change the 512 B picture.",
                "",
                "- **k=16 still starts ahead on OOD.** Before shots: k=16 0.841, linear 0.794, "
                "k=1 0.699 — the same 128 B bandwidth remake.",
                "- **Centroid add remains cheap.** k=16: 9 / 42 / 80 ms at 10 / 50 / 100 shots. "
                "Linear refit on train HVs plus shots: ~4–5 s.",
                "- **Gains match 512 B; linear does not overtake.** k=16 +0.013 / +0.049 / +0.070 "
                "(→ 0.853 / 0.890 / 0.910). Linear +0.010 / +0.058 / +0.104 (→ 0.804 / 0.852 / 0.898). "
                "At 512 B the linear head passed k=16 at 100 shots; at 128 B it does not.",
                "- **k=1 is still not the operating point.** 0.699 → 0.751 at 100 shots.",
                "- **Forgetting stays small for k=16** (0.008 at 100 shots). Linear drops ID more "
                "(0.945 → 0.926).",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _plot_k16_semantic2d(df: pd.DataFrame, fig: Path) -> None:
    id_ = df[df["split"] == "test_id"] if "split" in df.columns else df
    if id_.empty:
        return
    plot_metric_curves(
        id_,
        x="ber",
        y="accuracy",
        hue="method_label",
        title="Semantic2D real LiDAR: accuracy vs BER (128 B, test_id)",
        path=fig / "accuracy_k16_semantic2d.png",
        xlabel="BER",
        ylabel="Accuracy",
    )
    ood = df[df["split"] == "test_ood"] if "split" in df.columns else df
    if ood.empty:
        return
    plot_metric_curves(
        ood,
        x="ber",
        y="accuracy",
        hue="method_label",
        title="Semantic2D real LiDAR: accuracy vs BER (128 B, test_ood)",
        path=fig / "accuracy_k16_semantic2d_ood.png",
        xlabel="BER",
        ylabel="Accuracy",
    )


def _write_k16_semantic2d(df: pd.DataFrame, path: Path) -> None:
    hue = "method_label" if "method_label" in df.columns else "method"

    def acc(split: str, tag: str, ber: float) -> float | None:
        sub = df[(df["split"] == split) & (df[hue] == tag) & (df["ber"] == ber)]
        if sub.empty:
            return None
        return float(sub["accuracy"].mean())

    def fmt(x: float | None) -> str:
        return "n/a" if x is None else f"{x:.3f}"

    g = (
        df.groupby(["split", hue, "ber"])[["accuracy", "macro_f1"]]
        .mean()
        .reset_index()
        .round(4)
    )
    id0 = {
        "k16": acc("test_id", "hdc_k16", 0.0),
        "k1": acc("test_id", "hdc_k1", 0.0),
        "lin": acc("test_id", "hdc_linear", 0.0),
        "hash": acc("test_id", "binary_hash", 0.0),
        "pcm": acc("test_id", "quantized", 0.0),
    }
    id10 = {
        "k16": acc("test_id", "hdc_k16", 0.10),
        "lin": acc("test_id", "hdc_linear", 0.10),
        "pcm": acc("test_id", "quantized", 0.10),
        "hash": acc("test_id", "binary_hash", 0.10),
    }
    ood0 = {
        "k16": acc("test_ood", "hdc_k16", 0.0),
        "hash": acc("test_ood", "binary_hash", 0.0),
        "lin": acc("test_ood", "hdc_linear", 0.0),
        "k1": acc("test_ood", "hdc_k1", 0.0),
        "pcm": acc("test_ood", "quantized", 0.0),
    }
    path.write_text(
        "\n".join(
            [
                "# Real 2D LiDAR — Semantic2D at 128 B k=16",
                "",
                "Scans are real 2D LiDAR from Semantic2D (Zenodo `10.5281/zenodo.13730200`). "
                "Place labels are **derived** from the range profile plus object labels "
                "(door / furniture), not author-annotated corridor/room tags. Invalid beams "
                "are NaN; HDC uses `skip`. First-round `sim_indoor_v1` JSONL is unchanged.",
                "",
                "8265 scans (stride 10), 180 beams, 270° FOV. OOD environments: lobby + eng_9th. "
                "Class mix is uneven (room 38%, doorway 32%, cluttered 20%, corridor 6%, open 4%).",
                "",
                "Means over seeds:",
                "",
                _md_table(g),
                "",
                "Figures: `results/figures/accuracy_k16_semantic2d.png`, "
                "`results/figures/accuracy_k16_semantic2d_ood.png`.",
                "",
                "## Reading",
                "",
                "The question is whether the 128 B k=16 operating region from `sim_indoor_v1` "
                "(~0.95 ID, BER-flat through 0.10) survives a real planar scan and a building holdout.",
                "",
                f"- **Clean ID:** k=16 {fmt(id0['k16'])}, linear {fmt(id0['lin'])}, hashing "
                f"{fmt(id0['hash'])}, k=1 {fmt(id0['k1'])}, 8-bit PCM {fmt(id0['pcm'])}. "
                "k=16 is the best of this set. Absolute accuracy is far below the simulator; "
                "the ~0.95 region does **not** transfer. It is still a lift over the test_id "
                "majority class (room, 35%).",
                f"- **BER = 0.10, ID:** k=16 {fmt(id10['k16'])} (flat), hashing {fmt(id10['hash'])}, "
                f"linear {fmt(id10['lin'])} (drops), PCM {fmt(id10['pcm'])} (cliffs). "
                "The holographic-vs-not pattern is the same as on sim, at a lower ceiling. "
                "Linear still failed to converge in 600 LBFGS steps.",
                f"- **Clean OOD (lobby + 9th floor):** k=16 {fmt(ood0['k16'])}, hashing "
                f"{fmt(ood0['hash'])}, linear {fmt(ood0['lin'])}, k=1 {fmt(ood0['k1'])}, "
                f"PCM {fmt(ood0['pcm'])}. This is a near-majority scramble (OOD room share 32%). "
                "Do not read it as the indoor-sim OOD gap transferring.",
                "",
                "Takeaway: k=16 remains the method that is both strongest on ID and BER-flat "
                "at 128 B, but real scans with derived place tags are a harder task and the "
                "building holdout is not solved. Hardware OTA is still blocked on this VM.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _plot_k16_lidardataframes(df: pd.DataFrame, fig: Path) -> None:
    id_ = df[df["split"] == "test_id"] if "split" in df.columns else df
    if id_.empty:
        return
    plot_metric_curves(
        id_,
        x="ber",
        y="accuracy",
        hue="method_label",
        title="LidarDataFrames author labels: accuracy vs BER (128 B, test_id)",
        path=fig / "accuracy_k16_lidardataframes.png",
        xlabel="BER",
        ylabel="Accuracy",
    )
    ood = df[df["split"] == "test_ood"] if "split" in df.columns else df
    if ood.empty:
        return
    plot_metric_curves(
        ood,
        x="ber",
        y="accuracy",
        hue="method_label",
        title="LidarDataFrames author labels: accuracy vs BER (128 B, i.i.d. holdout)",
        path=fig / "accuracy_k16_lidardataframes_ood.png",
        xlabel="BER",
        ylabel="Accuracy",
    )


def _write_k16_lidardataframes(df: pd.DataFrame, path: Path) -> None:
    hue = "method_label" if "method_label" in df.columns else "method"

    def acc(split: str, tag: str, ber: float) -> float | None:
        sub = df[(df["split"] == split) & (df[hue] == tag) & (df["ber"] == ber)]
        if sub.empty:
            return None
        return float(sub["accuracy"].mean())

    def fmt(x: float | None) -> str:
        return "n/a" if x is None else f"{x:.3f}"

    g = (
        df.groupby(["split", hue, "ber"])[["accuracy", "macro_f1"]]
        .mean()
        .reset_index()
        .round(4)
    )
    id0 = {
        "k16": acc("test_id", "hdc_k16", 0.0),
        "k1": acc("test_id", "hdc_k1", 0.0),
        "lin": acc("test_id", "hdc_linear", 0.0),
        "hash": acc("test_id", "binary_hash", 0.0),
        "pcm": acc("test_id", "quantized", 0.0),
    }
    id10 = {
        "k16": acc("test_id", "hdc_k16", 0.10),
        "lin": acc("test_id", "hdc_linear", 0.10),
        "pcm": acc("test_id", "quantized", 0.10),
        "hash": acc("test_id", "binary_hash", 0.10),
    }
    path.write_text(
        "\n".join(
            [
                "# Real 2D LiDAR — LidarDataFrames at 128 B k=16 (author place labels)",
                "",
                "Scans are RPLiDAR A1 frames from Kaggle LidarDataFrames. Place labels are "
                "**author-assigned** room / corridor / doorway / hall (hall → `open_area`). "
                "411 frames, four classes, no `cluttered_area`. This is the labeled real-scan "
                "check that Semantic2D could not provide.",
                "",
                "The CSV has no building id. `test_ood` is a stratified i.i.d. holdout, **not** "
                "a floorplan shift. N is small (~80 test frames). First-round sim and Semantic2D "
                "JSONL are unchanged.",
                "",
                "Means over seeds:",
                "",
                _md_table(g),
                "",
                "Figures: `results/figures/accuracy_k16_lidardataframes.png`, "
                "`results/figures/accuracy_k16_lidardataframes_ood.png`.",
                "",
                "## Reading",
                "",
                "The question is whether 128 B k=16 still has an operating region when the "
                "place tags are author labels rather than derived heuristics.",
                "",
                f"- **Clean test_id:** k=16 {fmt(id0['k16'])}, linear {fmt(id0['lin'])}, "
                f"hashing {fmt(id0['hash'])}, k=1 {fmt(id0['k1'])}, PCM {fmt(id0['pcm'])}.",
                f"- **BER = 0.10, test_id:** k=16 {fmt(id10['k16'])}, hashing {fmt(id10['hash'])}, "
                f"linear {fmt(id10['lin'])}, PCM {fmt(id10['pcm'])}.",
                "",
                "On this small, balanced, author-labeled set the clean-channel ceiling is back "
                "near the simulator (~0.97). k=16 and linear both sit there and stay BER-flat; "
                "PCM still cliffs. That supports the Semantic2D reading: ~0.50 there was the "
                "derived labels, not 'real LiDAR cannot be classified at 128 B'.",
                "",
                "Caveats: 411 frames, four classes, i.i.d. holdout, authors already imputed "
                "missing returns. This is not a building-shift OOD test and not Semantic2D scale.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _plot_k16_lidardataframes_sensor(df: pd.DataFrame, fig: Path) -> None:
    id_ = df[df["split"] == "test_id"] if "split" in df.columns else df
    for kind, title, fname in (
        (
            "beam",
            "LidarDataFrames: beam dropout vs accuracy (128 B, test_id, BER = 0)",
            "accuracy_k16_lidardataframes_beam_drop.png",
        ),
        (
            "sector",
            "LidarDataFrames: sector dropout vs accuracy (128 B, test_id, BER = 0)",
            "accuracy_k16_lidardataframes_sector_drop.png",
        ),
    ):
        rows = []
        for _, r in id_.iterrows():
            rate = _sensor_rate(r.get("sensor", ""), kind)
            if rate is None:
                continue
            rows.append({**r.to_dict(), "drop_rate": rate})
        if not rows:
            continue
        plot_metric_curves(
            pd.DataFrame(rows),
            x="drop_rate",
            y="accuracy",
            hue="method_label",
            title=title,
            path=fig / fname,
            xlabel="Dropped fraction of beams",
            ylabel="Accuracy",
        )


def _write_k16_lidardataframes_sensor(df: pd.DataFrame, path: Path) -> None:
    hue = "method_label" if "method_label" in df.columns else "method"

    def acc(split: str, tag: str, sensor: str) -> float | None:
        sub = df[(df["split"] == split) & (df[hue] == tag) & (df["sensor"] == sensor)]
        if sub.empty:
            return None
        return float(sub["accuracy"].mean())

    def fmt(x: float | None) -> str:
        return "n/a" if x is None else f"{x:.3f}"

    g = (
        df.groupby(["split", hue, "sensor"])[["accuracy", "macro_f1"]]
        .mean()
        .reset_index()
        .round(4)
    )
    path.write_text(
        "\n".join(
            [
                "# Stage 3 remake — LidarDataFrames sensor dropout at 128 B",
                "",
                "Author-labeled RPLiDAR frames. Corruptions hit the scan **before** encoding "
                "(BER = 0). Budget 128 bytes, `D=1024`. k=16 skip / DROP / fill vs k=1 skip, "
                "linear skip, hashing, and 8-bit PCM. Sim `k16_sensor.jsonl` and "
                "`k16_sector_encode.jsonl` are unchanged.",
                "",
                "`test_ood` is an i.i.d. holdout, not a floorplan shift. Dropout and range "
                "scale do not need a building id; Stage 4 few-shot-after-shift is still "
                "blocked on this corpus (holdout N≈80 cannot run 50/100 shots per class).",
                "",
                "Means over seeds:",
                "",
                _md_table(g),
                "",
                "Figures: `results/figures/accuracy_k16_lidardataframes_beam_drop.png`, "
                "`results/figures/accuracy_k16_lidardataframes_sector_drop.png`.",
                "",
                "## Reading",
                "",
                "The question is whether the sim Stage 3 operating region (random beam drop "
                "holds; 30% sector drop with max-range fill fails; skip/DROP recover) still "
                "shows up on author-labeled real scans at the 128 B working point.",
                "",
                f"- **Clean test_id:** k=16 skip {fmt(acc('test_id', 'hdc_k16/skip', 'clean'))}, "
                f"fill {fmt(acc('test_id', 'hdc_k16/fill', 'clean'))}, "
                f"linear {fmt(acc('test_id', 'hdc_linear/skip', 'clean'))}, "
                f"hashing {fmt(acc('test_id', 'binary_hash', 'clean'))}, "
                f"PCM {fmt(acc('test_id', 'quantized', 'clean'))}.",
                f"- **30% random beam drop, test_id:** k=16 skip "
                f"{fmt(acc('test_id', 'hdc_k16/skip', 'beam_drop:drop_rate=0.3'))}, "
                f"fill {fmt(acc('test_id', 'hdc_k16/fill', 'beam_drop:drop_rate=0.3'))}, "
                f"linear {fmt(acc('test_id', 'hdc_linear/skip', 'beam_drop:drop_rate=0.3'))}, "
                f"hashing {fmt(acc('test_id', 'binary_hash', 'beam_drop:drop_rate=0.3'))}, "
                f"PCM {fmt(acc('test_id', 'quantized', 'beam_drop:drop_rate=0.3'))}.",
                f"- **30% sector drop, test_id:** k=16 skip "
                f"{fmt(acc('test_id', 'hdc_k16/skip', 'sector_drop:fraction=0.3'))}, "
                f"DROP {fmt(acc('test_id', 'hdc_k16/drop', 'sector_drop:fraction=0.3'))}, "
                f"fill {fmt(acc('test_id', 'hdc_k16/fill', 'sector_drop:fraction=0.3'))}, "
                f"linear {fmt(acc('test_id', 'hdc_linear/skip', 'sector_drop:fraction=0.3'))}, "
                f"hashing {fmt(acc('test_id', 'binary_hash', 'sector_drop:fraction=0.3'))}.",
                f"- **Range scale 1.15 / clip 6 m, test_id k=16 skip:** "
                f"{fmt(acc('test_id', 'hdc_k16/skip', 'range_scale:scale=1.15'))} / "
                f"{fmt(acc('test_id', 'hdc_k16/skip', 'clip:clip_to=6.0'))}.",
                "",
                "N is small (~80 test frames). Treat the ranking and the skip-vs-fill gap as "
                "the result, not the exact percentages.",
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
    mc_adapt: pd.DataFrame | None = None,
    k16_bw: pd.DataFrame | None = None,
    k16_sensor: pd.DataFrame | None = None,
    k16_noise: pd.DataFrame | None = None,
    k16_radio: pd.DataFrame | None = None,
    k16_sector_encode: pd.DataFrame | None = None,
    k16_adapt_128: pd.DataFrame | None = None,
    k16_semantic2d: pd.DataFrame | None = None,
    k16_lidardataframes: pd.DataFrame | None = None,
    k16_ldf_sensor: pd.DataFrame | None = None,
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
        "See `reports/stage1_bandwidth.md` for the first-round matrix (single prototype). "
        "On this 180-beam scan, 8-bit PCM saturates at ~188 bytes. A **single** HDC prototype "
        "is not a compression win (Outcome A fails for k=1). The k=16 remake is "
        "`reports/stage1_k16_bandwidth.md`.",
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
        "Sensor corruptions (pre-encoder) and OOD floorplan: `reports/stage3_shift.md` (k=1) and `reports/stage3_k16_sensor.md` (k=16 remake).",
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
    if mc_adapt is not None and not mc_adapt.empty:
        lines += [
            "## Few-shot multi-centroid adaptation",
            "",
            "See `reports/stage4_multicentroid_adapt.md`. OOD shots update the nearest centroid (or refit the linear head).",
            "",
        ]
        ga = (
            mc_adapt.groupby(["method", "shots_per_class"])[["new_acc", "old_acc", "forgetting", "adapt_ms"]]
            .mean()
            .reset_index()
            .round(4)
        )
        lines += [_md_table(ga)]
    if k16_bw is not None and not k16_bw.empty:
        lines += [
            "## k=16 bandwidth remake",
            "",
            "See `reports/stage1_k16_bandwidth.md`. Same payload family as Stage 1, with k=16 centroids, linear head, hashing, and 8-bit PCM. Dimension fills the budget.",
            "",
        ]
        gb = (
            k16_bw.groupby(["split", "method_label" if "method_label" in k16_bw.columns else "method", "budget_bytes"])[
                "accuracy"
            ]
            .mean()
            .reset_index()
            .round(4)
        )
        lines += [_md_table(gb)]
    if k16_sensor is not None and not k16_sensor.empty:
        lines += [
            "## k=16 sensor dropout remake",
            "",
            "See `reports/stage3_k16_sensor.md`. Beam and sector dropout before encoding, 512 bytes.",
            "",
        ]
        hue = "method_label" if "method_label" in k16_sensor.columns else "method"
        gs = (
            k16_sensor.groupby(["split", hue, "sensor"])["accuracy"]
            .mean()
            .reset_index()
            .round(4)
        )
        drop = gs[gs["sensor"].astype(str).str.contains("beam_drop|sector_drop|clean", regex=True)]
        lines += [_md_table(drop if not drop.empty else gs)]
    if k16_noise is not None and not k16_noise.empty:
        lines += [
            "## k=16 communication-noise remake",
            "",
            "See `reports/stage2_k16_noise.md`. BER at 128 B and 512 B; burst and packet loss at 128 B.",
            "",
        ]
        hue = "method_label" if "method_label" in k16_noise.columns else "method"
        ber = _k16_ber_rows(k16_noise)
        gb = (
            ber.groupby(["split", hue, "budget_bytes", "ber"])["accuracy"]
            .mean()
            .reset_index()
            .round(4)
        )
        lines += [_md_table(gb)]
    if k16_radio is not None and not k16_radio.empty:
        lines += [
            "## k=16 uncoded-radio remake",
            "",
            "See `reports/stage8_k16_radio.md`. BPSK-AWGN, block Rayleigh, and matched BER at 128 B and 512 B.",
            "",
        ]
        hue = "method_label" if "method_label" in k16_radio.columns else "method"
        gr = (
            k16_radio.groupby(["split", hue, "budget_bytes", "channel_kind", "snr_db"])["accuracy"]
            .mean()
            .reset_index()
            .round(4)
        )
        lines += [_md_table(gr)]
    if k16_sector_encode is not None and not k16_sector_encode.empty:
        lines += [
            "## Sector-drop encoder fix",
            "",
            "See `reports/stage3_k16_sector_encode.md`. Skip / DROP-bind invalid beams vs max-range fill.",
            "",
        ]
        hue = "method_label" if "method_label" in k16_sector_encode.columns else "method"
        gs = (
            k16_sector_encode.groupby(["split", hue, "sensor"])["accuracy"]
            .mean()
            .reset_index()
            .round(4)
        )
        lines += [_md_table(gs)]
    if k16_adapt_128 is not None and not k16_adapt_128.empty:
        lines += [
            "## k=16 few-shot remake at 128 B",
            "",
            "See `reports/stage4_k16_adaptation_128b.md`. 10/50/100-shot OOD at the 128 B operating point.",
            "",
        ]
        ga = (
            k16_adapt_128.groupby(["method", "shots_per_class"])[
                ["new_acc", "old_acc", "forgetting", "adapt_ms"]
            ]
            .mean()
            .reset_index()
            .round(4)
        )
        lines += [_md_table(ga)]
    if k16_semantic2d is not None and not k16_semantic2d.empty:
        lines += [
            "## Real 2D LiDAR (Semantic2D)",
            "",
            "See `reports/stage0_semantic2d.md`. 128 B remake on real scans with derived place labels.",
            "",
        ]
        hue = "method_label" if "method_label" in k16_semantic2d.columns else "method"
        gs = (
            k16_semantic2d.groupby(["split", hue, "ber"])["accuracy"]
            .mean()
            .reset_index()
            .round(4)
        )
        lines += [_md_table(gs)]
    if k16_lidardataframes is not None and not k16_lidardataframes.empty:
        lines += [
            "## Real 2D LiDAR (LidarDataFrames, author labels)",
            "",
            "See `reports/stage0_lidardataframes.md`. 128 B remake on 411 author-labeled scans. "
            "`test_ood` is i.i.d., not a building shift.",
            "",
        ]
        hue = "method_label" if "method_label" in k16_lidardataframes.columns else "method"
        gs = (
            k16_lidardataframes.groupby(["split", hue, "ber"])["accuracy"]
            .mean()
            .reset_index()
            .round(4)
        )
        lines += [_md_table(gs)]
    if k16_ldf_sensor is not None and not k16_ldf_sensor.empty:
        lines += [
            "## Stage 3 on LidarDataFrames (author labels)",
            "",
            "See `reports/stage3_k16_lidardataframes_sensor.md`. Beam / sector dropout, "
            "range scale, and clip at 128 B. Skip / DROP vs max-range fill. "
            "`test_ood` is i.i.d., not a building shift.",
            "",
        ]
        hue = "method_label" if "method_label" in k16_ldf_sensor.columns else "method"
        gs = (
            k16_ldf_sensor.groupby(["split", hue, "sensor"])["accuracy"]
            .mean()
            .reset_index()
            .round(4)
        )
        drop = gs[gs["sensor"].astype(str).str.contains("beam_drop|sector_drop|clean", regex=True)]
        lines += [_md_table(drop if not drop.empty else gs)]
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
        "| Clean 2D scan | k=1 prototype loses to hashing; k=16 / linear close that gap. See k=16 bandwidth remake. |",
        "| Random BER | k=16 stays flat at 128 B (~0.95). Linear head is not holographic at that budget. PCM cliffs. |",
        "| Burst / packet loss | k=16 holds 128-bit bursts and 20% packet loss at 128 B; a 512-bit burst (half the code) is a failure region |",
        "| Uncoded radio | k=16 stays flat at 128 B under BPSK-AWGN and block Rayleigh; matched BER tracks AWGN. Linear is hurt by clustered fades. |",
        "| Sensor dropout / scale | k=16 holds random beam drop. 30% sector drop with max-range fill is a fake opening (~0.39 ID). Skip/DROP recover ~0.90 ID / ~0.70–0.75 OOD. |",
        "| Real 2D LiDAR | Semantic2D derived labels ID ~0.50. LidarDataFrames author labels (411 frames): k=16 / linear ~0.97, PCM cliffs. Not a building OOD. |",
        "| Real LiDAR sensor dropout | LidarDataFrames 128 B: 30% beam drop k=16 skip ~0.90 vs fill ~0.79; 30% sector skip ~0.84 / DROP ~0.90 / fill ~0.67. PCM and hashing collapse. Not a building OOD. |",
        "| Hybrid encoder | Prototype head ~0.73–0.80; linear head on HDC codes can match/beat hashing |",
        "| Multi-centroid | k>1 lifts prototype accuracy while staying BER-flat; see OOD vs linear in the table |",
        "",
        "Configs in `configs/`. Frozen splits in `data/splits/sim_indoor_v1/`, `semantic2d_v1/`, and `lidardataframes_v1/`.",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
