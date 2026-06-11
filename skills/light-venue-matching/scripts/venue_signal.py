#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""venue_signal.py — 投稿 venue 五信号对照查询 (Light / light-venue-matching)

输入：--issn <ISSN> 和/或 --author "姓名"。
封装 OpenAlex Sources / Authors 查询，输出五信号对照 JSON：
  1. 发文量趋势        ← OpenAlex Sources counts_by_year
  2. 自引率粗查        ← 采样本刊近作 referenced_works，批量解析回指本刊比例(粗略外向自引)
  3. 审稿周期线索      ← db01 卡(--venues-csv 按 ISSN 取，或 --card-fields 内联)
  4. 作者与该刊匹配度  ← OpenAlex Authors x_concepts/topics 与 Sources 主题重叠
  5. APC 与分区        ← db01 卡 + OpenAlex Sources apc_usd

诚实约定：
- OpenAlex 2026 起需免费 API key；key/限流/计费/退避的唯一口径见
  m01(light-literature-search) references「OpenAlex 接入真相源」节，本脚本不复写数字，
  仅加 ?mailto= 进礼貌池。
- 任一信号取数失败 → 该信号 status="unavailable" + reason，不编数、不崩溃（能查多少出多少）。
- 作者重名严重：Authors search 取首个命中仅作线索，输出标 disambiguation_caveat，
  需 ORCID/机构二次确认，禁当定论（与 SKILL rubric 一致）。
- 自引率为"外向自引"粗估(本刊论文引用本刊的比例)，非官方入向期刊自引率，输出已注明 method。
- db01 审稿周期/APC/分区为社区/官方混合口径，引用各标来源年份(见 SKILL §3)。

用法：
    python scripts/venue_signal.py --issn 1234-5678 --author "Zhang San"
    python scripts/venue_signal.py --issn 1234-5678 --venues-csv <db01路径>/venues.csv
    python scripts/venue_signal.py --selftest
