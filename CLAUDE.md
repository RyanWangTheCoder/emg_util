# CLAUDE.md — emg_util

## Project Overview
- **Project**: `emg_util` — EMG+IMU Fatigue Monitoring (PC-side offline analysis + shared core library)
- **Description**: Offline/research codebase for a MyoWare-2.0 + IMU wearable that monitors muscle fatigue during tennis. It ingests the EMG/IMU/vitals CSV logs captured by the wearable system and produces per-swing fatigue features (MDF/RMS trends), diagnostics, figures, and the papers/patents derived from them. This is **Tier 3** (offline) of a three-tier system and the **canonical source of truth** for all signal-processing algorithms.
- **Language(s)**: Python 3.11 (numpy, pandas, scipy, matplotlib, scikit-learn, pyyaml, pytest; bleak for the capture-side tools)
- **Primary repo**: `git@github.com:wangxdflight/emg_util.git`
- **Conda env**: `fft-env` (workspace interpreter `…/miniconda3/envs/fft-env/bin/python` — host-specific, do not hardcode elsewhere)

## System Context (where emg_util sits)
The full system has four sibling repos and three processing tiers. emg_util consumes data the others capture, and the others consume emg_util's algorithms.

```
Wearable (ESP32 + MyoWare 2.0 EMG + IMU + MAX30105 vitals)
   │  Nordic UART Service (BLE), binary TLV frames, CRC16-CCITT
   ▼
Capture side  ──────────────────────────────────────────────
  arduino/myoware_imu_v2/   ESP32 firmware (.ino)            ← FSR settings, pin map, protocol
  arduino/py_scripts/       btCentral.py (PC BLE recorder → rotating CSV), sensordata_plotter.py (live UDP plot)
  btLeApp/app/              Android app (Java + Chaquopy Python); embeds emg_util as a GIT SUBMODULE
   │  emg_log_*.csv, imu_log_*.csv, vitals_log.csv (+ .meta.json)   |   frames_*.bin (Android)
   ▼
Analysis side ──────────────────────────────────────────────
  emg_util/   ← THIS REPO (Tier 3 offline + canonical algorithm library)
```

- **Tier 1 (real-time, ~95% acc, <10 ms):** Android `SessionCaptureActivity` + `sensordata_plotter.py --fatigue`.
- **Tier 2 (post-capture on-device, ~97%):** Android `offline_runner.py` decodes `frames_*.bin` → CSV, stitches.
- **Tier 3 (offline PC/Cloud, ~98%):** `emg_util_yaml_runner.py` + `tennis_analysis_cloud.ipynb` (Colab). **← emg_util.**

Sibling repos live next to this one. On the current host: `../arduino/py_scripts`, `../arduino/myoware_imu_v2`, `../btLeApp/app`. **Paths written inside `*.md` docs are often stale Windows paths (`C:\wangx\ftc\…`)** — ignore them; resolve relatively. See `emg.code-workspace` for the canonical multi-folder layout.

