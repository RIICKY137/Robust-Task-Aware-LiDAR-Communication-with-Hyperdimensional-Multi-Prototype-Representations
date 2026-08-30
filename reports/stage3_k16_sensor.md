# Stage 3 remake — k=16 HDC under sensor dropout

Corruptions hit the LiDAR scan **before** encoding. Budget 512 bytes, `D=4096`, BER = 0. Compared with k=1 prototypes, a linear head, hashing, and 8-bit PCM. First-round `sensor_shift.jsonl` is left unchanged.

In-distribution (`test_id`), mean over seeds:

| method_label | sensor | accuracy | macro_f1 |
| --- | --- | --- | --- |
| binary_hash | beam_drop:drop_rate=0.1 | 0.5035 | 0.4456 |
| binary_hash | beam_drop:drop_rate=0.3 | 0.2262 | 0.2167 |
| binary_hash | clean | 0.9216 | 0.8756 |
| binary_hash | clip:clip_to=6.0 | 0.8266 | 0.7725 |
| binary_hash | gauss:sigma=0.05 | 0.9207 | 0.8739 |
| binary_hash | gauss:sigma=0.15 | 0.9133 | 0.8658 |
| binary_hash | range_bias:bias=0.25 | 0.9102 | 0.8622 |
| binary_hash | range_scale:scale=1.15 | 0.9133 | 0.8677 |
| binary_hash | sector_drop:fraction=0.15 | 0.3933 | 0.3384 |
| binary_hash | sector_drop:fraction=0.3 | 0.2737 | 0.2286 |
| hdc_k1 | beam_drop:drop_rate=0.1 | 0.6703 | 0.6224 |
| hdc_k1 | beam_drop:drop_rate=0.3 | 0.4836 | 0.3576 |
| hdc_k1 | clean | 0.7313 | 0.6638 |
| hdc_k1 | clip:clip_to=6.0 | 0.6518 | 0.5753 |
| hdc_k1 | gauss:sigma=0.05 | 0.7316 | 0.6638 |
| hdc_k1 | gauss:sigma=0.15 | 0.7277 | 0.6604 |
| hdc_k1 | range_bias:bias=0.25 | 0.7354 | 0.6579 |
| hdc_k1 | range_scale:scale=1.15 | 0.7028 | 0.6327 |
| hdc_k1 | sector_drop:fraction=0.15 | 0.5753 | 0.5092 |
| hdc_k1 | sector_drop:fraction=0.3 | 0.4410 | 0.3066 |
| hdc_k16 | beam_drop:drop_rate=0.1 | 0.9437 | 0.9137 |
| hdc_k16 | beam_drop:drop_rate=0.3 | 0.8028 | 0.7406 |
| hdc_k16 | clean | 0.9597 | 0.9328 |
| hdc_k16 | clip:clip_to=6.0 | 0.8793 | 0.8449 |
| hdc_k16 | gauss:sigma=0.05 | 0.9575 | 0.9303 |
| hdc_k16 | gauss:sigma=0.15 | 0.9555 | 0.9268 |
| hdc_k16 | range_bias:bias=0.25 | 0.9506 | 0.9167 |
| hdc_k16 | range_scale:scale=1.15 | 0.9478 | 0.9160 |
| hdc_k16 | sector_drop:fraction=0.15 | 0.7926 | 0.7194 |
| hdc_k16 | sector_drop:fraction=0.3 | 0.3869 | 0.3058 |
| hdc_linear | beam_drop:drop_rate=0.1 | 0.7523 | 0.6912 |
| hdc_linear | beam_drop:drop_rate=0.3 | 0.5255 | 0.3739 |
| hdc_linear | clean | 0.9738 | 0.9547 |
| hdc_linear | clip:clip_to=6.0 | 0.5352 | 0.5035 |
| hdc_linear | gauss:sigma=0.05 | 0.9757 | 0.9584 |
| hdc_linear | gauss:sigma=0.15 | 0.9688 | 0.9457 |
| hdc_linear | range_bias:bias=0.25 | 0.9417 | 0.9025 |
| hdc_linear | range_scale:scale=1.15 | 0.8854 | 0.8477 |
| hdc_linear | sector_drop:fraction=0.15 | 0.5929 | 0.4638 |
| hdc_linear | sector_drop:fraction=0.3 | 0.4584 | 0.3271 |
| quantized | beam_drop:drop_rate=0.1 | 0.3314 | 0.3005 |
| quantized | beam_drop:drop_rate=0.3 | 0.2579 | 0.2257 |
| quantized | clean | 0.7473 | 0.6436 |
| quantized | clip:clip_to=6.0 | 0.6429 | 0.5568 |
| quantized | gauss:sigma=0.05 | 0.7404 | 0.6361 |
| quantized | gauss:sigma=0.15 | 0.7097 | 0.6085 |
| quantized | range_bias:bias=0.25 | 0.7589 | 0.6516 |
| quantized | range_scale:scale=1.15 | 0.7440 | 0.6389 |
| quantized | sector_drop:fraction=0.15 | 0.4228 | 0.3426 |
| quantized | sector_drop:fraction=0.3 | 0.3195 | 0.2224 |


Figures: `results/figures/accuracy_k16_beam_drop.png`, `results/figures/accuracy_k16_sector_drop.png`.

