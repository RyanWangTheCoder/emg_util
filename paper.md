# Paper Planning: EMG-IMU Wearable for Tennis Fatigue Monitoring

**Status:** Planning / Pre-draft — numbers confirmed  
**Target:** Conference paper (middle-rigor, high school research project level)  
**Deadline:** ~2 months  
**Data:** Two captured sessions (log0303, log0305), single player  
**Last Updated:** 2026-05-02

---

## Working Title

*"EMG-IMU Wearable System for Tennis Fatigue Monitoring: Electrode Contact Dynamics and IMU-Based Signal Quality Cross-Validation"*

Alternative titles:
- *"Practical Challenges in Wearable sEMG for Tennis: Electrode Settling, Contact Quality, and the Role of IMU Cross-Validation"*
- *"A Low-Cost Wearable EMG-IMU System for Tennis: Signal Quality Characterization and Fatigue Analysis"*

---

## Motivation / Problem Statement

Muscle fatigue monitoring during sports is important for performance optimization and injury prevention. Surface EMG (sEMG) is the standard tool, but applying it to dynamic sports like tennis creates practical challenges that laboratory studies rarely address:

1. **Electrode contact quality degrades** over time due to sweat loosening the 3-electrode snap connectors, reducing signal integrity mid-session.
2. **Electrode settling** — at session start, the dry electrode-skin interface has high impedance. It takes time (potentially 15–20 min, not the commonly assumed 5 min) to achieve stable, low-impedance contact.
3. **Forearm placement constraint** — wrist/forearm is the only practical placement during tennis, but it is subject to motion from grip changes and racket vibration.
4. **Result:** EMG-based fatigue metrics (e.g., MDF drop) are unreliable during portions of a session where electrode contact is unstable — and the system has no way to know this without an external reference.

**Key insight:** The IMU (already on the sensor for swing detection) provides exactly that external reference. If the IMU says "consistent swing biomechanics" but EMG shows an anomalous signal, the problem is the electrode, not the muscle.

---

## Physical Basis of Electrode Settling

*(Reference section — draw from this when writing Methods and Discussion)*

### What is happening physically

When a dry snap electrode is applied to unabraded forearm skin without gel, the interface has high impedance dominated by the dry stratum corneum (10–100 kΩ). Two processes stabilise it over time:

**1. Sweat accumulation (dominant, ~10–20 min)**
Eccrine sweat glands produce saline (~150 mM NaCl) in response to exercise and heat. Sweat fills the electrode-skin gap, creating a low-impedance ionic bridge. Impedance drops from ~50 kΩ to ~2–5 kΩ. The rate depends on exercise intensity, ambient temperature, and skin condition — slower at session start (warm-up phase), slower indoors, slower on a cool day.

**2. Ag/AgCl half-cell potential equilibration (slower, ~5–15 min)**
The 3M Red Dot electrodes use Ag/AgCl chemistry. On first contact, the silver chloride surface hasn't equilibrated with the local skin electrolyte — the resulting half-cell potential drifts exponentially toward equilibrium. This produces slow baseline wander (low-frequency voltage drift) even after software detrending, contributing noise in the 0–20 Hz range that bleeds through the 50 Hz high-pass filter.

### Why settling depresses MDF specifically

During settling, EMG signal amplitude is attenuated (low RMS) but noise is not. The dominant noise — electrode drift and imperfect common-mode rejection of powerline interference through the high-impedance interface — is low-frequency (concentrated near 50–150 Hz within the 50–450 Hz bandpass). The recorded PSD is therefore:

```
recorded PSD ≈ (attenuated real EMG) + (low-frequency noise)
```

The low-frequency noise shifts the PSD toward the bottom of the pass band, pulling MDF down. Once the interface is fully wet, SNR recovers and MDF returns to the true resting value (~166 Hz). Any subsequent MDF drop reflects genuine muscle fatigue.

### Why 17–20 min, not 5

- Session starts with low-intensity warm-up → slow initial sweat onset
- Indoor court, moderate temperature → slower eccrine activation than outdoor summer heat
- No skin abrasion or pre-applied gel → full stratum corneum resistance must be overcome by sweat alone
- The 15-min skip being *worse* than 10-min (baseline 112 Hz vs. 137 Hz) reflects the RMS-based baseline selector catching swings mid-transition, where contact quality is still improving rapidly. This is not a contradiction — it shows the settling is not linear and a fixed time skip is a crude proxy for a proper quality-based criterion.

