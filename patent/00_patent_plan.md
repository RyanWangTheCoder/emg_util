# Patent Action Plan — RAW/ENV/IMU Signal-Quality Validation

> **Current file set (as of 2026-06-01):** All working files are in `patent/` and use numbered prefixes: `01_invention_disclosure.md`, `02_public_disclosure_timeline.md`, `03_inventor_contribution_matrix.md`, `04_prior_art_search_notes.md`, `05_provisional_draft.md` / `.pdf`, `06_figures/`, `07_filing_receipt.md`. Earlier filename references elsewhere in this document (e.g., `patent_provisional_draft.md`, `inventor_contribution_table.md`) are historical planning examples and do not reflect the current folder.

This is an inventor action plan for preparing a focused provisional patent application around wearable EMG signal-quality validation. It is not legal advice. Because this work may involve a minor participant, university collaborators, prior/public disclosures, and employer IP policies, review the filing strategy with a registered patent attorney or the relevant invention-disclosure process before filing.

---

## 1. Executive Recommendation

Do **not** file a broad provisional titled only around "EMG/IMU fatigue monitoring." The stronger invention scope is:

> **Reliability-gated wearable EMG monitoring using simultaneous RAW EMG, hardware envelope, and IMU context to validate, delay, down-weight, correct, segment, suppress, or annotate downstream fatigue/activation metrics.**

This framing is supported by the project documentation and drafts:

- `icpics_draft.md` / `icpics_draft.pdf`: dual RAW/ENV hardware, synchronized 2 kHz EMG + 200 Hz IMU platform, BLE timing/reconnect handling, and pogo-pin ghost-signal diagnostic.
- `paper_cnib.md` / `paper_cnib.pdf`: trustworthiness-first fatigue interpretation, electrode settling, contact-quality metrics, IMU-conditioned interpretation, and session-gap artifact detection.
- `patent_provisional_draft.md`: current merged provisional draft containing the primary specification text.

The patentable center of gravity is the **trustworthiness gate**:

```text
RAW EMG          → physiology candidate
hardware ENV     → hardware/contact/saturation consistency
IMU              → movement/artifact/context
session timeline → continuity validity
quality gate     → confidence/action for fatigue or activation interpretation
```

---

## 2. Resolve Ownership, Inventorship, and Disclosure Constraints First

Before filing, clarify who owns the invention and who must be notified.

Because this project touches sensing, wearable signal processing, BLE, IMU, and fatigue monitoring, check whether the invention is personal, university/student work, employer-reportable, jointly owned, or subject to collaborator agreements.

### Action Items

1. Create an inventor/contributor table:
   - Who conceived each claimed idea?
   - Who implemented each idea?
   - Who validated, advised, tested, or wrote?
2. Separate:
   - **Inventors**: people who contributed to conception of claimed inventive concepts.
   - **Authors / testers / advisors**: contributors who may not be legal inventors.
3. Check:
   - employer invention policy;
   - university/professor involvement terms;
   - student/minor participation considerations;
   - public science fair, paper, poster, conference, code, or dataset disclosures.

**Important:** Inventorship is a legal determination. Make the evidence table and let counsel decide.

---

## 3. Freeze the Public-Disclosure Timeline

This is urgent because patents are first-to-file and public disclosures can affect rights.

Known possible disclosure events include:

- R. Wang, "Low-cost wearable kit and algorithms to predict and prevent muscle overuse injuries," AAAS Pacific Division, June 17–20, 2024.
- ICPICS draft/submission.
- CNIB draft/submission.
- GitHub, code, markdown, PDF, poster, slide, science fair, or shared-drive distribution.

Create:

```text
patent_public_disclosure_timeline.md
```

Suggested table:

