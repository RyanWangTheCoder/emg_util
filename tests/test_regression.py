"""
Regression Tests for EMG Analysis Pipeline

Tests the complete analysis pipeline using real data from regression_testlogs/
to ensure consistent behavior across code changes.

Run with: pytest tests/test_regression.py -v

Test Categories (use -m flag to run specific category):
  - data_loading: Data loading and integrity tests
  - signal_processing: Signal processing algorithm tests
  - swing_detection: Swing detection tests
  - fatigue: Fatigue analysis tests
  - pipeline: Full pipeline integration tests
  - baseline: Regression baseline tests
  - error_handling: Error handling and edge cases
  - plotter: Plotter offline mode tests
  - fast: Fast tests (< 5 seconds)
  - slow: Slow tests (> 5 seconds)

Examples:
  pytest tests/test_regression.py -m data_loading        # Only data loading tests
  pytest tests/test_regression.py -m "fast"              # Only fast tests
  pytest tests/test_regression.py -m "not slow"          # Skip slow tests
  pytest tests/test_regression.py -m "signal_processing or fatigue"  # Multiple categories
"""

import pytest
import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# sensordata_plotter.py is now in emg_util/ (same as parent directory)
# No additional path setup needed since parent is already in sys.path

import emg_util as core
import emg_util_yaml_runner as runner
import capture_loader as loader
import fatigue_monitor as fm


# Test data location
REGRESSION_DATA_DIR = Path(__file__).parent.parent / "regression_testlogs"
REGRESSION_OUTPUT_DIR = Path(__file__).parent.parent / "tests" / "regression_output"


@pytest.fixture(scope="module")
def regression_data():
    """Load regression test data once for all tests."""
    if not REGRESSION_DATA_DIR.exists():
        pytest.skip(f"Regression data not found: {REGRESSION_DATA_DIR}")
    
    # Create output directory
    REGRESSION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    return {
        "data_dir": REGRESSION_DATA_DIR,
        "output_dir": REGRESSION_OUTPUT_DIR,
    }


@pytest.fixture(scope="module")
def loaded_session(regression_data):
    """Load a complete session for testing."""
    data_dir = regression_data["data_dir"]
    
    # Discover sessions first
    sessions = loader.discover_sessions(str(data_dir))
    
    # Load session data using load_session_stitched
    emg_df, imu_df, reconnection_times, capture_ids = loader.load_session_stitched(sessions)
    
    # Create metadata (infer from data)
    emg_meta = {"fs_hz": 2000}  # Known EMG sampling rate
    imu_meta = {"fs_hz": 200}   # Known IMU sampling rate
    
    return {
        "emg_df": emg_df,
        "emg_meta": emg_meta,
        "imu_df": imu_df,
        "imu_meta": imu_meta,
    }


# ============================================================================
# Test 1: Data Loading & Integrity
# ============================================================================

@pytest.mark.data_loading
@pytest.mark.fast
class TestDataLoading:
    """Test data loading functions."""
    
    def test_emg_files_exist(self, regression_data):
        """Verify EMG log files exist."""
        data_dir = regression_data["data_dir"]
        emg_files = list(data_dir.glob("emg_log_*.csv"))
        assert len(emg_files) > 0, "No EMG CSV files found"
        
    def test_imu_files_exist(self, regression_data):
        """Verify IMU log files exist."""
        data_dir = regression_data["data_dir"]
        imu_files = list(data_dir.glob("imu_log_*.csv"))
        assert len(imu_files) > 0, "No IMU CSV files found"
    
    def test_load_emg_session(self, loaded_session):
        """Test EMG session loading."""
        emg_df = loaded_session["emg_df"]
        emg_meta = loaded_session["emg_meta"]
        
        # Check DataFrame structure
        assert isinstance(emg_df, pd.DataFrame)
        assert len(emg_df) > 0, "EMG DataFrame is empty"
        assert "ts_ms" in emg_df.columns
        assert "raw" in emg_df.columns
        
        # Check metadata
        assert isinstance(emg_meta, dict)
        assert "fs_hz" in emg_meta
        assert emg_meta["fs_hz"] == 2000, "Expected 2000 Hz sampling rate"
    
    def test_load_imu_session(self, loaded_session):
        """Test IMU session loading."""
        imu_df = loaded_session["imu_df"]
        imu_meta = loaded_session["imu_meta"]
        
        # Check DataFrame structure
        assert isinstance(imu_df, pd.DataFrame)
        assert len(imu_df) > 0, "IMU DataFrame is empty"
        assert "ts_ms" in imu_df.columns
        assert all(col in imu_df.columns for col in ["ax", "ay", "az", "gx", "gy", "gz"])
        
        # Check metadata
        assert isinstance(imu_meta, dict)
        assert "fs_hz" in imu_meta


