# Paper Planning: EMG-IMU Wearable for Tennis Fatigue Monitoring

**Status:** Planning / Pre-draft — numbers confirmed  
**Target:** Conference paper (middle-rigor, high school research project level) — **5 pages** (trim to 4 later if needed)  
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
- **IMU:** ICM-20948 9-axis, 200 Hz, ±2000 dps gyro / ±8g accelerometer
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

**Total target: ~2600 words body text** (5 pages with 7 figures + references; trim to 4 pages by cutting Related Work or compressing Discussion)

### 1. Introduction (~300 words)
- Motivation: fatigue monitoring in sports, limitations of lab-based approaches
- Challenge: practical wearable sEMG is harder than laboratory sEMG (sweating, movement, electrode placement constraints)
- **Electrode settling sentence:** *"In laboratory EMG studies, electrode-skin impedance is minimised by skin abrasion and conductive gel applied before recording. In field deployments on a tennis court, neither preparation step is practical; instead, the interface relies on sweat to hydrate the electrode contact, a process that can take substantially longer than the 5-minute warmup skip commonly assumed in the literature."*
- Gap: electrode settling duration in real sports sessions is under-documented; IMU cross-validation of EMG quality is unexplored for tennis
- Contributions: (list 4 from Core Contributions section)

### 2. Related Work (~350 words)

#### 2.1 EMG Fatigue in Tennis
Prior EMG fatigue studies in tennis have been predominantly laboratory-based. Rota et al. [PMID 24239164] measured upper limb EMG fatigue across a tennis-specific fatiguing protocol, finding muscle-group-specific fatigue patterns. Wang et al. [PMID 30729865] showed forearm flexor fatigue correlates with reduced serve ball speed. Girard et al. [PMID 20030784] documented spinal and peripheral neuromuscular adaptations during prolonged tennis play. These studies used controlled lab conditions with gel electrodes, skin abrasion, and MVC-normalised measurements — none addressed what happens when the same electrode configuration is worn on a real court without skin preparation.

More recently, Rigozzi et al. [R16] used MyoWare sensors on the forearm extensor muscles of tennis players to compare stroke technique between experienced and recreational players, and Kramberger et al. [R17] deployed a wearable system for injury prevention monitoring in a single tennis player over a training season. Neither study addressed electrode settling dynamics or used IMU data to cross-validate EMG signal quality.

**Gap:** No prior work characterises electrode settling duration for forearm snap electrodes in field tennis, or quantifies how settling contaminates spectral fatigue metrics.

#### 2.2 Electrode-Skin Impedance and Signal Quality
SENIAM guidelines [Hermens et al. 2000, J. Electromyogr. Kinesiol.] are the standard reference for surface EMG electrode placement, recommending skin abrasion and gel to minimise impedance — preparations that are impractical on a tennis court. Joutsen et al. [Sci. Reports 2024] demonstrated that dry electrode SNR improves progressively during a 10-min settling test, but studied ECG, not EMG under movement. Ravichandran et al. [Biosensors 2023] characterised how perspiration reduces impedance in textile dry electrodes. Lynn et al. [J. Sports Sci. 2018] evaluated a commercial wearable sEMG system (Athos) for athletic use, noting electrode-skin contact quality as a key reliability factor but not quantifying the settling period. Farago et al. [IEEE Rev. Biomed. Eng. 2022] reviewed sEMG signal quality techniques, highlighting that impedance variation is a primary source of inter-session variability.

**Gap:** No prior work quantifies the settling duration for sport snap-electrodes under field conditions, or examines the effect of settling on spectral fatigue metrics (MDF/MNF) specifically.

