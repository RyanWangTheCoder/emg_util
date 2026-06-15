# Paper 3: Quality-Aware Personalized Longitudinal Tracking and Modeling of Tennis Forearm Load and Next-Day Readiness Using Wearable sEMG–IMU

**Status:** Research program design — two-stage approach. Read paper2_plan.md and journal_draft.md for
the foundational platform and methodology (Paper 1/2) that this builds on.

**Primary claim:**
> A quality-aware, personalized longitudinal wearable framework can convert noisy real-tennis sEMG/IMU
> data into reliable session-level forearm load biomarkers that improve prediction of next-morning soreness
> and next-session readiness over volume-only baselines.

**Key principle:** Do not rush into AI. First create a high-quality longitudinal physiology + workload
dataset with validation experiments. Only after biomarkers and labels are credible, train personalized models.

**What this paper is NOT:** This is not another standalone ML/AI fatigue classifier. Recent adjacent work
already demonstrates high-performing multimodal fatigue classification in controlled settings, including
CNN-LSTM-Attention sEMG/IMU models and attention-based sEMG+ACC fusion models. Our contribution is
different: longitudinal, field-deployed, quality-aware, tennis-specific, personalized load-to-readiness
modeling. Layer-1 per-swing ML is used only to produce interpretable session-level load summaries for
Layer-2 readiness/soreness prediction.

**Relationship to earlier ML roadmap (`RESEARCH_ROADMAP.md`):** The earlier broad roadmap described a
different direction: N=20 participants, one 90-minute session each, multimodal sensor fusion with MVC/RPE
ground truth, and attention-based fusion. That approach is not Paper 3. This plan supersedes it for
Paper 3. The roadmap remains useful for feature ideas and validation references, but the Paper 3 contribution
is a single-subject longitudinal N-of-1 study focused on load-to-readiness modeling, not cross-subject
fatigue classification. Without this explicit statement, implementation may drift back toward the N=20
attention-fusion design.

---

## Scope Boundaries (Decided Upfront)

These are explicit constraints, not limitations to apologize for. Stating them early prevents scope creep.

| Out of scope | Reason | How it's handled |
|---|---|---|
| Cross-subject generalization | IRB barriers, inter-subject EMG variability | Framed as N-of-1 personalized methodology — this is the contribution, not a weakness |
| Supervised injury prediction | No injury ground-truth labels possible from a single player | Replaced by soreness/readiness decline as practical early-warning proxies |
| Deep learning (LSTM, transformer) | N=40–80 sessions too small; interpretability required | Classical ML only (elastic net, random forest); LSTM is future work |
| Per-swing ML as standalone contribution | Time-proxy labels are too weak for a standalone result | Layer 1 (per-swing RF) is a feature engineering step feeding Layer 2, not an independent claim |

**Injury risk framing:** We do not claim to predict injury. Instead, we flag periods where objective
load metrics (ACWR, MDF trends) exceed validated thresholds from sports science literature. This is
rule-based / signal processing — defensible without injury ground truth.

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
across sessions, fused with player self-report, to build a personalized readiness model and flag
load-intolerance patterns early enough to prevent injury.

---

---

## Research Program: Five Stages

**Canonical timeline (use consistently throughout):**

| Stage | Weeks | Description |
|---|---|---|
| Stage 0 | 1–3 | IRB, label design, analysis plan, feature freeze |
| Stage 1 | 4–12 | Pre-AI biomarker validation studies (7 studies) |
| Stage 2 setup | 13–15 | Finalize pipeline, QC framework, feature extractor |
| Stage 2 collection | 16–30+ | Longitudinal data collection (40–60 valid sessions) |
| Stage 3 | After N≥40 valid sessions | Feature freeze and extraction |
| Stage 4 | After Stage 3 | Predictive modeling and evaluation |
| Stage 5 | After Stage 4 | Write-up and submission |

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

**Canonical event labels** (three separate binary flags, pre-registered before data collection):

- **`soreness_escalation_event`:** next_morning_forearm_soreness ≥4/10 OR soreness increase ≥2 points from rolling baseline
- **`readiness_decline_event`:** next_session_forearm_readiness ≤2/5 OR readiness drop ≥1 point from rolling baseline
- **`load_intolerance_proxy_event`:** soreness_escalation_event OR readiness_decline_event OR unusual pain report

