# P07: The shipped tests cannot fail, are not collected by pytest, and some overwrite real data

**Severity:** Medium **Evidence:** reproduced by running the tests and `pytest`
**Component:** `src/tests/`

## What the code does

| Issue | Where | Detail |
|-------|-------|--------|
| Stale names | `ConfiguratorTest.py:10-13` | Uses `Configurator.CAMERA` and the key `cam_index`; the constants are `STEREO_CAMERA` / `MONOCULAR_CAMERA` and the key is `camera_index` |
| Failures swallowed | `ConfiguratorTest.py:15-16, 23-24` | `try: ... assert ... except Exception: print(...)`. `AssertionError` is an `Exception`, so a failing assertion is printed, not raised |
| Wrapped calls never raise | `StereoCalibratorTest.py:15-20, 27-32`, `MonocularCalibratorTest.py:15-20, 27-32` | `grabPreviewFrame()` and `calibrate()` already catch every exception internally, so the `except ...: assert False` branch is unreachable |
| Unconditional success message | `StereoCalibratorTest.py:41`, `MonocularCalibratorTest.py:41` | `print("All tests passed.")` runs whatever happened above it |
| Not discoverable | all files | Named `*Test.py`, not `test_*.py`; `TestConfigurator` has an `__init__`, which pytest refuses to collect |
| Side effects | `StereoCalibratorTest.py:34-41` | The only enabled test (`test_calibrate_method`) runs a real calibration and **overwrites the saved `.npz`** ([P02](P02-calibration-overwrites-saved-result-without-quality-gate.md)) |
| Camera handles | every calibrator test | Each test method builds a new calibrator, which opens the camera and is never released (not verified on hardware) |

## Evidence

```
$ python -m src.tests.ConfiguratorTest
Error loading camera config: type object 'Configurator' has no attribute 'CAMERA'
All tests completed.
$ echo $?
0
$ python -m pytest --collect-only -q src/tests
no tests collected in 0.00s
```

## Effects

- A broken `Configurator`, a renamed key, or a failed calibration would still report success.
- No automated safety net for the changes listed in this folder, which is how problems like
  [P03](P03-delete-does-not-mark-calibration-dirty.md) go unnoticed.
- Running the "tests" can destroy a good calibration.

## Suggested fix

Convert to real `pytest` tests (`test_*.py`, plain functions), let assertions fail, and keep camera-dependent
ones behind a marker. Hardware-free tests that already pass are in [testing.md](../testing.md); a fake camera plus
a temporary project root lets the calibrators be tested without touching real data.
