# Stage 1 remake — k=16 HDC vs bandwidth

Clean channel (BER = 0). Dimension fills the budget (`D = 8 × bytes`): 128 B → 1024, 512 B → 4096, 2048 B → 16384. The payload is still **one** hypervector per scan; `k` is the number of centroids at the receiver. First-round `bandwidth_sweep.jsonl` is left unchanged.

Means over seeds:

| split | method_label | budget_bytes | accuracy | macro_f1 | actual_bytes |
| --- | --- | --- | --- | --- | --- |
| test_id | binary_hash | 128 | 0.8638 | 0.7942 | 128.0000 |
| test_id | binary_hash | 512 | 0.9216 | 0.8756 | 512.0000 |
| test_id | binary_hash | 2048 | 0.9431 | 0.9075 | 2048.0000 |
| test_id | hdc_k1 | 128 | 0.7269 | 0.6566 | 128.0000 |
| test_id | hdc_k1 | 512 | 0.7313 | 0.6638 | 512.0000 |
| test_id | hdc_k1 | 2048 | 0.7352 | 0.6690 | 2048.0000 |
| test_id | hdc_k16 | 128 | 0.9533 | 0.9231 | 128.0000 |
| test_id | hdc_k16 | 512 | 0.9597 | 0.9328 | 512.0000 |
| test_id | hdc_k16 | 2048 | 0.9569 | 0.9290 | 2048.0000 |
| test_id | hdc_linear | 128 | 0.9453 | 0.9135 | 128.0000 |
| test_id | hdc_linear | 512 | 0.9738 | 0.9547 | 512.0000 |
| test_id | hdc_linear | 2048 | 0.9779 | 0.9614 | 2048.0000 |
| test_id | quantized | 128 | 0.7440 | 0.6417 | 128.0000 |
| test_id | quantized | 512 | 0.7473 | 0.6436 | 188.0000 |
| test_id | quantized | 2048 | 0.7473 | 0.6436 | 188.0000 |
| test_ood | binary_hash | 128 | 0.5834 | 0.5158 | 128.0000 |
| test_ood | binary_hash | 512 | 0.6228 | 0.5409 | 512.0000 |
| test_ood | binary_hash | 2048 | 0.6277 | 0.5545 | 2048.0000 |
| test_ood | hdc_k1 | 128 | 0.6990 | 0.5919 | 128.0000 |
| test_ood | hdc_k1 | 512 | 0.7114 | 0.6024 | 512.0000 |
| test_ood | hdc_k1 | 2048 | 0.7118 | 0.6015 | 2048.0000 |
| test_ood | hdc_k16 | 128 | 0.8405 | 0.6997 | 128.0000 |
| test_ood | hdc_k16 | 512 | 0.8502 | 0.7069 | 512.0000 |
| test_ood | hdc_k16 | 2048 | 0.8531 | 0.7171 | 2048.0000 |
| test_ood | hdc_linear | 128 | 0.7937 | 0.6375 | 128.0000 |
| test_ood | hdc_linear | 512 | 0.8169 | 0.6604 | 512.0000 |
| test_ood | hdc_linear | 2048 | 0.8191 | 0.6629 | 2048.0000 |
| test_ood | quantized | 128 | 0.7342 | 0.6016 | 128.0000 |
| test_ood | quantized | 512 | 0.7531 | 0.6096 | 188.0000 |
| test_ood | quantized | 2048 | 0.7531 | 0.6096 | 188.0000 |


Figures: `results/figures/accuracy_k16_bandwidth.png`, `results/figures/accuracy_k16_bandwidth_ood.png`.

## Reading

- **k=1 is still not a compressor.** Accuracy stays ~0.73 in-distribution at every budget.
- **k=16 saturates early.** At 128 B (`D=1024`) it is already ~0.95 in-distribution, matching hashing at 2048 B, and ~0.84 OOD (hashing stays ~0.58–0.63).
- Extra bytes help the **linear** head in-distribution (0.95 → 0.98) more than k=16. k=16 stays ahead of linear on OOD at every budget.
- 8-bit PCM saturates at 188 B and does not use the extra budget.
