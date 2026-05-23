#!/usr/bin/env python3
"""Assemble icpics_draft.docx from icpics_draft.md using icpics_Templates.docx (IEEE conf format).

IEEE conference template differs from SPLNPROC:
- Heading1 auto-numbers Roman (I, II, III), Heading2 auto-numbers Alpha (A, B, C)
- Figurecaption auto-numbers (Fig. 1, Fig. 2, ...)
- References auto-number ([1], [2], ...)
- Abstract / Keywords paragraphs use em-dash separator: 'Abstract—...' 'Keywords—...'
- Author blocks: Author paragraph (name) + 4 Affiliation paragraphs (dept, org/city, country, email)
- Body in TextBody style with first-line indent; 2-column layout
"""

import re
import sys
import zipfile
from pathlib import Path

import yaml
from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from PIL import Image, ImageDraw, ImageFont

ROOT = Path("/local/mnt/workspace/wangx/projects/emg_util")
TEMPLATE = ROOT / "icpics_Templates.docx"
SRC_MD = ROOT / "icpics_draft.md"
OUT_DOCX = ROOT / "icpics_draft.docx"


# ---------------------------------------------------------------------------
# Markdown frontmatter / inline parsing
# ---------------------------------------------------------------------------
def split_frontmatter(text: str):
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    fm = text[3:end].strip()
    body = text[end + 4 :].lstrip("\n")
    return yaml.safe_load(fm), body


def _unescape_md(text: str) -> str:
    r"""Strip markdown backslash-escapes for common special chars (\$, \*, \_, \\, etc.)."""
    return re.sub(r"\\([\\`*_{}\[\]()#+\-.!$])", r"\1", text)


def parse_inline(text: str):
    """Return list of (text, bold, italic, code, sub, sup) runs.
    Handles **bold**, *italic*, `code`, <sub>x</sub>, <sup>x</sup>, and unescapes
    backslash-escaped markdown specials (\\$, \\*, etc.) inside each run."""
    runs = []
    pattern = re.compile(
        r"(\*\*[^*]+\*\*)"          # 1: bold
        r"|(\*[^*]+\*)"              # 2: italic
        r"|(`[^`]+`)"                # 3: code
        r"|(<sub>[^<]+</sub>)"      # 4: subscript
        r"|(<sup>[^<]+</sup>)"      # 5: superscript
    )
    pos = 0
    for m in pattern.finditer(text):
        if m.start() > pos:
            runs.append((_unescape_md(text[pos:m.start()]), False, False, False, False, False))
        if m.group(1):
            runs.append((_unescape_md(m.group(1)[2:-2]), True, False, False, False, False))
        elif m.group(2):
            runs.append((_unescape_md(m.group(2)[1:-1]), False, True, False, False, False))
        elif m.group(3):
            runs.append((_unescape_md(m.group(3)[1:-1]), False, False, True, False, False))
        elif m.group(4):
            runs.append((_unescape_md(m.group(4)[5:-6]), False, False, False, True, False))
        elif m.group(5):
            runs.append((_unescape_md(m.group(5)[5:-6]), False, False, False, False, True))
        pos = m.end()
    if pos < len(text):
        runs.append((_unescape_md(text[pos:]), False, False, False, False, False))
    return runs


# ---------------------------------------------------------------------------
# DocX helpers
# ---------------------------------------------------------------------------
def clear_body(doc):
    body = doc.element.body
    for child in list(body):
        if child.tag in (qn("w:p"), qn("w:tbl")):
            body.remove(child)


def _apply_runs(paragraph, runs, header_bold=False):
    """Apply parsed runs to a paragraph. header_bold forces bold on every run
    (for table header cells)."""
    for tup in runs:
        # Tolerate both 4-field (legacy) and 6-field run tuples.
        text, bold, italic, code = tup[:4]
        sub = tup[4] if len(tup) > 4 else False
        sup = tup[5] if len(tup) > 5 else False
        r = paragraph.add_run(text)
        if bold or header_bold:
            r.bold = True
        # Treat inline `code` as italic (IEEE convention for inline variable names
        # and short identifiers in body text). Avoids "weird" monospace appearance.
        if italic or code:
            r.italic = True
        if sub:
            r.font.subscript = True
        if sup:
            r.font.superscript = True


def add_paragraph_styled(doc, style_name: str, runs=None, alignment=None):
    p = doc.add_paragraph()
    try:
        p.style = doc.styles[style_name]
    except KeyError:
        p.style = doc.styles["Normal"]
    if alignment is not None:
        p.alignment = alignment
    if runs:
        _apply_runs(p, runs)
    return p


