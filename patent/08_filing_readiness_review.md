# Filing Readiness Review — Provisional Patent Application

> Review date: 2026-06-12  
> Application draft reviewed: `05_provisional_draft.md` / `05_provisional_draft.pdf`  
> Scope: technical, drafting, consistency, enablement, and filing-package review.  
> Not legal advice. A registered patent attorney should review inventorship, claim strategy, ownership, foreign filing, and filing formalities.

---

## 1. Executive Assessment

The provisional package is technically strong and appears close to filing-ready from a drafting-support perspective. The strongest inventive framing is consistent across the folder:

> Reliability-gated wearable EMG monitoring using RAW/ENV consistency, IMU-based validity context, and session-continuity logic to classify signal trustworthiness and gate downstream fatigue or activation interpretation.

The current draft provides good written-description support for later claims because it includes:

- system architecture;
- data streams;
- RAW-derived envelope and feature computation;
- signal-quality metrics;
- failure-mode classifications;
- IMU-conditioned validity logic;
- baseline selection and fatigue gating;
- session continuity management;
- action outputs;
- representative embodiments;
- claim-style concepts;
- figure references;
- experimental examples;
- prior-art positioning.

The main remaining risks are not that the technical story is weak, but that some supporting documents are stale or not synchronized with the current filing state. These should be cleaned before filing or immediately after filing.

---

## 2. Files Reviewed

| File | Status | Notes |
|---|---|---|
| `00_patent_plan.md` | Useful, but partly stale | Contains a comprehensive strategy and final checklist. Some checklist items may need reconciliation with current filing status. |
| `01_invention_disclosure.md` | Good attorney-facing summary | Clear one-page style disclosure. Good for counsel or internal records. |
| `02_public_disclosure_timeline.md` | Important; needs exact dates | Correctly identifies CNIB as high-overlap and ICPICS as partial-overlap. Publication dates remain TBD. |
| `03_inventor_contribution_matrix.md` | Useful; counsel review needed | Strong contribution record. Minor-inventor/signature language is appropriately cautious here. |
| `04_prior_art_search_notes.md` | Good initial search | Strong differentiator summary. Formal patent search still pending for nonprovisional. |
| `05_provisional_draft.md` | Strong main draft | Good technical support. Section 23 contains stale TODOs that should be updated. |
| `05_provisional_draft.pdf` | Needs final verification | Receipt file says it is 365 KB and includes figures 1–7; verify exact PDF content before filing. |
| `06_figures/` | Present | Seven figure source files exist. Confirm embedded or attached in final PDF. |
| `07_filing_receipt.md` | Placeholder | Fill immediately after filing. Currently has TBD fields and unchecked submitted-document boxes. |

---

## 3. Filing-Readiness Checklist

### 3.1 Critical Before Filing

- [ ] Confirm the exact PDF to submit is `05_provisional_draft.pdf`.
- [ ] Open the PDF and verify:
  - [ ] title is correct;
  - [ ] all sections are present;
  - [ ] figures 1–7 are included or otherwise submitted;
  - [ ] no obvious formatting truncation occurred;
  - [ ] page numbers, captions, and figure references are acceptable;
  - [ ] no private notes, TODO comments, or misleading draft-only wording remain in the PDF.
- [ ] Confirm inventor list and spelling.
- [ ] Confirm who signs/submits in Patent Center for a minor inventor.
- [ ] Confirm entity status before payment.
- [ ] Confirm public disclosure dates if known, especially ICPICS and CNIB.
- [ ] Keep GitHub repositories private until filing is confirmed.
- [ ] Save the exact submitted PDF and filing confirmation.

### 3.2 Immediately After Filing

- [ ] Update `07_filing_receipt.md` with:
  - [ ] application number;
  - [ ] filing date;
  - [ ] confirmation number;
  - [ ] entity status;
  - [ ] fee paid;
  - [ ] exact submitted PDF filename;
  - [ ] payment receipt location;
  - [ ] nonprovisional deadline.
- [ ] Save the USPTO confirmation page as PDF in `patent/`.
- [ ] Record the 12-month nonprovisional deadline in calendar systems.
- [ ] Mark materials “patent pending” only after filing confirmation is received.
- [ ] Keep a frozen copy of the submitted PDF.

### 3.3 Within 12 Months After Filing