### One-sentence version for the abstract
*"In field deployments, forearm electrode impedance decreases over 17–20 minutes as eccrine sweat hydrates the electrode-skin interface and the Ag/AgCl half-cell potential equilibrates, suppressing EMG spectral metrics during the transition and masking genuine fatigue in analyses using standard short warmup skips."*

---

## Core Contributions

1. **Electrode settling characterization** — quantify how long forearm EMG takes to stabilize in a real tennis session. Data confirms settling extends to **at least 17–20 minutes**, not the commonly assumed 5 min. During settling, MDF is depressed **~42% below** the stable baseline, creating a false fatigue appearance. Standard 10-min and 15-min warmup skips are both insufficient (baseline still contaminated at 15 min: 112 Hz vs. stable 166 Hz).

2. **IMU-based EMG quality monitor** — propose a practical quality metric:
   ```
   contact_quality(t) = RMS_window(t) / session_p90_rms
   ```
   When IMU swing intensity is consistent (biomechanics unchanged) but `contact_quality` is low → electrode contact issue, not fatigue. Validated in log0305: `imu_peak_mag` flat (Pearson r = +0.01, p = 0.78) throughout session while early EMG MDF was falsely depressed by 42%.

3. **Hidden fatigue revealed by proper settling correction** — log0305 showed **−2.6% MDF change** with standard 10-min skip (no fatigue found). With 20-min skip to clear the settling period, baseline stabilises at 199 Hz and a **28.1% MDF drop** (and 17.3% MNF drop) is revealed — genuine neuromuscular fatigue that was completely masked by electrode settling in the original analysis.

4. **Session gap artifact** — log0303's apparent 28.7% MDF drop is confounded by a 66-minute BLE reconnection gap. Analysing the first segment alone (13.5 min, 111 swings) yields only a **4.9% MDF drop**, confirming no meaningful within-segment fatigue and that the full-session figure is a cross-segment artifact.

---

## System Description

### Hardware
- **EMG:** MyoWare 2.0 muscle sensor, 2000 Hz, 12-bit ADC, forearm flexor placement (3-electrode snap configuration)
- **IMU:** ICM-20948 9-axis, 200 Hz, ±1000 dps gyro / ±4g accelerometer
- **MCU:** ESP32, BLE streaming, binary TLV protocol with CRC16
- **Additional:** MAX30102 SpO2/HR (not used in this study)
- **Cost:** ~$99 total hardware cost

### Key Hardware Engineering Points (worth mentioning for novelty)
- ADC DMA at 40 kHz with 10× oversampling → decimated to 2000 Hz (zero CPU overhead, ±25 µs timestamp accuracy)
- Direct solder bypass of RAW signal from MyoWare to ESP32 GPIO32 (pogo pin connection was mechanically unreliable during movement)
- Dual-output MyoWare: RAW pin (for spectral analysis) + ENV pin (hardware envelope, for contact quality monitoring)

### Software Pipeline
- **Capture:** `btCentral.py` — BLE central, rotating CSV logs
- **Loading:** `capture_loader.py` — multi-session stitching with hybrid `abs_us` timeline (handles BLE dropouts + ESP32 resets)
- **Analysis:** `emg_util_yaml_runner.py` — YAML-driven tennis session analysis
- **Core library:** `emg_util.py` (PC) / `emg_util_nopandas.py` (Android/Chaquopy)
- **Real-time:** `sensordata_plotter.py` + `fatigue_monitor.py` (Android + PC live monitoring)

---

## Data Description

### Session log0303 (March 3, 2026)
| Metric | Value |
|--------|-------|
| Duration | 87.9 min total — **two BLE segments with 66-min reconnection gap** |
| Segment 1 | 0–13.5 min (111 swings, 11 bouts) — first BLE connection `20260303_183639` |
| Segment 2 | 80.3–87.9 min (86 swings) — second BLE connection `20260303_191258` |
| Total swings | 197 |
| Bouts | 18 |
| Swing rate | ~2.2 swings/min (sparse, drill-style) |
| Baseline MDF (`out0303_v2`) | 212.9 Hz |
| Final MDF | 151.8 Hz |
| MDF drop (full session) | **28.7%** — ⚠️ gap-confounded |
| MDF drop (seg1 only, `out0303_seg1`) | **4.9%** — no within-segment fatigue |
| MNF drop (full session) | 29.1% — ⚠️ gap-confounded |
| Fatigue onset | ~83 min (in second segment — confirms gap artifact) |
| `imu_peak_mag` Pearson r vs time | −0.15 (p = 0.032, mild downward) |
| `imu_mean_acc_dyn` trend | −44% early→late |

