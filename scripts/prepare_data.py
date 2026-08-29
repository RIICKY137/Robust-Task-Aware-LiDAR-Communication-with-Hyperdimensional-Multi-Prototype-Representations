#!/usr/bin/env python3
"""Stage 0: generate simulated indoor LiDAR, freeze splits, write data_report.md."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hdc_lidar import LABELS  # noqa: E402
from hdc_lidar.data.io import load_dataset, save_dataset  # noqa: E402
from hdc_lidar.data.simulator import generate_dataset  # noqa: E402
from hdc_lidar.features.viz import save_sample_grid  # noqa: E402
from hdc_lidar.types import ScanBatch  # noqa: E402


def class_table(labels: np.ndarray) -> dict[str, int]:
    c = Counter(int(x) for x in labels)
    return {LABELS[i]: int(c.get(i, 0)) for i in range(len(LABELS))}


def write_report(batch: ScanBatch, splits: dict, meta: dict, path: Path) -> None:
    lines = [
        "# Data report (Stage 0)",
        "",
        "Dataset: `sim_indoor_v1` — controllable 2D indoor LiDAR simulator used until a labeled public scan+place corpus is wired in.",
        "",
        "## Label definition",
        "",
        "Place labels are assigned from the robot pose against floorplan regions, not from adjacent-frame clustering:",
        "",
        "- `corridor` — narrow hall centerline",
        "- `room` — enclosed rectangular rooms",
        "- `doorway` — door opening volumes (sampled extra to reduce imbalance)",
        "- `open_area` — lobby / atrium",
        "- `cluttered_area` — storage with box obstacles",
        "",
        "## Sensor model",
        "",
        f"- Beams: **{batch.n_beams}** over 360°",
        f"- Max range: **{batch.max_range:.1f} m**",
        "- Additive Gaussian range noise σ = 1.5 cm at generation time",
        "- Invalid/no-hit returns are clipped to max range",
        "",
        "## Split protocol",
        "",
        "- **train**: trajectories 0..T-2 in `env_a` and `env_b`",
        "- **test_id**: held-out trajectory in the same buildings (no random frame shuffle)",
        "- **test_ood**: entire `env_ood` floorplan (different proportions, denser clutter)",
        "",
        "Adjacent time frames from one trajectory never appear in both train and test_id.",
        "",
        "## Counts",
        "",
        f"- Total scans: {len(batch)}",
        f"- Train: {len(splits['train'])}",
        f"- In-distribution test: {len(splits['test_id'])}",
        f"- Shifted / OOD test: {len(splits['test_ood'])}",
        "",
        "### Class balance (all data)",
        "",
        "| class | n | share |",
        "|---|---:|---:|",
    ]
    total = len(batch)
    for name, n in class_table(batch.labels).items():
        lines.append(f"| {name} | {n} | {n / total:.1%} |")
    lines += ["", "### Class balance by split", ""]
    for split, idx in splits.items():
        lines.append(f"**{split}**")
        lines.append("")
        lines.append("| class | n |")
        lines.append("|---|---:|")
        for name, n in class_table(batch.labels[idx]).items():
            lines.append(f"| {name} | {n} |")
        lines.append("")
    lines += [
        "## Leakage checks",
        "",
        "- Split files are frozen under `data/splits/sim_indoor_v1/*.json`.",
        "- `sample_id` is unique; trajectory IDs in train and test_id are disjoint.",
        "",
        f"Meta: `{json.dumps(meta)}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    packed = generate_dataset(n_beams=180, max_range=10.0, seed=7, n_traj_per_env=3)
    save_dataset(packed["arrays"], "sim_indoor_v1")
    batch, splits, meta = load_dataset("sim_indoor_v1")
    fig_dir = ROOT / "results" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    save_sample_grid(batch, fig_dir / "sample_scans.png", n_per_class=2, seed=0)
    write_report(batch, splits, meta, ROOT / "reports" / "data_report.md")
    print(f"saved {len(batch)} scans")
    print("splits", {k: len(v) for k, v in splits.items()})
    print("classes", class_table(batch.labels))


if __name__ == "__main__":
    main()
