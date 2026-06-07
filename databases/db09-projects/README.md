# db09 — 用户个人项目知识库

为每个科研项目建立**独立**知识库，长期陪伴项目从选题到成果转化。这是 a02(记忆PM)、a07(一致性) 的状态中枢，所有技能的产出都在此登记。

## project_card schema
`project_name, goal, current_stage, confirmed_idea, data_status, method_status, experiment_status, paper_status, ppt_status, code_status, risk_list, next_actions, decision_log, version_history`

- `current_stage`: 资料调研 | idea 构思 | 方案确认 | 数据准备 | 实验实现 | 结果分析 | 论文写作 | 图表制作 | 投稿准备 | 答辩展示 | 成果转化

## 顶层目录结构
```
db09-projects/
├── README.md              本说明
├── project_card_template.md
├── lessons.md             跨项目过程/方法论教训库（与 projects/ 平级，见下）
└── projects/<project_name>/   每个项目一个独立目录（结构见下）
```

## lessons.md — 跨项目过程教训库
全局单文件，追加式。收"做法层面的有效/失败经验"（踩坑、被拒、复现失败、流程省时），**不收**方法选型事实（→ db03 方法卡）与个人偏好（→ Light feedback 记忆）。格式：`- [YYYY-MM-DD] 阶段/场景 — 做法 — 结果(有效|失败) — 适用条件 — 来源项目slug`。写入纪律与检索时机见 a02 SKILL.md。

## 每个项目目录结构
```
projects/<project_name>/
├── project_card.md       项目卡(上述字段)
├── terminology.md        术语/指标/创新点统一定义表(供 a07)
├── decision_log.md       重大决策时间线(含 idea 取舍、方案变更)
├── version_history.md    论文/PPT/图表/代码各版本记录
├── literature/           m01 调研产出
├── reviews/              m14 审稿意见与 response
└── submissions/          投稿记录(venue/日期/状态/结果)
```

## 管理工具映射
- 代码/文本版本 → Git
- 数据/实验 → DVC / MLflow / W&B
- 文献 → Zotero
- 项目知识 → Obsidian / Notion / Markdown / Logseq
- 进展 → README + CHANGELOG

## 更新纪律（硬性，联动 a02）
每次完成：资料搜索 / idea 修改 / 实验运行 / 论文修改 / PPT 修改 / 投稿返修——**立即**更新对应 status + decision_log + version_history，避免上下文丢失。

## 与跨会话记忆的关系
项目级状态存这里(db09)；跨会话的用户偏好/项目背景/参考资源额外写入 Light 记忆文件并在 MEMORY.md 加索引(见 a02)。会话开始先读 project_card 恢复 `current_stage` 与 `next_actions`。

模板见 [project_card_template.md](project_card_template.md)。
