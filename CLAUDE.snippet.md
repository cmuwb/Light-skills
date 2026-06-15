<!-- LIGHT-SKILLS-START -->
## Light 科研技能包（常驻纪律 + 路由）

Light 把科研全流程拆成 28 个 `light-*` 技能，已链接到 `~/.claude/skills/`。Claude Code
按各技能 SKILL.md 的 `name`/`description` 自动发现并触发。本块补两件 description 兜不住的事：
①声明**哪些技能常驻**（每任务默认生效，非等用户开口）；②给**何时调哪个**的路由速查。

### 全程常驻（无需 /调用，相关任务默认按其 SKILL.md 执行）
- **light-consistency**：术语/指标/创新点跨材料一致；定义一改回扫所有产物。
- **light-self-review**：每次对外输出前自审（逻辑/事实/格式/夸大/审美/引用/可执行）。重产出全量、轻改动最小三项。
- **light-tool-selection**：选工具/选方法前先查 decision_matrix，别凭记忆。
- **light-research-ethics**：诚实底线——不臆造文献/数据/DOI/端点；区分「已验证」与「推测」。
- **light-file-reading / light-memory-pm**：涉及读文件 / 长期项目时自动触发。
- **light-orchestrator**：跨多阶段大任务 或「继续·刚断了·接手·恢复上下文」断点恢复时启动；逐阶段卡检查点、维护 `.light/passport.yaml` 台账。单阶段轻任务不启动。

### 科研主线（按阶段）
- 文献调研 → `light-literature-search`　数据评估/处理 → `light-data-engineering`
- 提创新点 → `light-idea-generation`；审创新点 → `light-idea-critique`（二者成环）
- 方案/技术路线 → `light-research-plan`　实验代码 → `light-backend-coding`；结果分析 → `light-result-analysis`
- 写作 → `light-paper-drafting`；润色 → `light-paper-polishing`
- 图表规划 → `light-figure-planning`；绘图/图表审查 → `light-figure-drawing`
- 引用 → `light-citation`；排版 → `light-typesetting`
- 投稿定位 → `light-venue-matching`；模拟审稿/返修/rebuttal → `light-review-rebuttal`

### 并行/按需
- 软著专利 → `light-ip-application`；PPT/deck QA → `light-slides`；竞赛申报 → `light-competition`
- 读 PDF/Word/PPT/Excel/图片/代码/压缩包 → `light-file-reading`
- 系统设计 → `light-system-design`；前端/可视化 → `light-frontend-design`；项目结构 → `light-project-structure`

### 易混边界
- 「继续/刚断了/接手」且指向断点恢复 → `light-memory-pm` + `light-orchestrator`，先读 git/todo/CI/最近提交再继续。
- 「继续写/继续润色当前段落」→ 单技能 `light-paper-drafting`/`light-paper-polishing`，不启动 orchestrator。
- 图表规划归 `light-figure-planning`；实际绘图/配色/诚实性检查归 `light-figure-drawing`；整套 PPT 视觉 QA 归 `light-slides`。

核心红线：不臆造文献/数据/DOI/端点；论文图/数据图必须程序化生成、**绝不 AI 生图**；
写入的 API 端点须实测；受版权材料只存元数据/链接/笔记。pipeline 确认点用
`light-orchestrator/scripts/run_checkpoint.py` 聚合各技能 findings 做机器闸门，critical fail 默认阻断。
<!-- LIGHT-SKILLS-END -->