# ============================================================================
# Test 2: Signal Processing
# ============================================================================

@pytest.mark.signal_processing
@pytest.mark.fast
class TestSignalProcessing:
    """Test core signal processing functions."""
    
    def test_preprocess_emg(self, loaded_session):
        """Test EMG preprocessing (bandpass + notch + detrend)."""
        emg_df = loaded_session["emg_df"]
        fs = loaded_session["emg_meta"]["fs_hz"]
        
        # Get a segment of raw EMG
        raw = emg_df["raw"].values[:10000]  # 5 seconds
        
        # Preprocess
        processed = fm.preprocess_emg(raw, fs=fs)
        
        # Verify output
        assert processed.shape == raw.shape
        assert not np.any(np.isnan(processed)), "NaN values in processed signal"
        assert not np.any(np.isinf(processed)), "Inf values in processed signal"
        
        # Verify filtering reduced noise (std should be lower)
        assert np.std(processed) < np.std(raw), "Preprocessing should reduce noise"
    
    def test_envelope(self, loaded_session):
        """Test EMG envelope extraction."""
        emg_df = loaded_session["emg_df"]
        fs = loaded_session["emg_meta"]["fs_hz"]
        
        # Get processed EMG
        raw = emg_df["raw"].values[:10000]
        processed = fm.preprocess_emg(raw, fs=fs)
        
        # Compute envelope
        env = core.envelope(processed, fs=fs, cutoff_hz=3.6)
        
        # Verify output
        assert env.shape == processed.shape
        assert not np.any(np.isnan(env)), "NaN values in envelope"
        assert np.all(env >= 0), "Envelope should be non-negative"
        assert np.mean(env) < np.mean(np.abs(processed)), "Envelope should smooth signal"
    
    def test_mdf_computation(self, loaded_session):
        """Test MDF (Median Frequency) computation."""
        emg_df = loaded_session["emg_df"]
        fs = loaded_session["emg_meta"]["fs_hz"]
        
        # Get a swing-length segment
        raw = emg_df["raw"].values[:2600]  # 1.3 seconds @ 2000 Hz
        processed = fm.preprocess_emg(raw, fs=fs)
        
        # Compute MDF
        mnf, mdf = core.mnf_mdf(processed, fs=fs)
        
        # Verify output
        assert isinstance(mdf, (int, float))
        assert isinstance(mnf, (int, float))
        assert 20 < mdf < 450, f"MDF {mdf} Hz outside expected range (20-450 Hz)"
        assert 20 < mnf < 450, f"MNF {mnf} Hz outside expected range (20-450 Hz)"
    
    def test_emg_features(self, loaded_session):
        """Test classic EMG features (MAV, RMS, WL, ZC, SSC)."""
        emg_df = loaded_session["emg_df"]
        fs = loaded_session["emg_meta"]["fs_hz"]
        
        # Get a segment
        raw = emg_df["raw"].values[:2600]
        processed = fm.preprocess_emg(raw, fs=fs)
        
        # Compute features
        mav = core.feat_mav(processed)
        rms = core.feat_rms(processed)
        wl = core.feat_wl(processed)
        zc = core.feat_zc(processed, thr=0.01)
        ssc = core.feat_ssc(processed, thr=0.01)
        
        # Verify outputs
        assert mav > 0, "MAV should be positive"
        assert rms > 0, "RMS should be positive"
        assert wl > 0, "WL should be positive"
        assert zc >= 0, "ZC should be non-negative"
        assert ssc >= 0, "SSC should be non-negative"
        assert rms >= mav, "RMS should be >= MAV"


