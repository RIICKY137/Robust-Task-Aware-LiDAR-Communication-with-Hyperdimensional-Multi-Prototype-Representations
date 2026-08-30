# Data report — Semantic2D place labels (derived)

Dataset: `semantic2d_v1` from Xie et al. Semantic2D (Zenodo `10.5281/zenodo.13730200`). Scans are real 2D LiDAR. Place tags are **derived** from the range profile plus point-wise object labels (door / furniture / opening), not author-annotated corridor/room tags.

Invalid / no-return beams (Hokuyo sentinel ≈ 60 m, non-finite, or ≤ 5 cm) are stored as NaN, not max-range fill. Finite ranges are clipped to 20 m for the encoder. Beams are resampled to 180 over the native 270° field of view. Stride 10 keeps the set comparable in size to `sim_indoor_v1`.

## Split protocol

- `test_ood`: held-out environments (building shift).
- `test_id`: last 20% of each remaining sequence (time order, not a random frame shuffle).
- `train`: the rest of those sequences.

Held-out environments: `['eng_9th', 'lobby']`

Total scans: 8265

## Class balance

| class | n | share |
|---|---:|---:|
| corridor | 529 | 6.4% |
| room | 3132 | 37.9% |
| doorway | 2634 | 31.9% |
| open_area | 358 | 4.3% |
| cluttered_area | 1612 | 19.5% |

### By split

**train** n=4203

| class | n |
|---|---:|
| corridor | 142 |
| room | 1782 |
| doorway | 1424 |
| open_area | 274 |
| cluttered_area | 581 |

**test_id** n=1053

| class | n |
|---|---:|
| corridor | 76 |
| room | 373 |
| doorway | 345 |
| open_area | 10 |
| cluttered_area | 249 |

**test_ood** n=3009

| class | n |
|---|---:|
| corridor | 311 |
| room | 977 |
| doorway | 865 |
| open_area | 74 |
| cluttered_area | 782 |

Meta: `{"dataset": "semantic2d_v1", "n_beams": 180, "max_range": 20.0, "n_samples": 8265, "label_names": ["corridor", "room", "doorway", "open_area", "cluttered_area"], "seed": 7, "split_counts": {"train": 4203, "test_id": 1053, "test_ood": 3009}, "fov_deg": 270.0, "ood_envs": ["eng_9th", "lobby"], "label_source": "derived_from_range_and_semantic2d_objects", "source": "zenodo:10.5281/zenodo.13730200", "stride": 10}`
