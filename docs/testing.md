# Testing

## What exists

| File | What it does | Camera |
|------|--------------|--------|
| `src/tests/StereoCameraTest.py` | Opens the stereo camera, grabs a frame, shows a live feed until `q` | Required |
| `src/tests/MonocularCameraTest.py` | Same for the monocular camera | Required |
| `src/tests/StereoCalibratorTest.py` | Runs a real calibration on the saved images (only `test_calibrate_method` is enabled in `__main__`) | Opened by the constructor; with none attached it prints an error and carries on, so saved images are what is really needed |
| `src/tests/MonocularCalibratorTest.py` | Constructs the calibrator, grabs a frame, runs a real calibration | Same as above (`test_initialization` does assert the camera opened) |
| `src/tests/DispatcherTest.py` | Builds the configured calibrator and checks it is not `None` | Opened as a side effect; the test still passes without one |
| `src/tests/ConfiguratorTest.py` | Loads configs | No |
| `src/tests/test_configurator_set_config.py` | Pytest-collectible regression test for `Configurator.setConfig` (file creation + key-preserving merge), using a temporary project root | No |

Run any of them from the repository root as a module, for example:

```bash
python -m src.tests.StereoCameraTest
```

## Limits you should know about

These are scripts you run and look at, not an automated suite:

- `pytest` collects **0 tests** from the `*Test.py` files (they are not named `test_*.py`, and
  `ConfiguratorTest` has an `__init__`). `src/tests/test_configurator_set_config.py` is the
  exception: it follows the `test_*.py` convention, so `pytest` does collect and run it.
- `ConfiguratorTest` refers to `Configurator.CAMERA` and the key `cam_index`, neither of
  which exists, and wraps everything in `try/except`, so it prints the error and still
  reports "All tests completed." with exit code 0.
- In the calibrator tests, the calls wrapped in `try/except ... assert False` (`calibrate()`,
  `grabPreviewFrame()`) already catch every exception internally, so those `assert False`
  branches can never run. `test_calibrate_method` also **overwrites your saved calibration**.

Details and fixes: [P07](problems/P07-shipped-tests-cannot-fail-and-are-not-collected.md).

## Hardware-free tests that work today

These need no camera and run under `pytest` (save as `src/tests/test_hardware_free.py`
and run `python -m pytest -q src/tests/test_hardware_free.py` from the repository root; they pass):

```python
import numpy as np
from src.helpers.CalibrationHelper import CalibrationHelper
from src.services.stereo.StereoCamera import StereoCamera
from src.utils.Configurator import Configurator


class FakeCapture:
    """Stands in for cv2.VideoCapture."""
    def __init__(self, frame):
        self.frame = frame

    def read(self):
        return True, self.frame

    def release(self):
        pass


def test_stereo_camera_splits_the_frame_in_half():
    cam = StereoCamera({"camera_index": 0})
    frame = np.zeros((10, 8, 3), np.uint8)
    frame[:, 4:] = 255                              # right half is white
    cam._StereoCamera__capture = FakeCapture(frame)  # name-mangled private attribute
    left, right = cam.getFrames()
    assert left.shape == right.shape == (10, 4, 3)
    assert left.max() == 0 and right.min() == 255


def test_object_points_are_in_millimetres():
    objp = CalibrationHelper.buildObjectPoints((8, 5), 30)
    assert objp.shape == (40, 3)
    assert objp[1, 0] == 30      # next corner along a row is one square away
    assert objp[8, 1] == 30      # first corner of the next row
    assert (objp[:, 2] == 0).all()


def test_checkerboard_config_has_required_keys():
    cfg = Configurator().fetchData(Configurator.CHECKERBOARD)
    assert {"columns", "rows", "square_size_mm"} <= set(cfg)
```

## Testing the calibrator without a camera

Replace the camera methods and feed synthetic checkerboard frames. This is how the problems
in [docs/problems](problems/README.md) were reproduced:

```python
from src.services.stereo.StereoCamera import StereoCamera
current = {"pair": (left_img, right_img)}              # numpy images you generate
StereoCamera.open = lambda self: None
StereoCamera.getFrames = lambda self: current["pair"]
```

Then construct `StereoCalibrator()`, call `saveImage((left, right))` for several rendered
poses, and call `calibrate()`. Two cautions: the calibrator writes to the real
`src/images/` and `src/matrices/` folders (point `Configurator.getProjectRoot` at a
temporary copy of the project to avoid clobbering your data), and calibration at full
1080p resolution is slow, so reduce the frame size for logic tests.
