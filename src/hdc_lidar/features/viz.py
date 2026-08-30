"""Scan visualization helpers."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from hdc_lidar import ID_TO_LABEL, LABELS
from hdc_lidar.types import ScanBatch


CLASS_COLORS = {
    "corridor": "#d4a017",
    "room": "#3b82f6",
    "doorway": "#ef4444",
    "open_area": "#22c55e",
    "cluttered_area": "#a855f7",
}


def polar_xy(
    ranges: np.ndarray,
    angle_min: float = 0.0,
    angle_max: float = 2 * np.pi,
    fov_deg: float | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    n = ranges.shape[-1]
    if fov_deg is not None:
        half = np.deg2rad(float(fov_deg) / 2.0)
        angle_min, angle_max = -half, half
        endpoint = float(fov_deg) < 359.0
    else:
        endpoint = False
    ang = np.linspace(angle_min, angle_max, n, endpoint=endpoint)
    r = np.asarray(ranges, dtype=np.float64)
    x = r * np.cos(ang)
    y = r * np.sin(ang)
    return x, y


def plot_scan(ax, ranges: np.ndarray, title: str, color: str = "#38bdf8", fov_deg: float | None = None) -> None:
    x, y = polar_xy(ranges, fov_deg=fov_deg)
    ax.scatter(x, y, s=8, c=color, alpha=0.85, linewidths=0)
    ax.scatter([0], [0], c="#f8fafc", s=28, zorder=3, marker="^")
    ax.set_aspect("equal")
    ax.set_title(title, color="#e2e8f0", fontsize=10)
    ax.set_facecolor("#0b1220")
    ax.tick_params(colors="#64748b")
    for spine in ax.spines.values():
        spine.set_color("#1e293b")
    ax.set_xlabel("x (m)", color="#94a3b8")
    ax.set_ylabel("y (m)", color="#94a3b8")


def save_sample_grid(
    batch: ScanBatch,
    path: Path,
    n_per_class: int = 2,
    seed: int = 0,
    fov_deg: float | None = None,
) -> None:
    rng = np.random.default_rng(seed)
    fig, axes = plt.subplots(len(LABELS), n_per_class, figsize=(4 * n_per_class, 3.2 * len(LABELS)))
    fig.patch.set_facecolor("#020617")
    for r, name in enumerate(LABELS):
        idx = np.where(batch.labels == r)[0]
        if len(idx) == 0:
            for c in range(n_per_class):
                ax = axes[r, c] if n_per_class > 1 else axes[r]
                ax.set_axis_off()
            continue
        pick = rng.choice(idx, size=min(n_per_class, len(idx)), replace=False)
        for c, j in enumerate(pick):
            ax = axes[r, c] if n_per_class > 1 else axes[r]
            plot_scan(
                ax,
                batch.ranges[j],
                f"{name} · {batch.sample_ids[j]}",
                CLASS_COLORS[name],
                fov_deg=fov_deg,
            )
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140, facecolor=fig.get_facecolor())
    plt.close(fig)


def plot_metric_curves(df, x: str, y: str, hue: str, title: str, path: Path, xlabel: str, ylabel: str) -> None:
    import pandas as pd

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    fig.patch.set_facecolor("#020617")
    ax.set_facecolor("#0b1220")
    for method, sub in df.groupby(hue):
        g = sub.groupby(x)[y].agg(["mean", "std"]).reset_index()
        ax.plot(g[x], g["mean"], marker="o", label=str(method))
        ax.fill_between(g[x], g["mean"] - g["std"].fillna(0), g["mean"] + g["std"].fillna(0), alpha=0.15)
    ax.set_title(title, color="#e2e8f0")
    ax.set_xlabel(xlabel, color="#94a3b8")
    ax.set_ylabel(ylabel, color="#94a3b8")
    ax.tick_params(colors="#94a3b8")
    ax.legend(facecolor="#0f172a", edgecolor="#1e293b", labelcolor="#e2e8f0")
    for spine in ax.spines.values():
        spine.set_color("#1e293b")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
