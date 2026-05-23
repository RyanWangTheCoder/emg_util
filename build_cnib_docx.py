#!/usr/bin/env python3
"""Assemble paper_cnib.docx from paper_cnib.md using splnproc1703_mac.docm template.

Applies CNIB/SPLNPROC custom paragraph styles (papertitle, author, address, abstract,
keywords, heading1, heading2, p1a, figurecaption, tablecaption, referenceitem) and
inserts figures with Alt-Text. Tables are real Word table objects.
"""

import os
import re
import shutil
import sys
import zipfile
from copy import deepcopy
from pathlib import Path

import yaml
from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_ROW_HEIGHT_RULE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from PIL import Image, ImageDraw, ImageFont

ROOT = Path("/local/mnt/workspace/wangx/projects/emg_util")
TEMPLATE = ROOT / "splnproc1703_mac.docm"
TEMPLATE_DOCX = ROOT / ".splnproc_clean.docx"  # macro-stripped working copy
SRC_MD = ROOT / "paper_cnib.md"
TIF_DIR = ROOT / "paper_figures_tif"
OUT_DOCX = ROOT / "paper_cnib.docx"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def strip_macros_to_docx(docm_path: Path, docx_path: Path) -> None:
    """Copy a .docm to .docx by stripping macro/customUI parts and rewriting content types."""
    DROP_PARTS = {"word/vbaProject.bin", "word/vbaData.xml"}

    with zipfile.ZipFile(docm_path, "r") as zin:
        names = zin.namelist()
        with zipfile.ZipFile(docx_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for name in names:
                if name in DROP_PARTS:
                    continue
                if name.startswith("customUI/"):
                    continue
                data = zin.read(name)

                if name == "[Content_Types].xml":
                    s = data.decode("utf-8")
                    # Switch document content type to .docx and drop macro types
                    s = s.replace(
                        "application/vnd.ms-word.document.macroEnabled.main+xml",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml",
                    )
                    s = re.sub(r"<Override[^/]*vbaProject[^/]*/>", "", s)
                    s = re.sub(r"<Default[^/]*macroEnabled[^/]*/>", "", s)
                    s = re.sub(r"<Override[^/]*customUI[^/]*/>", "", s)
                    data = s.encode("utf-8")

                if name.endswith(".rels"):
                    s = data.decode("utf-8")
                    # Drop relationships pointing to vbaProject.bin or customUI/* targets.
                    # Use [^>] (not [^/]) so the regex stops at the Relationship tag end,
                    # not at any '/' inside Target paths.
                    s = re.sub(
                        r"<Relationship\s[^>]*Target=\"[^\"]*vbaProject\.bin\"[^>]*/>",
                        "",
                        s,
                    )
                    s = re.sub(
                        r"<Relationship\s[^>]*Target=\"customUI/[^\"]+\"[^>]*/>",
                        "",
                        s,
                    )
                    s = re.sub(
                        r"<Relationship\s[^>]*Target=\"\.\./customUI/[^\"]+\"[^>]*/>",
                        "",
                        s,
                    )
                    data = s.encode("utf-8")

                zout.writestr(name, data)


# ---------------------------------------------------------------------------
# Markdown parsing
# ---------------------------------------------------------------------------
def split_frontmatter(text: str):
    """Split YAML frontmatter from markdown body."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    fm = text[3:end].strip()
    body = text[end + 4 :].lstrip("\n")
    return yaml.safe_load(fm), body


def parse_inline(text: str):
    """Parse inline markdown into list of (text, bold, italic, code) runs."""
    # Order: handle bold-italic, bold, italic, code
    runs = []

    # We do a simple state machine over the text. Patterns:
    # **bold**, *italic*, `code`. Greedy non-overlapping.
    pattern = re.compile(
        r"(\*\*[^*]+\*\*)"          # bold
        r"|(\*[^*]+\*)"             # italic
        r"|(`[^`]+`)"                # code
    )
    pos = 0
    for m in pattern.finditer(text):
        if m.start() > pos:
            runs.append((text[pos:m.start()], False, False, False))
        if m.group(1):
            runs.append((m.group(1)[2:-2], True, False, False))
        elif m.group(2):
            runs.append((m.group(2)[1:-1], False, True, False))
        elif m.group(3):
            runs.append((m.group(3)[1:-1], False, False, True))
        pos = m.end()
    if pos < len(text):
        runs.append((text[pos:], False, False, False))
    return runs


# ---------------------------------------------------------------------------
# DocX helpers
# ---------------------------------------------------------------------------
def clear_body(doc):
    """Remove all paragraphs/tables from the body but keep sectPr."""
    body = doc.element.body
    for child in list(body):
        if child.tag == qn("w:p") or child.tag == qn("w:tbl"):
            body.remove(child)


def set_pic_alt_text(picture_run_element, alt_text: str, title: str = ""):
    """Set Alt-Text (descr) and title on an inserted picture's drawing element."""
    drawing = picture_run_element.find(qn("w:drawing"))
    if drawing is None:
        return
    inline = None
    # Try inline first, then anchor; both can hold a docPr
    for child in drawing:
        tag = child.tag
        if tag.endswith("}inline") or tag.endswith("}anchor"):
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


def add_paragraph_styled(doc, style_name: str, runs=None, alignment=None):
    """Add paragraph with specified style + optional list of (text, bold, italic, code) runs."""
    p = doc.add_paragraph()
    p.style = doc.styles[style_name]
    if alignment is not None:
        p.alignment = alignment
    if runs:
        for text, bold, italic, code in runs:
            r = p.add_run(text)
            if bold:
                r.bold = True
            if italic:
                r.italic = True
            if code:
                # Inline code: use Courier; SPLNPROC has no inline code style, use mono font
                r.font.name = "Courier New"
    return p


def add_image_paragraph(doc, img_path: Path, alt_text: str, width_in: float = 6.0):
    """Insert centered image with given Alt-Text."""
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


# ---------------------------------------------------------------------------
# Body assembly
# ---------------------------------------------------------------------------
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


def add_table(doc, header_row, data_rows, caption_runs):
    """Insert tablecaption then a real Word table with bold header row."""
    if caption_runs:
        add_paragraph_styled(doc, "tablecaption", runs=caption_runs)

    cols = len(header_row)
    table = doc.add_table(rows=1 + len(data_rows), cols=cols)
    _add_table_borders(table._tbl)
    table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    table.autofit = True

    for j, cell_text in enumerate(header_row):
        cell = table.rows[0].cells[j]
        cell.text = ""
        p = cell.paragraphs[0]
        for text, bold, italic, code in parse_inline(cell_text.strip()):
            r = p.add_run(text)
            r.bold = True
            if italic:
                r.italic = True

    for i, row in enumerate(data_rows):
        for j, cell_text in enumerate(row):
            cell = table.rows[1 + i].cells[j]
            cell.text = ""
            p = cell.paragraphs[0]
            for text, bold, italic, code in parse_inline(cell_text.strip()):
                r = p.add_run(text)
                if bold:
                    r.bold = True
                if italic:
                    r.italic = True

    return table


def parse_md_table(lines):
    """Parse a contiguous markdown table block into (header, data_rows). Lines include
    the pipe-table syntax (header | header | header) and align row."""
    rows = []
    for line in lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)
    if len(rows) < 2:
        return None
    header = rows[0]
    # rows[1] is align row, skip
    data = rows[2:]
    return header, data


