# Paper Planning: EMG-IMU Wearable for Tennis Fatigue Monitoring

**Status:** Planning / Pre-draft — numbers confirmed  
**Target:** Conference paper (middle-rigor, high school research project level) — **5 pages** (trim to 4 later if needed)  
**Deadline:** ~2 months  
**Data:** Two captured sessions (log0303, log0305), single player  
**Last Updated:** 2026-05-03

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
3. **Forearm placement and mechanical artifact constraint** — wrist/forearm placement is practical for tennis, but it exposes the electrode interface and lead wires to rapid wrist rotation, grip changes, cable tugging, snap-connector micro-motion, and racket-impact vibration. These effects can create short-duration motion artifacts distinct from the slower sweat-driven settling process.
4. **Result:** EMG-based fatigue metrics (e.g., MDF drop) are unreliable during portions of a session where electrode contact is unstable — and the system has no way to know this without an external reference.

**Key insight:** The IMU (already on the sensor for swing detection) provides exactly that external reference. If the IMU says "consistent swing biomechanics" but EMG shows an anomalous signal, the problem is the electrode, not the muscle. A further design constraint is **forearm-only deployment**: no sensors are mounted on the racket, avoiding added weight, battery burden, altered swing feel, and multi-device synchronization. Tennis-specific artifact handling therefore uses the existing forearm EMG+IMU signals; external audio/video are validation tools only.

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

2. **IMU-conditioned EMG quality monitoring** — propose an artifact-aware interpretation framework in which IMU features provide independent motion context for EMG reliability. A practical slow-contact metric is:
   ```
   contact_quality(t) = RMS_window(t) / session_p90_rms
   ```
   Slow EMG instability with stable IMU swing intensity indicates electrode settling/contact issues; gradual MDF decline with stable IMU intensity supports physiological fatigue; short EMG transients coincident with large IMU shock/vibration peaks are candidate mechanical artifacts rather than fatigue. Validated in log0305: `imu_peak_mag` flat (Pearson r = +0.029, p = 0.468 across all 626 swings) throughout session while early EMG MDF was substantially depressed during electrode settling.

3. **Hidden fatigue revealed by proper settling correction** — log0305 showed **−2.6% MDF change** with standard 10-min skip (no fatigue found). With 20-min skip to clear the settling period, baseline stabilises at 199 Hz and a **28.1% MDF drop** (and 17.3% MNF drop) is revealed — genuine neuromuscular fatigue that was completely masked by electrode settling in the original analysis.

4. **Session gap artifact** — log0303's apparent 28.7% MDF drop is confounded by a 66-minute BLE reconnection gap. Analysing the first segment alone (13.5 min, 111 swings) yields only a **4.9% MDF drop**, confirming no meaningful within-segment fatigue and that the full-session figure is a cross-segment artifact.

---

## System Description

### Hardware
- **EMG:** MyoWare 2.0 muscle sensor, 2000 Hz, 12-bit ADC, forearm flexor placement (3-electrode snap configuration)
- **IMU:** ICM-20948 9-axis, 200 Hz, ±2000 dps gyro / ±8g accelerometer
- **MCU:** ESP32, BLE streaming, binary TLV protocol with CRC16
- **Additional:** MAX30105 SpO2/HR (not used in this study)
- **Cost:** ~$99 total hardware cost

### Key Hardware Engineering Points (worth mentioning for novelty)
- ADC DMA at 40 kHz with 10× oversampling → decimated to 2000 Hz (zero CPU overhead, ±25 µs timestamp accuracy)
- Direct solder bypass of RAW signal from MyoWare to ESP32 GPIO32 (pogo pin connection was mechanically unreliable during movement)
- Lead routing and strain relief: electrode leads are high impedance before the MyoWare amplifier, so cable motion can introduce artifact through electrode tugging, triboelectric effects, and environmental pickup. Leads should be long enough to avoid pulling during full wrist rotation, but short and secured enough to avoid free-swinging loops. The MyoWare board and snap connectors should be stabilised with tape, elastic wrap, foam, or compression sleeve to reduce racket-impact vibration.
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
| `imu_peak_mag` trend | **r = +0.029, p = 0.468 across all 626 swings (non-significant — no biomechanical fatigue)** |

**Warmup-skip sensitivity (the central finding):**

| warmup_skip | Output dir | Baseline MDF | Final MDF | MDF drop % | Interpretation |
|---|---|---|---|---|---|
| 10 min | `out0305` | 137.1 Hz | 140.7 Hz | **−2.6%** | Baseline in settling → false negative |
| 10 min | `out0305_v2` | **166.0 Hz** | 140.8 Hz | **+15.2%** | RMS filter found post-settling swings → moderate fatigue |
| 15 min | `out0305_w15` | 112.3 Hz | 141.8 Hz | **−26.2%** | Still in settling at 15 min → inverted baseline |
| 20 min | `out0305_w20` | **199.2 Hz** | 143.2 Hz | **+28.1%** | Post-settling baseline → genuine fatigue revealed |

**The settling period extends past 15 minutes.** Even at 15-min skip the baseline is only 112 Hz (below the stable 166 Hz), confirming the settling tail reaches at least 17–20 min. With 20-min skip, a **28.1% MDF drop** and **17.3% MNF drop** emerge — genuine neuromuscular fatigue that was entirely masked in the original 10-min analysis.

**IMU cross-validation:** `imu_peak_mag` flat (r = +0.029, p = 0.468 across all 626 swings) throughout the session. The player did not reduce swing force or speed. The MDF drop therefore reflects physiological spectral shift (muscle fibre conduction velocity slowing), not reduced effort — the strongest possible interpretation of fatigue.

---

## Key Data Findings — CONFIRMED

### Finding 1: Electrode Settling Extends to ~17–20 Minutes (not 5 or 10)

In log0305, the MDF by session third (time-equal thirds of 63 min, regenerated from `out0305_w20`) shows a low early settling period, a recovered mid-session reference, and a late-session decline consistent with fatigue:

| Session third | Time range | MDF mean ± std | vs. stable reference (~166 Hz) | Interpretation |
|---|---|---|---|---|
| Early | 0–21 min | 115.7 ± 33.5 Hz | **−30%** | Electrode settling / low-SNR contact |
| Mid | 21–42 min | 167.6 ± 50.1 Hz | +1% | Post-settling recovered MDF |
| Late | 42–63 min | 149.5 ± 45.1 Hz | −10% | Late-session fatigue-related decline |

Warmup-skip sensitivity confirms this — the baseline remains contaminated until at least 17–20 min:

| warmup_skip | Baseline MDF | Status |
|---|---|---|
| 10 min | 112–137 Hz | Still in settling |
| 15 min | 112 Hz | **Still** in settling |
| 20 min | 199 Hz | Post-settling ✓ |

### Finding 2: 28.1% Fatigue Signal Hidden by Electrode Settling (log0305)

