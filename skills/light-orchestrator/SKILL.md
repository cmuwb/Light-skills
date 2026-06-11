---
name: light-orchestrator
description: 编排器。当用户给出跨多个阶段的大任务（如"从这个数据集做到一篇论文""帮我把这个项目从调研做到投稿"）或要求"继续/刚断了/接手/恢复上下文"时，规划或恢复阶段化 pipeline，按 CONVENTIONS 阶段主线逐阶段调用相应技能，并在阶段间设置强制检查点（决策点 + 确认点），维护产物台账与断点交接。小任务（改摘要、画一张图、查引用）不走 pipeline，直接路由到单技能。
user-invocable: false
---

# 编排器（Orchestrator）

把"组合调用链路"从声明式描述变成可执行流程：规划阶段、调用技能、卡住检查点、记台账、断点续跑。它不亲自干活（写作、画图、分析都交给对应技能），只负责**调度、把关、恢复上下文与阶段交接**。

## 何时启动

**启动 pipeline**（任务跨 ≥3 个阶段、或用户明确要"全流程/从X做到Y"）：
- "从这个数据集做到一篇论文" / "把这个想法做成投稿" / "帮我把项目从头跑到投稿"。
- 用户给了原始材料（数据/想法）并要一个跨阶段的终产物（论文/申报书/答辩）。

**启动断点恢复**（即使当前只剩单一动作，也先恢复状态）：
- "继续" / "刚断了" / "接着来" / "接手 Claude/Codex/Hermes" / "恢复上下文" / "上次做到哪"。
- 用户说上一个 agent 一直断、让你找对话记录、继续某个长期项目。

**不启动**（直接路由到单技能，别用重流程拖累轻任务）：
- "改一下这段摘要" → m07 section/abstract 模式。
- "画张柱状图" → m11。
- "查这几条引用" → m10。
- 任何单一阶段、能一个技能闭环的任务。

判据：**这个任务需要跨技能交接产物或恢复旧状态吗？** 需要→orchestrator；不需要→单技能。

## 0. 断点恢复协议（用户说“继续/刚断了”时先做）

不要凭印象继续。先做最小恢复探针，拼出“当前事实状态”，再行动：

1. **工作区与版本**：读 `git status --short`、`git log --oneline -5`、当前分支、remote；若有 GitHub remote，再读最近 CI（如 `gh run list --branch <branch> --limit 3`）。
2. **当前任务单**：读取当前 Todo/TodoWrite/todo 工具状态；若没有，就从 passport、db09、最近提交重建最小任务单。
3. **项目台账**：优先读项目根目录 `.light/passport.yaml`；没有则读 `databases/db09-projects/projects/<project_name>/project_card.md`、`decision_log.md`、`version_history.md`。
4. **对话/外部交接**：只在两种情况下检索 transcript：①用户明确给出 Claude/Codex/Hermes 对话记录路径；②缓存路径/会话标题/项目 slug 与当前仓库或 db09 项目名明确匹配。检索时限定关键词为当前项目名、仓库路径、最近任务关键词；无法证明相关就标 `transcript: unavailable`，不得猜测不存在的记录，不读无关项目会话。
5. **产物与脏文件**：读相关 manifest / plan / diff / 未提交文件，判断“已完成但未提交”“已提交但未推送”“已推送等 CI”“CI 失败待修”等状态。
6. **恢复摘要**：继续前先内部形成五项事实：`当前阶段`、`已完成`、`未完成`、`阻塞/风险`、`下一步最小动作`。若下一步有副作用（提交、推送、重写历史、删除文件），按范围纪律确认或确保用户已授权。

若 `gh`/CI/todo/transcript 等某个探针不可用，不把它当硬阻断；在恢复摘要里标 `unavailable`，并用其余可用证据（git、passport、db09、文件 diff、用户提供材料）继续恢复。

