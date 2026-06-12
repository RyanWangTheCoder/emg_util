# Patent Worklog

---

## 2026-06-01 — Session 1: Pre-Filing Package Complete

### Goal
Complete all open pre-filing work items identified in `00_patent_plan.md` before the ICPICS and CNIB papers publish (~2026-07).

### Context
Two conference papers pending submission (ICPICS, CNIB). Content from these papers can appear in the patent — the risk is timing, not overlap. Filing the provisional before either paper publishes protects international rights. US grace period (1 year from own disclosure) applies after publication.

---

### Work Completed

#### 1. Public Disclosure Timeline (`02_public_disclosure_timeline.md`)
- Documented all known disclosure events: AAAS 2024 poster, ICPICS (pending), CNIB (pending), GitHub repo.
- **AAAS 2024 resolved as not relevant** — used Seeed sensor with no RAW output; RAW/ENV consistency checking could not have been disclosed.
- **GitHub confirmed private** — not a public disclosure; keep private until after filing.
- Per-paper disclosure analysis: CNIB has high overlap (IMU-conditioned validity, session-gap artifact, trustworthiness framing); ICPICS has partial overlap (pogo-pin diagnostic, paired RAW/ENV hardware); neither fully discloses the integrated RAW+ENV+IMU validity gate.
- **Filing deadline: before either paper publishes (~2026-07)**. Dates TBD — to be filled in when acceptance notices arrive.

#### 2. Figures 1–7 (`06_figures/`)
All seven figures drafted as ASCII/Markdown diagrams with captions and patent notes:

| File | Content |
|------|---------|
| `fig1_system_architecture.md` | Hardware block diagram: wearable → MCU → BLE → host quality evaluator → gated analytics |
| `fig2_method_flow.md` | Full method flowchart: acquire → preprocess → features → quality metrics → IMU context → continuity audit → classify (9 states) → act (8 actions) → output |
| `fig3_raw_env_consistency.md` | 5-case RAW/ENV diagnostic table + ratio timeline + amplitude scatter |
| `fig4_imu_decision_matrix.md` | IMU validity matrix + log0305 MDF timeline + contrast vs. conventional fusion |
| `fig5_baseline_gating.md` | 6-condition baseline gate flowchart + warmup-skip sensitivity chart (−2.6% / −26.2% / +28.1%) |
| `fig6_session_gap_audit.md` | log0303 gap timeline: 28.7% (artifact) vs. 4.9% (first segment only) |
| `fig7_ghost_signal_diagnostic.md` | Pogo-pin before/after: r=0.998 → r=−0.013 + three-condition detection flowchart |

Section 19 of `05_provisional_draft.md` updated to reference all seven files with inline summaries.

#### 3. Inventor / Contributor Matrix (`03_inventor_contribution_matrix.md`)
- **Sole inventor: Ryan Wang** (Westview High School).
- Larry Wang: hardware assembly, git, firmware support — implementation, not inventorship.
- Theodore (Teddy) Di: co-author (CNIB) — did not contribute to inventive concepts.
- Dr. YanMing Di: faculty advisor, statistical review — advisory role only.
- All four claim families (A–D) attributed to Ryan Wang.
- Action items: confirm OSU IP policy (Dr. Di advisory role), confirm Westview school IP policy, arrange guardian (Larry Wang) to sign USPTO oath/declaration as Ryan is a minor.

#### 4. Claim Concepts Expanded (`05_provisional_draft.md` §17)
Expanded from 5 draft concepts to **18 numbered claim concepts**:
- 3 independents: method (C1), system (C2), computer-readable medium (C3)
- 15 dependents (C4–C18) covering: action vocabulary, signal-quality metric enumeration, IMU context states, electrode settling, reduced-effort confound, ghost-channel detection, ENV saturation, quality-gated baseline selection, session continuity audit, raw-derived envelope computation, contact-quality metric, confidence score, user feedback/electrode prompt, real-time vs. offline, application domains.
- Section 18 restructured as a feature-area lookup table.

#### 5. Prior Art Search Notes (`04_prior_art_search_notes.md`)
- Catalogued all references from ICPICS and CNIB papers (15 references total).
- Risk assessment per claim family: all four families rated **Low–Low-Medium**.
- Closest threats: Farago 2023 (sEMG quality review), Joutsen 2024 (dry-electrode ECG quality), Bangaru 2022 (EMG/IMU fusion) — all differentiated clearly.
- Five strongest differentiators documented for attorney use.
- Five remaining search areas flagged for nonprovisional filing (not blocking for provisional).

#### 6. File Organization
All patent files moved into `patent/` subdirectory:

```
patent/
  00_patent_plan.md                       ← master action plan
  01_invention_disclosure.md              ← one-page invention disclosure
  02_public_disclosure_timeline.md        ← disclosure events and filing deadline
  03_inventor_contribution_matrix.md      ← sole inventor: Ryan Wang
  04_prior_art_search_notes.md            ← prior art by claim family
  05_provisional_draft.md                 ← full provisional specification
  05_provisional_draft.pdf               ← generated PDF (365 KB)
  07_filing_receipt.md                    ← fill in after filing: app number, date, deadlines
  deprecated_raw_env_imu_signal_quality.md
  worklog.md                              ← this file
  06_figures/
    fig1_system_architecture.md
    fig2_method_flow.md
    fig3_raw_env_consistency.md
    fig4_imu_decision_matrix.md
    fig5_baseline_gating.md
    fig6_session_gap_audit.md
    fig7_ghost_signal_diagnostic.md
```

#### 7. PDF Generation + PATH Config
- Added `fft-env/bin` to PATH in `.claude/settings.json` so `python` and `pandoc` are available by default in future sessions.
- Generated `05_provisional_draft.pdf` (365 KB) via pandoc HTML + Chrome headless (handles Unicode box-drawing characters in figures).
- Regeneration command:
  ```bash
  pandoc patent/05_provisional_draft.md -t html --standalone -o /tmp/draft.html && \
  google-chrome-stable --headless --disable-gpu --no-sandbox \
    --print-to-pdf=patent/05_provisional_draft.pdf --print-to-pdf-no-header /tmp/draft.html
  ```

---

### Remaining Pre-Filing Tasks

| Task | Owner | When |
|------|-------|------|
| Fill in ICPICS and CNIB publication dates in `02_public_disclosure_timeline.md` | Ryan/Larry | When acceptance notices arrive |
| Confirm OSU IP policy re: Dr. YanMing Di's advisory role | Larry | Before filing |
| Confirm Westview High School IP policy | Ryan/Larry | Before filing |
| Arrange guardian signature for USPTO oath/declaration | Larry | At filing time |
| Prior art formal search (5 categories in `04_prior_art_search_notes.md` §3) | Ryan | Before nonprovisional |
| Attorney review of provisional and inventorship | Counsel | Before filing |
| File provisional via USPTO Patent Center | Ryan/Larry + counsel | Before papers publish (~2026-07) |
| Record filing receipt, application number, 12-month deadline | Larry | At filing time |

---

*Session end: 2026-06-01*

---

## TODO

See `00_patent_plan.md §20` for the current filing checklist.