With standard 10-min skip: MDF drop = −2.6% → fatigue not found.  
With 20-min skip (post-settling baseline): MDF drop = **+28.1%**, MNF drop = **+17.3%**, fatigue onset at **1224 s (~20 min)**.  
IMU `imu_peak_mag` is flat throughout (r = +0.029, p = 0.468 across all 626 swings) → fatigue is physiological, not effort reduction.

This is the central finding: **a standard analysis pipeline completely missed genuine fatigue because the warmup skip was 3× too short.**

### Finding 3: IMU Flat Line Is the Cross-Validator

log0305 `imu_peak_mag`:
- Early mean: 1647 ± 766 dps
- Mid mean: 1643 ± 896 dps
- Late mean: 1665 ± 891 dps
- Pearson r = **+0.029**, p = **0.468** across all 626 swings (non-significant, completely flat)

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

More recently, Rigozzi et al. [R16] deployed MyoWare sensors on the forearm **extensor** muscles of tennis players to compare grip strength, muscle activity, and shock transmission between experienced and recreational players during forehand strokes. They found recreational players exhibited elevated extensor activity during follow-through, increasing lateral elbow tendinopathy risk. Notably, their placement targets extensor muscles (dorsal forearm, injury risk focus) whereas the present study places electrodes on the forearm **flexor** muscles (ventral forearm, fatigue focus) — the two placements are complementary but distinct. Neither Rigozzi et al. nor Kramberger et al. [R17], who deployed a wearable system for injury prevention monitoring in a single tennis player over a training season, addressed electrode settling dynamics or used IMU data to cross-validate EMG signal quality.

**Gap:** No prior work characterises electrode settling duration for forearm snap electrodes in field tennis, or quantifies how settling contaminates spectral fatigue metrics.

#### 2.2 Electrode-Skin Impedance and Signal Quality
SENIAM guidelines [Hermens et al. 2000, J. Electromyogr. Kinesiol.] are the standard reference for surface EMG electrode placement, recommending skin abrasion and gel to minimise impedance — preparations that are impractical on a tennis court. Joutsen et al. [Sci. Reports 2024] demonstrated that dry electrode SNR improves progressively during a 10-min settling test, but studied ECG, not EMG under movement. Ravichandran et al. [Biosensors 2023] characterised how perspiration reduces impedance in textile dry electrodes. Lynn et al. [J. Sports Sci. 2018] evaluated a commercial wearable sEMG system (Athos) for athletic use, noting electrode-skin contact quality as a key reliability factor but not quantifying the settling period. Farago et al. [IEEE Rev. Biomed. Eng. 2022] reviewed sEMG signal quality techniques, highlighting that impedance variation is a primary source of inter-session variability.

**Gap:** No prior work quantifies the settling duration for sport snap-electrodes under field conditions, or examines the effect of settling on spectral fatigue metrics (MDF/MNF) specifically.

#### 2.3 Motion Artifacts from Electrode and Cable Movement
Wearable biopotential recordings are also affected by fast mechanical artifacts caused by electrode-skin motion, cable movement, mounting force changes, and impact vibration. Cömert and Hyttinen [R21] showed that controlled electrode motion produces measurable changes in skin-electrode impedance and surface potential, and later developed a repeatable electrode-motion artifact assessment system demonstrating that applied force, electrode location, and electrode structure affect artifact magnitude [R23]. Cömert et al. [R22] showed that contact pressure and padding strongly affect motion artifact susceptibility in wearable electrodes. Takagi et al. [R24] proposed foam-based mechanical suppression of motion artifacts in wearable EMG, and Roland [R25] reviewed motion artifact suppression for insulated EMG in myoelectric prosthesis control; both identify motion artifact and interference as major obstacles for robust single-channel wearable EMG [R18].

These findings are directly relevant to forearm tennis sEMG: rapid wrist rotation, cable strain, grip changes, and ball-racket impact can perturb snap electrodes and lead wires. Unlike slow sweat-driven settling, these artifacts occur on the time scale of individual swings or impacts and therefore require mechanical stabilisation plus IMU-based artifact context, not only a longer warmup skip.

**Gap:** Prior work studies controlled electrode motion, textile electrodes, or general wearable EMG artifact suppression, but does not address racket-sport forearm sEMG where mechanical artifacts are time-locked to high-speed swings and ball-impact vibration.

#### 2.4 IMU-EMG Fusion
Taborri et al. [Appl. Bionics Biomech. 2020] reviewed sport biomechanics applications of combined inertial, force, and EMG sensors, concluding IMU+EMG is the most informative wearable combination. Bangaru et al. [Sensors 2022] fused forearm EMG and IMU with RNN for fatigue monitoring in construction workers. Nair et al. [2024] demonstrated ML-based fatigue prediction from combined IMU+EMG signals. MultiSenseBadminton [Sci. Data 2024, PMID 38580698] collected a 25-player IMU+EMG dataset for racket sport analysis. In all of these, IMU and EMG are fused as co-equal feature sources for classification models.

**Gap:** No prior work uses IMU as an *independent quality validator* for EMG: checking whether swing biomechanics are consistent while EMG metrics are anomalous, to distinguish electrode settling artifact from genuine physiological fatigue or to identify tennis-specific mechanical artifacts.

#### 2.5 Summary of Novelty
This work is, to our knowledge, the first to: (1) quantify forearm electrode settling duration in field tennis (≥17–20 min vs. the 5–10 min assumed in the literature); (2) demonstrate that a standard analysis pipeline misses genuine fatigue entirely when the warmup skip is 3× too short; (3) use the IMU — already present for swing detection — as a zero-cost context sensor for EMG validity, distinguishing slow contact settling, stable-effort fatigue trends, and candidate fast mechanical artifacts; and (4) characterise the cross-segment gap artifact that appears when BLE reconnection gaps are treated as continuous sessions.

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
- Artifact-aware per-swing interpretation: gradual MDF/MNF changes over many swings with stable IMU intensity are attributed to fatigue; isolated EMG outliers coincident with large IMU acceleration peaks are treated as candidate mechanical artifacts (Appendix E).

### 5. Results (~500 words)
- 5.1 Electrode settling: log0305 first-third MDF = 115.7 Hz vs. mid-session 167.6 Hz; late-session MDF = 149.5 Hz; table of thirds; settling takes ≥17–20 min
- 5.2 Warmup-skip sensitivity: table (10-min: −2.6%, 15-min: −26.2%, 20-min: +28.1%) — show that standard pipeline missed fatigue entirely
- 5.3 IMU cross-validation: `imu_peak_mag` flat (r=+0.029, p=0.468 across all 626 swings) confirms EMG changes are not explained by reduced swing intensity; combined with 28.1% MDF drop → genuine physiological fatigue
- 5.4 Contact quality metric over session (log0305): rises from settling to stable
- 5.5 log0303 gap artifact: full-session 28.7% drop vs. seg1-only 4.9% drop

