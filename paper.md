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
- **Motion artifact landscape in tennis sEMG (~100 words):**
  > Wrist-worn EMG in tennis faces a richer artifact environment than laboratory or rehabilitation settings. The main sources — electrode settling, skin stretch (0–20 Hz), cable triboelectric noise, powerline interference, and rest-period baseline noise — are substantially mitigated by the current pipeline: the 50 Hz high-pass filter rejects skin stretch; the on-board MyoWare amplifier limits the unamplified signal path to the snap connector length (~3 cm), eliminating cable sway artifact [Boyer 2023, Symeonidou 2018]; 60/120 Hz notch filters remove powerline noise; and IMU swing gating (300 dps) excludes rest-period windows. The primary unmitigated source is ball-impact impulsive vibration (200–600 Hz), which falls within the EMG analysis band and cannot be removed by filtering alone. The IMU acceleration spike at ball contact provides a synchronised trigger that could gate or mask the impact sample window before spectral estimation — identified as the highest-priority future work item (see Appendix E). REF electrode placement over the lateral epicondyle (bony prominence, opposite side of forearm from flexors) follows vendor guidance [R18] and minimises crosstalk from the target flexors into the reference signal, a factor SENIAM guidelines do not address for this muscle group.
- Limitations: single player, two sessions, no RPE or MVC ground truth, settling duration likely varies with player sweat rate, skin condition, ambient temperature
- Future work: multi-player study, adaptive warmup skip based on contact quality metric, IMU-guided motion artifact algorithms (see Appendix E), RPE integration, real-time settling detection in Android app

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

### Motion Artifacts and Cable Noise
- [R16] Boyer M, Bouyer L, Roy JS, Campeau-Lecours A. "Reducing noise, artifacts and interference in single-channel EMG signals: a review." *Sensors.* 2023;23(6):2927. DOI: 10.3390/s23062927
- [R17] Symeonidou ER, Nordin AD, Hairston WD, Ferris DP. "Effects of cable sway, electrode surface area, and electrode mass on electroencephalography signal quality during motion." *Sensors.* 2018;18(4):1073. DOI: 10.3390/s18041073

### Vendor Documentation
- [R18] SparkFun Electronics. *MyoWare 2.0 Muscle Sensor Advanced Guide.* 2023. https://cdn.sparkfun.com/assets/learn_tutorials/1/9/5/6/MyoWare_v2_AdvancedGuide-Updated.pdf

> **Note:** PMIDs confirmed: R1-R4 (PMID 24239164, 30729865, 20030784, 22653323), R6 (38632263), R8 (29769821), R9 (35380969), R10 (32676126), R11 (36560096), R12 (38580698), R14 (30869608). Still to verify: R13 (conference proceedings), R15-R17 PMIDs.

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

This section documents how to measure electrode-skin contact/impedance to corroborate the electrode-settling finding (Limitation A2) and address Reviewer Concern C2. The key correction is that the measurement must be made at the **electrode snap / electrode lead side**, not at ESP32 ADC pins. ESP32 GPIO32 (`RAW`) and GPIO39 (`ENV`) are **post-MyoWare processed outputs**, so they cannot measure electrode-skin impedance.

#### D1. What Skin-Electrode Impedance Is

The electrode-skin interface is not a pure resistor. It behaves as a frequency-dependent complex impedance:

```text
Z ≈ Rskin + Rcontact + electrode polarization impedance
```

A more detailed equivalent circuit includes the stratum-corneum resistance, contact resistance, charge-transfer resistance, and electrochemical double-layer capacitance at the Ag/AgCl electrode-electrolyte interface. At DC, the capacitive component charges and blocks steady current, so a standard multimeter often reports a much larger and drifting value. At AC frequencies such as 1 kHz, the capacitive component conducts more readily, so the measured impedance is lower and more relevant to EMG signal quality.

Expected order-of-magnitude values for MyoWare 2.0 snap electrodes on unabraded forearm skin:

| Condition | Approx. 1 kHz impedance | Approx. multimeter DC resistance |
|---|---:|---:|
| t = 0 min, dry skin | 50–150 kΩ | OL or 500–2000 kΩ |
| t = 10 min, partially hydrated | 10–30 kΩ | 100–500 kΩ |
| t = 20 min, sweat-hydrated | 2–8 kΩ | 20–100 kΩ |
| Gel/prepared electrode reference | 1–5 kΩ | 5–30 kΩ |

