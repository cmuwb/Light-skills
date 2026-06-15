# -*- coding: utf-8 -*-
"""证据强度契约 (light.evidence_strength.v1) — Light 升级地基契约 1/4。

目的
----
把 m06(result-analysis)已经算出的 q 值 / 效应量 / 置信区间，从"只存自己的
claim_evidence_table"升级为**全包共享的措辞校准源**，消灭"正文措辞强于证据"
这一全包通病(审查病1)。统计强度 → 允许的断言措辞档做机械映射。

被谁消费
--------
- m06 result-analysis : 产出方，emit evidence_strength.json
- m07 paper-drafting  : draft_lint --evidence，写作时卡措辞上限
- m08 paper-polishing : 润色时按 grade 绑定措辞强度
- m10 citation        : 引用支撑度 → 措辞
- m09 / m11           : 图表统计标注
- m16 slides          : action-title 措辞
- a07 consistency     : 证据↔措辞一致性维度
- a10 research-ethics : "结论夸大"门装上可执行工具

措辞档的依据
------------
学术写作的 hedging 阶梯(Hyland 1998《Hedging in Scientific Research Articles》)：
强证据才可用 demonstrate/establish 这类高确定性 factive 动词；弱证据须用
suggest/may/appear 等 hedge；不显著只能报 "no significant difference"。
本契约把这条人文惯例落成可机检的退出码门。

纯 Python stdlib，无第三方依赖。`python evidence_contract.py --selftest` 自测。
"""
from __future__ import annotations
import json
import re
import sys
from typing import Any

SCHEMA_ID = "light.evidence_strength.v1"

# ── 措辞档：grade → 允许/禁止的断言动词 + 是否强制 hedge ──────────────
# 动词按确定性强度分层。高档动词向下兼容(strong 可用 moderate/weak 的词)。
_VERB_TIERS = {
    "strong":   ["demonstrate", "establish", "show", "confirm", "prove_NO"],  # prove 仍保留克制
    "moderate": ["show", "indicate", "improve", "support", "find"],
    "weak":     ["suggest", "may", "appear", "seem", "could", "might", "tend to"],
    "none":     ["no significant difference", "not significant", "did not differ"],
}
# 高确定性断言动词全集(lint 时据此判断"是否在做强断言")
_ASSERTIVE_VERBS = [
    "prove", "proves", "proven", "proved",
    "demonstrate", "demonstrates", "demonstrated",
    "establish", "establishes", "established",
    "confirm", "confirms", "confirmed",
    "show", "shows", "showed", "shown",
    "significantly", "significant improvement", "substantially",
    "outperform", "outperforms", "outperformed",
    "superior", "best", "state-of-the-art", "sota",
]
# hedge 动词(弱证据应当使用)
_HEDGE_VERBS = ["suggest", "suggests", "may", "appear", "appears", "seem",
                "seems", "could", "might", "tend", "potentially", "preliminary"]


def grade_evidence(q_fdr: float | None,
                   effect_size: float | None,
                   ci95: list | tuple | None,
                   n: int | None) -> str:
    """把统计证据归一成四档之一: strong | moderate | weak | none。

    规则(保守，宁可低估证据强度):
    - none     : 不显著(q>=.05) 或 CI 跨 0 或 q 缺失
    - strong   : q<.01 且 |effect|>=0.5 且 CI 不跨 0 且 n>=30
    - moderate : 显著(q<.05) 且 |effect|>=0.5(中等以上效应)，但未达 strong 的全部条件
    - weak     : 显著但小效应(|effect|<0.5) 或 小样本(n<30)
    """
    # 不显著优先判定
    if q_fdr is None or q_fdr >= 0.05:
        return "none"
    if ci95 is not None and len(ci95) == 2:
        lo, hi = ci95
        if lo is not None and hi is not None and lo <= 0 <= hi:
            return "none"  # CI 跨 0 → 差异方向不确定
    eff = abs(effect_size) if effect_size is not None else None
    nn = n if n is not None else 0
    if q_fdr < 0.01 and eff is not None and eff >= 0.5 and nn >= 30:
        # 还需 CI 不跨 0(上面已排除跨0)
        return "strong"
    if nn and nn < 30:
        return "weak"  # 小样本封顶 weak，即便效应中等(估计不稳)
    if eff is not None and eff >= 0.5:
        return "moderate"
    return "weak"


