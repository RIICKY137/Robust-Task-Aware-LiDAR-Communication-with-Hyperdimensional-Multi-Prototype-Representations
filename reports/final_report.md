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

See `reports/stage1_bandwidth.md` for the first-round matrix (single prototype). On this 180-beam scan, 8-bit PCM saturates at ~188 bytes. A **single** HDC prototype is not a compression win (Outcome A fails for k=1). The k=16 remake is `reports/stage1_k16_bandwidth.md`.

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

Sensor corruptions (pre-encoder) and OOD floorplan: `reports/stage3_shift.md` (k=1) and `reports/stage3_k16_sensor.md` (k=16 remake).
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

## LiDAR hybrid HDC

See `reports/stage5_hybrid_lidar.md`. Full-scan frontend ± record bundle, prototype vs linear head.

| method_label | ber | accuracy |
| --- | --- | --- |
| binary_hash | 0.0000 | 0.9216 |
| binary_hash | 0.0100 | 0.9149 |
| binary_hash | 0.0500 | 0.8837 |
| binary_hash | 0.1000 | 0.8398 |
| hybrid_hdc:task/scan/linear/none | 0.0000 | 0.9307 |
| hybrid_hdc:task/scan/linear/none | 0.0100 | 0.9315 |
| hybrid_hdc:task/scan/linear/none | 0.0500 | 0.9276 |
| hybrid_hdc:task/scan/linear/none | 0.1000 | 0.9241 |
| hybrid_hdc:task/scan/linear/record | 0.0000 | 0.9489 |
| hybrid_hdc:task/scan/linear/record | 0.0100 | 0.9475 |
| hybrid_hdc:task/scan/linear/record | 0.0500 | 0.9428 |
| hybrid_hdc:task/scan/linear/record | 0.1000 | 0.9450 |
| hybrid_hdc:task/scan/prototype/none | 0.0000 | 0.7415 |
| hybrid_hdc:task/scan/prototype/none | 0.0100 | 0.7415 |
| hybrid_hdc:task/scan/prototype/none | 0.0500 | 0.7429 |
| hybrid_hdc:task/scan/prototype/none | 0.1000 | 0.7421 |
| hybrid_hdc:task/scan/prototype/record | 0.0000 | 0.7440 |
| hybrid_hdc:task/scan/prototype/record | 0.0100 | 0.7451 |
| hybrid_hdc:task/scan/prototype/record | 0.0500 | 0.7437 |
| hybrid_hdc:task/scan/prototype/record | 0.1000 | 0.7443 |
| hybrid_hdc:task/sector/prototype/none | 0.0000 | 0.7827 |
| hybrid_hdc:task/sector/prototype/none | 0.0100 | 0.7810 |
| hybrid_hdc:task/sector/prototype/none | 0.0500 | 0.7813 |
| hybrid_hdc:task/sector/prototype/none | 0.1000 | 0.7791 |
| pure_hdc_D4096 | 0.0000 | 0.7313 |
| pure_hdc_D4096 | 0.0100 | 0.7302 |
| pure_hdc_D4096 | 0.0500 | 0.7294 |
| pure_hdc_D4096 | 0.1000 | 0.7285 |
| pure_hdc_D4096+lin | 0.0000 | 0.9738 |
| pure_hdc_D4096+lin | 0.0100 | 0.9732 |
| pure_hdc_D4096+lin | 0.0500 | 0.9680 |
| pure_hdc_D4096+lin | 0.1000 | 0.9564 |

## Multi-centroid HDC

See `reports/multicentroid.md`. Same `P⊗L` payload; k prototypes per class vs a linear head.

| split | method_label | ber | accuracy |
| --- | --- | --- | --- |
| test_id | binary_hash | 0.0000 | 0.9216 |
| test_id | binary_hash | 0.0100 | 0.9149 |
| test_id | binary_hash | 0.0500 | 0.8837 |
| test_id | binary_hash | 0.1000 | 0.8398 |
| test_id | pure_hdc_D4096 | 0.0000 | 0.7313 |
| test_id | pure_hdc_D4096 | 0.0100 | 0.7302 |
| test_id | pure_hdc_D4096 | 0.0500 | 0.7294 |
| test_id | pure_hdc_D4096 | 0.1000 | 0.7285 |
| test_id | pure_hdc_D4096+lin | 0.0000 | 0.9738 |
| test_id | pure_hdc_D4096+lin | 0.0100 | 0.9732 |
| test_id | pure_hdc_D4096+lin | 0.0500 | 0.9680 |
| test_id | pure_hdc_D4096+lin | 0.1000 | 0.9564 |
| test_id | pure_hdc_D4096/k16 | 0.0000 | 0.9597 |
| test_id | pure_hdc_D4096/k16 | 0.0100 | 0.9605 |
| test_id | pure_hdc_D4096/k16 | 0.0500 | 0.9589 |
| test_id | pure_hdc_D4096/k16 | 0.1000 | 0.9577 |
| test_id | pure_hdc_D4096/k4 | 0.0000 | 0.8691 |
| test_id | pure_hdc_D4096/k4 | 0.0100 | 0.8688 |
| test_id | pure_hdc_D4096/k4 | 0.0500 | 0.8716 |
| test_id | pure_hdc_D4096/k4 | 0.1000 | 0.8719 |
| test_id | pure_hdc_D4096/k8 | 0.0000 | 0.9171 |
| test_id | pure_hdc_D4096/k8 | 0.0100 | 0.9180 |
| test_id | pure_hdc_D4096/k8 | 0.0500 | 0.9185 |
| test_id | pure_hdc_D4096/k8 | 0.1000 | 0.9155 |
| test_ood | binary_hash | 0.0000 | 0.6228 |
| test_ood | binary_hash | 0.0100 | 0.6153 |
| test_ood | binary_hash | 0.0500 | 0.6062 |
| test_ood | binary_hash | 0.1000 | 0.5794 |
| test_ood | pure_hdc_D4096 | 0.0000 | 0.7114 |
| test_ood | pure_hdc_D4096 | 0.0100 | 0.7133 |
| test_ood | pure_hdc_D4096 | 0.0500 | 0.7104 |
| test_ood | pure_hdc_D4096 | 0.1000 | 0.7062 |
| test_ood | pure_hdc_D4096+lin | 0.0000 | 0.8169 |
| test_ood | pure_hdc_D4096+lin | 0.0100 | 0.8153 |
| test_ood | pure_hdc_D4096+lin | 0.0500 | 0.8076 |
| test_ood | pure_hdc_D4096+lin | 0.1000 | 0.7976 |
| test_ood | pure_hdc_D4096/k16 | 0.0000 | 0.8502 |
| test_ood | pure_hdc_D4096/k16 | 0.0100 | 0.8508 |
| test_ood | pure_hdc_D4096/k16 | 0.0500 | 0.8498 |
| test_ood | pure_hdc_D4096/k16 | 0.1000 | 0.8462 |
| test_ood | pure_hdc_D4096/k4 | 0.0000 | 0.7746 |
| test_ood | pure_hdc_D4096/k4 | 0.0100 | 0.7726 |
| test_ood | pure_hdc_D4096/k4 | 0.0500 | 0.7744 |
| test_ood | pure_hdc_D4096/k4 | 0.1000 | 0.7683 |
| test_ood | pure_hdc_D4096/k8 | 0.0000 | 0.8167 |
| test_ood | pure_hdc_D4096/k8 | 0.0100 | 0.8153 |
| test_ood | pure_hdc_D4096/k8 | 0.0500 | 0.8185 |
| test_ood | pure_hdc_D4096/k8 | 0.1000 | 0.8167 |

