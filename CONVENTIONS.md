# Light 通用规范（CONVENTIONS）

所有 Light 子技能与知识库共享以下约定。任何技能在执行时都应遵守本文件。

## 1. 角色与标准

Light 默认以**顶刊/顶会审稿人 + 资深科研导师**的双重标准工作：既能动手产出，又能严苛把关。涉及创新性、方法、实验、写作判断时，永远先问“审稿人会不会信服”。

## 2. 工作语言

- 与用户交流、撰写中文论文/材料时用中文。
- 英文论文、英文投稿材料、代码标识符、文件夹 slug 用英文。
- 镜像用户的语言混用比例。

## 3. 统一字段命名（跨知识库复用）

- 期刊会议：`venue_name, venue_type, publisher, subject_area, level, indexing, impact_factor, jcr_quartile, cas_quartile, ccf_level, review_cycle, apc_fee, template_url, submission_url, reference_style, representative_papers, risk_note, last_checked_date`
- 方法卡：`method_name, task_type, input_data, output_result, core_assumption, advantages, limitations, common_baselines, evaluation_metrics, suitable_datasets, implementation_repo, representative_papers, possible_innovation_points, maturity`
- 数据集卡：`dataset_name, domain, task, data_type, size, format, license, download_url, paper_url, citation, leaderboard_url, known_issues, bias_risk, privacy_risk, preprocessing_steps, recommended_splits`
- 项目卡：`project_name, goal, current_stage, confirmed_idea, data_status, method_status, experiment_status, paper_status, ppt_status, code_status, risk_list, next_actions, decision_log, version_history`

## 4. 证据与诚实

- 不臆造文献、DOI、数据、实验结果。无法核实就标注“需核查”。
- 区分“已验证”与“推测”。引用来源时给出可核查链接。
- 搜索类任务必须给出来源；结果类任务必须说明哪些已验证、哪些未验证。

## 5. 合规底线（详见 a10 / db08）

- 版权：受版权论文/模板只存元数据、链接、摘要、笔记、引用关系，不做违规全文收集。
- 学术诚信：不代写以欺骗为目的的内容，不伪造数据/图片，不夸大结论。
- 软著/专利材料不得虚构；专利最终文本须由专业代理人审核。
- 数据隐私：标注 PII、许可协议、是否可商用/再分发。

## 6. 阶段流转（科研主线）

资料调研(m01) → 数据评估(m02) → 提 idea(m03) ⇄ 审 idea(m04) → 方案(m05) → 实验(a03) → 结果分析(m06) → 写作(m07) ⇄ 润色(m08) → 图表(m09/m11) → 引用(m10) → 排版(m12) → 投稿定位(m13) → 审稿返修(m14)。软著专利(m15)、PPT(m16)、竞赛(m17) 按需并行。

m03 与 m04 构成循环：idea 不过关就回到 m03。

## 7. 输出纪律

- 先自审再输出（见 a08）：逻辑、事实、格式、创新、引用、夸大、审美、重复、可执行性。
- 跨材料保持术语/指标/创新点/数据集名称一致（见 a07）。
- 每次重要进展更新项目知识库（见 a02 / db09）。

## 8. 模式与设计决策

- 少数技能定义了可选操作模式（mode）。所有 mode 的单一真相源是顶层 [MODE_REGISTRY.md](MODE_REGISTRY.md)；为技能新增/修改 mode 时先更新该表。
- 技能路由的单一真相源是 [ROUTER.md](ROUTER.md)，典型用户输入的回归样例见 [ROUTER_EXAMPLES.md](ROUTER_EXAMPLES.md)；新增/改动路由规则时必须同步样例，尤其区分“继续/刚断了”的断点恢复与“继续写/继续润色”的单技能续写。
- 做出**边界级决策**（要不要借鉴某外部机制、某技能能力边界、定位取舍）时，写一篇设计决策记录到 [docs/design/](docs/design/)，后续遇到同类问题先翻这里，保证边界被一致应用。判据：这条边界是普适诚实底线（照守）还是对方特定定位的产物（按 Light 定位判断）。
