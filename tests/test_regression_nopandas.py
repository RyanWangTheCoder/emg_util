"""
Regression Tests for the pandas-free EMG Analysis Pipeline (emg_util_nopandas.py)

Tests cover:
  1. Swing detection from IMU arrays (existing)
  2. load_decoded_emg_csv / load_decoded_imu_csv — host_rx_ms priority over dev_us
  3. stitch_decoded_session_from_paths — multi-capture stitching with BLE reconnect gaps
     and ESP32 resets (physical timeline construction)
  4. stitch_decoded_session — thin wrapper around stitch_decoded_session_from_paths
  5. Per-swing EMG features (compute_swing_emg_features)
  6. Baseline selection and fatigue deltas

Run with:
    pytest tests/test_regression_nopandas.py -v
    pytest tests/test_regression_nopandas.py -v -m nopandas
    pytest tests/test_regression_nopandas.py -v -k "host_rx_ms or stitch"
"""

import csv
import io
import json
import sys
import tempfile
from pathlib import Path
from typing import Dict, List

import numpy as np
import pytest

# Add parent directory to path to import emg_util_nopandas
sys.path.insert(0, str(Path(__file__).parent.parent))
# Also add the btLeApp python source dir to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "btLeApp" / "app" / "src" / "main" / "python"))

import emg_util_nopandas as nopandas

try:
    import btcentral_offline_decode as offline_decoder
    _HAVE_DECODER = True
except ImportError:
    _HAVE_DECODER = False

# Test data location (reuse from the main regression tests)
REGRESSION_DATA_DIR = Path(__file__).parent.parent / "regression_testlogs"

# ---------------------------------------------------------------------------
# Helpers: synthetic CSV writers
# ---------------------------------------------------------------------------

def _write_emg_csv(path: Path, rows: List[Dict], has_host_rx_ms: bool = True) -> None:
    """Write a minimal decoded emg_log_*.csv for testing."""
    fieldnames = ["dev_us", "emg_seq", "env", "raw", "ref", "frame_seq"]
    if has_host_rx_ms:
        fieldnames.append("host_rx_ms")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            row = {k: r.get(k, 0) for k in fieldnames}
            w.writerow(row)


def _write_imu_csv(path: Path, rows: List[Dict], has_host_rx_ms: bool = True) -> None:
    """Write a minimal decoded imu_log_*.csv for testing."""
    fieldnames = ["dev_us", "imu_seq", "ax", "ay", "az", "gx", "gy", "gz",
                  "acc_fsr_g", "gyro_fsr_dps", "frame_seq"]
    if has_host_rx_ms:
        fieldnames.append("host_rx_ms")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            row = {k: r.get(k, 0) for k in fieldnames}
            w.writerow(row)


def _make_emg_rows(n: int, dev_us_start: int, step_us: int = 500,
                   host_rx_ms_start: int = 0) -> List[Dict]:
    """Generate n synthetic EMG rows.

    host_rx_ms advances at the same rate as dev_us:
      step_us µs per sample  →  step_us / 1000 ms per sample
    e.g. 500 µs (2000 Hz) → 0.5 ms/sample, so 4000 samples = 2000 ms = 2 s.
    """
    rows = []
    for i in range(n):
        dev_us = dev_us_start + i * step_us
        # Advance host_rx_ms at the physical sample rate (step_us / 1000 ms per sample)
        host_rx_ms = int(host_rx_ms_start + i * step_us / 1000) if host_rx_ms_start > 0 else 0
        rows.append({
            "dev_us": dev_us,
            "emg_seq": i,
            "env": 100 + (i % 50),
            "raw": 2048 + int(200 * np.sin(2 * np.pi * i / 100)),
            "ref": 0,
            "frame_seq": i // 10,
            "host_rx_ms": host_rx_ms,
        })
    return rows


def _make_imu_rows(n: int, dev_us_start: int, step_us: int = 5000,
                   host_rx_ms_start: int = 0,
                   gyro_peak_at: int = -1,
                   gyro_fsr_dps: int = 1000) -> List[Dict]:
    """Generate n synthetic IMU rows. Optionally inject a gyro peak at index gyro_peak_at."""
    # LSB/dps for 1000 dps FSR = 32.8
    lsb_per_dps = 32.8
    rows = []
    for i in range(n):
        dev_us = dev_us_start + i * step_us
        host_rx_ms = (host_rx_ms_start + i * 5) if host_rx_ms_start > 0 else 0
        # Inject a 400 dps gyro peak at the specified index
        gz = int(400 * lsb_per_dps) if i == gyro_peak_at else int(10 * lsb_per_dps)
        rows.append({
            "dev_us": dev_us,
            "imu_seq": i,
            "ax": 8192,  # 1g at rest
            "ay": 0,
            "az": 0,
            "gx": 0,
            "gy": 0,
            "gz": gz,
            "acc_fsr_g": 4,
            "gyro_fsr_dps": gyro_fsr_dps,
            "frame_seq": i // 5,
            "host_rx_ms": host_rx_ms,
        })
    return rows


# ---------------------------------------------------------------------------
# Fixture: regression data (existing, requires frames.bin)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def regression_data_nopandas(tmp_path_factory):
    """
    Runs the offline decoder on the regression data's frames.bin and
    loads the resulting decoded CSVs. This simulates the Android pipeline.
    """
    if not _HAVE_DECODER:
        pytest.skip("btcentral_offline_decode not importable")
    if not REGRESSION_DATA_DIR.exists():
        pytest.skip(f"Regression data not found: {REGRESSION_DATA_DIR}")

    frames_bin_path = REGRESSION_DATA_DIR / "frames.bin"
    if not frames_bin_path.exists():
        pytest.skip(f"frames.bin not found in {REGRESSION_DATA_DIR}. Cannot run offline decoder.")

    temp_session_dir = tmp_path_factory.mktemp("decoded_session")
    (temp_session_dir / "frames.bin").symlink_to(frames_bin_path)

    summary = offline_decoder.decode_frames_bin_to_rotated_csv(str(temp_session_dir))
    decoded_dir = Path(summary["decoded_dir"])

    imu_paths = sorted(decoded_dir.glob("imu_log_*.csv"))
    if not imu_paths:
        pytest.fail("Offline decoder did not produce any imu_log_*.csv files.")

    all_imu_data = nopandas.load_emg_imu_logs(imu_paths)
    return all_imu_data