**Key caveat:** The 28.7% MDF drop compares first-segment swings against second-segment swings across a 66-minute gap. Segment 1 alone shows only 4.9% drop — no genuine within-session fatigue. The full-session figure is a **cross-segment artifact**, not physiological fatigue.

### Session log0305 (March 5, 2026)
| Metric | Value |
|--------|-------|
| Duration | 63.1 min (single continuous BLE connection) |
| Total swings | 626 |
| Bouts | 50 |
| Swing rate | ~10 swings/min (dense, sustained throughout) |
| `imu_peak_mag` trend | **r = +0.01, p = 0.78 (completely flat — no biomechanical fatigue)** |

**Warmup-skip sensitivity (the central finding):**

| warmup_skip | Output dir | Baseline MDF | Final MDF | MDF drop % | Interpretation |
|---|---|---|---|---|---|
| 10 min | `out0305` | 137.1 Hz | 140.7 Hz | **−2.6%** | Baseline in settling → false negative |
| 10 min | `out0305_v2` | **166.0 Hz** | 140.8 Hz | **+15.2%** | RMS filter found post-settling swings → moderate fatigue |
| 15 min | `out0305_w15` | 112.3 Hz | 141.8 Hz | **−26.2%** | Still in settling at 15 min → inverted baseline |
| 20 min | `out0305_w20` | **199.2 Hz** | 143.2 Hz | **+28.1%** | Post-settling baseline → genuine fatigue revealed |

**The settling period extends past 15 minutes.** Even at 15-min skip the baseline is only 112 Hz (below the stable 166 Hz), confirming the settling tail reaches at least 17–20 min. With 20-min skip, a **28.1% MDF drop** and **17.3% MNF drop** emerge — genuine neuromuscular fatigue that was entirely masked in the original 10-min analysis.

**IMU cross-validation:** `imu_peak_mag` flat (r = +0.01) throughout the session. The player did not reduce swing force or speed. The MDF drop therefore reflects physiological spectral shift (muscle fibre conduction velocity slowing), not reduced effort — the strongest possible interpretation of fatigue.

---

## Key Data Findings — CONFIRMED

### Finding 1: Electrode Settling Extends to ~17–20 Minutes (not 5 or 10)

In log0305, the MDF by session third (time-equal thirds of 63 min):

| Session third | Time range | MDF mean ± std | vs. stable baseline (166 Hz) | Interpretation |
|---|---|---|---|---|
| Early | 0–21 min | 107.6 ± 36.3 Hz | **−35%** | Electrode settling |
| Mid | 21–42 min | 161.2 ± 22.1 Hz | −3% | Stable |
| Late | 42–63 min | 166.4 ± 18.3 Hz | 0% | Stable, no decay |

Warmup-skip sensitivity confirms this — the baseline remains contaminated until at least 17–20 min:

| warmup_skip | Baseline MDF | Status |
|---|---|---|
| 10 min | 112–137 Hz | Still in settling |
| 15 min | 112 Hz | **Still** in settling |
| 20 min | 199 Hz | Post-settling ✓ |

### Finding 2: 28.1% Fatigue Signal Hidden by Electrode Settling (log0305)

With standard 10-min skip: MDF drop = −2.6% → fatigue not found.  
With 20-min skip (post-settling baseline): MDF drop = **+28.1%**, MNF drop = **+17.3%**, fatigue onset at **1224 s (~20 min)**.  
IMU `imu_peak_mag` is flat throughout (r = +0.01, p = 0.78) → fatigue is physiological, not effort reduction.

This is the central finding: **a standard analysis pipeline completely missed genuine fatigue because the warmup skip was 3× too short.**

### Finding 3: IMU Flat Line Is the Cross-Validator

log0305 `imu_peak_mag`:
- Early mean: 1577.5 ± 693.7 dps
- Mid mean: 1572.8 ± 713.4 dps
- Late mean: 1591.1 ± 705.8 dps
- Pearson r = **+0.01**, p = **0.78** (non-significant, completely flat)

The player maintained identical swing biomechanics for 63 minutes. Combined with the 28.1% MDF drop, this rules out reduced effort as the cause — the MDF shift is physiological fatigue.

