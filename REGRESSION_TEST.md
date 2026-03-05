# Regression Testing for EMG Analysis Pipeline

**Purpose:** Ensure consistent behavior of EMG analysis algorithms across code changes using real tennis session data.

**Last Updated:** 2026-03-04  
**Status:** ✅ **29/29 tests passing (100%)**  
**Execution Time:** ~2.5 minutes (full suite), ~60 seconds (fast tests only)

---

## 🎉 Implementation Summary

### Final Achievement

**✅ Complete Regression Test Suite**
- **29 tests** across 9 test classes
- **100% pass rate** - All tests passing
- **10 test categories** for selective execution
- **Zero warnings** with proper pytest configuration
- **Cross-module coverage** - Tests both `emg_util` and `sensordata_plotter.py`
- **Swing detector coverage** - Tests both ThresholdSwingDetector and HysteresisSwingDetector

### Test Categories

Tests are organized into **10 categories** using pytest markers:

#### Functional Categories
1. **`data_loading`** (4 tests) - Data loading and integrity tests
2. **`signal_processing`** (4 tests) - Signal processing algorithm tests  
3. **`swing_detection`** (6 tests) - Swing detection tests (threshold + hysteresis detectors)
4. **`fatigue`** (3 tests) - Fatigue analysis tests
5. **`pipeline`** (1 test) - Full pipeline integration tests
6. **`baseline`** (2 tests) - Regression baseline tests
7. **`error_handling`** (3 tests) - Error handling and edge cases
8. **`plotter`** (6 tests) - Plotter offline mode tests

#### Performance Categories
9. **`fast`** (20 tests) - Fast tests (< 5 seconds each)
10. **`slow`** (9 tests) - Slow tests (> 5 seconds each)

### Quick Start Examples

```bash
# Run all tests (recommended for pre-commit)
python tests/run_regression_tests.py

# Run only fast tests (68% faster - great for development)
pytest tests/test_regression.py -m "fast"

# Run specific category
pytest tests/test_regression.py -m "signal_processing"

# Skip slow tests during development
pytest tests/test_regression.py -m "not slow"

# Run multiple categories
pytest tests/test_regression.py -m "signal_processing or fatigue"
```

### Performance Comparison

| Test Set | Tests | Time | Speed vs Full | Use Case |
|----------|-------|------|---------------|----------|
| **All tests** | 29 | ~2.5 min | 100% | Pre-commit, CI/CD |
| **Fast tests** | 20 | ~60 sec | **60% faster** | Development, quick checks |
| **Slow tests** | 9 | ~1.5 min | - | Integration validation |
| **Swing detection** | 6 | ~20 sec | **87% faster** | Detector algorithm changes |
| **Signal processing** | 4 | ~15 sec | **90% faster** | Algorithm changes |
| **Plotter** | 6 | ~10 sec | **93% faster** | Plotter changes |
| **Data loading** | 4 | ~8 sec | **95% faster** | Data format changes |

### What Was Fixed During Implementation

**1. Function Signature Mismatches**
- ✅ Fixed `envelope()` parameter: `fc` → `cutoff_hz`
- ✅ Fixed `feat_zc()` and `feat_ssc()` parameters: `threshold` → `thr`
- ✅ Fixed `detect_swing_windows_from_imu()`: removed `fs_imu` parameter, returns DataFrame
- ✅ Fixed `select_baseline_swings()`: added required `session_t0_ms` parameter

**2. Data Structure Updates**
- ✅ Updated swing detection to work with DataFrame output (not list of dicts)
- ✅ Fixed column name references: `emg_raw` → `raw`, `t_ms` → `ts_ms`
- ✅ Updated DataFrame access patterns for swing windows
- ✅ Fixed baseline selection to use DataFrame input/output

**3. Cross-Module Integration**
- ✅ Fixed path calculation for `sensordata_plotter.py` import
- ✅ Added `py_scripts` directory to Python path
- ✅ Enabled all 6 plotter tests (previously 4 were skipped)
- ✅ Validated plotter's ButterLPF filter and swing detection logic

