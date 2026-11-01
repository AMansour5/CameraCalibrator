import cv2
from src.utils.Configurator import Configurator
from src.services.monocular.MonocularCamera import MonocularCamera

configurator = Configurator()
Monocular_camera_cfg = configurator.fetchData(Configurator.MONOCULAR_CAMERA)
Monocular_camera = MonocularCamera(Monocular_camera_cfg)
preview_width = Monocular_camera_cfg.get("preview_width", 640)

def test_camera_open():
    """Test if the Monocular camera can be opened successfully."""
    configurator = Configurator()
    Monocular_camera_cfg = configurator.fetchData(Configurator.MONOCULAR_CAMERA)
    Monocular_camera = MonocularCamera(Monocular_camera_cfg)
    Monocular_camera.open()
    capture = Monocular_camera.getCapture()
    assert capture is not None and capture.isOpened(), "Failed to open Monocular camera."
    Monocular_camera.release()

def test_frame_capture():
    """Test if a frame can be captured from the Monocular camera."""
    configurator = Configurator()
    Monocular_camera_cfg = configurator.fetchData(Configurator.MONOCULAR_CAMERA)
    Monocular_camera = MonocularCamera(Monocular_camera_cfg)
    Monocular_camera.open()
    frame = Monocular_camera.getFrames()
    assert frame is not None, "Failed to capture frame."
    Monocular_camera.release()

def test_view_feed():
    """Test if the Monocular camera feed can be viewed."""
    configurator = Configurator()
    Monocular_camera_cfg = configurator.fetchData(Configurator.MONOCULAR_CAMERA)
    Monocular_camera = MonocularCamera(Monocular_camera_cfg)
    Monocular_camera.open()
    while True:
        frame = Monocular_camera.getFrames()
        if frame is None:
            print("Failed to capture frame. Exiting.")
            break

        frame_resized = resize_for_preview(frame, preview_width)

        cv2.imshow("Monocular Camera Feed", frame_resized)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
    Monocular_camera.release()

def resize_for_preview(img, target_width):
    h, w = img.shape[:2]
    scale = target_width / w
    return cv2.resize(img, (target_width, int(h * scale)))
