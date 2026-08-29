"""Communication channel models applied to the transmitted bitstream."""

from __future__ import annotations

import numpy as np

from hdc_lidar.channels.radio import apply_radio, apply_radio_payloads
from hdc_lidar.types import ChannelConfig
from hdc_lidar.utils.bits import deinterleave_bits, interleave_bits


def apply_bit_flip(payload: bytes, ber: float, rng: np.random.Generator) -> bytes:
    if ber <= 0.0 or not payload:
        return payload
    arr = np.frombuffer(payload, dtype=np.uint8)
    bits = np.unpackbits(arr, bitorder="big")
    flips = rng.random(bits.size) < ber
    bits ^= flips.astype(np.uint8)
    packed = np.packbits(bits, bitorder="big")
    return packed[: len(payload)].tobytes()


def apply_burst_error(
    payload: bytes,
    burst_length: int,
    n_bursts: int,
    rng: np.random.Generator,
    mode: str = "flip",
) -> bytes:
    if burst_length <= 0 or n_bursts <= 0 or not payload:
        return payload
    arr = np.frombuffer(payload, dtype=np.uint8)
    bits = np.unpackbits(arr, bitorder="big")
    n = bits.size
    for _ in range(n_bursts):
        if burst_length >= n:
            start = 0
            end = n
        else:
            start = int(rng.integers(0, n - burst_length + 1))
            end = start + burst_length
        if mode == "erase":
            bits[start:end] = 0
        else:
            bits[start:end] ^= 1
    packed = np.packbits(bits, bitorder="big")
    return packed[: len(payload)].tobytes()


def apply_packet_loss(
    payload: bytes,
    packet_bytes: int,
    plr: float,
    rng: np.random.Generator,
    fill: int = 0,
) -> bytes:
    if plr <= 0.0 or not payload:
        return payload
    pkt = max(1, int(packet_bytes))
    chunks = [payload[i : i + pkt] for i in range(0, len(payload), pkt)]
    out = bytearray()
    fill_b = bytes([fill & 0xFF])
    for chunk in chunks:
        if rng.random() < plr:
            out.extend(fill_b * len(chunk))
        else:
            out.extend(chunk)
    return bytes(out)


def _radio_active(cfg: ChannelConfig) -> bool:
    return (
        cfg.modulation not in {"", "none"}
        and cfg.snr_db is not None
        and np.isfinite(cfg.snr_db)
    )


def apply_channel(payload: bytes, cfg: ChannelConfig, rng: np.random.Generator) -> bytes:
    data = payload
    order = None
    n_bits = len(data) * 8
    if cfg.interleave:
        data, order = interleave_bits(data, seed=cfg.seed + 17)
    if _radio_active(cfg):
        data = apply_radio(
            data,
            rng,
            modulation=cfg.modulation,
            snr_db=float(cfg.snr_db),
            fading=cfg.fading,
            coherence_symbols=cfg.coherence_symbols,
        )
    else:
        data = apply_bit_flip(data, cfg.ber, rng)
    data = apply_burst_error(data, cfg.burst_length, cfg.n_bursts, rng, cfg.burst_mode)
    data = apply_packet_loss(data, cfg.packet_bytes, cfg.packet_loss_rate, rng)
    if cfg.interleave and order is not None:
        data = deinterleave_bits(data, order, n_bits)
        data = data[: len(payload)]
    return data


def apply_channel_many(
    payloads: list[bytes], cfg: ChannelConfig, rng: np.random.Generator
) -> list[bytes]:
    """Vectorized radio when that is the only impairment; otherwise per-payload."""
    radio_only = (
        _radio_active(cfg)
        and cfg.ber <= 0.0
        and cfg.burst_length <= 0
        and cfg.packet_loss_rate <= 0.0
        and not cfg.interleave
    )
    if radio_only:
        return apply_radio_payloads(
            payloads,
            rng,
            modulation=cfg.modulation,
            snr_db=float(cfg.snr_db),
            fading=cfg.fading,
            coherence_symbols=cfg.coherence_symbols,
        )
    return [apply_channel(p, cfg, rng) for p in payloads]
