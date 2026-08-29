# Working region of HDC for task-aware LiDAR communication

This report answers the three questions in the project brief. It does **not** claim HDC wins everywhere.

## What was measured

- Task: 5-way place classification on `sim_indoor_v1`.
- Receiver classifies from the transmitted representation; the scan is never reconstructed.
- Methods: 8-bit quantization, PCA, binary hashing, pure HDC, autoencoder, hybrid neural-HDC.
- Stage 2 uses 5 seeds for burst and packet loss; BER used 3 seeds in the first-round matrix.

## RQ1 — bandwidth

See `reports/stage1_bandwidth.md`. On this 180-beam scan, 8-bit PCM saturates at ~188 bytes. Pure HDC is not a compression win (Outcome A fails). Binary hashing leads on a clean channel.

## RQ2 — communication noise

Random BER: `reports/stage2_noise.md` and `results/figures/accuracy_ber.png`.
Burst + interleaving: `results/figures/accuracy_burst.png`.
Packet loss (32 B packets, zero-fill): `results/figures/accuracy_packet_loss.png`.

BER means:

| method | 0.0 | 0.01 | 0.05 | 0.1 |
| --- | --- | --- | --- | --- |
| binary_hash | 0.9216 | 0.9149 | 0.8837 | 0.8398 |
| pca | 0.7548 | 0.3253 | 0.1889 | 0.1668 |
| pure_hdc | 0.7313 | 0.7302 | 0.7294 | 0.7285 |
| quantized | 0.7473 | 0.5695 | 0.3891 | 0.2949 |

Burst means:

| method | burst_length | interleave | accuracy |
| --- | --- | --- | --- |
| binary_hash | 0 | False | 0.9223 |
| binary_hash | 32 | False | 0.9143 |
| binary_hash | 32 | True | 0.9155 |
| binary_hash | 128 | False | 0.8968 |
| binary_hash | 128 | True | 0.8994 |
| binary_hash | 512 | False | 0.8089 |
| binary_hash | 512 | True | 0.8136 |
| binary_hash | 1024 | False | 0.6759 |
| binary_hash | 1024 | True | 0.6747 |
| pca | 0 | False | 0.7548 |
| pca | 32 | False | 0.3210 |
| pca | 32 | True | 0.3649 |
| pca | 128 | False | 0.2394 |
| pca | 128 | True | 0.2066 |
| pca | 512 | False | 0.1920 |
| pca | 512 | True | 0.1672 |
| pca | 1024 | False | 0.1879 |
| pca | 1024 | True | 0.1541 |
| pure_hdc | 0 | False | 0.7304 |
| pure_hdc | 32 | False | 0.7301 |
| pure_hdc | 32 | True | 0.7311 |
| pure_hdc | 128 | False | 0.7299 |
| pure_hdc | 128 | True | 0.7301 |
| pure_hdc | 512 | False | 0.7279 |
| pure_hdc | 512 | True | 0.7291 |
| pure_hdc | 1024 | False | 0.7261 |
| pure_hdc | 1024 | True | 0.7241 |
| quantized | 0 | False | 0.7473 |
| quantized | 32 | False | 0.6073 |
| quantized | 32 | True | 0.4853 |
| quantized | 128 | False | 0.5024 |
| quantized | 128 | True | 0.2969 |
| quantized | 512 | False | 0.2441 |
| quantized | 512 | True | 0.1723 |
| quantized | 1024 | False | 0.2023 |
| quantized | 1024 | True | 0.1466 |

Packet-loss means:

