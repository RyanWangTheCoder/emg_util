# TODO: Existing-Data Experiments for `log0303` and `log0305`

**Purpose:** Prioritized experiment list using only the two existing captures (`log0303`, `log0305`).  
**No new data required:** no microphone, no video, no racket sensor.  
**Primary goal:** strengthen Paper 1 findings and identify which tennis-specific artifact algorithms are worth pursuing for Paper 2.

---

## Summary Priority Table

> **Note on numbering:** Experiment IDs (column 1) match the section headers throughout
> this document. Priority rank (column 0) is the execution order. IDs 13 and 5b were added
> later; the ID sequence is not the same as the rank sequence for those two items.

| Rank | Experiment ID | Experiment | Primary value | Paper target |
|---:|---:|---|---|---|
| 1 | 1 | ✅ Warmup-skip sensitivity figure | Central claim: standard skip misses fatigue | Paper 1 |
| 2 | 2 | ✅ Electrode settling MDF/RMS curve | Central mechanism: settling lasts 17–20 min | Paper 1 |
| 3 | 3 | ✅ IMU consistency plot | Validates fatigue vs reduced effort | Paper 1 |
| 4 | 4 | ✅ Contact quality metric plot | Supports proposed EMG quality monitor | Paper 1 |
| 5 | 5 | ✅ `log0303` gap artifact visualization | Shows BLE gap/cross-segment artifact | Paper 1 |
| 6 | 5b | ✅ IMU-EMG diagnostic matrix (Figure 7) | 2×2 IMU vs EMG quality scatter | Paper 1 |
| 7 | 6 | ✅ Rest/noise-floor tracker | Strengthens contact/settling argument | Paper 1 / Paper 2 |
| 8 | 7 | ✅ Robust MDF outlier filtering | Handles transient artifacts | Paper 1 / Paper 2 |
| 9 | 8 | ✅ Early/mid/late PSD comparison | Explains MDF mechanism | Paper 1 |
| 10 | 9 | ✅ Adaptive settling endpoint | Turns finding into algorithm | Paper 1 / Paper 2 |
| 11 | 10 | ✅ **PSD around high-jerk events (gateway)** | **Gate for all impact algorithms** | **Paper 2** |
| 12 | 11 | Pre-impact MDF vs full-window MDF | Tests phase-gated spectral analysis | Paper 2 |
| 13 | 12 | Forearm-only impact-risk score | Prototype future artifact-risk metric | Paper 2 |
| 14 | 14 |✅ RAW/ENV consistency diagnostic | Hardware reliability / contact diagnostics | Paper 1 / Paper 2 |
| 15 | 15 | ✅ Swing intensity stratification | Controls for changing effort | Paper 1 |
| 16 | 16 | ✅ Bout-level fatigue analysis | Reduces per-swing noise | Paper 1 |
| 17 | 17 | Workload accumulation metric | Fatigue vs cumulative load | Paper 2 |
| 18 | 18 | BLE gap/session stitching audit | Validates timeline reconstruction | Paper 1 |
| 19 | 13 | Empty/contact separability limitation | Clarifies what existing data cannot prove | Future data |

---

# Priority 1 — Must-do for Paper 1

These should be completed first because they directly support the current paper’s central claims.

---

## 1. Warmup-Skip Sensitivity Figure

**Goal:** Show that a standard warmup skip can completely miss or invert fatigue findings.

### Data

Use existing analysis outputs:

```text
out0305
out0305_v2
out0305_w15
out0305_w20
```

### Compute / plot

For each warmup setting:

```text
baseline MDF
final MDF
MDF drop %
MNF drop %
```

Known values:

