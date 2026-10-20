from zope.interface import Interface

class ICalibrator(Interface):
    def grabPreviewFrame():
        """Grab frame(s), detect the calibration pattern, and return (display_frame, found, raw_data); display_frame is None on camera failure."""

    def saveImage(raw_data):
        """Persist the raw frame(s) returned by the last grabPreviewFrame() as the next calibration image(s)."""

    def deleteLastImage():
        """Remove the most recently saved calibration image(s)."""

    def isDirty():
        """Return True if images were saved since the last calibrate() call."""

    def getWindowName():
        """Return the preview window title for this calibrator."""

    def release():
        """Release camera resources."""

    def previewFrame():
        """Grab frame(s), apply the saved calibration, and return a display frame (or None if unavailable)."""

    def calibrate():
        """Perform the calibration process using the captured images. This method should compute the camera parameters and return them."""