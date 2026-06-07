# db02 写作样本卡（seed）

> 用法：抽取结构与论证策略迁移到当前论文，**不照抄原文**。来源链接仅作元数据，受版权全文不收录。

## 卡片模板
```yaml
- venue:
  title_pattern:            # 标题套路
  abstract_structure:       # 摘要分句逻辑
  intro_problem_gap_contribution:
  related_work_taxonomy:
  method_narrative:
  experiment_design:
  figure_table_logic:
  limitation_expression:
  contribution_sentence:
  reviewer_potential_questions:
  source_url:
```

## 高频可迁移套路（领域无关）

### 标题套路
- "方法名: 一句话能力描述"（如 "X-Net: Efficient ... for ..."）
- "动词开头的问题陈述"（如 "Learning to ... via ..."）
- 避免空泛词("A Study on")；体现新意与任务。

### 实验章节标准顺序
1. Experimental Setup（数据集 / baselines / 指标 / 实现细节 / 算力）
2. Main Results（主表 + 一段解读）
3. Ablation Study（逐组件，证明贡献来源）
4. Analysis（敏感性 / 收敛 / 复杂度）
5. Qualitative Results（可视化 / case study）
6. Limitations

### 审稿人高频追问（预演用，喂 m14）
- 创新点和最接近的工作 X 到底差在哪？
- 对比是否公平（同数据/同算力/同设置）？
- 提升是否统计显著（多种子+检验）？
- 消融能否证明提升来自所声称的组件？
- 在更大规模/真实场景能否泛化？
- 计算开销代价如何？

### 措辞红线（写作/润色共用）
慎用 novel / significantly / state-of-the-art / first，每个都要有证据支撑，否则审稿人反感。

## 待补充
按用户领域逐步加入 3–5 篇代表作的结构化卡片（从 OpenReview/arXiv 公开版抽取结构）。
