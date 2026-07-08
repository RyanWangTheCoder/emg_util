# CLAUDE.md — emg_util

## Project Overview
- **Project**: `emg_util` — EMG+IMU Fatigue Monitoring (offline analysis + canonical algorithm library)
- **Description**: Ingests EMG/IMU/vitals CSV logs from wearable, produces per-swing fatigue features (MDF/RMS trends), diagnostics, figures, papers. **Tier 3 (offline)** of three-tier system; **canonical source of truth** for all signal-processing algorithms.
- **Language(s)**: Python 3.11 (numpy, pandas, scipy, matplotlib, scikit-learn, pyyaml, pytest)
- **Primary repo**: `git@github.com:wangxdflight/emg_util.git`
- **Conda env**: `fft-env` (host-specific path; do not hardcode)
- **Workspace**: `emg.code-workspace` (multi-folder: emg_util, arduino/py_scripts, arduino/myoware_imu_v2, btLeApp/app)

## System Context
**Three-tier system:**
- **Tier 1 (real-time, ~95% acc):** Android `SessionCaptureActivity` + `sensordata_plotter.py --fatigue`
- **Tier 2 (post-capture, ~97%):** Android `offline_runner.py` decodes `frames_*.bin` → CSV
- **Tier 3 (offline, ~98%):** `emg_util_yaml_runner.py` + Colab ← **THIS REPO**

**Sibling repos:** `../arduino/py_scripts/` (capture), `../arduino/myoware_imu_v2/` (firmware), `../btLeApp/app/` (Android, embeds emg_util as submodule).

## Key Files & Entry Points
| File | Purpose |
|------|---------|
| `emg_util.py` | Core library (DSP/features, pandas-based) |
| `fatigue_monitor.py` | **Canonical** real-time fatigue inference (single source of truth) |
| `emg_util_yaml_runner.py` | Main CLI entry point for offline analysis |
| `capture_loader.py` | CSV I/O, time-alignment, IMU scaling |
| `tests/run_regression_tests.py` | Full regression test suite |
| `out0305_w20/` | **Canonical output** (warmup 20 min, use for all claims) |
| `log0305/` | **Golden session** (stable BLE, <2% saturation) |

**See Directory Structure section below for complete file layout.**

## Rules for Claude (enforced)
### ALWAYS
- **Read docs first:** `docs/HLD_emg_util.md` → `docs/HLD_Project.md` → `docs/RULES.md` → `docs/COMMANDS.md`
- **Discuss before coding** — propose → align → implement
- **Single source of truth:** edit `preprocess_emg()` / `FatigueMonitor` **only** in `fatigue_monitor.py`
- **Dual-file parity:** changes to `emg_util.py` must be **manually ported** to `emg_util_nopandas.py` (Android)
- **Backward compatibility:** add optional params; never remove/reorder without approval
- **Update CHANGELOG.md on EVERY commit** (root cause + fix + affected paths)
- **Add regression test** for every bug fix / feature / algorithm change
- **Test with real data:** use `data/log0305` (golden) for baseline; `data/log0303` only for edge cases

### NEVER
- Do **not** add `__init__.py` (Android imports rely on plain directory)
- Do **not** add CLI/`__main__` to `emg_util.py` (must stay pure library)
- Do **not** deduplicate `emg_util.py`↔`emg_util_nopandas.py` (intentional duplication)
- Do **not** hardcode absolute paths (user works across multiple SSH remotes)
- Do **not** cite RESEARCH_ROADMAP.md numbers as results (illustrative targets only)
- Do **not** modify CSV columns without updating `capture_loader.py`, `PROTOCOL.md`, `btCentral.py`

## Quick Navigation
| Need | Where |
|------|-------|
| Understand architecture | `docs/HLD_Project.md` (system) → `docs/HLD_emg_util.md` (this repo) |
| Learn algorithms | `fatigue_monitor.py` (canonical) → `emg_util.py` (full DSP) → `docs/SWING_DETECTION.md` |
| Find a function | `emg_util.py` (DSP) or `fatigue_monitor.py` (real-time) or `capture_loader.py` (I/O) |
| Modify CSV schema | `capture_loader.py` → `btCentral.py` → `PROTOCOL.md` → `emg_util_yaml_runner.py` |
| Change parameters | `config*.yaml` → `emg_util_yaml_runner.py` → `fatigue_monitor.py` |
| Debug fatigue calc | `emg_util_yaml_runner.py` → `emg_util.analyze_fatigue()` → `fatigue_monitor.py` |
| Check test failures | `tests/run_regression_tests.py` → `test_regression.py` or `test_regression_nopandas.py` |
| Understand results | `outputs/out0305_w20/` (canonical) → `analysis/paper_figures.py` → `papers/paper_cnib.md` / `papers/icpics_draft.md` |

