import cv2
from src.utils.Configurator import Configurator
from src.services.monocular.MonocularCamera import MonocularCamera

class MonocularCameraTest:
    def __init__(self):
        self.configurator = Configurator()
        self.Monocular_camera_cfg = self.configurator.fetchData(self.configurator.MONOCULAR_CAMERA)
        self.Monocular_camera = MonocularCamera(self.Monocular_camera_cfg)
        self.preview_width = self.Monocular_camera_cfg.get("preview_width", 640)
        self.capture = None

    def test_camera_open(self):
        """Test if the Monocular camera can be opened successfully."""
        self.Monocular_camera.open()
        self.capture = self.Monocular_camera.getCapture()
        assert self.capture is not None and self.capture.isOpened(), "Failed to open Monocular camera."

    def test_frame_capture(self):
        """Test if a frame can be captured from the Monocular camera."""
        frame = self.Monocular_camera.getFrames()
        assert frame is not None, "Failed to capture frame."

    def test_view_feed(self):
        """Test if the Monocular camera feed can be viewed."""
        while True:
            frame = self.Monocular_camera.getFrames()
            if frame is None:
                print("Failed to capture frame. Exiting.")
                break

            frame_resized = self.resize_for_preview(frame, self.preview_width)

            cv2.imshow("Monocular Camera Feed", frame_resized)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cv2.destroyAllWindows()
        self.Monocular_camera.release()

    def resize_for_preview(self, img, target_width):
        h, w = img.shape[:2]
        scale = target_width / w
        return cv2.resize(img, (target_width, int(h * scale)))

if __name__ == "__main__":
    test = MonocularCameraTest()
    test.test_camera_open()
    test.test_frame_capture()
    test.test_view_feed()