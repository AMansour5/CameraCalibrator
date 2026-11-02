# Identified problems

An earlier audit of this project (read every source file, then ran the code) found 16
problems. Twelve of them have since been fixed in the codebase — quality-gated, backed-up
calibration saves; a module entry point and installable package; real, collectible tests;
raised exceptions instead of printed errors; a non-blocking calibration thread; and more — and
have been removed from this list. **Four remain**, each with its own file: what the code does
(with file and line), how to trigger it, the evidence, the effects, and a suggested fix.

Severity:

- **Medium**: misleading or incomplete behaviour, or something that affects the accuracy of
  the result, without causing data loss.
- **Low**: polish, convenience, and portability.

| ID | Problem | Severity | Evidence |
|----|---------|----------|----------|
| [P01](P01-stereo-calibration-does-not-save-rectification-outputs.md) | The saved stereo calibration does not include the rectification outputs (`Q`, `R1`, `R2`, `P1`, `P2`) | Medium | Code + file inspection |
| [P02](P02-no-orientation-check-adaptive-subpixel-window-or-held-out-validation.md) | No checkerboard-orientation check, adaptive sub-pixel window, or held-out validation | Medium | Code reading + experiment |
| [P03](P03-live-corner-detection-runs-at-full-resolution-every-frame.md) | Live corner detection runs at full resolution on every displayed frame | Low | Code + relative timing |
| [P04](P04-shipped-camera-config-is-machine-specific.md) | The shipped camera config defaults are specific to one machine | Low | Repository inspection |

## What's already been fixed

For context, the issues that were found and have since been resolved:

- Image numbering derived from the highest existing file name instead of a file count, so
  deleting a file by hand no longer causes the next save to silently overwrite another image.
- Calibration results are written to a new time-stamped file under `.../time_stamped/` and
  never touch the accepted `<mode>_calib.npz` until you press `a` to promote them — no more
  silent, unconditional overwrite of a good calibration, and no more losing it with no backup.
- Deleting an image now marks the calibration dirty, the same as saving one.
- The preview now checks the live frame size against the size stored in the calibration file
  and raises `DifferentImageSizeError` instead of silently building wrong rectification maps.
- A camera that fails to open now raises a clear `CameraSetupError`/`RuntimeError`, and
  `release()` is a no-op when there is no camera to release.
- Failures are raised (`FileNotFoundError`, `TypeError`, `RuntimeError`,
  `CameraCalibrationError`, `CameraSetupError`, `DifferentImageSizeError`, `ValueError`)
  instead of printed and swallowed; an uncaught exception now exits with a non-zero status.
- The test suite was rewritten as real `test_*.py` pytest files with real assertions; it is
  collected and can fail.
- Dependencies are declared in `pyproject.toml` (`pip install -e .`), including version ranges.
- The project is installable and ships a console script (`calibrate-camera`), so it no longer
  has to be run as `python -m src...` from the repository root (that still works too).
- The stereo file now keeps the essential and fundamental matrices (`E`, `F`); the monocular
  file no longer reuses the misleading `R`/`T` names for per-image board poses — it saves
  `rvecs`/`tvecs` instead. Both files record `checkerboard` and `square_size_mm`.
- `ICamera`/`ICalibrator` docstrings now match what the implementations actually do, and
  `src/tests/test_interfaces.py` runs `zope.interface.verify.verifyClass` against all four
  implementations.
- Calibration now runs on a worker thread with a "CALIBRATING..." banner, so the window stays
  responsive and `q` waits for it to finish instead of freezing.
- Dead code, an unused constructor argument, a duplicate `Configurator` instantiation, mixed
  indentation, and the misspelled `matricies` results folder have all been cleaned up; the
  folder is `src/matrices/` and its `.npz` contents are git-ignored.

## How the remaining ones were verified

- Read the current source for every component referenced above and in the remaining problem
  files, and ran the real `StereoCalibrator`/`MonocularCalibrator` where relevant.
- Loaded a freshly produced time-stamped `.npz` file and compared its keys against the code
  that builds it and against the suggested schema.
- Ran the hardware-free part of the test suite (`python -m pytest -q src/tests/test_configurator.py
  src/tests/test_interfaces.py src/tests/test_calibration_banner.py
  src/tests/test_calibration_helper.py src/tests/test_timestamped_calibration.py`) and confirmed
  it passes.
- Environment: CPython 3.12, OpenCV 4.13.0, NumPy 2.4.4, PyYAML 6.0.3.

**Not verified:** behaviour on a real camera beyond what was already open in the sandbox
(driver buffering, device permissions across different hardware), and Windows/macOS. Timing
figures are from a single-core sandbox and are only quoted as relative scale.

## What works well

Worth keeping in mind while working on the above:

- **The calibration core is numerically sound.** On synthetic data with known ground truth, 16
  pairs recovered `fx = 532.5` (true 532.5 at half resolution) and a baseline of 119.2 mm (true
  119.3 mm) at 0.087 px RMS.
- **Clean layering.** Loop -> dispatcher -> interface -> implementation. A third camera type is
  a small addition.
- **Sound stereo practice.** Intrinsics are solved per camera first and then held fixed
  (`CALIB_FIX_INTRINSIC`); only pairs detected in *both* views are used; object points are in
  millimetres so the baseline comes out in real units.
- **Raw frames are saved**, not the annotated preview, and as lossless PNG.
- **The camera class checks the resolution the driver actually accepted** and warns when it
  differs, which prevents a whole class of wrong-split mistakes.
- **The accept/preview workflow is safe by construction**: `calibrate()` can be run as many
  times as you like without risking the last good result, and `previewFrame()` always shows the
  latest time-stamped output, accepted or not, so you can judge a calibration before committing
  to it.
- **Per-view reprojection errors** make it possible to spot the one bad capture in a set instead
  of only seeing a single aggregate RMS.
