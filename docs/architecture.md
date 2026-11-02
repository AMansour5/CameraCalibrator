# Architecture

## Layers

```
     calibrate-camera  (or: python -m src.services.CameraCalibrator)
                          |
                 CameraCalibrator.calibrate()          <- interactive loop (keys, cv2 windows,
                          |                                worker thread for calibrate())
                 Dispatcher.getCalibrator()            <- reads config/calibrator.yaml
                  /                      \
        StereoCalibrator            MonocularCalibrator   <- implement ICalibrator
              |                              |
        StereoCamera                 MonocularCamera      <- implement ICamera
              \                              /
               CalibrationHelper (static OpenCV wrappers)
                          |
         Configurator (YAML) , cv2 , numpy , src.exceptions.*
```

The loop knows nothing about stereo vs monocular. It only calls the `ICalibrator` methods, so
adding a third camera type means adding a calibrator + camera class and one branch in
`Dispatcher`.

## Components

| Component | Responsibility |
|-----------|----------------|
| `CameraCalibrator` | Owns the window and key handling; switches between capture and preview mode; runs `calibrate()` on a background thread for `c` and for `q` when dirty, drawing a red "CALIBRATING..." banner over the live feed meanwhile; always releases the camera and closes windows in a `finally` block |
| `Dispatcher` | Reads `chosen_calibrator` (plus `min_images`/`max_rms`) and returns a `StereoCalibrator` or `MonocularCalibrator`; raises `ValueError` for any other value |
| `ICalibrator` | The contract the loop relies on: `grabPreviewFrame`, `saveImage`, `deleteLastImage`, `isDirty`, `getWindowName`, `release`, `previewFrame`, `calibrate`, `acceptLatest` |
| `ICamera` | `open`, `getFrames`, `getCapture`, `release` |
| `StereoCamera` | Opens one `VideoCapture` (MJPG, 30 FPS requested), checks the resolution the driver actually accepted, and splits each frame at `width // 2` into left/right; raises `RuntimeError` if the device can't be opened |
| `MonocularCamera` | Same, without the split |
| `StereoCalibrator` / `MonocularCalibrator` | Detect the board for live feedback, save images, run the calibration, save a new time-stamped `.npz`, promote it to the final file on `acceptLatest()`, build preview maps |
| `CalibrationHelper` | Stateless helpers: object points, corner detection + sub-pixel refinement, `calibrateCamera`, per-view reprojection errors, delete-by-index, next-free-index lookup, time-stamped save/accept, image-size check, undistort / stereo-rectify maps |
| `Configurator` | Loads (and can update) the YAML files in `config/`; finds the project root by walking up until it sees both `config/` and `src/`; raises on a missing/invalid file instead of printing and returning `None` |
| `src.exceptions` | `CameraSetupError`, `CameraCalibrationError`, `DifferentImageSizeError` — raised instead of printed, so the entry point can report a real failure and exit non-zero |

## Startup sequence (stereo)

1. `Dispatcher` reads `chosen_calibrator`, `min_images`, `max_rms` -> `StereoCalibrator(min_images, max_rms)`.
2. `StereoCalibrator.__init__` loads the board + camera config, creates the image and result
   folders (including `.../time_stamped/`), derives the next free image index from the highest
   existing file name (`CalibrationHelper.getStartIndex`), and opens the camera.
3. `__setupCamera` opens the device, requests the resolution, prints
   `Requested WxH, camera reports WxH`, warns on mismatch, and grabs one test frame. If
   anything fails it raises `CameraSetupError` with the underlying message; the camera never
   ends up half-initialised.

## The main loop

```
capture mode:                          preview mode:
  grabPreviewFrame()                     previewFrame()  (rectified / undistorted,
    -> (display, found, raw)                latest time-stamped calibration)
  imshow(display)                        imshow(display)
  s (and found) -> saveImage(raw)        r -> back to capture mode
  c -> start calibrate() on a thread     a -> acceptLatest() (promote latest to final file)
  x -> deleteLastImage()                 q -> quit
  p -> preview mode
  a -> acceptLatest()
  q -> if dirty: start calibrate(), quit once it finishes; else quit immediately
```

While a calibration is running, the loop keeps showing live frames with a "CALIBRATING..."
banner and ignores capture/preview-switching keys; `q` during that time marks quit-pending and
exits as soon as the worker thread finishes.

`isDirty()` becomes `True` when an image is saved **or deleted**, and `False` after a
successful `calibrate()` call.

## Stereo calibration pipeline (`StereoCalibrator.calibrate`)

1. Collect `left/*.png` and `right/*.png` (sorted); counts must match and be non-zero, or a
   `RuntimeError` is raised (wrapped as `CameraCalibrationError`).
2. For each image: grayscale -> `findChessboardCorners` (default flags) -> `cornerSubPix`
   (11x11 half-window, 100 iterations / 1e-5).
3. Check left and right image sizes are equal.
4. Keep only file names that were detected in **both** views. Warn if fewer than 10.
5. `calibrateCamera` on each eye separately -> `K1, D1` (+ `rvecs`/`tvecs`) and `K2, D2`
   (default flags: full 5-coefficient model, focal lengths and principal point free).
6. `CalibrationHelper.perViewErrors` once per camera: prints every view's reprojection RMS and
   names the worst one.
7. `stereoCalibrate` with `CALIB_FIX_INTRINSIC` (intrinsics from step 5 held fixed; only `R`,
   `T`, `E`, `F` are solved) -> RMS.
8. Print results (baseline = `|T|`, per-camera and stereo RMS, warning if stereo RMS > 1.0).
9. `CalibrationHelper.saveTimestamped` writes a new file under `.../time_stamped/`; the
   accepted `<mode>_calib.npz` is untouched until `acceptLatest()` is called. Clears the dirty
   flag and cached rectification maps.

Object points are built in millimetres from `square_size_mm`, so `T` and the baseline come out
in millimetres.

## Monocular differences

Single image folder, one `calibrateCamera` call, a hard minimum of `min_images` captured
images plus a minimum of 5 *usable* ones (board actually detected), and the saved file keeps
the per-view pose vectors under their real names, `rvecs`/`tvecs` (not `R`/`T`). Preview uses
`getOptimalNewCameraMatrix(alpha=0)` then `initUndistortRectifyMap`.

## Extending

To add a camera type: implement `ICamera` and `ICalibrator`, add the class to `Dispatcher`, add
a config file name constant to `Configurator`, and document the new `chosen_calibrator` value.
