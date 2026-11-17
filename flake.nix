{
  description = ''John W. Terrell — resume: content in content/resume.yaml, layout in src/*.typ, rendered by Typst'';

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # Every font the renderers need is pinned here, so the PDF and the
        # self-contained HTML never reach for ~/Library/Fonts or a font CDN.
        #   inter, source-serif, jetbrains-mono  -> src/theme.typ and the HTML
        #   dejavu_fonts                         -> Typst's last-resort fallback
        # The office formats name recipient-side fonts instead (Cambria/Calibri/
        # Consolas in .docx, their LibreOffice metric clones in .odt); nothing is
        # bundled into those files.
        resume-fonts = pkgs.buildEnv {
          name = "resume-fonts";
          paths = [
            pkgs.inter
            pkgs.source-serif
            pkgs.jetbrains-mono
            pkgs.dejavu_fonts
          ];
          pathsToLink = [ "/share/fonts" ];
        };

        # The YAML-driven renderers that are not Typst. fonttools is only used by
        # build_html.py, to subset the pinned fonts before inlining them.
        content-renderers = pkgs.python3.withPackages (
          ps: [ ps.jinja2 ps.pyyaml ps.python-docx ps.fonttools ]
        );
      in
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            typst
            jq
            just
            yq # YAML queries for `just data`
            poppler-utils # pdfinfo, for `just pages`
            content-renderers
            tinymist # language server for src/*.typ
          ];
          env.TYPST_FONT_PATHS = "${resume-fonts}/share/fonts";
          env.RESUME_FONTS = "${resume-fonts}/share/fonts";
          shellHook = ''
            echo "resume: just build | just html | just docx | just odt | just watch"
          '';
        };
      }
    );
}