恢复时严禁：
- 只凭聊天记忆说“应该到 X 了”。必须有 git/passport/db09/todo/CI 等证据。
- 重跑已完成阶段，除非用户要求或证据显示产物无效。
- 看到未提交改动就直接覆盖；先读 diff，确认是本轮遗留还是用户新改动。

## 1. 规划 pipeline

按任务目标，从 CONVENTIONS 第 6 节的阶段主线裁出一条链（不是每次都全跑）。常见链见 `references/pipelines.md`。规划产出一张**阶段计划表**，每阶段都必须写清：调用哪个技能、输入、预期产出、落盘位置、检查点类型。

计划表模板：

| 阶段 | 技能 | 输入 | 产出/落盘 | 检查点 |
|---|---|---|---|---|
| 调研 | m01 literature-search | 用户问题 + db01/db03 背景 | `docs/literature_review.md` / 文献表 | ✓ 来源可核 |
| 方案 | m05 research-plan | 通过审查的 idea | `PROJECT_PLAN.md` / `experiments/experiment_matrix.md` | ✓ 可执行 |

原则：先把计划表给用户确认再开跑；如果用户说“继续刚才的任务”，只需恢复并继续当前阶段，不要重新规划整条链。

## 2. 阶段输入输出契约

跨技能交接必须有可落盘工件，不能只靠一句聊天总结。**工件命名的单一真相源是 CONVENTIONS §6.1 阶段工件契约表**；下表为其执行视角镜像，若与 CONVENTIONS §6.1 不一致以后者为准。项目已有约定时以项目约定为准，但必须在 passport 里记录路径。

| 阶段 | 上游输入 | 标准产物 / handoff artifact | 下游 |
|---|---|---|---|
| m01 调研 | 研究问题、关键词、目标领域 | `docs/literature_review.md` + evidence table（文献、claim、来源链接、可信度） | m03/m04/m07/m10 |
| m02 数据工程 | 数据文件/来源/任务定义 | `data_card.md` + `quality_report.md` + split/manifest | m05/a03/m06 |
| m03 idea 生成 | 调研 gap、数据约束、用户偏好 | `idea_candidates.md`（候选、机制、风险、验证方式） | m04 |
| m04 idea 审查 | 候选 idea | `critique_verdict.md` / scorecard / 是否回 m03 | m05 |
| m05 研究方案 | 放行 idea、数据卡、方法卡 | `PROJECT_PLAN.md` + `experiments/experiment_matrix.md` | a03/m06 |
| a03 实验代码 | 方案、数据、指标 | 可运行代码 + test/log + `run_manifest.md` | m06 |
| m06 结果分析 | 原始结果、实验矩阵 | `claim_evidence_table.md` + 统计检验报告 + 图表建议 | m07/m09 |
| m07/m08 写作润色 | claim/evidence、图表、引用 | `draft.md` / 修订稿 + GAP 台账 | m09/m10/m12 |
| m09/m11 图表 | claim/evidence、规划卡、source_card | `projects/<project_name>/figures/manifest.md` + 图文件 + checks | m07/m12 |
| m10 引用 | 草稿 citekey、候选文献 | `refs.bib` + `citation_audit.md`（真实性 + locator） | m12 |
| m12 排版 | 稿件、图、bib、模板 | 编译日志 + final PDF/DOCX | m13/m14/提交 |
| m14 返修 | 审稿意见、稿件、实验/图表 | `response_matrix.md` + response letter + 改稿 | m12/提交 |

每个阶段结束时，把“产物路径 + 验证输出摘要 + 下一阶段输入”写入 `.light/passport.yaml`；缺工件就不能声称该阶段完成。

## 3. 逐阶段执行 + 检查点

每个阶段：调用对应技能 → 产出落台账 → 过该阶段检查点 → 才进下一阶段。两类检查点（详见 `references/checkpoints.md`）：