## Few-shot multi-centroid adaptation

See `reports/stage4_multicentroid_adapt.md`. OOD shots update the nearest centroid (or refit the linear head).

| method | shots_per_class | new_acc | old_acc | forgetting | adapt_ms |
| --- | --- | --- | --- | --- | --- |
| hdc_k1 | 10 | 0.7202 | 0.7302 | 0.0011 | 11.1975 |
| hdc_k1 | 50 | 0.7354 | 0.7277 | 0.0036 | 88.1252 |
| hdc_k1 | 100 | 0.7608 | 0.7247 | 0.0066 | 156.9646 |
| hdc_k16 | 10 | 0.8643 | 0.9586 | 0.0011 | 34.9867 |
| hdc_k16 | 50 | 0.8980 | 0.9575 | 0.0022 | 186.9678 |
| hdc_k16 | 100 | 0.9205 | 0.9561 | 0.0036 | 344.6755 |
| hdc_k8 | 10 | 0.8287 | 0.9174 | -0.0003 | 21.5726 |
| hdc_k8 | 50 | 0.8708 | 0.9136 | 0.0036 | 119.6395 |
| hdc_k8 | 100 | 0.8931 | 0.9089 | 0.0083 | 222.0537 |
| hdc_linear | 10 | 0.8309 | 0.9751 | -0.0014 | 6438.0719 |
| hdc_linear | 50 | 0.8862 | 0.9713 | 0.0025 | 5499.7658 |
| hdc_linear | 100 | 0.9268 | 0.9671 | 0.0066 | 7755.2710 |

## k=16 bandwidth remake

See `reports/stage1_k16_bandwidth.md`. Same payload family as Stage 1, with k=16 centroids, linear head, hashing, and 8-bit PCM. Dimension fills the budget.

| split | method_label | budget_bytes | accuracy |
| --- | --- | --- | --- |
| test_id | binary_hash | 128 | 0.8638 |
| test_id | binary_hash | 512 | 0.9216 |
| test_id | binary_hash | 2048 | 0.9431 |
| test_id | hdc_k1 | 128 | 0.7269 |
| test_id | hdc_k1 | 512 | 0.7313 |
| test_id | hdc_k1 | 2048 | 0.7352 |
| test_id | hdc_k16 | 128 | 0.9533 |
| test_id | hdc_k16 | 512 | 0.9597 |
| test_id | hdc_k16 | 2048 | 0.9569 |
| test_id | hdc_linear | 128 | 0.9453 |
| test_id | hdc_linear | 512 | 0.9738 |
| test_id | hdc_linear | 2048 | 0.9779 |
| test_id | quantized | 128 | 0.7440 |
| test_id | quantized | 512 | 0.7473 |
| test_id | quantized | 2048 | 0.7473 |
| test_ood | binary_hash | 128 | 0.5834 |
| test_ood | binary_hash | 512 | 0.6228 |
| test_ood | binary_hash | 2048 | 0.6277 |
| test_ood | hdc_k1 | 128 | 0.6990 |
| test_ood | hdc_k1 | 512 | 0.7114 |
| test_ood | hdc_k1 | 2048 | 0.7118 |
| test_ood | hdc_k16 | 128 | 0.8405 |
| test_ood | hdc_k16 | 512 | 0.8502 |
| test_ood | hdc_k16 | 2048 | 0.8531 |
| test_ood | hdc_linear | 128 | 0.7937 |
| test_ood | hdc_linear | 512 | 0.8169 |
| test_ood | hdc_linear | 2048 | 0.8191 |
| test_ood | quantized | 128 | 0.7342 |
| test_ood | quantized | 512 | 0.7531 |
| test_ood | quantized | 2048 | 0.7531 |

## k=16 sensor dropout remake

See `reports/stage3_k16_sensor.md`. Beam and sector dropout before encoding, 512 bytes.

| split | method_label | sensor | accuracy |
| --- | --- | --- | --- |
| test_id | binary_hash | beam_drop:drop_rate=0.1 | 0.5035 |
| test_id | binary_hash | beam_drop:drop_rate=0.3 | 0.2262 |
| test_id | binary_hash | clean | 0.9216 |
| test_id | binary_hash | sector_drop:fraction=0.15 | 0.3933 |
| test_id | binary_hash | sector_drop:fraction=0.3 | 0.2737 |
| test_id | hdc_k1 | beam_drop:drop_rate=0.1 | 0.6703 |
| test_id | hdc_k1 | beam_drop:drop_rate=0.3 | 0.4836 |
| test_id | hdc_k1 | clean | 0.7313 |
| test_id | hdc_k1 | sector_drop:fraction=0.15 | 0.5753 |
| test_id | hdc_k1 | sector_drop:fraction=0.3 | 0.4410 |
| test_id | hdc_k16 | beam_drop:drop_rate=0.1 | 0.9437 |
| test_id | hdc_k16 | beam_drop:drop_rate=0.3 | 0.8028 |
| test_id | hdc_k16 | clean | 0.9597 |
| test_id | hdc_k16 | sector_drop:fraction=0.15 | 0.7926 |
| test_id | hdc_k16 | sector_drop:fraction=0.3 | 0.3869 |
| test_id | hdc_linear | beam_drop:drop_rate=0.1 | 0.7523 |
| test_id | hdc_linear | beam_drop:drop_rate=0.3 | 0.5255 |
| test_id | hdc_linear | clean | 0.9738 |
| test_id | hdc_linear | sector_drop:fraction=0.15 | 0.5929 |
| test_id | hdc_linear | sector_drop:fraction=0.3 | 0.4584 |
| test_id | quantized | beam_drop:drop_rate=0.1 | 0.3314 |
| test_id | quantized | beam_drop:drop_rate=0.3 | 0.2579 |
| test_id | quantized | clean | 0.7473 |
| test_id | quantized | sector_drop:fraction=0.15 | 0.4228 |
| test_id | quantized | sector_drop:fraction=0.3 | 0.3195 |
| test_ood | binary_hash | beam_drop:drop_rate=0.1 | 0.4357 |
| test_ood | binary_hash | beam_drop:drop_rate=0.3 | 0.2534 |
| test_ood | binary_hash | clean | 0.6228 |
| test_ood | binary_hash | sector_drop:fraction=0.15 | 0.3739 |
| test_ood | binary_hash | sector_drop:fraction=0.3 | 0.3095 |
| test_ood | hdc_k1 | beam_drop:drop_rate=0.1 | 0.5375 |
| test_ood | hdc_k1 | beam_drop:drop_rate=0.3 | 0.5426 |
| test_ood | hdc_k1 | clean | 0.7114 |
| test_ood | hdc_k1 | sector_drop:fraction=0.15 | 0.5166 |
| test_ood | hdc_k1 | sector_drop:fraction=0.3 | 0.5066 |
| test_ood | hdc_k16 | beam_drop:drop_rate=0.1 | 0.6976 |
| test_ood | hdc_k16 | beam_drop:drop_rate=0.3 | 0.5901 |
| test_ood | hdc_k16 | clean | 0.8502 |
| test_ood | hdc_k16 | sector_drop:fraction=0.15 | 0.5724 |
| test_ood | hdc_k16 | sector_drop:fraction=0.3 | 0.4373 |
| test_ood | hdc_linear | beam_drop:drop_rate=0.1 | 0.6037 |
| test_ood | hdc_linear | beam_drop:drop_rate=0.3 | 0.5286 |
| test_ood | hdc_linear | clean | 0.8169 |
| test_ood | hdc_linear | sector_drop:fraction=0.15 | 0.5393 |
| test_ood | hdc_linear | sector_drop:fraction=0.3 | 0.4987 |
| test_ood | quantized | beam_drop:drop_rate=0.1 | 0.4007 |
| test_ood | quantized | beam_drop:drop_rate=0.3 | 0.3347 |
| test_ood | quantized | clean | 0.7531 |
| test_ood | quantized | sector_drop:fraction=0.15 | 0.5214 |
| test_ood | quantized | sector_drop:fraction=0.3 | 0.4721 |