| Date | Disclosure | Audience | Public? | What technical details were disclosed? | Related to RAW/ENV/IMU validity gating? |
|---|---|---|---|---|---|
| 2024-06-17 to 2024-06-20 | AAAS Pacific Division poster | Conference | TBD | Low-cost wearable kit and algorithms to predict/prevent overuse injuries | TBD |
| TBD | ICPICS draft / submission | TBD | TBD | BLE platform, RAW/ENV, pogo-pin ghost signal | TBD |
| TBD | CNIB draft / submission | TBD | TBD | EMG validity, settling, IMU-conditioned interpretation | TBD |
| TBD | GitHub / code / markdown | TBD | TBD | TBD | TBD |

For each disclosure, answer:

> Did it disclose the specific combination of RAW/ENV consistency + IMU context + validity gating?

If not, the newer invention may still be separable. If yes, counsel needs exact dates.

---

## 4. Invention Scope and Claim Families

Do not treat everything as one undifferentiated idea. Organize the invention into claim families, with Family A as the main provisional focus and Families B–D as dependent embodiments.

### Family A — Main Focus: RAW/ENV/IMU Signal-Quality Validation

**Core invention:** A system computes RAW-derived envelope/amplitude features, compares them with hardware ENV and IMU context, and gates downstream EMG interpretation.

Supported by:

- MyoWare 2.0 has both RAW and ENV outputs.
- RAW is needed for spectral analysis.
- ENV provides a paired hardware signal from the same EMG sensor path.
- IMU is used as an independent biomechanical context channel rather than as a generic fused feature.
- Field EMG monitoring requires settling-aware baselines, contact-quality monitoring, IMU-conditioned interpretation, and continuity auditing.

### Family B — Baseline Selection and Fatigue Gating

**Core invention:** A baseline selector accepts only windows satisfying EMG quality, RAW/ENV consistency, IMU stability, and continuity conditions.

Supported by:

- Warmup-skip sensitivity changed fatigue interpretation dramatically.
- Baseline selection is a first-order determinant of fatigue interpretation.
- Low-RMS/noise-dominated baseline windows can invert fatigue metrics.

### Family C — Session Continuity / BLE Gap Validity Audit

**Core invention:** EMG fatigue interpretation is segmented, suppressed, or annotated across wireless discontinuities.

Supported by:

- `log0303` contained a 66-minute BLE reconnection gap.
- Full-session apparent MDF drop was 28.7%, while first continuous segment alone was 4.9%.
- Hybrid `abs_us` reconstruction preserves reconnect/device-reset discontinuities.

### Family D — Pogo-Pin / Ghost-Channel Diagnostic

**Core invention:** Detect ghost-channel analog coupling or floating ADC input in multiplexed wearable biosignal acquisition.

Supported by:

- RAW routed through pogo pins failed under movement.
- Diagnostic signature:
  - high RAW–ENV correlation;
  - near-zero RAW variance;
  - post-filter RAW flatline;
  - fixed by solder bypass.

**Recommendation:** Put all four families into one provisional if cost and effort allow, but make **Family A** the title and main independent concept. Families B–D become embodiments, dependent claim concepts, and examples.

---

## 5. One-Page Invention Disclosure

Before refining the provisional, create a crisp one-page disclosure for attorney or internal IP review.

Suggested file:

```text
patent/01_invention_disclosure_raw_env_imu_quality.md
```

Suggested content:

```markdown
# Invention Disclosure: Reliability-Gated Wearable EMG Monitoring Using RAW/ENV/IMU Consistency

## 1. Short Title
Systems and Methods for Signal-Quality Validation of Wearable Electromyography Using Simultaneous Raw EMG, Hardware Envelope, and Inertial Context

## 2. Problem
Wearable EMG fatigue metrics in field sports can be corrupted by electrode settling, contact degradation, hardware envelope saturation, raw-channel failure, motion artifact, reduced movement effort, and wireless discontinuities.

## 3. Key Insight
Instead of treating EMG features as automatically valid, the system first determines whether EMG-derived fatigue or activation metrics are trustworthy by comparing simultaneously acquired RAW EMG, hardware ENV, and IMU/session context.

## 4. Technical Solution
The system:
1. receives high-rate RAW EMG;
2. receives low-rate or paired hardware ENV from the same sensor;
3. receives IMU data;
4. computes RAW-derived RMS/envelope/spectral features;
5. compares RAW-derived amplitude/envelope features against hardware ENV;
6. detects saturation, flatline, contact settling, ghost-channel coupling, motion artifact, and session-gap confounds;
7. gates downstream fatigue/activation metrics by accepting, rejecting, delaying, down-weighting, correcting, segmenting, suppressing, or annotating them.

## 5. Evidence / Embodiments
- RAW/ENV paired MyoWare acquisition.
- RAW-derived spectral MDF/MNF.
- IMU-conditioned validity matrix.
- Warmup-skip sensitivity.
- Contact-quality metric.
- BLE gap artifact.
- Pogo-pin ghost signal diagnostic.

## 6. Commercial / Practical Value
Improves reliability of low-cost field EMG monitoring in sports, rehabilitation, occupational monitoring, gesture interfaces, prosthetics, and human-performance tracking.
```

---

## 6. Provisional Draft Structure

The current main draft is:

```text
/local/mnt/workspace/wangx/projects/emg_util/patent_provisional_draft.md
```

Recommended final structure:

```markdown
# Systems and Methods for Signal-Quality Validation of Wearable Electromyography Using Simultaneous Raw EMG, Hardware Envelope, and Inertial Context

## 1. Field
## 2. Background
## 3. Summary
## 4. System Architecture
## 5. Data Streams
## 6. RAW-Derived Envelope and Feature Computation
## 7. Signal-Quality Metrics
## 8. Failure-Mode Classification
## 9. IMU-Conditioned Validity Logic
## 10. Baseline Selection and Fatigue Gating
## 11. Quality-Gated Fatigue or Activation Monitoring
## 12. Session Continuity Logic
## 13. Exemplary Embodiments
## 14. Output and Actions
## 15. Advantages
## 16. Variations and Applications
## 17. Claim Concepts
## 18. Candidate Dependent Claim Features
## 19. Figures
## 20. Experimental Support
## 21. Prior-Art Risk Areas
## 22. Disclosure / Filing Notes
## 23. Next Drafting Tasks
## 24. Attorney Summary
## 25. Conclusion
```

The provisional does not need formal claims, oath/declaration, or information disclosure statement, but it must describe the invention with enough technical detail to support later claims. Include algorithms, thresholds, variations, figures, and examples.

---

## 7. Invention Figures to Add

Adding figures is the highest-ROI next step. They can initially be simple ASCII, Markdown tables, PowerPoint diagrams, or annotated plots.

### Figure 1 — System Architecture

```text
EMG Sensor
  ├── RAW output ─────┐
  └── ENV output ─────┤
                      ├── Processor / MCU ── Wireless/Wired Link ── Host or Mobile Device
IMU Sensor ───────────┘

Host / Mobile Processing:
  RAW preprocessing
  RAW-derived envelope
  RAW/ENV consistency check
  IMU context analysis
  Signal-quality classifier
  Fatigue / activation gating
  Confidence-aware output
```

Purpose: shows that the invention includes both hardware acquisition and software decision logic.

### Figure 2 — Overall Method Flow

```text
Acquire RAW EMG, hardware ENV, and IMU
        ↓
Preprocess RAW EMG
        ↓
Compute RAW-derived RMS, envelope, MDF, MNF
        ↓
Compare RAW-derived envelope with hardware ENV
        ↓
Compute IMU movement context
        ↓
Compute session continuity state
        ↓
Classify signal validity
        ↓
Accept / reject / delay / down-weight / segment / annotate EMG interpretation
```

Purpose: defines the core method and makes the trustworthiness gate explicit.

### Figure 3 — RAW/ENV Consistency Validation

