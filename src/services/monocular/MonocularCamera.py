import cv2
from zope.interface import implementer
from src.interfaces.ICamera import ICamera

@implementer(ICamera)
class MonocularCamera:
    def __init__(self, camera_cfg: dict):
        self.camera_index = camera_cfg.get("camera_index", 0)
        self.width = camera_cfg.get("width", 1280)
        self.height = camera_cfg.get("height", 720)
        self.preview_width = camera_cfg.get("preview_width", 640)
        self.__capture = None

    def open(self):
        try:
            self.__capture = cv2.VideoCapture(self.camera_index)
            if not self.__capture.isOpened():
                raise RuntimeError(f"Could not open camera index {self.camera_index}")
            self.__setupCamera()
        except Exception as e:
            print(f"Error opening camera: {e}")
            self.__capture = None

    def __setupCamera(self):
        try:
            if self.__capture is not None:
                self.__capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.__capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self.__capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
                self.__capture.set(cv2.CAP_PROP_FPS, 30)

                actual_w = int(self.__capture.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_h = int(self.__capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
                print(f"Requested {self.width}x{self.height}, camera reports {actual_w}x{actual_h}")
                if actual_w != self.width or actual_h != self.height:
                    print("WARNING: camera did not accept the requested resolution. "
                          "Update width/height to match what it reports.")
        except Exception as e:
            print(f"Error setting up camera: {e}")

    def getFrames(self):
        """Capture a frame from the monocular camera."""
        if self.__capture is not None:
            ret, frame = self.__capture.read()
            if not ret:
                print("Failed to grab frame")
                return None
            return frame
        else:
            print("Camera is not opened.")
            return None

    def getCapture(self):
        return self.__capture
    
    def release(self):
        if self.__capture is not None:
            self.__capture.release()
            self.__capture = None

    def resize_for_preview(self, img):
        h, w = img.shape[:2]
        scale = self.preview_width / w
        return cv2.resize(img, (self.preview_width, int(h * scale)))