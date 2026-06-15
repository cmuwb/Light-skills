#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_commitments.py — rebuttal 承诺账本核验（把手填 COMMITMENT_GAP 变成退出码契约）。

为什么有这个脚本（补 m14 最大的名实差距）
----------------------------------------
SKILL/模板用**脚本化口吻**承诺一堆强制门——"报 COMMITMENT_GAP""禁连续让步""已改可核须真能
指到位置"——但实际全是**手填 markdown 勾选，零自动化**（响应矩阵的"闭环自检"是 checkbox）。
对比 Review2Rebuttal 真有 author-approvals.json 工件级门禁。本脚本把响应矩阵从"看似有引擎实为
清单"变成真退出码契约：解析 response_matrix.md 表，机械核验每条承诺，拦住"空口已改"。

四类核验（critical→退出码 1）
----------------------------
  COMMITMENT_GAP（critical）：承诺"已改可核/已兑现"但"改动位置"列无具体定位锚（§/Table/Fig/表/图/
                  节/Section/L行号）——空口已改，裸模型高发幻觉。带 --evidence-map 时还核工件路径是否存在。
  PLANNED_AS_DONE（major）：承诺状态标"已兑现"但回应/改动含未来词（将/拟/计划/planned/待补）——自相矛盾。
  CONCESSION_NO_EVIDENCE（major）：concession≥4（撤回/降级）但回应+改动里无新证据/新实验标记——空口让步（反谄媚）。
  CONSECUTIVE_CONCESSION（major）：相邻两条都 concession≥4 且第二条无独立证据——连续让步（谄媚信号）。
  MAJOR_UNADDRESSED（critical）：severity=major 但回应与改动位置都为空——major 意见漏处理。

⚠ 诚实边界：解析 markdown 表 + 正则启发式，核的是"账本是否自洽、承诺是否有定位锚"，**不替你判
  改动本身对不对**；--evidence-map 才核工件存在性。不替代人读修订稿确认真改了。

用法：
  python check_commitments.py --matrix response_matrix.md
  python check_commitments.py --matrix response_matrix.md --evidence-map ev.json --json
  python check_commitments.py --selftest
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "_shared"))
try:
    from findings_schema import Finding, GateResult, FindingsReport  # noqa: E402
    _HAS_FINDINGS = True
except Exception:
    _HAS_FINDINGS = False

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# 具体定位锚：改动位置须指到哪一节/图/表/行
_LOCATOR = re.compile(r"§|\bSec(?:tion|\.)?\s*\d|Table\s*\d|Fig(?:ure|\.)?\s*\d|Eq\.?\s*\d|"
                      r"表\s*\d|图\s*\d|第.{1,3}节|附录|Appendix|\bL\d+|行\s*\d|公式\s*\d", re.I)
# 已兑现标记
_DONE = re.compile(r"已兑现|已改|已完成|done|✅|已补", re.I)
# 未来/计划词
_PLANNED = re.compile(r"将|拟|计划|planned|待补|待做|后续|TODO|尚未", re.I)
# 新证据/新实验标记（让步须挂这些）
_EVIDENCE = re.compile(r"新增|新表|新 ?Fig|新实验|补(?:充|了|做)|见(?:新|表|图|§)|实验|p\s*[<=]\s*0?\.\d|"
                       r"证据|Table\s*\d|Fig\w*\s*\d|表\s*\d|图\s*\d|§|附录", re.I)
# "已改可核"判定标记
_VERIFIABLE = re.compile(r"已改可核|已改.*核|verifiable", re.I)


def _split_row(line: str) -> list:
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return cells