## Common Commands
```bash
# Offline analysis (main pipeline)
python emg_util_yaml_runner.py --config config_w20.yaml --log-dir data/log0305 --out-dir outputs/out0305_w20

# Real-time plotter + offline replay
python sensordata_plotter.py --mode live --infer-sr --fatigue
python sensordata_plotter.py --mode offline --fatigue --emg-file <emg.csv> --imu-file <imu.csv>

# Tests
python tests/run_regression_tests.py            # full suite
pytest tests/test_regression.py -v              # pandas/PC
pytest tests/test_regression_nopandas.py -v     # Android

# Paper figures
python analysis/paper_figures.py
```

**Config variants:** `config.yaml` (full) · `config_fast.yaml` (fast, legacy) · `config_w20.yaml` (canonical, warmup 20 min)

## Domain Knowledge (Quick Reference)
- **RAW** — MyoWare hardware-bandpassed EMG (20–500 Hz). Only column for frequency analysis.
- **MDF** — Median Frequency of EMG PSD. **Primary fatigue marker — drops with fatigue.**
- **Swing** — One detected stroke (gyro-magnitude peak). **Threshold: 300 dps** (fixed).
- **Baseline** — 75th percentile MDF of valid swings (fresh muscle = highest MDF).
- **Fatigue** — `mdf_drop_pct = (baseline − current)/baseline × 100` (positive = fatigue).
- **FSR** — Full-scale range. **Always trust the frame, not assumptions.** Acc 2→4→8 g, gyro 250→1000→2000 dps.
- **Sampling rates:** EMG **2000 Hz**, IMU **200 Hz**, vitals ~every 30 s.

**Full terminology:** see `docs/HLD_emg_util.md` (Domain Knowledge section).

## Directory Structure (High-Level)
```
emg_util/
├── Core Library (importable, no CLI) — stay at root
│   ├── emg_util.py, emg_util_nopandas.py, fatigue_monitor.py, capture_loader.py,
│   ├── capture_health.py, emg_util_yaml_runner.py, sensordata_plotter.py,
│   ├── rest_recommendation.py, config*.yaml
├── docs/                          (HLD_Project.md, HLD_emg_util.md, RULES.md, COMMANDS.md,
│                                   SWING_DETECTION.md, COLAB_USAGE_GUIDE.md, etc.)
├── analysis/                      (paper_figures.py, fatigue_analysis.py, n2_preimpact_mdf.py,
│                                   gen_icpics_fig*.py, build_*_docx.py, tennis_analysis_cloud.ipynb)
├── papers/                        (icpics_draft.*, paper_cnib.*, journal_*.md, abstract.md,
│                                   mdpi_template/, paper_figures/, icpics_figures/, paper_figures_tif/,
│                                   cnib_template.docm, icpics_Templates.*, references.bib, *.zip)
├── irb/                           (IRB_*.md/.pdf/.docx, README_for_Prof_Di.txt, readme.pdf, profDi.zip)
├── data/                          (log0303/, log0303_seg1/, log0305/, log0303.zip, log0305.zip)
├── outputs/                       (out0303_seg1/, out0303_v2/, out0305/, out0305_v2/,
│                                   out0305_w15/, out0305_w20/, out0305_w20_impact/)
├── tests/                         (run_regression_tests.py, test_regression.py, test_regression_nopandas.py)
├── tools/                         (log_check.py, motion_artifact_analysis.py, …)
├── patent/                        (patent docs and worklog)
├── ML/                            (ML research and CAST submission)
└── Documents/                     (reference PDFs)
```

**Full directory structure:** see `docs/HLD_emg_util.md` (Directory Structure section).

## Environment & Setup
- **OS**: Linux (also Windows/macOS) · **Shell**: `/bin/tcsh` · **IDE**: VS Code Remote-SSH
- **Python**: 3.11 (conda env `fft-env`)
- **Setup:** `conda create -n fft-env python=3.11 && pip install -r requirements.txt`

## Cross-Repo Dependencies
When modifying shared data formats (CSV schema, FSR, protocol):
1. Update `emg_util/capture_loader.py` (CSV schema)
2. Update `arduino/py_scripts/btCentral.py` (CSV writer)
3. Update `PROTOCOL.md` (both repos)
4. Update `arduino/myoware_imu_v2/` firmware if needed
5. Run `./gradlew clean assembleDebug` (Android submodule)

**Never hardcode absolute paths** — user works across multiple SSH remotes.

## Context Management
- Long sessions → use `/handoff`. Durable facts go in MEMORY.md, not here.
- This file is stable project rules; do not add session-specific notes.
- For detailed info, see linked docs in `docs/` folder (HLD_emg_util.md, RULES.md, COMMANDS.md, etc.).
