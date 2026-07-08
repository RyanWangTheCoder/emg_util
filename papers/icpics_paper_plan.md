# ICPICS Paper Plan (Conference Submission)

**Status:** Drafting — polish pass scoped 2026-05-16
**Target venue:** ICPICS (International Conference on Power, Intelligent Computing and Systems)
**Format:** 6-page IEEE conference paper
**Submission template:** [icpics_Templates.doc](icpics_Templates.doc) (IEEE 2-column conference format, MS Word .doc — final formatting step is markdown → Word)
**Draft file:** [icpics_draft.md](icpics_draft.md)
**Relationship to Paper 1 (CNIB):** Paper 1 cites this system briefly; this paper does not claim Paper 1's scientific findings as a contribution.
**Relationship to journal extension:** see [Deferred to journal extension](#deferred-to-journal-extension) below.

---

## Strategy: conference-first, journal-extended

This plan scopes a **modest-but-honest conference paper** for ICPICS. The stronger novel contributions (`abs_us` stitching with ground-truth validation, Chaquopy dual-platform parity, expanded field-failure characterisation) are deliberately **held back** for an extended journal version targeting MDPI Sensors or IEEE JBHI.

**Why not BSN as the extended version:** BSN is a conference, so an ICPICS → BSN path would run into IEEE self-plagiarism rules. Conference → journal is the standard path; the journal version requires ~30–50% new material plus citation of the ICPICS paper.

**Why scope down for ICPICS:**
- The pogo-pin diagnosis is the only genuinely novel piece in the current scope — surrounding it with under-developed claims (Chaquopy with no figure, `abs_us` in one sentence) gives reviewers targets to push back on.
- Cutting Android/Chaquopy gives the paper one coherent story (firmware → BLE → PC capture → field validation) instead of a platform dichotomy that the current draft can't fully defend.
- The current 2,431-word draft is already 80% of the way to a tight 6-page conference paper; the additions below are mostly missing structure, not new analysis.

---

## Working title (unchanged from current draft)

*"A Dual-Core ESP32 Wearable for Real-Time Concurrent EMG and IMU Acquisition via DMA-Driven ADC and Self-Describing BLE Protocol"*

---

## Sharpened contributions (5)

The current draft lists 5 contributions but two are weak alone. Revised:

1. **DMA-driven 2 kHz EMG acquisition** with 10× hardware oversampling and per-sample timestamp back-calculation, empirically validated to ±25 µs across 2.3 M samples.
2. **Self-describing BLE protocol** — IMU FSR codes embedded in every frame, validated across three firmware FSR revisions with zero host code changes.
3. **Dual-core FreeRTOS architecture** with explicit task-priority assignment, achieving zero-drop concurrent EMG (2 kHz) + IMU (200 Hz) streaming over 150+ minutes of field sessions.
4. **Two-layer field-recovery mechanism**: device-side host watchdog (pause at 18 s, reboot at 30 s) combined with host-side hybrid `abs_us` timeline reconstruction that unifies BLE-dropout and ESP32-reset reconnection cases without requiring detection of which occurred. One between-run reconnect handled without file corruption or recording-pipeline failure.
5. **Field-failure documentation**: pogo-pin ADC charge-sharing ghost signal (r = 0.998 vs. ENV pre-filter, flatlines post-filter), root-cause diagnosis, and reproducible solder-bypass fix.

**Why combine watchdog + `abs_us` into one contribution:** alone, each is incremental; together they form a coherent "what makes BLE wearables survive unattended field sessions" claim that's stronger than either piece in isolation.

---

## Section structure (revised from current draft)

| § | Section | Word target | Delta from current | Notes |
|---|---|---:|---:|---|
| I | Introduction | 300 | −170 | Tighten contribution list to the 5 above |
| II | Related Work | 250 | **+250** | NEW — currently absent |
| III | System Architecture (HW + dual-core) | 350 | ~0 | Add pin-mapping note (GPIO 39/32 vs A4 silk label) and FSR history |
| IV | Signal Acquisition (DMA, timing, I2C) | 400 | ~0 | Largely as-is |
| V | Protocol Design (TLV, FSR, watchdog) | 350 | ~0 | Largely as-is |
| VI | Host Capture Pipeline (PC) | 350 | **+270** | EXPAND — see breakdown below |
| VII | Evaluation / Field Validation | 400 | +50 | Add Table 4 (field validation metrics summary) |
| VIII | Discussion | 250 | **+250** | NEW — currently absent |
| IX | Conclusion | 150 | ~0 | Drop any Android/Chaquopy mention |
| **Total** | | **~2800** | **+650** | Plus figures + tables ≈ 6 pages IEEE |

### Section VI breakdown (PC capture pipeline — main expansion)

Currently ~80 words; target ~350 words covering:
- Async BLE (Bleak) → asyncio queue → FrameParser → consumer task → CSV writer
- FrameParser: MAGIC re-sync, CRC16 validation, malformed-frame drop without stalling
- Rotating CSV files (`emg_log_<session_id>_<open_id>_<idx>.csv`, 30-min segments) + sidecar `.meta.json`
- Watchdog/reconnect: stall detection at 5 s, exponential backoff (0.5 s → 20 s)
- **Hybrid `abs_us` timeline (1 paragraph, ~80 w):** two-case unification — within-connection uses `dev_us`, between-connection gaps use `host_rx_ms` delta. Handles BLE-dropout and ESP32-reset cases without detecting which. Defer ground-truth validation to journal version.
- UDP mirror (optional, non-blocking, decimated to 500/50/50 Hz for RAW/ENV/IMU)

---

## What gets dropped from the current draft

| In current draft | Action | Reason |
|---|---|---|
| Abstract: "PC Python receiver and Android app using Chaquopy for on-device spectral analysis" | Delete the Android phrase | Out of scope; held for journal |
| § V.B "Android App (btLeApp)" subsection | Delete entire subsection (~80 w) | Out of scope; held for journal |
| Standalone "Software Analysis Pipeline" section (per [paper2_plan.md](paper2_plan.md)) | Do **not** add | This is a *systems* paper; analysis details (preprocessing, MDF, baseline protection) are Paper 1 territory. The system-relevant analysis bit (`abs_us`) lives in § VI. |

---

## Figures (3 existing, 1 new)

| # | Figure | Status | File |
|---|---|---|---|
| 1 | System architecture (dual-core, sensors, hosts) | ✅ done | [icpics_figures/fig_system_architecture.png](icpics_figures/fig_system_architecture.png) |
| 2 | Inter-sample interval distribution (2.3 M samples) | ✅ done | [icpics_figures/fig_timing_accuracy.png](icpics_figures/fig_timing_accuracy.png) |
| 3 | Binary TLV frame format | ✅ done | [icpics_figures/fig_protocol.png](icpics_figures/fig_protocol.png) |
| 4 | Pogo-pin ghost signal: pre/post bypass | **TODO** — caption is publication-ready in draft; image file pending | Target: [icpics_figures/fig_pogo_pin_pre_post.png](icpics_figures/fig_pogo_pin_pre_post.png) |

### Figure 4 detailed requirements

The image at `icpics_figures/fig_pogo_pin_pre_post.png` must visibly support the caption claims that already appear in [icpics_draft.md](icpics_draft.md) § VII.D:

> *Pogo-pin ghost-signal failure mode before and after direct RAW-to-GPIO32 solder bypass. Pre-bypass, RAW ghost-tracked ENV (r = 0.998) and the preprocessed EMG channel flatlined. Post-bypass, RAW showed independent AC oscillation during contraction and retained spectral content after preprocessing.*

**Required visual elements (must be readable in IEEE 2-column format):**

1. **Pre-bypass RAW vs ENV similarity** — overlaid or stacked traces showing RAW tracking ENV during contraction. The `r = 0.998` annotation must be visible in the figure or caption.
2. **Pre-bypass preprocessed/filtered RAW flatline** — this is the *load-bearing* panel: the novelty is not just "bad contact" but "looked plausible before filtering, silently failed after standard 50–450 Hz EMG preprocessing."
3. **Post-bypass independent RAW activity** — AC oscillation during contraction; filtered/preprocessed output is no longer flat (carries spectral content).
4. **Clear before/after labels** — "Pre-bypass" and "Post-bypass" panel titles. Trace labels: `RAW`, `ENV`, `Filtered RAW` (or equivalent).

**Acceptable layouts:**

- **Two-panel (preferred for tight 6-page layout):**
  - Panel A: Pre-bypass live plot — RAW tracks ENV; filtered RAW flatline
  - Panel B: Post-bypass live plot — RAW independent AC activity; filtered RAW active
- **Four-panel (richer, if space allows):**
  - Panel A: Pre-bypass time traces (RAW + ENV overlaid)
  - Panel B: RAW–ENV scatter with `r = 0.998` annotation
  - Panel C: Pre-bypass filtered RAW flatline
  - Panel D: Post-bypass filtered RAW with active EMG content

**Source acceptable:**

- Live `sensordata_plotter.py` screenshots (e.g. `--mode offline --emg-file log0303/<pre-bypass>.csv` and a post-bypass capture) are acceptable — practitioner-debug aesthetic adds credibility.
- Polished matplotlib analytical figure is also acceptable and arguably cleaner for IEEE 2-column rendering.

**Things to avoid in the final figure:**

- Do not include command-line snippets (`sensordata_plotter.py --raw-zoom`) in the caption; the caption in the draft is already trimmed.
- Do not include irrelevant traces (HR, SpO2, IMU magnitude) — keep the focus on RAW vs ENV vs filtered RAW.
- Make sure axis labels and legends are large enough to read at IEEE 2-column print width (~3.4 inches).

Pogo-pin figure is the strongest novelty hook and requires no new analysis — just a plot of pre-bypass log0303 RAW vs ENV with correlation overlay, plus filtered-RAW timeseries showing the flatline.

**Deliberately deferred to journal extension:**
- Fig 5 (`abs_us` stitching diagram + ground-truth validation against `host_rx_ms`)
- Fig 6 (Chaquopy per-swing latency distribution)
- Fig 7 (multi-session field validation timeline)

---

## Tables (1 existing, 3 new)

| # | Table | Status | Notes |
|---|---|---|---|
| I | Hardware BOM | ✅ in draft (§ II.A) | May add cost column to make ~$99 explicit |
| II | Inter-sample interval statistics | ✅ in draft (§ VI.A) | — |
| III | IMU FSR history across firmware revisions | **TODO** | Show ±250 → ±1000 → ±2000 dps progression and saturation rationale |
| IV | Field validation metrics summary | **TODO** | Sessions, duration, swings, BLE reconnections, CRC errors, sample drops — in one table |

(Protocol-comparison table from [paper2_plan.md](paper2_plan.md) deliberately deferred to journal — adds bulk without strong reviewer payoff for ICPICS.)

---

## Deferred to journal extension

These pieces are intentionally NOT in the ICPICS scope. They become the ~30–50% new material for the journal version (target: MDPI Sensors or IEEE JBHI).

| Piece | What's needed |
|---|---|
| **Chaquopy dual-platform** | Per-swing latency benchmark on Android (distribution across log0305's 626 swings); MDF result agreement PC↔Android; cold-start cost; figure + table |
| **`abs_us` ground-truth validation** | Quantify reconstruction error vs. `host_rx_ms` for the BLE reconnection events recorded in the field session (count to be verified from runtime health logs — at minimum the 1 between-run reconnect visible in CSVs); derive accuracy bounds; comparison against device-clock-only and host-clock-only alternatives; Figure 5 |
| **Pogo-pin characterisation depth** | Beyond r=0.998 — quantify ghost amplitude vs. ENV amplitude; ADC-mux charge-sharing model; before/after standard deviation distributions |
| **Multi-session field validation timeline** | Frame count, CRC errors, reconnection events plotted over 150+ min — Figure 7 |
| **Expanded Discussion / Related Work** | Doubled depth; protocol comparison table; positioning vs. Cerone 2019 / Lynn 2018 / Yang 2024 |
| **Software analysis pipeline section** | Preprocessing, swing detection, baseline protection — but only the parts that aren't in Paper 1 |

See [paper2_plan.md](paper2_plan.md) for the broader (currently BSN-targeted) plan; that plan should be retargeted to MDPI Sensors after ICPICS is submitted.

---

## Word budget reconciliation

| Source | Words |
|---|---|
| Current draft total | 2431 |
| − § V.B Android subsection | −80 |
| − Abstract/conclusion Android phrase | −20 |
| − Tightening of intro contribution list | −150 |
| + Related Work (NEW) | +250 |
| + § VI expansion (PC pipeline + `abs_us` paragraph) | +270 |
| + § VII expansion (Table 4 prose) | +50 |
| + Discussion (NEW) | +250 |
| **Target total** | **~3000** |

3000 words + 4 figures + 4 tables ≈ 6 pages IEEE conference format.

---

## Next steps (action list)

1. [ ] **Polish pass on current draft** to align with revised structure:
   - Drop § V.B Android subsection
   - Drop Android phrase from Abstract
   - Tighten Intro contribution list to the 5 sharpened contributions above
2. [ ] **Add Related Work section (§ II)** — ~250 w, position vs. Cerone 2019, Lynn 2018, Yang 2024, Taborri 2020
3. [ ] **Expand § VI (Host Capture Pipeline)** to ~350 w with FrameParser, rotating CSV, watchdog/reconnect, `abs_us` paragraph, UDP mirror
4. [ ] **Add Discussion section (§ VIII)** — ~250 w on pogo-pin generalisability, `abs_us` portability, BLE-throughput limits, single-sport limitation
5. [ ] **Generate Figure 4** (pogo-pin ghost signal RAW vs ENV) from log0303 pre-bypass data
6. [ ] **Add Table III** (IMU FSR history) and **Table IV** (field validation metrics summary)
7. [ ] **Update [paper2_plan.md](paper2_plan.md)** to retarget journal extension from BSN → MDPI Sensors / IEEE JBHI
8. [ ] **Run pre-submission checks**: word count, IEEE format, figure resolution, reference completeness

---

## Honest novelty disclaimer (for self-review before submission)

The ICPICS paper as scoped is on the **modest** end of novelty:
- Several contributions (DMA ADC, dual-core split, basic watchdog) are well-established practice and will not earn credit on their own.
- The pogo-pin diagnosis is the genuinely novel piece — make sure it survives polishing prominently (in Intro contribution list, in § VII evaluation, and in Discussion).
- If reviewers push back on novelty, fall back to: (a) the *combination* into a field-validated 150-min/0-drop system, (b) the pogo-pin documentation as a practitioner contribution, (c) the self-describing FSR protocol surviving 3 firmware revisions as a deployed artefact.
- Acceptance probability is reasonable for ICPICS (broad scope, permissive bar). Less so for higher-tier conferences without the journal-extension additions.
