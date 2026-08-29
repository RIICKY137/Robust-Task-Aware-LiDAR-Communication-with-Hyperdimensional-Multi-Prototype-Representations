# Stage 4 — few-shot adaptation after environment shift

Target is `test_ood` (held-out floorplan). Old-task accuracy is `test_id`. HDC and hybrid-task update class prototypes by adding the encoded shot (and subtracting the current prediction). The 8-bit baseline refits logistic regression on train features plus the shots. Times are wall-clock for the update only.

| shots_per_class | hdc_new_acc_mean | hdc_new_acc_std | hdc_old_acc_mean | hdc_old_acc_std | hdc_forgetting_mean | hdc_forgetting_std | hdc_adapt_ms_mean | hdc_adapt_ms_std | quant_new_acc_mean | quant_new_acc_std | quant_old_acc_mean | quant_old_acc_std | quant_forgetting_mean | quant_forgetting_std | quant_adapt_ms_mean | quant_adapt_ms_std | hybrid_new_acc_mean | hybrid_new_acc_std | hybrid_old_acc_mean | hybrid_old_acc_std | hybrid_forgetting_mean | hybrid_forgetting_std | hybrid_adapt_ms_mean | hybrid_adapt_ms_std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10.0000 | 0.7202 | 0.0080 | 0.7302 | 0.0034 | 0.0011 | 0.0017 | 11.4762 | 0.9558 | 0.7519 | 0.0082 | 0.7357 | 0.0074 | 0.0116 | 0.0074 | 13422.4493 | 1931.7273 | 0.7509 | 0.0309 | 0.7622 | 0.0174 | -0.0014 | 0.0005 | 12.3151 | 4.6790 |
| 50.0000 | 0.7354 | 0.0067 | 0.7277 | 0.0067 | 0.0036 | 0.0067 | 67.5838 | 0.6087 | 0.7809 | 0.0006 | 0.7274 | 0.0033 | 0.0199 | 0.0033 | 13382.0472 | 1528.4388 | 0.7612 | 0.0337 | 0.7592 | 0.0199 | 0.0017 | 0.0036 | 44.6393 | 20.0539 |
| 100.0000 | 0.7608 | 0.0077 | 0.7247 | 0.0082 | 0.0066 | 0.0066 | 129.3891 | 1.2800 | 0.7931 | 0.0059 | 0.7269 | 0.0017 | 0.0204 | 0.0017 | 13270.2267 | 2045.2343 | 0.7809 | 0.0282 | 0.7575 | 0.0213 | 0.0033 | 0.0036 | 85.1832 | 21.4627 |


Figure: `results/figures/accuracy_adaptation.png`.
