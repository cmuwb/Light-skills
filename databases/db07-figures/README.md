# db07 — 科研图表与可视化案例库

学习顶刊顶会图表的审美、布局、配色与组图逻辑，重点学"图表如何支撑论点"，服务 m09(图表规划) 与 m11(绘图)。

## figure_card schema
`figure_type, paper_source, research_field, purpose, data_required, layout, color_scheme, annotation_style, caption_style, possible_code_tool, replication_notes, where_to_place_in_paper`

## 数据来源
CVPR/ICCV/ECCV/NeurIPS/ICLR/ICML/AAAI/ACL/KDD/CHI 顶会，Nature/Science/Cell，Papers With Code，matplotlib/seaborn/plotly/ggplot2 gallery，Observable，Datawrapper examples，IEEE VIS。

## 图表类型库
折线、柱状、箱线、热力、雷达、散点、误差棒、混淆矩阵、ROC、PR、消融图、参数敏感性图、模型框架图、流程图、技术路线图、数据集示意图、可解释性可视化、真实效果图。

## 配色规范（统一）
- 色盲友好：viridis / ColorBrewer / Set2。
- 同一论文统一调色板（由 a07 跨图维护，链 db05/db06）。
- 黑白打印可辨：线型 + 标记 双重区分。
- 矢量优先(PDF/SVG)，位图 ≥300 dpi。

## 图表类型 → 工具 → 用途速查

| figure_type | 推荐工具 | 主要用途 |
|---|---|---|
| 主结果对比 | matplotlib/seaborn 柱状+误差棒 | 证明优于 baseline |
| 消融 | 分组柱状/折线 | 证明各组件贡献 |
| 参数敏感性 | 折线(多曲线) | 鲁棒性/调参分析 |
| ROC/PR/混淆矩阵 | sklearn + matplotlib | 分类性能 |
| 模型框架图 | TikZ/draw.io/Illustrator | 方法概览 |
| 流程/技术路线 | Graphviz/Mermaid/TikZ | 整体流程 |
| 可解释性 | SHAP/注意力热力图 | 机理证据 |
| 真实效果图 | 拼图(GridSpec/PPT) | 定性结果 |

## 使用方式
重点学"图支撑哪个 claim"，而非只学样式。每张参考图沉淀 figure_card，标注"放论文哪里"。

种子卡片见 [figure_cards.md](figure_cards.md)。

## 真实资源文件
- [resources_real.md](resources_real.md) — 真实绘图资源清单（Matplotlib/Seaborn/ggplot2 gallery、SciencePlots、ColorBrewer、viridis、Graphviz、BioRender 等，代表作被引由 OpenAlex 实拉）+ 8+ 个 figure_card（按"支撑哪个 claim + 工具 + 放论文哪里"组织）。
