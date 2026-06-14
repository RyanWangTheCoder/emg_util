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
- Generated `05_provisional_draft.pdf` (149 KB, 25 pages) via pandoc HTML + wkhtmltopdf — correctly renders fenced code blocks as multiline preformatted text.
- Regeneration command:
  ```bash
  # Step 1: strip admin section and renumber (run from emg_util/)
  python3 -c "
  import re
  with open('patent/05_provisional_draft.md') as f: content = f.read()
  content = re.sub(r'\n## 24\. ADMINISTRATIVE NOTES.*?(?=\n## \d+\.)', '', content, flags=re.DOTALL)
  lines = content.split('\n')
  hl = [(i, re.match(r'^## \d+\. (.+)', l).group(1)) for i,l in enumerate(lines) if re.match(r'^## \d+\.', l)]
  for seq,(idx,title) in enumerate(hl, 1): lines[idx] = f'## {seq}. {title}'
  open('/tmp/05_filing.md','w').write('\n'.join(lines))
  "

  # Step 2: pandoc → HTML with inline CSS
  pandoc /tmp/05_filing.md -t html --standalone \
    -V 'header-includes=<style>pre{white-space:pre;font-family:monospace;font-size:9pt;background:#f4f4f4;border:1px solid #ccc;padding:0.6em;page-break-inside:avoid}table{border-collapse:collapse;width:100%}th,td{border:1px solid #aaa;padding:0.3em 0.5em}</style>' \
    -o /tmp/draft_filing.html

  # Step 3: wkhtmltopdf -> PDF (raw)
  /local/mnt/workspace/wangx/miniconda3/envs/fft-env/bin/wkhtmltopdf \
    --page-size Letter \
    --margin-top 20mm --margin-bottom 20mm \
    --margin-left 20mm --margin-right 20mm \
    --no-header-line --no-footer-line \
    --encoding utf-8 \
    /tmp/draft_filing.html \
    /tmp/05_filing_raw.pdf

  # Step 4: Ghostscript -> embed all fonts (required by USPTO)
  gs -dBATCH -dNOPAUSE -dNOSAFER \
     -sDEVICE=pdfwrite \
     -dCompatibilityLevel=1.4 \
     -dPDFSETTINGS=/prepress \
     -dEmbedAllFonts=true \
     -dSubsetFonts=true \
     -dCompressFonts=true \
     -sOutputFile=patent/05_provisional_draft.pdf \
     /tmp/05_filing_raw.pdf

  # Verify: all fonts should show emb=yes sub=yes
  pdffonts patent/05_provisional_draft.pdf
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

---

## 2026-06-12 — Session 2: Filing-Ready Package

### Changes from pre-filing review

1. **OSU / Westview IP items closed** — both resolved as no-claim; removed from critical path
2. **07_filing_receipt.md created** — placeholder for application number, filing date, deadline
3. **Cover sheet fields drafted** — ready to paste into USPTO Patent Center
4. **Section 23 (stale TODO)** → converted to "Drafting Status" with completed/remaining checklist
5. **Minor-inventor language** → neutralized to "confirm with USPTO instructions"
6. **Representative thresholds added** — saturation (95% ADC, 10%/20% flags), flatline (1% variance), IMU artifact (300 deg/s, 3g, 50 m/s³), ghost-channel (r>0.95), session gap (60s), confidence score (5-factor weighted formula)
7. **"simultaneously" → "concurrently / time-aligned / common monitoring interval"** — in field section, C1, C2 system concept, attorney summary
8. **Definitions section added** (new §3) — RAW, ENV, IMU context, trustworthiness state as non-limiting terms
9. **Session-continuity variation broadened** — beyond BLE to wired, file-boundary, timestamp reset, device reset, etc.
10. **Section 24 (admin notes)** → marked internal-only in Markdown; stripped from filing PDF
11. **Larry Wang employer IP** → upgraded to "Checkpoint for counsel"
12. **Section numbering fixed** — top-level sections renumbered 1–26 (no duplicates); all subsections updated to match parent section numbers
13. **Field grammar fixed** — "using concurrently acquired or time-aligned data streams"
14. **§22 prior-art** → "concurrent, time-aligned, or common-interval" aligned with claim language
15. **PDF renderer switched** — Chrome headless → wkhtmltopdf 0.12.4 (correct pre/code block rendering)
16. **Unicode → ASCII** — em-dashes, arrows, box-drawing, minus signs replaced for clean PDF encoding

### Filing-ready status (as of 2026-06-12, end of session)

**Technical disclosure: GREEN.** Reviewed through multiple passes; all substantive issues resolved.

| Item | Status |
|---|---|
| Core invention story | Complete |
| Claim concepts C1–C18 | Complete |
| Definitions section | Complete |
| Representative thresholds | Complete |
| Figures 1–7 | **Complete — full diagrams embedded in §20** |
| Experimental examples | Complete |
| Prior-art positioning | Complete |
| PDF rendering | Clean — 35 pages, 205 KB, wkhtmltopdf |
| Section numbering | Fixed — no duplicates |
| Encoding artifacts | None visible |

---

### PDF Iteration History (what we tried and why it failed)

This took multiple passes. Documented here so future sessions don't repeat the same dead ends.

#### Attempt 1 — Chrome headless, default flags
- **Command:** `google-chrome-stable --headless --print-to-pdf=... /tmp/draft.html`
- **Problems:**
  - Browser print header/footer leaked into PDF: date (`6/12/26, 11:54 AM`), filename (`05_provisional_draft`), URL (`file:///tmp/draft.html`), and page counter (`1/26`) visible on every page.
  - Fenced code blocks collapsed into single inline paragraphs — all line breaks stripped.
  - Tables split across pages with no repeated headers.
