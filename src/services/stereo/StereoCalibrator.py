import os
import cv2
import glob 
import numpy as np
from zope.interface import implementer
from src.utils.Configurator import Configurator
from src.interfaces.ICalibrator import ICalibrator
from src.services.stereo.StereoCamera import StereoCamera
from src.helpers.CalibrationHelper import CalibrationHelper

@implementer(ICalibrator)
class StereoCalibrator:

    def __init__(self):
        self.configurator = Configurator()
        self.project_root = Configurator.getProjectRoot()
        self.camera_cfg = self.configurator.fetchData(Configurator.STEREO_CAMERA)
        self.camera = StereoCamera(self.camera_cfg)
        self.checkerboard_cfg = self.configurator.fetchData(Configurator.CHECKERBOARD)
        self.CHECKERBOARD = (self.checkerboard_cfg["columns"], self.checkerboard_cfg["rows"])
        self.SQUARE_SIZE_MM = self.checkerboard_cfg.get("square_size_mm", 30)
        self.CORNER_FLAGS = (
            cv2.CALIB_CB_ADAPTIVE_THRESH
            + cv2.CALIB_CB_NORMALIZE_IMAGE
            + cv2.CALIB_CB_FAST_CHECK
        )
        self.STEREO_FLAGS = cv2.CALIB_FIX_INTRINSIC
        self.SUBPIX_CRITERIA = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-5)
        self.CALIB_CRITERIA = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, 1e-6)
        self.__setupSaveDirectories()
        self.OUTPUT_FILE = os.path.join(self.MATRICES_DIR, "stereo_calib.npz")
        self.saved_count = len([f for f in os.listdir(self.IMAGES_LEFT_DIR) if f.endswith(".png")])
        self._dirty = False
        self._rectify_maps = None
        print(f"Starting from pair index {self.saved_count}. s:save c:calibrate x:delete last q:quit p:preview calibration")
        self.__setupCamera()
    
    def __setupSaveDirectories(self):
        self.IMAGES_LEFT_DIR = os.path.join(self.project_root, "src", "images", "stereo", "left")
        self.IMAGES_RIGHT_DIR = os.path.join(self.project_root, "src", "images", "stereo", "right")
        self.MATRICES_DIR = os.path.join(self.project_root, "src", "matrices", "stereo")
        os.makedirs(self.IMAGES_LEFT_DIR, exist_ok=True)
        os.makedirs(self.IMAGES_RIGHT_DIR, exist_ok=True)
        os.makedirs(self.MATRICES_DIR, exist_ok=True)

    def __setupCamera(self):
        try:
            self.camera.open()
            left_frame, right_frame = self.camera.getFrames()
            if left_frame is None or right_frame is None:
                raise RuntimeError("Failed to capture initial frames from the stereo camera.")
        except Exception as e:
            print(f"Error opening camera: {e}")
            self.camera = None

    def grabPreviewFrame(self):
        """Grab + annotate one pair; returns (display_frame, found, raw_pair)."""
        try:
            left_frame, right_frame = self.camera.getFrames()
            if left_frame is None or right_frame is None:
                print("Failed to capture frames.")
                return None, False, None

            gray_left = cv2.cvtColor(left_frame, cv2.COLOR_BGR2GRAY)
            gray_right = cv2.cvtColor(right_frame, cv2.COLOR_BGR2GRAY)
            found_left, corners_left = cv2.findChessboardCorners(gray_left, self.CHECKERBOARD, flags=self.CORNER_FLAGS)
            found_right, corners_right = cv2.findChessboardCorners(gray_right, self.CHECKERBOARD, flags=self.CORNER_FLAGS)
            disp_l = left_frame.copy()
            disp_r = right_frame.copy()
            if found_left:
                cv2.drawChessboardCorners(disp_l, self.CHECKERBOARD, corners_left, found_left)
            if found_right:
                cv2.drawChessboardCorners(disp_r, self.CHECKERBOARD, corners_right, found_right)
            disp_l = self.camera.resize_for_preview(disp_l)
            disp_r = self.camera.resize_for_preview(disp_r)
            both_found = found_left and found_right
            status_color = (0, 255, 0) if both_found else (0, 0, 255)
            status_text = "READY" if both_found else "board not found in both halves"
            combined_preview = cv2.hconcat([disp_l, disp_r])
            cv2.putText(
                combined_preview, f"{status_text} | saved:{self.saved_count} | s:save c:calibrate x:delete q:quit",
                (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2,
            )
            return combined_preview, both_found, (left_frame, right_frame)
        except Exception as e:
            print(f"Error during frame capture: {e}")
            return None, False, None

    def saveImage(self, raw_data):
        """Persist the given left/right pair as the next calibration images."""
        left_frame, right_frame = raw_data
        name = f"{self.saved_count:03d}.png"
        cv2.imwrite(os.path.join(self.IMAGES_LEFT_DIR, name), left_frame)
        cv2.imwrite(os.path.join(self.IMAGES_RIGHT_DIR, name), right_frame)
        print(f"Saved pair {name}")
        self.saved_count += 1
        self._dirty = True

    def deleteLastImage(self):
        if self.saved_count == 0:
            print("No images to delete.")
            return
        self.saved_count -= 1
        if CalibrationHelper.deleteLastSaved([self.IMAGES_LEFT_DIR, self.IMAGES_RIGHT_DIR], self.saved_count):
            print(f"Deleted pair {self.saved_count:03d}.png")
        else:
            print("No image files found to delete.")

    def isDirty(self):
        return self._dirty

    def getWindowName(self):
        return "Stereo capture (left | right)"

    def release(self):
        self.camera.release()

    def previewFrame(self):
        """Grab one pair and apply the saved rectification; returns a display frame or None."""
        if not os.path.exists(self.OUTPUT_FILE):
            print("No calibration data found yet. Press 'c' to calibrate first.")
            return None
        try:
            left_frame, right_frame = self.camera.getFrames()
            if left_frame is None or right_frame is None:
                print("Failed to capture frames.")
                return None

            if self._rectify_maps is None:
                data = np.load(self.OUTPUT_FILE)
                img_size = (left_frame.shape[1], left_frame.shape[0])
                self._rectify_maps = CalibrationHelper.buildStereoRectifyMaps(
                    data["K1"], data["D1"], data["K2"], data["D2"], data["R"], data["T"], img_size
                )

            map1x, map1y, map2x, map2y = self._rectify_maps
            rect_left = cv2.remap(left_frame, map1x, map1y, cv2.INTER_LINEAR)
            rect_right = cv2.remap(right_frame, map2x, map2y, cv2.INTER_LINEAR)
            disp_l = self.camera.resize_for_preview(rect_left)
            disp_r = self.camera.resize_for_preview(rect_right)
            combined = cv2.hconcat([disp_l, disp_r])
            cv2.putText(
                combined, "CALIBRATED PREVIEW | r:return q:quit",
                (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2,
            )
            return combined
        except Exception as e:
            print(f"Error during preview: {e}")
            return None

    def calibrate(self):
        """Perform the calibration process using the captured images."""
        # Implement the calibration logic here
        try:
            objp = CalibrationHelper.buildObjectPoints(self.CHECKERBOARD, self.SQUARE_SIZE_MM)
            left_paths = sorted(glob.glob(os.path.join(self.IMAGES_LEFT_DIR, "*.png")))
            right_paths = sorted(glob.glob(os.path.join(self.IMAGES_RIGHT_DIR, "*.png")))
            if len(left_paths) != len(right_paths) or len(left_paths) == 0:
                raise RuntimeError(
                    f"Mismatched or empty capture sets: {len(left_paths)} left, "
                    f"{len(right_paths)} right. Filenames must correspond 1:1."
                )
            print(f"Found {len(left_paths)} candidate pairs.\n")
            print("Detecting corners - LEFT camera")
            objpoints_left, imgpoints_left, img_size_left, used_left = CalibrationHelper.findCorners(
                left_paths, objp, self.CHECKERBOARD, self.SUBPIX_CRITERIA
            )
            print(f"Usable left images: {len(used_left)}/{len(left_paths)}\n")
            print("Detecting corners - RIGHT camera")
            objpoints_right, imgpoints_right, img_size_right, used_right = CalibrationHelper.findCorners(
                right_paths, objp, self.CHECKERBOARD, self.SUBPIX_CRITERIA
            )
            print(f"Usable right images: {len(used_right)}/{len(right_paths)}\n")
            if img_size_left != img_size_right:
                raise RuntimeError(
                    f"Image size mismatch: left {img_size_left}, right {img_size_right}"
                )
            # Keep only pairs where BOTH left and right detected the board
            used_left_set = set(os.path.basename(p) for p in used_left)
            used_right_set = set(os.path.basename(p) for p in used_right)
            common = used_left_set & used_right_set
            if len(common) < 10:
                print(
                    f"WARNING: only {len(common)} pairs have corners in both views. "
                    "Aim for 15-20+ for a stable stereo calibration."
                )
            # Filter the object points and image points to keep only common pairs
            objpoints_left, imgpoints_left = self.__filterByCommon(used_left, objpoints_left, imgpoints_left, common)
            objpoints_right, imgpoints_right = self.__filterByCommon(used_right, objpoints_right, imgpoints_right, common)

            # Calibrate each camera individually
            K1, D1, rms_left, _, _ = CalibrationHelper.calibrateSingle(
                objpoints_left, imgpoints_left, img_size_left, "LEFT", self.CALIB_CRITERIA)
            K2, D2, rms_right, _, _ = CalibrationHelper.calibrateSingle(
                objpoints_right, imgpoints_right, img_size_right, "RIGHT", self.CALIB_CRITERIA)

            # Perform stereo calibration
            K1, D1, K2, D2, R, T, rms_stereo = self.__stereoCalibrate(
                objpoints_left, imgpoints_left, imgpoints_right, K1, D1, K2, D2, img_size_left
            )

            # print calibration results
            self.__printCalibrationResults(K1, D1, K2, D2, R, T, rms_left, rms_right, rms_stereo)

            # Save calibration results to file
            np.savez(self.OUTPUT_FILE, K1=K1, D1=D1, K2=K2, D2=D2, R=R, T=T, img_size=img_size_left, rms_stereo=rms_stereo)
            print(f"Calibration results saved to {self.OUTPUT_FILE}")
            self._dirty = False
            self._rectify_maps = None
            
        except Exception as e:
            print(f"Error during calibration: {e}")

    def __stereoCalibrate(self, objpoints, imgpoints_left, imgpoints_right, K1, D1, K2, D2, img_size):
        rms_stereo, K1, D1, K2, D2, R, T, E, F = cv2.stereoCalibrate(
            objpoints, imgpoints_left, imgpoints_right,
            K1, D1, K2, D2, img_size,
            criteria=self.CALIB_CRITERIA,
            flags=self.STEREO_FLAGS,
        )
        print(f"[stereo] stereo calibration RMS reprojection error: {rms_stereo:.4f} px")
        return K1, D1, K2, D2, R, T, rms_stereo

    def __filterByCommon(self, paths, objpoints, imgpoints, common):
        obj_out, img_out = [], []
        for p, o, i in zip(paths, objpoints, imgpoints):
            if os.path.basename(p) in common:
                obj_out.append(o)
                img_out.append(i)
        return obj_out, img_out

    def __printCalibrationResults(self, K1, D1, K2, D2, R, T, rms_left, rms_right, rms_stereo):
        baseline_mm = np.linalg.norm(T)
        print("=== Stereo calibration result ===")
        print(f"Stereo RMS reprojection error: {rms_stereo:.4f} px")
        print(f"Baseline (distance between cameras): {baseline_mm:.2f} mm")
        print(f"Rotation between cameras (R):\n{R}")
        print(f"Translation between cameras (T, mm):\n{T.ravel()}")
        print(f"Left camera RMS reprojection error: {rms_left:.4f} px")
        print(f"Right camera RMS reprojection error: {rms_right:.4f} px")

        if rms_stereo > 1.0:
            print(
                "\nNOTE: stereo RMS > 1.0 px is high. Common causes: not enough "
                "coverage of frame edges, checkerboard not rigid/flat, motion blur "
                "during capture, or SQUARE_SIZE_MM not matching your real board. "
                "Consider recapturing before moving on to rectification."
            )