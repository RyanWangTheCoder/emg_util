# Paper 3: Longitudinal Field Monitoring of Tennis Forearm Load and Recovery Using Wearable sEMG–IMU and Personalized Predictive Modeling

**Status:** Research program design — two-stage approach. Read paper2_plan.md and journal_draft.md for
the foundational platform and methodology (Paper 1/2) that this builds on.

**Upgraded thesis:** Before AI can predict overuse risk, a wearable system must establish which field
biomarkers reflect fatigue, recovery, contact quality, and mechanical load. This study builds and validates
those biomarkers through controlled experiments, then uses them in a longitudinal personalized model of
readiness and soreness risk.

**Key principle:** Do not rush into AI. First create a high-quality longitudinal physiology + workload
dataset with validation experiments. Only after biomarkers and labels are credible, train personalized models.

---

## The Problem

Lateral elbow tendinopathy (tennis elbow), shoulder impingement, and wrist overuse injuries
are the dominant chronic injuries in recreational and competitive tennis. They share a common
cause: accumulated tissue load exceeding recovery capacity over days to weeks — not single-session
overexertion. Current monitoring approaches in youth/recreational tennis are:

1. **Subjective only** — player says "my arm hurts more lately" → too late, already injured
2. **Volume-only** (session count, hours played) — no muscle-level fatigue information
3. **Lab-only** — MVC tests, clinical assessments — not deployable at practice

The gap: no field-deployable system that tracks *objective* muscle-level fatigue accumulation
across sessions, fused with player self-report, to build a personalized injury-risk model.

---

---

## Research Program: Five Stages

### Stage 0: IRB, Label Design & Analysis Plan (weeks 1–3)

**Goal:** Define exactly what you are allowed to collect and what labels are worth collecting.
This is the foundation. Collecting months of data first and only later realizing the label form or consent scope was incomplete is a critical mistake to avoid.

#### Stage 0A — IRB / Ethics Scope

Confirm whether the existing IRB covers:

- repeated longitudinal sessions over months
- subjective fatigue ratings
- soreness/pain location reports
- sleep quality / readiness
- optional grip strength
- optional impedance measurements
- optional video annotation
- minor participant rules, if applicable
- data retention and de-identification
- whether "injury risk" language is allowed

**Important distinction:**

- **Safe wording:** fatigue, soreness, readiness, perceived exertion, training load
- **Potentially sensitive wording:** injury prediction, medical diagnosis, clinical risk score

For the paper, avoid claiming a clinical "injury-risk predictor" unless the IRB and dataset explicitly support that.
Instead, use: "soreness/readiness decline as practical early-warning proxies for load intolerance."

**Action items:**
- [ ] Review current IRB packet: [IRB_Packet_OSU_sEMG_IMU_Athletic_Practice.md](IRB_Packet_OSU_sEMG_IMU_Athletic_Practice.md)
- [ ] Confirm coverage for repeated sessions + subjective ratings
- [ ] If needed, submit amendment for new label items (soreness location, sleep, stress, readiness)
- [ ] Confirm minor participant rules and consent procedures
- [ ] Get written IRB approval before Stage 1 begins

#### Stage 0B — Label Design

Design the exact form before data collection. Keep it short enough to be completed every session.

Use three timepoints:

##### 1. Pre-session (30–60 seconds)

```
Date: ___  Time: ___

Session type planned: [ ] Practice [ ] Match [ ] Tournament [ ] Conditioning

Forearm readiness (1–5): ___
Overall readiness (1–5): ___

Current soreness (0–10):
  Forearm: ___
  Elbow: ___
  Shoulder: ___
  Wrist: ___

Sleep quality last night (1–5): ___

Unusual pain? [ ] Yes [ ] No
If yes, location/notes: _______________
```

##### 2. Post-session (ideally 30 min after)

```
Session-RPE CR10 (0–10): ___
Forearm-specific RPE CR10 (0–10): ___

Perceived technical intensity: [ ] Easy [ ] Moderate [ ] Hard

Session duration (min): ___
Session type: [ ] Practice [ ] Match [ ] Tournament

Unusual pain during session? [ ] Yes [ ] No
If yes, location: _______________
```

##### 3. Next morning (optional but high value)

```
Soreness (0–10):
  Forearm: ___
  Elbow: ___
  Wrist: ___
  Shoulder: ___

Overall readiness (1–5): ___

Pain affecting normal activity? [ ] Yes [ ] No
```

**Rationale:** Next-morning label may become more valuable than immediate RPE because overuse response often appears after the session.

**Action items:**
- [ ] Finalize label form (paper or phone app)
- [ ] Test form with 2–3 pilot sessions
- [ ] Refine based on feedback (clarity, time to complete, missing fields)
- [ ] Freeze form before Stage 1 begins

#### Stage 0C — Define Primary & Exploratory Outcomes

Pre-define outcomes before collecting data to reduce accidental p-hacking.

##### Primary Outcomes (pre-registered, hypothesis-driven)

**Primary outcome 1:** `next_morning_forearm_soreness` (0–10 scale)
- Reason: direct local response to forearm load
- Threshold for "elevated": ≥4/10

**Primary outcome 2:** `next_session_forearm_readiness` (1–5 scale)
- Reason: usable for recovery/readiness modeling
- Threshold for "declined": ≤2/5

##### Secondary Outcomes

- post-session forearm RPE (0–10)
- whole-body session-RPE (0–10)
- next-morning elbow/wrist/shoulder soreness (0–10)
- soreness escalation event (binary)

##### Exploratory Outcome

**`soreness_risk_proxy`** (binary event)

