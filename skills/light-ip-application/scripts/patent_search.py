#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patent_search.py — 在先技术(prior-art)检索辅助。

诚实声明(d:/skill/Light/CONVENTIONS.md):
  * OpenAlex 是本脚本唯一"免费、免 key、可程序化"的真实数据源(curl 实测 HTTP 200),
    用于"非专利文献(NPL)"型在先技术。
  * 专利数据库(EPO OPS / The Lens / USPTO ODP)均需注册凭证,本脚本提供
    "构造请求"的适配器(build_*_request),便于用户带 key 时直接发起;不内置任何
    伪造 key,也不臆造返回。
  * 端点状态(2026-06 curl 实测,见 references.md):
      - OpenAlex            GET  api.openalex.org/works                 -> 200 (免 key)
      - EPO OPS  auth       POST ops.epo.org/3.2/auth/accesstoken       -> 401 (需 key)
      - The Lens patent     POST api.lens.org/patent/search             -> 401 (需 token)
      - USPTO 程序化 API    POST api.uspto.gov/api/v1/patent/.../search -> 401 (需 X-Api-Key)
      - 旧 api.patentsview.org -> 301 弃用; search.patentsview.org -> DNS 失效
  * 检索结果仅供查新参考,FTO/新颖性/无效结论须由专利代理师/律师判定。

