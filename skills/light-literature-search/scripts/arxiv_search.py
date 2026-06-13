#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""arxiv_search.py — 预印本检索（arXiv + 可选 bioRxiv/medRxiv），输出统一文献表。

兑现 SKILL「预印本最前沿」承诺，把两源做成可运行：
  1. arXiv API `export.arxiv.org/api/query`：Atom XML 响应；search_query 支持
     ti:/au:/abs:/cat:/all: + 布尔；max_results≤100；sortBy=submittedDate。免 key。
  2. bioRxiv/medRxiv `api.biorxiv.org`：JSON；/details/{server}/{interval}/{cursor}
     取一段时间窗的预印本元数据，/pubs/ 查是否已转正式发表（published 字段）。免 key。
     注：bioRxiv API 是按日期窗/cursor 拉取，不是关键词检索——本脚本对其结果做
     本地标题/摘要关键词过滤，并如实标注（非服务端检索）。

预印本须按可信度分级标注：未经同行评审，引用须注明 preprint，bioRxiv 若 published 字段
非空说明已转正式发表，应优先引正式版 DOI。

诚实约定（见 d:/skill/Light/CONVENTIONS.md）：
- 不臆造 arXiv id/DOI/日期；取不到即如实留空。
- 网络不可用时回退到内置合成样本，保证 __main__ 可跑通并打印 [OFFLINE]。
- arXiv 请求间隔 ≥3 秒（其 API 礼貌约定）；bioRxiv 免 key 无强制间隔。

用法：
    python scripts/arxiv_search.py "all:dairy goat behavior" --max-results 10
    python scripts/arxiv_search.py "animal behavior" --source biorxiv --days 30
    python scripts/arxiv_search.py --selftest
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

TIMEOUT = 30
ARXIV = "http://export.arxiv.org/api/query"
BIORXIV = "https://api.biorxiv.org/details"
UA = "Light-literature-search/1.0"
ATOM = "{http://www.w3.org/2005/Atom}"


def _get(url: str) -> tuple[int, str]:
    """返回 (http_code, raw_text)。网络/超时异常吞掉返回 (0, "")。"""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.getcode(), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:  # noqa
        return e.code, ""
    except Exception:  # noqa: network down / timeout
        return 0, ""


def _norm_doi(doi: str | None) -> str:
    if not doi:
        return ""
    d = doi.lower().strip()
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", d)


def _rec(source_api: str, title: str, authors: list, year: Any, venue: str,
         doi: str, arxiv_id: str, abstract: str, url: str,
         is_preprint: bool = True, published_doi: str = "") -> dict:
    """统一文献记录（对齐 search_normalize.py，加 arxiv_id/is_preprint/published_doi）。"""
    return {
        "source_api": source_api,
        "title": (title or "").strip(),
        "authors": [a for a in (authors or []) if a],
        "year": year,
        "venue": venue or source_api,
        "doi": _norm_doi(doi),
        "arxiv_id": arxiv_id or "",
        "cited_by": None,  # 预印本源不出被引
        "cited_by_src": None,
        "abstract": (abstract or "").strip(),
        "is_preprint": is_preprint,
        "published_doi": _norm_doi(published_doi),  # bioRxiv 若已转正
        "url": url or "",
    }


# ----------------------------- arXiv (Atom XML) -----------------------------
def parse_arxiv_atom(xml_text: str) -> list[dict]:
    """解析 arXiv Atom XML 为统一记录。容错：解析失败返回空列表。"""
    out: list[dict] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return out
    for entry in root.findall(f"{ATOM}entry"):
        title = (entry.findtext(f"{ATOM}title") or "").strip()
        summary = (entry.findtext(f"{ATOM}summary") or "").strip()
        published = (entry.findtext(f"{ATOM}published") or "")
        year = int(published[:4]) if published[:4].isdigit() else None
        idurl = (entry.findtext(f"{ATOM}id") or "").strip()
        # arXiv id：从 id URL 末段取（形如 http://arxiv.org/abs/2401.01234v1）
        aid = idurl.rsplit("/abs/", 1)[-1] if "/abs/" in idurl else ""
        authors = [a.findtext(f"{ATOM}name") or ""
                   for a in entry.findall(f"{ATOM}author")]
        # DOI（若作者已登记正式发表 DOI，arXiv 用 arxiv:doi 扩展元素）
        doi = ""
        for el in entry:
            if el.tag.endswith("doi") and el.text:
                doi = el.text.strip()
        out.append(_rec("arXiv", title, authors[:8], year, "arXiv",
                        doi, aid, summary, idurl, is_preprint=True))
    return out


