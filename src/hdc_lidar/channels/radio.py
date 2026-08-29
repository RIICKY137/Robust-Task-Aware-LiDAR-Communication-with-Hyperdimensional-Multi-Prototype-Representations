"""Uncoded BPSK/QPSK over AWGN or Rayleigh fading, then hard-decision bits.

This is the Stage-8 radio model from the brief: structured physical-layer
errors vs the abstract i.i.d. BER coin-flip. Shared item memory is not
transmitted. Hard decisions keep the rest of the pipeline bit-oriented.
"""

from __future__ import annotations

import numpy as np
from scipy.special import erfc


def theoretical_ber(snr_db: float, modulation: str = "bpsk", fading: str = "none") -> float:
    """Uncoded bit error rate for Gray-coded BPSK/QPSK.

    `snr_db` is Eb/N0 in dB. Gray QPSK matches BPSK. Rayleigh uses the
    closed-form average BER (coherence time does not change the mean).
    """
    if snr_db is None or not np.isfinite(snr_db):
        return 0.0
    gamma = float(10 ** (float(snr_db) / 10.0))
    mod = modulation.lower()
    if mod not in {"bpsk", "qpsk"}:
        raise ValueError(f"unsupported modulation {modulation}")
    if fading in {"none", "awgn"}:
        return float(0.5 * erfc(np.sqrt(gamma)))
    if fading.startswith("rayleigh"):
        return float(0.5 * (1.0 - np.sqrt(gamma / (1.0 + gamma))))
    raise ValueError(f"unsupported fading {fading}")


def simulate_radio(
    bits: np.ndarray,
    rng: np.random.Generator,
    *,
    modulation: str,
    snr_db: float,
    fading: str = "none",
    coherence_symbols: int = 32,
) -> np.ndarray:
    """Hard-decision radio on a {0,1} bit array of shape (n_bits,) or (batch, n_bits)."""
    if snr_db is None or not np.isfinite(snr_db) or snr_db >= 40.0:
        return np.asarray(bits, dtype=np.uint8)
    arr = np.asarray(bits, dtype=np.uint8)
    batched = arr.ndim == 2
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    if arr.ndim != 2:
        raise ValueError("bits must be 1-D or 2-D")
    mod = modulation.lower()
    if mod == "bpsk":
        hat = _bpsk(arr, rng, snr_db=snr_db, fading=fading, coherence_symbols=coherence_symbols)
    elif mod == "qpsk":
        hat = _qpsk(arr, rng, snr_db=snr_db, fading=fading, coherence_symbols=coherence_symbols)
    else:
        raise ValueError(f"unsupported modulation {modulation}")
    return hat[0] if not batched else hat


def _bpsk(
    bits: np.ndarray,
    rng: np.random.Generator,
    *,
    snr_db: float,
    fading: str,
    coherence_symbols: int,
) -> np.ndarray:
    s = 2.0 * bits.astype(np.float64) - 1.0
    snr_lin = 10 ** (float(snr_db) / 10.0)
    if fading in {"none", "awgn"}:
        sigma = np.sqrt(1.0 / (2.0 * snr_lin))
        y = s + rng.normal(0.0, sigma, size=s.shape)
        return (y >= 0.0).astype(np.uint8)
    return _coherent_rayleigh_real(s, rng, snr_lin, fading, coherence_symbols)


def _qpsk(
    bits: np.ndarray,
    rng: np.random.Generator,
    *,
    snr_db: float,
    fading: str,
    coherence_symbols: int,
) -> np.ndarray:
    batch, n_bits = bits.shape
    pad = n_bits % 2
    work = np.pad(bits, ((0, 0), (0, pad)), mode="constant") if pad else bits
    pairs = work.reshape(batch, -1, 2).astype(np.float64)
    # Gray: bit 0 -> I, bit 1 -> Q. Amplitude 1/sqrt(2) so Es = 1, Eb = 1/2.
    i = (1.0 - 2.0 * pairs[:, :, 0]) / np.sqrt(2.0)
    q = (1.0 - 2.0 * pairs[:, :, 1]) / np.sqrt(2.0)
    symbols = i + 1j * q
    snr_lin = 10 ** (float(snr_db) / 10.0)
    n0 = 1.0 / (2.0 * snr_lin)  # N0 = Eb / (Eb/N0) with Eb = Es/2 = 1/2
    if fading in {"none", "awgn"}:
        sigma = np.sqrt(n0 / 2.0)
        noise = rng.normal(0.0, sigma, size=symbols.shape) + 1j * rng.normal(
            0.0, sigma, size=symbols.shape
        )
        y = symbols + noise
        z = y
    else:
        y, h = _apply_rayleigh(symbols, rng, n0, fading, coherence_symbols)
        z = np.conj(h) * y
    i_hat = (np.real(z) >= 0.0).astype(np.uint8)
    q_hat = (np.imag(z) >= 0.0).astype(np.uint8)
    # I >= 0 means bit 0 = 0 because I = (1 - 2 b0)/sqrt(2)
    decoded = np.stack([1 - i_hat, 1 - q_hat], axis=-1).reshape(batch, -1)
    return decoded[:, :n_bits]


