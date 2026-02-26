# EMG/IMU Fatigue Detection – Research Notes & Roadmap (Chat Summary)

> Notes captured from our discussion.
> Focus: EMG+IMU wearable fatigue detection using ESP32 + MyoWare EMG (2000 Hz) + SparkFun IMU (200 Hz), with an initial 3–5 month goal to publish a paper, while keeping AI/ML ideas for a later stage.

---

## 1) Your constraints & goals (as stated)

- **Timeline:** 3–5 months.
- **Hardware:** ESP32/Arduino-class device; SparkFun **MyoWare** EMG sensor (~2000 Hz); SparkFun IMU (~200 Hz).
- **Participant pools:** students, gym-goers, tennis courts (no construction site access).
- **Career orientation:** industry; want a publishable paper and recognition as decent research.
- **AI/ML:** acknowledge AI could help a lot, but defer to “next stage”.

---

## 2) Core baseline platform/pipeline (current direction)

### 2.1 Data sources
- **EMG:** raw (and possibly envelope) time series.
- **IMU:** gyro + accel.

### 2.2 Current pipeline structure (conceptual)
1. **Load/stream data** (ESP32 logs → offline analysis).
2. **Activity gating (IMU):** find work periods vs rest using gyro+acc intensity.
3. **Swing detection (IMU):** detect repetitive movement events (“swings”) via robust z-score thresholding.
4. **Per-swing windows:** define windows around swing peaks.
5. **Per-swing EMG features:** e.g., RMS/MAV/WL/ZC/SSC + spectral MNF/MDF.
6. **Bout segmentation:** group swings into bouts (using active segments/gaps).
7. (Optional) **Plots/correlation:** diagnostic plots and EMG–IMU feature correlation.

---

## 3) Near-term publishable study (3–5 months, pragmatic)

### 3.1 Honest novelty assessment we discussed
- A **simple weighted-sum fusion** of EMG features (MDF/RMS) + IMU movement quality is **incremental** (not top-tier novelty), but is still publishable in broad “sensors / applied” venues if:
  - methods are clean,
  - validation is clear,
  - results are presented well.

### 3.2 “Get it published” plan (Option D)
**Goal:** Publish a solid, incremental paper quickly.

**Simplify ruthlessly**:
- Single sport/task focus (tennis serves recommended).
- One session per participant.
- Avoid multi-session break optimization / longitudinal injury work for the first paper.

**Suggested initial study**
- **Participants:** n ≈ 20–25 tennis players.
- **Protocol:** repeated serves at controlled effort until fatigue criterion (e.g., RPE ≥ 17 or serve speed drop ≥ 20%).
- **Ground truth:** serve speed (radar gun) + RPE.

### 3.3 Multi-Domain Fatigue Index (MDFI) – simple interpretable form
A simple composite index combining:
- **MDF drop** (spectral shift)
- **RMS increase** (activation/effort)
- **IMU degradation** (e.g., jerk increase / ROM decrease / smoothness decrease)

Example structure:
- MDF_component = 100 × (Baseline_MDF − Current_MDF)/Baseline_MDF
- RMS_component = 100 × (Current_RMS − Baseline_RMS)/Baseline_RMS
- IMU_component = 100 × (Jerk_increase + ROM_decrease + Smoothness_decrease)/3
- MDFI = (MDF_component + RMS_component + IMU_component)/3

### 3.4 Key analysis outputs for paper
- Correlation of MDFI vs. **performance decline** (serve speed drop).
- Compare MDFI vs single indicators (MDF-only, RMS-only, IMU-only).
- Basic dependent-correlation comparison (e.g., Steiger’s Z) to support “MDFI improves association”.

### 3.5 Recommended target journals (pragmatic)
- **Sensors** (broad scope, incremental work acceptable)
- IEEE Sensors Journal
- Biomedical Signal Processing and Control
- Measurement

---

## 4) Areas to improve (non-AI first)

