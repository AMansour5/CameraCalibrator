# P09: The program only starts when run as a module from the repository root

**Severity:** Medium (first-run failure) **Evidence:** reproduced **Component:** `CameraCalibrator.py`, all `src/*` imports

## What the code does

Every import is absolute and starts with `src.` (for example `from src.utils.Dispatcher import Dispatcher`,
`CameraCalibrator.py:2`). That only works when the repository root is on `sys.path`. Running a file directly
puts that file's own folder (`src/services`) first instead.

## Evidence

```
$ python src/services/CameraCalibrator.py
  File ".../src/services/CameraCalibrator.py", line 2, in <module>
    from src.utils.Dispatcher import Dispatcher
ModuleNotFoundError: No module named 'src'            (exit code 1)

$ python -m src.services.CameraCalibrator            # from the repository root: works
```

The same applies to every test script (`python -m src.tests.StereoCameraTest`).

## Effects

- The most natural command (pressing "Run" on the file in an editor, or `python path/to/file.py`) fails.
- Nothing in the repository said how to launch it (the README was empty); the working command is now in the
  [README](../../README.md).
- `Configurator.getProjectRoot()` is another layout assumption (it walks up looking for `config/` and `src/`),
  so the project cannot be moved into a package or installed without edits.

## Suggested fix

Add a module entry point so the short command works:

```python
# src/__main__.py
from src.services.CameraCalibrator import CameraCalibrator

if __name__ == "__main__":
    CameraCalibrator.calibrate()
```

Then `python -m src` runs it (verified). For a longer-term fix, add a `pyproject.toml` and a console script
so it can be installed with `pip install -e .`.