Definition: Any of the following within a session or 1–3 sessions after high load:
- next-morning soreness ≥4/10, OR
- next-session readiness ≤2/5, OR
- soreness increase ≥2 points from baseline, OR
- pain persists for 2+ consecutive sessions, OR
- self-reported unusual pain affecting normal activity

**Rationale:** Gives you a non-clinical "risk proxy" without needing confirmed injury diagnosis.

**Action items:**
- [ ] Finalize primary/secondary/exploratory outcome definitions
- [ ] Pre-register thresholds for each outcome
- [ ] Document rationale for each outcome
- [ ] Freeze outcome definitions before Stage 1 begins

#### Stage 0D — Define Feature Freeze & Analysis Plan

Before modeling, decide:

- **Minimum sessions before model training:** 40
- **Target sessions:** 60–80
- **Valid EMG session criteria:** >80% data completeness, contact quality drift <threshold, no saturation
- **Missing label policy:** impute from adjacent sessions or exclude
- **Primary features:** Tier 1–3 (volume, mechanical load, EMG fatigue)
- **Exploratory features:** Tier 4–5 (recovery, quality-aware)
- **Model baselines:** persistence, volume-only, sports-science (session-RPE × duration)
- **Train/test strategy:** chronological split (70/30), leave-one-week-out validation
- **Feature engineering freeze:** no feature engineering after looking at target correlations

**Rationale:** Reduces the risk of accidental p-hacking and overfitting.

**Action items:**
- [ ] Finalize feature freeze criteria
- [ ] Document model baseline definitions
- [ ] Pre-register train/test strategy
- [ ] Commit to feature engineering freeze before Stage 1 begins
- [ ] Create analysis plan document (to be locked before Stage 2 data collection)

#### Stage 0 Deliverables (end of week 3)

- [ ] IRB approval or amendment confirmation
- [ ] Finalized label form (paper or app)
- [ ] Pre-registered outcome definitions with thresholds
- [ ] Feature freeze criteria and analysis plan document
- [ ] Ready to proceed to Stage 1

---

### Stage 1: Pre-AI Validation Studies (weeks 4–15)
Build and validate biomarkers before collecting the full longitudinal dataset.

**Study 1.1 — Label validity (2–4 weeks)**
- Collect after every session: whole-body RPE, forearm-specific RPE, soreness, readiness, sleep, stress
- Test-retest behavior across similar sessions
- Correlation among labels
- Decide final primary target before AI

**Study 1.2 — Impedance settling anchor (3–4 sessions)**
- Measure electrode-skin impedance at 0, 5, 10, 15, 20, 30 min
- Collect under different recovery states: well-rested, back-to-back, high-load, multi-day rest
- Does impedance drop track MDF rise?
- Does Phase I duration track impedance settling?

**Study 1.3 — Gel vs no-gel controlled comparison (3–5 paired sessions)**
- Same player, similar session type/intensity
- Does gel eliminate Phase I?
- Does gel reduce MDF drift?
- Do fatigue slopes after settling agree between gel and no-gel?

**Study 1.4 — Controlled fatigue calibration (1–2 sessions)**
- Standardized on-court or lab-like protocol: baseline → warmup → repeated forearm/wrist extensor task or ball machine blocks
- Fixed intensity blocks, e.g. 5 × 6 min with 2 min rest
- Collect RPE, MDF slope, RMS/envelope, grip strength per block
- Anchors "MDF decline = fatigue" in your exact wearable setup

**Study 1.5 — Recovery time-course probe (1 high-load session + follow-up)**
- After high-load session, collect short standardized readiness probes at: immediately post, next morning, 24h, 48h, 72h
- Each probe: 2–3 min standardized shadow swings or controlled wrist extension task
- Measure baseline MDF recovery, MDF response to standardized movement, Phase I duration, readiness/soreness
- Measures recovery dynamics directly

**Study 1.6 — Mechanical load validation (subset of sessions)**
- Compare practice vs match vs tournament
- Compare easy rally, hard rally, serve practice, match play
- Optional video annotation: forehand/backhand/serve, rally vs serve, estimated intensity
- Does gyro impulse distinguish session intensity better than swing count?
- Should features be separated by stroke type?

**Study 1.7 — Contact-quality and artifact taxonomy (ongoing)**
- Develop per-session quality metrics: valid EMG windows, contact-quality drift, RAW/ENV ratio, noise floor, saturation, dropout, BLE gaps, MDF confidence, motion artifact index
- Each session gets: usable / questionable / reject + reason codes
- Protects AI model from learning electrode artifacts as "fatigue"

### Stage 2: Longitudinal Data Collection (weeks 16–30+)
- Collect 40–80 sessions with validated labels and quality control
- Maintain logging discipline, weekly feature extraction
- No model fitting until N=40

### Stage 3: Feature Freeze & Extraction (after N=40)
- Finalize feature set based on Stage 1 validation
- Extract all features per session into `sessions.csv`
- Apply quality-control filtering

### Stage 4: Predictive Modeling (after N=40)
- Baseline models (persistence, sports-science, volume-only)
- Personalized models (elastic net, random forest, Bayesian updating)
- Validation: chronological split, leave-one-week-out
- Ablation: EMG-only, IMU-only, self-report-only

### Stage 5: Write-up & Submission
- Biomarker validation results
- Label validity findings
- Workload feature analysis
- Prediction performance
- Case studies of high-load weeks
- Overuse prevention roadmap

---

## Research Questions (Organized by Stage)

### Stage 0 RQs (IRB & Label Design)

**RQ0.1 (IRB scope).** What subjective data collection is ethically approved? What language is safe for the paper?

**RQ0.2 (label validity).** Which subjective labels are feasible to collect every session and meaningful for modeling?

**RQ0.3 (outcome definition).** What are the primary, secondary, and exploratory outcomes? What thresholds define "elevated soreness" or "readiness decline"?

