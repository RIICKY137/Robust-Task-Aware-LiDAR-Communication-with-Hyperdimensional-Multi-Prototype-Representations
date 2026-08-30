# Reports

Generated files:

- `data_report.md` — Stage 0 dataset, labels, splits, class balance (`python scripts/prepare_data.py`)
- `stage1_bandwidth.md` — clean-channel Accuracy–Bandwidth (`python scripts/aggregate_results.py`)
- `stage1_k16_bandwidth.md` — k=16 / linear / hashing remake at 128 / 512 / 2048 B
- `stage2_noise.md` — Accuracy–BER, burst, packet loss, packet+interleave
- `stage3_shift.md` — sensor corruption and OOD floorplan (first-round, k=1)
- `stage3_k16_sensor.md` — k=16 remake of beam / sector dropout
- `stage4_adaptation.md` — 10/50/100-shot HDC vs linear head vs hybrid
- `stage5_hybrid.md` — sector-stat neural-HDC (Stage 5)
- `stage5_hybrid_lidar.md` — full-scan LiDAR hybrid ± record bundle
- `stage4_multicentroid_adapt.md` — k=1/8/16 vs linear head, 10/50/100-shot OOD
- `multicentroid.md` — k prototypes per class vs linear head
- `stage8_radio.md` — uncoded BPSK/QPSK vs matched BER
- `final_report.md` — working-region summary for RQ1–RQ3

Do not draw publication figures by hand. Re-run `aggregate_results.py` from `results/raw/*.jsonl`.
