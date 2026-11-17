#!/usr/bin/env python3
"""Render content/resume.yaml to a Word .docx resume.

Word is a different medium: recruiters edit these, so the output uses real Word
styles (headings, List Bullet, hyperlinks) and a borderless two-column table for
the date gutter rather than trying to reproduce the PDF's accent bars exactly.
Fonts are the Word-safe equivalents of the PDF trio: Cambria / Calibri /
Consolas instead of Source Serif 4 / Inter / JetBrains Mono.

    python3 tools/build_docx.py content/resume.yaml build/Terrell-resume.docx
"""

from __future__ import annotations

import pathlib
import sys

import yaml
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ACCENT = RGBColor(0x1F, 0x3A, 0x5F)
INK = RGBColor(0x15, 0x18, 0x1D)
MUTED = RGBColor(0x5C, 0x66, 0x72)
HAIR = RGBColor(0xC9, 0xD0, 0xD9)
SERIF, SANS, MONO = "Cambria", "Calibri", "Consolas"

# Consolas is substituted for a wider mono by LibreOffice, so the gutter is
# sized for the substitution, not for Consolas itself.
GUTTER = Inches(1.15)
CONTENT = Inches(5.85)


def _border(paragraph, edge: str, colour: RGBColor, width_pt: float) -> None:
    """Give a paragraph a single border edge (Word paragraph borders)."""
    p_pr = paragraph._p.get_or_add_pPr()
    borders = p_pr.find(qn("w:pBdr"))
    if borders is None:
        borders = OxmlElement("w:pBdr")
        p_pr.append(borders)
    el = OxmlElement(f"w:{edge}")
    el.set(qn("w:val"), "single")
    el.set(qn("w:sz"), str(int(width_pt * 8)))
    el.set(qn("w:space"), "2")
    el.set(qn("w:color"), str(colour))
    borders.append(el)


def _cell_border(cell, edge: str, colour: RGBColor, width_pt: float) -> None:
    """Border on one edge of a table cell (the entry accent bar)."""
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.find(qn("w:tcBorders"))
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    el = OxmlElement(f"w:{edge}")
    el.set(qn("w:val"), "single")
    el.set(qn("w:sz"), str(int(width_pt * 8)))
    el.set(qn("w:color"), str(colour))
    borders.append(el)


def _cell_padding(cell, *, left=0.0, right=0.0) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    margins = OxmlElement("w:tcMar")
    for edge, inches in (("left", left), ("right", right)):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:w"), str(int(inches * 1440)))
        el.set(qn("w:type"), "dxa")
        margins.append(el)
    tc_pr.append(margins)

def _run(paragraph, text: str, *, font=SANS, size=9.5, bold=False, colour=INK):
    run = paragraph.add_run(text)
    run.font.name = font
    run.font.size = Pt(size)
    run.bold = bold
    run.font.color.rgb = colour
    return run


def _hyperlink(paragraph, url: str, text: str, *, size=9.5, bold=False, colour=INK):
    """python-docx has no hyperlink API; build the field by hand."""
    part = paragraph.part
    r_id = part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)
    run = OxmlElement("w:r")
    r_pr = OxmlElement("w:rPr")
    for tag, value in (
        ("w:rFonts", None),
        ("w:sz", str(int(size * 2))),
        ("w:color", str(colour)),
    ):
        el = OxmlElement(tag)
        if tag == "w:rFonts":
            el.set(qn("w:ascii"), SANS)
            el.set(qn("w:hAnsi"), SANS)
        else:
            el.set(qn("w:val"), value)
        r_pr.append(el)
    if bold:
        r_pr.append(OxmlElement("w:b"))
    run.append(r_pr)
    text_el = OxmlElement("w:t")
    text_el.set(qn("xml:space"), "preserve")
    text_el.text = text
    run.append(text_el)
    hyperlink.append(run)
    paragraph._p.append(hyperlink)


def _section(doc, title: str) -> None:
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(11)
    paragraph.paragraph_format.space_after = Pt(6)
    _run(paragraph, title.upper(), size=8.5, bold=True, colour=ACCENT)
    _border(paragraph, "bottom", HAIR, 0.5)