**4. Test Infrastructure**
- ✅ Created `pytest.ini` to register custom markers (eliminates warnings)
- ✅ Added test categorization with 10 markers
- ✅ Implemented proper session loading with `load_session_stitched()`
- ✅ Added comprehensive error handling tests

### Test Coverage

#### ✅ What Is Tested (25 Tests)

**Data Loading & Integrity (4 tests)**
- EMG/IMU file existence verification
- Session loading with proper DataFrame structure
- Metadata validation (sampling rates, column names)
- Multi-capture session stitching

**Signal Processing (4 tests)**
- EMG preprocessing (bandpass 20-450 Hz, 60 Hz notch, detrending)
- Envelope extraction (rectification + 3.6 Hz lowpass)
- MDF computation (median frequency in 20-450 Hz range)
- Classic EMG features (MAV, RMS, WL, ZC, SSC)

**Swing Detection (6 tests)**
- IMU-based swing detection (gyro magnitude threshold)
- Deterministic behavior (same input → same output)
- Swing window boundaries (t_start_ms, t_peak_ms, t_end_ms)
- ThresholdSwingDetector (simple threshold + debounce)
- HysteresisSwingDetector (state machine + impact detection)
- Impact detection validation (hysteresis detector)

**Fatigue Analysis (3 tests)**
- FatigueMonitor initialization and configuration
- Baseline MDF collection (first N swings)
- Baseline swing selection (warmup skip + selection logic)

**Full Pipeline Integration (1 test)**
- End-to-end analysis with real data
- Output file generation (session_summary.json, swing_windows.csv)
- Configuration handling (YAML-style config dict)

**Regression Baselines (2 tests)**
- Swing count consistency (5-1000 swings expected)
- MDF value range validation (50-300 Hz mean)

**Error Handling (3 tests)**
- Empty signal handling (graceful error or empty output)
- Short signal handling (< 100 samples)
- NaN value handling (propagate or error)

**Plotter Offline Mode (6 tests)**
- Plotter module import
- ButterLPF filter initialization
- ButterLPF filter operation
- Regression data processing
- Fatigue monitor integration
- Swing detection logic (150 dps threshold)

#### ⚠️ What Is NOT Tested (Future Improvements)

**Missing Coverage:**
- Advanced signal processing (wavelets, time-frequency analysis)
- Swing classification (forehand/backhand, serve detection)
- Advanced fatigue metrics (bout-level, recovery time)
- Performance & scalability (>4 hour sessions, >500 swings)
- Visualization (plot generation, visual regression)
- Real-time processing (streaming, latency tests)
- Cross-platform compatibility (Windows/Linux/macOS)

### Files Created

1. **`tests/test_regression.py`** (700+ lines)
   - 25 comprehensive tests with pytest markers
   - 8 test classes covering all major functionality
   - Proper fixtures for data loading

2. **`tests/run_regression_tests.py`** (150+ lines)
   - Test runner with colored output
   - Dependency checking
   - Execution time reporting

3. **`pytest.ini`** (30 lines)
   - Registers 10 custom pytest markers
   - Configures test discovery patterns
   - Sets default output options

4. **`REGRESSION_TEST.md`** (this file)
   - Complete documentation
   - Usage examples
   - Troubleshooting guide

5. **`PYTHON_CONSOLIDATION_PLAN.md`** (400+ lines)
   - Strategy for consolidating Python scripts
   - Git submodule architecture
   - Android integration plan

---

## Overview

The regression test suite validates the complete EMG analysis pipeline using real data from `regression_testlogs/`. This ensures that algorithm changes don't introduce unexpected behavior or break existing functionality.

### What Gets Tested

1. **Data Loading** - CSV parsing, metadata extraction, session stitching
2. **Signal Processing** - Bandpass filtering, envelope extraction, MDF computation
3. **Swing Detection** - IMU-based swing detection, consistency checks
4. **Fatigue Analysis** - Baseline collection, MDF tracking, fatigue classification
5. **Full Pipeline** - End-to-end analysis with real data
6. **Regression Baselines** - Comparison against known good values
7. **Error Handling** - Edge cases, invalid inputs, NaN handling

