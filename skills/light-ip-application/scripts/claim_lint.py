#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""claim_lint.py — 权利要求书一致性 linter（规则版，对标 Patent Bots 核心 + arxiv 2510.25402）。

为什么有这个脚本（补 m15 最大段位差）
--------------------------------------
SKILL/模板反复强调"每个权利要求特征都要在说明书找到支持""术语前后一致""从属项不引用更大
编号""单部分/两部分法别混用"——但此前**全仓库没有任何脚本校验这些**，全靠人工，是"宣称为
工作流要点、实则纯手工"的空头支票。Patent Bots 十年规则版产品的核心正是三类错误自动检测：
**numbering（编号/引用方向）、antecedent basis（在先基础）、word-support（说明书支持）**。
本脚本把这些落成纯 Python 规则检查（无需联网/LLM），让 m15 从"只会起草"升级到"起草+自检闭环"。

五类检查
--------
  1. 从属项引用方向（numbering）：不得引用编号 ≥ 自身的项；引用多项须用"或"（不得用"和/、"）
  2. antecedent basis：出现"所述/该/上述 X"但 X 在前文从未以"一种/一个 X"等首次引入 → 缺在先基础
  3. word-support：权利要求里的特征术语未在说明书正文出现 → 缺说明书支持（需传 --spec）
  4. 单部分/两部分法混用：单部分法的"包括以下步骤"骨架里出现"其特征在于" → 代理师直接打回
  5. 图-标记一致性（需 --spec）：说明书引用的附图标记号在"附图标记清单"里无定义 → 悬空标记

⚠ 诚实边界：纯正则规则，抓"形式层面的硬错"，**不替代专利代理师对实质内容的审核**；术语抽取
  是启发式，可能漏报/误报（如生造长术语切分）。每条报告结尾仍标"须代理师定稿"。阈值无；规则化判定。

用法：
  python claim_lint.py --claims ip/claims_draft.md [--spec ip/specification_draft.md]
  python claim_lint.py --claims ip/claims_draft.md --json     # 输出 light.findings.v1
  python claim_lint.py --selftest                              # 离线合成样本自测
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

_REF_MARKERS = ("所述", "该", "上述")
# 名词块：中文/字母/数字连续串（用于抽术语）
_NOUN = r"[一-龥A-Za-z0-9]+"


def parse_claims(text: str) -> list:
    """把权利要求文本拆成 [{"num":int, "body":str}]。

    识别行首"N." / "N、"（含代码块内）。一条权利要求从其编号行到下一编号行（或文末）。
    """
    # 去掉 markdown 代码围栏标记行，但保留内容
    lines = [ln for ln in text.splitlines() if not ln.strip().startswith("```")]
    claims = []
    cur = None
    head = re.compile(r"^\s*(\d+)\s*[\.、]\s*(.*)$")
    for ln in lines:
        m = head.match(ln)
        # 仅当像权利要求开头（含"一种"/"根据权利要求"/"其特征在于"等专利措辞）才作为新条目，
        # 避免把说明书里的普通编号列表误当权利要求。
        if m and re.search(r"一种|根据权利要求|其特征在于|计算机可读|电子设备", ln):
            if cur:
                claims.append(cur)
            cur = {"num": int(m.group(1)), "body": m.group(2).strip()}
        elif cur is not None:
            cur["body"] += "\n" + ln.strip()
    if cur:
        claims.append(cur)
    return claims


# 名词块截断点：动词/连词/助词/另一引用标记——中文无词边界，贪婪名词块须在此切断
_VERB_CUT = re.compile(
    r"所述|该|上述|的|包括|采用|进行|用于|运行|实现|执行|获取|提取|构建|生成|输出|包含|具有|"
    r"设置|连接|采集|计算|确定|根据|做|是|对|将|把|被|做校准")
_LOCALIZER = "上中下内外前后左右间的"


def _clean_term(raw: str) -> str:
    """把贪婪名词块裁成实际术语：去前导'的'、在首个动词/标记处切断、去尾部方位词。"""
    raw = raw.lstrip("的")
    m = _VERB_CUT.search(raw)
    if m:
        raw = raw[:m.start()]
    return raw.rstrip(_LOCALIZER)