| Warmup skip | Output dir | Baseline MDF | Final MDF | MDF drop | Interpretation |
|---|---|---:|---:|---:|---|
| 10 min | `out0305` | 137.1 Hz | 140.7 Hz | −2.6% | false negative |
| 10 min + RMS baseline | `out0305_v2` | 166.0 Hz | 140.8 Hz | +15.2% | moderate fatigue |
| 15 min | `out0305_w15` | 112.3 Hz | 141.8 Hz | −26.2% | inverted / still settling |
| 20 min | `out0305_w20` | 199.2 Hz | 143.2 Hz | +28.1% | fatigue revealed |

### Expected result

```text
10 min: fatigue missed
15 min: baseline still contaminated
20 min: true post-settling baseline, fatigue revealed
```

### Output

```text
Figure 4: warmup-skip sensitivity bar chart
```

### Paper value

This is one of the strongest Paper 1 figures.

---

## 2. Electrode Settling Curve with Rolling MDF/RMS

**Goal:** Make electrode settling visually obvious.

### Data

```text
log0305
out0305_w20/swing_features.csv
```

### Compute / plot

```text
per-swing MDF vs time
rolling median MDF, window = 5 or 10 swings
rolling RMS or contact_quality
vertical lines at 10, 15, 20 min
```

Candidate settling endpoint:

```text
first time rolling MDF sustains >= 150 Hz for 5 consecutive swings
```

### Expected result

```text
MDF rises from ~108 Hz early to ~160–166 Hz stable
settling extends to roughly 17–20 min
```

### Output

```text
Figure 2: MDF vs time, first 30 min of log0305
```

### Paper value

Central visual evidence for the settling claim.

---

## 3. IMU Consistency vs EMG Fatigue Trend

**Goal:** Show the player did not simply reduce swing effort.

### Data

```text
log0305
out0305_w20/swing_features.csv
```

### Compute / plot

```text
imu_peak_mag vs time
rolling median imu_peak_mag
Pearson r vs time
early / mid / late mean ± std
```

Known result:

```text
Pearson r = +0.01
p = 0.78
```

Known early/mid/late values:

```text
Early: 1577.5 ± 693.7 dps
Mid:   1572.8 ± 713.4 dps
Late:  1591.1 ± 705.8 dps
```

### Expected result

```text
IMU swing intensity remains flat while corrected MDF drops
```

### Output

```text
Figure 3: IMU peak magnitude over time
```

### Paper value

Supports the interpretation that corrected MDF drop is not simply reduced effort.

---

## 4. Contact Quality Metric Plot

**Goal:** Validate the proposed quality metric:

```text
contact_quality(t) = RMS_window(t) / session_p90_rms
```

### Data

```text
log0305
log0303
```

### Compute

```text
contact_quality_i = emg_rms_i / p90(emg_rms_session)
```

### Expected result

For `log0305`:

```text
early low / unstable contact_quality
mid/late stable contact_quality
```

For `log0303`:

```text
possible discontinuity across BLE segments
or different contact state after reconnection
```

### Output

```text
Figure 5: contact_quality over session
```

### Paper value

Supports IMU-conditioned EMG quality monitoring and gives an intuitive signal-quality plot.

---

## 5. `log0303` Gap Artifact Visualization

**Goal:** Show why `log0303` should not be interpreted as a continuous fatigue session.

### Data

```text
out0303_v2/swing_features.csv
out0303_seg1/swing_features.csv
```

### Compute / plot

```text
MDF vs reconstructed absolute time
mark 66-min BLE gap
mark segment 1 and segment 2
compare full-session drop vs segment-1-only drop
```

Known values:

```text
full session MDF drop: 28.7%
segment 1 only MDF drop: 4.9%
gap: ~66 min
```

### Expected result

```text
Full-session drop is cross-segment artifact.
Segment 1 alone shows no meaningful fatigue.
```

### Output

```text
Figure 6: log0303 MDF over time with gap annotation
```

### Paper value

Shows field deployment artifact and validates hybrid timeline reconstruction.

---

## 5b. IMU-EMG Diagnostic Matrix (Figure 7)

