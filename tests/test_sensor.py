from hdc_lidar.channels.sensor_corruption import apply_named
import numpy as np


def test_named_sensor_changes_scan_but_clean_does_not():
    rng = np.random.default_rng(0)
    x = np.full((4, 20), 3.0, dtype=np.float32)
    clean = apply_named("clean", x, rng, max_range=10.0)
    np.testing.assert_array_equal(clean, x)
    dropped = apply_named("beam_drop", x, rng, max_range=10.0, drop_rate=1.0)
    assert float(dropped.max()) == 10.0
    far = np.full((2, 8), 8.0, dtype=np.float32)
    clipped = apply_named("clip", far, rng, max_range=10.0, clip_to=6.0)
    assert float(clipped.max()) == 6.0
