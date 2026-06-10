#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mechanical_check.py — offline (no-API) mechanical issues for academic prose.

Catches what LanguageTool's generic grammar pass tends to miss in research
papers, and what reviewers flag fastest:

  1. Overclaim words      — unsupported strength adjectives/adverbs.
  2. AI-tone / filler      — phrases that read as machine-generated boilerplate.
  3. Hedge stacking        — piled-up hedges ("may possibly suggest").
  4. Passive overuse       — per-paragraph passive ratio over a threshold.
  5. Punctuation hygiene   — em-dash spacing, fullwidth punctuation in English,
                             double spaces, space-before-punctuation, Oxford-ish.

No network needed. Emits structured findings {line, col, category, issue,
suggestion, context}. Pure stdlib; runs anywhere.

Usage:
  python mechanical_check.py --file paper.txt
  python mechanical_check.py --text "..." --json
  echo "..." | python mechanical_check.py
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import argparse
import json
import re

# --- blacklists --------------------------------------------------------------
OVERCLAIM = [
    "significant", "significantly", "seminal", "novel", "groundbreaking",
    "revolutionary", "state-of-the-art", "cutting-edge", "remarkable",
    "remarkably", "dramatically", "drastically", "vastly", "tremendously",
    "extremely", "very", "highly effective", "extensive", "comprehensive",
    "superior", "outperforms", "best", "optimal", "perfect", "unprecedented",
    "clearly", "obviously", "undoubtedly", "certainly",
]
AI_TONE = [
    "in conclusion", "it is worth noting", "it is important to note",
    "it should be noted", "in today's world", "in the modern era",
    "delve into", "delving into", "a testament to", "plays a crucial role",
    "plays a vital role", "plays a pivotal role", "navigating the",
    "in the realm of", "shed light on", "pave the way", "paves the way",
    "leverage the power", "harness the power", "rich tapestry",
    "ever-evolving", "ever-changing", "first and foremost", "furthermore",
    "moreover", "in summary", "to summarize", "needless to say",
]
HEDGES = ["may", "might", "could", "possibly", "perhaps", "seem", "seems",
          "appear", "appears", "suggest", "suggests", "potentially",
          "arguably", "likely", "probably", "somewhat", "relatively"]

# Hedging 校准阶梯：强主张词 → 建议的降级替换（证据不足时往右降）。
# 见 references/argument_review.md 第 2 节。只在出现这些强词时提示，
# 是否真该降级仍需看证据强度，由作者判断。
CLAIM_DOWNGRADE = {
    "prove": "show / demonstrate（除非是数学证明，否则别用 prove）",
    "proves": "shows / demonstrates",
    "proven": "shown",
    "conclusively": "（删，或换 the results indicate）",
    "definitively": "（删，或换 indicate）",
    "unprecedented": "to our knowledge the first",
    "guarantees": "is expected to / typically",
    "always": "in our experiments / consistently",
    "never": "in no observed case",
    "proves that": "suggests that / indicates that",
}

# passive: form of "be" + past participle (heuristic, accepts -ed and common irregulars)
PASSIVE_RE = re.compile(
    r"\b(is|are|was|were|be|been|being|am)\s+(\w+ed|done|made|shown|given|"
    r"found|seen|taken|used|built|set|known|held|kept|sent|put|drawn|"
    r"chosen|written|proposed|obtained|achieved|performed|trained)\b",
    re.IGNORECASE,
)
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def linecol(text, off):
    prefix = text[:off]
    return prefix.count("\n") + 1, off - (prefix.rfind("\n") + 1) + 1


def ctx(text, s, e):
    return text[max(0, s - 25):e + 25].replace("\n", " ")


def add(out, text, s, e, cat, issue, sug):
    line, col = linecol(text, s)
    out.append({"line": line, "col": col, "category": cat, "issue": issue,
                "suggestion": sug, "context": ctx(text, s, e)})


def scan_phrases(text, out, words, cat, issue_tmpl, sug):
    for w in words:
        pat = r"\b" + re.escape(w).replace(r"\ ", r"\s+") + r"\b"
        for m in re.finditer(pat, text, re.IGNORECASE):
            add(out, text, m.start(), m.end(), cat,
                issue_tmpl.format(w=m.group(0)), sug)


def check_passive(text, out, threshold=0.4):
    """Flag paragraphs whose passive-sentence ratio exceeds threshold."""
    para_start = 0
    for para in re.split(r"(\n\s*\n)", text):
        if para.strip() and not para.isspace():
            sents = [s for s in SENT_SPLIT.split(para) if s.strip()]
            if len(sents) >= 3:
                npass = sum(1 for s in sents if PASSIVE_RE.search(s))
                ratio = npass / len(sents)
                if ratio > threshold:
                    line, col = linecol(text, para_start)
                    out.append({
                        "line": line, "col": col, "category": "passive_overuse",
                        "issue": f"{npass}/{len(sents)} sentences passive "
                                 f"({ratio:.0%} > {threshold:.0%}).",
                        "suggestion": "Rewrite some sentences in active voice "
                                      "(e.g. 'We trained...' not 'was trained').",
                        "context": para.strip()[:60].replace("\n", " "),
                    })
        para_start += len(para)
    # also flag every individual passive (fine-grained), capped
    for i, m in enumerate(PASSIVE_RE.finditer(text)):
        if i >= 50:
            break
        add(out, text, m.start(), m.end(), "passive_voice",
            f"Passive construction '{m.group(0)}'.",
            "Consider active voice if the agent matters.")


