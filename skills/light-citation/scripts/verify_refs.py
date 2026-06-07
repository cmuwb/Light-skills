#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_refs.py — 一批 DOI 的真实性 + 元数据一致性核验，产机读 JSON 报告。

对每个 DOI 同时查 Crossref `/works/{doi}` 与 OpenAlex `/works/https://doi.org/{doi}`，
核对：是否存在、标题/年份是否一致、被引数、是否自引、出版年龄。
汇总：中外文献占比、自引率、缺近 2 年标志、errors[].severity / warnings[]。

实测端点（2026-06-06，均 HTTP 200）：
  https://api.crossref.org/works/10.1038/s41597-023-02555-8?mailto=...
  https://api.openalex.org/works/https://doi.org/10.1038/...?mailto=...

诚实原则：只报 API 真实返回；查不到 -> error severity=high（疑似臆造/需核查），不替它圆场。

用法：
  python scripts/verify_refs.py 10.1038/s41597-023-02555-8 10.1145/3292500.3330701
  python scripts/verify_refs.py --file dois.txt --self-author "Vayssade" --out report.json
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

UA = "light-citation/1.0 (mailto:light.research@gmail.com)"
MAILTO = "light.research@gmail.com"
THIS_YEAR = datetime.date.today().year

CN_RE = re.compile(r"[一-鿿]")


def _get_json(url: str, timeout: int = 30):
    """返回 (http_code, obj_or_None)。"""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, None
    except (urllib.error.URLError, TimeoutError):
        return 0, None


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9一-鿿]+", "", (s or "").lower())


def _title_match(a: str, b: str) -> float:
    """粗略标题一致度：归一化后字符级 Jaccard（够用，不引外部依赖）。"""
    sa, sb = set(_norm(a)), set(_norm(b))
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def verify_one(doi: str, self_authors=None):
    """核验单个 DOI，返回结构化记录。"""
    self_authors = [s.lower() for s in (self_authors or [])]
    doi = doi.strip().replace("https://doi.org/", "").replace("doi:", "")
    rec = {"doi": doi, "found_crossref": False, "found_openalex": False,
           "http": {}, "title": None, "year": None,
           "cited_by_count": None, "is_cn": False, "is_self_cite": False,
           "errors": [], "warnings": []}

    # --- Crossref ---
    cr_url = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}?mailto={MAILTO}"
    code, cr = _get_json(cr_url)
    rec["http"]["crossref"] = code
    cr_title = cr_year = None
    authors_str = ""
    if code == 200 and cr and cr.get("message"):
        m = cr["message"]
        rec["found_crossref"] = True
        cr_title = (m.get("title") or [None])[0]
        rec["title"] = cr_title
        dp = m.get("issued", {}).get("date-parts", [[None]])
        cr_year = dp[0][0] if dp and dp[0] else None
        rec["year"] = cr_year
        rec["cited_by_count"] = m.get("is-referenced-by-count")
        auth = m.get("author", []) or []
        authors_str = " ".join((a.get("family", "") + " " + a.get("given", "")) for a in auth)
        rec["is_cn"] = bool(CN_RE.search(cr_title or "")) or "China" in authors_str
    else:
        rec["errors"].append({"severity": "high",
                              "msg": f"Crossref 查不到该 DOI（HTTP {code}）——疑似臆造或 DOI 错误，需核查"})

    # --- OpenAlex ---
    oa_url = (f"https://api.openalex.org/works/https://doi.org/{urllib.parse.quote(doi)}"
              f"?mailto={MAILTO}")
    code2, oa = _get_json(oa_url)
    rec["http"]["openalex"] = code2
    if code2 == 200 and oa and oa.get("id"):
        rec["found_openalex"] = True
        oa_title = oa.get("title")
        oa_year = oa.get("publication_year")
        if rec["year"] is None:
            rec["year"] = oa_year
        if rec["cited_by_count"] is None:
            rec["cited_by_count"] = oa.get("cited_by_count")
        # 一致性
        if cr_title and oa_title:
            sim = _title_match(cr_title, oa_title)
            if sim < 0.6:
                rec["warnings"].append(
                    f"Crossref 与 OpenAlex 标题不一致(相似度{sim:.2f})，请人工确认")
        if cr_year and oa_year and abs(cr_year - oa_year) > 1:
            rec["warnings"].append(f"年份不一致：Crossref {cr_year} vs OpenAlex {oa_year}")
        # 语言/国别
        if oa.get("language") == "zh":
            rec["is_cn"] = True
    else:
        if rec["found_crossref"]:
            rec["warnings"].append(f"OpenAlex 未收录（HTTP {code2}），仅 Crossref 单源，建议补证")
        else:
            rec["errors"].append({"severity": "high",
                                  "msg": f"Crossref+OpenAlex 双源均查不到（HTTP {code}/{code2}）——高度疑似臆造"})

    # --- 自引判断 ---
    if self_authors and authors_str:
        low = authors_str.lower()
        if any(sa in low for sa in self_authors):
            rec["is_self_cite"] = True

    # --- 时效性 ---
    if rec["year"] and rec["year"] <= THIS_YEAR - 6 and (rec["cited_by_count"] or 0) < 5:
        rec["warnings"].append(
            f"较旧({rec['year']})且被引偏低({rec['cited_by_count']})，代表性存疑")
    return rec