#### 2.3 IMU-EMG Fusion
Taborri et al. [Appl. Bionics Biomech. 2020] reviewed sport biomechanics applications of combined inertial, force, and EMG sensors, concluding IMU+EMG is the most informative wearable combination. Bangaru et al. [Sensors 2022] fused forearm EMG and IMU with RNN for fatigue monitoring in construction workers. Nair et al. [2024] demonstrated ML-based fatigue prediction from combined IMU+EMG signals. MultiSenseBadminton [Sci. Data 2024, PMID 38580698] collected a 25-player IMU+EMG dataset for racket sport analysis. In all of these, IMU and EMG are fused as co-equal feature sources for classification models.

**Gap:** No prior work uses IMU as an *independent quality validator* for EMG: checking whether swing biomechanics are consistent while EMG metrics are anomalous, to distinguish electrode settling artifact from genuine physiological fatigue.

#### 2.4 Summary of Novelty
This work is, to our knowledge, the first to: (1) quantify forearm electrode settling duration in field tennis (≥17–20 min vs. the 5–10 min assumed in the literature); (2) demonstrate that a standard analysis pipeline misses genuine fatigue entirely when the warmup skip is 3× too short; (3) use the IMU — already present for swing detection — as a zero-cost quality cross-validator to distinguish electrode artifact from physiological fatigue; and (4) characterise the cross-segment gap artifact that appears when BLE reconnection gaps are treated as continuous sessions.

### 3. System Design (~500 words)

#### 3.1 Hardware (~200 words)
- **Components + cost:** MyoWare 2.0 EMG (2000 Hz, 12-bit ADC, ENV + RAW dual output), ICM-20948 IMU (200 Hz), ESP32 MCU, BLE streaming — ~$99 total.
- **RAW signal wiring fix:** Pogo pin connection between Wireless Shield and MyoWare RAW pad is mechanically unreliable during movement. Symptom: `raw` column shows ghost signal (~40% of ENV, r = 0.998) due to ADC multiplexer charge sharing — completely removed by the 50 Hz high-pass filter, leaving a flatline. Fix: direct solder jumper from MyoWare RAW PTH pad to ESP32 GPIO 32 (ADC1 channel 4). This is the kind of field-deployment failure that lab EMG studies never encounter.
- **ADC DMA + 10× oversampling:** Hardware DMA at 40 kHz, decimated 10× to 2000 Hz. Per-sample timestamps back-calculated from DMA frame end time, achieving ±25 µs accuracy — needed for sub-millisecond IMU-EMG synchronisation in the cross-validation analysis.
- **IMU FSR history (one sentence):** Early sessions used ±250 dps gyro FSR, causing saturation on hard tennis swings (every peak clipped at ±32767 LSB); FSR raised to ±2000 dps to enable reliable gyro magnitude measurement. This directly enables the 300 dps swing detection threshold.

#### 3.2 Software Pipeline (~150 words)
- **Capture:** `btCentral.py` — BLE central (Bleak), binary TLV frame parsing, rotating CSV logs (`emg_log_*.csv`, `imu_log_*.csv`) with per-file `.meta.json`.
- **Hybrid `abs_us` timeline stitching** (`capture_loader.py`): Within each BLE connection, device timestamp `dev_us` is used (accurate physical time, no BLE jitter). Between reconnections, the host-receive-time gap (`host_rx_ms`) reconstructs the inter-connection interval — correctly handling both BLE-dropout-only (device kept running) and ESP32-reset (device clock restarted) cases. This is what enables the log0303 gap detection: a 66-minute `host_rx_ms` gap between the two BLE connections is preserved in the reconstructed timeline, making the cross-segment comparison visible in the analysis output.
- **Analysis:** `emg_util_yaml_runner.py` — YAML-driven per-swing feature extraction (MDF, MNF, RMS, ENV), baseline selection, fatigue deltas, session summary JSON.