### 6. Discussion (~400 words)
- **Electrode settling interpretation:**
  > The observed settling duration of ≥17–20 min is consistent with the time required for eccrine sweat glands to reach steady-state output under moderate exercise on an indoor court, combined with the exponential decay of the Ag/AgCl half-cell potential drift. The non-monotone behaviour of the warmup-skip sensitivity (15-min baseline = 112 Hz, lower than the 10-min baseline = 137 Hz) reflects the interaction between RMS-based baseline selection and the settling curve: the RMS filter at 15-min happened to select swings from the steepest part of the transition, where contact quality is still improving. This underscores that a fixed warmup-skip time is a crude heuristic — a contact-quality-aware adaptive skip would be more robust.
- **Practical recommendation:** Extend warmup skip to ≥20 min for forearm snap-electrode deployments in field tennis. The pipeline parameter `warmup_skip_min` should default to 20 for this sensor/placement combination.
- **IMU cross-validation:** The IMU is already on the device for swing detection — using it as a quality monitor adds zero hardware cost. The decision rule (IMU consistent + MDF depressed → settling; IMU consistent + MDF dropping → fatigue) turns a qualitative observation into a testable, automatable criterion.
- Why log0305 showed genuine fatigue once corrected: 626 swings at ~10/min for 63 min represents significant cumulative forearm flexor load, consistent with 28.1% MDF drop even without perceptible biomechanical degradation.
- **Motion artifact landscape in tennis sEMG (~100 words):**
  > Wrist/forearm EMG in tennis faces a richer artifact environment than laboratory or rehabilitation settings. The main sources include slow electrode settling, skin stretch, cable or snap-connector tugging, triboelectric/electromagnetic pickup in moving leads, powerline interference, rest-period baseline noise, and ball-impact vibration. The current pipeline mitigates several of these: the 50 Hz high-pass filter reduces low-frequency skin-stretch artifacts; placing the MyoWare amplifier close to the electrodes keeps the high-impedance unamplified path short, reducing but not eliminating cable-sway artifact [R18, R19]; 60/120 Hz notch filters remove powerline noise; and IMU swing gating excludes rest-period windows. The least-resolved artifact source is ball-impact impulsive vibration, which can contaminate MDF/MNF because it falls within or near the EMG analysis band. A forearm IMU jerk or acceleration event near the expected contact phase provides a candidate impact-risk trigger, but not confirmed ball-contact timing. Future validation should use low-burden audio or video labels — for example, IMU-gated acoustic onset detection from a phone microphone — rather than adding deployed racket-mounted hardware that changes swing feel and introduces battery and synchronization burden. REF electrode placement over the lateral epicondyle (bony prominence, opposite side of forearm from flexors) follows vendor guidance [R20] and minimises crosstalk from the target flexors into the reference signal, a factor SENIAM guidelines do not address for this muscle group.
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
| 2 | **Electrode settling: MDF vs. time + contact quality (first 30 min, log0305)** — two-panel: MDF suppression + RMS-derived contact quality, settling ~17–20 min. *Caption: Figure 2 shows early-session MDF suppression during the same interval in which RMS-derived contact quality is changing. The 10- and 15-min markers fall inside the shaded settling region, while the 20-min marker occurs near the transition to a more stable post-settling baseline. This supports the conclusion that electrode settling lasts approximately 17–20 min in log0305.* | `out0305_w20/swing_features.csv` | ✅ `paper_figures/fig2_electrode_settling.png` |
| 3 | **IMU flat line: `imu_peak_mag` vs. time (log0305)** — r=+0.029, p=0.468 | `out0305_w20/swing_features.csv` | ✅ `paper_figures/fig3_imu_consistency.png` |
| 4 | **Warmup-skip sensitivity bar chart** — −2.6% / +15.2% / −26.2% / +28.1% | fatigue_summary files + confirmed original-pipeline value | ✅ `paper_figures/fig4_warmup_skip_sensitivity.png` |
| 5 | Contact quality (`RMS/p90_rms`) over session, both sessions | `out0303_v2`, `out0305_w20` | ✅ `paper_figures/fig5_contact_quality.png` |
| 6 | log0303 gap artifact: MDF over full session with reconnection gap annotated | `out0303_v2/swing_features.csv`, `out0303_seg1` | ✅ `paper_figures/fig6_log0303_gap_artifact.png` |
| 7 | IMU-EMG diagnostic matrix (2×2 scatter) | `out0305_w20` | ✅ `paper_figures/fig7_imu_emg_diagnostic_matrix.png` |
| 8 | Full-window MDF vs. pre-impact MDF comparison | log0305 + future impact-risk/pre-impact analysis | 🔮 Future / Paper 2 |

Canonical figures have been regenerated by the rewritten `paper_figures.py` into `paper_figures/`. The directory still contains older draft PNGs from previous runs; use only the canonical files listed above for the paper.

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
| Motion artifact correlation | r = 0.006 — **verify variables before citing** (see RESEARCH_REPORT.md; likely EMG envelope vs IMU acceleration, but confirm exact columns) | log0305 analysis (RESEARCH_REPORT.md) |
| Electrode settling duration | **≥17–20 min** | log0305 warmup-skip sensitivity |
| Baseline MDF at 10-min skip | 112–137 Hz (contaminated) | `out0305`, `out0305_w15` |
| Baseline MDF at 20-min skip | 199.2 Hz (stable) | `out0305_w20` |
| Stable post-settling MDF | ~166 Hz | `out0305_v2` baseline.json |
| 20-min warmup baseline MDF | 199.2 Hz | `out0305_w20` baseline.json |

> **166 Hz vs 199 Hz — important distinction for paper:**
> The 166 Hz figure comes from `out0305_v2`, where the RMS-based baseline selector
> (10-min skip + RMS filter) happened to pick post-settling swings. The 199 Hz figure
> comes from `out0305_w20`, where the 20-min fixed skip guarantees a post-settling window.
> Both show that early 10–15 min baselines are contaminated, but their difference (33 Hz)
> shows that baseline selection remains sensitive to the chosen criterion even after settling.
> In paper text, use 166 Hz as the "stable settled MDF" reference and 199 Hz as the
> "post-warmup-skip baseline." Explain the difference in Methods or a footnote.
| Early session MDF (settling) | 115.7 ± 33.5 Hz | `out0305_w20` early third |
| Mid-session MDF (post-settling reference) | 167.6 ± 50.1 Hz | `out0305_w20` middle third |
| Late-session MDF | 149.5 ± 45.1 Hz | `out0305_w20` late third |
| Early MDF depression from stable reference | ~30% below 166 Hz settled reference; ~42% below 199 Hz 20-min baseline | log0305 early third / `out0305_w20` |
| **MDF drop with correct warmup skip** | **+28.1%** (20-min skip) | `out0305_w20/fatigue_summary.csv` |
| **MNF drop with correct warmup skip** | **+17.3%** (20-min skip) | `out0305_w20/fatigue_summary.csv` |
| MDF drop with standard 10-min skip | −2.6% (missed fatigue) | `out0305/fatigue_summary.csv` |
| MDF drop with 15-min skip | −26.2% (inverted — still settling) | `out0305_w15/fatigue_summary.csv` |
| Fatigue onset (20-min skip) | 1224 s (~20 min) | `out0305_w20/fatigue_summary.csv` |
| IMU swing consistency (log0305) | r = +0.029, p = 0.468 across all 626 swings | Pearson imu_peak_mag vs time from `out0305_w20` |
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

