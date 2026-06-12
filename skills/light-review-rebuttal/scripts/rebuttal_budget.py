#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rebuttal_budget.py — 会议 rebuttal 字数/页数预算检查（纯标准库，离线）。

会议 rebuttal 常有硬性 1 页或字数上限（ICLR/NeurIPS 等），超限直接被截断或拒收。
本脚本对 response letter / rebuttal 文本做预算核对：词数、字符数、估算页数，
对照所选会议预设上限给 PASS/WARN/FAIL。中英混排分别计词（英文按空白切，中文按字符）。

用法:
    python rebuttal_budget.py rebuttal.md --venue iclr
    python rebuttal_budget.py rebuttal.md --max-words 1000
    cat rebuttal.md | python rebuttal_budget.py --venue neurips
    python rebuttal_budget.py --selftest        # 离线自检，不读外部文件

预设上限仅为常见档位的工程近似，**以目标会议当年征稿/返修说明为准**（量纲逐年变）。
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

import argparse  # noqa: E402
import re  # noqa: E402
import unicodedata  # noqa: E402

# 常见会议 rebuttal 预算近似（words 上限 / 是否 1 页限）。须以官方当年说明为准。
VENUE_LIMITS = {
    "iclr": {"max_words": 0, "note": "ICLR 常按字符/markdown 框，单条 review 回复 ~5000 字符；按 markdown 框计"},
    "neurips": {"max_words": 0, "note": "NeurIPS 近年用单页 PDF 或固定字符框；以 OpenReview 当年框为准"},
    "cvpr": {"max_words": 0, "note": "CVPR rebuttal 限 1 页 PDF（含图表）"},
    "generic-1page": {"max_words": 650, "note": "1 页 ~650 词工程近似（单栏 11pt）"},
}

# 1 页纯文本词数近似（单栏，去掉图表）。仅用于估页，不作硬判。
WORDS_PER_PAGE = 650


def count_words(text):
    """中英混排计词：英文/数字按空白切分的 token；中日韩表意字符逐字计。"""
    cjk = 0
    for ch in text:
        if _is_cjk(ch):
            cjk += 1
    # 去掉 CJK 后按空白切，得拉丁词数
    latin_text = "".join(" " if _is_cjk(ch) else ch for ch in text)
    latin = len([t for t in re.split(r"\s+", latin_text) if t.strip()])
    return latin + cjk, latin, cjk


def _is_cjk(ch):
    try:
        name = unicodedata.name(ch)
    except ValueError:
        return False
    return "CJK" in name or "HIRAGANA" in name or "KATAKANA" in name


def strip_markup(text):
    """粗去 markdown 噪声（代码块/行内码/链接 URL/标题井号），让计词更接近正文。"""
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)  # 链接保留锚文本
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    return text


def assess(text, max_words, strip=True):
    body = strip_markup(text) if strip else text
    total, latin, cjk = count_words(body)
    pages = total / WORDS_PER_PAGE
    result = {
        "words_total": total, "words_latin": latin, "words_cjk": cjk,
        "chars": len(body), "est_pages": round(pages, 2), "max_words": max_words,
    }
    if max_words and max_words > 0:
        if total > max_words:
            result["verdict"] = "FAIL"
            result["msg"] = f"超限 {total - max_words} 词（{total}/{max_words}）"
        elif total > max_words * 0.9:
            result["verdict"] = "WARN"
            result["msg"] = f"逼近上限（{total}/{max_words}，余 {max_words - total} 词）"
        else:
            result["verdict"] = "PASS"
            result["msg"] = f"在预算内（{total}/{max_words}）"
    else:
        result["verdict"] = "INFO"
        result["msg"] = f"未设词数上限；估算 {result['est_pages']} 页（{total} 词，按 {WORDS_PER_PAGE} 词/页）"
    return result


def _render(r, venue_note=None):
    lines = [
        f"[{r['verdict']}] {r['msg']}",
        f"  词数: {r['words_total']}（拉丁 {r['words_latin']} + CJK {r['words_cjk']}）",
        f"  字符: {r['chars']}    估算页数: {r['est_pages']}",
    ]
    if venue_note:
        lines.append(f"  注: {venue_note}")
    return "\n".join(lines)


def _selftest():
    # 1) 英文短文本在 generic-1page 预算内 -> PASS
    r = assess("This is a short rebuttal. " * 10, 650)
    assert r["verdict"] == "PASS", r
    # 2) 超长 -> FAIL
    r2 = assess("word " * 800, 650)
    assert r2["verdict"] == "FAIL", r2
    assert r2["words_total"] == 800, r2
    # 3) 逼近上限 -> WARN
    r3 = assess("word " * 600, 650)
    assert r3["verdict"] == "WARN", r3
    # 4) 中英混排计词：5 个中文字 + 2 英文词
    n, lat, cjk = count_words("方法学有效 good work")
    assert cjk == 5 and lat == 2, (n, lat, cjk)
    # 5) markdown 去噪：代码块与链接不灌水
    body = strip_markup("see [paper](http://x.com/very/long/url) ```code block ignored```")
    assert "http" not in body and "code block" not in body, body
    # 6) 无上限 -> INFO + 估页
    r6 = assess("word " * 1300, 0)
    assert r6["verdict"] == "INFO" and r6["est_pages"] == 2.0, r6
    print("[selftest] PASS rebuttal_budget（计词/预算判定/中英混排/markdown去噪/估页）")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="会议 rebuttal 字数/页数预算检查")
    ap.add_argument("file", nargs="?", help="rebuttal 文本文件（缺省读 stdin）")
    ap.add_argument("--venue", choices=sorted(VENUE_LIMITS), help="按预设会议取上限")
    ap.add_argument("--max-words", type=int, default=None, help="自定义词数上限（覆盖 --venue）")
    ap.add_argument("--no-strip", action="store_true", help="不去 markdown 噪声，按原文计")
    ap.add_argument("--selftest", action="store_true", help="离线自检")
    args = ap.parse_args(argv)

    if args.selftest:
        return _selftest()

    note = None
    max_words = args.max_words
    if max_words is None and args.venue:
        max_words = VENUE_LIMITS[args.venue]["max_words"]
        note = VENUE_LIMITS[args.venue]["note"]
    if max_words is None:
        max_words = 0  # 无上限 -> INFO/估页

    if args.file:
        with open(args.file, encoding="utf-8") as f:
            text = f.read()
    else:
        text = sys.stdin.read()
    if not text.strip():
        ap.error("输入为空（给文件或从 stdin 喂文本）")

    r = assess(text, max_words, strip=not args.no_strip)
    print(_render(r, note))
    return 1 if r["verdict"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
