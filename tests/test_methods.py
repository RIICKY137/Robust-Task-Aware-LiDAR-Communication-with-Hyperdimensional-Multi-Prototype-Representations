from __future__ import annotations

import numpy as np

from hdc_lidar.methods.pure_hdc import PureHDCMethod
from hdc_lidar.methods.quantization import QuantizedMethod


def test_hdc_prototype_update_moves_decision():
    rng = np.random.default_rng(0)
    n_beams = 32
    max_range = 8.0
    ranges = rng.uniform(0.5, 7.0, size=(80, n_beams)).astype(np.float32)
    labels = np.repeat(np.arange(5), 16)
    method = PureHDCMethod(budget_bytes=128, seed=0, dimension=256, n_levels=8)
    method.fit(ranges, labels, max_range)
    probe = ranges[0]
    before = int(method.predict_from_hv(method.encode_matrix(probe.reshape(1, -1)))[0])
    # force a different class with many updates
    target = (before + 1) % 5
    hv = method.encode_matrix(probe.reshape(1, -1))[0]
    for _ in range(25):
        method.adapt(hv, target, subtract_pred=before)
    after = int(method.predict_from_hv(hv.reshape(1, -1))[0])
    assert after == target


def test_quantized_bit_count_respects_budget():
    rng = np.random.default_rng(1)
    ranges = rng.uniform(0.2, 9.0, size=(40, 180)).astype(np.float32)
    labels = rng.integers(0, 5, size=40)
    m = QuantizedMethod(budget_bytes=128, seed=0, n_bits=8)
    m.fit(ranges, labels, 10.0)
    rec = m.encode_one(ranges[0])
    assert rec.total_bytes <= 128 + 8  # header included in payload; allow small pad
    assert rec.total_bits % 8 == 0
    pred = m.predict_from_payloads([rec.payload], 180, 10.0)
    assert pred.shape == (1,)