- **Root cause:** Chrome headless `--print-to-pdf` has limited CSS `@media print` support; `white-space: pre` in code blocks was not honored.

#### Attempt 2 — Chrome headless with `--print-to-pdf-no-header` flag
- **Command:** added `--print-to-pdf-no-header --no-pdf-header-footer`
- **Problems:**
  - Header/footer partially suppressed but some artifacts remained.
  - Code blocks still collapsed inline — CSS `pre` rules not applied.
- **Root cause:** `--print-to-pdf-no-header` suppresses the browser's built-in header/footer bar but does not affect CSS-injected content; code block issue unrelated to headers.

#### Attempt 3 — Chrome headless with `--css` injected via pandoc stdin
- **Command:** `pandoc ... --css=/dev/stdin` piping CSS with `pre { white-space: pre-wrap !important; }`
- **Problems:**
  - `pdftotext` showed code blocks as multiline, suggesting fix worked — but the PDF reviewer reported equations still collapsed inline in the visual PDF.
  - Discrepancy between pdftotext extraction (looked OK) and actual rendered PDF (still collapsed).
- **Root cause:** Chrome's print rendering pipeline flattens `pre` content regardless of CSS `white-space` in some versions; pdftotext reads the underlying text stream which preserves newlines even if the visual layout collapses them.

#### Attempt 4 — Switch to wkhtmltopdf 0.12.4
- **Command:** `pandoc ... -t html --standalone -V 'header-includes=<style>pre{white-space:pre;...}</style>' -o /tmp/draft_filing.html && wkhtmltopdf --no-header-line --no-footer-line ... /tmp/draft_filing.html patent/05_provisional_draft.pdf`
- **Result:** Code blocks rendered correctly as multiline preformatted text. Tables stayed intact. No browser header/footer.
- **Remaining issue:** `pdftotext` showed `\x96` (Windows-1252 en-dash) and `\x92` (right-quote) glyphs — but these are font encoding artifacts in the text-extraction layer, not visible rendering problems. Confirmed by visual inspection.
- **Tool path:** `wkhtmltopdf` is at `/local/mnt/workspace/wangx/miniconda3/envs/fft-env/bin/wkhtmltopdf` (version 0.12.4 with patched Qt).

