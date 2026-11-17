#!/usr/bin/env python3
"""Render content/resume.yaml to a standalone HTML resume.

The PDF is laid out by Typst (src/*.typ); this is the second renderer over the
same content file. Layout lives in templates/resume.html.j2.

Fonts are inlined rather than fetched: $RESUME_FONTS (set by the flake's dev
shell) points at the pinned nixpkgs fonts, which are subset down to the
codepoints this page actually uses and embedded as data: URIs. The output is
one self-contained file with no network dependency. If RESUME_FONTS is unset,
the template falls back to the Google Fonts CDN link.

    python3 tools/build_html.py content/resume.yaml build/Terrell-resume.html
"""

from __future__ import annotations

import base64
import os
import pathlib
import subprocess
import sys
import tempfile

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = pathlib.Path(__file__).resolve().parent.parent

# (family, file under the font dir, CSS font-weight, format())
# Mirrors src/theme.typ: Inter for text, Source Serif 4 for the name only,
# JetBrains Mono for the date gutter. No italics are used.
FONTS = (
    ("Inter", "truetype/InterVariable.ttf", "400 700", "truetype"),
    ("Source Serif 4", "opentype/SourceSerif4-Regular.otf", "400", "opentype"),
    ("Source Serif 4", "opentype/SourceSerif4-Semibold.otf", "600", "opentype"),
    ("JetBrains Mono", "opentype/JetBrainsMono-Regular.otf", "400", "truetype"),
    ("JetBrains Mono", "opentype/JetBrainsMono-Medium.otf", "500", "truetype"),
)


def inline_fonts(html: str, font_dir: pathlib.Path) -> str:
    """Subset each pinned font to the glyphs this page uses, then base64 it."""
    used = pathlib.Path(tempfile.mkstemp()[1])
    used.write_text("".join(sorted(set(html))), encoding="utf-8")
    faces = []
    try:
        with tempfile.TemporaryDirectory() as tmp:
            for family, rel, weight, fmt in FONTS:
                source = font_dir / rel
                if not source.exists():
                    raise SystemExit(
                        f"missing {source} — RESUME_FONTS must point at the "
                        "flake's resume-fonts env"
                    )
                subset = pathlib.Path(tmp) / (pathlib.Path(rel).stem + ".font")
                subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "fontTools.subset",
                        f"--text-file={used}",
                        f"--output-file={subset}",
                        "--no-hinting",
                        "--desubroutinize",
                        str(source),
                    ],
                    check=True,
                )
                data = base64.b64encode(subset.read_bytes()).decode()
                faces.append(
                    f'@font-face{{font-family:"{family}";font-style:normal;'
                    f"font-weight:{weight};"
                    f"src:url(data:font/{fmt};base64,{data}) format(\"{fmt}\");}}"
                )
    finally:
        used.unlink(missing_ok=True)
    return "\n".join(faces)


def render(data_path: pathlib.Path, out_path: pathlib.Path) -> None:
    cv = yaml.safe_load(data_path.read_text())

    env = Environment(
        loader=FileSystemLoader(ROOT / "templates"),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("resume.html.j2")

    # Render once without fonts to learn which codepoints the page needs, then
    # again with the subsets inlined.
    font_dir = os.environ.get("RESUME_FONTS")
    draft = template.render(cv=cv, font_css="")
    font_css = inline_fonts(draft, pathlib.Path(font_dir)) if font_dir else ""
    html = template.render(cv=cv, font_css=font_css)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)
    how = f"{len(FONTS)} font subsets inlined" if font_css else "CDN fonts"
    print(f"wrote {out_path} ({how})")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    render(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]))