| method | packet_loss_rate | accuracy |
| --- | --- | --- |
| binary_hash | 0.0000 | 0.9223 |
| binary_hash | 0.0100 | 0.9201 |
| binary_hash | 0.0500 | 0.9012 |
| binary_hash | 0.1000 | 0.8840 |
| binary_hash | 0.2000 | 0.8330 |
| binary_hash | 0.4000 | 0.7359 |
| pca | 0.0000 | 0.7548 |
| pca | 0.0100 | 0.7488 |
| pca | 0.0500 | 0.7195 |
| pca | 0.1000 | 0.6882 |
| pca | 0.2000 | 0.6285 |
| pca | 0.4000 | 0.5128 |
| pure_hdc | 0.0000 | 0.7304 |
| pure_hdc | 0.0100 | 0.7299 |
| pure_hdc | 0.0500 | 0.7312 |
| pure_hdc | 0.1000 | 0.7289 |
| pure_hdc | 0.2000 | 0.7271 |
| pure_hdc | 0.4000 | 0.7251 |
| quantized | 0.0000 | 0.7473 |
| quantized | 0.0100 | 0.7417 |
| quantized | 0.0500 | 0.7082 |
| quantized | 0.1000 | 0.6620 |
| quantized | 0.2000 | 0.5857 |
| quantized | 0.4000 | 0.4224 |

## RQ3 — shift and adaptation

Sensor corruptions (pre-encoder) and OOD floorplan: `reports/stage3_shift.md`.

| shots_per_class | hdc_new_acc | hdc_old_acc | hdc_forgetting | hdc_adapt_ms | quant_new_acc | quant_old_acc | quant_forgetting | quant_adapt_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.0000 | 0.7212 | 0.7307 | -0.0008 | 1.8491 | 0.7448 | 0.7349 | 0.0124 | 14375.4380 |
| 2.0000 | 0.7242 | 0.7332 | -0.0033 | 7.1728 | 0.7437 | 0.7390 | 0.0083 | 11775.5495 |
| 5.0000 | 0.7247 | 0.7258 | 0.0041 | 5.8309 | 0.7496 | 0.7357 | 0.0116 | 13288.1509 |
| 10.0000 | 0.7318 | 0.7241 | 0.0058 | 23.2973 | 0.7596 | 0.7291 | 0.0182 | 13059.7154 |
| 20.0000 | 0.7383 | 0.7225 | 0.0075 | 33.7809 | 0.7649 | 0.7299 | 0.0174 | 11337.6466 |


## Hybrid HDC (Stage 5)

See `reports/stage5_hybrid.md`. This tests whether a task-trained encoder recovers the geometry that record-based pure HDC drops, while keeping a binary HDC payload.

| method_label | ber | accuracy |
| --- | --- | --- |
| autoencoder | 0.0000 | 0.9006 |
| autoencoder | 0.0100 | 0.4935 |
| autoencoder | 0.0500 | 0.3170 |
| autoencoder | 0.1000 | 0.2717 |
| binary_hash | 0.0000 | 0.9216 |
| binary_hash | 0.0100 | 0.9149 |
| binary_hash | 0.0500 | 0.8837 |
| binary_hash | 0.1000 | 0.8398 |
| hybrid_hdc:frozen | 0.0000 | 0.7266 |
| hybrid_hdc:frozen | 0.0100 | 0.7263 |
| hybrid_hdc:frozen | 0.0500 | 0.7258 |
| hybrid_hdc:frozen | 0.1000 | 0.7225 |
| hybrid_hdc:task | 0.0000 | 0.7608 |
| hybrid_hdc:task | 0.0100 | 0.7622 |
| hybrid_hdc:task | 0.0500 | 0.7611 |
| hybrid_hdc:task | 0.1000 | 0.7597 |
| pure_hdc_D4096 | 0.0000 | 0.7313 |
| pure_hdc_D4096 | 0.0100 | 0.7302 |
| pure_hdc_D4096 | 0.0500 | 0.7294 |
| pure_hdc_D4096 | 0.1000 | 0.7285 |

## Operating region

| Regime | Current reading |
|---|---|
| Clean 2D scan | Hashing / AE beat pure HDC |
| Random BER | Pure HDC almost flat; PCM/PCA cliff |
| Burst / packet loss | See Stage 2 tables — binary codes degrade slower than float PCA |
| Sensor dropout / scale | See Stage 3; not billed as communication noise |
| Few-shot OOD | HDC updates are milliseconds vs seconds |
| Hybrid encoder | Stage 5: does task MLP + HDC close the hashing gap? |

Configs in `configs/`. Frozen splits in `data/splits/sim_indoor_v1/`.