def parse_matrix(text: str) -> list:
    """解析 response_matrix.md 的意见台账表，返回行 dict 列表。"""
    lines = text.splitlines()
    header_idx = None
    cols = []
    for i, ln in enumerate(lines):
        if "|" in ln and "concession" in ln.lower() and ("改动" in ln or "改动位置" in ln):
            cols = [c.lower() for c in _split_row(ln)]
            header_idx = i
            break
    if header_idx is None:
        return []

    def col_of(*keys):
        for j, c in enumerate(cols):
            if any(k in c for k in keys):
                return j
        return None

    idx = {
        "id": col_of("id"), "sev": col_of("严重度", "severity"),
        "conc": col_of("concession"), "resp": col_of("回应"),
        "loc": col_of("改动位置", "改动"), "rerev": col_of("re-review", "判定"),
        "status": col_of("承诺状态", "承诺"),
    }
    rows = []
    for ln in lines[header_idx + 1:]:
        if "|" not in ln:
            if ln.strip() and not ln.strip().startswith("#"):
                continue
            if ln.strip().startswith("#"):
                break
            continue
        cells = _split_row(ln)
        if not cells or set(cells[0]) <= set("-: "):   # 分隔行 |---|---|
            continue
        if cells[0].lower() in ("id", "") or len(cells) < 3:
            continue

        def get(key):
            j = idx.get(key)
            return cells[j] if (j is not None and j < len(cells)) else ""
        conc_raw = get("conc")
        m = re.search(r"\d", conc_raw)
        rows.append({
            "id": get("id"), "severity": get("sev"), "concession": int(m.group()) if m else None,
            "response": get("resp"), "location": get("loc"),
            "rereview": get("rerev"), "status": get("status"),
        })
    return rows


def check(rows: list, evidence_map: dict | None = None) -> dict:
    issues = []
    prev_concede = False
    for r in rows:
        rid = r["id"] or "?"
        loc = r["location"]
        resp = r["response"]
        claims_done = bool(_VERIFIABLE.search(r["rereview"]) or _DONE.search(r["status"]))
        has_locator = bool(_LOCATOR.search(loc))

        # 1. COMMITMENT_GAP：承诺已改可核但无定位锚
        if claims_done and not has_locator:
            issues.append({"id": rid, "code": "COMMITMENT_GAP", "severity": "critical",
                           "msg": f"{rid} 承诺『已改可核/已兑现』但改动位置无具体定位锚（§/Table/Fig/节/行）"
                                  f"：「{loc or '空'}」——空口已改，须指到修订稿具体位置。"})
        # 1b. evidence_map 工件核验
        if claims_done and evidence_map is not None:
            path = evidence_map.get(rid)
            if not path or not os.path.exists(path):
                issues.append({"id": rid, "code": "COMMITMENT_GAP", "severity": "critical",
                               "msg": f"{rid} 承诺已改但 evidence_map 无可达工件（path={path!r}）——"
                                      f"工件级核验失败，主张降级为 planned 待签。"})
        # 2. PLANNED_AS_DONE：标已兑现却含未来词
        if _DONE.search(r["status"]) and _PLANNED.search(resp + " " + loc):
            issues.append({"id": rid, "code": "PLANNED_AS_DONE", "severity": "major",
                           "msg": f"{rid} 承诺状态标已兑现，但回应/改动含未来词（将/拟/计划/待补）——"
                                  f"自相矛盾，未做就别标已兑现，改 planned。"})
        # 3. CONCESSION_NO_EVIDENCE：让步≥4 无新证据
        concede = r["concession"] is not None and r["concession"] >= 4
        if concede and not _EVIDENCE.search(resp + " " + loc):
            issues.append({"id": rid, "code": "CONCESSION_NO_EVIDENCE", "severity": "major",
                           "msg": f"{rid} concession={r['concession']}(撤回/降级) 但回应无新证据/新实验标记"
                                  f"——空口让步（反谄媚：让步必须挂新证据）。"})
        # 4. CONSECUTIVE_CONCESSION：相邻两条都≥4 且第二条无独立证据
        if concede and prev_concede and not _EVIDENCE.search(resp + " " + loc):
            issues.append({"id": rid, "code": "CONSECUTIVE_CONCESSION", "severity": "major",
                           "msg": f"{rid} 与上一条连续让步（相邻 concession≥4）且无独立证据"
                                  f"——谄媚信号，第二条须独立证明否则降为 ≤3。"})
        prev_concede = concede
        # 5. MAJOR_UNADDRESSED：major 但回应与改动都空
        if "major" in r["severity"].lower() and not resp.strip() and not loc.strip():
            issues.append({"id": rid, "code": "MAJOR_UNADDRESSED", "severity": "critical",
                           "msg": f"{rid} severity=major 但回应与改动位置都为空——major 意见漏处理，必逐条回。"})

    by = {"critical": 0, "major": 0, "minor": 0}
    for i in issues:
        by[i["severity"]] = by.get(i["severity"], 0) + 1
    return {"n_rows": len(rows), "n_issues": len(issues), "by_severity": by, "issues": issues}


