#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""search_normalize.py — 多源文献检索与规范化（OpenAlex + Crossref）。

功能：
1. urllib 直连 OpenAlex /works 与 Crossref /works（无第三方依赖，按需带 mailto 进礼貌池）。
2. 还原 OpenAlex 的 abstract_inverted_index 为正文摘要。
3. 跨源按 DOI 去重归并（无 DOI 回退到 规范化标题+年）。
4. 按 cited_by 排序。
5. 输出统一文献表：JSON + Markdown。

诚实约定（见 d:/skill/Light/CONVENTIONS.md）：
- 不臆造 DOI/被引；被引数标来源库（OpenAlex vs Crossref 口径不同，不可直接比）。
- 网络不可用时回退到内置合成样本，保证 __main__ 可跑通并打印 [OFFLINE] 标记。
- 礼貌池邮箱经环境变量 OPENALEX_MAILTO / CROSSREF_MAILTO 或 --mailto 传入；不传则匿名（不伪造）。
- OpenAlex key 经环境变量 OPENALEX_API_KEY 或 --api-key 传入（2026 起需 key，口径见 references）。

用法：
    python scripts/search_normalize.py "dairy goat behavior" --per-page 10 --mailto you@inst.edu
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# 礼貌池邮箱：优先环境变量 OPENALEX_MAILTO / CROSSREF_MAILTO，其次 --mailto，不传则匿名（不伪造）。
# 不再硬编码伪造邮箱（旧版硬编码了一个 example.com 占位邮箱，违反 OpenAlex/Crossref 礼貌池约定且无意义）。
# OpenAlex API key：2026 起 OpenAlex 需免费 key，经 --api-key 或环境变量 OPENALEX_API_KEY 传入；
# key/限流/计费的唯一口径见本技能 references「OpenAlex 接入真相源」节，本脚本不复写数字。
_MAILTO = (os.environ.get("OPENALEX_MAILTO") or os.environ.get("CROSSREF_MAILTO") or "").strip()
_API_KEY = os.environ.get("OPENALEX_API_KEY", "").strip()
TIMEOUT = 30


def _user_agent() -> str:
    if _MAILTO:
        return "Light-literature-search/1.0 (mailto:%s)" % _MAILTO
    return "Light-literature-search/1.0"


def _oa_params(params: dict) -> dict:
    """给 OpenAlex 查询参数按需注入 mailto（礼貌池）与 api_key（2026 起需 key）。"""
    p = dict(params)
    if _MAILTO:
        p["mailto"] = _MAILTO
    if _API_KEY:
        p["api_key"] = _API_KEY
    return p


def _cr_params(params: dict) -> dict:
    """给 Crossref 查询参数按需注入 mailto（礼貌池）。Crossref 不需 api_key。"""
    p = dict(params)
    if _MAILTO:
        p["mailto"] = _MAILTO
    return p


def _get_json(url: str) -> tuple[int, Any]:
    """返回 (http_code, parsed_json_or_None)。任何异常吞掉返回 (0, None)。"""
    req = urllib.request.Request(url, headers={"User-Agent": _user_agent(), "Accept": "application/json"})
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
def search_openalex(query: str, per_page: int = 10, from_date: str = "") -> tuple[int, list[dict]]:
    params = {
        "search": query,
        "per-page": str(per_page),
        "sort": "cited_by_count:desc",
        "select": "id,doi,title,publication_year,cited_by_count,"
                  "authorships,primary_location,abstract_inverted_index,type,"
                  "referenced_works",
    }
    # 定期追踪：只取 from_date 之后发表的（增量重跑用，YYYY-MM-DD）。
    if from_date:
        params["filter"] = "from_publication_date:" + from_date
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(_oa_params(params))
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
def search_crossref(query: str, rows: int = 10, from_date: str = "") -> tuple[int, list[dict]]:
    params = {
        "query.bibliographic": query,
        "rows": str(rows),
        "sort": "is-referenced-by-count",
        "order": "desc",
        "select": "DOI,title,author,issued,container-title,"
                  "is-referenced-by-count,type,abstract",
    }
    # 定期追踪：只取 from_date 之后发表的（Crossref 用 from-pub-date 过滤）。
    if from_date:
        params["filter"] = "from-pub-date:" + from_date
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(_cr_params(params))
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