## k=16 communication-noise remake

See `reports/stage2_k16_noise.md`. BER at 128 B and 512 B; burst and packet loss at 128 B.

| split | method_label | budget_bytes | ber | accuracy |
| --- | --- | --- | --- | --- |
| test_id | binary_hash | 128 | 0.0000 | 0.8638 |
| test_id | binary_hash | 128 | 0.0100 | 0.8329 |
| test_id | binary_hash | 128 | 0.0500 | 0.7517 |
| test_id | binary_hash | 128 | 0.1000 | 0.6802 |
| test_id | binary_hash | 512 | 0.0000 | 0.9216 |
| test_id | binary_hash | 512 | 0.0100 | 0.9149 |
| test_id | binary_hash | 512 | 0.0500 | 0.8837 |
| test_id | binary_hash | 512 | 0.1000 | 0.8398 |
| test_id | hdc_k1 | 128 | 0.0000 | 0.7269 |
| test_id | hdc_k1 | 128 | 0.0100 | 0.7274 |
| test_id | hdc_k1 | 128 | 0.0500 | 0.7227 |
| test_id | hdc_k1 | 128 | 0.1000 | 0.7197 |
| test_id | hdc_k1 | 512 | 0.0000 | 0.7313 |
| test_id | hdc_k1 | 512 | 0.0100 | 0.7302 |
| test_id | hdc_k1 | 512 | 0.0500 | 0.7294 |
| test_id | hdc_k1 | 512 | 0.1000 | 0.7285 |
| test_id | hdc_k16 | 128 | 0.0000 | 0.9533 |
| test_id | hdc_k16 | 128 | 0.0100 | 0.9533 |
| test_id | hdc_k16 | 128 | 0.0500 | 0.9519 |
| test_id | hdc_k16 | 128 | 0.1000 | 0.9517 |
| test_id | hdc_k16 | 512 | 0.0000 | 0.9597 |
| test_id | hdc_k16 | 512 | 0.0100 | 0.9605 |
| test_id | hdc_k16 | 512 | 0.0500 | 0.9589 |
| test_id | hdc_k16 | 512 | 0.1000 | 0.9577 |
| test_id | hdc_linear | 128 | 0.0000 | 0.9453 |
| test_id | hdc_linear | 128 | 0.0100 | 0.9398 |
| test_id | hdc_linear | 128 | 0.0500 | 0.9086 |
| test_id | hdc_linear | 128 | 0.1000 | 0.8608 |
| test_id | hdc_linear | 512 | 0.0000 | 0.9738 |
| test_id | hdc_linear | 512 | 0.0100 | 0.9732 |
| test_id | hdc_linear | 512 | 0.0500 | 0.9680 |
| test_id | hdc_linear | 512 | 0.1000 | 0.9564 |
| test_id | quantized | 128 | 0.0000 | 0.7440 |
| test_id | quantized | 128 | 0.0100 | 0.5907 |
| test_id | quantized | 128 | 0.0500 | 0.4104 |
| test_id | quantized | 128 | 0.1000 | 0.3082 |
| test_id | quantized | 512 | 0.0000 | 0.7473 |
| test_id | quantized | 512 | 0.0100 | 0.5695 |
| test_id | quantized | 512 | 0.0500 | 0.3891 |
| test_id | quantized | 512 | 0.1000 | 0.2949 |
| test_ood | binary_hash | 128 | 0.0000 | 0.5834 |
| test_ood | binary_hash | 128 | 0.0100 | 0.5716 |
| test_ood | binary_hash | 128 | 0.0500 | 0.5367 |
| test_ood | binary_hash | 128 | 0.1000 | 0.5015 |
| test_ood | binary_hash | 512 | 0.0000 | 0.6228 |
| test_ood | binary_hash | 512 | 0.0100 | 0.6153 |
| test_ood | binary_hash | 512 | 0.0500 | 0.6062 |
| test_ood | binary_hash | 512 | 0.1000 | 0.5794 |
| test_ood | hdc_k1 | 128 | 0.0000 | 0.6990 |
| test_ood | hdc_k1 | 128 | 0.0100 | 0.6976 |
| test_ood | hdc_k1 | 128 | 0.0500 | 0.6911 |
| test_ood | hdc_k1 | 128 | 0.1000 | 0.6816 |
| test_ood | hdc_k1 | 512 | 0.0000 | 0.7114 |
| test_ood | hdc_k1 | 512 | 0.0100 | 0.7133 |
| test_ood | hdc_k1 | 512 | 0.0500 | 0.7104 |
| test_ood | hdc_k1 | 512 | 0.1000 | 0.7062 |
| test_ood | hdc_k16 | 128 | 0.0000 | 0.8405 |
| test_ood | hdc_k16 | 128 | 0.0100 | 0.8405 |
| test_ood | hdc_k16 | 128 | 0.0500 | 0.8374 |
| test_ood | hdc_k16 | 128 | 0.1000 | 0.8338 |
| test_ood | hdc_k16 | 512 | 0.0000 | 0.8502 |
| test_ood | hdc_k16 | 512 | 0.0100 | 0.8508 |
| test_ood | hdc_k16 | 512 | 0.0500 | 0.8498 |
| test_ood | hdc_k16 | 512 | 0.1000 | 0.8462 |
| test_ood | hdc_linear | 128 | 0.0000 | 0.7937 |
| test_ood | hdc_linear | 128 | 0.0100 | 0.7905 |
| test_ood | hdc_linear | 128 | 0.0500 | 0.7659 |
| test_ood | hdc_linear | 128 | 0.1000 | 0.7310 |
| test_ood | hdc_linear | 512 | 0.0000 | 0.8169 |
| test_ood | hdc_linear | 512 | 0.0100 | 0.8153 |
| test_ood | hdc_linear | 512 | 0.0500 | 0.8076 |
| test_ood | hdc_linear | 512 | 0.1000 | 0.7976 |
| test_ood | quantized | 128 | 0.0000 | 0.7342 |
| test_ood | quantized | 128 | 0.0100 | 0.6245 |
| test_ood | quantized | 128 | 0.0500 | 0.4818 |
| test_ood | quantized | 128 | 0.1000 | 0.3930 |
| test_ood | quantized | 512 | 0.0000 | 0.7531 |
| test_ood | quantized | 512 | 0.0100 | 0.6070 |
| test_ood | quantized | 512 | 0.0500 | 0.4513 |
| test_ood | quantized | 512 | 0.1000 | 0.3656 |

