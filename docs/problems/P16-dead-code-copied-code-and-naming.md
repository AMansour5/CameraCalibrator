# P16: Dead code, leftovers from another project, and a misspelled folder name

**Severity:** Low (maintainability) **Evidence:** searched the repository for usages **Component:** `Configurator`, `Dispatcher`, `CameraCalibrator`, `CalibrationHelper`

## Findings as originally reported

The details below describe the repository when this issue was filed; see the current audit for what remains.

| Item | Where | Detail |
|------|-------|--------|
| Unused `pkg` argument | `Configurator.py:10-12, 25-27` | Redirects to `src/<pkg>/config`; no such folders exist and nothing passes it |
| Unused `setConfig` | `Configurator.py:65-98` | No callers. Its docstring says `data_type` is "e.g., 'cameras', 'joystick_buttons'", which are names from a different project |
| Unused `getConfigsNames` | `Configurator.py:32-34` | No callers |
| Identity mapping | `Configurator.py:40-49` | An `if/elif` chain that maps each constant to itself |
| Second `Configurator` | `Dispatcher.py:10` | `Configurator().CALIBRATOR` creates another instance only to read a constant |
| Folder spelled `matricies` | `StereoCalibrator.py:41`, `MonocularCalibrator.py:38`, and the committed directory | Should be `matrices`; the spelling is hard-coded in two places and in the tracked files, so renaming later means moving data too |
| Static-only class | `CameraCalibrator.py:9-12, 51` | A class with one static method, instantiated in `__main__` just to call it |
| Mixed indentation | `CalibrationHelper.py:8-13, 17-41` | Two methods use 12-space bodies inside the class; the others use 8 |

## Evidence at time of report

```
$ grep -rn "setConfig\|getConfigsNames\|Configurator(\s*[\"'a-z]" src --include=*.py | grep -v Configurator.py
(no usages)
```

## Effects

- Readers spend time understanding unused methods and identity mapping.
- A misspelled results directory can leave saved results disconnected from the path used by the calibrators.
- Unused YAML-rewriting code (`yaml.safe_dump`) would drop comments and key order if someone ever started using it.

## Current audit

This status reflects the current, **uncommitted** working tree. All items are now resolved.

| Item | Status |
|------|--------|
| Remove the unused `pkg` argument | **Done:** config lookup now uses the root `config/` directory |
| Remove unused `getConfigsNames` | **Done** |
| `setConfig` | **Done:** kept (no callers found, but kept rather than removed) and now covered by a regression test, `src/tests/test_configurator_set_config.py`; docstring example corrected |
| Simplify `__getYamlFile` identity mapping | **Done:** replaced the `if/elif` chain with a membership check against the supported constants |
| Avoid second `Configurator` in `Dispatcher` | **Done** |
| Use consistent `CalibrationHelper` indentation | **Done** |
| Call static `CameraCalibrator.calibrate` without an instance | **Done:** `__main__` now calls `CameraCalibrator.calibrate()` directly |
| Rename results folder to `matrices` | **Done:** both calibrator paths use `src/matrices/`, the files were moved out of the misspelled `src/matrcies/`, that directory was removed, and `src/matrices/**/*.npz` was added to `.gitignore` (resolving the overlapping part of [P15](P15-tracked-artifacts-and-machine-specific-config.md)) |

## Verification

- `python -m pytest -q src/tests/test_configurator_set_config.py` — 2 passed.
- Manual check: `Configurator().fetchData(Configurator.CHECKERBOARD)` still returns the expected keys, and an
  unknown `data_type` still raises the same `TypeError` message as before.
- Manual check: `CameraCalibrator.calibrate` is callable as `CameraCalibrator.calibrate()` without instantiation.
- `src/matrices/monocular/monocular_calib.npz` and `src/matrices/stereo/stereo_calib.npz` exist; `src/matrcies/`
  no longer exists; `git status --ignored` shows `src/matrices/` as ignored.

