# P14: Live corner detection runs at full resolution on every displayed frame

**Severity:** Low (preview lag) **Evidence:** code reading; relative cost measured on synthetic frames
**Component:** `StereoCalibrator.grabPreviewFrame`, `MonocularCalibrator.grabPreviewFrame`

## What the code does

Each loop iteration converts both halves to gray and runs `findChessboardCorners` on each at the native
resolution (`Stereo:63-66`; `Monocular:60-61`). With the shipped 3840 x 1080 stereo setting that is two 1920 x 1080 searches
per displayed frame. Only the picture shown is downscaled afterwards.

## Evidence

Corner detection on the same synthetic 1920 x 1080 frame at three sizes (single-core sandbox, noisy synthetic image, so
the absolute times are not representative of your machine):

| Size | Relative cost | Board found? |
|------|---------------|--------------|
| 1920 x 1080 | 1.0 | yes |
| 960 x 540 | about 0.075 (13 x cheaper, more than the 4 x drop in pixels) | yes |
| 640 x 360 | negligible | **no** (squares about 12 px) |

## Effects

- The preview frame rate is limited by detection, not by the camera, so the live view lags behind the board you are moving.
  Lag makes it harder to hold the board steady and to judge when `READY` is accurate.
- Going to a very small size is not free: the board stops being detected when it is small or far.

## Suggested fix

Detect on a half-size copy and scale the corners back for drawing; keep the saved image at full resolution (calibration should
use full-resolution corners, which it does):

```python
SCALE = 0.5
small = cv2.resize(gray_left, None, fx=SCALE, fy=SCALE, interpolation=cv2.INTER_AREA)
found, corners = cv2.findChessboardCorners(small, self.CHECKERBOARD, flags=self.CORNER_FLAGS)
if found:
    corners = corners / SCALE          # back to full-resolution coordinates
```

Or detect only every few frames. Choose the scale so the squares stay at least about 15-20 px wide.
