---
name: light-project-structure
description: 规范整洁的项目文件夹整理。当任务涉及新建项目、整理已有项目结构、规整文件命名与版本时使用。规划 data、src、models、results、figures、docs、paper、ppt、patent、software-copyright、experiments、logs、configs、references、assets、notebooks 等目录，保证结构清晰、命名规范、版本可追踪，便于写论文、答辩、申请软著专利与复现实验。
user-invocable: false
---

# 项目文件夹规范整理

## 标准科研项目骨架
```
project-name/
├── data/            原始/中间/处理后数据（大文件走 DVC）
│   ├── raw/ interim/ processed/ external/
├── src/             源代码
├── models/          模型权重与定义
├── results/         实验结果（指标、输出文件）
├── figures/         论文/报告用图
├── docs/            项目文档
├── paper/           论文（LaTeX/Word 工程）
├── ppt/             演示文稿
├── patent/          专利材料
├── software-copyright/  软著材料
├── experiments/     实验脚本与配置（按实验编号）
├── logs/            运行日志（MLflow/W&B 本地）
├── configs/         配置（Hydra yaml）
├── references/      文献库（Zotero 导出/.bib）
├── assets/          图标/模板/素材
├── notebooks/       探索性分析
├── README.md  CHANGELOG.md  .gitignore  pyproject.toml/environment.yml
```

数据分层沿用 Cookiecutter Data Science：`raw/`(原始不可变) `interim/`(中间) `processed/`(建模用最终) `external/`(第三方源)。notebooks 用"编号-缩写-描述"命名（如 `1.0-jl-eda.ipynb`）。

## 数据流即 DAG（核心方法）

把整个项目想成一张**有向无环图**：节点是数据/产物，边是确定性变换脚本。沿三条铁律组织目录：

1. **raw 不可变（immutable）**：`data/raw/` 一旦落地永不就地修改、永不被脚本写回。任何清洗/转换都读 raw、写 `interim/` 或 `processed/`。这样原始事实始终可回溯，DAG 有可信源头。
2. **每个产物都能从上游重算**：`processed/`、`models/`、`results/`、`figures/` 都是 DAG 的下游节点，删掉也能由"上游数据 + 代码 + params"重新生成——因此它们进 `.gitignore`/DVC，不进 Git 文本库。能重算的不入库，是 DAG 思路的直接推论。
3. **notebooks 拆探索 vs 报告**：`notebooks/exploratory/`（草稿、可乱、编号命名 `1.0-jl-eda.ipynb`）与 `notebooks/reports/`（干净、可重跑、产出对外图表）分流。探索性 notebook 不进 DAG 关键路径；定稿逻辑要下沉到 `src/`，被 notebook 和管线共同 import，避免"逻辑只活在某个 cell 里"。

用 `dvc.yaml` 把这张 DAG 显式声明出来（stage 的 `deps`→`outs` 就是图的边），`dvc repro` 据此只重跑受影响的下游节点；`dvc dag` 可打印依赖图。

## 命名规范
- 目录/文件用小写+连字符或下划线，不用空格中文。
- 实验/版本带日期或序号：`exp_004_ablation`, `paper_v3`, `fig3_ablation_v2`。
- 数据文件含版本/划分标记；结果文件名映射到实验编号，可追溯。

## 整理动作
1. 盘点已有项目（借 repo-intake-and-plan 思路）：先读 README→扫 setup 脚本与文档化命令→把工作流归类为 推理/训练/评估，再据此给散落文件归位。
2. 新项目骨架：**首选 `scripts/scaffold.py`**——一条命令建全树 + 拷模板 + 可选 `--dvc/--poetry`：
   `python scripts/scaffold.py ./my-proj --name my-proj --poetry --dvc`（生成 data 四分层 + notebooks 探索/报告分流 + src 包 + 落地 6 模板；目标非空需 `--force`）。或用 CCDS（`pipx install cookiecutter-data-science` 后 `ccds`）；或按上面骨架手工生成。无论哪种，都要落 README/CHANGELOG/PROJECT_PLAN/.gitignore/.editorconfig/pyproject.toml。
3. 重命名规范化→补 README/CHANGELOG→产出"文件归位说明"（借 handoff 结构：Key Decisions 表 + 失败尝试 + 警告）。

## 版本与依赖
- Git 管文本，DVC 管大文件：`dvc init`→`dvc add data/x.csv`(生成 `.dvc` 小文件并自动写 .gitignore)→`git add *.dvc .gitignore`→`dvc remote add -d storage s3://...`→`dvc push`。拉取：`git pull && dvc pull`。`.dvc`/`dvc.yaml`/`dvc.lock`/`.dvc/config` 入 Git，数据本体进 DVC。
- 多阶段管线用 `dvc.yaml`(stage 字段：`cmd` 必填、`deps`、`params`、`outs`、`metrics`、`plots`)，`dvc repro` 只重跑变更阶段（`frozen:true` 阶段跳过）；实验用 `dvc exp run/show/diff`。
- 依赖锁定用 Poetry：`poetry init`→`poetry add`→`poetry install`(有 lock 按精确版本装)。dev/test 依赖放 `[tool.poetry.group.dev.dependencies]`。应用项目提交 `poetry.lock`。