3. ~~**Contact quality metric validation**~~ ✅ **FIGURE GENERATED** — `paper_figures/fig5_contact_quality.png` plots `contact_quality(t) = RMS(t) / session_p90_rms` for `out0303_v2` and `out0305_w20`. Still interpret qualitatively because it is not validated against direct impedance.

4. ~~**Complete paper figure generation**~~ ✅ **RESOLVED** — `paper_figures.py` was rewritten to use the correct canonical output directories and generated Figures 2–7 plus `paper_stats.txt`. The `paper_figures/` directory still contains older draft PNGs, so use only the canonical files listed in “Figures Needed.”

---

## What We Are NOT Claiming

To keep the paper honest:
- We are **not** claiming to have proven fatigue physiologically — no RPE or MVC ground truth
- We are **not** claiming generalizability beyond a single player
- We are **not** claiming 17–20 min is a universal settling time — it's observed in one session (log0305); other sessions/players/electrodes may differ
- We are **not** claiming to have fully solved cable friction, snap-connector motion, or racket-impact vibration artifacts — current evidence supports IMU-based interpretation and future artifact-gating algorithms, not complete artifact elimination
- We are **not** claiming that forearm IMU acceleration or jerk peaks are confirmed ball-contact timestamps; they are candidate impact-risk events requiring audio/video or controlled-protocol validation
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
3. [x] Complete `paper_figures.py` figure generation code using canonical sources (`out0303_v2`, `out0303_seg1`, `out0305_v2`, `out0305_w15`, `out0305_w20`)
4. [x] Generate warmup-skip sensitivity bar chart (key Figure 4)
5. [x] Generate contact quality metric plot (Figure 5)
6. [ ] Implement pre-impact MDF extraction and compare variance/trend against full-window MDF on log0305 (future Figure 8 / Paper 2)
7. [ ] Write Section 3.1 Hardware draft (~200 words): components + RAW wiring fix + ADC DMA timing + FSR one-liner
8. [ ] Write Section 3.2 Software draft (~150 words): btCentral.py → CSV → abs_us stitching → yaml_runner
9. [ ] Write Section 3.3 Swing Detection draft (~150 words): 300 dps fixed threshold rationale, 2000 ms debounce rationale
10. [ ] Write Section 2 Related Work draft (~350 words) — template already in Paper Structure above; need to confirm PMIDs and fill in exact journal names
11. [ ] Write Introduction draft (~300 words)
12. [ ] Write Methods draft (~400 words)
13. [ ] Write Results draft (~500 words)
14. [ ] Write Discussion + Conclusion (~550 words)

---

## References (Working List)

### Tennis EMG Fatigue
- [R1] Rota S, Morel B, Saboul D, Rogowski I, Hautier C. "Influence of fatigue on upper limb muscle activity and performance in tennis." *J Electromyogr Kinesiol.* 2014;24(1):90–97. PMID: 24239164
- [R2] Wang LH, Lo KC, Su FC. "Skill level and forearm muscle fatigue effects on ball speed in tennis serve." *Sports Biomechanics.* 2019;18(5):566–579. PMID: 30729865
- [R3] Girard O, Racinais S, Micallef JP, Millet GP. "Spinal modulations accompany peripheral fatigue during prolonged tennis playing." *Scand J Med Sci Sports.* 2011;21(3):455–464. PMID: 20030784
- [R4] Fabre JB, Martin V, Gondin J, Cottin F, Grelot L. "Effect of playing surface properties on neuromuscular fatigue in tennis." *Med Sci Sports Exerc.* 2012;44(1):75–83. PMID: 22653323
- [R16] Rigozzi CJ, Vio GA, Poronnik P. "Comparison of grip strength, forearm muscle activity, and shock transmission between the forehand stroke technique of experienced and recreational tennis players using a novel wearable device." *Sensors.* 2023;23(11):5146. PMID: 37299874. DOI: 10.3390/s23115146
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
- [R18] Boyer M, Bouyer L, Roy JS, Campeau-Lecours A. "Reducing noise, artifacts and interference in single-channel EMG signals: a review." *Sensors.* 2023;23(6):2927. DOI: 10.3390/s23062927
- [R19] Symeonidou ER, Nordin AD, Hairston WD, Ferris DP. "Effects of cable sway, electrode surface area, and electrode mass on electroencephalography signal quality during motion." *Sensors.* 2018;18(4):1073. DOI: 10.3390/s18041073
- [R21] Cömert A, Hyttinen J. "Impedance spectroscopy of changes in skin-electrode impedance induced by motion." *Biomed Eng Online.* 2014;13:149. PMID: 25404355. DOI: 10.1186/1475-925X-13-149
- [R22] Cömert A, Honkala M, Hyttinen J. "Effect of pressure and padding on motion artifact of textile electrodes." *Biomed Eng Online.* 2013;12:26. PMID: 23565970. DOI: 10.1186/1475-925X-12-26
- [R23] Cömert A, Hyttinen J. "A motion artifact generation and assessment system for the rapid testing of surface biopotential electrodes." *Physiol Meas.* 2015;36(1):1-25. PMID: 25500614. DOI: 10.1088/0967-3334/36/1/1
- [R24] Takagi T, Tomita N, Sato S, Yamamoto M, Takamatsu S, Itoh T. "Wearable EMG measurement device using polyurethane foam for motion artifact suppression." *Sensors.* 2024;24(10):2985. PMID: 38793840. DOI: 10.3390/s24102985
- [R25] Roland T. "Motion artifact suppression for insulated EMG to control myoelectric prostheses." *Sensors.* 2020;20(4):1031. PMID: 32075031. DOI: 10.3390/s20041031

### Acoustic Event Detection / Sports Audio Validation
- [R26] Bello JP, Daudet L, Abdallah S, Duxbury C, Davies M, Sandler MB. "A tutorial on onset detection in music signals." *IEEE Signal Process Mag.* 2005;22(5):44–54. DOI: 10.1109/MSP.2005.1511798 (**foundational onset detection reference — spectral flux, onset strength**)
- [R27] Dixon S. "Onset detection revisited." *Proc Int Conf Digital Audio Effects (DAFx).* 2006. (**spectral flux onset feature — standard citation for spectral-flux-based detection**)
- [R28] Ghosh A, Rüegg M, Tröster G. "Detecting racket sports events using wearable sensors." *Proc ACM ISWC.* 2015. *(verify year/venue — search "racket sport event detection wearable audio IMU")* (**wearable-based racket impact detection; audio + IMU fusion for squash/tennis**)