# ============================================================================
# Test 3: Swing Detection
# ============================================================================

@pytest.mark.swing_detection
@pytest.mark.slow
class TestSwingDetection:
    """Test swing detection algorithms."""
    
    def test_detect_swings_from_imu(self, loaded_session):
        """Test IMU-based swing detection."""
        imu_df = loaded_session["imu_df"]
        
        # Detect swings (returns DataFrame)
        swings_df = core.detect_swing_windows_from_imu(
            imu_df,
            baseline_s=2.0,
            z_thr=5.0,
            min_consec=3,
            min_gap_ms=300.0,
            pre_ms=250.0,
            post_ms=450.0,
        )
        
        # Verify output
        assert isinstance(swings_df, pd.DataFrame)
        assert len(swings_df) > 0, "Should detect at least one swing"
        
        # Check DataFrame structure
        assert "swing_id" in swings_df.columns
        assert "t_peak_ms" in swings_df.columns
        assert "t_start_ms" in swings_df.columns
        assert "t_end_ms" in swings_df.columns
    
    def test_swing_detection_consistency(self, loaded_session):
        """Test that swing detection is deterministic."""
        imu_df = loaded_session["imu_df"]
        
        # Detect swings twice
        swings1 = core.detect_swing_windows_from_imu(imu_df)
        swings2 = core.detect_swing_windows_from_imu(imu_df)
        
        # Should be identical
        assert len(swings1) == len(swings2)
        assert swings1["t_peak_ms"].equals(swings2["t_peak_ms"])
        assert swings1["t_start_ms"].equals(swings2["t_start_ms"])
        assert swings1["t_end_ms"].equals(swings2["t_end_ms"])


# ============================================================================
# Test 4: Fatigue Analysis
# ============================================================================

@pytest.mark.fatigue
@pytest.mark.slow
class TestFatigueAnalysis:
    """Test fatigue monitoring and analysis."""
    
    def test_fatigue_monitor_initialization(self):
        """Test FatigueMonitor initialization."""
        monitor = fm.FatigueMonitor(
            fs=2000,
            warmup_skip_min=0,  # No warmup for testing
            baseline_swings=5,
        )
        
        # Get summary to verify initialization
        summary = monitor.get_summary()
        assert summary is not None
        assert isinstance(summary, dict)
    
    def test_fatigue_monitor_baseline_collection(self, loaded_session):
        """Test baseline collection in FatigueMonitor."""
        emg_df = loaded_session["emg_df"]
        imu_df = loaded_session["imu_df"]
        
        # Detect swings (returns DataFrame)
        swings_df = core.detect_swing_windows_from_imu(imu_df)
        
        if len(swings_df) < 5:
            pytest.skip("Not enough swings for baseline test")
        
        # Initialize monitor
        monitor = fm.FatigueMonitor(fs=2000, warmup_skip_min=0, baseline_swings=5)
        
        # Process first 5 swings
        for i in range(min(5, len(swings_df))):
            swing = swings_df.iloc[i]
            
            # Extract EMG window
            t_start_ms = swing["t_start_ms"]
            t_end_ms = swing["t_end_ms"]
            emg_window = emg_df[
                (emg_df["ts_ms"] >= t_start_ms) & (emg_df["ts_ms"] < t_end_ms)
            ]["raw"].values
            
            if len(emg_window) < 2000:
                continue
            
            result = monitor.push_swing(
                emg_window[:2600],
                t_peak_ms=swing["t_peak_ms"],
                imu_peak_mag=swing.get("peak_mag", 200.0),
            )
            
            # Check result structure
            assert "swing_id" in result
            assert "mdf" in result
            assert "fatigue_level" in result
            
            # First 4 should be warming up
            if i < 4:
                assert result["fatigue_level"] == "warming_up"
            else:
                # 5th swing should have baseline ready
                assert result["baseline_ready"] == True
    
    def test_baseline_selection(self, loaded_session):
        """Test baseline swing selection."""
        imu_df = loaded_session["imu_df"]
        
        # Detect swings (returns DataFrame)
        swings_df = core.detect_swing_windows_from_imu(imu_df)
        
        if len(swings_df) < 20:
            pytest.skip("Not enough swings for baseline selection test")
        
        # Get session start time
        session_t0_ms = imu_df["ts_ms"].min()
        
        # Select baseline swings (takes DataFrame, returns DataFrame)
        baseline_df = core.select_baseline_swings(
            swings_df,
            session_t0_ms=session_t0_ms,
            warmup_skip_min=0,
            baseline_swings=10,
        )
        
        # Verify output
        assert isinstance(baseline_df, pd.DataFrame)
        assert len(baseline_df) <= 10
        assert len(baseline_df) > 0


