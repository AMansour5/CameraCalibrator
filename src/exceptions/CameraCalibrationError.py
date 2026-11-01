class CameraCalibrationError(Exception):
    """Raised for errors in the camera calibration process."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)