| Case | RAW Behavior | ENV Behavior | RAW/ENV Correlation | Interpretation | Action |
|---|---|---|---|---|---|
| Normal | Oscillating | Smooth envelope | Moderate | Valid EMG | Accept |
| Settling | Low amplitude, recovering | Smooth | Moderate | Electrode settling | Delay baseline |
| Saturation | Clipped or high amplitude | Clipped | High | Hardware saturation | Flag/reduce trust |
| Flatline | Near-zero variance | Normal or changing | Very high or abnormal | Raw channel failure / ghost signal | Reject |
| Contact loss | Low amplitude | Low amplitude | Variable | Low SNR / poor contact | Reduce confidence |

Purpose: supports RAW/ENV comparison novelty.

### Figure 4 — IMU-Conditioned EMG Validity Matrix

| IMU / Session Context | EMG Observation | Interpretation | Action |
|---|---|---|---|
| Stable movement intensity | Early low MDF later recovers | Electrode settling | Delay baseline |
| Stable movement intensity | Gradual MDF/MNF decline | Fatigue-consistent change | Allow fatigue analysis |
| Declining movement intensity | MDF/MNF decline | Reduced-effort confound | Reduce confidence |
| Large shock or vibration | Isolated EMG outlier | Motion artifact likely | Down-weight or reject |
| Session discontinuity | Baseline shift across segments | Cross-segment artifact | Analyze separately |

Purpose: distinguishes this invention from generic EMG/IMU feature fusion.

### Figure 5 — Quality-Gated Baseline Selection

```text
Candidate baseline windows
        ↓
Quality checks:
  RAW variance sufficient?
  ENV saturation below threshold?
  RAW/ENV consistency acceptable?
  Contact-quality metric acceptable?
  IMU context stable?
  No session gap?
        ↓
Accepted baseline pool
        ↓
Robust baseline MDF/RMS estimation
        ↓
Fatigue metrics computed relative to trusted baseline
```

Purpose: supports baseline-gating embodiment.

### Figure 6 — Session Continuity Audit

```text
Full Session with BLE gap:
  Apparent MDF drop: 28.7%
  Interpretation: fatigue? (unsafe)

Segment 1 only:
  MDF drop: 4.9%
  Interpretation: no meaningful within-segment fatigue

Action:
  Analyze segments separately
  Suppress cross-segment fatigue metric
```

Purpose: supports wireless/session discontinuity logic.

### Figure 7 — Ghost Signal / Hardware Failure Diagnostic

```text
Failure signature:
  • RAW and ENV highly correlated
  • RAW variance abnormally low
  • RAW flatlines after bandpass filtering
  • RAW lacks independent AC muscle content

Classification:
  Ghost-channel coupling or raw-channel failure

Action:
  Reject RAW-derived spectral metrics
  Flag hardware/contact failure
  Prompt repair or sensor adjustment
```

Purpose: supports concrete hardware-failure diagnostic embodiment.

---

## 8. Metrics Table for the Provisional

| Metric | Source | Purpose | Possible Gate/Action |
|---|---|---|---|
| RAW RMS | RAW EMG | amplitude/contact/activation context | reject low-SNR baseline |
| RAW software envelope | RAW EMG | compare with hardware ENV | detect mismatch or failure |
| Hardware ENV mean/max | ENV | envelope/contact/saturation context | flag ENV saturation |
| RAW/ENV correlation | RAW + ENV | detect coupling or consistency | detect ghost channel or mismatch |
| RAW variance | RAW | detect flatline / floating input | reject window/session |
| ENV saturation count/% | ENV | detect clipping | reduce ENV trust |
| Contact quality = RMS/session_p90_rms | RAW-derived RMS | qualitative contact indicator | delay baseline or annotate confidence |
| IMU peak gyro magnitude | IMU | swing intensity context | distinguish fatigue vs effort |
| IMU shock/jerk | IMU | motion artifact context | down-weight outlier |
| Session continuity / `abs_us` gap | host/device timing | gap artifact detection | segment analysis |

