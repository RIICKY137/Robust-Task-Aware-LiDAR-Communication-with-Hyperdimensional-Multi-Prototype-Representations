# Real 2D LiDAR — LidarDataFrames at 128 B k=16 (author place labels)

Scans are RPLiDAR A1 frames from Kaggle LidarDataFrames. Place labels are **author-assigned** room / corridor / doorway / hall (hall → `open_area`). 411 frames, four classes, no `cluttered_area`. This is the labeled real-scan check that Semantic2D could not provide.

The CSV has no building id. `test_ood` is a stratified i.i.d. holdout, **not** a floorplan shift. N is small (~80 test frames). First-round sim and Semantic2D JSONL are unchanged.

Means over seeds:

| split | method_label | ber | accuracy | macro_f1 |
| --- | --- | --- | --- | --- |
| test_id | binary_hash | 0.0000 | 0.8594 | 0.8575 |
| test_id | binary_hash | 0.0500 | 0.7952 | 0.7942 |
| test_id | binary_hash | 0.1000 | 0.7028 | 0.6959 |
| test_id | hdc_k1 | 0.0000 | 0.9679 | 0.9671 |
| test_id | hdc_k1 | 0.0500 | 0.9639 | 0.9630 |
| test_id | hdc_k1 | 0.1000 | 0.9518 | 0.9510 |
| test_id | hdc_k16 | 0.0000 | 0.9679 | 0.9668 |
| test_id | hdc_k16 | 0.0500 | 0.9639 | 0.9626 |
| test_id | hdc_k16 | 0.1000 | 0.9719 | 0.9715 |
| test_id | hdc_linear | 0.0000 | 0.9759 | 0.9754 |
| test_id | hdc_linear | 0.0500 | 0.9558 | 0.9550 |
| test_id | hdc_linear | 0.1000 | 0.9679 | 0.9675 |
| test_id | quantized | 0.0000 | 0.9036 | 0.8990 |
| test_id | quantized | 0.0500 | 0.5984 | 0.5858 |
| test_id | quantized | 0.1000 | 0.4177 | 0.3947 |
| test_ood | binary_hash | 0.0000 | 0.8008 | 0.7993 |
| test_ood | binary_hash | 0.0500 | 0.7805 | 0.7769 |
| test_ood | binary_hash | 0.1000 | 0.6870 | 0.6742 |
| test_ood | hdc_k1 | 0.0000 | 0.8984 | 0.8987 |
| test_ood | hdc_k1 | 0.0500 | 0.8984 | 0.8980 |
| test_ood | hdc_k1 | 0.1000 | 0.9065 | 0.9060 |
| test_ood | hdc_k16 | 0.0000 | 0.9472 | 0.9455 |
| test_ood | hdc_k16 | 0.0500 | 0.9390 | 0.9369 |
| test_ood | hdc_k16 | 0.1000 | 0.9431 | 0.9413 |
| test_ood | hdc_linear | 0.0000 | 0.9756 | 0.9751 |
| test_ood | hdc_linear | 0.0500 | 0.9756 | 0.9751 |
| test_ood | hdc_linear | 0.1000 | 0.9715 | 0.9709 |
| test_ood | quantized | 0.0000 | 0.8537 | 0.8418 |
| test_ood | quantized | 0.0500 | 0.5488 | 0.5293 |
| test_ood | quantized | 0.1000 | 0.4228 | 0.4025 |


Figures: `results/figures/accuracy_k16_lidardataframes.png`, `results/figures/accuracy_k16_lidardataframes_ood.png`.

## Reading

The question is whether 128 B k=16 still has an operating region when the place tags are author labels rather than derived heuristics.

- **Clean test_id:** k=16 0.968, linear 0.976, hashing 0.859, k=1 0.968, PCM 0.904.
- **BER = 0.10, test_id:** k=16 0.972, hashing 0.703, linear 0.968, PCM 0.418.

Do not treat this as a replacement for Semantic2D scale or a building-shift OOD test.
