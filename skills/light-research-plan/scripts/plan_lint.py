#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plan_lint.py — 实验矩阵四要素齐全性检查 (Light / light-research-plan)

检查实验矩阵 Markdown 表每个实验行是否齐备四要素，缺一即提示：
  1. 假设      ← "对应假设" 列非空且形如 H1/H2…
  2. 变量      ← "数据集" 与 "baseline" 列均非空（自变量/控制变量的最小落地）
  3. 指标      ← "指标" 列非空
  4. 停止条件  ← "完成判定" 列非空（用什么结果回答该假设、达到判定门槛）

对应 EXP-Bench 四要素与 SKILL「实验设计」纪律：设计与结论最易跑偏。
纯离线、只读、不产文件；--selftest 用内置样例自测。

用法：
    python scripts/plan_lint.py --file experiments/experiment_matrix.md
    python scripts/plan_lint.py --selftest
退出码：0 全齐 / 1 有缺项或无法解析（可接 CI）。
"""
from __future__ import annotations
import argparse
import re
import sys

# 列名 → 要素的别名映射（容忍模板措辞差异）
COL_ALIASES = {
    "hypothesis": ("对应假设", "假设"),
    "dataset": ("数据集", "data", "数据"),
    "baseline": ("baseline", "基线", "对照"),
    "metric": ("指标", "metric", "评价指标"),
    "stop": ("完成判定", "停止条件", "判定", "成功标准"),
}
# 占位符（模板未填）视为缺项
PLACEHOLDER_RE = re.compile(r"^\s*(\{\{.*\}\}|[-—–]|n/?a|tbd|待定|待填|\.\.\.|…)?\s*$", re.I)
# 实验行 ID 形态：EXP-01 / ABL-02 / SEN-01 / GEN/ROB 等
EXP_ID_RE = re.compile(r"^[A-Z]{2,4}-?\d+$")
HYP_RE = re.compile(r"\bH\d+\b")


def _is_blank(cell: str) -> bool:
    return bool(PLACEHOLDER_RE.match(cell or ""))


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def parse_tables(text: str) -> list[list[list[str]]]:
    """把 Markdown 里所有管线表解析为 [表][行][单元格]。"""
    tables, cur = [], []
    for line in text.splitlines():
        if line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            cur.append(cells)
        else:
            if cur:
                tables.append(cur)
                cur = []
    if cur:
        tables.append(cur)
    return tables


def _is_separator(row: list[str]) -> bool:
    return all(re.fullmatch(r":?-{2,}:?", c.strip() or "") for c in row if c.strip() != "") \
        and any("-" in c for c in row)


def find_experiment_table(tables: list[list[list[str]]]) -> tuple[list[str], list[list[str]]] | None:
    """找含"对应假设/假设"列且有实验 ID 行的表，返回 (表头, 数据行)。"""
    for tbl in tables:
        if len(tbl) < 2:
            continue
        header = tbl[0]
        norm_header = [_norm(h) for h in header]
        has_hyp = any(any(a in nh for a in (_norm(x) for x in COL_ALIASES["hypothesis"]))
                      for nh in norm_header)
        if not has_hyp:
            continue
        rows = [r for r in tbl[1:] if not _is_separator(r)]
        # 至少一行首列像实验 ID
        if any(EXP_ID_RE.match((r[0] or "").strip()) for r in rows if r):
            return header, rows
    return None


def _col_index(header: list[str], element: str) -> int | None:
    for i, h in enumerate(header):
        nh = _norm(h)
        if any(_norm(alias) in nh for alias in COL_ALIASES[element]):
            return i
    return None


def lint(text: str) -> dict:
    tables = parse_tables(text)
    found = find_experiment_table(tables)
    if not found:
        return {"ok": False, "error": "未找到实验矩阵表（需含「对应假设」列且有 EXP-/ABL- 等实验行）"}
    header, rows = found
    idx = {el: _col_index(header, el) for el in COL_ALIASES}
    missing_cols = [el for el, i in idx.items() if i is None]
    findings = []
    checked = 0
    for r in rows:
        if not r or not EXP_ID_RE.match((r[0] or "").strip()):
            continue
        checked += 1
        exp_id = r[0].strip()
        gaps = []
        # 假设
        i = idx["hypothesis"]
        if i is None or i >= len(r) or _is_blank(r[i]) or not HYP_RE.search(r[i]):
            gaps.append("假设(对应假设列空或非 H#)")
        # 变量：数据集 + baseline 都要有
        for el, label in (("dataset", "数据集"), ("baseline", "baseline")):
            j = idx[el]
            if j is None or j >= len(r) or _is_blank(r[j]):
                gaps.append(f"变量({label}空)")
        # 指标
        k = idx["metric"]
        if k is None or k >= len(r) or _is_blank(r[k]):
            gaps.append("指标(空)")
        # 停止条件
        m = idx["stop"]
        if m is None or m >= len(r) or _is_blank(r[m]):
            gaps.append("停止条件(完成判定空)")
        if gaps:
            findings.append({"exp_id": exp_id, "gaps": gaps})
    return {"ok": len(findings) == 0 and not missing_cols,
            "checked_rows": checked, "missing_columns": missing_cols,
            "findings": findings}


def _print_report(rep: dict) -> None:
    if rep.get("error"):
        print(f"[plan_lint] 解析失败: {rep['error']}")
        return
    print(f"[plan_lint] 检查 {rep['checked_rows']} 个实验行")
    if rep["missing_columns"]:
        print(f"  ⚠ 表头缺列: {', '.join(rep['missing_columns'])}（无法核对对应要素）")
    if rep["findings"]:
        for f in rep["findings"]:
            print(f"  ✗ {f['exp_id']}: 缺 {', '.join(f['gaps'])}")
    else:
        print("  ✓ 所有实验行四要素齐全（假设/变量/指标/停止条件）")


def _selftest() -> int:
    good = """
