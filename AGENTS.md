# AGENTS.md — resume pipeline

One YAML file (`content/resume.yaml`) is the single source of truth. Four
independent renderers read it and produce four formats from the same content:

| Format | Renderer | Layout lives in |
|---|---|---|
| PDF (the canonical one) | Typst | `src/theme.typ` |
| HTML (self-contained) | Jinja2 + fonttools | `templates/resume.html.j2` |
| DOCX | python-docx | `tools/build_docx.py` |
| ODT | hand-written ODF (stdlib only) | `tools/build_odt.py` |

The renderers deliberately have **different** layouts — each format is tuned
for its medium (e.g. the DOCX uses a borderless two-column table because
recipients edit it in Word). They share data, not design.

## File map

| File | Role |
|---|---|
| `content/resume.yaml` | **The only file you edit for content.** All facts, no markup. |
| `src/resume.typ` | Typst entry: page setup, section order, which sections are optional. |
| `src/theme.typ` | Typst design tokens (fonts, colors, spacing) + the section renderers. |
| `templates/resume.html.j2` | HTML layout (Jinja2). |
| `tools/build_html.py` | Renders the HTML; subsets + inlines fonts as `data:` URLs. |
| `tools/build_docx.py` | Renders the DOCX. |
| `tools/build_odt.py` | Renders the ODT by writing the ODF zip package directly (5 XML parts). |
| `flake.nix` / `flake.lock` | Pins everything: typst, fonts, python3 + jinja2/pyyaml/python-docx/fonttools, just, yq, poppler-utils, tinymist. |
| `justfile` | Build recipes (see below). |
| `build/` | Generated outputs. Gitignored. |

## Editing content

Edit **only** `content/resume.yaml`. Blank or missing fields are skipped by
every renderer, and empty optional sections drop out entirely (see
`#maybe` below), so it is safe to leave a section empty while writing.

Key schema (all renderers read the same keys):

- `meta.updated` — bump this date whenever content changes.
- `identity` — `name`, `title`, `email`, `phone`, `location`,
  `links` (list of `{label, url}`).
- `summary` — folded scalar, one paragraph.
- `skills` — list of `{label, items: [...]}` groups.
- `experience` — list of `{company, role, start, end, note, bullets, stack,
  location?}`. `note` is the one-line context under the header; `bullets` are
  the detail; `stack` is the trailing tech line.
- `patents` / `open_source` / `software` / `education` — list of
  `{dates, head, sub?, url?}`; only `head` is required.

## Building

Everything runs inside the flake dev shell:

```sh
nix develop            # then: just build-all
# or one-shot:
nix develop --command just build-all
```

Recipes:

| Recipe | What it does |
|---|---|
| `build` | Typst → `build/Terrell-resume.pdf`, prints page count + size. |
| `html` / `docx` / `odt` | One renderer each, same output naming. |
| `build-all` | All four (default is `build`). |
| `watch` | `typst watch` — rebuilds the PDF on save. |
| `open` | Build, then open the PDF. |
| `pages` | Page count + `pdftotext` dump = what an ATS parser sees. |
| `data` | `yq` sanity check: section counts, job list, blank contact fields. |
| `clean` | `rm -rf build/`. |

After any change: `just build-all` must succeed and `just data` must show the
expected counts.

## Adding a section

1. Add the key to `content/resume.yaml` (follow the schema above).
2. Wire it into **all four renderers**:
   - `src/resume.typ` — add a `#maybe("Title", cv.key, renderer)` call (or
     `#section(...)` if it must always render). `#maybe` drops the section
     when the list is empty; `#section` always renders.
   - `src/theme.typ` — add the Typst renderer function.
   - `templates/resume.html.j2` — add the Jinja block.
   - `tools/build_docx.py` and `tools/build_odt.py` — add the equivalent
     block (both read the same keys via `.get(...)`).
3. Rebuild all four and check each output.

## Design & fonts

- Typst design tokens (fonts, colors, spacing) live in `src/theme.typ`.
- **PDF and HTML embed fonts**: the flake pins Inter, Source Serif 4,
  JetBrains Mono, DejaVu (`buildEnv resume-fonts`); `TYPST_FONT_PATHS` feeds
  Typst, `RESUME_FONTS` feeds the Python renderers. `build_html.py` subsets
  each face with fonttools and inlines it as a `data:` `@font-face`, so the
  HTML is fully self-contained; the Google Fonts CDN link in the template is
  a fallback only when `RESUME_FONTS` is unset.
- **Office formats deliberately do NOT embed fonts**: the DOCX names
  Cambria/Calibri/Consolas and the ODT names Caladea/Carlito/Liberation Mono
  (metric-compatible LibreOffice clones). Embedding would break editing on
  machines that lack the fonts — the recipient's machine renders them.

## Gotchas

- **`nix develop` fails on a repo with zero commits** — the flake resolves to
  a nonexistent store path (`error: path '…-source/flake.nix' does not
  exist`). Fix: make an initial commit. If it recurs, check `git log` first.
- **Don't embed fonts in the office formats** (see above) — it defeats the
  editability that is the whole point of the DOCX/ODT outputs.
- `build/` is gitignored; never commit generated files.
- The ODT is written by hand (stdlib `zipfile` + 5 XML parts) because odfpy
  can't express page masters or list-level styles; don't "simplify" it to
  odfpy.
- Typst renders empty content as stray parentheses — if you see `()` in the
  PDF, a field is empty where a value is expected.

## What has been done so far

- Built the pipeline from scratch: one YAML source → PDF/HTML/DOCX/ODT,
  orchestrated by `justfile`, all deps pinned in `flake.nix`.
- Chose **YAML** over JSON (native Typst `yaml()`, comments, folded scalars)
  and **Typst** over ASCIIDoc as the primary renderer.
- Fixed four cross-renderer defects: body-text font fallback, date-gutter
  wrapping, stray parentheses from empty content, and ODT style
  visibility / font-weight / line-height / grid-width bugs.
- Made the HTML self-contained (subsetted, inlined fonts).
- Wrote the ODT renderer by hand to avoid the odfpy dependency.
- Verified end-to-end: PDF is 2 pages of US Letter with fully embedded fonts
  (no external references); HTML/DOCX/ODT render the same content.
- Git history: `cc73eea` initial pipeline commit; `e9b9c18` a WIP content
  edit (wording change in one experience bullet, committed by the user).
