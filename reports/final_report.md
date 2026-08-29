# Working region of HDC for task-aware LiDAR communication

This report answers the three questions in the project brief. It does **not** claim HDC wins everywhere.

## What was measured

- Task: 5-way place classification on `sim_indoor_v1`.
- Receiver classifies from the transmitted representation; the scan is never reconstructed.
- Methods: 8-bit quantization, PCA, binary hashing, pure HDC, autoencoder, hybrid neural-HDC.
- Stage 2 uses 5 seeds for burst and packet loss; BER used 3 seeds in the first-round matrix.
- Stage 4 uses 10 / 50 / 100 shots per class, 3 seeds.
- Stage 8 is uncoded BPSK/QPSK at a grid of Eb/N0, plus matched i.i.d. BER.

## RQ1 — bandwidth

See `reports/stage1_bandwidth.md`. On this 180-beam scan, 8-bit PCM saturates at ~188 bytes. Pure HDC is not a compression win (Outcome A fails). Binary hashing leads on a clean channel.

## RQ2 — communication noise

Random BER: `reports/stage2_noise.md` and `results/figures/accuracy_ber.png`.
Burst + interleaving: `results/figures/accuracy_burst.png`.
Packet loss (32 B packets, zero-fill): `results/figures/accuracy_packet_loss.png`.
Packet loss + interleaving: `results/figures/accuracy_packet_interleave.png`.

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

Packet-loss × interleave means:

| method | packet_loss_rate | interleave | accuracy |
| --- | --- | --- | --- |
| binary_hash | 0.0000 | False | 0.9216 |
| binary_hash | 0.1000 | False | 0.8868 |
| binary_hash | 0.1000 | True | 0.8835 |
| binary_hash | 0.2000 | False | 0.8337 |
| binary_hash | 0.2000 | True | 0.8484 |
| binary_hash | 0.4000 | False | 0.7412 |
| binary_hash | 0.4000 | True | 0.7633 |
| pca | 0.0000 | False | 0.7548 |
| pca | 0.1000 | False | 0.6849 |
| pca | 0.1000 | True | 0.5998 |
| pca | 0.2000 | False | 0.6239 |
| pca | 0.2000 | True | 0.4844 |
| pca | 0.4000 | False | 0.5090 |
| pca | 0.4000 | True | 0.3005 |
| pure_hdc | 0.0000 | False | 0.7313 |
| pure_hdc | 0.1000 | False | 0.7324 |
| pure_hdc | 0.1000 | True | 0.7299 |
| pure_hdc | 0.2000 | False | 0.7296 |
| pure_hdc | 0.2000 | True | 0.7291 |
| pure_hdc | 0.4000 | False | 0.7280 |
| pure_hdc | 0.4000 | True | 0.7305 |
| quantized | 0.0000 | False | 0.7473 |
| quantized | 0.1000 | False | 0.6647 |
| quantized | 0.1000 | True | 0.5438 |
| quantized | 0.2000 | False | 0.5866 |
| quantized | 0.2000 | True | 0.4115 |
| quantized | 0.4000 | False | 0.4217 |
| quantized | 0.4000 | True | 0.2389 |

## RQ3 — shift and adaptation

Sensor corruptions (pre-encoder) and OOD floorplan: `reports/stage3_shift.md`.
Few-shot prototype / head updates: `reports/stage4_adaptation.md`.

| shots_per_class | hdc_new_acc | hdc_old_acc | hdc_forgetting | hdc_adapt_ms | quant_new_acc | quant_old_acc | quant_forgetting | quant_adapt_ms | hybrid_new_acc | hybrid_old_acc | hybrid_forgetting | hybrid_adapt_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10.0000 | 0.7202 | 0.7302 | 0.0011 | 11.4762 | 0.7519 | 0.7357 | 0.0116 | 13422.4493 | 0.7509 | 0.7622 | -0.0014 | 12.3151 |
| 50.0000 | 0.7354 | 0.7277 | 0.0036 | 67.5838 | 0.7809 | 0.7274 | 0.0199 | 13382.0472 | 0.7612 | 0.7592 | 0.0017 | 44.6393 |
| 100.0000 | 0.7608 | 0.7247 | 0.0066 | 129.3891 | 0.7931 | 0.7269 | 0.0204 | 13270.2267 | 0.7809 | 0.7575 | 0.0033 | 85.1832 |


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

