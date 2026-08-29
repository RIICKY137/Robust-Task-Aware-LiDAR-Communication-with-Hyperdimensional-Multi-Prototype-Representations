# Multi-centroid HDC

The transmitted payload is still one bipolar hypervector per scan (`P_i ⊗ L_Q(r_i)` bundled). What changes is the receiver: k-means on the training hypervectors of each class, then nearest-centroid cosine. `k=1` is the original class-wide sum. The linear head is the same logistic classifier used with hashing, trained on the same codes.

| split | method_label | ber | accuracy | macro_f1 |
| --- | --- | --- | --- | --- |
| test_id | binary_hash | 0.0000 | 0.9216 | 0.8756 |
| test_id | binary_hash | 0.0100 | 0.9149 | 0.8706 |
| test_id | binary_hash | 0.0500 | 0.8837 | 0.8268 |
| test_id | binary_hash | 0.1000 | 0.8398 | 0.7758 |
| test_id | pure_hdc_D4096 | 0.0000 | 0.7313 | 0.6638 |
| test_id | pure_hdc_D4096 | 0.0100 | 0.7302 | 0.6625 |
| test_id | pure_hdc_D4096 | 0.0500 | 0.7294 | 0.6620 |
| test_id | pure_hdc_D4096 | 0.1000 | 0.7285 | 0.6599 |
| test_id | pure_hdc_D4096+lin | 0.0000 | 0.9738 | 0.9547 |
| test_id | pure_hdc_D4096+lin | 0.0100 | 0.9732 | 0.9540 |
| test_id | pure_hdc_D4096+lin | 0.0500 | 0.9680 | 0.9448 |
| test_id | pure_hdc_D4096+lin | 0.1000 | 0.9564 | 0.9285 |
| test_id | pure_hdc_D4096/k16 | 0.0000 | 0.9597 | 0.9328 |
| test_id | pure_hdc_D4096/k16 | 0.0100 | 0.9605 | 0.9342 |
| test_id | pure_hdc_D4096/k16 | 0.0500 | 0.9589 | 0.9313 |
| test_id | pure_hdc_D4096/k16 | 0.1000 | 0.9577 | 0.9297 |
| test_id | pure_hdc_D4096/k4 | 0.0000 | 0.8691 | 0.8164 |
| test_id | pure_hdc_D4096/k4 | 0.0100 | 0.8688 | 0.8155 |
| test_id | pure_hdc_D4096/k4 | 0.0500 | 0.8716 | 0.8206 |
| test_id | pure_hdc_D4096/k4 | 0.1000 | 0.8719 | 0.8206 |
| test_id | pure_hdc_D4096/k8 | 0.0000 | 0.9171 | 0.8688 |
| test_id | pure_hdc_D4096/k8 | 0.0100 | 0.9180 | 0.8706 |
| test_id | pure_hdc_D4096/k8 | 0.0500 | 0.9185 | 0.8713 |
| test_id | pure_hdc_D4096/k8 | 0.1000 | 0.9155 | 0.8666 |
| test_ood | binary_hash | 0.0000 | 0.6228 | 0.5409 |
| test_ood | binary_hash | 0.0100 | 0.6153 | 0.5351 |
| test_ood | binary_hash | 0.0500 | 0.6062 | 0.5322 |
| test_ood | binary_hash | 0.1000 | 0.5794 | 0.5112 |
| test_ood | pure_hdc_D4096 | 0.0000 | 0.7114 | 0.6024 |
| test_ood | pure_hdc_D4096 | 0.0100 | 0.7133 | 0.6040 |
| test_ood | pure_hdc_D4096 | 0.0500 | 0.7104 | 0.6012 |
| test_ood | pure_hdc_D4096 | 0.1000 | 0.7062 | 0.5962 |
| test_ood | pure_hdc_D4096+lin | 0.0000 | 0.8169 | 0.6604 |
| test_ood | pure_hdc_D4096+lin | 0.0100 | 0.8153 | 0.6582 |
| test_ood | pure_hdc_D4096+lin | 0.0500 | 0.8076 | 0.6486 |
| test_ood | pure_hdc_D4096+lin | 0.1000 | 0.7976 | 0.6413 |
| test_ood | pure_hdc_D4096/k16 | 0.0000 | 0.8502 | 0.7069 |
| test_ood | pure_hdc_D4096/k16 | 0.0100 | 0.8508 | 0.7080 |
| test_ood | pure_hdc_D4096/k16 | 0.0500 | 0.8498 | 0.7089 |
| test_ood | pure_hdc_D4096/k16 | 0.1000 | 0.8462 | 0.7040 |
| test_ood | pure_hdc_D4096/k4 | 0.0000 | 0.7746 | 0.6470 |
| test_ood | pure_hdc_D4096/k4 | 0.0100 | 0.7726 | 0.6451 |
| test_ood | pure_hdc_D4096/k4 | 0.0500 | 0.7744 | 0.6496 |
| test_ood | pure_hdc_D4096/k4 | 0.1000 | 0.7683 | 0.6426 |
| test_ood | pure_hdc_D4096/k8 | 0.0000 | 0.8167 | 0.6847 |
| test_ood | pure_hdc_D4096/k8 | 0.0100 | 0.8153 | 0.6852 |
| test_ood | pure_hdc_D4096/k8 | 0.0500 | 0.8185 | 0.6899 |
| test_ood | pure_hdc_D4096/k8 | 0.1000 | 0.8167 | 0.6854 |


Figure: `results/figures/accuracy_multicentroid_ber.png` (in-distribution).

Reading: if raising k lifts in-distribution accuracy toward the linear head while staying BER-flat, the 0.73 ceiling was unimodal prototypes, not a weak code. OOD (`test_ood`) is the check that extra centroids did not just memorize the training building. Few-shot updates still add to the nearest centroid.
