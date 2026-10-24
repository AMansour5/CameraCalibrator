# Usage guide

## Before you start

1. **Board.** Print a checkerboard and mount it on something rigid and flat (foam board,
   acrylic, glass). Paper that bows is the most common hidden source of error.
2. **Measure it.** Use a ruler on the *printed* square, not the value in the file you
   printed from; printers scale. Put it in `config/checkerboard.yaml` as `square_size_mm`.
3. **Count inner corners.** `columns` x `rows` are the corners where four squares meet.
   A 9 x 6 *squares* board is `columns: 8`, `rows: 5`.
   Prefer a pattern where one count is even and the other odd (8 x 5 is fine). If both
   are even or both are odd, the pattern looks the same rotated 180 degrees and the
   corner order can flip between the left and right views ([P13](problems/P13-no-calibration-quality-diagnostics-or-safeguards.md)).
4. **Camera.** Set the device and the *combined* resolution in the camera config file
   ([configuration.md](configuration.md)).

## Workflow

### 1. Start

```bash
python -m src.services.CameraCalibrator      # from the repository root
```

At startup the console prints `Requested WxH, camera reports WxH`. If they differ you will
also see a `WARNING`; fix the config before capturing anything, because for a stereo
camera the left/right split is computed from the width the camera really delivers.

### 2. Capture

The window shows the live image with detected corners drawn on it and a status line:
`READY` (green) or `board not found ...` (red), plus how many images are saved.
`s` only saves when the board is detected (in **both** halves for stereo).

Aim for **20-30 good views**. What matters is variety, not count:

- Cover the **whole frame, especially the edges and corners**. Lens distortion is
  strongest there, and a model fitted only to the centre extrapolates badly at the edges.
- **Tilt** the board in different directions (not just move it). Flat-on views barely
  constrain the focal length.
- Vary the **distance** across the range you will actually use.
- Hold the board **still** when you press `s` to avoid motion blur.
- Keep the whole board inside both halves with a margin; avoid glare on the squares.

Made a mistake? `x` deletes the last-numbered saved image (the one at index *saved count - 1*). See
[P01](problems/P01-image-numbering-overwrites-existing-pairs.md) before deleting files by hand.

### 3. Calibrate

Press `c`. The console prints how many images were usable, per-camera RMS error, then
the stereo RMS, the baseline (`|T|`, in mm) and the rotation `R`. During this time the
window does not update ([P12](problems/P12-calibration-blocks-the-ui-loop.md)). The result
is written to `src/matrices/<mode>/<mode>_calib.npz`, **replacing any previous result**
([P02](problems/P02-calibration-overwrites-saved-result-without-quality-gate.md)).

### 4. Check it

- **RMS reprojection error.** The code warns above 1.0 px. Aim well below that.
- **Baseline (stereo).** Compare `|T|` with the physical distance between the two lenses.
  A consistent percentage error usually means `square_size_mm` is wrong.
- **Preview (`p`).** Stereo shows the rectified pair side by side; the same physical
  point must sit on the same horizontal row in both images. Monocular shows the
  undistorted image; straight lines in the world must look straight. `r` returns to capture.

If the live resolution differs from the one used for calibration the preview is wrong
without warning ([P04](problems/P04-preview-ignores-stored-image-size.md)).

### 5. Quit

`q` quits. If you saved images since the last calibration, it **calibrates first** and
overwrites the result. To quit without that, calibrate (`c`) or stop with `Ctrl+C`.

## Starting over

Delete the whole `src/images/<mode>/` folder (both `left/` and `right/` for stereo)
rather than individual files; deleting single files in the middle makes the next saved
image overwrite an existing one ([P01](problems/P01-image-numbering-overwrites-existing-pairs.md)).

## Troubleshooting

| What you see | Likely cause | What to do |
|---|---|---|
| `Could not open camera index ...` | Wrong device path/index, device busy, or no permission | Check `ls /dev/video*` or `v4l2-ctl --list-devices`; close other apps using the camera; on Linux make sure your user can read the device |
| `Camera is not opened.` then `Error opening camera: ...`, program ends with `'NoneType' object has no attribute 'release'` | The camera failed to open; the last message is a side effect | Read the first error above it ([P05](problems/P05-camera-open-failure-crashes-on-release.md)) |
| `WARNING: camera did not accept the requested resolution` | Driver offers different modes | Set `combined_width/height` to what it reports |
| `board not found in both halves` | Board partly out of frame, glare, too tilted, too small, or `columns/rows` count squares instead of inner corners | Re-check the counts; improve lighting; move closer |
| `Mismatched or empty capture sets` | `left/` and `right/` have different numbers of files | Delete both folders and recapture |
| `WARNING: only N pairs have corners in both views` | Too few usable pairs | Capture more; the result is still saved ([P02](problems/P02-calibration-overwrites-saved-result-without-quality-gate.md)) |
| `NOTE: stereo RMS > 1.0 px is high` | Poor edge coverage, bendy board, motion blur, or wrong `square_size_mm` | Recapture; the result is still saved |
| `Error: The file '...yaml' was not found.` followed by a `TypeError` | Missing config file | Restore the file ([P06](problems/P06-errors-printed-not-raised-exit-code-always-zero.md)) |
| `ModuleNotFoundError: No module named 'src'` | Run as a script instead of a module | `python -m src.services.CameraCalibrator` from the repo root |
| `ModuleNotFoundError: No module named 'zope'` (or `cv2`, `yaml`) | Dependency not installed | `pip install opencv-python numpy pyyaml zope.interface` |
| Preview looks stretched or shifted | Live resolution differs from calibration resolution | Restore the original resolution settings and recalibrate if you changed them |