# ===========================================================================
# 1. Swing detection (existing test, kept intact)
# ===========================================================================

@pytest.mark.nopandas
@pytest.mark.slow
class TestNoPandasSwingDetection:
    """Test pandas-free swing detection."""

    def test_swing_detection_nopandas_from_arrays(self, regression_data_nopandas):
        """Test the array-based swing detection in emg_util_nopandas."""
        imu_data = regression_data_nopandas

        assert "ts_ms" in imu_data
        assert len(imu_data["ts_ms"]) > 0, "IMU data is empty"

        swing_windows = nopandas.detect_swing_windows_from_imu(
            ts_ms=imu_data["ts_ms"],
            ax=imu_data["ax"], ay=imu_data["ay"], az=imu_data["az"],
            gx=imu_data["gx"], gy=imu_data["gy"], gz=imu_data["gz"],
            thr_gyro_dps=300.0, thr_acc_g=0.0, min_gap_ms=2000.0,
            pre_ms=250.0, post_ms=450.0, use_gyro=True,
            gyro_fsr_dps=1000, acc_fsr_g=4,
        )

        assert isinstance(swing_windows, list)
        assert len(swing_windows) > 0, "Should detect at least one swing"

        first_swing = swing_windows[0]
        assert isinstance(first_swing, dict)
        for key in ("swing_id", "t_peak_ms", "t_start_ms", "t_end_ms", "peak_mag"):
            assert key in first_swing, f"Missing key: {key}"
        assert first_swing["swing_id"] == 0

        assert 5 <= len(swing_windows) <= 1000, \
            f"Swing count {len(swing_windows)} outside expected range [5, 1000]"

        peak_times = [s["t_peak_ms"] for s in swing_windows]
        assert np.all(np.diff(peak_times) > 0), "Swing peak times must be monotonically increasing"


# ===========================================================================
# 2. load_decoded_emg_csv / load_decoded_imu_csv — host_rx_ms priority
# ===========================================================================

class TestLoadDecodedCsvHostRxMs:
    """Verify that host_rx_ms is used as ts_ms when non-zero (Layer 3 of the fix)."""

    def test_emg_csv_uses_host_rx_ms_when_nonzero(self, tmp_path):
        """ts_ms should equal host_rx_ms when host_rx_ms > 0."""
        rows = _make_emg_rows(10, dev_us_start=1_000_000, host_rx_ms_start=1_740_000_000_000)
        p = tmp_path / "emg_log_test_000.csv"
        _write_emg_csv(p, rows)

        d = nopandas.load_decoded_emg_csv(p)
        assert d["ts_ms"].shape[0] == 10
        # ts_ms should be host_rx_ms values (1_740_000_000_000, 1_740_000_000_001, ...)
        assert d["ts_ms"][0] == pytest.approx(1_740_000_000_000.0)
        assert d["ts_ms"][1] == pytest.approx(1_740_000_000_001.0)
        # NOT dev_us/1000 (which would be 1000.0)
        assert d["ts_ms"][0] != pytest.approx(1000.0)

    def test_emg_csv_falls_back_to_dev_us_when_host_rx_ms_zero(self, tmp_path):
        """ts_ms should fall back to dev_us/1000 when host_rx_ms == 0."""
        rows = _make_emg_rows(10, dev_us_start=2_000_000, host_rx_ms_start=0)
        p = tmp_path / "emg_log_test_000.csv"
        _write_emg_csv(p, rows)

        d = nopandas.load_decoded_emg_csv(p)
        # ts_ms = dev_us / 1000 = 2000.0, 2000.5, 2001.0, ...
        assert d["ts_ms"][0] == pytest.approx(2000.0)
        assert d["ts_ms"][1] == pytest.approx(2000.5)

    def test_emg_csv_falls_back_when_no_host_rx_ms_column(self, tmp_path):
        """Legacy CSV without host_rx_ms column: ts_ms = dev_us/1000."""
        rows = _make_emg_rows(5, dev_us_start=500_000, host_rx_ms_start=0)
        p = tmp_path / "emg_log_legacy_000.csv"
        _write_emg_csv(p, rows, has_host_rx_ms=False)

        d = nopandas.load_decoded_emg_csv(p)
        assert d["ts_ms"][0] == pytest.approx(500.0)

    def test_imu_csv_uses_host_rx_ms_when_nonzero(self, tmp_path):
        """IMU CSV: ts_ms should equal host_rx_ms when host_rx_ms > 0."""
        rows = _make_imu_rows(8, dev_us_start=1_000_000, host_rx_ms_start=1_740_000_000_000)
        p = tmp_path / "imu_log_test_000.csv"
        _write_imu_csv(p, rows)

        d = nopandas.load_decoded_imu_csv(p)
        assert d["ts_ms"][0] == pytest.approx(1_740_000_000_000.0)
        assert d["ts_ms"][1] == pytest.approx(1_740_000_000_005.0)  # step = 5 ms

    def test_imu_csv_falls_back_to_dev_us_when_host_rx_ms_zero(self, tmp_path):
        """IMU CSV: ts_ms = dev_us/1000 when host_rx_ms == 0."""
        rows = _make_imu_rows(5, dev_us_start=3_000_000, host_rx_ms_start=0)
        p = tmp_path / "imu_log_test_000.csv"
        _write_imu_csv(p, rows)

        d = nopandas.load_decoded_imu_csv(p)
        assert d["ts_ms"][0] == pytest.approx(3000.0)


# ===========================================================================
# 3. stitch_decoded_session_from_paths — physical timeline construction
# ===========================================================================

