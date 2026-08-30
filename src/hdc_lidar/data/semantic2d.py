"""Import Semantic2D 2D LiDAR scans and derive place labels from geometry.

Semantic2D (Xie et al., Zenodo 10.5281/zenodo.13730200) has point-wise object
labels (wall, door, chair, …), not corridor/room/doorway tags. Place classes
here are derived from the range profile plus those object labels, then split
by environment — the brief's second option when a map/trajectory corpus has
no place tags.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from hdc_lidar import LABEL_TO_ID, LABELS

# Semantic2D object ids (dataset README / SALSA label set).
SEM_CHAIR = 1
SEM_DOOR = 2
SEM_SOFA = 6
SEM_TABLE = 7

N_BEAMS_OUT = 180
MAX_RANGE = 20.0
FOV_DEG = 270.0
# Hokuyo UTM-30LX-EW no-return sentinel used in this corpus (RANGE_MAX=60).
NO_RETURN = 59.0

# Zenodo v1 session folders → map names. Used when *_map dirs are not unpacked.
SEQ_ENV = {
    "2024-04-04-12-16-41": "lobby",
    "2024-04-04-13-48-45": "eng_6th",
    "2024-04-04-14-18-32": "eng_9th",
    "2024-04-04-14-50-01": "eng_8th",
    "2024-04-11-14-37-14": "eng_4th",
    "2024-04-11-15-24-29": "corridor",
}


def resample_scan(values: np.ndarray, n_out: int = N_BEAMS_OUT, kind: str = "linear") -> np.ndarray:
    x = np.asarray(values, dtype=np.float32).reshape(-1)
    if x.size == n_out:
        return x
    idx = np.linspace(0, x.size - 1, n_out)
    if kind == "nearest":
        take = np.clip(np.round(idx).astype(np.int32), 0, x.size - 1)
        return x[take]
    lo = np.floor(idx).astype(np.int32)
    hi = np.minimum(lo + 1, x.size - 1)
    w = (idx - lo).astype(np.float32)
    return ((1.0 - w) * x[lo] + w * x[hi]).astype(np.float32)


def sanitize_ranges(
    ranges: np.ndarray,
    max_range: float = MAX_RANGE,
    no_return: float = NO_RETURN,
) -> np.ndarray:
    """Mark sensor holes as NaN; clip remaining finite ranges to max_range.

    Valid far indoor returns stay finite. Only the no-return sentinel (and
    non-positive / non-finite values) become NaN — not every beam above 20 m.
    """
    x = np.asarray(ranges, dtype=np.float32).copy()
    bad = ~np.isfinite(x) | (x <= 0.05) | (x >= no_return)
    x[bad] = np.nan
    finite = np.isfinite(x)
    x[finite] = np.minimum(x[finite], np.float32(max_range))
    return x


def derive_place(ranges: np.ndarray, semantic: np.ndarray | None) -> int:
    """Map one scan to corridor / room / doorway / open_area / cluttered_area.

    Doorway is a nearby door, not 'a door exists somewhere in the scan'.
    Corridor geometry is applied when that nearby-door test fails.
    """
    r = np.asarray(ranges, dtype=np.float32)
    filled = np.where(np.isfinite(r), r, MAX_RANGE)
    n = filled.size
    left = filled[: n // 3]
    mid = filled[n // 3 : 2 * n // 3]
    right = filled[2 * n // 3 :]
    left_w = float(np.percentile(left, 20))
    right_w = float(np.percentile(right, 20))
    mid_d = float(np.percentile(mid, 50))
    width = left_w + right_w
    mean_r = float(np.nanmean(np.where(np.isfinite(r), r, np.nan)))
    if not np.isfinite(mean_r):
        mean_r = MAX_RANGE
    p90 = float(np.percentile(filled, 90))

    door_frac = 0.0
    n_door_near = 0
    door_med = np.inf
    n_furn_near = 0
    if semantic is not None and semantic.size == n:
        door = semantic == SEM_DOOR
        furn = np.isin(semantic, [SEM_CHAIR, SEM_SOFA, SEM_TABLE])
        door_frac = float(np.mean(door))
        near = np.isfinite(r) & (r < 4.0)
        n_door_near = int(np.sum(door & near))
        if n_door_near:
            door_med = float(np.median(r[door & near]))
        n_furn_near = int(np.sum(furn & near))

    # In / at a doorway: several door-labeled beams close to the robot.
    if n_door_near >= 6 and door_med < 3.5 and door_frac < 0.28:
        return LABEL_TO_ID["doorway"]
    if width < 3.4 and mid_d > max(4.0, 1.2 * width):
        return LABEL_TO_ID["corridor"]
    if n_furn_near >= 12 and width < 9.0 and mean_r < 8.0:
        return LABEL_TO_ID["cluttered_area"]
    if mean_r > 8.0 or p90 > 14.0:
        return LABEL_TO_ID["open_area"]
    return LABEL_TO_ID["room"]


def _map_to_env(name: str) -> str:
    if name.endswith("_map"):
        name = name[: -len("_map")]
    parts = name.split("_")
    while parts and parts[0].isdigit():
        parts = parts[1:]
    return "_".join(parts) if parts else name


def _env_id(scans_dir: Path) -> str:
    parent = Path(scans_dir).parent
    maps = sorted(p.name for p in parent.iterdir() if p.is_dir() and p.name.endswith("_map"))
    if maps:
        return _map_to_env(maps[0])
    return SEQ_ENV.get(parent.name, parent.name)


def discover_sequences(root: Path) -> list[tuple[str, Path]]:
    """Return (env_id, scans_lidar_dir) for each Semantic2D sequence."""
    root = Path(root)
    found = []
    for scans_dir in sorted(root.rglob("scans_lidar")):
        if not scans_dir.is_dir():
            continue
        env = _env_id(scans_dir)
        if env in {"", ".", "data", "semantic2d"}:
            env = scans_dir.parent.name or "seq"
        found.append((env, scans_dir))
    return found


def _load_optional(path: Path) -> np.ndarray | None:
    if not path.exists():
        return None
    return np.load(path, allow_pickle=True)


def _frame_key(path: Path):
    try:
        return int(path.stem)
    except ValueError:
        return path.stem


def load_sequence_frames(scans_dir: Path, stride: int = 10) -> list[dict]:
    files = sorted(scans_dir.glob("*.npy"), key=_frame_key)
    if not files:
        files = sorted(scans_dir.glob("*.npz"), key=_frame_key)
    out = []
    sem_dir = scans_dir.parent / "semantic_label"
    pos_dir = scans_dir.parent / "positions"
    for i, fp in enumerate(files):
        if i % max(1, stride) != 0:
            continue
        raw = np.load(fp, allow_pickle=True)
        if isinstance(raw, np.lib.npyio.NpzFile):
            raw = raw[raw.files[0]]
        native = np.asarray(raw, dtype=np.float32).reshape(-1)
        ranges = resample_scan(sanitize_ranges(native))
        stem = fp.stem
        sem = _load_optional(sem_dir / f"{stem}.npy")
        if sem is not None:
            sem = resample_scan(
                np.asarray(sem, dtype=np.float32).reshape(-1), kind="nearest"
            ).astype(np.int32)
        pos = _load_optional(pos_dir / f"{stem}.npy")
        pose = np.zeros(3, dtype=np.float32)
        if pos is not None:
            p = np.asarray(pos, dtype=np.float32).reshape(-1)
            pose[: min(3, p.size)] = p[: min(3, p.size)]
        out.append(
            {
                "ranges": ranges,
                "semantic": sem,
                "pose": pose,
                "stem": stem,
            }
        )
    return out


def build_arrays(
    root: Path,
    stride: int = 10,
    seed: int = 7,
    ood_envs: list[str] | None = None,
) -> dict:
    seqs = discover_sequences(root)
    if not seqs:
        raise FileNotFoundError(f"no scans_lidar folders under {root}")
    env_names = sorted({e for e, _ in seqs})
    if ood_envs is None:
        # Hold out the last two environments alphabetically as a building shift.
        ood_envs = env_names[-2:] if len(env_names) >= 3 else env_names[-1:]
    ood_set = set(ood_envs)

    ranges_l = []
    labels_l = []
    env_l = []
    traj_l = []
    sid_l = []
    pose_l = []
    split_l = []

    for env, scans_dir in seqs:
        frames = load_sequence_frames(scans_dir, stride=stride)
        n = len(frames)
        if n == 0:
            continue
        id_cut = int(n * 0.8)
        for i, fr in enumerate(frames):
            lab = derive_place(fr["ranges"], fr["semantic"])
            ranges_l.append(fr["ranges"])
            labels_l.append(lab)
            env_l.append(env)
            traj_l.append(env)
            sid_l.append(f"{env}_{fr['stem']}")
            pose_l.append(fr["pose"])
            if env in ood_set:
                split_l.append("test_ood")
            elif i >= id_cut:
                split_l.append("test_id")
            else:
                split_l.append("train")

    ranges = np.stack(ranges_l).astype(np.float32)
    labels = np.asarray(labels_l, dtype=np.int32)
    return {
        "ranges": ranges,
        "labels": labels,
        "env_ids": np.asarray(env_l, dtype=object),
        "traj_ids": np.asarray(traj_l, dtype=object),
        "sample_ids": np.asarray(sid_l, dtype=object),
        "poses": np.stack(pose_l).astype(np.float32),
        "splits": np.asarray(split_l, dtype=object),
        "n_beams": np.int32(N_BEAMS_OUT),
        "max_range": np.float32(MAX_RANGE),
        "fov_deg": np.float32(FOV_DEG),
        "label_names": np.asarray(LABELS),
        "seed": np.int32(seed),
        "ood_envs": np.asarray(list(ood_set), dtype=object),
        "stride": np.int32(stride),
    }
