#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""schema_lint.py — schema 设计 + 迁移锁安全的可执行检查（把 prose 规则编译成 Squawk 式 linter）。

为什么有这个脚本（补 a04 与 Squawk/Atlas 最大段位差）
----------------------------------------------------
SKILL/references.md 大篇幅讲迁移锁安全（CREATE INDEX CONCURRENTLY、ADD COLUMN DEFAULT 锁表、
ADD CONSTRAINT 须 NOT VALID）与 RLS 性能五条、设计规范（表要 PK、FK 要索引、要审计列），但此前
**全是 prose 提醒，零执行**——竞品 Squawk/Atlas 是真把这些规则编译成 DDL 解析器执行。本脚本把
已写好的规则落成确定性检查，让 a04 的"迁移安全/RLS 安全"从口号变成可跑的产出门禁。

两种输入
--------
  --spec schema.yaml ：er_diagram.py 同款 YAML（扩展 fk_to/indexes/rls/policies/sensitive 字段），
                       做**设计期 lint**：表无 PK、FK 无索引、缺审计列、rls:true 无 policy、
                       policy 列未建索引（RLS 性能坑 171ms→0.1ms）、PII 列未开 RLS（合规）。
  --ddl migration.sql ：解析 CREATE/ALTER DDL，做**迁移锁安全 lint**（Squawk 核心）：
                       CREATE INDEX 缺 CONCURRENTLY、ADD COLUMN 带 DEFAULT、ADD CONSTRAINT 缺
                       NOT VALID、ALTER COLUMN TYPE 改类型锁表。

每条告警附 severity + references.md 锚点。critical/major 命中→退出码 1，出 light.findings.v1
（挂 _shared/findings_schema）接 a08/orchestrator 闸门。

⚠ 诚实边界：YAML 设计 lint 依赖你按扩展 schema 标了 fk_to/indexes/policies；DDL lint 是正则解析
  （非完整 SQL parser），抓常见高危形态，会漏报复杂语句，**不替代生产迁移的人工审 + 灰度**。

用法：
  python schema_lint.py --spec schema.yaml
  python schema_lint.py --ddl migration.sql --json
  python schema_lint.py --selftest
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)                       # 复用 er_diagram.load_spec
sys.path.insert(0, os.path.join(_HERE, "..", "..", "_shared"))
try:
    from er_diagram import load_spec               # noqa: E402
    _HAS_LOAD = True
except Exception:
    _HAS_LOAD = False
try:
    from findings_schema import Finding, GateResult, FindingsReport  # noqa: E402
    _HAS_FINDINGS = True
except Exception:
    _HAS_FINDINGS = False

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

_REF = "references.md"
_AUDIT_COLS = ("created_at", "updated_at")


def _has_key(col: dict, k: str) -> bool:
    key = str(col.get("key", "")).upper()
    return k in [x.strip() for x in key.replace("/", ",").split(",")]


