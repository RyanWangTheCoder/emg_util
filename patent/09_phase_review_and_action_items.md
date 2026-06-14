# Phase Review and Action Items — Provisional Patent Package

> Review date: 2026-06-12  
> Scope: requested Phase 1–5 review of filing package, draft quality, patent-strength support, filing checklist, and optional Markdown edits.  
> Not legal advice. Use this as a technical/drafting checklist for attorney review and filing operations.

---

## Phase 1 — Filing Package Audit

### 1.1 Files Compared

| File | Current role | Audit result |
|---|---|---|
| `00_patent_plan.md` | Master planning document and checklist | Useful but contains historical filename references and planning examples that no longer match the current folder names. Section 20 is the current final filing checklist. |
| `05_provisional_draft.md` | Main provisional specification | Strong and mostly synchronized. Section 23 is now a drafting-status section, not a stale TODO list. |
| `07_filing_receipt.md` | Post-filing receipt capture sheet | Correctly remains a placeholder until filing occurs. Contains TBD fields that must be filled immediately after filing. |
| `02_public_disclosure_timeline.md` | Public-disclosure and filing-deadline record | Good structure. ICPICS and CNIB publication dates remain TBD and should be updated as soon as known. |

### 1.2 Stale TODOs / Inconsistent Filenames

#### `00_patent_plan.md`

The file still contains older suggested filenames in planning/example sections:

| Location / context | Older reference | Current file |
|---|---|---|
| Early support list | `patent_provisional_draft.md` | `patent/05_provisional_draft.md` |
| Public-disclosure example | `patent_public_disclosure_timeline.md` | `patent/02_public_disclosure_timeline.md` |
| Draft path example | `/local/mnt/workspace/wangx/projects/emg_util/patent_provisional_draft.md` | `/local/mnt/workspace/wangx/projects/emg_util/patent/05_provisional_draft.md` |
| Filing package example | `patent_provisional_draft.pdf` | `patent/05_provisional_draft.pdf` |
| Internal records example | `inventor_contribution_table.md`, `prior_art_notes.md` | `03_inventor_contribution_matrix.md`, `04_prior_art_search_notes.md` |
| Suggested project file set | `05_provisional_draft_raw_env_imu_quality.md`, `07_claim_concepts.md`, `08_attorney_review_questions.md` | Current package uses `05_provisional_draft.md` and now has `08_filing_readiness_review.md`, `09_phase_review_and_action_items.md` |

Assessment: these are not fatal because the plan is partly historical and advisory, but they can confuse filing operations. Prefer a short note in `00_patent_plan.md` saying the current file set is the numbered `patent/` folder.

#### `05_provisional_draft.md`

Section 23 currently reads:

- all pre-filing drafting tasks complete as of 2026-06-01;
- remaining before filing:
  - obtain ICPICS and CNIB publication dates;
  - file provisional through Patent Center;
  - record filing receipt.

Assessment: this is no longer the stale TODO list that appeared in an earlier version. It is acceptable. Optional refinement: add “PDF verification” and “confirm minor-inventor cover-sheet signature/submission requirements” to the remaining-before-filing list.

#### `07_filing_receipt.md`

TBD values are expected before filing:

- application number;
- filing date;
- confirmation number;
- fee paid;
- nonprovisional deadline;
- pro bono status.

Assessment: not stale; this is intentionally a post-filing worksheet.

#### `02_public_disclosure_timeline.md`

TBD publication dates remain for ICPICS and CNIB.

Assessment: pending, not obsolete. If filing occurs before either publication, this does not block immediate provisional filing, but it should be completed for records.

### 1.3 Filing-Status Contradictions

No hard contradiction found. Current status appears to be:

- draft/specification package is ready or near-ready;
- PDF exists;
- filing receipt is not yet filled;
- filing is not yet recorded as complete.

The only ambiguity is that some planning language says “final checklist” while `07_filing_receipt.md` is still blank. This is normal if filing is imminent but not complete.

### 1.4 Checklist Item Classification

