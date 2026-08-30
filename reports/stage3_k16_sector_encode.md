# Sector-drop encoder fix — skip / DROP vs max-range fill

k=16 at 512 B (`D=4096`). `fill` writes missing beams as max-range (a fake opening). `skip` omits non-finite beams from the bundle. `drop` binds a dedicated DROP item. First-round `k16_sensor.jsonl` is unchanged.

Means over seeds:

| split | method_label | sensor | accuracy | macro_f1 |
| --- | --- | --- | --- | --- |
| test_id | binary_hash | beam_drop:drop_rate=0.1 | 0.5035 | 0.4456 |
| test_id | binary_hash | beam_drop:drop_rate=0.3 | 0.2262 | 0.2167 |
| test_id | binary_hash | clean | 0.9216 | 0.8756 |
| test_id | binary_hash | sector_drop:fraction=0.15 | 0.3933 | 0.3384 |
| test_id | binary_hash | sector_drop:fraction=0.3 | 0.2737 | 0.2286 |
| test_id | hdc_k16/drop | beam_drop:drop_rate=0.1 | 0.9555 | 0.9267 |
| test_id | hdc_k16/drop | beam_drop:drop_rate=0.3 | 0.9489 | 0.9177 |
| test_id | hdc_k16/drop | clean | 0.9597 | 0.9328 |
| test_id | hdc_k16/drop | sector_drop:fraction=0.15 | 0.9473 | 0.9151 |
| test_id | hdc_k16/drop | sector_drop:fraction=0.3 | 0.8989 | 0.8475 |
| test_id | hdc_k16/fill | beam_drop:drop_rate=0.1 | 0.9437 | 0.9137 |
| test_id | hdc_k16/fill | beam_drop:drop_rate=0.3 | 0.8028 | 0.7406 |
| test_id | hdc_k16/fill | clean | 0.9597 | 0.9328 |
| test_id | hdc_k16/fill | sector_drop:fraction=0.15 | 0.7926 | 0.7194 |
| test_id | hdc_k16/fill | sector_drop:fraction=0.3 | 0.3869 | 0.3058 |
| test_id | hdc_k16/skip | beam_drop:drop_rate=0.1 | 0.9547 | 0.9253 |
| test_id | hdc_k16/skip | beam_drop:drop_rate=0.3 | 0.9500 | 0.9191 |
| test_id | hdc_k16/skip | clean | 0.9597 | 0.9328 |
| test_id | hdc_k16/skip | sector_drop:fraction=0.15 | 0.9426 | 0.9059 |
| test_id | hdc_k16/skip | sector_drop:fraction=0.3 | 0.9017 | 0.8479 |
| test_ood | binary_hash | beam_drop:drop_rate=0.1 | 0.4357 | 0.4289 |
| test_ood | binary_hash | beam_drop:drop_rate=0.3 | 0.2534 | 0.2634 |
| test_ood | binary_hash | clean | 0.6228 | 0.5409 |
| test_ood | binary_hash | sector_drop:fraction=0.15 | 0.3739 | 0.3465 |
| test_ood | binary_hash | sector_drop:fraction=0.3 | 0.3095 | 0.2655 |
| test_ood | hdc_k16/drop | beam_drop:drop_rate=0.1 | 0.8183 | 0.6744 |
| test_ood | hdc_k16/drop | beam_drop:drop_rate=0.3 | 0.8277 | 0.6834 |
| test_ood | hdc_k16/drop | clean | 0.8502 | 0.7069 |
| test_ood | hdc_k16/drop | sector_drop:fraction=0.15 | 0.7992 | 0.6528 |
| test_ood | hdc_k16/drop | sector_drop:fraction=0.3 | 0.7525 | 0.6185 |
| test_ood | hdc_k16/fill | beam_drop:drop_rate=0.1 | 0.6976 | 0.5610 |
| test_ood | hdc_k16/fill | beam_drop:drop_rate=0.3 | 0.5901 | 0.4193 |
| test_ood | hdc_k16/fill | clean | 0.8502 | 0.7069 |
| test_ood | hdc_k16/fill | sector_drop:fraction=0.15 | 0.5724 | 0.4008 |
| test_ood | hdc_k16/fill | sector_drop:fraction=0.3 | 0.4373 | 0.1926 |
| test_ood | hdc_k16/skip | beam_drop:drop_rate=0.1 | 0.7990 | 0.6554 |
| test_ood | hdc_k16/skip | beam_drop:drop_rate=0.3 | 0.7689 | 0.6171 |
| test_ood | hdc_k16/skip | clean | 0.8502 | 0.7069 |
| test_ood | hdc_k16/skip | sector_drop:fraction=0.15 | 0.7667 | 0.6155 |
| test_ood | hdc_k16/skip | sector_drop:fraction=0.3 | 0.7019 | 0.5575 |


Figures: `results/figures/accuracy_k16_sector_encode.png`, `results/figures/accuracy_k16_sector_encode_beam.png`.

## Reading

The question is whether telling the encoder that a hole is invalid (instead of open space) recovers sector-drop accuracy without hurting random beam dropout or the clean channel.

- **Clean is unchanged.** Hashing is 0.922 ID / 0.623 OOD. k=16 fill, skip, and DROP are identical at 0.960 ID / 0.850 OOD — there are no non-finite beams, so the three encoders write the same HV.
- **30% sector drop was the encoder, not the classifier.** ID: fill 0.387 (same as the first-round remake), skip 0.902, DROP 0.899, hashing 0.274. OOD: fill 0.437, skip 0.702, DROP 0.753.
- **Random beam drop does not regress; skip/DROP improve it.** ID 30% beam drop: fill 0.803, skip 0.950, DROP 0.949. Fill still writes scattered holes as max-range, so those random gaps were a milder version of the same fake opening.
- **DROP vs skip.** On this grid they are close on ID. DROP is a bit ahead on OOD holes (a bound DROP item stays in the bundle; skip shortens it). Neither is a universal win over the other. Hashing has no DROP item and stays the max-range-fill control.
