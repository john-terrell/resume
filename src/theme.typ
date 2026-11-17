// Design tokens and section renderers.
// Content never lives here — it comes from content/resume.yaml.
// Change the look of the resume by editing this file only.
//
// Every top-level definition is prefixed with `#`: a .typ file is in markup
// mode, so a bare `let` would be parsed as text.

// ---------------------------------------------------------------- tokens

#let accent = rgb("#1F3A5F") // navy: rules, dates, markers
#let ink = rgb("#15181D") // body text
#let muted = rgb("#5C6672") // secondary text
#let hair = rgb("#C9D0D9") // hairline rules

#let font = (
  body: "Inter",
  display: "Source Serif 4", // name only: one serif against an all-sans page
  mono: "JetBrains Mono", // date gutter
)

#let size = (
  name: 26pt,
  title: 10.5pt,
  entry: 10.6pt,
  body: 9.3pt,
  small: 8.1pt,
  gutter: 8.3pt,
  heading: 8.3pt,
)

#let gap = (section: 11pt, entry: 9pt, rule: 5pt)

#let gutter-width = 1.0in

// ------------------------------------------------------------ primitives

#let rule(weight: 0.4pt, colour: hair) = line(
  length: 100%,
  stroke: (thickness: weight, paint: colour),
)

#let eyebrow(s) = text(size: size.heading, weight: "bold", fill: accent, tracking: 0.17em)[#upper(s)]

/// Section heading: letterspaced eyebrow over a hairline. The heading is
/// glued to the first item so it can never be orphaned at a page foot.
#let section(title, body) = {
  v(gap.section)
  let items = if type(body) == array { body } else { (body,) }
  block(breakable: false)[
    #eyebrow(title)
    #v(-3pt)
    #rule()
    #v(gap.rule)
    #items.first()
  ]
  if items.len() > 1 {
    v(gap.entry)
    stack(dir: ttb, spacing: gap.entry, ..items.slice(1))
  }
}

/// Section that disappears entirely when its data is empty.
#let maybe(title, items, render) = {
  if items.len() == 0 {
    return[]
  }
  section(title, render(items))
}

/// Right-aligned date gutter, tabular figures, set against a left accent bar.
#let gutter(dates) = {
  set text(font: font.mono, size: size.gutter, fill: accent, features: ("tnum",))
  align(right + horizon, dates)
}

/// En-dash markers in the accent colour instead of the usual bullet.
#let points-list(items) = {
  set par(leading: 4.4pt)
  list(..items, indent: 0pt, body-indent: 0.85em, marker: text(size: 8pt, fill: accent)[–])
}

/// One entry: accent bar, date gutter, then head / note / bullets / stack.
#let entry(dates, head, sub: "", note: "", points: (), stack: (), url: "", bar: accent) = {
  block(
    width: 100%,
    inset: (left: 9pt, y: 0pt),
    stroke: (left: (thickness: 1.7pt, paint: bar)),
  )[
    #grid(
      columns: (gutter-width, 1fr),
      column-gutter: 10pt,
      align: horizon,
      gutter(dates),
      [
        #text(size: size.entry, weight: "semibold", fill: ink)[
          #if url != "" { link(url, head) } else { head }
        ]
        #if sub != "" [
          #h(7pt)
          #text(size: size.small, fill: muted)[#sub]
        ]
        #if note != "" [
          #v(1.5pt)
          #set text(size: size.small, fill: muted)
          #note
        ]
        #if points.len() > 0 [#points-list(points)]
        #if stack.len() > 0 [
          #v(2.5pt)
          #set text(font: font.mono, size: 7.3pt, fill: muted)
          #stack.join("  ·  ")
        ]
      ],
    )
  ]
}

/// Label column hugging the content column: dense, and reads like a spec sheet.
#let skills(groups) = {
  set text(size: size.body, fill: ink)
  let cells = ()
  for g in groups {
    if g.items.len() == 0 {
      continue
    }
    cells.push(align(right + horizon)[
      #text(size: size.small, weight: "bold", fill: accent, tracking: 0.04em)[#g.label]
    ])
    cells.push([#g.items.join(",  ")])
  }
  grid(columns: (1.15in, 1fr), column-gutter: 11pt, row-gutter: 3.5pt, ..cells)
}

// --------------------------------------------------------------- sections

#let identity(id) = {
  text(font: font.display, size: size.name, weight: "semibold", fill: ink, tracking: 0.01em)[#id.name]
  v(3pt)
  text(size: size.title, weight: "medium", fill: accent, tracking: 0.05em)[#id.title]
  v(5pt)
  rule(weight: 1.2pt, colour: accent)
  v(6pt)
  let bits = ()
  if id.email != "" {
    bits.push(link("mailto:" + id.email)[#id.email])
  }
  if id.phone != "" {
    bits.push(link("tel:" + id.phone.replace(" ", ""))[#id.phone])
  }
  if id.location != "" {
    bits.push([#id.location])
  }
  for l in id.links {
    if l.url != "" {
      bits.push(link(l.url)[#l.label])
    }
  }
  set text(size: size.small, fill: muted)
  let dot = [#h(5pt)#text(fill: hair)[·]#h(5pt)]
  bits.join(dot)
}

#let experience(jobs) = jobs.map((j) => entry(
  [#j.start#h(4pt)–#h(4pt)#j.end],
  j.company,
  sub: j.role,
  note: j.note,
  points: j.bullets,
  stack: j.stack,
))

#let credentials(items) = items.map((it) => entry(
  it.at("dates", default: ""),
  it.head,
  sub: it.at("sub", default: ""),
  note: it.at("note", default: ""),
  url: it.at("url", default: ""),
  bar: hair,
))