- [ ] Complete formal prior-art search.
- [ ] Engage counsel for nonprovisional claims well before the deadline.
- [ ] Implement and document `quality_gate.py` or equivalent algorithm if possible.
- [ ] Collect more validation data if available.
- [ ] Consider whether new matter requires a second provisional before any new publication.

---

## 4. Strengths of the Draft

### 4.1 Clear Novelty Center

The draft consistently distinguishes the invention from generic EMG feature extraction or EMG/IMU fusion by emphasizing a trustworthiness gate:

```text
RAW EMG + hardware ENV + IMU context + session continuity
    -> signal-quality metrics
    -> trustworthiness classification
    -> downstream action on fatigue/activation interpretation
```

This is a strong framing because it positions the invention as reliability-aware sensing rather than merely another fatigue classifier.

### 4.2 Good Claim-Family Support

The draft supports at least five claim families:

1. RAW/ENV/IMU trustworthiness gate.
2. Quality-gated baseline selection.
3. Session continuity / BLE gap validity audit.
4. Ghost-channel / hardware failure diagnostic.
5. Confidence-aware real-time or offline output.

### 4.3 Good Technical Detail

The draft includes representative computations, including:

- RAW DC removal;
- rectification;
- software envelope generation;
- RAW/ENV ratio;
- RAW/ENV correlation;
- ENV saturation percentage;
- RAW flatline detection;
- contact-quality score;
- IMU movement stability trends;
- high-motion artifact thresholds;
- quality-gated baseline selection.

This helps enablement and written-description support.

### 4.4 Useful Experimental Examples

The examples are helpful and concrete:

- `log0305`: continuous 63.1-minute tennis session, 626 swings, low ENV saturation, stable IMU.
- `log0303`: BLE gap causing misleading full-session fatigue interpretation.
- Pogo-pin failure: high RAW/ENV correlation, near-zero variance, post-filter flatline, fixed by solder bypass.

These examples should be kept as non-limiting embodiments.

---

## 5. Issues to Fix or Note

### Issue 1 — `05_provisional_draft.md` Section 23 is stale

Section 23 lists tasks that appear already completed:

- create attorney-facing invention disclosure;
- add system diagrams;
- draft full prose;
- draft claim-style concepts;
- build public-disclosure timeline;
- list inventors;
- identify closest prior art references.

Recommendation:

- Before filing, remove Section 23 from the submitted PDF or update it to say these tasks are complete / records are in companion files.
- If already filed, leave the filed PDF unchanged but update the Markdown working copy for future nonprovisional work.

### Issue 2 — Filing status is not synchronized

`07_filing_receipt.md` is still a placeholder. If filing has occurred, update it immediately. If filing has not occurred, keep it as the post-filing capture sheet.

Recommendation:

- Treat `07_filing_receipt.md` as the source of truth after submission.
- Treat `00_patent_plan.md` as the planning archive, not the filing-status source of truth.

### Issue 3 — Exact public disclosure dates remain TBD

`02_public_disclosure_timeline.md` still has expected `~2026-07` dates for ICPICS and CNIB.

Recommendation:

- If filing occurs before publication, this is acceptable for immediate filing readiness.
- Still update exact publication dates later for records and future nonprovisional/international analysis.

### Issue 4 — Minor-inventor signature formalities should remain neutral

`03_inventor_contribution_matrix.md` uses cautious language:

> Confirm with USPTO Patent Center instructions who must sign the provisional cover sheet for a minor inventor.

This is better than definitive language. Avoid rigid statements such as “guardian signs oath/declaration,” because provisionals generally do not require oath/declaration and signature rules should be confirmed from USPTO instructions or counsel.

Recommendation:

- Update any remaining definitive guardian-signature language in planning checklists to match the neutral wording from `03_inventor_contribution_matrix.md`.

### Issue 5 — PDF verification not yet evidenced

The folder contains `05_provisional_draft.pdf`, and `07_filing_receipt.md` states it includes figures 1–7. However, the Markdown review alone does not prove the PDF exactly matches the intended filing package.

Recommendation:

- Open the PDF before filing.
- Confirm all figures and captions are included.
- Confirm the submitted PDF is the intended final version.

---

## 6. Drafting Improvements Recommended Before Nonprovisional

These are not necessarily blockers for a provisional, but would strengthen a later nonprovisional.

### 6.1 Add Representative Threshold Examples