**RQ0.4 (analysis plan).** What is the feature freeze criteria? What are the model baselines? What is the train/test strategy?

### Stage 1 RQs (Pre-AI Validation)

**RQ1.1 (label validity).** Which subjective labels are stable and meaningful?
- Is session-RPE enough, or is forearm-specific RPE better?
- Is next-morning soreness more predictive than immediate post-session RPE?
- Do readiness scores fluctuate meaningfully?

**RQ1.2 (impedance settling).** What does MDF Phase I settling actually represent?
- Does impedance drop track MDF rise?
- Does Phase I duration track impedance settling?
- Does residual fatigue alter Phase I independent of impedance?

**RQ1.3 (gel vs no-gel).** Can we separate electrode artifact from physiology?
- Does gel eliminate Phase I?
- Do fatigue slopes after settling agree between gel and no-gel?

**RQ1.4 (controlled fatigue).** Does MDF decline reliably indicate fatigue in your wearable setup?
- Does MDF slope correlate with perceived forearm fatigue in controlled blocks?
- Does grip strength decline track MDF decline?

**RQ1.5 (recovery dynamics).** How do EMG biomarkers recover over time?
- Does baseline MDF recover over 24–72 h?
- Does MDF response to standardized movement normalize?
- Does Phase I duration change with recovery?

**RQ1.6 (mechanical load).** Which IMU metric best represents tennis load?
- Does gyro impulse distinguish session intensity better than swing count?
- Does swing density predict RPE better than total swings?
- Should features be separated by stroke type?

**RQ1.7 (quality control).** Can we reliably flag bad sessions?
- What percent of sessions are usable / questionable / reject?
- Do quality flags correlate with feature reliability?

### Stage 2–5 RQs (AI Longitudinal Modeling)

**RQ2.1 (feasibility).** Can the wearable pipeline produce complete per-session EMG/IMU features across 40–80 sessions with <5% missing-data rate?

**RQ2.2 (within-session fatigue validity).** Do per-session MDF drop, MDF slope, or post-settling MDF change correlate with session-RPE and forearm-specific RPE (r > 0.4)?

**RQ2.3 (readiness biomarker).** Do Phase I settling duration, baseline MDF, or contact-quality trajectories vary systematically with days-since-last-session and pre-session readiness?

**RQ2.4 (longitudinal prediction).** Do rolling objective load features (acute/chronic IMU impulse, swing density, MDF trends) improve prediction of next-session readiness/soreness over simple volume and duration baselines (ΔR² > 0.05)?

**RQ2.5 (exploratory risk proxy).** Do periods of elevated rolling load precede soreness escalation, readiness decline, or self-reported unusual pain events?

---

## Why This Two-Stage Approach?

**Stage 1 (Pre-AI validation) is essential because:**

- Without validated biomarkers, AI models learn noise and artifact, not physiology
- Dry-electrode settling is ambiguous: could be contact artifact, sweat, residual fatigue, or temperature
- Subjective labels (RPE, soreness, readiness) may not be reliable or meaningful
- IMU workload features (swing count, gyro impulse) need validation against actual tennis intensity
- A single-athlete dataset is small; overfitting risk is high unless features are interpretable and grounded

**Stage 2 (AI modeling) is justified because:**

- Once biomarkers are validated, the relationship between load history and next-session fatigue is nonlinear and person-specific
- Multiple input streams (EMG features, IMU features, RPE, session spacing) interact in ways that linear models may underfit
- Within-subject personalization is explicitly the goal — a model trained on this player's 40–80 sessions should outperform a generic population model
- Personalized Bayesian updating is a natural fit for single-subject longitudinal data

**Realistic AI scope for N=40–80 sessions:**

1. **Persistence baseline** — next readiness = previous readiness
2. **Sports-science baseline** — session-RPE × duration, ACWR using duration or swing count
3. **IMU workload model** — gyro impulse ACWR, high-intensity swing ACWR
4. **EMG workload model** — MDF fatigue load, MDF recovery state
5. **Combined personalized model** — elastic net / ridge regression
6. **Nonlinear exploratory model** — random forest or gradient boosting (exploratory only)
7. **Bayesian updating model** — updates personalized risk/readiness estimate session by session
8. **Future work (not this paper)** — LSTM or transformer over session-level time series

**Key principle:** For N=40–80 sessions, interpretability and statistical rigor matter more than model complexity.
The AI angle is "personalized longitudinal modeling with validated biomarkers," not deep learning.

---

---

## Prediction Targets & Feature Hierarchy

### Primary Prediction Targets (Stage 2+)

- **next-session forearm readiness** (1–5 scale)
- **next-morning soreness** (0–10 scale)
- **post-session forearm RPE** (0–10 scale)

### Secondary Targets

- whole-body session-RPE
- MDF fatigue magnitude
- Phase I duration
- recovery-probe MDF baseline

### Exploratory Target

- **soreness escalation event:** soreness ≥4/10 AND readiness ≤2/5 for ≥2 consecutive sessions, OR self-reported unusual elbow/wrist/shoulder pain

---

### Feature Hierarchy (Tier 1 → Tier 5)

#### Tier 1: Volume Baseline
- session duration (min)
- swing count
- session type (practice / match / tournament)
- days since last session

#### Tier 2: Mechanical Load (IMU)
- cumulative gyro impulse
- high-intensity swing count (gyro > 95th percentile)
- swing density (swings/min)
- 95th percentile gyro magnitude
- serve-like swing count (if detectable)
- forehand/backhand clusters (if separable)

