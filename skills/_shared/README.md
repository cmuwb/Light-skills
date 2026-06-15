# `skills/_shared` —— Light 跨技能地基契约层

阶段0 的地基。把"一句聊天 prose 总结"式的跨技能交接,换成**机器可读的结构化契约** `light.findings.v1`。下游技能(passport 判定、证据-措辞门、draft-lint、引用支撑、审稿意见分类、记忆)据此按统一格式交接 findings,不再靠自然语言传 verdict。

解决的病灶:病1(prose 交接)、病六(a01 passport 有确认点但 gate 没接线)、金矿3/4(findings 接口闭环 + 防陈旧证据)。

## 目录文件清单

| 文件 | 角色 | 说明 |
|------|------|------|
| `findings_schema.py` | 数据契约(地基契约4 之一) | 定义 `light.findings.v1` 的三个数据类 + JSON 序列化/反序列化/校验 |
| `gate_runner.py` | 执行器(地基契约4 之二) | `run_gates` 把多个 gate 函数聚合成一份 `FindingsReport` |
| `__init__.py` | 包入口 | 把上述符号提升到 `skills._shared` 命名空间,作为阶段1 的稳定 import 面 |
| `README.md` | 本文件 | 契约说明 / 函数清单 / 阶段1 消费方式 / 依赖降级矩阵 |

> 注:`findings_schema.py` 与 `gate_runner.py` 在各自 docstring 中自述为"地基契约4 之一/之二",即二者合起来构成阶段0 的 findings 交接契约。`_shared` 目录当前只含这两个契约脚本,`__init__.py`/`README.md` 为包装与文档,不是独立契约。

## 契约一:`findings_schema.py`

`light.findings.v1` 的数据形态:

```json
{"schema":"light.findings.v1","producer":"a08","target":"draft.md",
 "verdict":"pass|fail|warn",
 "gates":[{"gate":"evidence_wording","status":"fail","severity":"critical",
           "findings":[{"loc":"draft.md:42","issue":"...","fix":"..."}]}],
 "summary":"...","fresh_evidence":true}
```

数据类与关键函数:

| 符号 | 类型 | 作用 |
|------|------|------|
| `Finding(loc, issue, fix="", evidence=None, rule=None)` | dataclass | 单条发现:定位 + 问题 + 修正(+ 可选证据/触发规则名) |
| `GateResult(gate, status="pass", severity="info", findings=[], note="")` | dataclass | 单个 gate 结果;构造期即校验 status/severity 合法性 |
| `GateResult.is_blocking()` | 方法 | 是否构成阻断(`fail` + `critical`) |
| `FindingsReport(producer, target, gates=[], verdict=None, summary="", fresh_evidence=False)` | dataclass | 一次交接的完整报告 |
| `FindingsReport.compute_verdict()` | 方法 | 推导整体裁定:任一 critical fail→`fail`;否则任意 fail/warn→`warn`;全 pass/skip→`pass` |
| `FindingsReport.worst_severity()` | 方法 | 所有非 pass gate 中最严重的 severity |
| `FindingsReport.finalize()` | 方法 | 把 verdict 落定为推导值(若未显式给定),返回自身 |
| `FindingsReport.to_json()` / `.to_dict()` | 方法 | 机读序列化(`ensure_ascii=False`) |
| `FindingsReport.from_json(s)` / `.from_dict(d)` | 静态 | 反序列化,内部调 `validate` |
| `validate(d)` | 函数 | 校验 dict 是否合法报告;schema 不符或缺必填字段抛 `ValueError` |
| `SCHEMA_ID` | 常量 | `"light.findings.v1"` |
| `VALID_STATUS / VALID_VERDICT / VALID_SEVERITY` | 常量 | 受控取值元组 |

取值约定:
- `status` ∈ `pass / fail / warn / skip`
- `verdict` ∈ `pass / fail / warn`
- `severity` ∈ `critical / major / minor / info`

## 契约二:`gate_runner.py`

把多个独立 gate 函数跑成一份统一报告。这是 **a01 passport 确认点判定的接线处**:passport 不再消费 prose verdict,改读本报告的 `verdict` 字段。

