# P11: The interfaces describe a contract the implementations do not honour or check

**Severity:** Medium (design) **Evidence:** reproduced with `zope.interface.verify` **Component:** `ICalibrator`, `ICamera`, both camera and calibrator classes

## What the code does

- `ICalibrator.calibrate()` is documented as computing the camera parameters **and returning them**
  (`ICalibrator.py:25-26`). Both implementations save to disk and return `None`.
- `ICamera.getFrames()` is one method with two different return shapes: a `(left, right)` tuple for stereo and a single
  array for monocular (`ICamera.py:14-19`).
- `ICamera.open()` has no stated way to report failure; both implementations swallow errors ([P05](P05-camera-open-failure-crashes-on-release.md)).
- `@implementer(...)` only *declares* conformance. Nothing in the project calls `verifyClass` / `verifyObject`.

## Evidence

```
verifyClass(ICalibrator, StereoCalibrator): True
verifyClass(ICamera, StereoCamera): True
verifyClass(ICamera, MonocularCamera): True
ICalibrator.calibrate() is documented to 'return' the camera parameters; actual return value: None
```

`verifyClass` passes because it checks method names and signatures only. It cannot see return values.

## Effects

- Code written against `ICamera` cannot treat stereo and monocular cameras the same: it has to know which one it has
  to unpack the result. The abstraction does not abstract.
- Callers of `calibrate()` get nothing back, so a future caller (for example a depth pipeline) must re-read the file.
- The interface layer adds a dependency (`zope.interface`, [P08](P08-no-dependency-manifest.md)) without providing the checking that is its main benefit.
- Today the loop only uses `ICalibrator` and never calls `getFrames` directly, so nothing breaks yet; the risk is in new code.

## Suggested fix

- Decide what `calibrate()` returns (for example a result dict with `K`, `D`, `rms`, and the stereo extras) and make both
  implementations return it, or change the docstring to say it returns nothing.
- Make `getFrames()` always return a tuple (monocular: `(frame,)`) or split it into `getFrame()` / `getStereoFrames()`.
- Add one test that runs `verifyClass`, or switch to `abc.ABC` / `typing.Protocol` (no extra package).
