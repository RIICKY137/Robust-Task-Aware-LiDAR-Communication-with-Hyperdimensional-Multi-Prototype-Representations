# Stage 2 remake — k=16 HDC under bitstream noise

Dimension fills the budget: 128 B → `D=1024`, 512 B → `D=4096`. The payload is still **one** hypervector per scan. First-round `noise_sweep.jsonl` / `burst_sweep.jsonl` / `packet_loss_sweep.jsonl` are unchanged.

BER means over seeds:

| split | method_label | budget_bytes | ber | accuracy | macro_f1 |
| --- | --- | --- | --- | --- | --- |
| test_id | binary_hash | 128 | 0.0000 | 0.8638 | 0.7942 |
| test_id | binary_hash | 128 | 0.0100 | 0.8329 | 0.7621 |
| test_id | binary_hash | 128 | 0.0500 | 0.7517 | 0.6642 |
| test_id | binary_hash | 128 | 0.1000 | 0.6802 | 0.5994 |
| test_id | binary_hash | 512 | 0.0000 | 0.9216 | 0.8756 |
| test_id | binary_hash | 512 | 0.0100 | 0.9149 | 0.8706 |
| test_id | binary_hash | 512 | 0.0500 | 0.8837 | 0.8268 |
| test_id | binary_hash | 512 | 0.1000 | 0.8398 | 0.7758 |
| test_id | hdc_k1 | 128 | 0.0000 | 0.7269 | 0.6566 |
| test_id | hdc_k1 | 128 | 0.0100 | 0.7274 | 0.6575 |
| test_id | hdc_k1 | 128 | 0.0500 | 0.7227 | 0.6515 |
| test_id | hdc_k1 | 128 | 0.1000 | 0.7197 | 0.6492 |
| test_id | hdc_k1 | 512 | 0.0000 | 0.7313 | 0.6638 |
| test_id | hdc_k1 | 512 | 0.0100 | 0.7302 | 0.6625 |
| test_id | hdc_k1 | 512 | 0.0500 | 0.7294 | 0.6620 |
| test_id | hdc_k1 | 512 | 0.1000 | 0.7285 | 0.6599 |
| test_id | hdc_k16 | 128 | 0.0000 | 0.9533 | 0.9231 |
| test_id | hdc_k16 | 128 | 0.0100 | 0.9533 | 0.9223 |
| test_id | hdc_k16 | 128 | 0.0500 | 0.9519 | 0.9203 |
| test_id | hdc_k16 | 128 | 0.1000 | 0.9517 | 0.9185 |
| test_id | hdc_k16 | 512 | 0.0000 | 0.9597 | 0.9328 |
| test_id | hdc_k16 | 512 | 0.0100 | 0.9605 | 0.9342 |
| test_id | hdc_k16 | 512 | 0.0500 | 0.9589 | 0.9313 |
| test_id | hdc_k16 | 512 | 0.1000 | 0.9577 | 0.9297 |
| test_id | hdc_linear | 128 | 0.0000 | 0.9453 | 0.9135 |
| test_id | hdc_linear | 128 | 0.0100 | 0.9398 | 0.9068 |
| test_id | hdc_linear | 128 | 0.0500 | 0.9086 | 0.8627 |
| test_id | hdc_linear | 128 | 0.1000 | 0.8608 | 0.8012 |
| test_id | hdc_linear | 512 | 0.0000 | 0.9738 | 0.9547 |
| test_id | hdc_linear | 512 | 0.0100 | 0.9732 | 0.9540 |
| test_id | hdc_linear | 512 | 0.0500 | 0.9680 | 0.9448 |
| test_id | hdc_linear | 512 | 0.1000 | 0.9564 | 0.9285 |
| test_id | quantized | 128 | 0.0000 | 0.7440 | 0.6417 |
| test_id | quantized | 128 | 0.0100 | 0.5907 | 0.5067 |
| test_id | quantized | 128 | 0.0500 | 0.4104 | 0.3631 |
| test_id | quantized | 128 | 0.1000 | 0.3082 | 0.2734 |
| test_id | quantized | 512 | 0.0000 | 0.7473 | 0.6436 |
| test_id | quantized | 512 | 0.0100 | 0.5695 | 0.4940 |
| test_id | quantized | 512 | 0.0500 | 0.3891 | 0.3477 |
| test_id | quantized | 512 | 0.1000 | 0.2949 | 0.2653 |
| test_ood | binary_hash | 128 | 0.0000 | 0.5834 | 0.5158 |
| test_ood | binary_hash | 128 | 0.0100 | 0.5716 | 0.5067 |
| test_ood | binary_hash | 128 | 0.0500 | 0.5367 | 0.4747 |
| test_ood | binary_hash | 128 | 0.1000 | 0.5015 | 0.4543 |
| test_ood | binary_hash | 512 | 0.0000 | 0.6228 | 0.5409 |
| test_ood | binary_hash | 512 | 0.0100 | 0.6153 | 0.5351 |
| test_ood | binary_hash | 512 | 0.0500 | 0.6062 | 0.5322 |
| test_ood | binary_hash | 512 | 0.1000 | 0.5794 | 0.5112 |
| test_ood | hdc_k1 | 128 | 0.0000 | 0.6990 | 0.5919 |
| test_ood | hdc_k1 | 128 | 0.0100 | 0.6976 | 0.5900 |
| test_ood | hdc_k1 | 128 | 0.0500 | 0.6911 | 0.5844 |
| test_ood | hdc_k1 | 128 | 0.1000 | 0.6816 | 0.5765 |
| test_ood | hdc_k1 | 512 | 0.0000 | 0.7114 | 0.6024 |
| test_ood | hdc_k1 | 512 | 0.0100 | 0.7133 | 0.6040 |
| test_ood | hdc_k1 | 512 | 0.0500 | 0.7104 | 0.6012 |
| test_ood | hdc_k1 | 512 | 0.1000 | 0.7062 | 0.5962 |
| test_ood | hdc_k16 | 128 | 0.0000 | 0.8405 | 0.6997 |
| test_ood | hdc_k16 | 128 | 0.0100 | 0.8405 | 0.7008 |
| test_ood | hdc_k16 | 128 | 0.0500 | 0.8374 | 0.6975 |
| test_ood | hdc_k16 | 128 | 0.1000 | 0.8338 | 0.6923 |
| test_ood | hdc_k16 | 512 | 0.0000 | 0.8502 | 0.7069 |
| test_ood | hdc_k16 | 512 | 0.0100 | 0.8508 | 0.7080 |
| test_ood | hdc_k16 | 512 | 0.0500 | 0.8498 | 0.7089 |
| test_ood | hdc_k16 | 512 | 0.1000 | 0.8462 | 0.7040 |
| test_ood | hdc_linear | 128 | 0.0000 | 0.7937 | 0.6375 |
| test_ood | hdc_linear | 128 | 0.0100 | 0.7905 | 0.6365 |
| test_ood | hdc_linear | 128 | 0.0500 | 0.7659 | 0.6140 |
| test_ood | hdc_linear | 128 | 0.1000 | 0.7310 | 0.5870 |
| test_ood | hdc_linear | 512 | 0.0000 | 0.8169 | 0.6604 |
| test_ood | hdc_linear | 512 | 0.0100 | 0.8153 | 0.6582 |
| test_ood | hdc_linear | 512 | 0.0500 | 0.8076 | 0.6486 |
| test_ood | hdc_linear | 512 | 0.1000 | 0.7976 | 0.6413 |
| test_ood | quantized | 128 | 0.0000 | 0.7342 | 0.6016 |
| test_ood | quantized | 128 | 0.0100 | 0.6245 | 0.5113 |
| test_ood | quantized | 128 | 0.0500 | 0.4818 | 0.3893 |
| test_ood | quantized | 128 | 0.1000 | 0.3930 | 0.3048 |
| test_ood | quantized | 512 | 0.0000 | 0.7531 | 0.6096 |
| test_ood | quantized | 512 | 0.0100 | 0.6070 | 0.5027 |
| test_ood | quantized | 512 | 0.0500 | 0.4513 | 0.3745 |
| test_ood | quantized | 512 | 0.1000 | 0.3656 | 0.2902 |


