# Few-shot OOD remake at 128 B

Same protocol as `reports/stage4_multicentroid_adapt.md`, at the 128 B operating point (`D=1024`). `hdc_k1` / `hdc_k16` add (and subtract the current prediction from) the nearest class centroid. `hdc_linear` refits logistic regression on train hypervectors plus the labeled shots. First-round `adaptation.jsonl` and `multicentroid_adaptation.jsonl` are unchanged.

Means over seeds:

| method | shots_per_class | before_new_acc_mean | before_new_acc_std | new_acc_mean | new_acc_std | delta_new_mean | delta_new_std | before_old_acc_mean | before_old_acc_std | old_acc_mean | old_acc_std | forgetting_mean | forgetting_std | adapt_ms_mean | adapt_ms_std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hdc_k1 | 10 | 0.6990 | 0.0063 | 0.7070 | 0.0052 | 0.0081 | 0.0027 | 0.7269 | 0.0027 | 0.7283 | 0.0008 | -0.0014 | 0.0029 | 3.8749 | 0.0515 |
| hdc_k1 | 50 | 0.6990 | 0.0063 | 0.7216 | 0.0075 | 0.0226 | 0.0025 | 0.7269 | 0.0027 | 0.7227 | 0.0069 | 0.0041 | 0.0090 | 23.8353 | 8.4910 |
| hdc_k1 | 100 | 0.6990 | 0.0063 | 0.7511 | 0.0063 | 0.0522 | 0.0063 | 0.7269 | 0.0027 | 0.7213 | 0.0037 | 0.0055 | 0.0017 | 40.7021 | 3.3227 |
| hdc_k16 | 10 | 0.8405 | 0.0114 | 0.8533 | 0.0110 | 0.0128 | 0.0009 | 0.9533 | 0.0019 | 0.9531 | 0.0021 | 0.0003 | 0.0027 | 8.9237 | 0.3355 |
| hdc_k16 | 50 | 0.8405 | 0.0114 | 0.8897 | 0.0030 | 0.0492 | 0.0087 | 0.9533 | 0.0019 | 0.9508 | 0.0021 | 0.0025 | 0.0038 | 41.8532 | 1.6139 |
| hdc_k16 | 100 | 0.8405 | 0.0114 | 0.9100 | 0.0017 | 0.0695 | 0.0112 | 0.9533 | 0.0019 | 0.9450 | 0.0027 | 0.0083 | 0.0041 | 80.0889 | 2.5577 |
| hdc_linear | 10 | 0.7937 | 0.0105 | 0.8037 | 0.0027 | 0.0100 | 0.0080 | 0.9453 | 0.0054 | 0.9448 | 0.0053 | 0.0006 | 0.0029 | 3915.3021 | 1767.1152 |
| hdc_linear | 50 | 0.7937 | 0.0105 | 0.8519 | 0.0074 | 0.0583 | 0.0174 | 0.9453 | 0.0054 | 0.9312 | 0.0065 | 0.0141 | 0.0029 | 5045.6929 | 1398.3578 |
| hdc_linear | 100 | 0.7937 | 0.0105 | 0.8976 | 0.0080 | 0.1040 | 0.0155 | 0.9453 | 0.0054 | 0.9263 | 0.0083 | 0.0191 | 0.0066 | 5016.7579 | 513.9568 |


Figure: `results/figures/accuracy_k16_adaptation_128b.png`.

## Reading

The question is Outcome C at 128 B: does a cheap centroid update still close the OOD gap relative to refitting a linear head, and does shrinking D from 4096 to 1024 change the 512 B picture.

- **k=16 still starts ahead on OOD.** Before shots: k=16 0.841, linear 0.794, k=1 0.699 — the same 128 B bandwidth remake.
- **Centroid add remains cheap.** k=16: 9 / 42 / 80 ms at 10 / 50 / 100 shots. Linear refit on train HVs plus shots: ~4–5 s.
- **Gains match 512 B; linear does not overtake.** k=16 +0.013 / +0.049 / +0.070 (→ 0.853 / 0.890 / 0.910). Linear +0.010 / +0.058 / +0.104 (→ 0.804 / 0.852 / 0.898). At 512 B the linear head passed k=16 at 100 shots; at 128 B it does not.
- **k=1 is still not the operating point.** 0.699 → 0.751 at 100 shots.
- **Forgetting stays small for k=16** (0.008 at 100 shots). Linear drops ID more (0.945 → 0.926).
