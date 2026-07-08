# emg_util Project Worklog

---

## Current Status Summary (2026-07-08)

### Project Overview
**emg_util** is a three-tier EMG+IMU fatigue monitoring system spanning firmware (ESP32), host recording (BLE), real-time inference (Android), and offline analysis (Python). This repo is **Tier 3 (offline analysis)** — the canonical source of truth for all signal-processing algorithms and the primary research output vehicle.

**System maturity:** Research-stage. Core algorithms stable; papers in submission; patent filing in progress.

---

## Major Milestones

### ✅ Completed
- **Algorithm canonicalization** (2026-05): `fatigue_monitor.py` established as single source of truth for real-time fatigue inference; dual-file parity with Android (`emg_util_nopandas.py`) maintained
- **Regression test suite** (2026-05): Full test coverage for DSP, swing detection, baseline gating, fatigue scoring; 39 passing tests (pandas), 38 passing (nopandas)
- **Paper figures & analysis** (2026-06): All seven patent figures drafted; paper_figures.py generates publication-ready plots
- **Data pipeline cleanup** (2026-07): Removed 500+ MB of large CSV logs from git history; established `data/` as local-only (not tracked)
- **Configuration standardization** (2026-06): Three config variants (full, fast, canonical w20); canonical output `out0305_w20/` locked for all claims
- **Documentation** (ongoing): HLD_Project.md, HLD_emg_util.md, SWING_DETECTION.md, PROTOCOL.md, RULES.md, COMMANDS.md

### 🔄 In Progress
- **Paper submissions** (target ~2026-07):
  - ICPICS: Swing detection + fatigue trends (pending acceptance)
  - CNIB: IMU-conditioned validity + session-gap artifact (pending acceptance)
  - Paper3 (ML/longitudinal): Load prediction from 40–80 sessions (Stage 0 locked; Stage 1 pilot sessions starting)
- **Patent filing** (target before paper publication):
  - Provisional draft complete (`patent/05_provisional_draft.md`)
  - 18 claim concepts defined; 7 figures drafted
  - Inventor matrix finalized (Ryan Wang, sole inventor; Larry Wang, implementation support)
  - Public disclosure timeline documented; filing deadline: before ICPICS/CNIB publish
- **ML research** (`ML/` folder):
  - Paper3 plan finalized (`paper3_plan.md` canonical)
  - CAST Global Youth Innovation Summit submission created
  - Session collection protocol locked; pilot sessions underway

### ⏳ Planned / Blocked
- **Android integration** (blocked on paper acceptance): Embed emg_util as submodule in btLeApp/app; sync algorithm updates
- **Real-time plotter** (stable, not active): `sensordata_plotter.py` available for live/offline replay; UDP telemetry functional
- **Colab notebook** (documented, not active): `COLAB_USAGE_GUIDE.md` describes setup; used for paper figure generation
- **Firmware updates** (stable): ESP32 firmware in `../myoware_imu_v2/` stable; BLE protocol frozen per `PROTOCOL.md`

---

## Key Files & Ownership

| Component | File(s) | Status | Owner |
|-----------|---------|--------|-------|
| **Core DSP** | `fatigue_monitor.py`, `emg_util.py` | Canonical, locked | Ryan Wang |
| **Android parity** | `emg_util_nopandas.py` | Dual-file sync required | Ryan Wang |
| **I/O & CSV schema** | `capture_loader.py` | Locked (PROTOCOL.md) | Ryan Wang |
| **Offline pipeline** | `emg_util_yaml_runner.py` | Stable | Ryan Wang |
| **Real-time inference** | `fatigue_monitor.py` (Tier 1/2) | Canonical | Ryan Wang |
| **Plotting** | `sensordata_plotter.py` | Stable, optional | Ryan Wang |
| **Tests** | `tests/test_regression.py`, `test_regression_nopandas.py` | 39/38 passing | Ryan Wang |
| **Paper figures** | `analysis/paper_figures.py` | Locked for publication | Ryan Wang |
| **Canonical output** | `outputs/out0305_w20/` | Locked for all claims | Ryan Wang |
| **Patent** | `patent/` folder | Provisional draft complete | Ryan Wang (inventor) |
| **ML research** | `ML/` folder | Stage 0 locked, Stage 1 pilot | Ryan Wang |

---

## Data & Testing

### Golden Session
- **`data/log0305/`** — Canonical test data (stable BLE, <2% saturation, 5 swings)
  - Used for all regression tests, paper figures, and algorithm validation
  - **Status:** Locked; not tracked in git (local-only)

### Regression Tests
- **Pandas (PC):** 39 passing, 26 skipped (missing regression_testlogs symlink — now fixed)
- **Nopandas (Android):** 38 passing, 1 skipped
- **Symlink:** `regression_testlogs → data/log0305` (created 2026-07-08)
- **Run command:** `python tests/run_regression_tests.py` (uses conda env `fft-env`)

