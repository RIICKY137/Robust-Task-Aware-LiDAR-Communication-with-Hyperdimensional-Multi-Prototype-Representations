"""Streamlit lab for dataset inspection, live classification, and result curves."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from hdc_lidar import ID_TO_LABEL, LABELS
from hdc_lidar.channels import apply_channel
from hdc_lidar.data.io import load_dataset
from hdc_lidar.evaluation.metrics import task_metrics
from hdc_lidar.features.viz import CLASS_COLORS, polar_xy
from hdc_lidar.methods import build_method
from hdc_lidar.types import ChannelConfig
from hdc_lidar.utils.gitinfo import repo_root


def _load_results() -> pd.DataFrame:
    raw = repo_root() / "results" / "raw"
    rows = []
    if raw.exists():
        for p in sorted(raw.glob("*.jsonl")):
            for line in p.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rows.append(json.loads(line))
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def _dataset():
    return load_dataset("sim_indoor_v1")


@st.cache_resource(show_spinner="Fitting encoder and classifier…")
def _fit_method(
    name: str,
    budget: int,
    seed: int,
    dimension: int,
    hdc_head: str = "prototype",
    hybrid_frontend: str = "sector",
    hybrid_head: str = "prototype",
    hybrid_mix: str = "none",
    hybrid_mode: str = "task",
    n_centroids: int = 1,
):
    batch, splits, _ = _dataset()
    train = batch.subset(splits["train"])
    kwargs: dict = {}
    if name in {"pure_hdc", "binary_hash", "hybrid_hdc"}:
        kwargs["dimension"] = dimension
    if name == "pure_hdc":
        kwargs["head"] = hdc_head
        kwargs["n_centroids"] = n_centroids
    if name == "hybrid_hdc":
        kwargs["mode"] = hybrid_mode
        kwargs["frontend"] = hybrid_frontend
        kwargs["head"] = hybrid_head
        kwargs["mix"] = hybrid_mix
    method = build_method(name, budget, seed=seed, **kwargs)
    method.fit(train.ranges, train.labels, train.max_range)
    return method


def main() -> None:
    st.set_page_config(
        page_title="HDC Task-Aware LiDAR Communication",
        page_icon="📡",
        layout="wide",
    )
    st.markdown(
        """
        <style>
        .stApp { background: #020617; color: #e2e8f0; }
        h1, h2, h3 { letter-spacing: -0.02em; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("HDC Task-Aware LiDAR Communication")
    st.caption(
        "Bandwidth-constrained, noisy robotic LiDAR · environment classification without point-cloud reconstruction"
    )

    try:
        batch, splits, meta = _dataset()
    except FileNotFoundError:
        st.error("No processed dataset yet. Run `python scripts/prepare_data.py` first.")
        return

    page = st.sidebar.radio("Lab", ["Overview", "Scan viewer", "Live channel", "Results"])
    if page == "Overview":
        _overview(batch, splits, meta)
    elif page == "Scan viewer":
        _viewer(batch, splits)
    elif page == "Live channel":
        _live(batch, splits)
    else:
        _results()


def _overview(batch, splits, meta) -> None:
    st.subheader("Stage 0 dataset")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Scans", f"{len(batch):,}")
    c2.metric("Beams / scan", str(batch.n_beams))
    c3.metric("Max range", f"{batch.max_range:.1f} m")
    c4.metric("Classes", str(len(LABELS)))
    st.write(
        "Labels are geometric place categories on simulated indoor trajectories. "
        "Splits are by trajectory and building: `test_id` holds out a path in known buildings; "
        "`test_ood` is a held-out floorplan (`env_ood`)."
    )
    rows = []
    for split, idx in splits.items():
        labs = batch.labels[idx]
        row = {"split": split, "n": int(len(idx))}
        for i, name in enumerate(LABELS):
            row[name] = int(np.sum(labs == i))
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
    st.markdown(
        """
**Research questions this lab is built to answer**

1. Same byte budget, higher task accuracy?
2. Smoother accuracy drop under BER / burst / packet loss?
3. Cheaper few-shot prototype updates after environment shift?
        """
    )


def _viewer(batch, splits) -> None:
    split = st.selectbox("Split", list(splits.keys()))
    label = st.selectbox("Class", LABELS)
    idx = splits[split]
    mask = batch.labels[idx] == LABELS.index(label)
    local = idx[mask]
    if len(local) == 0:
        st.warning("No scans for that class in this split.")
        return
    k = st.slider("Sample", 0, int(len(local) - 1), 0)
    j = int(local[k])
    ranges = batch.ranges[j]
    x, y = polar_xy(ranges)
    import plotly.graph_objects as go

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="markers",
            marker=dict(size=5, color=CLASS_COLORS[label]),
            name="returns",
        )
    )
    fig.add_trace(
        go.Scatter(x=[0], y=[0], mode="markers", marker=dict(size=12, symbol="triangle-up", color="white"), name="robot")
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#020617",
        plot_bgcolor="#0b1220",
        height=520,
        title=f"{batch.sample_ids[j]} · {batch.env_ids[j]} · {batch.traj_ids[j]}",
        xaxis=dict(title="x (m)", scaleanchor="y", scaleratio=1),
        yaxis=dict(title="y (m)"),
        margin=dict(l=40, r=20, t=50, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.write(
        {
            "label": label,
            "pose_xy_yaw": [float(v) for v in batch.poses[j]],
            "min_range": float(ranges.min()),
            "mean_range": float(ranges.mean()),
        }
    )


def _live(batch, splits) -> None:
    st.subheader("Transmit representation → noisy channel → classify")
    c1, c2, c3 = st.columns(3)
    method_name = c1.selectbox(
        "Method",
        ["quantized", "pca", "binary_hash", "pure_hdc", "autoencoder", "hybrid_hdc"],
        index=3,
    )
    budget = c2.selectbox("Budget (bytes/sample)", [128, 512, 2048], index=1)
    ber = c3.select_slider("BER", options=[0.0, 0.001, 0.005, 0.01, 0.02, 0.05, 0.10, 0.20], value=0.01)
    plr = st.select_slider("Packet loss", options=[0.0, 0.01, 0.05, 0.10, 0.20, 0.40], value=0.0)
    burst = st.select_slider("Burst length (bits)", options=[0, 32, 128, 512, 1024], value=0)
    interleave = st.checkbox("Bit interleave (shared permutation)", value=False)
    radio_mod = st.selectbox("Radio modulation", ["none", "bpsk", "qpsk"], index=0)
    snr_db = st.select_slider("Eb/N0 (dB)", options=[12.0, 8.0, 6.0, 4.0, 2.0, 0.0, -2.0], value=6.0)
    fading = st.selectbox("Fading", ["none", "rayleigh_iid", "rayleigh_block"], index=0)
    if radio_mod != "none":
        st.caption("Radio replaces the BER coin-flip. Burst and packet loss still apply after demodulation.")
    dim = st.select_slider("HDC / hash dimension cap", options=[1024, 4096, 8192], value=4096)
    hdc_head = "prototype"
    n_centroids = 1
    hybrid_frontend, hybrid_head, hybrid_mix, hybrid_mode = "sector", "prototype", "none", "task"
    if method_name == "pure_hdc":
        hdc_head = st.selectbox("HDC head", ["prototype", "linear"], index=0)
        if hdc_head == "prototype":
            n_centroids = int(st.select_slider("Centroids per class", options=[1, 4, 8, 16], value=1))
    if method_name == "hybrid_hdc":
        hybrid_mode = st.selectbox("Hybrid train", ["task", "frozen"], index=0)
        hybrid_frontend = st.selectbox("LiDAR frontend", ["scan", "sector"], index=0)
        hybrid_head = st.selectbox("Hybrid head", ["prototype", "linear"], index=0)
        hybrid_mix = st.selectbox("Mix record HDC", ["record", "none"], index=0)
    split = st.selectbox("Evaluate on", ["test_id", "test_ood", "train"], index=0)
    seed = 7
    method = _fit_method(
        method_name,
        int(budget),
        seed,
        int(dim),
        hdc_head,
        hybrid_frontend,
        hybrid_head,
        hybrid_mix,
        hybrid_mode,
        n_centroids,
    )

    idx = splits[split]
    k = st.slider("Scan index in split", 0, int(len(idx) - 1), 0)
    j = int(idx[k])
    rec = method.encode_one(batch.ranges[j])
    if radio_mod != "none":
        channel = ChannelConfig(
            modulation=radio_mod,
            snr_db=float(snr_db),
            fading=fading,
            burst_length=int(burst),
            n_bursts=0 if burst == 0 else 1,
            packet_loss_rate=float(plr),
            interleave=bool(interleave),
            seed=seed,
        )
    else:
        channel = ChannelConfig(
            ber=float(ber),
            burst_length=int(burst),
            n_bursts=0 if burst == 0 else 1,
            packet_loss_rate=float(plr),
            interleave=bool(interleave),
            seed=seed,
        )
    noisy = apply_channel(rec.payload, channel, np.random.default_rng(seed + k))
    pred = method.predict_from_payloads([noisy], batch.n_beams, batch.max_range)[0]
    true = int(batch.labels[j])
    left, right = st.columns(2)
    left.metric("True place", ID_TO_LABEL[true])
    right.metric("Predicted after channel", ID_TO_LABEL[int(pred)], delta="match" if pred == true else "miss")
    st.write(
        {
            "payload_bytes": round(rec.total_bytes, 2),
            "payload_bits": rec.total_bits,
            "budget_bytes": budget,
            "shared_item_memory_bytes": method.shared_memory_bytes(),
            "classifier_bytes": method.model_bytes(),
        }
    )

    if st.button("Score entire split under this channel", type="primary"):
        test = batch.subset(idx)
        records = method.encode_batch(test.ranges)
        rng = np.random.default_rng(seed)
        payloads = [apply_channel(r.payload, channel, rng) for r in records]
        yhat = method.predict_from_payloads(payloads, test.n_beams, test.max_range)
        m = task_metrics(test.labels, yhat)
        st.metric("Accuracy", f"{m['accuracy']:.3f}")
        st.metric("Macro-F1", f"{m['macro_f1']:.3f}")
        st.dataframe(pd.DataFrame(m["per_class"]).T, use_container_width=True)
        st.text(m["report"])


def _results() -> None:
    df = _load_results()
    if df.empty:
        st.info("No `results/raw/*.jsonl` yet. Run the Stage 1–3 sweep scripts.")
        return
    st.subheader("Logged experiments")
    st.dataframe(df, use_container_width=True, height=280)
    import plotly.express as px

    def _chart(data, x, y, color, title):
        if data.empty or x not in data.columns:
            return
        g = data.groupby([color, x], as_index=False)[y].mean()
        fig = px.line(g, x=x, y=y, color=color, markers=True, title=title, template="plotly_dark")
        fig.update_layout(paper_bgcolor="#020617", plot_bgcolor="#0b1220")
        st.plotly_chart(fig, use_container_width=True)

    clean = df.copy()
    for col, default in (("ber", 0.0), ("burst_length", 0), ("packet_loss_rate", 0.0)):
        if col not in clean.columns:
            clean[col] = default
        clean[col] = pd.to_numeric(clean[col], errors="coerce").fillna(default)
    if "method_tag" in clean.columns:
        clean["curve"] = clean["method_tag"].where(clean["method_tag"].notna(), clean["method"])
    else:
        clean["curve"] = clean["method"]

    bw = clean[(clean["ber"] == 0) & (clean["burst_length"] == 0) & (clean["packet_loss_rate"] == 0)]
    if "sensor" in bw.columns:
        bw = bw[bw["sensor"].isna() | (bw["sensor"] == "clean") | (bw["sensor"] == "")]
    if "budget_bytes" in bw.columns:
        _chart(bw, "budget_bytes", "accuracy", "curve", "Accuracy vs communication budget (clean channel)")
    if "sensor" in clean.columns:
        drop = clean[clean["sensor"].fillna("").astype(str).str.startswith("beam_drop")]
        if not drop.empty:
            _chart(drop, "sensor", "accuracy", "curve", "Accuracy vs beam dropout (sensor, BER = 0)")
        sector = clean[clean["sensor"].fillna("").astype(str).str.startswith("sector_drop")]
        if not sector.empty:
            _chart(sector, "sensor", "accuracy", "curve", "Accuracy vs sector dropout (sensor, BER = 0)")
    noise = clean[(clean["burst_length"] == 0) & (clean["packet_loss_rate"] == 0)].copy()
    burst = clean[(clean["ber"] == 0) & (clean["packet_loss_rate"] == 0)].copy()
    plr = clean[(clean["ber"] == 0) & (clean["burst_length"] == 0)].copy()
    if "budget_bytes" in noise.columns:
        for frame in (noise, burst, plr):
            frame["curve_b"] = (
                frame["curve"].astype(str)
                + " / "
                + pd.to_numeric(frame["budget_bytes"], errors="coerce").fillna(0).astype(int).astype(str)
                + "B"
            )
        _chart(noise, "ber", "accuracy", "curve_b", "Accuracy vs bit error rate")
        _chart(burst, "burst_length", "accuracy", "curve_b", "Accuracy vs burst length")
        _chart(plr, "packet_loss_rate", "accuracy", "curve_b", "Accuracy vs packet loss")
    else:
        _chart(noise, "ber", "accuracy", "curve", "Accuracy vs bit error rate")
        _chart(burst, "burst_length", "accuracy", "curve", "Accuracy vs burst length")
        _chart(plr, "packet_loss_rate", "accuracy", "curve", "Accuracy vs packet loss")
    if "snr_db" in clean.columns:
        radio = clean[pd.to_numeric(clean["snr_db"], errors="coerce").notna()].copy()
        if "sweep" in radio.columns and (radio["sweep"] == "k16_radio").any():
            radio = radio[radio["sweep"] == "k16_radio"]
        if not radio.empty:
            kind = (
                radio["channel_kind"].astype(str)
                if "channel_kind" in radio.columns
                else "radio"
            )
            radio["curve_r"] = radio["curve"].astype(str) + " / " + kind
            if "budget_bytes" in radio.columns:
                radio["curve_r"] = (
                    radio["curve_r"]
                    + " / "
                    + pd.to_numeric(radio["budget_bytes"], errors="coerce")
                    .fillna(0)
                    .astype(int)
                    .astype(str)
                    + "B"
                )
            _chart(radio, "snr_db", "accuracy", "curve_r", "Accuracy vs Eb/N0 (radio)")


if __name__ == "__main__":
    main()
