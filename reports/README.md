# Reports

Generated files:

- `data_report.md` — Stage 0 dataset, labels, splits, class balance (`python scripts/prepare_data.py`)
- `stage1_bandwidth.md` — clean-channel Accuracy–Bandwidth (`python scripts/aggregate_results.py`)
- `stage2_noise.md` — Accuracy–BER
- `final_report.md` — working-region summary for RQ1–RQ3

Do not draw publication figures by hand. Re-run `aggregate_results.py` from `results/raw/*.jsonl`.
