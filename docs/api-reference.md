# API reference

Method names use the repository's `camelCase`. Private (double-underscore) methods are
omitted except where they matter.

## `src.services.CameraCalibrator.CameraCalibrator`

| Method | Description |
|--------|-------------|
| `calibrate()` *(static)* | Builds the calibrator via `Dispatcher`, runs the interactive loop, and always closes windows and releases the camera in a `finally` block |

`python -m src.services.CameraCalibrator` calls it inside a `try/except Exception` that
only prints `An error occurred: ...` ([P06](problems/P06-errors-printed-not-raised-exit-code-always-zero.md)).

## `src.utils.Dispatcher.Dispatcher`

| Method | Description |
|--------|-------------|
| `getCalibrator()` *(static)* | Reads `chosen_calibrator`; returns `StereoCalibrator()` for `stereo`, `MonocularCalibrator()` for `monocular`, else raises `ValueError` |

## `src.utils.Configurator.Configurator(pkg=None)`

Constants: `CHECKERBOARD`, `STEREO_CAMERA`, `MONOCULAR_CAMERA`, `CALIBRATOR`.

| Method | Description |
|--------|-------------|
| `getProjectRoot()` *(static)* | Walks up from the file until a directory containing both `config/` and `src/` is found; raises `FileNotFoundError` otherwise |
| `fetchData(data_type)` | Returns the parsed YAML as a dict. **On a missing file, bad YAML or unknown type it prints a message and returns `None`** |
| `setConfig(data_type, new_data)` | Merges `new_data` into the YAML file and rewrites it. Not used anywhere in the project |
| `getConfigsNames()` | Returns the constant values. Not used anywhere |

`pkg` (when set) redirects to `src/<pkg>/config`; no such folders exist and nothing passes it.

## `src.interfaces`

### `ICamera`
`open()`, `getFrames()`, `getCapture()`, `release()`.
`getFrames()` returns `(left, right)` for stereo and a single frame for monocular.

### `ICalibrator`
| Method | Intended behaviour |
|--------|--------------------|
| `grabPreviewFrame()` | Grab frame(s), detect the board, return `(display_frame, found, raw_data)`; `display_frame` is `None` on camera failure |
| `saveImage(raw_data)` | Save the raw frame(s) from the last `grabPreviewFrame` as the next calibration image(s) |
| `deleteLastImage()` | Remove the most recently saved image(s) |
| `isDirty()` | `True` if images were saved since the last `calibrate()` |
| `getWindowName()` | Window title |
| `release()` | Release the camera |
| `previewFrame()` | Grab frame(s), apply the saved calibration, return a display frame or `None` |
| `calibrate()` | Documented as computing *and returning* the parameters; both implementations save to disk and return `None` ([P11](problems/P11-interface-contracts-not-enforced-or-honoured.md)) |

## `StereoCamera(camera_cfg)` / `MonocularCamera(camera_cfg)`

| Method | Description |
|--------|-------------|
| `open()` | Opens the device, requests resolution / MJPG / 30 FPS, prints requested vs actual size. On failure prints and leaves the capture as `None` (does not raise, returns nothing) |
| `getFrames()` | Reads one frame. Stereo returns `(left, right)` split at `width // 2`; monocular returns the frame. Returns `(None, None)` / `None` on failure |
| `getCapture()` | The underlying `cv2.VideoCapture` (or `None`) |
| `release()` | Releases and clears the capture |
| `resize_for_preview(img)` | Resize to `preview_width`, keeping aspect ratio |

## `StereoCalibrator()` / `MonocularCalibrator()`

Both implement `ICalibrator`. Public attributes set in `__init__`: `camera`, `CHECKERBOARD`
`(columns, rows)`, `SQUARE_SIZE_MM`, `OUTPUT_FILE`, `saved_count`.

Notable behaviour:
- `saved_count` starts as the **number of `*.png` files** in the (left) image folder and
  names the next file `f"{saved_count:03d}.png"` ([P01](problems/P01-image-numbering-overwrites-existing-pairs.md)).
- `calibrate()` catches every exception, prints `Error during calibration: ...` and returns `None`.
- Stereo enforces no minimum number of usable pairs (it only prints a warning below 10). Monocular refuses to calibrate below 5 usable images (the error is caught and printed).
- Constructing either class opens the camera.

## `CalibrationHelper` (all static)

| Method | Description |
|--------|-------------|
| `buildObjectPoints(CHECKERBOARD, SQUARE_SIZE_MM)` | `(cols*rows, 3)` float32 board-frame corner coordinates in mm, `Z = 0` |
| `findCorners(paths, objp, CHECKERBOARD, SUBPIX_CRITERIA)` | Detects + sub-pixel-refines corners; returns `(objpoints, imgpoints, img_size, used_files)`. Prints `[skip]` for images without a board |
| `calibrateSingle(objpoints, imgpoints, img_size, label, CALIB_CRITERIA)` | `cv2.calibrateCamera`; prints and returns `(K, D, rms, rvecs, tvecs)` |
| `deleteLastSaved(dirs, index)` | Deletes `f"{index:03d}.png"` from each directory; returns whether anything was deleted |
| `buildUndistortMaps(K, D, img_size)` | `getOptimalNewCameraMatrix(alpha=0)` + `initUndistortRectifyMap` |
| `buildStereoRectifyMaps(K1, D1, K2, D2, R, T, img_size)` | `stereoRectify(CALIB_ZERO_DISPARITY, alpha=0)` + two undistort-rectify maps. **Discards `Q`** ([P10](problems/P10-calibration-file-schema-misleading-and-incomplete.md)) |
