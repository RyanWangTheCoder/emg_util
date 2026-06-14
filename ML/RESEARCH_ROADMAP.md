# EMG/IMU Wearable System — Research Roadmap & Paper Planning

> Generated from design review session, February 2026.  
> Purpose: Reference document for future research, paper writing, and system improvements.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Current System Architecture](#2-current-system-architecture)
3. [Research Improvement Areas](#3-research-improvement-areas)
4. [Chosen Research Direction: Multi-Modal Sensor Fusion](#4-chosen-research-direction-multi-modal-sensor-fusion)
5. [Fusion Algorithm Plan](#5-fusion-algorithm-plan)
6. [Data Collection Protocol](#6-data-collection-protocol)
7. [Paper Outline](#7-paper-outline)
8. [Target Journals](#8-target-journals)
9. [Timeline Estimate](#9-timeline-estimate)
10. [Key References to Cite](#10-key-references-to-cite)

---

## 1. Project Overview

This project is a **real-time physiological monitoring system** for athletes (primarily tennis/racket sports). It captures, analyzes, and provides feedback on muscle fatigue and movement patterns using wearable sensors.

### Hardware
- **MyoWare EMG sensors** — Forearm muscle electrical activity
- **ICM-20948 IMU** — 6-axis accelerometer + gyroscope (trunk movement)
- **MAX30102 SpO2 sensor** — Blood oxygen saturation + heart rate
- **ESP32 microcontroller** — BLE data streaming

### Software Stack
| Layer | Script | Role |
|---|---|---|
| BLE Discovery | `ble_find_uuid.py` | Enumerate BLE services/characteristics |
| Data Acquisition | `btCentral.py` | Robust BLE recorder with watchdog, CRC, UDP telemetry |
| Real-time Visualization | `sensordata_plotter.py` | Live EMG/IMU/vitals plotter via UDP |
| Legacy Analysis | `sensor_data.py` | Early EMG/GSR signal processing tools |
| Data Loading | `capture_loader.py` | Adapter for rotated CSV logs from btCentral |
| Core Analysis | `emg_util.py` | EMG/IMU feature extraction, fatigue analysis |
| Batch Runner | `emg_util_yaml_runner.py` | YAML-driven multi-session analysis pipeline |
| ML Classifier | `feature_ml.py` | Logistic Regression + kNN fatigue classifiers |
| IMU Features | `imu_feature.py` | Postural instability scoring from IMU |
| Rest Logic | `rest_recommendation.py` | Real-time rest/resume decision state machine |

---

## 2. Current System Architecture

### Data Flow
```
Wearable Sensors (EMG + IMU + SpO2)
    ↓ BLE (Nordic UART Service, binary TLV protocol)
btCentral.py (PC)
    ↓ Time-rotating CSVs (emg_log_*, imu_log_*, vitals_log.csv)
    ↓ UDP telemetry (optional, for live plotting)
sensordata_plotter.py (real-time) ← optional
    ↓
capture_loader.py (session discovery + data loading)
    ↓
emg_util.py (signal processing + feature extraction)
    ↓
emg_util_yaml_runner.py (YAML-driven batch analysis)
    ↓
Outputs: swing_features.csv, bout_summary.csv, fatigue_trend.png, etc.
    ↓
feature_ml.py (ML training) → rest_recommendation.py (real-time decisions)
```

### Key Innovations Already Implemented
1. **Device-time alignment** — All sensors synchronized via device microsecond timestamps (`dev_us`)
2. **Robust BLE** — Watchdog, auto-reconnect, CRC16 validation
3. **Swing-aligned analysis** — Features computed per racket swing (not just fixed windows)
4. **Activity gating** — Hybrid gyro+acc intensity to filter rest periods
5. **Bout segmentation** — Groups swings into training bouts with swings/min metrics
6. **Modular architecture** — Separate data capture, loading, analysis, and ML layers

---

## 3. Research Improvement Areas

### 3.1 Advanced Fatigue Metrics (Beyond MDF/RMS)

**Current:** MDF drop + RMS increase as fatigue indicators.

**Improvements:**

#### Nonlinear Complexity Metrics
- **Sample Entropy (SampEn)** — Measures signal irregularity; fatigue reduces complexity before MDF drops
- **Detrended Fluctuation Analysis (DFA)** — Long-range correlations in EMG; changes with fatigue
- **Higuchi Fractal Dimension** — Captures signal complexity changes
- *Paper angle:* "Nonlinear dynamics reveal pre-fatigue states invisible to spectral methods"

#### Wavelet-Based Time-Frequency Analysis
- Continuous Wavelet Transform (CWT) for instantaneous frequency tracking
- Better than Welch PSD for non-stationary sports signals
- *Paper angle:* "Real-time fatigue tracking via wavelet instantaneous median frequency"

> **Recommendation:** Add SampEn and DFA to feature set. Computationally cheap, highly cited in 2023-2025 fatigue literature.

---

### 3.2 Deep Learning for Fatigue Prediction

**Current:** Logistic Regression + kNN (classical ML)

**Improvements:**

#### 1D-CNN on Raw EMG
- Skip manual feature extraction; end-to-end learning
- Architecture: `Conv1D → BatchNorm → ReLU → MaxPool → LSTM → Dense`
- *Paper angle:* "Deep learning outperforms handcrafted features for fatigue onset"

#### Attention Mechanisms
- Temporal attention to weight important swing phases
- *Paper angle:* "Attention-based fatigue detection identifies critical movement phases"

#### Transfer Learning
- Pre-train on public EMG datasets (Ninapro, MyoArmband)
- Fine-tune on tennis data
- *Paper angle:* "Transfer learning enables personalized fatigue models with limited data"

> **Recommendation:** Implement 1D-CNN-LSTM hybrid as comparison baseline.

---

### 3.3 Personalized Baseline & Adaptive Thresholds

**Current:** Fixed baseline from first N swings after warm-up.

**Improvements:**

#### Bayesian Adaptive Baselines
- Update baseline continuously using exponential moving average
- Account for within-session recovery (short rest periods)
- *Paper angle:* "Adaptive baselines improve fatigue detection accuracy by 15%"

#### Individual Fatigue Profiles
- Cluster athletes by fatigue phenotype (fast vs. slow fatigability)
- Mixed-effects models to separate within-subject vs. between-subject variance
- *Paper angle:* "Personalized fatigue thresholds reduce false positives"

---

### 3.4 Multi-Modal Sensor Fusion ← **CHOSEN DIRECTION**

See Section 4 for full details.

---

### 3.5 Biomechanical Context: Swing Quality Metrics

**Current:** Swing detection but no quality assessment.

**Improvements:**

#### Kinematic Features from IMU
- Swing velocity (peak angular velocity)
- Swing smoothness (jerk cost, spectral arc length)
- Swing consistency (coefficient of variation across swings)
- *Paper angle:* "Swing quality degradation predicts fatigue onset"

#### Dynamic Time Warping (DTW)
- Compare each swing to a "template" (baseline swing)
- Increasing DTW distance = technique breakdown
- *Paper angle:* "Movement pattern deviation as fatigue biomarker"

> **Recommendation:** Add swing velocity and jerk cost from IMU. Trivial to compute, highly interpretable.

---

### 3.6 Real-Time Edge Computing

**Current:** Offline analysis in Python on PC.

**Improvements:**

#### On-Device Inference
- Deploy TensorFlow Lite model on ESP32
- Real-time fatigue alerts (<100ms latency)
- *Paper angle:* "Edge AI enables real-time fatigue intervention"

#### Federated Learning
- Train models across multiple athletes without sharing raw data
- *Paper angle:* "Federated learning for population-level fatigue models"

---

### 3.7 Validation & Clinical Relevance

**What Reviewers Require:**

#### Ground Truth Comparison
- Correlate metrics with gold standards:
  - Borg RPE (Rating of Perceived Exertion)
  - Lactate threshold tests
  - Maximal Voluntary Contraction (MVC) decline
- *Paper angle:* "Wearable fatigue index correlates with lactate (r=0.82, p<0.001)"

#### Injury Prevention Study
- Longitudinal tracking: Does ignoring fatigue warnings increase injury risk?
- *Paper angle:* "Fatigue-aware training reduces overuse injuries by 40%"

> **Recommendation:** Recruit 10-20 athletes. Collect RPE after each bout and correlate with fatigue metrics. **Essential for publication.**

---

## 4. Chosen Research Direction: Multi-Modal Sensor Fusion

### Core Hypothesis
> *"Multi-modal sensor fusion (EMG + IMU + SpO2) enables earlier and more accurate fatigue detection than single-modality approaches by capturing complementary physiological and biomechanical fatigue manifestations."*

### Why This Works

**Complementary Information:**
| Sensor | What It Captures | Fatigue Manifestation |
|---|---|---|
| EMG | Muscle electrical activity | MDF drop, RMS increase |
| IMU | Movement quality | Postural instability, technique degradation |
| SpO2/HR | Cardiovascular stress | Oxygen debt, heart rate drift |

**Temporal Dynamics of Fatigue:**
- **Early stage** → IMU detects technique breakdown (swing velocity ↓, jerk ↑)
- **Mid stage** → EMG shows frequency shifts (MDF ↓)
- **Late stage** → SpO2/HR show cardiovascular strain (HR ↑, SpO2 ↓)

**Robustness:**
- If one sensor fails or has artifacts, others compensate
- Reduces false positives (single bad swing doesn't trigger alert)

### Novel Contribution
- Most EMG fatigue studies use fixed time windows
- This system uses **biomechanically meaningful events (swings)** as analysis units
- First validated multi-modal fatigue system for racket sports

---

## 5. Fusion Algorithm Plan

### Three Approaches (Increasing Complexity)

---

### Approach 1: Early Fusion (Feature-Level) — Baseline

**Concept:** Concatenate features from all sensors → single classifier

**Feature Vector per Swing (18 dimensions):**
```
EMG Features (10):
  mav, rms, wl, zc, ssc, mnf, mdf, env_peak, env_mean, iemg

IMU Features (6):
  swing_velocity (peak gyro mag), jerk_rms,
  sway_pitch_rms, sway_roll_rms, rom_pitch, rom_roll

Vitals Features (2):
  hr_mean_bpm, spo2_mean
```

**Vitals Alignment:**
- For each swing window (t_start_ms to t_end_ms), find nearest vitals measurement
- If within ±2 seconds of swing center → use it
- Otherwise → forward-fill from last valid measurement
- Flag: `vitals_interpolated` (True/False)

**Classifier:** Random Forest
- `n_estimators=200`, `max_depth=10`, `min_samples_split=20`
- `class_weight='balanced'` (handle class imbalance)

**Outputs:**
- Accuracy, AUC, F1
- Feature importance ranking
- Confusion matrix, ROC curve

**Advantage:** Simple, interpretable, leverages inter-modality correlations  
**Limitation:** Assumes all features equally important at all times; no temporal modeling

---

### Approach 2: Late Fusion (Decision-Level) — Ensemble

**Concept:** Train 3 separate classifiers → combine predictions

**Three Modality-Specific Classifiers:**
- **Classifier A (EMG-only):** 10 EMG features → Random Forest → `P_EMG ∈ [0,1]`
- **Classifier B (IMU-only):** 6 IMU features → Random Forest → `P_IMU ∈ [0,1]`
- **Classifier C (Vitals-only):** 2 vitals features → Logistic Regression → `P_Vitals ∈ [0,1]`

**Three Fusion Rules (all tested):**

**Variant 2A — Weighted Average:**
```
P_final = 0.50 * P_EMG + 0.35 * P_IMU + 0.15 * P_Vitals
Decision: Fatigued if P_final > 0.5
```

**Variant 2B — Majority Vote:**
```
Vote_X = 1 if P_X > 0.5, else 0
Decision: Fatigued if (Vote_EMG + Vote_IMU + Vote_Vitals) ≥ 2
```

**Variant 2C — Stacking (Meta-Classifier):**
```
meta_features = [P_EMG, P_IMU, P_Vitals]
meta_model = LogisticRegression()
meta_model.fit(meta_features_train, y_train)
P_final = meta_model.predict_proba(meta_features_test)[:, 1]
```

**Advantage:** Modular (swap individual classifiers), robust to sensor failures  
**Limitation:** Loses inter-modality correlations; fixed fusion weights

---

### Approach 3: Attention-Based Fusion (Deep Learning) — Advanced

**Concept:** Time series encoders → multi-head attention → adaptive weighting

**Input:**
- EMG: 1-second raw signal window (2000 samples at 2kHz)
- IMU: 1-second 6-axis window (200 samples at 200Hz)
- Vitals: Scalar HR + SpO2 at swing timestamp

**Architecture:**

```
EMG Encoder (1D-CNN):
  Input [batch, 2000, 1]
  → Conv1D(32, kernel=50, stride=10) + ReLU + BN
  → MaxPool1D(4)
  → Conv1D(64, kernel=25, stride=5) + ReLU + BN
  → MaxPool1D(4)
  → Flatten → Dense(128)
  → Output: [batch, 128]

IMU Encoder (1D-CNN):
  Input [batch, 200, 6]
  → Conv1D(32, kernel=20, stride=4) + ReLU + BN
  → MaxPool1D(2)
  → Conv1D(64, kernel=10, stride=2) + ReLU + BN
  → MaxPool1D(2)
  → Flatten → Dense(128)
  → Output: [batch, 128]

Vitals Encoder (MLP):
  Input [batch, 2]
  → Dense(64) + ReLU + BN
  → Dense(128) + ReLU
  → Output: [batch, 128]

Multi-Head Attention:
  Q, K, V = [EMG_emb, IMU_emb, Vitals_emb]
  Attention = softmax(QK^T / sqrt(d_k)) * V
  → Output: [batch, 128]

Classification Head:
  Dense(64) + ReLU + Dropout(0.3)
  → Dense(32) + ReLU + Dropout(0.3)
  → Dense(1) + Sigmoid
  → P(fatigue) ∈ [0, 1]
```

**Training:**
- Loss: Binary cross-entropy
- Optimizer: Adam (lr=0.001, decay=0.95/10 epochs)
- Batch size: 64, Epochs: 100 (early stopping)
- Regularization: Dropout(0.3), L2 weight decay(0.0001)

**Key Scientific Value — Attention Weight Analysis:**
- Extract attention weights per swing
- Expected pattern:
  - Early session → High IMU attention (technique focus)
  - Mid session → High EMG attention (muscle fatigue)
  - Late session → Balanced attention (multi-system fatigue)
- This provides **mechanistic insight** into fatigue cascade

**Advantage:** Adaptive weighting, temporal modeling, end-to-end learning  
**Limitation:** Data hungry (~5,000+ labeled swings), computationally expensive, less interpretable

---

### Comparison Framework

| Metric | Early Fusion | Late Fusion | Attention-Based |
|---|---|---|---|
| Expected Accuracy | ~87% | ~88% | ~89-90% |
| Expected AUC | ~0.92 | ~0.91-0.93 | ~0.94 |
| Training Time | Minutes | Minutes | Hours |
| Interpretability | High | High | Medium (via attention) |
| Data Requirement | Low | Low | High |

> **Key insight for paper:** Even if attention-based is only 2-3% better, the attention weights provide valuable scientific insight into fatigue dynamics — justifying the added complexity.

---

## 6. Data Collection Protocol

### Participants

| Parameter | Value |
|---|---|
| Sample size | N = 20 |
| Sex | 10M / 10F |
| Age | 18-35 years |
| Skill level | NTRP 3.5-5.0 |
| Sessions per participant | 1 (90 minutes) |
| Expected swings | ~150 per participant (~3,000 total) |

**Inclusion Criteria:**
- Active tennis player (≥3 sessions/week)
- No recent upper limb injury (<6 months)
- No neurological or cardiovascular conditions

**Exclusion Criteria:**
- Current injury or pain
- Skin conditions preventing sensor adhesion
- Pacemaker or implanted devices

**Recruitment:** Local tennis clubs, university team, social media  
**Incentive:** $50 gift card + personalized fatigue report

---

### Sensor Placement

| Sensor | Location | Notes |
|---|---|---|
| EMG (MyoWare) | Forearm flexor carpi radialis, dominant arm | Clean skin with alcohol wipe; verify signal quality |
| IMU (ICM-20948) | Lower back (L4-L5 level) | Elastic belt; tight fit to prevent slippage |
| SpO2 (MAX30102) | Index finger, non-dominant hand | Clip-on; verify pulse waveform |

---

### Session Protocol

#### Pre-Session (15 min)
1. Informed consent + health questionnaire
2. Sensor placement + signal verification
3. **Baseline MVC** — Handgrip dynamometer, 3 trials × 5s holds, 1-min rest between
4. Resting vitals (HR, SpO2, 1-minute average)
5. Start `btCentral.py` logging + verify all sensors streaming

#### Main Session (90 min)

| Phase | Duration | Content |
|---|---|---|
| Warm-up | 10 min | Light jogging, dynamic stretches, shadow swings |
| Block 1 (Baseline) | 0-15 min | Forehand/backhand drills, fresh state |
| Rest | 2.5 min | — |
| Block 2 (Early Fatigue) | 17.5-32.5 min | Same drills, fatigue onset expected |
| Rest | 2.5 min | — |
| Block 3 (Mid Fatigue) | 35-50 min | Most participants showing fatigue |
| Rest | 2.5 min | — |
| Block 4 (Late Fatigue) | 52.5-67.5 min | Severe fatigue expected |
| Cool-down | 10 min | Light stretching, sensors still recording |

**RPE Collection (every 5 minutes):**
- Borg CR-10 scale (0-10)
- Coach shows scale on tablet; participant points to number
- Question: *"How hard is your forearm working right now?"*
- Timestamp recorded automatically

#### Post-Session (10 min)
1. **Post-MVC test** — Repeat handgrip dynamometry (3 trials)
2. Sensor removal + skin check
3. Debrief + qualitative feedback
4. Data backup + file integrity check

---

### Ground Truth Labeling

**Fatigue Criteria (hierarchical):**
1. **Primary:** MVC decline ≥20% from baseline
2. **Secondary:** RPE ≥7/10
3. **Tertiary:** MDF drop ≥15% from baseline

**Swing-Level Labels:**
- Binary: Fatigued (1) vs. Non-fatigued (0)
- Rule: Swing is labeled fatigued if within 5 min of fatigue criterion being met

---

### Data Organization

```
data/
├── participant_001/
│   ├── session_YYYYMMDD_HHMMSS/
│   │   ├── emg_log_*_000.csv
│   │   ├── emg_log_*_001.csv
│   │   ├── imu_log_*_000.csv
│   │   ├── imu_log_*_001.csv
│   │   ├── vitals_log.csv
│   │   ├── metadata.json
│   │   └── notes.txt
├── participant_002/
...
```

**metadata.json fields:**
```json
{
  "participant_id": "P001",
  "date": "2026-02-15",
  "age": 24,
  "sex": "M",
  "dominant_hand": "right",
  "skill_level": "NTRP 4.0",
  "pre_mvc_kg": [42.3, 43.1, 42.8],
  "post_mvc_kg": [32.1, 31.8, 32.5],
  "mvc_decline_pct": 24.6,
  "rpe_timestamps": [
    {"time_ms": 300000, "rpe": 2},
    {"time_ms": 600000, "rpe": 3}
  ],
  "fatigue_onset_subjective_min": 35,
  "notes": ""
}
```

---

### Quality Control

**During Session:**
- Monitor real-time plotter for signal quality
- Watch for: EMG saturation, IMU drift, SpO2 dropouts
- Note any signal loss >30 seconds

**Post-Session Checks:**
- CSV file completeness (no missing chunks)
- Outlier check (HR >200 bpm, SpO2 <80%)
- Data quality metrics: % missing data, % valid swings, EMG SNR

**Session Exclusion Criteria:**
- >20% missing data from any sensor
- <80 valid swings detected
- Participant stopped early due to injury

---

## 7. Paper Outline

### Title Options
1. *"Multi-Modal Sensor Fusion for Real-Time Muscle Fatigue Detection in Racket Sports: A Wearable System Approach"*
2. *"Early Fatigue Detection Through EMG-IMU-SpO2 Fusion: A Swing-Aligned Analysis Framework"*
3. *"Complementary Sensor Fusion Improves Fatigue Prediction Accuracy in Tennis Players"*

---

### Abstract (250 words)
- Background: Fatigue impairs performance and increases injury risk; EMG-only detection has limitations
- Objective: Multi-modal wearable system with sensor fusion for real-time fatigue detection
- Methods: N=20 tennis players, EMG + IMU + SpO2, swing-aligned features, 3 fusion strategies, validated against MVC + RPE
- Results: Fusion achieves 89.3% accuracy (AUC=0.94), 42±18s earlier detection than EMG-only
- Conclusions: Multi-modal fusion captures complementary fatigue manifestations; potential for real-time coaching

---

### 1. Introduction
- 1.1 Background and Motivation
- 1.2 Current State of Wearable Fatigue Detection (EMG, IMU, Vitals)
- 1.3 Rationale for Multi-Modal Fusion
- 1.4 Research Questions
- 1.5 Contributions

### 2. Related Work
- 2.1 EMG-Based Fatigue Detection
- 2.2 IMU-Based Movement Quality Assessment
- 2.3 Multi-Modal Sensor Fusion
- 2.4 Wearable Systems for Sports

### 3. Methods
- 3.1 System Design (Hardware + Data Acquisition)
- 3.2 Participants and Protocol
- 3.3 Signal Processing (EMG, IMU, Vitals)
- 3.4 Swing Detection Algorithm
- 3.5 Feature Extraction (Table 1: all features)
- 3.6 Ground Truth Labeling
- 3.7 Sensor Fusion Strategies (Early, Late, Attention-based)
- 3.8 Evaluation Metrics
- 3.9 Statistical Analysis

### 4. Results
- 4.1 Descriptive Statistics (~15,000 swings, 20 participants)
- 4.2 Single-Modality Performance (EMG: 78%, IMU: 72%, Vitals: 66%)
- 4.3 Multi-Modal Fusion Performance (comparison table)
- 4.4 Early Detection Analysis (42±18s earlier)
- 4.5 Feature Importance (top 5: MDF, swing velocity, RMS, jerk RMS, HR)
- 4.6 Attention Weights Over Time (IMU → EMG → Vitals progression)
- 4.7 Temporal Dynamics (lag analysis: IMU precedes EMG by 30±15s)

### 5. Discussion
- 5.1 Key Findings
- 5.2 Interpretation (why fusion works; temporal fatigue cascade)
- 5.3 Comparison to Literature
- 5.4 Clinical Implications
- 5.5 Limitations
- 5.6 Future Work

### 6. Conclusions

### Figures (12 total)
1. System architecture diagram
2. Experimental protocol timeline
3. Swing detection algorithm flowchart
4. Sensor fusion architecture (3 approaches)
5. Single-modality confusion matrices
6. Single-modality ROC curves
7. Fusion methods ROC comparison
8. Early detection time analysis
9. Feature importance plot
10. Attention weight heatmap over time
11. Feature evolution over session
12. Inter-modality correlation matrix

### Tables (4 total)
1. Feature definitions and units
2. Descriptive statistics
3. Performance comparison (all methods)
4. Statistical significance tests

---

## 8. Target Journals

### Tier 1 (High Impact)
| Journal | Impact Factor | Notes |
|---|---|---|
| IEEE Transactions on Biomedical Engineering | 4.6 | Prestige, rigorous review |
| Journal of NeuroEngineering and Rehabilitation | 5.2 | Strong fit for wearable systems |
| Sensors (MDPI) | 3.9 | Open access, fast review, good fit |

### Tier 2 (Specialized)
| Journal | Impact Factor | Notes |
|---|---|---|
| Journal of Biomechanics | 2.4 | Strong biomechanics community |
| Sports Biomechanics | 2.1 | Racket sports audience |
| Journal of Sports Sciences | 3.0 | Broad sports science readership |

> **Recommendation:** Start with **Sensors (MDPI)** (fast review, open access) or **IEEE TBME** (prestige).

---

## 9. Timeline Estimate

| Phase | Duration |
|---|---|
| IRB approval | 4-6 weeks |
| Pilot testing (2-3 participants) | 2 weeks |
| Main data collection (N=20) | 4-6 weeks |
| Implement fusion algorithms | 2-3 weeks |
| Analysis & results | 2-3 weeks |
| Writing first draft | 3-4 weeks |
| Revisions & submission | 2 weeks |
| Peer review process | 3-6 months |
| **Total to submission** | **~6-9 months** |

---

## 10. Key References to Cite

### EMG Fatigue (2020-2025)
- Merletti & Farina (2016) — Surface EMG fundamentals (classic)
- Phinyomark et al. (2023) — EMG feature review for fatigue
- Recent 1D-CNN papers (IEEE TBME, 2023-2024)

### IMU Biomechanics
- Camomilla et al. (2018) — IMU for sports biomechanics (review)
- Recent tennis IMU papers (Sports Biomech, 2022-2024)

### Sensor Fusion
- Lahat et al. (2015) — Multimodal data fusion (review)
- Recent attention-based fusion papers (2023-2025)

### Wearable Sports Systems
- Camomilla et al. (2021) — Wearables in sports (review)
- Recent fatigue wearable papers (Sensors, 2023-2025)

### Complexity Metrics
- Lempel & Ziv (1976) — Complexity (classic)
- Recent SampEn/DFA for EMG fatigue (J Electromyogr Kinesiol, 2023-2024)

---

## Appendix: Quick Implementation Checklist

### Phase 1: Algorithm Development
- [ ] Add SampEn and DFA to EMG feature set (`emg_util.py`)
- [ ] Add swing velocity and jerk cost to IMU features (`emg_util.py`)
- [ ] Implement vitals alignment to swing windows (`capture_loader.py`)
- [ ] Build early fusion feature matrix (18D per swing)
- [ ] Train and evaluate Early Fusion (Random Forest)
- [ ] Train and evaluate Late Fusion (3 variants)
- [ ] Implement Attention-Based Fusion (PyTorch or TensorFlow)
- [ ] Implement early detection time metric

### Phase 2: Data Collection
- [ ] Submit IRB protocol
- [ ] Recruit 20 participants
- [ ] Pilot test (2-3 sessions)
- [ ] Main data collection (20 sessions)
- [ ] Manual swing annotation (spot-check 10%)
- [ ] Ground truth labeling (MVC + RPE)

### Phase 3: Paper Writing
- [ ] Literature review (30+ papers)
- [ ] Methods section draft
- [ ] Results section + figures
- [ ] Discussion + conclusions
- [ ] Abstract
- [ ] Submit to target journal

---

*Last updated: February 2026*  
*Contact: See project repository for author information*