Figures: `results/figures/accuracy_k16_ber_128.png`, `results/figures/accuracy_k16_ber_512.png`, `results/figures/accuracy_k16_ber_128_ood.png`, `results/figures/accuracy_k16_ber_512_ood.png`.

Burst (128 B only, one contiguous flip block, no interleave):

| split | method_label | burst_length | accuracy |
| --- | --- | --- | --- |
| test_id | binary_hash | 128 | 0.6415 |
| test_id | binary_hash | 512 | 0.1878 |
| test_id | hdc_k1 | 128 | 0.7150 |
| test_id | hdc_k1 | 512 | 0.1983 |
| test_id | hdc_k16 | 128 | 0.9508 |
| test_id | hdc_k16 | 512 | 0.1585 |
| test_id | hdc_linear | 128 | 0.8268 |
| test_id | hdc_linear | 512 | 0.1734 |
| test_id | quantized | 128 | 0.4493 |
| test_id | quantized | 512 | 0.1944 |
| test_ood | binary_hash | 128 | 0.4816 |
| test_ood | binary_hash | 512 | 0.2044 |
| test_ood | hdc_k1 | 128 | 0.6785 |
| test_ood | hdc_k1 | 512 | 0.1947 |
| test_ood | hdc_k16 | 128 | 0.8348 |
| test_ood | hdc_k16 | 512 | 0.1908 |
| test_ood | hdc_linear | 128 | 0.7102 |
| test_ood | hdc_linear | 512 | 0.2018 |
| test_ood | quantized | 128 | 0.5200 |
| test_ood | quantized | 512 | 0.2816 |


