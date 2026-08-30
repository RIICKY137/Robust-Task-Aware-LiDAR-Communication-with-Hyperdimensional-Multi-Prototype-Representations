# Stage 3 remake — LidarDataFrames sensor dropout at 128 B

Author-labeled RPLiDAR frames. Corruptions hit the scan **before** encoding (BER = 0). Budget 128 bytes, `D=1024`. k=16 skip / DROP / fill vs k=1 skip, linear skip, hashing, and 8-bit PCM. Sim `k16_sensor.jsonl` and `k16_sector_encode.jsonl` are unchanged.

`test_ood` is an i.i.d. holdout, not a floorplan shift. Dropout and range scale do not need a building id; Stage 4 few-shot-after-shift is still blocked on this corpus (holdout N≈80 cannot run 50/100 shots per class).

Means over seeds:

| split | method_label | sensor | accuracy | macro_f1 |
| --- | --- | --- | --- | --- |
| test_id | binary_hash | beam_drop:drop_rate=0.1 | 0.5221 | 0.4779 |
| test_id | binary_hash | beam_drop:drop_rate=0.3 | 0.4498 | 0.3897 |
| test_id | binary_hash | clean | 0.8594 | 0.8575 |
| test_id | binary_hash | clip:clip_to=6.0 | 0.6948 | 0.6704 |
| test_id | binary_hash | gauss:sigma=0.05 | 0.8635 | 0.8629 |
| test_id | binary_hash | gauss:sigma=0.15 | 0.8635 | 0.8623 |
| test_id | binary_hash | range_bias:bias=0.25 | 0.8353 | 0.8360 |
| test_id | binary_hash | range_scale:scale=1.15 | 0.8273 | 0.8242 |
| test_id | binary_hash | sector_drop:fraction=0.15 | 0.5301 | 0.5274 |
| test_id | binary_hash | sector_drop:fraction=0.3 | 0.4819 | 0.4517 |
| test_id | hdc_k1/skip | beam_drop:drop_rate=0.1 | 0.8956 | 0.8941 |
| test_id | hdc_k1/skip | beam_drop:drop_rate=0.3 | 0.8434 | 0.8354 |
| test_id | hdc_k1/skip | clean | 0.9679 | 0.9671 |
| test_id | hdc_k1/skip | clip:clip_to=6.0 | 0.9357 | 0.9339 |
| test_id | hdc_k1/skip | gauss:sigma=0.05 | 0.9679 | 0.9671 |
| test_id | hdc_k1/skip | gauss:sigma=0.15 | 0.9558 | 0.9547 |
| test_id | hdc_k1/skip | range_bias:bias=0.25 | 0.9518 | 0.9514 |
| test_id | hdc_k1/skip | range_scale:scale=1.15 | 0.9317 | 0.9306 |
| test_id | hdc_k1/skip | sector_drop:fraction=0.15 | 0.8474 | 0.8432 |
| test_id | hdc_k1/skip | sector_drop:fraction=0.3 | 0.7871 | 0.7823 |
| test_id | hdc_k16/drop | beam_drop:drop_rate=0.1 | 0.9639 | 0.9630 |
| test_id | hdc_k16/drop | beam_drop:drop_rate=0.3 | 0.9518 | 0.9502 |
| test_id | hdc_k16/drop | clean | 0.9679 | 0.9668 |
| test_id | hdc_k16/drop | clip:clip_to=6.0 | 0.8233 | 0.7850 |
| test_id | hdc_k16/drop | gauss:sigma=0.05 | 0.9598 | 0.9580 |
| test_id | hdc_k16/drop | gauss:sigma=0.15 | 0.9719 | 0.9710 |
| test_id | hdc_k16/drop | range_bias:bias=0.25 | 0.9598 | 0.9593 |
| test_id | hdc_k16/drop | range_scale:scale=1.15 | 0.9719 | 0.9707 |
| test_id | hdc_k16/drop | sector_drop:fraction=0.15 | 0.9197 | 0.9166 |
| test_id | hdc_k16/drop | sector_drop:fraction=0.3 | 0.8996 | 0.8962 |
| test_id | hdc_k16/fill | beam_drop:drop_rate=0.1 | 0.8835 | 0.8811 |
| test_id | hdc_k16/fill | beam_drop:drop_rate=0.3 | 0.7912 | 0.7772 |
| test_id | hdc_k16/fill | clean | 0.9679 | 0.9668 |
| test_id | hdc_k16/fill | clip:clip_to=6.0 | 0.8233 | 0.7850 |
| test_id | hdc_k16/fill | gauss:sigma=0.05 | 0.9598 | 0.9580 |
| test_id | hdc_k16/fill | gauss:sigma=0.15 | 0.9719 | 0.9710 |
| test_id | hdc_k16/fill | range_bias:bias=0.25 | 0.9598 | 0.9593 |
| test_id | hdc_k16/fill | range_scale:scale=1.15 | 0.9719 | 0.9707 |
| test_id | hdc_k16/fill | sector_drop:fraction=0.15 | 0.8153 | 0.8070 |
| test_id | hdc_k16/fill | sector_drop:fraction=0.3 | 0.6667 | 0.6515 |
| test_id | hdc_k16/skip | beam_drop:drop_rate=0.1 | 0.9157 | 0.9139 |
| test_id | hdc_k16/skip | beam_drop:drop_rate=0.3 | 0.8956 | 0.8945 |
| test_id | hdc_k16/skip | clean | 0.9679 | 0.9668 |
| test_id | hdc_k16/skip | clip:clip_to=6.0 | 0.8233 | 0.7850 |
| test_id | hdc_k16/skip | gauss:sigma=0.05 | 0.9598 | 0.9580 |
| test_id | hdc_k16/skip | gauss:sigma=0.15 | 0.9719 | 0.9710 |
| test_id | hdc_k16/skip | range_bias:bias=0.25 | 0.9598 | 0.9593 |
| test_id | hdc_k16/skip | range_scale:scale=1.15 | 0.9719 | 0.9707 |
| test_id | hdc_k16/skip | sector_drop:fraction=0.15 | 0.8635 | 0.8608 |
| test_id | hdc_k16/skip | sector_drop:fraction=0.3 | 0.8434 | 0.8380 |
| test_id | hdc_linear/skip | beam_drop:drop_rate=0.1 | 0.8032 | 0.7870 |
| test_id | hdc_linear/skip | beam_drop:drop_rate=0.3 | 0.7470 | 0.7134 |
| test_id | hdc_linear/skip | clean | 0.9759 | 0.9754 |
| test_id | hdc_linear/skip | clip:clip_to=6.0 | 0.7871 | 0.7338 |
| test_id | hdc_linear/skip | gauss:sigma=0.05 | 0.9759 | 0.9754 |
| test_id | hdc_linear/skip | gauss:sigma=0.15 | 0.9598 | 0.9589 |
| test_id | hdc_linear/skip | range_bias:bias=0.25 | 0.9518 | 0.9512 |
| test_id | hdc_linear/skip | range_scale:scale=1.15 | 0.9518 | 0.9515 |
| test_id | hdc_linear/skip | sector_drop:fraction=0.15 | 0.7229 | 0.6839 |
| test_id | hdc_linear/skip | sector_drop:fraction=0.3 | 0.6627 | 0.6283 |
| test_id | quantized | beam_drop:drop_rate=0.1 | 0.6466 | 0.6336 |
| test_id | quantized | beam_drop:drop_rate=0.3 | 0.3896 | 0.3055 |
| test_id | quantized | clean | 0.9036 | 0.8990 |
| test_id | quantized | clip:clip_to=6.0 | 0.8554 | 0.8451 |
| test_id | quantized | gauss:sigma=0.05 | 0.9036 | 0.8990 |
| test_id | quantized | gauss:sigma=0.15 | 0.9036 | 0.8992 |
| test_id | quantized | range_bias:bias=0.25 | 0.9036 | 0.9011 |
| test_id | quantized | range_scale:scale=1.15 | 0.9157 | 0.9140 |
| test_id | quantized | sector_drop:fraction=0.15 | 0.5823 | 0.5405 |
| test_id | quantized | sector_drop:fraction=0.3 | 0.3815 | 0.2913 |
| test_ood | binary_hash | beam_drop:drop_rate=0.1 | 0.5122 | 0.4788 |
| test_ood | binary_hash | beam_drop:drop_rate=0.3 | 0.4756 | 0.4185 |
| test_ood | binary_hash | clean | 0.8008 | 0.7993 |
| test_ood | binary_hash | clip:clip_to=6.0 | 0.7195 | 0.6980 |
| test_ood | binary_hash | gauss:sigma=0.05 | 0.8130 | 0.8128 |
| test_ood | binary_hash | gauss:sigma=0.15 | 0.8333 | 0.8328 |
| test_ood | binary_hash | range_bias:bias=0.25 | 0.7642 | 0.7616 |
| test_ood | binary_hash | range_scale:scale=1.15 | 0.8171 | 0.8144 |
| test_ood | binary_hash | sector_drop:fraction=0.15 | 0.5650 | 0.5730 |
| test_ood | binary_hash | sector_drop:fraction=0.3 | 0.5081 | 0.4883 |
| test_ood | hdc_k1/skip | beam_drop:drop_rate=0.1 | 0.8374 | 0.8387 |
| test_ood | hdc_k1/skip | beam_drop:drop_rate=0.3 | 0.8130 | 0.8143 |
| test_ood | hdc_k1/skip | clean | 0.8984 | 0.8987 |
| test_ood | hdc_k1/skip | clip:clip_to=6.0 | 0.8293 | 0.8256 |
| test_ood | hdc_k1/skip | gauss:sigma=0.05 | 0.8902 | 0.8905 |
| test_ood | hdc_k1/skip | gauss:sigma=0.15 | 0.8943 | 0.8954 |
| test_ood | hdc_k1/skip | range_bias:bias=0.25 | 0.8943 | 0.8965 |
| test_ood | hdc_k1/skip | range_scale:scale=1.15 | 0.8821 | 0.8840 |
| test_ood | hdc_k1/skip | sector_drop:fraction=0.15 | 0.8171 | 0.8182 |
| test_ood | hdc_k1/skip | sector_drop:fraction=0.3 | 0.7642 | 0.7651 |
| test_ood | hdc_k16/drop | beam_drop:drop_rate=0.1 | 0.9350 | 0.9336 |
| test_ood | hdc_k16/drop | beam_drop:drop_rate=0.3 | 0.9187 | 0.9178 |
| test_ood | hdc_k16/drop | clean | 0.9472 | 0.9455 |
| test_ood | hdc_k16/drop | clip:clip_to=6.0 | 0.8049 | 0.7665 |
| test_ood | hdc_k16/drop | gauss:sigma=0.05 | 0.9472 | 0.9452 |
| test_ood | hdc_k16/drop | gauss:sigma=0.15 | 0.9472 | 0.9460 |
| test_ood | hdc_k16/drop | range_bias:bias=0.25 | 0.9634 | 0.9630 |
| test_ood | hdc_k16/drop | range_scale:scale=1.15 | 0.9472 | 0.9455 |
| test_ood | hdc_k16/drop | sector_drop:fraction=0.15 | 0.8984 | 0.8935 |
| test_ood | hdc_k16/drop | sector_drop:fraction=0.3 | 0.8902 | 0.8839 |
| test_ood | hdc_k16/fill | beam_drop:drop_rate=0.1 | 0.8577 | 0.8581 |
| test_ood | hdc_k16/fill | beam_drop:drop_rate=0.3 | 0.8171 | 0.8067 |
| test_ood | hdc_k16/fill | clean | 0.9472 | 0.9455 |
| test_ood | hdc_k16/fill | clip:clip_to=6.0 | 0.8049 | 0.7665 |
| test_ood | hdc_k16/fill | gauss:sigma=0.05 | 0.9472 | 0.9452 |
| test_ood | hdc_k16/fill | gauss:sigma=0.15 | 0.9472 | 0.9460 |
| test_ood | hdc_k16/fill | range_bias:bias=0.25 | 0.9634 | 0.9630 |
| test_ood | hdc_k16/fill | range_scale:scale=1.15 | 0.9472 | 0.9455 |
| test_ood | hdc_k16/fill | sector_drop:fraction=0.15 | 0.8008 | 0.7931 |
| test_ood | hdc_k16/fill | sector_drop:fraction=0.3 | 0.6463 | 0.6297 |
| test_ood | hdc_k16/skip | beam_drop:drop_rate=0.1 | 0.8862 | 0.8858 |
| test_ood | hdc_k16/skip | beam_drop:drop_rate=0.3 | 0.8780 | 0.8786 |
| test_ood | hdc_k16/skip | clean | 0.9472 | 0.9455 |
| test_ood | hdc_k16/skip | clip:clip_to=6.0 | 0.8049 | 0.7665 |
| test_ood | hdc_k16/skip | gauss:sigma=0.05 | 0.9472 | 0.9452 |
| test_ood | hdc_k16/skip | gauss:sigma=0.15 | 0.9472 | 0.9460 |
| test_ood | hdc_k16/skip | range_bias:bias=0.25 | 0.9634 | 0.9630 |
| test_ood | hdc_k16/skip | range_scale:scale=1.15 | 0.9472 | 0.9455 |
| test_ood | hdc_k16/skip | sector_drop:fraction=0.15 | 0.8455 | 0.8453 |
| test_ood | hdc_k16/skip | sector_drop:fraction=0.3 | 0.8577 | 0.8550 |
| test_ood | hdc_linear/skip | beam_drop:drop_rate=0.1 | 0.7764 | 0.7585 |
| test_ood | hdc_linear/skip | beam_drop:drop_rate=0.3 | 0.6992 | 0.6565 |
| test_ood | hdc_linear/skip | clean | 0.9756 | 0.9751 |
| test_ood | hdc_linear/skip | clip:clip_to=6.0 | 0.7886 | 0.7399 |
| test_ood | hdc_linear/skip | gauss:sigma=0.05 | 0.9634 | 0.9624 |
| test_ood | hdc_linear/skip | gauss:sigma=0.15 | 0.9675 | 0.9670 |
| test_ood | hdc_linear/skip | range_bias:bias=0.25 | 0.9797 | 0.9792 |
| test_ood | hdc_linear/skip | range_scale:scale=1.15 | 0.9715 | 0.9711 |
| test_ood | hdc_linear/skip | sector_drop:fraction=0.15 | 0.7439 | 0.7146 |
| test_ood | hdc_linear/skip | sector_drop:fraction=0.3 | 0.6667 | 0.6315 |
| test_ood | quantized | beam_drop:drop_rate=0.1 | 0.6626 | 0.6526 |
| test_ood | quantized | beam_drop:drop_rate=0.3 | 0.3821 | 0.3019 |
| test_ood | quantized | clean | 0.8537 | 0.8418 |
| test_ood | quantized | clip:clip_to=6.0 | 0.8293 | 0.8113 |
| test_ood | quantized | gauss:sigma=0.05 | 0.8577 | 0.8455 |
| test_ood | quantized | gauss:sigma=0.15 | 0.8577 | 0.8458 |
| test_ood | quantized | range_bias:bias=0.25 | 0.8415 | 0.8302 |
| test_ood | quantized | range_scale:scale=1.15 | 0.8415 | 0.8301 |
| test_ood | quantized | sector_drop:fraction=0.15 | 0.5691 | 0.5479 |
| test_ood | quantized | sector_drop:fraction=0.3 | 0.4106 | 0.3236 |


Figures: `results/figures/accuracy_k16_lidardataframes_beam_drop.png`, `results/figures/accuracy_k16_lidardataframes_sector_drop.png`.

## Reading

The question is whether the sim Stage 3 operating region (random beam drop holds; 30% sector drop with max-range fill fails; skip/DROP recover) still shows up on author-labeled real scans at the 128 B working point.

- **Clean test_id:** k=16 skip 0.968, fill 0.968, linear 0.976, hashing 0.859, PCM 0.904.
- **30% random beam drop, test_id:** k=16 skip 0.896, fill 0.791, linear 0.747, hashing 0.450, PCM 0.390.
- **30% sector drop, test_id:** k=16 skip 0.843, DROP 0.900, fill 0.667, linear 0.663, hashing 0.482.
- **Range scale 1.15 / clip 6 m, test_id k=16 skip:** 0.972 / 0.823.

N is small (~80 test frames). Treat the ranking and the skip-vs-fill gap as the result, not the exact percentages.
