#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rank_ideas.py — 候选 idea 排序（m03 内部 triage，收敛三套评分为唯一裁定）。

idea-generation 原有三套评分（五维1-5 / 三维1-10 / 影响×工作量二维）并存却无统一裁定规则，
操作者困惑该信哪个。本脚本明确**分工**并给唯一排序：
  - 影响×工作量二维 → 做收敛漏斗主排序键（高影响低工作量优先 = 高"性价比"）
  - 三维(novelty/feasibility/impact 1-10) → 做快速 triage 入场分（可选）
  这是 m03 **内部 triage**，不替代 m04 的八维严审——只决定"先把哪几个送 m04"。

输入：JSON 数组，每条 {id, title, impact(1-5), effort(1-5), novelty?, feasibility?, impact10?}。
排序键（字典序）：性价比 impact/effort 降序 → impact 降序 → effort 升序 → id 升序（确定性）。
输出 top-k + 完整排名 + 每条的"先做/缓做/砍"建议。

诚实：影响/工作量是**主观快评**，本脚本只做"按声明值确定性排序"，不判 idea 真实价值（那靠 m04）。
分数从哪来要人填，垃圾进垃圾出。

用法：
  python rank_ideas.py --in candidates.json --top-k 3
  python rank_ideas.py --selftest
"""
from __future__ import annotations
import argparse
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def rank(items: list, top_k: int = 0) -> dict:
    rows = []
    for it in items:
        imp = float(it.get("impact", 0) or 0)
        eff = float(it.get("effort", 0) or 0)
        ratio = round(imp / eff, 3) if eff > 0 else (imp if imp else 0.0)
        rows.append({
            "id": it.get("id", "?"), "title": it.get("title", ""),
            "impact": imp, "effort": eff, "value_ratio": ratio,
            "novelty": it.get("novelty"), "feasibility": it.get("feasibility"),
        })
    # 字典序：性价比↓ → impact↓ → effort↑ → id↑
    rows.sort(key=lambda r: (-r["value_ratio"], -r["impact"], r["effort"], str(r["id"])))
    # 建议分档：前 1/3 先做、中段缓做、低性价比(<1 且影响低)砍
    n = len(rows)
    for i, r in enumerate(rows):
        if r["value_ratio"] < 1 and r["impact"] <= 2:
            r["advice"] = "砍（低影响且工作量不划算）"
        elif i < max(1, n // 3):
            r["advice"] = "先做（高性价比，优先送 m04）"
        else:
            r["advice"] = "缓做（次优先，资源允许再送）"
    passlist = rows[:top_k] if top_k else rows
    return {"n": n, "ranked": rows, "top_k": top_k, "shortlist": passlist,
            "note": ("影响×工作量为主观快评，本脚本只做确定性排序做 m03 内部 triage，"
                     "决定先送哪几个 idea 给 m04；不替代 m04 八维严审。")}


def render(res: dict) -> str:
    lines = [f"# 候选 idea 排序（m03 triage，共 {res['n']} 条）", "",
             "| 排名 | id | 标题 | 影响 | 工作量 | 性价比 | 建议 |",
             "|---|---|---|---|---|---|---|"]
    for i, r in enumerate(res["ranked"], 1):
        lines.append(f"| {i} | {r['id']} | {(r['title'] or '')[:40]} | {r['impact']:.0f} | "
                     f"{r['effort']:.0f} | {r['value_ratio']} | {r['advice']} |")
    lines += ["", f"> {res['note']}"]
    return "\n".join(lines)


def _selftest() -> int:
    print("### rank_ideas 离线自测", file=sys.stderr)
    items = [
        {"id": "I-01", "title": "高影响低工作量", "impact": 5, "effort": 2},   # 性价比 2.5
        {"id": "I-02", "title": "中规中矩", "impact": 3, "effort": 3},          # 1.0
        {"id": "I-03", "title": "低影响高工作量", "impact": 2, "effort": 5},    # 0.4 → 砍
        {"id": "I-04", "title": "高影响高工作量", "impact": 5, "effort": 5},    # 1.0
    ]
    res = rank(items, top_k=2)
    order = [r["id"] for r in res["ranked"]]
    # I-01 性价比最高排第一
    assert order[0] == "I-01", order
    # I-03 低影响低性价比 → 砍
    i03 = next(r for r in res["ranked"] if r["id"] == "I-03")
    assert "砍" in i03["advice"], i03
    # I-01 先做
    i01 = next(r for r in res["ranked"] if r["id"] == "I-01")
    assert "先做" in i01["advice"], i01
    # 同性价比(I-02/I-04 都 1.0) 按 impact 降序：I-04(5) 在 I-02(3) 前
    assert order.index("I-04") < order.index("I-02"), order
    # top_k 截断
    assert len(res["shortlist"]) == 2, res
    # 渲染
    md = render(res)
    assert "性价比" in md and "triage" in md, md
    # effort=0 不崩
    rank([{"id": "x", "impact": 3, "effort": 0}])
    print("[selftest] PASS rank_ideas offline")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="候选 idea 排序（m03 内部 triage）")
    ap.add_argument("--in", dest="infile", help="候选 JSON 数组")
    ap.add_argument("--top-k", type=int, default=0)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest or not args.infile:
        return _selftest()
    with open(args.infile, encoding="utf-8") as f:
        items = json.load(f)
    res = rank(items, args.top_k)
    print(json.dumps(res, ensure_ascii=False, indent=2) if args.json else render(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