- **决策点 🧑**：需要用户选分支才能继续。如 m04 idea 不过关（打回 m03 还是放行？）、投哪个 venue、用哪种输出格式。**不替用户决定。**
- **确认点 ✓**：机器先验证（跑 a08 self-review / a07 consistency / a10 research-ethics 闸门），出报告 → 用户确认 → 推进。**诚信门不达标默认阻断**，不静默跳过；同一阶段最多 2 轮整体返修（细则见 `references/checkpoints.md`），仍不达标的转为“已知局限”如实记录，而非假装修好。

确认点的证据必须是新鲜的：当前轮命令输出、文件 diff、CI run、脚本 selftest、人工确认记录之一；不能只写“已检查”。

## 4. 维护产物台账

全程维护一份**产物台账**（passport），记录每阶段：产出了什么、过了哪些闸门、哪些标了 GAP、用户在决策点选了什么。格式与存储位置见 `references/passport.md`（固定存项目根目录 `.light/passport.yaml`）。启动时先查该文件是否存在——存在即续跑、不存在即新建。台账纳入 a02 memory-pm 的项目记忆，**任务中断后可据此续跑**。

台账最小更新规则：
- 每完成一个阶段，当场追加，不攒到最后补。
- 每个 artifact 写相对项目根目录的路径。
- gate 写 PASS/FAIL/WARN 和证据来源。
- 用户决策写 `choice` 与 `by: user`。
- GAP / known_limitations 如实记录。

## 5. 断点交接输出（handoff）

长任务每次暂停、提交、等待用户/CI/实验、或上下文可能压缩前，必须留下这段交接摘要。可以写入聊天、passport 的 notes，或项目 `version_history.md`：

```md
## Handoff
- 当前阶段：<pipeline 阶段 / 当前 skill>
- 已完成：<产物路径 + 验证摘要>
- 工作区状态：<clean / 未提交文件 / 已提交未推送 / 等 CI>
- 最新提交/CI：<sha / run id / conclusion>
- 未完成：<下一步最小动作，不超过 3 条>
- 阻塞/风险：<需要用户决策 / 数据缺口 / 诚信风险 / 无>
- 续接命令/入口：<下一位 agent 应先读哪些文件或跑哪些命令>
```

用户后续说“继续”时，先读这段 handoff 作为入口，但**不能把 handoff 当作当前事实**；仍要刷新 `git status`、todo、passport/db09、CI/远端等当前证据。没有 handoff 才退回“断点恢复协议”。

## 边界（重要）

- 编排器**不绕过任何常驻闸门**。self-review / consistency / research-ethics / tool-selection 在每个阶段照常后台生效。
- 编排器**不替用户做研究决策**。idea 选哪个、结论怎么定、投哪里——都是决策点，交用户拍板。这条边界（"可借鉴 ARS 的调度形态，但不接管研究判断"）的设计决策记录见仓库 `docs/design/2026-06-08-ars-borrow-boundary.md`（仅在仓库内，未随安装分发）。
- 分级原则：大任务上完整 pipeline，小任务直接单技能。宁可少编排，不可为编排而编排。
- 断点恢复不是“重新做一遍”。已验证、已提交、已入 passport 的阶段默认不重做；若当前 diff、依赖、远端状态或 CI 显示证据已失效，只重验受影响的最小范围；只在证据失效、用户要求或下游发现矛盾时回滚。

## 自检清单

- [ ] 是否先判断该任务该 pipeline、单技能，还是断点恢复？
- [ ] 若是“继续/刚断了”，是否读了 git/todo/passport/db09/CI 等证据？
- [ ] 是否明确当前阶段、已完成、未完成、下一步最小动作？
- [ ] 是否为每个跨技能交接产物写了落盘路径？
- [ ] 是否在决策点停下让用户选，而不是替用户决定？
- [ ] 是否在确认点给出真实验证证据，而不是口头说通过？
- [ ] 是否更新 `.light/passport.yaml` 或留下 handoff，保证下次能续接？