**Goal:** Show the 2×2 decision logic that distinguishes settling, fatigue, reduced effort,
and mechanical artifacts using IMU and EMG as independent axes.

### Data

```text
out0305_w20/swing_features.csv   (IMU flat, MDF drops after settling → fatigue quadrant)
out0303_v2/swing_features.csv    (cross-segment artifact)
```

### Compute / plot

Scatter: `imu_peak_mag` (x-axis, effort proxy) vs `mdf` (y-axis), coloured by session third
(early / mid / late) for log0305.

Optionally overlay the 2×2 interpretation quadrants:

```text
IMU flat   + MDF stable     → normal (post-settling, no fatigue)
IMU flat   + MDF dropping   → physiological fatigue
IMU flat   + MDF depressed  → electrode settling (early session)
IMU rising + MDF rising     → warm-up
```

### Expected result

```text
Early swings cluster at low MDF (settling) despite normal IMU intensity
Late swings cluster at low MDF (fatigue) despite normal IMU intensity
IMU intensity remains flat across all three thirds
```

### Output

```text
Figure 7: IMU-EMG diagnostic matrix scatter, log0305
```

### Paper value

Makes the core IMU cross-validation logic visual and directly supports Core Contribution 2.

---

# Priority 2 — High-Value Existing-Data Experiments

These strengthen the current paper and may become Paper 1 additions or Paper 2 bridge analyses.

---

## 6. IMU-Quiet EMG Baseline Tracker

**Goal:** Use IMU-defined rest windows as an in-situ signal-quality proxy.

### Data

```text
log0305 primarily
log0303 secondarily
```

### Method

Implemented as sliding-window scan over all IMU data (not restricted to between-swing gaps —
see implementation notes below):

```text
sliding 500 ms IMU windows (100 samples @ 200 Hz, 50% overlap)
accept window if gyro_mag < 50 dps for ≥90% of samples
compute DC-removed raw EMG RMS in matching EMG window
smooth with rolling median over 10 windows
```

Note: wording is "IMU-quiet EMG baseline" not "between-swing rest" because the
implementation scans all IMU data, not exclusively inter-swing gaps. If strictly
between-swing tracking is needed, implement gap-restricted selection using
`t_start_ms` / `t_end_ms` from swing_features.csv.

### Metrics

```text
rest_rms
noise_floor_trend
noise_floor early/mid/late
```

### Interpretation

```text
high early rest noise / instability → settling/contact issue
stable mid-session rest noise → better contact
late increase → possible electrode degradation / sweat loosening
```

### Expected value

This is stronger than swing RMS alone because rest windows have minimal voluntary contraction.

### Risk

Dense tennis sessions may have few clean rest windows, but `log0305` likely has enough between bouts.

---

## 7. EMG Outlier Detection and Robust Fatigue Slope

**Goal:** Make fatigue trend estimation less sensitive to transient artifacts.

### Data

```text
log0305
log0303 segment 1
```

### Method

```text
rolling median MDF, window = 7 swings
MAD = median absolute deviation
outlier if |MDF - local_median| > 3 * MAD
```

Then compare:

```text
fatigue slope before outlier rejection
fatigue slope after outlier rejection
ordinary least squares vs Theil-Sen robust regression
```

### Expected result

```text
log0305 corrected fatigue trend remains
variance decreases
log0303 segment 1 remains near-flat
```

### Output

```text
MDF time series with outliers marked
table of slope/drop before and after robust filtering
```

### Paper value

Good artifact-aware postprocessing method that does not need impact timing.

---

## 8. Early / Mid / Late PSD Comparison

**Goal:** Explain why MDF changes during settling and fatigue.

### Data

```text
log0305 raw EMG or per-swing PSD if available
```

### Method

Aggregate normalized PSD for:

```text
early settling swings
mid stable swings
late swings
```

Suggested bands:

```text
low band: 50–150 Hz
mid band: 150–250 Hz
high band: 250–450 Hz
```

