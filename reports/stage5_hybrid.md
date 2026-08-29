# Stage 5 — hybrid neural-HDC

`hybrid_hdc:frozen` maps sector statistics through `sign(Rz)` into HDC prototypes. `hybrid_hdc:task` first trains a small MLP on the place labels, freezes the hidden layer, then uses the same HDC head. Binary hashing remains the non-HDC binary control.

| method_label | ber | accuracy | macro_f1 |
| --- | --- | --- | --- |
| autoencoder | 0.0000 | 0.9006 | 0.8460 |
| autoencoder | 0.0100 | 0.4935 | 0.4428 |
| autoencoder | 0.0500 | 0.3170 | 0.2863 |
| autoencoder | 0.1000 | 0.2717 | 0.2413 |
| binary_hash | 0.0000 | 0.9216 | 0.8756 |
| binary_hash | 0.0100 | 0.9149 | 0.8706 |
| binary_hash | 0.0500 | 0.8837 | 0.8268 |
| binary_hash | 0.1000 | 0.8398 | 0.7758 |
| hybrid_hdc:frozen | 0.0000 | 0.7266 | 0.6289 |
| hybrid_hdc:frozen | 0.0100 | 0.7263 | 0.6287 |
| hybrid_hdc:frozen | 0.0500 | 0.7258 | 0.6279 |
| hybrid_hdc:frozen | 0.1000 | 0.7225 | 0.6253 |
| hybrid_hdc:task | 0.0000 | 0.7608 | 0.6647 |
| hybrid_hdc:task | 0.0100 | 0.7622 | 0.6667 |
| hybrid_hdc:task | 0.0500 | 0.7611 | 0.6652 |
| hybrid_hdc:task | 0.1000 | 0.7597 | 0.6624 |
| pure_hdc_D4096 | 0.0000 | 0.7313 | 0.6638 |
| pure_hdc_D4096 | 0.0100 | 0.7302 | 0.6625 |
| pure_hdc_D4096 | 0.0500 | 0.7294 | 0.6620 |
| pure_hdc_D4096 | 0.1000 | 0.7285 | 0.6599 |


Figure: `results/figures/accuracy_hybrid_ber.png`.
