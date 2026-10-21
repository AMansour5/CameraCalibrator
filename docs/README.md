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

- Python 3.8+ (exercised on 3.12.3)
- A camera reachable by OpenCV (`/dev/videoN` on Linux; an integer index also works)
- A printed checkerboard on a **rigid, flat** surface
- Python packages (there is no `requirements.txt` yet, see [problem P08](docs/problems/P08-no-dependency-manifest.md)):

```bash
pip install opencv-python numpy pyyaml zope.interface
```

Last verified with OpenCV 4.13.0, NumPy 2.4.4, PyYAML 6.0.3.

## Quick start

1. **Describe your board** in `config/checkerboard.yaml`. `columns` and `rows` count
   **inner corners**, not squares (a board with 9 x 6 squares has 8 x 5 inner corners).
   Measure `square_size_mm` on the printed board with a ruler.
2. **Describe your camera** in `config/stereo_camera.yaml` (or `monocular_camera.yaml`).
   For a stereo camera, `combined_width` x `combined_height` is the size of the *whole*
   side-by-side frame, not one eye.
3. **Pick the mode** in `config/calibrator.yaml`: `chosen_calibrator: stereo` or `monocular`.
4. **Run from the repository root** (it must be run as a module, see
   [problem P09](docs/problems/P09-entry-point-requires-module-invocation.md)):

```bash
python -m src.services.CameraCalibrator
```

5. Hold the board in view. When the status line says **READY**, press `s` to save the
   frame. Collect 20-30 varied views, then press `c` to calibrate.

## Controls

| Key | Capture mode | Preview mode |
|-----|--------------|--------------|
| `s` | Save the current frame/pair (only when the board is detected, in **both** halves for stereo) | - |
| `c` | Run the calibration on all saved images and write the result file | - |
| `x` | Delete the most recently numbered saved image/pair | - |
| `p` | Switch to preview of the saved calibration | - |
| `r` | - | Return to capture mode |
| `q` | Quit. **If images were saved since the last calibration, this first runs a calibration** (see [P02](docs/problems/P02-calibration-overwrites-saved-result-without-quality-gate.md)) | Same |

## What gets written

| Path | Content |
|------|---------|
| `src/images/stereo/left/NNN.png`, `src/images/stereo/right/NNN.png` | Saved stereo pairs (same file name in both folders) |
| `src/images/monocular/NNN.png` | Saved monocular frames |
| `src/matricies/stereo/stereo_calib.npz` | Stereo calibration result |
| `src/matricies/monocular/monocular_calib.npz` | Monocular calibration result |

Image folders are created automatically and `*.png` / `*.jpg` are git-ignored. The
`.npz` files are **tracked in git** (see [P15](docs/problems/P15-tracked-artifacts-and-machine-specific-config.md)).
File contents are documented in [docs/calibration-output.md](docs/calibration-output.md).

## Reading the result

The tool prints the RMS reprojection error in pixels. Rule of thumb used by the code:
above **1.0 px** it prints a warning. Lower is better; well under 0.5 px is a good
result. A low RMS alone does not prove the calibration is right, so also check the
preview (`p`): in the stereo preview, the same physical point should sit at the same
row in the left and right images.

## Project layout

```
config/                    YAML settings (calibrator, checkerboard, cameras)
src/
  services/
    CameraCalibrator.py    Entry point + interactive loop (keys, windows)
    stereo/                StereoCamera (frame splitting) + StereoCalibrator
    monocular/             MonocularCamera + MonocularCalibrator
  interfaces/              ICamera, ICalibrator (zope.interface contracts)
  helpers/                 CalibrationHelper (OpenCV wrappers shared by both modes)
  utils/                   Configurator (YAML access), Dispatcher (picks the calibrator)
  matricies/               Calibration results (sic: spelling, see P16)
  tests/                   Hardware-dependent scripts (see docs/testing.md)
```

## Documentation

| Document | What it covers |
|----------|----------------|
| [docs/usage.md](docs/usage.md) | Step-by-step capture workflow, coverage advice, troubleshooting |
| [docs/configuration.md](docs/configuration.md) | Every config key, defaults, and gotchas |
| [docs/architecture.md](docs/architecture.md) | How the pieces fit together and the main loop |
| [docs/calibration-output.md](docs/calibration-output.md) | `.npz` contents and how to use them (rectification, depth) |
| [docs/api-reference.md](docs/api-reference.md) | Classes and methods |
| [docs/testing.md](docs/testing.md) | The shipped tests, their limits, and a hardware-free way to test |
| [docs/problems/](docs/problems/README.md) | 16 identified problems, each with evidence, effects and a fix |

*Documentation written against commit `ccaebd1`.*