## Realistic radio (Stage 8)

See `reports/stage8_radio.md`. Uncoded BPSK/QPSK hard decisions vs matched i.i.d. BER at the same Eb/N0.

| method | channel_kind | snr_db | accuracy |
| --- | --- | --- | --- |
| binary_hash | bpsk_awgn | -2.0000 | 0.8150 |
| binary_hash | bpsk_awgn | 0.0000 | 0.8650 |
| binary_hash | bpsk_awgn | 2.0000 | 0.9009 |
| binary_hash | bpsk_awgn | 4.0000 | 0.9144 |
| binary_hash | bpsk_awgn | 6.0000 | 0.9194 |
| binary_hash | bpsk_awgn | 8.0000 | 0.9218 |
| binary_hash | bpsk_rayleigh_block | -2.0000 | 0.7445 |
| binary_hash | bpsk_rayleigh_block | 0.0000 | 0.7896 |
| binary_hash | bpsk_rayleigh_block | 2.0000 | 0.8274 |
| binary_hash | bpsk_rayleigh_block | 4.0000 | 0.8545 |
| binary_hash | bpsk_rayleigh_block | 6.0000 | 0.8829 |
| binary_hash | bpsk_rayleigh_block | 8.0000 | 0.9009 |
| binary_hash | matched_ber | -2.0000 | 0.8042 |
| binary_hash | matched_ber | 0.0000 | 0.8636 |
| binary_hash | matched_ber | 2.0000 | 0.8951 |
| binary_hash | matched_ber | 4.0000 | 0.9127 |
| binary_hash | matched_ber | 6.0000 | 0.9207 |
| binary_hash | matched_ber | 8.0000 | 0.9218 |
| binary_hash | qpsk_awgn | -2.0000 | 0.8172 |
| binary_hash | qpsk_awgn | 0.0000 | 0.8652 |
| binary_hash | qpsk_awgn | 2.0000 | 0.8962 |
| binary_hash | qpsk_awgn | 4.0000 | 0.9149 |
| binary_hash | qpsk_awgn | 6.0000 | 0.9199 |
| binary_hash | qpsk_awgn | 8.0000 | 0.9216 |
| pca | bpsk_awgn | -2.0000 | 0.1566 |
| pca | bpsk_awgn | 0.0000 | 0.1756 |
| pca | bpsk_awgn | 2.0000 | 0.1952 |
| pca | bpsk_awgn | 4.0000 | 0.2773 |
| pca | bpsk_awgn | 6.0000 | 0.5769 |
| pca | bpsk_awgn | 8.0000 | 0.7390 |
| pca | bpsk_rayleigh_block | -2.0000 | 0.1679 |
| pca | bpsk_rayleigh_block | 0.0000 | 0.1707 |
| pca | bpsk_rayleigh_block | 2.0000 | 0.1834 |
| pca | bpsk_rayleigh_block | 4.0000 | 0.1867 |
| pca | bpsk_rayleigh_block | 6.0000 | 0.1914 |
| pca | bpsk_rayleigh_block | 8.0000 | 0.1950 |
| pca | matched_ber | -2.0000 | 0.1638 |
| pca | matched_ber | 0.0000 | 0.1754 |
| pca | matched_ber | 2.0000 | 0.2010 |
| pca | matched_ber | 4.0000 | 0.2831 |
| pca | matched_ber | 6.0000 | 0.5929 |
| pca | matched_ber | 8.0000 | 0.7387 |
| pca | qpsk_awgn | -2.0000 | 0.1646 |
| pca | qpsk_awgn | 0.0000 | 0.1707 |
| pca | qpsk_awgn | 2.0000 | 0.1820 |
| pca | qpsk_awgn | 4.0000 | 0.2767 |
| pca | qpsk_awgn | 6.0000 | 0.5880 |
| pca | qpsk_awgn | 8.0000 | 0.7376 |
| pure_hdc | bpsk_awgn | -2.0000 | 0.7266 |
| pure_hdc | bpsk_awgn | 0.0000 | 0.7280 |
| pure_hdc | bpsk_awgn | 2.0000 | 0.7266 |
| pure_hdc | bpsk_awgn | 4.0000 | 0.7271 |
| pure_hdc | bpsk_awgn | 6.0000 | 0.7305 |
| pure_hdc | bpsk_awgn | 8.0000 | 0.7316 |
| pure_hdc | bpsk_rayleigh_block | -2.0000 | 0.7266 |
| pure_hdc | bpsk_rayleigh_block | 0.0000 | 0.7288 |
| pure_hdc | bpsk_rayleigh_block | 2.0000 | 0.7327 |
| pure_hdc | bpsk_rayleigh_block | 4.0000 | 0.7318 |
| pure_hdc | bpsk_rayleigh_block | 6.0000 | 0.7321 |
| pure_hdc | bpsk_rayleigh_block | 8.0000 | 0.7324 |
| pure_hdc | matched_ber | -2.0000 | 0.7296 |
| pure_hdc | matched_ber | 0.0000 | 0.7288 |
| pure_hdc | matched_ber | 2.0000 | 0.7288 |
| pure_hdc | matched_ber | 4.0000 | 0.7296 |
| pure_hdc | matched_ber | 6.0000 | 0.7294 |
| pure_hdc | matched_ber | 8.0000 | 0.7307 |
| pure_hdc | qpsk_awgn | -2.0000 | 0.7313 |
| pure_hdc | qpsk_awgn | 0.0000 | 0.7299 |
| pure_hdc | qpsk_awgn | 2.0000 | 0.7285 |
| pure_hdc | qpsk_awgn | 4.0000 | 0.7294 |
| pure_hdc | qpsk_awgn | 6.0000 | 0.7299 |
| pure_hdc | qpsk_awgn | 8.0000 | 0.7307 |
| quantized | bpsk_awgn | -2.0000 | 0.2541 |
| quantized | bpsk_awgn | 0.0000 | 0.3115 |
| quantized | bpsk_awgn | 2.0000 | 0.4096 |
| quantized | bpsk_awgn | 4.0000 | 0.5510 |
| quantized | bpsk_awgn | 6.0000 | 0.6877 |
| quantized | bpsk_awgn | 8.0000 | 0.7390 |
| quantized | bpsk_rayleigh_block | -2.0000 | 0.2428 |
| quantized | bpsk_rayleigh_block | 0.0000 | 0.2657 |
| quantized | bpsk_rayleigh_block | 2.0000 | 0.2947 |
| quantized | bpsk_rayleigh_block | 4.0000 | 0.3510 |
| quantized | bpsk_rayleigh_block | 6.0000 | 0.3891 |
| quantized | bpsk_rayleigh_block | 8.0000 | 0.4557 |
| quantized | matched_ber | -2.0000 | 0.2552 |
| quantized | matched_ber | 0.0000 | 0.3259 |
| quantized | matched_ber | 2.0000 | 0.4275 |
| quantized | matched_ber | 4.0000 | 0.5413 |
| quantized | matched_ber | 6.0000 | 0.6877 |
| quantized | matched_ber | 8.0000 | 0.7426 |
| quantized | qpsk_awgn | -2.0000 | 0.2648 |
| quantized | qpsk_awgn | 0.0000 | 0.3259 |
| quantized | qpsk_awgn | 2.0000 | 0.4178 |
| quantized | qpsk_awgn | 4.0000 | 0.5540 |
| quantized | qpsk_awgn | 6.0000 | 0.6780 |
| quantized | qpsk_awgn | 8.0000 | 0.7387 |

## Operating region

| Regime | Current reading |
|---|---|
| Clean 2D scan | Hashing / AE beat pure HDC |
| Random BER | Pure HDC almost flat; PCM/PCA cliff |
| Burst / packet loss | Binary codes degrade slower than float PCA; interleave hurts PCM |
| Uncoded radio | Pure HDC stays flat under BPSK/QPSK AWGN and block Rayleigh; PCM/PCA still cliff. Matched i.i.d. BER tracks AWGN. |
| Sensor dropout / scale | See Stage 3; not billed as communication noise |
| Few-shot OOD | HDC updates are milliseconds vs seconds for a linear refit |
| Hybrid encoder | Task MLP + HDC is BER-flat but still below hashing |

Configs in `configs/`. Frozen splits in `data/splits/sim_indoor_v1/`.