| Item | Source | Status | Notes |
|---|---|---|---|
| One-page invention disclosure | `05_provisional_draft.md` §23 | Complete | `01_invention_disclosure.md` exists. |
| Figures 1–7 | `05_provisional_draft.md` §23 | Complete as source files | `06_figures/` contains all seven figure Markdown files. Confirm included in PDF. |
| Full prose specification | `05_provisional_draft.md` §23 | Complete | Main draft is complete. |
| Claim-style concepts | `05_provisional_draft.md` §23 | Complete | C1–C18 present. |
| Public-disclosure timeline | `05_provisional_draft.md` §23 | Complete but pending exact dates | `02_public_disclosure_timeline.md` exists. |
| Inventor/contributor matrix | `05_provisional_draft.md` §23 | Complete but counsel review pending | `03_inventor_contribution_matrix.md` exists. |
| Prior-art search notes | `05_provisional_draft.md` §23 | Complete for provisional; pending formal search for nonprovisional | `04_prior_art_search_notes.md` exists. |
| Confirm ICPICS/CNIB exact publication dates | multiple | Pending | Not a blocker if filing before publication; important for records. |
| Attorney review | `00_patent_plan.md` | Pending | Recommended before filing if possible; essential before nonprovisional. |
| Confirm minor-inventor signature/submission requirements | `03_inventor_contribution_matrix.md`, `00_patent_plan.md` | Pending | Keep wording neutral; confirm with USPTO instructions or counsel. |
| File through Patent Center | `00_patent_plan.md`, `05_provisional_draft.md` | Pending | No receipt data yet. |
| Save filing receipt/application number | `07_filing_receipt.md` | Pending until filed | Fill immediately after filing. |
| Record 12-month deadline | `07_filing_receipt.md` | Pending until filed | Deadline = filing date + 12 months. |
| Mark “patent pending” | `00_patent_plan.md` | Pending until filed | Do not mark before confirmation. |

---

## Phase 2 — Draft Quality Review

### 2.1 Missing Support for Claim Concepts

Overall support is strong.

| Claim concept / family | Support in draft | Assessment |
|---|---|---|
| C1 method | §§3, 6–12, 17 | Well supported. |
| C2 system | §4, §17 | Well supported. |
| C3 computer-readable medium | §17 and processing descriptions | Adequate. |
| C4 modification actions | §§11, 14, 17 | Well supported. |
| C5 signal-quality metrics | §7 | Strong. |
| C6 motion context | §9 | Strong. |
| C7 electrode settling | §§9, 10, 13.2 | Strong. |
| C8 reduced-effort confound | §9 | Adequate; could be strengthened with a second concrete example in nonprovisional. |
| C9 ghost-channel failure | §§7.2, 7.4, 13.4 | Strong, especially with thresholds and experimental r values. |
| C10 ENV saturation | §§7.3, 13.1 | Strong. |
| C11 baseline selection | §10 | Strong. |
| C12 session continuity | §§12, 13.5 | Strong. |
| C13 raw-derived envelope | §6 | Strong. |
| C14 contact quality | §7.6 | Adequate; threshold examples could be expanded in nonprovisional. |
| C15 confidence score | §11.5 | Stronger now because representative weighted formula is present. |
| C16 user feedback | §11.6, §14 | Adequate. |
| C17 real-time/offline | §§4, 16, 17 | Adequate. |
| C18 application scope | §16 | Strong. |

### 2.2 Overly Narrow Wording

Potentially narrowing terms:

| Term / phrase | Location | Risk | Recommended approach |
|---|---|---|---|
| “simultaneously acquired” | title/summary/claims | Could imply exact same-time sampling rather than aligned windows | In nonprovisional, use “simultaneously, concurrently, time-aligned, or corresponding to overlapping monitoring windows.” |
| “same wearable electromyography sensor” | claim concepts | Good for current invention, but may exclude separate but co-located front ends | Add alternatives: same sensor, same electrode pair, same muscle region, or associated EMG acquisition path. |
| Tennis examples | experimental support | Good example, but should not limit invention | Current draft has broader applications; keep examples non-limiting. |
| 2 kHz / 200 Hz / BLE / ESP32 / MyoWare | hardware embodiment | Could narrow if overemphasized | Draft already says not limited; keep “one implemented embodiment” language. |

### 2.3 Unsupported Absolute Statements

No severe unsupported absolute statements found. The draft mostly uses cautious language:

- “in some embodiments”;
- “may”;
- “candidate local fatigue”;
- “fatigue-consistent.”