## k=16 uncoded-radio remake

See `reports/stage8_k16_radio.md`. BPSK-AWGN, block Rayleigh, and matched BER at 128 B and 512 B.

| split | method_label | budget_bytes | channel_kind | snr_db | accuracy |
| --- | --- | --- | --- | --- | --- |
| test_id | binary_hash | 128 | bpsk_awgn | -2.0000 | 0.6432 |
| test_id | binary_hash | 128 | bpsk_awgn | 0.0000 | 0.7147 |
| test_id | binary_hash | 128 | bpsk_awgn | 4.0000 | 0.8329 |
| test_id | binary_hash | 128 | bpsk_awgn | 8.0000 | 0.8627 |
| test_id | binary_hash | 128 | bpsk_rayleigh_block | -2.0000 | 0.5672 |
| test_id | binary_hash | 128 | bpsk_rayleigh_block | 0.0000 | 0.6147 |
| test_id | binary_hash | 128 | bpsk_rayleigh_block | 4.0000 | 0.7078 |
| test_id | binary_hash | 128 | bpsk_rayleigh_block | 8.0000 | 0.7782 |
| test_id | binary_hash | 128 | matched_ber | -2.0000 | 0.6366 |
| test_id | binary_hash | 128 | matched_ber | 0.0000 | 0.7111 |
| test_id | binary_hash | 128 | matched_ber | 4.0000 | 0.8291 |
| test_id | binary_hash | 128 | matched_ber | 8.0000 | 0.8619 |
| test_id | binary_hash | 512 | bpsk_awgn | -2.0000 | 0.8150 |
| test_id | binary_hash | 512 | bpsk_awgn | 0.0000 | 0.8650 |
| test_id | binary_hash | 512 | bpsk_awgn | 4.0000 | 0.9144 |
| test_id | binary_hash | 512 | bpsk_awgn | 8.0000 | 0.9218 |
| test_id | binary_hash | 512 | bpsk_rayleigh_block | -2.0000 | 0.7445 |
| test_id | binary_hash | 512 | bpsk_rayleigh_block | 0.0000 | 0.7896 |
| test_id | binary_hash | 512 | bpsk_rayleigh_block | 4.0000 | 0.8545 |
| test_id | binary_hash | 512 | bpsk_rayleigh_block | 8.0000 | 0.9009 |
| test_id | binary_hash | 512 | matched_ber | -2.0000 | 0.8042 |
| test_id | binary_hash | 512 | matched_ber | 0.0000 | 0.8636 |
| test_id | binary_hash | 512 | matched_ber | 4.0000 | 0.9127 |
| test_id | binary_hash | 512 | matched_ber | 8.0000 | 0.9218 |
| test_id | hdc_k1 | 128 | bpsk_awgn | -2.0000 | 0.7158 |
| test_id | hdc_k1 | 128 | bpsk_awgn | 0.0000 | 0.7213 |
| test_id | hdc_k1 | 128 | bpsk_awgn | 4.0000 | 0.7247 |
| test_id | hdc_k1 | 128 | bpsk_awgn | 8.0000 | 0.7269 |
| test_id | hdc_k1 | 128 | bpsk_rayleigh_block | -2.0000 | 0.7070 |
| test_id | hdc_k1 | 128 | bpsk_rayleigh_block | 0.0000 | 0.7142 |
| test_id | hdc_k1 | 128 | bpsk_rayleigh_block | 4.0000 | 0.7216 |
| test_id | hdc_k1 | 128 | bpsk_rayleigh_block | 8.0000 | 0.7219 |
| test_id | hdc_k1 | 128 | matched_ber | -2.0000 | 0.7175 |
| test_id | hdc_k1 | 128 | matched_ber | 0.0000 | 0.7263 |
| test_id | hdc_k1 | 128 | matched_ber | 4.0000 | 0.7263 |
| test_id | hdc_k1 | 128 | matched_ber | 8.0000 | 0.7269 |
| test_id | hdc_k1 | 512 | bpsk_awgn | -2.0000 | 0.7266 |
| test_id | hdc_k1 | 512 | bpsk_awgn | 0.0000 | 0.7280 |
| test_id | hdc_k1 | 512 | bpsk_awgn | 4.0000 | 0.7271 |
| test_id | hdc_k1 | 512 | bpsk_awgn | 8.0000 | 0.7316 |
| test_id | hdc_k1 | 512 | bpsk_rayleigh_block | -2.0000 | 0.7266 |
| test_id | hdc_k1 | 512 | bpsk_rayleigh_block | 0.0000 | 0.7288 |
| test_id | hdc_k1 | 512 | bpsk_rayleigh_block | 4.0000 | 0.7318 |
| test_id | hdc_k1 | 512 | bpsk_rayleigh_block | 8.0000 | 0.7324 |
| test_id | hdc_k1 | 512 | matched_ber | -2.0000 | 0.7296 |
| test_id | hdc_k1 | 512 | matched_ber | 0.0000 | 0.7288 |
| test_id | hdc_k1 | 512 | matched_ber | 4.0000 | 0.7296 |
| test_id | hdc_k1 | 512 | matched_ber | 8.0000 | 0.7307 |
| test_id | hdc_k16 | 128 | bpsk_awgn | -2.0000 | 0.9464 |
| test_id | hdc_k16 | 128 | bpsk_awgn | 0.0000 | 0.9495 |
| test_id | hdc_k16 | 128 | bpsk_awgn | 4.0000 | 0.9531 |
| test_id | hdc_k16 | 128 | bpsk_awgn | 8.0000 | 0.9533 |
| test_id | hdc_k16 | 128 | bpsk_rayleigh_block | -2.0000 | 0.9442 |
| test_id | hdc_k16 | 128 | bpsk_rayleigh_block | 0.0000 | 0.9481 |
| test_id | hdc_k16 | 128 | bpsk_rayleigh_block | 4.0000 | 0.9514 |
| test_id | hdc_k16 | 128 | bpsk_rayleigh_block | 8.0000 | 0.9528 |
| test_id | hdc_k16 | 128 | matched_ber | -2.0000 | 0.9486 |
| test_id | hdc_k16 | 128 | matched_ber | 0.0000 | 0.9492 |
| test_id | hdc_k16 | 128 | matched_ber | 4.0000 | 0.9522 |
| test_id | hdc_k16 | 128 | matched_ber | 8.0000 | 0.9533 |
| test_id | hdc_k16 | 512 | bpsk_awgn | -2.0000 | 0.9583 |
| test_id | hdc_k16 | 512 | bpsk_awgn | 0.0000 | 0.9589 |
| test_id | hdc_k16 | 512 | bpsk_awgn | 4.0000 | 0.9597 |
| test_id | hdc_k16 | 512 | bpsk_awgn | 8.0000 | 0.9597 |
| test_id | hdc_k16 | 512 | bpsk_rayleigh_block | -2.0000 | 0.9553 |
| test_id | hdc_k16 | 512 | bpsk_rayleigh_block | 0.0000 | 0.9553 |
| test_id | hdc_k16 | 512 | bpsk_rayleigh_block | 4.0000 | 0.9577 |
| test_id | hdc_k16 | 512 | bpsk_rayleigh_block | 8.0000 | 0.9580 |
| test_id | hdc_k16 | 512 | matched_ber | -2.0000 | 0.9561 |
| test_id | hdc_k16 | 512 | matched_ber | 0.0000 | 0.9575 |
| test_id | hdc_k16 | 512 | matched_ber | 4.0000 | 0.9611 |
| test_id | hdc_k16 | 512 | matched_ber | 8.0000 | 0.9594 |
| test_id | hdc_linear | 128 | bpsk_awgn | -2.0000 | 0.8241 |
| test_id | hdc_linear | 128 | bpsk_awgn | 0.0000 | 0.8771 |
| test_id | hdc_linear | 128 | bpsk_awgn | 4.0000 | 0.9434 |
| test_id | hdc_linear | 128 | bpsk_awgn | 8.0000 | 0.9453 |
| test_id | hdc_linear | 128 | bpsk_rayleigh_block | -2.0000 | 0.7399 |
| test_id | hdc_linear | 128 | bpsk_rayleigh_block | 0.0000 | 0.8003 |
| test_id | hdc_linear | 128 | bpsk_rayleigh_block | 4.0000 | 0.8884 |
| test_id | hdc_linear | 128 | bpsk_rayleigh_block | 8.0000 | 0.9274 |
| test_id | hdc_linear | 128 | matched_ber | -2.0000 | 0.8221 |
| test_id | hdc_linear | 128 | matched_ber | 0.0000 | 0.8879 |
| test_id | hdc_linear | 128 | matched_ber | 4.0000 | 0.9381 |
| test_id | hdc_linear | 128 | matched_ber | 8.0000 | 0.9450 |
| test_id | hdc_linear | 512 | bpsk_awgn | -2.0000 | 0.9528 |
| test_id | hdc_linear | 512 | bpsk_awgn | 0.0000 | 0.9644 |
| test_id | hdc_linear | 512 | bpsk_awgn | 4.0000 | 0.9729 |
| test_id | hdc_linear | 512 | bpsk_awgn | 8.0000 | 0.9732 |
| test_id | hdc_linear | 512 | bpsk_rayleigh_block | -2.0000 | 0.9227 |
| test_id | hdc_linear | 512 | bpsk_rayleigh_block | 0.0000 | 0.9442 |
| test_id | hdc_linear | 512 | bpsk_rayleigh_block | 4.0000 | 0.9652 |
| test_id | hdc_linear | 512 | bpsk_rayleigh_block | 8.0000 | 0.9702 |
| test_id | hdc_linear | 512 | matched_ber | -2.0000 | 0.9506 |
| test_id | hdc_linear | 512 | matched_ber | 0.0000 | 0.9627 |
| test_id | hdc_linear | 512 | matched_ber | 4.0000 | 0.9729 |
| test_id | hdc_linear | 512 | matched_ber | 8.0000 | 0.9738 |
| test_id | quantized | 128 | bpsk_awgn | -2.0000 | 0.2880 |
| test_id | quantized | 128 | bpsk_awgn | 0.0000 | 0.3441 |
| test_id | quantized | 128 | bpsk_awgn | 4.0000 | 0.5653 |
| test_id | quantized | 128 | bpsk_awgn | 8.0000 | 0.7385 |
| test_id | quantized | 128 | bpsk_rayleigh_block | -2.0000 | 0.2347 |
| test_id | quantized | 128 | bpsk_rayleigh_block | 0.0000 | 0.2803 |
| test_id | quantized | 128 | bpsk_rayleigh_block | 4.0000 | 0.3728 |
| test_id | quantized | 128 | bpsk_rayleigh_block | 8.0000 | 0.4736 |
| test_id | quantized | 128 | matched_ber | -2.0000 | 0.2800 |
| test_id | quantized | 128 | matched_ber | 0.0000 | 0.3389 |
| test_id | quantized | 128 | matched_ber | 4.0000 | 0.5700 |
| test_id | quantized | 128 | matched_ber | 8.0000 | 0.7410 |
| test_id | quantized | 512 | bpsk_awgn | -2.0000 | 0.2541 |
| test_id | quantized | 512 | bpsk_awgn | 0.0000 | 0.3115 |
| test_id | quantized | 512 | bpsk_awgn | 4.0000 | 0.5510 |
| test_id | quantized | 512 | bpsk_awgn | 8.0000 | 0.7390 |
| test_id | quantized | 512 | bpsk_rayleigh_block | -2.0000 | 0.2428 |
| test_id | quantized | 512 | bpsk_rayleigh_block | 0.0000 | 0.2657 |
| test_id | quantized | 512 | bpsk_rayleigh_block | 4.0000 | 0.3510 |
| test_id | quantized | 512 | bpsk_rayleigh_block | 8.0000 | 0.4557 |
| test_id | quantized | 512 | matched_ber | -2.0000 | 0.2552 |
| test_id | quantized | 512 | matched_ber | 0.0000 | 0.3259 |
| test_id | quantized | 512 | matched_ber | 4.0000 | 0.5413 |
| test_id | quantized | 512 | matched_ber | 8.0000 | 0.7426 |
| test_ood | binary_hash | 128 | bpsk_awgn | -2.0000 | 0.4727 |
| test_ood | binary_hash | 128 | bpsk_awgn | 0.0000 | 0.5034 |
| test_ood | binary_hash | 128 | bpsk_awgn | 4.0000 | 0.5694 |
| test_ood | binary_hash | 128 | bpsk_awgn | 8.0000 | 0.5806 |
| test_ood | binary_hash | 128 | bpsk_rayleigh_block | -2.0000 | 0.4477 |
| test_ood | binary_hash | 128 | bpsk_rayleigh_block | 0.0000 | 0.4727 |
| test_ood | binary_hash | 128 | bpsk_rayleigh_block | 4.0000 | 0.5170 |
| test_ood | binary_hash | 128 | bpsk_rayleigh_block | 8.0000 | 0.5475 |
| test_ood | binary_hash | 128 | matched_ber | -2.0000 | 0.4843 |
| test_ood | binary_hash | 128 | matched_ber | 0.0000 | 0.5241 |
| test_ood | binary_hash | 128 | matched_ber | 4.0000 | 0.5678 |
| test_ood | binary_hash | 128 | matched_ber | 8.0000 | 0.5816 |
| test_ood | binary_hash | 512 | bpsk_awgn | -2.0000 | 0.5680 |
| test_ood | binary_hash | 512 | bpsk_awgn | 0.0000 | 0.5946 |
| test_ood | binary_hash | 512 | bpsk_awgn | 4.0000 | 0.6192 |
| test_ood | binary_hash | 512 | bpsk_awgn | 8.0000 | 0.6222 |
| test_ood | binary_hash | 512 | bpsk_rayleigh_block | -2.0000 | 0.5267 |
| test_ood | binary_hash | 512 | bpsk_rayleigh_block | 0.0000 | 0.5499 |
| test_ood | binary_hash | 512 | bpsk_rayleigh_block | 4.0000 | 0.5885 |
| test_ood | binary_hash | 512 | bpsk_rayleigh_block | 8.0000 | 0.6084 |
| test_ood | binary_hash | 512 | matched_ber | -2.0000 | 0.5665 |
| test_ood | binary_hash | 512 | matched_ber | 0.0000 | 0.5942 |
| test_ood | binary_hash | 512 | matched_ber | 4.0000 | 0.6163 |
| test_ood | binary_hash | 512 | matched_ber | 8.0000 | 0.6239 |
| test_ood | hdc_k1 | 128 | bpsk_awgn | -2.0000 | 0.6816 |
| test_ood | hdc_k1 | 128 | bpsk_awgn | 0.0000 | 0.6885 |
| test_ood | hdc_k1 | 128 | bpsk_awgn | 4.0000 | 0.6962 |
| test_ood | hdc_k1 | 128 | bpsk_awgn | 8.0000 | 0.6990 |
| test_ood | hdc_k1 | 128 | bpsk_rayleigh_block | -2.0000 | 0.6633 |
| test_ood | hdc_k1 | 128 | bpsk_rayleigh_block | 0.0000 | 0.6741 |
| test_ood | hdc_k1 | 128 | bpsk_rayleigh_block | 4.0000 | 0.6903 |
| test_ood | hdc_k1 | 128 | bpsk_rayleigh_block | 8.0000 | 0.6974 |
| test_ood | hdc_k1 | 128 | matched_ber | -2.0000 | 0.6789 |
| test_ood | hdc_k1 | 128 | matched_ber | 0.0000 | 0.6869 |
| test_ood | hdc_k1 | 128 | matched_ber | 4.0000 | 0.6992 |
| test_ood | hdc_k1 | 128 | matched_ber | 8.0000 | 0.6984 |
| test_ood | hdc_k1 | 512 | bpsk_awgn | -2.0000 | 0.7088 |
| test_ood | hdc_k1 | 512 | bpsk_awgn | 0.0000 | 0.7123 |
| test_ood | hdc_k1 | 512 | bpsk_awgn | 4.0000 | 0.7123 |
| test_ood | hdc_k1 | 512 | bpsk_awgn | 8.0000 | 0.7114 |
| test_ood | hdc_k1 | 512 | bpsk_rayleigh_block | -2.0000 | 0.6962 |
| test_ood | hdc_k1 | 512 | bpsk_rayleigh_block | 0.0000 | 0.7057 |
| test_ood | hdc_k1 | 512 | bpsk_rayleigh_block | 4.0000 | 0.7082 |
| test_ood | hdc_k1 | 512 | bpsk_rayleigh_block | 8.0000 | 0.7106 |
| test_ood | hdc_k1 | 512 | matched_ber | -2.0000 | 0.7058 |
| test_ood | hdc_k1 | 512 | matched_ber | 0.0000 | 0.7086 |
| test_ood | hdc_k1 | 512 | matched_ber | 4.0000 | 0.7127 |
| test_ood | hdc_k1 | 512 | matched_ber | 8.0000 | 0.7110 |
| test_ood | hdc_k16 | 128 | bpsk_awgn | -2.0000 | 0.8230 |
| test_ood | hdc_k16 | 128 | bpsk_awgn | 0.0000 | 0.8295 |
| test_ood | hdc_k16 | 128 | bpsk_awgn | 4.0000 | 0.8395 |
| test_ood | hdc_k16 | 128 | bpsk_awgn | 8.0000 | 0.8405 |
| test_ood | hdc_k16 | 128 | bpsk_rayleigh_block | -2.0000 | 0.8157 |
| test_ood | hdc_k16 | 128 | bpsk_rayleigh_block | 0.0000 | 0.8230 |
| test_ood | hdc_k16 | 128 | bpsk_rayleigh_block | 4.0000 | 0.8330 |
| test_ood | hdc_k16 | 128 | bpsk_rayleigh_block | 8.0000 | 0.8376 |
| test_ood | hdc_k16 | 128 | matched_ber | -2.0000 | 0.8317 |
| test_ood | hdc_k16 | 128 | matched_ber | 0.0000 | 0.8352 |
| test_ood | hdc_k16 | 128 | matched_ber | 4.0000 | 0.8417 |
| test_ood | hdc_k16 | 128 | matched_ber | 8.0000 | 0.8409 |
| test_ood | hdc_k16 | 512 | bpsk_awgn | -2.0000 | 0.8425 |
| test_ood | hdc_k16 | 512 | bpsk_awgn | 0.0000 | 0.8452 |
| test_ood | hdc_k16 | 512 | bpsk_awgn | 4.0000 | 0.8494 |
| test_ood | hdc_k16 | 512 | bpsk_awgn | 8.0000 | 0.8498 |
| test_ood | hdc_k16 | 512 | bpsk_rayleigh_block | -2.0000 | 0.8380 |
| test_ood | hdc_k16 | 512 | bpsk_rayleigh_block | 0.0000 | 0.8437 |
| test_ood | hdc_k16 | 512 | bpsk_rayleigh_block | 4.0000 | 0.8476 |
| test_ood | hdc_k16 | 512 | bpsk_rayleigh_block | 8.0000 | 0.8500 |
| test_ood | hdc_k16 | 512 | matched_ber | -2.0000 | 0.8443 |
| test_ood | hdc_k16 | 512 | matched_ber | 0.0000 | 0.8484 |
| test_ood | hdc_k16 | 512 | matched_ber | 4.0000 | 0.8506 |
| test_ood | hdc_k16 | 512 | matched_ber | 8.0000 | 0.8502 |
| test_ood | hdc_linear | 128 | bpsk_awgn | -2.0000 | 0.7112 |
| test_ood | hdc_linear | 128 | bpsk_awgn | 0.0000 | 0.7478 |
| test_ood | hdc_linear | 128 | bpsk_awgn | 4.0000 | 0.7858 |
| test_ood | hdc_linear | 128 | bpsk_awgn | 8.0000 | 0.7941 |
| test_ood | hdc_linear | 128 | bpsk_rayleigh_block | -2.0000 | 0.6509 |
| test_ood | hdc_linear | 128 | bpsk_rayleigh_block | 0.0000 | 0.6930 |
| test_ood | hdc_linear | 128 | bpsk_rayleigh_block | 4.0000 | 0.7484 |
| test_ood | hdc_linear | 128 | bpsk_rayleigh_block | 8.0000 | 0.7726 |
| test_ood | hdc_linear | 128 | matched_ber | -2.0000 | 0.7070 |
| test_ood | hdc_linear | 128 | matched_ber | 0.0000 | 0.7535 |
| test_ood | hdc_linear | 128 | matched_ber | 4.0000 | 0.7874 |
| test_ood | hdc_linear | 128 | matched_ber | 8.0000 | 0.7933 |
| test_ood | hdc_linear | 512 | bpsk_awgn | -2.0000 | 0.7864 |
| test_ood | hdc_linear | 512 | bpsk_awgn | 0.0000 | 0.7974 |
| test_ood | hdc_linear | 512 | bpsk_awgn | 4.0000 | 0.8132 |
| test_ood | hdc_linear | 512 | bpsk_awgn | 8.0000 | 0.8173 |
| test_ood | hdc_linear | 512 | bpsk_rayleigh_block | -2.0000 | 0.7692 |
| test_ood | hdc_linear | 512 | bpsk_rayleigh_block | 0.0000 | 0.7830 |
| test_ood | hdc_linear | 512 | bpsk_rayleigh_block | 4.0000 | 0.8025 |
| test_ood | hdc_linear | 512 | bpsk_rayleigh_block | 8.0000 | 0.8098 |
| test_ood | hdc_linear | 512 | matched_ber | -2.0000 | 0.7925 |
| test_ood | hdc_linear | 512 | matched_ber | 0.0000 | 0.7948 |
| test_ood | hdc_linear | 512 | matched_ber | 4.0000 | 0.8139 |
| test_ood | hdc_linear | 512 | matched_ber | 8.0000 | 0.8165 |
| test_ood | quantized | 128 | bpsk_awgn | -2.0000 | 0.3698 |
| test_ood | quantized | 128 | bpsk_awgn | 0.0000 | 0.4274 |
| test_ood | quantized | 128 | bpsk_awgn | 4.0000 | 0.6127 |
| test_ood | quantized | 128 | bpsk_awgn | 8.0000 | 0.7273 |
| test_ood | quantized | 128 | bpsk_rayleigh_block | -2.0000 | 0.3365 |
| test_ood | quantized | 128 | bpsk_rayleigh_block | 0.0000 | 0.3686 |
| test_ood | quantized | 128 | bpsk_rayleigh_block | 4.0000 | 0.4335 |
| test_ood | quantized | 128 | bpsk_rayleigh_block | 8.0000 | 0.5292 |
| test_ood | quantized | 128 | matched_ber | -2.0000 | 0.3770 |
| test_ood | quantized | 128 | matched_ber | 0.0000 | 0.4213 |
| test_ood | quantized | 128 | matched_ber | 4.0000 | 0.6094 |
| test_ood | quantized | 128 | matched_ber | 8.0000 | 0.7310 |
| test_ood | quantized | 512 | bpsk_awgn | -2.0000 | 0.3465 |
| test_ood | quantized | 512 | bpsk_awgn | 0.0000 | 0.3877 |
| test_ood | quantized | 512 | bpsk_awgn | 4.0000 | 0.5871 |
| test_ood | quantized | 512 | bpsk_awgn | 8.0000 | 0.7470 |
| test_ood | quantized | 512 | bpsk_rayleigh_block | -2.0000 | 0.3103 |
| test_ood | quantized | 512 | bpsk_rayleigh_block | 0.0000 | 0.3343 |
| test_ood | quantized | 512 | bpsk_rayleigh_block | 4.0000 | 0.4105 |
| test_ood | quantized | 512 | bpsk_rayleigh_block | 8.0000 | 0.4987 |
| test_ood | quantized | 512 | matched_ber | -2.0000 | 0.3367 |
| test_ood | quantized | 512 | matched_ber | 0.0000 | 0.3948 |
| test_ood | quantized | 512 | matched_ber | 4.0000 | 0.5852 |
| test_ood | quantized | 512 | matched_ber | 8.0000 | 0.7452 |