def _entry(doc, dates: str, head: str, *, sub="", note="", bullets=(), stack=(), url="", bar=ACCENT):
    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    table.autofit = False
    # Column widths, not just cell widths: LibreOffice lays tables out from the
    # table grid, which python-docx only updates through the column objects.
    table.columns[0].width = GUTTER
    table.columns[1].width = CONTENT
    gutter, body = table.rows[0].cells
    gutter.width = GUTTER
    body.width = CONTENT
    _cell_border(body, "left", bar, 1.7)
    _cell_padding(gutter, right=0.07)
    _cell_padding(body, left=0.09)
    for cell in (gutter, body):
        cell.paragraphs[0].paragraph_format.space_after = Pt(0)

    if dates:
        p = gutter.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        _run(p, dates, font=MONO, size=8.5, colour=ACCENT)

    p = body.paragraphs[0]
    _run(p, head, size=10.5, bold=True)
    if sub:
        _run(p, f"   {sub}", size=8.5, colour=MUTED)

    if note:
        p = body.add_paragraph()
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(0)
        _run(p, " ".join(note.split()), size=8.5, colour=MUTED)

    for point in bullets:
        p = body.add_paragraph(style="List Bullet")
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(0)
        _run(p, " ".join(point.split()))

    if stack:
        p = body.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        _run(p, "  ·  ".join(stack), font=MONO, size=7.5, colour=MUTED)

    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return body


def _credential(doc, item) -> None:
    _entry(
        doc,
        item.get("dates", ""),
        item["head"].strip(),
        sub=item.get("sub", ""),
        url=item.get("url", ""),
        bar=HAIR,
    )


def render(data_path: pathlib.Path, out_path: pathlib.Path) -> None:
    cv = yaml.safe_load(data_path.read_text())
    identity = cv["identity"]

    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin = section.bottom_margin = Inches(0.55)
    section.left_margin = section.right_margin = Inches(0.62)

    normal = doc.styles["Normal"]
    normal.font.name = SANS
    normal.font.size = Pt(9.5)
    normal.font.color.rgb = INK
    normal.paragraph_format.space_after = Pt(0)

    name = doc.add_paragraph()
    _run(name, identity["name"], font=SERIF, size=24, bold=True)

    title = doc.add_paragraph()
    title.paragraph_format.space_after = Pt(6)
    _run(title, identity["title"], size=10.5, bold=True, colour=ACCENT)
    _border(title, "bottom", ACCENT, 1.2)

    contact = doc.add_paragraph()
    contact.paragraph_format.space_after = Pt(2)
    bits = []
    if identity.get("email"):
        bits.append(("mailto:" + identity["email"], identity["email"]))
    if identity.get("phone"):
        bits.append(("tel:" + identity["phone"].replace(" ", ""), identity["phone"]))
    if identity.get("location"):
        bits.append((None, identity["location"]))
    for link in identity.get("links", []):
        if link.get("url"):
            bits.append((link["url"], link["label"]))
    for index, (url, text) in enumerate(bits):
        if index:
            _run(contact, "   ·   ", size=8.5, colour=HAIR)
        if url:
            _hyperlink(contact, url, text, size=8.5)
        else:
            _run(contact, text, size=8.5, colour=MUTED)

    _section(doc, "Profile")
    profile = doc.add_paragraph()
    profile.paragraph_format.space_after = Pt(0)
    _run(profile, " ".join(cv["summary"].split()))

    _section(doc, "Technical Skills")
    for group in cv["skills"]:
        if not group.get("items"):
            continue
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(1)
        _run(p, f"{group['label']}: ", size=9.5, bold=True, colour=ACCENT)
        _run(p, ", ".join(group["items"]))

    _section(doc, "Experience")
    for job in cv["experience"]:
        body = _entry(
            doc,
            f"{job['start']} – {job['end']}",
            job["company"],
            sub=job.get("role", ""),
            note=job.get("note", ""),
            bullets=[b.strip() for b in job.get("bullets", [])],
            stack=job.get("stack", []),
        )
        if job.get("url"):
            _hyperlink(body.paragraphs[0], job["url"], job["url"], size=7.5, colour=MUTED)

    for heading, key in (
        ("Patents", "patents"),
        ("Open Source", "open_source"),
        ("Notable Software", "software"),
        ("Education", "education"),
    ):
        items = cv.get(key) or []
        if not items:
            continue
        _section(doc, heading)
        for item in items:
            _credential(doc, item)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_path)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    render(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]))