def set_pic_alt_text(picture_run_element, alt_text: str, title: str = ""):
    drawing = picture_run_element.find(qn("w:drawing"))
    if drawing is None:
        return
    inline = None
    for child in drawing:
        if child.tag.endswith("}inline") or child.tag.endswith("}anchor"):
            inline = child
            break
    if inline is None:
        return
    docPr = None
    for child in inline:
        if child.tag.endswith("}docPr"):
            docPr = child
            break
    if docPr is None:
        return
    docPr.set("descr", alt_text)
    if title:
        docPr.set("title", title)


def add_image_paragraph(doc, img_path: Path, alt_text: str, width_in: float = 3.0):
    """Centered image, IEEE 2-column ≈ 3.3 inch column width; 3.0" leaves margin.
    Override width_in for compact figures (e.g., 2.5\")."""
    p = doc.add_paragraph()
    try:
        p.style = doc.styles["image"]
    except KeyError:
        p.style = doc.styles["Normal"]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(str(img_path), width=Inches(width_in))
    set_pic_alt_text(run.element, alt_text, title=alt_text[:80])
    return p


def _add_table_borders(tbl_element):
    tblPr = tbl_element.find(qn("w:tblPr"))
    if tblPr is None:
        tblPr = OxmlElement("w:tblPr")
        tbl_element.insert(0, tblPr)
    existing = tblPr.find(qn("w:tblBorders"))
    if existing is not None:
        tblPr.remove(existing)
    tblBorders = OxmlElement("w:tblBorders")
    for name in ("top", "left", "bottom", "right", "insideH", "insideV"):
        b = OxmlElement(f"w:{name}")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "4")
        b.set(qn("w:space"), "0")
        b.set(qn("w:color"), "000000")
        tblBorders.append(b)
    tblPr.append(tblBorders)


def add_table(doc, header_row, data_rows):
    """Insert a Word table with bold header (Tablecolhead) + body (TableContents)."""
    cols = len(header_row)
    table = doc.add_table(rows=1 + len(data_rows), cols=cols)
    _add_table_borders(table._tbl)
    table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    table.autofit = True

    for j, cell_text in enumerate(header_row):
        cell = table.rows[0].cells[j]
        cell.text = ""
        p = cell.paragraphs[0]
        try:
            p.style = doc.styles["Tablecolhead"]
        except KeyError:
            pass
        _apply_runs(p, parse_inline(cell_text.strip()), header_bold=True)

    for i, row in enumerate(data_rows):
        for j, cell_text in enumerate(row):
            cell = table.rows[1 + i].cells[j]
            cell.text = ""
            p = cell.paragraphs[0]
            try:
                p.style = doc.styles["TableContents"]
            except KeyError:
                pass
            _apply_runs(p, parse_inline(cell_text.strip()))

    return table


def parse_md_table(lines):
    rows = []
    for line in lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)
    if len(rows) < 2:
        return None
    header = rows[0]
    data = rows[2:]
    return header, data


# ---------------------------------------------------------------------------
# Author parsing — markdown lines like:
# **Ryan Wang** — Westview High School, San Diego, CA, USA
# ---------------------------------------------------------------------------
def parse_author_lines(text: str):
    """Find the author block immediately after the title. Returns list of dicts:
    [{'name': ..., 'dept': '', 'org': ..., 'city_country': ..., 'email': ...}]
    """
    authors = []
    line_re = re.compile(r"^\s*\*\*([^*]+)\*\*\s*[—–-]\s*(.+?)\s*$")
    for line in text.split("\n"):
        m = line_re.match(line)
        if m:
            name = m.group(1).strip()
            rest = m.group(2).strip()
            # Heuristic: split affiliation by commas
            # "Westview High School, San Diego, CA, USA"
            # → org='Westview High School', city='San Diego, CA', country='USA'
            parts = [p.strip() for p in rest.split(",")]
            if len(parts) >= 3:
                org = parts[0]
                country = parts[-1]
                city_country = ", ".join(parts[1:])
            elif len(parts) == 2:
                org, city_country = parts[0], parts[1]
                country = parts[1]
            else:
                org = rest
                city_country = ""
                country = ""
            # Department prefix: match "Professor, Department of Statistics" pattern
            dept = ""
            if parts[0].lower().startswith(("professor", "department", "dept")):
                dept = parts[0]
                org = parts[1] if len(parts) > 1 else ""
                city_country = ", ".join(parts[2:]) if len(parts) > 2 else ""
            authors.append({
                "name": name,
                "dept": dept,
                "org": org,
                "city_country": city_country,
            })
    return authors


