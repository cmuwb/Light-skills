# db02 — 顶级论文写作能力训练库

把顶级论文拆成**结构化写作样本**（不是存 PDF），训练 m07(写作)、m08(润色)、m14(审稿模拟) 的判断力。

## 样本 schema（每篇一条 writing_card）
`title_pattern, abstract_structure, intro_problem_gap_contribution, related_work_taxonomy, method_narrative, experiment_design, figure_table_logic, limitation_expression, contribution_sentence, reviewer_potential_questions, venue, source_url`

## 数据来源
CVPR/ICCV/ECCV/NeurIPS/ICLR/ICML/AAAI/IJCAI/ACL/EMNLP/KDD/WWW/SIGIR/CHI、Nature/Science/Cell、IEEE/ACM/Springer/Elsevier、arXiv、OpenReview、Papers With Code。

## 使用方式（重要）
**抽取结构、表达策略、论证方式，绝不照抄原文**。每次写作时调用对应样本，迁移其骨架到当前论文。

## 可复用写作套路（已沉淀）

### 摘要结构（5 段式）
背景一句 → 问题/gap 一句 → 本文方法一句 → 关键结果(带数字) 一句 → 意义/影响 一句。

### 引言 problem-gap-contribution
1. 领域重要性(为什么这个问题值得解决)
2. 现状与不足(已有工作做到哪、缺什么 gap，带引用)
3. 本文做法(一句话概括)
4. 贡献清单(3 条左右，bullet)
5. 结果预告(主要数字)

### 相关工作 taxonomy
按方法族/任务分 2–4 类，每类先综述再点"与本文差异"，避免编年体流水账。

### 方法叙事
直觉 → 形式化定义 → 整体框架(配图) → 各模块 → 复杂度/理论性质。

### 贡献句式模板
"We propose X, the first/a novel ... that ... ; unlike prior work which ..., our method ..."（慎用 first/novel，需站得住）。

### 局限性表达
主动承认 2–3 条真实局限 + 对应未来工作，体现严谨，降低审稿人攻击面。

种子样本见 [writing_cards.md](writing_cards.md)。

## 真实数据文件
- [samples_real.md](samples_real.md) — 16 篇真实顶会/顶刊论文写作结构拆解（标题/被引/DOI 由 OpenAlex 实拉，如 ResNet 被引 22 万、AlphaFold、Adam），含摘要还原与结构分析。
- [samples_recent_2024_2026.md](samples_recent_2024_2026.md) — 8 篇 2024–2026 顶会顶刊写作样本（LLM/扩散时代），补 2012–2021 经典样本的时代缺口：VAR(NeurIPS24 最佳)、Generative Image Dynamics/Rich Human Feedback(CVPR24 最佳)、BioCLIP/Mip-Splatting(CVPR24 最佳学生)、农业 YOLO 综述、癌症影像基础模型与 ChemCrow(Nature MI)。元数据 OpenAlex 实拉、获奖身份官方页实查，**只存结构笔记 + reviewer_potential_questions，不存全文**。
- [patterns_library.md](patterns_library.md) — 各章节写作套路与句式库 + 措辞红线，附权威写作指南来源（Whitesides、Ten Simple Rules 等）。