**Rationale:** Separating the two components avoids the AND/OR ambiguity that arises from mixing soreness
and readiness thresholds. `load_intolerance_proxy_event` is the composite risk signal used for case studies
and exploratory analysis. Not a clinical injury endpoint — frame as a practical load-intolerance proxy.

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

### Stage 1: Pre-AI Validation Studies (weeks 4–12)
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

**Study 1.7 — Contact-quality and artifact taxonomy (ongoing) — Named Contribution**

**Contribution name:** *A quality-aware biomarker extraction framework for wearable sports EMG in dynamic field settings*

This is not just preprocessing hygiene — it is a named paper contribution. Real-world applicability
and advanced signal processing remain a major gap in wearable sports EMG literature. A 2025 scoping
review (BMC Sports Science, Medicine and Rehabilitation) reported that IMUs are the most commonly used
sensors, sensor fusion is gaining traction, and gaps remain in advanced processing methods and
real-world applicability. The quality framework enables everything else in the paper; without
it, session-level features computed from bad data will corrupt the regression model and invalidate claims.

- Develop per-session quality metrics: valid EMG windows, contact-quality drift, RAW/ENV ratio, noise floor, saturation, dropout, BLE gaps, MDF confidence, motion artifact index
- Each session gets: usable / questionable / reject + reason codes
- **Report quality statistics as a result:** % usable sessions, most common failure modes, quality flag correlation with feature reliability
- **Ablation:** show that including low-quality sessions degrades model performance — this quantifies the value of the QC framework
- Protects AI model from learning electrode artifacts as "fatigue"

### Stage 2: Longitudinal Data Collection (weeks 16–30+)
*Stage 2 setup (weeks 13–15): finalize pipeline, QC framework, and feature extractor — see "Immediate Action Items: Phase 2 Setup" below. Longitudinal collection begins week 16.*
- Collect 40 valid minimum / 60 valid target / 80 valid stretch sessions with validated labels and quality control
- Maintain logging discipline, weekly feature extraction
- No model fitting until N=40 valid usable sessions

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

**Conference version (strong, realistic — build this first):**
1. Quality-aware real-tennis dataset and pipeline (QC framework as contribution)
2. Validated session-level biomarkers from real field data
3. Stroke-aware load quantification (serve vs. groundstroke breakdown)
4. Early personalized prediction of next-morning soreness / next-session readiness
5. Ablation showing value beyond volume-only workload metrics

**Journal version (stronger, more distinctive — extends conference):**
1. Full Stage 1 validation studies (at minimum: impedance settling + controlled fatigue calibration)
2. 40 valid minimum / 60 valid target / 80 valid stretch longitudinal sessions with complete quality-control reporting
3. Stroke-aware load features with video-annotation validation subset
4. Small replication cohort (N=2–4, biomarker/QC validation only) — strengthens generalizability claims
5. Decision-oriented outputs: soft risk proxy, case studies of high-load weeks
6. Full ablation suite including no-QC condition

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

**Two-layer ML architecture (single subject, self-report labeled):**

**Layer 1 — Per-swing fatigue/load proxy estimation (feature engineering step, not standalone claim)**
- Input: 18-feature vector per swing (EMG time-domain, frequency-domain, envelope, IMU kinematics)
- Labels: time-in-session proxy, calibrated against session-level forearm RPE — these are **weak proxy
  labels, not ground truth fatigue labels**. Do not call them "fatigue classes" in the paper.
- Model: Random Forest estimator (design in `ML/ML_FATIGUE_CLASSIFICATION.md`)
- **Do NOT report Layer 1 classification accuracy as a primary result.** Adjacent papers already
  dominate this space with attention-based multimodal classifiers and high headline numbers. Comparing
  real-tennis weak-label accuracy against controlled lab classification invites unfavorable review.
- Language: use `load_score_proxy`, `within-session load index`, `late-session load score`,
  or `RF-derived load/fatigue index` — avoid "fatigue classification", "ground truth fatigue labels",
  "high fatigue class"
