"""HDC task-aware LiDAR communication research toolkit."""

__version__ = "0.1.0"

LABELS = (
    "corridor",
    "room",
    "doorway",
    "open_area",
    "cluttered_area",
)
LABEL_TO_ID = {name: i for i, name in enumerate(LABELS)}
ID_TO_LABEL = dict(enumerate(LABELS))
