import cv2
import sys
import threading
import traceback
from src.utils.Dispatcher import Dispatcher
"""
An orchestral class that manages calibration of cameras 
- as input it requires the type of the camera(monocular or stereo)
- then it loads the required camera object, loads the correct cfg and initializes the camera 
-- opens the camera, gets the frames and applies find corners to them to allow selecting saving the correct frames, when we press a button it calibrates, prints the results and errors then saves the calibration data, it doesn't shut the program as it allows to continue capturing images and calibrating them and printing
"""
class CameraCalibrator:

    @staticmethod
    def drawCalibrationBanner(frame, text="CALIBRATING... please wait"):
        out = frame.copy()
        h, w = out.shape[:2]
        cv2.rectangle(out, (0, 0), (w - 1, h - 1), (0, 0, 255), 6)
        cv2.rectangle(out, (0, 0), (w - 1, 40), (0, 0, 255), -1)
        cv2.putText(out, text, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        return out

    @staticmethod
    def _runCalibration(calibrator):
        try:
            calibrator.calibrate()
        except Exception as e:
            print(f"Calibration failed: {e}")
            traceback.print_exc()
        finally:
            print("Calibration finished.")

    @staticmethod
    def calibrate():
        calibrator = Dispatcher.getCalibrator()
        window_name = calibrator.getWindowName()
        preview_mode = False
        worker = None
        quit_pending = False

        def startCalibration():
            nonlocal worker
            worker = threading.Thread(target=CameraCalibrator._runCalibration, args=(calibrator,), daemon=True)
            worker.start()

        try:
            while True:
                if worker is not None and not worker.is_alive():
                    worker = None
                    if quit_pending:
                        break
                calibrating = worker is not None
                if calibrating:
                    preview_mode = False
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
                if calibrating:
                    text = "CALIBRATING... will quit when done" if quit_pending else "CALIBRATING... please wait"
                    display = CameraCalibrator.drawCalibrationBanner(display, text)
                cv2.imshow(window_name, display)

                key = cv2.waitKey(1) & 0xFF
                if calibrating:
                    if key == ord("q"):
                        quit_pending = True
                    continue
                if key == ord("q"):
                    if calibrator.isDirty():
                        quit_pending = True
                        startCalibration()
                        continue
                    break
                elif key == ord("p"):
                    preview_mode = True
                elif key == ord("r"):
                    preview_mode = False
                elif not preview_mode and key == ord("s") and found:
                    calibrator.saveImage(raw_data)
                elif key == ord("a"):
                    calibrator.acceptLatest()
                elif not preview_mode and key == ord("c"):
                    startCalibration()
                elif not preview_mode and key == ord("x"):
                    calibrator.deleteLastImage()
        finally:
            if worker is not None:
                worker.join()
            cv2.destroyAllWindows()
            calibrator.release()

if __name__ == "__main__":
    try:
        CameraCalibrator.calibrate()
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
        sys.exit(1)