- Purpose: produces session-aggregate load descriptors for Layer 2. Report these aggregates, not accuracy:
  - `late_session_load_depth` — mean proxy score in final third of session
  - `high_load_swing_frac` — fraction of swings with high proxy score
  - `load_onset_swing` — swing index where high-load proxy first persists
  - `load_proxy_slope` — linear regression of proxy score over session time
  - `emg_imu_disagreement_rate` — fraction of swings where EMG and IMU features conflict
  - `layer1_confidence_mean` — mean RF prediction probability (low = uncertain signal quality)

**Layer 2 — Cross-session readiness regression (primary ML contribution)**
- Input: session-level Tier 1–5 features including Layer 1 outputs
- Labels: player self-report — post-session forearm RPE, pre-session readiness, next-morning soreness
- Model: elastic net / ridge regression (primary); random forest (exploratory nonlinear)
- Primary claim: objective wearable features (EMG load + IMU workload) improve next-session
  readiness prediction over volume-only baselines (ΔR² > 0.05)

**Self-report labeling strategy:**
- Post-session (30 min after): session-RPE CR10, forearm-specific RPE — anchors Layer 1 proxy labels
- Pre-session: readiness 1–5, forearm soreness 0–10 — primary regression targets
- Next morning: soreness 0–10 — highest-value target (overuse response appears after session)
- Consistency mitigation: standardized prompts, immediate collection, periodic RPE anchor checks

**Canonical label names (use these exact names in all code and paper text):**

| Canonical name | Scale | Collection time | Role |
|---|---|---|---|
| `pre_session_forearm_readiness` | 1–5 | Before session N | Input feature for session N model |
| `next_session_forearm_readiness` | 1–5 | Before session N+1 | **Primary prediction target** (created by shifting `pre_session_forearm_readiness` back one session) |
| `next_morning_forearm_soreness` | 0–10 | Morning after session N | **Primary prediction target** |
| `post_session_forearm_rpe` | 0–10 CR10 | 30 min after session N | Secondary target; also anchors Layer 1 labels |
| `post_session_whole_body_rpe` | 0–10 CR10 | 30 min after session N | Confound control |
| `soreness_escalation_event` | binary | Derived | Exploratory: next_morning_forearm_soreness ≥4/10 OR soreness increase ≥2 points from rolling baseline |
| `readiness_decline_event` | binary | Derived | Exploratory: next_session_forearm_readiness ≤2/5 OR readiness drop ≥1 point from rolling baseline |
| `load_intolerance_proxy_event` | binary | Derived | Exploratory: soreness_escalation_event OR readiness_decline_event OR unusual pain report |

**Important target-shifting rule:**
`next_session_forearm_readiness` at row N = `pre_session_forearm_readiness` at row N+1.
This one-step-ahead shift must be applied before any model training. Never use current-session
pre_session_readiness as a prediction target — that is the input, not the output.

**Realistic AI models for N=40–80 sessions:**

1. **Persistence baseline** — next readiness = previous readiness
2. **Volume baseline** — session-RPE × duration, swing count only
3. **IMU workload model** — gyro impulse ACWR, high-intensity swing ACWR
4. **EMG workload model** — MDF fatigue load, MDF recovery state (Layer 1 outputs)
5. **Combined personalized model** — elastic net / ridge regression (Tier 1–4 features)
6. **Nonlinear exploratory model** — random forest or gradient boosting (exploratory only)
7. **Bayesian updating model** — updates personalized readiness estimate session by session
8. **Future work (not this paper)** — LSTM, cross-subject transfer learning

**Key principle:** For N=40–80 sessions, interpretability and statistical rigor matter more than model
complexity. The AI angle is "personalized longitudinal modeling with validated biomarkers," not deep learning.
Layer 1 per-swing ML is a feature engineering step. Layer 2 cross-session regression is the publishable claim.

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

- **soreness escalation event:** `soreness_escalation_event` = next_morning_forearm_soreness ≥4/10 OR soreness increase ≥2 points from rolling baseline
- **readiness decline event:** `readiness_decline_event` = next_session_forearm_readiness ≤2/5 OR readiness drop ≥1 point from rolling baseline
- **load intolerance proxy event:** `load_intolerance_proxy_event` = soreness_escalation_event OR readiness_decline_event OR unusual pain report

---

### Feature Hierarchy (Tier 1 → Tier 5)