Figure: `results/figures/accuracy_k16_burst_128.png`.

Packet loss (128 B only, 32-byte packets, zero-fill):

| split | method_label | packet_loss_rate | accuracy |
| --- | --- | --- | --- |
| test_id | binary_hash | 0.0500 | 0.8216 |
| test_id | binary_hash | 0.1000 | 0.7752 |
| test_id | binary_hash | 0.2000 | 0.6824 |
| test_id | hdc_k1 | 0.0500 | 0.7291 |
| test_id | hdc_k1 | 0.1000 | 0.7230 |
| test_id | hdc_k1 | 0.2000 | 0.7167 |
| test_id | hdc_k16 | 0.0500 | 0.9522 |
| test_id | hdc_k16 | 0.1000 | 0.9495 |
| test_id | hdc_k16 | 0.2000 | 0.9459 |
| test_id | hdc_linear | 0.0500 | 0.9196 |
| test_id | hdc_linear | 0.1000 | 0.8917 |
| test_id | hdc_linear | 0.2000 | 0.8310 |
| test_id | quantized | 0.0500 | 0.7078 |
| test_id | quantized | 0.1000 | 0.6529 |
| test_id | quantized | 0.2000 | 0.5631 |
| test_ood | binary_hash | 0.0500 | 0.5598 |
| test_ood | binary_hash | 0.1000 | 0.5334 |
| test_ood | binary_hash | 0.2000 | 0.4879 |
| test_ood | hdc_k1 | 0.0500 | 0.6988 |
| test_ood | hdc_k1 | 0.1000 | 0.6994 |
| test_ood | hdc_k1 | 0.2000 | 0.6903 |
| test_ood | hdc_k16 | 0.0500 | 0.8384 |
| test_ood | hdc_k16 | 0.1000 | 0.8356 |
| test_ood | hdc_k16 | 0.2000 | 0.8252 |
| test_ood | hdc_linear | 0.0500 | 0.7818 |
| test_ood | hdc_linear | 0.1000 | 0.7687 |
| test_ood | hdc_linear | 0.2000 | 0.7259 |
| test_ood | quantized | 0.0500 | 0.7045 |
| test_ood | quantized | 0.1000 | 0.6665 |
| test_ood | quantized | 0.2000 | 0.5897 |


Figure: `results/figures/accuracy_k16_plr_128.png`.

## Reading

- **k=16 stays BER-flat at 128 B.** In-distribution accuracy is ~0.95 from BER 0 to 0.10, matching the 512 B curve. k=1 is also flat, but stuck at ~0.73.
- **The linear head is not holographic at 128 B.** It drops ~0.95 → ~0.86 in-distribution at BER 0.10. At 512 B the same head was almost flat. Hashing at 128 B falls ~0.86 → ~0.68; 8-bit PCM cliffs ~0.74 → ~0.31.
- **Scattered packet loss (32 B packets) is still in the k=16 region.** At PLR 0.20, k=16 stays ~0.95; linear and hashing drop.
- **A 512-bit burst on a 1024-bit code is a failure region for everyone.** Half the hypervector is flipped as one block; accuracy collapses to chance-level. A 128-bit burst does not move k=16.
