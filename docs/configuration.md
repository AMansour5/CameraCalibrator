# Configuration

All settings live in `config/*.yaml` at the repository root. They are read when the
calibrator is created, so restart the program after editing.

## `config/calibrator.yaml`

| Key | Values | Meaning |
|-----|--------|---------|
| `chosen_calibrator` | `stereo` or `monocular` | Which calibrator the dispatcher builds. Anything else raises `ValueError: Unknown calibrator type: ...` |
| `min_images` | integer, default `10` | Minimum number of captured images before `calibrate()` will run. **Enforced for monocular** (raises if fewer are on disk); stereo only prints a warning below 10 *usable* pairs regardless of this value |
| `max_rms` | float (px), default `1.0` | Threshold above which the console prints a "high RMS" note after calibrating. This is informational only — the result is still saved either way; see [P02](problems/P02-no-orientation-check-adaptive-subpixel-window-or-held-out-validation.md) |

## `config/checkerboard.yaml` (shared by both modes)

| Key | Required | Default in code | Meaning |
|-----|----------|-----------------|---------|
| `columns` | yes | none (`KeyError` if missing) | Number of **inner corners** along the board's width |
| `rows` | yes | none (`KeyError` if missing) | Number of **inner corners** along the board's height |
| `square_size_mm` | no | `30` | Side of one printed square in millimetres. Sets the unit of `T` and the baseline |

Shipped values: `columns: 8`, `rows: 5`, `square_size_mm: 30` (a 9 x 6 squares board).

Notes:
- Count inner corners, not squares.
- One even and one odd count gives an unambiguous orientation; two even or two odd does not ([P02](problems/P02-no-orientation-check-adaptive-subpixel-window-or-held-out-validation.md)).
- If you change these after capturing images, the saved images no longer match the
  settings; recapture or restore the old values before calibrating.

## `config/stereo_camera.yaml`

| Key | Default in code | Meaning |
|-----|-----------------|---------|
| `camera_index` | `0` | Anything `cv2.VideoCapture` accepts: an integer, or a device path such as `/dev/video2` |
| `combined_width` | `1280` | Width of the **whole** side-by-side frame in pixels (left + right) |
| `combined_height` | `480` | Height of the frame in pixels |
| `preview_width` | `640` | Width each half is resized to for the on-screen preview. Saved images are full size |

Shipped values: `/dev/video2`, `3840 x 1080` (so each eye is `1920 x 1080`), preview `640`.

The camera class also requests MJPG and 30 FPS (not configurable). The frame is split at
`width // 2`. If the camera returns a different size than requested, set the values to what
it reports.

## `config/monocular_camera.yaml`

| Key | Default in code | Meaning |
|-----|-----------------|---------|
| `camera_index` | `0` | As above |
| `width` | `1280` | Frame width |
| `height` | `720` | Frame height |
| `preview_width` | `640` | Preview width |

Shipped values: `/dev/video0`, `1280 x 720`, preview `640`.

## Gotchas

- Device paths like `/dev/video2` are Linux-specific and can change when USB devices are
  re-plugged or the machine reboots ([P04](problems/P04-shipped-camera-config-is-machine-specific.md)). On Windows/macOS use an integer index.
- A missing or unreadable config file now raises (`FileNotFoundError`, `RuntimeError`, or
  `TypeError`) instead of printing a message and returning `None`, so the program fails
  immediately with a clear cause rather than later with a confusing symptom.
- The values are not validated (no range or type checks).