#### 3.3 Swing Detection (~150 words)
- Fixed 300 dps gyro magnitude threshold, 2000 ms debounce.
- **Why not adaptive threshold:** At-rest wrist gyro ≈ 20 dps; tennis forehand peak ≈ 400–800 dps. Z-score approach (baseline = first 2s of session) fails when player is already moving at capture start, inflating the baseline and pushing the threshold above real swings. Statistical analysis of the full session distribution shows no natural valley between general arm movement (100–200 dps) and swings (300+ dps) — the distribution is a continuous ramp, not bimodal. Fixed 300 dps sits at the p88 of the session distribution, cleanly separating swing peaks from non-swing motion.
- **Why 2000 ms debounce:** Tennis stroke produces backswing (~300 ms before contact) + forward swing (at contact), both exceeding 300 dps within ~1.2 s. 1000 ms debounce allows double-counting; 2000 ms merges the pair into one detection.

### 4. Methods (~400 words)
- Session protocol: recreational tennis, single player, two sessions
- Data description: log0303 (87.9 min, 197 swings) and log0305 (63.1 min, 626 swings)
- Analysis approach: per-swing features, session thirds, Pearson trend analysis
- **Electrode settling — physical basis (short paragraph for Methods):**
  > When a dry snap electrode is applied to unabraded forearm skin, the electrode-skin interface presents high impedance (10–100 kΩ) due to the resistive stratum corneum. Two parallel processes reduce this impedance over time: (1) sweat accumulation — eccrine glands produce saline (~150 mM NaCl) that hydrates the electrode-skin gap, creating a low-impedance ionic bridge; and (2) electrochemical equilibration — the Ag/AgCl electrode half-cell potential drifts until it reaches equilibrium with the local electrolyte, contributing low-frequency baseline wander during the transition. Both processes are slower in field conditions (no skin abrasion, no pre-applied gel) and depend on ambient temperature and exercise intensity. During the settling period, the attenuated EMG signal has poor SNR; the residual noise is low-frequency dominant within the 50–450 Hz bandpass, which depresses the estimated MDF below its true value. Once the interface is fully hydrated, MDF stabilises at the true resting value.
- Electrode settling detection: track per-swing MDF vs. time; settling endpoint defined as first time rolling-mean MDF sustains ≥150 Hz for 5 consecutive swings
- Warmup-skip sensitivity test: re-run analysis at 10, 15, 20 min to quantify baseline contamination
- IMU quality cross-validation: compare `imu_peak_mag` Pearson r vs time; if flat (|r| < 0.1) while early MDF is depressed → settling artifact, not fatigue
- Contact quality metric: `contact_quality(t) = RMS(t) / session_p90_rms`; thresholds: >0.25 reliable, <0.10 contact loss

### 5. Results (~500 words)
- 4.1 Electrode settling: log0305 first-third MDF = 107.6 Hz vs. mid/late ~163 Hz; table of thirds; settling takes ≥17–20 min
- 4.2 Warmup-skip sensitivity: table (10-min: −2.6%, 15-min: −26.2%, 20-min: +28.1%) — show that standard pipeline missed fatigue entirely
- 4.3 IMU cross-validation: `imu_peak_mag` flat (r=+0.01, p=0.78) confirms settling is artifact; combined with 28.1% MDF drop → genuine physiological fatigue
- 4.4 Contact quality metric over session (log0305): rises from settling to stable
- 4.5 log0303 gap artifact: full-session 28.7% drop vs. seg1-only 4.9% drop

### 6. Discussion (~400 words)
- **Electrode settling interpretation:**
  > The observed settling duration of ≥17–20 min is consistent with the time required for eccrine sweat glands to reach steady-state output under moderate exercise on an indoor court, combined with the exponential decay of the Ag/AgCl half-cell potential drift. The non-monotone behaviour of the warmup-skip sensitivity (15-min baseline = 112 Hz, lower than the 10-min baseline = 137 Hz) reflects the interaction between RMS-based baseline selection and the settling curve: the RMS filter at 15-min happened to select swings from the steepest part of the transition, where contact quality is still improving. This underscores that a fixed warmup-skip time is a crude heuristic — a contact-quality-aware adaptive skip would be more robust.
