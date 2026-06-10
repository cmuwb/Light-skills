---
name: light-backend-coding
description: 后端代码编写、逻辑强、安全性高、可读性好、版本控制、代码审查。当任务需要写实验代码、模型代码、数据处理代码、可视化代码、后端接口或系统逻辑时使用。要求逻辑清晰、安全、可读、可维护、便于复现/扩展/部署。支持 Git 版本管理、代码审查、注释规范、README、依赖管理、环境配置、运行说明与项目结构整理。
user-invocable: false
---

# 后端代码编写与审查

## 写代码前
读现有代码，匹配项目的风格、约定与依赖库，不擅自引入新框架(CONVENTIONS)。明确输入输出、边界条件、复现要求(种子/版本)。

## 代码质量标准
- **逻辑清晰**：单一职责、小函数、清楚的数据流。
- **安全**：参数化查询、输入校验、异常处理；不硬编码密钥(走环境变量/配置)；不回显敏感值(a10)。
- **可读**：命名达意、注释解释"为什么"而非"是什么"、与周围代码同密度。
- **可维护/可扩展**：低耦合、配置化(Hydra)、避免过度工程。
- **可复现**：固定随机种子、锁依赖版本、记录环境、确定性数据划分。

## 工程实践
- **版本控制**：Git；功能分支不直接推 main；有意义的提交信息；仅用户明确要求才提交/推送。
- **依赖/环境**：
  - uv（推荐，Rust 实现快 10-100x）：`uv init` → `uv add <pkg>` → `uv lock`/`uv sync`(按 `uv.lock` 精确复现) → `uv run`；`uv python pin 3.11` 锁 Python 版本。
  - Poetry：`poetry add` → `poetry install`(按 `poetry.lock`)；依赖放 PEP 621 `[project.dependencies]`，dev 依赖入 `[tool.poetry.group.dev]`；CI 固定 Poetry 版本。
  - 始终提交 lock 文件，CI 用 `uv sync`/`poetry install` 还原确定性环境。
- **测试**：pytest——文件 `test_*.py`、函数 `test_*` 自动发现，纯 `assert`；`@pytest.fixture`(scope function/module/session) 做依赖注入，`@pytest.mark.parametrize` 跑多组输入，共享 fixture 放 `conftest.py`。新功能/修 bug 先配测试，改完跑 `pytest -x` 验证。覆盖率 `pytest --cov=pkg --cov-report=term-missing`，CI 出 `--cov-report=xml`。
- **质量门**：
  - Ruff：`[tool.ruff.lint]` 用 `select`/`extend-select`(如加 `B`)/`ignore`(如 `E501`)；`[tool.ruff]` 设 `line-length`/`target-version`；CI 分别跑 `ruff check .` 与 `ruff format --check .`(linter 与 formatter 是两个命令)。
  - pre-commit：`.pre-commit-config.yaml` 的 `repos` 用 `rev` 锁版本(tag/SHA，勿用浮动分支)；接 `astral-sh/ruff-pre-commit` 的 `ruff`(`args:[--fix]`)+`ruff-format`；`pre-commit install` 启用，CI 跑 `pre-commit run --all-files`。
  - SonarQube(必要时)：`sonar-project.properties` 设 `sonar.sources`/`sonar.tests`/`sonar.python.coverage.reportPaths=coverage.xml`；Quality Gate 卡阈值；token 走 secrets。
- **CI**：GitHub Actions 放 `.github/workflows/*.yml`；`actions/checkout@v6` + `actions/setup-python@v6`(`cache:"pip"`，缓存默认关须显式开)；`strategy.matrix.python-version` 多版本并行；典型流水线 checkout → 装依赖 → `ruff check` → `pytest`；secrets 用 `${{ secrets.X }}` 注入。
- **资产清单防漂移**：当仓库有 `WHATS_INCLUDED.md` / 资产索引 / manifest 这类人工清单时，新增脚本或模板不能只更新文件本身；要加 CI 校验防漏登。校验器应解析清单中的 canonical 区段/表格，按精确键（如 `(skill_slug, script_name)`）检查缺失、重复、陈旧项；不要用全文件 basename 字符串匹配，否则模板区的顺手提及或同名脚本会造成假通过。检测入口也要用 AST/结构化方式（如真实 `if __name__ == "__main__"`），不要只搜 `__main__` 字符串。补齐覆盖后及时把“缺 selftest warning”升级为 hard gate，防止后续回退。
- **脚本自测入口治理**：给技能脚本补自测时优先新增显式 `--selftest`/兼容别名，保持原 CLI 行为不破坏；自测必须离线、用合成数据或 `TemporaryDirectory`，包含真实断言，并清理生成物。对可选依赖（如外部二进制、网络服务、重型解释库）采用“可用则验证、不可用则断言降级路径”的策略，不把缺环境当作失败。
- **文档**：README(安装/运行/复现命令)、关键模块注释、运行说明。

