from src.services.monocular.MonocularCalibrator import MonocularCalibrator

class TestMonocularCalibrator:
    def test_initialization(self):
        calibrator = MonocularCalibrator()
        assert calibrator.camera is not None
        assert calibrator.CHECKERBOARD is not None
        assert calibrator.SQUARE_SIZE_MM is not None

    def test_grab_preview_frame_method_exists(self):
        calibrator = MonocularCalibrator()
        assert hasattr(calibrator, 'grabPreviewFrame')
        assert callable(getattr(calibrator, 'grabPreviewFrame'))

    def test_grab_preview_frame_method(self):
        calibrator = MonocularCalibrator()
        try:
            calibrator.grabPreviewFrame()
        except Exception as e:
            assert False, f"grabPreviewFrame method raised an exception: {e}"

    def test_calibrate_method_exists(self):
        calibrator = MonocularCalibrator()
        assert hasattr(calibrator, 'calibrate')
        assert callable(getattr(calibrator, 'calibrate'))

    def test_calibrate_method(self):
        calibrator = MonocularCalibrator()
        try:
            calibrator.calibrate()
        except Exception as e:
            assert False, f"calibrate method raised an exception: {e}"

if __name__ == "__main__":
    test_calibrator = TestMonocularCalibrator()
    test_calibrator.test_initialization()
    # test_calibrator.test_grab_preview_frame_method_exists()
    test_calibrator.test_grab_preview_frame_method()
    test_calibrator.test_calibrate_method_exists()
    test_calibrator.test_calibrate_method()
    print("All tests passed.")