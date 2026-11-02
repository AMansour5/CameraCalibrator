# P04: The shipped camera config defaults are specific to one machine

**Severity:** Low **Evidence:** config files **Component:** `config/`

## What the repository does

`config/stereo_camera.yaml` uses `camera_index: /dev/video2` and
`config/monocular_camera.yaml` uses `/dev/video0`: Linux paths for the author's current USB
layout. There is no `config/*.example.yaml` or generic fallback shipped alongside them.

(The other half of this problem as originally filed — generated `.npz` calibration files being
tracked in git — is fixed: `src/matrices/**/*.npz` is in `.gitignore` and nothing under
`src/matrices/` is tracked.)

## Effects

- The default camera settings fail on Windows/macOS, and `/dev/videoN` numbers can change after
  re-plugging or rebooting. This is often the first error a new user sees (`Could not open
  camera index /dev/video2`).
- Anyone adapting the project for their own camera has to edit the shipped YAML in place
  instead of copying a template, which makes it easy to accidentally commit a personal device
  path as the new default.

## Suggested fix

- Ship `config/*.example.yaml` (copy to `*.yaml` locally), or use generic defaults
  (`camera_index: 0`).
- On Linux a stable name such as `/dev/v4l/by-id/<your-camera>` survives re-plugging.
