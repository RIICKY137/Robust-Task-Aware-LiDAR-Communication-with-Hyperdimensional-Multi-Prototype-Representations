# Stage 2 — communication robustness

Noise is applied to the serialized payload. Receiver uses a pre-agreed layout; dropped packets are filled with zeros.

## Random bit flips

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

## Burst errors

| method | burst_length | interleave | accuracy_mean | accuracy_std |
| --- | --- | --- | --- | --- |
| binary_hash | 0 | False | 0.9223 | 0.0047 |
| binary_hash | 32 | False | 0.9143 | 0.0041 |
| binary_hash | 32 | True | 0.9155 | 0.0032 |
| binary_hash | 128 | False | 0.8968 | 0.0098 |
| binary_hash | 128 | True | 0.8994 | 0.0097 |
| binary_hash | 512 | False | 0.8089 | 0.0145 |
| binary_hash | 512 | True | 0.8136 | 0.0204 |
| binary_hash | 1024 | False | 0.6759 | 0.0233 |
| binary_hash | 1024 | True | 0.6747 | 0.0247 |
| pca | 0 | False | 0.7548 | 0.0000 |
| pca | 32 | False | 0.3210 | 0.0076 |
| pca | 32 | True | 0.3649 | 0.0294 |
| pca | 128 | False | 0.2394 | 0.0111 |
| pca | 128 | True | 0.2066 | 0.0079 |
| pca | 512 | False | 0.1920 | 0.0059 |
| pca | 512 | True | 0.1672 | 0.0125 |
| pca | 1024 | False | 0.1879 | 0.0114 |
| pca | 1024 | True | 0.1541 | 0.0204 |
| pure_hdc | 0 | False | 0.7304 | 0.0039 |
| pure_hdc | 32 | False | 0.7301 | 0.0036 |
| pure_hdc | 32 | True | 0.7311 | 0.0058 |
| pure_hdc | 128 | False | 0.7299 | 0.0045 |
| pure_hdc | 128 | True | 0.7301 | 0.0041 |
| pure_hdc | 512 | False | 0.7279 | 0.0033 |
| pure_hdc | 512 | True | 0.7291 | 0.0037 |
| pure_hdc | 1024 | False | 0.7261 | 0.0036 |
| pure_hdc | 1024 | True | 0.7241 | 0.0062 |
| quantized | 0 | False | 0.7473 | 0.0000 |
| quantized | 32 | False | 0.6073 | 0.0135 |
| quantized | 32 | True | 0.4853 | 0.0084 |
| quantized | 128 | False | 0.5024 | 0.0117 |
| quantized | 128 | True | 0.2969 | 0.0152 |
| quantized | 512 | False | 0.2441 | 0.0109 |
| quantized | 512 | True | 0.1723 | 0.0183 |
| quantized | 1024 | False | 0.2023 | 0.0094 |
| quantized | 1024 | True | 0.1466 | 0.0405 |

Figure: `results/figures/accuracy_burst.png`. Interleaving permutes bits with a shared seed before the burst, then inverts the permutation at the receiver.

## Packet loss

