#!/usr/bin/env python3
"""Stage 0 for LidarDataFrames: author place labels, freeze stratified splits."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hdc_lidar import LABELS  # noqa: E402
from hdc_lidar.data.io import load_dataset, processed_dir, save_dataset  # noqa: E402
from hdc_lidar.data.lidardataframes import FOV_DEG, build_arrays  # noqa: E402
from hdc_lidar.features.viz import save_sample_grid  # noqa: E402

RAW = ROOT / "data" / "raw" / "lidardataframes"
NAME = "lidardataframes_v1"
CSV_CANDIDATES = [
    RAW / "FourClassDS.csv",
    RAW / "lidardataframes.csv",
]


def class_table(labels: np.ndarray) -> dict[str, int]:
    c = Counter(int(x) for x in labels)
    return {LABELS[i]: int(c.get(i, 0)) for i in range(len(LABELS))}


def write_report(batch, splits: dict, meta: dict, path: Path) -> None:
    total = len(batch)
    lines = [
        "# Data report — LidarDataFrames (author place labels)",
        "",
        "Dataset: `lidardataframes_v1` from [LidarDataFrames](https://www.kaggle.com/datasets/tareqalhmiedat/lidardataframes) "
        "(RPLiDAR A1). Place tags are **author-labeled** environment types, not derived heuristics.",
        "",
        "Four classes in the CSV: room, corridor, doorway, hall. Hall is mapped to `open_area`. "
        "`cluttered_area` is unused. Ranges are millimetres, converted to metres, resampled 360→180 beams, "
        "clipped at 12 m (A1 max). ≤5 cm → NaN.",
        "",
        "## Split protocol",
        "",
        "The CSV has **no building or trajectory id**. Splits are stratified 60/20/20 by class "
        "(seed 7). `test_ood` is a second i.i.d. holdout, **not** a floorplan shift. "
        "Do not read it as Semantic2D-style building OOD.",
        "",
        f"Total scans: {total}",
        "",
        "## Class balance",
        "",
        "| class | n | share |",
        "|---|---:|---:|",
    ]
    for name, n in class_table(batch.labels).items():
        lines.append(f"| {name} | {n} | {n / max(total, 1):.1%} |")
    lines += ["", "### By split", ""]
    for split, idx in splits.items():
        lines.append(f"**{split}** n={len(idx)}")
        lines.append("")
        lines.append("| class | n |")
        lines.append("|---|---:|")
        for name, n in class_table(batch.labels[idx]).items():
            lines.append(f"| {name} | {n} |")
        lines.append("")
    lines += [f"Meta: `{json.dumps(meta)}`", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    csv_path = next((p for p in CSV_CANDIDATES if p.exists()), None)
    if csv_path is None:
        raise SystemExit(
            "Missing FourClassDS.csv. Place it at "
            f"{RAW}/FourClassDS.csv (from the Kaggle LidarDataFrames archive)."
        )
    arrays = build_arrays(csv_path, seed=7)
    save_dataset(arrays, NAME)
    meta_path = ROOT / "data" / "splits" / NAME / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["label_source"] = "author_lidardataframes_place_tags"
    meta["source"] = "kaggle:tareqalhmiedat/lidardataframes"
    meta["fov_deg"] = float(FOV_DEG)
    meta["n_classes_present"] = 4
    meta["split_note"] = "stratified_60_20_20_iid_test_ood_is_not_building_shift"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    batch, splits, meta = load_dataset(NAME)
    fig_dir = ROOT / "results" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    save_sample_grid(
        batch,
        fig_dir / "sample_scans_lidardataframes.png",
        n_per_class=2,
        seed=0,
        fov_deg=float(FOV_DEG),
    )
    write_report(batch, splits, meta, ROOT / "reports" / "data_report_lidardataframes.md")
    print(f"saved {len(batch)} scans -> {processed_dir(NAME)}")
    print("splits", {k: len(v) for k, v in splits.items()})
    print("classes", class_table(batch.labels))


if __name__ == "__main__":
    main()
