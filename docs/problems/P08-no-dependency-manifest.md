# P08: No dependency list

**Severity:** Medium (first-run failure) **Evidence:** `git ls-files` shows none; import failure observed
**Component:** repository root

## What the code does

The code imports `cv2`, `numpy`, `yaml` (PyYAML) and `zope.interface`, but the repository has no
`requirements.txt`, `pyproject.toml` or `setup.py`. The README was empty, so nothing else says what to install.

## Evidence

```
$ git ls-files | grep -E "requirements|pyproject|setup"
(nothing)
$ python -m src.services.CameraCalibrator        # in an environment without zope.interface
ModuleNotFoundError: No module named 'zope'
```

## Effects

- A fresh clone fails at import time, one missing package at a time (`cv2`, then `yaml`, then `zope`).
- `zope.interface` is the least obvious dependency (a rarely-used package for a small project), so it is the one
  people are most likely to hit.
- No record of which versions work. This documentation was verified with OpenCV 4.13.0, NumPy 2.4.4, PyYAML 6.0.3.

## Suggested fix

Add `requirements.txt`:

```
opencv-python
numpy
PyYAML
zope.interface
```

then pin the versions you have actually tested (`pip freeze | grep -iE "opencv|numpy|yaml|zope"`).
Consider replacing `zope.interface` with `abc.ABC` or `typing.Protocol` ([P11](P11-interface-contracts-not-enforced-or-honoured.md)) to drop one dependency.