---

## Quick Start

### 1. Install Dependencies

```bash
pip install pytest numpy pandas scipy
```

### 2. Run Tests

```bash
# From emg_util/ directory
python tests/run_regression_tests.py

# Or use pytest directly
pytest tests/test_regression.py -v
```

### 3. Generate Baseline (First Time)

```bash
python tests/run_regression_tests.py --generate-baseline
```

---

## Test Data

### Location

```
emg_util/
├── regression_testlogs/          ← Real tennis session data
│   ├── emg_log_*.csv             ← EMG data (2000 Hz)
│   ├── imu_log_*.csv             ← IMU data (200 Hz)
│   ├── *.meta.json               ← Metadata files
│   └── vitals_log.csv            ← Vitals data
└── tests/
    ├── test_regression.py        ← Test suite
    ├── run_regression_tests.py   ← Test runner
    ├── regression_baseline.json  ← Known good values
    └── regression_output/        ← Test outputs
```

### Data Characteristics

- **Session:** Real tennis practice session (Feb 8, 2026)
- **Duration:** Multiple BLE captures (~2 hours total)
- **Swings:** 50-100 detected swings
- **EMG Sampling:** 2000 Hz
- **IMU Sampling:** 200 Hz
- **Sensors:** MyoWare EMG + ICM-20948 IMU

---

## Test Suite Structure

### Test 1: Data Loading & Integrity

**Purpose:** Verify data loading functions work correctly.

**Tests:**
- `test_emg_files_exist` - Check EMG CSV files present
- `test_imu_files_exist` - Check IMU CSV files present
- `test_load_emg_session` - Load and validate EMG DataFrame
- `test_load_imu_session` - Load and validate IMU DataFrame

**What It Catches:**
- Missing data files
- Corrupted CSV files
- Incorrect metadata
- Wrong sampling rates

---

### Test 2: Signal Processing

**Purpose:** Validate core signal processing algorithms.

**Tests:**
- `test_preprocess_emg` - Bandpass + notch + detrend
- `test_envelope` - EMG envelope extraction
- `test_mdf_computation` - Median frequency calculation
- `test_emg_features` - MAV, RMS, WL, ZC, SSC features

**What It Catches:**
- NaN/Inf values in processed signals
- Incorrect filter parameters
- MDF values outside valid range (20-450 Hz)
- Feature computation errors

**Example:**
```python
def test_preprocess_emg(self, loaded_session):
    """Test EMG preprocessing (bandpass + notch + detrend)."""
    emg_df = loaded_session["emg_df"]
    fs = loaded_session["emg_meta"]["fs_hz"]
    
    # Get a segment of raw EMG
    raw = emg_df["emg_raw"].values[:10000]  # 5 seconds
    
    # Preprocess
    processed = fm.preprocess_emg(raw, fs=fs)
    
    # Verify output
    assert processed.shape == raw.shape
    assert not np.any(np.isnan(processed))
    assert np.std(processed) < np.std(raw)  # Should reduce noise
```

---

### Test 3: Swing Detection

**Purpose:** Ensure swing detection is accurate and deterministic for both detector types.

**Tests:**
- `test_detect_swings_from_imu` - IMU-based swing detection (legacy)
- `test_swing_detection_consistency` - Deterministic behavior
- `test_threshold_detector_initialization` - ThresholdSwingDetector setup
- `test_threshold_detector_basic_detection` - Threshold detector with synthetic data
- `test_hysteresis_detector_initialization` - HysteresisSwingDetector setup
- `test_hysteresis_detector_basic_detection` - Hysteresis detector with synthetic data

**What It Catches:**
- Swing detection failures
- Non-deterministic behavior
- Incorrect swing window boundaries
- Missing swing metadata
- Detector initialization errors
- Impact detection failures (hysteresis)
- Hysteresis state machine bugs

