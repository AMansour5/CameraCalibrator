# P04: Preview builds its maps from the live frame size and ignores the size stored in the calibration

**Severity:** Medium (silently wrong preview) **Evidence:** reproduced by running the real `StereoCalibrator`
**Component:** `StereoCalibrator.previewFrame`, `MonocularCalibrator.previewFrame`

## What the code does

Calibration stores `img_size` in the `.npz` (`Stereo:206`, `Monocular:160`), but `previewFrame` never reads it.
It takes the size from the frame it just grabbed (`Stereo:131`, `Monocular:117`) and builds the rectification /
undistortion maps for that size, using `K` and `D` that are in pixel units of the *calibration* resolution.

## How to trigger it

Calibrate at one resolution, then change `combined_width`/`combined_height` (or let the driver fall back to a
different mode), and press `p`.

## Evidence

Calibrated at 960 x 540 per eye, then fed 640 x 360 frames:

```
calibrated at (w,h): (960, 540) | live frames (w,h): (640, 360)
preview returned an image: True | rectify maps built for (w,h): (640, 360) | messages printed: ''
```

No exception, no warning, and the status bar still says `CALIBRATED PREVIEW`.

## Effects

- A wrong rectification/undistortion is displayed as if it were the calibration result. You may
  conclude a good calibration is bad (or the reverse).
- The same mismatch silently breaks any later code that loads the file and applies it to frames of a
  different size ([calibration-output.md](../calibration-output.md)).
- Less obvious trigger: copying someone else's `.npz` ([P15](P15-tracked-artifacts-and-machine-specific-config.md)).

## Suggested fix

```python
data = np.load(self.OUTPUT_FILE)
calib_size = tuple(int(v) for v in data["img_size"])
live_size = (left_frame.shape[1], left_frame.shape[0])
if live_size != calib_size:
    print(f"Calibrated at {calib_size} but live frames are {live_size}. "
          "Restore the resolution or recalibrate.")
    return None            # the loop already handles None by returning to capture mode
```