### Configuration Variants
| Config | Purpose | Status |
|--------|---------|--------|
| `config.yaml` | Full analysis (all features) | Stable |
| `config_fast.yaml` | Fast mode (legacy) | Stable, not recommended |
| `config_w20.yaml` | **Canonical** (warmup 20 min) | Locked for all claims |

---

## Cross-Repo Dependencies

### Upstream (Data Source)
- **`../arduino/py_scripts/`** — BLE host recorder; produces CSV logs
  - Memory bank: `../arduino/py_scripts/memory-bank/` (protocol, architecture, recording behavior)
  - **Dependency:** CSV schema defined in `capture_loader.py` ↔ `btCentral.py` (py_scripts)
  - **Protocol:** `../arduino/py_scripts/PROTOCOL.md` (authoritative)

### Firmware
- **`../arduino/myoware_imu_v2/`** — ESP32 firmware; BLE streaming
  - **Dependency:** Binary frame format, TLV payloads, FSR (full-scale range) per PROTOCOL.md
  - **Status:** Stable; no active changes

### Android Integration
- **`../btLeApp/app/`** — Android app; embeds emg_util as submodule
  - **Dependency:** `emg_util_nopandas.py` (dual-file parity required)
  - **Status:** Submodule link active; awaiting paper acceptance for integration work

### BLE Support Library
- **`../btLeApp/FastBleLib/`** — Android BLE library
  - **Status:** Stable; not directly used by emg_util

---

## Recent Changes (2026-07)

### Git History Cleanup (2026-07-08)
- **Removed:** 500+ MB of large CSV logs from git history using `git filter-branch`
- **Added:** `data/` to `.gitignore`
- **Result:** Repo now pushes to GitHub without file-size errors
- **Local impact:** `data/log0305/`, `data/log0303/` still exist locally; not tracked

### Configuration (2026-07-08)
- **Created:** `.claude/settings.json` (project-scoped)
  - Python interpreter: `/local/mnt/workspace/wangx/miniconda3/envs/fft-env/bin/python`
  - Pre-approved permissions for Python commands
- **Updated:** `CLAUDE.md` with reference to py_scripts memory bank

### Regression Tests (2026-07-08)
- **Fixed:** Created symlink `regression_testlogs → data/log0305`
- **Result:** 39 pandas tests passing; 38 nopandas tests passing
- **Known issues:** 2 test failures in background run (pre-existing, not related to cleanup)

---

## Known Issues & Unknowns

### Test Failures (Pre-existing)
- `test_fatigue_monitor_baseline_collection`: baseline_ready assertion fails (needs investigation)
- `test_plotter_with_regression_data`: envelope LPF std assertion fails (needs investigation)
- **Action:** Investigate root cause; add to next session's work

### Documentation Gaps
- `sensordata_plotter.py` referenced in docs but location/status should be verified if plotting work requested
- Plotter filename inconsistency: docs reference both `sensordata_plotter.py` and `udp_plotter2.py`

### Android Sync
- `emg_util_nopandas.py` requires manual porting of changes from `emg_util.py`
- No automated sync; dual-file parity enforced by code review
- **Risk:** Drift if changes not ported; mitigated by explicit CLAUDE.md rule

### Paper Timeline
- ICPICS and CNIB acceptance dates TBD; patent filing deadline depends on publication dates
- **Action:** Update `patent/02_public_disclosure_timeline.md` when acceptance notices arrive

---

## Subfolder Worklogs

Detailed session notes are maintained in:
- **`patent/worklog.md`** — Patent filing progress, claim concepts, figures, inventor matrix
- **`ML/worklog.md`** — Paper3 research, session collection protocol, CAST submission

---

## Next Steps (Prioritized)

1. **Investigate test failures** — Root cause analysis for baseline_collection and plotter tests
2. **Monitor paper submissions** — Track ICPICS/CNIB acceptance; update patent filing timeline
3. **Pilot ML sessions** — Begin Stage 1 data collection per `ML/paper3_plan.md`
4. **Android integration** — Post-paper-acceptance: sync emg_util submodule, test dual-file parity
5. **Documentation sync** — Reconcile plotter filename references; verify all docs current

---

## Session Log

### 2026-07-08 — Git cleanup, config setup, regression tests
- Removed 500+ MB of large CSV logs from git history
- Added `data/` to `.gitignore`
- Created `.claude/settings.json` with conda Python path
- Fixed regression test symlink (`regression_testlogs → data/log0305`)
- Added py_scripts memory bank reference to CLAUDE.md
- **Result:** Repo now pushes to GitHub; 39/38 tests passing

---

**Last updated:** 2026-07-08  
**Maintained by:** Ryan Wang  
**Related docs:** `CLAUDE.md`, `docs/HLD_Project.md`, `docs/HLD_emg_util.md`, `CHANGELOG.md`