gate 函数契约(供消费技能实现):

```python
def my_gate(artifact) -> GateResult:
    # artifact 为任意被检查对象(路径/dict/文本),由 gate 自解释
    ...
    return GateResult("my_gate", "pass", "info")
```

关键函数:

| 符号 | 作用 |
|------|------|
| `run_gates(gate_fns, artifact, producer="gate_runner", target="", summary="", fresh_evidence=False) -> FindingsReport` | 顺序执行所有 gate,聚合成报告并 `finalize()` |
| `run_gates_to_json(gate_fns, artifact, **kw) -> str` | 同上但直接出 JSON 字符串 |
| `GateFn` | 类型别名 `Callable[[Any], GateResult]` |

诚实纪律(不静默吞错):
- gate 内部抛异常 → 捕获并记为 `status=fail / severity=critical` 的 GateResult,携带 traceback 作为 `evidence`,`rule="gate_runner.exception"`。
- gate 返回非 `GateResult` → 同样记为 critical fail。
- 任一 critical fail → 整体 `verdict=fail`。

## 阶段1 如何 import 消费

两种方式,按调用方与 `_shared` 的关系择一:

方式 A —— 作为包导入(调用方在 `skills` 包内、或 `skills` 的父目录在 `sys.path`):

```python
from skills._shared import (
    Finding, GateResult, FindingsReport, validate, SCHEMA_ID,
    run_gates, run_gates_to_json,
)

def evidence_gate(draft_path) -> GateResult:
    findings = []  # ... 检查逻辑
    return GateResult("evidence_wording", "pass", "info", findings)

report = run_gates([evidence_gate], "draft.md",
                   producer="a01", target="draft.md", fresh_evidence=True)
if report.verdict == "fail":
    handle_block(report)          # passport 在此判定确认点
payload = report.to_json()        # 交给 db09 记忆 / m14 审稿分类
```

方式 B —— 技能脚本独立运行(与 `_shared` 不同包,沿用现有脚本风格):

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "_shared"))
from findings_schema import FindingsReport, GateResult, Finding
from gate_runner import run_gates
```

> `gate_runner.py` 已同时支持两种 import(顶部 `try: from findings_schema ... except ImportError: from .findings_schema ...`),包模式与脚本模式都能跑。

消费侧契约要点:
- 产出方填 `producer`(自己技能号)、`target`(被检工件)、`fresh_evidence`(本轮证据是否新算,金矿4 防陈旧)。
- 消费方只读 `verdict` 做判定、读 `gates[].findings[]` 做定位修正,不解析 prose。
- 跨进程/跨会话交接一律走 `to_json()` / `from_json()`,不传 Python 对象。

## 依赖降级矩阵

| 依赖项 | 要求 | 缺失/降级时行为 |
|--------|------|----------------|
| Python | 3.7+(dataclass) | 实测 3.11.13 全绿;无 3.7 以下兼容承诺 |
| `findings_schema` | gate_runner 的硬依赖(同目录) | 找不到则 import 失败——这是契约骨架,不降级 |
| 网络 | 不需要 | 纯本地,无网络调用 |
| 外部数据/数据库 | 不需要 | 无外部读写 |
| 第三方包 | 无 | 仅 stdlib(`sys/json/argparse/dataclasses/typing/traceback`) |
| 上游 gate 函数抛异常 | —— | 不中断:转记为 critical fail + traceback,整体 verdict=fail |
| gate 返回类型不符 | 应返回 GateResult | 不静默:记为 critical fail |
| `verdict` 未显式给定 | —— | `finalize()`/`to_dict()` 自动按 gates 推导 |
| `stdout` 非 UTF-8(Windows 控制台) | —— | 两脚本顶部 `sys.stdout.reconfigure(encoding="utf-8")`,中文不乱码 |

## 自测

```
python skills/_shared/findings_schema.py --selftest   # 9 组断言,退出码 0/1
python skills/_shared/gate_runner.py     --selftest   # 7 组断言,退出码 0/1
```

无参数运行 `findings_schema.py` 默认也跑自测;`gate_runner.py` 同理。`findings_schema.py --validate FILE` 可校验一份外部 findings JSON。
