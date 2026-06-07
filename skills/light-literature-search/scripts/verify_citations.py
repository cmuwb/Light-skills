#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_citations.py — DOI 引用核验与幻觉引用标记。

思路（诚实第一）：
- 拿一条待核验引用（DOI + 声称的标题/作者/年/期刊），回 Crossref 内容协商
  (Accept: application/vnd.citationstyles.csl+json) 取权威元数据。
- 比对标题相似度、年份、首作者姓氏、期刊，给出 verdict：
  VERIFIED / METADATA_MISMATCH / DOI_NOT_FOUND（疑似幻觉）/ NO_DOI（需人工）。
- 产出核查报告（JSON + 文本）。

不臆造：DOI 解析失败即标 DOI_NOT_FOUND，不替用户脑补正确 DOI。

用法：
    python scripts/verify_citations.py            # 跑内置真实 DOI 自测
    python scripts/verify_citations.py 10.xxxx/yy --title "..." --year 2023
"""
from __future__ import annotations
import argparse
import difflib
import json
import re
import sys
import urllib.parse
import urllib.request
from typing import Any

MAILTO = "light-skill@example.com"
TIMEOUT = 30
UA = "Light-literature-search/1.0 (mailto:%s)" % MAILTO


def _norm_doi(doi: str) -> str:
    d = (doi or "").lower().strip()
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", d)


def _title_sim(a: str, b: str) -> float:
    na = re.sub(r"[^a-z0-9]+", " ", (a or "").lower()).strip()
    nb = re.sub(r"[^a-z0-9]+", " ", (b or "").lower()).strip()
    if not na or not nb:
        return 0.0
    return round(difflib.SequenceMatcher(None, na, nb).ratio(), 3)


def fetch_doi_csl(doi: str) -> tuple[int, dict | None]:
    """DOI 内容协商取 CSL-JSON。先打 doi.org，失败回退 Crossref /works/{doi}。"""
    doi = _norm_doi(doi)
    headers = {"User-Agent": UA, "Accept": "application/vnd.citationstyles.csl+json"}
    url = "https://doi.org/" + urllib.parse.quote(doi, safe="/().;:")
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.getcode(), json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:  # noqa
        if e.code == 404:
            return 404, None
    except Exception:
        pass
    # 回退 Crossref
    cr = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/().;:")
    cr += "?mailto=" + MAILTO
    req2 = urllib.request.Request(cr, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req2, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
            return resp.getcode(), data.get("message")
    except urllib.error.HTTPError as e:  # noqa
        return e.code, None
    except Exception:
        return 0, None


def _meta_from_csl(m: dict) -> dict:
    """CSL-JSON 或 Crossref message -> 统一元数据。"""
    title = m.get("title")
    if isinstance(title, list):
        title = title[0] if title else ""
    ct = m.get("container-title")
    if isinstance(ct, list):
        ct = ct[0] if ct else ""
    year = None
    for k in ("issued", "published", "published-print", "published-online"):
        dp = (m.get(k) or {}).get("date-parts")
        if dp and dp[0] and dp[0][0]:
            year = dp[0][0]
            break
    authors = []
    for a in m.get("author", []) or []:
        fam = a.get("family") or a.get("name") or ""
        if fam:
            authors.append(fam)
    return {"title": title or "", "container": ct or "", "year": year, "authors": authors}


def verify_one(claim: dict) -> dict:
    """claim: {doi, title?, year?, first_author?}。返回核查结果。"""
    doi = _norm_doi(claim.get("doi", ""))
    rep: dict[str, Any] = {"claim": claim, "doi": doi}
    if not doi:
        rep["verdict"] = "NO_DOI"
        rep["note"] = "无 DOI，无法自动核验，需人工查证（疑似来源不明）。"
        return rep
    code, meta = fetch_doi_csl(doi)
    rep["http_code"] = code
    if code == 404 or meta is None:
        rep["verdict"] = "DOI_NOT_FOUND"
        rep["note"] = "DOI 无法解析，疑似幻觉引用或 DOI 拼写错误。"
        return rep
    authoritative = _meta_from_csl(meta)
    rep["authoritative"] = authoritative
    issues = []
    # 标题比对
    if claim.get("title"):
        sim = _title_sim(claim["title"], authoritative["title"])
        rep["title_similarity"] = sim
        if sim < 0.6:
            issues.append(f"标题相似度低({sim})：声称={claim['title']!r} vs 实际={authoritative['title']!r}")
    # 年份比对
    if claim.get("year") and authoritative.get("year"):
        if int(claim["year"]) != int(authoritative["year"]):
            issues.append(f"年份不符：声称={claim['year']} vs 实际={authoritative['year']}")
    # 首作者
    if claim.get("first_author") and authoritative.get("authors"):
        fa = claim["first_author"].split()[-1].lower()
        if fa not in [a.lower() for a in authoritative["authors"]]:
            issues.append(f"首作者姓氏未匹配：声称={claim['first_author']!r} vs 实际作者={authoritative['authors'][:3]}")
    rep["issues"] = issues
    rep["verdict"] = "VERIFIED" if not issues else "METADATA_MISMATCH"
    return rep


def verify_batch(claims: list[dict]) -> dict:
    results = [verify_one(c) for c in claims]
    summary = {}
    for r in results:
        summary[r["verdict"]] = summary.get(r["verdict"], 0) + 1
    return {"total": len(results), "summary": summary, "results": results}


def report_text(batch: dict) -> str:
    lines = ["# 引用核查报告", "",
             f"共 {batch['total']} 条。判定分布：{batch['summary']}", ""]
    flag = {"VERIFIED": "[OK]", "METADATA_MISMATCH": "[!]",
            "DOI_NOT_FOUND": "[幻觉?]", "NO_DOI": "[需人工]"}
    for i, r in enumerate(batch["results"], 1):
        lines.append(f"## {i}. {flag.get(r['verdict'], '')} {r['verdict']}  DOI={r.get('doi') or 'NA'}")
        if r.get("http_code") is not None:
            lines.append(f"- HTTP={r['http_code']}")
        if r.get("authoritative"):
            a = r["authoritative"]
            lines.append(f"- 权威元数据：{a['title']!r} ({a['year']}) {a['container']!r} 作者={a['authors'][:3]}")
        if r.get("title_similarity") is not None:
            lines.append(f"- 标题相似度={r['title_similarity']}")
        for iss in r.get("issues", []):
            lines.append(f"- 问题：{iss}")
        if r.get("note"):
            lines.append(f"- 说明：{r['note']}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="DOI 引用核验与幻觉标记")
    ap.add_argument("doi", nargs="?", default="")
    ap.add_argument("--title", default="")
    ap.add_argument("--year", default="")
    ap.add_argument("--first-author", default="")
    ap.add_argument("--json-out", default="")
    args = ap.parse_args()

    if args.doi:
        claims = [{"doi": args.doi, "title": args.title or None,
                   "year": args.year or None, "first_author": args.first_author or None}]
    else:
        # 内置真实 DOI 自测：1 真实可核验 + 1 故意标题错配 + 1 伪造 DOI
        claims = [
            {"doi": "10.1038/s41597-023-02555-8",
             "title": "A dataset", "year": 2023, "first_author": None},
            {"doi": "10.1038/s41597-023-02555-8",
             "title": "Completely unrelated fabricated title about quantum goats",
             "year": 1999, "first_author": "Nobody"},
            {"doi": "10.0000/this-doi-does-not-exist-9999",
             "title": "Phantom paper", "year": 2024, "first_author": "Ghost"},
        ]
        print("[SELFTEST] 用 3 条样本核验：真实DOI / 标题年份错配 / 伪造DOI", file=sys.stderr)

    batch = verify_batch(claims)
    txt = report_text(batch)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(batch, f, ensure_ascii=False, indent=2)
    print(txt)
    print(f"[SUMMARY] {batch['summary']}")


if __name__ == "__main__":
    main()

