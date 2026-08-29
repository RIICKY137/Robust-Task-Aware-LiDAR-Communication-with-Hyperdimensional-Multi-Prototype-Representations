# LiDAR hybrid HDC — full scan, record bundle, linear vs prototype

Stage 5 used 16-sector summaries, so the neural-HDC hybrid never saw the same geometry as binary hashing. This follow-up uses 2D LiDAR features (normalized range + circular derivative), optionally bundled with record-based `P_i ⊗ L_Q(r_i)`, and compares HDC prototypes against the same logistic head hashing uses.

| method_label | ber | accuracy | macro_f1 |
| --- | --- | --- | --- |
| binary_hash | 0.0000 | 0.9216 | 0.8756 |
| binary_hash | 0.0100 | 0.9149 | 0.8706 |
| binary_hash | 0.0500 | 0.8837 | 0.8268 |
| binary_hash | 0.1000 | 0.8398 | 0.7758 |
| hybrid_hdc:task/scan/linear/none | 0.0000 | 0.9307 | 0.8854 |
| hybrid_hdc:task/scan/linear/none | 0.0100 | 0.9315 | 0.8867 |
| hybrid_hdc:task/scan/linear/none | 0.0500 | 0.9276 | 0.8811 |
| hybrid_hdc:task/scan/linear/none | 0.1000 | 0.9241 | 0.8764 |
| hybrid_hdc:task/scan/linear/record | 0.0000 | 0.9489 | 0.9134 |
| hybrid_hdc:task/scan/linear/record | 0.0100 | 0.9475 | 0.9123 |
| hybrid_hdc:task/scan/linear/record | 0.0500 | 0.9428 | 0.9044 |
| hybrid_hdc:task/scan/linear/record | 0.1000 | 0.9450 | 0.9093 |
| hybrid_hdc:task/scan/prototype/none | 0.0000 | 0.7415 | 0.6309 |
| hybrid_hdc:task/scan/prototype/none | 0.0100 | 0.7415 | 0.6307 |
| hybrid_hdc:task/scan/prototype/none | 0.0500 | 0.7429 | 0.6328 |
| hybrid_hdc:task/scan/prototype/none | 0.1000 | 0.7421 | 0.6310 |
| hybrid_hdc:task/scan/prototype/record | 0.0000 | 0.7440 | 0.6478 |
| hybrid_hdc:task/scan/prototype/record | 0.0100 | 0.7451 | 0.6491 |
| hybrid_hdc:task/scan/prototype/record | 0.0500 | 0.7437 | 0.6473 |
| hybrid_hdc:task/scan/prototype/record | 0.1000 | 0.7443 | 0.6489 |
| hybrid_hdc:task/sector/prototype/none | 0.0000 | 0.7827 | 0.6927 |
| hybrid_hdc:task/sector/prototype/none | 0.0100 | 0.7810 | 0.6908 |
| hybrid_hdc:task/sector/prototype/none | 0.0500 | 0.7813 | 0.6916 |
| hybrid_hdc:task/sector/prototype/none | 0.1000 | 0.7791 | 0.6888 |
| pure_hdc_D4096 | 0.0000 | 0.7313 | 0.6638 |
| pure_hdc_D4096 | 0.0100 | 0.7302 | 0.6625 |
| pure_hdc_D4096 | 0.0500 | 0.7294 | 0.6620 |
| pure_hdc_D4096 | 0.1000 | 0.7285 | 0.6599 |
| pure_hdc_D4096+lin | 0.0000 | 0.9738 | 0.9547 |
| pure_hdc_D4096+lin | 0.0100 | 0.9732 | 0.9540 |
| pure_hdc_D4096+lin | 0.0500 | 0.9680 | 0.9448 |
| pure_hdc_D4096+lin | 0.1000 | 0.9564 | 0.9285 |


Figure: `results/figures/accuracy_hybrid_lidar_ber.png`.

Reading: if the linear head on record-based HDC matches or beats hashing, the hashing gap was the prototype classifier, not missing geometry in `P⊗L`. If prototypes stay near 0.73 while the linear head jumps, Outcome B (BER-flat binary codes) can coexist with a strong task head — the operating region is then 'HDC payload + trained head', not 'HDC prototypes everywhere'.
