# Data report (Stage 0)

Dataset: `sim_indoor_v1` — controllable 2D indoor LiDAR simulator used until a labeled public scan+place corpus is wired in.

## Label definition

Place labels are assigned from the robot pose against floorplan regions, not from adjacent-frame clustering:

- `corridor` — narrow hall centerline
- `room` — enclosed rectangular rooms
- `doorway` — door opening volumes (sampled extra to reduce imbalance)
- `open_area` — lobby / atrium
- `cluttered_area` — storage with box obstacles

## Sensor model

- Beams: **180** over 360°
- Max range: **10.0 m**
- Additive Gaussian range noise σ = 1.5 cm at generation time
- Invalid/no-hit returns are clipped to max range

## Split protocol

- **train**: trajectories 0..T-2 in `env_a` and `env_b`
- **test_id**: held-out trajectory in the same buildings (no random frame shuffle)
- **test_ood**: entire `env_ood` floorplan (different proportions, denser clutter)

Adjacent time frames from one trajectory never appear in both train and test_id.

## Counts

- Total scans: 5315
- Train: 2415
- In-distribution test: 1207
- Shifted / OOD test: 1693

### Class balance (all data)

| class | n | share |
|---|---:|---:|
| corridor | 1306 | 24.6% |
| room | 1582 | 29.8% |
| doorway | 396 | 7.5% |
| open_area | 1619 | 30.5% |
| cluttered_area | 412 | 7.8% |

### Class balance by split

**train**

| class | n |
|---|---:|
| corridor | 725 |
| room | 729 |
| doorway | 229 |
| open_area | 586 |
| cluttered_area | 146 |

**test_id**

| class | n |
|---|---:|
| corridor | 361 |
| room | 367 |
| doorway | 113 |
| open_area | 293 |
| cluttered_area | 73 |

**test_ood**

| class | n |
|---|---:|
| corridor | 220 |
| room | 486 |
| doorway | 54 |
| open_area | 740 |
| cluttered_area | 193 |

## Leakage checks

- Split files are frozen under `data/splits/sim_indoor_v1/*.json`.
- `sample_id` is unique; trajectory IDs in train and test_id are disjoint.

Meta: `{"dataset": "sim_indoor_v1", "n_beams": 180, "max_range": 10.0, "n_samples": 5315, "label_names": ["corridor", "room", "doorway", "open_area", "cluttered_area"], "seed": 7, "split_counts": {"train": 2415, "test_id": 1207, "test_ood": 1693}}`
