import numpy as np
from src.services.CameraCalibrator import CameraCalibrator


def test_banner_marks_frame_without_mutating_input():
    frame = np.zeros((100, 200, 3), dtype=np.uint8)
    out = CameraCalibrator.drawCalibrationBanner(frame)
    assert frame.sum() == 0
    assert out.sum() > 0