# Map figure file basenames in markdown -> renamed Figure N TIFFs.
# The script will detect the order they appear and rename in sequence.
def discover_figure_order(body: str):
    """Return ordered list of (md_path, caption) in the order they appear."""
    figs = []
    pat = re.compile(r"!\[([^\]]+)\]\(([^)]+)\)", re.MULTILINE)
    for m in pat.finditer(body):
        figs.append((m.group(2), m.group(1)))
    return figs


# Panel-label overlay specs per source PNG. Each entry: list of (label, x_px, y_px).
# Coordinates are pixel positions of the top-left of each panel (above the plot).
PANEL_LABELS = {
    "fig2_electrode_settling.png": [
        ("A)", 30, 50),    # Panel 1: MDF over time at top
        ("B)", 30, 680),   # Panel 2: phase summary middle (gap between panels)
        ("C)", 30, 1145),  # Panel 3: IMU intensity (gap between panels)
    ],
    "fig4_warmup_skip_sensitivity.png": [
        ("A)", 30, 165),    # Below figure title, left panel
        ("B)", 1010, 165),  # Below figure title, right panel
    ],
}


def _load_label_font(size_px):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size_px)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def overlay_panel_labels(im: Image.Image, png_basename: str) -> Image.Image:
    """If the PNG has known multi-panel layout, draw 'A)', 'B)', 'C)' labels at top-left."""
    spec = PANEL_LABELS.get(png_basename)
    if not spec:
        return im
    if im.mode != "RGB":
        im = im.convert("RGB")
    draw = ImageDraw.Draw(im)
    font_size = max(28, im.size[0] // 50)  # ~33-39 px depending on image width
    font = _load_label_font(font_size)
    for text, x, y in spec:
        # Draw a small white rectangle behind for legibility
        try:
            bbox = draw.textbbox((x, y), text, font=font)
            pad = 4
            draw.rectangle(
                (bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad),
                fill=(255, 255, 255),
            )
        except AttributeError:
            pass
        draw.text((x, y), text, fill=(0, 0, 0), font=font)
    return im


# ---------------------------------------------------------------------------
# TIFF conversion
# ---------------------------------------------------------------------------
def convert_pngs_to_tiffs(figs, tif_dir: Path):
    """Convert PNG figures to TIFF at 300 DPI, renamed FigureN.tif. Returns
    list of (tif_path, caption) in same order. Multi-panel figures get A)/B)/C)
    labels overlaid at the top-left of each panel (CNIB requirement)."""
    tif_dir.mkdir(parents=True, exist_ok=True)
    out = []
    for i, (png_rel, caption) in enumerate(figs, start=1):
        png_path = ROOT / png_rel
        if not png_path.exists():
            print(f"WARN: figure not found: {png_path}", file=sys.stderr)
            continue
        tif_name = f"Figure{i}.tif"
        tif_path = tif_dir / tif_name
        im = Image.open(png_path)
        if im.mode == "RGBA":
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[3])
            im = bg
        elif im.mode != "RGB":
            im = im.convert("RGB")
        im = overlay_panel_labels(im, png_path.name)
        im.save(tif_path, format="TIFF", dpi=(300, 300), compression="tiff_lzw")
        out.append((tif_path, caption))
        print(f"  TIFF: {tif_name}  size={im.size}  300 DPI  ({png_path.name})")
    return out