OOD (`test_ood`), mean over seeds:

| method_label | sensor | accuracy | macro_f1 |
| --- | --- | --- | --- |
| binary_hash | beam_drop:drop_rate=0.1 | 0.4357 | 0.4289 |
| binary_hash | beam_drop:drop_rate=0.3 | 0.2534 | 0.2634 |
| binary_hash | clean | 0.6228 | 0.5409 |
| binary_hash | clip:clip_to=6.0 | 0.5300 | 0.4897 |
| binary_hash | gauss:sigma=0.05 | 0.6235 | 0.5420 |
| binary_hash | gauss:sigma=0.15 | 0.6202 | 0.5409 |
| binary_hash | range_bias:bias=0.25 | 0.6171 | 0.5418 |
| binary_hash | range_scale:scale=1.15 | 0.6013 | 0.5281 |
| binary_hash | sector_drop:fraction=0.15 | 0.3739 | 0.3465 |
| binary_hash | sector_drop:fraction=0.3 | 0.3095 | 0.2655 |
| hdc_k1 | beam_drop:drop_rate=0.1 | 0.5375 | 0.4098 |
| hdc_k1 | beam_drop:drop_rate=0.3 | 0.5426 | 0.3582 |
| hdc_k1 | clean | 0.7114 | 0.6024 |
| hdc_k1 | clip:clip_to=6.0 | 0.6261 | 0.5480 |
| hdc_k1 | gauss:sigma=0.05 | 0.7084 | 0.6010 |
| hdc_k1 | gauss:sigma=0.15 | 0.7021 | 0.5959 |
| hdc_k1 | range_bias:bias=0.25 | 0.6820 | 0.5658 |
| hdc_k1 | range_scale:scale=1.15 | 0.5838 | 0.4803 |
| hdc_k1 | sector_drop:fraction=0.15 | 0.5166 | 0.3586 |
| hdc_k1 | sector_drop:fraction=0.3 | 0.5066 | 0.3065 |
| hdc_k16 | beam_drop:drop_rate=0.1 | 0.6976 | 0.5610 |
| hdc_k16 | beam_drop:drop_rate=0.3 | 0.5901 | 0.4193 |
| hdc_k16 | clean | 0.8502 | 0.7069 |
| hdc_k16 | clip:clip_to=6.0 | 0.7058 | 0.6116 |
| hdc_k16 | gauss:sigma=0.05 | 0.8474 | 0.7042 |
| hdc_k16 | gauss:sigma=0.15 | 0.8488 | 0.7051 |
| hdc_k16 | range_bias:bias=0.25 | 0.7671 | 0.6316 |
| hdc_k16 | range_scale:scale=1.15 | 0.6814 | 0.5635 |
| hdc_k16 | sector_drop:fraction=0.15 | 0.5724 | 0.4008 |
| hdc_k16 | sector_drop:fraction=0.3 | 0.4373 | 0.1926 |
| hdc_linear | beam_drop:drop_rate=0.1 | 0.6037 | 0.4270 |
| hdc_linear | beam_drop:drop_rate=0.3 | 0.5286 | 0.3235 |
| hdc_linear | clean | 0.8169 | 0.6604 |
| hdc_linear | clip:clip_to=6.0 | 0.5279 | 0.4186 |
| hdc_linear | gauss:sigma=0.05 | 0.8122 | 0.6545 |
| hdc_linear | gauss:sigma=0.15 | 0.8114 | 0.6553 |
| hdc_linear | range_bias:bias=0.25 | 0.7994 | 0.6295 |
| hdc_linear | range_scale:scale=1.15 | 0.7413 | 0.5959 |
| hdc_linear | sector_drop:fraction=0.15 | 0.5393 | 0.3318 |
| hdc_linear | sector_drop:fraction=0.3 | 0.4987 | 0.2779 |
| quantized | beam_drop:drop_rate=0.1 | 0.4007 | 0.3209 |
| quantized | beam_drop:drop_rate=0.3 | 0.3347 | 0.2302 |
| quantized | clean | 0.7531 | 0.6096 |
| quantized | clip:clip_to=6.0 | 0.6545 | 0.5563 |
| quantized | gauss:sigma=0.05 | 0.7405 | 0.6007 |
| quantized | gauss:sigma=0.15 | 0.7202 | 0.5887 |
| quantized | range_bias:bias=0.25 | 0.6958 | 0.5599 |
| quantized | range_scale:scale=1.15 | 0.6450 | 0.5173 |
| quantized | sector_drop:fraction=0.15 | 0.5214 | 0.3555 |
| quantized | sector_drop:fraction=0.3 | 0.4721 | 0.2629 |


## Reading

- **Scattered beam dropout is the k=16 operating region.** At 10% random beam drop, in-distribution k=16 stays near clean (~0.94) while hashing falls to ~0.50 and the linear head to ~0.75. At 30% it is still ~0.80 vs ~0.23 hashing / ~0.53 linear.
- **Contiguous sector drop is a failure region.** 15% sector drop: k=16 ~0.79 vs linear ~0.59 vs hashing ~0.39. At 30% (~54 adjacent beams) k=16 collapses to ~0.39, no better than k=1.
- Mild range noise / bias barely moves k=16. Range clip to 6 m hurts the linear head more than nearest-centroid (~0.54 vs ~0.88 in-distribution).
