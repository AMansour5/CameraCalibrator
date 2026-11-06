# CameraCalibrator

An interactive tool for calibrating cameras with a checkerboard, built on OpenCV.
It supports two kinds of camera:

| Mode | Camera | Produces |
|------|--------|----------|
| `monocular` | One ordinary camera | Camera matrix `K`, distortion coefficients `D` |
| `stereo` | A **single-sensor stereo camera** that outputs one side-by-side frame (left half + right half) | `K1, D1, K2, D2` for each eye, plus the rotation `R` and translation `T` between them |

The tool shows a live preview, tells you whether the board is detected, lets you save
the good frames, runs the calibration on demand, and can preview the result
(rectified pair for stereo, undistorted image for monocular).

> **Not supported:** two physically separate cameras on two device indices. The stereo
> camera class opens one `cv2.VideoCapture` and splits each frame down the middle.

## Requirements

- Python 3.9+ (exercised on 3.12.3)
- A camera reachable by OpenCV (`/dev/videoN` on Linux; an integer index also works)
- A printed checkerboard on a **rigid, flat** surface

Dependencies are declared in `pyproject.toml`. From the repository root:

```bash
pip install -e .
```

This installs `opencv-python`, `numpy`, `PyYAML` and `zope.interface` (pinned to the ranges
in `pyproject.toml`) and registers a `calibrate-camera` console script. Add `pip install -e
".[dev]"` instead if you also want `pytest`.

Last verified with OpenCV 4.13.0, NumPy 2.4.4, PyYAML 6.0.3.

## Quick start

1. **Describe your board** in `config/checkerboard.yaml`. `columns` and `rows` count
   **inner corners**, not squares (a board with 9 x 6 squares has 8 x 5 inner corners).
   Measure `square_size_mm` on the printed board with a ruler.
2. **Describe your camera** in `config/stereo_camera.yaml` (or `monocular_camera.yaml`).
   For a stereo camera, `combined_width` x `combined_height` is the size of the *whole*
   side-by-side frame, not one eye.
3. **Pick the mode** in `config/calibrator.yaml`: `chosen_calibrator: stereo` or `monocular`.
4. **Run it:**

```bash
calibrate-camera                        # after `pip install -e .`
# or, from the repository root, without installing:
python -m src.services.CameraCalibrator
```

5. Hold the board in view. When the status line says **READY**, press `s` to save the
   frame. Collect 20-30 varied views, then press `c` to calibrate.

## Controls

| Key | Capture mode | Preview mode |
|-----|--------------|--------------|
| `s` | Save the current frame/pair (only when the board is detected, in **both** halves for stereo) | - |
| `c` | Run the calibration in the background and write a new time-stamped result file | - |
| `a` | Accept the latest time-stamped result as the final calibration | Same |
| `x` | Delete the most recently numbered saved image/pair | - |
| `p` | Switch to preview of the latest time-stamped calibration (accepted or not) | - |
| `r` | - | Return to capture mode |
| `q` | Quit. If images were saved or deleted since the last calibration, this first runs a calibration (as a new time-stamped file; the accepted result is untouched) and quits once it finishes | Same |

## What gets written

| Path | Content |
|------|---------|
| `src/images/stereo/left/NNN.png`, `src/images/stereo/right/NNN.png` | Saved stereo pairs (same file name in both folders) |
| `src/images/monocular/NNN.png` | Saved monocular frames |
| `src/matrices/<mode>/time_stamped/<mode>_calib_YYYYMMDD_HHMMSS.npz` | Every calibration run; never overwritten |
| `src/matrices/stereo/stereo_calib.npz` | Accepted stereo calibration result (written only by pressing `a`) |
| `src/matrices/monocular/monocular_calib.npz` | Accepted monocular calibration result (written only by pressing `a`) |

Image folders are created automatically and `*.png` / `*.jpg` are git-ignored, as are all
`.npz` files (`*.npz` in `.gitignore`). File contents are documented in
[docs/calibration-output.md](docs/calibration-output.md).

## Reading the result

The tool prints the RMS reprojection error in pixels, both overall and per captured view (so
a single bad capture doesn't hide inside a good average). Rule of thumb used by the code:
above **1.0 px** (configurable via `max_rms` in `config/calibrator.yaml`) it prints a warning,
but still saves the result as a time-stamped file for you to inspect — it only becomes the
accepted calibration once you press `a`. Lower is better; well under 0.5 px is a good result.
A low RMS alone does not prove the calibration is right, so also check the preview (`p`): in
the stereo preview, the same physical point should sit at the same row in the left and right
images.

## Project layout

```
config/                    YAML settings (calibrator, checkerboard, cameras)
src/
  services/
    CameraCalibrator.py    Entry point + interactive loop (keys, windows, background calibration)
    stereo/                StereoCamera (frame splitting) + StereoCalibrator
    monocular/             MonocularCamera + MonocularCalibrator
  interfaces/              ICamera, ICalibrator (zope.interface contracts)
  helpers/                 CalibrationHelper (OpenCV wrappers shared by both modes)
  utils/                   Configurator (YAML access), Dispatcher (picks the calibrator)
  exceptions/              CameraSetupError, CameraCalibrationError, DifferentImageSizeError, FewImagesError
  matrices/                Calibration results (accepted + time-stamped history)
  tests/                   pytest test_*.py files (see docs/testing.md for which need a camera)
```

## Documentation

| Document | What it covers |
|----------|----------------|
| [docs/usage.md](docs/usage.md) | Step-by-step capture workflow, coverage advice, troubleshooting |
| [docs/configuration.md](docs/configuration.md) | Every config key, defaults, and gotchas |
| [docs/architecture.md](docs/architecture.md) | How the pieces fit together and the main loop |
| [docs/calibration-output.md](docs/calibration-output.md) | `.npz` contents and how to use them (rectification, depth) |
| [docs/api-reference.md](docs/api-reference.md) | Classes and methods |
| [docs/testing.md](docs/testing.md) | The test suite, which files need a camera, and a hardware-free way to test |
| [docs/problems/](docs/problems/README.md) | Remaining known issues, each with evidence, effects and a fix |
| [docs/Camera_Calibration.pdf](docs/Camera_Calibration.pdf) | Camera calibration study notes |