Recommended continued caution:

- Avoid “proves fatigue.”
- Avoid “guarantees signal quality.”
- Prefer “improves,” “classifies,” “indicates,” “flags,” “reduces likelihood,” or “conditions interpretation.”

### 2.4 Ambiguous Terms

| Term | Possible ambiguity | Recommendation |
|---|---|---|
| trustworthiness | May be broad | Good umbrella term; keep tied to classification/state/action. |
| validity | Could imply legal/scientific truth | Use as “signal validity” or “interpretation validity,” not absolute physiological truth. |
| confidence | Could mean statistical probability or heuristic score | Draft now gives weighted-score example; label as representative/non-limiting. |
| hardware envelope | Could be analog ENV, digitized ENV, or MCU-derived low-rate envelope | Draft covers hardware-derived/low-rate envelope; good. |
| RAW/ENV consistency | Could mean correlation only | Draft lists ratio, shape, timing, saturation, variance; good. |

### 2.5 Terminology Consistency

Terminology is generally consistent:

- RAW / raw EMG: used interchangeably but understandable.
- ENV / hardware envelope: used interchangeably but understandable.
- IMU / motion context: consistent.
- trustworthiness / validity / confidence: related but distinct enough.

Optional improvement for nonprovisional: add a short definitions section:

```text
RAW refers to a raw or substantially unprocessed EMG waveform.
ENV refers to a hardware-derived or sensor-provided envelope or amplitude channel.
IMU context refers to acceleration, gyroscope, jerk, movement intensity, impact, or stability information.
Trustworthiness state refers to a classifier output used to modify downstream interpretation.
```

### 2.6 Examples That Might Accidentally Limit the Invention

Current examples are appropriately framed as embodiments. To further reduce limiting risk:

- Keep “one embodiment,” “representative,” and “non-limiting” language near thresholds.
- Avoid saying thresholds are required.
- Avoid saying tennis-specific behavior is necessary.
- Avoid requiring BLE gaps specifically; use wireless, wired, file, timestamp, reset, and segment discontinuities.

---

## Phase 3 — Patent-Strength Review by Claim Family

### Family 1 — RAW/ENV/IMU Trustworthiness Gate

Support: strong.

Key support:

- §3 summary of RAW + ENV + IMU + session continuity;
- §6 raw-derived envelope;
- §7 metrics;
- §8 failure modes;
- §9 IMU-conditioned validity;
- §11 downstream gating;
- C1/C2/C3.

Strength: this remains the central inventive story and is well supported.

Potential enhancement: broaden “simultaneously” in later claims to include time-aligned or overlapping acquisition.

### Family 2 — Quality-Gated Baseline Selection

Support: strong.

Key support:

- §10 baseline candidate filtering;
- representative p90 RMS threshold;
- conditions including RAW variance, ENV saturation, RAW/ENV consistency, contact quality, IMU context, and continuity;
- C11.

Strength: strong written-description support and practical motivation.

Potential enhancement: add more live-processing variants in nonprovisional.

### Family 3 — Session Continuity / BLE Gap Validity Audit

Support: strong.

Key support:

- §12 session continuity management;
- §13.5 session gap artifact;
- experimental example in §20.2;
- C12.

Strength: strong and concrete.

Potential enhancement: broaden beyond BLE to any wireless, wired, file, timestamp, reset, synchronization, or upload discontinuity.

### Family 4 — Ghost-Channel / Hardware Failure Diagnostic

Support: strong.

Key support:

- §7.2 correlation;
- §7.4 raw flatline;
- §13.4 ghost signal detection;
- §20.3 pogo-pin failure;
- C9.

Strength: very concrete diagnostic with experimental values.

Potential enhancement: include variants for ADC mux charge-sharing, floating input, connector failure, cable intermittency, and analog crosstalk.

### Family 5 — Real-Time and Offline Confidence-Aware Output

Support: adequate to strong.

Key support:

- §11.5 annotation/confidence score;
- §11.6 alert;
- §14 outputs/actions;
- §16 real-time/offline applications;
- C15–C17.

Strength: now stronger because the draft includes a representative weighted confidence score.

Potential enhancement: add UI/action examples: color-coded confidence, haptic alert, app notification, data-quality label in CSV, API output.

---

