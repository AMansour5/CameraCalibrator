from src.interfaces.ICamera import ICamera
from zope.interface.verify import verifyClass
from src.interfaces.ICalibrator import ICalibrator
from src.services.stereo.StereoCamera import StereoCamera
from src.services.stereo.StereoCalibrator import StereoCalibrator
from src.services.monocular.MonocularCamera import MonocularCamera
from src.services.monocular.MonocularCalibrator import MonocularCalibrator

def test_stereo_calibrator():
    verifyClass(ICalibrator, StereoCalibrator)

def test_monocular_calibrator():
    verifyClass(ICalibrator, MonocularCalibrator)

def test_monocular_camera():
    verifyClass(ICamera, MonocularCamera)

def test_stereo_camera():
    verifyClass(ICamera, StereoCamera)
