import os
import cv2
import numpy as np

class CalibrationHelper:
    @staticmethod
    def buildObjectPoints(CHECKERBOARD, SQUARE_SIZE_MM):
            """3D coordinates of checkerboard corners in the board's own frame,
            Z=0 since the board is planar. Scaled to real-world mm."""
            objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
            objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)
            objp *= SQUARE_SIZE_MM
            return objp
        
    @staticmethod
    def findCorners(image_paths, objp, CHECKERBOARD, SUBPIX_CRITERIA):
            """Detect + subpixel-refine checkerboard corners across a set of images.
            Returns matched object points, image points, and image size."""
            objpoints = []
            imgpoints = []
            img_size = None
            used_files = []
        
            for path in image_paths:
                img = cv2.imread(path)
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                img_size = gray.shape[::-1]  # (width, height)
        
                found, corners = cv2.findChessboardCorners(gray, CHECKERBOARD)
                if not found:
                    print(f"  [skip] no checkerboard found in {os.path.basename(path)}")
                    continue
                
                corners_refined = cv2.cornerSubPix(
                    gray, corners, (11, 11), (-1, -1), SUBPIX_CRITERIA
                )
                objpoints.append(objp)
                imgpoints.append(corners_refined)
                used_files.append(path)
        
            return objpoints, imgpoints, img_size, used_files
    
    @staticmethod
    def calibrateSingle(objpoints, imgpoints, img_size, label, CALIB_CRITERIA):
        rms, K, D, rvecs, tvecs = cv2.calibrateCamera(
            objpoints, imgpoints, img_size, None, None, criteria=CALIB_CRITERIA
        )
        print(f"[{label}] intrinsic calibration RMS reprojection error: {rms:.4f} px")
        print(f"[{label}] camera matrix K:\n{K}")
        print(f"[{label}] distortion coeffs D: {D.ravel()}")
        return K, D, rms, rvecs, tvecs

    @staticmethod
    def deleteLastSaved(dirs, index):
        """Delete the sequence-indexed image file from each dir, if present."""
        name = f"{index:03d}.png"
        deleted_any = False
        for d in dirs:
            path = os.path.join(d, name)
            if os.path.exists(path):
                os.remove(path)
                deleted_any = True
        return deleted_any

    @staticmethod
    def buildUndistortMaps(K, D, img_size):
        new_K, _ = cv2.getOptimalNewCameraMatrix(K, D, img_size, alpha=0)
        return cv2.initUndistortRectifyMap(K, D, None, new_K, img_size, cv2.CV_32FC1)

    @staticmethod
    def buildStereoRectifyMaps(K1, D1, K2, D2, R, T, img_size):
        R1, R2, P1, P2, _, _, _ = cv2.stereoRectify(
            K1, D1, K2, D2, img_size, R, T,
            flags=cv2.CALIB_ZERO_DISPARITY, alpha=0,
        )
        map1x, map1y = cv2.initUndistortRectifyMap(K1, D1, R1, P1, img_size, cv2.CV_32FC1)
        map2x, map2y = cv2.initUndistortRectifyMap(K2, D2, R2, P2, img_size, cv2.CV_32FC1)
        return map1x, map1y, map2x, map2y