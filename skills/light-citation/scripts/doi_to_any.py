#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""doi_to_any.py — DOI 一键转多格式引用。

通过 DOI.org 内容协商（Content Negotiation）一次取回 BibTeX 与 CSL JSON，
再由 CSL JSON 在本地排版成 GB/T 7714-2015（顺序编码制）中文国标文本。

实测端点（2026-06-06，HTTP 200）：
  curl -LH "Accept: application/x-bibtex" https://doi.org/10.1038/s41597-023-02555-8
  curl -LH "Accept: application/vnd.citationstyles.csl+json" https://doi.org/<doi>

诚实原则（CONVENTIONS §4）：只对真实 DOI 协商，不臆造字段；取不到即如实报错。

用法：
  python scripts/doi_to_any.py 10.1038/s41597-023-02555-8
  python scripts/doi_to_any.py 10.1038/... --format bibtex|csljson|gbt7714|all
"""
from __future__ import annotations

import argparse
import html
import json
import sys
import urllib.error
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

DOI_BASE = "https://doi.org/"
UA = "light-citation/1.0 (mailto:light.research@gmail.com)"
ACCEPT = {
    "bibtex": "application/x-bibtex",
    "csljson": "application/vnd.citationstyles.csl+json",
    "ris": "application/x-research-info-systems",
}


def _has_cjk(text: str) -> bool:
    """判断字符串是否含 CJK 汉字（用于推断 langid）。"""
    for ch in text or "":
        if "一" <= ch <= "鿿" or "㐀" <= ch <= "䶿":
            return True
    return False


def inject_langid(bibtex: str) -> str:
    """给 BibTeX 条目注入 langid 字段（GB/T 7714 排版必需）。

    按 author/title 是否含 CJK 字符判定：含汉字→langid={chinese}，否则→{english}。
    已存在 langid 的条目不重复注入。诚实原则：只依据真实字段判定，不臆造。
    """
    if not bibtex or "@" not in bibtex:
        return bibtex
    if "langid" in bibtex.lower():
        return bibtex
    lang = "chinese" if _has_cjk(bibtex) else "english"
    # 定位 @type{citekey, 后的首个逗号，在其后插入 langid 字段（兼容单行/多行）
    brace = bibtex.find("{")
    if brace == -1:
        return bibtex
    comma = bibtex.find(",", brace)
    if comma == -1:
        return bibtex
    return f"{bibtex[:comma + 1]} langid={{{lang}}},{bibtex[comma + 1:]}"


def negotiate(doi: str, kind: str, timeout: int = 30):
    """对 DOI 做内容协商，返回 (http_code, text)。kind ∈ ACCEPT。"""
    doi = doi.strip().replace("https://doi.org/", "").replace("doi:", "")
    req = urllib.request.Request(
        DOI_BASE + doi,
        headers={"Accept": ACCEPT[kind], "User-Agent": UA},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


# ---------- CSL JSON -> GB/T 7714-2015 顺序编码制排版 ----------
_TYPE_TAG = {
    "article-journal": "J",
    "paper-conference": "C",
    "book": "M",
    "chapter": "M",
    "thesis": "D",
    "report": "R",
    "patent": "P",
    "standard": "S",
    "dataset": "DS",
    "webpage": "EB/OL",
    "article": "J",
}


def _fmt_authors_gbt(authors, limit: int = 3) -> str:
    """GB/T 7714：作者≤3 全列，>3 取前 limit 加 '等'。姓前名后，名取首字母大写。"""
    if not authors:
        return "[佚名]"
    names = []
    for a in authors:
        if "literal" in a:
            names.append(a["literal"])
            continue
        fam = (a.get("family") or "").strip()
        giv = (a.get("given") or "").strip()
        if fam and giv:
            # 西文：FamilyName G. M.（缩写名）；中文姓名 family 已含全名时直接用
            initials = " ".join(p[0].upper() + "." for p in giv.replace(".", " ").split() if p)
            names.append(f"{fam} {initials}".strip())
        else:
            names.append(fam or giv or a.get("name", ""))
    if len(names) > limit:
        return ", ".join(names[:limit]) + ", 等"
    return ", ".join(names)


def csljson_to_gbt7714(csl: dict) -> str:
    """把单条 CSL JSON 排版成 GB/T 7714-2015 顺序编码制书目文本。"""
    typ = csl.get("type", "article-journal")
    tag = _TYPE_TAG.get(typ, "J")
    authors = _fmt_authors_gbt(csl.get("author") or [])
    title = html.unescape((csl.get("title") or "")).rstrip(".")
    container = html.unescape(csl.get("container-title") or csl.get("publisher") or "")
    issued = csl.get("issued", {}).get("date-parts", [[None]])
    year = issued[0][0] if issued and issued[0] else ""
    vol = csl.get("volume", "")
    issue = csl.get("issue", "")
    page = csl.get("page", "")
    doi = csl.get("DOI") or csl.get("DOI".lower(), "")

    parts = [f"{authors}. {title}[{tag}]."]
    if container:
        seg = f" {container}"
        if year:
            seg += f", {year}"
        if vol:
            seg += f", {vol}"
            if issue:
                seg += f"({issue})"
        if page:
            seg += f": {page}"
        parts.append(seg + ".")
    elif year:
        parts.append(f" {year}.")
    if doi:
        parts.append(f" DOI: {doi}.")
    return "".join(parts)


def main(argv=None):
    ap = argparse.ArgumentParser(description="DOI -> BibTeX / CSL JSON / GB-T 7714")
    ap.add_argument("doi", help="DOI，如 10.1038/s41597-023-02555-8")
    ap.add_argument("--format", default="all",
                    choices=["bibtex", "csljson", "gbt7714", "all"])
    args = ap.parse_args(argv)

    want = ["bibtex", "csljson", "gbt7714"] if args.format == "all" else [args.format]

    # gbt7714 与 csljson 都依赖 CSL JSON
    csl_obj = None
    if "csljson" in want or "gbt7714" in want:
        code, txt = negotiate(args.doi, "csljson")
        print(f"[content-negotiation csljson] HTTP {code}", file=sys.stderr)
        if code == 200:
            csl_obj = json.loads(txt)

    if "bibtex" in want:
        code, txt = negotiate(args.doi, "bibtex")
        print(f"[content-negotiation bibtex] HTTP {code}", file=sys.stderr)
        print("=== BibTeX ===")
        print(inject_langid(txt.strip()) if code == 200 else f"[ERROR HTTP {code}] {txt[:200]}")

    if "csljson" in want:
        print("=== CSL JSON ===")
        print(json.dumps(csl_obj, ensure_ascii=False, indent=2)
              if csl_obj else "[ERROR] 取 CSL JSON 失败")

    if "gbt7714" in want:
        print("=== GB/T 7714-2015（顺序编码制） ===")
        print(csljson_to_gbt7714(csl_obj) if csl_obj else "[ERROR] 缺 CSL JSON，无法排版")
    return 0


def _selftest():
    """__main__ 自测：真 DOI 实测，记 HTTP 码。"""
    doi = "10.1038/s41597-023-02555-8"
    print("### doi_to_any 自测 DOI:", doi)
    code_b, bib = negotiate(doi, "bibtex")
    print("BibTeX HTTP", code_b)
    assert code_b == 200 and "@" in bib, "bibtex 协商失败"
    bib_tagged = inject_langid(bib.strip())
    print(bib_tagged[:240], "...\n")
    assert "langid={english}" in bib_tagged, "英文条目应注入 langid=english"

    # langid 注入断言：含中文的条目应得到 langid=chinese
    cn_entry = (
        "@article{zhang2024shenjing,\n"
        "  title = {深度神经网络研究},\n"
        "  author = {张三 and 李四},\n"
        "  year = {2024},\n}"
    )
    cn_tagged = inject_langid(cn_entry)
    print("--- 中文条目 langid 注入 ---")
    print(cn_tagged)
    assert "langid={chinese}" in cn_tagged, "含中文条目应得到 langid=chinese"
    # 幂等：已含 langid 不重复注入
    assert inject_langid(cn_tagged).count("langid") == 1, "langid 注入应幂等"
    print("[OK] langid 注入断言通过\n")

    code_c, csl = negotiate(doi, "csljson")
    print("CSL JSON HTTP", code_c)
    assert code_c == 200, "csljson 协商失败"
    obj = json.loads(csl)
    print("title:", (obj.get("title") or "")[:60])

    print("\n--- GB/T 7714 排版 ---")
    print(csljson_to_gbt7714(obj))
    print("\n[OK] doi_to_any 自测通过（3 格式均产出，HTTP 200）")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        _selftest()
    else:
        sys.exit(main())
