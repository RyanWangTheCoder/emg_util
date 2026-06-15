# ML/ Worklog

---

## 2026-06-14 — paper3_plan.md final review pass + CAST submission creation

### Session summary

Two parallel tracks today: (1) multi-round review and editing of `paper3_plan.md` to reach
canonical master-plan status, and (2) creation of the CAST Global Youth Innovation Summit
submission (`cast_submission.md` → PDF + docx).

---

### paper3_plan.md — changes made

All edits were review-driven (reviewer: Xiaodong Wang via Copilot/SharePoint comments).

**Round 1 edits**
- Stage 1 heading: `weeks 4–15` → `weeks 4–12` (matches canonical timeline table)
- Strawman outline item 7: removed LSTM; now "elastic net/ridge primary + RF/gradient boosting exploratory"
- Layer 1 aggregate variable rename: `fatigue_depth` → `late_session_load_depth`, `fatigue_slope` → `load_proxy_slope`
- Event label definitions reconciled across 4 locations — replaced `soreness_risk_proxy` with three canonical binary flags:
  - `soreness_escalation_event`: next_morning_forearm_soreness ≥4 OR soreness increase ≥2 from rolling baseline
  - `readiness_decline_event`: next_session_forearm_readiness ≤2 OR readiness drop ≥1 from rolling baseline
  - `load_intolerance_proxy_event`: soreness_escalation_event OR readiness_decline_event OR unusual pain
- Contribution #3: softened self-report "accepted standard" claim; session-RPE = Foster 2001 standard; forearm RPE + next-morning soreness = "localized endpoints for this N-of-1 design"
- Session count: literature table and differentiation table → "40 valid min / 60 valid target / 80 valid stretch"
- Must-do list: `40–80 session collection` → canonical wording
- `model_ready_sessions.csv` spec: added `source_quality_status` field for auditability
- `swing_features.csv`: `fatigue_score_proxy` → `load_score_proxy` (full consistency with load_* naming)
- Layer 1 language list: `fatigue_score_proxy` → `load_score_proxy`

**Round 2 edits**
- Phase 1 action items heading: `weeks 4–15` → `weeks 4–12`
- Phase 2 data collection subsection: `weeks 13–26+` → `weeks 16–30+`
- Stage 2 short summary: `40–80 sessions` → canonical; `N=40` → `N=40 valid usable sessions`
- Proposed Paper Outline: `40–80 sessions protocol` → canonical wording

**Round 3 edits (final)**
- Journal version: `40–80 longitudinal sessions` → canonical min/target/stretch
- "What paper does NOT claim": `N=40–80` → canonical min/target/stretch
- Stage 2 summary: added setup sentence ("Stage 2 setup weeks 13–15; collection begins week 16")

**Final verdict from reviewer:** `paper3_plan.md` is now the canonical master plan — no further
revisions needed. Next action: lock Stage 0 definitions, implement session/label/QC file schema,
begin pilot sessions.

---

### task_cast.md — changes made

- Track corrected: `AI / Healthcare & Biotechnology` → `AI / Robotics` (two occurrences)
- Student and mentor names filled in: Ryan Wang / Xiaodong Wang

---

### CAST submission files created

**`cast_submission.md`** — standalone clean submission document (no planning wrapper):
- Extracted from `task_cast.md` draft content
- ICM-20948 (not LSM6DS3) confirmed as current hardware
- Three figures embedded from existing figure directories:
  - Fig 1: `../icpics_figures/fig_system_architecture.png` — system architecture
  - Fig 2: `../paper_figures/fig2_electrode_settling.png` — MDF three-phase trajectory
  - Fig 3: `../paper_figures/fig13_swing_intensity_stratification.png` — per-swing MDF vs. time by intensity
- Layer 1 language updated to match paper3_plan.md discipline (load_score_proxy, not fatigue classifier)
- All 5 references included (Foster 2001, Merletti 2004, Gabbett 2016, Rota 2014, Phinyomark 2018)
- Section 2, 3, 6 trimmed to fit 8-page limit at 1.5 line spacing

---

### Regenerating cast_submission.pdf

Requirements: `pandoc`, `xelatex`, Times New Roman font (`ttf-mscorefonts-installer`).

**Install Times New Roman (one-time, requires sudo):**
```bash
sudo apt-get install ttf-mscorefonts-installer
sudo fc-cache -f -v
# verify:
fc-list | grep -i "times new roman"
```

**Generate PDF** (run from `ML/` directory):
```bash
cd /path/to/emg_util/ML

pandoc cast_submission.md -o cast_submission.pdf \
  --pdf-engine=xelatex \
  -V mainfont="Times New Roman" \
  -V fontsize=12pt \
  -V geometry="margin=1in" \
  -V linestretch=1.5 \
  -V colorlinks=true \
  --lua-filter=<(cat << 'EOF'
function Image(el)
  if string.find(el.src, "fig2_electrode") then
    el.attributes['width'] = '55%'
    el.attributes['height'] = '2.8in'
  elseif string.find(el.src, "fig_system") then
    el.attributes['width'] = '85%'
  else
    el.attributes['width'] = '70%'
  end
  return el
end
EOF
)
```

Result: 8 pages, Times New Roman 12pt, 1-inch margins, 1.5 line spacing.
Fig 1 (system arch) at 85%, Fig 2 (MDF trajectory) height-capped to fit, Fig 3 not included.

**Generate docx** (backup; manual font/spacing formatting needed in Word):
```bash
pandoc cast_submission.md -o cast_submission.docx \
  --lua-filter=<(cat << 'EOF'
function Image(el)
  if string.find(el.src, "fig2_electrode") then
    el.attributes['width'] = '55%'
    el.attributes['height'] = '2.8in'
  elseif string.find(el.src, "fig_system") then
    el.attributes['width'] = '85%'
  else
    el.attributes['width'] = '70%'
  end
  return el
end
EOF
)
```

**Note on image paths:** the `![](../paper_figures/...)` paths in `cast_submission.md` are relative
to the `ML/` directory. Always run pandoc from `ML/` or the images will not resolve.

---

### CAST competition details

- **Competition:** CAST Global Youth Innovation & Entrepreneurship Summit
- **Track:** Track A — Research & Innovation (AI / Robotics)
- **Division:** Senior Division (15–18)
- **Student:** Ryan Wang | **Mentor:** Xiaodong Wang
- **Project title:** SmartArmor: A Wearable AI System for Personalized Fatigue Monitoring and Overuse Injury Prevention in Youth Tennis Players
- **Application deadline:** June 1, 2026
- **Western Regional:** July 11, 2026, Irvine CA (5-min pitch + Q&A; bring printed poster if possible)
- **Registration fee:** $80 early bird / $100 regular

---

### Files in ML/ after this session

| File | Description |
|---|---|
| `paper3_plan.md` | Canonical master research plan (finalized) |
| `task_cast.md` | CAST competition planning doc + strategy notes + submission checklist |
| `cast_submission.md` | Clean CAST submission source (edit this, regenerate PDF/docx) |
| `cast_submission.pdf` | Submission-ready PDF (8 pages, Times New Roman 12pt) |
| `cast_submission.docx` | Backup docx (requires manual font/spacing in Word) |
| `RESEARCH_ROADMAP.md` | Earlier N=20 attention-fusion roadmap (superseded by paper3_plan.md for Paper 3) |
| `ML_FATIGUE_CLASSIFICATION.md` | Layer 1 RF per-swing design details |
| `ML_FATIGUE_CLASSIFICATION_PART2.md` | Layer 1 RF continued |