class TestStitchDecodedSessionFromPaths:
    """
    Tests for stitch_decoded_session_from_paths() — the core stitching function.

    Scenarios tested:
      A. Single capture (baseline)
      B. Two captures with BLE reconnect gap (host_rx_ms jumps forward)
      C. ESP32 reset between captures (dev_us restarts from 0, host_rx_ms continuous)
      D. Legacy files without host_rx_ms (fallback to dev_us/1000)
      E. Correct ordering when captures arrive out of filename order
    """

    EMG_FS = 2000.0  # Hz

    def _make_session(self, tmp_path: Path, captures: List[Dict]) -> List[Path]:
        """
        Build a set of decoded EMG CSV files for a multi-capture session.

        Each entry in `captures` is a dict:
          dev_us_start   int   — ESP32 device clock at start of capture
          host_rx_ms_start int — wall-clock ms at start of capture (0 = legacy)
          n_samples      int   — number of EMG samples
          step_us        int   — sample interval in µs (default 500 = 2000 Hz)
        """
        paths = []
        for i, cap in enumerate(captures):
            rows = _make_emg_rows(
                n=cap["n_samples"],
                dev_us_start=cap["dev_us_start"],
                step_us=cap.get("step_us", 500),
                host_rx_ms_start=cap.get("host_rx_ms_start", 0),
            )
            p = tmp_path / f"emg_log_cap{i:03d}_000.csv"
            _write_emg_csv(p, rows, has_host_rx_ms=cap.get("host_rx_ms_start", 0) > 0)
            paths.append(p)
        return paths

    def test_single_capture_basic(self, tmp_path):
        """Single capture: stitching should return correct sample count."""
        paths = self._make_session(tmp_path, [
            {"dev_us_start": 0, "host_rx_ms_start": 1_740_000_000_000, "n_samples": 4000},
        ])
        result = nopandas.stitch_decoded_session_from_paths(
            emg_paths=paths, imu_paths=[], emg_fs_hz=self.EMG_FS)
        assert result["summary"]["num_emg_samples"] == 4000

    def test_two_captures_ble_reconnect_gap(self, tmp_path):
        """
        Two captures with a 10-second BLE reconnect gap.
        host_rx_ms is continuous; dev_us is also continuous (no reset).
        After stitching, total samples = sum of both captures.
        Session duration should reflect the gap.

        Timeline (host_rx_ms):
          Capture 1: t=0..2s   (4000 samples @ 2000 Hz = 2 s)
          Gap:       10 s
          Capture 2: t=12..14s (4000 samples @ 2000 Hz = 2 s)
          Total span (first to last sample): ~14 s
        """
        t0_ms = 1_740_000_000_000
        gap_ms = 10_000
        n = 4000
        step_us = 500  # 2000 Hz → 0.5 ms/sample

        # Duration of one capture in ms: n * step_us / 1000
        cap_dur_ms = n * step_us // 1000  # = 2000 ms = 2 s

        paths = self._make_session(tmp_path, [
            {"dev_us_start": 0,
             "host_rx_ms_start": t0_ms,
             "n_samples": n, "step_us": step_us},
            {"dev_us_start": n * step_us + gap_ms * 1000,       # dev_us continues
             "host_rx_ms_start": t0_ms + cap_dur_ms + gap_ms,   # t0 + 2000 + 10000
             "n_samples": n, "step_us": step_us},
        ])
        result = nopandas.stitch_decoded_session_from_paths(
            emg_paths=paths, imu_paths=[], emg_fs_hz=self.EMG_FS)

        assert result["summary"]["num_emg_samples"] == 2 * n
        # Duration = first-to-last sample span: 2s + 10s gap + 2s = ~14s
        dur = result["summary"]["session_duration_s"]
        assert dur == pytest.approx(14.0, abs=0.1), \
            f"Expected ~14s duration (2s+10s gap+2s), got {dur:.2f}s"

    def test_esp32_reset_between_captures(self, tmp_path):
        """
        ESP32 reset: dev_us restarts from 0 in capture 2.
        host_rx_ms is continuous (wall-clock).
        Stitching must use host_rx_ms to avoid timestamp overlap.
        """
        t0_ms = 1_740_000_000_000
        n = 2000
        step_us = 500

        paths = self._make_session(tmp_path, [
            {"dev_us_start": 0,
             "host_rx_ms_start": t0_ms,
             "n_samples": n, "step_us": step_us},
            # ESP32 reset: dev_us restarts from 0
            {"dev_us_start": 0,
             "host_rx_ms_start": t0_ms + n + 5_000,  # 5s gap in wall-clock
             "n_samples": n, "step_us": step_us},
        ])
        result = nopandas.stitch_decoded_session_from_paths(
            emg_paths=paths, imu_paths=[], emg_fs_hz=self.EMG_FS)

        assert result["summary"]["num_emg_samples"] == 2 * n
        # Duration should be ~6s (1s data + 5s gap + 1s data), not ~1s (if dev_us overlap)
        dur = result["summary"]["session_duration_s"]
        assert dur > 5.0, \
            f"Duration {dur:.2f}s too short — ESP32 reset not handled (timestamps overlapping)"

    def test_legacy_files_no_host_rx_ms(self, tmp_path):
        """Legacy files without host_rx_ms: stitching falls back to dev_us/1000.

        Timeline (dev_us → ts_ms):
          Capture 1: 0 .. 999_500 µs  →  0 .. 999.5 ms  (1 s)
          Gap:       5_000_000 µs = 5 s
          Capture 2: 6_000_000 .. 6_999_500 µs  →  6000 .. 6999.5 ms  (1 s)
          Total span (first to last sample): ~7 s
        """
        n = 2000
        step_us = 500  # 2000 Hz → 0.5 ms/sample, 2000 samples = 1 s
        paths = self._make_session(tmp_path, [
            {"dev_us_start": 0, "host_rx_ms_start": 0, "n_samples": n, "step_us": step_us},
            {"dev_us_start": n * step_us + 5_000_000,  # 1_000_000 + 5_000_000 = 6_000_000 µs
             "host_rx_ms_start": 0, "n_samples": n, "step_us": step_us},
        ])
        result = nopandas.stitch_decoded_session_from_paths(
            emg_paths=paths, imu_paths=[], emg_fs_hz=self.EMG_FS)

        assert result["summary"]["num_emg_samples"] == 2 * n
        # Duration = dev_us based: first(0ms) to last(6999.5ms) = ~7s
        dur = result["summary"]["session_duration_s"]
        assert dur == pytest.approx(7.0, abs=0.2)

    def test_out_of_order_paths_sorted_by_ts_ms(self, tmp_path):
        """
        Paths passed in reverse order: stitching must sort by ts_ms, not path order.
        """
        t0_ms = 1_740_000_000_000
        n = 1000
        step_us = 500

        p1 = tmp_path / "emg_log_cap001_000.csv"
        p2 = tmp_path / "emg_log_cap000_000.csv"  # earlier capture, later filename

        _write_emg_csv(p1, _make_emg_rows(n, dev_us_start=n * step_us,
                                           host_rx_ms_start=t0_ms + n))
        _write_emg_csv(p2, _make_emg_rows(n, dev_us_start=0,
                                           host_rx_ms_start=t0_ms))

        # Pass in reverse order (p1 before p2)
        result = nopandas.stitch_decoded_session_from_paths(
            emg_paths=[p1, p2], imu_paths=[], emg_fs_hz=self.EMG_FS)

        assert result["summary"]["num_emg_samples"] == 2 * n

    def test_empty_emg_paths_raises(self, tmp_path):
        """Empty path list should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            nopandas.stitch_decoded_session_from_paths(
                emg_paths=[], imu_paths=[], emg_fs_hz=self.EMG_FS)

    def test_with_imu_swing_detection(self, tmp_path):
        """
        Two captures with IMU data. Inject a gyro peak in each capture.
        Swing detection should find 2 swings with correct wall-clock timestamps.
        """
        t0_ms = 1_740_000_000_000
        n_emg = 4000
        n_imu = 400
        emg_step_us = 500   # 2000 Hz
        imu_step_us = 5000  # 200 Hz
        gap_ms = 5_000

        # EMG paths
        emg_paths = self._make_session(tmp_path, [
            {"dev_us_start": 0, "host_rx_ms_start": t0_ms,
             "n_samples": n_emg, "step_us": emg_step_us},
            {"dev_us_start": 0, "host_rx_ms_start": t0_ms + n_emg + gap_ms,
             "n_samples": n_emg, "step_us": emg_step_us},
        ])

        # IMU paths — one peak per capture
        imu_p1 = tmp_path / "imu_log_cap0_000.csv"
        imu_p2 = tmp_path / "imu_log_cap1_000.csv"
        _write_imu_csv(imu_p1, _make_imu_rows(
            n_imu, dev_us_start=0, host_rx_ms_start=t0_ms,
            gyro_peak_at=n_imu // 2))
        _write_imu_csv(imu_p2, _make_imu_rows(
            n_imu, dev_us_start=0, host_rx_ms_start=t0_ms + n_emg + gap_ms,
            gyro_peak_at=n_imu // 2))

        result = nopandas.stitch_decoded_session_from_paths(
            emg_paths=emg_paths, imu_paths=[imu_p1, imu_p2],
            emg_fs_hz=self.EMG_FS,
            swing_pre_ms=100.0, swing_post_ms=200.0,
        )

        swings = result["swing_windows"]
        assert len(swings) >= 2, \
            f"Expected ≥2 swings (one per capture), got {len(swings)}"

        # The two swings should be separated by at least the gap
        if len(swings) >= 2:
            gap_between = swings[1]["t_peak_ms"] - swings[0]["t_peak_ms"]
            assert gap_between > gap_ms * 0.8, \
                f"Swings too close ({gap_between:.0f} ms) — gap not preserved in timeline"


# ===========================================================================
# 4. stitch_decoded_session — thin wrapper
# ===========================================================================

class TestStitchDecodedSession:
    """stitch_decoded_session(decoded_dir) is a thin wrapper — verify it delegates correctly."""

    EMG_FS = 2000.0

    def test_single_dir_matches_from_paths(self, tmp_path):
        """stitch_decoded_session and stitch_decoded_session_from_paths must return same result."""
        n = 2000
        rows = _make_emg_rows(n, dev_us_start=0, host_rx_ms_start=1_740_000_000_000)
        p = tmp_path / "emg_log_test_000.csv"
        _write_emg_csv(p, rows)

        r1 = nopandas.stitch_decoded_session(tmp_path, emg_fs_hz=self.EMG_FS)
        r2 = nopandas.stitch_decoded_session_from_paths(
            emg_paths=[p], imu_paths=[], emg_fs_hz=self.EMG_FS)

        assert r1["summary"]["num_emg_samples"] == r2["summary"]["num_emg_samples"]
        assert r1["summary"]["session_duration_s"] == pytest.approx(
            r2["summary"]["session_duration_s"], abs=0.001)

    def test_raises_when_no_emg_csv(self, tmp_path):
        """Should raise FileNotFoundError when decoded_dir has no emg_log_*.csv."""
        with pytest.raises(FileNotFoundError):
            nopandas.stitch_decoded_session(tmp_path, emg_fs_hz=self.EMG_FS)


# ===========================================================================
# 5. Per-swing EMG features
# ===========================================================================

class TestComputeSwingEmgFeatures:
    """compute_swing_emg_features() — verify output structure and IMU feature computation."""

    FS = 2000.0

    def _make_signals(self, n: int = 4000):
        """Synthetic preprocessed EMG + envelope + timestamps."""
        t = np.arange(n, dtype=np.float64) / self.FS
        proc = np.sin(2 * np.pi * 50 * t) * 200.0
        env = np.abs(proc)
        ts_ms = t * 1000.0
        return proc, env, ts_ms

    def test_output_structure(self):
        """Each swing feature row must have required keys."""
        proc, env, ts_ms = self._make_signals()
        swings = [{"swing_id": 0, "t_start_ms": 500.0, "t_peak_ms": 700.0,
                   "t_end_ms": 900.0, "peak_z": 400.0, "peak_mag": 400.0}]
        feats = nopandas.compute_swing_emg_features(proc, env, ts_ms, self.FS, swings)

        assert len(feats) == 1
        row = feats[0]
        for key in ("swing_id", "t_start_ms", "t_peak_ms", "t_end_ms",
                    "emg_env_peak", "emg_env_mean", "emg_iemg",
                    "mav", "rms", "wl", "zc", "ssc", "mnf", "mdf",
                    "imu_mean_acc_dyn", "imu_peak_acc_dyn"):
            assert key in row, f"Missing key: {key}"

    def test_imu_acc_dyn_computed_when_provided(self):
        """imu_mean_acc_dyn and imu_peak_acc_dyn should be finite when IMU data provided."""
        proc, env, ts_ms = self._make_signals()
        swings = [{"swing_id": 0, "t_start_ms": 500.0, "t_peak_ms": 700.0,
                   "t_end_ms": 900.0, "peak_z": 400.0, "peak_mag": 400.0}]

        imu_ts_ms = np.linspace(0, 2000, 400)
        imu_acc_dyn = np.ones(400) * 0.5  # 0.5g dynamic acceleration

        feats = nopandas.compute_swing_emg_features(
            proc, env, ts_ms, self.FS, swings,
            imu_ts_ms=imu_ts_ms, imu_acc_dyn=imu_acc_dyn)

        assert np.isfinite(feats[0]["imu_mean_acc_dyn"])
        assert feats[0]["imu_mean_acc_dyn"] == pytest.approx(0.5, abs=0.01)

    def test_imu_acc_dyn_nan_when_not_provided(self):
        """imu_mean_acc_dyn should be NaN when IMU data not provided."""
        proc, env, ts_ms = self._make_signals()
        swings = [{"swing_id": 0, "t_start_ms": 500.0, "t_peak_ms": 700.0,
                   "t_end_ms": 900.0, "peak_z": 400.0, "peak_mag": 400.0}]
        feats = nopandas.compute_swing_emg_features(proc, env, ts_ms, self.FS, swings)
        assert np.isnan(feats[0]["imu_mean_acc_dyn"])

    def test_empty_swings_returns_empty(self):
        """Empty swing list should return empty list."""
        proc, env, ts_ms = self._make_signals()
        feats = nopandas.compute_swing_emg_features(proc, env, ts_ms, self.FS, [])
        assert feats == []


# ===========================================================================
# 6. Baseline selection and fatigue deltas
# ===========================================================================

class TestBaselineAndFatigueDeltas:
    """compute_baseline_from_swing_features + apply_baseline_deltas."""

    def _make_swing_feats(self, n: int, mdf_start: float = 100.0,
                          mdf_drop_per_swing: float = 1.0,
                          t0_ms: float = 0.0) -> List[Dict]:
        rows = []
        for i in range(n):
            rows.append({
                "swing_id": i,
                "t_start_ms": t0_ms + i * 5000.0,
                "t_peak_ms": t0_ms + i * 5000.0 + 350.0,
                "t_end_ms": t0_ms + i * 5000.0 + 700.0,
                "mdf": mdf_start - i * mdf_drop_per_swing,
                "rms": 200.0 + i * 2.0,
                "mav": 150.0,
                "wl": 1000.0,
                "emg_env_mean": 300.0,
                "emg_iemg": 0.15,
                "imu_mean_acc_dyn": 1.0 - i * 0.01,
                "peak_z": 400.0,
                "peak_mag": 400.0,
            })
        return rows

    def test_baseline_median_mdf(self):
        """Baseline MDF should be 75th percentile of selected baseline swings.

        Fresh muscles have the HIGHEST MDF, so the baseline uses the 75th percentile
        (not median) to represent the fresh state.  This prevents warm-up swings with
        lower MDF from anchoring the baseline too low.
        """
        feats = self._make_swing_feats(20, mdf_start=100.0, mdf_drop_per_swing=1.0,
                                       t0_ms=400_000.0)  # after 5-min warmup
        base_swings = nopandas.select_baseline_swings(
            feats, session_t0_ms=0.0, warmup_skip_min=5.0, baseline_swings=10)
        baseline = nopandas.compute_baseline_from_swing_features(base_swings)

        assert "mdf" in baseline
        assert np.isfinite(baseline["mdf"])
        # First 10 swings after warmup: MDF = 100, 99, 98, ..., 91
        # 75th percentile of [91..100] = 97.75  (matches emg_util.py behavior)
        assert baseline["mdf"] == pytest.approx(97.75, abs=1.0)

    def test_apply_baseline_deltas_mdf_drop(self):
        """mdf_drop_pct should be positive when MDF decreases from baseline."""
        baseline = {"mdf": 100.0, "rms": 200.0, "imu_mean_acc_dyn": 1.0}
        rows = [{"swing_id": 0, "mdf": 80.0, "rms": 220.0, "imu_mean_acc_dyn": 0.8}]
        out = nopandas.apply_baseline_deltas(rows, baseline)

        assert out[0]["mdf_drop_pct"] == pytest.approx(20.0, abs=0.01)
        assert out[0]["rms_increase_pct"] == pytest.approx(10.0, abs=0.01)
        assert out[0]["acc_drop_pct"] == pytest.approx(20.0, abs=0.01)

    def test_apply_baseline_deltas_no_drop(self):
        """mdf_drop_pct should be 0 when MDF equals baseline."""
        baseline = {"mdf": 100.0, "rms": 200.0}
        rows = [{"swing_id": 0, "mdf": 100.0, "rms": 200.0}]
        out = nopandas.apply_baseline_deltas(rows, baseline)
        assert out[0]["mdf_drop_pct"] == pytest.approx(0.0, abs=0.001)

    def test_warmup_skip_filters_early_swings(self):
        """Swings before warmup_skip_min should not be selected as baseline."""
        # 5 swings before 5-min mark, 15 swings after
        early = self._make_swing_feats(5, mdf_start=50.0, t0_ms=0.0)   # 0–25s
        late = self._make_swing_feats(15, mdf_start=100.0, t0_ms=310_000.0)  # after 5 min
        all_swings = early + late

        base_swings = nopandas.select_baseline_swings(
            all_swings, session_t0_ms=0.0, warmup_skip_min=5.0, baseline_swings=10)
        baseline = nopandas.compute_baseline_from_swing_features(base_swings)

        # Baseline MDF should be ~100 (from late swings), not ~50 (from early swings)
        assert baseline["mdf"] > 80.0, \
            f"Baseline MDF {baseline['mdf']:.1f} too low — warmup filter not working"

    def test_empty_swing_feats_returns_empty_baseline(self):
        """Empty swing features should return empty baseline dict."""
        baseline = nopandas.compute_baseline_from_swing_features([])
        assert baseline == {}

    def test_apply_baseline_deltas_empty_rows(self):
        """Empty rows should return empty list."""
        out = nopandas.apply_baseline_deltas([], {"mdf": 100.0})
        assert out == []


# ===========================================================================
# 7. Cross-version consistency: emg_util.py vs emg_util_nopandas.py
# ===========================================================================

class TestSwingDetectionCrossVersion:
    """
    Verify that emg_util.detect_swing_windows_from_imu_arrays (pandas, Windows)
    and emg_util_nopandas.detect_swing_windows_from_imu_arrays (no-pandas, Android)
    produce identical swing counts, peak times, and peak magnitudes on the same
    synthetic IMU data.

    This is the canonical cross-platform consistency check.

    Algorithm parity checklist (both versions must implement identically):
      ✅ build_time_axis_from_ts — same logic, different input type
      ✅ FSR conversion maps (_GYR_MAP, _ACC_MAP)
      ✅ mag_dps = sqrt(gx²+gy²+gz²) / gyr_lsb
      ✅ Optional acc gate: amag_g >= thr_acc_g
      ✅ Contiguous above-threshold region → peak at argmax(mag_dps)
      ✅ Min-gap enforcement: keep highest peak within min_gap_ms
      ✅ Window merging: merge overlapping [t_start, t_end] windows
    """

    # Shared parameters — must match between both calls
    THR_GYRO_DPS = 300.0
    THR_ACC_G    = 0.0
    MIN_GAP_MS   = 2000.0
    PRE_MS       = 250.0
    POST_MS      = 450.0
    GYRO_FSR     = 1000
    ACC_FSR      = 4

    def _make_imu_arrays(self, n: int = 2000, fs_hz: float = 200.0,
                         swing_at_samples=None):
        """
        Synthetic IMU arrays with optional gyro peaks.

        swing_at_samples: list of sample indices where a 400 dps peak is injected.
        """
        if swing_at_samples is None:
            swing_at_samples = []

        lsb_per_dps = 32.8  # 1000 dps FSR
        dt_ms = 1000.0 / fs_hz
        ts_ms = np.arange(n, dtype=np.float64) * dt_ms

        gx = np.zeros(n, dtype=np.float64)
        gy = np.zeros(n, dtype=np.float64)
        gz = np.full(n, 10.0 * lsb_per_dps, dtype=np.float64)  # 10 dps baseline

        for idx in swing_at_samples:
            if 0 <= idx < n:
                gz[idx] = 400.0 * lsb_per_dps  # 400 dps peak

        ax = np.full(n, 8192.0)  # 1g at rest (acc_fsr=4 → 8192 LSB/g)
        ay = np.zeros(n)
        az = np.zeros(n)

        return ts_ms, ax, ay, az, gx, gy, gz

    def _run_pandas(self, ts_ms, ax, ay, az, gx, gy, gz):
        """Run the pandas (Windows) version."""
        import emg_util as core_pandas
        df = core_pandas.detect_swing_windows_from_imu_arrays(
            ts_ms, ax, ay, az, gx, gy, gz,
            thr_gyro_dps=self.THR_GYRO_DPS,
            thr_acc_g=self.THR_ACC_G,
            min_gap_ms=self.MIN_GAP_MS,
            pre_ms=self.PRE_MS,
            post_ms=self.POST_MS,
        )
        # Convert DataFrame to list of dicts for uniform comparison
        return df.to_dict("records")

    def _run_nopandas(self, ts_ms, ax, ay, az, gx, gy, gz):
        """Run the nopandas (Android) version."""
        return nopandas.detect_swing_windows_from_imu(
            ts_ms, ax, ay, az, gx, gy, gz,
            thr_gyro_dps=self.THR_GYRO_DPS,
            thr_acc_g=self.THR_ACC_G,
            min_gap_ms=self.MIN_GAP_MS,
            pre_ms=self.PRE_MS,
            post_ms=self.POST_MS,
            gyro_fsr_dps=self.GYRO_FSR,
            acc_fsr_g=self.ACC_FSR,
        )

    def test_no_swings_both_empty(self):
        """No peaks above threshold → both return empty."""
        ts_ms, ax, ay, az, gx, gy, gz = self._make_imu_arrays(n=400)
        pd_rows  = self._run_pandas(ts_ms, ax, ay, az, gx, gy, gz)
        np_rows  = self._run_nopandas(ts_ms, ax, ay, az, gx, gy, gz)
        assert len(pd_rows) == 0
        assert len(np_rows) == 0

    def test_single_swing_same_peak_time(self):
        """One peak → both detect it at the same t_peak_ms."""
        ts_ms, ax, ay, az, gx, gy, gz = self._make_imu_arrays(
            n=1000, swing_at_samples=[500])
        pd_rows = self._run_pandas(ts_ms, ax, ay, az, gx, gy, gz)
        np_rows = self._run_nopandas(ts_ms, ax, ay, az, gx, gy, gz)

        assert len(pd_rows) == 1, f"pandas: expected 1 swing, got {len(pd_rows)}"
        assert len(np_rows) == 1, f"nopandas: expected 1 swing, got {len(np_rows)}"
        assert pd_rows[0]["t_peak_ms"] == pytest.approx(np_rows[0]["t_peak_ms"], abs=1.0)
        assert pd_rows[0]["peak_mag"]  == pytest.approx(np_rows[0]["peak_mag"],  abs=0.01)

    def test_two_swings_same_count_and_times(self):
        """Two peaks separated by > min_gap_ms → both detect 2 swings at same times."""
        # 200 Hz, 5000 samples = 25s; peaks at 2s (400) and 12s (2400)
        ts_ms, ax, ay, az, gx, gy, gz = self._make_imu_arrays(
            n=5000, swing_at_samples=[400, 2400])
        pd_rows = self._run_pandas(ts_ms, ax, ay, az, gx, gy, gz)
        np_rows = self._run_nopandas(ts_ms, ax, ay, az, gx, gy, gz)

        assert len(pd_rows) == len(np_rows), \
            f"Swing count mismatch: pandas={len(pd_rows)}, nopandas={len(np_rows)}"
        assert len(pd_rows) == 2

        for i, (pr, nr) in enumerate(zip(pd_rows, np_rows)):
            assert pr["t_peak_ms"] == pytest.approx(nr["t_peak_ms"], abs=1.0), \
                f"Swing {i}: t_peak_ms mismatch pandas={pr['t_peak_ms']:.1f} nopandas={nr['t_peak_ms']:.1f}"
            assert pr["peak_mag"] == pytest.approx(nr["peak_mag"], abs=0.01), \
                f"Swing {i}: peak_mag mismatch"
            assert pr["t_start_ms"] == pytest.approx(nr["t_start_ms"], abs=1.0)
            assert pr["t_end_ms"]   == pytest.approx(nr["t_end_ms"],   abs=1.0)

    def test_two_peaks_within_min_gap_keep_highest(self):
        """
        Two peaks within min_gap_ms → both keep the HIGHER peak (not the first).
        This tests the min-gap enforcement logic is identical.
        """
        # 200 Hz; peaks at 1s (200) and 1.5s (300) — gap = 500ms < 2000ms
        # Peak at 300 is higher (400 dps) than peak at 200 (350 dps)
        lsb = 32.8
        ts_ms, ax, ay, az, gx, gy, gz = self._make_imu_arrays(n=2000)
        gz[200] = 350.0 * lsb  # lower peak at 1s
        gz[300] = 400.0 * lsb  # higher peak at 1.5s

        pd_rows = self._run_pandas(ts_ms, ax, ay, az, gx, gy, gz)
        np_rows = self._run_nopandas(ts_ms, ax, ay, az, gx, gy, gz)

        assert len(pd_rows) == 1, f"pandas: expected 1 swing (merged), got {len(pd_rows)}"
        assert len(np_rows) == 1, f"nopandas: expected 1 swing (merged), got {len(np_rows)}"
        # Both should keep the higher peak (at sample 300 = 1.5s)
        assert pd_rows[0]["t_peak_ms"] == pytest.approx(np_rows[0]["t_peak_ms"], abs=1.0)
        assert pd_rows[0]["peak_mag"]  == pytest.approx(400.0, abs=0.1)
        assert np_rows[0]["peak_mag"]  == pytest.approx(400.0, abs=0.1)

    def test_window_boundaries_identical(self):
        """t_start_ms = t_peak_ms - pre_ms, t_end_ms = t_peak_ms + post_ms."""
        ts_ms, ax, ay, az, gx, gy, gz = self._make_imu_arrays(
            n=1000, swing_at_samples=[500])
        pd_rows = self._run_pandas(ts_ms, ax, ay, az, gx, gy, gz)
        np_rows = self._run_nopandas(ts_ms, ax, ay, az, gx, gy, gz)

        assert len(pd_rows) == 1 and len(np_rows) == 1
        tp_pd = pd_rows[0]["t_peak_ms"]
        tp_np = np_rows[0]["t_peak_ms"]
        assert pd_rows[0]["t_start_ms"] == pytest.approx(tp_pd - self.PRE_MS,  abs=0.1)
        assert pd_rows[0]["t_end_ms"]   == pytest.approx(tp_pd + self.POST_MS, abs=0.1)
        assert np_rows[0]["t_start_ms"] == pytest.approx(tp_np - self.PRE_MS,  abs=0.1)
        assert np_rows[0]["t_end_ms"]   == pytest.approx(tp_np + self.POST_MS, abs=0.1)

    def test_empty_input_both_return_empty(self):
        """Empty arrays → both return empty."""
        empty = np.array([])
        pd_rows = self._run_pandas(empty, empty, empty, empty, empty, empty, empty)
        np_rows = self._run_nopandas(empty, empty, empty, empty, empty, empty, empty)
        assert len(pd_rows) == 0
        assert len(np_rows) == 0


# ===========================================================================
# 8. ENV Gating (Activation Detection) - nopandas version
# ===========================================================================

class TestENVGatingNoPandas:
    """Test ENV-based activation gating functions (nopandas version)."""

    def test_compute_env_gate_threshold_percentile(self):
        """Test ENV threshold computation (percentile mode) - nopandas."""
        # Synthetic ENV signal
        env = np.random.rand(20000) * 2000 + 500  # 500-2500 ADC range
        
        # Compute threshold (percentile mode)
        threshold = nopandas.compute_env_gate_threshold(
            env, emg_fs_hz=2000.0,
            mode='percentile',
            percentile=75.0,
            window_sec=1.0,
        )
        
        # Verify output
        assert isinstance(threshold, float)
        assert np.isfinite(threshold)
        assert threshold > 0, "Threshold should be positive"
        assert threshold < 4095, "Threshold should be within ADC range"
        
        # Threshold should be between median and max
        assert np.median(env) < threshold < np.max(env)
    
    def test_compute_env_gate_threshold_absolute(self):
        """Test ENV threshold computation (absolute mode) - nopandas."""
        # Dummy ENV signal
        env = np.random.rand(10000) * 2000
        
        # Compute threshold (absolute mode)
        threshold = nopandas.compute_env_gate_threshold(
            env, emg_fs_hz=2000.0,
            mode='absolute',
            absolute_threshold=1651.0,
        )
        
        # Should return the absolute value
        assert threshold == 1651.0
    
    def test_apply_env_gate_to_swings_list(self):
        """Test ENV gating on list of dicts (nopandas path)."""
        # Synthetic ENV signal with clear high/low distinction
        # p75 of [500, 500, ..., 2000, 2000, ..., 600, 600, ...] ≈ 1125
        # So swing at 2000 should be active, swings at 500/600 should be inactive
        env = np.concatenate([
            np.ones(2000) * 500,   # Low ENV (rest)
            np.ones(2000) * 2000,  # High ENV (active) - clearly above p75
            np.ones(2000) * 600,   # Low ENV (rest)
        ])
        emg_ts_ms = np.arange(len(env)) * 0.5  # 2000 Hz → 0.5 ms/sample
        
        # Swings at different ENV levels
        swings = [
            {"swing_id": 0, "t_start_ms": 500.0, "t_end_ms": 1000.0},   # Low ENV (~500)
            {"swing_id": 1, "t_start_ms": 2500.0, "t_end_ms": 3000.0},  # High ENV (~2000)
            {"swing_id": 2, "t_start_ms": 4500.0, "t_end_ms": 5000.0},  # Low ENV (~600)
        ]
        
        # ENV gating config - use percentile mode
        env_gate_cfg = {
            'enable': True,
            'mode': 'percentile',
            'percentile': 50.0,  # Use median so threshold ≈ 600, making swing 1 active
            'absolute_threshold': 1651.0,
            'window_sec': 1.0,
        }
        
        # Apply gating
        gated_swings = nopandas.apply_env_gate_to_swings(
            swings, env, emg_ts_ms, 2000.0, env_gate_cfg
        )
        
        # Verify output
        assert isinstance(gated_swings, list)
        assert len(gated_swings) == len(swings)
        assert all('env_active' in s for s in gated_swings)
        
        # Check env_active values
        assert all(s['env_active'] in [0, 1] for s in gated_swings)
        
        # Swing 1 (high ENV) should be active
        assert gated_swings[1]['env_active'] == 1, \
            f"Swing 1 should be active (ENV=2000 > threshold), got env_active={gated_swings[1]['env_active']}"
        
        # At least one swing should be active
        assert sum(s['env_active'] for s in gated_swings) > 0
    
    def test_apply_env_gate_disabled(self):
        """Test ENV gating when disabled (all swings marked active) - nopandas."""
        # Dummy data
        env = np.random.rand(5000) * 2000
        emg_ts_ms = np.arange(len(env)) * 0.5
        
        swings = [
            {"swing_id": 0, "t_start_ms": 500.0, "t_end_ms": 1000.0},
            {"swing_id": 1, "t_start_ms": 2500.0, "t_end_ms": 3000.0},
        ]
        
        # ENV gating config (disabled)
        env_gate_cfg = {
            'enable': False,
            'mode': 'percentile',
            'percentile': 75.0,
        }
        
        # Apply gating
        gated_swings = nopandas.apply_env_gate_to_swings(
            swings, env, emg_ts_ms, 2000.0, env_gate_cfg
        )
        
        # All swings should be marked active when disabled
        assert all(s['env_active'] == 1 for s in gated_swings)
    
    def test_env_gate_threshold_consistency(self):
        """Test that ENV threshold is deterministic - nopandas."""
        # Fixed ENV signal
        np.random.seed(42)
        env = np.random.rand(20000) * 2000
        
        # Compute threshold twice
        thr1 = nopandas.compute_env_gate_threshold(
            env, emg_fs_hz=2000.0, mode='percentile', percentile=75.0
        )
        thr2 = nopandas.compute_env_gate_threshold(
            env, emg_fs_hz=2000.0, mode='percentile', percentile=75.0
        )
        
        # Should be identical
        assert thr1 == thr2
    
    def test_env_gate_percentile_range(self):
        """Test ENV threshold with different percentiles - nopandas."""
        # Fixed ENV signal
        np.random.seed(42)
        env = np.random.rand(20000) * 2000
        
        # Compute thresholds at different percentiles
        thr_50 = nopandas.compute_env_gate_threshold(
            env, emg_fs_hz=2000.0, mode='percentile', percentile=50.0
        )
        thr_75 = nopandas.compute_env_gate_threshold(
            env, emg_fs_hz=2000.0, mode='percentile', percentile=75.0
        )
        thr_90 = nopandas.compute_env_gate_threshold(
            env, emg_fs_hz=2000.0, mode='percentile', percentile=90.0
        )
        
        # Higher percentile should give higher threshold
        assert thr_50 < thr_75 < thr_90
    
    def test_env_gate_empty_swings(self):
        """Test ENV gating with empty swing list - nopandas."""
        env = np.random.rand(5000) * 2000
        emg_ts_ms = np.arange(len(env)) * 0.5
        
        env_gate_cfg = {
            'enable': True,
            'mode': 'percentile',
            'percentile': 75.0,
        }
        
        # Apply gating to empty list
        gated_swings = nopandas.apply_env_gate_to_swings(
            [], env, emg_ts_ms, 2000.0, env_gate_cfg
        )
        
        # Should return empty list
        assert gated_swings == []
    
    def test_env_gate_integration_with_swing_features(self):
        """Test ENV gating integration with compute_swing_emg_features - nopandas."""
        # Synthetic signals
        n = 10000
        proc = np.sin(2 * np.pi * 50 * np.arange(n) / 2000.0) * 200.0
        env_sig = np.abs(proc) + np.random.rand(n) * 500 + 1000  # 1000-1700 range
        ts_ms = np.arange(n) * 0.5
        
        # Create swings
        swings = [
            {"swing_id": 0, "t_start_ms": 500.0, "t_peak_ms": 700.0,
             "t_end_ms": 900.0, "peak_z": 400.0, "peak_mag": 400.0},
            {"swing_id": 1, "t_start_ms": 2500.0, "t_peak_ms": 2700.0,
             "t_end_ms": 2900.0, "peak_z": 400.0, "peak_mag": 400.0},
        ]
        
        # Apply ENV gating
        env_gate_cfg = {
            'enable': True,
            'mode': 'percentile',
            'percentile': 75.0,
        }
        gated_swings = nopandas.apply_env_gate_to_swings(
            swings, env_sig, ts_ms, 2000.0, env_gate_cfg
        )
        
        # Verify env_active was added by apply_env_gate_to_swings
        assert all('env_active' in s for s in gated_swings), \
            "apply_env_gate_to_swings should add env_active field"
        
        # Compute features (should preserve env_active field from input)
        feats = nopandas.compute_swing_emg_features(
            proc, env_sig, ts_ms, 2000.0, gated_swings
        )
        
        # compute_swing_emg_features should preserve env_active from input swings
        # Check if env_active is in the output (it should be copied from input)
        for i, f in enumerate(feats):
            if 'env_active' in gated_swings[i]:
                assert 'env_active' in f, \
                    f"compute_swing_emg_features should preserve env_active from input swing {i}"
                assert f['env_active'] == gated_swings[i]['env_active'], \
                    f"env_active value should match input for swing {i}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "nopandas"])
