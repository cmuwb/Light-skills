#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""session_start_resident.py — Light 常驻纪律的确定性注入钩子（Claude Code SessionStart）。

为什么存在：Claude Code 技能只有两种触发——用户打 /name，或模型读 description 那句
自主判断相关才加载。没有第三种。正文只在被调用那次进上下文，compaction 后可能整个掉。
于是 ROUTER/CONVENTIONS 写的"a07-a10 所有任务后台生效""常驻、输出前必跑"在纯
description 机制下是**愿望非保证**，全靠概率匹配。self-review/research-ethics 这种
要求 100% 触发的兜不住。

本钩子是用户决定的"CLAUDE.md + hooks 双保险"里的 hook 半边：在每次会话开始
（SessionStart）由 harness 确定性地把常驻技能清单 + 何时必跑，注入为 additionalContext。
这是 harness 层的强制，不依赖模型自觉，补 description 概率匹配的缺口。

设计纪律：
- 纯 stdlib、零网络、跨平台（Windows/macOS/Linux 同一份）。
- 读 stdin 的 hook 输入 JSON（Claude Code SessionStart 协议），输出 hookSpecificOutput
  .additionalContext。解析失败也**不**让会话崩——降级为直接打印纪律文本到 stdout。
- 注入内容是**指针式精简清单**（哪些技能常驻、何时必跑），不复制各 SKILL 正文，避免
  上下文膨胀与真相源分裂；详细判据仍在各 SKILL.md / ROUTER.md / CONVENTIONS.md。
- 幂等无副作用：只读 + 输出，绝不写任何文件。

安装：见 .claude/INSTALL.md，把本脚本注册为 SessionStart hook（settings.json 片段
在 hooks/settings.snippet.json）。自测：python session_start_resident.py --selftest
"""
from __future__ import annotations

import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# 常驻纪律精简版（单一真相源仍在 ROUTER.md §常驻技能 / CONVENTIONS / 各 SKILL）
RESIDENT_CONTEXT = """\
# Light 科研技能包 · 常驻纪律（SessionStart 注入）

下列为**常驻技能**：无需用户显式 /调用，凡相关任务都应主动按其 SKILL.md 执行。
这是 harness 层提醒，不是可选建议——尤其 a08/a10 要求每次对外输出前都过一遍。

- **a07 consistency**：术语/指标/创新点跨材料一致性，定义一改回扫所有产物。
- **a08 self-review**：每次对外输出前自审（逻辑/事实/格式/夸大/审美/引用/可执行）。重产出跑全量、轻改动跑最小三项。
- **a09 tool-selection**：选工具/选方法前先查 decision_matrix，别凭记忆。
- **a10 research-ethics**：学术伦理与诚实底线——不臆造文献/数据/DOI/端点，区分「已验证」与「推测」。
- **a01 file-reading / a02 memory-pm**：涉及读文件或长期项目时自动触发。
- **light-orchestrator**：跨多阶段大任务 / "继续·刚断了·接手" 断点恢复时启动，逐阶段卡检查点、维护 .light/passport.yaml 台账。

核心红线：不编造（不可逾越）；论文图/数据图必须程序化生成、绝不 AI 生图；
写入的 API 端点须实测；受版权材料只存元数据/链接/笔记。
确认点用 light-orchestrator/scripts/run_checkpoint.py 聚合各技能 findings 做机器闸门，
critical fail 默认阻断，不靠"口头说跑了"。
"""

HOOK_EVENT = "SessionStart"


def build_output(payload: dict) -> dict:
    """构造 Claude Code SessionStart hook 的输出 JSON。

    协议：hookSpecificOutput.additionalContext 会被注入到模型上下文。
    payload 是 harness 传入的 hook 输入（含 session_id/source 等），这里不强依赖其字段，
    仅用于未来可能的来源判别；当前对所有 source 注入同一份常驻纪律。
    """
    return {
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT,
            "additionalContext": RESIDENT_CONTEXT,
        }
    }


def run(stdin_text: str) -> str:
    """读 hook 输入文本 → 返回应打印到 stdout 的 JSON 文本。
    解析失败不抛：降级为仍输出常驻纪律（保证纪律一定注入，错误不静默吞但不阻断会话）。"""
    try:
        payload = json.loads(stdin_text) if stdin_text.strip() else {}
        if not isinstance(payload, dict):
            payload = {}
    except (json.JSONDecodeError, ValueError):
        sys.stderr.write("[session_start_resident] hook 输入非合法 JSON，降级仍注入常驻纪律\n")
        payload = {}
    return json.dumps(build_output(payload), ensure_ascii=False)


def _selftest() -> int:
    failures = []

    def check(cond, msg):
        if not cond:
            failures.append(msg)

    # 1. 合法 SessionStart 输入 → 结构正确、含常驻清单
    out = run(json.dumps({"session_id": "x", "source": "startup",
                          "hook_event_name": "SessionStart"}))
    d = json.loads(out)
    hso = d.get("hookSpecificOutput", {})
    check(hso.get("hookEventName") == "SessionStart", "hookEventName 应为 SessionStart")
    ctx = hso.get("additionalContext", "")
    for tok in ("a07", "a08", "a09", "a10", "orchestrator", "不编造", "run_checkpoint"):
        check(tok in ctx, f"注入上下文应含 {tok}")

    # 2. 空 stdin → 仍注入（降级不崩）
    out = run("")
    check("a08" in json.loads(out)["hookSpecificOutput"]["additionalContext"],
          "空输入应降级仍注入纪律")

    # 3. 非法 JSON → 不抛、仍注入
    out = run("not-json{{{")
    check("research-ethics" in json.loads(out)["hookSpecificOutput"]["additionalContext"]
          or "a10" in json.loads(out)["hookSpecificOutput"]["additionalContext"],
          "非法 JSON 应降级仍注入纪律")

    # 4. 输出必须是单个合法 JSON 对象（harness 要能解析）
    try:
        json.loads(run(json.dumps({"source": "resume"})))
    except Exception as e:  # noqa: BLE001
        check(False, f"输出应为合法 JSON：{e}")

    if failures:
        print("[selftest] session_start_resident SOME FAILED:")
        for f in failures:
            print("  -", f)
        return 1
    print("[selftest] session_start_resident ALL PASS（4 组断言）")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return _selftest()
    # 正常 hook 模式：读 stdin，输出注入 JSON
    print(run(sys.stdin.read()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
