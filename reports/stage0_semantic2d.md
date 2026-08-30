# Real 2D LiDAR — Semantic2D at 128 B k=16

Scans are real 2D LiDAR from Semantic2D (Zenodo `10.5281/zenodo.13730200`). Place labels are **derived** from the range profile plus object labels (door / furniture), not author-annotated corridor/room tags. Invalid beams are NaN; HDC uses `skip`. First-round `sim_indoor_v1` JSONL is unchanged.

8265 scans (stride 10), 180 beams, 270° FOV. OOD environments: lobby + eng_9th. Class mix is uneven (room 38%, doorway 32%, cluttered 20%, corridor 6%, open 4%).

Means over seeds:

| split | method_label | ber | accuracy | macro_f1 |
| --- | --- | --- | --- | --- |
| test_id | binary_hash | 0.0000 | 0.3833 | 0.3190 |
| test_id | binary_hash | 0.0500 | 0.3257 | 0.2593 |
| test_id | binary_hash | 0.1000 | 0.3014 | 0.2404 |
| test_id | hdc_k1 | 0.0000 | 0.3488 | 0.3242 |
| test_id | hdc_k1 | 0.0500 | 0.3371 | 0.3091 |
| test_id | hdc_k1 | 0.1000 | 0.3412 | 0.3148 |
| test_id | hdc_k16 | 0.0000 | 0.5046 | 0.4857 |
| test_id | hdc_k16 | 0.0500 | 0.5074 | 0.4884 |
| test_id | hdc_k16 | 0.1000 | 0.5008 | 0.4756 |
| test_id | hdc_linear | 0.0000 | 0.4511 | 0.4421 |
| test_id | hdc_linear | 0.0500 | 0.3966 | 0.3684 |
| test_id | hdc_linear | 0.1000 | 0.3650 | 0.3208 |
| test_id | quantized | 0.0000 | 0.3552 | 0.3219 |
| test_id | quantized | 0.0500 | 0.2067 | 0.1912 |
| test_id | quantized | 0.1000 | 0.1570 | 0.1525 |
| test_ood | binary_hash | 0.0000 | 0.3286 | 0.2617 |
| test_ood | binary_hash | 0.0500 | 0.3048 | 0.2417 |
| test_ood | binary_hash | 0.1000 | 0.2940 | 0.2318 |
| test_ood | hdc_k1 | 0.0000 | 0.2345 | 0.2584 |
| test_ood | hdc_k1 | 0.0500 | 0.2347 | 0.2578 |
| test_ood | hdc_k1 | 0.1000 | 0.2365 | 0.2569 |
| test_ood | hdc_k16 | 0.0000 | 0.3483 | 0.2900 |
| test_ood | hdc_k16 | 0.0500 | 0.3451 | 0.2875 |
| test_ood | hdc_k16 | 0.1000 | 0.3395 | 0.2831 |
| test_ood | hdc_linear | 0.0000 | 0.3256 | 0.2819 |
| test_ood | hdc_linear | 0.0500 | 0.2954 | 0.2593 |
| test_ood | hdc_linear | 0.1000 | 0.2838 | 0.2517 |
| test_ood | quantized | 0.0000 | 0.2529 | 0.2409 |
| test_ood | quantized | 0.0500 | 0.1681 | 0.1635 |
| test_ood | quantized | 0.1000 | 0.1401 | 0.1366 |


Figures: `results/figures/accuracy_k16_semantic2d.png`, `results/figures/accuracy_k16_semantic2d_ood.png`.

## Reading

The question is whether the 128 B k=16 operating region from `sim_indoor_v1` (~0.95 ID, BER-flat through 0.10) survives a real planar scan and a building holdout.

- **Clean ID:** k=16 0.505, linear 0.451, hashing 0.383, k=1 0.349, 8-bit PCM 0.355. k=16 is the best of this set. Absolute accuracy is far below the simulator; the ~0.95 region does **not** transfer. It is still a lift over the test_id majority class (room, 35%).
- **BER = 0.10, ID:** k=16 0.501 (flat), hashing 0.301, linear 0.365 (drops), PCM 0.157 (cliffs). The holographic-vs-not pattern is the same as on sim, at a lower ceiling. Linear still failed to converge in 600 LBFGS steps.
- **Clean OOD (lobby + 9th floor):** k=16 0.348, hashing 0.329, linear 0.326, k=1 0.235, PCM 0.253. This is a near-majority scramble (OOD room share 32%). Do not read it as the indoor-sim OOD gap transferring.

Takeaway: k=16 remains the method that is both strongest on ID and BER-flat at 128 B, but real scans with derived place tags are a harder task and the building holdout is not solved. Hardware OTA is still blocked on this VM.