def build_report(dois, self_authors=None):
    items = [verify_one(d, self_authors) for d in dois if d.strip()]
    n = len(items)
    cn = sum(1 for r in items if r["is_cn"])
    self_n = sum(1 for r in items if r["is_self_cite"])
    recent = sum(1 for r in items if (r["year"] or 0) >= THIS_YEAR - 2)
    n_err = sum(len(r["errors"]) for r in items)
    summary = {
        "total": n,
        "verified_ok": sum(1 for r in items if r["found_crossref"] and not r["errors"]),
        "high_severity_errors": n_err,
        "cn_count": cn, "foreign_count": n - cn,
        "cn_ratio": round(cn / n, 3) if n else 0,
        "self_citation_rate": round(self_n / n, 3) if n else 0,
        "recent_2y_count": recent,
        "missing_recent_2y": recent == 0 and n > 0,
        "checked_at": datetime.date.today().isoformat(),
    }
    return {"summary": summary, "items": items}


def main(argv=None):
    ap = argparse.ArgumentParser(description="批量 DOI 真实性/一致性核验 -> 机读 JSON")
    ap.add_argument("dois", nargs="*", help="DOI 列表")
    ap.add_argument("--file", help="每行一个 DOI 的文件")
    ap.add_argument("--self-author", action="append", default=[],
                    help="本文作者姓氏（判自引），可多次")
    ap.add_argument("--out", help="报告输出路径（默认 stdout）")
    args = ap.parse_args(argv)

    dois = list(args.dois)
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            dois += [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
    if not dois:
        ap.error("请提供至少一个 DOI 或 --file")

    report = build_report(dois, args.self_author)
    out = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"报告已写入 {args.out}", file=sys.stderr)
    else:
        print(out)
    return 0


def _selftest():
    """__main__ 自测：1 真 DOI + 1 假 DOI，验证报告结构与 HTTP 码记录。"""
    print("### verify_refs 自测")
    dois = ["10.1038/s41597-023-02555-8", "10.9999/this-doi-does-not-exist-xyz"]
    rep = build_report(dois, self_authors=["Vayssade"])
    print(json.dumps(rep, ensure_ascii=False, indent=2)[:1400])
    s = rep["summary"]
    assert rep["items"][0]["found_crossref"], "真 DOI 应被 Crossref 命中"
    assert rep["items"][0]["http"]["crossref"] == 200, "真 DOI Crossref 应 HTTP 200"
    assert rep["items"][1]["errors"], "假 DOI 应产 high severity error"
    assert s["self_citation_rate"] > 0, "应识别自引"
    print("\n[OK] verify_refs 自测通过：真 DOI HTTP200 命中、假 DOI 标 high error、自引率/中外占比已算")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        _selftest()
    else:
        sys.exit(main())