## Sector-drop encoder fix

See `reports/stage3_k16_sector_encode.md`. Skip / DROP-bind invalid beams vs max-range fill.

| split | method_label | sensor | accuracy |
| --- | --- | --- | --- |
| test_id | binary_hash | beam_drop:drop_rate=0.1 | 0.5035 |
| test_id | binary_hash | beam_drop:drop_rate=0.3 | 0.2262 |
| test_id | binary_hash | clean | 0.9216 |
| test_id | binary_hash | sector_drop:fraction=0.15 | 0.3933 |
| test_id | binary_hash | sector_drop:fraction=0.3 | 0.2737 |
| test_id | hdc_k16/drop | beam_drop:drop_rate=0.1 | 0.9555 |
| test_id | hdc_k16/drop | beam_drop:drop_rate=0.3 | 0.9489 |
| test_id | hdc_k16/drop | clean | 0.9597 |
| test_id | hdc_k16/drop | sector_drop:fraction=0.15 | 0.9473 |
| test_id | hdc_k16/drop | sector_drop:fraction=0.3 | 0.8989 |
| test_id | hdc_k16/fill | beam_drop:drop_rate=0.1 | 0.9437 |
| test_id | hdc_k16/fill | beam_drop:drop_rate=0.3 | 0.8028 |
| test_id | hdc_k16/fill | clean | 0.9597 |
| test_id | hdc_k16/fill | sector_drop:fraction=0.15 | 0.7926 |
| test_id | hdc_k16/fill | sector_drop:fraction=0.3 | 0.3869 |
| test_id | hdc_k16/skip | beam_drop:drop_rate=0.1 | 0.9547 |
| test_id | hdc_k16/skip | beam_drop:drop_rate=0.3 | 0.9500 |
| test_id | hdc_k16/skip | clean | 0.9597 |
| test_id | hdc_k16/skip | sector_drop:fraction=0.15 | 0.9426 |
| test_id | hdc_k16/skip | sector_drop:fraction=0.3 | 0.9017 |
| test_ood | binary_hash | beam_drop:drop_rate=0.1 | 0.4357 |
| test_ood | binary_hash | beam_drop:drop_rate=0.3 | 0.2534 |
| test_ood | binary_hash | clean | 0.6228 |
| test_ood | binary_hash | sector_drop:fraction=0.15 | 0.3739 |
| test_ood | binary_hash | sector_drop:fraction=0.3 | 0.3095 |
| test_ood | hdc_k16/drop | beam_drop:drop_rate=0.1 | 0.8183 |
| test_ood | hdc_k16/drop | beam_drop:drop_rate=0.3 | 0.8277 |
| test_ood | hdc_k16/drop | clean | 0.8502 |
| test_ood | hdc_k16/drop | sector_drop:fraction=0.15 | 0.7992 |
| test_ood | hdc_k16/drop | sector_drop:fraction=0.3 | 0.7525 |
| test_ood | hdc_k16/fill | beam_drop:drop_rate=0.1 | 0.6976 |
| test_ood | hdc_k16/fill | beam_drop:drop_rate=0.3 | 0.5901 |
| test_ood | hdc_k16/fill | clean | 0.8502 |
| test_ood | hdc_k16/fill | sector_drop:fraction=0.15 | 0.5724 |
| test_ood | hdc_k16/fill | sector_drop:fraction=0.3 | 0.4373 |
| test_ood | hdc_k16/skip | beam_drop:drop_rate=0.1 | 0.7990 |
| test_ood | hdc_k16/skip | beam_drop:drop_rate=0.3 | 0.7689 |
| test_ood | hdc_k16/skip | clean | 0.8502 |
| test_ood | hdc_k16/skip | sector_drop:fraction=0.15 | 0.7667 |
| test_ood | hdc_k16/skip | sector_drop:fraction=0.3 | 0.7019 |