#### Tier 1: Volume Baseline
- session duration (min)
- swing count
- session type (practice / match / tournament)
- days since last session

#### Tier 2: Mechanical Load (IMU) — Stroke-Aware (Central Contribution)

**Rationale:** Generic "swing count" or "total gyro impulse" loses the tennis-specific overuse story.
Tennis involves repeated high-load strokes, and sports injury literature highlights abrupt changes in
acute-to-chronic workload as an important extrinsic injury-related factor. Tennis serve biomechanics
work also shows that segmental angular velocities differ by serve type and relate to performance.
Therefore, stroke-aware load features aggregate load both globally and by stroke category. Stroke-aware
features are primary **only if validated against video annotation** on a subset of sessions; otherwise
they are reported as exploratory.

**Required features (every session):**
- cumulative gyro impulse (all strokes)
- high-intensity swing count (gyro > 95th percentile)
- swing density (swings/min)
- 95th percentile gyro magnitude
- **serve-like swing count** — IMU peak pattern, gyro > serve threshold
- **serve-specific forearm load** — gyro impulse from serve-like swings only
- **forehand/backhand cluster counts** — separated by IMU peak asymmetry
- **stroke-type forearm load breakdown** — serve vs. forehand vs. backhand gyro impulse totals

**Why stroke-aware is a contribution:** Tennis involves repeated high-load strokes, and sports injury
literature identifies abrupt increases in acute-to-chronic workload ratio as a strong extrinsic
injury-related factor. Tennis serve biomechanics research also shows that upper-body segmental
angular velocities differ by stroke type and relate to performance, supporting the need to avoid
collapsing all strokes into a single undifferentiated load metric. In our targeted review, we did
not identify a longitudinal wearable EMG paper that separates forearm load by stroke type at session scale.

**Caveat:** Stroke-aware features (serve-specific load, forehand/backhand counts) are treated as
**primary contributions if validated against video annotation** on a subset of sessions; otherwise
they are reported as exploratory. This prevents reviewer challenge of "how do you know those are serves?"

**Stroke-aware validation hierarchy:**
1. **Primary (with video validation):** Binary serve vs. non-serve detection — pre-define agreement
   threshold: macro-F1 ≥ 0.75 OR serve-detection precision ≥ 0.80 AND recall ≥ 0.70. If met,
   serve-specific load features are primary contributions.
2. **Secondary/exploratory (with video):** Forehand vs. backhand cluster separation — harder to
   validate reliably from wrist-mounted IMU alone; report as exploratory even if video exists.
3. **If no video annotation:** Report all stroke-type features as "unsupervised high-load swing
   clusters" — do not claim named stroke types. The load decomposition (high-gyro vs. low-gyro
   swings) remains valid; the stroke-type label does not.

#### Tier 3: EMG Fatigue
- MDF drop after settling (Phase III magnitude, %)
- MDF slope in final phase (Hz/min)
- RMS/envelope increase (dB)
- post-settling baseline MDF (Hz)
- fatigue index per swing cluster
- MDF confidence / PSD peak quality

#### Tier 4: Recovery & Context
- sleep quality (1–5)
- pre_session_forearm_readiness (1–5)
- prior-session forearm soreness (0–10)
- days_since_last_high_load_session (derived)
- rolling_soreness_7d (rolling mean of last 7 days soreness)
- readiness_trend_3session (slope of last 3 pre-session readiness values)
- rolling acute/chronic load (ACWR — see ACWR validity rule)
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

**Target:** 1 player, sessions collected over 3–6 months (e.g., September–February, including
tournament weeks, rest weeks, practice-only weeks).

**Canonical session-count targets (use these consistently throughout the document):**
- **Minimum analyzable dataset:** 40 valid (usable) sessions
- **Target dataset:** 60 valid sessions
- **Stretch dataset:** 80 valid sessions
- **Expected duration:** 3–6 months depending on schedule, session type mix, and QC rejection rate

**Rationale for N=40–60:**
- 40 valid sessions: sufficient for chronological train/test split (70/30) with ~28 training sessions
- 60 valid sessions: preferred — ~42 training sessions, enough for elastic net with cross-validation
- Stretch (80): more robust validation, ablation studies, and leave-one-week-out validation
- Realistic for a single athlete over a competitive season, accounting for ~15–20% session rejection rate

