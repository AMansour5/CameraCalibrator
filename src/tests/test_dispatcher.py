from src.utils.Dispatcher import Dispatcher

def test_get_calibrator():
    calibrator = Dispatcher.getCalibrator()
    print(f"Calibrator: {calibrator}")
    assert calibrator is not None
