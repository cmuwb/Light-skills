#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_routing_eval.py — 工具路由回归 eval(借 RouteLLM benchmark / skill-creator eval 思路)。

把 detect_stack 的 task→tool 映射从"断言"变成"可验证":读 evals/tool_choice_eval.json
里的期望(类别/工具/别名规范/no-signal/异味),跑真实映射函数打分。RULES/ALIASES/SMELLS
任何改动都应跑此 eval——命中率掉了即回归报警,防阈值/规则漂移(竞品 RouteLLM 用 benchmark、
skill-creator 用 with/without eval 正是为此)。

用法:
  python run_routing_eval.py                 # 跑全 eval, 打印命中率, 退出码 0/1
  python run_routing_eval.py --json          # 机读结果
  python run_routing_eval.py --selftest      # 合成 eval 自测(不依赖外部 JSON)

依赖:纯 stdlib;复用同目录 detect_stack 的 suggest/_canon/check_smells。
设计:eval 全过(命中率=100%)才退 0;任何样例未达期望即退 1(CI 可接)。
"""
import sys, os, json, argparse

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import detect_stack as ds  # 复用映射真相源,不复制规则


def _eval_path():
    return os.path.join(os.path.dirname(__file__), "..", "evals", "tool_choice_eval.json")


def load_eval(path=None):
    p = path or _eval_path()
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _category_of(dep):
    """对单个依赖跑 suggest,返回 (命中类别 or None, 命中工具列表)。"""
    by_cat, matched = ds.suggest([dep])
    if not by_cat:
        return None, matched
    cat = next(iter(by_cat))
    return cat, matched


def run_eval(spec):
    """跑一份 eval spec,返回结构化结果(分项 + 汇总命中率 + 失败明细)。"""
    results = {"routing": [], "alias": [], "no_signal": [], "smell": []}
    fails = []

    for c in spec.get("routing_cases", []):
        by_cat, matched = ds.suggest(c["deps"])
        cats = set(by_cat.keys())
        ok_cat = c["expect_category"] in cats
        ok_tool = c.get("expect_tool") in matched if c.get("expect_tool") else True
        ok = ok_cat and ok_tool
        results["routing"].append({"id": c["id"], "pass": ok,
                                   "got_categories": sorted(cats), "matched": matched})
        if not ok:
            fails.append(f"routing {c['id']}: 期望类别 {c['expect_category']}"
                         f"/工具 {c.get('expect_tool')}，实得 {sorted(cats)}/{matched}")

    for c in spec.get("alias_cases", []):
        canon = ds._canon(c["dep"])
        cat, matched = _category_of(c["dep"])
        ok_canon = canon == c["canon"]
        ok_cat = cat == c["expect_category"]
        ok_matched = c["dep"] in matched  # 原始名应进 matched(别名也算命中)
        ok = ok_canon and ok_cat and ok_matched
        results["alias"].append({"id": c["id"], "pass": ok,
                                 "got_canon": canon, "got_category": cat})
        if not ok:
            fails.append(f"alias {c['id']}: {c['dep']} 期望规范到 {c['canon']}"
                         f"/类别 {c['expect_category']}，实得 {canon}/{cat}")

    for c in spec.get("no_signal_cases", []):
        by_cat, matched = ds.suggest([c["dep"]])
        ok = not matched  # 不该臆造命中
        results["no_signal"].append({"id": c["id"], "pass": ok, "matched": matched})
        if not ok:
            fails.append(f"no_signal {c['id']}: {c['dep']} 不该命中却命中 {matched}")

    for c in spec.get("smell_cases", []):
        ctx = {"deps": c.get("deps", []),
               "conda_deps": c.get("conda_deps", []),
               "pip_deps": c.get("pip_deps", []),
               "uses_defaults_channel": c.get("uses_defaults_channel", False)}
        smell_ids = {s["id"] for s in ds.check_smells(ctx)}
        ok = c["expect_smell"] in smell_ids
        results["smell"].append({"id": c["id"], "pass": ok,
                                 "got_smells": sorted(smell_ids)})
        if not ok:
            fails.append(f"smell {c['id']}: 期望异味 {c['expect_smell']}，"
                         f"实得 {sorted(smell_ids)}")

    total = sum(len(v) for v in results.values())
    passed = sum(1 for v in results.values() for r in v if r["pass"])
    return {
        "total": total, "passed": passed,
        "hit_rate": round(passed / total, 4) if total else 0.0,
        "results": results, "fails": fails,
    }


def print_eval(rep):
    print("=" * 56)
    print("工具路由 eval(task→tool 映射回归)")
    print("=" * 56)
    for section in ("routing", "alias", "no_signal", "smell"):
        rows = rep["results"][section]
        npass = sum(1 for r in rows if r["pass"])
        print(f"  {section:10s}: {npass}/{len(rows)} pass")
    print(f"\n命中率: {rep['passed']}/{rep['total']} = {rep['hit_rate']*100:.1f}%")
    if rep["fails"]:
        print("\n[未达期望(回归报警)]")
        for f in rep["fails"]:
            print(f"  - {f}")


def _selftest():
    """合成一份内联 eval,不依赖外部 JSON,断言 eval 引擎本身正确。"""
    spec = {
        "routing_cases": [
            {"id": "t1", "deps": ["pandas"], "expect_category": "数据处理", "expect_tool": "pandas"},
            {"id": "t2", "deps": ["fastapi"], "expect_category": "后端", "expect_tool": "fastapi"},
        ],
        "alias_cases": [
            {"id": "ta", "dep": "torch-geometric", "canon": "torch", "expect_category": "深度学习"},
        ],
        "no_signal_cases": [{"id": "tn", "dep": "made-up-pkg-zzz"}],
        "smell_cases": [
            {"id": "ts", "deps": ["tensorflow", "torch"], "expect_smell": "double_dl_framework"},
            {"id": "ts2", "conda_deps": ["numpy"], "pip_deps": ["numpy"], "expect_smell": "pip_conda_mix"},
        ],
    }
    rep = run_eval(spec)
    failures = []
    if rep["hit_rate"] != 1.0:
        failures.append(f"合成 eval 应全过，实得命中率 {rep['hit_rate']}: {rep['fails']}")

    # 负样例:故意给错期望，断言 eval 能抓出来(不是永远绿)
    bad = run_eval({"routing_cases": [
        {"id": "bad", "deps": ["pandas"], "expect_category": "后端"}]})
    if bad["hit_rate"] == 1.0:
        failures.append("错期望应被 eval 判失败，却全过(eval 失灵)")

    # 真实外部 eval JSON 也应当全绿(规则与基准一致)
    try:
        real = run_eval(load_eval())
        if real["hit_rate"] != 1.0:
            failures.append(f"外部 tool_choice_eval.json 命中率 {real['hit_rate']} "
                            f"<100%(规则漂移): {real['fails']}")
    except FileNotFoundError:
        print("  [注] 未找到外部 eval JSON，仅跑合成自测")

    print_eval(rep)
    print("\n--- 自检断言 ---")
    for msg in failures:
        print(f"  [FAIL] {msg}")
    if not failures:
        print("  [PASS] 合成 eval 全绿")
        print("  [PASS] 错期望被正确判失败")
        print("  [PASS] 外部 eval JSON 全绿(无规则漂移)")
    print(f"\n自检结果: {'全部通过' if not failures else '存在失败'}")
    return 0 if not failures else 1


def main():
    ap = argparse.ArgumentParser(description="工具路由回归 eval")
    ap.add_argument("--json", action="store_true", help="输出机读结果")
    ap.add_argument("--selftest", "--self-test", dest="selftest",
                    action="store_true", help="合成 eval 自测")
    args = ap.parse_args()
    if args.selftest:
        return _selftest()
    rep = run_eval(load_eval())
    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print_eval(rep)
    return 0 if rep["hit_rate"] == 1.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