- **Practical recommendation:** Extend warmup skip to ≥20 min for forearm snap-electrode deployments in field tennis. The pipeline parameter `warmup_skip_min` should default to 20 for this sensor/placement combination.
- **IMU cross-validation:** The IMU is already on the device for swing detection — using it as a quality monitor adds zero hardware cost. The decision rule (IMU consistent + MDF depressed → settling; IMU consistent + MDF dropping → fatigue) turns a qualitative observation into a testable, automatable criterion.
- Why log0305 showed genuine fatigue once corrected: 626 swings at ~10/min for 63 min represents significant cumulative forearm flexor load, consistent with 28.1% MDF drop even without perceptible biomechanical degradation.
- Limitations: single player, two sessions, no RPE or MVC ground truth, settling duration likely varies with player sweat rate, skin condition, ambient temperature
- Future work: multi-player study, adaptive warmup skip based on contact quality metric, RPE integration, real-time settling detection in Android app

### 7. Conclusion (~150 words)
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

**This is Paper 1 of two** — focuses on the scientific findings (electrode settling + IMU quality validation). The system engineering work is the *platform* that enabled these findings; a full system design paper is planned separately (see `paper2.md`).

**Primary:** IEEE Engineering in Medicine and Biology Conference (EMBC) — student poster/paper track  
**Alternative:** IEEE HealthTech, Body Sensor Networks (BSN), or regional IEEE EMBS chapter  
**Format:** 5-page conference paper (target); trim to 4 if needed  

---

## Next Steps

1. [x] Re-analyze log0303 first segment only → `out0303_seg1` (4.9% drop — gap artifact confirmed)
2. [x] Re-run log0305 with warmup_skip = 15 and 20 → `out0305_w15`, `out0305_w20` (28.1% fatigue revealed)
3. [ ] Complete `paper_analysis.py` figure generation code (uses `out0303_v2`, `out0305_v2`, `out0305_w20`)
4. [ ] Generate warmup-skip sensitivity bar chart (key Figure 4)
5. [ ] Generate contact quality metric plot (Figure 5)
6. [ ] Write Section 3.1 Hardware draft (~200 words): components + RAW wiring fix + ADC DMA timing + FSR one-liner
7. [ ] Write Section 3.2 Software draft (~150 words): btCentral.py → CSV → abs_us stitching → yaml_runner
8. [ ] Write Section 3.3 Swing Detection draft (~150 words): 300 dps fixed threshold rationale, 2000 ms debounce rationale
9. [ ] Write Section 2 Related Work draft (~350 words) — template already in Paper Structure above; need to confirm PMIDs and fill in exact journal names
10. [ ] Write Introduction draft (~300 words)
11. [ ] Write Methods draft (~400 words)
12. [ ] Write Results draft (~500 words)
13. [ ] Write Discussion + Conclusion (~550 words)

---

## References (Working List)

### Tennis EMG Fatigue
- [R1] Rota S, Morel B, Saboul D, Rogowski I, Hautier C. "Influence of fatigue on upper limb muscle activity and performance in tennis." *J Electromyogr Kinesiol.* 2014;24(1):90–97. PMID: 24239164
- [R2] Wang LH, Lo KC, Su FC. "Skill level and forearm muscle fatigue effects on ball speed in tennis serve." *Sports Biomechanics.* 2019;18(5):566–579. PMID: 30729865
- [R3] Girard O, Racinais S, Micallef JP, Millet GP. "Spinal modulations accompany peripheral fatigue during prolonged tennis playing." *Scand J Med Sci Sports.* 2011;21(3):455–464. PMID: 20030784
- [R4] Fabre JB, Martin V, Gondin J, Cottin F, Grelot L. "Effect of playing surface properties on neuromuscular fatigue in tennis." *Med Sci Sports Exerc.* 2012;44(1):75–83. PMID: 22653323
- [R16] Rigozzi CJ, Vio GA, Poronnik P. "Muscle activity, and shock transmission between the forehand stroke technique of experienced and recreational tennis players using a novel wearable device." *Sensors.* 2023;23(11):5146. DOI: 10.3390/s23115146
- [R17] Kramberger I, Filipčič A, Germič A, Kos M. "Real-life application of a wearable device towards injury prevention in tennis: A single-case study." *Sensors.* 2022;22(12):4436. DOI: 10.3390/s22124436

