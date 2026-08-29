"""2D occupancy floorplans and LiDAR raycasting."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from hdc_lidar import LABEL_TO_ID, LABELS


@dataclass
class Wall:
    x0: float
    y0: float
    x1: float
    y1: float


@dataclass
class Obstacle:
    x0: float
    y0: float
    x1: float
    y1: float


@dataclass
class Region:
    name: str
    x0: float
    y0: float
    x1: float
    y1: float

    def contains(self, x: float, y: float, margin: float = 0.0) -> bool:
        return (self.x0 + margin) <= x <= (self.x1 - margin) and (self.y0 + margin) <= y <= (
            self.y1 - margin
        )

    def sample_pose(self, rng: np.random.Generator, margin: float = 0.35) -> tuple[float, float, float]:
        x = float(rng.uniform(self.x0 + margin, self.x1 - margin))
        y = float(rng.uniform(self.y0 + margin, self.y1 - margin))
        yaw = float(rng.uniform(-np.pi, np.pi))
        return x, y, yaw

    def centerline_waypoints(self, step: float = 0.4, axis: str = "x") -> list[tuple[float, float]]:
        cx = 0.5 * (self.x0 + self.x1)
        cy = 0.5 * (self.y0 + self.y1)
        pts: list[tuple[float, float]] = []
        if axis == "x":
            xs = np.arange(self.x0 + 0.4, self.x1 - 0.4, step)
            pts = [(float(x), cy) for x in xs]
        else:
            ys = np.arange(self.y0 + 0.4, self.y1 - 0.4, step)
            pts = [(cx, float(y)) for y in ys]
        return pts


@dataclass
class Building:
    env_id: str
    regions: list[Region]
    walls: list[Wall]
    obstacles: list[Obstacle] = field(default_factory=list)
    doorways: list[Region] = field(default_factory=list)

    def label_at(self, x: float, y: float) -> str:
        for d in self.doorways:
            if d.contains(x, y, margin=0.0):
                return "doorway"
        # smallest containing region wins (doorway already handled)
        hits = [r for r in self.regions if r.contains(x, y, margin=0.0)]
        if not hits:
            return "open_area"
        hits.sort(key=lambda r: (r.x1 - r.x0) * (r.y1 - r.y0))
        return hits[0].name


def _rect_walls(x0: float, y0: float, x1: float, y1: float) -> list[Wall]:
    return [
        Wall(x0, y0, x1, y0),
        Wall(x1, y0, x1, y1),
        Wall(x1, y1, x0, y1),
        Wall(x0, y1, x0, y0),
    ]


def _punch_door(walls: list[Wall], x0: float, y0: float, x1: float, y1: float, gap: float = 0.12) -> list[Wall]:
    """Remove wall segments that fully lie inside a door opening (with slack)."""
    kept: list[Wall] = []
    for w in walls:
        mx, my = 0.5 * (w.x0 + w.x1), 0.5 * (w.y0 + w.y1)
        if (x0 - gap) <= mx <= (x1 + gap) and (y0 - gap) <= my <= (y1 + gap):
            # split long walls around the door instead of dropping entire edges
            if abs(w.y0 - w.y1) < 1e-6:
                # horizontal wall
                y = w.y0
                left, right = min(w.x0, w.x1), max(w.x0, w.x1)
                d0, d1 = min(x0, x1), max(x0, x1)
                if left < d0:
                    kept.append(Wall(left, y, d0, y))
                if d1 < right:
                    kept.append(Wall(d1, y, right, y))
            elif abs(w.x0 - w.x1) < 1e-6:
                x = w.x0
                bot, top = min(w.y0, w.y1), max(w.y0, w.y1)
                d0, d1 = min(y0, y1), max(y0, y1)
                if bot < d0:
                    kept.append(Wall(x, bot, x, d0))
                if d1 < top:
                    kept.append(Wall(x, d1, x, top))
            continue
        kept.append(w)
    return kept


def _add_box_obstacles(x0: float, y0: float, x1: float, y1: float, rng: np.random.Generator, n: int) -> list[Obstacle]:
    obs: list[Obstacle] = []
    for _ in range(n):
        w = float(rng.uniform(0.35, 0.9))
        h = float(rng.uniform(0.35, 0.9))
        x = float(rng.uniform(x0 + 0.4, max(x0 + 0.5, x1 - w - 0.4)))
        y = float(rng.uniform(y0 + 0.4, max(y0 + 0.5, y1 - h - 0.4)))
        obs.append(Obstacle(x, y, x + w, y + h))
    return obs


def make_office_building(env_id: str, rng: np.random.Generator, variant: str = "a") -> Building:
    """Compose corridor / rooms / doorway / open lobby / cluttered storage."""
    if variant == "a":
        corridor = Region("corridor", 0.0, 4.0, 18.0, 6.2)
        rooms = [
            Region("room", 1.0, 0.0, 5.5, 4.0),
            Region("room", 6.5, 0.0, 11.0, 4.0),
            Region("room", 1.0, 6.2, 5.5, 10.2),
            Region("room", 6.5, 6.2, 11.0, 10.2),
        ]
        lobby = Region("open_area", 18.0, 1.5, 26.0, 9.0)
        storage = Region("cluttered_area", 12.0, 6.2, 16.5, 10.5)
        doors = [
            Region("doorway", 2.6, 3.75, 3.6, 4.25),
            Region("doorway", 8.2, 3.75, 9.2, 4.25),
            Region("doorway", 2.6, 5.95, 3.6, 6.45),
            Region("doorway", 8.2, 5.95, 9.2, 6.45),
            Region("doorway", 17.75, 4.7, 18.25, 5.6),
            Region("doorway", 13.6, 5.95, 14.6, 6.45),
        ]
    elif variant == "b":
        corridor = Region("corridor", 0.0, 5.0, 20.0, 7.4)
        rooms = [
            Region("room", 0.8, 0.2, 6.2, 5.0),
            Region("room", 7.4, 0.2, 12.8, 5.0),
            Region("room", 14.0, 0.2, 19.2, 5.0),
            Region("room", 2.0, 7.4, 8.0, 12.0),
        ]
        lobby = Region("open_area", 20.0, 2.0, 28.5, 11.0)
        storage = Region("cluttered_area", 10.0, 7.4, 15.5, 12.2)
        doors = [
            Region("doorway", 2.8, 4.75, 3.9, 5.25),
            Region("doorway", 9.4, 4.75, 10.5, 5.25),
            Region("doorway", 16.0, 4.75, 17.1, 5.25),
            Region("doorway", 4.4, 7.15, 5.5, 7.65),
            Region("doorway", 19.75, 5.7, 20.25, 6.7),
            Region("doorway", 12.0, 7.15, 13.1, 7.65),
        ]
    else:  # OOD: different proportions, narrower hall, denser clutter
        corridor = Region("corridor", 0.0, 6.0, 22.0, 7.6)
        rooms = [
            Region("room", 0.5, 0.0, 7.5, 6.0),
            Region("room", 8.5, 0.0, 14.0, 6.0),
            Region("room", 1.0, 7.6, 6.0, 13.5),
            Region("room", 15.0, 7.6, 21.5, 14.0),
        ]
        lobby = Region("open_area", 22.0, 0.5, 32.0, 12.5)
        storage = Region("cluttered_area", 8.0, 7.6, 14.2, 13.8)
        doors = [
            Region("doorway", 3.2, 5.75, 4.4, 6.25),
            Region("doorway", 10.4, 5.75, 11.5, 6.25),
            Region("doorway", 2.8, 7.35, 3.9, 7.85),
            Region("doorway", 17.4, 7.35, 18.5, 7.85),
            Region("doorway", 21.75, 6.4, 22.25, 7.3),
            Region("doorway", 10.4, 7.35, 11.6, 7.85),
        ]

    regions = [corridor, lobby, storage, *rooms]
    walls: list[Wall] = []
    for r in regions:
        walls.extend(_rect_walls(r.x0, r.y0, r.x1, r.y1))
    for d in doors:
        walls = _punch_door(walls, d.x0, d.y0, d.x1, d.y1)

    n_boxes = 7 if variant == "ood" else 4
    obstacles = _add_box_obstacles(storage.x0, storage.y0, storage.x1, storage.y1, rng, n=n_boxes)
    if variant == "ood":
        # extra clutter leaking into a room
        obstacles += _add_box_obstacles(rooms[0].x0, rooms[0].y0, rooms[0].x1, rooms[0].y1, rng, n=3)
    for ob in obstacles:
        walls.extend(_rect_walls(ob.x0, ob.y0, ob.x1, ob.y1))

    return Building(env_id=env_id, regions=regions, walls=walls, obstacles=obstacles, doorways=doors)


def _ray_segment_hit(
    ox: float, oy: float, dx: float, dy: float, wall: Wall, max_range: float
) -> float | None:
    """Return range if the ray origin+t*dir hits the segment, else None."""
    vx, vy = wall.x1 - wall.x0, wall.y1 - wall.y0
    denom = dx * vy - dy * vx
    if abs(denom) < 1e-9:
        return None
    qx, qy = wall.x0 - ox, wall.y0 - oy
    t = (qx * vy - qy * vx) / denom
    u = (qx * dy - qy * dx) / denom
    if t < 1e-4 or t > max_range or u < 0.0 or u > 1.0:
        return None
    return float(t)


def raycast_scan(
    x: float,
    y: float,
    yaw: float,
    walls: list[Wall],
    n_beams: int,
    max_range: float,
    angle_min: float = 0.0,
    angle_max: float = 2 * np.pi,
) -> np.ndarray:
    angles = np.linspace(angle_min, angle_max, n_beams, endpoint=False) + yaw
    ranges = np.full(n_beams, max_range, dtype=np.float32)
    c = np.cos(angles)
    s = np.sin(angles)
    for i in range(n_beams):
        best = max_range
        dx, dy = float(c[i]), float(s[i])
        for w in walls:
            hit = _ray_segment_hit(x, y, dx, dy, w, max_range)
            if hit is not None and hit < best:
                best = hit
        ranges[i] = best
    return ranges


def interpolate_path(waypoints: list[tuple[float, float]], step: float) -> list[tuple[float, float, float]]:
    if len(waypoints) < 2:
        return []
    poses: list[tuple[float, float, float]] = []
    for (x0, y0), (x1, y1) in zip(waypoints[:-1], waypoints[1:]):
        dist = float(np.hypot(x1 - x0, y1 - y0))
        n = max(1, int(np.ceil(dist / step)))
        yaw = float(np.arctan2(y1 - y0, x1 - x0))
        for k in range(n):
            t = k / n
            poses.append((float(x0 + t * (x1 - x0)), float(y0 + t * (y1 - y0)), yaw))
    x1, y1 = waypoints[-1]
    poses.append((x1, y1, poses[-1][2] if poses else 0.0))
    return poses


def building_waypoints(building: Building) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for r in building.regions:
        axis = "x" if (r.x1 - r.x0) >= (r.y1 - r.y0) else "y"
        pts.extend(r.centerline_waypoints(step=0.45, axis=axis))
    for d in building.doorways:
        pts.append((0.5 * (d.x0 + d.x1), 0.5 * (d.y0 + d.y1)))
    return pts


def generate_dataset(
    n_beams: int = 180,
    max_range: float = 10.0,
    seed: int = 7,
    range_noise: float = 0.015,
    n_traj_per_env: int = 3,
) -> dict:
    rng = np.random.default_rng(seed)
    specs = [
        ("env_a", "a", "train"),
        ("env_b", "b", "train"),
        ("env_ood", "ood", "ood"),
    ]
    ranges_l: list[np.ndarray] = []
    labels_l: list[int] = []
    env_l: list[str] = []
    traj_l: list[str] = []
    sid_l: list[str] = []
    pose_l: list[list[float]] = []
    split_l: list[str] = []
    buildings: dict[str, Building] = {}

    for env_id, variant, group in specs:
        building = make_office_building(env_id, rng, variant=variant)
        buildings[env_id] = building
        base_wp = building_waypoints(building)
        n_traj = 1 if group == "ood" else n_traj_per_env
        for t in range(n_traj):
            traj_id = f"{env_id}_traj{t}"
            wp = list(base_wp)
            rng.shuffle(wp)
            # keep a connected-ish tour by sorting along x then weaving
            wp.sort(key=lambda p: (round(p[1], 0), p[0]))
            if t % 2 == 1:
                wp = list(reversed(wp))
            poses = interpolate_path(wp, step=0.35)
            # extra doorway samples so the rare class is usable
            extra = []
            for d in building.doorways:
                for _ in range(6):
                    extra.append(d.sample_pose(rng, margin=0.05))
            all_poses = poses + extra
            # hold out one trajectory in train envs as ID test
            if group == "train":
                split = "test_id" if t == n_traj_per_env - 1 else "train"
            else:
                split = "test_ood"
            for i, (x, y, yaw) in enumerate(all_poses):
                yaw_n = yaw + float(rng.normal(0, 0.05))
                scan = raycast_scan(x, y, yaw_n, building.walls, n_beams, max_range)
                if range_noise > 0:
                    scan = np.clip(scan + rng.normal(0, range_noise, size=scan.shape), 0.05, max_range)
                    scan = scan.astype(np.float32)
                lab = building.label_at(x, y)
                ranges_l.append(scan)
                labels_l.append(LABEL_TO_ID[lab])
                env_l.append(env_id)
                traj_l.append(traj_id)
                sid_l.append(f"{traj_id}_{i:05d}")
                pose_l.append([x, y, yaw_n])
                split_l.append(split)

    data = {
        "ranges": np.stack(ranges_l).astype(np.float32),
        "labels": np.asarray(labels_l, dtype=np.int32),
        "env_ids": np.asarray(env_l),
        "traj_ids": np.asarray(traj_l),
        "sample_ids": np.asarray(sid_l),
        "poses": np.asarray(pose_l, dtype=np.float32),
        "splits": np.asarray(split_l),
        "max_range": np.float32(max_range),
        "n_beams": np.int32(n_beams),
        "label_names": np.asarray(LABELS),
        "seed": np.int32(seed),
    }
    return {"arrays": data, "buildings": buildings}


__all__ = [
    "Building",
    "Region",
    "Wall",
    "generate_dataset",
    "make_office_building",
    "raycast_scan",
    "LABELS",
]
