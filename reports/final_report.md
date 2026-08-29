# Working region of HDC for task-aware LiDAR communication

This report answers the three questions in the project brief. It does **not** claim HDC wins everywhere.

## What was measured

- Task: 5-way place classification (corridor / room / doorway / open / cluttered) on `sim_indoor_v1`.
- Receiver classifies from the transmitted representation; the scan is never reconstructed for the metric.
- First-round methods: 8-bit quantization, PCA, binary hashing, pure HDC. Autoencoder and hybrid HDC are implemented for later stages.
- Splits: trajectory hold-out (`test_id`) and a different floorplan (`test_ood`).

## RQ1 — bandwidth

On a 180-beam 2D scan, full 8-bit PCM is only **188 bytes** including header. Raising the budget above that does not add beams, so quantization saturates. HDC at D=8K is **1024 bytes**, already larger than the raw 8-bit scan — this is the brief's Risk 2.

Clean-channel ID accuracy (means over 3 seeds): binary hashing is strongest (~0.86 at 128 B, ~0.92 at 512 B). Pure HDC sits with 8-bit PCM and PCA around **0.73–0.75** and barely moves with D. So HDC is **not** a bandwidth winner here (Outcome A fails). The hashing vs HDC gap is Risk 3: much of the clean-channel gain is **binarization + a trained linear head**, not position-level binding.

See `reports/stage1_bandwidth.md` and `results/figures/accuracy_bandwidth.png`.

## RQ2 — noise (clearest HDC advantage)

At a 512-byte cap, flipping bits in the **payload** (not the labels):

| method | 0.0 | 0.01 | 0.05 | 0.1 |
| --- | --- | --- | --- | --- |
| binary_hash | 0.9216 | 0.9149 | 0.8837 | 0.8398 |
| pca | 0.7548 | 0.3253 | 0.1889 | 0.1668 |
| pure_hdc | 0.7313 | 0.7302 | 0.7294 | 0.7285 |
| quantized | 0.7473 | 0.5695 | 0.3891 | 0.2949 |

Pure HDC is almost flat from BER 0 to 0.10 (**~0.731 → ~0.729**). 8-bit PCM drops **0.75 → 0.29**. PCA float32 bits collapse **0.75 → 0.17**. Binary hashing degrades slowly (**0.92 → 0.84**) but still faster than HDC.

This is **Outcome B**: at matched budget, HDC shows repeatable graceful degradation versus at least two reasonable baselines, across seeds. Binary hashing shares the binary codebook robustness; HDC's extra structure did not win clean accuracy, but Hamming/cosine to analog prototypes is the most noise-stable classifier in this matrix.

Figure: `results/figures/accuracy_ber.png`.

## RQ3 — few-shot adaptation

| shots_per_class | hdc_new_acc | hdc_old_acc | hdc_forgetting | hdc_adapt_ms | quant_new_acc | quant_old_acc | quant_forgetting | quant_adapt_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.0000 | 0.7212 | 0.7307 | -0.0008 | 1.8491 | 0.7448 | 0.7349 | 0.0124 | 14375.4380 |
| 2.0000 | 0.7242 | 0.7332 | -0.0033 | 7.1728 | 0.7437 | 0.7390 | 0.0083 | 11775.5495 |
| 5.0000 | 0.7247 | 0.7258 | 0.0041 | 5.8309 | 0.7496 | 0.7357 | 0.0116 | 13288.1509 |
| 10.0000 | 0.7318 | 0.7241 | 0.0058 | 23.2973 | 0.7596 | 0.7291 | 0.0182 | 13059.7154 |
| 20.0000 | 0.7383 | 0.7225 | 0.0075 | 33.7809 | 0.7649 | 0.7299 | 0.0174 | 11337.6466 |


HDC prototype add/subtract on OOD shots runs in **milliseconds** vs **~12 s** to refit the 8-bit logistic head on train+shots. OOD accuracy gains are modest for both; the linear head still ends slightly higher. Forgetting stays < 1 pp for HDC and ~1–2 pp for the refit. This is a **cost** win (Outcome C on update time), not an accuracy win.

## Mapped operating region (Outcome D)

| Regime | What happens |
|---|---|
| Clean channel, 2D 180-beam scan | Binary hashing (or AE) beats pure HDC. HDC ≈ 8-bit PCM. |
| Budget ≫ 188 bytes | Extra bytes do not help 8-bit PCM; HDC larger than the scan is not a compression win. |
| BER 1–10% on the payload | **HDC holds accuracy**; PCM and PCA cliff. Hashing holds most but not all. |
| Few OOD labels | HDC updates are 100–1000× faster; accuracy recovery is small on this shift. |
| Next levers | Region pooling, temporal n-grams, hybrid encoder (Stage 5), real labeled LiDAR. |

## Reproducibility

Configs in `configs/`. Frozen splits in `data/splits/sim_indoor_v1/`. Every JSONL row stores method, budget, BER, seed, and git commit.

