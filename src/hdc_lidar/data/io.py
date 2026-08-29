from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from hdc_lidar.types import ScanBatch
from hdc_lidar.utils.gitinfo import repo_root


def processed_dir(name: str = "sim_indoor_v1") -> Path:
    path = repo_root() / "data" / "processed" / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def splits_dir(name: str = "sim_indoor_v1") -> Path:
    path = repo_root() / "data" / "splits" / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_dataset(arrays: dict, name: str = "sim_indoor_v1") -> Path:
    out = processed_dir(name) / "scans.npz"
    np.savez_compressed(out, **arrays)
    split_root = splits_dir(name)
    splits = arrays["splits"]
    ids = arrays["sample_ids"]
    mapping = {}
    for split in ("train", "test_id", "test_ood"):
        chosen = ids[splits == split].tolist()
        mapping[split] = chosen
        (split_root / f"{split}.json").write_text(json.dumps(chosen, indent=2), encoding="utf-8")
    meta = {
        "dataset": name,
        "n_beams": int(arrays["n_beams"]),
        "max_range": float(arrays["max_range"]),
        "n_samples": int(len(ids)),
        "label_names": arrays["label_names"].tolist(),
        "seed": int(arrays["seed"]),
        "split_counts": {k: len(v) for k, v in mapping.items()},
    }
    (split_root / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return out


def load_dataset(name: str = "sim_indoor_v1") -> tuple[ScanBatch, dict[str, np.ndarray], dict]:
    arrays = np.load(processed_dir(name) / "scans.npz", allow_pickle=True)
    batch = ScanBatch(
        ranges=arrays["ranges"],
        labels=arrays["labels"],
        env_ids=arrays["env_ids"],
        traj_ids=arrays["traj_ids"],
        sample_ids=arrays["sample_ids"],
        poses=arrays["poses"],
        max_range=float(arrays["max_range"]),
        n_beams=int(arrays["n_beams"]),
    )
    split_idx = {}
    splits = arrays["splits"]
    for split in ("train", "test_id", "test_ood"):
        split_idx[split] = np.where(splits == split)[0]
    meta = json.loads((splits_dir(name) / "meta.json").read_text(encoding="utf-8"))
    return batch, split_idx, meta