def lint_spec(spec: dict) -> list:
    """设计期 lint：吃 er_diagram 同款 YAML（含扩展字段）。"""
    issues = []
    entities = (spec or {}).get("entities", {}) or {}
    for ename, ent in entities.items():
        cols = ent.get("columns", []) or []
        colnames = [c.get("name") for c in cols]
        indexes = set(ent.get("indexes", []) or [])
        # PK 也算"有索引"
        pk_cols = {c.get("name") for c in cols if _has_key(c, "PK")}
        indexed = indexes | pk_cols

        # 1. 表无 PK
        if not pk_cols:
            issues.append({"loc": f"entity:{ename}", "code": "NO-PK", "severity": "major",
                           "msg": f"表 {ename} 无主键（PK）——每表应有主键，否则无法稳定定位行/复制/分区。",
                           "ref": f"{_REF}#表设计"})
        # 2. FK 列无索引
        for c in cols:
            is_fk = _has_key(c, "FK") or bool(c.get("fk_to"))
            if is_fk and c.get("name") not in indexed:
                issues.append({"loc": f"{ename}.{c.get('name')}", "code": "FK-NO-INDEX",
                               "severity": "major",
                               "msg": f"外键列 {ename}.{c.get('name')} 无索引——FK 关联查询/级联删全表扫，"
                                      f"应建索引。", "ref": f"{_REF}#索引"})
        # 3. 缺审计列
        missing_audit = [a for a in _AUDIT_COLS if a not in colnames]
        if missing_audit:
            issues.append({"loc": f"entity:{ename}", "code": "NO-AUDIT-COLS", "severity": "minor",
                           "msg": f"表 {ename} 缺审计列 {missing_audit}——建议加 created_at/updated_at 便于追溯。",
                           "ref": f"{_REF}#审计列"})
        # 4. rls:true 但无 policy
        rls_on = bool(ent.get("rls"))
        policies = ent.get("policies", []) or []
        if rls_on and not policies:
            issues.append({"loc": f"entity:{ename}", "code": "RLS-NO-POLICY", "severity": "critical",
                           "msg": f"表 {ename} 开了 RLS(rls:true) 但无任何 policy——RLS 开启后默认拒绝所有访问，"
                                  f"无 policy = 数据完全不可达或越权风险，必须定义 policy。",
                           "ref": f"{_REF}#RLS"})
        # 5. policy 引用列未建索引（RLS 性能坑）
        for p in policies:
            for pcol in (p.get("on_columns", []) or []):
                if pcol not in indexed:
                    issues.append({"loc": f"{ename}.policy:{p.get('name','?')}",
                                   "code": "POLICY-COL-NO-INDEX", "severity": "major",
                                   "msg": f"表 {ename} 的 RLS policy 引用列 {pcol} 未建索引——policy 列无索引"
                                          f"会让每次访问全表扫(实测 171ms→<0.1ms)，必须为 policy 过滤列建索引。",
                                   "ref": f"{_REF}#RLS性能"})
        # 6. PII/PHI 列但未开 RLS（合规）
        sens = [c.get("name") for c in cols
                if str(c.get("sensitive", "")).lower() in ("pii", "phi")]
        if sens and not rls_on:
            issues.append({"loc": f"entity:{ename}", "code": "PII-NO-RLS", "severity": "major",
                           "msg": f"表 {ename} 含敏感列 {sens}(PII/PHI) 但未开 RLS——含人类受试者个人/健康信息"
                                  f"的表应开行级安全并限定可见范围(IRB/GDPR/合规)。",
                           "ref": f"{_REF}#敏感列"})
    return issues


def lint_ddl(sql: str) -> list:
    """迁移锁安全 lint（Squawk 式）：正则解析 CREATE/ALTER 语句标高危锁操作。"""
    issues = []
    # 去注释，按 ; 切语句
    sql_nc = re.sub(r"--[^\n]*", "", sql)
    statements = [s.strip() for s in sql_nc.split(";") if s.strip()]
    for st in statements:
        flat = re.sub(r"\s+", " ", st).strip()
        up = flat.upper()
        # 1. CREATE INDEX 缺 CONCURRENTLY
        if re.match(r"CREATE\s+(UNIQUE\s+)?INDEX", up) and "CONCURRENTLY" not in up:
            issues.append({"loc": flat[:60], "code": "INDEX-NOT-CONCURRENT", "severity": "major",
                           "msg": "CREATE INDEX 未用 CONCURRENTLY——在大表上会锁写阻塞业务，"
                                  "迁移中应 CREATE INDEX CONCURRENTLY（注意不能在事务块内）。",
                           "ref": f"{_REF}#迁移锁安全"})
        # 2. ADD COLUMN 带 DEFAULT（旧版 PG 会重写全表）
        if re.search(r"ALTER\s+TABLE.+ADD\s+COLUMN.+DEFAULT", up):
            issues.append({"loc": flat[:60], "code": "ADD-COLUMN-DEFAULT", "severity": "major",
                           "msg": "ADD COLUMN 带 DEFAULT——PG 11 前会重写整表并 AccessExclusiveLock 锁表，"
                                  "大表上应分步：先加可空列→分批回填→再设默认/约束。",
                           "ref": f"{_REF}#迁移锁安全"})
        # 3. ADD CONSTRAINT (FK/CHECK) 缺 NOT VALID
        if re.search(r"ADD\s+CONSTRAINT", up) and re.search(r"FOREIGN\s+KEY|CHECK", up) \
                and "NOT VALID" not in up:
            issues.append({"loc": flat[:60], "code": "CONSTRAINT-NOT-VALID", "severity": "major",
                           "msg": "ADD CONSTRAINT(FK/CHECK) 未用 NOT VALID——会全表扫描校验并锁表，"
                                  "应先 ADD ... NOT VALID 再 VALIDATE CONSTRAINT（后者锁更轻）。",
                           "ref": f"{_REF}#迁移锁安全"})
        # 4. ALTER COLUMN TYPE（改类型重写锁表）
        if re.search(r"ALTER\s+(COLUMN\s+)?\w+\s+TYPE|ALTER\s+COLUMN.+SET\s+DATA\s+TYPE", up):
            issues.append({"loc": flat[:60], "code": "ALTER-COLUMN-TYPE", "severity": "major",
                           "msg": "ALTER COLUMN TYPE 改类型——通常重写整表并锁表，"
                                  "大表应新增列+回填+切换而非直接改类型。",
                           "ref": f"{_REF}#迁移锁安全"})
    return issues