#### Tier 3: EMG Fatigue
- MDF drop after settling (Phase III magnitude, %)
- MDF slope in final phase (Hz/min)
- RMS/envelope increase (dB)
- post-settling baseline MDF (Hz)
- fatigue index per swing cluster
- MDF confidence / PSD peak quality

#### Tier 4: Recovery & Context
- sleep quality (1–5)
- pre-session readiness (1–5)
- prior-session soreness
- days since last session
- rolling acute/chronic load (ACWR)
- perceived stress (1–5)

#### Tier 5: Quality-Aware Features
- valid EMG window percentage
- contact-quality drift
- MDF confidence
- impedance if measured
- motion artifact index
- BLE gap duration

---

### Primary vs. Exploratory Outcomes

**Primary outcomes (pre-registered, hypothesis-driven):**
- RQ1.1–RQ1.7: Biomarker validation (Stage 1)
- RQ2.1–RQ2.4: Feasibility, fatigue validity, readiness biomarker, longitudinal prediction (Stage 2+)

**Exploratory outcomes (hypothesis-generating, not confirmatory):**
- RQ2.5: Soreness/readiness decline as soft proxy for load intolerance
- Feature importance rankings from random forest
- Personalized model coefficients and their stability over time
- Stroke-type-specific load features

**Injury prediction:** Framed as motivation and future work, not a primary validated outcome.
True overuse injury is a clinical endpoint; a single-athlete observational study cannot strongly validate it.
Instead, we use soreness escalation and readiness decline as practical early-warning proxies for load intolerance.

---

## Stage 2: Longitudinal Data Collection Protocol

**Target:** 1 player, **40–80 sessions** over 3–6 months (e.g., September–February, including
tournament weeks, rest weeks, practice-only weeks).

**Rationale for N=40–80:**
- Sufficient for chronological train/test split (70/30) with ~56 training sessions
- Enough variation in load, recovery, and readiness to fit nonlinear models without overfitting
- Realistic for a single athlete over a competitive season
- Stretch target (80) allows for more robust validation and ablation studies

**Missing-data policy (pre-registered):**
- If a session has <80% of EMG/IMU data, exclude it from analysis (report count)
- If a session lacks RPE or readiness label, impute from adjacent sessions or exclude
- Report all exclusions and sensitivity analysis with/without imputation

**Model evaluation strategy (pre-registered):**
- **Chronological split:** first 70% of sessions for training, last 30% for testing (respects temporal structure, avoids data leakage)
- **Leave-one-week-out validation:** if enough data, validate on held-out weeks
- **Baseline comparisons:** always report persistence, volume, and objective-load baselines
- **Metrics:** MAE, RMSE, Spearman/Pearson correlation (not just R²)
- **Ablation:** test EMG-only, IMU-only, self-report-only models to isolate contributions

---



**Per-session capture (objective):**
- Full BLE EMG+IMU capture with btCentral.py (same hardware as Papers 1/2)
- Extract per-session features (see Feature Hierarchy above)
- Apply quality-control filtering (Stage 1.7 results)

**Per-session label (subjective, <2 minutes of overhead):**
- **Session-RPE**: Borg CR10 scale (0–10), collected 30 min post-session
- **Forearm-specific RPE**: CR10 scale (0–10) — "How fatigued does your forearm/arm feel specifically?"
- **Pre-session readiness**: 1–5 scale ("How do your forearm/arm feel right now?")
- **Next-morning soreness**: 0–10 scale (collected before next session)
- **Sleep quality last night**: 1–5 (confound control)
- **Session type**: practice / match / tournament (categorical)
- **Opponent level / drill intensity**: easy / medium / hard (categorical)
- **Notes**: unusual pain, injury history, equipment changes, etc. (free text)

**Per-session survey template (finalized after Stage 1.1):**
```
Session #: ___  Date: ___  Duration: ___ min  Type: [ ] Practice [ ] Match [ ] Tournament

IMMEDIATELY AFTER (30 min post-session):
  Session-RPE (0–10): ___
  Forearm-specific RPE (0–10): ___

BEFORE NEXT SESSION:
  Pre-session readiness (1–5): ___
  Next-morning soreness (0–10): ___
  Sleep quality (1–5): ___
  Opponent level (easy/med/hard): ___
  Notes: _______________
```

**Quality control per session (automated):**
- Valid EMG window percentage
- Contact-quality drift
- MDF confidence
- Motion artifact index
- BLE gap duration
- Session classification: usable / questionable / reject

### When to collect impedance (from paper2_plan.md §H1)
At sessions 1, 10, 20 (or first session of each month), measure impedance with LCR meter at
t=0,5,10,15,20,30 min to anchor the Phase I settling curve. This ties into RQ2.

---

## Comprehensive Feature Table (Stage 2+)