### 4.1 Stronger physiological grounding
- Clearly motivate each feature as capturing a different fatigue mechanism:
  - **MDF/MNF** → conduction velocity / spectral compression.
  - **RMS/MAV/iEMG** → recruitment/effort.
  - **Jerk/smoothness/ROM/variability** → movement quality and coordination degradation.

### 4.2 Robustness to real-world noise
- Use robust statistics (median/MAD) and quality checks:
  - electrode shift / motion artifact detection,
  - missing data handling,
  - baseline drift.

### 4.3 Personalization without ML (future “Paper 2” candidate)
We discussed this as **more novel** than MDFI alone, still non-AI:
- **Personalized thresholds** based on baseline variability (e.g., threshold = baseline − k·SD, or robust analog).
- Demonstrate reduced false alarms vs a fixed population threshold.

### 4.4 Recovery dynamics (also relatively under-studied)
- Characterize recovery via exponential models:
  - fatigue_metric(t) ≈ A·exp(−t/τ) + C
- Compare recovery time constants across modalities:
  - EMG spectral recovery vs performance recovery vs IMU movement quality recovery.

---

## 5) Future research roadmap (higher novelty options)

> These ideas were brainstormed as stronger novelty pathways, but likely beyond a 3–5 month “first paper” scope.

### 5.1 “Next stage” (still possibly minimal AI)
- **Personalized recovery + adaptive breaks**: individualized τ and adaptive rest recommendations.
- **Task-specific fatigue signatures**: compare multiple tasks/sports and show distinct fatigue “fingerprints”.
- **Minimal sensor set optimization**: identify the minimal configuration that maintains performance.

### 5.2 AI/ML (explicitly deferred to later)
We discussed several ML-heavy directions:
- **Predictive fatigue models** (forecast 10–15 minutes ahead).
- **Uncertainty-aware prediction** (Bayesian models providing confidence).
- **Cross-task transfer learning** (train on one task, deploy on another).
- **Explainable models** (feature attributions / counterfactuals).
- **Federated learning** for privacy-preserving multi-site training.
- **Synthetic data generation** (GANs) for data scarcity.

### 5.3 Highest-impact but longer studies
- **Fatigue → injury prediction** (longitudinal cohort). High novelty and impact, but requires months and many participants.
- **Team-level fatigue “contagion”** modeling in group settings (also high novelty, more complex logistics).

---

## 6) Practical execution tips (for paper acceptance)

- Keep the study **tight** and claims modest.
- Make the validation metric clear (serve speed decline + RPE).
- Provide 3–5 clean figures:
  - fatigue progression (MDF/RMS/IMU/performance vs time),
  - MDFI vs performance scatter with regression,
  - comparison of correlations (bar chart + CI),
  - optional Bland–Altman or ROC-style detection view.
- Pre-register a simple analysis plan (optional but helps rigor).
- Write limitations openly:
  - single muscle site,
  - single sport task,
  - modest sample size,
  - equal weights (if you don’t optimize yet).

---

## 7) Optional patent angle (conceptual)

Potential claims (requires prior-art check):
- A real-time method combining EMG spectral + EMG amplitude + IMU movement-quality into a fatigue index.
- A personalization method deriving thresholds from baseline variability.
- A break recommendation method using individualized recovery kinetics.

---

## 8) Suggested next steps (action list)

1. Decide initial single-task study (tennis serve recommended).
2. Confirm measurement of performance (radar gun for serve speed).
3. Run pilot sessions (n=3–5) to validate logging quality.
4. Lock protocol and analysis plan.
5. Recruit n≈20–25 and collect data.
6. Analyze and draft the “MDFI validation” paper.
7. Keep a “Paper 2” plan: personalization + recovery kinetics.

---

## 9) Key takeaway

- **MDFI alone is incremental but publishable** if executed cleanly.
- **Personalized thresholds and recovery kinetics** are promising non-AI extensions with stronger novelty.
- AI/ML can be a strong later-stage enhancement once you have a solid dataset and baseline results.
