class FewImagesError(Exception):
    """Raised when there are not enough images for calibration."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)