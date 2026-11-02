# Testing

The test suite is real `pytest` tests (`test_*.py`, plain `assert` statements), fully
collected by `pytest`. Nine files, 32 tests in total.

## Hardware-free (no camera needed)

These never open a camera and are safe to run at any time, including in CI:

| File | What it covers |
|------|--------------------------------------------------------------------------------|
| `test_configurator.py` | Loading real config files, and `setConfig`'s create/merge behaviour against a temporary project root |
| `test_interfaces.py` | `zope.interface.verify.verifyClass` for `ICamera` and `ICalibrator` against all four implementations |
| `test_calibration_banner.py` | `CameraCalibrator.drawCalibrationBanner` does not mutate its input frame |
| `test_calibration_helper.py` | `CalibrationHelper.perViewErrors` flags the worst of several synthetic views |
| `test_timestamped_calibration.py` | Time-stamped saves never overwrite, `acceptLatest`/`previewFrame` pick the newest file, using a monkeypatched camera and a temporary project root (see below for the pattern) |

Run just these:

```bash
python -m pytest -q src/tests/test_configurator.py src/tests/test_interfaces.py \
    src/tests/test_calibration_banner.py src/tests/test_calibration_helper.py \
    src/tests/test_timestamped_calibration.py
```

## Hardware-dependent (need a real camera)

These construct a real `StereoCamera`/`MonocularCamera`/`StereoCalibrator`/
`MonocularCalibrator`, which opens the device configured in `config/stereo_camera.yaml` /
`config/monocular_camera.yaml` in `__init__`. Without a camera at that index they fail fast
with `CameraSetupError`; `test_*_view_feed` opens a window and blocks on `q`.

| File | What it does |
|------|--------------|
| `test_stereocamera.py` | Opens the stereo camera, grabs a frame, shows a live feed until `q` |
| `test_monocularcamera.py` | Same for the monocular camera |
| `test_stereocalibrator.py` | Builds a real `StereoCalibrator`, grabs a preview frame, and runs a real calibration on whatever is in `src/images/stereo/` |
| `test_monocularcalibrator.py` | Same for `MonocularCalibrator` |
| `test_dispatcher.py` | Builds whichever calibrator `config/calibrator.yaml` selects (opens its camera as a side effect) |

`test_calibrate_method` in the calibrator tests calls the real `calibrate()`. Because
calibration now writes to `.../time_stamped/` and never touches the accepted
`<mode>_calib.npz` directly, running it does **not** overwrite your last accepted result —
worst case it adds an extra time-stamped file.

Running the whole suite without a camera attached will hang or fail on these five files; run
only the hardware-free selection above if you don't have one, or pass `-k` to skip them, for
example:

```bash
python -m pytest -q src/tests -k "not camera and not calibrator and not dispatcher"
```

## Testing the calibrators without a camera

`test_timestamped_calibration.py` shows the pattern used to exercise a calibrator with no
hardware: monkeypatch the camera's `open`/`getFrames` and point `Configurator.getProjectRoot`
at a temporary directory so nothing touches your real `src/images/`/`src/matrices/`:

```python
def _make_calibrator(tmp_path, monkeypatch):
    monkeypatch.setattr(MonocularCamera, "open", lambda self: None)
    monkeypatch.setattr(MonocularCamera, "getFrames", lambda self: np.zeros((20, 20, 3), np.uint8))
    monkeypatch.setattr(Configurator, "getProjectRoot", lambda: str(tmp_path))
    monkeypatch.setattr(
        Configurator, "fetchData",
        lambda self, name: {"columns": 8, "rows": 5} if name == Configurator.CHECKERBOARD else {},
    )
    return MonocularCalibrator()
```

From there, call `saveImage(frame)` for several rendered poses and `calibrate()` as usual.
Calibrating at full 1080p resolution is slow, so keep synthetic frames small for logic tests
(the frames above are 20x20, enough to exercise the save/accept/preview plumbing without
running real corner detection).