def _aggregate(issues: list, target: str) -> dict:
    by = {"critical": 0, "major": 0, "minor": 0}
    for i in issues:
        by[i["severity"]] = by.get(i["severity"], 0) + 1
    return {"target": target, "n_issues": len(issues), "by_severity": by, "issues": issues}


def to_findings(rep: dict) -> dict:
    if not _HAS_FINDINGS:
        gates = [{"gate": i["code"], "status": "fail" if i["severity"] in ("critical", "major") else "warn",
                  "severity": i["severity"],
                  "findings": [{"loc": i["loc"], "issue": i["msg"], "fix": i.get("ref", ""), "rule": i["code"]}]}
                 for i in rep["issues"]]
        verdict = "fail" if (rep["by_severity"].get("critical") or rep["by_severity"].get("major")) \
            else ("warn" if rep["issues"] else "pass")
        return {"schema": "light.findings.v1", "producer": "a04", "target": rep["target"],
                "verdict": verdict, "gates": gates, "summary": f"schema lint:{rep['n_issues']}问题",
                "fresh_evidence": True, "_degraded": True}
    r = FindingsReport(producer="a04", target=rep["target"], fresh_evidence=True,
                       summary=f"schema/迁移 lint：{rep['n_issues']} 问题")
    if not rep["issues"]:
        r.gates.append(GateResult("schema_lint", "pass", "info"))
    for i in rep["issues"]:
        # major 也阻断（迁移锁/RLS 性能是真会出事故的）
        status = "fail" if i["severity"] in ("critical", "major") else "warn"
        sev = "critical" if i["severity"] == "critical" else ("major" if i["severity"] == "major" else "minor")
        r.gates.append(GateResult(i["code"], status, sev,
                                  [Finding(i["loc"], i["msg"], fix=i.get("ref", ""), rule=i["code"])]))
    return r.finalize().to_dict()


def to_markdown(rep: dict) -> str:
    b = rep["by_severity"]
    lines = [f"# schema/迁移 lint — {rep['target']}：{rep['n_issues']} 问题"
             f"（critical={b.get('critical',0)} major={b.get('major',0)} minor={b.get('minor',0)}）\n"]
    if not rep["issues"]:
        lines.append("✓ 未发现设计/迁移锁高危问题。")
    for i in rep["issues"]:
        lines.append(f"- [{i['severity']}] {i['code']} @ {i['loc']}：{i['msg']}  ({i.get('ref','')})")
    lines.append("\n> 正则/规则启发式，抓常见高危形态，不替代生产迁移人工审+灰度。")
    return "\n".join(lines)


