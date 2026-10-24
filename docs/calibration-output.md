# Calibration output files

Both files are NumPy `.npz` archives written with `np.savez` (not compressed). Load them
with `np.load(path)`; the keys below are what `load(...).files` returns.

All lengths that depend on the board (`T`, the baseline) are in **millimetres**, because
the object points are built from `square_size_mm`. Image sizes are `(width, height)` in
pixels; for stereo this is the size of **one eye**, not the combined frame.

## `src/matrices/stereo/stereo_calib.npz`

| Key | Shape | Meaning |
|-----|-------|---------|
| `K1`, `K2` | 3x3 | Camera matrix of the left / right eye (`fx, fy, cx, cy` in pixels) |
| `D1`, `D2` | 1x5 | Distortion `(k1, k2, p1, p2, k3)` of the left / right eye |
| `R` | 3x3 | Rotation taking left-camera coordinates to right-camera coordinates |
| `T` | 3x1 | Translation (mm) from the same mapping. `abs(T[0])` is roughly the baseline |
| `img_size` | 2 | `(width, height)` of one eye |
| `rms_stereo` | scalar | RMS reprojection error of the stereo calibration (px) |

Convention: a 3D point `X_left` in the left camera frame is `R @ X_left + T` in the right
camera frame. For a right camera that sits to the right of the left one, `T[0]` is negative.

**Not saved:** the per-camera RMS (printed only), the essential/fundamental matrices, the
rectification outputs (`R1, R2, P1, P2, Q`), and any record of which board / square size /
date produced the file ([P10](problems/P10-calibration-file-schema-misleading-and-incomplete.md)).

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
differ a lot, see the example below.

### Example: the file committed in the repository (commit `ccaebd1`)

| Quantity | Value |
|----------|-------|
| `img_size` | 1920 x 1080 per eye |
| `rms_stereo` | 0.9938 px (just under the 1.0 px warning level) |
| Baseline `abs(T)` | 119.4 mm |
| Left `fx, fy` / `cx, cy` | 1065.6, 1066.6 / 1005.1, 604.2 |
| Right `fx, fy` / `cx, cy` | 1068.4, 1072.0 / 887.5, 634.1 |
| Image centre | 960, 540 |
| Rectified `f` with `alpha=0` | **1765.7 px** (1.66 x the original `fx`) |
| Rectified `f` with `alpha=-1` | 1069.3 px |

Forcing both principal points to the image centre drops the `alpha=0` zoom from 1.66 x to
1.04 x, so the large principal-point offsets are what drive it. Practical effect: with
`alpha=0` the rectified image keeps only the central part of the frame, and depth computed
with `K1`'s `fx` instead of the rectified `f` would be about 40% off. See
[P13](problems/P13-no-calibration-quality-diagnostics-or-safeguards.md).

## `src/matrices/monocular/monocular_calib.npz`

| Key | Shape | Meaning |
|-----|-------|---------|
| `K` | 3x3 | Camera matrix |
| `D` | 1x5 | Distortion `(k1, k2, p1, p2, k3)` |
| `R` | (N,3,1) | **Per-image board rotation vectors** (`rvecs`), one per image used. *Not* a camera-to-camera rotation |
| `T` | (N,3,1) | **Per-image board translation vectors** (`tvecs`), one per image used |
| `img_size` | 2 | `(width, height)` |
| `rms` | scalar | RMS reprojection error (px) |

The committed file has `N = 20`, `img_size = 1280 x 720`, `rms = 0.6245`, `fx = 784.2`.

The key names `R` and `T` mean something different here than in the stereo file
([P10](problems/P10-calibration-file-schema-misleading-and-incomplete.md)). `R`/`T` are not needed to undistort images.

### Using it: undistortion

The preview builds a new camera matrix with `alpha=0` (crop to valid pixels) that is
**not** saved, so reproduce it:

```python
d = np.load("src/matrices/monocular/monocular_calib.npz")
K, D = d["K"], d["D"]
size = tuple(int(v) for v in d["img_size"])
new_K, _ = cv2.getOptimalNewCameraMatrix(K, D, size, alpha=0)
m1, m2 = cv2.initUndistortRectifyMap(K, D, None, new_K, size, cv2.CV_32FC1)
undistorted = cv2.remap(frame, m1, m2, cv2.INTER_LINEAR)
```

If you instead call `cv2.undistort(frame, K, D)` you get a different crop/zoom than the
preview shows. Use `new_K` as the camera matrix of the *undistorted* image in later
geometry (e.g. when back-projecting pixels).

## Compatibility

Both files are tied to the resolution and the board settings used when they were created.
Using them with frames of a different size is not detected anywhere in the code
([P04](problems/P04-preview-ignores-stored-image-size.md)).