| method | packet_loss_rate | accuracy_mean | accuracy_std | macro_f1_mean | macro_f1_std |
| --- | --- | --- | --- | --- | --- |
| binary_hash | 0.0000 | 0.9223 | 0.0047 | 0.8795 | 0.0083 |
| binary_hash | 0.0100 | 0.9201 | 0.0042 | 0.8759 | 0.0073 |
| binary_hash | 0.0500 | 0.9012 | 0.0057 | 0.8545 | 0.0130 |
| binary_hash | 0.1000 | 0.8840 | 0.0065 | 0.8338 | 0.0111 |
| binary_hash | 0.2000 | 0.8330 | 0.0055 | 0.7699 | 0.0093 |
| binary_hash | 0.4000 | 0.7359 | 0.0236 | 0.6547 | 0.0189 |
| pca | 0.0000 | 0.7548 | 0.0000 | 0.6430 | 0.0000 |
| pca | 0.0100 | 0.7488 | 0.0034 | 0.6385 | 0.0038 |
| pca | 0.0500 | 0.7195 | 0.0062 | 0.6147 | 0.0036 |
| pca | 0.1000 | 0.6882 | 0.0110 | 0.5911 | 0.0076 |
| pca | 0.2000 | 0.6285 | 0.0103 | 0.5449 | 0.0084 |
| pca | 0.4000 | 0.5128 | 0.0084 | 0.4586 | 0.0085 |
| pure_hdc | 0.0000 | 0.7304 | 0.0039 | 0.6636 | 0.0033 |
| pure_hdc | 0.0100 | 0.7299 | 0.0039 | 0.6632 | 0.0032 |
| pure_hdc | 0.0500 | 0.7312 | 0.0041 | 0.6647 | 0.0039 |
| pure_hdc | 0.1000 | 0.7289 | 0.0064 | 0.6608 | 0.0068 |
| pure_hdc | 0.2000 | 0.7271 | 0.0066 | 0.6578 | 0.0062 |
| pure_hdc | 0.4000 | 0.7251 | 0.0097 | 0.6498 | 0.0088 |
| quantized | 0.0000 | 0.7473 | 0.0000 | 0.6436 | 0.0000 |
| quantized | 0.0100 | 0.7417 | 0.0021 | 0.6390 | 0.0033 |
| quantized | 0.0500 | 0.7082 | 0.0029 | 0.6108 | 0.0040 |
| quantized | 0.1000 | 0.6620 | 0.0127 | 0.5722 | 0.0117 |
| quantized | 0.2000 | 0.5857 | 0.0146 | 0.5129 | 0.0150 |
| quantized | 0.4000 | 0.4224 | 0.0090 | 0.3828 | 0.0133 |

Figure: `results/figures/accuracy_packet_loss.png`.

## Packet loss + bit interleaving

| method | packet_loss_rate | interleave | accuracy_mean | accuracy_std |
| --- | --- | --- | --- | --- |
| binary_hash | 0.0000 | False | 0.9216 | 0.0058 |
| binary_hash | 0.1000 | False | 0.8868 | 0.0070 |
| binary_hash | 0.1000 | True | 0.8835 | 0.0083 |
| binary_hash | 0.2000 | False | 0.8337 | 0.0069 |
| binary_hash | 0.2000 | True | 0.8484 | 0.0147 |
| binary_hash | 0.4000 | False | 0.7412 | 0.0213 |
| binary_hash | 0.4000 | True | 0.7633 | 0.0229 |
| pca | 0.0000 | False | 0.7548 | 0.0000 |
| pca | 0.1000 | False | 0.6849 | 0.0124 |
| pca | 0.1000 | True | 0.5998 | 0.0185 |
| pca | 0.2000 | False | 0.6239 | 0.0057 |
| pca | 0.2000 | True | 0.4844 | 0.0199 |
| pca | 0.4000 | False | 0.5090 | 0.0091 |
| pca | 0.4000 | True | 0.3005 | 0.0161 |
| pure_hdc | 0.0000 | False | 0.7313 | 0.0017 |
| pure_hdc | 0.1000 | False | 0.7324 | 0.0029 |
| pure_hdc | 0.1000 | True | 0.7299 | 0.0014 |
| pure_hdc | 0.2000 | False | 0.7296 | 0.0053 |
| pure_hdc | 0.2000 | True | 0.7291 | 0.0038 |
| pure_hdc | 0.4000 | False | 0.7280 | 0.0110 |
| pure_hdc | 0.4000 | True | 0.7305 | 0.0093 |
| quantized | 0.0000 | False | 0.7473 | 0.0000 |
| quantized | 0.1000 | False | 0.6647 | 0.0085 |
| quantized | 0.1000 | True | 0.5438 | 0.0211 |
| quantized | 0.2000 | False | 0.5866 | 0.0155 |
| quantized | 0.2000 | True | 0.4115 | 0.0440 |
| quantized | 0.4000 | False | 0.4217 | 0.0050 |
| quantized | 0.4000 | True | 0.2389 | 0.0481 |

Figure: `results/figures/accuracy_packet_interleave.png`. Bits are permuted with a shared seed, packets are dropped, then the permutation is inverted. A lost packet therefore punches scattered holes instead of one contiguous zero block.
