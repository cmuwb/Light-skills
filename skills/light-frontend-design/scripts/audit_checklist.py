#!/usr/bin/env python3
"""audit_checklist.py — mechanical, countable layout-quality checks.

Each rule returns Pass/Fail with the actual count vs. threshold, so a human or
agent can verify objectively (no "looks good" hand-waving). Rules implement the
upgrade brief's countable checklist:

  R1 eyebrow instances        <= ceil(sectionCount / 3)
  R2 consecutive image+text   <= 2 in a row
  R3 layout-family diversity  >= 4 distinct families when sections >= 8
  R4 hero subtext             <= 20 words AND <= 4 lines
  R5 nav height               single line, <= 80px
  R6 bento grid               N content items == N cells (no empty/overflow)

Input: an HTML string/file annotated with light data-attributes so the check is
unambiguous (the skill's templates emit these). Pure stdlib (html.parser); no
deps. Runs a synthetic self-test under __main__.
"""
from __future__ import annotations
import math
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser


@dataclass
class Section:
    layout_family: str = ""          # data-layout="split|bento|hero|full|grid|stack"
    has_eyebrow: bool = False        # element with data-role="eyebrow"
    is_image_text_split: bool = False
    order: int = 0


@dataclass
class Doc:
    sections: list[Section] = field(default_factory=list)
    hero_subtext: str = ""
    nav_height_px: float | None = None
    nav_single_line: bool = True
    bento_cells: int = 0
    bento_items: int = 0


class _Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.doc = Doc()
        self._order = 0
        self._capture_hero = False
        self._hero_buf: list[str] = []

    def handle_starttag(self, tag: str, attrs_list):
        attrs = dict(attrs_list)
        role = attrs.get("data-role", "")
        if tag == "section":
            self._order += 1
            s = Section(
                layout_family=attrs.get("data-layout", ""),
                is_image_text_split=attrs.get("data-layout", "") == "split",
                order=self._order,
            )
            self.doc.sections.append(s)
        if role == "eyebrow" and self.doc.sections:
            self.doc.sections[-1].has_eyebrow = True
        if role == "hero-subtext":
            self._capture_hero = True
        if role == "nav":
            h = attrs.get("data-height-px")
            if h:
                self.doc.nav_height_px = float(h)
            self.doc.nav_single_line = attrs.get("data-single-line", "true") == "true"
        if role == "bento":
            self.doc.bento_items = int(attrs.get("data-items", "0"))
            self.doc.bento_cells = int(attrs.get("data-cells", "0"))

    def handle_endtag(self, tag: str):
        if self._capture_hero and tag in ("p", "div", "span", "h1", "h2"):
            self._capture_hero = False

    def handle_data(self, data: str):
        if self._capture_hero:
            self._hero_buf.append(data)

    def close(self):
        super().close()
        self.doc.hero_subtext = " ".join(self._hero_buf).strip()
        return self.doc


@dataclass
class Result:
    rule: str
    passed: bool
    detail: str


def audit(html: str) -> list[Result]:
    doc = _Parser()
    doc.feed(html)
    doc.close()
    d = doc.doc
    n = len(d.sections)
    out: list[Result] = []

    # R1 eyebrow instances <= ceil(n/3)
    eyebrows = sum(1 for s in d.sections if s.has_eyebrow)
    cap = math.ceil(n / 3) if n else 0
    out.append(Result("R1 eyebrow<=ceil(sections/3)", eyebrows <= cap,
                      f"{eyebrows} eyebrows, cap {cap} ({n} sections)"))

    # R2 consecutive image+text split <= 2
    run = best = 0
    for s in d.sections:
        run = run + 1 if s.is_image_text_split else 0
        best = max(best, run)
    out.append(Result("R2 consecutive image+text split<=2", best <= 2,
                      f"longest split run = {best}"))

    # R3 layout-family diversity >= 4 when n >= 8
    fams = {s.layout_family for s in d.sections if s.layout_family}
    if n >= 8:
        out.append(Result("R3 layout families>=4 (n>=8)", len(fams) >= 4,
                          f"{len(fams)} families: {sorted(fams)}"))
    else:
        out.append(Result("R3 layout families>=4 (n>=8)", True,
                          f"skipped (n={n}<8); {len(fams)} families present"))

    # R4 hero subtext <= 20 words AND <= 4 lines
    words = len(d.hero_subtext.split()) if d.hero_subtext else 0
    lines = len([l for l in re.split(r"<br|\n", d.hero_subtext) if l.strip()]) or (1 if words else 0)
    out.append(Result("R4 hero subtext<=20 words & <=4 lines",
                      words <= 20 and lines <= 4,
                      f"{words} words, {lines} line(s)"))

    # R5 nav single line and <= 80px
    h = d.nav_height_px
    ok = (h is not None and h <= 80 and d.nav_single_line)
    out.append(Result("R5 nav single-line & <=80px", ok,
                      f"height={h}px, single_line={d.nav_single_line}"))

    # R6 bento N items == N cells
    ok6 = d.bento_cells == d.bento_items
    out.append(Result("R6 bento items==cells", ok6,
                      f"items={d.bento_items}, cells={d.bento_cells}"))
    return out


def render(results: list[Result]) -> str:
    lines = []
    for r in results:
        tag = "PASS" if r.passed else "FAIL"
        lines.append(f"[{tag}] {r.rule}: {r.detail}")
    n_pass = sum(1 for r in results if r.passed)
    lines.append(f"--- {n_pass}/{len(results)} rules passed ---")
    return "\n".join(lines)


_GOOD = """
<nav data-role="nav" data-height-px="64" data-single-line="true">logo</nav>
<section data-layout="hero">
  <span data-role="eyebrow">New</span>
  <h1>Title</h1>
  <p data-role="hero-subtext">Short punchy promise that stays well under twenty words total here.</p>
</section>
<section data-layout="split"><img/><div>text</div></section>
<section data-layout="split"><img/><div>text</div></section>
<section data-layout="bento" data-role="bento" data-items="4" data-cells="4"></section>
<section data-layout="full"><h2>full</h2></section>
<section data-layout="grid"><h2>grid</h2></section>
<section data-layout="stack"><h2>stack</h2></section>
<section data-layout="hero"><h2>cta</h2></section>
"""

_BAD = """
<nav data-role="nav" data-height-px="120" data-single-line="false">logo</nav>
<section data-layout="split"><span data-role="eyebrow">A</span><img/><div>t</div></section>
<section data-layout="split"><span data-role="eyebrow">B</span><img/><div>t</div></section>
<section data-layout="split"><span data-role="eyebrow">C</span><img/><div>t</div></section>
<section data-layout="hero">
  <p data-role="hero-subtext">This hero subtext is deliberately far too long because it keeps going and going well past the twenty word ceiling that the rule allows here today friend.</p>
</section>
<section data-layout="bento" data-role="bento" data-items="5" data-cells="6"></section>
"""

if __name__ == "__main__":
    print("=== GOOD doc (expect mostly PASS) ===")
    g = audit(_GOOD)
    print(render(g))
    assert all(r.passed for r in g), "GOOD doc should pass every rule"

    print("\n=== BAD doc (expect several FAIL) ===")
    b = audit(_BAD)
    print(render(b))
    failed = {r.rule for r in b if not r.passed}
    # R1, R2, R4, R5, R6 must all catch the bad doc
    for needle in ("R1", "R2", "R4", "R5", "R6"):
        assert any(needle in f for f in failed), f"{needle} should FAIL on BAD doc"

    print("\nself-test OK")