# ============================================================================
# Test 5: Full Pipeline Integration
# ============================================================================

@pytest.mark.pipeline
@pytest.mark.slow
class TestFullPipeline:
    """Test complete analysis pipeline."""
    
    def test_analyze_tennis_session(self, regression_data):
        """Test full session analysis pipeline."""
        data_dir = regression_data["data_dir"]
        output_dir = regression_data["output_dir"]
        
        # Create minimal config
        config = {
            "session": {
                "emg_glob": "emg_log_*.csv",
                "imu_glob": "imu_log_*.csv",
                "emg_fs_hz": 2000,
                "imu_fs_fallback_hz": 200,
                "use_physical_units": True,
                "out_dir": str(output_dir),
            },
            "features": {
                "mode": "medium",  # Fast mode for testing
            },
            "swing_detection": {
                "use_gyro": True,
                "z_thr": 5.0,
            },
            "baseline": {
                "mode": "swing",
                "warmup_skip_min": 0,
                "baseline_swings": 10,
            },
            "plots": {
                "enable": False,  # Skip plots for speed
            },
            "diagnostics": {
                "emg_imu_correlation": {"enable": False},
                "activity_overlay": {"enable": False},
            },
            "health": {
                "enable": False,  # Skip health check for speed
            },
        }
        
        # Run analysis
        try:
            result_dir = runner.analyze_tennis_session(
                str(data_dir),
                config,
                str(output_dir),
            )
            
            # Verify outputs exist
            assert Path(result_dir).exists()
            assert (Path(result_dir) / "session_summary.json").exists()
            assert (Path(result_dir) / "swing_windows.csv").exists()
            
            # Load and verify session summary
            with open(Path(result_dir) / "session_summary.json") as f:
                summary = json.load(f)
            
            assert "num_swings" in summary
            assert "total_duration_min" in summary
            assert summary["num_swings"] > 0
            
        except Exception as e:
            pytest.fail(f"Full pipeline test failed: {e}")


# ============================================================================
# Test 6: Regression Baselines
# ============================================================================