### Metrics

```text
MDF
MNF
spectral centroid
low-band fraction
high-band fraction
```

### Expected result

```text
early settling: lower-frequency dominated / noisy
mid stable: higher MDF
late fatigue: corrected MDF lower than post-settling baseline
```

### Output

```text
PSD overlay early/mid/late
band energy table
```

### Paper value

Mechanistic support for the MDF-based interpretation.

---

## 9. Adaptive Settling Endpoint Detection

**Goal:** Replace fixed warmup skip with a data-driven criterion.

### Data

```text
log0305
```

### Candidate criteria

```text
rolling MDF median > 150 Hz for 5 consecutive swings
contact_quality > 0.25 for 5 consecutive swings
rolling MDF std < threshold
IMU intensity not changing strongly
```

### Compare

```text
adaptive endpoint time vs fixed 20-min skip
baseline MDF from adaptive endpoint vs baseline MDF from 20-min skip
fatigue drop using adaptive baseline
```

### Expected result

```text
adaptive endpoint approximately agrees with 17–20 min stabilization
```

### Output

```text
detected settling endpoint time
baseline selected by adaptive method
fatigue result using adaptive skip
```

### Paper value

Turns the observational finding into a practical algorithm.

### Risk and Results (updated 2026-05-03)

**Grid search result:** An exhaustive grid of 432 parameter combinations (MDF threshold
160–190 Hz, std threshold 20–40 Hz, CQ threshold 0.20–0.30, n=5/10/15, guard time
0/10/12/15 min) was run on log0305. Results:

- 321/432 combinations never trigger within the session.
- Best achievable endpoint: t=12.9 min — baseline MDF 98.8 Hz (still in settling).
- Highest MDF drop among triggered: 7.1% — versus 28.1% from 20-min fixed skip.
- **No grid combination approximates the 20-min endpoint or the 28.1% fatigue result.**

**Conclusion:** Simple threshold-based adaptive detection is insufficient on a single
session. The 20-min fixed skip outperforms all adaptive criteria tested here.

**Critical data need:** More captured sessions from different players, ambient
conditions, and electrode states are the **highest-priority requirement** for
Experiment 9. With 5+ sessions, a calibrated adaptive criterion could potentially
be learned and cross-validated. Without multi-session data, any threshold we
choose is overfit to log0305 by construction.

**Recommended paper wording:**
> "An initial adaptive settling detector based on causal rolling MDF, MDF variance,
> and contact quality triggered at 8.8 min — 11 min earlier than the 20-min fixed
> skip — producing only 7.1% MDF drop vs. 28.1%. An exhaustive grid of 432 threshold
> combinations confirmed that no simple criterion approximates the 20-min endpoint on
> this session. Cross-session calibration with data from multiple players is required."

**Placement:** Future work / appendix. Not a validated Paper 1 algorithm.

**Grid output:** `paper_figures/table_exp9_adaptive_settling_grid.csv`


---

# Priority 3 — Tennis-Specific Impact / Artifact Experiments Using Existing Data

These test the future tennis-specific novelty using existing logs only.

---

## 10. PSD Around High-Jerk Events ⚑ Gateway for Batch C

**Goal:** Test whether high-jerk forearm events show EMG spectral artifacts.

> **Gateway role:** This is the minimum viable test before investing time in Experiments
> 11 and 12. If PSD shows no measurable difference between near-jerk and away-from-jerk
> windows, the impact-artifact hypothesis is weak and Batch C (11, 12) should be
> deprioritised in favour of other Batch B items. Run this before 11 and 12.

### Data

```text
log0305 raw IMU + raw EMG
```

### Method

For each swing:

```text
find peak acc jerk or acc_dyn event
extract EMG 50 ms around event
extract control EMG 50 ms away from event, preferably pre-event / pre-contact phase
compute PSD_event and PSD_control
```

### Metrics