# 实验矩阵

| 实验ID | 对应假设 | 数据集(db04) | baseline(db03) | 指标 | 随机种子 | 状态 | 完成判定 |
|--------|----------|--------------|----------------|------|----------|------|----------|
| EXP-01 | H1 | ImageNet | ResNet50 | top-1 | 0,1,2 | 未开始 | top-1 > baseline 且 p<0.05 |
"""
    rep = lint(good)
    assert rep["ok"], rep
    assert rep["checked_rows"] == 1 and not rep["findings"], rep

    bad = """
| 实验ID | 对应假设 | 数据集(db04) | baseline(db03) | 指标 | 状态 | 完成判定 |
|--------|----------|--------------|----------------|------|------|----------|
| EXP-01 | H1 | ImageNet | ResNet50 | top-1 | 未开始 | top-1 > baseline 且 p<0.05 |
| EXP-02 | {{假设}} | {{数据集}} | ResNet50 | top-1 | 未开始 | {{判定门槛}} |
| ABL-01 | H2 | CIFAR | 移除X | acc | 未开始 | — |
"""
    rep2 = lint(bad)
    assert not rep2["ok"], rep2
    assert rep2["checked_rows"] == 3, rep2
    ids = {f["exp_id"] for f in rep2["findings"]}
    assert ids == {"EXP-02", "ABL-01"}, rep2
    exp02 = next(f for f in rep2["findings"] if f["exp_id"] == "EXP-02")
    assert any("假设" in g for g in exp02["gaps"]), exp02
    assert any("数据集" in g for g in exp02["gaps"]), exp02
    assert any("停止条件" in g for g in exp02["gaps"]), exp02
    abl = next(f for f in rep2["findings"] if f["exp_id"] == "ABL-01")
    assert any("停止条件" in g for g in abl["gaps"]), abl

    # 无实验表 → 报错而非崩
    rep3 = lint("# 没有表格\n普通文字。")
    assert not rep3["ok"] and rep3.get("error"), rep3
    print("[selftest] PASS plan_lint（齐全/缺项/无表三路径）")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="实验矩阵四要素齐全性检查")
    ap.add_argument("--file", help="实验矩阵 Markdown 路径")
    ap.add_argument("--selftest", action="store_true", help="离线样例自测")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(_selftest())
    if not args.file:
        ap.error("需 --file <实验矩阵.md> 或 --selftest")
    with open(args.file, encoding="utf-8") as f:
        rep = lint(f.read())
    _print_report(rep)
    sys.exit(0 if rep["ok"] else 1)


if __name__ == "__main__":
    main()
