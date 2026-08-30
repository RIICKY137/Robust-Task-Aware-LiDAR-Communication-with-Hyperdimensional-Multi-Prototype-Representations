# HDC Task-Aware LiDAR Communication

面向带宽受限、信道不稳定机器人系统的 **HDC 任务感知 LiDAR 通信** 研究仓库。

HDC-based task-aware communication for bandwidth-constrained robotic LiDAR. The receiver **does not reconstruct the scan**. It classifies place type from the transmitted representation: corridor, room, doorway, open area, or cluttered area.

This repository follows the project brief: compare HDC against quantization, PCA, autoencoder, and binary hashing under a **shared byte budget**, then stress the bitstream with bit flips, bursts, and packet loss, then measure few-shot prototype updates after environment shift. HDC is **not** assumed to win. The goal is the **operating region** (bandwidth × noise × adaptation cost) where it helps or fails.

## What is implemented (Stage 0 → first-round matrix)

| Piece | Status |
|---|---|
| 2D LiDAR simulator + trajectory/environment splits | yes |
| 8-bit / raw / 4-bit quantization + logistic classifier | yes |
| PCA coefficients (train-only fit) | yes |
| Random binary hashing (no HDC binding) | yes |
| Pure HDC (position ⊗ level, bundle, prototypes) | yes |
| MLP autoencoder latent + hybrid neural-HDC | yes |
| BER, burst, packet loss, packet+interleave, uncoded radio | yes |
| Sensor dropout / scale (pre-encoder, not mixed with BER) | yes |
| Few-shot HDC / hybrid prototype add/subtract (10/50/100) | yes |
| Unit tests for HDC ops, bit accounting, channels, splits | yes |
| Streamlit lab for scans, live channel, curves | yes |

Later stages in the brief that are still open: a real public 2D LiDAR + place-label dataset (the simulator is the Stage 0 fallback), and a hardware radio trace. Stage 8 here is an uncoded BPSK/QPSK + AWGN/Rayleigh model, not over-the-air captures.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run the pipeline in the required order

```bash
# Stage 0 — data, splits, sample figures, reports/data_report.md
python scripts/prepare_data.py

# Smoke: five methods, 512 bytes, clean channel
python scripts/train_baselines.py
pytest

# Stage 1 — Accuracy–Bandwidth (BER = 0). First-round used k=1 prototypes.
python scripts/run_bandwidth_sweep.py

# Stage 1 remake — k=16 / linear / hashing / 8-bit at 128 / 512 / 2048 B
python scripts/run_k16_bandwidth.py

# Stage 2 — Accuracy–BER at 512 bytes
python scripts/run_noise_sweep.py
python scripts/run_burst_sweep.py
python scripts/run_packet_loss_sweep.py

# Stage 2 remake — k=16 / linear / hashing / 8-bit at 128 B (and 512 B BER control)
python scripts/run_k16_noise.py

# Stage 3 — sensor dropout / scale / OOD floorplan (not mixed with BER)
python scripts/run_sensor_shift.py

# Stage 3 remake — k=16 under beam / sector dropout
python scripts/run_k16_sensor.py

# Sector-drop encoder fix — skip / DROP vs max-range fill (512 B, k=16)
python scripts/run_k16_sector_encode.py
# Missing beams as NaN, not max-range. Do not overwrite k16_sensor.jsonl.

# Stage 4 remake — few-shot OOD at the 128 B operating point (k=1 / k=16 / linear)
python scripts/run_k16_adaptation_128b.py
# Does not overwrite adaptation.jsonl or multicentroid_adaptation.jsonl.

# Stage 4 — 10 / 50 / 100-shot OOD HDC vs 8-bit logistic vs hybrid
python scripts/run_shift_adaptation.py

# Few-shot OOD: multi-centroid k=1/8/16 vs linear head
python scripts/run_multicentroid_adaptation.py

# Multi-centroid HDC vs single prototype vs linear head
python scripts/run_multicentroid.py

# LiDAR hybrid HDC — full-scan frontend ± record bundle vs hashing
python scripts/run_hybrid_lidar.py

# Stage 8 — uncoded BPSK/QPSK + AWGN/Rayleigh vs matched BER
python scripts/run_radio_sweep.py
python scripts/run_packet_interleave_sweep.py

# Stage 8 remake — k=16 at 128 B (BPSK AWGN / block Rayleigh / matched BER)
python scripts/run_k16_radio.py

# Figures + markdown from raw JSONL (never hand-edit the curves)
python scripts/aggregate_results.py
```

Interactive lab (dataset browser, live BER, logged curves):

```bash
python scripts/serve_lab.py 43187
```

## Communication accounting

Per-sample bits include the serialized representation **and** on-the-wire scale / header metadata. Shared HDC item memories, PCA bases, and hashing matrices are **not** billed per scan; they are reported as `shared_memory_bytes` on every result row.

First-round budget grid: **128 / 512 / 2048 bytes**. HDC dimensions **1K / 4K / 8K** are only run when they fit the budget (`D ≤ 8 × bytes`).

## Repository layout

Matches the brief:

```
configs/ datasets, methods, experiments
src/hdc_lidar/
  data/        simulator + frozen split I/O
  methods/     quantization, pca, autoencoder, binary_hash, pure_hdc, hybrid_hdc
  channels/    bit_flip, burst_error, packet_loss, radio (BPSK/QPSK), sensor_corruption
  adaptation/  prototype update and shot sampling
  evaluation/  accuracy, macro-F1, confusion, forgetting
scripts/       prepare_data, sweeps, aggregate
tests/
results/raw|tables|figures
reports/
```

## Success criteria (from the brief)

A meaningful result is **any** of: (A) similar accuracy at fewer bytes, (B) slower drop under BER/burst/loss, (C) cheaper few-shot recovery after shift, or (D) a clearly mapped failure region. Do not report only the best seed.

## License

Research code. Cite the project brief if you reuse the protocol.
