#!/usr/bin/env python3
"""ai_tell_lint.py — mechanically flag the "AI-generated" tells.

Scans HTML/JSX/CSS source text for the blacklisted patterns from the skill's
AI-tell section. Each finding reports file position + the offending snippet so
it can be verified and fixed. Pure stdlib. Self-tests under __main__.

Blacklist (all machine-detectable):
  T1 scroll cue        : "scroll down", "scroll to explore", a bouncing
                         chevron/mouse hint near the hero.
  T2 section-numbering : eyebrow text like "01 /", "02.", "(01)" used as a
                         decorative section counter.
  T3 version footer    : "v1.0.0", "Made with", "Powered by <generic>" style
                         filler footers.
  T4 em-dash           : the literal em-dash character used as prose punctuation
                         (a notorious LLM tell). Suggests en-dash/comma/rewrite.
"""
from __future__ import annotations
import re
from dataclasses import dataclass


@dataclass
class Finding:
    rule: str
    line: int
    snippet: str


# T1 scroll cues
_SCROLL = re.compile(
    r"(scroll\s*(down|to\s*explore|for\s*more)|scroll-(cue|hint|indicator)|"
    r"\bbounc\w*\s+(chevron|arrow|mouse))",
    re.I,
)
# T2 decorative section numbering used as eyebrow ("01 /", "02.", "(03)")
_SECNUM = re.compile(r"""(data-role=["']eyebrow["'][^>]*>\s*\(?0?\d{1,2}\s*[./)])""", re.I)
_SECNUM_TEXT = re.compile(r">\s*\(?0\d\s*[./)]\s*<")
# T3 version / "made with" footers
_VERSION = re.compile(r"(v\d+\.\d+\.\d+|made\s+with\s+(love|❤|claude|ai|v0)|powered\s+by\s+\w+)", re.I)
# T4 em-dash as punctuation (the em-dash char itself)
_EMDASH = re.compile("—")


def lint(text: str) -> list[Finding]:
    findings: list[Finding] = []
    for i, line in enumerate(text.splitlines(), 1):
        for rule, rx in (
            ("T1 scroll-cue", _SCROLL),
            ("T2 section-numbering eyebrow", _SECNUM),
            ("T2 section-numbering eyebrow", _SECNUM_TEXT),
            ("T3 version/made-with footer", _VERSION),
            ("T4 em-dash", _EMDASH),
        ):
            m = rx.search(line)
            if m:
                snip = line.strip()[:80]
                findings.append(Finding(rule, i, snip))
    return findings


def render(findings: list[Finding]) -> str:
    if not findings:
        return "CLEAN: no AI-tells found."
    return "\n".join(f"L{f.line} [{f.rule}] {f.snippet}" for f in findings)


_DIRTY = """
<section data-layout="hero">
  <span data-role="eyebrow">01 / Intro</span>
  <h1>Hi</h1>
  <a class="scroll-cue">Scroll down to explore</a>
</section>
<p>We move fast — then we ship.</p>
<footer>Made with love · v1.2.3 · Powered by Acme</footer>
"""

_CLEAN = """
<section data-layout="hero">
  <span data-role="eyebrow">New release</span>
  <h1>Hi</h1>
</section>
<p>We move fast, then we ship.</p>
<footer>(c) 2026 Acme. All rights reserved.</footer>
"""

if __name__ == "__main__":
    print("=== DIRTY (expect findings T1-T4) ===")
    d = lint(_DIRTY)
    print(render(d))
    rules = {f.rule[:2] for f in d}
    for needle in ("T1", "T2", "T3", "T4"):
        assert needle in rules, f"{needle} should be flagged in DIRTY"

    print("\n=== CLEAN (expect none) ===")
    c = lint(_CLEAN)
    print(render(c))
    assert not c, "CLEAN doc should have zero findings"

    print("\nself-test OK")