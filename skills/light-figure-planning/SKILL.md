---
name: light-figure-planning
description: 根据论文内容规划应该做哪些图、哪些表、插在哪里、各起什么作用。当用户需要论文图表规划时使用。图表不限于统计图，也包括数据集真实效果图、模型输出示例、案例展示、可解释性可视化等。规划框架图、技术路线图、数据集示意图、模型结构图、算法流程图、结果对比/消融/敏感性图、真实效果图、统计表/对比表等，以审稿人标准判断哪些必做、哪些冗余。
---

# 论文图表设计规划

## 定位
图表服务论点，不是装饰。每个图表先回答：**它支撑哪个 claim？删掉它论文会不会缺一块？**

## 规划流程
1. 通读论文(或大纲) + m06 结果，列出全部 claim。
2. 给每个 claim 匹配最有说服力的呈现形式。
3. 标注优先级：**必做**(支撑核心贡献) / **可做**(增强) / **可删**(冗余或弱)。
4. 排版位置：哪张进正文、哪张进附录、组图怎么组。

## 图表类型清单（按需选，附建议工具）
- **概念/方法**：框架图、技术路线图、模型结构图、算法流程图、数据流图。→ 精排可编辑源用 diagrams.net(XML)；与 LaTeX 同源用 TikZ；关系/依赖自动布局用 Graphviz(dot)；文档内嵌草图用 Mermaid；生命科学机制图用 BioRender。
- **数据**：数据集示意图、样本分布、标注示例。→ 统计分布用 seaborn/matplotlib；示意排版用 draw.io/TikZ。
- **定量结果**：主结果对比图/表、消融图、参数敏感性曲线、收敛曲线、ROC/PR、混淆矩阵、雷达图。→ matplotlib(精排)+seaborn(统计便捷)；R 用 ggplot2；交互补充材料用 Plotly/Altair。
- **定性结果**：真实效果图、模型输出示例、case study、失败案例、可解释性可视化(注意力/SHAP/特征图)。
- **表**：指标汇总表、对比表、消融表、数据集统计表、复杂度表。

## 工具选型速查（写进规划卡的"建议工具"字段）
- **统计/定量图**：matplotlib（控制最细）、seaborn（自动 CI/分面）、ggplot2（R 的 grammar of graphics）、Plotly/Altair（交互+静态导出）。
- **出版级矢量、公式标签多**：TikZ/PGFPlots，与 LaTeX 同源，字体公式无缝。
- **框架/系统图，要可编辑矢量源**：diagrams.net（`.drawio` 即 XML，可程序化批量改）。
- **关系/依赖/自动布局**：Graphviz（dot 分层；neato/fdp 弹簧；sfdp 大图）。
- **文档内嵌草图/流程**：Mermaid（GitHub/Notion 原生渲染，diagram-as-code）。
- **生命科学机制/实验流程**：BioRender（5 万+验证图标，注意出版授权）。
- **最终多-panel 拼版/对已导出图手工精修矢量**：Inkscape（免费，CLI `inkscape in.svg --export-type=pdf,svg`，转曲 `--export-text-to-path`）或 Adobe Illustrator（行业标准，`.ai` 私有非开放格式，跨工具存 PDF/SVG）。把异源面板（mpl 导出 PDF + 位图 + 文字标签）自由对齐组装成单张投稿图。