def check_punctuation(text, out):
    for m in re.finditer(r"\w-{2,3}\w|\s—\w|\w—\s", text):
        add(out, text, m.start(), m.end(), "punctuation",
            "Em-dash spacing inconsistent (mix of -- and — / missing or stray spaces).",
            "Pick one style: spaced em-dash ' — ' or unspaced '—'; be consistent.")
    for m in re.finditer(r"[，。；：（）！？、“”‘’]", text):
        add(out, text, m.start(), m.end(), "punctuation",
            f"Fullwidth/CJK punctuation '{m.group(0)}' in English text.",
            "Replace with ASCII equivalent (, . ; : ( ) ! ? \" ').")
    for m in re.finditer(r"\S {2,}\S", text):
        add(out, text, m.start(), m.end(), "punctuation",
            "Multiple consecutive spaces.", "Collapse to a single space.")
    for m in re.finditer(r"\s+[,.;:!?]", text):
        add(out, text, m.start(), m.end(), "punctuation",
            "Space before punctuation.", "Remove the space before the mark.")


def check_hedge_stack(text, out):
    """Two+ hedges within a short window = wishy-washy."""
    hedge_pat = r"\b(" + "|".join(HEDGES) + r")\b"
    for sent in SENT_SPLIT.split(text):
        hits = list(re.finditer(hedge_pat, sent, re.IGNORECASE))
        if len(hits) >= 2:
            s = text.find(sent)
            if s >= 0:
                words = ", ".join(h.group(0) for h in hits)
                add(out, text, s, s + len(sent), "hedge_stacking",
                    f"Stacked hedges ({words}) weaken the claim.",
                    "Keep at most one hedge; commit to the finding.")


def check_claim_strength(text, out):
    """Hedging 校准阶梯：强主张词给出建议的降级替换（见 argument_review.md §2）。"""
    for word, repl in CLAIM_DOWNGRADE.items():
        pat = re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE)
        for m in pat.finditer(text):
            add(out, text, m.start(), m.end(), "claim_strength",
                f"Strong claim '{m.group(0)}' — match assertion strength to evidence.",
                f"If evidence is not conclusive, downgrade: {repl}")


def run(text):
    out = []
    scan_phrases(text, out, OVERCLAIM, "overclaim",
                 "Overclaim/unsupported intensifier '{w}'.",
                 "Replace with measurable evidence or delete.")
    scan_phrases(text, out, AI_TONE, "ai_tone",
                 "AI-tone / filler phrase '{w}'.",
                 "Cut or rewrite directly; reviewers read it as boilerplate.")
    check_hedge_stack(text, out)
    check_claim_strength(text, out)
    check_passive(text, out)
    check_punctuation(text, out)
    out.sort(key=lambda f: (f["line"], f["col"]))
    cats = {}
    for f in out:
        cats[f["category"]] = cats.get(f["category"], 0) + 1
    return {"_meta": {"n_findings": len(out), "by_category": cats}, "findings": out}



def _selftest() -> int:
    sample = ("In conclusion, our novel method significantly outperforms all baselines. "
              "It is worth noting that the results was obtained and were evaluated . "
              "This may possibly suggest a remarkable improvement ， which proves that the method is state-of-the-art.")
    result = run(sample)
    meta = result["_meta"]
    cats = meta["by_category"]
    assert meta["n_findings"] >= 6, meta
    for cat in ("overclaim", "ai_tone", "hedge_stacking", "punctuation", "claim_strength"):
        assert cats.get(cat, 0) >= 1, cats
    print(f"[selftest] PASS mechanical_check findings={meta['n_findings']}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Offline mechanical paper check.")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--text")
    g.add_argument("--file")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true", help="run offline synthetic self-test")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(_selftest())

    if args.text is not None:
        text = args.text
    elif args.file:
        with open(args.file, encoding="utf-8") as f:
            text = f.read()
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        text = ("In conclusion, our novel method significantly outperforms "
                "all baselines. It is worth noting that the results was "
                "obtained and were evaluated . This may possibly suggest a "
                "remarkable improvement ， which is clearly state-of-the-art.")
        print("[self-test: no input given, using built-in sample]\n", file=sys.stderr)

    result = run(text)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    m = result["_meta"]
    print(f"findings={m['n_findings']}  by_category={m['by_category']}")
    for f in result["findings"]:
        print(f"  L{f['line']}:C{f['col']} [{f['category']}] {f['issue']}")
        print(f"      → {f['suggestion']}")


if __name__ == "__main__":
    main()
