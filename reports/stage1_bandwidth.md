# Stage 1 — bandwidth vs task accuracy

Clean channel (BER = 0). Means over seeds. HDC item memory is pre-shared and not counted in per-sample bytes.

| method | budget_bytes | accuracy | macro_f1 | actual_bytes |
| --- | --- | --- | --- | --- |
| binary_hash | 128 | 0.8638 | 0.7942 | 128.0000 |
| binary_hash | 512 | 0.9216 | 0.8756 | 512.0000 |
| binary_hash | 2048 | 0.9431 | 0.9075 | 2048.0000 |
| pca | 128 | 0.7432 | 0.6481 | 128.0000 |
| pca | 512 | 0.7548 | 0.6430 | 512.0000 |
| pca | 2048 | 0.7490 | 0.6451 | 728.0000 |
| pure_hdc | 128 | 0.7269 | 0.6566 | 128.0000 |
| pure_hdc | 512 | 0.7291 | 0.6602 | 320.0000 |
| pure_hdc | 2048 | 0.7309 | 0.6628 | 554.6667 |
| quantized | 128 | 0.7440 | 0.6417 | 128.0000 |
| quantized | 512 | 0.7473 | 0.6436 | 188.0000 |
| quantized | 2048 | 0.7473 | 0.6436 | 188.0000 |


Figures: `results/figures/accuracy_bandwidth.png`, `results/figures/macrof1_bandwidth.png`.