@pytest.mark.baseline
@pytest.mark.slow
class TestRegressionBaselines:
    """Test against known baseline values to catch regressions."""
    
    def test_swing_count_baseline(self, loaded_session):
        """Test that swing count is consistent with baseline."""
        imu_df = loaded_session["imu_df"]
        
        # Detect swings (returns DataFrame)
        swings_df = core.detect_swing_windows_from_imu(imu_df)
        
        # Expected range based on regression data
        # (Update these values after establishing baseline)
        MIN_EXPECTED_SWINGS = 5
        MAX_EXPECTED_SWINGS = 1000
        
        assert MIN_EXPECTED_SWINGS <= len(swings_df) <= MAX_EXPECTED_SWINGS, \
            f"Swing count {len(swings_df)} outside expected range"
    
    def test_mdf_range_baseline(self, loaded_session):
        """Test that MDF values are in expected range."""
        emg_df = loaded_session["emg_df"]
        
        # Sample multiple windows
        mdf_values = []
        for i in range(0, len(emg_df) - 2600, 5000):
            raw = emg_df["raw"].values[i:i+2600]
            if len(raw) < 2600:
                continue
            processed = fm.preprocess_emg(raw, fs=2000)
            _, mdf = core.mnf_mdf(processed, fs=2000)
            mdf_values.append(mdf)
        
        if len(mdf_values) == 0:
            pytest.skip("No MDF values computed")
        
        # Check range
        mean_mdf = np.mean(mdf_values)
        assert 50 < mean_mdf < 300, f"Mean MDF {mean_mdf} Hz outside expected range"


# ============================================================================
# Test 7: Error Handling
# ============================================================================

@pytest.mark.error_handling
@pytest.mark.fast
class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_empty_signal(self):
        """Test handling of empty signal."""
        # Empty signal should either raise error or return empty
        try:
            result = fm.preprocess_emg(np.array([]), fs=2000)
            assert len(result) == 0, "Empty input should return empty output"
        except (ValueError, IndexError):
            pass  # Expected - empty signal not supported
    
    def test_short_signal(self):
        """Test handling of very short signal."""
        short_signal = np.random.randn(100)
        # Should either work or raise clear error
        try:
            result = fm.preprocess_emg(short_signal, fs=2000)
            assert len(result) == len(short_signal)
        except (ValueError, RuntimeError):
            pass  # Expected for very short signals
    
    def test_nan_in_signal(self):
        """Test handling of NaN values."""
        signal_with_nan = np.random.randn(2600)
        signal_with_nan[1000:1100] = np.nan
        
        # Preprocessing with NaN should either handle gracefully or raise error
        try:
            result = fm.preprocess_emg(signal_with_nan, fs=2000)
            # If it succeeds, check if NaNs propagated
            # (Some implementations may propagate NaN, which is acceptable)
            assert len(result) == len(signal_with_nan)
        except (ValueError, RuntimeError):
            pass  # Expected if NaN handling not implemented


# ============================================================================
# Test 8: Plotter Offline Mode (sensordata_plotter.py)
# ============================================================================

