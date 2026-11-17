// Page setup and section order. Look and feel live in src/theme.typ.
#import "theme.typ": *

#let cv = yaml("../content/resume.yaml")

#set page(
  paper: "us-letter",
  margin: (top: 0.55in, x: 0.62in, bottom: 0.62in),
  footer: context {
    // Only page 2 onwards: a loose sheet should still identify its owner.
    if counter(page).get().first() > 1 {
      set text(size: 7.4pt, fill: muted)
      grid(
        columns: (1fr, auto),
        [#cv.identity.name],
        [#counter(page).display("1") of #counter(page).final().first()],
      )
    }
  },
)

#set text(font: font.body, size: size.body, fill: ink, lang: "en", hyphenate: false)
#set par(justify: true, leading: 5pt, spacing: 5pt)

#identity(cv.identity)

#section("Profile", [#cv.summary])
#section("Technical Skills", skills(cv.skills))
#section("Experience", experience(cv.experience))
#maybe("Patents", cv.patents, credentials)
#maybe("Open Source", cv.open_source, credentials)
#maybe("Notable Software", cv.software, credentials)
#maybe("Education", cv.education, credentials)