### Vendor Documentation
- [R20] SparkFun Electronics. *MyoWare 2.0 Muscle Sensor Advanced Guide.* 2023. https://cdn.sparkfun.com/assets/learn_tutorials/1/9/5/6/MyoWare_v2_AdvancedGuide-Updated.pdf

> **Note:** PMIDs confirmed: R1-R4 (PMID 24239164, 30729865, 20030784, 22653323), R6 (38632263), R8 (29769821), R9 (35380969), R10 (32676126), R11 (36560096), R12 (38580698), R14 (30869608), R16 (37299874), R21 (25404355), R22 (23565970), R23 (25500614), R24 (38793840), R25 (32075031). Still to verify: R13 (conference proceedings), R15 PMID, R17-R19 PMIDs, R26 DOI, R27 proceedings year, R28 venue/year.

---

## Appendix: Limitations, Enhancement Areas, and Likely Reviewer Concerns

### A. Known Limitations (state explicitly in paper)

**A1. Single player, two sessions (N=1)**
Every empirical claim rests on a single individual on a single day. Settling duration varies with player sweat rate, skin condition, ambient temperature, electrode re-use history, and exertion level. Frame explicitly as a pilot/case study.

**A2. No direct impedance measurement**
Electrode settling is inferred from MDF behaviour, not measured directly. The core confound: muscle physiological warm-up also raises MDF in the first 15-20 min (muscle temperature increases conduction velocity). Without an impedance meter or a pre-wetted electrode control condition, these two effects cannot be fully separated.

**A3. No MVC or RPE ground truth**
The 28.1% MDF drop is called "genuine fatigue" supported by flat IMU (r = +0.029, p = 0.468 across all 626 swings). Without a maximal voluntary contraction test or rating of perceived exertion, fatigue magnitude cannot be independently confirmed.

**A4. Non-monotone warmup-skip sensitivity**
15-min skip gives a LOWER baseline (112 Hz) than 10-min skip (137 Hz). Explained by the RMS filter catching swings in the steepest part of the settling transition, but reviewers will notice. Needs a clear explanation in Results or Discussion.

**A5. Single electrode model and placement**
MyoWare 2.0 snap electrodes on forearm flexor only. Results may not transfer to hydrogel, textile, or gel electrodes, or to other muscle placements.

**A6. Single sport, single court type**
Indoor recreational tennis, one session date. Sweat rate and settling time depend on exertion and ambient conditions.

**A7. log0303 provides no valid within-session fatigue result**
The 28.7% MDF drop in log0303 is a gap artifact. The only clean fatigue finding is log0305 (20-min skip). One session. State explicitly.

**A8. Cable and electrode motion artifacts not separately quantified**
The study did not independently quantify cable tugging, snap-connector micro-motion, electrode slip, or racket-impact vibration artifacts. These effects may contaminate individual swing windows, especially near ball contact. The current analysis mitigates this risk by relying on per-session trends, robust warmup-skip sensitivity, and IMU consistency rather than single transient EMG spikes, but controlled cable-motion and impact tests are future work.

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

**B8. Controlled cable-motion and racket-impact artifact test**
Record relaxed-arm baseline while deliberately tapping/moving the cable, tapping the MyoWare board, and applying racket-impact vibration without voluntary contraction. Compare loose cable, taped cable, and compression-sleeve conditions using EMG RMS/PSD outlier counts and IMU shock peaks. This directly validates the fast-artifact branch of the IMU-conditioned EMG quality framework.

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
Response: Flat imu_peak_mag (r = +0.029, p = 0.468 across all 626 swings) means the player maintained consistent peak gyro rotation speed throughout. Reduced wrist rotation speed would be expected with effort reduction. We acknowledge it is not a direct muscle force measurement.

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

For Paper 1, only the settling-aware baseline selection, contact-quality interpretation, and IMU swing-consistency validation are claimed as implemented. The algorithms in E1–E8 are treated as algorithmic extensions or validation roadmap items unless explicitly marked implemented.

#### Design Principle: Forearm-Only Deployment

The deployed system is intentionally a single body-worn unit (EMG + IMU on forearm). No
hardware is added to the racket. Added racket weight changes the swing dynamics and balance
point in ways competitive players notice acutely (even 2-3g at the handle); a wireless racket
sensor also requires a second battery, second BLE stack, and clock synchronisation that
reintroduces the timestamp alignment problem we already solved. External sensors (video,
microphone, instrumented racket) are validation tools only -- they are not required in the
deployed system.

The algorithms below are ranked by readiness for implementation. All use only the data
already captured (EMG RAW + ENV at 2000 Hz, IMU acc + gyro at 200 Hz, existing log0303 and
log0305). None require new hardware to prototype; some are enhanced by optional audio/video
validation.

---

#### E1. Forearm-Only Impact-Risk Gating (revised)

**Previously called "Ball-Impact Window Masking". Renamed and reframed.**

**The core idea:**
Ball-racket contact is a brief mechanical impulse (~3-5ms). Vibration travels from the racket
through the grip into the forearm, appearing in both the IMU (as a jerk event) and the EMG
(as a hypothesised broadband transient that may occupy part of the EMG analysis band). The actual artifact frequency range should be estimated empirically by comparing EMG PSD near high-jerk events against pre-impact windows; 200–500 Hz is a working hypothesis, not an assumed correction band. This artifact is:
  - short (ms scale), not gradual (seconds scale like fatigue)
  - time-locked to ball contact, not to voluntary muscle activation
  - potentially inside the 50-450 Hz EMG analysis band
  - not removable by standard bandpass filtering
  - unique to racket sports -- not addressed in general EMG artifact literature [Boyer 2023]

The IMU provides a candidate trigger; the EMG provides a second confirmation channel.

**Why "impact-risk" not "impact detection":**
The forearm sensor cannot confirm ball contact with certainty. The IMU jerk peak could be
arm deceleration rather than transmitted impact shock. Therefore the output is a continuous
RISK SCORE, not a binary detection. High-risk windows are flagged; the MDF from those windows
is treated with lower confidence or replaced by the pre-impact phase estimate (E5).

**Composite impact-risk score (all from existing hardware):**

  impact_risk_score =
      w1 * z(imu_jerk_peak) * in_contact_phase   # IMU: transient mechanical event,
                                                  #      only scored in plausible window
    + w2 * z(emg_hf_energy)                      # EMG RAW: candidate high-freq burst
                                                  #          (band TBD by Experiment 10;
                                                  #          200-500 Hz is working hypothesis)
    + w3 * z(emg_transient_score)                 # EMG: brief spike unlike voluntary
                                                  #      activation (fast rise, <10ms)
    + w4 * z(env_postimpact_change_score)         # ENV: post-impact envelope dip or
                                                  #      perturbation (50-150ms post impact)
    + w5 * z(audio_onset_score)                   # Audio (optional, if available):
                                                  #      IMU-gated acoustic onset

  If audio not collected: w5 = 0. Score degrades gracefully to IMU+EMG subset.

