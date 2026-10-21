# P03: Deleting an image does not mark the calibration as out of date

**Severity:** Medium **Evidence:** reproduced by running the real `StereoCalibrator`
**Component:** `StereoCalibrator`, `MonocularCalibrator`, `CameraCalibrator`

## What the code does

`_dirty` is set to `True` only in `saveImage` (`Stereo:97`, `Monocular:83`) and cleared after a successful
calibration (`Stereo:208`, `Monocular:162`). `deleteLastImage` (`Stereo:99-107`, `Monocular:85-93`) never touches it.
The loop uses `isDirty()` to decide whether `q` should calibrate first (`CameraCalibrator.py:31-34`).

## How to trigger it

Save images, press `c`, notice the last image was bad, press `x` to remove it, press `q`.

## Evidence

```
after saving 10 pairs, isDirty: True
after calibrate(), isDirty: False | rms_stereo=0.112px  fx=530.2  baseline=119.4mm
after deleteLastImage(), isDirty: False -> pressing q now would NOT recalibrate;
   the saved calibration still reflects 10 pairs while only 9 remain on disk
```

## Effects

- The on-disk calibration still includes the image you just deleted, which is usually the one you deleted
  *because it was bad*. You believe you removed it; the result says otherwise.
- Nothing tells you. The next recalibration only happens if you save another image or press `c`.
- Compounds [P02](P02-calibration-overwrites-saved-result-without-quality-gate.md): the dirty flag is the only guard the program has around calibration, and it is incomplete.

## Suggested fix

One line in each `deleteLastImage`, when a file was actually removed:

```python
if CalibrationHelper.deleteLastSaved([...], self.saved_count):
    self._dirty = True
    print(f"Deleted pair {self.saved_count:03d}.png")
```
