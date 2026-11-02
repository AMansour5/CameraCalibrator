# P01: The saved stereo calibration does not include the rectification outputs (`Q`, `R1`, `R2`, `P1`, `P2`)

**Severity:** Medium **Evidence:** read from the code and a freshly produced `.npz` file **Component:** `CalibrationHelper`, `StereoCalibrator`

## What the code does

`StereoCalibrator.calibrate()` saves `K1, D1, K2, D2, R, T, E, F, img_size, rms_left,
rms_right, rms_stereo, checkerboard, square_size_mm`. `E` and `F` are kept now (they used to
be computed and discarded), and the monocular file no longer reuses the misleading `R`/`T`
names for per-image board poses — it saves `rvecs`/`tvecs` instead. What is still missing is
the **rectification** itself: `cv2.stereoRectify` is only called inside `previewFrame()`, and
`CalibrationHelper.buildStereoRectifyMaps` unpacks `R1, R2, P1, P2, _, _, _`, throwing away
`Q` and the valid-pixel ROIs.

## Evidence

```
$ python3 -c "import numpy as np, glob; d = np.load(sorted(glob.glob('src/matrices/stereo/time_stamped/*.npz'))[-1]); print(d.files)"
['K1', 'D1', 'K2', 'D2', 'R', 'T', 'E', 'F', 'img_size', 'rms_left', 'rms_right', 'rms_stereo', 'checkerboard', 'square_size_mm']
```

No `Q`, `R1`, `R2`, `P1`, `P2`, or ROI anywhere in the file.

## Effects

- Anything that wants to turn disparity into depth (or just rectify a pair) has to call
  `cv2.stereoRectify` itself, with the same `alpha=0` and `CALIB_ZERO_DISPARITY` flags the
  preview uses, to get a matching `Q` and focal length. Getting this wrong is easy and silent
  — see the worked example in [calibration-output.md](../calibration-output.md) showing how
  far the raw `K1[0,0]` can be from the rectified focal length.
- There is still no schema version stored *inside* the array data (the file name carries a
  timestamp via `CalibrationHelper.saveTimestamped`, but a copy renamed by hand loses it).

## Suggested fix

```python
R1, R2, P1, P2, Q, roi1, roi2 = cv2.stereoRectify(K1, D1, K2, D2, size, R, T,
                                                  flags=cv2.CALIB_ZERO_DISPARITY, alpha=0)
np.savez(saved_path, K1=K1, D1=D1, K2=K2, D2=D2, R=R, T=T, E=E, F=F,
         R1=R1, R2=R2, P1=P1, P2=P2, Q=Q, roi1=roi1, roi2=roi2,
         img_size=img_size, rms_left=rms_left, rms_right=rms_right, rms_stereo=rms_stereo,
         checkerboard=self.CHECKERBOARD, square_size_mm=self.SQUARE_SIZE_MM)
```