**Missing-data policy (pre-registered):**
- If a session has <80% of EMG/IMU data, exclude it from analysis (report count)
- If a session lacks RPE or readiness label, impute from adjacent sessions or exclude
- Report all exclusions and sensitivity analysis with/without imputation

**Model evaluation strategy (pre-registered, mandatory reporting):**
- **Chronological split:** first 70% of sessions for training, last 30% for testing (respects temporal structure, avoids data leakage)
- **Leave-one-week-out validation:** if enough data, validate on held-out weeks
- **Mandatory baselines — ALL must be reported:**
  1. Persistence baseline: next readiness = previous readiness
  2. Volume-only baseline: swing count + session duration
  3. Sports-science baseline: session-RPE × duration (Foster 2001 standard)
  4. IMU-only model
  5. EMG-only model
  6. Self-report-only model
- **Metrics:** MAE, RMSE, Spearman ρ, Pearson r (not just R² — R² can be misleading for small N)
- **Calibration plots:** predicted vs. actual readiness/soreness scatter for each model
- **Event-based evaluation for soreness escalation proxy:** precision/recall for flagging high-load weeks
- **Case studies:** 2–3 high-load weeks showing how load features preceded soreness/readiness decline
- **No-QC ablation:** rerun best model including rejected sessions — quantifies QC framework value

*Rationale: The BJSM 2024 sports ML injury review found that many models look good numerically but
have questionable clinical relevance due to missing baselines and narrow evaluation. Mandatory baselines
and ablations are the direct counter to that criticism.*

**ACWR validity rule (pre-registered):**
ACWR features (`acute_load_7d`, `chronic_load_28d`, `acwr`) are computed only after ≥21 days of
prior recorded data. Sessions before this threshold receive missing indicators for ACWR columns and
are excluded from ACWR-specific analyses. Report the warm-up exclusion count explicitly. Sensitivity
analysis: test ACWR with 7:28, 7:21, and 3:14 windows; report which performs best on the validation
set without re-selecting on test set.

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
| `days_since_last_session` | timestamp | 1 | Recovery window — keep in Tier 1 only |
| `cumulative_gyro_impulse` | IMU | 2 | Total mechanical load (area under gyro magnitude) |
| `high_intensity_swing_count` | IMU | 2 | Swings with gyro > 95th percentile |
| `swing_density_per_min` | IMU+timestamp | 2 | Intensity proxy (workload rate) |
| `gyro_95th_percentile` | IMU | 2 | Peak impact intensity |
| `serve_like_swing_count` | IMU | 2 | **Stroke-aware:** serves (gyro pattern + threshold) |
| `serve_gyro_impulse` | IMU | 2 | **Stroke-aware:** forearm load from serve-like swings only |
| `forehand_count` | IMU | 2 | **Stroke-aware:** forehand cluster count |
| `backhand_count` | IMU | 2 | **Stroke-aware:** backhand cluster count |
| `stroke_load_breakdown` | IMU | 2 | **Stroke-aware:** gyro impulse per stroke type |
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
| `acwr` | derived | 4 | Acute:chronic load ratio — **valid only after ≥21 days of prior data; mark missing for earlier sessions** |
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

**Gap statement:** In our targeted review of adjacent wearable fatigue, sports injury ML, and tennis
biomechanics literature, we did not identify a study that combines all four elements: (1) longitudinal
real-tennis sEMG/IMU monitoring across a competitive season, (2) quality-aware EMG session screening
with ablation quantifying its value, (3) stroke-aware forearm load aggregation validated against video
annotation, and (4) personalized prediction of next-morning soreness or next-session readiness from
within-session fatigue biomarkers. This combination is the core novelty of Paper 3.

**Strongest novelty claim:** A low-cost field-deployable EMG/IMU system enables longitudinal, session-level
muscle-load tracking in real tennis practice. The core contribution is the intra-to-inter session bridge:
per-swing objective fatigue metrics linked to next-session readiness, validated against athlete self-report.
By validating biomarkers through controlled experiments first, we create a personalized dataset linking
objective forearm fatigue biomarkers, mechanical load, recovery spacing, and subjective readiness.
This is novel, achievable with a single subject, and directly applicable to athlete monitoring.

---