# ---------------------------------------------------------------------------
# Main build
# ---------------------------------------------------------------------------
def build():
    text = SRC_MD.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)

    figs = discover_figure_order(body)
    tif_figs = convert_pngs_to_tiffs(figs, TIF_DIR)
    # Map md_path -> tif_path for substitution
    md_to_tif = {fp[0]: tp[0] for fp, tp in zip(figs, tif_figs)}
    md_to_index = {fp[0]: i + 1 for i, fp in enumerate(figs)}

    # Open template (.docm zip) as Document. python-docx requires .docx content types,
    # so we first strip macros and rewrite [Content_Types].xml.
    strip_macros_to_docx(TEMPLATE, TEMPLATE_DOCX)
    doc = Document(str(TEMPLATE_DOCX))
    clear_body(doc)

    # ---- Title ----
    add_paragraph_styled(doc, "papertitle", runs=parse_inline(fm["title"]))

    # ---- Authors (single line, with superscript affiliation numbers) ----
    authors = fm["author"]
    # Build affiliation index map (ordered, deduped)
    aff_list = []
    aff_index = {}
    for a in authors:
        aff = a["affiliation"]
        if aff not in aff_index:
            aff_index[aff] = len(aff_list) + 1
            aff_list.append(aff)

    p = doc.add_paragraph()
    p.style = doc.styles["author"]
    for i, a in enumerate(authors):
        if i > 0:
            sep = ", and " if i == len(authors) - 1 else ", "
            p.add_run(sep)
        p.add_run(a["name"])
        sup = p.add_run(str(aff_index[a["affiliation"]]))
        sup.font.superscript = True

    # ---- Addresses (one paragraph per affiliation, last one carries email line) ----
    # Per CNIB rule: only the corresponding author's email goes on the title page.
    # Find the author flagged corresponding=true; fall back to first email or fm["email"].
    corr_email = None
    for a in authors:
        if a.get("corresponding") and a.get("email"):
            corr_email = a["email"]
            break
    if not corr_email:
        for a in authors:
            if a.get("email"):
                corr_email = a["email"]
                break
    if not corr_email:
        corr_email = fm.get("email")

    for idx, aff in enumerate(aff_list):
        p = doc.add_paragraph()
        p.style = doc.styles["address"]
        sup = p.add_run(str(idx + 1))
        sup.font.superscript = True
        p.add_run(" " + aff)
        if idx == len(aff_list) - 1 and corr_email:
            p.add_run().add_break()
            email_run = p.add_run(corr_email)
            email_run.font.name = "Courier New"
            try:
                email_run.style = doc.styles["e-mail"]
            except KeyError:
                pass

    # ---- Abstract ----
    abstract_text = fm["abstract"].strip().replace("\n", " ")
    abstract_text = re.sub(r"\s+", " ", abstract_text)
    p = doc.add_paragraph()
    p.style = doc.styles["abstract"]
    bold = p.add_run("Abstract. ")
    bold.bold = True
    for text, b, i, c in parse_inline(abstract_text):
        r = p.add_run(text)
        if b:
            r.bold = True
        if i:
            r.italic = True

    # ---- Keywords ----
    kw_list = fm["keywords"]
    if isinstance(kw_list, list):
        kw_text = ", ".join(kw_list)
    else:
        kw_text = str(kw_list)
    p = doc.add_paragraph()
    p.style = doc.styles["keywords"]
    bold = p.add_run("Keywords: ")
    bold.bold = True
    p.add_run(kw_text + ".")

    # ---- Body ----
    parse_body(doc, body, md_to_tif, md_to_index)

    OUT_DOCX.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUT_DOCX))
    print(f"\nSaved: {OUT_DOCX}")