Notes:

- `contact_quality(t) = RMS(t) / session_p90_rms` is a qualitative relative indicator, not direct impedance validation.
- Hybrid `abs_us` timeline and reconnect handling support continuity-aware analysis.

---

## 9. Claim Concepts

Formal claims are not required for a provisional, but include claim concepts to preserve scope.

### Independent Method Concept

```text
A method comprising:
receiving raw electromyography samples from a wearable electromyography sensor;
receiving hardware envelope samples acquired from the wearable electromyography sensor;
receiving inertial measurement samples from a wearable inertial sensor;
computing a raw-derived amplitude or envelope feature from the raw electromyography samples;
generating one or more signal-quality metrics by comparing the raw-derived amplitude or envelope feature with the hardware envelope samples;
determining an inertial context from the inertial measurement samples;
classifying a trustworthiness state of one or more electromyography windows based on the signal-quality metrics and the inertial context; and
modifying downstream interpretation of electromyography-derived activation or fatigue metrics based on the trustworthiness state.
```

### Independent System Concept

```text
A wearable sensing system comprising:
an electromyography sensor configured to output raw electromyography data and hardware envelope data;
an inertial measurement unit configured to output motion data; and
one or more processors configured to derive raw-based features, compare the raw-based features with the hardware envelope data, determine motion context from the motion data, classify signal trustworthiness, and gate downstream electromyography-derived metrics based on the classification.
```

### Computer-Readable Medium Concept

```text
A non-transitory computer-readable medium storing instructions that, when executed by one or more processors, cause the processors to receive RAW EMG, hardware ENV, and IMU data; compute signal-quality metrics; determine motion context; classify EMG trustworthiness; and modify downstream EMG interpretation.
```

### Dependent Concept Examples

```text
The method of claim 1, wherein modifying downstream interpretation comprises accepting, rejecting, delaying, down-weighting, correcting, segmenting, suppressing, or annotating an EMG-derived fatigue metric.

The method of claim 1, wherein the signal-quality metrics comprise at least one of RAW variance, RAW/ENV correlation, ENV saturation percentage, RAW-derived RMS, RAW-derived software envelope, hardware ENV maximum, or RAW/ENV ratio.

The method of claim 1, wherein the inertial context identifies stable movement intensity, declining movement intensity, transient shock, vibration, or motion discontinuity.

The method of claim 1, wherein a baseline window is accepted only if the signal-quality metrics and inertial context satisfy one or more quality conditions.

The method of claim 1, wherein a ghost-channel failure is detected based on high correlation between RAW and ENV, near-zero RAW variance, and a flatline after bandpass filtering.
```

---

## 10. Experimental Examples to Include

Use data as **examples**, not limitations.

### Example 1 — Continuous Tennis Session

Suggested wording:

> In one embodiment, a tennis forearm EMG–IMU system was used. In a continuous 63.1-minute session with 626 detected swings, the system observed a three-phase MDF trajectory: early low MDF attributed to electrode settling, mid-session settled reference, and later fatigue-consistent decline while IMU swing intensity remained stable.

Support:

- `log0305`: 63.1 min, 626 swings.
- Stable IMU swing-intensity proxy: r = +0.029, p = 0.468.
- Low ENV saturation: 1.4%.
- Zero RAW flatlines.

### Example 2 — Session Gap Artifact

Suggested wording:

> In another embodiment, session continuity auditing prevented a false fatigue conclusion where a 66-minute BLE reconnection gap produced an apparent full-session MDF drop of 28.7%, while the first continuous segment alone showed 4.9% change.

Support:

- `log0303`: two BLE segments separated by a large gap.
- Full-session drop = 28.7%.
- Segment-only drop = 4.9%.

### Example 3 — Pogo-Pin / Ghost Signal Diagnostic