@pytest.mark.plotter
@pytest.mark.fast
class TestPlotterOffline:
    """Test sensordata_plotter.py offline mode with regression data."""
    
    def test_plotter_import(self):
        """Test that sensordata_plotter.py can be imported."""
        try:
            import sensordata_plotter
            assert hasattr(sensordata_plotter, 'run_offline')
            assert hasattr(sensordata_plotter, 'ButterLPF')
        except ImportError as e:
            pytest.skip(f"sensordata_plotter not available: {e}")
    
    def test_butter_lpf_initialization(self):
        """Test ButterLPF filter initialization."""
        try:
            from sensordata_plotter import ButterLPF
        except ImportError:
            pytest.skip("sensordata_plotter not available")
        
        # Initialize filter
        lpf = ButterLPF(fs_hz=2000.0, cutoff_hz=3.6)
        
        assert lpf.fs_hz == 2000.0
        assert lpf.cutoff_hz == 3.6
        assert lpf.b is not None
        assert lpf.a is not None
        assert lpf.zi is not None
    
    def test_butter_lpf_filtering(self):
        """Test ButterLPF filter operation."""
        try:
            from sensordata_plotter import ButterLPF
        except ImportError:
            pytest.skip("sensordata_plotter not available")
        
        lpf = ButterLPF(fs_hz=2000.0, cutoff_hz=3.6)
        
        # Test with synthetic signal
        signal = np.sin(2 * np.pi * 10 * np.linspace(0, 1, 2000))  # 10 Hz sine
        filtered = [lpf.update(x) for x in signal]
        
        # Verify output
        assert len(filtered) == len(signal)
        assert all(not np.isnan(f) for f in filtered)
        assert all(not np.isinf(f) for f in filtered)
        
        # Filtered signal should be smoother (lower std)
        assert np.std(filtered) < np.std(signal)
    
    def test_plotter_with_regression_data(self, regression_data):
        """Test plotter can process regression EMG data."""
        try:
            from sensordata_plotter import ButterLPF
        except ImportError:
            pytest.skip("sensordata_plotter not available")
        
        data_dir = regression_data["data_dir"]
        
        # Find first EMG CSV file
        emg_files = sorted(data_dir.glob("emg_log_*.csv"))
        if not emg_files:
            pytest.skip("No EMG files found")
        
        emg_file = emg_files[0]
        
        # Read EMG data
        import csv
        t_ms, raw_values = [], []
        with open(emg_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    t = int(row.get('host_rx_ms', '0'))
                    r = float(row.get('raw', 'nan'))
                    if not np.isnan(r):
                        t_ms.append(t)
                        raw_values.append(r)
                except (ValueError, KeyError):
                    continue
                
                # Limit to first 10000 samples for speed
                if len(raw_values) >= 10000:
                    break
        
        if len(raw_values) < 100:
            pytest.skip("Not enough valid EMG samples")
        
        # Process with LPF (same as plotter does)
        lpf = ButterLPF(fs_hz=2000.0, cutoff_hz=3.6)
        env_lpf = [lpf.update(abs(r)) for r in raw_values]
        
        # Verify output
        assert len(env_lpf) == len(raw_values)
        assert all(not np.isnan(e) for e in env_lpf)
        assert all(e >= 0 for e in env_lpf), "Envelope should be non-negative"
        
        # Envelope should be smoother than raw
        assert np.std(env_lpf) < np.std(np.abs(raw_values))
    
    def test_plotter_fatigue_integration(self, regression_data):
        """Test plotter's fatigue monitoring integration."""
        try:
            from fatigue_monitor import FatigueMonitor
            
            # Initialize monitor (same as plotter does)
            monitor = FatigueMonitor(
                fs=2000.0,
                warmup_skip_min=0.0,
                baseline_swings=5,
            )
            
            # Verify monitor can be used
            summary = monitor.get_summary()
            assert summary is not None
            assert isinstance(summary, dict)
            
        except ImportError:
            pytest.skip("FatigueMonitor not available")
    
    def test_plotter_swing_detection_logic(self):
        """Test plotter's gyro-based swing detection logic."""
        # Simulate gyro magnitude data
        imu_thr_dps = 150.0
        
        # Test data: below threshold, peak, below threshold
        gyro_mags = [50, 100, 180, 200, 180, 100, 50]  # Peak at index 3
        
        # Simulate peak detection (same logic as plotter)
        in_peak = False
        peak_gyro_mag = 0.0
        peak_index = -1
        detected_peaks = []
        
        for i, gmag in enumerate(gyro_mags):
            if gmag >= imu_thr_dps:
                if not in_peak:
                    # Start of new peak
                    in_peak = True
                    peak_gyro_mag = gmag
                    peak_index = i
                else:
                    # Update if higher
                    if gmag > peak_gyro_mag:
                        peak_gyro_mag = gmag
                        peak_index = i
            elif in_peak:
                # End of peak - record it
                detected_peaks.append((peak_index, peak_gyro_mag))
                in_peak = False
                peak_gyro_mag = 0.0
        
        # Should detect exactly one peak at the highest point
        assert len(detected_peaks) == 1
        assert detected_peaks[0][0] == 3  # Peak at index 3
        assert detected_peaks[0][1] == 200.0  # Peak magnitude


# ============================================================================
# Test Runner Configuration
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