## 质量门（配置要点）
- Ruff（替代 flake8+black+isort）：`[tool.ruff]` 设 `line-length`/`target-version`，`[tool.ruff.lint]` 设 `select=["E","F","I","B"]`、`ignore=["E501"]`；命令 `ruff check --fix`、`ruff format`。注意 W/C901 默认不开。
- pre-commit：`.pre-commit-config.yaml` 列 `repos`(repo/rev/hooks/id)，`rev` 钉死 tag/SHA；通用 hook 用 trailing-whitespace、end-of-file-fixer、check-yaml；接 `astral-sh/ruff-pre-commit`(ruff + ruff-format)。装：`pre-commit install`，首次 `pre-commit run --all-files`。
- EditorConfig：`.editorconfig` 顶部 `root=true`；`[*]` 设 charset/end_of_line/indent；`[Makefile]` 单列 `indent_style=tab`。
- .gitignore：用 GitHub Python 模板（`__pycache__/`、`.venv`、`.pytest_cache/`、`.ruff_cache/`、`.mypy_cache/`、`build/`/`dist/` 等）；DVC 管的数据目录交给 DVC 自动写，勿手写冲突；lock 文件按项目类型决定是否提交（应用别忽略）。
- 任务运行器二选一：团队已用 make 给 Makefile(`make data`/`make train`)；要跨平台一致+可读性给 Taskfile(`Taskfile.yml`，sources/generates 做 checksum 跳过、`task -l`/`-w`)。

## 与项目库对应
目录结构与 db09 project_card 的各 status 字段一一对应（paper_status↔paper/，code_status↔src/，data_status↔data/…），便于 a02 跟踪进度。

## 现成模板（本技能目录 `templates/`，可直接复制使用）
- `scripts/scaffold.py` — **一条命令生成全套骨架**：建标准目录树 + 拷下面 6 个模板到项目根（去 `.template` 后缀）+ 写 `src/<module>/__init__.py`；`--poetry` 加写 `pyproject.toml`（Poetry+Ruff），`--dvc` 加写 `dvc.yaml`（有 dvc 则 `dvc init`），`--force` 覆盖非空目录。空目录补 `.gitkeep`。已实测可跑（synth 自测：建树→解析 pyproject→非空守卫均通过）。
- `templates/PROJECT_STRUCTURE.md` — 科研项目标准目录结构说明 + 命名规范 + 与 db09 字段对应 + 生成方式。
- `templates/README.template.md` — README 模板（状态表/环境/目录/数据/复现/结果/引用）。
- `templates/PROJECT_PLAN.template.md` — 实现计划模板（借 writing-plans：2–5 分钟可勾选任务 + No-Placeholders 强制规则 + 验收/前置/失败尝试/关键决策/阻塞）。
- `templates/CHANGELOG.template.md` — CHANGELOG 模板（Keep a Changelog + SemVer）。
- `templates/python-research.gitignore` — Python 科研项目 .gitignore，基线取自 GitHub 官方 `github/gitignore` 的 Python.gitignore（raw 实测 HTTP 200 @2026-06-06），末尾补充模型权重/日志/wandb/mlruns 等科研条目；复制为根目录 `.gitignore`。
- `templates/editorconfig.template` — EditorConfig 模板；复制为根目录 `.editorconfig`。
- `templates/pre-commit-config.template.yaml` — pre-commit 质量门模板（pre-commit-hooks 的 trailing-whitespace/end-of-file-fixer/check-yaml + ruff-pre-commit 的 ruff `--fix`/ruff-format，rev 钉死 tag，用 `pre-commit autoupdate --freeze` 维护）；复制为根目录 `.pre-commit-config.yaml`，仅在 git 仓库内 `pre-commit install` 后生效。

新建项目时优先 `python scripts/scaffold.py <dir> [--poetry --dvc]` 一步到位；或手工把上述文件复制到项目根（gitignore/editorconfig 去掉模板后缀），填充 README/CHANGELOG/PROJECT_PLAN 中的 `{{占位符}}` 即可。

## 产出
规整后的目录树 + 上面 `templates/` 的 README/CHANGELOG/.gitignore/.editorconfig 落地文件 + 一份"文件归位说明"。

## 衔接
为 m05/a03/a04 提供落地结构；为 m15(软著专利)、m07(论文)、m16(PPT) 预留对应目录；状态同步 a02/db09。
整理任务量大时按"可独立完成+带验收标准+标依赖顺序"拆解（借 to-issues 的垂直切片思路：每个任务是一条端到端可独立认领的路径，而非横向按层切）；复杂整理先出"精确路径+具体动作+验证步骤"的计划再执行，写到无上下文者也能照做的程度（借 writing-plans，任务粒度 2–5 分钟）。复现/审计场景固定 `repro_outputs/` 归档每次跑的结果，落 verified/partial/blocked 三态标记 + 输出 + `PATCHES.md`（改了哪些文件）+ 假设与阻塞清单（借 minimal-run-and-audit）。

> 工具与方法的可核查细节（真实命令/配置/端点/链接）见同目录 `references.md`；现成可复制模板见同目录 `templates/`。