Suggested wording:

> In another embodiment, a RAW-channel routing failure was detected using a high RAW–ENV correlation, near-zero RAW variance, and post-filter RAW flatline, and was repaired using a solder bypass.

Support:

- Pearson r = 0.998 vs ENV before repair.
- Near-zero variance.
- Post-filter flatline.
- Post-bypass filtered ENV–RAW correlation dropped to r = -0.013.

### Wording Caution

Avoid saying:

> This proves fatigue.

Prefer:

> fatigue-consistent

or:

> candidate local fatigue

because the current field sessions lack direct MVC, RPE, grip-force, or ball-speed ground truth.

---

## 11. Focused Prior-Art Search Plan

A perfect patentability search is not required before filing a provisional, but a focused search helps position the invention.

Search categories:

1. **EMG signal quality analysis**
   - sEMG signal quality index
   - electrode contact quality EMG
   - dry electrode impedance EMG
   - EMG artifact detection

2. **EMG envelope + raw signal**
   - hardware envelope raw EMG comparison
   - MyoWare raw envelope validation
   - dual-output EMG signal quality

3. **IMU-conditioned EMG validity**
   - IMU motion artifact EMG detection
   - EMG IMU artifact suppression
   - wearable EMG IMU fatigue validation

4. **Baseline selection / warmup gating**
   - EMG fatigue baseline selection
   - median frequency baseline warmup
   - dry electrode settling EMG fatigue

5. **Wireless continuity / session gap**
   - wearable biosignal BLE discontinuity artifact
   - EMG fatigue session gap detection

6. **ADC ghost channel / multiplexed ADC crosstalk**
   - multiplexed ADC charge sharing biosignal
   - floating ADC input channel coupling
   - EMG raw envelope crosstalk diagnostic

Important prior-art starting points from project drafts include:

- sEMG signal quality analysis reviews;
- EMG artifact/noise/interference reviews;
- low-cost wearable EMG systems;
- commercial EMG/IMU systems;
- dry electrode impedance/contact studies;
- EMG+IMU fatigue classification systems.

---

## 12. Filing Strategy

### DIY Provisional May Be Acceptable If

- A quick priority date is needed.
- The invention is still evolving.
- Counsel will later prepare the nonprovisional.
- The provisional includes enough technical detail, variations, figures, algorithms, thresholds, and examples.

### Attorney-Prepared Is Better If

- Employer or university ownership may apply.
- The invention may become commercially important.
- Publication is planned soon.
- Stronger claim support is needed.
- There are multiple inventors, including a minor.
- International filing options matter.

A U.S. provisional generally requires:

1. written description / specification;
2. cover sheet;
3. fee.

A provisional does not require formal claims, oath/declaration, or an information disclosure statement, but it lasts 12 months and must be followed by a corresponding nonprovisional within that period to benefit from the provisional filing date.

---

## 13. Filing Package Checklist

Prepare:

```text
1. Specification PDF
   patent_provisional_draft.pdf

2. Drawings PDF
   patent_figures.pdf
   or figures embedded in the specification

3. Provisional cover sheet
   PTO/SB/16

4. Fee payment
   large/small/micro entity as applicable

5. Internal records
   inventor_contribution_table.md
   patent_public_disclosure_timeline.md
   prior_art_notes.md
   patent_followup_plan.md
```

Checklist:

- [ ] Confirm invention title.
- [ ] Confirm inventor list and contributions.
- [ ] Confirm ownership / assignment obligations.
- [ ] Confirm public disclosure timeline.
- [ ] Confirm all figures are included and referenced.
- [ ] Confirm all key embodiments are described.
- [ ] Confirm broad variations are included.
- [ ] Confirm claim concepts are clear and broad enough.
- [ ] Convert specification and figures to PDF.
- [ ] Prepare provisional cover sheet.
- [ ] Confirm entity status and fee.
- [ ] File through attorney or USPTO Patent Center.
- [ ] Save filing receipt and application number.
- [ ] Record 12-month nonprovisional deadline.