def _extract_ref_terms(body: str):
    """抽出"所述/该/上述 X"里的术语 X 及其在 body 中的起始位置 [(term, pos), ...]。"""
    out = []
    # 名词块不得跨越下一个引用标记（否则贪婪捕获会吞掉后一个"所述X"导致漏抽）
    pat = re.compile(r"(所述|该|上述)\s*((?:(?!所述|该|上述)[一-龥A-Za-z0-9])+)")
    for m in pat.finditer(body):
        term = _clean_term(m.group(2))
        if term:
            out.append((term, m.start(2)))
    return out


def _introduced_before(term: str, pretext: str) -> bool:
    """term 是否在 pretext 中以"非所述/该/上述"形式（首次引入）出现过。"""
    idx = 0
    while True:
        p = pretext.find(term, idx)
        if p < 0:
            return False
        prefix = pretext[max(0, p - 3):p]
        if not any(prefix.endswith(mk) for mk in _REF_MARKERS):
            return True   # 找到一个非引用式的首次出现
        idx = p + 1


def check_antecedent_basis(claims: list) -> list:
    """检查 antecedent basis：所述 X 前须有 X 的首次引入（全文累积，跨权利要求）。"""
    issues = []
    cumulative = ""   # 到目前为止扫过的全部权利要求文本（在先引入可跨项）
    for c in claims:
        body = c["body"]
        for term, pos in _extract_ref_terms(body):
            # 在先文本 = 此前所有权利要求 + 本条 body 中该位置之前的部分
            pretext = cumulative + body[:pos]
            if not _introduced_before(term, pretext):
                issues.append({
                    "loc": f"权利要求{c['num']}",
                    "code": "ANTECEDENT-BASIS",
                    "severity": "major",
                    "msg": f"权利要求{c['num']}出现「所述/该{term}」但前文未先以「一种/一个{term}」等"
                           f"首次引入——缺在先基础(antecedent basis)，会被审查员指缺乏引用基础。"})
        cumulative += body + "\n"
    return issues


def check_numbering(claims: list) -> list:
    """从属项引用方向 + 多项引用须用"或"。"""
    issues = []
    nums = {c["num"] for c in claims}
    for c in claims:
        body = c["body"]
        # 找"根据权利要求 ... 所述"里的被引编号串
        for m in re.finditer(r"根据权利要求\s*([0-9、，,和或至\s]+?)\s*(?:所述|中任一项|任一项)", body):
            span = m.group(1)
            refed = [int(x) for x in re.findall(r"\d+", span)]
            # 引用方向：不得引用编号 >= 自身
            bad = [r for r in refed if r >= c["num"]]
            if bad:
                issues.append({
                    "loc": f"权利要求{c['num']}", "code": "NUMBERING-DIRECTION",
                    "severity": "major",
                    "msg": f"权利要求{c['num']}引用了编号≥自身的项 {bad}——从属项不得引用编号更大或自身的项。"})
            # 引用不存在的项
            missing = [r for r in refed if r not in nums]
            if missing:
                issues.append({
                    "loc": f"权利要求{c['num']}", "code": "NUMBERING-NONEXIST",
                    "severity": "major",
                    "msg": f"权利要求{c['num']}引用了不存在的权利要求 {missing}。"})
            # 多项引用须用"或"，不得用"和/、/,"（"至...任一项"的范围式除外）
            is_range = bool(re.search(r"至\s*\d+\s*(?:中)?任一项", body))
            if len(refed) >= 2 and not is_range and ("和" in span or "、" in span or "," in span or "，" in span):
                issues.append({
                    "loc": f"权利要求{c['num']}", "code": "MULTI-REF-NOT-OR",
                    "severity": "minor",
                    "msg": f"权利要求{c['num']}引用多项 {refed} 但用了「和/、」——规范要求多项引用用「或」"
                           f"（如「根据权利要求1或2所述」）。"})
    return issues