无网络/无 key 时:运行 `python patent_search.py --selftest` 用内置离线样本自测
请求构造与排序逻辑,不发任何网络请求。
"""
from __future__ import annotations
import argparse
import json
import sys
import urllib.parse
import urllib.request

OPENALEX_BASE = "https://api.openalex.org"


def _http_get_json(url: str, timeout: float = 30.0) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "light-ip-application/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def build_openalex_url(query: str, *, from_year: int | None = None,
                       to_year: int | None = None, per_page: int = 25,
                       mailto: str | None = None) -> str:
    """构造 OpenAlex /works 检索 URL(NPL 在先技术)。

    per_page 上限 200(API 实测 201 -> HTTP 400)。建议带 mailto 进 polite pool。
    """
    per_page = max(1, min(int(per_page), 200))
    params: list[tuple[str, str]] = [
        ("search", query),
        ("per_page", str(per_page)),
        ("select", "id,title,publication_year,doi,cited_by_count,authorships"),
    ]
    filters = []
    if from_year is not None:
        filters.append(f"from_publication_date:{int(from_year)}-01-01")
    if to_year is not None:
        filters.append(f"to_publication_date:{int(to_year)}-12-31")
    if filters:
        params.append(("filter", ",".join(filters)))
    if mailto:
        params.append(("mailto", mailto))
    return f"{OPENALEX_BASE}/works?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)


def search_openalex_npl(query: str, **kw) -> list[dict]:
    """实发 OpenAlex 检索,归一化为 prior-art 候选记录。免 key。"""
    url = build_openalex_url(query, **kw)
    data = _http_get_json(url)
    out = []
    for w in data.get("results", []):
        insts = []
        for a in (w.get("authorships") or [])[:5]:
            for ins in (a.get("institutions") or []):
                if ins.get("display_name"):
                    insts.append(ins["display_name"])
        out.append({
            "source": "OpenAlex(NPL)",
            "id": w.get("id"),
            "title": w.get("title"),
            "year": w.get("publication_year"),
            "doi": w.get("doi"),
            "cited_by_count": w.get("cited_by_count", 0),
            "institutions": sorted(set(insts))[:5],
        })
    return out


# ---- 专利库适配器:构造请求(需用户自带 key),不内置伪造凭证 ----

def build_lens_request(query: str, size: int = 25) -> dict:
    """The Lens 专利检索请求体(ES 风格 DSL)。发起需 Authorization: Bearer <token>。"""
    return {
        "method": "POST",
        "url": "https://api.lens.org/patent/search",
        "headers": {"Authorization": "Bearer <YOUR_LENS_TOKEN>",
                    "Content-Type": "application/json"},
        "body": {"query": {"match": {"title": query}}, "size": int(size),
                 "include": ["lens_id", "biblio", "abstract"]},
    }


def build_epo_ops_search(cql: str, range_hdr: str = "1-25") -> dict:
    """EPO OPS published-data 检索。先 OAuth2 换 Bearer token(/auth/accesstoken)。"""
    return {
        "method": "GET",
        "url": "https://ops.epo.org/3.2/rest-services/published-data/search",
        "params": {"q": cql},
        "headers": {"Authorization": "Bearer <OPS_ACCESS_TOKEN>", "Range": range_hdr},
        "note": "CQL 字段: ti= ab= ta= txt= pa= in= cpc= ipc= pn= pd=; 每页<=100,翻页用 Range 头",
    }


def build_uspto_odp_request(query_json: dict) -> dict:
    """USPTO 程序化 API(ODP 迁移后)。需 X-Api-Key(api.uspto.gov 实测 401=需鉴权)。"""
    return {
        "method": "POST",
        "url": "https://api.uspto.gov/api/v1/patent/applications/search",
        "headers": {"X-Api-Key": "<YOUR_USPTO_ODP_KEY>", "Content-Type": "application/json"},
        "body": query_json,
        "note": "旧 api.patentsview.org 已 301 弃用; search.patentsview.org DNS 失效; 统一走 api.uspto.gov",
    }


def rank_candidates(records: list[dict]) -> list[dict]:
    """按被引次数降序排候选(被引高者更可能是关键在先技术)。"""
    return sorted(records, key=lambda r: r.get("cited_by_count", 0) or 0, reverse=True)


_OFFLINE_SAMPLE = [
    {"source": "OpenAlex(NPL)", "id": "W1", "title": "A graphene battery method",
     "year": 2017, "doi": "10.x/a", "cited_by_count": 300, "institutions": ["MIT"]},
    {"source": "OpenAlex(NPL)", "id": "W2", "title": "Neural net patent landscape",
     "year": 2019, "doi": "10.x/b", "cited_by_count": 50, "institutions": ["THU"]},
]


def _selftest() -> int:
    # 1) URL 构造与 per_page 上限钳制
    u = build_openalex_url("graphene battery", from_year=2015, to_year=2020,
                           per_page=999, mailto="a@b.com")
    assert "per_page=200" in u, u
    assert "from_publication_date%3A2015" in u or "from_publication_date:2015" in u, u
    assert "mailto=a%40b.com" in u, u
    # 2) 适配器请求体结构
    assert build_lens_request("x")["url"].endswith("/patent/search")
    assert build_epo_ops_search("ti=x")["params"]["q"] == "ti=x"
    assert build_uspto_odp_request({"q": "x"})["headers"]["X-Api-Key"].startswith("<")
    # 3) 排序
    ranked = rank_candidates(list(_OFFLINE_SAMPLE))
    assert ranked[0]["cited_by_count"] == 300, ranked
    print("[selftest] OK  url=", u)
    print("[selftest] ranked top:", ranked[0]["title"])
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="在先技术检索辅助(OpenAlex NPL + 专利库请求构造)")
    ap.add_argument("query", nargs="?", help="检索关键词")
    ap.add_argument("--from-year", type=int, default=None)
    ap.add_argument("--to-year", type=int, default=None)
    ap.add_argument("--per-page", type=int, default=10)
    ap.add_argument("--mailto", default=None, help="进入 OpenAlex polite pool")
    ap.add_argument("--selftest", action="store_true", help="离线自测(不联网)")
    ap.add_argument("--print-adapters", action="store_true", help="打印专利库请求构造示例")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()
    if args.print_adapters:
        print(json.dumps({
            "lens": build_lens_request("neural network"),
            "epo_ops": build_epo_ops_search('ti=neural and ab=network'),
            "uspto_odp": build_uspto_odp_request({"q": "neural network"}),
        }, ensure_ascii=False, indent=2))
        return 0
    if not args.query:
        ap.error("需要 query(或用 --selftest / --print-adapters)")
    recs = rank_candidates(search_openalex_npl(
        args.query, from_year=args.from_year, to_year=args.to_year,
        per_page=args.per_page, mailto=args.mailto))
    print(f"# NPL 在先技术候选(OpenAlex) query={args.query!r} n={len(recs)}")
    for i, r in enumerate(recs, 1):
        print(f"{i}. [{r['year']}] {r['title']}  (cited={r['cited_by_count']}) {r['doi'] or ''}")
    print("\n注:仅 NPL 文献;专利库检索请用 --print-adapters 取请求模板,自带 key 发起。"
          "查新/FTO 结论须代理师判定。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