## 出版级硬规格（规划卡里据此约束执行）
- **分辨率/格式**：线稿矢量(PDF/EPS/SVG)或 600–1200 DPI；位图 300–600 DPI、TIFF/PNG，**绝不用 JPEG 存科研数据**。matplotlib 设 `pdf.fonttype=42` 避免 Type-3 字体被拒。
- **配色**：离散用 Okabe-Ito（`#E69F00 #56B4E9 #009E73 #F0E442 #0072B2 #D55E00 #CC79A7`），连续量用 viridis/plasma/cividis；颜色之外加冗余编码(线型/marker)；**灰度+色盲双测**。
- **字体**：无衬线(Arial/Helvetica)，最终印刷尺寸下最小 **5 pt**、最大 7 pt（Nature 规格，✅ curl 实测）；标签 sentence case，单位入括号。
- **列宽**（按目标期刊设图宽，mm；下值仅 Nature 经 curl 实测，其余出版商官网对 curl/WebFetch 返回 403 付费墙，为公开作者指南通行值，投稿前务必以目标刊官网为准）：
  - **Nature**（✅ curl 实测 www.nature.com/nature/for-authors/final-submission，HTTP 200）：单栏 **89**、双栏 **183**，最大高 **170**（留题注空间）。
  - **Science (AAAS)**（⚠️付费墙未实测）：三档——单栏 ≈**55**(5.5 cm)、双栏 ≈**120**(12 cm)、整页 ≈**183**(18.3 cm)。注意 Science 无"175"这一档。
  - **Cell Press**（⚠️付费墙未实测）：单栏 **85**、1.5 栏 **114**、整页 **174**。注意整页是 174 非 178。
  - **Elsevier**（⚠️付费墙未实测，含 db01 的 Computers and Electronics in Agriculture 等）：最小 **30**、单栏 **90**、1.5 栏 **140**、双栏/整页 **190**。
  - **IEEE**（⚠️付费墙未实测，IEEEtran 双栏版式）：单栏 ≈**88.9**(3.5 in)、双栏/整页文本宽 ≈**181.9**(7.16 in)。
  - **MDPI**（⚠️付费墙未实测，含 db01 的 Animals）：单列版式正文宽 ≈**170**，图按此宽或其整数分数排；线稿/组合图建议 1000 DPI、照片 ≥300 DPI。
  - 导出按 mm 设尺寸（如 ggplot2 `ggsave(w,h,units='mm',dpi=300)`、mpl `figsize` 换算）。
- **统计严谨**：必带误差棒(SD/SEM/CI，caption 注明)、样本量 n、显著性标记，尽量画散点。
- **多 panel**：matplotlib GridSpec / subplots；加粗大写 A/B/C 标号；跨 panel 风格、尺度一致。

## 每个图表的规划卡（交 m11 执行）
图表编号、类型、目的(支撑哪个 claim)、所需数据、建议工具(见上选型速查)、布局、配色基调(默认 Okabe-Ito/viridis)、标注要点、caption 草稿、放置位置、优先级、**target_journal**、**column**。对应 db07 figure_card 字段。
- **图表编号**：固定 `F#` 命名图、`T#` 命名表（F=Figure、T=Table，如 F1/F2/T1），与 m07 论文模板的 `[图位 F1]`/`[表位 T1]` 占位对齐，作为图↔图号↔caption 的锚点。
- **target_journal**：目标期刊键，取 m11 `figure_export.py` 的 `JOURNAL_SPECS` 键之一：`nature`/`science`/`cell`/`plos`/`ieee`/`elsevier`。决定物理栏宽 mm、最小字号、首选格式，m11 据此直接传 `save_for_journal`，避免栏宽臆测导致整张图物理尺寸作废。
- **column**：栏宽档位，取 `single`/`double`/`full`/`onehalf`（须为该刊在 `JOURNAL_SPECS` 里实有的键，如 `full` 仅 science、`onehalf` 仅 plos/elsevier）。
**建议工具二选一判定**：异源面板组合（代码图 + 位图 + 文字标签）/ 需逐像素对齐与自由精修 → 手工矢量编辑（Inkscape/Illustrator）；同源同类数据图、追求复现性 → 代码生成（GridSpec/subplots）。
概念/示意类可先出 **ASCII 线框 + 文案 + 配色 + 图标/图表类型建议**（content-first 蓝图），把信息架构定死再交执行。

## 审稿人视角自检
- 核心贡献是否每条都有图/表支撑？
- 有没有"好看但不传递信息"的图？删。
- 表格能不能图示化得更直观？
- 组图逻辑是否清晰（同类对齐、尺度一致）？
- caption 能否脱离正文独立读懂？
- 示意图按 5 维评分（各 0–2，合 10）：**科学准确性 / 清晰可读 / 标签质量 / 布局构图 / 专业度**；journal 级目标 ≥8.5。
- 投稿前 13 点核查：分辨率·格式·尺寸·可读性·色盲安全·灰度兼容·坐标轴标签(含单位)·误差棒·panel 标号·显著性标记·图例清晰·字体一致·去装饰元素。

## 衔接
规划卡交 m11 绘制；与 m07/m08 同步确保图文一致；风格登记 db07 与项目库 db09，并由 a07 维护全文图表风格统一。

---
工具真实端点、API 参数、各绘图库用法与已知坑见 `references.md`。
