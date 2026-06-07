#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""search_normalize.py — 多源文献检索与规范化（OpenAlex + Crossref）。

功能：
1. urllib 直连 OpenAlex /works 与 Crossref /works（无第三方依赖，带 mailto 进礼貌池）。
2. 还原 OpenAlex 的 abstract_inverted_index 为正文摘要。
3. 跨源按 DOI 去重归并（无 DOI 回退到 规范化标题+年）。
4. 按 cited_by 排序。
5. 输出统一文献表：JSON + Markdown。

诚实约定（见 d:/skill/Light/CONVENTIONS.md）：
- 不臆造 DOI/被引；被引数标来源库（OpenAlex vs Crossref 口径不同，不可直接比）。
- 网络不可用时回退到内置合成样本，保证 __main__ 可跑通并打印 [OFFLINE] 标记。

用法：
    python scripts/search_normalize.py "dairy goat behavior" --per-page 10
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

MAILTO = "light-skill@example.com"
TIMEOUT = 30
UA = "Light-literature-search/1.0 (mailto:%s)" % MAILTO


def _get_json(url: str) -> tuple[int, Any]:
    """返回 (http_code, parsed_json_or_None)。任何异常吞掉返回 (0, None)。"""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            code = resp.getcode()
            data = json.loads(resp.read().decode("utf-8", "replace"))
            return code, data
    except urllib.error.HTTPError as e:  # noqa
        return e.code, None
    except Exception:  # noqa: network down / timeout / json error
        return 0, None


def restore_abstract(inv: dict | None) -> str:
    """OpenAlex abstract_inverted_index -> 正文。inv: {word: [pos,...]}。"""
    if not inv:
        return ""
    positions: list[tuple[int, str]] = []
    for word, idxs in inv.items():
        for i in idxs:
            positions.append((i, word))
    positions.sort(key=lambda x: x[0])
    return " ".join(w for _, w in positions)


def _norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (t or "").lower())


def _norm_doi(doi: str | None) -> str:
    if not doi:
        return ""
    d = doi.lower().strip()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    return d


# ----------------------------- OpenAlex -----------------------------
def search_openalex(query: str, per_page: int = 10) -> tuple[int, list[dict]]:
    params = {
        "search": query,
        "per-page": str(per_page),
        "sort": "cited_by_count:desc",
        "mailto": MAILTO,
        "select": "id,doi,title,publication_year,cited_by_count,"
                  "authorships,primary_location,abstract_inverted_index,type,"
                  "referenced_works",
    }
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    code, data = _get_json(url)
    out: list[dict] = []
    if data and "results" in data:
        for w in data["results"]:
            auths = [a.get("author", {}).get("display_name", "")
                     for a in w.get("authorships", [])][:8]
            loc = w.get("primary_location") or {}
            src = loc.get("source") or {}
            out.append({
                "source_api": "OpenAlex",
                "title": w.get("title") or "",
                "authors": [a for a in auths if a],
                "year": w.get("publication_year"),
                "venue": src.get("display_name") or "",
                "doi": _norm_doi(w.get("doi")),
                "cited_by": w.get("cited_by_count"),
                "cited_by_src": "OpenAlex",
                "type": w.get("type") or "",
                "abstract": restore_abstract(w.get("abstract_inverted_index")),
                "url": w.get("id") or "",
                "referenced_works": w.get("referenced_works") or [],
            })
    return code, out


# ----------------------------- Crossref -----------------------------
def search_crossref(query: str, rows: int = 10) -> tuple[int, list[dict]]:
    params = {
        "query.bibliographic": query,
        "rows": str(rows),
        "sort": "is-referenced-by-count",
        "order": "desc",
        "select": "DOI,title,author,issued,container-title,"
                  "is-referenced-by-count,type,abstract",
        "mailto": MAILTO,
    }
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    code, data = _get_json(url)
    out: list[dict] = []
    if data and data.get("message", {}).get("items"):
        for it in data["message"]["items"]:
            auths = []
            for a in it.get("author", []) or []:
                nm = (a.get("given", "") + " " + a.get("family", "")).strip()
                if nm:
                    auths.append(nm)
            year = None
            dp = it.get("issued", {}).get("date-parts", [[None]])
            if dp and dp[0]:
                year = dp[0][0]
            ct = it.get("container-title") or [""]
            ttl = it.get("title") or [""]
            abs = re.sub(r"<[^>]+>", "", it.get("abstract", "") or "").strip()
            out.append({
                "source_api": "Crossref",
                "title": ttl[0] if ttl else "",
                "authors": auths[:8],
                "year": year,
                "venue": ct[0] if ct else "",
                "doi": _norm_doi(it.get("DOI")),
                "cited_by": it.get("is-referenced-by-count"),
                "cited_by_src": "Crossref",
                "type": it.get("type") or "",
                "abstract": abs,
                "url": "https://doi.org/" + it.get("DOI") if it.get("DOI") else "",
            })
    return code, out


