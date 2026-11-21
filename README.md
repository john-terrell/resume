# Resume

One content file, four renderers. The resume lives in `content/resume.yaml`;
layout and design live in `src/`. Typst renders the PDF, and Python scripts
render HTML, DOCX, and ODT from the same YAML.

## Layout

| Path | Purpose |
|---|---|
| `content/resume.yaml` | The only file you edit for content |
| `src/resume.typ` | Page setup + section order (Typst) |
| `src/theme.typ` | Design tokens: fonts, colour, spacing, section renderers |
| `templates/resume.html.j2` | Jinja2 template for the web version |
| `tools/build_html.py` | HTML renderer (inlines subset fonts via fonttools) |
| `tools/build_docx.py` | Word renderer (python-docx) |
| `tools/build_odt.py` | LibreOffice renderer (stdlib ODF) |
| `justfile` | Build recipes |
| `flake.nix` | Pinned toolchain + fonts (reproducible on any machine) |
| `.github/workflows/release.yml` | Tag-triggered release |

## Requirements

- [Nix](https://nixos.org/download/) with flakes enabled (`nix develop` needs
  `experimental-features = nix-command flakes` in `~/.config/nix/nix.conf`).
- [just](https://github.com/casey/just) — installed by the shell below.

Everything else (typst, yq, python packages, fonts) is pinned in the flake.

## Updating the resume

Edit `content/resume.yaml`. Structure:

```yaml
meta:       # schema version + last-updated date
identity:   # name, title, email, phone, location, links[]
summary:    # folded scalar, one paragraph
skills:     # [{label, items[]}]
experience: # [{company, role, start, end, note, bullets[], stack[]}]
patents:    # [{head, sub, note, url}]
open_source: # [{head, sub, note, url}]
education:  # [{head, sub}]
```

Blank or missing fields are skipped, so it is safe to leave a section empty
while writing. No markup in the data — plain YAML only.

Sanity-check after editing (section counts, job list, blank contact fields):

```sh
just data
```

## Generating output

Enter the pinned environment, then build:

```sh
nix develop
```

| Command | Output |
|---|---|
| `just build` | `build/Terrell-resume.pdf` |
| `just html` | `build/Terrell-resume.html` (self-contained, fonts inlined) |
| `just docx` | `build/Terrell-resume.docx` |
| `just odt` | `build/Terrell-resume.odt` |
| `just build-all` | all four |
| `just watch` | rebuild the PDF on save |
| `just pages` | page count + ATS text dump |
| `just data` | content sanity check |

Or skip the shell and run a single recipe directly:

```sh
nix develop --command just build-all
```

## Creating a release

Releases are tag-triggered. Push a date-based tag (format `YYYYMMDD`) and the
GitHub Action builds all four formats in the flake and publishes them as
release assets:

```sh
git add -A && git commit -m "Update resume: <what changed>"
git tag 20261121
git push origin main 20261121
```

The workflow (`.github/workflows/release.yml`) runs on `push` of a tag matching
`20*`:

1. Installs Nix (`DeterminateSystems/determinate-nix-action`).
2. `just data` — sanity gate.
3. `just build-all` — same pinned build as local.
4. Creates a GitHub Release named after the tag with the four files as assets,
   with auto-generated release notes from the commits since the last tag.

The built-in `GITHUB_TOKEN` has write scope; no extra secrets are needed.

> Note: the workflow runs from the tag's commit, not from `main`. If you fix
> the workflow itself, make sure the tag points at a commit that contains the
> fix.
