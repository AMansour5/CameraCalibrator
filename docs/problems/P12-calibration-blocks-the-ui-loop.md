# P12: Calibration runs inside the key handler and freezes the window

**Severity:** Medium (usability) **Evidence:** structure of the code; duration measured only on synthetic data
**Component:** `CameraCalibrator`, `StereoCalibrator`, `MonocularCalibrator`

## What the code does

`c` and the auto-calibrate on `q` call `calibrator.calibrate()` synchronously (`CameraCalibrator.py:33, 42`).
It detects corners in **every** saved image at full resolution (with `cornerSubPix`), then runs `calibrateCamera`
(per camera) and `stereoCalibrate` (up to 200 iterations). Meanwhile the loop does not run: no frame is read,
`imshow`/`waitKey` are not called, and nothing is printed until each stage finishes.

## Evidence

Duration depends on image count, resolution and CPU. For scale only: 8 synthetic 1920x1080 pairs took about
**81 s** on a single-core sandbox (noisy synthetic images; your machine will be much faster, real images may differ).
That the window is unresponsive for the whole time follows directly from the code structure.

## Effects

- The window shows no update and the desktop may mark it "not responding"; there is no progress message
  or hint that something is happening.
- Pressing `q` can start this computation ([P02](P02-calibration-overwrites-saved-result-without-quality-gate.md)), which looks like the program hanging on exit.
- Frames the driver queued while the loop was blocked are the next ones read afterwards (expected V4L2 behaviour,
  not measured here), so the first frames after calibration may be stale.
- It grows with the dataset, so it gets worse exactly when you have collected a good set.

## Suggested fix

Minimum: draw a "Calibrating..." banner and call `cv2.waitKey(1)` once before the call, print progress per stage, and
read-and-discard a few frames afterwards. Better: run `calibrate()` on a worker thread (keep all
`imshow`/`waitKey` on the main thread) and show a status line until it finishes.