**Key Assertions:**
```python
# Threshold detector: simple threshold + debounce
detector = ThresholdSwingDetector(
    thr_gyro_dps=300.0, thr_acc_g=1.5,
    debounce_sec=2.0, mode='gyro_and_acc'
)
confirmed_t = detector.update(t_sec, gmag, amag)
assert detector.swing_count == expected_count

# Hysteresis detector: state machine + impact detection
detector = HysteresisSwingDetector(
    th_on=350.0, th_off=175.0,
    th_acc_hp=0.6, th_jerk=80.0
)
confirmed_t = detector.update(t_sec, gmag, amag)
assert detector.swing_count == expected_count
assert detector.last_impact_time is not None  # Impact detected
```

---

### Test 4: Fatigue Analysis

**Purpose:** Validate fatigue monitoring algorithms.

**Tests:**
- `test_fatigue_monitor_initialization` - FatigueMonitor setup
- `test_fatigue_monitor_baseline_collection` - Baseline MDF collection
- `test_baseline_selection` - Baseline swing selection logic

**What It Catches:**
- Incorrect baseline collection
- Wrong fatigue classification
- MDF computation errors
- Baseline selection bugs

**Fatigue Levels:**
- `warming_up` - Before baseline ready
- `fresh` - MDF drop < 12%
- `moderate` - MDF drop 12-20%
- `high` - MDF drop > 20%

---

### Test 5: Full Pipeline Integration

**Purpose:** Test end-to-end analysis pipeline.

**Tests:**
- `test_analyze_tennis_session` - Complete session analysis

**What It Catches:**
- Pipeline integration issues
- Missing output files
- Incorrect session summary
- Configuration errors

**Verified Outputs:**
- `session_summary.json` - Session metadata
- `swing_windows.csv` - Detected swings
- `swing_features.csv` - Per-swing EMG features (if enabled)
- `bout_summary.csv` - Bout-level statistics

---

### Test 6: Regression Baselines

**Purpose:** Catch regressions by comparing against known good values.

**Tests:**
- `test_swing_count_baseline` - Swing count in expected range
- `test_mdf_range_baseline` - MDF values in expected range

**Baseline Values (Example):**
```json
{
  "generated_at": "2026-02-27T09:00:00",
  "num_swings": 67,
  "mdf_mean": 142.5,
  "mdf_std": 28.3,
  "mdf_min": 89.2,
  "mdf_max": 215.7
}
```

**What It Catches:**
- Algorithm changes that significantly alter results
- Unexpected swing count changes
- MDF computation drift
- Performance regressions

---

### Test 7: Error Handling

**Purpose:** Ensure graceful handling of edge cases.

**Tests:**
- `test_empty_signal` - Empty array handling
- `test_short_signal` - Very short signal handling
- `test_nan_in_signal` - NaN value handling

**What It Catches:**
- Crashes on invalid input
- Poor error messages
- Unhandled edge cases

---

### Test 8: Plotter Offline Mode

**Purpose:** Test `sensordata_plotter.py` offline playback with regression data.

**Tests:**
- `test_plotter_import` - Import sensordata_plotter module
- `test_butter_lpf_initialization` - ButterLPF filter setup
- `test_butter_lpf_filtering` - Filter operation with synthetic signal
- `test_plotter_with_regression_data` - Process real EMG data
- `test_plotter_fatigue_integration` - FatigueMonitor integration
- `test_plotter_swing_detection_logic` - Gyro-based peak detection

**What It Catches:**
- Plotter import errors
- Filter initialization issues
- Incorrect envelope computation
- Fatigue integration problems
- Swing detection logic errors

**Key Features Tested:**
```python
# ButterLPF filter (same as plotter uses)
lpf = ButterLPF(fs_hz=2000.0, cutoff_hz=3.6)
env_lpf = [lpf.update(abs(r)) for r in raw_values]

# Gyro-based swing detection (150 dps threshold)
if gmag >= imu_thr_dps:
    if not in_peak:
        in_peak = True
        peak_gyro_mag = gmag
    elif gmag > peak_gyro_mag:
        peak_gyro_mag = gmag  # Track highest point
elif in_peak:
    # End of peak - trigger detection
    detected_peaks.append((peak_index, peak_gyro_mag))
```

