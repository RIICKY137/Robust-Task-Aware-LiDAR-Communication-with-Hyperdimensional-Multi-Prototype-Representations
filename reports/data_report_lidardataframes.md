# Data report — LidarDataFrames (author place labels)

Dataset: `lidardataframes_v1` from [LidarDataFrames](https://www.kaggle.com/datasets/tareqalhmiedat/lidardataframes) (RPLiDAR A1). Place tags are **author-labeled** environment types, not derived heuristics.

Four classes in the CSV: room, corridor, doorway, hall. Hall is mapped to `open_area`. `cluttered_area` is unused. Ranges are millimetres, converted to metres, resampled 360→180 beams, clipped at 12 m (A1 max). ≤5 cm → NaN.

## Split protocol

The CSV has **no building or trajectory id**. Splits are stratified 60/20/20 by class (seed 7). `test_ood` is a second i.i.d. holdout, **not** a floorplan shift. Do not read it as Semantic2D-style building OOD.

Total scans: 411

## Class balance

| class | n | share |
|---|---:|---:|
| corridor | 100 | 24.3% |
| room | 109 | 26.5% |
| doorway | 99 | 24.1% |
| open_area | 103 | 25.1% |
| cluttered_area | 0 | 0.0% |

### By split

**train** n=246

| class | n |
|---|---:|
| corridor | 60 |
| room | 65 |
| doorway | 59 |
| open_area | 62 |
| cluttered_area | 0 |

**test_id** n=83

| class | n |
|---|---:|
| corridor | 20 |
| room | 22 |
| doorway | 20 |
| open_area | 21 |
| cluttered_area | 0 |

**test_ood** n=82

| class | n |
|---|---:|
| corridor | 20 |
| room | 22 |
| doorway | 20 |
| open_area | 20 |
| cluttered_area | 0 |

Meta: `{"dataset": "lidardataframes_v1", "n_beams": 180, "max_range": 12.0, "n_samples": 411, "label_names": ["corridor", "room", "doorway", "open_area", "cluttered_area"], "seed": 7, "split_counts": {"train": 246, "test_id": 83, "test_ood": 82}, "fov_deg": 360.0, "label_source": "author_lidardataframes_place_tags", "source": "kaggle:tareqalhmiedat/lidardataframes", "n_classes_present": 4, "split_note": "stratified_60_20_20_iid_test_ood_is_not_building_shift"}`