| Feature | Source | Tier | Rationale |
|:---|:---|:---|:---|
| `session_duration_min` | timestamp | 1 | Clock-time load |
| `swing_count` | IMU | 1 | Total session volume |
| `session_type` | categorical | 1 | Practice vs. match load profile differs |
| `days_since_last_session` | timestamp | 1 | Recovery window |
| `cumulative_gyro_impulse` | IMU | 2 | Total mechanical load (area under gyro magnitude) |
| `high_intensity_swing_count` | IMU | 2 | Swings with gyro > 95th percentile |
| `swing_density_per_min` | IMU+timestamp | 2 | Intensity proxy (workload rate) |
| `gyro_95th_percentile` | IMU | 2 | Peak impact intensity |
| `serve_like_swing_count` | IMU | 2 | Serves (if detectable) |
| `forehand_backhand_clusters` | IMU | 2 | Stroke-type separation (if separable) |
| `mdf_phase3_drop_pct` | sEMG | 3 | Phase III fatigue magnitude |
| `mdf_slope_final_phase` | sEMG | 3 | Fatigue rate (Hz/min) |
| `rms_envelope_increase_db` | sEMG | 3 | Muscle activation increase |
| `mdf_baseline_hz` | sEMG | 3 | Post-settling stable MDF — neuromuscular state at session start |
| `mdf_settling_duration_min` | sEMG | 3 | Phase I length — readiness biomarker candidate |
| `mdf_confidence` | sEMG | 3 | PSD peak quality |
| `sleep_quality` | self-report | 4 | Confound control |
| `pre_session_readiness` | self-report | 4 | Residual soreness proxy |
| `prior_session_soreness` | self-report | 4 | Load history context |
| `acute_load_7d` | rolling IMU | 4 | ACWR numerator: sum of gyro impulse over last 7 days |
| `chronic_load_28d` | rolling IMU | 4 | ACWR denominator: rolling 28-day average |
| `acwr` | derived | 4 | Acute:chronic load ratio |
| `perceived_stress` | self-report | 4 | Confound control |
| `valid_emg_window_pct` | QC | 5 | Data quality |
| `contact_quality_drift` | QC | 5 | Electrode stability |
| `motion_artifact_index` | QC | 5 | Movement contamination |
| `ble_gap_duration_s` | QC | 5 | Connectivity issues |
| `impedance_if_measured` | optional | 5 | Electrode-skin impedance (Stage 1.2) |

**Target labels:**
- `session_rpe`: whole-body (0–10)
- `forearm_rpe`: forearm-specific (0–10) — primary target
- `next_session_readiness`: 1-step-ahead prediction (1–5) — primary target
- `next_morning_soreness`: 0–10 — primary target
- `soreness_escalation_event`: binary flag (exploratory)

---

## Hypotheses to Test

### Stage 1 Hypotheses (Pre-AI Validation)

**H1.1 (label validity).** Forearm-specific RPE and next-morning soreness are more stable and predictive
than whole-body session-RPE. Correlation with objective EMG/IMU features: r > 0.3.

**H1.2 (impedance settling).** Phase I duration correlates with impedance settling time (r > 0.5).
Residual fatigue alters Phase I independent of impedance (partial correlation > 0.3 after controlling for impedance).

**H1.3 (gel vs no-gel).** Gel eliminates Phase I settling. Fatigue slopes after settling agree between
gel and no-gel (r > 0.7). This confirms Phase I is electrode artifact, not physiology.

**H1.4 (controlled fatigue).** MDF slope in controlled fatigue blocks correlates with perceived forearm
fatigue (r > 0.5). Grip strength decline tracks MDF decline (r > 0.4).

**H1.5 (recovery dynamics).** Baseline MDF recovers over 24–72 h. MDF response to standardized movement
normalizes with recovery (r > 0.4 with days since high-load session).

**H1.6 (mechanical load).** Gyro impulse distinguishes session intensity better than swing count (ΔR² > 0.05
in predicting session-RPE). Swing density predicts RPE better than total swings (ΔR² > 0.05).

**H1.7 (quality control).** >80% of sessions are usable. Quality flags correlate with feature reliability
(sessions with low quality scores have higher prediction error).

### Stage 2–4 Hypotheses (AI Longitudinal Modeling)

**H2.1 (feasibility).** >95% of sessions produce complete EMG/IMU features with <5% missing-data rate.

**H2.2 (within-session fatigue validity).** MDF drop, MDF slope, and post-settling MDF change correlate
with forearm-specific RPE (r > 0.4) across ≥40 sessions.

**H2.3 (readiness biomarker).** Phase I settling duration and baseline MDF vary systematically with
days-since-last-session and pre-session readiness (r > 0.3).

**H2.4 (longitudinal prediction).** Rolling objective load features (acute/chronic IMU impulse, swing density,
MDF trends) improve prediction of next-session readiness/soreness over volume baselines (ΔR² > 0.05).

**H2.5 (exploratory: load-soreness link).** High-ACWR periods (rolling load > 75th percentile) precede
soreness escalation or readiness decline events (within 1–3 sessions). Reported as hypothesis-generating.

---

## Connections to Existing Literature

**Session-RPE (Foster et al. 2001):** Standard training load quantification. Most tennis load studies use
session-RPE × session duration as the "training load" proxy. We replace the duration multiplier with
sEMG-derived muscle load and validate forearm-specific RPE as a more sensitive target.

**Acute:chronic workload ratio (Gabbett 2016):** ACWR from GPS/accelerometry is used in soccer and rugby
to predict injury risk. Applied to sEMG for upper-extremity sport is novel. We validate IMU-derived ACWR
against EMG fatigue biomarkers.

**Dry-electrode impedance dynamics (Joutsen 2024, Ravichandran 2023):** These established impedance settling
in lab. Paper 3 uses Phase I duration as a field-accessible proxy and validates it with LCR meter measurements.

**MDF/MNF decline in tennis (Rota et al. 2014, Wang LH 2019):** Established MDF decline in controlled tennis
sessions. Paper 3 extends to longitudinal within-subject tracking and validates against controlled fatigue.

**Wearable EMG for fatigue monitoring (Farina & Merletti 2004, Phinyomark et al. 2018):** Established EMG
spectral features for fatigue. Paper 3 applies these in real-world tennis with validation experiments.

**Gap statement (novel):** No existing published study:
1. Validates dry-electrode settling interpretation using impedance measurements and gel/no-gel controls
2. Develops and validates a quality-control framework for real-world EMG/IMU in sport
3. Tracks sEMG spectral fatigue features longitudinally across 40+ real tennis sessions
4. Fuses validated biomarkers with session-RPE and recovery metrics in a personalized load model
5. Demonstrates that objective muscle-load features improve prediction over volume-only training load