def check_part_mixing(claims: list) -> list:
    """单部分/两部分法混用：单部分骨架"包括以下步骤"里出现"其特征在于"=致命错误。"""
    issues = []
    for c in claims:
        body = c["body"]
        is_independent = bool(re.search(r"一种", body)) and not body.lstrip().startswith("根据权利要求") \
            and "根据权利要求" not in body[:12]
        if not is_independent:
            continue
        is_method = bool(re.search(r"方法", body[:30]))
        single_skeleton = bool(re.search(r"包括以下步骤|包括以下", body))
        has_char_clause = "其特征在于" in body
        # 写法A(单部分,"包括以下步骤")明确"不写其特征在于"，混入即打回
        if is_method and single_skeleton and has_char_clause:
            issues.append({
                "loc": f"权利要求{c['num']}", "code": "PART-METHOD-MIXING",
                "severity": "major",
                "msg": f"权利要求{c['num']}（独立方法权项）同时用了单部分法「包括以下步骤」骨架与"
                       f"「其特征在于」——单部分法不应写「其特征在于」，两部分法不写「包括以下步骤」式全列。"
                       f"二选一别混用，否则代理师直接打回（共有特征塞进特征部分=最常见致命错误）。"})
    return issues


def _spec_markers(spec: str):
    """从说明书'附图标记清单'抽已定义标记号集合（形如 1-机架 / 1：机架 / 1. 机架）。"""
    defined = set()
    # 抓"附图标记"段后面的"数字-中文"对
    for m in re.finditer(r"(\d+)\s*[-—:：．\.、]\s*[一-龥]", spec):
        defined.add(int(m.group(1)))
    return defined


def check_word_support(claims: list, spec: str) -> list:
    """word-support：权利要求的"所述 X"特征术语未在说明书正文出现 → 缺支持。"""
    issues = []
    seen = set()
    for c in claims:
        for term, _ in _extract_ref_terms(c["body"]):
            if term in seen or len(term) < 2:
                continue
            seen.add(term)
            # 纯字母数字短标号（S1/S2）不算实质术语，跳过
            if re.fullmatch(r"[A-Za-z]?\d+", term):
                continue
            if term not in spec:
                issues.append({
                    "loc": f"权利要求(术语:{term})", "code": "WORD-SUPPORT",
                    "severity": "major",
                    "msg": f"权利要求术语「{term}」未在说明书正文出现——缺说明书支持(word-support)，"
                           f"权利要求须以说明书为依据，否则会被指得不到说明书支持而驳回。"})
    return issues


def check_figure_markers(claims: list, spec: str) -> list:
    """图-标记一致性：说明书具体实施方式引用的标记号在'附图标记清单'里无定义=悬空。"""
    issues = []
    defined = _spec_markers(spec)
    if not defined:
        return issues   # 无标记清单则不强求（诚实：不凭空报）
    # 实施方式里引用的标记：中文词后紧跟数字（如"机架1""电机2"），取数字
    referenced = set()
    for m in re.finditer(r"[一-龥]{2,}\s*(\d{1,3})(?![\d%])", spec):
        n = int(m.group(1))
        if 1 <= n <= 999:
            referenced.add(n)
    dangling = sorted(referenced - defined)
    # 只报"被引用却未定义"的悬空标记（保守，避免清单含未用标记的误报）
    if dangling:
        issues.append({
            "loc": "说明书/附图标记", "code": "FIGURE-MARKER-DANGLING",
            "severity": "minor",
            "msg": f"说明书引用了标记号 {dangling[:10]} 但'附图标记清单'未定义——"
                   f"悬空标记，核对附图标记清单是否漏列或正文标记号笔误（图-标记一致性）。"})
    return issues