## Differentiation from Papers 1 and 2

| | Paper 1 (journal_draft.md) | Paper 2 (paper2_plan.md) | Paper 3 (this) |
|:---|:---|:---|:---|
| **Focus** | Trustworthy per-session sEMG methodology | Engineering platform | Quality-aware personalized longitudinal load-to-readiness model |
| **Time horizon** | Single session | Single session | 3–6 months, 40 valid min / 60 valid target / 80 valid stretch sessions |
| **Subjects** | 1 pilot → N3 multi-subject | 1 | 1 (full longitudinal) + 2–4 (biomarker/QC validation only) |
| **AI component** | None | None | Central — but elastic net / RF, not deep learning |
| **Outcome variable** | MDF trajectory | BLE reliability, latency | Next-morning soreness, next-session readiness |
| **Novel contribution** | Settling-aware methodology | Embedded systems | Quality-aware + stroke-aware + personalized load-to-readiness pipeline |
| **IRB scope** | Athletic practice sessions | Same | Same + subjective ratings + optional small cohort for biomarker validation |

---

## Strawman Paper Outline

1. Introduction — overuse injury in tennis; gap in objective longitudinal monitoring
2. Related Work — session-RPE, ACWR, wearable EMG fatigue, tennis injury epidemiology
3. System and Per-Session Pipeline — (cite Paper 1/2; brief) + new: per-session feature extraction
4. Data Collection — single-player longitudinal protocol, N sessions, schedule, labeling
5. Within-Session Features — MDF three-phase characterization at scale (N sessions)
6. Cross-Session Load Model — ACWR analogue from IMU; rolling features
7. AI Model — baselines + elastic net/ridge primary model + RF/gradient boosting exploratory personalization
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
- [ ] **Define exploratory outcome:** canonical event labels (three separate binary flags):
  - `soreness_escalation_event`: next_morning_forearm_soreness ≥4/10 OR soreness increase ≥2 points from rolling baseline
  - `readiness_decline_event`: next_session_forearm_readiness ≤2/5 OR readiness drop ≥1 point from rolling baseline
  - `load_intolerance_proxy_event`: soreness_escalation_event OR readiness_decline_event OR unusual pain report
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

## Immediate Action Items: Phase 1 (Weeks 4–12)

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

#### Setup (weeks 13–15)
- [ ] **Finalize feature extractor** — extend `emg_util_yaml_runner.py` to emit all Tier 1–5 features per session into `sessions.csv`
- [ ] **Implement quality-control filtering** — apply Stage 1.7 rules to each session
- [ ] **Set up weekly analysis pipeline** — automated feature extraction, quality flagging, missing-data reporting
- [ ] **Pre-register feature set** — freeze all features before analyzing any AI model results

**Required output files (all must be produced before Stage 4 modeling):**

```text
sessions.csv             — all extracted features for ALL sessions (including questionable/rejected)
                           columns: subject_id, session_id, session_date, session_type,
                                    source_log_dir, emg_segment_count, imu_segment_count,
                                    quality_status, quality_reason_codes,
                                    [all Tier 1–5 features], [all canonical label columns]

session_quality.csv      — QC metrics and rejection reason codes per session
                           columns: session_id, quality_status, valid_emg_window_pct,
                                    contact_quality_drift, ble_gap_duration_s,
                                    mdf_confidence, motion_artifact_index, rejection_reason

swing_features.csv       — per-swing feature vectors and Layer 1 proxy scores
                           columns: session_id, swing_id, t_peak_ms, [18 EMG+IMU features],
                                    load_score_proxy, stroke_type_guess, layer1_confidence

model_ready_sessions.csv — QC-filtered, label-complete rows ready for Layer 2 regression
                           (sessions.csv filtered to quality_status=usable AND labels present)
                           Must include: source_quality_status (carries the original QC flag from
                           sessions.csv for auditability and downstream debugging)

readiness_labels.csv     — canonical label columns with target-shifted next_session values
                           columns: session_id, pre_session_forearm_readiness,
                                    next_session_forearm_readiness (shifted from N+1),
                                    next_morning_forearm_soreness, post_session_forearm_rpe,
                                    soreness_escalation_event, load_intolerance_proxy_event
```

