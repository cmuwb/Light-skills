# -*- coding: utf-8 -*-
"""
skills._shared —— Light 技能包的跨技能地基契约层。

阶段0 地基:把"一句聊天 prose 交接"换成机器可读的结构化契约,
让下游技能(a01 passport 判定 / a07 证据-措辞门 / m07 draft-lint /
m10 引用支撑 / m14 审稿意见分类 / db09 记忆)按统一格式交接 findings。

对外稳定接口(阶段1 起按此 import 消费):

    from skills._shared import (
        Finding, GateResult, FindingsReport,   # 数据契约 (findings_schema)
        validate, SCHEMA_ID,                    # 校验 / schema 标识
        run_gates, run_gates_to_json,           # gate 聚合执行器 (gate_runner)
    )

或在技能脚本内(与 _shared 不在同包时)按路径 import:

    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "_shared"))
    from findings_schema import FindingsReport, GateResult, Finding
    from gate_runner import run_gates

依赖:纯 Python stdlib,无网络、无外部数据、无第三方包。
"""
from .findings_schema import (
    Finding,
    GateResult,
    FindingsReport,
    validate,
    SCHEMA_ID,
    VALID_STATUS,
    VALID_VERDICT,
    VALID_SEVERITY,
)
from .gate_runner import run_gates, run_gates_to_json, GateFn
from .evidence_contract import (
    grade_evidence,
    allowed_verb_tier,
    lint_wording,
    build_evidence_json,
)
from .semantic_sim import (
    similarity,
    most_similar,
    is_near_duplicate,
    set_embed_fn,
    set_llm_scorer,
)
from .visual_qa import (
    detect_geometry_issues,
    visual_qa_rubric,
    qa_report,
)

__all__ = [
    # findings 契约
    "Finding",
    "GateResult",
    "FindingsReport",
    "validate",
    "SCHEMA_ID",
    "VALID_STATUS",
    "VALID_VERDICT",
    "VALID_SEVERITY",
    "run_gates",
    "run_gates_to_json",
    "GateFn",
    # 证据强度契约
    "grade_evidence",
    "allowed_verb_tier",
    "lint_wording",
    "build_evidence_json",
    # 语义相似度契约
    "similarity",
    "most_similar",
    "is_near_duplicate",
    "set_embed_fn",
    "set_llm_scorer",
    # 视觉 QA 契约
    "detect_geometry_issues",
    "visual_qa_rubric",
    "qa_report",
]

__schema_version__ = SCHEMA_ID  # "light.findings.v1"
