# Results on git

Numbers live in `raw/*.jsonl`. Tables, figures, and `reports/*.md` are generated from those files by `python scripts/aggregate_results.py`. Do not hand-edit the curves. Do not overwrite first-round sim JSONL when adding a remake.

Working-region narrative: [`reports/milestone_summary.md`](../reports/milestone_summary.md).

## Tracked (already on `main`)

| Sweep JSONL | Dataset | What it is | Report |
|---|---|---|---|
| `bandwidth_sweep.jsonl` | sim | Stage 1, k=1 | `reports/stage1_bandwidth.md` |
| `k16_bandwidth.jsonl` | sim | Stage 1 remake, k=16 / linear | `reports/stage1_k16_bandwidth.md` |
| `noise_sweep.jsonl`, `burst_sweep.jsonl`, `packet_loss_sweep.jsonl`, `packet_interleave_sweep.jsonl` | sim | Stage 2 first round | `reports/stage2_noise.md` |
| `k16_noise.jsonl` | sim | Stage 2 remake, 128 B | `reports/stage2_k16_noise.md` |
| `sensor_shift.jsonl` | sim | Stage 3 first round (fill) | `reports/stage3_shift.md` |
| `k16_sensor.jsonl` | sim | Stage 3 remake, 512 B | `reports/stage3_k16_sensor.md` |
| `k16_sector_encode.jsonl` | sim | skip / DROP vs fill | `reports/stage3_k16_sector_encode.md` |
| `adaptation.jsonl`, `multicentroid_adaptation.jsonl` | sim | Stage 4 first round | `reports/stage4_adaptation.md` |
| `k16_adaptation_128b.jsonl` | sim | Stage 4 remake, 128 B | `reports/stage4_k16_adaptation_128b.md` |
| `hybrid_sweep.jsonl`, `hybrid_lidar_sweep.jsonl` | sim | Stage 5 | `reports/stage5_hybrid.md` |
| `radio_sweep.jsonl` | sim | Stage 8 first round | `reports/stage8_radio.md` |
| `k16_radio.jsonl` | sim | Stage 8 remake, 128 B | `reports/stage8_k16_radio.md` |
| `k16_semantic2d.jsonl` | Semantic2D | 128 B, derived labels | `reports/stage0_semantic2d.md` |
| `k16_lidardataframes.jsonl` | LidarDataFrames | 128 B BER, author labels | `reports/stage0_lidardataframes.md` |
| `k16_lidardataframes_sensor.jsonl` | LidarDataFrames | Stage 3 dropout at 128 B | `reports/stage3_k16_lidardataframes_sensor.md` |

Also tracked: `results/figures/`, `results/tables/`, frozen splits under `data/splits/`.

## Not on git (by design)

| Path | Why |
|---|---|
| `data/raw/` | Semantic2D archive (~2 GB), Kaggle CSV |
| `data/processed/` | `scans.npz` rebuilt by prepare scripts |
| `results/models/` | fitted weights, if any |
| `.venv/` | local environment |

Rebuild processed arrays after clone:

```bash
python scripts/prepare_data.py
python scripts/prepare_semantic2d.py      # needs data/raw/semantic2d/
python scripts/prepare_lidardataframes.py # needs data/raw/lidardataframes/FourClassDS.csv
```

Splits in `data/splits/` are frozen; do not reshuffle them.
