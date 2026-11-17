#!/usr/bin/env python3
"""Render content/resume.yaml to a LibreOffice .odt resume.

Same content file as the Typst PDF and the .docx, laid out with ODF idioms: a
page-master for the margins, named paragraph styles, real text:list bullets,
and a two-column table per entry whose body cell carries the accent bar.

The package is written directly (mimetype, manifest, styles.xml, content.xml,
meta.xml) rather than through odfpy: odfpy 1.4.1 cannot express page-master or
list-level styles at all — its style-family validator rejects "page" and
"list-level", and it refuses style:page-layout as a child of style:style.
stdlib only.

Fonts are the metric clones LibreOffice ships, so the document looks the same
on any machine: Caladea (Cambria) / Carlito (Calibri) / Liberation Mono.

    python3 tools/build_odt.py content/resume.yaml build/Terrell-resume.odt
"""

from __future__ import annotations

import pathlib
import sys
import zipfile
from xml.sax.saxutils import escape

import yaml

ACCENT = "#1f3a5f"
INK = "#15181d"
MUTED = "#5c6672"
HAIR = "#c9d0d9"

SERIF, SANS, MONO = "Caladea", "Carlito", "Liberation Mono"
PAGE_W, PAGE_H = "215.9mm", "279.4mm"
MARGIN_X, MARGIN_Y = "15.75mm", "14mm"
GUTTER, BODY = 25.4, 159.0  # mm; sums to the text width
DASH = "\u2013"
DOT = "\u00b7"

NAMESPACES = (
    'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
    'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
    'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" '
    'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
    'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
    'xmlns:xlink="http://www.w3.org/1999/xlink"'
)


def text_props(*, font=SANS, size="9.5pt", weight=None, colour=INK, spacing=None):
    parts = [f'style:font-name="{font}"', f'fo:font-size="{size}"', f'fo:color="{colour}"']
    if weight:
        parts.append(f'fo:font-weight="{weight}"')
    if spacing:
        parts.append(f'style:letter-spacing="{spacing}"')
    return f"<style:text-properties {' '.join(parts)}/>"


def para_style(
    name,
    *,
    font=SANS,
    size="9.5pt",
    weight=None,
    colour=INK,
    spacing=None,
    props="",
):
    return (
        f'<style:style style:name="{name}" style:family="paragraph">'
        f"<style:paragraph-properties {props}/>"
        f"{text_props(font=font, size=size, weight=weight, colour=colour, spacing=spacing)}"
        f"</style:style>"
    )


def text_style(name, *, font=SANS, size="9.5pt", weight=None, colour=INK):
    return (
        f'<style:style style:name="{name}" style:family="text">'
        f"{text_props(font=font, size=size, weight=weight, colour=colour)}"
        f"</style:style>"
    )


def styles_xml() -> str:
    named = "".join(
        (
            '<style:default-style style:family="paragraph">'
            '<style:paragraph-properties fo:widows="1" fo:orphans="1" '
            'fo:line-height="128%"/>'
            f"{text_props()}"
            "</style:default-style>",
            para_style("Standard", props='fo:margin-bottom="0pt"'),
            para_style(
                "Name",
                font=SERIF,
                size="24pt",
                weight="bold",
                props='fo:margin-bottom="1pt"',
            ),
            para_style(
                "Title",
                size="10.5pt",
                weight="bold",
                colour=ACCENT,
                props=f'fo:border-bottom="1.2pt solid {ACCENT}" '
                'fo:padding-bottom="5pt" fo:margin-bottom="6pt"',
            ),
            para_style(
                "Contact",
                size="8.5pt",
                colour=MUTED,
                props='fo:margin-bottom="2pt"',
            ),
            para_style(
                "Section",
                size="8.5pt",
                weight="bold",
                colour=ACCENT,
                spacing="0.8pt",
                props=f'fo:border-bottom="0.5pt solid {HAIR}" '
                'fo:padding-bottom="3pt" fo:margin-top="11pt" '
                'fo:margin-bottom="6pt" fo:keep-with-next="always"',
            ),
            para_style("Note", size="8.5pt", colour=MUTED, props='fo:margin-bottom="0pt"'),
            para_style(
                "Stack",
                font=MONO,
                size="7.5pt",
                colour=MUTED,
                props='fo:margin-top="2pt" fo:margin-bottom="0pt"',
            ),
            para_style(
                "Gutter",
                font=MONO,
                size="8.5pt",
                colour=ACCENT,
                props='fo:text-align="end" fo:margin-bottom="0pt"',
            ),
            para_style("Bullet", props='fo:margin-bottom="0pt"'),
            text_style("Sub", size="8.5pt", colour=MUTED),
            text_style("Tech", size="9.5pt", weight="bold", colour=ACCENT),
            '<text:list-style style:name="ListBullet">'
            f'<text:list-level-style-bullet text:level="1" text:bullet-char="{DASH}">'
            '<style:list-level-properties text:space-before="10pt" '
            'text:min-label-width="10pt"/>'
            f"{text_props(colour=ACCENT)}"
            "</text:list-level-style-bullet>"
            "</text:list-style>",
        )
    )


    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<office:document-styles {NAMESPACES} office:version=\"1.2\">"
        f"<office:styles>{named}</office:styles>"
        '<office:automatic-styles>'
        f'<style:page-layout style:name="pm1">'
        f'<style:page-layout-properties fo:page-width="{PAGE_W}" '
        f'fo:page-height="{PAGE_H}" style:print-orientation="portrait" '
        f'fo:margin-top="{MARGIN_Y}" fo:margin-bottom="{MARGIN_Y}" '
        f'fo:margin-left="{MARGIN_X}" fo:margin-right="{MARGIN_X}"/>'
        "</style:page-layout>"
        "</office:automatic-styles>"
        '<office:master-styles><style:master-page style:name="Standard" '
        'style:page-layout-name="pm1"/></office:master-styles>'
        "</office:document-styles>"
    )


