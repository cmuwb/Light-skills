#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sycophancy_guard.py — 反谄媚硬协议的可计算部分。

实现 references/contract.md B 节:
  - 反驳应答 1-5 评分制的统计
  - concession-rate (给 4/5 的让步比例) 计算与 >50% 报警
  - 禁连续让步检查 (同一作者连续两条都 >=4 且第二条无新证据 -> 违规)
  - 让步必须挂证据 (4/5 无 evidence -> 强制降为 3)

无外部依赖, 自带 __main__ 自测。
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Rebuttal:
    text: str
    score: int          # 1-5, 见 contract.md 表
    has_new_evidence: bool = False   # 是否挂了新证据/新检索


def normalize(rebuttals: list) -> list:
    """让步(4/5)必须挂证据, 否则强制降为3。返回(归一化后score, 备注)。"""
    out = []
    for r in rebuttals:
        s, note = r.score, ""
        if s not in (1, 2, 3, 4, 5):
            raise ValueError(f"score must be 1-5, got {s}")
        if s >= 4 and not r.has_new_evidence:
            s, note = 3, "让步无新证据->强制降为3"
        out.append((s, note))
    return out


def concession_rate(norm_scores: list) -> float:
    if not norm_scores:
        return 0.0
    concessions = sum(1 for s in norm_scores if s >= 4)
    return round(concessions / len(norm_scores) * 100, 1)


def check_consecutive(norm_scores: list) -> list:
    """禁连续让步: 相邻两条都>=4 即违规(归一化后仍>=4说明都挂了证据,
    但协议仍禁止连续让步,需第二条独立证明,此处标记需人工复核)。"""
    flags = []
    for i in range(1, len(norm_scores)):
        if norm_scores[i] >= 4 and norm_scores[i - 1] >= 4:
            flags.append(f"连续让步 @反驳#{i}#{i+1} -> 需第二条独立新证据,否则按<=3")
    return flags


def audit(rebuttals: list) -> dict:
    norm = normalize(rebuttals)
    scores = [s for s, _ in norm]
    rate = concession_rate(scores)
    consec = check_consecutive(scores)
    alert = rate > 50.0
    return {
        "normalized": norm,
        "concession_rate": rate,
        "sycophancy_alert": alert,
        "alert_msg": f"⚠ SYCOPHANCY-ALERT: concession-rate={rate}%" if alert else "",
        "consecutive_flags": consec,
    }


def _selftest():
    # 案例1: worked example 的两条反驳 (A=2 重述, B=5 新证据)
    rs = [Rebuttal("数据私有所以算首次", 2),
          Rebuttal("补了ISIC公开集+4.1% p<0.01", 5, has_new_evidence=True)]
    a = audit(rs)
    print(f"[1] rate={a['concession_rate']}% alert={a['sycophancy_alert']}")
    assert a["concession_rate"] == 50.0 and not a["sycophancy_alert"]

    # 案例2: 谄媚 - 4条里3条让步且都挂证据 -> rate 75% 报警
    rs2 = [Rebuttal("e1", 5, True), Rebuttal("e2", 5, True),
           Rebuttal("e3", 3), Rebuttal("e4", 4, True)]
    a2 = audit(rs2)
    print(f"[2] rate={a2['concession_rate']}% -> {a2['alert_msg']}")
    assert a2["sycophancy_alert"] and a2["concession_rate"] == 75.0
    assert a2["consecutive_flags"], "应检测到连续让步"

    # 案例3: 让步无证据 -> 强制降为3, 不计入concession
    rs3 = [Rebuttal("空口让步", 5, has_new_evidence=False),
           Rebuttal("普通澄清", 3)]
    a3 = audit(rs3)
    print(f"[3] normalized={a3['normalized']} rate={a3['concession_rate']}%")
    assert a3["concession_rate"] == 0.0, a3
    assert "强制降为3" in a3["normalized"][0][1]

    # 案例4: 范围校验
    try:
        normalize([Rebuttal("bad", 6)])
        raise AssertionError("should raise")
    except ValueError:
        print("[4] score range guard ... OK")

    print("\nALL SELFTESTS PASSED")


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if len(sys.argv) > 2 or (len(sys.argv) == 2 and sys.argv[1] != "--selftest"):
        raise SystemExit(f"usage: python {sys.argv[0]} [--selftest]")
    _selftest()
