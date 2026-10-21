# Identified problems

Sixteen problems found by reading every source file and then **running the code**. Each one has its own file with
the same layout: what the code does (with file and line), how to trigger it, the evidence, the effects, and a suggested fix.

Severity:

- **High**: can lose data or silently replace a good calibration with a bad one.
- **Medium**: misleading or fragile behaviour that appears in normal use, or that makes the project hard to run or trust.
- **Low**: polish and maintainability.

| ID | Problem | Severity | Evidence |
|----|---------|----------|----------|
| [P01](P01-image-numbering-overwrites-existing-pairs.md) | New images are numbered by file count and can overwrite existing ones | **High** | Reproduced |
| [P02](P02-calibration-overwrites-saved-result-without-quality-gate.md) | Calibration always overwrites the saved result: no quality gate, no backup, and `q` triggers it | **High** | Reproduced |
| [P03](P03-delete-does-not-mark-calibration-dirty.md) | Deleting an image does not mark the calibration out of date | Medium | Reproduced |
| [P04](P04-preview-ignores-stored-image-size.md) | Preview ignores the stored image size, so a resolution change gives a silently wrong preview | Medium | Reproduced |
| [P05](P05-camera-open-failure-crashes-on-release.md) | A camera that fails to open ends with a misleading `'NoneType' ... 'release'` error | Medium | Reproduced |
| [P06](P06-errors-printed-not-raised-exit-code-always-zero.md) | Errors are printed, not raised; the exit code is always 0 | Medium | Reproduced |
| [P07](P07-shipped-tests-cannot-fail-and-are-not-collected.md) | The shipped tests cannot fail, are not collected by pytest, and one overwrites real data | Medium | Reproduced |
| [P08](P08-no-dependency-manifest.md) | No dependency list | Medium | Reproduced |
| [P09](P09-entry-point-requires-module-invocation.md) | Starts only when run as a module from the repository root | Medium | Reproduced |
| [P10](P10-calibration-file-schema-misleading-and-incomplete.md) | Saved files are incomplete (no `Q`, no provenance) and `R`/`T` mean different things in each file | Medium | File inspection + code |
| [P11](P11-interface-contracts-not-enforced-or-honoured.md) | Interface contracts are neither honoured nor checked | Medium | Reproduced |
| [P12](P12-calibration-blocks-the-ui-loop.md) | Calibration runs inside the key handler and freezes the window | Medium | Code structure (duration measured on synthetic data only) |
| [P13](P13-no-calibration-quality-diagnostics-or-safeguards.md) | No per-image errors, orientation check, or held-out validation; the committed calibration shows warning signs | Medium | Experiment + analysis of the committed file |
| [P14](P14-live-corner-detection-runs-at-full-resolution-every-frame.md) | Live corner detection runs at full resolution on every frame | Low | Code + relative timing |
| [P15](P15-tracked-artifacts-and-machine-specific-config.md) | Generated calibration files are tracked in git; config is machine-specific | Low | Repository inspection |
| [P16](P16-dead-code-copied-code-and-naming.md) | Dead code, leftovers from another project, a misspelled folder | Low | Code search |

## Suggested order of attack

Four fixes take only a few lines each and remove the most friction or risk:

1. **P03**: one line in each `deleteLastImage`.
2. **P05**: guard `release()` with `if self.camera is not None`.
3. **P08** and **P09**: add `requirements.txt` and `src/__main__.py`.

Then the ones that protect your data and results: **P01** (numbering), **P02** (quality gate + backup + `q` behaviour),
**P04** (size check). After that **P06** (raise instead of print) and **P07** (real tests), which make later changes safe.
**P13** is the one that most affects the *accuracy* of what you produce.

## How these were verified

- Cloned the repository (commit `ccaebd1`) and read every source file, both `.npz` files, the configs and the tests.
- Ran the program as shipped (no camera attached) to observe the entry-point and camera-failure behaviour and exit codes.
- Drove the **real** `StereoCalibrator` with a fake camera that serves synthetic checkerboard frames matching your config
  (8 x 5 inner corners, 30 mm squares, about 119 mm baseline), in a scratch copy of the repository. This reproduced P01-P04 and P11, and
  gave the P02 numbers. Frames were rendered at 1920 x 1080 and halved for the slower calibration runs.
- Tested the code snippets used in the docs and fixes (rectification from the committed file, the per-view error function, the
  `src/__main__.py` entry point, the hardware-free tests).
- Environment: CPython 3.12.3, OpenCV 4.13.0, NumPy 2.4.4, PyYAML 6.0.3.

**Not verified:** behaviour on a real camera (driver buffering, `cv2.imshow` windows and key handling, device permissions),
real photographs of a printed board (synthetic frames are cleaner), and Windows/macOS. Timing figures are from a single-core sandbox and are
only quoted as relative scale. Where a point rests on code reading only, the problem file says so.

## What works well

Worth keeping while fixing the above:

- **The calibration core is numerically sound.** On synthetic data with known ground truth, 16 pairs recovered `fx = 532.5` (true 532.5 at half
  resolution) and a baseline of 119.2 mm (true 119.3 mm) at 0.087 px RMS.
- **Clean layering.** Loop -> dispatcher -> interface -> implementation. A third camera type is a small addition.
- **Sound stereo practice.** Intrinsics are solved per camera first and then held fixed (`CALIB_FIX_INTRINSIC`); only pairs detected in *both* views are used;
  object points are in millimetres so the baseline comes out in real units.
- **Raw frames are saved**, not the annotated preview, and as lossless PNG.
- **The camera class checks the resolution the driver actually accepted** and warns when it differs, which prevents a whole class of wrong-split mistakes.
- **A bad `chosen_calibrator` gives a clear error** (`Unknown calibrator type: ...`), and the camera and windows are released in a `finally` block.