**Why separate files matter:**
- `sessions.csv` vs `model_ready_sessions.csv` split enables the no-QC ablation (rerun model on full sessions.csv)
- `session_quality.csv` is a paper result, not just preprocessing metadata
- `readiness_labels.csv` keeps the target-shifting logic explicit and auditable

#### Data Collection (weeks 16–30+)
- [ ] **Collect 40–60 sessions** (target) / 80 (stretch) with validated labels and quality control
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
5. **Longitudinal 40 valid min / 60 valid target / 80 valid stretch session collection** — Main dataset
6. **Quality-control scoring** — Prevents garbage-in/garbage-out AI

### High-Value Optional (Strengthens Paper 3)
7. **Recovery probe after hard sessions** — Very novel and powerful
8. **Video annotation subset** — Validates IMU stroke-type classification (serve vs. forehand vs. backhand)
9. **Grip strength pre/post** — Simple external fatigue proxy, anchors MDF decline interpretation
10. **Small replication cohort (N=2–4 players, biomarker/QC only)** — Even 2–4 additional athletes
    collected for Stage 1 validation only (not full longitudinal) would materially strengthen the journal
    version. Specific value: (a) confirms QC framework generalizes beyond one player's electrode placement
    and skin characteristics; (b) confirms MDF settling and controlled-fatigue findings are not
    idiosyncratic to one subject; (c) allows reviewers to accept Stage 1 biomarker claims with higher
    confidence. Does NOT require full 40–80 sessions per player — 3–5 controlled sessions per player
    is sufficient for biomarker plausibility. IRB and logistics are manageable at this small scale.

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
   - 40 valid minimum / 60 valid target / 80 valid stretch sessions protocol
   - Labels and session metadata
   - Quality control and missing-data policy

5. **Feature Extraction & Hierarchy (Stage 3)**
   - Tier 1–5 features (volume, mechanical load, EMG fatigue, recovery, quality)
   - Quality-aware filtering
   - Feature freeze before modeling

6. **Predictive Modeling (Stage 4)**
   - Baseline models (persistence, volume-only, session-RPE×duration)
   - Combined personalized model: elastic net / ridge regression (primary)
   - Nonlinear exploratory model: random forest or gradient boosting (exploratory only)
   - Validation method (chronological split, leave-one-week-out)
   - Ablation studies (EMG-only, IMU-only, self-report-only, no-QC)
   - Note: No deep learning (LSTM, transformer) — N=40–60 sessions is too small; LSTM is future work

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

### Four Headline Contributions

**1. Quality-aware EMG/IMU biomarker extraction framework for dynamic field tennis**
- Named contribution, not background preprocessing
- Settling-aware, contact-drift-aware, activity-gated, motion-artifact-filtered
- Produces usable/questionable/reject session classification with quantified value (ablation)
- Addresses the real-world applicability gap identified in sensor-based sports injury literature: a 2025 scoping review (BMC Sports Science, Medicine and Rehabilitation) reported that IMUs are the most used sensors, sensor fusion is gaining traction, and gaps remain in advanced processing and real-world applicability

**2. Stroke-aware objective forearm-load quantification across sessions**
- Serve-specific vs. forehand vs. backhand load decomposition at session scale
- Supports the stroke-aware load story: tennis involves repeated high-load strokes, and sports injury literature identifies abrupt acute-to-chronic workload ratio increases as a strong extrinsic injury-related factor; serve biomechanics studies show segmental angular velocities differ by serve type and relate to performance, supporting stroke-type separation over undifferentiated totals
- **Primary if validated against video annotation on a subset of sessions; otherwise reported as exploratory**
- Validated against session-RPE and mechanical load differences across session types
- Not found in existing longitudinal wearable EMG papers

**3. Personalized prediction of next-morning soreness and next-session readiness**
- Intra-to-inter session bridge: per-swing fatigue aggregates → session-level readiness regression
- Self-report labels as practical sports-science targets: session-RPE is a standard training-load measure (Foster 2001), while forearm-specific RPE and next-morning soreness provide localized readiness/load-intolerance endpoints for this N-of-1 design
- Single-athlete N-of-1 personalized model, not generic population model — this is the design, not a weakness
- Framed as soreness/readiness decline proxy, explicitly not clinical injury prediction (avoids BJSM criticism)

