# Google Colab Usage Guide

## Quick Start: Running Tennis Analysis on Google Colab

This guide shows you how to use `tennis_analysis_cloud.ipynb` on Google Colab for fast cloud processing.

---

## Step 1: Prepare Your Files

### A. Python Scripts (Required)
Upload these files to Google Drive (e.g., `/MyDrive/Tennis_Project/scripts/`):
- `emg_util.py`
- `emg_util_yaml_runner.py`
- `capture_loader.py`
- `capture_health.py`
- `imu_feature.py`
- `rest_recommendation.py` (optional)
- `feature_ml.py` (optional)

### B. Log Files (Your Data)

**Option 1: Upload Individual CSVs**
- Upload all your CSV files to Drive (e.g., `/MyDrive/Tennis_Project/raw_logs/`)
- Files should be named: `emg_log_*.csv`, `imu_log_*.csv`, `vitals_log.csv`

**Option 2: Upload ZIP File (Easier!)**
1. On your PC, zip your log folder:
   ```
   logs_new.zip
   ├── emg_log_20260207_184822__000.meta.json
   ├── emg_log_20260207_184822_20260207_184836_000.csv
   ├── imu_log_20260207_184822__000.meta.json
   ├── imu_log_20260207_184822_20260207_184836_000.csv
   └── vitals_log.csv
   ```

2. Upload `logs_new.zip` to Google Drive

3. In Colab, add this cell after Cell 1 (Mount Drive):
   ```python
   # OPTIONAL: Extract ZIP file
   import zipfile
   
   zip_path = '/content/drive/MyDrive/Tennis_Project/logs_new.zip'
   extract_to = '/content/drive/MyDrive/Tennis_Project/raw_logs'
   
   if os.path.exists(zip_path):
       print(f'Extracting {zip_path}...')
       with zipfile.ZipFile(zip_path, 'r') as zip_ref:
           zip_ref.extractall(extract_to)
       print(f'✅ Extracted to {extract_to}')
   else:
       print(f'⚠️  ZIP not found: {zip_path}')
   ```

---

## Step 2: Update Paths in Notebook

Open `tennis_analysis_cloud.ipynb` in Colab, then in **Cell 2**, update these paths:

```python
if IN_COLAB:
    # Update these to match YOUR Google Drive layout
    SCRIPT_DIR = '/content/drive/MyDrive/Tennis_Project/scripts'
    LOG_DIR = '/content/drive/MyDrive/Tennis_Project/raw_logs'
    OUT_DIR = '/content/drive/MyDrive/Tennis_Project/processed_out'
```

---

## Step 3: Run the Notebook

1. **Run Cell 1** → Mounts Google Drive (you'll need to authorize)
2. **Run Cell 2** → Configures paths (check for ✅ messages)
3. **Run Cell 3** → Imports modules (should see "✅ Tennis analysis modules imported")
4. **Run Cell 4** → Loads configuration
5. **Run Cell 5** → Discovers sessions (should find your log files)
6. **Run Cell 6** → **Runs analysis** (this is the slow part on local PC, fast on Colab!)
7. **Run Cell 7** → Aggregates results into master dataset
8. **Run Cell 8** → Visualizes fatigue progression

---

## What You Get

After running all cells, you'll find in your `OUT_DIR`:

### Per-Session Outputs:
```
processed_out/
├── emg_log_20260207_184822/
│   ├── swing_features.csv          # Per-swing EMG + IMU features
│   ├── bout_summary.csv            # Bout-level aggregates
│   ├── session_summary.json        # Session metadata
│   ├── plots/
│   │   ├── emg_overview.png
│   │   ├── imu_overview.png
│   │   ├── fatigue_analysis.png
│   │   └── ...
```

### Aggregated Outputs:
```
processed_out/
├── MASTER_TRAINING_DATA.csv        # All swings from all sessions
└── dashboard_fatigue.png           # Multi-session fatigue visualization
```

---

## Key Features

### ✅ Automatic EMG Health Filtering
The system automatically detects and filters out:
- Electrode contact loss (zeros, flatlines)
- Sensor disconnects (gaps in data)
- Poor signal quality intervals

This is handled by `capture_health.py` and is **enabled by default** in the config.

### ✅ Fatigue Detection
- **MDF (Median Frequency)** drop detection
- **RMS (muscle effort)** increase detection
- Per-swing fatigue metrics
- Baseline comparison

### ✅ Swing Detection
- IMU-based swing detection (gyroscope peaks)
- Configurable thresholds
- Pre/post swing windows for EMG analysis

---

## Troubleshooting

### "Script dir NOT found"
- Check that you uploaded all `.py` files to the correct Drive folder
- Update `SCRIPT_DIR` in Cell 2 to match your actual path

### "Log dir NOT found"
- Check that you uploaded/extracted your CSV files
- Update `LOG_DIR` in Cell 2 to match your actual path

### "No sessions found"
- Verify your CSV files are named correctly: `emg_log_*.csv`, `imu_log_*.csv`
- Check that files are in the `LOG_DIR` folder (not in a subfolder)

### Import errors
- Make sure all `.py` files are in `SCRIPT_DIR`
- Required files: `emg_util.py`, `emg_util_yaml_runner.py`, `capture_loader.py`, `capture_health.py`, `imu_feature.py`

---

## Local vs Cloud Comparison

| Feature | Local PC | Google Colab |
|---------|----------|--------------|
| Speed | Slow (single core) | Fast (multi-core) |
| Setup | Already configured | Need to upload files |
| Cost | Free | Free (with limits) |
| Data location | On your PC | In Google Drive |
| Best for | Quick tests | Batch processing |

---

## Advanced: Parallel Processing

By default, the notebook runs sequentially (one session at a time). This is safe for Colab.

For local Jupyter with many sessions, you can enable parallel processing:

In **Cell 6**, change:
```python
USE_PARALLEL = True  # Enable multi-core processing
```

⚠️ **Note:** Parallel processing on Colab can be unreliable. Stick with sequential for cloud.

---

## Need Help?

1. Check that all paths in Cell 2 are correct
2. Verify all required `.py` files are uploaded
3. Make sure CSV files follow the naming convention
4. Check the console output for specific error messages

The notebook uses the **exact same analysis** as running `emg_util_yaml_runner.py` locally, just faster on cloud hardware!