## Architecture & Key Files
```
emg_util.py              — CORE LIBRARY (pandas/SciPy). Pure importable, NO CLI. (docstring header stale: "emg_util_bt.py")
emg_util_yaml_runner.py  — THE CLI entry point. analyze_tennis_session(log_dir, cfg, out_dir). (stale header: "an.py")
emg_util_nopandas.py     — Android/Chaquopy port: dict-of-numpy-arrays, no pandas/matplotlib/CLI. Mirrors emg_util.py.
fatigue_monitor.py       — CANONICAL FatigueMonitor + preprocess_emg(). pandas-free, scipy-OPTIONAL. Single source of truth.
capture_loader.py        — I/O + time-alignment + IMU unit-scaling ONLY (discover_sessions, load_session_stitched). No DSP.
capture_health.py        — EMG-only BAD-interval detection (zeros/flatline/gaps) to filter swings over bad electrode contact.
imu_baseline.py          — ImuBaseline: adaptive swing threshold from session gyro stats (numpy-only, Android-copyable).
imu_feature.py           — windowed IMU features + Postural Instability Score (research/demo; __main__ may be truncated).
feature_ml.py            — standalone EMG fatigue ML demo (LogReg/kNN). Runs at import; needs emg_example.csv in cwd.
fatigue_analysis.py / fatigue_analysis2.py / *.py — one-off study scripts (some have hardcoded paths — edit before running).
config.yaml + config_fast/w15/w20/w20_impact.yaml — analysis configs (one schema, tuned variants).
tests/test_regression.py (pandas) + test_regression_nopandas.py (Android) ; tests/run_regression_tests.py ; pytest.ini
regression_testlogs/     — real session data (Feb 8 2026); tests auto-skip if absent.
log0303/ log0305/        — captured sessions (canonical input data). out0305_w20/ = canonical fatigue result.
Docs: HLD_Project.md (system-wide end-to-end), HLD_emg_util.md (this repo), RULES.md, COMMANDS.md,
      SWING_DETECTION.md, REGRESSION_TEST.md, CHANGELOG.md,
      RESEARCH_REPORT.md (Paper 1, implemented), RESEARCH_ROADMAP.md (forward-looking, NOT measured results), todo.md
Paper/figure pipeline: paper_figures.py, journal_draft.md, mdpi_template/, references.bib, build_*_docx.py
```

## Domain Knowledge / Terminology
- **EMG / sEMG** — (surface) electromyography, the muscle electrical signal.
- **RAW** — MyoWare hardware-bandpassed (20–500 Hz) AC EMG, the **only** column used for frequency analysis. ADC 12-bit (0–4095), biased ~**1843** counts (NOT 2048).
- **ENV** — MyoWare hardware envelope (rectified + LPF ~3.6 Hz). Activation/quality proxy only; **unusable for MDF/MNF**. `ENV_sw` = software envelope = `abs(RAW − DC)` → Butterworth LPF.
- **REF** — reference channel; disabled in firmware (`REF_CONNECTED=false`), not used in analysis.
- **MDF** — **Median Frequency** of EMG PSD. **Primary fatigue marker — drops with fatigue** (~150–200 Hz fresh → lower).
- **MNF** — Mean (power-weighted) Frequency.
- **RMS / MAV / WL / ZC / SSC / IEMG** — time-domain EMG features (RMS rises with fatigue; ZC/SSC thr=0.01).
- **IMU** — accelerometer (`ax,ay,az`) + gyroscope (`gx,gy,gz`). **Chip is ambiguous in docs (ICM-20948 vs LSM6DS3) — verify against firmware before quoting.**
- **dps** — degrees/sec (gyro). **g** — gravity unit (accel). **acc_dyn** = `|acc_mag − 1g|` (gravity-removed effort proxy; the reliable IMU fatigue signal while gyro was saturating).
- **FSR** — full-scale range. **LSB→physical**: acc `{2:16384, 4:8192, 8:4096, 16:2048}` LSB/g; gyro `{250:131.0, 500:65.5, 1000:32.8, 2000:16.4}` LSB/dps.
- **swing** — one detected stroke (gyro-magnitude peak). **bout** — group of swings between rest gaps.
- **dev_us** — device µs timestamp (accurate within a BLE connection; resets to 0 on ESP32 reboot; raw 32-bit wraps ~71.6 min, host-extended to 64-bit).
- **host_rx_ms** — PC/phone wall-clock receive time (monotonic; bridges reconnect gaps).
- **abs_us** — reconstructed absolute timeline (hybrid: `dev_us` within a connection + `host_rx_ms` gap-bridging across reconnects). Built by `load_session_stitched()`. **Use abs_us for swing detection/debounce**, never raw host_rx_ms (~49% inflated) or raw dev_us (resets).
- **Chaquopy** — Python-on-Android runtime running `emg_util_nopandas.py` / `fatigue_monitor.py` on-device.
- **Sampling rates (hardware-fixed):** EMG **2000 Hz** (40 kHz ADC ÷ 10× oversample, 12-bit), IMU **200 Hz**, vitals (SpO2/HR) ~every 30 s.