**Strongest novelty claim:** A low-cost field-deployable EMG/IMU system enables longitudinal, session-level
muscle-load tracking in real tennis practice. By validating biomarkers through controlled experiments first,
we create a personalized dataset linking objective forearm fatigue biomarkers, mechanical load, recovery
spacing, and subjective readiness. This is novel, achievable, and directly applicable to athlete monitoring
and overuse injury prevention.

---

## Stage 0: IRB & Label Design Protocol

**Objective:** Finalize IRB coverage, design per-session survey, and pre-register study design before any data collection.

**Q1: Session-RPE scale.** Borg CR10 (0–10) vs. Borg 6–20 RPE vs. simple 1–5?
*Recommendation: Borg CR10 — simplest to explain, continuous enough for regression, most used in sports science since Foster 2001.*

**Q2: Whole-session RPE vs. forearm-specific?** Standard session-RPE covers the whole body. We will add a forearm-specific question ("how fatigued does your forearm/arm feel specifically?") alongside whole-body RPE. Two questions, 10 seconds each.
*Recommendation: Include both.*

**Q3: ACWR window sizes.** 7:28 days is the classic Gabbett ratio. For a youth tennis player who plays 3–5×/week, 7:21 or 3:14 may be more appropriate. Should be tuned to the specific player's schedule.
*Recommendation: Start with 7:28, then test 7:21 and 3:14 in sensitivity analysis.*

**Q4: How to handle tournament weeks.** Multiple matches in 2–3 days: very different load profile from practice. Session type as a categorical covariate is necessary.
*Recommendation: Include session type in all models; report separate results for practice vs. match.*

**Q5: Soft endpoints for load intolerance.** Instead of true injury (rare in 40–80 sessions), use: soreness escalation (pre-session readiness dropping below threshold for 3+ consecutive sessions), next-morning soreness spike (>2-point increase), or self-reported unusual pain event.
*Recommendation: Pre-register thresholds before data collection.*

**Q6: Ethical/IRB scope.** This is longitudinal (months, single subject). Review current IRB packet — [IRB_Packet_OSU_sEMG_IMU_Athletic_Practice.md](IRB_Packet_OSU_sEMG_IMU_Athletic_Practice.md) — to confirm it covers repeated sessions and collection of subjective ratings (RPE, readiness, soreness, sleep, stress). If the player is a minor, parental consent procedures apply.
*Recommendation: Confirm IRB coverage before Stage 1 begins.*

**Q7: Phase I settling mechanism.** The settling biomarker hypothesis (H1.2) is physically ambiguous: longer rest could mean *more* sweat clearance (impedance higher = longer settling) OR *more* residual fatigue (faster re-hydration from prior session). Stage 1.2 impedance measurements (LCR meter, paper2_plan.md §H1) would directly answer this.
*Recommendation: Collect impedance at sessions 1, 10, 20 to anchor Phase I interpretation.*

---

## Differentiation from Papers 1 and 2

| | Paper 1 (journal_draft.md) | Paper 2 (paper2_plan.md) | Paper 3 (this) |
|:---|:---|:---|:---|
| **Focus** | Trustworthy per-session sEMG methodology | Engineering platform | Longitudinal AI load model |
| **Time horizon** | Single session | Single session | 3–5 months, 40–60 sessions |
| **Subjects** | 1 pilot → N3 multi-subject | 1 | 1 (start) → small cohort |
| **AI component** | None | None | Central |
| **Outcome variable** | MDF trajectory | BLE reliability, latency | Session-RPE, injury risk |
| **Novel contribution** | Settling-aware methodology | Embedded systems | Personalized load model |
| **IRB scope** | Athletic practice sessions | Same | Same + subjective ratings |

---

## Strawman Paper Outline

1. Introduction — overuse injury in tennis; gap in objective longitudinal monitoring
2. Related Work — session-RPE, ACWR, wearable EMG fatigue, tennis injury epidemiology
3. System and Per-Session Pipeline — (cite Paper 1/2; brief) + new: per-session feature extraction
4. Data Collection — single-player longitudinal protocol, N sessions, schedule, labeling
5. Within-Session Features — MDF three-phase characterization at scale (N sessions)
6. Cross-Session Load Model — ACWR analogue from IMU; rolling features
7. AI Model — baseline (linear) + main (random forest / LSTM) + personalization
8. Results — RQ1–RQ4 hypothesis tests; feature importance; load-RPE correlation
9. Discussion — settling as readiness biomarker; ACWR from EMG; limitations
10. Conclusion and Future Work — multi-subject; intervention study (recommend rest)

---

---

## Immediate Action Items: Phase 0 (Weeks 1–3)

### Phase 0A — IRB / Ethics Scope

- [ ] **Review current IRB packet** — [IRB_Packet_OSU_sEMG_IMU_Athletic_Practice.md](IRB_Packet_OSU_sEMG_IMU_Athletic_Practice.md)
- [ ] **Confirm coverage for:**
  - repeated longitudinal sessions over months
  - subjective fatigue ratings (RPE, soreness, readiness)
  - soreness/pain location reports
  - sleep quality and stress
  - optional grip strength
  - optional impedance measurements
  - optional video annotation
  - minor participant rules and consent procedures
- [ ] **Identify gaps** — what new items need IRB amendment?
- [ ] **Draft amendment if needed** — add new label items, clarify "soreness/readiness decline" language
- [ ] **Get written IRB approval** before Stage 1 begins

### Phase 0B — Label Design

