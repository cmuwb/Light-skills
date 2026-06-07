#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""precheck_log.py — 扫描 LaTeX .log，汇总编译问题报告（纯标准库，无外部依赖）。

抓取：
  - Undefined references / citations（未定义引用、未定义文献）
  - Multiply defined labels（重复标签）
  - Overfull / Underfull \\hbox & \\vbox（盒子溢出）
  - Missing figure / file not found（图片/文件找不到）
  - Undefined control sequence（未定义命令，常因缺宏包）
  - Missing $ inserted / runaway argument 等致命错误（LaTeX Error / ! 行）
  - Font / package warnings 汇总计数

用法：
  python precheck_log.py path/to/file.log [--json] [--max N]
  无参数运行 → 跑内置样例 log 自测。

退出码：0=无致命错误；1=存在 LaTeX Error / undefined control sequence 等致命项。
"""
from __future__ import annotations
import sys
import re
import json
import argparse
from collections import Counter

# --- 正则规则表：(键, 严重度, 编译后的正则, 说明) ---------------------------
SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}

RULES = [
    ("latex_error", "error",
     re.compile(r"^! LaTeX Error: (.+)$", re.M),
     "LaTeX 致命错误"),
    ("tex_error", "error",
     re.compile(r"^! (Undefined control sequence|Missing \$ inserted|"
                r"Missing \} inserted|Runaway argument|Emergency stop|"
                r"Paragraph ended before|Too many \}|Extra \}|"
                r"Double superscript|Misplaced alignment)\.?", re.M),
     "TeX 引擎致命错误"),
    ("undef_ref", "warning",
     re.compile(r"(?:Reference|LaTeX Warning: Reference) [`'\"]([^'\"]+)['\"] "
                r"on page \d+ undefined", re.M),
     "未定义的交叉引用 \\ref/\\label"),
    ("undef_cite", "warning",
     re.compile(r"(?:Citation|LaTeX Warning: Citation) [`'\"]([^'\"]+)['\"] "
                r"on page \d+ undefined", re.M),
     "未定义的文献引用 \\cite（多半要跑 bibtex/biber）"),
    ("multiply_label", "warning",
     re.compile(r"LaTeX Warning: Label [`'\"]([^'\"]+)['\"] multiply defined", re.M),
     "标签重复定义"),
    ("overfull_hbox", "warning",
     re.compile(r"^Overfull \\hbox \(([\d.]+)pt too wide\)(.*)$", re.M),
     "Overfull \\hbox（行内容过宽，可能溢出页边）"),
    ("underfull_hbox", "info",
     re.compile(r"^Underfull \\hbox \(badness (\d+)\)(.*)$", re.M),
     "Underfull \\hbox（行内容过稀）"),
    ("overfull_vbox", "warning",
     re.compile(r"^Overfull \\vbox \(([\d.]+)pt too high\)(.*)$", re.M),
     "Overfull \\vbox（竖向溢出）"),
    ("missing_file", "error",
     re.compile(r"(?:! LaTeX Error: File [`'\"]([^'\"]+)['\"] not found|"
                r"^! Unable to load picture or PDF file [`'\"]?([^'\".]+\.\w+)['\"]?)", re.M),
     "找不到文件/图片"),
    ("missing_graphic", "error",
     re.compile(r"LaTeX Warning: File [`'\"]([^'\"]+)['\"] not found", re.M),
     "graphicx 找不到图片文件"),
    ("rerun", "info",
     re.compile(r"(Rerun to get cross-references right|"
                r"Label\(s\) may have changed)", re.M),
     "需要再次编译以收敛交叉引用/目录"),
    ("font_warning", "info",
     re.compile(r"^LaTeX Font Warning: (.+)$", re.M),
     "字体警告"),
    ("pkg_warning", "info",
     re.compile(r"^Package (\w+) Warning: (.+)$", re.M),
     "宏包警告"),
]


def scan(text: str) -> dict:
    """扫描 log 文本，返回结构化结果。"""
    findings = {}
    for key, sev, rx, desc in RULES:
        hits = []
        for m in rx.finditer(text):
            # 取第一个非空捕获组作为可读详情；无组则取整行
            groups = [g for g in m.groups() if g]
            detail = " | ".join(groups) if groups else m.group(0).strip()
            hits.append(detail.strip())
        if hits:
            findings[key] = {"severity": sev, "desc": desc,
                             "count": len(hits), "items": hits}
    return findings


def summarize(findings: dict, max_items: int = 8) -> str:
    """生成人类可读报告。"""
    if not findings:
        return "OK: 未发现 undefined refs / overfull hbox / missing figure 等问题。"
    lines = []
    sev_counts = Counter()
    for f in findings.values():
        sev_counts[f["severity"]] += f["count"]
    head = (f"发现问题：errors={sev_counts['error']} "
            f"warnings={sev_counts['warning']} infos={sev_counts['info']}")
    lines.append(head)
    lines.append("=" * len(head))
    # 按严重度排序输出
    for key in sorted(findings,
                      key=lambda k: SEVERITY_ORDER[findings[k]["severity"]]):
        f = findings[key]
        tag = {"error": "[ERR ]", "warning": "[WARN]", "info": "[INFO]"}[f["severity"]]
        lines.append(f"\n{tag} {key} ×{f['count']} — {f['desc']}")
        for item in f["items"][:max_items]:
            lines.append(f"    - {item}")
        if f["count"] > max_items:
            lines.append(f"    ... 其余 {f['count'] - max_items} 条省略")
    return "\n".join(lines)


def has_fatal(findings: dict) -> bool:
    return any(f["severity"] == "error" for f in findings.values())


SAMPLE_LOG = r"""
This is pdfTeX, Version 3.141592653-2.6-1.40.25 (TeX Live 2023)
(./paper.tex
LaTeX2e <2023-11-01>
(./IEEEtran.cls
Document Class: IEEEtran 2015/08/26 V1.8b)
! Undefined control sequence.
l.42 \includegrpahics
                     [width=\linewidth]{fig1.png}
! LaTeX Error: File `fig1.png' not found.
See the LaTeX manual or LaTeX Companion for explanation.
LaTeX Warning: File `results/plot.pdf' not found on input line 88.
Overfull \hbox (15.2pt too wide) in paragraph at lines 120--122
[]\OT1/cmr/m/n/10 This is a very long line that does not fit nicely
Underfull \hbox (badness 1300) in paragraph at lines 130--131
LaTeX Warning: Reference `fig:arch' on page 3 undefined on input line 145.
LaTeX Warning: Citation `smith2020' on page 4 undefined on input line 200.
LaTeX Warning: Citation `doe2019' on page 4 undefined on input line 201.
LaTeX Warning: Label `sec:intro' multiply defined.
LaTeX Font Warning: Font shape `OT1/cmr/bx/sc' undefined.
Package hyperref Warning: Token not allowed in a PDF string.
LaTeX Warning: There were undefined references.
LaTeX Warning: Label(s) may have changed. Rerun to get cross-references right.
)
"""


def main(argv=None):
    p = argparse.ArgumentParser(description="扫描 LaTeX .log 汇总编译问题")
    p.add_argument("logfile", nargs="?", help="LaTeX .log 路径；省略则跑内置自测")
    p.add_argument("--json", action="store_true", help="输出 JSON")
    p.add_argument("--max", type=int, default=8, help="每类最多展示条数")
    args = p.parse_args(argv)

    if args.logfile:
        with open(args.logfile, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        src = args.logfile
    else:
        text = SAMPLE_LOG
        src = "<内置样例 log（自测）>"

    findings = scan(text)
    if args.json:
        print(json.dumps({"source": src, "fatal": has_fatal(findings),
                          "findings": findings}, ensure_ascii=False, indent=2))
    else:
        print(f"# precheck_log 报告 — 来源: {src}\n")
        print(summarize(findings, args.max))
    return 1 if has_fatal(findings) else 0


if __name__ == "__main__":
    sys.exit(main())