## Key Algorithm Parameters (must stay consistent across PC/Android/plotter)
- **`preprocess_emg()`** (canonical, in `fatigue_monitor.py`): `detrend` → 4th-order Butterworth bandpass **50–450 Hz** (low cutoff raised 20→50 Hz on 2026-02-25 to reject 20–50 Hz motion artifact) → 60 Hz + 120 Hz `iirnotch` (Q=30). SciPy-optional: falls back to DC-removal-only when SciPy absent (MDF then differs).
- **Envelope**: rectify + 2nd-order Butterworth LPF **3.6 Hz**.
- **MDF/MNF**: Welch PSD, `nperseg=min(1024,len)`, `noverlap=min(512,…)`, Hann; numpy-FFT/Hamming fallback when SciPy absent.
- **Swing detection** (`detect_swing_windows_from_imu`): fixed gyro-magnitude threshold **300 dps** (≈p88; NOT z-score), `min_gap_ms`/debounce **2000 ms** (merges back-swing+forward-swing), window `pre_ms=250 / post_ms=450`, `mdf_pad_ms=300` → push_swing window **2600 samples = 1300 ms @ 2000 Hz**. `already_in_dps=True` by default (data pre-scaled by loader). All paths (Android, plotter, runner, core) aligned to 300 dps / 2000 ms as of 2026-03-07.
- **Baseline**: `warmup_skip_min` (skip electrode-settling) → RMS quality filter (keep swings with `rms ≥ 0.25 × session p90 RMS`) → **baseline MDF = 75th percentile** of valid swings (fresh muscle = highest MDF; RMS baseline uses median). `baseline_swings=20`.
- **Fatigue**: `mdf_drop_pct = (baseline − current)/baseline × 100` (positive = fatigue). Real-time levels: warming_up / fresh (<12%) / moderate (12–20%) / high (>20%).
- **ML** (mostly proposed): RandomForest, **Leave-One-Session-Out** CV only (never random split), within-subject median/IQR normalization, macro-F1 primary metric, prioritize 'high'-class recall.

## Data Formats
- **Capture CSV (btCentral / PC):** `emg_log_<session_id>_<open_id>_<idx>.csv` cols `dev_us,emg_seq,env,raw,ref,frame_seq,host_rx_ms`; `imu_log_…csv` cols `dev_us,…,ax,ay,az,gx,gy,gz,acc_fsr_g,gyro_fsr_dps,host_rx_ms`; `vitals_log.csv` (append-only). Each CSV has a sibling `*.meta.json`. `session_id`/`open_id` = `YYYYMMDD_HHMMSS` (open_id may add `_mmm`). **All files in one folder = ONE tennis session**; rotation (`_000,_001,…`) is file-management, not session boundaries.
- **Android decoded CSV:** `emg_decoded.csv` (`timestamp_us,seq,channel,value,sample_rate` — long format), `imu_decoded.csv`, `vitals_decoded.csv`; from `frames_*.bin` (14-byte header + TLV + CRC16).
- **In-memory schemas:** `EMG_IMU_COLS = [ts_ms,env,raw,ref,ax,ay,az,gx,gy,gz]`; `VITALS_COLS = [ts_ms,spo2,hr_bpm,age_ms,flags,brightness]`.
- **Outputs** (per `out_dir`): `swing_windows.csv`, `swing_features.csv`, `bout_summary.csv`, `baseline.json`, `session_summary.json`, `fatigue_summary.csv`, `capture_segments.csv`, `emg_bad_intervals.csv`, `emg_imu_correlation.json`, `fatigue_trend.png`, `imu_activity_overlay.png`.

