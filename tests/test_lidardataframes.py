from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from hdc_lidar import LABEL_TO_ID
from hdc_lidar.data.lidardataframes import build_arrays, map_csv_label, sanitize_mm, stratified_split


def test_map_csv_label():
    assert map_csv_label(0) == LABEL_TO_ID["room"]
    assert map_csv_label(1) == LABEL_TO_ID["corridor"]
    assert map_csv_label(2) == LABEL_TO_ID["doorway"]
    assert map_csv_label(3) == LABEL_TO_ID["open_area"]


def test_sanitize_mm_converts_and_clips():
    x = np.array([872.0, 0.0, 25000.0], dtype=np.float32)
    y = sanitize_mm(x, max_range=12.0)
    assert np.isclose(y[0], 0.872, atol=1e-3)
    assert np.isnan(y[1])
    assert np.isclose(y[2], 12.0)


def test_stratified_split_keeps_all_classes(tmp_path: Path):
    labels = np.array([0] * 10 + [1] * 10 + [2] * 10 + [3] * 10)
    splits = stratified_split(labels, seed=7)
    assert set(splits.tolist()) == {"train", "test_id", "test_ood"}
    for part in ("train", "test_id", "test_ood"):
        present = set(labels[splits == part].tolist())
        assert present == {0, 1, 2, 3}


def test_build_arrays_from_tiny_csv(tmp_path: Path):
    rows = []
    csv_id = {"room": 0, "corridor": 1, "doorway": 2, "hall": 3}
    for name, cid in csv_id.items():
        for i in range(8):
            dist = 900 if name == "corridor" else 4000
            row = {str(b): float(dist + (b % 7)) for b in range(360)}
            if name == "corridor":
                for b in list(range(0, 60)) + list(range(300, 360)):
                    row[str(b)] = 1200.0
            row["id"] = cid
            rows.append(row)
    path = tmp_path / "FourClassDS.csv"
    pd.DataFrame(rows).to_csv(path, index=True)
    arrays = build_arrays(path, seed=7)
    assert arrays["ranges"].shape == (32, 180)
    assert set(arrays["labels"].tolist()) == {
        LABEL_TO_ID["room"],
        LABEL_TO_ID["corridor"],
        LABEL_TO_ID["doorway"],
        LABEL_TO_ID["open_area"],
    }
    assert LABEL_TO_ID["cluttered_area"] not in set(arrays["labels"].tolist())
    assert set(arrays["splits"].tolist()) == {"train", "test_id", "test_ood"}
