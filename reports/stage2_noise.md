# Stage 2 — bit-error robustness

Fixed 512 bytes/sample budget. Bit flips applied to the serialized payload, not to the classifier output.

| method | ber | accuracy_mean | accuracy_std | macro_f1_mean | macro_f1_std |
| --- | --- | --- | --- | --- | --- |
| binary_hash | 0.0000 | 0.9216 | 0.0058 | 0.8756 | 0.0090 |
| binary_hash | 0.0100 | 0.9149 | 0.0075 | 0.8706 | 0.0084 |
| binary_hash | 0.0500 | 0.8837 | 0.0099 | 0.8268 | 0.0180 |
| binary_hash | 0.1000 | 0.8398 | 0.0038 | 0.7758 | 0.0183 |
| pca | 0.0000 | 0.7548 | 0.0000 | 0.6430 | 0.0000 |
| pca | 0.0100 | 0.3253 | 0.0089 | 0.2887 | 0.0057 |
| pca | 0.0500 | 0.1889 | 0.0155 | 0.1819 | 0.0126 |
| pca | 0.1000 | 0.1668 | 0.0091 | 0.1548 | 0.0095 |
| pure_hdc | 0.0000 | 0.7313 | 0.0017 | 0.6638 | 0.0013 |
| pure_hdc | 0.0100 | 0.7302 | 0.0037 | 0.6625 | 0.0029 |
| pure_hdc | 0.0500 | 0.7294 | 0.0047 | 0.6620 | 0.0051 |
| pure_hdc | 0.1000 | 0.7285 | 0.0017 | 0.6599 | 0.0025 |
| quantized | 0.0000 | 0.7473 | 0.0000 | 0.6436 | 0.0000 |
| quantized | 0.0100 | 0.5695 | 0.0075 | 0.4940 | 0.0092 |
| quantized | 0.0500 | 0.3891 | 0.0118 | 0.3477 | 0.0077 |
| quantized | 0.1000 | 0.2949 | 0.0086 | 0.2653 | 0.0079 |


Figure: `results/figures/accuracy_ber.png`.