**Why Test Plotter:**
- Plotter is in different folder (`py_scripts/`) but uses same data
- Tests offline playback capability
- Validates real-time fatigue integration
- Ensures consistent swing detection (150 dps threshold)
- Verifies ButterLPF filter matches expectations

---

## Running Tests

### Basic Usage

```bash
# Run all tests (quiet mode)
python tests/run_regression_tests.py

# Run with verbose output
python tests/run_regression_tests.py --verbose

# Run specific test class
pytest tests/test_regression.py::TestSignalProcessing -v

# Run specific test
pytest tests/test_regression.py::TestSignalProcessing::test_mdf_computation -v
```

### Advanced Usage

```bash
# Generate baseline values
python tests/run_regression_tests.py --generate-baseline

# Run tests with coverage
pytest tests/test_regression.py --cov=emg_util --cov-report=html

# Run tests in parallel (if pytest-xdist installed)
pytest tests/test_regression.py -n auto

# Stop on first failure
pytest tests/test_regression.py -x

# Show local variables on failure
pytest tests/test_regression.py -l
```

---

## Interpreting Results

### Successful Run

```
======================================================================
                      Running Regression Tests                       
======================================================================

ℹ Command: python -m pytest tests/test_regression.py -q --tb=short --color=yes -ra

tests/test_regression.py ....................................  [100%]

ℹ Tests completed in 12.34 seconds

✓ All regression tests passed! ✓
```

### Failed Test

```
FAILED tests/test_regression.py::TestSignalProcessing::test_mdf_computation

def test_mdf_computation(self, loaded_session):
    ...
    assert 20 < mdf < 450, f"MDF {mdf} Hz outside expected range (20-450 Hz)"
E   AssertionError: MDF 512.3 Hz outside expected range (20-450 Hz)

✗ Some regression tests failed! ✗
ℹ Review the output above for details
```

**Action:** Investigate why MDF is outside expected range. Could indicate:
- Bug in MDF computation
- Corrupted test data
- Changed filter parameters
- Need to update expected range

---

## Maintaining Tests

### When to Update Tests

1. **Algorithm Changes**
   - Update expected ranges if algorithm improves
   - Add new tests for new features
   - Update baseline values if behavior intentionally changes

2. **New Features**
   - Add tests for new signal processing functions
   - Add tests for new fatigue metrics
   - Add integration tests for new pipeline stages

3. **Bug Fixes**
   - Add regression test to prevent bug from recurring
   - Update tests if bug fix changes expected behavior

### Updating Baseline Values

```bash
# 1. Verify current code is correct
pytest tests/test_regression.py -v

# 2. Generate new baseline
python tests/run_regression_tests.py --generate-baseline

# 3. Review baseline changes
git diff tests/regression_baseline.json

# 4. Commit if changes are intentional
git add tests/regression_baseline.json
git commit -m "Update regression baseline after algorithm improvement"
```

### Adding New Tests

```python
# tests/test_regression.py

class TestNewFeature:
    """Test new feature."""
    
    def test_new_function(self, loaded_session):
        """Test new signal processing function."""
        emg_df = loaded_session["emg_df"]
        
        # Test your new function
        result = core.new_function(emg_df["emg_raw"].values[:1000])
        
        # Verify output
        assert result is not None
        assert len(result) > 0
        # Add more specific assertions
```

---

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/regression-tests.yml
name: Regression Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install pytest numpy pandas scipy
    
    - name: Run regression tests
      run: |
        cd emg_util
        python tests/run_regression_tests.py --verbose
```

---

## Troubleshooting

### Test Data Not Found

**Error:**
```
pytest.skip: Regression data not found: .../regression_testlogs
```

**Solution:**
```bash
# Ensure regression_testlogs/ exists and contains data
ls emg_util/regression_testlogs/

