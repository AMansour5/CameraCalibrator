# P02: No checkerboard-orientation check, adaptive sub-pixel window, or held-out validation

**Severity:** Medium (affects accuracy, not crashes) **Evidence:** code reading and a small experiment
**Component:** `CalibrationHelper`, `StereoCalibrator`, `MonocularCalibrator`

## What the code does

`CalibrationHelper.perViewErrors` now computes and prints each view's reprojection RMS and
flags the worst one; both calibrators call it once per camera after `calibrateCamera`. That
fixed the original "only one global RMS number" complaint (a single bad capture used to be
invisible in the aggregate error). Four related gaps remain:

1. **No check on pattern orientation.** If `columns` and `rows` are both even or both odd, the
   corner grid looks identical after a 180 degree rotation, so the detector can number the
   corners from opposite ends in the left and right views. The shipped 8 x 5 is safe (one even,
   one odd); nothing stops a config change to, say, 9 x 7.
2. **Fixed sub-pixel window.** `cornerSubPix` is still called with a hard-coded half-window of
   11 (a 23 x 23 px window, `CalibrationHelper.py`) regardless of how large the squares appear.
   A common rule of thumb is that the window should stay smaller than the spacing between
   corners.
3. **No held-out validation.** The reported RMS (overall and per-view) is the training error on
   the same images used to fit the model.
4. **Free distortion model.** The default 5-coefficient model with free principal point is
   fitted from the captured views, with no option to constrain it (for example
   `cv2.CALIB_FIX_K3` or `cv2.CALIB_FIX_PRINCIPAL_POINT`).

## Evidence

Ten synthetic views, one with badly localised corners, fed through `perViewErrors`:

```
overall RMS: 1.63 px
per-view errors: [0.36, 0.39, 0.4, 5.0, 0.37, 0.39, 0.46, 0.44, 0.42, 0.4]      worst view: 3
```

Nine good views at about 0.4 px; one bad one at 5.0 px. The per-view check (now shipped)
finds it instantly; before it existed, only the 1.63 px aggregate was visible.

With `fx` about 1066 px and 30 mm squares, corner spacing in the image is about 32 px at 1.0 m,
22.8 px at 1.4 m and 16 px at 2.0 m, against the fixed 23 px window — beyond roughly 1.4 m the
window spans neighbouring corners (point 2).

## Effects

- Orientation flips (point 1) can produce a stereo calibration that is wildly wrong while the
  per-camera calibrations look fine.
- A fixed sub-pixel window (point 2) under- or over-reaches depending on distance, with no
  feedback that it happened.
- Without held-out validation (point 3), a low training RMS does not guarantee the model
  generalises to new views.
- No distortion-model options (point 4) means there is no quick way to compare a more
  constrained fit against the default when the periphery is poorly modelled.

## Suggested fix

- Validate the config: `assert columns % 2 != rows % 2`.
- Scale the sub-pixel window from the measured corner spacing (for example 0.4 x the distance
  between neighbouring detected corners, at least 3).
- Reserve a few pairs and report the error on them.
- Try `cv2.CALIB_FIX_K3` and/or `cv2.CALIB_FIX_PRINCIPAL_POINT` and compare the rectified
  result; capture more strongly tilted views and views near the frame edges (see
  [usage.md](../usage.md)).
