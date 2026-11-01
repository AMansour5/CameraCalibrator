from src.services.stereo.StereoCalibrator import StereoCalibrator

def test_initialization():
    calibrator = StereoCalibrator()
    assert calibrator.camera is not None
    assert calibrator.CHECKERBOARD is not None
    assert calibrator.SQUARE_SIZE_MM is not None

def test_grab_preview_frame_method_exists():
    calibrator = StereoCalibrator()
    assert hasattr(calibrator, 'grabPreviewFrame')
    assert callable(getattr(calibrator, 'grabPreviewFrame'))

def test_grab_preview_frame_method():
    calibrator = StereoCalibrator()
    try:
        calibrator.grabPreviewFrame()
    except Exception as e:
        assert False, f"grabPreviewFrame method raised an exception: {e}"

def test_calibrate_method_exists():
    calibrator = StereoCalibrator()
    assert hasattr(calibrator, 'calibrate')
    assert callable(getattr(calibrator, 'calibrate'))

def test_calibrate_method():
    calibrator = StereoCalibrator()
    try:
        calibrator.calibrate()
    except Exception as e:
        assert False, f"calibrate method raised an exception: {e}"