<!-- LIGHT-SKILLS-START -->
## Light 科研技能包（路由说明）

当用户的请求涉及科研全流程时，调用 `~/.agents/skills/light/` 下对应技能的 SKILL.md，按其指令执行。

科研主线（按阶段）：
- 资料调研 → `light-literature-search`
- 数据评估/处理 → `light-data-engineering`
- 提创新点 → `light-idea-generation`；审创新点 → `light-idea-critique`（二者构成循环）
- 方案/技术路线 → `light-research-plan`
- 实验代码 → `light-backend-coding`；结果分析 → `light-result-analysis`
- 论文写作 → `light-paper-drafting`；润色 → `light-paper-polishing`
- 图表规划 → `light-figure-planning`；绘图 → `light-figure-drawing`
- 引用整理 → `light-citation`；排版 → `light-typesetting`
- 投稿定位 → `light-venue-matching`；审稿返修/rebuttal → `light-review-rebuttal`

并行/按需：
- 软著专利 → `light-ip-application`；PPT → `light-slides`；竞赛申报 → `light-competition`
- 读文件/PDF → `light-file-reading`；项目记忆与状态 → `light-memory-pm`
- 系统设计 → `light-system-design`；前端/可视化 → `light-frontend-design`；项目结构 → `light-project-structure`

全程常驻（每次输出前自检）：
- 术语/指标/创新点跨材料一致 → `light-consistency`
- 输出前自审（逻辑/事实/格式/夸大/审美）→ `light-self-review`
- 选工具/选方法 → `light-tool-selection`
- 学术伦理与合规底线 → `light-research-ethics`

核心纪律：不臆造文献/数据/DOI/端点；区分「已验证」与「推测」；凡写入的 API 端点须实测；受版权材料只存元数据/链接/笔记。
<!-- LIGHT-SKILLS-END -->
