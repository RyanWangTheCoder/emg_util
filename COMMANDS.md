# EMG Utility Commands Reference

Quick reference for running Python scripts in the EMG utility package.

**Base Directory:** `C:\wangx\ftc\emg_util`

---

## Table of Contents

- [Data Capture](#data-capture)
- [Real-Time Visualization](#real-time-visualization)
- [Analysis Pipeline](#analysis-pipeline)
- [Offline Analysis](#offline-analysis)
- [Testing](#testing)
- [Utilities](#utilities)

---

## Data Capture

### BLE Central (Data Collection)

Capture EMG and IMU data from MyoWare sensor via BLE:

```bash
# Basic capture with auto-rotation every 20 minutes
python btCentral.py --name MyoW1 --outdir logs_new --rotate-min 20

# With UDP streaming enabled
python btCentral.py --name MyoW1 --outdir logs_new --rotate-min 20 --udp-enable

# Custom BLE device name and output directory
python btCentral.py --name MyCustomDevice --outdir custom_logs --rotate-min 30
```

**Common Options:**
- `--name`: BLE device name to connect to (e.g., MyoW1)
- `--outdir`: Output directory for log files
- `--rotate-min`: Minutes before rotating to new log file
- `--udp-enable`: Enable UDP streaming for real-time visualization

**Output Files:**
- `emg_log_YYYYMMDD_HHMMSS_*.csv` - EMG data
- `imu_log_YYYYMMDD_HHMMSS_*.csv` - IMU data
- `*.meta.json` - Metadata files

---

## Real-Time Visualization

### Live Mode (Real-Time Plotting)

Visualize EMG and IMU data in real-time during capture:

```bash
# Basic live mode with auto sample rate detection
python sensordata_plotter.py --mode live --infer-sr

# Live mode with dynamic RAW signal zoom (highly recommended for resting noise inspection)
python sensordata_plotter.py --mode live --infer-sr --raw-zoom

# Live mode with fatigue monitoring
python sensordata_plotter.py --mode live --fatigue --imu-thr-dps 150 --fatigue-warmup-min 0

# Explicit EMG utility path (if not in default location)
python sensordata_plotter.py --mode live --fatigue --emg-util-path C:\wangx\ftc\emg_util

# Custom UDP port
python sensordata_plotter.py --mode live --udp-port 5005
```

**Common Options:**
- `--mode live`: Enable real-time visualization
- `--infer-sr`: Auto-detect sample rate from incoming data
- `--raw-zoom`: Enable dynamic Y-axis zooming for the RAW signal plot
- `--fatigue`: Enable fatigue monitoring
- `--imu-thr-dps`: IMU threshold in degrees/second for swing detection (default: 150)
- `--fatigue-warmup-min`: Warmup period in minutes before fatigue tracking (default: 0)
- `--emg-util-path`: Path to emg_util directory (default: C:\wangx\ftc\emg_util)
- `--udp-port`: UDP port for receiving data (default: 5005)

**Fatigue Monitoring:**
- Requires `--fatigue` flag
- Uses gyroscope peaks to detect swings
- Tracks MDF (Median Frequency) decline over time
- Displays fatigue level: warming_up → fresh → moderate → high

---

## Analysis Pipeline

### Full Session Analysis

Run complete EMG/IMU analysis pipeline with YAML configuration:

```bash
# Standard analysis with default config
python emg_util_yaml_runner.py --config config.yaml --log-dir ..\arduino\py_scripts\logs_new\

# Fast analysis (reduced features, no plots)
python emg_util_yaml_runner.py --config config_fast.yaml --log-dir ..\arduino\py_scripts\logs_new\

# Custom output directory
python emg_util_yaml_runner.py --config config.yaml --log-dir path\to\logs --out-dir path\to\output
```

**Common Options:**
- `--config`: Path to YAML configuration file
- `--log-dir`: Directory containing EMG/IMU log files
- `--out-dir`: Output directory for results (optional, defaults to log-dir/out_*)

**Configuration Files:**
- `config.yaml` - Full analysis with all features and plots
- `config_fast.yaml` - Fast mode for quick analysis

---

## Offline Analysis

### Offline Mode (Post-Processing)

Analyze previously captured data files:

```bash
# Basic offline analysis (EMG only)
python sensordata_plotter.py --mode offline --emg-file emg_log_20260131_235524_20260131_235538_000

# Offline analysis with RAW signal zoomed in (+/- 500 counts from DC bias)
python sensordata_plotter.py --mode offline --emg-file emg_log_20260131_235524_20260131_235538_000 --raw-zoom

# Saturation check with custom Y-axis range
python sensordata_plotter.py --mode offline --emg-file emg_log_20260131_235524_20260131_235538_000 --emg-ymax 4095 --max-points 100000

# With IMU data overlay (EMG + IMU on one figure)
python sensordata_plotter.py --mode offline --emg-file emg_log_20260131_235524_20260131_235538_000 --imu-file imu_log_20260131_235524_20260131_235538_000

# IMU-only plot (from an IMU CSV file; pass the name without the .csv extension)
python sensordata_plotter.py --mode offline --imu-file imu_log_20260131_235524_20260131_235538_000

# Custom sample rates
python sensordata_plotter.py --mode offline --emg-file mydata --emg-sr 2000 --imu-sr 200
```

**How to interpret the IMU figure (offline IMU-only or IMU overlay):**

- **Top plot: Acceleration (g)**
  - `ax`, `ay`, `az`: 3-axis accelerometer channels in units of g.
  - `acc_mag`: total acceleration magnitude (sqrt(ax² + ay² + az²)).
  - Typical behavior: `acc_mag` should sit near **1.0 g** when stationary (gravity), with spikes/variation indicating motion.

- **Bottom plot: Rotation (dps)**
  - `gx`, `gy`, `gz`: 3-axis gyroscope channels in degrees/second (dps).
  - `gyro_mag`: total rotation magnitude (sqrt(gx² + gy² + gz²)).
  - Typical behavior: near-zero when stationary; sharp peaks correspond to fast rotations (e.g., swings/reps). These peaks are what the analysis uses for swing detection.

**Common Options:**
- `--mode offline`: Enable offline analysis mode
- `--emg-file`: EMG CSV file (without .csv extension)
- `--imu-file`: IMU CSV file (optional, without .csv extension)
- `--emg-ymax`: Maximum Y-axis value for EMG plot (useful for saturation check)
- `--raw-zoom`: Zooms the RAW subplot Y-axis to +/- 500 counts around the midpoint
- `--max-points`: Maximum number of points to plot (for performance)
- `--emg-sr`: EMG sample rate in Hz (default: 2000)
- `--imu-sr`: IMU sample rate in Hz (default: 200)

**Saturation Check:**
- Use `--emg-ymax 4095` to check if signal is clipping at ADC maximum
- Use `--max-points` to limit plotting for large files

---

## Testing

### Regression Tests

Run the complete test suite:

```bash
# Run all tests
python -m pytest tests/test_regression.py -v

# Run specific test categories
python -m pytest tests/test_regression.py -m data_loading -v
python -m pytest tests/test_regression.py -m signal_processing -v
python -m pytest tests/test_regression.py -m fatigue -v
python -m pytest tests/test_regression.py -m plotter -v

# Run only fast tests (skip slow tests)
python -m pytest tests/test_regression.py -m "not slow" -v

# Run with coverage report
python -m pytest tests/test_regression.py --cov=. --cov-report=html
```

**Test Categories:**
- `data_loading` - Data loading and integrity tests
- `signal_processing` - Signal processing algorithm tests
- `swing_detection` - Swing detection tests
- `fatigue` - Fatigue analysis tests
- `pipeline` - Full pipeline integration tests
- `baseline` - Regression baseline tests
- `error_handling` - Error handling and edge cases
- `plotter` - Plotter offline mode tests
- `fast` - Fast tests (< 5 seconds)
- `slow` - Slow tests (> 5 seconds)

---

## Utilities

### BLE UUID Discovery

Find BLE service and characteristic UUIDs:

```bash
# Scan for BLE devices and discover UUIDs
python ble_find_uuid.py

# Connect to specific device
python ble_find_uuid.py --name MyoW1
```

### Capture Loader (Python API)

Load and process captured session data programmatically:

```python
import capture_loader as loader

# Discover sessions in directory
sessions = loader.discover_sessions("logs_new")

# Load stitched session data
emg_df, imu_df, reconnection_times, capture_ids = loader.load_session_stitched(sessions)

# Load individual capture
emg_df, emg_meta = loader.load_emg_capture("logs_new/emg_log_20260131_235524_20260131_235538_000.csv")
imu_df, imu_meta = loader.load_imu_capture("logs_new/imu_log_20260131_235524_20260131_235538_000.csv")
```

### Fatigue Monitor (Python API)

Use fatigue monitoring in custom scripts:

```python
from fatigue_monitor import FatigueMonitor

# Initialize monitor
monitor = FatigueMonitor(
    fs=2000,                    # EMG sample rate
    warmup_skip_min=2.0,        # Warmup period
    baseline_swings=10          # Number of baseline swings
)

# Process swing data
result = monitor.push_swing(
    emg_window,                 # EMG data array
    t_peak_ms=timestamp,        # Peak timestamp
    imu_peak_mag=gyro_magnitude # Gyro magnitude
)

# Get fatigue level
print(result["fatigue_level"])  # "warming_up", "fresh", "moderate", "high"
print(result["mdf"])            # Median frequency
```

---

## Common Workflows

### Workflow 1: Live Capture with Real-Time Monitoring

```bash
# Terminal 1: Start data capture
python btCentral.py --name MyoW1 --outdir logs_new --rotate-min 20 --udp-enable

# Terminal 2: Start real-time visualization with fatigue monitoring
python sensordata_plotter.py --mode live --fatigue --imu-thr-dps 150 --fatigue-warmup-min 0
```

### Workflow 2: Offline Analysis

```bash
# Step 1: Run full analysis pipeline
python emg_util_yaml_runner.py --config config.yaml --log-dir logs_new\

# Step 2: Visual inspection of specific file
python sensordata_plotter.py --mode offline --emg-file emg_log_20260131_235524_20260131_235538_000 --emg-ymax 4095
```

### Workflow 3: Quick Saturation Check

```bash
# Check if EMG signal is saturating (clipping at ADC max)
python sensordata_plotter.py --mode offline --emg-file emg_log_20260131_235524_20260131_235538_000 --emg-ymax 4095 --max-points 100000
```

---

## Configuration Files

### config.yaml (Full Analysis)

Standard configuration with all features enabled:
- Full feature extraction (MAV, RMS, WL, ZC, SSC, MNF, MDF)
- Swing detection with gyroscope
- Fatigue analysis with baseline
- All diagnostic plots
- Health checks

### config_fast.yaml (Fast Analysis)

Optimized for speed:
- Reduced feature set (medium mode)
- Plots disabled
- Minimal diagnostics
- Faster processing

---

## Troubleshooting

### Common Issues

**Issue: "Module not found" errors**
```bash
# Ensure you're in the correct directory
cd C:\wangx\ftc\emg_util

# Or use absolute paths
python C:\wangx\ftc\emg_util\sensordata_plotter.py --mode live
```

**Issue: UDP connection timeout in live mode**
```bash
# Check if btCentral is running with --udp-enable
# Check firewall settings
# Try different port: --udp-port 5006
```

**Issue: Fatigue monitor not working**
```bash
# Ensure emg_util path is correct
python sensordata_plotter.py --mode live --fatigue --emg-util-path C:\wangx\ftc\emg_util

# Check that fatigue_monitor.py exists in emg_util directory
```

**Issue: Tests failing**
```bash
# Ensure regression test data exists
# Check that all dependencies are installed: numpy, pandas, scipy, matplotlib, pytest
pip install -r requirements.txt
```

---

## Environment Setup

### Required Python Packages

```bash
pip install numpy pandas scipy matplotlib pytest bleak pyyaml
```

### Directory Structure

```
C:\wangx\ftc\
├── emg_util/                      # Core analysis library
│   ├── emg_util.py
│   ├── fatigue_monitor.py
│   ├── capture_loader.py
│   ├── emg_util_yaml_runner.py
│   ├── sensordata_plotter.py
│   ├── btCentral.py
│   ├── config.yaml
│   ├── config_fast.yaml
│   ├── tests/
│   │   └── test_regression.py
│   └── regression_testlogs/
│
└── arduino/
    └── py_scripts/
        └── logs_new/              # Default capture directory
```

---

## Additional Resources

- **High-Level Design:** See `HIGH_LEVEL_DESIGN.md` for architecture overview
- **Consolidation Plan:** See `PYTHON_CONSOLIDATION_PLAN.md` for code organization strategy
- **Changelog:** See `CHANGELOG.md` for version history
- **Protocol:** See `PROTOCOL.md` for BLE communication protocol details

---

**Last Updated:** 2026-02-27