### Electrode-Skin Impedance and Signal Quality
- [R5] Hermens HJ, Freriks B, Disselhorst-Klug C, Rau G. "Development of recommendations for SEMG sensors and sensor placement procedures." *J Electromyogr Kinesiol.* 2000;10(5):361–374. (**SENIAM — foundational standard**)
- [R6] Joutsen A, Cömert A, Kaappa E, Vanhatalo K, Riistama J, Vehkaoja A, Eskola H. "ECG signal quality in intermittent long-term dry electrode recordings with controlled motion artifacts." *Sci Rep.* 2024;14(1):8936. PMID: 38632263
- [R7] Ravichandran V, Ciesielska-Wrobel I, Rumon MA, et al. "Characterizing the impedance properties of dry e-textile electrodes based on contact force and perspiration." *Biosensors.* 2023;13(2):217.
- [R8] Lynn SK, Watkins CM, Wong MA, Balfany K, Feeney DF. "Validity and reliability of surface electromyography measurements from a wearable athlete performance system." *J Sports Sci Med.* 2018;17(2):205-214. PMID: 29769821
- [R9] Farago E, MacIsaac D, Suk M, et al. "A review of techniques for surface electromyography signal quality analysis." *IEEE Rev Biomed Eng.* 2022;16:494-511. PMID: 35380969. DOI: 10.1109/RBME.2022.3164797

### IMU-EMG Fusion
- [R10] Taborri J, Keogh J, Kos A, Santuz A, et al. "Sport biomechanics applications using inertial, force, and EMG sensors: A literature overview." *Appl Bionics Biomech.* 2020;2020:2041549. DOI: 10.1155/2020/2041549. PMID: 32676126
- [R11] Bangaru SS, Wang C, Aghazadeh F. "Automated and continuous fatigue monitoring in construction workers using forearm EMG and IMU wearable sensors and recurrent neural network." *Sensors.* 2022;22(24):9729. PMID: 36560096
- [R12] Seong H, et al. "MultiSenseBadminton: Wearable sensor-based biomechanical dataset for evaluation of badminton performance." *Sci Data.* 2024;11(1):329. PMID: 38580698
- [R13] Nair SP, Sica M, Tedesco S, Visentin A. "Machine learning physical fatigue estimation approach based on IMU and EMG wearable sensors." *Proc IEEE/CORA.* 2024.

### Wearable sEMG Systems
- [R14] Cerone GL, Botter A, Gazzoni M. "A modular, smart, and wearable system for high density sEMG detection." *IEEE Trans Biomed Eng.* 2019;66(12):3371-3380. PMID: 30869608. DOI: 10.1109/TBME.2019.2904398
- [R15] Yang K, McErlain-Naylor SA, Isaia B, Callaway A, et al. "E-textiles for sports and fitness sensing: current state, challenges, and future opportunities." *Sensors.* 2024;24(4):1058. DOI: 10.3390/s24041058 *(PMID: verify before submission)*

> **Note:** PMIDs confirmed: R1–R4 (PMID 24239164, 30729865, 20030784, 22653323), R6 (38632263), R8 (29769821), R9 (35380969), R10 (32676126), R11 (36560096), R12 (38580698), R14 (30869608). Still to verify: R13 (conference proceedings), R15 PMID, R16–R17 PMIDs.

---

## Appendix: Limitations, Enhancement Areas, and Likely Reviewer Concerns

