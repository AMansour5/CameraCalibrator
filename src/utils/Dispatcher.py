from src.utils.Configurator import Configurator
from src.services.stereo.StereoCalibrator import StereoCalibrator
from src.services.monocular.MonocularCalibrator import MonocularCalibrator

class Dispatcher:

    @staticmethod
    def getCalibrator():
        configurator = Configurator()
        calibrator_cfg = configurator.fetchData(Configurator().CALIBRATOR)
        chosen_calibrator = calibrator_cfg.get("chosen_calibrator", None)
        if chosen_calibrator == "stereo":
            return StereoCalibrator()
        elif chosen_calibrator == "monocular":
            return MonocularCalibrator()
        else:
            raise ValueError(f"Unknown calibrator type: {chosen_calibrator}")