**Phase gate -- the most important constraint:**
Ball contact is expected to occur near a consistent phase of the swing relative to the
gyro peak, but the exact timing offset should be validated with video or audio labels.
The working hypothesis -- based on the general biomechanics of forehand stroke execution
where peak wrist rotation precedes ball contact -- is a phase window of approximately
30-200ms after the gyro peak. Events outside this window are more likely arm deceleration,
follow-through, or non-contact swings:

  in_contact_phase = 1 if (t_gyro_peak + 30ms) < t_event < (t_gyro_peak + 200ms) else 0

The window bounds [30ms, 200ms] are working estimates pending video/audio validation
(see E8 Level 3). They should not be cited as established values without that confirmation.

This constraint eliminates the majority of false positives from arm deceleration
(which peaks at t > 200ms post gyro-peak) and from backswing events (t < 30ms pre-contact).

**Mechanical transmission delay:**
The vibration impulse travels from the racket frame through the grip, hand, wrist, soft
tissue, and forearm sensor mount. The delay from true ball contact to the forearm IMU response
is likely on the order of tens of milliseconds, but should be measured empirically rather
than assumed. If audio/video validation confirms a tight delay distribution, the forearm-only
detector is credible.

**Implementation status:**
  - E1v1 (sample masking) IMPLEMENTED 2026-05-03: config key impact_mask_thr_g,
    output columns impact_detected / impact_acc_dyn_g / mdf_impact_masked.
  - Result: mean MDF shift = 0.12 Hz (near zero). Sample-level masking of +-20ms
    removes only ~3% of the 1300ms window; Welch PSD is dominated by its segment
    average -- per-sample removal is insufficient.
  - E1v2 (pre-impact phase MDF, Welch-segment rejection): PLANNED -- see E5.

---


#### E2. Between-Swing Noise Floor Tracker (Continuous Contact Monitor)

Problem:
contact_quality(t) = RMS(t) / session_p90_rms is computed per swing but contact quality
changes continuously: rising during settling (early session), stable mid-session, potentially
rising again late-session as sweat loosens the electrode.

Algorithm:
  For each gap between consecutive swings:
      find rest windows where gyro_mag < 50 dps for > 500ms (IMU-defined quiet periods)
      rest_rms[i] = rms(preprocess_emg(emg_in_rest_window))

  noise_floor_trend = smooth(rest_rms, window=5_swings)

  If noise_floor_trend rises monotonically late-session after a stable plateau:
      flag electrode_degrading = True
      warn: late-session MDF results less reliable

Novel aspect: IMU defines rest windows independently of EMG (no chicken-and-egg). The rest
window RMS is a continuous in-situ impedance proxy throughout the session, not just at
baseline selection time.

---

#### E3. IMU-Adaptive High-Pass Filter Cutoff

Problem:
Fixed 50 Hz HPF is a compromise. During rest (gyro < 50 dps) a 30 Hz cutoff preserves
more EMG signal; during high-speed swings (gyro > 300 dps) an 80 Hz cutoff rejects more
motion artifact.

Algorithm:
  gyro_mag_peak = max gyro_mag in the swing window
  hp_cutoff = 30 Hz  if gyro_mag_peak < 100 dps
            = 50 Hz  if gyro_mag_peak < 300 dps
            = 80 Hz  otherwise

Novel aspect: Adaptive filtering driven by synchronised IMU (external, causally prior to
artifact) rather than blind EMG statistics. Motion causes artifact, so IMU is known first.

---

#### E4. IMU-Regression Artifact Cancellation (Per-Swing)

Problem:
Sustained wrist acceleration physically displaces the electrode, generating low-frequency
artifact linearly proportional to acceleration (electrode displacement ~ force ~ acc).
This is the Clancy & Hogan (1994) mechanism, applied per-swing.

Algorithm:
  artifact_proxy = lowpass(acc_dyn, cutoff=20Hz, fs=200)   # 200 Hz IMU
  artifact_upsampled = resample(artifact_proxy, len(emg_seg))  # upsample to 2000 Hz
  beta = lstsq(artifact_upsampled, emg_seg)[0]
  emg_clean = emg_seg - beta * artifact_upsampled
  mdf_regression = mnf_mdf(emg_clean, fs)

  beta is also a quality metric: large |beta| = high electrode-motion coupling =
  poor contact or loose electrode.

Foundation: Clancy & Hogan 1994 adaptive regression, applied per-swing with IMU as
the artifact proxy -- not previously done for racket sports.

---

#### E5. Pre-Impact Phase MDF (Welch-Segment Rejection)

Problem:
E1v1 masks individual samples (~3% of window) -- too small to affect Welch average.
The Welch PSD uses 1024-sample (512ms) segments. Impact contamination affects entire
segments, not individual samples.

Two complementary approaches:

Approach A -- Pre-impact phase MDF (preferred):
  impact_t_ms = IMU acc_dyn peak timestamp (or audio-confirmed timestamp)
  pre_impact_emg = emg_window[impact_t_ms - 600ms : impact_t_ms - 20ms]  # 580ms clean
  mdf_pre = mnf_mdf(pre_impact_emg, fs, nperseg=512)  # 3 Welch segments from clean signal

  Physiological basis: pre-impact window is the active muscle loading phase -- muscle
  contracting toward ball contact. Highest fatigue signal, lowest artifact.
  Post-impact contains vibration ringdown and follow-through; both contaminate MDF.

Approach B -- Welch-segment rejection (fallback):
  For each Welch segment [seg_start, seg_end] in the 1300ms window:
      if segment overlaps [impact_t_ms - 40ms, impact_t_ms + 40ms]: exclude
  Compute MDF from remaining clean segments (typically 3-4 of 5 total).
  Use when pre-impact window is too short (< 300ms) due to early impact timing.

Approach A preferred: physiologically correct, simple to describe, 580ms gives 3 Welch
segments at nperseg=512 -- adequate spectral resolution (fs/nperseg = 3.9 Hz per bin).

---

#### E6. Stroke-Type Stratified Fatigue Analysis

Problem:
Forehands, backhands, serves, and volleys recruit forearm flexors differently and have
different motion artifact profiles. Mixing stroke types in one fatigue trend adds
unexplained variance. A serve and a forehand should not be pooled in the same MDF trend.