The current draft uses some example thresholds, such as `rms_threshold = 0.25 * p90_rms`. More examples would help later claim support.

Potential additions:

```text
ENV saturation threshold:
  env_hw >= 0.95 * ADC_full_scale

RAW flatline threshold:
  raw_variance < variance_min for at least T seconds

Ghost-channel threshold:
  corr(raw, env) > 0.95
  and raw_variance < variance_min
  and filtered_raw_rms < rms_min

Session gap threshold:
  inter-sample gap > K times expected sample interval
  or reconnect event detected
  or device timestamp reset detected

IMU shock threshold:
  gyro_mag > gyro_threshold
  or acc_dyn > acc_threshold
  or jerk > jerk_threshold
```

Use “in some embodiments” language so these thresholds remain examples, not limitations.

### 6.2 Add Confidence-Score Formula Example

A representative confidence score could help support confidence-aware output claims:

```text
confidence = 1.0
confidence -= w1 * raw_env_mismatch_score
confidence -= w2 * env_saturation_score
confidence -= w3 * flatline_score
confidence -= w4 * imu_artifact_score
confidence -= w5 * session_gap_score
confidence = clamp(confidence, 0, 1)
```

### 6.3 Add More Alternative Embodiments

The draft already has a good variations section. For nonprovisional preparation, consider expanding:

- multiple EMG channels;
- no hardware ENV but second independent amplitude channel;
- impedance sensor as optional additional validity input;
- ECG/EEG/EOG analogs;
- embedded-only operation without host computer;
- mobile-only operation;
- cloud-based batch processing;
- wired acquisition without BLE;
- other wireless links.

### 6.4 Clarify “Simultaneous”

The claim concepts use “simultaneously” for RAW and hardware envelope. To avoid unnecessary narrowness, future claim drafting may use broader phrasing:

- “corresponding to a common monitoring interval”
- “temporally aligned”
- “acquired from the same sensor during overlapping windows”
- “sampled concurrently or time-synchronized”

This gives flexibility for systems where RAW and ENV are sampled at different rates or multiplexed.

---

## 7. Prior-Art Positioning Notes

The strongest differentiating arguments are already captured well in `04_prior_art_search_notes.md`.

Use these themes consistently:

1. **Not raw-only EMG quality analysis**
   - The invention uses a hardware envelope output as a paired quality/context channel.

2. **Not generic EMG/IMU fusion**
   - IMU is used to determine whether EMG interpretation is trustworthy, not merely as another classifier feature.

3. **Not fixed warmup**
   - Baseline selection is dynamically quality-gated.

4. **Not ordinary BLE logging**
   - Session continuity is treated as a validity condition for fatigue interpretation.

5. **Not generic ADC crosstalk**
   - The ghost-channel diagnostic is specific to wearable biosignal acquisition and RAW/ENV paired channels.

---

## 8. Recommended Immediate Edits

If editing the working Markdown before PDF generation, prioritize these changes:

1. Update or remove stale Section 23 in `05_provisional_draft.md`.
2. Synchronize `00_patent_plan.md` final checklist with current filing status.
3. Change any definitive minor-inventor signature statement to neutral wording:
   > Confirm with USPTO Patent Center instructions or counsel who must sign/submit the provisional cover sheet for a minor inventor.
4. Add a short “Representative Non-Limiting Thresholds” subsection to `05_provisional_draft.md`.
5. Add a short “Representative Confidence Score” subsection to `05_provisional_draft.md`.
6. Confirm figure references and PDF inclusion.

---

## 9. Overall Recommendation

From a technical drafting perspective, the provisional is strong enough to preserve the main invention concept if the final PDF includes the current specification and figures.

The most important immediate actions are:

1. verify the exact filing PDF;
2. file before CNIB/ICPICS public disclosure if not already filed;
3. update `07_filing_receipt.md` immediately after filing;
4. calendar the 12-month nonprovisional deadline;
5. prepare for attorney-led nonprovisional claim drafting.

The application’s strongest patent story is:

> A wearable EMG system should not automatically interpret EMG-derived fatigue or activation features. It should first determine whether the EMG signal is trustworthy by comparing RAW-derived features with a hardware envelope channel, interpreting those metrics in IMU and session-continuity context, and then gating, suppressing, segmenting, delaying, down-weighting, or annotating downstream physiological interpretation.