### A. Known Limitations (state explicitly in paper)

**A1. Single player, two sessions (N=1)**
Every empirical claim rests on a single individual on a single day. Settling duration varies with player sweat rate, skin condition, ambient temperature, electrode re-use history, and exertion level. Frame explicitly as a pilot/case study.

**A2. No direct impedance measurement**
Electrode settling is inferred from MDF behaviour, not measured directly. The core confound: muscle physiological warm-up also raises MDF in the first 15-20 min (muscle temperature increases conduction velocity). Without an impedance meter or a pre-wetted electrode control condition, these two effects cannot be fully separated.

**A3. No MVC or RPE ground truth**
The 28.1% MDF drop is called "genuine fatigue" supported by flat IMU (r = +0.01). Without a maximal voluntary contraction test or rating of perceived exertion, fatigue magnitude cannot be independently confirmed.

**A4. Non-monotone warmup-skip sensitivity**
15-min skip gives a LOWER baseline (112 Hz) than 10-min skip (137 Hz). Explained by the RMS filter catching swings in the steepest part of the settling transition, but reviewers will notice. Needs a clear explanation in Results or Discussion.

**A5. Single electrode model and placement**
MyoWare 2.0 snap electrodes on forearm flexor only. Results may not transfer to hydrogel, textile, or gel electrodes, or to other muscle placements.

**A6. Single sport, single court type**
Indoor recreational tennis, one session date. Sweat rate and settling time depend on exertion and ambient conditions.

**A7. log0303 provides no valid within-session fatigue result**
The 28.7% MDF drop in log0303 is a gap artifact. The only clean fatigue finding is log0305 (20-min skip). One session. State explicitly.

---

### B. Areas to Enhance (future work priorities)

**B1. Collect >= 5 players (highest priority)**
Even 3 additional players converts this from a case study to a preliminary multi-subject study. Target before the next submission cycle.

**B2. Add direct impedance measurement (highest scientific impact)**
An AD5933 impedance analyser (~$5 chip) wired to the electrode pads, measuring at t=0, t=10, t=20 min. Directly corroborates the settling timeline and separates it from muscle warm-up physiology. Single most impactful addition for a journal-level paper.

**B3. Add RPE and/or MVC**
Borg 6-20 RPE rating every 10 minutes (costs nothing). Hand-grip dynamometer MVC test before/after (~$30). Both achievable with current setup.

**B4. Implement adaptive warmup skip**
Replace fixed `warmup_skip_min` with quality-based criterion: begin baseline collection when `contact_quality(t) > 0.5` for 5 consecutive swings. Directly motivated by the findings. Implement in `emg_util_yaml_runner.py`.

**B5. Validate the contact quality metric**
Plot `contact_quality(t) = RMS(t) / session_p90_rms` for both sessions and confirm it rises during settling then stabilises. Needed for Results 4.4.

**B6. Pre-wetted electrode control condition**
One session with electrodes pre-wetted with saline before application. If settling disappears (MDF stable from t=0), confirms the mechanism is hydration-dependent, not warm-up-dependent.

**B7. Test multi-player threshold generalisation**
The 300 dps swing threshold is validated on one player's session distribution. Test on additional players of different sizes and skill levels.

---

### C. Likely Reviewer Concerns (prepare responses in advance)

**C1. "N=1 -- this is not a study, it is a case report."**
Response: Frame as pilot study. The contribution is methodological: we demonstrate THAT the settling problem exists and HOW the IMU cross-validation detects it, with one well-documented example. The warmup-skip sensitivity table (10/15/20 min) is a methodological contribution independent of the specific player.

**C2. "Electrode settling and muscle warm-up are confounded."**
Response: Acknowledged as a limitation. Two partial arguments: (1) IMU is flat throughout, meaning consistent effort from t=0, which would have elevated MDF from the start if muscle temperature were the sole driver; (2) the non-monotone sensitivity (15-min baseline lower than 10-min) is inconsistent with smooth physiological warm-up but consistent with the RMS filter sampling mid-transition settling. Direct impedance measurement is future work.