def entry_family(bar: str, key: str) -> str:
    """Table, column and cell styles for one family of entry tables.

    These are automatic styles, so they live in content.xml: ODF scopes
    automatic styles to the document part that declares them.
    """
    return (
        f'<style:style style:name="{key}-table" style:family="table">'
        f'<style:table-properties style:width="{GUTTER + BODY}mm" '
        'table:align="margins"/>'
        "</style:style>"
        f'<style:style style:name="{key}-gutter" style:family="table-column">'
        f'<style:table-column-properties style:column-width="{GUTTER}mm"/>'
        "</style:style>"
        f'<style:style style:name="{key}-body" style:family="table-column">'
        f'<style:table-column-properties style:column-width="{BODY}mm"/>'
        "</style:style>"
        f'<style:style style:name="{key}-cell-gutter" style:family="table-cell">'
        '<style:table-cell-properties fo:padding-right="5pt" '
        'fo:vertical-align="top"/>'
        "</style:style>"
        f'<style:style style:name="{key}-cell-body" style:family="table-cell">'
        f'<style:table-cell-properties fo:border-left="1.7pt solid {bar}" '
        'fo:padding-left="7pt" fo:vertical-align="top"/>'
        "</style:style>"
    )


def link(url: str, label: str) -> str:
    return (
        f'<text:a xlink:type="simple" xlink:href="{escape(url)}">'
        f"{escape(label)}</text:a>"
    )


def entry_table(dates, head, *, sub="", note="", points=(), stack=(), key="job") -> str:
    cells = []
    gutter = f'<text:p text:style-name="Gutter">{escape(dates)}</text:p>' if dates else ""
    cells.append(f'<table:table-cell table:style-name="{key}-cell-gutter">{gutter}</table:table-cell>')

    body = [f'<text:p text:style-name="Standard">{escape(head)}']
    if sub:
        body.append(f'<text:span text:style-name="Sub">   {escape(sub)}</text:span>')
    body.append("</text:p>")
    if note:
        body.append(f'<text:p text:style-name="Note">{escape(" ".join(note.split()))}</text:p>')
    if points:
        items = "".join(
            f'<text:list-item><text:p text:style-name="Bullet">'
            f'{escape(" ".join(point.split()))}</text:p></text:list-item>'
            for point in points
        )
        body.append(f'<text:list text:style-name="ListBullet">{items}</text:list>')
    if stack:
        body.append(
            f'<text:p text:style-name="Stack">{escape(f"  {DOT}  ".join(stack))}</text:p>'
        )
    cells.append(
        f'<table:table-cell table:style-name="{key}-cell-body" '
        f'office:value-type="string">{"".join(body)}</table:table-cell>'
    )

    return (
        f'<table:table table:style-name="{key}-table">'
        f'<table:table-column table:style-name="{key}-gutter"/>'
        f'<table:table-column table:style-name="{key}-body"/>'
        f'<table:table-row>{"".join(cells)}</table:table-row>'
        "</table:table>"
    )


