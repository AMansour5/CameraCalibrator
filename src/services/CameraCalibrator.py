import cv2
from src.utils.Dispatcher import Dispatcher
"""
An orchestral class that manages calibration of cameras 
- as input it requires the type of the camera(monocular or stereo)
- then it loads the required camera object, loads the correct cfg and initializes the camera 
-- opens the camera, gets the frames and applies find corners to them to allow selecting saving the correct frames, when we press a button it calibrates, prints the results and errors then saves the calibration data, it doesn't shut the program as it allows to continue capturing images and calibrating them and printing
"""
class CameraCalibrator:

    @staticmethod
    def calibrate():
        calibrator = Dispatcher.getCalibrator()
        window_name = calibrator.getWindowName()
        preview_mode = False
        try:
            while True:
                if preview_mode:
                    display = calibrator.previewFrame()
                    if display is None:
                        preview_mode = False
                        continue
                    found, raw_data = False, None
                else:
                    display, found, raw_data = calibrator.grabPreviewFrame()
                    if display is None:
                        break
                cv2.imshow(window_name, display)

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    if calibrator.isDirty():
                        calibrator.calibrate()
                    break
                elif key == ord("p"):
                    preview_mode = True
                elif key == ord("r"):
                    preview_mode = False
                elif not preview_mode and key == ord("s") and found:
                    calibrator.saveImage(raw_data)
                elif not preview_mode and key == ord("c"):
                    calibrator.calibrate()
                elif not preview_mode and key == ord("x"):
                    calibrator.deleteLastImage()
        finally:
            cv2.destroyAllWindows()
            calibrator.release()

if __name__ == "__main__":
    try:
        CameraCalibrator().calibrate()
    except Exception as e:
        print(f"An error occurred: {e}")