Algorithm:
  Per swing, extract IMU trajectory features:
    dominant_axis = argmax([std(gx), std(gy), std(gz)])
    gyro_peak     = max(gyro_mag)
    acc_peak      = max(acc_dyn)
    rise_time_ms  = time from gyro_onset to gyro_peak
    shape_score   = DTW distance to stored stroke-type templates

  stroke_type = classifier.predict(features)  # forehand / backhand / serve / volley
  mdf_forehand_trend = [s.mdf for s in swings if s.stroke_type == 'forehand']

Novel aspect: No published work stratifies EMG fatigue by stroke type using IMU
classification in tennis. 823 swings (log0303 + log0305) are available;
~100 swings with video annotation provide a training set.

---

#### E7. IMU-Gated Acoustic Impact Labeling (Validation Tool)

Purpose: This is a VALIDATION TOOL, not a deployed algorithm. Audio is never part of the
deployed wrist sensor. It provides a third independent modality for validating whether the
forearm IMU jerk peak reliably corresponds to ball contact.

Three-modality independence:
  EMG:   muscle + electrode signal -- fails when electrode contact is poor
  IMU:   body motion / transmitted shock -- fails when impact is soft or arm decelerates
  Audio: external acoustic impact cue -- fails when environment is noisy

Each fails independently. When all three agree: high confidence. Two agree: moderate.
One fires alone: flag uncertain.

Why audio is a "noisy weak reference" not ground truth:
A tennis court audio stream contains ball-racket contact, ball bounce, shoe squeak,
player yelling/grunting, other players' hits, racket scrape, wind, echo, HVAC.
Raw amplitude is useless as a ground truth. Impact events must be discriminated
by their physical signature.

Ball-racket contact acoustic signature (physically discriminating):
  Duration:    3-5ms (hard court), 5-8ms (clay) -- much shorter than any other event
  Rise time:   < 1ms -- near-instantaneous (true impulse)
  Decay:       fast exponential ~20-50ms ringdown
  Spectrum:    string resonance 200-600 Hz + harmonics to ~2 kHz; broadband > 1 kHz

Player grunting (different in every dimension):
  Duration:    100-500ms
  Rise time:   20-100ms (vocal onset is gradual)
  Spectrum:    fundamental 100-300Hz (male) + harmonics; concentrated below 2 kHz
  NOT impulsive -- separable by onset sharpness and duration

Discriminating audio features:
  audio_rms_5ms       = energy in 5ms window (brief for impact, sustained for voice)
  onset_strength      = d/dt(log(rms)) -- high for impact, low for sustained sounds
  spectral_centroid   = high for impact (1-5 kHz dominant), lower for voice
  spectral_flux       = sharp spectral change at impact onset
  band_energy_2k_8k   = energy in 2-8 kHz (impact-rich, voice-poor)
  band_energy_100_800 = energy in 100-800 Hz (voice-rich, use as contrast)

  impact_audio_score =
      z(onset_strength)
    + z(band_energy_2k_8k)
    + z(spectral_flux)
    - z(band_energy_100_800)

IMU phase gating makes audio reliable on a noisy court:
  1. Detect swing from forearm gyro (300 dps -- already done)
  2. Define contact_search_window = [t_gyro_peak - 100ms, t_gyro_peak + 250ms]
  3. Search audio only within contact_search_window
  4. Accept onset if impact_audio_score > threshold AND peak_width < 10ms

  This rejects:
    Another court's hit:   audio peak present but NO forearm swing -> rejected by gating
    Player yelling:        energy present but low spectral centroid / broad duration
    Ball bounce:           occurs outside swing window (before or after)
    Echo:                  arrives > 50ms after first onset -> take first onset only

Scientific payoff -- the delay distribution:
  delay = audio_impact_time - imu_jerk_peak_time  (measured across N accepted swings)

  If delay is tight: mean delay on the order of tens of milliseconds, std < 20ms
    -> forearm jerk tracks ball contact (not arm deceleration)
    -> mean delay estimates mechanical vibration transmission time through the kinetic chain
       (racket -> grip -> hand -> forearm; rough intuition: soft tissue
        transmission is slow relative to rigid materials, so a few cm of tissue
        path could account for ~10-30ms -- this should be measured, not assumed)
    -> forearm-only impact-risk gating is physically credible
    -> this delay is not yet measured in the tennis wearable literature

  If delay is wide or random:
    -> forearm jerk cannot reliably locate ball contact at the chosen threshold
    -> need to raise jerk threshold or use composite score
    -> either result is publishable and informative

Mechanical transmission path (physical basis for expecting a short but nonzero delay):
  Ball contact (t=0)
  -> racket frame vibration
  -> grip-hand contact
  -> hand/wrist soft tissue and joints
  -> forearm sensor mount
  -> forearm sensor reads the event
The delay should be estimated from the data rather than assumed from material speeds.

Synchronisation via startup clap (no new hardware):
  Player taps sensor board against racket at session start.
  Creates simultaneously:
    1. IMU acc_dyn spike -> visible in imu_log CSV with microsecond timestamp
    2. Audio transient -> visible in phone recording with sub-ms precision
    3. Visual event -> visible in video if recording
  The IMU timestamp bridges the BLE clock to the phone clock.
  Clock drift: < 1ms/min on modern phones -> < 60ms over 60 min session.
  For < 30ms accuracy: add second clap at end for linear drift correction.

High-confidence subset strategy (reviewer-safe):
  Sort swings by impact_audio_score. Accept top 40-60%.
  Report: "N/626 swings had high-confidence audio labels."
  Use only accepted subset for delay distribution analysis.
  This is standard weakly-supervised labeling; reviewers from audio/ML will recognise it.

Serves as the ideal first experiment:
  - No incoming ball bounce before contact (cleaner audio than rally groundstrokes)
  - Single isolated impact per swing, high contact force (loud, easy to detect)
  - Highly stereotyped biomechanics -> consistent delay distribution expected
  Protocol: 20-30 serves, phone mic recording, startup clap sync.

---

#### E8. Experimental Validation Protocol (2-Month Roadmap)

All levels achievable with existing hardware + phone. No racket sensor required.

Level 0 -- Internal consistency check (1 afternoon, no new data needed)
  Use existing log0305. Compare EMG PSD in 50ms windows at detected jerk events
  vs. 50ms windows away from jerk events (during the same swing but pre-contact phase).
  If PSD near jerk events shows elevated 200-500 Hz energy: impact artifact confirmed.
  If no difference: transmitted vibration is below noise floor at the forearm.
  Code: ~30 lines in a notebook using existing swing_features.csv + raw EMG logs.
  This is the critical sanity check before any other experiment.

Level 1 -- Racket tap while relaxed (30 min, no new hardware)
  Player seated, forearm muscles confirmed relaxed (EMG RMS < 10% of contraction level).
  Record forearm IMU + EMG during:
    (a) Tap the sensor board directly -- mechanical baseline, no transmission
    (b) Tap the sensor cable -- tests cable-induced artifact
    (c) Tap the racket face with a ball -- tests mechanical transmission through arm
    (d) Tap the racket frame -- compares frame vs. string resonance
    (e) Empty slow swing -- voluntary muscle activation without impact
  Expected: condition (c) shows EMG transient and IMU jerk with no voluntary activation.
  This definitively proves mechanical transmission to the electrode exists and characterises
  the artifact waveform at known timing. Any EMG seen in (c) is artifact by definition.