def allowed_verb_tier(grade: str) -> dict:
    """grade → {allowed, forbidden, hedge_required}。"""
    grade = grade if grade in _VERB_TIERS else "none"
    if grade == "strong":
        return {"allowed": ["demonstrate", "establish", "show", "confirm"],
                "forbidden": [],  # 强证据基本不禁(prove 仍建议克制但不硬禁)
                "hedge_required": False}
    if grade == "moderate":
        return {"allowed": ["show", "indicate", "improve", "support", "find"],
                "forbidden": ["prove", "demonstrate", "establish", "confirm"],
                "hedge_required": False}
    if grade == "weak":
        return {"allowed": ["suggest", "may", "appear", "seem", "could", "might"],
                "forbidden": ["prove", "demonstrate", "establish", "confirm",
                              "show", "significantly", "outperform", "superior"],
                "hedge_required": True}
    # none
    return {"allowed": ["no significant difference", "not significant", "did not differ"],
            "forbidden": _ASSERTIVE_VERBS[:],
            "hedge_required": True}


def lint_wording(text: str, claim_evidence: dict) -> list:
    """扫一段正文的断言动词，对照该 claim 的证据 grade，超档即报 violation。

    claim_evidence: 单条 claim 的证据 dict，至少含 evidence_grade(或可由
    q_fdr/effect_size/ci95/n 现算)。返回 violations 列表，每条含定位与降级建议。
    """
    grade = claim_evidence.get("evidence_grade")
    if grade is None:
        grade = grade_evidence(claim_evidence.get("q_fdr"),
                               claim_evidence.get("effect_size"),
                               claim_evidence.get("ci95"),
                               claim_evidence.get("n"))
    tier = allowed_verb_tier(grade)
    forbidden = set(v.lower() for v in tier["forbidden"])
    violations = []
    low = text.lower()
    for verb in sorted(forbidden, key=len, reverse=True):
        # 允许常见词形变化(demonstrate→demonstrates/demonstrated);多词短语整体匹配
        if " " in verb:
            pat = r"\b" + re.escape(verb) + r"\b"
        else:
            pat = r"\b" + re.escape(verb) + r"(?:s|es|ed|d|ing)?\b"
        for m in re.finditer(pat, low):
            # 计算行号(1-based)
            line_no = text.count("\n", 0, m.start()) + 1
            suggest = (tier["allowed"][0] if tier["allowed"] else "(remove claim)")
            violations.append({
                "loc": f"line {line_no}, col {m.start() - low.rfind(chr(10), 0, m.start())}",
                "matched": verb,
                "grade": grade,
                "issue": f"措辞 '{verb}' 强于证据档 '{grade}'",
                "suggestion": f"降级为 '{suggest}'" + ("，并加 hedge" if tier["hedge_required"] else ""),
            })
    # hedge 强制但全文无 hedge 词
    if tier["hedge_required"] and not any(re.search(r"\b" + re.escape(h) + r"\b", low) for h in _HEDGE_VERBS):
        violations.append({
            "loc": "whole",
            "matched": None,
            "grade": grade,
            "issue": f"证据档 '{grade}' 要求 hedge，但正文无任何 hedge 措辞",
            "suggestion": "加入 suggest/may/appear 等 hedge，或报 'no significant difference'",
        })
    return violations


def build_evidence_json(claims: list) -> dict:
    """把一组 claim(含 q_fdr/effect_size/ci95/n)产出为 light.evidence_strength.v1。

    自动补 evidence_grade / allowed_verbs / forbidden_verbs / hedge_required。
    """
    out_claims = []
    for c in claims:
        grade = c.get("evidence_grade") or grade_evidence(
            c.get("q_fdr"), c.get("effect_size"), c.get("ci95"), c.get("n"))
        tier = allowed_verb_tier(grade)
        out_claims.append({
            "claim_id": c.get("claim_id"),
            "text": c.get("text", ""),
            "q_fdr": c.get("q_fdr"),
            "effect_size": c.get("effect_size"),
            "effect_kind": c.get("effect_kind", "cohens_d"),
            "ci95": c.get("ci95"),
            "n": c.get("n"),
            "evidence_grade": grade,
            "allowed_verbs": tier["allowed"],
            "forbidden_verbs": tier["forbidden"],
            "hedge_required": tier["hedge_required"],
        })
    return {"schema": SCHEMA_ID,
            "source": "m06:claim_evidence_table",
            "claims": out_claims}


