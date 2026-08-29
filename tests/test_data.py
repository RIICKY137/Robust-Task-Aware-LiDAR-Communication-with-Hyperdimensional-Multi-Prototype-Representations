from __future__ import annotations

from hdc_lidar.data.simulator import generate_dataset, make_office_building
from hdc_lidar import LABELS
import numpy as np


def test_simulator_has_all_classes_and_disjoint_traj_splits():
    packed = generate_dataset(n_beams=90, max_range=8.0, seed=1, range_noise=0.0, n_traj_per_env=2)
    arr = packed["arrays"]
    assert set(int(x) for x in np.unique(arr["labels"])) == set(range(len(LABELS)))
    train_traj = set(arr["traj_ids"][arr["splits"] == "train"].tolist())
    id_traj = set(arr["traj_ids"][arr["splits"] == "test_id"].tolist())
    ood_env = set(arr["env_ids"][arr["splits"] == "test_ood"].tolist())
    assert train_traj.isdisjoint(id_traj)
    assert ood_env == {"env_ood"}


def test_building_variants_differ():
    rng = np.random.default_rng(0)
    a = make_office_building("a", rng, "a")
    b = make_office_building("b", rng, "ood")
    assert a.regions[0].x1 != b.regions[0].x1
    assert all(r.name in LABELS for r in a.regions)