## Phase 4 — Concise Filing-Readiness Checklist

### 4.1 Files to Submit / Preserve

- [ ] `05_provisional_draft.pdf` — final specification PDF.
- [ ] Figures 1–7 — either embedded in PDF or included as submitted drawings.
- [ ] Patent Center provisional cover sheet / online bibliographic data.
- [ ] Fee payment confirmation.
- [ ] Exact copy of submitted PDF.
- [ ] USPTO filing receipt / confirmation page.

### 4.2 Final PDF Verification

- [ ] Open `05_provisional_draft.pdf`.
- [ ] Confirm title matches intended title.
- [ ] Confirm all sections are present.
- [ ] Confirm figures 1–7 are present and readable.
- [ ] Confirm claim concepts are present.
- [ ] Confirm no stale TODO list appears in the PDF.
- [ ] Confirm PDF is the same file uploaded to Patent Center.
- [ ] Save a frozen copy after filing.

### 4.3 Inventor / Contributor Records

- [ ] Preserve `03_inventor_contribution_matrix.md`.
- [ ] Confirm inventor name and address information.
- [ ] Confirm minor-inventor submission/signature requirements using USPTO instructions or counsel.
- [ ] Provide contribution matrix to counsel for nonprovisional inventorship review.

### 4.4 Disclosure Dates

- [ ] Update ICPICS publication date when known.
- [ ] Update CNIB publication date when known.
- [ ] Keep GitHub repositories private until filing confirmation.
- [ ] Do not release new public materials before deciding whether new matter should be protected.

### 4.5 Entity Status / Fee

- [ ] Confirm micro-entity or small-entity status before payment.
- [ ] Save payment receipt.
- [ ] Record fee amount in `07_filing_receipt.md`.

### 4.6 Receipt / Application Number Capture

- [ ] Record application number.
- [ ] Record confirmation number.
- [ ] Record filing date.
- [ ] Record exact submitted PDF filename and hash if desired.
- [ ] Save confirmation PDF in `patent/`.

### 4.7 12-Month Nonprovisional Deadline

- [ ] Compute deadline as filing date + 12 months.
- [ ] Record in `07_filing_receipt.md`.
- [ ] Add calendar reminders at 9 months, 6 months, 3 months, and 1 month before deadline.
- [ ] Engage attorney well before deadline.

### 4.8 Post-Filing Marking and Publication Precautions

- [ ] Use “patent pending” only after filing confirmation.
- [ ] Before any new paper/poster/code release, check whether it contains new matter.
- [ ] Consider a second provisional for new algorithms, validation data, UI, or implementation details not in the filed application.

---

## Phase 5 — Optional Markdown Edits

### 5.1 Edits Already Reflected or Not Needed

- `05_provisional_draft.md` Section 23 is no longer a stale “next drafting tasks” list; it is a “Drafting Status” section with completed and remaining items.
- `00_patent_plan.md` guardian/minor language at the final checklist is already neutral:
  > Confirm with USPTO Patent Center instructions who must sign the provisional cover sheet submission for a minor inventor.
- `05_provisional_draft.md` already includes representative threshold examples for:
  - ENV saturation;
  - RAW flatline;
  - IMU artifact thresholds;
  - ghost-channel detection;
  - confidence scoring.

### 5.2 Recommended Future Edits

1. Add a current-file-set note near the top of `00_patent_plan.md` to prevent confusion from historical filenames.
2. Add PDF verification as an explicit remaining-before-filing item in `05_provisional_draft.md` §23.
3. Add minor-inventor signature/submission confirmation as an explicit remaining-before-filing item in `05_provisional_draft.md` §23.
4. Add a short definitions section to the nonprovisional draft.
5. For later nonprovisional, broaden claim wording around “simultaneous” to include time-aligned / overlapping windows.

---

## Recommended Immediate Action Order

1. Open and verify `05_provisional_draft.pdf`.
2. If the PDF still has stale content, regenerate it from current `05_provisional_draft.md`.
3. Confirm minor-inventor Patent Center submission/signature requirements.
4. File before ICPICS/CNIB public release if not already filed.
5. Immediately fill `07_filing_receipt.md`.
6. Calendar the nonprovisional deadline.
7. Keep this review, the filing receipt, and the exact submitted PDF together as the prosecution record.