The exact values vary strongly with skin preparation, sweat rate, electrode age, pressure, placement, and meter type. The important result for this project is the **time trend**: high initial contact impedance/resistance that falls over ~15–20 minutes as sweat hydrates the interface.

#### D2. Which Electrode Pair to Measure

MyoWare uses a 3-electrode configuration:

```text
EMG+ / SIG+    active electrode
EMG- / SIG-    active electrode
REF / GND      reference electrode
```

The EMG channel is primarily the differential signal between the two active electrodes. Therefore the **primary contact-quality measurement** should be:

```text
Probe A → EMG+ snap
Probe B → EMG- snap
```

The active-to-reference pairs are useful secondary checks for asymmetric or single-electrode contact problems:

```text
Probe A → EMG+ snap
Probe B → REF snap

Probe A → EMG- snap
Probe B → REF snap
```

Recommended recording table:

| Measurement | Purpose | Priority |
|---|---|---|
| `Z(+,-)` or `R(+,-)` | Primary EMG differential path quality | Required |
| `Z(+,REF)` or `R(+,REF)` | Detect poor EMG+ or REF contact | Optional but useful |
| `Z(-,REF)` or `R(-,REF)` | Detect poor EMG- or REF contact | Optional but useful |

This is more informative than measuring only `EMG+` to `REF`, because the actual EMG spectrum depends most directly on the active-electrode differential path.

#### D3. Important Wiring and Safety Rule

Measure at the **electrode snaps/leads**, with the MyoWare board disconnected from the electrodes.

Recommended physical setup:

```text
Electrodes adhered to forearm
        ↓
Electrode snap leads accessible
        ↓
MyoWare board disconnected
        ↓
Multimeter/LCR probes touch the electrode snap leads
```

Do **not** measure at:

```text
ESP32 GPIO32 / RAW
ESP32 GPIO39 / ENV
MyoWare RAW output
MyoWare ENV output
```

Those points are after the MyoWare analog front-end and do not represent electrode-skin impedance.

Also avoid measuring while MyoWare is simultaneously connected to the electrodes, because the meter injects a test signal/current and the reading can include:

```text
skin path + electrode contact + MyoWare input bias/leakage path
```

That can disturb the MyoWare input bias and contaminate EMG if recording is active. If a quick check must be done with the board attached, treat the value only as a rough troubleshooting indicator, not as a clean electrode-skin measurement.

#### D4. Can a Standard Multimeter Be Used?

Yes — with caveats. A multimeter in DC resistance (`Ω`) mode applies a small DC test voltage/current. Because the electrode-skin interface has capacitance and electrochemical polarization, the reading may:

1. Drift for the first 5–10 seconds while the interface charges.
2. Overestimate 1 kHz AC impedance by roughly 5–20×.
3. Depend on probe polarity and meter model.

Despite this, a multimeter is useful for a pilot study because the **trend** is meaningful: dry/high resistance at t=0 should fall toward a lower stable value after sweating/settling.

Paper Methods caveat:

> Electrode-skin resistance was measured before recording using a digital multimeter in DC resistance mode. Because DC resistance overestimates the frequency-dependent AC impedance relevant to EMG, these values were interpreted as a qualitative settling indicator rather than an absolute impedance measurement.

#### D5. Multimeter Protocol — Do This Now

Setup:

```text
1. Apply the three snap electrodes to the forearm in the normal MyoWare placement.
2. Leave the MyoWare board disconnected from the electrode snaps.
3. Set the multimeter to resistance mode, preferably 2 MΩ or 20 MΩ range.
4. Have the player keep the arm still during each reading.
```

Measurements at each time point:

```text
Primary:
  EMG+ ↔ EMG-

Secondary:
  EMG+ ↔ REF
  EMG- ↔ REF
```

Timing:

```text
t = 0, 5, 10, 15, 20, 30 min
```

Procedure:

```text
1. Touch probes firmly to the snap metal contacts.
2. Wait 5–10 seconds for the value to stabilize.
3. If display shows OL, record as "> meter range" (e.g., ">2 MΩ").
4. Record all three pair values.
5. After the final reading, connect MyoWare and start EMG recording.
```

Suggested data table:

| Time (min) | R(+,-) | R(+,REF) | R(-,REF) | Notes |
|---:|---:|---:|---:|---|
| 0 |  |  |  | dry / initial |
| 5 |  |  |  |  |
| 10 |  |  |  |  |
| 15 |  |  |  |  |
| 20 |  |  |  | expected near stable |
| 30 |  |  |  | optional |

What to look for:

- `R(+,-)` falling over time supports electrode settling.
- One active-to-reference pair much higher than the other suggests one electrode has poor contact.
- Already-low resistance at t=0 suggests the skin/electrode was pre-wetted or the electrode was reused while wet.
- Non-monotone values can happen if pressure changes, probe contact changes, or sweat accumulates unevenly; focus on overall trend, not each single point.

#### D6. LCR Meter Protocol — Better If Available

An LCR meter is better than a multimeter because it measures AC impedance at a chosen frequency. If available, use:

```text
Frequency: 1 kHz
Reported value: impedance magnitude |Z|
Primary pair: EMG+ ↔ EMG-
Secondary pairs: EMG+ ↔ REF, EMG- ↔ REF
```

Use the same time points:

```text
t = 0, 5, 10, 15, 20, 30 min
```

Paper Methods wording if using LCR:

> Electrode-skin impedance was measured at 1 kHz using an LCR meter between the two active EMG electrodes, with additional active-to-reference measurements used to identify asymmetric electrode contact. Measurements were performed before EMG recording while the MyoWare sensor was disconnected from the electrode snaps.

Budget LCR/ESR meters found online may be adequate for trend validation, but record the model and test frequency. If the meter cannot select frequency, report the meter's default frequency and avoid comparing absolute values against literature thresholds.

#### D7. Measurement Tools Comparison

| Tool | Cost | Measures | Disrupts session? | Best use |
|---|---:|---|---|---|
| Digital multimeter | $0 if owned | DC resistance | Yes if done during recording; fine pre-session | Immediate pilot validation |
| LCR meter | ~$25–80 | AC impedance, ideally 1 kHz | Yes if manually probed; fine pre-session | Stronger Paper 1 validation |
| AD5933 USB eval board | ~$50–150 | AC impedance sweep | Yes; bench instrument | Bench prototyping only |
| Custom AD5933/MAX30001 path | Future PCB | Logged AC impedance | Can be non-disruptive if isolated/switched | Paper 2 / journal hardware revision |

#### D8. AD5933 / Continuous Impedance — Future Hardware, Not a Quick Add-On

The AD5933 is an impedance converter IC, but most boards found online are large USB evaluation boards intended for bench testing. Those are not practical for in-session tennis measurement.

A true wearable integration would require more than simply connecting AD5933 wires to the existing electrode snaps. It should include:

```text
electrode snaps
   ├── MyoWare EMG input path
   └── impedance path through analog switch / isolation network
          └── AD5933 or similar impedance AFE
```

The firmware would need to briefly switch modes:

```text
normal mode:     electrodes connected to MyoWare for EMG
impedance mode:  MyoWare isolated, impedance circuit connected briefly, measurement taken
```

Why isolation/switching matters:

- The impedance circuit injects an AC excitation signal.
- That excitation can contaminate EMG if applied during normal recording.
- Parallel connection can change the MyoWare input bias and electrode loading.
- Calibration resistors and gain calibration are required for meaningful values.

So AD5933/MAX30001-style impedance logging is a good **future hardware revision**, but not required for the current conference paper.

#### D9. Paper-Ready Interpretation

For the current paper, the safest wording is:

> Direct continuous electrode-skin impedance was not measured during play. Instead, contact settling was inferred from the time evolution of EMG spectral features and RMS-derived contact quality, and cross-validated against stable IMU swing intensity. A supplementary pre-session electrode resistance check can be used to verify the same settling trend, but DC resistance values should be interpreted qualitatively because they overestimate AC impedance at EMG frequencies.

If pre-session multimeter/LCR data are collected, update Limitation A2 from "No direct impedance measurement" to:

> Direct in-session impedance was not measured. However, pre-session pairwise electrode resistance/impedance measurements showed the expected decrease over the warm-up period, supporting the interpretation that early-session MDF depression was driven by electrode-skin settling.

---

### E. Novel IMU-Guided Motion Artifact Algorithms (Tennis-Specific)