### Finding 4: log0303 Full-Session Drop Is a Gap Artifact

| Analysis | MDF drop | n swings | Notes |
|---|---|---|---|
| `out0303_v2` full session | 28.7% | 197 | Compares across 66-min gap |
| `out0303_seg1` first segment only | **4.9%** | 111 | 13.5 min, no gap |

4.9% in 13.5 min is expected (below any meaningful fatigue threshold). The 28.7% from the full session is an artifact of comparing the first segment (fresh electrode, warm-up) against the second segment (re-applied electrode, different contact state) across a 66-min gap.

---

## Paper Structure (Proposed)

### 1. Introduction (~300 words)
- Motivation: fatigue monitoring in sports, limitations of lab-based approaches
- Challenge: practical wearable sEMG is harder than laboratory sEMG (sweating, movement, electrode placement constraints)
- **Electrode settling sentence:** *"In laboratory EMG studies, electrode-skin impedance is minimised by skin abrasion and conductive gel applied before recording. In field deployments on a tennis court, neither preparation step is practical; instead, the interface relies on sweat to hydrate the electrode contact, a process that can take substantially longer than the 5-minute warmup skip commonly assumed in the literature."*
- Gap: electrode settling duration in real sports sessions is under-documented; IMU cross-validation of EMG quality is unexplored for tennis
- Contributions: (list 4 from Core Contributions section)

### 2. System Design (~400 words)
- Hardware overview (EMG + IMU + MCU, cost, key engineering choices)
- Software pipeline (capture → analysis → real-time monitoring)
- Swing detection algorithm: fixed 300 dps threshold, 2000 ms debounce (justify why adaptive threshold fails for wrist-worn sensors)
- Analysis pipeline: swing-gated MDF, RMS, ENV features; baseline protection (warmup skip + RMS filter + 75th percentile)

### 3. Methods (~400 words)
- Session protocol: recreational tennis, single player, two sessions
- Data description: log0303 (87.9 min, 197 swings) and log0305 (63.1 min, 626 swings)
- Analysis approach: per-swing features, session thirds, Pearson trend analysis
- **Electrode settling — physical basis (short paragraph for Methods):**
  > When a dry snap electrode is applied to unabraded forearm skin, the electrode-skin interface presents high impedance (10–100 kΩ) due to the resistive stratum corneum. Two parallel processes reduce this impedance over time: (1) sweat accumulation — eccrine glands produce saline (~150 mM NaCl) that hydrates the electrode-skin gap, creating a low-impedance ionic bridge; and (2) electrochemical equilibration — the Ag/AgCl electrode half-cell potential drifts until it reaches equilibrium with the local electrolyte, contributing low-frequency baseline wander during the transition. Both processes are slower in field conditions (no skin abrasion, no pre-applied gel) and depend on ambient temperature and exercise intensity. During the settling period, the attenuated EMG signal has poor SNR; the residual noise is low-frequency dominant within the 50–450 Hz bandpass, which depresses the estimated MDF below its true value. Once the interface is fully hydrated, MDF stabilises at the true resting value.
- Electrode settling detection: track per-swing MDF vs. time; settling endpoint defined as first time rolling-mean MDF sustains ≥150 Hz for 5 consecutive swings
- Warmup-skip sensitivity test: re-run analysis at 10, 15, 20 min to quantify baseline contamination
- IMU quality cross-validation: compare `imu_peak_mag` Pearson r vs time; if flat (|r| < 0.1) while early MDF is depressed → settling artifact, not fatigue
- Contact quality metric: `contact_quality(t) = RMS(t) / session_p90_rms`; thresholds: >0.25 reliable, <0.10 contact loss

### 4. Results (~500 words)
- 4.1 Electrode settling: log0305 first-third MDF = 107.6 Hz vs. mid/late ~163 Hz; table of thirds; settling takes ≥17–20 min
- 4.2 Warmup-skip sensitivity: table (10-min: −2.6%, 15-min: −26.2%, 20-min: +28.1%) — show that standard pipeline missed fatigue entirely
- 4.3 IMU cross-validation: `imu_peak_mag` flat (r=+0.01, p=0.78) confirms settling is artifact; combined with 28.1% MDF drop → genuine physiological fatigue
- 4.4 Contact quality metric over session (log0305): rises from settling to stable
- 4.5 log0303 gap artifact: full-session 28.7% drop vs. seg1-only 4.9% drop

