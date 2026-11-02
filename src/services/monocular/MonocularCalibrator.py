import os
import cv2
import glob 
import numpy as np
from zope.interface import implementer
from src.utils.Configurator import Configurator
from src.interfaces.ICalibrator import ICalibrator
from src.helpers.CalibrationHelper import CalibrationHelper
from src.exceptions.CameraSetupError import CameraSetupError
from src.services.monocular.MonocularCamera import MonocularCamera
from src.exceptions.CameraCalibrationError import CameraCalibrationError
from src.exceptions.DifferentImageSizeError import DifferentImageSizeError

@implementer(ICalibrator)
class MonocularCalibrator:
    def __init__(self, min_images=10, max_rms=1.0):
        self.configurator = Configurator()
        self.camera_cfg = self.configurator.fetchData(Configurator.MONOCULAR_CAMERA)
        self.camera = MonocularCamera(self.camera_cfg)
        self.checkerboard_cfg = self.configurator.fetchData(Configurator.CHECKERBOARD)
        self.CHECKERBOARD = (self.checkerboard_cfg["columns"], self.checkerboard_cfg["rows"])
        self.SQUARE_SIZE_MM = self.checkerboard_cfg.get("square_size_mm", 30)
        self.CORNER_FLAGS = (
            cv2.CALIB_CB_ADAPTIVE_THRESH
            + cv2.CALIB_CB_NORMALIZE_IMAGE
            + cv2.CALIB_CB_FAST_CHECK
        )
        self.SUBPIX_CRITERIA = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-5)
        self.CALIB_CRITERIA = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, 1e-6)
        self.__setupSaveDirectories()
        self.OUTPUT_FILE = os.path.join(self.MATRICES_DIR, "monocular_calib.npz")
        self.saved_count = len([f for f in os.listdir(self.IMAGES_DIR) if f.endswith(".png")])
        self.image_index = CalibrationHelper.getStartIndex([self.IMAGES_DIR])
        self.min_images = min_images
        self.max_rms = max_rms
        self._dirty = False
        self._undistort_maps = None
        self._maps_source = None
        print(f"Saved images: {self.saved_count}. Starting from image index {self.image_index}. s:save c:calibrate a:accept x:delete last q:quit p:preview calibration")
        self.__setupCamera()
    
    def __setupSaveDirectories(self):
        project_root = Configurator.getProjectRoot()
        self.IMAGES_DIR = os.path.join(project_root, "src", "images", "monocular")
        self.MATRICES_DIR = os.path.join(project_root, "src", "matrices", "monocular")
        self.TIMESTAMPED_DIR = os.path.join(self.MATRICES_DIR, "time_stamped")
        os.makedirs(self.IMAGES_DIR, exist_ok=True)
        os.makedirs(self.MATRICES_DIR, exist_ok=True)
        os.makedirs(self.TIMESTAMPED_DIR, exist_ok=True)

    def acceptLatest(self):
        """Promote the latest time-stamped calibration to the final file."""
        latest = CalibrationHelper.latestTimestamped(self.TIMESTAMPED_DIR)
        if latest is None:
            print("No time-stamped calibration to accept. Press 'c' to calibrate first.")
            return False
        CalibrationHelper.acceptCalibration(latest, self.OUTPUT_FILE)
        print(f"Accepted {os.path.basename(latest)} -> {self.OUTPUT_FILE}")
        return True

    def __setupCamera(self):
        try:
            self.camera.open()
            frame = self.camera.getFrames()
            if frame is None:
                raise RuntimeError("Failed to capture initial frame from the monocular camera.")
        except Exception as e:
            raise CameraSetupError(f"Failed to open monocular camera: {e}")

    def grabPreviewFrame(self):
        """Grab + annotate one frame; returns (display_frame, found, raw_frame)."""
        try:
            frame = self.camera.getFrames()
            if frame is None:
                print("Failed to capture frame.")
                return None, False, None

            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            found, corners = cv2.findChessboardCorners(gray_frame, self.CHECKERBOARD, flags=self.CORNER_FLAGS)
            disp = frame.copy()
            if found:
                cv2.drawChessboardCorners(disp, self.CHECKERBOARD, corners, found)
            disp = self.camera.resize_for_preview(disp)
            status_color = (0, 255, 0) if found else (0, 0, 255)
            status_text = "READY" if found else "board not found"
            cv2.putText(
                disp, f"{status_text} | saved:{self.saved_count} | s:save c:calibrate a:accept x:delete q:quit",
                (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2,
            )
            return disp, found, frame
        except Exception as e:
            print(f"Error during frame capture: {e}")
            return None, False, None

    def saveImage(self, raw_frame):
        """Persist the given frame as the next calibration image."""
        name = f"{self.image_index:03d}.png"
        cv2.imwrite(os.path.join(self.IMAGES_DIR, name), raw_frame)
        print(f"Saved image {name}")
        self.saved_count += 1
        self.image_index += 1
        self._dirty = True

    def deleteLastImage(self):
        if self.saved_count == 0:
            print("No images to delete.")
            return
        self.saved_count -= 1
        self.image_index -= 1
        if CalibrationHelper.deleteLastSaved([self.IMAGES_DIR], self.image_index):
            self._dirty = True
            print(f"Deleted image {self.image_index:03d}.png")
        else:
            print("No image file found to delete.")

    def isDirty(self):
        return self._dirty

    def getWindowName(self):
        return "Monocular capture"

    def release(self):
        if self.camera is not None:
            self.camera.release()

    def previewFrame(self):
        """Grab one frame and apply the saved undistortion; returns a display frame or None."""
        latest = CalibrationHelper.latestTimestamped(self.TIMESTAMPED_DIR)
        if latest is None:
            print("No calibration data found yet. Press 'c' to calibrate first.")
            return None
        try:
            frame = self.camera.getFrames()
            if frame is None:
                print("Failed to capture frame.")
                return None

            if self._undistort_maps is None or self._maps_source != latest:
                data = np.load(latest)
                img_size = (frame.shape[1], frame.shape[0])
                if not CalibrationHelper.checkImageSize(img_size, data):
                    raise DifferentImageSizeError(
                        f"Captured image size {img_size} does not match calibration size {int(data['img_size'][0]), int(data['img_size'][1])}"
                    )
                self._undistort_maps = CalibrationHelper.buildUndistortMaps(data["K"], data["D"], img_size)
                self._maps_source = latest

            map1, map2 = self._undistort_maps
            undistorted = cv2.remap(frame, map1, map2, cv2.INTER_LINEAR)
            disp = self.camera.resize_for_preview(undistorted)
            cv2.putText(
                disp, "LATEST CALIBRATION PREVIEW | a:accept r:return q:quit",
                (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2,
            )
            return disp
        except Exception as e:
            print(f"Error during preview: {e}")
            return None

    def calibrate(self):
        """Perform the calibration process using the captured images."""
        try:
            objp = CalibrationHelper.buildObjectPoints(self.CHECKERBOARD, self.SQUARE_SIZE_MM)
            image_paths = sorted(glob.glob(os.path.join(self.IMAGES_DIR, "*.png")))
            if len(image_paths) == 0:
                raise RuntimeError("No images found for calibration. Capture images first.")
            elif len(image_paths) < self.min_images:
                raise RuntimeError(
                    f"Not enough images for calibration. Found {len(image_paths)}, but minimum required is {self.min_images}."
                )

            print("Detecting corners in captured images...")
            objpoints, imgpoints, img_size, used_files = CalibrationHelper.findCorners(
                image_paths, objp, self.CHECKERBOARD, self.SUBPIX_CRITERIA
            )
            print(f"Usable images: {len(used_files)}/{len(image_paths)}\n")
            if len(objpoints) < 5:
                raise RuntimeError(
                    f"Not enough usable images for calibration. Found {len(objpoints)}. "
                    "Aim for 15-20+ for a stable calibration."
                )

            # Calibrate the monocular camera
            K, D, rms, rvecs, tvecs = CalibrationHelper.calibrateSingle(
                objpoints, imgpoints, img_size, "Monocular Camera", self.CALIB_CRITERIA
            )

            # Print calibration results
            self.__printCalibrationResults(K, D, rms)

            # Save the calibration matrices
            saved_path = CalibrationHelper.saveTimestamped(
                self.TIMESTAMPED_DIR, "monocular_calib",
                K=K, D=D, rvecs=rvecs, tvecs=tvecs, img_size=img_size, rms=rms, checkerboard=self.CHECKERBOARD, square_size_mm=self.SQUARE_SIZE_MM
            )
            print(f"Calibration matrices saved to {saved_path}. Press 'a' to accept as the final calibration.")
            self._dirty = False
            self._undistort_maps = None
        except Exception as e:
            raise CameraCalibrationError(f"Error during calibration: {e}")

    def __printCalibrationResults(self, K, D, rms):
        print("=== Monocular calibration result ===")
        print(f"RMS reprojection error: {rms:.4f} px")
        print(f"Camera matrix K:\n{K}")
        print(f"Distortion coeffs D: {D.ravel()}")

        if rms > self.max_rms:
            print(
                f"\nNOTE: RMS > {self.max_rms:.1f} px is high. Common causes: not enough "
                "coverage of frame edges, checkerboard not rigid/flat, motion blur "
                "during capture, or SQUARE_SIZE_MM not matching your real board. "
                "Consider recapturing before moving on to rectification."
            )