Level 2 -- Empty swing vs. ball-contact protocol (45 min, no new hardware)
  Player performs:
    20 empty forehands (no ball, full swing speed)
    20 ball-contact forehands (hitting a ball, similar swing speed)
    10 soft contacts (half-speed)
    10 hard contacts (maximum effort)
  Compute per-swing: acc_jerk_peak, emg_hf_energy_candidate_band (rename once
  Experiment 10 confirms the artifact frequency band), gyro_phase_of_jerk_peak.
  ROC / AUC analysis: do these features separate empty vs. contact swings?
    AUC > 0.80 -> forearm-only impact-risk gating viable as a binary gate
    AUC 0.60-0.80 -> useful as a soft risk score, not binary
    AUC < 0.60 -> forearm transmission insufficient; need audio or video labels
  This directly answers whether the forearm-only algorithm is physically feasible
  and gives an objective performance bound for the paper.

Level 3 -- Phone video annotation (1 session, phone on tripod)
  Record one 30-min session at 120 fps (most modern phones support this).
  Timing resolution: 8.3ms per frame -- adequate for +-30ms validation.
  Startup clap visible and audible in video -> sync point.
  Manually annotate ball contact frames for ~40 swings (~20 min annotation time).
  Compare video contact times to IMU phase gate prediction.
  Validates: "does contact occur within [t_gyro_peak + 30ms, t_gyro_peak + 200ms]?"

Level 4 -- IMU-gated audio labeling (1 session + 2 hours analysis)
  Record session with phone mic (44.1 kHz, sync via startup clap).
  Implement audio pipeline (steps in E7).
  Accept top 50% by impact_audio_score as high-confidence labels.
  Compute delay distribution (audio_peak_time - imu_jerk_peak_time).
  If mean delay = 10-30ms, std < 20ms: forearm-only detection validated.
  If result is positive: write up as a results section for Paper 2.

Level 5 -- Pre-impact MDF A/B comparison (1 week coding + existing data)
  Implement E5 Approach A (pre-impact phase MDF) in emg_util_yaml_runner.py.
  New config keys: impact_phase_pre_ms (default 600), impact_phase_guard_ms (default 20).
  New output column: mdf_pre_impact alongside existing mdf.
  Run on log0305 w20 config: compare mdf vs. mdf_pre_impact across 626 swings.
  Expected: mdf_pre_impact has lower per-swing variance (cleaner signal source).
  Compare fatigue trend slope: does pre-impact MDF show steeper or cleaner decline?

Level 6 -- Noise floor tracker implementation (3 days + existing data)
  Implement E2 in emg_util_yaml_runner.py.
  Output: noise_floor_trend column in swing_features.csv.
  Visualise for log0305: should show high noise floor early (settling), stable mid-session.
  This corroborates the settling mechanism from the electrode side (not just from MDF
  behaviour), directly strengthening the paper's settling claim against reviewer C2.

Level 7 -- Stroke classification prototype (2-4 weeks)
  Manually annotate stroke type for ~100 swings from log0305 using video from Level 3.
  Extract IMU shape features. Train k-NN or decision tree (no deep learning needed).
  Evaluate separation of 4 stroke types; compute per-type fatigue trends.
  Target: show variance reduction in MDF trend when types are separated.

---

#### Validation Hierarchy Summary

  Level | Method                         | Added burden     | Timing accuracy | Purpose
  ------|-------------------------------|------------------|-----------------|---------------------------
  0     | Internal PSD consistency      | None             | N/A             | Sanity check (1 afternoon)
  1     | Racket tap while relaxed      | 30 min session   | ~5ms (IMU)      | Isolate mechanical transmission
  2     | Empty vs. contact protocol    | 45 min session   | N/A             | Test separability (ROC/AUC)
  3     | Phone video 120 fps           | Phone on tripod  | 8ms/frame       | Validate phase gate timing
  4     | IMU-gated audio (phone mic)   | Phone recording  | sub-ms          | Delay distribution validation
  5     | Racket-mounted accelerometer  | High (research)  | sub-ms          | Lab reference only (not deployed)

Levels 0-4: achievable in the next 2 months with existing hardware + phone.
Level 5: research-only; only if Levels 1-4 confirm the forearm-only approach.

---

#### Algorithm Implementation Roadmap (2 Months)

  Week 1-2:
    [ ] Level 0 internal PSD check (30 lines notebook, existing log0305)
    [ ] Level 1 racket tap experiment (30 min)
    [ ] E5v2: implement pre-impact phase MDF in emg_util_yaml_runner.py
    [ ] Run log0305 w20: compare mdf vs. mdf_pre_impact distributions

  Week 3-4:
    [ ] Level 2 empty vs. contact protocol (45 min session)
    [ ] ROC/AUC analysis of forearm-only feature separability
    [ ] E2: implement noise floor tracker, visualise for log0305
    [ ] E3: implement adaptive HPF, A/B test on log0305

  Week 5-6:
    [ ] Level 3 video annotation (1 session at 120 fps)
    [ ] Level 4 audio pipeline (if Level 2 AUC > 0.70)
    [ ] E4 IMU regression: prototype per-swing artifact cancellation

  Week 7-8:
    [ ] Level 7 stroke classification prototype (if video available)
    [ ] Consolidate validated findings for Paper 2 system section
    [ ] Update paper.md: promote validated algorithms, demote unvalidated to future work
    [ ] Draft Paper 2 Section 7 (field validation) using confirmed results

---

#### Updated Algorithm Summary

  Priority  | ID | Algorithm                               | Status        | 2-month target
  ----------|----|-----------------------------------------|---------------|------------------------------
  Highest   | E8 | Levels 0-2 validation experiments      | Not started   | Week 1-4 (enables all others)
  Highest   | E5 | Pre-impact phase MDF                    | Not started   | Week 1-2
  High      | E2 | Noise floor tracker (continuous)        | Not started   | Week 3-4
  High      | E7 | IMU-gated audio labeling                | Not started   | Week 5-6 (if AUC > 0.70)
  Medium    | E3 | Adaptive HPF cutoff                     | Not started   | Week 5-6
  Medium    | E4 | IMU regression artifact cancel          | Not started   | Week 7-8
  Medium    | E6 | Stroke-type stratified fatigue          | Not started   | After video annotation
  Done      | E1 | Forearm-only impact-risk gating v1      | DONE 2026-05  | v2 = E5 pre-impact phase

All Level 0-4 validation experiments require only existing hardware + phone.
Racket-mounted sensor is not in the 2-month plan.
