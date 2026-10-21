# P05: If the camera cannot be opened, the program ends with a misleading `'NoneType' ... 'release'` error

**Severity:** Medium **Evidence:** reproduced by running the real program with no camera attached
**Component:** `StereoCalibrator`, `MonocularCalibrator`, `StereoCamera`, `MonocularCamera`, `CameraCalibrator`

## What the code does

- `StereoCamera.open()` catches every error, prints it, and leaves its capture as `None`
  (`StereoCamera.py:14-22`); it neither raises nor returns a status.
- The calibrator's `__setupCamera` then notices the failed test read, prints another message, and replaces its
  own camera with `None` (`Stereo:46-54`, `Monocular:42-50`).
- The loop's first `grabPreviewFrame()` calls `self.camera.getFrames()` on `None`, which is caught and printed
  (`Stereo:85-87`), and the loop ends.
- The `finally` block calls `calibrator.release()` -> `self.camera.release()` on `None` (`Stereo:115-116`,
  `Monocular:101-102`), which raises. `__main__` catches and prints it (`CameraCalibrator.py:49-53`).

## Evidence

Output of `python -m src.services.CameraCalibrator` with `/dev/video2` absent:

```
Error opening camera: Could not open camera index /dev/video2
Camera is not opened.
Error opening camera: Failed to capture initial frames from the stereo camera.
Error during frame capture: 'NoneType' object has no attribute 'getFrames'
An error occurred: 'NoneType' object has no attribute 'release'
```

The last line, which is what a user remembers, describes a side effect, not the cause. The process exit code is 0 ([P06](P06-errors-printed-not-raised-exit-code-always-zero.md)).

## Effects

- Wrong-index, busy-device and permission problems all end with the same unhelpful final message.
- With no camera you cannot recalibrate from images you **already saved**: the loop exits before any key
  (`c`) can be pressed, even though `calibrate()` itself does not need the camera.
- `release()` raising in `finally` means any cleanup added after it would be skipped.

## Suggested fix

```python
def release(self):
    if self.camera is not None:
        self.camera.release()
```

and make failure explicit: have `open()` return a bool (or raise), let `__init__` raise one clear
`RuntimeError("Could not open camera <index> ...")`, and let the entry point report it
(see [P06](P06-errors-printed-not-raised-exit-code-always-zero.md)). If offline calibration is wanted, allow the loop to start in a mode where `c` works without a camera.