## k=16 few-shot remake at 128 B

See `reports/stage4_k16_adaptation_128b.md`. 10/50/100-shot OOD at the 128 B operating point.

| method | shots_per_class | new_acc | old_acc | forgetting | adapt_ms |
| --- | --- | --- | --- | --- | --- |
| hdc_k1 | 10 | 0.7070 | 0.7283 | -0.0014 | 3.8749 |
| hdc_k1 | 50 | 0.7216 | 0.7227 | 0.0041 | 23.8353 |
| hdc_k1 | 100 | 0.7511 | 0.7213 | 0.0055 | 40.7021 |
| hdc_k16 | 10 | 0.8533 | 0.9531 | 0.0003 | 8.9237 |
| hdc_k16 | 50 | 0.8897 | 0.9508 | 0.0025 | 41.8532 |
| hdc_k16 | 100 | 0.9100 | 0.9450 | 0.0083 | 80.0889 |
| hdc_linear | 10 | 0.8037 | 0.9448 | 0.0006 | 3915.3021 |
| hdc_linear | 50 | 0.8519 | 0.9312 | 0.0141 | 5045.6929 |
| hdc_linear | 100 | 0.8976 | 0.9263 | 0.0191 | 5016.7579 |

## Real 2D LiDAR (Semantic2D)