def to_findings(rep: dict) -> dict:
    if not _HAS_FINDINGS:
        gates = [{"gate": i["code"], "status": "fail", "severity": i["severity"],
                  "findings": [{"loc": i["id"], "issue": i["msg"], "fix": "", "rule": i["code"]}]}
                 for i in rep["issues"]]
        verdict = "fail" if rep["by_severity"].get("critical") else ("warn" if rep["issues"] else "pass")
        return {"schema": "light.findings.v1", "producer": "m14", "target": "response_matrix.md",
                "verdict": verdict, "gates": gates, "summary": f"承诺核验:{rep['n_issues']}问题",
                "fresh_evidence": True, "_degraded": True}
    r = FindingsReport(producer="m14", target="response_matrix.md", fresh_evidence=True,
                       summary=f"rebuttal 承诺账本核验：{rep['n_rows']}行/{rep['n_issues']}问题")
    if not rep["issues"]:
        r.gates.append(GateResult("commitment_ledger", "pass", "info"))
    for i in rep["issues"]:
        r.gates.append(GateResult(i["code"], "fail", i["severity"],
                                  [Finding(i["id"], i["msg"], rule=i["code"])]))
    return r.finalize().to_dict()


def to_markdown(rep: dict) -> str:
    b = rep["by_severity"]
    lines = [f"# rebuttal 承诺账本核验 — {rep['n_rows']} 行，{rep['n_issues']} 问题"
             f"（critical={b.get('critical',0)} major={b.get('major',0)}）\n"]
    if not rep["issues"]:
        lines.append("✓ 承诺账本自洽：已改可核均有定位锚、让步均挂证据、major 无漏。")
    for i in rep["issues"]:
        lines.append(f"- [{i['severity']}] {i['code']} @ {i['id']}：{i['msg']}")
    lines.append("\n> 解析表+正则启发式，核账本自洽性，不替你判改动对错；--evidence-map 才核工件存在。")
    return "\n".join(lines)


