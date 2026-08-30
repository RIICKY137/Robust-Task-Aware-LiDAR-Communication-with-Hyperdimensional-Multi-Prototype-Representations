from __future__ import annotations

from pathlib import Path

import numpy as np

from hdc_lidar import LABEL_TO_ID
from hdc_lidar.data.semantic2d import derive_place, resample_scan, sanitize_ranges


def test_resample_scan_length():
    x = np.arange(1081, dtype=np.float32)
    y = resample_scan(x, 180)
    assert y.shape == (180,)
    assert np.isclose(y[0], 0.0)
    assert np.isclose(y[-1], 1080.0, atol=1.0)


def test_sanitize_marks_invalid_as_nan():
    x = np.array([1.0, 0.0, np.inf, 3.0, 99.0, 25.0, 60.0], dtype=np.float32)
    y = sanitize_ranges(x, max_range=20.0)
    assert np.isfinite(y[0])
    assert np.isnan(y[1])
    assert np.isnan(y[2])
    assert np.isfinite(y[3])
    assert np.isnan(y[4])
    assert np.isclose(y[5], 20.0)  # far but real return, clipped not NaN
    assert np.isnan(y[6])  # sensor no-return sentinel


def test_derive_place_corridor_doorway_open():
    n = 180
    corridor = np.full(n, 8.0, dtype=np.float32)
    corridor[:60] = 1.2
    corridor[120:] = 1.2
    assert derive_place(corridor, None) == LABEL_TO_ID["corridor"]

    doorway = corridor.copy()
    sem = np.zeros(n, dtype=np.int32)
    sem[70:95] = 2  # door
    doorway[70:95] = 2.0
    assert derive_place(doorway, sem) == LABEL_TO_ID["doorway"]

    opened = np.full(n, 18.0, dtype=np.float32)
    assert derive_place(opened, None) == LABEL_TO_ID["open_area"]

    room = np.full(n, 4.5, dtype=np.float32)
    assert derive_place(room, None) == LABEL_TO_ID["room"]

    cluttered = np.full(n, 3.2, dtype=np.float32)
    furn = np.zeros(n, dtype=np.int32)
    furn[20:50] = 1  # chairs nearby
    assert derive_place(cluttered, furn) == LABEL_TO_ID["cluttered_area"]


def test_build_arrays_from_fake_sequence(tmp_path: Path):
    from hdc_lidar.data.semantic2d import build_arrays

    env_a = tmp_path / "office_a" / "scans_lidar"
    env_b = tmp_path / "office_b" / "scans_lidar"
    env_c = tmp_path / "lobby" / "scans_lidar"
    for folder, dist in ((env_a, 4.5), (env_b, 4.8), (env_c, 18.0)):
        folder.mkdir(parents=True)
        sem_dir = folder.parent / "semantic_label"
        sem_dir.mkdir()
        for i in range(12):
            scan = np.full(1081, dist, dtype=np.float32)
            if dist < 10:
                scan[:360] = 1.3
                scan[-360:] = 1.3
            np.save(folder / f"{i:04d}.npy", scan)
            np.save(sem_dir / f"{i:04d}.npy", np.zeros(1081, dtype=np.int32))
    arrays = build_arrays(tmp_path, stride=1, seed=7, ood_envs=["lobby"])
    assert arrays["ranges"].shape[1] == 180
    assert set(arrays["splits"].tolist()) == {"train", "test_id", "test_ood"}
    assert (arrays["env_ids"][arrays["splits"] == "test_ood"] == "lobby").all()
    train_traj = set(arrays["traj_ids"][arrays["splits"] == "train"].tolist())
    id_traj = set(arrays["traj_ids"][arrays["splits"] == "test_id"].tolist())
    # ID holdout is later frames of the same sequences, so traj ids overlap; envs must not include lobby.
    assert "lobby" not in train_traj
    assert "lobby" not in id_traj


def test_seq_env_names_from_zenodo_folders(tmp_path: Path):
    from hdc_lidar.data.semantic2d import SEQ_ENV, discover_sequences

    scans = tmp_path / "2024-04-11-15-24-29" / "scans_lidar"
    scans.mkdir(parents=True)
    (scans / "0001.npy").write_bytes(b"")
    found = discover_sequences(tmp_path)
    assert found[0][0] == SEQ_ENV["2024-04-11-15-24-29"] == "corridor"
