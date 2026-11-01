class CameraSetupError(Exception):
    """Raised for errors in the camera setup process."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)