# Stage 3 — sensor corruption and environment shift

These perturbations hit the LiDAR scan **before** encoding. They are not mixed into BER/PLR tables.

In-distribution test (`test_id`), mean over seeds:

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
| hybrid_hdc:task | beam_drop:drop_rate=0.1 | 0.2748 | 0.2193 |
| hybrid_hdc:task | beam_drop:drop_rate=0.3 | 0.1433 | 0.0818 |
| hybrid_hdc:task | clean | 0.7608 | 0.6647 |
| hybrid_hdc:task | clip:clip_to=6.0 | 0.6669 | 0.5768 |
| hybrid_hdc:task | gauss:sigma=0.05 | 0.7575 | 0.6632 |
| hybrid_hdc:task | gauss:sigma=0.15 | 0.7352 | 0.6484 |
| hybrid_hdc:task | range_bias:bias=0.25 | 0.7741 | 0.6731 |
| hybrid_hdc:task | range_scale:scale=1.15 | 0.7517 | 0.6570 |
| hybrid_hdc:task | sector_drop:fraction=0.15 | 0.4753 | 0.3617 |
| hybrid_hdc:task | sector_drop:fraction=0.3 | 0.3101 | 0.1789 |
| pca | beam_drop:drop_rate=0.1 | 0.3670 | 0.3225 |
| pca | beam_drop:drop_rate=0.3 | 0.2709 | 0.2277 |
| pca | clean | 0.7548 | 0.6430 |
| pca | clip:clip_to=6.0 | 0.6355 | 0.5523 |
| pca | gauss:sigma=0.05 | 0.7531 | 0.6417 |
| pca | gauss:sigma=0.15 | 0.7305 | 0.6246 |
| pca | range_bias:bias=0.25 | 0.7523 | 0.6395 |
| pca | range_scale:scale=1.15 | 0.7357 | 0.6250 |
| pca | sector_drop:fraction=0.15 | 0.4236 | 0.3346 |
| pca | sector_drop:fraction=0.3 | 0.3173 | 0.2168 |
| pure_hdc_D4096 | beam_drop:drop_rate=0.1 | 0.6703 | 0.6224 |
| pure_hdc_D4096 | beam_drop:drop_rate=0.3 | 0.4836 | 0.3576 |
| pure_hdc_D4096 | clean | 0.7313 | 0.6638 |
| pure_hdc_D4096 | clip:clip_to=6.0 | 0.6518 | 0.5753 |
| pure_hdc_D4096 | gauss:sigma=0.05 | 0.7316 | 0.6638 |
| pure_hdc_D4096 | gauss:sigma=0.15 | 0.7277 | 0.6604 |
| pure_hdc_D4096 | range_bias:bias=0.25 | 0.7354 | 0.6579 |
| pure_hdc_D4096 | range_scale:scale=1.15 | 0.7028 | 0.6327 |
| pure_hdc_D4096 | sector_drop:fraction=0.15 | 0.5753 | 0.5092 |
| pure_hdc_D4096 | sector_drop:fraction=0.3 | 0.4410 | 0.3066 |
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


OOD (`test_ood`) is the held-out floorplan with the same corruptions. See `results/tables/sensor_shift.csv`.