def _coherent_rayleigh_real(
    s: np.ndarray,
    rng: np.random.Generator,
    snr_lin: float,
    fading: str,
    coherence_symbols: int,
) -> np.ndarray:
    n0 = 1.0 / snr_lin
    y, h = _apply_rayleigh(s.astype(np.complex128), rng, n0, fading, coherence_symbols)
    z = np.real(np.conj(h) * y)
    return (z >= 0.0).astype(np.uint8)


def _apply_rayleigh(
    symbols: np.ndarray,
    rng: np.random.Generator,
    n0: float,
    fading: str,
    coherence_symbols: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Multiply by CN(0,1) fading. Block fading shares h across `coherence_symbols`."""
    batch, n_sym = symbols.shape
    if fading == "rayleigh_iid":
        block = 1
    elif fading == "rayleigh_block":
        block = max(1, int(coherence_symbols))
    else:
        raise ValueError(f"unsupported fading {fading}")
    n_blocks = int(np.ceil(n_sym / block))
    h_blocks = (
        rng.normal(0.0, 1.0 / np.sqrt(2.0), size=(batch, n_blocks))
        + 1j * rng.normal(0.0, 1.0 / np.sqrt(2.0), size=(batch, n_blocks))
    )
    h = np.repeat(h_blocks, block, axis=1)[:, :n_sym]
    sigma = np.sqrt(n0 / 2.0)
    noise = rng.normal(0.0, sigma, size=symbols.shape) + 1j * rng.normal(
        0.0, sigma, size=symbols.shape
    )
    return h * symbols + noise, h


def apply_radio(
    payload: bytes,
    rng: np.random.Generator,
    *,
    modulation: str,
    snr_db: float,
    fading: str = "none",
    coherence_symbols: int = 32,
) -> bytes:
    if not payload or modulation in {"", "none"}:
        return payload
    bits = np.unpackbits(np.frombuffer(payload, dtype=np.uint8), bitorder="big")
    hat = simulate_radio(
        bits,
        rng,
        modulation=modulation,
        snr_db=snr_db,
        fading=fading,
        coherence_symbols=coherence_symbols,
    )
    packed = np.packbits(hat, bitorder="big")
    return packed[: len(payload)].tobytes()


def apply_radio_payloads(
    payloads: list[bytes],
    rng: np.random.Generator,
    *,
    modulation: str,
    snr_db: float,
    fading: str = "none",
    coherence_symbols: int = 32,
) -> list[bytes]:
    """Batch radio when every payload has the same length (typical sweep cell)."""
    if not payloads:
        return payloads
    n = len(payloads[0])
    if any(len(p) != n for p in payloads):
        return [
            apply_radio(
                p,
                rng,
                modulation=modulation,
                snr_db=snr_db,
                fading=fading,
                coherence_symbols=coherence_symbols,
            )
            for p in payloads
        ]
    arr = np.empty((len(payloads), n), dtype=np.uint8)
    for i, p in enumerate(payloads):
        arr[i] = np.frombuffer(p, dtype=np.uint8)
    bits = np.unpackbits(arr, axis=1, bitorder="big")
    hat = simulate_radio(
        bits,
        rng,
        modulation=modulation,
        snr_db=snr_db,
        fading=fading,
        coherence_symbols=coherence_symbols,
    )
    packed = np.packbits(hat, axis=1, bitorder="big")[:, :n]
    return [row.tobytes() for row in packed]