"""
from __future__ import annotations
import argparse
import csv
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

MAILTO = "light-skill@example.com"
UA = "Light-venue-matching/1.0 (mailto:%s)" % MAILTO
TIMEOUT = 30
OA = "https://api.openalex.org"

# 采样上限（控制请求数；注释解释取舍）
SELF_REF_SAMPLE_WORKS = 25     # 采样本刊近作篇数
SELF_REF_MAX_REFS = 200        # 解析的被引文献 ID 上限
RESOLVE_CHUNK = 50             # OpenAlex OR 过滤单批上限


def http_fetch(url: str) -> dict:
    """真实 GET，返回解析后的 JSON dict。失败抛异常由上层捕获降级。"""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


def _add_mailto(params: dict) -> str:
    p = dict(params)
    p.setdefault("mailto", MAILTO)
    return urllib.parse.urlencode(p)


def _sid_short(sid: str) -> str:
    return (sid or "").rsplit("/", 1)[-1]


# ---- OpenAlex 实体查询 -------------------------------------------------

def oa_source_by_issn(issn: str, fetch) -> dict | None:
    url = f"{OA}/sources/issn:{urllib.parse.quote(issn)}?" + _add_mailto({
        "select": "id,display_name,works_count,cited_by_count,apc_usd,"
                  "is_oa,is_in_doaj,summary_stats,counts_by_year,x_concepts,topics"})
    return fetch(url)


def oa_author_by_name(name: str, fetch) -> dict | None:
    url = f"{OA}/authors?" + _add_mailto({
        "search": name, "per_page": 1,
        "select": "id,display_name,works_count,cited_by_count,summary_stats,"
                  "last_known_institutions,x_concepts,topics,orcid"})
    data = fetch(url)
    results = (data or {}).get("results") or []
    return results[0] if results else None


# ---- 五信号 ------------------------------------------------------------

def signal_volume_trend(source: dict) -> dict:
    """信号1：发文量趋势（counts_by_year 近 3 年均值 vs 更早 3 年均值）。"""
    if not source:
        return {"status": "unavailable", "reason": "source 未取到"}
    cby = sorted(source.get("counts_by_year") or [], key=lambda r: r.get("year", 0))
    years = [(r.get("year"), r.get("works_count", 0)) for r in cby if r.get("year")]
    if len(years) < 4:
        return {"status": "unavailable", "reason": "counts_by_year 不足 4 年", "by_year": years}
    recent = [w for _, w in years[-3:]]
    earlier = [w for _, w in years[-6:-3]] or [w for _, w in years[:-3]]
    r_mean = sum(recent) / len(recent)
    e_mean = sum(earlier) / len(earlier) if earlier else 0
    if e_mean == 0:
        trend = "unknown"
    elif r_mean > e_mean * 1.15:
        trend = "rising"
    elif r_mean < e_mean * 0.85:
        trend = "declining"
    else:
        trend = "stable"
    return {"status": "ok", "trend": trend,
            "recent3y_mean_works": round(r_mean, 1),
            "earlier3y_mean_works": round(e_mean, 1),
            "by_year": years[-6:],
            "note": "发文量激增(rising 且量大)可能是掠夺信号，对照 SKILL 预警筛查"}


def _concept_weights(entity: dict) -> dict:
    """从实体取 {concept_id: score}，优先 x_concepts，回退 topics。"""
    out = {}
    for c in (entity.get("x_concepts") or []):
        cid = _sid_short(c.get("id", ""))
        if cid:
            out[cid] = float(c.get("score", 0) or 0)
    if out:
        return out
    for t in (entity.get("topics") or []):
        tid = _sid_short(t.get("id", ""))
        if tid:
            out[tid] = float(t.get("count", 0) or 0)
    return out


def signal_author_match(author: dict, source: dict) -> dict:
    """信号4：作者与该刊主题重叠（x_concepts/topics 加权 Jaccard）。"""
    if not author or not source:
        return {"status": "unavailable", "reason": "author 或 source 未取到"}
    aw = _concept_weights(author)
    sw = _concept_weights(source)
    if not aw or not sw:
        return {"status": "unavailable", "reason": "缺主题/概念字段"}
    inter = set(aw) & set(sw)
    union = set(aw) | set(sw)
    jacc = len(inter) / len(union) if union else 0
    overlap_score = sum(min(aw[c], sw[c]) for c in inter)
    level = "高" if jacc >= 0.4 else ("中" if jacc >= 0.15 else "低")
    shared = sorted(inter, key=lambda c: min(aw[c], sw[c]), reverse=True)[:5]
    return {"status": "ok", "match_level": level,
            "jaccard": round(jacc, 3), "weighted_overlap": round(overlap_score, 3),
            "shared_concepts": shared,
            "disambiguation_caveat": "作者按姓名 search 取首个命中，重名未排歧，"
                                     "需 ORCID/机构二次确认，勿当定论"}


def signal_self_citation(source: dict, fetch) -> dict:
    """信号2：自引率粗查（外向自引：采样本刊近作 → 解析其 referenced_works → 回指本刊比例）。

    说明：OpenAlex 不直接给官方"入向期刊自引率"。这里用可计算的外向自引粗估：
    抽 N 篇本刊近作，收集它们引用的文献，批量解析这些被引文献的 primary source，
    统计回指本刊的占比。是粗略信号（受样本与年份影响），输出已注明 method 与样本量。
    任一步失败 → unavailable，不编数。
    """
    if not source:
        return {"status": "unavailable", "reason": "source 未取到"}
    sid = _sid_short(source.get("id", ""))
    if not sid:
        return {"status": "unavailable", "reason": "source 无 id"}
    try:
        sample_url = f"{OA}/works?" + _add_mailto({
            "filter": f"primary_location.source.id:{sid}",
            "select": "id,referenced_works", "per_page": SELF_REF_SAMPLE_WORKS,
            "sort": "publication_date:desc"})
        works = (fetch(sample_url) or {}).get("results") or []
        ref_ids = []
        for w in works:
            ref_ids.extend(_sid_short(r) for r in (w.get("referenced_works") or []))
        ref_ids = [r for r in ref_ids if r][:SELF_REF_MAX_REFS]
        if not ref_ids:
            return {"status": "unavailable", "reason": "采样近作无 referenced_works",
                    "sample_works": len(works)}
        self_hits = 0
        for i in range(0, len(ref_ids), RESOLVE_CHUNK):
            chunk = ref_ids[i:i + RESOLVE_CHUNK]
            url = f"{OA}/works?" + _add_mailto({
                "filter": f"ids.openalex:{'|'.join(chunk)},primary_location.source.id:{sid}",
                "select": "id", "per_page": RESOLVE_CHUNK})
            self_hits += (fetch(url) or {}).get("meta", {}).get("count", 0)
        rate = self_hits / len(ref_ids)
        flag = "偏高(>25%，留意自引操纵)" if rate > 0.25 else "常规区间"
        return {"status": "ok", "self_ref_rate": round(rate, 3),
                "sample_works": len(works), "refs_resolved": len(ref_ids),
                "self_refs": self_hits, "flag": flag,
                "method": "外向自引粗估(本刊论文引用本刊比例)，非官方入向自引率；受样本/年份影响"}
    except Exception as e:  # noqa: BLE001 — 优雅降级
        return {"status": "unavailable", "reason": f"查询失败: {e.__class__.__name__}"}


def _load_card_from_csv(issn: str, venue_name: str, csv_path: str) -> dict | None:
    """按 ISSN 或刊名从 db01 venues.csv 取一行卡（indexing/issn 字段含 ISSN 时匹配）。"""
    try:
        with open(csv_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                blob = " ".join(str(v) for v in row.values())
                if (issn and issn in blob) or (venue_name and venue_name and
                        venue_name.lower() in (row.get("venue_name", "") or "").lower()):
                    return row
    except OSError:
        return None
    return None


def signal_review_cycle(card: dict | None) -> dict:
    """信号3：审稿周期线索（来自 db01 卡 review_cycle 字段）。"""
    if not card:
        return {"status": "unavailable",
                "reason": "无 db01 卡(传 --venues-csv 或 --card-fields review_cycle=...)"}
    rc = (card.get("review_cycle") or "").strip()
    if not rc:
        return {"status": "unavailable", "reason": "db01 卡 review_cycle 为空"}
    fast = any(k in rc for k in ("周", "week", "天", "day")) and \
        not any(k in rc for k in ("月", "month"))
    return {"status": "ok", "review_cycle": rc,
            "fast_flag": "审稿异常快需对照掠夺特征" if fast else "—",
            "source": f"db01 卡 last_checked={card.get('last_checked_date', '?')}，投前重核"}


def signal_apc_quartile(card: dict | None, source: dict) -> dict:
    """信号5：APC 与分区（db01 卡为主，OpenAlex apc_usd 兜底）。"""
    out = {"status": "ok"}
    got = False
    if card:
        for k in ("apc_fee", "cas_quartile", "jcr_quartile", "impact_factor",
                  "level", "indexing"):
            v = (card.get(k) or "").strip()
            if v:
                out[k] = v
                got = True
        out["source"] = f"db01 卡 last_checked={card.get('last_checked_date', '?')}"
    oa_apc = (source or {}).get("apc_usd")
    if oa_apc is not None:
        out["openalex_apc_usd"] = oa_apc
        got = True
    if (source or {}).get("is_in_doaj"):
        out["doaj"] = True
        got = True
    if not got:
        return {"status": "unavailable", "reason": "db01 卡与 OpenAlex 均无 APC/分区"}
    out["note"] = "三套分区(JCR/SJR/中科院)口径不同，引用须标来源年份，禁混用(SKILL §3)"
    return out


def assemble(issn: str, author_name: str, card: dict | None, fetch) -> dict:
    """跑全部五信号，组装对照 JSON。各信号独立降级。"""
    source = None
    if issn:
        try:
            source = oa_source_by_issn(issn, fetch)
        except Exception as e:  # noqa: BLE001
            source = None
            src_err = e.__class__.__name__
    author = None
    if author_name:
        try:
            author = oa_author_by_name(author_name, fetch)
        except Exception:  # noqa: BLE001
            author = None
    report = {
        "query": {"issn": issn or None, "author": author_name or None},
        "venue": {
            "openalex_id": _sid_short(source.get("id", "")) if source else None,
            "display_name": source.get("display_name") if source else None,
            "works_count": source.get("works_count") if source else None,
            "h_index": ((source or {}).get("summary_stats") or {}).get("h_index"),
        },
        "author": {
            "display_name": author.get("display_name") if author else None,
            "h_index": ((author or {}).get("summary_stats") or {}).get("h_index"),
            "orcid": author.get("orcid") if author else None,
        } if author_name else None,
        "signals": {
            "1_volume_trend": signal_volume_trend(source),
            "2_self_citation": signal_self_citation(source, fetch),
            "3_review_cycle": signal_review_cycle(card),
            "4_author_match": signal_author_match(author, source) if author_name
            else {"status": "unavailable", "reason": "未提供 --author"},
            "5_apc_quartile": signal_apc_quartile(card, source),
        },
    }
    if issn and source is None:
        report["venue"]["fetch_error"] = locals().get("src_err", "未取到 source")
    avail = sum(1 for s in report["signals"].values() if s.get("status") == "ok")
    report["summary"] = {"signals_ok": avail, "signals_total": 5,
                         "caveat": "OpenAlex 接入口径见 m01 真相源节；期刊数据投前重核(CONVENTIONS §1)"}
    return report


# ---- 离线 selftest（mock fetcher，不打网络）----------------------------

class _MockFetcher:
    """按 URL 形态返回 mock JSON，覆盖五信号全路径。"""

    def __init__(self):
        # 80 篇近作各引 1 篇；解析时每 4 篇回指本刊 → 自引率应 ≈0.25
        self._work_ids = [f"W{i:02d}" for i in range(80)]

    def __call__(self, url: str) -> dict:
        if "/sources/issn:" in url:
            return self._source()
        if "/authors?" in url:
            return {"results": [self._author()]}
        if "ids.openalex" in url:  # 解析回指本刊的批次（冒号被编码，匹配前缀即可）
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            filt = qs.get("filter", [""])[0]
            chunk = []
            for part in filt.split(","):
                if part.startswith("ids.openalex:"):
                    chunk = part.split(":", 1)[1].split("|")
            hits = sum(1 for wid in chunk if self._is_self(wid))
            return {"meta": {"count": hits}, "results": []}
        if "/works?" in url:  # 采样近作
            return {"results": [{"id": f"S{i}", "referenced_works":
                    [f"https://openalex.org/{w}"]}
                    for i, w in enumerate(self._work_ids)]}
        raise RuntimeError(f"mock 未覆盖 URL: {url}")

    @staticmethod
    def _is_self(wid: str) -> bool:
        try:
            return int(wid[1:]) % 4 == 0
        except ValueError:
            return False

    @staticmethod
    def _source() -> dict:
        return {
            "id": "https://openalex.org/S123", "display_name": "Journal of Mock Studies",
            "works_count": 5000, "cited_by_count": 90000, "apc_usd": 1800,
            "is_oa": True, "is_in_doaj": True,
            "summary_stats": {"h_index": 95, "2yr_mean_citedness": 4.2},
            "counts_by_year": [
                {"year": 2019, "works_count": 200}, {"year": 2020, "works_count": 210},
                {"year": 2021, "works_count": 230}, {"year": 2022, "works_count": 300},
                {"year": 2023, "works_count": 340}, {"year": 2024, "works_count": 360}],
            "x_concepts": [{"id": "https://openalex.org/C41008148", "score": 80},
                           {"id": "https://openalex.org/C154945302", "score": 60},
                           {"id": "https://openalex.org/C119857082", "score": 40}],
        }

    @staticmethod
    def _author() -> dict:
        return {
            "id": "https://openalex.org/A99", "display_name": "Zhang San",
            "works_count": 60, "cited_by_count": 1500,
            "summary_stats": {"h_index": 22}, "orcid": None,
            "x_concepts": [{"id": "https://openalex.org/C41008148", "score": 75},
                           {"id": "https://openalex.org/C154945302", "score": 50},
                           {"id": "https://openalex.org/C777", "score": 20}],
        }


def _selftest() -> int:
    fetch = _MockFetcher()
    card = {"venue_name": "Journal of Mock Studies", "review_cycle": "约 8 周一审",
            "apc_fee": "1800 USD", "cas_quartile": "2区", "jcr_quartile": "Q2",
            "last_checked_date": "2026-06-11", "indexing": "SCIE; ISSN 1234-5678"}
    rep = assemble("1234-5678", "Zhang San", card, fetch)
    sig = rep["signals"]
    assert sig["1_volume_trend"]["status"] == "ok", sig["1_volume_trend"]
    assert sig["1_volume_trend"]["trend"] == "rising", sig["1_volume_trend"]
    assert sig["2_self_citation"]["status"] == "ok", sig["2_self_citation"]
    assert abs(sig["2_self_citation"]["self_ref_rate"] - 0.25) < 0.05, sig["2_self_citation"]
    assert sig["3_review_cycle"]["status"] == "ok", sig["3_review_cycle"]
    assert sig["4_author_match"]["status"] == "ok", sig["4_author_match"]
    assert sig["4_author_match"]["match_level"] in ("高", "中"), sig["4_author_match"]
    assert sig["5_apc_quartile"]["status"] == "ok", sig["5_apc_quartile"]
    assert rep["summary"]["signals_ok"] == 5, rep["summary"]

    # 降级路径：无卡 + 无作者 → 信号3/4 unavailable，不崩
    rep2 = assemble("1234-5678", "", None, fetch)
    assert rep2["signals"]["3_review_cycle"]["status"] == "unavailable"
    assert rep2["signals"]["4_author_match"]["status"] == "unavailable"
    assert rep2["signals"]["1_volume_trend"]["status"] == "ok"

    # source 取数失败 → venue fetch_error，信号不崩
    def boom(url):
        raise urllib.error.URLError("offline")
    rep3 = assemble("1234-5678", "", card, boom)
    assert rep3["signals"]["1_volume_trend"]["status"] == "unavailable"
    assert rep3["signals"]["3_review_cycle"]["status"] == "ok"  # 卡信号不依赖网络
    print("[selftest] PASS venue_signal（五信号 + 降级 + 离线）")
    return 0


def _parse_card_fields(pairs: list[str]) -> dict | None:
    if not pairs:
        return None
    card = {}
    for p in pairs:
        if "=" in p:
            k, v = p.split("=", 1)
            card[k.strip()] = v.strip()
    return card or None


def main() -> None:
    ap = argparse.ArgumentParser(description="投稿 venue 五信号对照查询")
    ap.add_argument("--issn", default="", help="期刊 ISSN（信号1/2/5 主键）")
    ap.add_argument("--author", default="", help="作者姓名（信号4，重名需 ORCID 排歧）")
    ap.add_argument("--venues-csv", default="", help="db01 venues.csv 路径，按 ISSN/刊名取卡")
    ap.add_argument("--card-fields", nargs="*", default=[],
                    help="内联 db01 卡字段，如 review_cycle='8周' apc_fee='1800 USD'")
    ap.add_argument("--json-out", default="")
    ap.add_argument("--selftest", action="store_true", help="离线 mock 自测")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(_selftest())

    if not args.issn and not args.author:
        ap.error("至少提供 --issn 或 --author 其一")

    card = _parse_card_fields(args.card_fields)
    if card is None and args.venues_csv:
        card = _load_card_from_csv(args.issn, args.author, args.venues_csv)

    report = assemble(args.issn, args.author, card, http_fetch)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            f.write(text)
    print(text)
    s = report["summary"]
    print(f"\n[SUMMARY] signals_ok={s['signals_ok']}/{s['signals_total']}", file=sys.stderr)


if __name__ == "__main__":
    main()
