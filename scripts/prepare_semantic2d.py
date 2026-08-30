#!/usr/bin/env python3
"""Stage 0 for Semantic2D: unpack, derive place labels, freeze splits."""

from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hdc_lidar import LABELS  # noqa: E402
from hdc_lidar.data.io import load_dataset, save_dataset  # noqa: E402
from hdc_lidar.data.semantic2d import FOV_DEG, build_arrays, discover_sequences  # noqa: E402
from hdc_lidar.data.io import processed_dir  # noqa: E402
from hdc_lidar.features.viz import save_sample_grid  # noqa: E402

RAW = ROOT / "data" / "raw" / "semantic2d"
NAME = "semantic2d_v1"
ARCHIVE_CANDIDATES = [
    RAW / "semantic2d.tar.gz",
    RAW / "semantic2d_data.zip",
]


def _extract(archive: Path, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    marker = dest / ".extracted"
    if marker.exists() and discover_sequences(dest):
        return dest
    print("extracting", archive, "(scans / labels / poses only)")
    if archive.suffixes[-2:] == [".tar", ".gz"] or archive.suffix == ".tgz":
        subprocess.check_call(
            [
                "tar",
                "-xzf",
                str(archive),
                "-C",
                str(dest),
                "--wildcards",
                "semantic2d/*/scans_lidar/*.npy",
                "semantic2d/*/semantic_label/*.npy",
                "semantic2d/*/positions/*.npy",
            ]
        )
    elif archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(dest)
    else:
        raise ValueError(f"unknown archive {archive}")
    marker.write_text(str(archive.name), encoding="utf-8")
    return dest


def class_table(labels: np.ndarray) -> dict[str, int]:
    c = Counter(int(x) for x in labels)
    return {LABELS[i]: int(c.get(i, 0)) for i in range(len(LABELS))}


def write_report(batch, splits: dict, meta: dict, path: Path) -> None:
    total = len(batch)
    lines = [
        "# Data report — Semantic2D place labels (derived)",
        "",
        "Dataset: `semantic2d_v1` from Xie et al. Semantic2D (Zenodo "
        "`10.5281/zenodo.13730200`). Scans are real 2D LiDAR. Place tags are "
        "**derived** from the range profile plus point-wise object labels "
        "(door / furniture / opening), not author-annotated corridor/room tags.",
        "",
        "Invalid / no-return beams (Hokuyo sentinel ≈ 60 m, non-finite, or ≤ 5 cm) "
        "are stored as NaN, not max-range fill. Finite ranges are clipped to 20 m for the encoder. "
        "Beams are resampled to 180 over the native 270° field of view. Stride 10 keeps the "
        "set comparable in size to `sim_indoor_v1`.",
        "",
        "## Split protocol",
        "",
        "- `test_ood`: held-out environments (building shift).",
        "- `test_id`: last 20% of each remaining sequence (time order, not a random frame shuffle).",
        "- `train`: the rest of those sequences.",
        "",
        f"Held-out environments: `{meta.get('ood_envs')}`",
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
    archive = next((p for p in ARCHIVE_CANDIDATES if p.exists()), None)
    if archive is None:
        raise SystemExit(
            "Missing Semantic2D archive. Download "
            "https://zenodo.org/records/13730200/files/semantic2d.tar.gz?download=1 "
            f"to {RAW}/semantic2d.tar.gz"
        )
    unpacked = _extract(archive, RAW / "unpacked")
    seqs = discover_sequences(unpacked)
    print("sequences", [(e, str(p)) for e, p in seqs])
    arrays = build_arrays(unpacked, stride=10, seed=7)
    save_dataset(arrays, NAME)
    # persist ood env list on meta
    meta_path = ROOT / "data" / "splits" / NAME / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["ood_envs"] = arrays["ood_envs"].tolist()
    meta["label_source"] = "derived_from_range_and_semantic2d_objects"
    meta["source"] = "zenodo:10.5281/zenodo.13730200"
    meta["fov_deg"] = float(FOV_DEG)
    meta["stride"] = int(arrays["stride"])
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    batch, splits, meta = load_dataset(NAME)
    fig_dir = ROOT / "results" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    save_sample_grid(
        batch,
        fig_dir / "sample_scans_semantic2d.png",
        n_per_class=2,
        seed=0,
        fov_deg=float(FOV_DEG),
    )
    write_report(batch, splits, meta, ROOT / "reports" / "data_report_semantic2d.md")
    print(f"saved {len(batch)} scans -> {processed_dir(NAME)}")
    print("splits", {k: len(v) for k, v in splits.items()})
    print("classes", class_table(batch.labels))
    print("ood_envs", meta.get("ood_envs"))


if __name__ == "__main__":
    main()
