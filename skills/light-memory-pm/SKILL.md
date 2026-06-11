---
name: light-memory-pm
description: 上下文管理、记忆持久化与科研项目管理。当任务涉及长期项目、需要记住项目背景/进展/版本/偏好，或需要把项目拆成阶段任务时使用（常驻）。持续记住研究方向、已定 idea、数据、实验进度、论文/PPT/图表/代码版本、投稿记录、用户偏好、目标期刊。把项目拆成阶段任务并建立任务清单、时间线、里程碑、风险清单与版本记录。
user-invocable: false
---

# 上下文管理、记忆持久化与科研项目管理

## Hermes 会话链恢复
当用户说新窗口/昨天对话找不到、恢复后消息太少、或要求把长任务恢复到某个工作区时，不要只看最近一条 session 或默认列表；应检查 Hermes `state.db` 的 `parent_session_id`、`archived`、`cwd` 与消息计数，恢复完整压缩主链和相关子会话。具体可复用流程见 `references/hermes_session_lineage_recovery.md`。

## 持久化（用 Light 记忆系统 + 项目库 db09）
- 跨会话事实写入记忆文件(user/feedback/project/reference)，并在 MEMORY.md 加索引行。其中 **feedback 记忆槽的「跨项目过程教训」部分结构化落地为 db09 顶层 `lessons.md`**（与 `projects/` 平级，格式见下）；feedback 记忆文件本身仍存个人偏好类反馈。
- 项目级状态写入 db09 的 project_card：`project_name, goal, current_stage, confirmed_idea, data_status, method_status, experiment_status, paper_status, ppt_status, code_status, risk_list, next_actions, decision_log, version_history`。
- 相对日期一律转绝对日期再存。
- **两层记忆模型**（借 LangGraph checkpointer/Store 与 mem0 的作用域设计）：会话级状态(≈thread_id，短期、随会话压缩可丢)与项目级状态(≈跨会话的 Store/db09，长期、按"项目"namespace 持久)分开管理。关键事实即使能被自动抽取也要显式写入——自动记忆(mem0 式 LLM 抽取)会漏记，db09 是权威来源。

## 记忆写入机制（招牌功能，硬性定义）
四类记忆文件**存哪、什么格式、何时写、何时读**，照此执行，不得省略。

### 存哪（落盘路径）
全部存到 db09，每个项目一个独立目录（相对本技能目录为 `../../databases/db09-projects/projects/<project_name>/`）：
```
databases/db09-projects/projects/<project_name>/
├── project_card.md       项目卡：14 字段总览（next_actions 在此）
├── terminology.md        术语/指标/创新点统一定义表（供 a07）
├── decision_log.md       重大决策时间线
└── version_history.md    论文/PPT/图表/代码各版本记录
（可选子目录 literature/ reviews/ submissions/ 见 db09 README）
```
`<project_name>` 用短横线英文 slug（如 `dairygoat-detect-track`）。已存在实例可直接参考：`projects/dairygoat-detect-track/`（3 个文件齐全，version_history.md 待该项目首次出版本时补建）。

### 什么格式（四文件确切结构，模板见 db09 `project_card_template.md`）
1. **project_card.md** — 顶部 YAML frontmatter（`project_name` / `created` 绝对日期），正文 `# 项目卡：<中文标题>`，再用一个 ```yaml 代码块装 14 字段：`project_name, goal, current_stage, confirmed_idea, data_status, method_status, experiment_status, paper_status, ppt_status, code_status, risk_list, next_actions`，末两字段写 `decision_log: 见 decision_log.md`、`version_history: 见 version_history.md`。多行字段用 `|` 块标量。
2. **terminology.md** — Markdown 表：`| 类别 | 标准叫法 | 缩写 | 英文 | 备注 |`，类别取 方法/数据集/指标/创新点；创新点行标准措辞须与论文/PPT/软著一字对齐。
3. **decision_log.md** — 每行一条：`- [YYYY-MM-DD] 决策 — 理由 — 来源(m03/m04/m14…)`。只追加不改写，保留时间线。
4. **version_history.md** — 每行一条：`- [YYYY-MM-DD] 材料(论文/PPT/图/代码) vN — 变更摘要`，与 git tag 对齐（见下「管理工具映射」）。

## 该记什么
项目背景、研究问题、已确认 idea、数据情况、实验进度、论文/PPT/图表/代码各自版本、投稿与审稿记录、用户偏好(写作风格/工具/格式)、目标期刊、格式要求、重要决策(decision_log)。
**不记**：代码结构、git 历史、能从仓库直接看出的东西。

## 项目阶段拆解
把项目拆成：资料调研→idea 构思→方案确认→数据准备→实验实现→结果分析→论文写作→图表制作→投稿准备→答辩展示→成果转化。每阶段建：
- **任务清单**(可勾选)、**时间线/甘特**、**里程碑**、**风险清单**、**版本记录**。
- 落到工具时：一个阶段=一个里程碑(GitHub milestone，带 due 日期)，阶段内任务=带 `- [ ]` 复选框的条目，风险项打 `risk` 标记。`- [x]` 用于已完成项，便于自动统计进度。

## 管理工具映射（见 a09，具体用法见 references.md）
- **代码/文本/稿件版本→Git**：里程碑版本用带注释标签 `git tag -a v1.2.0 -m "..."`（注释标签才被 `git describe` 识别）；遵循 SemVer；论文/PPT 也打 tag（如 `submit-icml2026`）并与 version_history 对齐。CHANGELOG 按 Keep a Changelog（Added/Changed/Fixed/Removed + 日期）。大文件不进 Git，交 DVC。标签需 `git push --tags` 才上传。
- **数据/实验→DVC / MLflow / W&B**：DVC 用 `dvc add` 生成 `.dvc` 指针、`dvc.yaml` 定义 stage(cmd/deps/params/outs/metrics)、`dvc exp run`+`dvc metrics diff` 对比；data_status/experiment_status 直接挂 `.dvc`/`dvc.lock` 的 commit。MLflow 用 `start_run`+`log_param/log_metric/log_artifact`，run_id 串联 method/experiment 状态。W&B 用 `wandb.init/log`、Artifacts 做血缘、Sweeps 调超参；记 run URL。
- **文献→Zotero**：Web API 基址 `https://api.zotero.org`，`/users/<id>/items`、`/collections`，带 `Zotero-API-Version:3` 与 API key；可导出 BibTeX/CSL-JSON；写操作用 `If-Unmodified-Since-Version` 乐观锁，遵守 Backoff/Retry-After 退避。
- **项目知识→Obsidian / Notion / Logseq / Markdown**：Obsidian 用 frontmatter 承载 project_card 字段、Dataview 聚合成看板；Notion API(`/databases/{id}/query`，`Notion-Version` 头，约 3 req/s 限流)把字段映射成 database 属性；Logseq 用 journals 做 decision_log 时间线 + query 汇总未完成项。
- **进展→README + CHANGELOG**。