def parse_body(doc, body: str, md_to_tif: dict, md_to_index: dict):
    lines = body.split("\n")
    i = 0
    after_heading = False  # next paragraph should use p1a
    in_references = False
    while i < len(lines):
        line = lines[i]

        # Skip blank
        if line.strip() == "":
            i += 1
            continue

        # Heading 1 (## )
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m and not line.startswith("###"):
            heading = m.group(1)
            in_references = heading.lower().startswith("references")
            # heading1 in template auto-numbers — strip the manual "N. " prefix
            heading_clean = re.sub(r"^\d+\.\s+", "", heading)
            add_paragraph_styled(doc, "heading1", runs=parse_inline(heading_clean))
            after_heading = True
            i += 1
            continue

        # Heading 2 (### )
        m = re.match(r"^###\s+(.+?)\s*$", line)
        if m:
            text = m.group(1)
            # heading2 in template auto-numbers (1.1 …) — strip the manual "N.N " prefix
            text = re.sub(r"^\d+\.\d+\s+", "", text)
            add_paragraph_styled(doc, "heading2", runs=parse_inline(text))
            after_heading = True
            i += 1
            continue

        # Heading 3 (#### )
        m = re.match(r"^####\s+(.+?)\s*$", line)
        if m:
            add_paragraph_styled(doc, "heading 3", runs=parse_inline(m.group(1)))
            after_heading = True
            i += 1
            continue

        # Figure: ![caption](path)
        m = re.match(r"^!\[([^\]]+)\]\(([^)]+)\)\s*$", line)
        if m:
            caption = m.group(1)
            md_path = m.group(2)
            tif_path = md_to_tif.get(md_path)
            if tif_path is None:
                print(f"WARN: no TIFF mapping for {md_path}")
                i += 1
                continue
            # Strip the "Figure N. " prefix; keep the rest as descriptive Alt-Text
            cap_rest = caption
            mfig = re.match(r"^Figure\s*\d+\.\s*(.+)$", caption, re.DOTALL)
            if mfig:
                cap_rest = mfig.group(1)
            # Alt-Text: full descriptive caption (Word convention).
            alt = re.sub(r"\s+", " ", cap_rest).strip()
            add_image_paragraph(doc, tif_path, alt_text=alt, width_in=5.7)
            n = md_to_index[md_path]
            p = doc.add_paragraph()
            p.style = doc.styles["figurecaption"]
            bold = p.add_run(f"Figure {n}. ")
            bold.bold = True
            for text, b, it, c in parse_inline(cap_rest):
                r = p.add_run(text)
                if b: r.bold = True
                if it: r.italic = True
            after_heading = False
            i += 1
            continue

        # Table block
        if line.lstrip().startswith("|"):
            # Look for explicit table caption pattern in preceding line: "**Table 1.** caption text"
            # Such caption was emitted as a paragraph; nothing to do here. Just gather rows.
            tbl_lines = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                tbl_lines.append(lines[i])
                i += 1
            res = parse_md_table(tbl_lines)
            if res:
                header, data = res
                add_table(doc, header, data, caption_runs=None)
            after_heading = False
            continue

        # Reference list item: starts with number. Only inside References section.
        m = re.match(r"^(\d+)\.\s+(.+)$", line)
        if m and in_references:
            text = m.group(2)
            # Continue collecting continuation lines
            while i + 1 < len(lines) and lines[i + 1].strip() and not re.match(r"^(\d+)\.\s+", lines[i + 1]) and not lines[i + 1].startswith(("#", "!", "|")):
                text += " " + lines[i + 1].strip()
                i += 1
            p = doc.add_paragraph()
            p.style = doc.styles["referenceitem"]
            # referenceitem in template auto-numbers — DO NOT include "N. " prefix
            for tx, b, it, c in parse_inline(text):
                r = p.add_run(tx)
                if b: r.bold = True
                if it: r.italic = True
            i += 1
            continue

        # Standalone "Table N." caption paragraph (markdown bold)
        # "**Table 1.** caption text"
        m = re.match(r"^\*\*Table\s*(\d+)\.\*\*\s*(.+?)\s*$", line)
        if m:
            n = m.group(1)
            cap = m.group(2)
            p = doc.add_paragraph()
            p.style = doc.styles["tablecaption"]
            bold = p.add_run(f"Table {n}. ")
            bold.bold = True
            for tx, b, it, c in parse_inline(cap):
                r = p.add_run(tx)
                if b: r.bold = True
                if it: r.italic = True
            after_heading = False
            i += 1
            continue

        # Regular paragraph: collect contiguous non-blank, non-special lines
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
            para_lines.append(nxt)
            i += 1
        joined = " ".join(l.strip() for l in para_lines)
        joined = re.sub(r"\s+", " ", joined)
        style = "p1a" if after_heading else "Normal"
        add_paragraph_styled(doc, style, runs=parse_inline(joined))
        after_heading = False


if __name__ == "__main__":
    build()