```text
PSD_event / PSD_control
energy ratio in 50–150 Hz
energy ratio in 150–250 Hz
energy ratio in 250–450 Hz
MDF_event - MDF_control
```

### Possible outcomes

If event PSD has elevated high-frequency energy:

```text
impact/vibration artifact is plausible
```

If no difference:

```text
transmitted vibration may be weak
or event localization is wrong
```

### Output

```text
PSD ratio plot: event vs control
table of band ratios
```

### Paper value

Most important existing-data sanity check for the impact-artifact idea.

---

## 11. Pre-Impact MDF vs Full-Window MDF

**Goal:** Test whether phase-gated MDF is cleaner than full-window MDF.

### Data

```text
log0305
```

### Method

Using candidate event time from IMU:

```text
mdf_full = current MDF from full swing window
mdf_pre = MDF from t_event - 600 ms to t_event - 20 ms
```

Compare:

```text
variance
outlier rate
fatigue trend slope
correlation with IMU shock score
MDF drop %
```

### Expected result

If pre-impact phase avoids impact/follow-through artifacts:

```text
mdf_pre should have lower variance
fatigue trend should remain or become cleaner
```

### Output

```text
Figure 8: full-window MDF vs pre-impact MDF
table: variance, slope, drop %, outlier rate
```

### Risk

Candidate event timing may be wrong, so “pre-impact” may not truly be pre-impact without audio/video labels.

---

## 12. Forearm-Only Impact-Risk Score Prototype

**Goal:** Build an unsupervised soft artifact-risk score.

### Data

```text
log0305
```

### Candidate features

```text
imu_jerk_peak
acc_dyn_peak
emg_hf_energy_200_500
emg_transient_score
phase relative to gyro peak
MDF local outlier score
```

### Score

Example:

```text
impact_risk_score =
    z(imu_jerk_peak) * in_contact_phase
  + z(emg_hf_energy)
  + z(emg_transient_score)
  + z(MDF_outlier_score)
```

### Test

```text
Does high impact_risk correlate with MDF outliers?
Does removing top 10–20% high-risk swings reduce MDF variance?
Does fatigue trend remain after removing high-risk swings?
```

### Expected result

```text
high-risk rejection reduces variance without eliminating fatigue trend
```

### Paper value

Useful future algorithm, but without labels it should be framed as artifact-risk, not confirmed impact detection.

---

## 13. Empty / Contact Separability Limitation

**Goal:** Explicitly document what cannot be proven with existing logs.

### Limitation

Unless `log0303` or `log0305` already label each swing as empty swing vs ball-contact swing, existing data cannot support:

```text
empty swing vs ball-contact ROC/AUC
true ball-contact detector validation
```

### What can be done instead

Proxy analysis:

```text
high-jerk vs low-jerk swings
high-acc vs low-acc swings
MDF outliers vs non-outliers
```

### Paper value

Keeps claims honest and motivates future controlled protocol.

---

# Priority 4 — Secondary Analyses

Useful but less urgent.

---

## 14. RAW / ENV Consistency Diagnostic

**Goal:** Detect hardware/contact failure modes.

### Data

```text
log0303 and log0305 raw / ENV logs, if available
```

### Metrics

```text
raw_rms per swing
env_mean or env_peak per swing
corr(envelope(raw), ENV)
raw saturation count
raw flatline count
raw_env_ratio
```

### Questions

```text
Did RAW and ENV agree after solder fix?
Were there periods where ENV looked active but RAW was weak?
Did contact_quality correlate with ENV?
```

### Output

```text
RAW vs ENV scatter
RAW/ENV ratio over time
saturation/flatline counts
```

### Paper value

Supports hardware-engineering reliability discussion.

---

## ✅ 15. Swing Intensity Stratification

**Goal:** Ensure fatigue trend is not due to changing swing intensity distribution.

### Data

```text
log0305
```

### Method

Bin swings by IMU intensity:

```text
low intensity
medium intensity
high intensity
```

Or regress:

```text
MDF ~ time + imu_peak_mag
```

### Expected result

```text
time/fatigue trend remains after accounting for IMU intensity
```

### Output

```text
regression table
MDF trend adjusted for IMU intensity
```

### Paper value

Stronger control for reduced-effort confound.

---

## ✅ 16. Bout-Level Fatigue Analysis

**Goal:** Reduce per-swing noise by aggregating into bouts.

### Data

```text
log0305: 50 bouts
log0303: 18 bouts
```

### Method

For each bout:

```text
median MDF
median MNF
median RMS
median contact_quality
median imu_peak_mag
bout swing count
```

Then fit trends across bouts.

### Expected result

```text
bout-level log0305 fatigue trend is cleaner than per-swing trend
log0303 segment 1 remains weak / flat
```

### Output

```text
bout-level MDF and IMU trends
```

### Paper value

More stable figures and less noise.

---

## 17. Swing-Rate / Workload Accumulation Metric

**Goal:** Relate fatigue to accumulated workload instead of clock time.

### Data

```text
log0305
log0303 segment 1
```

### Metrics

```text
cumulative swings
cumulative gyro impulse
cumulative acc_dyn
bout density
```

### Test

```text
MDF vs clock time
MDF vs cumulative swing count
MDF vs cumulative IMU load
```

### Expected result

```text
log0305 dense session shows meaningful fatigue
log0303 sparse segment shows little fatigue
```

### Paper value

Tennis fatigue depends on workload, not just elapsed time.

---

## 18. BLE Gap / Session Stitching Quality Audit

**Goal:** Validate the hybrid `abs_us` timeline reconstruction.

### Data

```text
log0303
log0305
```

### Check

```text
host_rx_ms gaps
dev_us resets
file boundaries
timestamp monotonicity
swing distribution around gaps
```

### Expected result

```text
log0303: major 66-min gap preserved
log0305: continuous connection with no major gap
```

### Output

```text
gap audit table
timeline diagnostic plot
```

### Paper value

Supports field-deployment reliability and explains `log0303` artifact.

---

# Recommended Execution Batches

## Batch A — Paper 1 figures

Do first.

```text
✅ 1.  Warmup-skip sensitivity figure
✅ 2.  Electrode settling MDF/RMS curve
✅ 3.  IMU consistency plot
✅ 4.  Contact quality metric plot
✅ 5.  log0303 gap artifact plot
✅ 5b. IMU-EMG diagnostic matrix (Figure 7)
```

Expected deliverable:

```text
paper_analysis.py generates Figures 2–7
```

---

## Batch B — Strengthen Paper 1 analysis + gateway test

Do second.

```text
✅ 10. PSD around high-dynamic events (gateway) — NULL RESULT
    acc_dyn peaks at swing apex (median offset = -4.7 ms from gyro peak),
    not at ball contact. Near-peak delta_log_hf_lf = -0.27 (negative, not positive).
    Spearman rho = -0.37 (harder swings → more negative delta).
    CONCLUSION: acc_dyn does not locate ball contact. Batch C deprioritized.
    Trigger localization is the bottleneck → motivates E8 Level 1 racket tap test.
✅ 6.  Rest/noise-floor tracker
✅ 7.  Robust MDF outlier filtering
✅ 8.  Early/mid/late PSD comparison
✅ 9.  Adaptive settling endpoint
✅ 15. Swing intensity stratification
✅ 16. Bout-level fatigue analysis
```

Expected deliverable:

```text
PSD ratio plot (Experiment 10) gates Batch C decision
additional tables / optional appendix plots for Paper 1
```

---

## Batch C — Tennis-specific future algorithms

⛔ DEPRIORITIZED based on Experiment 10 null result.

The acc_dyn peak does not reliably locate ball contact (it finds the swing apex at
median offset -4.7 ms from gyro peak). Without a valid impact trigger, pre-impact phase
MDF and impact-risk scoring algorithms are not grounded in the current data.