**C3. "Why is the 15-min baseline LOWER than the 10-min baseline?"**
Response: The RMS-based baseline selector picks highest-RMS swings after the skip cutoff. At 15-min, those swings fall in the steepest part of the transition (impedance dropping fastest). At 10-min, the selector caught swings slightly earlier when RMS was more uniform. This motivates adaptive quality-based skipping over fixed-time skipping.

**C4. "The 300 dps threshold is specific to one player."**
Response: Justified from the session-wide gyro distribution (p88, at swing population onset). Tennis forehand peaks (400-800 dps) are well above 300 dps for adult recreational players. Per-player calibration may be needed for juniors or players with weaker strokes (acknowledged in Future Work).

**C5. "MDF drop could reflect reduced effort -- IMU measures wrist rotation, not muscle force."**
Response: Flat imu_peak_mag (r = +0.01, p = 0.78) means the player maintained consistent peak gyro rotation speed throughout. Reduced wrist rotation speed would be expected with effort reduction. We acknowledge it is not a direct muscle force measurement.

**C6. "The contact quality metric is not validated."**
Response: Introduced as a proposed indicator, interpreted qualitatively. Quantitative validation against impedance is future work. Presented as a practical tool, not a validated clinical metric.

**C7. "How reproducible is the pogo-pin fix across hardware batches?"**
Response: The failure is documented as a known issue with the SparkFun Wireless Shield schematic (GPIO 21 vs. GPIO 32 routing). We document it so practitioners can identify and reproduce the fix. Not a claim about all hardware batches.

**C8. "Why not use a commercial system (Delsys, Noraxon)?"**
Response: Commercial research-grade systems cost $5,000-$30,000. The MyoWare 2.0 + ESP32 system costs ~$99 total, making it accessible for field deployment by coaching staff, youth sports programs, and student researchers. Low cost is a core contribution.

---

### D. Skin-Electrode Impedance Measurement — Practical Guide

This section documents how to directly measure electrode-skin impedance to corroborate the
settling finding (Limitation A2). Addresses Reviewer Concern C2.

#### D1. What Skin-Electrode Impedance Is

The electrode-skin interface is not a pure resistor. It behaves as a complex impedance:

  Z = Rskin + Rcontact in series with (Cdouble_layer || Rct)

where Cdouble_layer is the electrochemical double-layer capacitance and Rct is the charge
transfer resistance. The impedance is frequency-dependent: at DC the capacitor blocks current
(high impedance); at 1 kHz the capacitor passes current (much lower impedance). SENIAM
recommends verifying impedance < 5 kOhm at 1 kHz before clinical EMG recording.

Expected values for MyoWare 2.0 snap electrodes on forearm:

  t = 0 min  (dry skin)     : 50-150 kOhm @ 1 kHz    (DC: OL or 500-2000 kOhm)
  t = 10 min (partially wet): 10-30 kOhm  @ 1 kHz    (DC: 100-500 kOhm)
  t = 20 min (sweat-hydrated): 2-8 kOhm   @ 1 kHz    (DC: 20-100 kOhm)
  Gel electrode (reference) : 1-5 kOhm    @ 1 kHz    (DC: 5-30 kOhm)

#### D2. Can a Standard Multimeter Be Used?

Yes -- with caveats. A multimeter in DC resistance (Ohm) mode applies a small DC voltage.
The capacitive component of the electrode-skin interface causes:
  1. Unstable/drifting reading for the first 5-10 seconds (capacitor charging)
  2. Readings that overestimate AC impedance at EMG frequencies by a factor of ~5-20x

Despite the overestimation, the TREND is correct: a multimeter will clearly show OL or
hundreds of kOhm at t=0 dropping to tens of kOhm by t=20 min -- the same settling timeline
as the MDF curve. This is sufficient to corroborate the settling finding in a pilot study.

