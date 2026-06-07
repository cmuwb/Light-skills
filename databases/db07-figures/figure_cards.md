# db07 图表卡（seed）

> 重点学"图支撑哪个 claim"，不只学样式。配色色盲友好且全文统一(a07)。

## 卡片模板
```yaml
- figure_type:
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
```

## 种子卡片

```yaml
- figure_type: 主结果对比柱状图(带误差棒)
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
  research_field: 通用
  purpose: 证明每个创新组件的贡献
  data_required: 逐组件移除后的指标
  layout: 分组柱状 或 累加折线
  color_scheme: 统一调色板, full model 高亮
  caption_style: 列明各变体含义
  possible_code_tool: matplotlib
  where_to_place_in_paper: 实验-消融

- figure_type: 模型框架图
  research_field: 通用
  purpose: 一图讲清方法整体结构与数据流
  data_required: 无(示意)
  layout: 左输入→中间模块→右输出, 箭头标数据流
  color_scheme: 模块分色但克制, 与论文主色一致
  annotation_style: 模块名 + 关键张量维度标注
  possible_code_tool: draw.io / Illustrator / TikZ
  replication_notes: 矢量导出; 字号缩放后仍可读
  where_to_place_in_paper: 方法章节开头

- figure_type: 可解释性热力图(注意力/SHAP)
  research_field: 通用
  purpose: 提供机理证据, 支撑"为什么有效"
  data_required: 注意力权重 / SHAP 值
  layout: 原始输入 + 叠加热力
  color_scheme: 顺序色图(viridis), 带色标
  possible_code_tool: SHAP / matplotlib
  where_to_place_in_paper: 结果分析/讨论
```

## 待补充
按用户领域补充图表卡，沉淀统一调色板与组图模板。