def _selftest() -> int:
    print("### check_commitments 离线自测", file=sys.stderr)
    matrix = """
# 回应矩阵
| ID | 审稿人 | 意见原文(摘) | 分类 | 严重度 | concession(1-5) | 我方回应(摘) | 改动位置(节/图/行) | re-review 判定 | 承诺状态 |
|---|---|---|---|---|---|---|---|---|---|
| R1-1 | R1 | baseline 弱 | 实验 | major | 3 | 补 X 对比 见新表3 | §4.2 Table 3 新增行 | 已改可核 | ✅已兑现 |
| R1-2 | R1 | novelty 不清 | 创新性 | major | 4 | 承认不清,重写差异段 | 改了相关部分 | 已改可核 | ✅已兑现 |
| R2-1 | R2 | 加局限讨论 | 写作 | minor | 5 | 接受,新增局限讨论段 | §6 新增局限段 | 已改可核 | ✅已兑现 |
| R2-2 | R2 | 为何不比 Z | 实验 | major | 2 | Z 不可比,说明 | 回应信脚注 | 仅回应不改稿 | ⏳待确认 |
| R3-1 | R3 | 统计显著? | soundness | major | 4 | 同意,将补显著性检验 | 待补 | 已改可核 | ✅已兑现 |
| R3-2 | R3 | 写作建议 | 写作 | major | | | | | |
"""
    rows = parse_matrix(matrix)
    assert len(rows) == 6, [r["id"] for r in rows]
    rep = check(rows)
    print(to_markdown(rep), file=sys.stderr)
    by_id = {}
    for i in rep["issues"]:
        by_id.setdefault(i["id"], set()).add(i["code"])
    # R1-1 干净（有定位锚+证据）→ 无问题
    assert "R1-1" not in by_id, by_id
    # R1-2 已改可核但"改了相关部分"无定位锚 → COMMITMENT_GAP；concession4 但有"重写差异段"算证据? 无 _EVIDENCE 命中→也 CONCESSION_NO_EVIDENCE
    assert "COMMITMENT_GAP" in by_id.get("R1-2", set()), by_id
    # R2-1 minor concession5 "新增局限段" 有证据+定位锚 → 干净
    assert "R2-1" not in by_id, by_id
    # R3-1 已兑现却"将补/待补" → PLANNED_AS_DONE + COMMITMENT_GAP(无定位锚)
    assert "PLANNED_AS_DONE" in by_id.get("R3-1", set()), by_id
    # R3-2 major 但回应/改动空 → MAJOR_UNADDRESSED
    assert "MAJOR_UNADDRESSED" in by_id.get("R3-2", set()), by_id
    print("[1] COMMITMENT_GAP/PLANNED_AS_DONE/MAJOR_UNADDRESSED 命中,干净行不误报 ... OK", file=sys.stderr)

    # 退出码：有 critical → findings verdict=fail
    f = to_findings(rep)
    assert f["schema"] == "light.findings.v1" and f["verdict"] == "fail", f
    print("[2] findings verdict=fail ... OK", file=sys.stderr)

    # 连续让步检测：两条相邻 concession≥4 且第二条无证据
    m2 = """
| ID | 严重度 | concession(1-5) | 我方回应 | 改动位置 | re-review 判定 | 承诺状态 |
|---|---|---|---|---|---|---|
| A | minor | 4 | 接受意见 见新表2 | Table 2 | 已改可核 | ✅已兑现 |
| B | minor | 5 | 也接受,无新料 | 无 | 仅回应不改稿 | ⏳ |
"""
    r2 = check(parse_matrix(m2))
    codes2 = {i["code"] for i in r2["issues"] if i["id"] == "B"}
    assert "CONSECUTIVE_CONCESSION" in codes2 and "CONCESSION_NO_EVIDENCE" in codes2, r2["issues"]
    print("[3] 连续让步 + 空口让步检测 ... OK", file=sys.stderr)

    # evidence_map 工件核验
    m3 = """
| ID | 严重度 | concession(1-5) | 我方回应 | 改动位置 | re-review 判定 | 承诺状态 |
|---|---|---|---|---|---|---|
| C | major | 3 | 补实验 | §5 Table 4 | 已改可核 | ✅已兑现 |
"""
    rc = check(parse_matrix(m3), evidence_map={"C": "/no/such/file.png"})
    assert any(i["code"] == "COMMITMENT_GAP" and "工件" in i["msg"] for i in rc["issues"]), rc["issues"]
    print("[4] evidence_map 工件不存在 → COMMITMENT_GAP ... OK", file=sys.stderr)

    # 全干净矩阵 → 零问题
    clean = """
| ID | 严重度 | concession(1-5) | 我方回应 | 改动位置 | re-review 判定 | 承诺状态 |
|---|---|---|---|---|---|---|
| X | major | 3 | 补对比 见新表 | §4 Table 3 | 已改可核 | ✅已兑现 |
| Y | minor | 2 | 礼貌反驳 | 回应信 | 仅回应不改稿 | ⏳ |
"""
    rcl = check(parse_matrix(clean))
    assert rcl["n_issues"] == 0, rcl["issues"]
    print("[5] 干净矩阵零问题 ... OK", file=sys.stderr)

    print("[selftest] PASS check_commitments offline")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="rebuttal 承诺账本核验（COMMITMENT_GAP 退出码契约）")
    ap.add_argument("--matrix", help="response_matrix.md 路径")
    ap.add_argument("--evidence-map", help="JSON {意见ID: 工件路径}，核工件存在性")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest or not args.matrix:
        return _selftest()
    with open(args.matrix, encoding="utf-8") as f:
        rows = parse_matrix(f.read())
    ev = None
    if args.evidence_map:
        with open(args.evidence_map, encoding="utf-8") as f:
            ev = json.load(f)
    rep = check(rows, evidence_map=ev)
    print(json.dumps(to_findings(rep), ensure_ascii=False, indent=2) if args.json else to_markdown(rep))
    return 1 if rep["by_severity"].get("critical") else 0


if __name__ == "__main__":
    sys.exit(main())
