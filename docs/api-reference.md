# API reference

Method names use the repository's `camelCase`. Private (double-underscore) methods are
omitted except where they matter.

## `src.services.CameraCalibrator.CameraCalibrator`

| Method | Description |
|--------|-------------|
| `calibrate()` *(static)* | Builds the calibrator via `Dispatcher`, runs the interactive loop (running the actual `calibrate()` call on a background thread so the window stays responsive), and always closes windows and releases the camera in a `finally` block |
| `drawCalibrationBanner(frame, text=...)` *(static)* | Returns a copy of `frame` with a red border/banner drawn on it; used while a background calibration is running |

Both the installed console script (`calibrate-camera`) and
`python -m src.services.CameraCalibrator` call `CameraCalibrator.calibrate()` directly. The
module's own `__main__` block additionally wraps it in `try/except Exception`, prints the
error, and calls `sys.exit(1)`; an uncaught exception from the console script form instead
propagates as a normal Python traceback with a non-zero exit code.

## `src.utils.Dispatcher.Dispatcher`

| Method | Description |
|--------|-------------|
| `getCalibrator()` *(static)* | Reads `chosen_calibrator`, `min_images`, `max_rms`; returns `StereoCalibrator(min_images, max_rms)` for `stereo`, `MonocularCalibrator(min_images, max_rms)` for `monocular`, else raises `ValueError` |

## `src.utils.Configurator.Configurator()`

Constants: `CHECKERBOARD`, `STEREO_CAMERA`, `MONOCULAR_CAMERA`, `CALIBRATOR`.

| Method | Description |
|--------|-------------|
| `getProjectRoot()` *(static)* | Walks up from the file until a directory containing both `config/` and `src/` is found; raises `FileNotFoundError` otherwise |
| `fetchData(data_type)` | Returns the parsed YAML as a dict. Raises `FileNotFoundError` for a missing file, `RuntimeError` for invalid YAML, or `TypeError` for an unsupported `data_type` |
| `setConfig(data_type, new_data)` | Merges `new_data` into the YAML file and rewrites it, creating the file if needed. Not called anywhere in the project; covered by `src/tests/test_configurator.py` |

## `src.exceptions`

| Exception | Raised by |
|-----------|-----------|
| `CameraSetupError` | `StereoCalibrator`/`MonocularCalibrator.__setupCamera` when the camera can't be opened or won't deliver an initial frame |
| `CameraCalibrationError` | `StereoCalibrator`/`MonocularCalibrator.calibrate` when anything in the calibration pipeline fails (not enough images, mismatched sets, an OpenCV error, ...) |
| `DifferentImageSizeError` | `previewFrame()` when the live frame size doesn't match the size stored in the calibration file |

## `src.interfaces`

### `ICamera`
`open()`, `getFrames()`, `getCapture()`, `release()`.
`getFrames()` returns `(left, right)` for stereo and a single frame for monocular — the
docstring states this explicitly, and `src/tests/test_interfaces.py` runs
`zope.interface.verify.verifyClass` against both implementations.

### `ICalibrator`
| Method | Documented behaviour |
|--------|--------------------|
| `grabPreviewFrame()` | Grab frame(s), detect the board, return `(display_frame, found, raw_data)`; `display_frame` is `None` on camera failure |
| `saveImage(raw_data)` | Save the raw frame(s) from the last `grabPreviewFrame` as the next calibration image(s) |
| `deleteLastImage()` | Remove the most recently saved image(s); marks the calibration dirty |
| `isDirty()` | `True` if images were saved or deleted since the last `calibrate()` |
| `getWindowName()` | Window title |
| `release()` | Release the camera (a no-op if the camera was never opened) |
| `previewFrame()` | Grab frame(s), apply the **latest time-stamped** calibration (accepted or not), return a display frame or `None` |
| `calibrate()` | Runs the calibration pipeline and saves it as a new time-stamped result; the accepted file is not touched. Returns `None` — the result has to be read back from disk |
| `acceptLatest()` | Copy the latest time-stamped calibration over the accepted `<mode>_calib.npz`; returns `True` on success, `False` if there is nothing to accept yet |

Covered end-to-end (save/accept/preview, without real hardware) by
`src/tests/test_timestamped_calibration.py`.

