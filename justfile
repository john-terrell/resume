# Resume pipeline. Run inside `nix develop` (or: nix develop --command just build).
#
#   content/resume.yaml   the only place you edit content
#   src/resume.typ        page setup + section order
#   src/theme.typ         design tokens (fonts, colour, spacing) + section renderers
#   templates/resume.html.j2 + tools/build_html.py   the web renderer
#   tools/build_docx.py       the Word renderer
#   tools/build_odt.py        the LibreOffice renderer

name        := "Terrell-resume"
src         := "src/resume.typ"
out         := "build"
pdf         := out + "/" + name + ".pdf"
html        := out + "/" + name + ".html"
docx        := out + "/" + name + ".docx"
odt         := out + "/" + name + ".odt"
data        := "content/resume.yaml"

default: build

# render the PDF
build:
    @mkdir -p {{out}}
    typst compile --root . --format pdf {{src}} {{pdf}}
    @pdfinfo {{pdf}} | grep -E '^(Pages|Page size)'

# render the HTML resume (same content, its own layout)
html:
    @mkdir -p {{out}}
    python3 tools/build_html.py {{data}} {{html}}

build-all: build html docx odt

# render the Word resume (for portals that demand .docx)
docx:
    @mkdir -p {{out}}
    python3 tools/build_docx.py {{data}} {{docx}}

# render the LibreOffice resume
odt:
    @mkdir -p {{out}}
    python3 tools/build_odt.py {{data}} {{odt}}

# rebuild on save
watch:
    @mkdir -p {{out}}
    typst watch --root . --format pdf {{src}} {{pdf}}

# open the PDF in the default viewer
open: build
    open {{pdf}}

# page count + a text dump of what an ATS parser will actually see
pages: build
    @pdfinfo {{pdf}} | grep '^Pages'
    @pdftotext -layout {{pdf}} - | head -20

# sanity-check the content file: required keys, job count, empty fields left to fill
data:
    @yq -r '"jobs          \(.experience | length)\nskills        \(.skills | length) groups\npatents       \(.patents | length)\nopen source   \(.open_source | length)\neducation     \(.education | length)"' {{data}}
    @yq -r '.experience[] | "  \(.start)–\(.end)  \(.company)"' {{data}}
    @yq -r '[.identity.email, .identity.phone, .identity.location] | map(select(. == "")) | length | "blank contact fields: \(.) of 3"' {{data}}

clean:
    rm -rf {{out}}
