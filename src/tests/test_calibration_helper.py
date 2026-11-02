import numpy as np
import cv2
from src.helpers.CalibrationHelper import CalibrationHelper


def _make_view(objp, K, D, rvec, tvec, noise=0.0):
    """Project a checkerboard with a known pose; optionally jitter the 'detected' corners."""
    imgp, _ = cv2.projectPoints(objp, rvec, tvec, K, D)
    if noise:
        imgp = imgp + noise
    return imgp.astype(np.float32)


def test_per_view_errors_flags_the_worst_view():
    K = np.array([[1000.0, 0, 320], [0, 1000.0, 240], [0, 0, 1]])
    D = np.zeros((5, 1))
    objp = np.zeros((6, 3), np.float32)
    objp[:, :2] = np.mgrid[0:3, 0:2].T.reshape(-1, 2) * 30

    rvecs = [np.array([[0.0], [0.0], [0.0]]) for _ in range(4)]
    tvecs = [np.array([[0.0], [0.0], [500.0 + 10 * i]]) for i in range(4)]
    labels = [f"view_{i:03d}.png" for i in range(4)]

    objpoints = [objp for _ in range(4)]
    imgpoints = [
        _make_view(objp, K, D, rvecs[0], tvecs[0]),
        _make_view(objp, K, D, rvecs[1], tvecs[1]),
        _make_view(objp, K, D, rvecs[2], tvecs[2], noise=15.0),  # deliberately bad view
        _make_view(objp, K, D, rvecs[3], tvecs[3]),
    ]

    errs = CalibrationHelper.perViewErrors(objpoints, imgpoints, rvecs, tvecs, K, D, labels, "TEST")

    assert len(errs) == 4
    worst_idx = int(np.argmax(errs))
    assert worst_idx == 2
    assert errs[2] > 10 * max(errs[0], errs[1], errs[3])


def test_per_view_errors_empty_input_returns_empty_list():
    K = np.eye(3)
    D = np.zeros((5, 1))
    assert CalibrationHelper.perViewErrors([], [], [], [], K, D, [], "TEST") == []