# ---------------------------------------------------------------------------
# Body parsing
# ---------------------------------------------------------------------------
def parse_body(doc, body: str, fig_paths: dict, fig_index: dict):
    lines = body.split("\n")
    i = 0
    after_heading = False
    in_references = False
    while i < len(lines):
        line = lines[i]

        if line.strip() == "":
            i += 1
            continue

        # Fenced code block: ``` ... ``` — skip entirely. Inline code is preferred
        # (rendered as italic in IEEE style); long code blocks aren't appropriate
        # for a 6-page IEEE paper anyway.
        if line.lstrip().startswith("```"):
            i += 1
            while i < len(lines) and not lines[i].lstrip().startswith("```"):
                i += 1
            i += 1  # skip closing fence
            continue

        # H1: ## Heading
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m and not line.startswith("###"):
            heading = m.group(1)
            in_references = heading.lower().startswith("references")
            # Strip auto-Roman prefix "I. " / "II. " etc.
            heading_clean = re.sub(r"^[IVX]+\.\s+", "", heading)
            # Also handle "References" + "Abstract"/"Keywords" which we render specially
            if heading.lower() == "abstract" or heading.lower() == "keywords":
                # Skip — handled separately by the caller (frontmatter abstract/keywords)
                i += 1
                continue
            add_paragraph_styled(doc, "Heading1", runs=parse_inline(heading_clean))
            after_heading = True
            i += 1
            continue

        # H2: ### Heading
        m = re.match(r"^###\s+(.+?)\s*$", line)
        if m:
            text = m.group(1)
            # Strip auto-Alpha prefix "A. " / "B. " etc.
            text = re.sub(r"^[A-Z]\.\s+", "", text)
            add_paragraph_styled(doc, "Heading2", runs=parse_inline(text))
            after_heading = True
            i += 1
            continue

        # H3: #### Heading
        m = re.match(r"^####\s+(.+?)\s*$", line)
        if m:
            add_paragraph_styled(doc, "Heading3", runs=parse_inline(m.group(1)))
            after_heading = True
            i += 1
            continue

        # Figure
        m = re.match(r"^!\[([^\]]+)\]\(([^)]+)\)\s*$", line)
        if m:
            caption = m.group(1)
            md_path = m.group(2)
            img_path = ROOT / md_path
            if not img_path.exists():
                print(f"WARN: figure not found: {img_path}", file=sys.stderr)
                i += 1
                continue
            # Strip "Fig. N. " auto-num prefix
            cap_rest = caption
            mfig = re.match(r"^Fig\.?\s*\d+\.?\s*(.+)$", caption, re.DOTALL)
            if mfig:
                cap_rest = mfig.group(1)
            alt = re.sub(r"\s+", " ", cap_rest).strip()
            # Per-figure width: emg-imu sync figure is wide-aspect; narrower fits column.
            fig_width = 2.7 if "emg_imu_sync" in img_path.name else 3.0
            add_image_paragraph(doc, img_path, alt_text=alt, width_in=fig_width)
            # Caption — Figurecaption auto-numbers, so just emit cap_rest
            p = doc.add_paragraph()
            p.style = doc.styles["Figurecaption"]
            _apply_runs(p, parse_inline(cap_rest))
            after_heading = False
            i += 1
            continue

        # Table block
        if line.lstrip().startswith("|"):
            tbl_lines = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                tbl_lines.append(lines[i])
                i += 1
            res = parse_md_table(tbl_lines)
            if res:
                add_table(doc, res[0], res[1])
            after_heading = False
            continue

        # Standalone "**Table N.** caption" before a table → emit as Caption style
        m = re.match(r"^\*\*Table\s*([IVX0-9]+)\.\*\*\s*(.+?)\s*$", line)
        if m:
            n = m.group(1)
            cap = m.group(2)
            p = doc.add_paragraph()
            try:
                p.style = doc.styles["Caption"]
            except KeyError:
                p.style = doc.styles["Normal"]
            bold = p.add_run(f"Table {n}. ")
            bold.bold = True
            _apply_runs(p, parse_inline(cap))
            after_heading = False
            i += 1
            continue

        # Reference list item
        m = re.match(r"^(\d+)\.\s+(.+)$", line)
        if m and in_references:
            text = m.group(2)
            while i + 1 < len(lines) and lines[i + 1].strip() and not re.match(r"^(\d+)\.\s+", lines[i + 1]) and not lines[i + 1].startswith(("#", "!", "|")):
                text += " " + lines[i + 1].strip()
                i += 1
            p = doc.add_paragraph()
            try:
                p.style = doc.styles["References"]
            except KeyError:
                p.style = doc.styles["Normal"]
            _apply_runs(p, parse_inline(text))
            i += 1
            continue

        # Skip yaml-like author lines (already handled in title block)
        if re.match(r"^\*\*[^*]+\*\*\s*[—–-]\s*", line):
            i += 1
            continue

        # Skip date line like "*2026*" or just "*Year*"
        if re.match(r"^\*\d{4}\*\s*$", line):
            i += 1
            continue

        # Regular paragraph
        para_lines = [line]
        i += 1
        while i < len(lines):
            nxt = lines[i]
            if nxt.strip() == "":
                break
            if nxt.startswith(("#", "!", "|", "**Table")):
                break
            if re.match(r"^\d+\.\s+", nxt) and in_references:
                break
            if re.match(r"^\*\*[^*]+\*\*\s*[—–-]\s*", nxt):  # author line
                break
            para_lines.append(nxt)
            i += 1
        joined = " ".join(l.strip() for l in para_lines)
        joined = re.sub(r"\s+", " ", joined)
        add_paragraph_styled(doc, "TextBody", runs=parse_inline(joined))
        after_heading = False


