from __future__ import annotations

import numpy as np

from hdc_lidar.channels import apply_bit_flip, apply_burst_error, apply_channel, apply_packet_loss
from hdc_lidar.types import ChannelConfig
from hdc_lidar.utils.bits import measured_ber, pack_bipolar, unpack_bipolar


def test_pack_roundtrip():
    rng = np.random.default_rng(0)
    hv = np.where(rng.integers(0, 2, size=128) == 1, 1, -1).astype(np.int8)
    blob = pack_bipolar(hv)
    rec = unpack_bipolar(blob, 128)
    np.testing.assert_array_equal(hv, rec)
    assert len(blob) * 8 == 128


def test_bit_flip_rate_matches_ber():
    rng = np.random.default_rng(1)
    payload = bytes(rng.integers(0, 256, size=2000, dtype=np.uint8).tolist())
    ber = 0.05
    noisy = apply_bit_flip(payload, ber, rng)
    emp = measured_ber(payload, noisy)
    assert abs(emp - ber) < 0.01


def test_packet_loss_zeros_fraction():
    rng = np.random.default_rng(2)
    payload = bytes([1]) * 320  # 10 packets of 32
    out = apply_packet_loss(payload, packet_bytes=32, plr=1.0, rng=rng, fill=0)
    assert out == bytes(320)


def test_burst_flips_contiguous_bits():
    rng = np.random.default_rng(3)
    payload = bytes([0]) * 16
    out = apply_burst_error(payload, burst_length=16, n_bursts=1, rng=rng, mode="flip")
    assert out != payload


def test_interleave_scatters_a_burst():
    rng = np.random.default_rng(4)
    payload = bytes([0]) * 64
    cfg = ChannelConfig(burst_length=64, n_bursts=1, interleave=True, seed=0)
    out = apply_channel(payload, cfg, rng)
    bits = np.unpackbits(np.frombuffer(out, dtype=np.uint8), bitorder="big")
    # After deinterleave a contiguous burst should not remain one solid block of ones.
    runs = np.diff(np.where(np.concatenate([[0], bits, [0]]))[0])
    longest = int(runs.max()) if runs.size else 0
    assert bits.sum() > 0
    assert longest < 64
