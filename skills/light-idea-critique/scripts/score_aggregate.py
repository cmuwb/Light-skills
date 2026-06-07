#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""score_aggregate.py — idea 严审加权聚合 + 否决项 + 判决映射。

实现 references/rubric.md 的：
  - 八维度权重加权求和 (Weighted, 0-100)
  - Weighted -> Overall(1-10) 线性映射
  - 否决项 (gate before score) 优先于加权分
  - decision mapping 表

无外部数据依赖；自带 __main__ 用合成数据自测（含 examples 的皮肤镜案例）。
仅用标准库，便于在任意环境跑通。
"""
from __future__ import annotations
from dataclasses import dataclass, field

# 维度 -> 权重（合计 1.00），见 rubric.md
WEIGHTS = {
    "originality": 0.20,
    "soundness": 0.18,
    "data": 0.14,
    "experiment": 0.14,
    "contribution": 0.13,
    "delta": 0.08,
    "feasibility": 0.07,
    "impact": 0.06,
}
CORE_DIMS = ("originality", "soundness", "data", "experiment")


@dataclass
class Verdict:
    weighted: float
    overall: int
    decision: str
    reasons: list = field(default_factory=list)


def _check_weights():
    total = round(sum(WEIGHTS.values()), 6)
    assert total == 1.0, f"weights must sum to 1.0, got {total}"


def weighted_score(scores: dict) -> float:
    """scores: {dim: 0-100}. 缺失维度视为错误。"""
    missing = set(WEIGHTS) - set(scores)
    if missing:
        raise ValueError(f"missing dimensions: {sorted(missing)}")
    for d, v in scores.items():
        if d not in WEIGHTS:
            raise ValueError(f"unknown dimension: {d}")
        if not (0 <= v <= 100):
            raise ValueError(f"{d} score out of range 0-100: {v}")
    return round(sum(scores[d] * WEIGHTS[d] for d in WEIGHTS), 2)


def to_overall(weighted: float) -> int:
    return int(round(1 + weighted / 100 * 9))


def decide(scores: dict, unresolved_critical: bool = False) -> Verdict:
    """否决项与 decision mapping 取更严者。"""
    w = weighted_score(scores)
    ov = to_overall(w)
    reasons = []

    # --- 否决项 (gate) ---
    gate_cap = None  # 可达到的最宽判决
    if scores["originality"] < 45:
        gate_cap = "不通过"
        reasons.append("否决:创新性<45(套壳/无检索)->直接不通过")
    low_core = [d for d in CORE_DIMS if scores[d] < 45]
    if len(low_core) >= 2:
        gate_cap = "不通过"
        reasons.append(f"否决:核心维度两项<45 {low_core}->不通过")
    if unresolved_critical:
        # 最高只能有条件通过
        if gate_cap != "不通过":
            gate_cap = "有条件通过"
        reasons.append("否决:存在未化解CRITICAL->最高有条件通过")

    # --- decision mapping 表 ---
    if w >= 80:
        mapped = "通过"
    elif w >= 65:
        mapped = "有条件通过"
    elif w >= 50:
        mapped = "有条件通过（重大）"
    elif w >= 35:
        mapped = "不通过"
    else:
        mapped = "不通过"
    reasons.append(f"decision-mapping:Weighted={w}->{mapped}")

    # 取更严者
    rank = {"通过": 3, "有条件通过": 2, "有条件通过（重大）": 2, "不通过": 0}
    final = mapped
    if gate_cap is not None and rank[gate_cap] < rank[mapped]:
        final = gate_cap
        reasons.append(f"取更严:gate({gate_cap})覆盖mapping({mapped})")

    # 额外:通过要求无核心维度<60
    if final == "通过":
        low60 = [d for d in CORE_DIMS if scores[d] < 60]
        if low60:
            final = "有条件通过"
            reasons.append(f"降级:通过要求核心维度>=60,但{low60}<60")

    return Verdict(weighted=w, overall=ov, decision=final, reasons=reasons)


def _selftest():
    _check_weights()
    print("[1] weights sum to 1.0 ... OK")

    # 案例A: examples 的皮肤镜 idea(创新性42, 命中否决)
    derm = dict(originality=42, soundness=50, data=55, experiment=48,
                contribution=50, delta=45, feasibility=80, impact=58)
    vA = decide(derm, unresolved_critical=True)
    print(f"[A] dermoscopy Weighted={vA.weighted} Overall={vA.overall} -> {vA.decision}")
    for r in vA.reasons:
        print("      -", r)
    assert abs(vA.weighted - 51.2) < 0.5, vA.weighted
    assert vA.decision == "不通过", vA.decision  # 创新性<45压顶

    # 案例B: 强 idea, 各维高分, 应通过
    strong = dict(originality=88, soundness=85, data=82, experiment=84,
                  contribution=86, delta=80, feasibility=85, impact=82)
    vB = decide(strong)
    print(f"[B] strong     Weighted={vB.weighted} Overall={vB.overall} -> {vB.decision}")
    assert vB.weighted >= 80 and vB.decision == "通过", vB

    # 案例C: 中等 idea, 无否决, 应有条件通过
    mid = dict(originality=70, soundness=68, data=66, experiment=64,
               contribution=70, delta=62, feasibility=75, impact=65)
    vC = decide(mid)
    print(f"[C] mid        Weighted={vC.weighted} Overall={vC.overall} -> {vC.decision}")
    assert vC.decision.startswith("有条件通过"), vC

    # 案例D: 高 Weighted 但有未化解 CRITICAL -> 降到有条件通过
    vD = decide(strong, unresolved_critical=True)
    print(f"[D] strong+CRIT Weighted={vD.weighted} -> {vD.decision}")
    assert vD.decision == "有条件通过", vD

    # 案例E: 范围/缺维校验
    try:
        weighted_score({"originality": 50})
        raise AssertionError("should have raised on missing dims")
    except ValueError:
        print("[E] missing-dimension guard ... OK")
    try:
        weighted_score({**strong, "originality": 120})
        raise AssertionError("should have raised on out-of-range")
    except ValueError:
        print("[F] out-of-range guard ... OK")

    print("\nALL SELFTESTS PASSED")


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    _selftest()
