#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gate_runner.py —— gate 聚合执行器 (Light / _shared 地基契约4 之二)

把多个独立 gate 函数(a07 证据↔措辞、m10 引用支撑、m07 draft-lint、a10 结论夸大门 ...)
跑成一份统一的 light.findings.v1 报告。任一 critical fail -> 整体 verdict=fail。
这是 a01 passport 确认点判定的接线处:passport 不再消费 prose verdict,改读本报告。

gate 函数契约(供消费技能实现):
  def my_gate(artifact) -> GateResult
      入参 artifact 为任意被检查对象(路径/dict/文本均可,由 gate 自解释)
      返回一个 GateResult;若内部抛异常,run_gates 会捕获并记为 critical fail(不静默吞)

用法:
  python gate_runner.py --selftest        # 合成 gate 自测, 退出码 0/1
  消费方 import:
      from gate_runner import run_gates
      from findings_schema import GateResult, Finding
      report = run_gates([gate_a, gate_b], artifact, producer="a01", target="draft.md")
      if report.verdict == "fail": ...

依赖:纯 Python stdlib + 同目录 findings_schema。无网络、无外部数据。
"""
import sys, json, argparse, traceback
from typing import Callable, List, Any, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 同目录 import:既支持作为脚本直接跑,也支持作为包模块被 import
try:
    from findings_schema import Finding, GateResult, FindingsReport
except ImportError:  # 作为包 skills._shared 被导入时
    from .findings_schema import Finding, GateResult, FindingsReport  # type: ignore

GateFn = Callable[[Any], GateResult]


def run_gates(gate_fns: List[GateFn], artifact: Any,
              producer: str = "gate_runner", target: str = "",
              summary: str = "", fresh_evidence: bool = False) -> FindingsReport:
    """顺序执行所有 gate 函数,聚合成一份 FindingsReport。

    - 每个 gate_fn(artifact) 应返回 GateResult。
    - gate 抛异常不静默:记为一个 status=fail / severity=critical 的 GateResult,
      携带 traceback 作为 finding,保证错误浮出水面(诚实纪律)。
    - 整体 verdict 由 FindingsReport.compute_verdict 推导:任一 critical fail -> fail。
    """
    gates: List[GateResult] = []
    for fn in gate_fns:
        name = getattr(fn, "__name__", repr(fn))
        try:
            gr = fn(artifact)
            if not isinstance(gr, GateResult):
                raise TypeError(
                    f"gate {name!r} 返回 {type(gr).__name__},应返回 GateResult")
            gates.append(gr)
        except Exception as e:  # noqa: BLE001 —— 故意全捕获,转成可见 critical fail
            tb = traceback.format_exc(limit=3)
            gates.append(GateResult(
                gate=name,
                status="fail",
                severity="critical",
                findings=[Finding(
                    loc=f"gate:{name}",
                    issue=f"gate 执行抛异常: {type(e).__name__}: {e}",
                    fix="修复该 gate 实现或其输入工件",
                    evidence=tb.strip(),
                    rule="gate_runner.exception",
                )],
                note="gate 抛异常被 gate_runner 捕获并记为 critical fail(未静默)",
            ))
    if not summary:
        n_fail = sum(1 for g in gates if g.status == "fail")
        n_warn = sum(1 for g in gates if g.status == "warn")
        summary = (f"{len(gates)} gate 执行: {n_fail} fail / {n_warn} warn / "
                   f"{len(gates) - n_fail - n_warn} pass")
    report = FindingsReport(
        producer=producer, target=target,
        gates=gates, summary=summary, fresh_evidence=fresh_evidence,
    )
    return report.finalize()


def run_gates_to_json(gate_fns: List[GateFn], artifact: Any, **kw) -> str:
    """便捷封装:跑完直接出 JSON 字符串(机读优先)。"""
    return run_gates(gate_fns, artifact, **kw).to_json()


# ---------------------------------------------------------------- selftest
def _selftest() -> int:
    failures = []

    def check(cond, msg):
        if not cond:
            failures.append(msg)

    # 合成 gate:一个 pass、一个 critical fail、一个 warn、一个抛异常
    def gate_pass(art) -> GateResult:
        return GateResult("ok_gate", "pass", "info")

    def gate_crit(art) -> GateResult:
        return GateResult("evidence_wording", "fail", "critical",
                          [Finding(f"{art}:42", "断言夸大", "降级 prove->suggest")])

    def gate_warn(art) -> GateResult:
        return GateResult("style", "warn", "minor",
                          [Finding(f"{art}:3", "口语化", "改正式")])

    def gate_boom(art) -> GateResult:
        raise RuntimeError("模拟 gate 内部炸了")

    # 1. 有 critical fail -> 整体 fail
    rep = run_gates([gate_pass, gate_crit, gate_warn], "draft.md",
                    producer="a01", target="draft.md")
    check(rep.verdict == "fail", "含 critical fail 时整体应 fail")
    check(rep.producer == "a01" and rep.target == "draft.md", "producer/target 应透传")
    check(len(rep.gates) == 3, "应有 3 个 gate 结果")

    # 2. 无 critical、有 warn -> warn
    rep2 = run_gates([gate_pass, gate_warn], "sec.md")
    check(rep2.verdict == "warn", "仅 warn 时整体应 warn")

    # 3. 全 pass -> pass
    rep3 = run_gates([gate_pass, gate_pass], "x")
    check(rep3.verdict == "pass", "全 pass 时整体应 pass")

    # 4. gate 抛异常 -> 被捕获为 critical fail, 不静默, 整体 fail
    rep4 = run_gates([gate_pass, gate_boom], "y")
    check(rep4.verdict == "fail", "gate 抛异常应导致整体 fail")
    boom = [g for g in rep4.gates if g.gate == "gate_boom"]
    check(len(boom) == 1 and boom[0].is_blocking(), "异常 gate 应记为 critical fail")
    check("抛异常" in boom[0].findings[0].issue, "异常 finding 应说明抛异常")
    check(boom[0].findings[0].evidence and "RuntimeError" in boom[0].findings[0].evidence,
          "异常 finding 应带 traceback 证据")

    # 5. gate 返回非 GateResult -> 也记为 critical fail
    def gate_bad(art):
        return "我不是 GateResult"
    rep5 = run_gates([gate_bad], "z")
    check(rep5.verdict == "fail", "gate 返回错类型应导致 fail")

    # 6. 输出 JSON 合法且可被 findings_schema 反序列化
    js = run_gates_to_json([gate_pass, gate_crit], "draft.md",
                           producer="a01", target="draft.md")
    back = FindingsReport.from_json(js)
    check(back.verdict == "fail", "JSON 往返后 verdict 应保真")
    check(any(g.gate == "evidence_wording" for g in back.gates), "往返后 gate 名应保真")

    # 7. summary 自动生成包含计数
    check("gate 执行" in rep.summary, "summary 应自动汇总计数")

    if failures:
        print("gate_runner selftest 失败:")
        for f in failures:
            print("  -", f)
        return 1
    print("gate_runner selftest 全绿: 7 组断言通过 (含异常捕获/类型校验/JSON往返)")
    return 0


def main():
    ap = argparse.ArgumentParser(description="gate 聚合执行器 (run_gates)")
    ap.add_argument("--selftest", action="store_true", help="运行合成 gate 自测")
    ap.parse_args()
    return _selftest()


if __name__ == "__main__":
    sys.exit(main())
