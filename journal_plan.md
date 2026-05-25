# Journal Submission Plan: Combined MDPI Sensors Paper

**Status:** Planning — supersedes [paper2_plan.md](paper2_plan.md) (single-paper journal extension)
**Target:** [MDPI Sensors](https://www.mdpi.com/journal/sensors), regular submission (Special Issue tag chosen later)
**Format:** ~15–25 page journal article
**Source papers:** [paper_cnib.md](paper_cnib.md) + [icpics_draft.md](icpics_draft.md) (with [icpics_draft_long.md](icpics_draft_long.md) as reference)
**Authors:** Ryan Wang, Theodore Di, Dr. YanMing Di
**Last Updated:** 2026-05-24

---

## Context

Two conference submissions exist on the same EMG–IMU wearable project, sharing the same two field sessions (log0303, log0305):

- **Paper A (CNIB):** [paper_cnib.md](paper_cnib.md) — *"Field Validity of Wearable sEMG Fatigue Metrics in Tennis: Electrode Settling, Contact Quality, and IMU-Conditioned Interpretation"*. Methodology: three-phase MDF trajectory, warmup-skip sensitivity, IMU-conditioned EMG validity, contact-quality monitoring, session-gap artifact detection.
- **Paper B (ICPICS):** [icpics_draft.md](icpics_draft.md) (6-page) and [icpics_draft_long.md](icpics_draft_long.md) (extended). System: ESP32 dual-core, ADC DMA + decimation, self-describing BLE TLV protocol, two-layer watchdog, hybrid `abs_us` reconstruction, pogo-pin ghost-signal field failure.

The goal is to combine both into a single journal submission to MDPI Sensors that goes beyond either conference paper. IEEE-style conference→journal extension policy expects ~30–50% new content; we plan four new contributions (below) that comfortably clear that bar.

**Why this merge instead of two journal papers?** The methodology and platform are tightly coupled — the spectral fatigue analysis requires RAW EMG access (only available because we routed past the pogo pin), the gap-artifact detection requires the hybrid `abs_us` timeline, and the IMU-conditioned validity framework requires synchronized 2 kHz EMG + 200 Hz IMU. A combined paper makes that coupling explicit. Two separate papers would force artificial separation and weaken both.

---

## Strategic Decisions

| Decision | Choice |
|---|---|
| Story angle | **Methodology-first, platform as enabler** |
| Target | MDPI Sensors, regular submission |
| Authors | Ryan Wang, Theodore Di, Dr. YanMing Di |
| Length | ~15–25 pages (MDPI Sensors typical) |

### Four new contributions beyond the conference papers

1. **Quantitative `abs_us` validation** — explicitly deferred from ICPICS §VI to journal version
2. **Ball-impact masking analysis** — May 2026 work in [CHANGELOG](CHANGELOG.md), pre-impact MDF window
3. **Multi-subject / multi-session data collection** — addresses the single-subject limitation of both conference papers
4. **Expanded comparative analysis** — engineering comparison table + deeper related-work positioning

---

## Working Title (proposed)

*"Trustworthy Field sEMG Fatigue Monitoring on a Low-Cost Wearable: Electrode Settling, IMU-Conditioned Validity, and Continuity Auditing on a $99 ESP32 Platform"*

Alternatives:
- *"Field-Validity Engineering for Wearable sEMG Fatigue Monitoring: A $99 ESP32–IMU Platform with Settling-Aware Methodology in Tennis"*
- *"From $99 Hardware to Trustworthy Spectral Fatigue: A Field-Debuggable EMG–IMU Wearable for Tennis"*

---

## Target Paper Structure

```
1. Introduction
   - Field-validity problem for wearable sEMG fatigue
   - Why no-gel forearm + tennis is a hard case
   - Platform-as-enabler thesis (RAW spectral access, abs_us, IMU context)
   - Combined contributions list (methodology + platform)

2. Related Work
   - Lab vs. field sEMG fatigue (SENIAM, Rota, Wang LH, Girard)
   - Dry electrode / contact quality (Joutsen, Boyer, Ravichandran)
   - IMU+EMG fusion vs. IMU-as-context (Taborri, Bangaru)
   - Low-cost wearable EMG platforms (Cerone, Lynn, Yang, MultiSenseBadminton)
   - Commercial reference (Delsys, Noraxon)
   - Gap statement: trustworthiness-first, end-to-end, field-debuggable

3. The $99 ESP32 EMG–IMU Platform (compact — platform-as-enabler)
   3.1 Hardware ($99 BoM, RAW+ENV, electrode placement, pogo-pin fix)
   3.2 Dual-core FreeRTOS scheduling
   3.3 ADC DMA oversampling + 10× decimation, ±25 µs timestamps
   3.4 Self-describing BLE TLV protocol (FSR codes survive firmware revisions)
   3.5 Two-layer watchdog + hybrid abs_us timeline reconstruction

4. Methodology: Trustworthy Field sEMG Fatigue
   4.1 No-added-gel field configuration (rationale)
   4.2 Physical basis of electrode settling (sweat + Ag/AgCl)
   4.3 Signal processing (detrend → bandpass 50–450 Hz → notch 60/120 Hz → Welch PSD)
   4.4 Swing detection (300 dps, 2000 ms debounce — distribution-based threshold)
   4.5 IMU-conditioned EMG validity framework (Table 1 from paper_cnib)
   4.6 Warmup-skip sensitivity protocol
   4.7 Contact-quality metric
   4.8 NEW: Ball-impact window masking (IMU-guided, pre-impact MDF window)

5. Field Validation: Platform Reliability
   5.1 Timestamp accuracy (98.65% within ±25 µs over 7.5M samples)
   5.2 EMG/IMU sequence loss accounting (per-session)
   5.3 BLE reconnection robustness
   5.4 NEW: Quantitative abs_us validation against host_rx_ms ground truth
   5.5 Pogo-pin ghost-signal field failure (diagnosis + bypass)

6. Methodology Results
   6.1 Three-phase MDF trajectory (Phase I settling, II reference, III fatigue-consistent)
   6.2 Warmup-skip sensitivity (−2.6% / −26.2% / +28.1%)
   6.3 IMU-conditioned validity (r = +0.029, IMU stable across 626 swings)
   6.4 Contact-quality evolution
   6.5 Session-gap artifact (log0303: 28.7% spurious vs. 4.9% real)
   6.6 NEW: Ball-impact masking impact on MDF estimates
   6.7 NEW: Multi-subject results (generalization of 3-phase pattern)

7. Discussion
   7.1 Platform–methodology coupling (RAW access, abs_us, IMU-as-context all required)
   7.2 Generalization beyond tennis / single subject
   7.3 Pogo-pin failure mode generalizes to any multiplexed-ADC wearable
   7.4 Practical recommendations for field sEMG deployment
   7.5 Limitations (no MVC/RPE/ball-speed ground truth, BLE 4.2 throughput ceiling)

8. Conclusion
9. References (merged + expanded)
```

---

## Content Mapping: Source → Target

| Target section | From paper_cnib | From icpics_draft | New material |
|---|---|---|---|
| §1 Intro | §1 (motivation, field validity) | §I (cost barrier, engineering gap) | Combined thesis |
| §2 Related Work | §1 refs [1–15] | §II refs [3–10] | Comparative table (N4) |
| §3 Platform | §2 (compact hardware) | §III–§VI (full system) | — |
| §4 Methodology | §2.swing-detect, §3 all | — | §4.8 ball-impact (N2) |
| §5 Field validation | §4.5 (gap artifact) | §VII A–D | §5.4 abs_us validation (N1) |
| §6 Method results | §4.1–4.4 (all results) | — | §6.6 impact (N2), §6.7 multi-subj (N3) |
| §7 Discussion | §5 | §VIII | Cross-cutting platform–method coupling |

---

## New Content (4 items) — Implementation Detail

### N1. Quantitative `abs_us` validation (deferred from ICPICS §VI)

- **Plan:** Compare three timeline reconstructions per BLE event:
  1. `dev_us`-only (fails on device reset)
  2. `host_rx_ms`-only (loses µs precision within connection)
  3. Hybrid `abs_us` (current rule from `capture_loader.load_session_stitched()`)
- **Metric:** Reconstruction error vs. `host_rx_ms` ground truth (median, p99)
- **Data:** Within-run BLE re-subscriptions in log0305 + the 1 between-run reconnect in log0303
- **Output:** New figure (timeline error CDF) + table of error bounds
- **Sanity check:** Median error should fall within BLE notification interval (7.5–30 ms)
- **Code:** New analysis script under `emg_util/`, reusing existing `capture_loader.load_session_stitched()`

### N2. Ball-impact masking analysis (CHANGELOG 2026-05-03)

- **Status:** First implementation done in `emg_util_yaml_runner.py`. Finding: sample-level ±20 ms masking has near-zero mean MDF effect (~3% of 1300 ms window — Welch segment averaging dominates).
- **Plan for paper:** Implement Approach B from CHANGELOG — pre-impact MDF window `[t_impact-600 ms, t_impact-20 ms]` (~580 ms, nperseg=512). Reanalyze log0305 (507/626 swings have impact ≥ 3.0g) and report MDF distribution shift.
- **Theoretical hook:** Demonstrates IMU-conditioned EMG cleaning (uses IMU as artifact detector) — strengthens the "IMU as context" framework presented in §4.5.
- **Output:** New figure: per-swing MDF before/after impact-aware windowing, plus statistical comparison.
- **Dual-file rule:** Update both `emg_util.py` and `emg_util_nopandas.py`; run `pytest tests/test_regression.py -v` and `pytest tests/test_regression_nopandas.py -v` before committing.

### N3. Multi-subject / multi-session collection

- **Goal:** Minimum 3 additional subjects × 1 session each, ≥45 min per session, with same hardware and IRB protocol.
- **IRB:** Confirm IRB packet at [IRB_Packet_OSU_sEMG_IMU_Athletic_Practice.md](IRB_Packet_OSU_sEMG_IMU_Athletic_Practice.md) is still active. Re-consent each new subject per [IRB_requirements.md](IRB_requirements.md).
- **Pre-collection blockers:** Verify the four algorithm fixes from CHANGELOG (impact masking, window merging, baseline RMS filtering, swing detection) are stable and regression-tested.
- **Per-subject analysis:** 3-phase MDF check, settling duration variability, IMU correlation distribution.
- **Output:** Per-subject summary table + cross-subject 3-phase phase-mean figure.
- **Significance:** This is the single largest new contribution — moves the paper from "pilot" (n=1) to "small-cohort validation" (n=4+).
- **Risk:** Calendar-bound. Plan early; coordinate with subject availability.

### N4. Expanded comparative analysis

- **Engineering comparison table** — across this work, Delsys Trigno, Noraxon Ultium, Cerone HD-sEMG, Lynn/Athos, Yang e-textiles, MultiSenseBadminton:
  - Cost
  - Sample rate (EMG / IMU)
  - RAW EMG access
  - BLE protocol robustness (self-describing? CRC? watchdog?)
  - `abs_us`-equivalent feature (timeline reconstruction across reconnects)
  - Multi-platform support (PC + Android)
  - Open hardware/software status
- **Methodology comparison narrative** — position vs. Rota 2014, Wang LH 2019, Girard 2011, plus the SENIAM gap on forearm electrode placement.
- **No new experiments** — citation/table work only. Cheapest of the four new items; can begin immediately.

---

## Critical Files

### Sources (read-only references)
- [paper_cnib.md](paper_cnib.md) — CNIB methodology paper
- [icpics_draft.md](icpics_draft.md) — ICPICS 6-page conference paper
- [icpics_draft_long.md](icpics_draft_long.md) — Extended ICPICS draft
- [paper_plan.md](paper_plan.md) — CNIB planning doc (full background)
- [paper2_plan.md](paper2_plan.md) — Earlier journal-extension plan (superseded by this doc)
- [HIGH_LEVEL_DESIGN.md](HIGH_LEVEL_DESIGN.md) — System architecture reference
- [CHANGELOG.md](CHANGELOG.md) — Recent algorithm work

### To create
- `journal_draft.md` — eventual journal manuscript (built incrementally per content-mapping table)
- Analysis scripts for N1 (`abs_us_validate.py`), N2 (pre-impact MDF in `emg_util_yaml_runner.py`), N3 (multi-subject pipeline)

### Figures (already exist — to reuse)
**From [paper_figures/](paper_figures/):**
- `fig2_electrode_settling.png` (3-phase trajectory)
- `fig3_imu_consistency.png` (IMU stability across phases)
- `fig4_warmup_skip_sensitivity.png` (warmup-skip)
- `fig5_contact_quality.png` (contact quality)
- `fig6_log0303_gap_artifact.png` (gap artifact)
- `fig7_imu_emg_diagnostic_matrix.png` (IMU–EMG matrix)
- `fig11_psd_early_mid_late.png` (PSD comparison)
- `fig15_ble_gap_audit.png` (BLE gap audit)
- `fig16_raw_env_consistency.png` (RAW–ENV)

**From [icpics_figures/](icpics_figures/):**
- `fig_system_architecture.png`
- `fig_protocol.png`
- `fig_timing_accuracy.png`
- `fig_emg_imu_sync.png`

**New figures needed:**
- abs_us reconstruction error CDF (N1)
- Pre-impact MDF distribution (N2)
- Cross-subject 3-phase summary (N3)
- Engineering comparison table rendered (N4)

---

## Action Plan (sequenced)

1. **N4 first (cheapest):** Expanded comparative analysis — pure citation work, no new data needed. Can begin immediately.
2. **N1 next:** Quantitative `abs_us` validation script. Existing log0303/log0305 data sufficient.
3. **N2:** Implement pre-impact MDF window (Approach B). Update both `emg_util.py` and `emg_util_nopandas.py` per dual-file rule. Run regression tests.
4. **Outline draft:** Assemble `journal_draft.md` skeleton — pull text from both source papers per content-mapping table, mark TODOs for new sections.
5. **N3 (largest, longest):** Multi-subject data collection. Confirm IRB; identify subjects; collect; analyze; integrate results.
6. **Full draft + figure consolidation:** Finalize all figures (renumber across merged paper), polish prose, format per MDPI Sensors LaTeX template / MDPI ref style.
7. **Internal review:** Dr. Di reviews; address comments.
8. **Submission package:** Cover letter, suggested reviewers, MDPI Sensors author-guidelines compliance.

---

## Verification

How we'll know each piece works:

- **N1 (abs_us validation):** New script reproduces published `abs_us` reconstruction; computes error vs. `host_rx_ms` ground truth and emits CDF figure. Sanity: median error within BLE notification interval (7.5–30 ms).
- **N2 (impact masking):** Pre-impact MDF differs measurably from full-window MDF on swings with `impact_acc_dyn_g >= 3.0`. Run `pytest tests/test_regression.py -v` and `pytest tests/test_regression_nopandas.py -v` after dual-file changes.
- **N3 (multi-subject):** End-to-end pipeline (BLE capture → CSV → fatigue analysis) runs cleanly on each new subject; per-subject 3-phase pattern recovered (or, if not, the paper reports the variability honestly).
- **N4 (related work):** Comparison-table cells all have a defended citation; no "TBD" entries at submission.
- **Manuscript:** PDF compiles cleanly via pandoc/xelatex; word/page count within MDPI Sensors expectations (~15–25 pages).
- **Reproducibility:** Every figure can be regenerated from a recorded analysis-output directory (`out0303_*`, `out0305_*`, `out_subject*_*`).

---

## Open Questions to Revisit

- Special Issue choice: track Sensors SI calls; consider sports biomechanics or wearable health/biosignal monitoring SIs as they open.
- Multi-subject hardware: do we have enough sensor units for parallel subject sessions, or do we need to swap one unit between subjects?
- Cover letter strategy: emphasize the trustworthiness-first framing as a contribution to the field, not just the engineering deliverable.

---

## Build Workflow (Validated 2026-05-25)

### Overview

`journal_draft.md` is the **master working document** — write prose, add citations,
update sections here. `journal_sensors_pandoc.tex` is auto-generated by pandoc; never
edit it by hand. `journal_sensors.tex` is an older hand-translated version kept for
reference.

### File Map

| File | Role |
|---|---|
| `journal_draft.md` | Master manuscript (edit this) |
| `references.bib` | BibTeX database (edit when adding citations) |
| `mdpi_template/mdpi_pandoc_template.tex` | Pandoc → MDPI LaTeX template (rarely edit) |
| `mdpi_template/journal_sensors_pandoc.tex` | Auto-generated — **do not edit** |
| `mdpi_template/journal_sensors_pandoc.pdf` | Compiled output |
| `mdpi_template/paper_figures → ../paper_figures` | Symlink |
| `mdpi_template/icpics_figures → ../icpics_figures` | Symlink |

### Citation Format

In `journal_draft.md`, cite using `[@key]` syntax. Keys are in `references.bib`:

```markdown
electrode settling [@joutsen2024; @ravichandran2023]
Rota et al. [@rota2014] found that MDF declines...
```

To add a new reference: add the `@article{...}` entry to `references.bib`, then use
`[@newkey]` in the text.

### Build Command (one-liner, run from `emg_util/`)

```bash
pandoc journal_draft.md \
  --template mdpi_template/mdpi_pandoc_template.tex \
  --bibliography references.bib \
  --natbib \
  --syntax-highlighting=none \
  --shift-heading-level-by=-1 \
  --wrap=preserve \
  -o mdpi_template/journal_sensors_pandoc.tex && \
cd mdpi_template && \
pdflatex -interaction=nonstopmode journal_sensors_pandoc.tex && \
bibtex journal_sensors_pandoc && \
pdflatex -interaction=nonstopmode journal_sensors_pandoc.tex && \
pdflatex -interaction=nonstopmode journal_sensors_pandoc.tex
```

Output: `mdpi_template/journal_sensors_pandoc.pdf` (23 pages as of 2026-05-25).

### Why 3× pdflatex?

- **Pass 1:** Compiles content, generates `.aux` with citation keys
- **bibtex:** Reads `.aux` + `references.bib`, writes `.bbl` with formatted references
- **Pass 2:** Reads `.bbl`, resolves `\cite{}` → numbers, fixes cross-refs
- **Pass 3:** Resolves any remaining forward references and page numbers

### Template Compatibility Fixes (do not remove from `mdpi_pandoc_template.tex`)

These are required for pandoc 3.x + MDPI class compatibility:

| Fix | Reason |
|---|---|
| `\usepackage{longtable}` | Pandoc generates markdown tables as longtable |
| `\newcommand{\pandocbounded}[1]{#1}` | Pandoc 3.x wraps images in `\pandocbounded{}` |
| `\define@key{Gin}{alt}{}` | Pandoc 3.x adds `alt={}` to `\includegraphics`; not supported by graphicx |
| `\newcounter{none}` | longtable sets `\LTcaptype=none`; MDPI class needs this counter |
| `\newunicodechar{≤}{...}` etc. | pdflatex can't handle Unicode math symbols natively |
| `\providecommand{\tightlist}{...}` | Pandoc adds `\tightlist` to list environments |
| `--shift-heading-level-by=-1` | journal_draft.md uses `##` for §1, §2 etc. → maps to `\section` |
| `--natbib` | Uses MDPI's own `Definitions/mdpi.bst` for reference formatting |
