# P10: The saved calibration files are incomplete and use misleading key names

**Severity:** Medium **Evidence:** read from the committed `.npz` files and the code **Component:** `StereoCalibrator`, `MonocularCalibrator`, `CalibrationHelper`

## What the code does

**Stereo** (`Stereo:206`) saves only `K1, D1, K2, D2, R, T, img_size, rms_stereo`.
`E` and `F` are computed and thrown away (`Stereo:214-222`); the per-camera RMS values are printed but not stored;
the rectification products are discarded: `buildStereoRectifyMaps` unpacks `R1, R2, P1, P2, _, _, _`, so `Q` and the
valid regions are dropped (`CalibrationHelper.py:72`).

**Monocular** (`Monocular:160`) saves `R=rvecs, T=tvecs`. These are the board pose **in each captured image**
(shape `(20, 3, 1)` in the committed file), not a camera-to-camera transform.

Neither file records the board size, square size, a timestamp, or any camera identity.

## Evidence

```
stereo keys: ['D1', 'D2', 'K1', 'K2', 'R', 'T', 'img_size', 'rms_stereo']
mono   keys: ['D', 'K', 'R', 'T', 'img_size', 'rms']        R: (20, 3, 1)   T: (20, 3, 1)
```

For the committed stereo file the rectified focal length (what depth needs) is 1765.7 px with `alpha=0`, against a
raw `K1[0,0]` of 1065.6 px ([calibration-output.md](../calibration-output.md)).

## Effects

- **Depth pipelines must recompute `stereoRectify`** to get `Q`, and must know to use the rectified focal length.
  Using `K1`'s `fx` instead gives roughly 40% error for this file.
- The same names `R` and `T` mean opposite things in the two files. A loader written for the stereo file and
  pointed at the monocular one will read per-image board poses as extrinsics without error.
- You cannot tell later whether a file matches the current `config/checkerboard.yaml`. A wrong
  `square_size_mm` silently scales `T` and the baseline.
- You cannot see which calibration was worse, or when it was made; the only per-camera quality figure is lost.

## Suggested fix

Save the full picture and a schema version:

```python
R1, R2, P1, P2, Q, roi1, roi2 = cv2.stereoRectify(K1, D1, K2, D2, size, R, T,
                                                  flags=cv2.CALIB_ZERO_DISPARITY, alpha=0)
np.savez(self.OUTPUT_FILE, K1=K1, D1=D1, K2=K2, D2=D2, R=R, T=T, E=E, F=F,
         R1=R1, R2=R2, P1=P1, P2=P2, Q=Q, img_size=size,
         rms_stereo=rms_stereo, rms_left=rms_left, rms_right=rms_right,
         checkerboard=self.CHECKERBOARD, square_size_mm=self.SQUARE_SIZE_MM,
         created=time.strftime("%Y-%m-%dT%H:%M:%S"), schema_version=2)
```

and for the monocular file rename the keys to `rvecs` / `tvecs` (or drop them, nothing reads them).
