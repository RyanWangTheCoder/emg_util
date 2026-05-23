#!/usr/bin/env python3
"""Post-process pandoc-generated docx to fix table styles and None paragraph styles."""

import sys
from copy import deepcopy
from lxml import etree
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

INPUT = "/local/mnt/workspace/wangx/projects/emg_util/icpics_draft.docx"
OUTPUT = "/local/mnt/workspace/wangx/projects/emg_util/icpics_draft_fixed.docx"

def add_table_borders(tbl_element):
    """Add visible borders to a table via direct XML (works even without a named style)."""
    tblPr = tbl_element.find(qn("w:tblPr"))
    if tblPr is None:
        tblPr = OxmlElement("w:tblPr")
        tbl_element.insert(0, tblPr)

    # Remove existing tblBorders if any
    existing = tblPr.find(qn("w:tblBorders"))
    if existing is not None:
        tblPr.remove(existing)

    tblBorders = OxmlElement("w:tblBorders")
    for border_name in ("top", "left", "bottom", "right", "insideH", "insideV"):
        border = OxmlElement(f"w:{border_name}")
        border.set(qn("w:val"), "single")
        border.set(qn("w:sz"), "4")
        border.set(qn("w:space"), "0")
        border.set(qn("w:color"), "000000")
        tblBorders.append(border)
    tblPr.append(tblBorders)


def set_table_width(tbl_element, width_pct=100):
    """Set table to span full page width."""
    tblPr = tbl_element.find(qn("w:tblPr"))
    if tblPr is None:
        tblPr = OxmlElement("w:tblPr")
        tbl_element.insert(0, tblPr)

    existing = tblPr.find(qn("w:tblW"))
    if existing is not None:
        tblPr.remove(existing)

    tblW = OxmlElement("w:tblW")
    tblW.set(qn("w:w"), str(width_pct * 50))  # 5000 = 100% in twentieths of a percent
    tblW.set(qn("w:type"), "pct")
    tblPr.insert(0, tblW)


def fix_normal_alignment(doc):
    """The template sets Normal=CENTER (for title/author area). Override to JUSTIFY for body text."""
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    doc.styles["Normal"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def fix_none_style(doc):
    """Replace None paragraph styles with 'Normal'."""
    for p in doc.paragraphs:
        if p.style is None or p.style.name is None:
            p.style = doc.styles["Normal"]


def bold_first_row(table):
    """Make the first row bold (table header)."""
    if not table.rows:
        return
    for cell in table.rows[0].cells:
        for para in cell.paragraphs:
            for run in para.runs:
                run.font.bold = True


def main():
    doc = Document(INPUT)

    fix_normal_alignment(doc)
    fix_none_style(doc)

    for table in doc.tables:
        add_table_borders(table._tbl)
        set_table_width(table._tbl)
        bold_first_row(table)

    doc.save(OUTPUT)
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