#### Attempt 5 — Unicode → ASCII cleanup + full figures embedded
- **Problem found:** `06_figures/` contained rich multi-diagram ASCII box figures for all 7 figures, but §20 of the spec only had brief one-line text stubs. Figures were effectively absent from the filing PDF.
- **Fix:** Embedded complete diagram content from all 7 figure files directly into §20 of the Markdown spec.
- **Unicode cleanup:** wkhtmltopdf 0.12.4 struggles with Unicode beyond basic Latin. Replaced all em-dashes, en-dashes, arrows (→←↓↑), box-drawing chars (─│┌┐└┘├┤┬┴┼═║╔╗╚╝), special symbols (≥≤±²³µ•·), and Unicode minus (U+2212) with ASCII equivalents before PDF generation.
- **Final PDF:** 35 pages, 205 KB. All 7 figures fully present with diagrams, captions, and patent notes.

#### Final PDF generation command (canonical)

```bash
# Run from /local/mnt/workspace/wangx/projects/emg_util/

# Step 1: build filing copy (strip §24 admin notes, renumber, ASCII-clean)
python3 scripts/build_filing_pdf.py   # or inline python — see session 2 transcript

# Step 2: pandoc -> HTML with inline CSS
pandoc /tmp/05_provisional_draft_filing.md -t html --standalone \
  -V 'header-includes=<style>
    body{font-family:Georgia,serif;font-size:11pt;max-width:7in;margin:auto}
    h1,h2,h3{font-family:Arial,sans-serif;page-break-after:avoid}
    pre{white-space:pre;font-family:"Courier New",monospace;font-size:8pt;
        background:#f4f4f4;border:1px solid #ccc;padding:0.5em;margin:0.8em 0;
        page-break-inside:avoid;line-height:1.3}
    code{font-family:"Courier New",monospace;font-size:9pt}
    table{border-collapse:collapse;width:100%;margin-bottom:1em;page-break-inside:avoid}
    th,td{border:1px solid #aaa;padding:0.25em 0.4em;font-size:9pt}
    tr{page-break-inside:avoid}thead{display:table-header-group}
    @page{margin:1in}
  </style>' \
  -o /tmp/draft_filing.html

# Step 3: wkhtmltopdf -> PDF
/local/mnt/workspace/wangx/miniconda3/envs/fft-env/bin/wkhtmltopdf \
  --page-size Letter \
  --margin-top 20mm --margin-bottom 20mm \
  --margin-left 20mm --margin-right 20mm \
  --no-header-line --no-footer-line \
  --encoding utf-8 \
  /tmp/draft_filing.html \
  patent/05_provisional_draft.pdf
```

#### Key lessons
1. **Chrome headless does not reliably honor `white-space: pre` in print mode** — use wkhtmltopdf for technical patent specs with code blocks.
2. **pdftotext is not a reliable visual proxy** — it reads text streams, not rendered layout. Always do a visual check.
3. **Unicode box-drawing chars break wkhtmltopdf 0.12.4** — always run a Unicode→ASCII pass before PDF generation.
4. **Figure source files must be embedded in the spec** — external file references are invisible in the filed PDF.

---

### Still open (not blocking filing)

| Task | Owner |
|---|---|
| **File via USPTO Patent Center using Larry's account** | Larry |
| Fill 07_filing_receipt.md immediately after filing | Larry |
| Update ICPICS/CNIB publication dates when known | Ryan/Larry |
| Employer IP checkpoint (Larry Wang) | Counsel |

### Minor inventor / ID.me finding (2026-06-12)

- Ryan attempted ID.me verification at USPTO Patent Center using US passport + SSN.
- **ID.me rejected — does not meet age requirement** (ID.me requires 18+).
- **Resolution: Larry files using his own Patent Center account.**
  - Larry creates/uses his USPTO.gov account (ID.me verified with his driver's license).
  - Ryan is listed as the **inventor** on the provisional cover sheet — this is what matters legally.
  - Larry is listed as the **correspondence contact**.
  - The account holder submitting the filing does not need to be the inventor for a provisional.
  - Oath/declaration is **not required for a provisional** — the age/guardian issue only arises at nonprovisional stage, by which time counsel will be involved.
- This is standard practice and does not affect Ryan's inventorship or patent rights.

*Session end: 2026-06-12*