**4. Evidence that objective load biomarkers outperform volume-only baselines**
- Mandatory ablation: persistence, volume-only, session-RPE×duration, IMU-only, EMG-only, self-report-only
- ΔR² > 0.05 target for combined model over best volume baseline
- Calibration plots and case studies of high-load weeks anchor clinical relevance

### What this paper explicitly does NOT claim
- Injury prediction (no injury ground truth — use soreness/readiness decline proxies)
- Cross-subject generalization (single subject by design — N-of-1 methodology is the contribution)
- Deep learning superiority (elastic net / random forest for 40 valid minimum / 60 valid target / 80 valid stretch sessions; LSTM is future work)
- Classification accuracy as primary metric (Layer 1 RF serves Layer 2, not reviewed as standalone)

### Literature positioning

| This paper | Adjacent work | Why we differ |
|---|---|---|
| Longitudinal 40 valid min / 60 valid target / 80 valid stretch real-tennis sessions | Lab fatigue induction, 1–2 sessions (MDPI 2025, PLOS ONE 2025) | Ecological validity, overuse timeframe |
| Next-morning soreness / readiness regression | Fatigue state classification (binary or 3-class) | Decision-oriented, not just detection |
| Quality-aware framework (usable/reject per session) | Signal processing described but not validated as contribution | Named QC contribution with ablation |
| Stroke-aware load (serve vs. forehand vs. backhand) | Generic swing count or total activity | Tennis-specific overuse mechanism |
| N-of-1 personalized model, single athlete | Cross-subject LOSO (35–80 subjects) | Personalization angle, single-IRB feasible |
| Classical ML (elastic net, RF), interpretable | CNN-LSTM-Attention (87.94%), multilevel attention (92%) | N too small for DL; interpretability required |

---

## Appendix A: Stage 0 Design Decisions

These are one-time decisions to make before data collection begins. Captured here to avoid revisiting
them mid-study. Answers are locked once Stage 1 begins.

**Q1: Session-RPE scale.** Borg CR10 (0–10) vs. Borg 6–20 RPE vs. simple 1–5?
*Decision: Borg CR10 — simplest to explain, continuous enough for regression, most used in sports science since Foster 2001.*

**Q2: Whole-session RPE vs. forearm-specific?** Standard session-RPE covers the whole body. We will add a forearm-specific question ("how fatigued does your forearm/arm feel specifically?") alongside whole-body RPE. Two questions, 10 seconds each.
*Decision: Include both.*

**Q3: ACWR window sizes.** 7:28 days is the classic Gabbett ratio. For a youth tennis player who plays 3–5×/week, 7:21 or 3:14 may be more appropriate. Should be tuned to the specific player's schedule.
*Decision: Start with 7:28, then test 7:21 and 3:14 in sensitivity analysis.*

**Q4: How to handle tournament weeks.** Multiple matches in 2–3 days: very different load profile from practice. Session type as a categorical covariate is necessary.
*Decision: Include session type in all models; report separate results for practice vs. match.*

**Q5: Soft endpoints for load intolerance.** Instead of true injury (rare in 40–80 sessions), use: soreness escalation (pre-session readiness dropping below threshold for 3+ consecutive sessions), next-morning soreness spike (>2-point increase), or self-reported unusual pain event.
*Decision: Pre-register thresholds before data collection.*

**Q6: Ethical/IRB scope.** This is longitudinal (months, single subject). Review current IRB packet — [IRB_Packet_OSU_sEMG_IMU_Athletic_Practice.md](../IRB_Packet_OSU_sEMG_IMU_Athletic_Practice.md) — to confirm it covers repeated sessions and collection of subjective ratings (RPE, readiness, soreness, sleep, stress). If the player is a minor, parental consent procedures apply.
*Decision: Confirm IRB coverage before Stage 1 begins.*

**Q7: Phase I settling mechanism.** The settling biomarker hypothesis (H1.2) is physically ambiguous: longer rest could mean *more* sweat clearance (impedance higher = longer settling) OR *more* residual fatigue (faster re-hydration from prior session). Stage 1.2 impedance measurements (LCR meter, paper2_plan.md §H1) would directly answer this.
*Decision: Collect impedance at sessions 1, 10, 20 to anchor Phase I interpretation.*
