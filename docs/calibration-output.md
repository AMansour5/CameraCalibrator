# Calibration output files

Both files are NumPy `.npz` archives, written (not compressed) by
`CalibrationHelper.saveTimestamped`. A calibration run never touches the accepted file
directly — it writes a new file under `.../time_stamped/<mode>_calib_YYYYMMDD_HHMMSS.npz`
and leaves `.../<mode>_calib.npz` alone until you press `a` (`acceptLatest()`), which copies
the latest time-stamped file over it. Load either kind with `np.load(path)`; the keys below
are what `load(...).files` returns.

All lengths that depend on the board (`T`, the baseline) are in **millimetres**, because the
object points are built from `square_size_mm`. Image sizes are `(width, height)` in pixels;
for stereo this is the size of **one eye**, not the combined frame.

## `src/matrices/stereo/<time_stamped/>stereo_calib*.npz`

| Key | Shape | Meaning |
|-----|-------|---------|
| `K1`, `K2` | 3x3 | Camera matrix of the left / right eye (`fx, fy, cx, cy` in pixels) |
| `D1`, `D2` | 1x5 | Distortion `(k1, k2, p1, p2, k3)` of the left / right eye |
| `R` | 3x3 | Rotation taking left-camera coordinates to right-camera coordinates |
| `T` | 3x1 | Translation (mm) from the same mapping. `abs(T[0])` is roughly the baseline |
| `E` | 3x3 | Essential matrix |
| `F` | 3x3 | Fundamental matrix |
| `img_size` | 2 | `(width, height)` of one eye |
| `rms_left`, `rms_right` | scalar | Per-camera RMS reprojection error (px) from the individual `calibrateCamera` calls |
| `rms_stereo` | scalar | RMS reprojection error of the stereo calibration (px) |
| `checkerboard` | 2 | `(columns, rows)` inner-corner counts used for this run |
| `square_size_mm` | scalar | Square size used for this run |

Convention: a 3D point `X_left` in the left camera frame is `R @ X_left + T` in the right
camera frame. For a right camera that sits to the right of the left one, `T[0]` is negative.

**Not saved:** the rectification outputs (`R1, R2, P1, P2, Q`, valid-pixel ROIs) — they are
computed on the fly inside `previewFrame()` and discarded, so code that needs depth has to
call `cv2.stereoRectify` itself (see [P01](problems/P01-stereo-calibration-does-not-save-rectification-outputs.md)).

### Using it: rectification and depth

```python
import cv2, numpy as np

d = np.load("src/matrices/stereo/stereo_calib.npz")
K1, D1, K2, D2, R, T = (d[k] for k in ("K1", "D1", "K2", "D2", "R", "T"))
size = tuple(int(v) for v in d["img_size"])            # (width, height) of ONE eye

R1, R2, P1, P2, Q, _, _ = cv2.stereoRectify(
    K1, D1, K2, D2, size, R, T, flags=cv2.CALIB_ZERO_DISPARITY, alpha=0)  # same as the preview
map1 = cv2.initUndistortRectifyMap(K1, D1, R1, P1, size, cv2.CV_32FC1)
map2 = cv2.initUndistortRectifyMap(K2, D2, R2, P2, size, cv2.CV_32FC1)

rect_left  = cv2.remap(left,  *map1, cv2.INTER_LINEAR)   # left / right = the two halves of a frame
rect_right = cv2.remap(right, *map2, cv2.INTER_LINEAR)

# After rectification, depth follows from disparity d (pixels):  Z = f * B / d
f, B = float(Q[2, 3]), abs(1.0 / float(Q[3, 2]))          # rectified focal length (px), baseline (mm)
```

**Use the rectified focal length `f` from `Q` (or `P1[0, 0]`), not `K1[0, 0]`.** They can
differ a lot. A locally captured 1920x1080-per-eye calibration (16 pairs, `rms_stereo` 1.06 px)
had `K1[0,0] = 1065.2` px but a rectified `P1[0,0]` of `1186.9` px at `alpha=0` — about an 11%
difference, which is roughly the error you would get in computed depth by using the wrong one.
The gap grows with how far the two principal points are from the image centre and from each
other, so it is worth checking for your own camera rather than assuming it is small.

## `src/matrices/monocular/<time_stamped/>monocular_calib*.npz`

| Key | Shape | Meaning |
|-----|-------|---------|
| `K` | 3x3 | Camera matrix |
| `D` | 1x5 | Distortion `(k1, k2, p1, p2, k3)` |
| `rvecs` | (N,3,1) | Per-image board rotation vectors, one per image used in the fit |
| `tvecs` | (N,3,1) | Per-image board translation vectors, one per image used in the fit |
| `img_size` | 2 | `(width, height)` |
| `rms` | scalar | RMS reprojection error (px) |
| `checkerboard` | 2 | `(columns, rows)` inner-corner counts used for this run |
| `square_size_mm` | scalar | Square size used for this run |

A locally captured example: `N = 51`, `img_size = 1280 x 720`, `rms = 0.718`, `fx = 770.3`.
`rvecs`/`tvecs` describe each image's board pose relative to the camera; they are not a
camera-to-camera transform and are not needed to undistort images.

### Using it: undistortion

The preview builds a new camera matrix with `alpha=0` (crop to valid pixels) that is **not**
saved, so reproduce it:

```python
d = np.load("src/matrices/monocular/monocular_calib.npz")
K, D = d["K"], d["D"]
size = tuple(int(v) for v in d["img_size"])
new_K, _ = cv2.getOptimalNewCameraMatrix(K, D, size, alpha=0)
m1, m2 = cv2.initUndistortRectifyMap(K, D, None, new_K, size, cv2.CV_32FC1)
undistorted = cv2.remap(frame, m1, m2, cv2.INTER_LINEAR)
```

If you instead call `cv2.undistort(frame, K, D)` you get a different crop/zoom than the
preview shows. Use `new_K` as the camera matrix of the *undistorted* image in later geometry
(e.g. when back-projecting pixels).

## Compatibility

Both files are tied to the resolution and the board settings used when they were created.
`previewFrame()` now checks the live frame size against the stored `img_size` and raises
`DifferentImageSizeError` if they don't match, but code that loads a file directly and applies
it to frames of a different size still has to do that check itself.