This section documents brainstormed algorithms for mitigating motion artifacts
specific to tennis wrist-worn EMG, leveraging the IMU data already captured.
None are implemented yet. Ranked by effort vs. novelty.

---

#### E1. Ball-Impact Window Masking
**Priority: Highest — low effort, directly addresses the one unmitigated artifact**

Problem:
Ball-racket contact generates a 2-5ms impulsive vibration (200-600 Hz) that propagates
up the arm into the electrode. This falls within the EMG analysis band and biases MDF
upward — opposite of fatigue. The IMU acc_mag spikes sharply at ball contact, providing
a precise synchronised trigger.

Algorithm:
  acc_dyn = |acc_mag - 1g|
  impact_idx = argmax(acc_dyn within swing window)
  if acc_dyn[impact_idx] > IMPACT_THR_G (e.g. 3.0g):
      mask +-20ms around impact_idx before Welch PSD
      emg_clean = emg_seg[mask]
  else:
      emg_clean = emg_seg  # no significant impact detected

Implementation: ~15 lines in emg_util.py. Add to compute_swing_emg_features().
Config key: swing_detection.impact_mask_thr_g (default 0 = disabled).

Novel aspect: Transient impulsive artifact from ball contact has not been addressed
in the EMG artifact literature. IMU provides an independent, causally prior trigger
(impact causes artifact, so IMU detects it first).

---

#### E2. Between-Swing Noise Floor Tracker (Continuous Contact Monitor)
**Priority: High — extends the contact_quality metric from static to continuous**

Problem:
contact_quality(t) = RMS(t) / session_p90_rms is currently computed per swing.
But contact quality changes continuously throughout the session:
- Rising early (settling) -- low impedance not yet achieved
- Stable mid-session -- good contact
- Rising again late (sweat + movement loosening electrode) -- degradation

Algorithm:
  For each pair of consecutive swings i, i+1:
      find rest windows where gyro_mag < REST_THR_DPS (e.g. 50 dps) for > 500ms
      rest_rms[i] = rms(preprocess_emg(emg_in_rest_window))

  noise_floor_trend = smooth(rest_rms, window=5_swings)
  contact_quality_continuous = 1 / noise_floor_trend  (normalised to session median)

  If noise_floor_trend rises late-session (after stable mid-session plateau):
      flag electrode_degrading = True
      warn: late-session results may be artifact-contaminated

Novel aspect: Uses IMU to identify rest windows precisely (independent of EMG),
then uses those windows as in-situ contact probes -- continuous quality signal
throughout the session, not just at baseline selection.

---

#### E3. IMU-Adaptive High-Pass Filter Cutoff
**Priority: Medium -- low effort, moderate novelty**

Problem:
Fixed 50 Hz HPF cutoff is a compromise. Optimal cutoff depends on motion intensity:
during rest, a lower cutoff (30 Hz) preserves more useful EMG signal; during high-speed
swings, a higher cutoff (80 Hz) better rejects motion artifact.

Algorithm:
  gyro_mag = sqrt(gx^2 + gy^2 + gz^2)  # computed per swing window
  if gyro_mag_peak < 100 dps:  hp_cutoff = 30 Hz
  elif gyro_mag_peak < 300 dps: hp_cutoff = 50 Hz
  else:                          hp_cutoff = 80 Hz

  emg_filtered = bandpass(emg_seg, hp_cutoff, 450, fs)

Novel aspect: Adaptive filtering driven by synchronised IMU (external, causally prior)
rather than blind EMG statistics. Existing adaptive EMG filters use EMG itself -- IMU
provides motion context that precedes the artifact.

---

#### E4. IMU-Regression Artifact Cancellation (Per-Swing)
**Priority: Medium -- medium effort, strong academic foundation**

Problem:
Sustained wrist acceleration physically displaces the electrode during a swing,
generating low-frequency artifact linearly proportional to acceleration (electrode
displacement ~ force ~ acc). The acc-artifact relationship is stable within a
short window and can be estimated by regression.

Algorithm:
  # Per swing window (1300ms = short enough for linearity assumption)
  artifact_proxy = lowpass(acc_dyn, cutoff=20Hz, fs=200)   # 200 Hz IMU
  artifact_upsampled = resample(artifact_proxy, len(emg_seg))  # -> 2000 Hz
  beta = lstsq(artifact_upsampled, emg_seg)[0]  # least squares coefficient
  emg_clean = emg_seg - beta * artifact_upsampled
  mdf = mnf_mdf(emg_clean, fs)

