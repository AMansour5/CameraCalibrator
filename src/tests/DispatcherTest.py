from src.utils.Dispatcher import Dispatcher

class DispatcherTest:
    def test_get_calibrator(self):
        calibrator = Dispatcher.getCalibrator()
        print(f"Calibrator: {calibrator}")
        assert calibrator is not None

if __name__ == "__main__":
    test = DispatcherTest()
    test.test_get_calibrator()