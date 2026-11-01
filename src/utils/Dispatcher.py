from src.utils.Configurator import Configurator
from src.services.stereo.StereoCalibrator import StereoCalibrator
from src.services.monocular.MonocularCalibrator import MonocularCalibrator

class Dispatcher:

    @staticmethod
    def getCalibrator():
        configurator = Configurator()
        calibrator_cfg = configurator.fetchData(configurator.CALIBRATOR)
        chosen_calibrator = calibrator_cfg.get("chosen_calibrator", None)
        if chosen_calibrator == "stereo":
            return StereoCalibrator(min_images=calibrator_cfg.get("min_images", 10), max_rms=calibrator_cfg.get("max_rms", 1.0))
        elif chosen_calibrator == "monocular":
            return MonocularCalibrator(min_images=calibrator_cfg.get("min_images", 10), max_rms=calibrator_cfg.get("max_rms", 1.0))
        else:
            raise ValueError(f"Unknown calibrator type: {chosen_calibrator}")