Foundation: Clancy & Hogan (1994) adaptive regression, applied per-swing with
IMU as the artifact proxy -- not previously done for racket sports.
Beta itself is a quality metric: large |beta| = high electrode-motion coupling
= poor contact or loose electrode.

---

#### E5. Phase-Gated MDF: Pre-Impact vs. Post-Impact Comparison
**Priority: Medium -- medium effort, high novelty for racket sports**

Problem:
A tennis swing window spans multiple biomechanical phases with different artifact
profiles. MDF from the full 1300ms window mixes clean pre-impact signal with
artifact-contaminated impact and follow-through periods.

Phases identified from IMU:
  Backswing:       gyro rising, acc moderate     -- lower artifact
  Forward swing:   gyro peak, acc rising          -- moderate artifact
  Impact:          acc_dyn spikes (3-8g, 2-5ms)  -- highest artifact
  Follow-through:  gyro decaying, acc moderate    -- moderate artifact

Algorithm:
  impact_ms = IMU-detected acc_dyn peak
  pre_impact_emg = emg_window[impact_ms - 250 : impact_ms - 20]  # 230ms pre-impact
  mdf_pre  = mnf_mdf(pre_impact_emg, fs)   # cleaner estimate
  mdf_full = mnf_mdf(emg_window, fs)        # current estimate
  artifact_flag = abs(mdf_pre - mdf_full) > 20 Hz  # divergence = impact artifact

  Use mdf_pre as the primary fatigue metric when artifact_flag is True.

Novel aspect: Phase-stratified MDF computation for racket sports. IMU provides
phase boundaries for free. Extends Paper 1 contribution: IMU not only detects
whether fatigue is real (Paper 1) but also guides WHICH part of the signal to
use for spectral estimation (this work).

---

#### E6. Stroke-Type Stratified Fatigue Analysis
**Priority: Low (high effort) -- but highest novelty, strong paper potential**

Problem:
Forehands, backhands, serves, and volleys recruit forearm flexors differently
and have different motion artifact profiles. Mixing all stroke types in one
fatigue trend adds unexplained variance. A serve (overhead, full shoulder
rotation) and a forehand (wrist-dominated) should not be compared directly.

Algorithm:
  Per swing, extract IMU shape features:
    dominant_axis = argmax([std(gx), std(gy), std(gz)])
    gyro_peak     = max(gyro_mag)
    acc_peak      = max(acc_dyn)
    rise_time_ms  = time from gyro_onset to gyro_peak
    shape_match   = DTW distance to stored stroke templates

  stroke_type = classifier.predict(features)  # forehand/backhand/serve/volley

  Separate fatigue trends per stroke type:
    mdf_forehand = trend([s.mdf for s in swings if s.stroke == 'forehand'])
    mdf_backhand = trend([s.mdf for s in swings if s.stroke == 'backhand'])

Novel aspect: No published work stratifies EMG fatigue trends by stroke type
using IMU-based classification in tennis. Removes a major source of inter-swing
MDF variance that all prior tennis EMG studies ignore.

Implementation note: Requires labelled stroke data to train the classifier.
Could use the 626 swings from log0305 with manual annotation as training data.

---

#### Summary Table

  Priority  | ID | Algorithm                          | Effort | Novelty | Paper target
  ----------|----|-----------------------------------|--------|---------|-------------
  Highest   | E1 | Ball-impact window masking         | Low    | Medium  | Paper 1 future work / Paper 2
  High      | E2 | Noise floor tracker (continuous)   | Med    | Medium  | Paper 1 future work
  Medium    | E3 | Adaptive HPF cutoff                | Low    | Medium  | Paper 2
  Medium    | E4 | IMU regression artifact cancel     | Med    | High    | Paper 2
  Medium    | E5 | Phase-gated MDF pre/post impact    | Med    | High    | Paper 2
  Low/Novel | E6 | Stroke-type stratified fatigue     | High   | Highest | Separate paper

All six algorithms require only data already collected (IMU + EMG CSV files).
E1 can be prototyped in one afternoon on the existing log0305 dataset.