# ----------------------------- 去重归并 -----------------------------
def dedup_merge(records: list[dict]) -> list[dict]:
    """跨源按 DOI 优先归并；无 DOI 回退 规范化标题+年。"""
    buckets: dict[str, dict] = {}
    for r in records:
        key = _norm_doi(r.get("doi")) or (_norm_title(r.get("title")) + str(r.get("year") or ""))
        if not key:
            key = str(id(r))
        if key not in buckets:
            r = dict(r)
            r["cited_by_by_src"] = {}
            if r.get("cited_by") is not None:
                r["cited_by_by_src"][r["cited_by_src"]] = r["cited_by"]
            r["sources"] = [r["source_api"]]
            buckets[key] = r
        else:
            b = buckets[key]
            if r["source_api"] not in b["sources"]:
                b["sources"].append(r["source_api"])
            if r.get("cited_by") is not None:
                b["cited_by_by_src"][r["cited_by_src"]] = r["cited_by"]
            if len(r.get("abstract", "")) > len(b.get("abstract", "")):
                b["abstract"] = r["abstract"]
            if not b.get("doi") and r.get("doi"):
                b["doi"] = r["doi"]
            if not b.get("venue") and r.get("venue"):
                b["venue"] = r["venue"]
    merged = list(buckets.values())

    def _sortkey(x: dict) -> int:
        vals = [v for v in x.get("cited_by_by_src", {}).values() if isinstance(v, int)]
        return max(vals) if vals else -1
    merged.sort(key=_sortkey, reverse=True)
    return merged


# ----------------------------- 输出 -----------------------------
def to_markdown(records: list[dict], query: str) -> str:
    lines = [f"# 文献表：{query}", "",
             f"共 {len(records)} 条（跨源去重后，按被引降序）。被引数标来源库，"
             "OpenAlex/Crossref 口径不同不可直接比。", "",
             "| # | 标题 | 年 | venue | 被引(来源) | 来源API | DOI |",
             "|---|------|----|-------|-----------|---------|-----|"]
    for i, r in enumerate(records, 1):
        cb = "; ".join(f"{v}({k})" for k, v in r.get("cited_by_by_src", {}).items()) or "NA"
        title = (r.get("title") or "").replace("|", "/")[:80]
        lines.append(f"| {i} | {title} | {r.get('year') or ''} | "
                     f"{(r.get('venue') or '')[:30]} | {cb} | "
                     f"{'+'.join(r.get('sources', []))} | {r.get('doi') or ''} |")
    return "\n".join(lines)


def run(query: str, per_page: int = 10, offline_sample: bool = False) -> dict:
    offline = False
    recs: list[dict] = []
    if not offline_sample:
        oa_code, oa = search_openalex(query, per_page)
        cr_code, cr = search_crossref(query, per_page)
        print(f"[HTTP] OpenAlex={oa_code} Crossref={cr_code}", file=sys.stderr)
        recs = oa + cr
        if oa_code == 0 and cr_code == 0:
            offline = True
    if offline_sample or offline:
        offline = True
        recs = _SYNTHETIC
        print("[OFFLINE] 网络不可达，使用内置合成样本验证管线。", file=sys.stderr)
    merged = dedup_merge(recs)
    return {"query": query, "offline": offline, "raw_count": len(recs),
            "merged_count": len(merged), "records": merged}


_SYNTHETIC = [
    {"source_api": "OpenAlex", "title": "Automated behaviour monitoring of dairy goats",
     "authors": ["A Smith", "B Lee"], "year": 2021,
     "venue": "Computers and Electronics in Agriculture",
     "doi": "10.1016/j.compag.2021.100001", "cited_by": 88, "cited_by_src": "OpenAlex",
     "type": "article", "abstract": "We present a system for goat behaviour.", "url": "openalex:W1"},
    {"source_api": "Crossref", "title": "Automated Behaviour Monitoring of Dairy Goats",
     "authors": ["Alice Smith"], "year": 2021,
     "venue": "Computers and Electronics in Agriculture",
     "doi": "10.1016/j.compag.2021.100001", "cited_by": 61, "cited_by_src": "Crossref",
     "type": "journal-article", "abstract": "",
     "url": "https://doi.org/10.1016/j.compag.2021.100001"},
    {"source_api": "OpenAlex", "title": "Accelerometer-based activity recognition in goats",
     "authors": ["C Wang"], "year": 2019, "venue": "Animals", "doi": "10.3390/ani9120999",
     "cited_by": 45, "cited_by_src": "OpenAlex", "type": "article",
     "abstract": "Activity recognition using sensors.", "url": "openalex:W2"},
]


def main() -> None:
    ap = argparse.ArgumentParser(description="多源文献检索与规范化")
    ap.add_argument("query", nargs="?", default="dairy goat behavior")
    ap.add_argument("--per-page", type=int, default=10)
    ap.add_argument("--offline", action="store_true", help="强制用合成样本")
    ap.add_argument("--json-out", default="")
    ap.add_argument("--md-out", default="")
    args = ap.parse_args()

    result = run(args.query, args.per_page, offline_sample=args.offline)
    md = to_markdown(result["records"], args.query)

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    if args.md_out:
        with open(args.md_out, "w", encoding="utf-8") as f:
            f.write(md)

    print(md)
    print(f"\n[SUMMARY] query={args.query!r} offline={result['offline']} "
          f"raw={result['raw_count']} merged={result['merged_count']}")


if __name__ == "__main__":
    main()