def lint(claims_text: str, spec_text: str | None = None) -> dict:
    claims = parse_claims(claims_text)
    issues = []
    issues += check_numbering(claims)
    issues += check_antecedent_basis(claims)
    issues += check_part_mixing(claims)
    if spec_text:
        issues += check_word_support(claims, spec_text)
        issues += check_figure_markers(claims, spec_text)
    by_sev = {"major": 0, "minor": 0}
    for i in issues:
        by_sev[i["severity"]] = by_sev.get(i["severity"], 0) + 1
    return {"n_claims": len(claims), "claims": [c["num"] for c in claims],
            "n_issues": len(issues), "by_severity": by_sev, "issues": issues,
            "spec_checked": bool(spec_text),
            "note": "纯规则 linter，抓形式硬错(编号/在先基础/说明书支持/混用/悬空标记)，须代理师定稿。"}


def _sev_map(sev: str) -> str:
    """linter 严重度→findings_schema 词表：major=形式硬错(代理师直接打回)→critical(阻断 a08 闸门)。"""
    return {"major": "critical", "minor": "minor"}.get(sev, "info")


def to_findings(rep: dict) -> dict:
    """转 light.findings.v1（挂 _shared/findings_schema），接 a08 自检闸门。"""
    if not _HAS_FINDINGS:
        gates = []
        for i in rep["issues"]:
            gates.append({"gate": i["code"], "status": "fail" if i["severity"] == "major" else "warn",
                          "severity": _sev_map(i["severity"]),
                          "findings": [{"loc": i["loc"], "issue": i["msg"], "fix": "", "rule": i["code"]}]})
        verdict = "fail" if rep["by_severity"].get("major") else ("warn" if rep["issues"] else "pass")
        return {"schema": "light.findings.v1", "producer": "m15", "target": "ip/claims_draft.md",
                "verdict": verdict, "gates": gates, "summary": f"权利要求 linter:{rep['n_issues']}问题",
                "fresh_evidence": True, "_degraded": True}
    r = FindingsReport(producer="m15", target="ip/claims_draft.md", fresh_evidence=True,
                       summary=f"权利要求一致性 linter：{rep['n_claims']}项/{rep['n_issues']}问题")
    if not rep["issues"]:
        r.gates.append(GateResult("claim_consistency", "pass", "info"))
    for i in rep["issues"]:
        status = "fail" if i["severity"] == "major" else "warn"
        r.gates.append(GateResult(i["code"], status, _sev_map(i["severity"]),
                                  [Finding(i["loc"], i["msg"], rule=i["code"])]))
    return r.finalize().to_dict()


def to_markdown(rep: dict) -> str:
    lines = [f"# 权利要求一致性检查 — {rep['n_claims']} 项权利要求，{rep['n_issues']} 个问题"
             f"（major={rep['by_severity'].get('major',0)} minor={rep['by_severity'].get('minor',0)}）\n"]
    if not rep["issues"]:
        lines.append("✓ 未发现形式硬错（编号/在先基础/混用"
                     + ("/说明书支持/悬空标记" if rep["spec_checked"] else "") + "）。")
    for i in rep["issues"]:
        lines.append(f"- [{i['severity']}] {i['code']} @ {i['loc']}：{i['msg']}")
    if not rep["spec_checked"]:
        lines.append("\n> 未传 --spec：word-support 与图-标记一致性未检（传说明书可补这两类）。")
    lines.append(f"\n> {rep['note']}")
    return "\n".join(lines)


