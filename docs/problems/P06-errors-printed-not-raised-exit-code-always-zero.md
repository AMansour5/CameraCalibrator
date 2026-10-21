# P06: Errors are printed instead of raised, so failures are hidden and the exit code is always 0

**Severity:** Medium **Evidence:** reproduced by running the real program and the `Configurator`
**Component:** `Configurator`, `StereoCalibrator`, `MonocularCalibrator`, `StereoCamera`, `CameraCalibrator`

## What the code does

Almost every failure path is `except Exception as e: print(...)`:

| Location | Behaviour |
|----------|-----------|
| `Configurator.fetchData` (`:53-64`) | Prints the problem and **returns `None`** for a missing file, bad YAML, or unknown type |
| `Configurator.setConfig` (`:65-98`) | Prints and returns |
| `StereoCalibrator.calibrate` (`:211-212`), `MonocularCalibrator.calibrate` (`:164-165`) | Prints `Error during calibration: ...`; caller cannot tell it failed |
| `StereoCamera.open` (`:20-22`) | Prints, returns nothing |
| `CameraCalibrator.py:49-53` | `except Exception as e: print(f"An error occurred: {e}")` then exits normally |

## Evidence

1. No camera attached: the program fails, yet `echo $?` prints `0`.
2. A config file is missing (here `config/checkerboard.yaml`):

```
Error: The file '<repo>/config/checkerboard.yaml' was not found.
TypeError: 'NoneType' object is not subscriptable
```

The real cause is one line; the exception that actually propagates describes a symptom (`None[...]`) in a different file.

3. For contrast, `Dispatcher` does this correctly: a typo in `chosen_calibrator` raises
   `ValueError: Unknown calibrator type: sterero`.

## Effects

- Scripts, CI, or a wrapper cannot detect failure: exit code is always 0.
- Tracebacks are lost, so the file and line that failed are not shown (only `str(e)`).
- Messages about symptoms (`NoneType ...`) appear far from their cause.
- A failed calibration looks like a finished one: `calibrate()` returns the same `None` either way, and the
  window just keeps running.

## Suggested fix

Raise from the low-level code, handle once at the top:

```python
# fetchData: raise FileNotFoundError / KeyError instead of printing and returning None

if __name__ == "__main__":
    import sys, traceback
    try:
        CameraCalibrator.calibrate()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
```

Inside the interactive loop it is reasonable to catch a failed `calibrate()` so the window survives, but
log the traceback and report failure to the user instead of swallowing it silently.