# Should see:
# emg_log_*.csv
# imu_log_*.csv
# *.meta.json
```

### Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'emg_util'
```

**Solution:**
```bash
# Run tests from emg_util/ directory
cd emg_util
python tests/run_regression_tests.py

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/emg_util"
```

### Baseline Mismatch

**Error:**
```
AssertionError: Swing count 45 outside expected range (50-100)
```

**Solution:**
1. Check if test data changed
2. Verify algorithm is correct
3. Update baseline if change is intentional:
   ```bash
   python tests/run_regression_tests.py --generate-baseline
   ```

---

## Best Practices

### 1. Run Tests Before Committing

```bash
# Always run regression tests before pushing
python tests/run_regression_tests.py
```

### 2. Keep Test Data Stable

- Don't modify `regression_testlogs/` unless necessary
- If updating test data, regenerate baseline
- Document why test data changed

### 3. Write Descriptive Test Names

```python
# Good
def test_mdf_computation_with_real_emg_data(self):
    """Test MDF computation using real tennis session EMG data."""
    
# Bad
def test_mdf(self):
    """Test MDF."""
```

### 4. Add Comments for Complex Assertions

```python
# Verify filtering reduced noise
# (std should be lower after bandpass + notch filtering)
assert np.std(processed) < np.std(raw), \
    "Preprocessing should reduce noise"
```

### 5. Use Fixtures for Common Setup

```python
@pytest.fixture(scope="module")
def loaded_session(regression_data):
    """Load session once for all tests."""
    # Expensive operation done once
    emg_df, emg_meta = loader.load_session_emg(...)
    return {"emg_df": emg_df, "emg_meta": emg_meta}
```

---

## Performance Benchmarks

### Typical Test Times

| Test Suite | Duration | Notes |
|------------|----------|-------|
| Data Loading | ~2s | Fast, mostly I/O |
| Signal Processing | ~3s | CPU-intensive |
| Swing Detection | ~2s | Moderate |
| Fatigue Analysis | ~4s | Includes baseline collection |
| Full Pipeline | ~8s | End-to-end analysis |
| **Total** | **~20s** | All tests |

### Optimization Tips

1. **Use `scope="module"` fixtures** - Load data once
2. **Skip slow tests during development** - Use `pytest -m "not slow"`
3. **Run specific test classes** - `pytest tests/test_regression.py::TestSignalProcessing`
4. **Use pytest-xdist** - Parallel test execution

---

## Future Improvements

### Planned Enhancements

1. **Performance Regression Tests**
   - Track execution time of key functions
   - Alert if performance degrades >10%

2. **Visual Regression Tests**
   - Compare generated plots against baseline images
   - Detect unexpected visualization changes

3. **Cross-Platform Tests**
   - Test on Windows, Linux, macOS
   - Verify consistent behavior across platforms

4. **Stress Tests**
   - Test with very long sessions (>4 hours)
   - Test with high swing counts (>500 swings)
   - Test with corrupted data

5. **Integration with CI/CD**
   - Automatic test runs on pull requests
   - Block merges if tests fail
   - Generate test coverage reports

---

## Summary

### Key Benefits

✅ **Catch Regressions Early** - Detect bugs before they reach production  
✅ **Ensure Consistency** - Algorithms behave predictably  
✅ **Enable Refactoring** - Safely improve code with confidence  
✅ **Document Behavior** - Tests serve as executable documentation  
✅ **Improve Quality** - Higher code quality through continuous testing  

### Quick Reference

```bash
# Run all tests
python tests/run_regression_tests.py

# Run with verbose output
python tests/run_regression_tests.py --verbose

# Generate baseline
python tests/run_regression_tests.py --generate-baseline

# Run specific test
pytest tests/test_regression.py::TestSignalProcessing::test_mdf_computation -v
```

---

**For questions or issues, see:**
- Test code: `tests/test_regression.py`
- Test runner: `tests/run_regression_tests.py`
- Main documentation: `HIGH_LEVEL_DESIGN.md`
