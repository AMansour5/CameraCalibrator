# P16: Dead code, leftovers from another project, and a misspelled folder name

**Severity:** Low (maintainability) **Evidence:** searched the repository for usages **Component:** `Configurator`, `Dispatcher`, `CameraCalibrator`, `CalibrationHelper`

## What the code contains

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

## Evidence

```
$ grep -rn "setConfig\|getConfigsNames\|Configurator(\s*[\"'a-z]" src --include=*.py | grep -v Configurator.py
(no usages)
```

## Effects

- Readers spend time understanding code that never runs, and may trust the `setConfig` docstring about keys that do not exist here.
- The typo spreads: every new consumer of the results path has to copy it.
- Unused YAML-rewriting code (`yaml.safe_dump`) would drop comments and key order if someone ever started using it.

## Suggested fix

Delete the unused members (or add tests that use them), simplify `__getYamlFile` to a membership check, fix the docstring, normalise
the indentation, and rename `matricies` to `matrices` (update the two path constants and move the files in one commit).
