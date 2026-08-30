# Simulated / public LiDAR data

Processed arrays are written by `python scripts/prepare_data.py` and are gitignored.

```
data/
  processed/sim_indoor_v1/scans.npz
  splits/sim_indoor_v1/{train,test_id,test_ood,meta}.json
```

## Current generator

`sim_indoor_v1` is a controllable 2D indoor simulator (Stage 0 fallback in the project brief):

- 180-beam planar LiDAR, 10 m max range
- Five place classes: corridor, room, doorway, open_area, cluttered_area
- Train/ID test split by **trajectory** inside `env_a` and `env_b`
- OOD test is a different floorplan `env_ood`

Do not reshuffle frames across those JSON split files.

## Swapping in a real dataset

`semantic2d_v1` is wired from Semantic2D (Zenodo 10.5281/zenodo.13730200). Place labels are **derived** from the range profile plus object labels. Invalid beams are NaN.

```bash
# archive is gitignored under data/raw/semantic2d/
python scripts/prepare_semantic2d.py
python scripts/run_k16_semantic2d.py
```

Add another loader under `src/hdc_lidar/data/` that emits the same `ScanBatch` fields and freeze files under `data/splits/<name>/`. Prefer public corpora that already have place or scene tags. If you only have trajectories plus a map, derive labels from map regions and split by session or building — never by random frame order.
