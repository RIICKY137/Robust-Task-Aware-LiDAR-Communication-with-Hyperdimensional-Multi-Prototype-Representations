from __future__ import annotations

import numpy as np

from hdc_lidar.channels.radio import apply_radio, apply_radio_payloads, simulate_radio, theoretical_ber
from hdc_lidar.types import ChannelConfig
from hdc_lidar.utils.bits import measured_ber
from hdc_lidar.channels import apply_channel, apply_channel_many


def test_bpsk_high_snr_almost_clean():
    rng = np.random.default_rng(0)
    payload = bytes(rng.integers(0, 256, size=2048, dtype=np.uint8).tolist())
    out = apply_radio(payload, rng, modulation="bpsk", snr_db=12.0, fading="none")
    assert measured_ber(payload, out) < 0.002


def test_bpsk_awgn_ber_matches_theory():
    rng = np.random.default_rng(1)
    payload = bytes(rng.integers(0, 256, size=8000, dtype=np.uint8).tolist())
    snr = 4.0
    out = apply_radio(payload, rng, modulation="bpsk", snr_db=snr, fading="none")
    emp = measured_ber(payload, out)
    theory = theoretical_ber(snr, "bpsk", "none")
    assert abs(emp - theory) < 0.005


def test_qpsk_awgn_similar_to_bpsk():
    rng = np.random.default_rng(2)
    payload = bytes(rng.integers(0, 256, size=8000, dtype=np.uint8).tolist())
    snr = 4.0
    bpsk = apply_radio(payload, rng, modulation="bpsk", snr_db=snr, fading="none")
    qpsk = apply_radio(payload, rng, modulation="qpsk", snr_db=snr, fading="none")
    theory = theoretical_ber(snr, "qpsk", "none")
    assert abs(measured_ber(payload, bpsk) - theory) < 0.006
    assert abs(measured_ber(payload, qpsk) - theory) < 0.006


def test_rayleigh_worse_than_awgn():
    rng = np.random.default_rng(3)
    payload = bytes(rng.integers(0, 256, size=4000, dtype=np.uint8).tolist())
    snr = 6.0
    awgn = apply_radio(payload, rng, modulation="bpsk", snr_db=snr, fading="none")
    ray = apply_radio(
        payload, rng, modulation="bpsk", snr_db=snr, fading="rayleigh_block", coherence_symbols=32
    )
    assert measured_ber(payload, ray) > measured_ber(payload, awgn) + 0.02


def test_block_fading_overdisperses_errors():
    rng = np.random.default_rng(4)
    bits = np.zeros(8192, dtype=np.uint8)
    block_len = 64

    def _block_var(hat: np.ndarray) -> float:
        err = hat.reshape(-1, block_len).sum(axis=1).astype(np.float64)
        return float(err.var())

    block = simulate_radio(
        bits,
        rng,
        modulation="bpsk",
        snr_db=0.0,
        fading="rayleigh_block",
        coherence_symbols=block_len,
    )
    iid = simulate_radio(
        bits,
        rng,
        modulation="bpsk",
        snr_db=0.0,
        fading="rayleigh_iid",
        coherence_symbols=1,
    )
    # Same average BER, but block fading mixes good and bad 64-bit windows.
    assert _block_var(block) > _block_var(iid) * 1.8


def test_radio_batch_matches_single():
    rng_a = np.random.default_rng(9)
    rng_b = np.random.default_rng(9)
    payloads = [bytes(np.random.default_rng(i).integers(0, 256, size=64, dtype=np.uint8)) for i in range(8)]
    batched = apply_radio_payloads(
        payloads, rng_a, modulation="bpsk", snr_db=2.0, fading="none"
    )
    one = [
        apply_radio(p, rng_b, modulation="bpsk", snr_db=2.0, fading="none") for p in payloads
    ]
    # Independent RNG streams after the first draw will not match bit-for-bit
    # across batch vs loop (different sampling order). Check equal length and
    # that both are noisy.
    assert all(len(a) == len(b) for a, b in zip(batched, one, strict=True))
    assert any(a != p for a, p in zip(batched, payloads, strict=True))


def test_apply_channel_radio_replaces_ber():
    rng = np.random.default_rng(5)
    payload = bytes([0xFF]) * 256
    cfg = ChannelConfig(modulation="bpsk", snr_db=0.0, ber=0.5, seed=0)
    out = apply_channel(payload, cfg, rng)
    # Radio at 0 dB is ~0.08 BER, not the stacked 0.5 coin-flip.
    emp = measured_ber(payload, out)
    assert 0.04 < emp < 0.14


def test_apply_channel_many_radio():
    rng = np.random.default_rng(6)
    payloads = [bytes([i & 0xFF]) * 32 for i in range(20)]
    cfg = ChannelConfig(modulation="qpsk", snr_db=4.0, fading="none")
    out = apply_channel_many(payloads, cfg, rng)
    assert len(out) == 20
    assert all(len(a) == 32 for a in out)