- [ ] **Finalize pre-session form** — date, readiness, soreness (forearm/elbow/shoulder/wrist), sleep, notes
- [ ] **Finalize post-session form** — session-RPE, forearm-specific RPE, intensity, duration, unusual pain
- [ ] **Finalize next-morning form** — soreness (forearm/elbow/wrist/shoulder), readiness, pain affecting activity
- [ ] **Test with 2–3 pilot sessions** — measure time to complete, clarity, missing fields
- [ ] **Refine based on feedback** — adjust wording, add/remove fields
- [ ] **Freeze form** before Stage 1 begins

### Phase 0C — Define Primary & Exploratory Outcomes

- [ ] **Define primary outcome 1:** `next_morning_forearm_soreness` (0–10, threshold ≥4/10)
- [ ] **Define primary outcome 2:** `next_session_forearm_readiness` (1–5, threshold ≤2/5)
- [ ] **Define secondary outcomes:** post-session forearm RPE, whole-body session-RPE, elbow/wrist/shoulder soreness
- [ ] **Define exploratory outcome:** `soreness_risk_proxy` (binary event: soreness ≥4/10 OR readiness ≤2/5 OR soreness increase ≥2 points OR pain persists 2+ sessions)
- [ ] **Pre-register thresholds** — document rationale for each
- [ ] **Freeze outcome definitions** before Stage 1 begins

### Phase 0D — Define Feature Freeze & Analysis Plan

- [ ] **Finalize feature freeze criteria:**
  - Minimum sessions before model training: 40
  - Target sessions: 60–80
  - Valid EMG session: >80% data completeness, contact quality drift <threshold, no saturation
  - Missing label policy: impute or exclude
- [ ] **Define model baselines:** persistence, volume-only, sports-science (session-RPE × duration)
- [ ] **Pre-register train/test strategy:** chronological split (70/30), leave-one-week-out validation
- [ ] **Commit to feature engineering freeze** — no feature engineering after looking at target correlations
- [ ] **Create analysis plan document** — lock before Stage 2 data collection

#### Phase 0 Deliverables (end of week 3)

- [ ] IRB approval or amendment confirmation
- [ ] Finalized label form (paper or app)
- [ ] Pre-registered outcome definitions with thresholds
- [ ] Feature freeze criteria and analysis plan document
- [ ] Ready to proceed to Stage 1

---

## Immediate Action Items: Phase 1 (Weeks 4–15)

#### Study 1.1 — Label Validity (weeks 3–6)
- [ ] **Collect 2–4 weeks of sessions** with full survey: whole-body RPE, forearm-specific RPE, soreness, readiness, sleep, stress
- [ ] **Analyze test-retest behavior** across similar sessions
- [ ] **Compute correlations** among labels
- [ ] **Identify which labels correlate most with objective EMG/IMU**
- [ ] **Decide final primary target** before AI (likely forearm-specific RPE or next-morning soreness)

#### Study 1.2 — Impedance Settling Anchor (weeks 4–6)
- [ ] **Schedule 3–4 impedance sessions** under different recovery states
- [ ] **Measure electrode-skin impedance** at 0, 5, 10, 15, 20, 30 min with LCR meter
- [ ] **Collect under:** well-rested, back-to-back sessions, high-load tournament, multi-day rest
- [ ] **Analyze:** Does impedance drop track MDF rise? Does Phase I duration track impedance settling?
- [ ] **Determine:** Is Phase I mostly contact artifact or physiological?

#### Study 1.3 — Gel vs No-Gel Controlled Comparison (weeks 5–8)
- [ ] **Schedule 3–5 paired sessions** (same player, similar type/intensity)
- [ ] **Collect:** one no-gel dry electrode session, one gel/prepped session per pair
- [ ] **Analyze:** Does gel eliminate Phase I? Do fatigue slopes after settling agree?
- [ ] **Conclusion:** Separates electrode artifact from physiology

#### Study 1.4 — Controlled Fatigue Calibration (weeks 6–7)
- [ ] **Design standardized protocol:** baseline → warmup → repeated forearm/wrist extensor task or ball machine blocks
- [ ] **Collect 1–2 sessions:** 5 × 6 min blocks with 2 min rest, RPE after each block
- [ ] **Measure:** MDF slope, RMS/envelope, grip strength per block
- [ ] **Analyze:** Does MDF slope correlate with perceived forearm fatigue (r > 0.5)?
- [ ] **Anchor:** "MDF decline = fatigue" in your exact wearable setup

#### Study 1.5 — Recovery Time-Course Probe (weeks 7–9)
- [ ] **Select 1 high-load session** (match or tournament)
- [ ] **Collect short readiness probes** at: immediately post, next morning, 24h, 48h, 72h
- [ ] **Each probe:** 2–3 min standardized shadow swings or controlled wrist extension task
- [ ] **Measure:** baseline MDF, MDF response to standardized movement, Phase I duration, readiness/soreness
- [ ] **Analyze:** Does baseline MDF recover over 24–72 h? Does Phase I duration change with recovery?

#### Study 1.6 — Mechanical Load Validation (weeks 8–10)
- [ ] **Collect subset of sessions** with video annotation (optional): forehand/backhand/serve, rally vs serve, estimated intensity
- [ ] **Compare:** practice vs match vs tournament, easy rally vs hard rally vs serve practice
- [ ] **Analyze:** Does gyro impulse distinguish session intensity better than swing count (ΔR² > 0.05)?
- [ ] **Decide:** Should features be separated by stroke type?

#### Study 1.7 — Contact-Quality & Artifact Taxonomy (weeks 9–12, ongoing)
- [ ] **Develop per-session quality metrics:** valid EMG windows, contact-quality drift, RAW/ENV ratio, noise floor, saturation, dropout, BLE gaps, MDF confidence, motion artifact index
- [ ] **Classify each session:** usable / questionable / reject + reason codes
- [ ] **Analyze:** >80% usable? Do quality flags correlate with feature reliability?
- [ ] **Output:** Quality-control framework for Stage 2