def content_xml(cv: dict) -> str:
    identity = cv["identity"]
    out = []

    out.append(f'<text:p text:style-name="Name">{escape(identity["name"])}</text:p>')
    out.append(f'<text:p text:style-name="Title">{escape(identity["title"])}</text:p>')

    bits = []
    if identity.get("email"):
        bits.append(link("mailto:" + identity["email"], identity["email"]))
    if identity.get("phone"):
        bits.append(
            link("tel:" + identity["phone"].replace(" ", ""), identity["phone"])
        )
    if identity.get("location"):
        bits.append(escape(identity["location"]))
    for item in identity.get("links", []):
        if item.get("url"):
            bits.append(link(item["url"], item["label"]))
    out.append(
        '<text:p text:style-name="Contact">'
        + f"   {DOT}   ".join(bits)
        + "</text:p>"
    )

    out.append('<text:p text:style-name="Section">PROFILE</text:p>')
    out.append(
        f'<text:p text:style-name="Standard">{escape(" ".join(cv["summary"].split()))}</text:p>'
    )

    out.append('<text:p text:style-name="Section">TECHNICAL SKILLS</text:p>')
    for group in cv["skills"]:
        if not group.get("items"):
            continue
        out.append(
            f'<text:p text:style-name="Standard">'
            f'<text:span text:style-name="Tech">{escape(group["label"])}: </text:span>'
            f"{escape(', '.join(group['items']))}</text:p>"
        )

    out.append('<text:p text:style-name="Section">EXPERIENCE</text:p>')
    for job in cv["experience"]:
        out.append(
            entry_table(
                f"{job['start']} {DASH} {job['end']}",
                job["company"],
                sub=job.get("role", ""),
                note=job.get("note", ""),
                points=[b.strip() for b in job.get("bullets", [])],
                stack=job.get("stack", []),
            )
        )

    for title, key in (
        ("PATENTS", "patents"),
        ("OPEN SOURCE", "open_source"),
        ("NOTABLE SOFTWARE", "software"),
        ("EDUCATION", "education"),
    ):
        items = cv.get(key) or []
        if not items:
            continue
        out.append(f'<text:p text:style-name="Section">{title}</text:p>')
        for item in items:
            out.append(
                entry_table(
                    item.get("dates", ""),
                    item["head"].strip(),
                    sub=item.get("sub", ""),
                    key="cred",
                )
            )

    return (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f"<office:document-content {NAMESPACES} office:version=\"1.2\">"
        "<office:automatic-styles>"
        + entry_family(ACCENT, "job")
        + entry_family(HAIR, "cred")
        + "</office:automatic-styles>"
        f"<office:body><office:text>{''.join(out)}</office:text></office:body>"
        "</office:document-content>"
    )


def meta_xml(cv: dict) -> str:
    name = cv["identity"]["name"]
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<office:document-meta '
        'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" '
        'office:version="1.2">'
        "<office:meta>"
        f'<dc:title>{escape(name)} — resume</dc:title>'
        f'<dc:initial-creator>{escape(name)}</dc:initial-creator>'
        '<meta:generator>tools/build_odt.py</meta:generator>'
        "</office:meta></office:document-meta>"
    )


MANIFEST = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<manifest:manifest '
    'xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" '
    'manifest:version="1.2">'
    '<manifest:file-entry manifest:full-path="/" manifest:version="1.2" '
    'manifest:media-type="application/vnd.oasis.opendocument.text"/>'
    '<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>'
    '<manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>'
    '<manifest:file-entry manifest:full-path="meta.xml" manifest:media-type="text/xml"/>'
    "</manifest:manifest>"
)


def render(data_path: pathlib.Path, out_path: pathlib.Path) -> None:
    cv = yaml.safe_load(data_path.read_text())
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as package:
        # The mimetype entry must be first, stored, and unterminated.
        info = zipfile.ZipInfo("mimetype")
        info.compress_type = zipfile.ZIP_STORED
        package.writestr(info, "application/vnd.oasis.opendocument.text")
        package.writestr("META-INF/manifest.xml", MANIFEST)
        package.writestr("styles.xml", styles_xml())
        package.writestr("content.xml", content_xml(cv))
        package.writestr("meta.xml", meta_xml(cv))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    render(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]))