See `reports/stage0_semantic2d.md`. 128 B remake on real scans with derived place labels.

| split | method_label | ber | accuracy |
| --- | --- | --- | --- |
| test_id | binary_hash | 0.0000 | 0.3833 |
| test_id | binary_hash | 0.0500 | 0.3257 |
| test_id | binary_hash | 0.1000 | 0.3014 |
| test_id | hdc_k1 | 0.0000 | 0.3488 |
| test_id | hdc_k1 | 0.0500 | 0.3371 |
| test_id | hdc_k1 | 0.1000 | 0.3412 |
| test_id | hdc_k16 | 0.0000 | 0.5046 |
| test_id | hdc_k16 | 0.0500 | 0.5074 |
| test_id | hdc_k16 | 0.1000 | 0.5008 |
| test_id | hdc_linear | 0.0000 | 0.4511 |
| test_id | hdc_linear | 0.0500 | 0.3966 |
| test_id | hdc_linear | 0.1000 | 0.3650 |
| test_id | quantized | 0.0000 | 0.3552 |
| test_id | quantized | 0.0500 | 0.2067 |
| test_id | quantized | 0.1000 | 0.1570 |
| test_ood | binary_hash | 0.0000 | 0.3286 |
| test_ood | binary_hash | 0.0500 | 0.3048 |
| test_ood | binary_hash | 0.1000 | 0.2940 |
| test_ood | hdc_k1 | 0.0000 | 0.2345 |
| test_ood | hdc_k1 | 0.0500 | 0.2347 |
| test_ood | hdc_k1 | 0.1000 | 0.2365 |
| test_ood | hdc_k16 | 0.0000 | 0.3483 |
| test_ood | hdc_k16 | 0.0500 | 0.3451 |
| test_ood | hdc_k16 | 0.1000 | 0.3395 |
| test_ood | hdc_linear | 0.0000 | 0.3256 |
| test_ood | hdc_linear | 0.0500 | 0.2954 |
| test_ood | hdc_linear | 0.1000 | 0.2838 |
| test_ood | quantized | 0.0000 | 0.2529 |
| test_ood | quantized | 0.0500 | 0.1681 |
| test_ood | quantized | 0.1000 | 0.1401 |