#### Study 1 Deliverables (end of week 12)
- [ ] Validated label set (primary target identified)
- [ ] Impedance settling interpretation (Phase I mechanism clarified)
- [ ] Gel vs no-gel conclusion (artifact vs physiology separated)
- [ ] Controlled fatigue calibration (MDF-fatigue anchor established)
- [ ] Recovery dynamics (baseline MDF recovery time-course)
- [ ] Mechanical load features (IMU feature ranking)
- [ ] Quality-control framework (session classification rules)

---

## Immediate Action Items: Phase 2 (Weeks 16–30+)

#### Setup (week 13)
- [ ] **Finalize feature extractor** — extend `emg_util_yaml_runner.py` to emit all Tier 1–5 features per session into `sessions.csv`
- [ ] **Implement quality-control filtering** — apply Stage 1.7 rules to each session
- [ ] **Set up weekly analysis pipeline** — automated feature extraction, quality flagging, missing-data reporting
- [ ] **Pre-register feature set** — freeze all features before analyzing any AI model results

#### Data Collection (weeks 13–26+)
- [ ] **Collect 40–80 sessions** with validated labels and quality control
- [ ] **Maintain logging discipline** — date, duration, type, partner level logged every session
- [ ] **Weekly feature extraction** — no model fitting until N=40
- [ ] **Monitor missing-data rate** — target <5%
- [ ] **Track quality flags** — report usable / questionable / reject counts

#### Phase 2 Deliverables (after N=40)
- [ ] Complete `sessions.csv` with all features and labels
- [ ] Quality-control report (missing-data rate, session classification)
- [ ] Ready for Stage 3 (Feature Freeze & Extraction)

---

## Prioritized Experiments (Must-Do vs. High-Value Optional)

### Must-Do (Critical for Paper 3)
1. **Per-session survey protocol** — Without good labels, AI is weak
2. **Impedance measurements** — Critical for interpreting Phase I
3. **Gel vs no-gel sessions** — Critical artifact/physiology separation
4. **Controlled fatigue calibration** — Anchors MDF fatigue
5. **Longitudinal 40–80 session collection** — Main dataset
6. **Quality-control scoring** — Prevents garbage-in/garbage-out AI

### High-Value Optional (Strengthens Paper 3)
7. **Recovery probe after hard sessions** — Very novel and powerful
8. **Video annotation subset** — Validates IMU workload features
9. **Grip strength pre/post** — Simple external fatigue proxy
10. **Small cohort expansion** — Even N=3–5 athletes would make the paper much stronger (but adds IRB/logistics complexity)

---

## Proposed Paper Outline (After All Stages Complete)

1. **Introduction**
   - Overuse injury motivation (tennis elbow, shoulder impingement, wrist injuries)
   - Lack of field-deployable muscle-load monitoring
   - Need for validated biomarkers before AI

2. **System Overview**
   - Briefly cite Paper 1/2 platform
   - EMG/IMU capture and session pipeline

3. **Pre-AI Biomarker Validation Studies (Stage 1)**
   - Study 1.1: Label validity (which subjective labels are reliable?)
   - Study 1.2: Impedance settling (what does Phase I represent?)
   - Study 1.3: Gel vs no-gel (artifact vs physiology)
   - Study 1.4: Controlled fatigue calibration (MDF-fatigue anchor)
   - Study 1.5: Recovery time-course (baseline MDF recovery dynamics)
   - Study 1.6: Mechanical load validation (IMU feature ranking)
   - Study 1.7: Contact-quality taxonomy (quality-control framework)

4. **Longitudinal Data Collection (Stage 2)**
   - 40–80 sessions protocol
   - Labels and session metadata
   - Quality control and missing-data policy

5. **Feature Extraction & Hierarchy (Stage 3)**
   - Tier 1–5 features (volume, mechanical load, EMG fatigue, recovery, quality)
   - Quality-aware filtering
   - Feature freeze before modeling

6. **Predictive Modeling (Stage 4)**
   - Baseline models (persistence, volume, sports-science)
   - Personalized models (elastic net, random forest, Bayesian updating)
   - Validation method (chronological split, leave-one-week-out)
   - Ablation studies (EMG-only, IMU-only, self-report-only)

7. **Results**
   - Stage 1 biomarker validation findings
   - Label validity and feature importance
   - Workload feature analysis
   - Prediction performance (MAE, RMSE, correlation)
   - Case studies of high-load weeks and recovery patterns

8. **Discussion**
   - What biomarkers mean physiologically
   - What AI can/cannot predict
   - Field deployment implications
   - Overuse prevention roadmap
   - Limitations and future work

9. **Conclusion**

---

## Paper 3 Contribution Set

Paper 3 claims:

1. **First longitudinal field dataset** of tennis forearm sEMG/IMU load across 40+ real sessions using low-cost wearable hardware.

2. **Validation of dry-electrode settling interpretation** using impedance measurements and gel/no-gel controls — separates electrode artifact from physiology.

3. **Quality-aware per-session EMG biomarker extraction** for real-world sport — develops and validates a quality-control framework.

4. **IMU-derived mechanical load features** beyond swing count — validates gyro impulse, swing density, and stroke-type separation.

5. **Personalized predictive model** for readiness/soreness using combined EMG, IMU, and subjective features — demonstrates within-subject personalization.

6. **Evidence that objective muscle-load features improve prediction** over volume-only training load — quantifies the value of biomarker-driven modeling.

7. **Overuse injury prevention roadmap** — frames soreness/readiness decline as practical early-warning proxies for load intolerance.

This is much stronger than simply "AI predicts injury risk." The paper is a rigorous research program that validates biomarkers first, then models them.