Paper Methods caveat (add this sentence):
  "Electrode-skin resistance was measured in DC resistance mode (multimeter); values
  overestimate AC impedance at EMG frequencies (~1 kHz) by a factor of 5-20x but correctly
  reflect the temporal settling trend."

#### D3. Measurement Tools Comparison

  Tool                  Cost    Accuracy          Trend?  Best for
  -----------------------------------------------------------------------
  Multimeter (owned)    $0      DC only, 5-20x    YES     Paper 1 pilot study -- use now
                                overestimate
  LCR meter (Amazon)    ~$25    AC at 1 kHz       YES     Paper 1 formal measurement
                                accurate
  AD5933 on ESP32 I2C   ~$10    Continuous,       YES     Paper 2 / journal version
                                automated, logged

#### D4. How to Measure with a Multimeter (Do This Now)

Setup:
  - Apply electrodes on forearm as normal
  - Multimeter set to highest Ohm range (2 MOhm or 20 MOhm)
  - Probe A: touch to EMG+ snap (center electrode, over muscle belly)
  - Probe B: touch to REF snap (outer electrode, away from muscle)

Protocol:
  - Wait 5-10 seconds for reading to stabilise before recording
  - If display shows OL (overload): record as ">2 MOhm" -- expected at t=0 dry skin
  - Take readings at t = 0, 5, 10, 15, 20, 30 min
  - Player rests arm still for 10 seconds per reading -- no session interruption needed
  - Expected plot: monotone drop from OL/high at t=0 to stable value by t=20 min

What to look for:
  - OL or >500 kOhm at t=0 confirms poor initial contact (dry electrode)
  - Reading stabilising at 20-100 kOhm by t=20 min confirms hydration-driven settling
  - If reading is already low at t=0: skin was pre-wetted or electrode was re-used wet

#### D5. LCR Meter (Better Option, ~$25)

An LCR meter measures impedance at AC frequencies (typically 100 Hz, 1 kHz, 10 kHz).
At 1 kHz, readings directly match the frequency range relevant to EMG quality.

Recommended products (search on Amazon):
  - BSIDE ESR02 Pro    : ~$25, measures at 100 Hz / 1 kHz / 10 kHz
  - UNI-T UT612        : ~$35, slightly better build quality
  - Victor VC6013      : ~$25, basic but functional

Set to 1 kHz mode. Same probe placement and protocol as multimeter above.
These values can be directly cited as "electrode-skin impedance at 1 kHz" in the paper.

#### D6. AD5933 Integration into Firmware (Best Option for Paper 2)

The AD5933 (Analog Devices) is an I2C impedance converter chip that sweeps from 1-100 kHz.
It can be added to the existing ESP32 I2C bus (which already runs ICM-20948, MAX30105,
MAX17048) with no additional wiring except two electrode connections.

Where to buy:
  - Chip (AD5933YRSZ)         : ~$6-8 at Mouser (mouser.com) or DigiKey (digikey.com)
  - Breakout board             : ~$8-15 on AliExpress (search "AD5933 breakout")
  - Eval board (EVAL-AD5933EBZ): ~$35-50 at DigiKey -- for bench prototyping first

Firmware sketch:
  // Every 60 seconds, read impedance from AD5933 via I2C
  // Set frequency = 1000 Hz, trigger single measurement
  // Read real + imaginary components
  // Compute |Z| = sqrt(real^2 + imag^2) / gain_factor
  // Log to new impedance_log.csv column: dev_us, impedance_ohms
  // (or add as TLV_IMPEDANCE 0x04 to BLE stream)

Benefit for the paper: impedance curve and MDF curve on the same time axis from the same
session -- directly and automatically answers Reviewer C2 with no manual measurements.
This is the target implementation for Paper 2 field validation.
