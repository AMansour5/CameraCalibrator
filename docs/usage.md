# Usage guide

## Before you start

1. **Board.** Print a checkerboard and mount it on something rigid and flat (foam board,
   acrylic, glass). Paper that bows is the most common hidden source of error.
2. **Measure it.** Use a ruler on the *printed* square, not the value in the file you printed
   from; printers scale. Put it in `config/checkerboard.yaml` as `square_size_mm`.
3. **Count inner corners.** `columns` x `rows` are the corners where four squares meet. A
   9 x 6 *squares* board is `columns: 8`, `rows: 5`.
   Prefer a pattern where one count is even and the other odd (8 x 5 is fine). If both are
   even or both are odd, the pattern looks the same rotated 180 degrees and the corner order
   can flip between the left and right views ([P02](problems/P02-no-orientation-check-adaptive-subpixel-window-or-held-out-validation.md)).
4. **Camera.** Set the device and the *combined* resolution in the camera config file
   ([configuration.md](configuration.md)).

## Workflow

### 1. Start

```bash
calibrate-camera                        # after `pip install -e .`
# or, from the repository root, without installing:
python -m src.services.CameraCalibrator
```

At startup the console prints `Requested WxH, camera reports WxH`. If they differ you will
also see a `WARNING`; fix the config before capturing anything, because for a stereo camera
the left/right split is computed from the width the camera really delivers. If the camera
can't be opened at all, the program raises a clear error and exits instead of starting with a
blank window.

### 2. Capture

The window shows the live image with detected corners drawn on it and a status line:
`READY` (green) or `board not found ...` (red), plus how many images are saved. `s` only saves
when the board is detected (in **both** halves for stereo).

Aim for **20-30 good views**. What matters is variety, not count:

- Cover the **whole frame, especially the edges and corners**. Lens distortion is strongest
  there, and a model fitted only to the centre extrapolates badly at the edges.
- **Tilt** the board in different directions (not just move it). Flat-on views barely
  constrain the focal length.
- Vary the **distance** across the range you will actually use.
- Hold the board **still** when you press `s` to avoid motion blur.
- Keep the whole board inside both halves with a margin; avoid glare on the squares.

Made a mistake? `x` deletes the last-numbered saved image and marks the calibration dirty.
Deleting files by hand is also safe now: the next saved image is numbered from the highest
existing file name, not a plain count, so it won't collide with one you left in place.

### 3. Calibrate

Press `c` (or `q` when there are unsaved images). A red "CALIBRATING..." banner appears over
the still-live preview while the pipeline runs in the background, so the window stays
responsive. The console prints how many images were usable, each view's reprojection error
(with the worst one called out), per-camera RMS, then the stereo RMS, the baseline (`|T|`, in
mm) and the rotation `R`.

The result is written to a **new** file,
`src/matrices/<mode>/time_stamped/<mode>_calib_YYYYMMDD_HHMMSS.npz`; the accepted
`<mode>_calib.npz` is **not** changed. Press `a` to accept the latest time-stamped result — it
is copied over `src/matrices/<mode>/<mode>_calib.npz`. Preview (`p`) always shows the latest
time-stamped result, accepted or not, so you can judge it before accepting. Time-stamped files
are never deleted automatically, so you always have a trail of previous runs to fall back to.

### 4. Check it

- **RMS reprojection error.** The code warns above 1.0 px (configurable via `max_rms` in
  `config/calibrator.yaml`). Aim well below that.
- **Per-view errors.** If one view stands out well above the rest, it's usually the one to
  recapture rather than accepting a worse overall result.
- **Baseline (stereo).** Compare `|T|` with the physical distance between the two lenses. A
  consistent percentage error usually means `square_size_mm` is wrong.
- **Preview (`p`).** Stereo shows the rectified pair side by side; the same physical point
  must sit on the same horizontal row in both images. Monocular shows the undistorted image;
  straight lines in the world must look straight. `r` returns to capture.

If the live resolution differs from the one used for calibration, `previewFrame()` raises
`DifferentImageSizeError` rather than silently showing a wrong preview.

### 5. Quit

`q` quits. If you saved or deleted images since the last calibration, it runs `calibrate()`
first (as a new time-stamped file, not overwriting the accepted result) and then quits once
that finishes. To quit immediately, calibrate (`c`) first so nothing is left dirty.

## Starting over

Delete the whole `src/images/<mode>/` folder (both `left/` and `right/` for stereo), or
individual files — either is safe now, since the next saved file's number always comes from
the highest one still present.

## Troubleshooting

| What you see | Likely cause | What to do |
|---|---|---|
| `CameraSetupError: Failed to open ... camera: Could not open camera index ...` | Wrong device path/index, device busy, or no permission | Check `ls /dev/video*` or `v4l2-ctl --list-devices`; close other apps using the camera; on Linux make sure your user can read the device |
| `WARNING: camera did not accept the requested resolution` | Driver offers different modes | Set `combined_width/height` (or `width/height`) to what it reports |
| `board not found in both halves` | Board partly out of frame, glare, too tilted, too small, or `columns/rows` count squares instead of inner corners | Re-check the counts; improve lighting; move closer |
| `CameraCalibrationError: ... Mismatched or empty capture sets` | `left/` and `right/` have different numbers of files | Delete both folders and recapture |
| `WARNING: only N pairs have corners in both views` | Too few usable pairs | Capture more; the result is still saved as a time-stamped file (not accepted until you press `a`) |
| `NOTE: stereo RMS > 1.0 px is high` / `NOTE: RMS > ... px is high` | Poor edge coverage, bendy board, motion blur, or wrong `square_size_mm` | Recapture; the result is still saved as a time-stamped file |
| `FileNotFoundError: ... was not found` | Missing config file | Restore the file in `config/` |
| `ModuleNotFoundError: No module named 'src'` | Run as a script instead of a module | `python -m src.services.CameraCalibrator` from the repo root, or install the package and use `calibrate-camera` |
| `ModuleNotFoundError: No module named 'cv2'` (or `yaml`, `zope`) | Dependencies not installed | `pip install -e .` from the repository root |
| Preview looks stretched or shifted | Live resolution differs from calibration resolution | Restore the original resolution settings and recalibrate if you changed them |
