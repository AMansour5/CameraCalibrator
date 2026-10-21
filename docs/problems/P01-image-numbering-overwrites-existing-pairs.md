# P01: New images are numbered by file count, so they can overwrite existing ones

**Severity:** High (silent data loss) **Evidence:** reproduced by running the real `StereoCalibrator`
**Component:** `StereoCalibrator`, `MonocularCalibrator`

## What the code does

When a calibrator starts it sets `saved_count` to the **number of `*.png` files** in the image folder, and
names the next image `f"{saved_count:03d}.png"`:

- `src/services/stereo/StereoCalibrator.py:32` (count) and `:92` (name)
- `src/services/monocular/MonocularCalibrator.py:29` and `:79`

A count equals "the next free number" only if the files are numbered `000 ... N-1` with no gaps. Any gap
breaks that.

## How to trigger it

1. Save pairs `000`-`004`.
2. Delete `002.png` (and its twin on the other side) by hand because it was a bad shot.
3. Start the program again. It counts 4 files, so the next pair is named `004.png`, which already exists.
4. Press `s`: `004.png` is overwritten with no warning.

## Evidence

Reproduced with a fake camera feeding synthetic frames to the real class:

```
new session starts at index: 4 (files on disk: 000,001,003,004)
004.png hash before/after saving 'next' pair: a583292e -> 7ac69c71 | overwritten: True
pairs on disk now: 4 (4 before the save, 4 after: nothing was added)
```

Related, by code reading: `deleteLastImage` decrements `saved_count` and deletes that index
(`StereoCalibrator.py:99-107`). With the gap above, `x` deletes `003.png`, not the highest-numbered
`004.png`. Neither method checks the return value of `cv2.imwrite` (`:93-94`, `Monocular:80`), so a
failed write (disk full, bad path) is reported as `Saved pair ...` and the counter still advances.

## Effects

- A good calibration image is replaced by a different one, and the folder never grows. You think you have
  25 images; you may have fewer.
- Pressing `x` can remove an unrelated image.
- Because the stereo pairs must match by file name, a failed write to only one side leaves an unmatched
  file and later raises `Mismatched or empty capture sets`.
- Hand-tidying the dataset (a very natural thing to do) is exactly what triggers it.

## Suggested fix

Derive the next index from the largest existing number, check the write result, and make delete target
that same number:

```python
@staticmethod
def nextIndex(*dirs):
    used = [int(f[:-4]) for d in dirs for f in os.listdir(d)
            if f.endswith(".png") and f[:-4].isdigit()]
    return max(used, default=-1) + 1

# saveImage:
ok_l = cv2.imwrite(path_l, left_frame); ok_r = cv2.imwrite(path_r, right_frame)
if not (ok_l and ok_r):
    raise IOError("Failed to write calibration pair")
```

Until then: delete the whole `left/` and `right/` folders rather than single files.