## Common Commands
```bash
# Offline analysis (the main pipeline) — log_dir is the WHOLE capture folder (all connections stitched)
python emg_util_yaml_runner.py --config config.yaml --log-dir <logs_dir> [--out-dir <out>]
python emg_util_yaml_runner.py --config config_fast.yaml --log-dir <logs> --out-dir <out>   # medium mode, no plots

# Real-time / offline viewer + fatigue replay (sensordata_plotter.py also lives in py_scripts/)
python sensordata_plotter.py --mode live --infer-sr --fatigue --fatigue-warmup-min 5.0
python sensordata_plotter.py --mode offline --fatigue --replay-no-scroll \
       --emg-file <emg.csv> --imu-file <imu.csv> --fatigue-baseline-swings 5

# Tests — run from emg_util/ (or add it to PYTHONPATH)
python tests/run_regression_tests.py            # full suite (pre-commit recommended)
pytest tests/test_regression.py -v              # pandas/PC
pytest tests/test_regression_nopandas.py -v     # Android pandas-free
pytest tests/ -m "fast" / -m "signal_processing" / -k "ENV"   # markers in pytest.ini (--strict-markers)
python tests/run_regression_tests.py --generate-baseline      # ONLY for intentional algorithm changes

# Paper / figure build
python paper_figures.py
pandoc journal_draft.md --template mdpi_template/mdpi_pandoc_template.tex --bibliography references.bib \
       --natbib --shift-heading-level-by=-1 --wrap=preserve -o mdpi_template/journal_sensors_pandoc.tex

pip install -r requirements.txt
```
Configs are tuned variants of one schema: `config.yaml` (mode `both`, warmup 10) · `config_fast.yaml` (mode `medium`, plots off, **older schema**: legacy z-score swing detection, no `env_gating`, FSR 4/1000) · `config_w15/w20` (warmup 15/20, paper experiments — **`out0305_w20` is canonical**) · `config_w20_impact` (impact masking on). The full configs use fixed-300-dps swing detection and `env_gating`.

## Rules for Claude (from RULES.md — enforced)
### ALWAYS
- **Read the docs first** (HLD_emg_util.md / HLD_Project.md / RULES.md / COMMANDS.md / relevant `*.md`) before changing code.
- **Discuss and get explicit approval before writing code** — propose → align → then implement.
- **Single source of truth:** edit `preprocess_emg()` / `FatigueMonitor` **only** in `fatigue_monitor.py` (both `emg_util.py` and `emg_util_nopandas.py` import it). Keep DSP/feature math in `emg_util.py`; keep CLI/logging/plotting/I-O in the runners.
- **Dual-file parity:** changes to shared functions in `emg_util.py` must be **manually ported** to `emg_util_nopandas.py` (envelope, mnf_mdf, feat_*, robust_zscore, detect_swing_windows_from_imu, select_baseline_swings, compute_baseline_from_swing_features, apply_baseline_deltas, compute_swing_emg_features) and verified by `TestSwingDetectionCrossVersion`.
- **Backward compatibility is mandatory** — add optional params/new functions; never remove/reorder params or change return types without approval + deprecation path. New config keys default to old behavior.
- **Update `CHANGELOG.md` on EVERY commit** (root cause + fix + affected paths). Update HLD_emg_util.md (and HLD_Project.md if cross-component) / docstrings / COMMANDS.md when behavior or CLI changes.
- **Add a regression test** for every bug fix / new feature / algorithm change; run the full suite before committing.
- Propagate FSR/config changes to ALL of: `capture_loader.py`, `config*.yaml`, `tennis_analysis_cloud.ipynb`, and capture-side `btCentral.py`.
- Run `./gradlew clean assembleDebug` (Android) when changing code the submodule consumes.

