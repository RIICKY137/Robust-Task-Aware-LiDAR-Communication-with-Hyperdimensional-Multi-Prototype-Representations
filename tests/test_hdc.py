from __future__ import annotations

import numpy as np
import pytest

from hdc_lidar.hdc_ops import bind, bundle, encode_scans, hamming_distance, locality_preserving_levels, random_hv


def test_bind_is_xor_for_bipolar():
    rng = np.random.default_rng(0)
    a = random_hv(1, 256, rng)[0]
    b = random_hv(1, 256, rng)[0]
    c = bind(a, b)
    assert c.dtype == np.int8
    np.testing.assert_array_equal(bind(c, b), a)


def test_bundle_recovers_repeated_vector():
    rng = np.random.default_rng(1)
    v = random_hv(1, 128, rng)
    stacked = np.repeat(v, 7, axis=0)
    out = bundle(stacked, binarize=True)
    np.testing.assert_array_equal(out, v[0])


def test_locality_preserving_levels_are_ordered():
    rng = np.random.default_rng(2)
    levels = locality_preserving_levels(16, 512, rng, flips_per_step=16)
    d_adj = hamming_distance(levels[0], levels[1])
    d_far = hamming_distance(levels[0], levels[-1])
    assert d_adj < d_far


def test_encode_scans_is_deterministic():
    rng = np.random.default_rng(3)
    pos = random_hv(10, 64, rng)
    lev = random_hv(8, 64, rng)
    ranges = np.full((4, 10), 3.0)
    a = encode_scans(ranges, pos, lev, max_range=10.0, n_levels=8)
    b = encode_scans(ranges, pos, lev, max_range=10.0, n_levels=8)
    np.testing.assert_array_equal(a, b)
    assert a.shape == (4, 64)
    assert set(np.unique(a)).issubset({-1, 1})


def test_encode_skip_omits_invalid_beams():
    rng = np.random.default_rng(4)
    pos = random_hv(8, 64, rng)
    lev = random_hv(8, 64, rng)
    ranges = np.full((3, 8), 3.0)
    full = encode_scans(ranges, pos, lev, max_range=10.0, n_levels=8, binarize_out=False)
    nan_ranges = ranges.copy()
    nan_ranges[:, 5:] = np.nan
    skipped = encode_scans(
        nan_ranges, pos, lev, max_range=10.0, n_levels=8, binarize_out=False, invalid_mode="skip"
    )
    prefix = encode_scans(ranges[:, :5], pos[:5], lev, max_range=10.0, n_levels=8, binarize_out=False)
    np.testing.assert_array_equal(skipped, prefix)
    filled = encode_scans(nan_ranges, pos, lev, max_range=10.0, n_levels=8, binarize_out=False, invalid_mode="fill")
    assert not np.array_equal(filled, skipped)
    assert not np.array_equal(filled, full)


def test_encode_drop_uses_drop_item():
    rng = np.random.default_rng(5)
    pos = random_hv(6, 32, rng)
    lev = random_hv(4, 32, rng)
    drop = random_hv(1, 32, rng)[0]
    ranges = np.full((2, 6), 2.0)
    ranges[:, :3] = np.nan
    out = encode_scans(
        ranges, pos, lev, max_range=8.0, n_levels=4, binarize_out=False, invalid_mode="drop", drop_hv=drop
    )
    skipped = encode_scans(
        ranges, pos, lev, max_range=8.0, n_levels=4, binarize_out=False, invalid_mode="skip"
    )
    assert not np.array_equal(out, skipped)
    with pytest.raises(ValueError, match="drop_hv"):
        encode_scans(ranges, pos, lev, max_range=8.0, n_levels=4, invalid_mode="drop")