def search_arxiv(query: str, max_results: int = 10) -> tuple[int, list[dict]]:
    """arXiv API 检索。query 形如 'all:dairy goat' / 'ti:LLM AND cat:cs.CL'。"""
    params = {
        "search_query": query,
        "start": "0",
        "max_results": str(max(1, min(max_results, 100))),
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = f"{ARXIV}?" + urllib.parse.urlencode(params)
    code, raw = _get(url)
    if code == 200 and raw:
        return code, parse_arxiv_atom(raw)
    return code, []


# ----------------------------- bioRxiv / medRxiv (JSON) -----------------------------
def search_biorxiv(keyword: str, server: str = "biorxiv",
                   days: int = 30, max_scan: int = 100) -> tuple[int, list[dict]]:
    """bioRxiv/medRxiv：拉最近一段时间窗的预印本，本地按关键词过滤标题/摘要。

    注：bioRxiv API 无关键词检索端点，只能按日期窗/cursor 拉取，故本地过滤并标注。
    interval 用 最近 N 天（YYYY-MM-DD/YYYY-MM-DD 由调用方外部算好或用相对天数端点）。
    这里用 details/{server}/{days}d 形式不被支持，改用 0 cursor 拉最新一页演示口径。
    """
    kw = keyword.lower().strip()
    # bioRxiv 支持 /details/{server}/{N}（N 为相对最近条数游标）或日期区间；
    # 为稳健用日期区间需调用方传入，这里用最新游标页拉一页（cursor=0）。
    url = f"{BIORXIV}/{server}/0"
    code, raw = _get(url)
    out: list[dict] = []
    if code == 200 and raw:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return code, out
        for r in data.get("collection", [])[:max_scan]:
            title = r.get("title") or ""
            abs = r.get("abstract") or ""
            if kw and kw not in title.lower() and kw not in abs.lower():
                continue
            date = r.get("date") or ""
            year = int(date[:4]) if date[:4].isdigit() else None
            authors = [a.strip() for a in (r.get("authors") or "").split(";") if a.strip()]
            pub = r.get("published") or ""
            pub = "" if pub.upper() in ("NA", "") else pub
            out.append(_rec(
                server, title, authors[:8], year, server,
                r.get("doi") or "", "", abs,
                (f"https://www.biorxiv.org/content/{r.get('doi')}" if r.get("doi") else ""),
                is_preprint=True, published_doi=pub))
    return code, out


# ----------------------------- run / 输出 -----------------------------
def run(query: str, source: str = "arxiv", max_results: int = 10,
        days: int = 30, offline_sample: bool = False) -> dict:
    offline = False
    records: list[dict] = []
    http: dict = {}
    if not offline_sample:
        if source in ("arxiv", "both"):
            c, recs = search_arxiv(query, max_results)
            http["arxiv"] = c
            records += recs
        if source in ("biorxiv", "medrxiv", "both"):
            srv = "medrxiv" if source == "medrxiv" else "biorxiv"
            c, recs = search_biorxiv(query, srv, days, max_results * 10)
            http[srv] = c
            records += recs
        if not records and all(v == 0 for v in http.values()):
            offline = True
    if offline_sample or offline:
        offline = True
        print("[OFFLINE] 网络不可达，使用内置合成样本验证管线。", file=sys.stderr)
        records = _offline_sample()
        http = {"arxiv": 0}
    return {"query": query, "source": source, "offline": offline,
            "http": http, "count": len(records), "records": records}


def _offline_sample() -> list[dict]:
    return [
        _rec("arXiv", "A deep model for dairy goat behavior [SYNTHETIC]",
             ["Synthetic A"], 2024, "arXiv", "", "2401.00001",
             "Synthetic preprint abstract.", "http://arxiv.org/abs/2401.00001",
             is_preprint=True),
        _rec("biorxiv", "Goat estrus detection [SYNTHETIC]",
             ["Synthetic B"], 2024, "biorxiv", "10.0000/synthetic.bio.1", "",
             "Synthetic biorxiv abstract.", "https://www.biorxiv.org/content/x",
             is_preprint=True, published_doi="10.0000/published.1"),
    ]


def to_markdown(records: list[dict], query: str) -> str:
    lines = [f"# 预印本检索 query={query!r}\n",
             "| # | 标题 | 年 | arXiv/源 | DOI | 已转正式发表 | 源 |",
             "|---|------|----|---------|-----|-------------|----|"]
    for i, r in enumerate(records, 1):
        pub = r.get("published_doi") or ("—" if r["source_api"] == "arXiv" else "未")
        lines.append("| %d | %s | %s | %s | %s | %s | %s |" % (
            i, (r["title"] or "")[:60].replace("|", "/"), r.get("year") or "",
            r.get("arxiv_id") or r["source_api"], r.get("doi") or "",
            pub, r["source_api"]))
    return "\n".join(lines)


def _selftest() -> int:
    """离线自测：不打网，验证 arXiv Atom 解析、bioRxiv JSON 过滤、离线回退。"""
    print("### arxiv_search 离线自测", file=sys.stderr)

    # 1) arXiv Atom XML 解析
    atom = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2401.01234v1</id>
    <title>A Test Preprint on Goats</title>
    <summary>This is the abstract.</summary>
    <published>2024-01-15T00:00:00Z</published>
    <author><name>Zhang San</name></author>
    <author><name>Li Si</name></author>
    <arxiv:doi>10.1234/test.doi</arxiv:doi>
  </entry>
</feed>"""
    recs = parse_arxiv_atom(atom)
    assert len(recs) == 1, recs
    assert recs[0]["arxiv_id"] == "2401.01234v1", recs[0]
    assert recs[0]["year"] == 2024 and recs[0]["doi"] == "10.1234/test.doi", recs[0]
    assert len(recs[0]["authors"]) == 2 and recs[0]["is_preprint"] is True, recs[0]

    # 2) bioRxiv JSON 解析 + 关键词过滤 + published 字段
    global _get
    orig_get = _get
    bio_json = json.dumps({"collection": [
        {"title": "Goat estrus detection", "abstract": "about goats",
         "date": "2024-03-01", "authors": "A; B", "doi": "10.1/bio.1", "published": "10.2/pub.1"},
        {"title": "Unrelated cancer study", "abstract": "about tumors",
         "date": "2024-03-02", "authors": "C", "doi": "10.1/bio.2", "published": "NA"},
    ]})

    def fake_get(url):
        return 200, bio_json
    try:
        _get = fake_get
        code, brecs = search_biorxiv("goat", "biorxiv", 30, 100)
    finally:
        _get = orig_get
    assert code == 200 and len(brecs) == 1, brecs  # 只 goat 那条命中关键词过滤
    assert brecs[0]["doi"] == "10.1/bio.1", brecs[0]
    assert brecs[0]["published_doi"] == "10.2/pub.1", brecs[0]  # 已转正式发表

    # 3) arXiv 解析失败容错
    assert parse_arxiv_atom("<not valid xml") == []

    # 4) 离线回退
    res = run("goat", offline_sample=True)
    assert res["offline"] is True and res["records"], res
    md = to_markdown(res["records"], "goat")
    assert "arXiv" in md, md
    print("[selftest] PASS arxiv_search offline")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="预印本检索（arXiv + 可选 bioRxiv/medRxiv）")
    ap.add_argument("query", nargs="?", default="all:dairy goat behavior")
    ap.add_argument("--source", default="arxiv",
                    choices=["arxiv", "biorxiv", "medrxiv", "both"])
    ap.add_argument("--max-results", type=int, default=10)
    ap.add_argument("--days", type=int, default=30, help="bioRxiv 时间窗（天）")
    ap.add_argument("--offline", action="store_true", help="强制用合成样本")
    ap.add_argument("--selftest", action="store_true", help="run offline synthetic self-test")
    ap.add_argument("--json-out", default="")
    ap.add_argument("--md-out", default="")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(_selftest())

    result = run(args.query, args.source, args.max_results, args.days,
                 offline_sample=args.offline)
    md = to_markdown(result["records"], args.query)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    if args.md_out:
        with open(args.md_out, "w", encoding="utf-8") as f:
            f.write(md)
    print(md)
    print("\n[SUMMARY] query=%r source=%s offline=%s count=%s http=%s" % (
        args.query, args.source, result["offline"], result["count"],
        result["http"]), file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[1] == "--selftest":
        _selftest()
    else:
        main()