# ---------------------------------------------------------------------------
# Main build
# ---------------------------------------------------------------------------
def build():
    text = SRC_MD.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)

    # Markdown title is "# Title" since there's no frontmatter title — locate it
    title_m = re.search(r"^#\s+(.+?)\s*$", body, re.MULTILINE)
    if not title_m:
        sys.exit("No '# Title' line found in markdown body")
    title = title_m.group(1)

    # Author block: lines like '**Name** — affiliation' immediately after title
    authors = parse_author_lines(body)

    # Find Abstract section
    abs_match = re.search(r"^##\s+Abstract\s*\n+(.+?)(?=\n##\s)", body, re.DOTALL | re.MULTILINE)
    abstract_text = abs_match.group(1).strip() if abs_match else ""
    abstract_text = re.sub(r"\s+", " ", abstract_text)

    # Keywords from frontmatter or default
    kw = fm.get("keywords")
    if isinstance(kw, list):
        kw_text = "; ".join(kw)
    elif isinstance(kw, str):
        kw_text = kw
    else:
        kw_text = ""

    # Strip the title, author block, *date*, Abstract section from body before parse_body
    body_after_title = body[title_m.end():]
    # Drop lines: author-format lines + the *2026* date line
    lines = body_after_title.split("\n")
    cleaned = []
    skip_until_section = True
    for line in lines:
        stripped = line.strip()
        if skip_until_section:
            if stripped.startswith("##"):
                skip_until_section = False
                cleaned.append(line)
            # else skip everything before first ##
            continue
        cleaned.append(line)
    body_clean = "\n".join(cleaned)
    # Drop the Abstract section (from "## Abstract" up to the next "## ")
    body_clean = re.sub(
        r"^##\s+Abstract\s*\n.+?(?=\n##\s)",
        "",
        body_clean,
        count=1,
        flags=re.DOTALL | re.MULTILINE,
    )

    # Open template, clear body
    doc = Document(str(TEMPLATE))
    clear_body(doc)

    # ---- Title ----
    add_paragraph_styled(doc, "Papertitle", runs=parse_inline(title))

    # ---- Authors ----
    # IEEE conf format: each author = Author paragraph (name) followed by
    # 4 Affiliation paragraphs (dept, org, city/country, email).
    for a in authors:
        add_paragraph_styled(doc, "Author", runs=[(a["name"], False, False, False)])
        # dept (optional)
        if a.get("dept"):
            add_paragraph_styled(doc, "Affiliation", runs=[(a["dept"], False, False, False)])
        # org
        if a.get("org"):
            add_paragraph_styled(doc, "Affiliation", runs=[(a["org"], False, False, False)])
        # city/country
        if a.get("city_country"):
            add_paragraph_styled(doc, "Affiliation", runs=[(a["city_country"], False, False, False)])
        # email
        if a.get("email"):
            add_paragraph_styled(doc, "Affiliation", runs=[(a["email"], False, False, False)])

    # ---- Abstract ----
    p = doc.add_paragraph()
    try:
        p.style = doc.styles["Abstract"]
    except KeyError:
        p.style = doc.styles["Normal"]
    bi = p.add_run("Abstract—")
    bi.bold = True
    bi.italic = True
    _apply_runs(p, parse_inline(abstract_text))

    # ---- Keywords ----
    if kw_text:
        p = doc.add_paragraph()
        try:
            p.style = doc.styles["Keywords"]
        except KeyError:
            p.style = doc.styles["Normal"]
        bi = p.add_run("Keywords—")
        bi.bold = True
        bi.italic = True
        p.add_run(kw_text)

    # ---- Body sections ----
    parse_body(doc, body_clean, {}, {})

    OUT_DOCX.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUT_DOCX))
    print(f"Saved: {OUT_DOCX}")


if __name__ == "__main__":
    build()
