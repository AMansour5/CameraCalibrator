"""Hardware-free tests for time-stamped calibration saves and accept.

Run from the repository root: python -m pytest -q src/tests/test_timestamped_calibration.py
"""
import numpy as np
from src.helpers.CalibrationHelper import CalibrationHelper
from src.services.monocular.MonocularCalibrator import MonocularCalibrator
from src.services.monocular.MonocularCamera import MonocularCamera
from src.utils.Configurator import Configurator


def test_save_timestamped_never_overwrites_and_latest_is_newest(tmp_path):
    first = CalibrationHelper.saveTimestamped(str(tmp_path), "m", K=np.eye(3))
    second = CalibrationHelper.saveTimestamped(str(tmp_path), "m", K=np.eye(3) * 2)
    assert first != second
    assert CalibrationHelper.latestTimestamped(str(tmp_path)) == second
    assert np.load(second)["K"][0, 0] == 2


def test_latest_timestamped_empty_or_missing(tmp_path):
    assert CalibrationHelper.latestTimestamped(str(tmp_path)) is None
    assert CalibrationHelper.latestTimestamped(str(tmp_path / "nope")) is None


def test_accept_calibration_replaces_destination(tmp_path):
    src = CalibrationHelper.saveTimestamped(str(tmp_path), "m", K=np.eye(3) * 5)
    dst = str(tmp_path / "final.npz")
    CalibrationHelper.acceptCalibration(src, dst)
    assert np.load(dst)["K"][0, 0] == 5
    assert not (tmp_path / "final.npz.tmp").exists()


def _make_calibrator(tmp_path, monkeypatch):
    monkeypatch.setattr(MonocularCamera, "open", lambda self: None)
    monkeypatch.setattr(MonocularCamera, "getFrames", lambda self: np.zeros((20, 20, 3), np.uint8))
    monkeypatch.setattr(Configurator, "getProjectRoot", lambda: str(tmp_path))
    monkeypatch.setattr(
        Configurator, "fetchData",
        lambda self, name: {"columns": 8, "rows": 5} if name == Configurator.CHECKERBOARD else {},
    )
    return MonocularCalibrator()


def test_accept_latest_and_preview_use_timestamped(tmp_path, monkeypatch):
    cal = _make_calibrator(tmp_path, monkeypatch)
    assert cal.acceptLatest() is False
    assert cal.previewFrame() is None
    assert not (tmp_path / "src" / "matrices" / "monocular" / "monocular_calib.npz").exists()

    K = np.array([[10.0, 0, 10], [0, 10, 10], [0, 0, 1]])
    older = CalibrationHelper.saveTimestamped(cal.TIMESTAMPED_DIR, "monocular_calib", K=K, D=np.zeros(5))
    newer = CalibrationHelper.saveTimestamped(cal.TIMESTAMPED_DIR, "monocular_calib", K=K * 1.0, D=np.zeros(5))

    assert cal.previewFrame() is not None
    assert cal._maps_source == newer
    assert not (tmp_path / "src" / "matrices" / "monocular" / "monocular_calib.npz").exists()

    assert cal.acceptLatest() is True
    assert np.array_equal(np.load(cal.OUTPUT_FILE)["K"], np.load(newer)["K"])
    assert older != newer