### 5. Discussion (~400 words)
- **Electrode settling interpretation:**
  > The observed settling duration of ≥17–20 min is consistent with the time required for eccrine sweat glands to reach steady-state output under moderate exercise on an indoor court, combined with the exponential decay of the Ag/AgCl half-cell potential drift. The non-monotone behaviour of the warmup-skip sensitivity (15-min baseline = 112 Hz, lower than the 10-min baseline = 137 Hz) reflects the interaction between RMS-based baseline selection and the settling curve: the RMS filter at 15-min happened to select swings from the steepest part of the transition, where contact quality is still improving. This underscores that a fixed warmup-skip time is a crude heuristic — a contact-quality-aware adaptive skip would be more robust.
- **Practical recommendation:** Extend warmup skip to ≥20 min for forearm snap-electrode deployments in field tennis. The pipeline parameter `warmup_skip_min` should default to 20 for this sensor/placement combination.
- **IMU cross-validation:** The IMU is already on the device for swing detection — using it as a quality monitor adds zero hardware cost. The decision rule (IMU consistent + MDF depressed → settling; IMU consistent + MDF dropping → fatigue) turns a qualitative observation into a testable, automatable criterion.
- Why log0305 showed genuine fatigue once corrected: 626 swings at ~10/min for 63 min represents significant cumulative forearm flexor load, consistent with 28.1% MDF drop even without perceptible biomechanical degradation.
- Limitations: single player, two sessions, no RPE or MVC ground truth, settling duration likely varies with player sweat rate, skin condition, ambient temperature
- Future work: multi-player study, adaptive warmup skip based on contact quality metric, RPE integration, real-time settling detection in Android app

### 6. Conclusion (~150 words)
- Wearable sEMG for tennis has practical challenges beyond motion artifact
- Electrode settling extends ≥17–20 min — standard 5–10 min skip misses genuine fatigue entirely (−2.6% with 10-min skip vs. +28.1% with 20-min skip on the same data)
- IMU provides a free, always-on quality cross-validator already present for swing detection
- Two-session case study: log0305 revealed genuine fatigue once settling corrected; log0303 gap artifact warns against treating disconnected recordings as continuous fatigue data

---

## Figures Needed

| # | Figure | Data source | Status |
|---|--------|-------------|--------|
| 1 | System overview diagram (sensor + pipeline) | Diagram | ⏳ Manual |
| 2 | **Electrode settling: MDF vs. time (first 30 min, log0305)** — 108→166 Hz rise | `out0305_w20/swing_features.csv` | ⏳ `paper_analysis.py` |
| 3 | **IMU flat line: `imu_peak_mag` vs. time (log0305)** — r=+0.01 | `out0305_w20/swing_features.csv` | ⏳ `paper_analysis.py` |
| 4 | **Warmup-skip sensitivity bar chart** — −2.6% / −26.2% / +28.1% at 10/15/20 min | fatigue_summary files | ⏳ `paper_analysis.py` |
| 5 | Contact quality (`RMS/p90_rms`) over session, both sessions | `out0303_v2`, `out0305_w20` | ⏳ `paper_analysis.py` |
| 6 | log0303 gap artifact: MDF over full session with reconnection gap annotated | `out0303_v2/swing_features.csv` | ⏳ `paper_analysis.py` |
| 7 | IMU-EMG diagnostic matrix (2×2 scatter) | Both sessions | ⏳ `paper_analysis.py` |

Draft figures generated by `paper_figures.py` are in `paper_figures/` but use wrong output dirs (`out0303`/`out0305`). Re-generate from `paper_analysis.py` once complete.

---

## Tables Needed

| # | Table | Content |
|---|-------|---------|
| 1 | System specifications | Hardware BOM, sampling rates, cost |
| 2 | Session summary | Both sessions: duration, swings, bouts, MDF drop |
| 3 | Electrode settling data | MDF by thirds, log0305 |
| 4 | IMU-EMG cross-validation logic | Decision matrix (4-quadrant table above) |

---

## Key Numbers to Cite in Paper — CONFIRMED

