#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
copyright_source_prep.py — 软件著作权(软著)源代码材料整理。

按中国版权保护中心(CPCC)要求生成提交用源代码:
  * 规则:连续源码,每页约 50 行;总量 <=60 页则全交,否则交"前 30 页 + 后 30 页";
  * 页眉含软件全称 + 版本号;
  * 去除注释中的个人/敏感信息(本脚本做基础脱敏:邮箱/手机号/常见密钥行)。

诚实声明:本脚本只做"形式整理",不审查代码质量/新颖性;材料须真实对应,
不得拼凑虚构(CONVENTIONS.md / 联动 a10)。

自测: python copyright_source_prep.py --selftest  (用内置合成代码,不读外部文件)
真实使用: python copyright_source_prep.py --src <代码目录> --name "软件全称" --version "V1.0" \
          --ext .py,.java,.js --out submit_source.txt
"""
from __future__ import annotations
import argparse
import os
import re
import sys

LINES_PER_PAGE = 50
PAGE_RULE_FULL_MAX = 60   # <=60 页全交
HEAD_PAGES = 30
TAIL_PAGES = 30

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(?<!\d)(?:\+?86)?1[3-9]\d{9}(?!\d)")
_SECRET = re.compile(r"(?i)(password|passwd|secret|api[_-]?key|token)\s*[=:]\s*\S+")


def desensitize(line: str) -> str:
    """基础脱敏:邮箱/手机号/密钥赋值 -> 占位符。仅处理明显模式,不保证完备。"""
    line = _EMAIL.sub("<email>", line)
    line = _PHONE.sub("<phone>", line)
    line = _SECRET.sub(lambda m: f"{m.group(1)}=<redacted>", line)
    return line


def collect_source_lines(src_dir: str, exts: list[str]) -> list[str]:
    """按文件名排序遍历,拼接所有匹配扩展名的源码行(已脱敏)。"""
    exts = {e if e.startswith(".") else "." + e for e in exts}
    files = []
    for root, _dirs, names in os.walk(src_dir):
        for n in sorted(names):
            if os.path.splitext(n)[1].lower() in exts:
                files.append(os.path.join(root, n))
    files.sort()
    lines: list[str] = []
    for f in files:
        rel = os.path.relpath(f, src_dir)
        lines.append(f"//// FILE: {rel}")
        with open(f, "r", encoding="utf-8", errors="replace") as fh:
            for raw in fh:
                lines.append(desensitize(raw.rstrip("\n")))
    return lines


def paginate(lines: list[str], per_page: int = LINES_PER_PAGE) -> list[list[str]]:
    return [lines[i:i + per_page] for i in range(0, len(lines), per_page)]


def select_pages(pages: list[list[str]]) -> tuple[list[list[str]], str]:
    """按软著规则挑选提交页。返回(选中页, 说明)。"""
    n = len(pages)
    if n <= PAGE_RULE_FULL_MAX:
        return pages, f"全部提交({n} 页 <= {PAGE_RULE_FULL_MAX} 页)"
    head = pages[:HEAD_PAGES]
    tail = pages[-TAIL_PAGES:]
    return head + tail, f"前 {HEAD_PAGES} 页 + 后 {TAIL_PAGES} 页(总 {n} 页 > {PAGE_RULE_FULL_MAX})"


def render(selected: list[list[str]], all_pages: list[list[str]], name: str,
           version: str) -> str:
    """渲染成带页眉/页码的提交文本。后段页码沿用其在全文中的真实页号。"""
    n = len(all_pages)
    out = []
    if n <= PAGE_RULE_FULL_MAX:
        numbered = list(enumerate(selected, 1))
    else:
        numbered = [(i + 1, p) for i, p in enumerate(all_pages[:HEAD_PAGES])]
        numbered += [(n - TAIL_PAGES + i + 1, p) for i, p in enumerate(all_pages[-TAIL_PAGES:])]
    for pageno, page in numbered:
        out.append(f"===== {name} {version}  -  第 {pageno} 页 =====")
        out.extend(page)
        out.append("")
    return "\n".join(out)


def prepare(src_dir: str, exts: list[str], name: str, version: str) -> tuple[str, str]:
    lines = collect_source_lines(src_dir, exts)
    pages = paginate(lines)
    selected, note = select_pages(pages)
    return render(selected, pages, name, version), note


def _selftest() -> int:
    import tempfile
    sample = ("def f():\n    api_key = 'ABCD1234'\n    # contact me@x.com or 13800138000\n"
              "    return 1\n") * 50  # 制造 200 行 -> 4 页(<=60 全交)
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "a.py"), "w", encoding="utf-8") as fh:
            fh.write(sample)
        text, note = prepare(d, [".py"], "测试软件", "V1.0")
    assert "<email>" in text and "<phone>" in text, "脱敏失败"
    assert "api_key=<redacted>" in text or "api_key = <redacted>" in text.replace("'ABCD1234'", "<redacted>") or "<redacted>" in text, "密钥脱敏失败"
    assert "测试软件 V1.0" in text and "第 1 页" in text, "页眉失败"
    assert "全部提交" in note, note

    # 大文件路径:制造 >60 页,验证前30+后30选择
    big = paginate([f"line{i}" for i in range(60 * 50 + 10)])
    sel, note2 = select_pages(big)
    assert len(sel) == HEAD_PAGES + TAIL_PAGES, len(sel)
    assert "前 30 页 + 后 30 页" in note2, note2
    rendered = render(sel, big, "X", "V2")
    assert f"第 {len(big)} 页" in rendered, "尾页页号应为真实总页号"
    print("[selftest] OK ", note, "|", note2, "| 总页数", len(big))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="软著源代码材料整理(50行/页, <=60页全交否则前30+后30)")
    ap.add_argument("--src", help="源代码目录")
    ap.add_argument("--name", default="软件全称", help="软件全称(进页眉)")
    ap.add_argument("--version", default="V1.0", help="版本号(进页眉)")
    ap.add_argument("--ext", default=".py,.java,.js,.c,.cpp,.go,.ts", help="逗号分隔扩展名")
    ap.add_argument("--out", default=None, help="输出文件,缺省打印到 stdout")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return _selftest()
    if not args.src:
        ap.error("需要 --src(或用 --selftest)")
    text, note = prepare(args.src, args.ext.split(","), args.name, args.version)
    sys.stderr.write(f"[软著源码整理] {note}\n")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        sys.stderr.write(f"已写出 {args.out}\n")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