## 调试与审查
- **系统化调试(systematic-debugging)**：动手前先定位根因——①逐字读错误/栈/行号 ②稳定复现 ③查最近改动(git diff/新依赖/环境) ④多组件系统在各边界加埋点定位是哪层断 ⑤反向追踪数据流到源头，在源头修而非症状处修。提单一假设、一次只改一个变量验证；先写失败测试再修。连修 3 次仍失败→停手质疑架构，这是结构问题不是 bug。
- **自我代码审查(requesting/receiving-code-review 视角)**：审查维度按严重度分级——Critical(立即修)/Important(下个任务前修)/Minor(记录待后)；评估每条建议的五查：对本库技术正确吗、会破坏现有功能吗、当前实现为何这么写、跨平台/版本可行吗、有完整上下文吗；加 YAGNI 检查(grep 实际用法，无人用就别加)。回应技术化、动作导向，不做表演性赞同。
- **改进架构(improve-codebase-architecture)**：用"删除测试"诊断——设想删掉某模块，复杂度消失=穿透层(浅，可吸收)，复杂度在多个调用方重现=深模块(值得留)。把浅模块改造成"小接口藏大实现"的深模块，集中知识、保证局部性；"接口即测试面"。
- **拆子任务(subagent-driven-development 思路)**：每任务给全新隔离上下文(只传必要信息不传会话史)，做完先过规格符合性审查再过代码质量审查(顺序不可乱)，发现问题回修复审循环；不并行派多个实现。
- **收尾分支(finishing-a-development-branch)**：合并前必须全测试通过；顺序为合并→在结果上重跑测试→移除 worktree→删分支(反了 `git branch -d` 会失败)；丢弃工作需显式确认，无请求不 force-push。

## 安全提示
创建网络暴露的接口/服务时，若无鉴权必须主动指出安全影响(security_awareness)，不静默上线无认证服务。

## 产出
可运行代码 + 测试 + 依赖/环境说明 + README + 运行命令。结构交 a06 规整。
起步可直接复制同目录 `assets/project-scaffold/`（含 `pyproject.toml`/`.pre-commit-config.yaml`/CI/示例模块+测试 + `CODE_REVIEW_CHECKLIST.md` + `scripts/`(边界调试埋点)，版本号已实测、`pytest` 实跑通过）。
推荐 TDD(test-driven-development)：先写最小失败测试并**亲眼看它失败**(确认是功能缺失而非拼写错)→ 写最简实现转绿 → 绿灯后才重构；无失败测试不写生产代码。

代码取向对照（最小够用 vs 过度工程；源头校验 vs 症状补丁）：

```python
# Bad：过度工程——测试只要求重试 3 次，却预先堆了一堆没人用的旋钮(YAGNI)
def retry(fn, max_retries=3, backoff="exponential", on_retry=None, jitter=True): ...

# Good：刚好让当前测试通过，需求长出来再加参数
def retry(fn, attempts=3):
    for i in range(attempts):
        try:
            return fn()
        except Exception:
            if i == attempts - 1:
                raise
```

```python
# Bad：症状处补丁——坏值已传到下游，每个用到的地方各打一个补丁
def report(scores):
    scores = [0 if s != s else s for s in scores]  # 这里擦 NaN
    ...
# 别处又得再擦一次，根因(产生 NaN 的源头)没动，补丁会越长越多

# Good：在数据进入系统的源头校验/修复一次，下游干净(systematic-debugging Phase 1.5)
def load_scores(raw):
    scores = parse(raw)
    if any(s != s for s in scores):       # 源头发现即拒绝
        raise ValueError("输入含 NaN，拒绝在源头")
    return scores
```

## 衔接
实现 m05 方案与 m02 流水线；优先复用 db03 方法卡的 `implementation_repo`（已验证的官方实现/库，如 HuggingFace Transformers、scikit-learn、xgboost/lightgbm、diffusers）而非从零造轮子；产出供 m06 分析；代码版本登记 db09；系统级设计交 a04。

---
工具硬信息(真实端点/参数/配置/工作流)见同目录 `references.md`。
深用专题：TDD 红旗与合理化反驳表见 `references/tdd_redflags.md`；系统化调试四阶段+边界埋点见 `references/debug_protocol.md`（配套可跑模板 `assets/project-scaffold/scripts/debug_instrument.sh` 与 `boundary_trace.py`）；自审清单 `assets/project-scaffold/CODE_REVIEW_CHECKLIST.md`。
资产清单/manifest 防漂移校验模式见 `references/asset_manifest_governance.md`。