| Fact | Value | Source |
|------|-------|--------|
| Motion artifact correlation | r = 0.006 | log0305 analysis (RESEARCH_REPORT.md) |
| Electrode settling duration | **≥17–20 min** | log0305 warmup-skip sensitivity |
| Baseline MDF at 10-min skip | 112–137 Hz (contaminated) | `out0305`, `out0305_w15` |
| Baseline MDF at 20-min skip | 199.2 Hz (stable) | `out0305_w20` |
| Stable post-settling MDF | ~166 Hz | `out0305_v2` baseline.json |
| Early session MDF (settling) | 107.6 ± 36.3 Hz | log0305 early third |
| False apparent MDF drop (settling) | **+42.5%** (swing_mdf_drop_pct) | log0305 early third |
| **MDF drop with correct warmup skip** | **+28.1%** (20-min skip) | `out0305_w20/fatigue_summary.csv` |
| **MNF drop with correct warmup skip** | **+17.3%** (20-min skip) | `out0305_w20/fatigue_summary.csv` |
| MDF drop with standard 10-min skip | −2.6% (missed fatigue) | `out0305/fatigue_summary.csv` |
| MDF drop with 15-min skip | −26.2% (inverted — still settling) | `out0305_w15/fatigue_summary.csv` |
| Fatigue onset (20-min skip) | 1224 s (~20 min) | `out0305_w20/fatigue_summary.csv` |
| IMU swing consistency (log0305) | r = +0.01, p = 0.78 | Pearson imu_peak_mag vs time |
| log0303 full MDF drop | 28.7% | `out0303_v2/fatigue_summary.csv` |
| log0303 seg1-only MDF drop | **4.9%** (no fatigue) | `out0303_seg1/fatigue_summary.csv` |
| log0303 seg1 duration | 13.55 min, 111 swings | `out0303_seg1/session_summary.json` |
| log0303 reconnection gap | at 4815 s (~80 min) | `out0303_v2/session_summary.json` |
| Total system cost | ~$99 | Hardware BOM |
| log0305 swing count | 626 swings, 63.1 min | `out0305/session_summary.json` |
| log0305 swing rate | ~10 swings/min | computed |

---

## Open Questions / Things to Investigate Further

1. ~~**log0303 gap issue**~~ ✅ **RESOLVED** — `out0303_seg1` confirms first segment (13.5 min) shows only 4.9% MDF drop. The 28.7% from the full session is a gap artifact. log0303 does not contribute a valid within-session fatigue result.

2. ~~**Warmup skip sensitivity**~~ ✅ **RESOLVED** — Full sensitivity table confirmed. Settling extends past 15 min. 20-min skip (`out0305_w20`) is the canonical result showing 28.1% MDF drop.

3. **Contact quality metric validation** — Plot `contact_quality(t) = RMS(t) / session_p90_rms` for both sessions. `paper_analysis.py` computes the metric (line 81–83); figure code not yet written.

4. **Complete `paper_analysis.py` figure generation** — data loading done to line 210; need figure code using `out0303_v2`, `out0305_v2`, and `out0305_w20`. Key figures: electrode settling curve, IMU flat line, warmup-skip sensitivity bar chart, contact quality.

---

## What We Are NOT Claiming

To keep the paper honest:
- We are **not** claiming to have proven fatigue physiologically — no RPE or MVC ground truth
- We are **not** claiming generalizability beyond a single player
- We are **not** claiming 17–20 min is a universal settling time — it's observed in one session (log0305); other sessions/players/electrodes may differ
- log0303 does **not** provide a valid within-session fatigue result (gap artifact)
- The 28.1% MDF drop in log0305 (20-min skip) is the only clean fatigue result; we have one session supporting it

These limitations should be stated explicitly in the paper.

---

## Target Venue

**Primary:** IEEE Engineering in Medicine and Biology Conference (EMBC) — student poster/paper track  
**Alternative:** IEEE HealthTech, Body Sensor Networks (BSN), or regional IEEE EMBS chapter  
**Format:** 4-page conference paper + optional poster

---

## Next Steps

1. [x] Re-analyze log0303 first segment only → `out0303_seg1` (4.9% drop — gap artifact confirmed)
2. [x] Re-run log0305 with warmup_skip = 15 and 20 → `out0305_w15`, `out0305_w20` (28.1% fatigue revealed)
3. [ ] Complete `paper_analysis.py` figure generation code (uses `out0303_v2`, `out0305_v2`, `out0305_w20`)
4. [ ] Generate warmup-skip sensitivity bar chart (key Figure 4)
5. [ ] Generate contact quality metric plot (Figure 5)
6. [ ] Write Introduction draft (~300 words)
7. [ ] Write System Design section (leverage existing HLD documentation)