Required before revisiting:
  - Level 1: racket tap test (E8) to confirm mechanical transmission exists
  - Level 3/4: video or audio labels to locate actual ball contact timing

```text
⛔ 11. Pre-impact MDF vs full-window MDF   — needs valid impact trigger first
⛔ 12. Forearm-only impact-risk score      — needs valid impact trigger first
```

---

## Batch D — System robustness

Do fourth.

```text
13. RAW/ENV consistency diagnostic
17. Workload accumulation metric
18. BLE gap/session stitching audit
```

Expected deliverable:

```text
system reliability evidence and workload interpretation
```

---

# Implementation Notes

## Input File Reference

All paths relative to `/local/mnt/workspace/wangx/projects/emg_util/`.

### Pre-computed swing feature files (Experiments 1–9, 11–12, 14–17)

```text
out0305/swing_features.csv          # 10-min skip, no RMS filter
out0305_v2/swing_features.csv       # 10-min skip + RMS baseline filter
out0305_w15/swing_features.csv      # 15-min skip
out0305_w20/swing_features.csv      # 20-min skip  ← canonical fatigue result
out0303_v2/swing_features.csv       # full session (2 BLE connections, gap-confounded)
out0303_seg1/swing_features.csv     # first segment only (13.5 min, no gap)
```

### Fatigue summary files (Experiment 1)

```text
out0305/fatigue_summary.csv
out0305_v2/fatigue_summary.csv
out0305_w15/fatigue_summary.csv
out0305_w20/fatigue_summary.csv
out0303_v2/fatigue_summary.csv
out0303_seg1/fatigue_summary.csv
```

### Raw EMG + IMU logs (Experiments 8, 10, 11, 14, 18)

```text
log0305/emg_log_20260305_192734_*.csv   # 5 rotation files, 63 min
log0305/imu_log_20260305_192734_*.csv   # 5 rotation files, 63 min
log0303/emg_log_20260303_*.csv          # 2 BLE connections, 4 rotation files
log0303/imu_log_20260303_*.csv          # 2 BLE connections, 5 rotation files
```

### Session-level summary files

```text
out0305_w20/session_summary.json
out0303_v2/session_summary.json
out0303_seg1/session_summary.json
```

---

## Preferred output files

Use a dedicated output directory, for example:

```text
paper_analysis_outputs/
  figures/
  tables/
  diagnostics/
```

## Suggested generated files

```text
fig_electrode_settling_log0305.png
fig_imu_consistency_log0305.png
fig_warmup_skip_sensitivity.png
fig_contact_quality.png
fig_log0303_gap_artifact.png
fig_psd_early_mid_late.png
fig_high_jerk_psd_ratio.png
fig_full_vs_preimpact_mdf.png
table_warmup_skip_sensitivity.csv
table_bout_level_summary.csv
table_gap_audit.csv
```

## Suggested analysis order in code

```text
1. Load canonical swing feature files.
2. Load fatigue summaries.
3. Generate Paper 1 core figures.
4. Add optional diagnostics.
5. Add future-algorithm prototypes.
```

---

# Current Recommendation

For the current Paper 1, prioritize:

```text
Batch A: 1, 2, 3, 4, 5, 5b
Batch B: 6, 7, 8, 9, 14, 15  (preceded by Experiment 10 as gateway)
```

For Paper 2 / future tennis-specific novelty, proceed to Batch C only if Experiment 10
shows measurable PSD elevation near high-jerk events:

```text
Batch C: 11, 12
```

The single most important new existing-data experiment beyond the current Paper 1 figures is:

```text
Experiment 10: PSD around high-jerk events vs pre-event control windows
```

because it directly tests whether impact/vibration artifact is visible in the existing EMG
logs before investing more time in impact-gating algorithms. It is the gateway to Batch C.