## 更新纪律（硬性）
每次完成：资料搜索、idea 修改、实验运行、论文修改、PPT 修改、投稿返修——**立即**更新 db09 对应字段与 decision_log，避免长期项目上下文丢失。

**触发→写入对照**：idea 定稿→改 `confirmed_idea` + 追加 decision_log；实验跑完→改 `experiment_status` + `next_actions`；论文/PPT/代码出新版→改对应 `*_status` + 追加 version_history（并打 git tag）；方案变更/取舍→追加 decision_log；新术语/指标/创新点定名→补 terminology.md。

**跨项目教训回写（节制，避免噪声）**：仅当某决策产生了**可跨项目复用的过程教训**——踩坑、被审稿/导师否掉、复现失败、某流程显著省时/避雷——才在追加 decision_log 的**同时**回写一条 lesson 到 db09 顶层 `lessons.md`（格式：`- [YYYY-MM-DD] 阶段/场景 — 做法 — 结果(有效|失败) — 适用条件 — 来源项目slug`）。日常项目内决策**不强制**回写。边界：方法选型事实归 db03 方法卡，个人偏好归 feedback 记忆，二者不进 lessons.md。

### 写入步骤示例（落地一次实验进展）
假设刚跑完检测 baseline，项目 `dairygoat-detect-track`：
1. **读现状**：Read `databases/db09-projects/projects/dairygoat-detect-track/project_card.md`，看 `experiment_status` 与 `next_actions` 当前值。
2. **改项目卡**：用 Edit 把 `experiment_status` 从「方案级…尚无真实实验数据」改为「E1 检测 baseline 已跑：YOLOv11 imgsz=1280，mAP@0.5:0.95=0.71（CherryChèvre 验证集）」；同步把 `next_actions` 第 1 条勾掉/替换为下一步。
3. **追加决策日志**：Edit `decision_log.md` 末尾加一行 `- [2026-06-06] 检测 baseline 定为 YOLOv11@1280 — mAP 0.71 优于 RT-DETR 0.68 且推理更快 — 来源 E1 实验`。
4. **记版本**：若产出可复现权重/代码 tag，Edit `version_history.md` 加 `- [2026-06-06] 代码 v0.2.0 — 检测 baseline 可复现，git tag v0.2.0`，并 `git tag -a v0.2.0 -m "det baseline"`。
5. **跨会话索引**：若涉及用户长期偏好/项目背景，另写入 Light 记忆文件并在 MEMORY.md 加索引行（见「衔接」）。
日期一律用绝对日期（今天=系统 currentDate），相对日期先换算。

## 会话开始时
先读项目库与记忆：定位 `databases/db09-projects/projects/<project_name>/project_card.md`，**优先读 `next_actions` 字段**确认"上次做到哪、下一步是什么"，必要时再读 decision_log 末几条与 version_history。会话长时被压缩后，靠 db09/记忆而非短期记忆恢复状态。

**复用历史教训**：新项目立项，或选定方法/投稿策略**前**，先 Grep db09 顶层 `lessons.md` 检索同类"阶段/场景"关键词（如 `方案确认`/`数据准备`/`投稿`）的历史有效做法；命中可复用的，在写 decision_log 时注明"复用自 lesson [日期]"。

## 衔接
是所有技能的状态中枢：m01–m17 的产出都在此登记，a06 的目录与之对应。

---
各工具的真实端点/参数/已知坑见 `references.md`。
