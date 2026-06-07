#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""calibration.py — 可选 calibration mode。

喂入一批"已知结局"的 idea(真实被顶会接收=正例 / 被拒或撤回=负例),
用本技能的判决(通过=预测正 / 不通过=预测负)算混淆矩阵与:
  - FNR (假阴率): 实际该接收却被判不通过的比例 -> 评审过严, 漏放好 idea
  - FPR (假阳率): 实际被拒却被判通过的比例 -> 评审过松, 谄媚放行坏 idea
  - precision/recall/accuracy

用于校准本技能的严格度。借 academic-paper-reviewer 的 calibration 模式。
"有条件通过"按保守计为"不通过"(未放行 m05)。
无外部依赖, 自带合成数据自测。
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class CalibItem:
    idea_id: str
    actual_accept: bool      # 已知结局: True=真实被接收
    decision: str            # 本技能判决文本


def _predicted_positive(decision: str) -> bool:
    # 仅"通过"算放行(预测正); 有条件/不通过都未放行 m05
    return decision.strip() == "通过"


def confusion(items: list) -> dict:
    tp = fp = tn = fn = 0
    for it in items:
        pred = _predicted_positive(it.decision)
        if it.actual_accept and pred:
            tp += 1
        elif it.actual_accept and not pred:
            fn += 1
        elif (not it.actual_accept) and pred:
            fp += 1
        else:
            tn += 1
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn}


def metrics(items: list) -> dict:
    c = confusion(items)
    tp, fp, tn, fn = c["tp"], c["fp"], c["tn"], c["fn"]
    n = len(items)

    def safe(a, b):
        return round(a / b, 3) if b else None

    return {
        **c,
        "n": n,
        "FNR": safe(fn, fn + tp),   # 漏放好idea
        "FPR": safe(fp, fp + tn),   # 放行坏idea
        "precision": safe(tp, tp + fp),
        "recall": safe(tp, tp + fn),
        "accuracy": safe(tp + tn, n),
    }


def interpret(m: dict) -> str:
    msgs = []
    if m["FNR"] is not None and m["FNR"] > 0.4:
        msgs.append(f"FNR={m['FNR']} 偏高: 评审过严, 在漏放好idea, 检查否决项是否过激")
    if m["FPR"] is not None and m["FPR"] > 0.3:
        msgs.append(f"FPR={m['FPR']} 偏高: 评审过松/谄媚, 在放行坏idea, 收紧通过线与反谄媚")
    if not msgs:
        msgs.append("FNR/FPR 在可接受范围, 严格度大致校准")
    return " | ".join(msgs)


def _selftest():
    # 合成 8 个已知结局 idea
    items = [
        CalibItem("a1", True, "通过"),            # TP
        CalibItem("a2", True, "通过"),            # TP
        CalibItem("a3", True, "有条件通过"),       # FN (好idea被卡)
        CalibItem("a4", True, "不通过"),           # FN
        CalibItem("b1", False, "不通过"),          # TN
        CalibItem("b2", False, "有条件通过（重大）"),  # TN
        CalibItem("b3", False, "不通过"),          # TN
        CalibItem("b4", False, "通过"),            # FP (坏idea放行)
    ]
    m = metrics(items)
    print("confusion:", {k: m[k] for k in ("tp", "fp", "tn", "fn")})
    print("FNR:", m["FNR"], "FPR:", m["FPR"],
          "precision:", m["precision"], "recall:", m["recall"],
          "accuracy:", m["accuracy"])
    print("interpret:", interpret(m))
    assert m["tp"] == 2 and m["fn"] == 2 and m["tn"] == 3 and m["fp"] == 1
    assert m["FNR"] == round(2 / 4, 3)   # 0.5
    assert m["FPR"] == round(1 / 4, 3)   # 0.25
    assert m["precision"] == round(2 / 3, 3)

    # 空输入不崩
    m0 = metrics([])
    assert m0["FNR"] is None and m0["n"] == 0
    print("\nALL SELFTESTS PASSED")


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    _selftest()
