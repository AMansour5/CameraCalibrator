# P02: Calibration always overwrites the saved result, with no quality gate and no backup

**Severity:** High (can silently replace a good calibration with a bad one)
**Evidence:** reproduced by running the real `StereoCalibrator` **Component:** `StereoCalibrator`, `MonocularCalibrator`, `CameraCalibrator`

## What the code does

1. **Warnings do not stop anything.** Stereo prints `WARNING: only N pairs ...` below 10 pairs
   (`StereoCalibrator.py:182-186`) and `NOTE: stereo RMS > 1.0 px is high` (`:242-248`), then
   continues. Stereo has no minimum at all; monocular enforces 5 images (`Monocular:145`) but has no RMS limit.
2. **The result is written unconditionally** with `np.savez(self.OUTPUT_FILE, ...)` (`Stereo:206`,
   `Monocular:160`). No backup of the previous file is made.
3. **Quitting calibrates.** Pressing `q` runs `calibrator.calibrate()` if any image was saved since the last
   calibration (`CameraCalibrator.py:31-34`). No key quits without it once an image has been saved (only `Ctrl+C` in the terminal does).

## Evidence

Starting from a good 16-pair calibration, then replacing it in two ways (synthetic frames; the first
file's values are the reference):

| Run | `rms_stereo` | `fx` (half-res px) | Baseline (true 119.3 mm) | Saved? |
|-----|--------------|--------------------|--------------------------|--------|
| Good, 16 pairs | 0.087 px | 532.5 | 119.2 mm | yes |
| (a) only 3 pairs | 0.139 px | 523.4 | 121.3 mm | **yes**, only a warning printed |
| (b) 12 pairs, 4 with a mismatched right frame | **26.721 px** | 530.6 | 126.5 mm | **yes**, `NOTE: ... > 1.0` printed |

In both bad cases the good file on disk was replaced. (The synthetic frames are cleaner than real
captures, so real-world damage from run (a) would likely be larger.)

## Effects

- A single accidental `q` after one extra bad capture replaces a good calibration. The loss is permanent
  (no backup, and the `.npz` is the only record of the previous values).
- A calibration with a 26 px error is stored as if it were valid; downstream code (rectification, depth)
  has no way to know.
- Quitting can trigger a long blocking computation ([P12](P12-calibration-blocks-the-ui-loop.md)) the user did not ask for.

## Suggested fix

```python
MIN_PAIRS, MAX_STEREO_RMS = 10, 1.0

if len(common) < MIN_PAIRS:
    raise RuntimeError(f"Only {len(common)} usable pairs; need {MIN_PAIRS}")
...
if rms_stereo > MAX_STEREO_RMS:
    print("RMS too high; NOT saving. Recapture, or raise MAX_STEREO_RMS to override.")
    return
if os.path.exists(self.OUTPUT_FILE):
    shutil.copy2(self.OUTPUT_FILE, self.OUTPUT_FILE + ".bak")
np.savez(...)
```

And in the loop make `q` only quit (print a hint if `isDirty()`), leaving calibration to `c`.
