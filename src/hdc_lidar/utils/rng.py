from __future__ import annotations

import numpy as np


def rng(seed: int | None = None) -> np.random.Generator:
    return np.random.default_rng(seed)


def seed_everything(seed: int) -> np.random.Generator:
    import random

    random.seed(seed)
    np.random.seed(seed)
    return rng(seed)