### NEVER
- Do **not** add `__init__.py` to this dir — Android imports rely on it being a plain directory on `sys.path`.
- Do **not** add a CLI/`__main__` to `emg_util.py` (it must stay a pure library).
- Do **not** "deduplicate" `emg_util.py`↔`emg_util_nopandas.py`, `sensordata_plotter.py`↔`realtime_bridge.py`, `emg_util_yaml_runner.py`↔`offline_runner.py`, or `btCentral.py`↔`btcentral_offline_decode.py` — the duplication is intentional. Ask first (RULES.md Rule 7).
- Do **not** use `fatigue_monitor.py` for offline trend analysis (it's real-time per-swing only) — use `emg_util.analyze_fatigue()` / the runner's per-swing summary.
- Do **not** hardcode absolute paths (user works across multiple SSH remotes / shells).
- Do **not** cite RESEARCH_ROADMAP.md numbers (87–90% acc, AUC 0.94, "r=0.82 lactate") as results — they are illustrative targets.
- Do **not** delete/overwrite code or add dependencies without explicit confirmation.
- Commit message format: `[Component] Brief description` + detail bullets + `Documentation:`/`Tested:`/`Affects:`. Vague messages ("fix mdf") are forbidden.

## Gotchas & Constraints
- **FSR history is messy:** acc 2→4→8 g, gyro 250→1000→2000 dps over time (gyro saturated at 250 dps; raised 2026-02-25). Configs disagree (full=8/2000, fast=4/1000). **Always trust the FSR code in the IMU_META_V2 frame / per-row `acc_fsr_g`/`gyro_fsr_dps` columns**, not a fixed assumption. Wrong FSR defaults scale gyro ~4× too small → zero swings detected.
- **Gyro pre-2026-02-25 sessions are saturated** — use `imu_mean_acc_dyn` (not gyro) for effort/fatigue there.
- **Noise-dominated baseline** is the recurring fatigue bug: poor early electrode contact → flat-spectrum MDF ~100 Hz; if baseline anchors there, real swings give *negative* `mdf_drop_pct`. The RMS filter + warmup-skip exist to prevent this. Electrode settling lasts ~17–20 min (hence `out0305_w20`).
- **RAW must be physically connected:** a floating RAW pogo-pin makes the 50 Hz high-pass wipe the ghost signal to a flatline → all MDF/MNF/RMS invalid. Verify resting RAW ≈ 1843 (not flat, not saturated). RAW solders to ESP32 **GPIO 32** — the pad labeled "A4" is I2C SDA/GPIO 21 (no ADC), and the firmware `// A4` comment is wrong.
- **`acc_dyn` peak = swing APEX, not ball contact** (median −4.7 ms from gyro peak) — impact-triggered analysis isn't grounded without an external trigger.
- **Per-swing MDF is noisy** (CV ~38.7%) — average over 10–20 swings or multi-session trends; single-session adaptive endpoint detection fails.
- **`env_mean` means different things**: real-time = `nanmean(abs(raw))`; offline = `emg_env_mean` from `envelope()`. Don't compare directly.
- **BLE reconnect resets `dev_us`→0 and sends `seg=0`** — plotter/loader must re-anchor `t0` and clear buffers or the plot freezes / samples get dropped.
- **Test counts in REGRESSION_TEST.md are internally inconsistent** (61/53/29/25) — count actual tests, don't trust a single number. `regression_baseline.json` generator (`run_regression_tests.py`) may use stale column names (`emg_raw`) / signatures — verify against current code.
- **Two real sessions drive everything:** `log0305` (the "Golden Session", stable BLE, <2% saturation) and `log0303` (gap-confounded counter-example — **do not use for fatigue claims**).
- **IRB / human-subjects context:** captured data comes from a 2-minor-participant pilot (Ryan Wang, Theodore Di) under an IRB packet; the engineering paper (`paper_cnib.md`) is intentionally separate from the IRB-authorized study. `*.md` are source of truth; `.docx`/`.pdf` are generated.

## Environment
- **OS**: Linux · **Shell**: `/bin/tcsh` (note: some default-PATH commands need full paths) · **IDE**: VS Code Remote-SSH (`emg.code-workspace`)
- **Interpreter**: conda env `fft-env` (host-specific path; don't assume it exists elsewhere)

## Context Management
- Long sessions → summarize and use `/handoff`. Durable facts go in MEMORY.md, not here.
- This file is stable project rules; do not add session-specific notes.