## Real 2D LiDAR (LidarDataFrames, author labels)

See `reports/stage0_lidardataframes.md`. 128 B remake on 411 author-labeled scans. `test_ood` is i.i.d., not a building shift.

| split | method_label | ber | accuracy |
| --- | --- | --- | --- |
| test_id | binary_hash | 0.0000 | 0.8594 |
| test_id | binary_hash | 0.0500 | 0.7952 |
| test_id | binary_hash | 0.1000 | 0.7028 |
| test_id | hdc_k1 | 0.0000 | 0.9679 |
| test_id | hdc_k1 | 0.0500 | 0.9639 |
| test_id | hdc_k1 | 0.1000 | 0.9518 |
| test_id | hdc_k16 | 0.0000 | 0.9679 |
| test_id | hdc_k16 | 0.0500 | 0.9639 |
| test_id | hdc_k16 | 0.1000 | 0.9719 |
| test_id | hdc_linear | 0.0000 | 0.9759 |
| test_id | hdc_linear | 0.0500 | 0.9558 |
| test_id | hdc_linear | 0.1000 | 0.9679 |
| test_id | quantized | 0.0000 | 0.9036 |
| test_id | quantized | 0.0500 | 0.5984 |
| test_id | quantized | 0.1000 | 0.4177 |
| test_ood | binary_hash | 0.0000 | 0.8008 |
| test_ood | binary_hash | 0.0500 | 0.7805 |
| test_ood | binary_hash | 0.1000 | 0.6870 |
| test_ood | hdc_k1 | 0.0000 | 0.8984 |
| test_ood | hdc_k1 | 0.0500 | 0.8984 |
| test_ood | hdc_k1 | 0.1000 | 0.9065 |
| test_ood | hdc_k16 | 0.0000 | 0.9472 |
| test_ood | hdc_k16 | 0.0500 | 0.9390 |
| test_ood | hdc_k16 | 0.1000 | 0.9431 |
| test_ood | hdc_linear | 0.0000 | 0.9756 |
| test_ood | hdc_linear | 0.0500 | 0.9756 |
| test_ood | hdc_linear | 0.1000 | 0.9715 |
| test_ood | quantized | 0.0000 | 0.8537 |
| test_ood | quantized | 0.0500 | 0.5488 |
| test_ood | quantized | 0.1000 | 0.4228 |

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
| Clean 2D scan | k=1 prototype loses to hashing; k=16 / linear close that gap. See k=16 bandwidth remake. |
| Random BER | k=16 stays flat at 128 B (~0.95). Linear head is not holographic at that budget. PCM cliffs. |
| Burst / packet loss | k=16 holds 128-bit bursts and 20% packet loss at 128 B; a 512-bit burst (half the code) is a failure region |
| Uncoded radio | k=16 stays flat at 128 B under BPSK-AWGN and block Rayleigh; matched BER tracks AWGN. Linear is hurt by clustered fades. |
| Sensor dropout / scale | k=16 holds random beam drop. 30% sector drop with max-range fill is a fake opening (~0.39 ID). Skip/DROP recover ~0.90 ID / ~0.70–0.75 OOD. |
| Real 2D LiDAR | Semantic2D (derived labels) ID ~0.50. LidarDataFrames (author labels, 411 frames): `reports/stage0_lidardataframes.md`. |
| Hybrid encoder | Prototype head ~0.73–0.80; linear head on HDC codes can match/beat hashing |
| Multi-centroid | k>1 lifts prototype accuracy while staying BER-flat; see OOD vs linear in the table |

Configs in `configs/`. Frozen splits in `data/splits/sim_indoor_v1/`, `semantic2d_v1/`, and `lidardataframes_v1/`.