def _selftest() -> int:
    print("### claim_lint 离线自测", file=sys.stderr)

    # 病态权利要求：①从属项引用更大编号 ②antecedent basis 缺 ③多项引用用"和" ④单部分混用其特征在于
    bad_claims = """
1. 一种目标检测方法，包括以下步骤：
   S1. 获取图像；
   S2. 提取所述特征金字塔；
   其特征在于，对所述置信度阈值做校准。
2. 根据权利要求 3 所述的方法，其特征在于，所述特征金字塔包括多尺度融合。
3. 根据权利要求 1 和 2 所述的方法，其特征在于：补充限定。
"""
    rep = lint(bad_claims)
    codes = {i["code"] for i in rep["issues"]}
    print(to_markdown(rep), file=sys.stderr)
    assert rep["n_claims"] == 3, rep["claims"]
    assert "NUMBERING-DIRECTION" in codes, codes        # 权2引用权3(更大)
    assert "ANTECEDENT-BASIS" in codes, codes           # 所述特征金字塔/置信度阈值无首次引入
    assert "PART-METHOD-MIXING" in codes, codes         # 权1单部分骨架+其特征在于
    assert "MULTI-REF-NOT-OR" in codes, codes           # 权3"1和2"应"1或2"
    # findings 转换
    f = to_findings(rep)
    assert f["schema"] == "light.findings.v1" and f["verdict"] == "fail", f

    # 健康权利要求：单部分法不写其特征在于，术语先引入，从属引用方向正确
    good_claims = """
1. 一种基于特征金字塔的目标检测方法，包括以下步骤：
   S1. 获取图像，构建一个特征金字塔；
   S2. 在所述特征金字塔上提取候选框；
   S3. 对候选框做分类。
2. 根据权利要求 1 所述的方法，其特征在于，所述特征金字塔采用多尺度融合。
3. 根据权利要求 1 或 2 所述的方法，其特征在于，进一步包括非极大值抑制。
"""
    rg = lint(good_claims)
    print(f"[good] issues={[i['code'] for i in rg['issues']]}", file=sys.stderr)
    assert not any(i["severity"] == "major" for i in rg["issues"]), rg["issues"]

    # word-support：传说明书，权利要求术语缺说明书支持
    claims_ws = """
1. 一种方法，包括：构建一个目标检测模型；在所述目标检测模型上运行所述蒸馏模块。
"""
    spec_missing = "本发明涉及一种方法。具体实施方式：所述目标检测模型用于检测。"  # 缺"蒸馏模块"
    rw = lint(claims_ws, spec_missing)
    ws = [i for i in rw["issues"] if i["code"] == "WORD-SUPPORT"]
    assert any("蒸馏模块" in i["msg"] for i in ws), rw["issues"]
    assert not any("目标检测模型" in i["msg"] for i in ws), "目标检测模型在说明书中应不报"
    print("[word-support] 缺术语报警/有术语不报 ... OK", file=sys.stderr)

    # 图-标记悬空：说明书引用标记5但清单只定义1-3
    spec_fig = """附图标记清单：1-机架；2-电机；3-传感器。
具体实施方式：机架1上安装电机2，传感器3采集数据，控制器5做处理。"""
    rf = lint("1. 一种装置，其特征在于，包括机架。", spec_fig)
    assert any(i["code"] == "FIGURE-MARKER-DANGLING" for i in rf["issues"]), rf["issues"]
    print("[figure-marker] 悬空标记5检出 ... OK", file=sys.stderr)

    # 健康全绿：claims+spec 都干净 → 无 major
    clean_spec = "本发明一种基于特征金字塔的目标检测方法。所述特征金字塔采用多尺度融合，包括非极大值抑制。具体实施方式给出特征金字塔与候选框流程。"
    rc = lint(good_claims, clean_spec)
    assert not any(i["severity"] == "major" for i in rc["issues"]), rc["issues"]
    print("[clean] claims+spec 无 major ... OK", file=sys.stderr)

    print("[selftest] PASS claim_lint offline")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="权利要求一致性 linter（规则版）")
    ap.add_argument("--claims", help="权利要求书 md/txt 路径")
    ap.add_argument("--spec", help="说明书 md/txt 路径（启用 word-support + 图-标记检查）")
    ap.add_argument("--json", action="store_true", help="输出 light.findings.v1 JSON")
    ap.add_argument("--selftest", action="store_true", help="离线合成样本自测")
    args = ap.parse_args()

    if args.selftest or not args.claims:
        return _selftest()
    with open(args.claims, encoding="utf-8") as f:
        ctext = f.read()
    stext = None
    if args.spec:
        with open(args.spec, encoding="utf-8") as f:
            stext = f.read()
    rep = lint(ctext, stext)
    if args.json:
        print(json.dumps(to_findings(rep), ensure_ascii=False, indent=2))
    else:
        print(to_markdown(rep))
    # major 问题 → 退出码 1（可接 a08 闸门 / CI）
    return 1 if rep["by_severity"].get("major") else 0


if __name__ == "__main__":
    sys.exit(main())