## `StereoCamera(camera_cfg)` / `MonocularCamera(camera_cfg)`

| Method | Description |
|--------|-------------|
| `open()` | Opens the device, requests resolution / MJPG / 30 FPS, prints requested vs actual size. Raises `RuntimeError` if the device can't be opened |
| `getFrames()` | Reads one frame. Stereo returns `(left, right)` split at `width // 2`; monocular returns the frame. Returns `(None, None)` / `None` on a single failed read (does not raise — a transient dropped frame is expected during live capture) |
| `getCapture()` | The underlying `cv2.VideoCapture` (or `None`) |
| `release()` | Releases and clears the capture; safe to call when nothing was opened |
| `resize_for_preview(img)` | Resize to `preview_width`, keeping aspect ratio |

## `StereoCalibrator(min_images=10, max_rms=1.0)` / `MonocularCalibrator(min_images=10, max_rms=1.0)`

Both implement `ICalibrator`. Public attributes set in `__init__`: `camera`, `CHECKERBOARD`
`(columns, rows)`, `SQUARE_SIZE_MM`, `OUTPUT_FILE` (the accepted file path), `TIMESTAMPED_DIR`,
`saved_count`.

Notable behaviour:
- `saved_count` is the number of `*.png` files found at startup; the **next** file name comes
  from `CalibrationHelper.getStartIndex`, which uses the highest existing index + 1 rather
  than a plain count, so deleting a file by hand does not cause the next save to collide with
  one that still exists.
- `calibrate()` raises `CameraCalibrationError` on failure instead of printing and returning.
- Monocular refuses to calibrate below `min_images` captured images or 5 *usable* ones
  (raises `RuntimeError`, wrapped as `CameraCalibrationError`). Stereo only prints a warning
  below 10 usable pairs (its `min_images` constructor argument is accepted but not enforced).
- Constructing either class opens the camera; a failure raises `CameraSetupError`.

## `CalibrationHelper` (all static)

| Method | Description |
|--------|-------------|
| `buildObjectPoints(CHECKERBOARD, SQUARE_SIZE_MM)` | `(cols*rows, 3)` float32 board-frame corner coordinates in mm, `Z = 0` |
| `findCorners(paths, objp, CHECKERBOARD, SUBPIX_CRITERIA)` | Detects + sub-pixel-refines corners; returns `(objpoints, imgpoints, img_size, used_files)`. Prints `[skip]` for images without a board |
| `calibrateSingle(objpoints, imgpoints, img_size, label, CALIB_CRITERIA)` | `cv2.calibrateCamera`; prints and returns `(K, D, rms, rvecs, tvecs)` |
| `perViewErrors(objpoints, imgpoints, rvecs, tvecs, K, D, labels, title)` | Reprojects each view, prints its RMS and the file name of the worst one, returns the list of per-view errors |
| `deleteLastSaved(dirs, index)` | Deletes `f"{index:03d}.png"` from each directory; returns whether anything was deleted |
| `getStartIndex(dirs)` | Highest existing `NNN.png` index across `dirs`, plus one (`-1 + 1 = 0` if none exist) |
| `saveTimestamped(directory, prefix, **arrays)` | `np.savez`s `arrays` to `<prefix>_YYYYMMDD_HHMMSS.npz`, disambiguating with a numeric suffix if that name is somehow already taken; returns the path |
| `latestTimestamped(directory)` | Newest `*.npz` in `directory` by name, or `None` |
| `acceptCalibration(src, dst)` | Copies `src` over `dst` via a temp file + `os.replace`, so a crash mid-copy can't leave `dst` half-written |
| `checkImageSize(img_size, data)` | `True` if `img_size` matches the `img_size` stored in the loaded `.npz` `data` |
| `buildUndistortMaps(K, D, img_size)` | `getOptimalNewCameraMatrix(alpha=0)` + `initUndistortRectifyMap` |
| `buildStereoRectifyMaps(K1, D1, K2, D2, R, T, img_size)` | `stereoRectify(CALIB_ZERO_DISPARITY, alpha=0)` + two undistort-rectify maps. **Discards `Q`** ([P01](problems/P01-stereo-calibration-does-not-save-rectification-outputs.md)) |