def save(report: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ──────────────────────────── selftest ────────────────────────────
def _selftest() -> int:
    ok = True

    def check(cond, msg):
        nonlocal ok
        status = "PASS" if cond else "FAIL"
        if not cond:
            ok = False
        print(f"  [{status}] {msg}")

    print("evidence_contract selftest")
    # 1. grade 分档
    check(grade_evidence(0.001, 0.9, [0.4, 1.3], 120) == "strong", "强证据→strong")
    check(grade_evidence(0.02, 0.7, [0.2, 1.0], 80) == "moderate", "显著中效应→moderate")
    check(grade_evidence(0.03, 0.2, [0.05, 0.4], 200) == "weak", "显著小效应→weak")
    check(grade_evidence(0.01, 0.8, [0.5, 1.1], 20) == "weak", "小样本n<30→weak")
    check(grade_evidence(0.20, 0.9, [-0.1, 1.5], 100) == "none", "不显著→none")
    check(grade_evidence(0.001, 0.9, [-0.2, 1.5], 100) == "none", "CI跨0→none")
    check(grade_evidence(None, 0.9, None, 100) == "none", "q缺失→none")

    # 2. 措辞档
    t_strong = allowed_verb_tier("strong")
    check("demonstrate" in t_strong["allowed"] and not t_strong["hedge_required"],
          "strong 允许 demonstrate 且无需 hedge")
    t_weak = allowed_verb_tier("weak")
    check("suggest" in t_weak["allowed"] and "demonstrate" in t_weak["forbidden"]
          and t_weak["hedge_required"], "weak 允许 suggest 禁 demonstrate 须 hedge")
    t_none = allowed_verb_tier("none")
    check("show" in t_none["forbidden"], "none 禁 show 等所有断言")

    # 3. lint 抓超档
    weak_claim = {"q_fdr": 0.03, "effect_size": 0.2, "ci95": [0.05, 0.4], "n": 200}
    v1 = lint_wording("Our method demonstrates a significant improvement.", weak_claim)
    check(any(x["matched"] == "demonstrate" for x in v1), "lint 抓到 weak 证据下的 demonstrate")
    check(any(x["matched"] == "significantly" or "significant improvement" in (x["matched"] or "")
              for x in v1) or len(v1) >= 1, "lint 报告了超档措辞")
    # 合规措辞不报(除可能的 hedge 要求)
    v2 = lint_wording("Our method may suggest a modest gain.", weak_claim)
    hard = [x for x in v2 if x["matched"] is not None]
    check(len(hard) == 0, "合规弱措辞无硬性 violation")
    # strong 证据下 demonstrate 合法
    strong_claim = {"q_fdr": 0.001, "effect_size": 0.9, "ci95": [0.4, 1.3], "n": 120}
    v3 = lint_wording("We demonstrate a clear effect.", strong_claim)
    check(len([x for x in v3 if x["matched"] == "demonstrate"]) == 0,
          "strong 证据下 demonstrate 不报")

    # 4. build_evidence_json + 往返
    rep = build_evidence_json([
        {"claim_id": "c1", "text": "A>B", "q_fdr": 0.001, "effect_size": 0.9,
         "ci95": [0.4, 1.3], "n": 120},
        {"claim_id": "c2", "text": "C~D", "q_fdr": 0.3, "effect_size": 0.1,
         "ci95": [-0.2, 0.4], "n": 50},
    ])
    check(rep["schema"] == SCHEMA_ID, "schema id 正确")
    check(rep["claims"][0]["evidence_grade"] == "strong", "c1 强证据")
    check(rep["claims"][1]["evidence_grade"] == "none", "c2 不显著")
    s = json.dumps(rep, ensure_ascii=False)
    check(json.loads(s)["claims"][0]["allowed_verbs"], "JSON 往返保真")

    print("ALL PASS" if ok else "SOME FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    print(__doc__)
    print("用法: python evidence_contract.py --selftest")
