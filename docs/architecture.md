# Architecture

## Layers

```
            python -m src.services.CameraCalibrator
                          |
                 CameraCalibrator.calibrate()          <- interactive loop (keys, cv2 windows)
                          |
                 Dispatcher.getCalibrator()            <- reads config/calibrator.yaml
                  /                      \
        StereoCalibrator            MonocularCalibrator   <- implement ICalibrator
              |                              |
        StereoCamera                 MonocularCamera      <- implement ICamera
              \                              /
               CalibrationHelper (static OpenCV wrappers)
                          |
                  Configurator (YAML) , cv2 , numpy
```

The loop knows nothing about stereo vs monocular. It only calls the `ICalibrator`
methods, so adding a third camera type means adding a calibrator + camera class and one
branch in `Dispatcher`.

## Components

| Component | Responsibility |
|-----------|----------------|
| `CameraCalibrator` | Owns the window and key handling; switches between capture and preview mode; calibrates on `c` and on `q` (if dirty); always releases the camera and closes windows in a `finally` block |
| `Dispatcher` | Reads `chosen_calibrator` and returns a `StereoCalibrator` or `MonocularCalibrator`; raises `ValueError` for any other value |
| `ICalibrator` | The contract the loop relies on: `grabPreviewFrame`, `saveImage`, `deleteLastImage`, `isDirty`, `getWindowName`, `release`, `previewFrame`, `calibrate` |
| `ICamera` | `open`, `getFrames`, `getCapture`, `release` |
| `StereoCamera` | Opens one `VideoCapture` (MJPG, 30 FPS requested), checks the resolution the driver actually accepted, and splits each frame at `width // 2` into left/right |
| `MonocularCamera` | Same, without the split |
| `StereoCalibrator` / `MonocularCalibrator` | Detect the board for live feedback, save images, run the calibration, save the `.npz`, build preview maps |
| `CalibrationHelper` | Stateless helpers: object points, corner detection + sub-pixel refinement, `calibrateCamera`, delete-by-index, undistort / stereo-rectify maps |
| `Configurator` | Loads (and can update) the YAML files in `config/`; finds the project root by walking up until it sees both `config/` and `src/` |

## Startup sequence (stereo)

1. `Dispatcher` reads `chosen_calibrator` -> `StereoCalibrator()`.
2. `StereoCalibrator.__init__` loads the board + camera config, creates the image and
   result folders, counts existing `*.png` files in `left/` to initialise `saved_count`,
   and opens the camera.
3. `__setupCamera` opens the device, requests the resolution, prints
   `Requested WxH, camera reports WxH`, warns on mismatch, and grabs one test frame.
   If anything fails it prints an error and sets `self.camera = None` ([P05](problems/P05-camera-open-failure-crashes-on-release.md)).

## The main loop

```
capture mode:                         preview mode:
  grabPreviewFrame()                    previewFrame()  (rectified / undistorted)
    -> (display, found, raw)              -> None if no calibration file / camera fail
  imshow(display)                       imshow(display)
  s (and found) -> saveImage(raw)       r -> back to capture mode
  c -> calibrate()   (blocks, P12)      q -> quit
  x -> deleteLastImage()
  p -> preview mode
  q -> calibrate() if dirty, then quit
```

`isDirty()` becomes `True` when an image is saved and `False` after a successful
calibration. It is **not** set by deletions ([P03](problems/P03-delete-does-not-mark-calibration-dirty.md)).

## Stereo calibration pipeline (`StereoCalibrator.calibrate`)

1. Collect `left/*.png` and `right/*.png` (sorted); counts must match and be non-zero.
2. For each image: grayscale -> `findChessboardCorners` (default flags) ->
   `cornerSubPix` (11x11 half-window, 100 iterations / 1e-5).
3. Check left and right image sizes are equal.
4. Keep only file names that were detected in **both** views. Warn if fewer than 10.
5. `calibrateCamera` on each eye separately -> `K1, D1` and `K2, D2` (default flags: full
   5-coefficient model, focal lengths and principal point free).
6. `stereoCalibrate` with `CALIB_FIX_INTRINSIC` (intrinsics from step 5 held fixed;
   only `R` and `T` are solved) -> `R`, `T`, RMS.
7. Print results (baseline = `|T|`, per-camera and stereo RMS, warning if stereo RMS > 1.0).
8. `np.savez` the result; clear the dirty flag and cached rectification maps.

Object points are built in millimetres from `square_size_mm`, so `T` and the baseline come
out in millimetres.

## Monocular differences

Single image folder, one `calibrateCamera` call, minimum 5 usable images, and the saved
file keeps the per-view `rvecs`/`tvecs` under the names `R`/`T` ([P10](problems/P10-calibration-file-schema-misleading-and-incomplete.md)).
Preview uses `getOptimalNewCameraMatrix(alpha=0)` then `initUndistortRectifyMap`.

## Extending

To add a camera type: implement `ICamera` and `ICalibrator`, add the
class to `Dispatcher`, add a config file name constant to `Configurator`, and document
the new `chosen_calibrator` value.
