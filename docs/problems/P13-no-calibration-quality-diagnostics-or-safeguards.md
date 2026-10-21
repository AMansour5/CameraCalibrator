# P13: No calibration quality diagnostics or safeguards

**Severity:** Medium (affects accuracy, not crashes) **Evidence:** code reading, a small experiment, and analysis of the committed file
**Component:** `CalibrationHelper`, `StereoCalibrator`, `MonocularCalibrator`

## What the code does

1. **Only one global RMS number.** `rvecs` and `tvecs` are discarded in the stereo path
   (`Stereo:192-195` unpack them into `_`), and the monocular path keeps but never uses them, so the error of
   each individual image is never computed.
2. **No check on pattern orientation.** If `columns` and `rows` are both even or both odd, the corner grid looks
   identical after a 180 degree rotation, so the detector can number the corners from opposite ends in the left and right
   views. The shipped 8 x 5 is safe (one even, one odd); nothing stops a config change to, say, 9 x 7.
3. **Fixed sub-pixel window.** `cornerSubPix` is called with a half-window of 11 (a 23 x 23 px window,
   `CalibrationHelper.py:34-36`) regardless of how large the squares appear. A common rule of thumb is that the
   window should stay smaller than the spacing between corners.
4. **No held-out validation.** The reported RMS is the training error on the same images.
5. **Free distortion model.** The default 5-coefficient model with free principal point is fitted from the captured views,
   with no option to constrain it.

## Evidence

**Experiment (point 1).** Ten synthetic views, one with badly localised corners. The overall RMS gives no hint which view:

```
overall RMS: 1.63 px
per-view errors: [0.36, 0.39, 0.4, 5.0, 0.37, 0.39, 0.46, 0.44, 0.42, 0.4]      worst view: 3
```

Nine good views at about 0.4 px; one bad one at 5.0 px. A per-view check finds it instantly. (The earlier
mismatched-pairs run in [P02](P02-calibration-overwrites-saved-result-without-quality-gate.md) likewise reached 26.7 px with no indication of which pairs caused it.)

**Point 3.** With `fx` about 1066 px and 30 mm squares, corner spacing in the image is about 32 px at 1.0 m,
22.8 px at 1.4 m and 16 px at 2.0 m, against a 23 px window. Beyond roughly 1.4 m the window spans neighbouring corners.

**The committed stereo calibration** (`src/matricies/stereo/stereo_calib.npz`, see [calibration-output.md](../calibration-output.md)) shows several signs
that the intrinsics may be poorly constrained. These are observations; the cause cannot be proven from the file alone:

| Observation | Value |
|-------------|-------|
| `rms_stereo` | 0.9938 px, just under the code's own 1.0 px warning level |
| Principal point vs image centre (960, 540) | left (+45, +64) px; right (-73, +94) px; the two eyes differ by 118 px in `cx` |
| Rectified focal length, `alpha=0` | 1765.7 px = 1.66 x the raw `fx` (1.04 x if the principal points are forced to the centre) |
| Valid region with `alpha=1` | about 4% of the frame |

## Effects

- A single bad capture cannot be identified, so users recapture everything or accept a worse result.
- Orientation flips (point 2) produce a stereo calibration that is wildly wrong while the per-camera calibrations look fine.
- For this file, `alpha=0` rectification keeps only the central part of the image and depth computed with the wrong focal
  length is far off ([P10](P10-calibration-file-schema-misleading-and-incomplete.md)). It also leaves the periphery poorly modelled, which is consistent with
  too little edge coverage or too many free parameters.

## Suggested fix

- Compute and print per-view errors, list the worst, and offer to drop them and recalibrate:

```python
def perViewErrors(objpoints, imgpoints, rvecs, tvecs, K, D):
    errs = []
    for o, i, r, t in zip(objpoints, imgpoints, rvecs, tvecs):
        proj, _ = cv2.projectPoints(o, r, t, K, D)
        errs.append(cv2.norm(i, proj, cv2.NORM_L2) / np.sqrt(len(o)))
    return errs
```

- Validate the config: `assert columns % 2 != rows % 2`.
- Scale the sub-pixel window from the measured corner spacing (for example 0.4 x the distance between neighbouring
  detected corners, at least 3).
- Reserve a few pairs and report the error on them.
- Try `cv2.CALIB_FIX_K3` and/or `cv2.CALIB_FIX_PRINCIPAL_POINT` and compare the rectified result; capture more strongly tilted views and
  views near the frame edges (see [usage.md](../usage.md)).
