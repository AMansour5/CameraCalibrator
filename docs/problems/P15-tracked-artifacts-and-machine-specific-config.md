# P15: Generated calibration files are tracked in git, and the shipped config is specific to one machine

**Severity:** Low **Evidence:** `git ls-files`; config files **Component:** repository, `config/`, `.gitignore`

## What the repository does

- `.gitignore` ignores `*.png`, `*.jpg`, `__pycache__/`, `*.pyc` and `.vscode/`, but **not** `*.npz`. Both result files
  are committed: `src/matrices/stereo/stereo_calib.npz` and `src/matrices/monocular/monocular_calib.npz`.
- They belong to the author's cameras (the stereo file: 1920 x 1080 per eye, baseline 119.4 mm).
- `config/stereo_camera.yaml` uses `camera_index: /dev/video2` and `config/monocular_camera.yaml` uses `/dev/video0`:
  Linux paths for the author's current USB layout.

**Status:** the `.npz`-tracking half is resolved in the working tree: `src/matrices/**/*.npz` is now in
`.gitignore` and the two previously committed files are removed, as part of finishing the `matricies` →
`matrices` rename ([P16](P16-dead-code-copied-code-and-naming.md)). The machine-specific `config/*.yaml`
defaults below are still open.

## Effects

- Anyone who clones the repository starts with someone else's calibration. Pressing `p` shows a "CALIBRATED PREVIEW" that
  is wrong for their camera, with no warning ([P04](P04-preview-ignores-stored-image-size.md)). Any code that loads the file silently uses the wrong parameters.
- Every calibration run modifies a tracked binary, so `git status` is always dirty and it is easy to commit (and overwrite) a
  teammate's calibration by accident. Binary diffs are not reviewable.
- The default camera settings fail on Windows/macOS, and `/dev/videoN` numbers can change after re-plugging or rebooting.
  This is the first error a new user sees ([P05](P05-camera-open-failure-crashes-on-release.md)).

## Suggested fix

- ~~Add `src/matrices/**/*.npz` to `.gitignore` and run `git rm --cached` on the two files.~~ **Done.** If a
  sample is useful, keep it in `examples/` with a note that it is not yours.
- Ship `config/*.example.yaml` (copy to `*.yaml` locally), or use generic defaults (`camera_index: 0`).
- On Linux a stable name such as `/dev/v4l/by-id/<your-camera>` survives re-plugging.