---

## 14. Post-Filing Plan

After filing, create:

```text
patent_followup_plan.md
```

Suggested content:

```markdown
# Patent Follow-Up Plan

## Filing date
TBD

## 12-month nonprovisional deadline
TBD

## Before publication / conference submission
- Confirm provisional filed.
- Confirm inventor list.
- Confirm ownership/assignment.
- Confirm no new material omitted.

## During the 12-month period
- Add more sessions / subjects if available.
- Implement real-time quality gate.
- Add live warning UI.
- Validate RAW/ENV thresholds.
- Add impedance if available.
- Prepare nonprovisional claims.
```

Do not rely on any restoration grace period as a plan.

---

## 15. Technical Implementation to Strengthen the Patent

From a patent-strength perspective, the best next engineering step is turning the validity concept into a concrete algorithm.

Implement:

```text
quality_gate.py
```

Inputs:

```text
RAW EMG
hardware ENV
IMU
session timeline / abs_us
BLE segment IDs
```

Outputs:

```text
quality_state
confidence_score
failure_flags
recommended_action
```

Example states:

```python
VALID = "valid_emg"
SETTLING = "electrode_settling"
LOW_SNR = "contact_loss_or_low_snr"
ENV_SAT = "hardware_env_saturation"
RAW_FLATLINE = "raw_channel_flatline"
GHOST = "ghost_channel_coupling"
MOTION_ARTIFACT = "motion_artifact_likely"
REDUCED_MOTION_CONFOUND = "reduced_motion_confound"
SESSION_GAP = "session_gap_confound"
```

Example actions:

```python
ACCEPT
REJECT
DELAY_BASELINE
DOWN_WEIGHT
SEGMENT_SEPARATELY
SUPPRESS_FATIGUE_OUTPUT
SHOW_CONFIDENCE_WARNING
PROMPT_ELECTRODE_ADJUSTMENT
```

This strengthens the provisional because it shows the invention is not merely an observation; it is an implementable system and method.

---

## 16. Patent-Friendly Wording

### Prefer

- trustworthiness;
- validity gating;
- confidence score;
- modifying downstream interpretation;
- accepting, rejecting, delaying, down-weighting, correcting, segmenting, suppressing, or annotating;
- IMU as independent context;
- RAW/ENV consistency;
- hardware envelope as quality/context signal;
- session continuity audit;
- fatigue-consistent.

### Avoid Over-Narrowing

Avoid limiting the invention to only:

- tennis;
- MyoWare;
- ESP32;
- 2 kHz;
- 200 Hz;
- 20-minute threshold;
- BLE only;
- forearm only;
- MDF only.

Use language like:

> In some embodiments...

Then include alternatives:

- other muscles;
- other sports;
- rehabilitation;
- workplace ergonomics;
- wired or wireless;
- different sample rates;
- different envelope rates;
- phone, watch, microcontroller, host computer, cloud;
- multiple EMG channels;
- optional impedance sensor;
- ECG/EEG/other biosignal variants if appropriate.

---

## 17. Suggested Project File Set

Recommended organization:

```text
/local/mnt/workspace/wangx/projects/emg_util/patent/
  01_invention_disclosure_raw_env_imu_quality.md
  02_public_disclosure_timeline.md
  03_inventor_contribution_matrix.md
  04_prior_art_search_notes.md
  05_provisional_draft_raw_env_imu_quality.md
  06_figures/
      fig1_system_architecture.md
      fig2_method_flow.md
      fig3_raw_env_consistency.md
      fig4_imu_decision_matrix.md
      fig5_baseline_gating.md
      fig6_session_gap_audit.md
      fig7_ghost_signal_diagnostic.md
  07_claim_concepts.md
  08_attorney_review_questions.md
```

Current working files already present in project root include:

```text
patent_plan.md
patent_provisional_draft.md
patent_raw_env_imu_signal_quality_deprecated.md
```

---

## 18. Concrete Step-by-Step Plan

### Phase 1 — Clean Invention Scope

1. Finalize one-page invention disclosure.
2. Create inventor contribution matrix.
3. Create public disclosure timeline.
4. Decide whether this is personal, university, joint, or employer-reportable.
5. Freeze current code/data/docs as evidence.

### Phase 2 — Strengthen Provisional

6. Add Figures 1–7.
7. Add example embodiments:
   - RAW/ENV paired acquisition;
   - IMU-conditioned validity;
   - baseline gating;
   - session continuity;
   - ghost-channel diagnostic.
8. Add variation section.
9. Add claim concepts and dependent claim support.
10. Add prior-art differentiation wording.

### Phase 3 — Review Before Filing

11. Review for overclaiming:
    - say "fatigue-consistent," not "proved fatigue," unless ground truth supports it.
12. Review for under-disclosure:
    - include algorithms, thresholds, alternatives, pseudocode, failure states.
13. Review ownership/inventorship with counsel/company/university as needed.
14. Run focused prior-art search.
15. Update the provisional with differentiators.

### Phase 4 — File

16. Convert to PDF.
17. Prepare USPTO provisional cover sheet.
18. Confirm entity status and fee.
19. File via USPTO Patent Center or through counsel.
20. Save receipt, application number, filing date, and exact submitted PDF.

### Phase 5 — After Filing

21. Mark materials "patent pending" only after filing.
22. Track 12-month nonprovisional deadline.
23. Continue experiments and real-time implementation.
24. Before any paper/poster/code release, check whether new matter should be added in a second provisional.
25. Prepare nonprovisional claims well before the 12-month deadline.

---

## 19. Immediate Next Action

*(Completed 2026-06-01 — see Section 20 for current TODO.)*

---

## 20. TODO — Final Filing Checklist

*Last updated: 2026-06-01*

### Critical Path (complete before filing)

- [ ] **Fill in paper publication dates** — when ICPICS and CNIB acceptance notices arrive, update the two TBD dates in `02_public_disclosure_timeline.md`. These dates set the hard filing deadline.
- [x] **Confirm OSU IP policy** — resolved: Dr. YanMing Di's advisory-only role does not trigger OSU ownership; no inventive conception, no OSU resources used.
- [x] **Confirm Westview High School IP policy** — resolved: extracurricular personal research on Ryan's own equipment; high schools do not claim student personal project IP.
- [ ] **Attorney review** — provide counsel with `01_invention_disclosure.md`, `05_provisional_draft.pdf`, and `03_inventor_contribution_matrix.md` for inventorship determination and claim review before filing.

### At Filing Time

- [ ] **Guardian signature** — Confirm with USPTO Patent Center instructions who must sign the provisional cover sheet submission for a minor inventor; arrange accordingly at filing time.
- [ ] **File via USPTO Patent Center** — upload `05_provisional_draft.pdf`, cover sheet (PTO/SB/16), pay filing fee (~$320 micro entity / ~$800 small entity).
- [ ] **Save filing receipt** — record application number, filing date, and exact submitted PDF filename.
- [ ] **Record 12-month nonprovisional deadline** — calendar the date 12 months from filing; nonprovisional must be filed by then to claim provisional priority.

### After Filing (within 12 months)

- [ ] **Formal prior art search** — complete the 5 unsearched categories in `04_prior_art_search_notes.md §3`.
- [ ] **Implement `quality_gate.py`** — working implementation strengthens the nonprovisional's enablement argument.
- [ ] **Mark materials "patent pending"** — only after filing confirmation is received.
- [ ] **Prepare nonprovisional claims** — engage counsel well before the 12-month deadline.

This visual story is the strongest foundation for claim scope, enablement, and examiner/attorney understanding.