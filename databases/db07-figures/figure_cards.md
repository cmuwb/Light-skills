# db07 图表卡（seed）

> 重点学"图支撑哪个 claim"，不只学样式。配色色盲友好且全文统一(a07)。

## 卡片模板
```yaml
- figure_type:
  figure_id:           # F# 图 / T# 表 (如 F1/T1), 与 m07 模板 [图位 F1]/[表位 T1] 对齐
  paper_source:        # 仅元数据/链接
  research_field:
  purpose:             # 支撑哪个 claim
  data_required:
  layout:
  color_scheme:
  annotation_style:
  caption_style:
  possible_code_tool:
  replication_notes:
  where_to_place_in_paper:
  target_journal:      # JOURNAL_SPECS 键: nature/science/cell/plos/ieee/elsevier
  column:              # single/double/full/onehalf (须为该刊实有的键)
```

## 种子卡片

```yaml
- figure_type: 主结果对比柱状图(带误差棒)
  paper_source: 通用实验结果图; 使用目标期刊/会议图表规范与统计显著性报告要求作为约束
  research_field: 通用
  purpose: 证明本方法显著优于 baselines
  data_required: 各方法多次运行的均值+标准差
  layout: 分组柱状, x=数据集/设置, y=指标
  color_scheme: 本方法用强调色, baseline 中性色; 色盲友好
  annotation_style: 误差棒 + 显著性星标 + 数值标签
  caption_style: 自洽, 说明指标/数据集/重复次数
  possible_code_tool: matplotlib/seaborn
  replication_notes: 多种子计算 std; 注意 y 轴不误导(不截断造假)
  where_to_place_in_paper: 实验-主结果

- figure_type: 消融分组柱状/折线
  paper_source: 通用 ablation study 图; 来源为机器学习/实验论文常见消融图类型, 具体样式按目标期刊重绘
  research_field: 通用
  purpose: 证明每个创新组件的贡献
  data_required: 逐组件移除后的指标
  layout: 分组柱状 或 累加折线
  color_scheme: 统一调色板, full model 高亮
  annotation_style: 标出 full model、去除组件名称与关键下降幅度, 不用过密显著性符号
  caption_style: 列明各变体含义
  possible_code_tool: matplotlib
  replication_notes: 组件命名需与方法章节一致; 每个变体同训练设置/同随机种子, 避免不公平消融
  where_to_place_in_paper: 实验-消融

- figure_type: 模型框架图
  paper_source: 通用方法框架图; 学结构表达而非复制具体论文图, 以本方法真实数据流为准
  research_field: 通用
  purpose: 一图讲清方法整体结构与数据流
  data_required: 无(示意)
  layout: 左输入→中间模块→右输出, 箭头标数据流
  color_scheme: 模块分色但克制, 与论文主色一致
  annotation_style: 模块名 + 关键张量维度标注
  caption_style: 从输入、核心模块、输出三层说明方法; 图注不替代正文推导
  possible_code_tool: draw.io / Illustrator / TikZ
  replication_notes: 矢量导出; 字号缩放后仍可读
  where_to_place_in_paper: 方法章节开头

- figure_type: 可解释性热力图(注意力/SHAP)
  paper_source: 通用可解释性图; SHAP/attention 解释需结合方法局限与领域知识审慎使用
  research_field: 通用
  purpose: 提供机理证据, 支撑"为什么有效"
  data_required: 注意力权重 / SHAP 值
  layout: 原始输入 + 叠加热力
  color_scheme: 顺序色图(viridis), 带色标
  annotation_style: 标出高响应区域/特征, 同时给反例或失败样本避免挑图
  caption_style: 说明解释方法、样本选择规则、颜色含义与不可作因果解释的限制
  possible_code_tool: SHAP / matplotlib
  replication_notes: 固定样本选择规则与随机种子; attention 不等同解释, SHAP 需说明背景集
  where_to_place_in_paper: 结果分析/讨论
```

## 待补充
按用户领域补充图表卡，沉淀统一调色板与组图模板。