def run(query: str, per_page: int = 10, offline_sample: bool = False,
        from_date: str = "", known_dois: set | None = None) -> dict:
    offline = False
    recs: list[dict] = []
    if not offline_sample:
        oa_code, oa = search_openalex(query, per_page, from_date)
        cr_code, cr = search_crossref(query, per_page, from_date)
        print(f"[HTTP] OpenAlex={oa_code} Crossref={cr_code}", file=sys.stderr)
        recs = oa + cr
        if oa_code == 0 and cr_code == 0:
            offline = True
    if offline_sample or offline:
        offline = True
        recs = _SYNTHETIC
        print("[OFFLINE] 网络不可达，使用内置合成样本验证管线。", file=sys.stderr)
    merged = dedup_merge(recs)
    out = {"query": query, "offline": offline, "from_date": from_date,
           "raw_count": len(recs), "merged_count": len(merged), "records": merged}
    # 定期追踪：给了已读库 DOI 集合，则切出"新增（去重后未见过）"条目做增量 diff。
    if known_dois is not None:
        known = {_norm_doi(d) for d in known_dois if d}
        new_recs = [r for r in merged if _norm_doi(r.get("doi")) and _norm_doi(r["doi"]) not in known]
        out["known_count"] = len(known)
        out["new_count"] = len(new_recs)
        out["new_records"] = new_recs
    return out


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



def _selftest() -> int:
    result = run("dairy goat behavior", per_page=3, offline_sample=True)
    assert result["offline"] is True, result
    assert result["raw_count"] >= 2 and result["merged_count"] >= 2, result
    dois = {r.get("doi") for r in result["records"]}
    assert "10.1016/j.compag.2021.100001" in dois, dois
    md = to_markdown(result["records"], "dairy goat behavior")
    assert "10.1016/j.compag.2021.100001" in md and "dairy goats" in md.lower(), md
    # 定期追踪增量 diff：已读库含合成样本里的一条 DOI，则新增应排除它。
    incr = run("dairy goat behavior", per_page=3, offline_sample=True,
               from_date="2020-01-01",
               known_dois={"10.1016/j.compag.2021.100001"})
    assert incr["from_date"] == "2020-01-01", incr
    assert incr["known_count"] == 1, incr
    new_dois = {r.get("doi") for r in incr["new_records"]}
    assert "10.1016/j.compag.2021.100001" not in new_dois, incr  # 已读，被剔
    assert "10.3390/ani9120999" in new_dois, incr                # 未读，留作新增
    assert incr["new_count"] == len(incr["new_records"]) >= 1, incr
    print("[selftest] PASS search_normalize (含 --from-date 增量 diff)")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="多源文献检索与规范化")
    ap.add_argument("query", nargs="?", default="dairy goat behavior")
    ap.add_argument("--per-page", type=int, default=10)
    ap.add_argument("--offline", action="store_true", help="强制用合成样本")
    ap.add_argument("--from-date", default="",
                    help="定期追踪：只取该日期(YYYY-MM-DD)之后发表的文献，做增量重跑")
    ap.add_argument("--known-dois", default="",
                    help="定期追踪：已读库 DOI 清单文件(每行一个)，输出标出新增条目")
    ap.add_argument("--selftest", action="store_true", help="run offline synthetic self-test")
    ap.add_argument("--json-out", default="")
    ap.add_argument("--md-out", default="")
    ap.add_argument("--mailto", default="",
                    help="礼貌池邮箱（也可设环境变量 OPENALEX_MAILTO / CROSSREF_MAILTO）；不传则匿名查")
    ap.add_argument("--api-key", default="",
                    help="OpenAlex API key（也可设环境变量 OPENALEX_API_KEY）；口径见本技能 references")
    args = ap.parse_args()

    global _MAILTO, _API_KEY
    if args.mailto:
        _MAILTO = args.mailto.strip()
    if args.api_key:
        _API_KEY = args.api_key.strip()

    if args.selftest:
        sys.exit(_selftest())

    known: set | None = None
    if args.known_dois:
        with open(args.known_dois, encoding="utf-8") as f:
            known = {ln.strip() for ln in f if ln.strip() and not ln.startswith("#")}

    result = run(args.query, args.per_page, offline_sample=args.offline,
                 from_date=args.from_date, known_dois=known)
    md = to_markdown(result["records"], args.query)

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    if args.md_out:
        with open(args.md_out, "w", encoding="utf-8") as f:
            f.write(md)

    print(md)
    summary = (f"\n[SUMMARY] query={args.query!r} offline={result['offline']} "
               f"raw={result['raw_count']} merged={result['merged_count']}")
    if args.from_date:
        summary += f" from_date={args.from_date}"
    if "new_count" in result:
        summary += f" known={result['known_count']} new={result['new_count']}"
    print(summary)


if __name__ == "__main__":
    main()



