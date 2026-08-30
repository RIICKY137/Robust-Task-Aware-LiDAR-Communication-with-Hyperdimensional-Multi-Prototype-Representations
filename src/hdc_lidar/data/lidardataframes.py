"""Import LidarDataFrames (Kaggle) — author-labeled 2D place classes.

CSV `id` column (dataset card): room=0, corridor=1, doorway=2, hall=3.
Hall maps to `open_area`. There is no cluttered_area class. Ranges are millimetres
from an RPLiDAR A1 (360 beams). The CSV has no building or trajectory ids, so
test_ood is a second stratified holdout, not a floorplan shift.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from hdc_lidar import LABEL_TO_ID, LABELS
from hdc_lidar.data.semantic2d import resample_scan

N_BEAMS_OUT = 180
MAX_RANGE = 12.0
FOV_DEG = 360.0

# Dataset card labels → this repo's place ids.
CSV_ID_TO_NAME = {
    0: "room",
    1: "corridor",
    2: "doorway",
    3: "open_area",  # hall
}


def _beam_columns(df: pd.DataFrame) -> list[str]:
    cols = []
    for i in range(360):
        name = str(i)
        if name not in df.columns:
            raise ValueError(f"missing beam column {name}")
        cols.append(name)
    return cols


def sanitize_mm(ranges_mm: np.ndarray, max_range: float = MAX_RANGE) -> np.ndarray:
    x = np.asarray(ranges_mm, dtype=np.float32) / 1000.0
    bad = ~np.isfinite(x) | (x <= 0.05)
    x = x.copy()
    x[bad] = np.nan
    finite = np.isfinite(x)
    x[finite] = np.minimum(x[finite], np.float32(max_range))
    return x


def map_csv_label(csv_id: int) -> int:
    name = CSV_ID_TO_NAME.get(int(csv_id))
    if name is None:
        raise ValueError(f"unknown LidarDataFrames id {csv_id}")
    return LABEL_TO_ID[name]


def stratified_split(labels: np.ndarray, seed: int = 7) -> np.ndarray:
    """60/20/20 by class. test_ood is i.i.d., not a building holdout."""
    rng = np.random.default_rng(seed)
    out = np.empty(len(labels), dtype=object)
    for c in np.unique(labels):
        idx = np.where(labels == c)[0]
        rng.shuffle(idx)
        n = len(idx)
        n_train = int(round(n * 0.60))
        n_id = int(round(n * 0.20))
        n_train = min(n_train, n - 2) if n >= 3 else max(n - 2, 0)
        n_id = min(n_id, n - n_train - 1) if n - n_train >= 2 else max(n - n_train - 1, 0)
        out[idx[:n_train]] = "train"
        out[idx[n_train : n_train + n_id]] = "test_id"
        out[idx[n_train + n_id :]] = "test_ood"
    return out


def build_arrays(csv_path: Path, seed: int = 7) -> dict:
    df = pd.read_csv(csv_path)
    if "id" not in df.columns:
        raise ValueError("FourClassDS.csv must have an 'id' label column")
    beams = df[_beam_columns(df)].to_numpy(dtype=np.float32)
    csv_ids = df["id"].to_numpy(dtype=np.int32)
    labels = np.asarray([map_csv_label(i) for i in csv_ids], dtype=np.int32)
    ranges = np.stack([resample_scan(sanitize_mm(row)) for row in beams]).astype(np.float32)
    splits = stratified_split(labels, seed=seed)
    n = len(labels)
    sample_ids = np.asarray([f"ldf_{i:04d}" for i in range(n)], dtype=object)
    return {
        "ranges": ranges,
        "labels": labels,
        "env_ids": np.asarray(["lidardataframes"] * n, dtype=object),
        "traj_ids": np.asarray(["lidardataframes"] * n, dtype=object),
        "sample_ids": sample_ids,
        "poses": np.zeros((n, 3), dtype=np.float32),
        "splits": splits,
        "n_beams": np.int32(N_BEAMS_OUT),
        "max_range": np.float32(MAX_RANGE),
        "fov_deg": np.float32(FOV_DEG),
        "label_names": np.asarray(LABELS),
        "seed": np.int32(seed),
        "csv_ids": csv_ids,
    }