def _selftest() -> int:
    print("### schema_lint 离线自测", file=sys.stderr)

    # --- 设计 lint：故意制造各类问题 ---
    bad_spec = {"entities": {
        "User": {  # 无 PK、含 PII 但无 RLS、缺审计列
            "columns": [{"name": "email", "type": "varchar", "sensitive": "pii"},
                        {"name": "org_id", "type": "int", "key": "FK", "fk_to": "Org.id"}],
        },
        "Doc": {  # rls 开但无 policy
            "rls": True,
            "columns": [{"name": "id", "key": "PK"}, {"name": "created_at"}, {"name": "updated_at"}],
        },
        "Audit": {  # rls + policy 但 policy 列未建索引
            "rls": True,
            "columns": [{"name": "id", "key": "PK"}, {"name": "tenant_id", "type": "int"},
                        {"name": "created_at"}, {"name": "updated_at"}],
            "policies": [{"name": "tenant_iso", "on_columns": ["tenant_id"]}],
        },
    }}
    issues = lint_spec(bad_spec)
    codes = {i["code"] for i in issues}
    print(to_markdown(_aggregate(issues, "spec")), file=sys.stderr)
    for need in ("NO-PK", "FK-NO-INDEX", "NO-AUDIT-COLS", "RLS-NO-POLICY",
                 "POLICY-COL-NO-INDEX", "PII-NO-RLS"):
        assert need in codes, f"{need} 未命中: {codes}"
    print("[1] 设计 lint 六类问题全命中 ... OK", file=sys.stderr)

    # 干净 spec：有 PK、FK 建索引、审计列齐、RLS 有 policy 且 policy 列有索引
    good_spec = {"entities": {"T": {
        "rls": True,
        "indexes": ["org_id", "tenant_id"],
        "columns": [{"name": "id", "key": "PK"}, {"name": "org_id", "key": "FK"},
                    {"name": "tenant_id"}, {"name": "created_at"}, {"name": "updated_at"}],
        "policies": [{"name": "iso", "on_columns": ["tenant_id"]}],
    }}}
    gi = lint_spec(good_spec)
    assert not gi, f"干净 spec 不应报: {[i['code'] for i in gi]}"
    print("[2] 干净 spec 零误报 ... OK", file=sys.stderr)

    # --- 迁移锁安全 lint：四类高危 ---
    bad_ddl = """
    CREATE INDEX idx_u_email ON users (email);
    ALTER TABLE users ADD COLUMN status int DEFAULT 0;
    ALTER TABLE posts ADD CONSTRAINT fk_u FOREIGN KEY (uid) REFERENCES users(id);
    ALTER TABLE logs ALTER COLUMN amount TYPE bigint;
    """
    di = lint_ddl(bad_ddl)
    dcodes = {i["code"] for i in di}
    print(to_markdown(_aggregate(di, "ddl")), file=sys.stderr)
    for need in ("INDEX-NOT-CONCURRENT", "ADD-COLUMN-DEFAULT", "CONSTRAINT-NOT-VALID", "ALTER-COLUMN-TYPE"):
        assert need in dcodes, f"{need} 未命中: {dcodes}"
    print("[3] 迁移锁 lint 四类高危全命中 ... OK", file=sys.stderr)

    # 安全的迁移：CONCURRENTLY + NOT VALID
    good_ddl = """
    CREATE INDEX CONCURRENTLY idx_u_email ON users (email);
    ALTER TABLE posts ADD CONSTRAINT fk_u FOREIGN KEY (uid) REFERENCES users(id) NOT VALID;
    """
    gd = lint_ddl(good_ddl)
    assert not gd, f"安全迁移不应报: {[i['code'] for i in gd]}"
    print("[4] 安全迁移(CONCURRENTLY/NOT VALID) 零误报 ... OK", file=sys.stderr)

    # findings 转换 + verdict
    f = to_findings(_aggregate(issues, "spec"))
    assert f["schema"] == "light.findings.v1" and f["verdict"] == "fail", f
    print("[5] findings verdict=fail ... OK", file=sys.stderr)

    print("[selftest] PASS schema_lint offline")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="schema 设计 + 迁移锁安全 lint")
    ap.add_argument("--spec", help="er_diagram 同款 YAML/JSON（设计 lint）")
    ap.add_argument("--ddl", help="迁移/DDL .sql（迁移锁安全 lint）")
    ap.add_argument("--json", action="store_true", help="输出 light.findings.v1 JSON")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest or (not args.spec and not args.ddl):
        return _selftest()

    issues, target = [], ""
    if args.spec:
        if not _HAS_LOAD:
            print("er_diagram.load_spec 不可用，无法解析 spec", file=sys.stderr)
            return 2
        with open(args.spec, encoding="utf-8") as f:
            spec = load_spec(f.read())
        issues += lint_spec(spec)
        target = args.spec
    if args.ddl:
        with open(args.ddl, encoding="utf-8") as f:
            issues += lint_ddl(f.read())
        target = args.ddl if not target else f"{target}+{args.ddl}"
    rep = _aggregate(issues, target)
    print(json.dumps(to_findings(rep), ensure_ascii=False, indent=2) if args.json else to_markdown(rep))
    return 1 if (rep["by_severity"].get("critical") or rep["by_severity"].get("major")) else 0


if __name__ == "__main__":
    sys.exit(main())
