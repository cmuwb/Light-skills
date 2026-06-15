# -*- coding: utf-8 -*-
"""review_lint.py — 自查证据闸门（Light a09，把"闸门话术"变成可执行检查器）。

为什么
------
审查头号名实差距：本技能此前 `scripts/` 为空，SKILL.md 却通篇"闸门函数/当场重跑/
数失败条数"等强执行话术——读者误以为有自动化校验，实则 100% 靠模型自觉。TACL 2024
证明自我承诺式自纠最不可靠，缺**外部验证器**时形同虚设。本脚本是那个外部验证器：
扫描待交付文本 + 本轮工具调用日志，产出机器可读 findings，exit≠0 阻断交付。

三类检测
--------
① hype 词：novel/significantly/SOTA/outperform(s) all/state-of-the-art/robust/
   seamless 等——带行号 + 是否邻近显著性证据(p 值/CI/±std)。无证据的 hype → FAIL。
② 未验证完成声明：出现"测试通过/已修复/构建成功/all pass/fixed/works now"，
   但本轮工具日志里无对应命令的 exit 0 输出 → 高危(自我承诺无外部证据)。
③ 定量主张缺引用/支撑：数字结论(x%、提升 N)附近无引用锚点或证据指针 → 提示补。

挂接共享地基契约 findings_schema + gate_runner，产出 light.findings.v1，
可被 orchestrator passport / CI 直接消费。纯 stdlib。
`python review_lint.py deliverable.md [--log toollog.txt] [--json]` / `--selftest`。
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
    from gate_runner import run_gates  # noqa: E402
    _HAS_FINDINGS = True
except Exception:
    _HAS_FINDINGS = False

# ① hype 词（举证责任在作者的强主张）
HYPE = re.compile(
    r"\b(significantly|significant|state[- ]of[- ]the[- ]art|SOTA|"
    r"outperform\w*|novel|robust|seamless\w*|best[- ]ever|unprecedented|"
    r"dramatic\w*|substantial\w*|remarkabl\w*)\b", re.I)
HYPE_CJK = re.compile(r"(显著|大幅|远超|碾压|最优|前所未有|突破性|革命性|完美)")
# 显著性/证据邻近信号
SIG = re.compile(r"p\s*[<=>]\s*0?\.\d+|95%\s*CI|±\s*\d|\bstd\b|q\s*[<=]|d\s*=", re.I)
# ② 未验证完成声明
DONE_CLAIM = re.compile(
    r"\b(tests?\s+pass\w*|all\s+pass\w*|build\s+(succeed\w*|success\w*|pass\w*)|"
    r"fixed|works?\s+now|verified|done\b)\b", re.I)
DONE_CJK = re.compile(r"(测试通过|已修复|构建成功|跑通了|验证通过|搞定|完成了)")
# 工具日志里的成功证据（exit 0 / passed / ALL PASS 等）
LOG_OK = re.compile(r"(exit\s*(code)?\s*[:=]?\s*0|退出码\s*[:=]?\s*0|"
                    r"\bPASS\b|passed|ok\b|✓)", re.I)
# ③ 定量主张
QUANT = re.compile(r"\d+(?:\.\d+)?\s*%|\b(?:提升|提高|降低|reduc\w*|improv\w*|increas\w*)\s*\d")
# 引用/证据锚点
CITE_ANCHOR = re.compile(r"\[\d+\]|\\cite|\bdoi\b|10\.\d{4}|\(20\d\d\)|表\s*\d|figure|图\s*\d|table", re.I)


def _split_sentences(text):
    return re.split(r"(?<=[.!?。！？])\s+|\n", text)


def lint_text(text, tool_log=""):
    """返回 (findings_list, counts)。findings 为 dict 列表(可转 Finding)。"""
    findings = []
    lines = text.splitlines()
    log_has_ok = bool(LOG_OK.search(tool_log)) if tool_log else False

    # ① hype 词 + 邻近证据判定
    for i, ln in enumerate(lines, 1):
        for m in list(HYPE.finditer(ln)) + list(HYPE_CJK.finditer(ln)):
            window = " ".join(lines[max(0, i - 2):i + 1])
            if not SIG.search(window):
                findings.append({
                    "severity": "high", "rule": "hype_no_evidence",
                    "loc": f"L{i}", "msg": f"强主张'{m.group(0)}'附近无显著性证据(p/CI/±std)",
                    "suggestion": "补显著性检验结果，或降级措辞(如 may/suggest)"})

    # ② 未验证完成声明
    for i, ln in enumerate(lines, 1):
        dm = DONE_CLAIM.search(ln) or DONE_CJK.search(ln)
        if dm and not log_has_ok:
            findings.append({
                "severity": "high", "rule": "unverified_done_claim",
                "loc": f"L{i}", "msg": f"完成声明'{dm.group(0)}'但本轮工具日志无 exit 0/PASS 证据",
                "suggestion": "贴出实际命令输出与退出码，或撤回声明(TACL2024:自我承诺不可靠)"})

    # ③ 定量主张缺引用/证据锚点
    sents = _split_sentences(text)
    for s in sents:
        if QUANT.search(s) and not CITE_ANCHOR.search(s):
            findings.append({
                "severity": "medium", "rule": "quant_no_anchor",
                "loc": s.strip()[:50], "msg": "定量主张附近无引用/表图/证据锚点",
                "suggestion": "标注来源(引用/表X/图X)或证据指针"})

    counts = {"high": sum(1 for f in findings if f["severity"] == "high"),
              "medium": sum(1 for f in findings if f["severity"] == "medium"),
              "total": len(findings)}
    return findings, counts


def build_report(text, tool_log=""):
    """产出 light.findings.v1 报告（挂接共享契约）。"""
    raw, counts = lint_text(text, tool_log)
    if not _HAS_FINDINGS:
        return {"schema": "light.findings.v1(degraded)", "counts": counts,
                "findings": raw, "verdict": "fail" if counts["high"] else "pass",
                "_note": "findings_schema 契约不可用，降级输出"}

    def _fs(rule):
        return [Finding(loc=f["loc"], issue=f["msg"], fix=f["suggestion"], rule=f["rule"])
                for f in raw if f["rule"] == rule]

    # hype/done 无证据 → critical fail(拉整体 verdict=fail);quant → minor warn
    def gate_hype(ctx):
        fs = _fs("hype_no_evidence")
        return GateResult(gate="hype_no_evidence",
                          status="fail" if fs else "pass",
                          severity="critical" if fs else "info", findings=fs)

    def gate_done(ctx):
        fs = _fs("unverified_done_claim")
        return GateResult(gate="unverified_done_claim",
                          status="fail" if fs else "pass",
                          severity="critical" if fs else "info", findings=fs)

    def gate_quant(ctx):
        fs = _fs("quant_no_anchor")
        return GateResult(gate="quant_no_anchor",
                          status="warn" if fs else "pass",
                          severity="minor" if fs else "info", findings=fs)

    report = run_gates([gate_hype, gate_done, gate_quant], {},
                       producer="a09:review_lint", target="deliverable")
    d = report.to_dict()
    d["counts"] = counts
    return d


def _selftest() -> int:
    ok = True

    def check(cond, msg):
        nonlocal ok
        if not cond:
            ok = False
        print(f"  [{'PASS' if cond else 'FAIL'}] {msg}")

    print("review_lint selftest")
    check(_HAS_FINDINGS, "findings_schema/gate_runner 契约可导入")

    # ① hype 无证据 → high
    f1, c1 = lint_text("Our method significantly outperforms all baselines.")
    check(any(f["rule"] == "hype_no_evidence" for f in f1), "无证据 hype 被标 high")
    # hype 有邻近证据 → 不报
    f2, c2 = lint_text("Our method outperforms baselines (p<0.001, 95% CI [0.1,0.3]).")
    check(not any(f["rule"] == "hype_no_evidence" for f in f2), "有显著性证据的主张不报")

    # ② 完成声明无日志证据 → high
    f3, c3 = lint_text("All tests pass and the build succeeded.")
    check(any(f["rule"] == "unverified_done_claim" for f in f3), "无日志证据的完成声明被标")
    # 有日志 exit 0 → 不报
    f4, c4 = lint_text("All tests pass.", tool_log="$ pytest\n12 passed\nexit code 0")
    check(not any(f["rule"] == "unverified_done_claim" for f in f4), "有 exit0 日志的完成声明不报")

    # ③ 定量无锚点 → medium；有引用 → 不报
    f5, c5 = lint_text("We improve accuracy by 4.2% over the prior work.")
    check(any(f["rule"] == "quant_no_anchor" for f in f5), "定量无锚点被标 medium")
    f6, c6 = lint_text("We improve accuracy by 4.2% (see Table 3).")
    check(not any(f["rule"] == "quant_no_anchor" for f in f6), "有表引用的定量不报")

    # 中文同理
    f7, _ = lint_text("本方法显著优于所有基线。")
    check(any(f["rule"] == "hype_no_evidence" for f in f7), "中文 hype 被标")
    f8, _ = lint_text("测试通过，已修复该 bug。")
    check(any(f["rule"] == "unverified_done_claim" for f in f8), "中文完成声明被标")

    # 报告挂接 findings 契约
    rep = build_report("Our novel method significantly beats SOTA.")
    if _HAS_FINDINGS:
        check(rep.get("schema") == "light.findings.v1", "产出 light.findings.v1")
        check(rep.get("verdict") in ("fail", "warn", "pass"), "有 verdict")
        check(rep["verdict"] == "fail", "无证据强主张→verdict fail")

    # 干净文本 → pass
    clean = build_report("We report accuracy of 0.9 (Table 2). Results may suggest a gain (p<0.01).",
                         tool_log="exit code 0")
    check(clean["verdict"] in ("pass", "warn"), "干净文本不 fail")

    print("ALL PASS" if ok else "SOME FAILED")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="自查证据闸门(可执行检查器,非提示词)")
    ap.add_argument("file", nargs="?", help="待交付文本")
    ap.add_argument("--log", help="本轮工具调用日志文件(用于核验完成声明)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(_selftest())
    if not a.file:
        print(__doc__); return
    text = open(a.file, encoding="utf-8").read()
    tool_log = open(a.log, encoding="utf-8").read() if a.log and os.path.exists(a.log) else ""
    rep = build_report(text, tool_log)
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print(f"verdict={rep['verdict']}  counts={rep.get('counts', rep.get('summary'))}")
        for g in rep.get("gates", []):
            for f in g.get("findings", []):
                print(f"  [{g.get('severity')}] {f.get('loc')}: {f.get('issue')}")
    sys.exit(1 if rep["verdict"] == "fail" else 0)


if __name__ == "__main__":
    main()
