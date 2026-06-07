# 参考工具研究笔记（light-figure-planning）

逐工具核查笔记，服务于"论文图表规划"。每个工具给出：是什么 / 可复用方法（真实端点、参数、API 要点） / 链接 / 已知坑或局限。研究日期 2026-06。

---

## Scientific Visualization skill（社区科研技能）

【是什么】把 Claude 变成"出版级科研绘图"助手，面向 Nature/Science/Cell/PLOS 投稿规格。核心是一套 journal-specific 样式预设 + 导出/校验脚本，主力用 matplotlib，辅以 seaborn、plotly。

【可复用方法】
- 6 步工作流：Plan（定目标期刊+图类型）→ Configure（套期刊样式，如 `configure_for_journal('nature','single')`）→ Create（标签、色盲安全色、统计标注）→ Verify（尺寸/字号/色彩可达性核对期刊规格）→ Export（矢量 PDF/EPS，位图 TIFF/PNG，对应 DPI）→ Review（按印刷尺寸在正文语境下看）。
- 提供脚本骨架可借鉴：`figure_export.py`（多格式导出+尺寸合规检查）、`style_presets.py`（期刊样式）、`color_palettes.py`（Okabe-Ito 等色盲安全调色板）、`publication.mplstyle` / `nature.mplstyle`（mpl 样式文件）。
- 硬规格（可直接当规划约束）：
  - 分辨率：线稿 600–1200 DPI 或矢量；位图 300–600 DPI，TIFF/PNG，**绝不用 JPEG 存科研数据**。
  - 配色：默认 Okabe-Ito（`#E69F00 #56B4E9 #009E73 #F0E442 #0072B2 #D55E00 #CC79A7`）；连续量用 viridis/plasma/cividis；颜色之外加冗余编码（线型/marker）；灰度测试。
  - 字体：无衬线（Arial/Helvetica），最终印刷尺寸下最小 6–7 pt；标签 sentence case，单位放括号。
  - 列宽（按目标刊设图宽，mm）：详见下方独立小节"出版商图宽硬规格核查表"（Nature 经 curl 实测，其余付费墙未实测）。原笔记中"Science 双栏 175""Cell 双栏 178"为错误值，已更正并补全 Elsevier/IEEE/MDPI。
  - 统计：必带误差棒（SD/SEM/CI 在 caption 注明）、样本量 n、显著性标记、尽量画出散点。
  - 多panel：GridSpec 布局，加粗大写 A/B/C 标号，跨 panel 风格一致。
- 13 点投稿前自检：分辨率/格式/尺寸/可读性/色盲安全/灰度兼容/坐标轴标签/误差棒/panel标号/显著性/图例清晰/字体一致/去装饰。

【链接】https://www.aitmpl.com/component/skills/scientific/scientific-visualization ；色板理论 Okabe & Ito https://jfly.uni-koeln.de/color/

【已知坑】是社区第三方技能（非 anthropics/skills 官方仓库里的）。规格数字以投稿前查目标期刊最新 author guidelines 为准。

---

## Scientific Schematics skill（社区科研技能）

【是什么】从自然语言描述生成出版级科研示意图（流程图、网络结构、通路图、电路、系统框图）。注意：主力是 **AI 生图**，不是代码矢量绘制。

【可复用方法】
- "智能迭代精修"循环：Nano Banana Pro（OpenRouter）生图 → Gemini 3 Pro 按 5 维各 0–2 分打分（科学准确性/清晰度/标签质量/布局/专业度，合 10 分）→ 达到文档类型阈值则停（journal 8.5、poster 7.0、presentation 6.5），否则改 prompt 重生，**最多 2 轮**。产物含版本化图片 + JSON 评审日志。
- 入口：`python scripts/generate_schematic.py "描述" -o out.png --doc-type journal --iterations 2 -v`；Python API `ScientificSchematicGenerator.generate_iterative()`。
- 5 维评分表非常适合直接拿来当**示意图评审维度**清单。
- 设计原则同上：Okabe-Ito、灰度兼容、形状+颜色冗余、无衬线 7–8pt、白底高对比、线宽 ≥0.5pt 常用 1–2pt、矢量优先（LaTeX 用 PDF、web 用 SVG、PNG 兜底）。"clarity over complexity"。
- QA：重叠检测、色盲/灰度模拟、分辨率校验、视觉质量报告随图归档。

【链接】https://playbooks.com/skills/k-dense-ai/scientific-agent-skills/scientific-schematics ；可比库 Schemdraw https://schemdraw.readthedocs.io 、NetworkX https://networkx.org

【已知坑】依赖外部付费 API（OPENROUTER_API_KEY）。AI 生图对精确数值/文字标签不可靠，最终图的文字需人工核对；不适合需要严格可编辑矢量源的场景。

---

## Infographics skill（社区技能）

【是什么】**规划/规格工具**而非生图工具——在动手设计前把"数据故事"的信息架构定下来。

【可复用方法】
- 输出一份蓝图：ASCII 线框布局 + 内容层级 + 可直接粘贴的文案 + 配色板 + 字体建议 + 图标/图表类型建议。
- 支持的版式：时间线、流程、数据密集型（stat-heavy）、对比。
- 理念：content-first，把结构与内容决策前置，省掉与设计师反复返工。
- 与本技能高度同构：可借鉴"先出 ASCII 线框 + 文案 + 配色 + 图表类型建议"的规划交付物形态。

【链接】https://claudemarketplaces.com/skills/claude-office-skills/skills/infographic

【已知坑】只产文本蓝图，不出真实图形（无 HTML/SVG 渲染）。适合规划阶段，执行仍需绘图工具。

---

## Markdown & Mermaid Writing skill（社区技能）

【是什么】用 Mermaid 文本语法生成可在 GitHub/GitLab/Notion/markdown 查看器直接渲染的图，输出 markdown 代码块或 `.mmd`/`.mermaid` 文件。仅需 Read/Write 工具，轻量。

【可复用方法】
- 4 步：识别图类型 → 规划结构（列节点/实体+关系）→ 生成语法 → 输出。
- 覆盖 10 类：flowchart（方向 TD/LR/BT/RL）、sequenceDiagram、classDiagram、erDiagram、stateDiagram、gantt、pie、mindmap、timeline、gitGraph。
- 防错规则（直接可用）：4 空格缩进；节点 ID 短而唯一（A/B/node1）；含特殊字符的文本加引号 `A["Text (parens)"]`；subgraph 用 `end` 闭合；无尾随空白；`end` 单词在 flowchart 中需引号包裹。

【链接】技能 https://playbooks.com/skills/johnlarkin1/claude-code-extensions/mermaid ；语法权威 https://mermaid.js.org/intro/syntax-reference

【已知坑】拼写/未知关键字会静默失败或破图。复杂排版能力弱，论文出版级矢量图仍建议 TikZ/draw.io。

---

## Matplotlib

【是什么】Python 出版级绘图基础库，控制粒度最细，是上面科研技能的主力后端。

【可复用方法】
- 出版级 rcParams 要点：`figure.dpi`/`savefig.dpi=300+`、`font.family='sans-serif'`、`font.size` 按印刷尺寸设、`axes.spines.top/right=False`、`savefig.bbox='tight'`、`pdf.fonttype=42`（避免 Type-3 字体被期刊拒）。
- 用 `.mplstyle` 文件 + `plt.style.use(...)` 统一风格；`constrained_layout=True` 或 `fig.tight_layout()` 防重叠。
- 多 panel：`fig, axs = plt.subplots(...)` 或 `GridSpec`；矢量导出 `fig.savefig('f.pdf')`，位图 `dpi=600`。
- 配色用 ColormapsRegistry，连续量 viridis 系（感知均匀）。

【链接】https://matplotlib.org/stable/ ；样式表 https://matplotlib.org/stable/users/explain/customizing.html

【已知坑】默认样式不达投稿标准（字号偏小、有顶右框线、DPI 低）；中文需手动设字体；EPS+透明度有坑，矢量优先 PDF。

---

## Seaborn

【是什么】基于 matplotlib 的统计可视化高层库，自动算置信区间、做分面。

【可复用方法】
- 两类函数要分清：**figure-level**（`relplot`/`displot`/`catplot`，自带 FacetGrid，返回 FacetGrid，用 `g.savefig`）vs **axes-level**（`scatterplot`/`lineplot`/`boxplot`/`heatmap`，画在传入的 ax 上，便于嵌进 matplotlib 多 panel）。
- 新 **objects 接口**（0.12+）：`so.Plot(data, x, y).add(so.Dot()).add(so.Line(), so.PolyFit())`——声明式语法，类似 grammar of graphics。
- `sns.set_theme(style='whitegrid', context='paper')`；调色板 `sns.color_palette('colorblind')`。
- 统计自动化：`lineplot` 默认按 x 聚合并画 95% CI；`barplot` 带 bootstrap CI。

【链接】https://seaborn.pydata.org/ ；函数总览 https://seaborn.pydata.org/tutorial/function_overview.html

【已知坑】figure-level 与 axes-level 混用易乱（前者自建 figure，不能塞进已有 subplot）；精细定制最终仍要落到 matplotlib。

---

## Plotly (Python)

【是什么】交互式图库，可导出静态图用于出版。

【可复用方法】
- 静态导出引擎是 **Kaleido**：`pip install --upgrade kaleido`。Kaleido v1 不再内置 Chrome，需 `plotly_get_chrome` 或 `plotly.io.get_chrome()` 装 Chromium。
- 导出：`fig.write_image("f.png")`（按扩展名推断格式）；`fig.to_image(format="png", width=600, height=350, scale=2)`，`scale>1` 提分辨率。
- 支持格式：位图 PNG/JPEG/WebP，矢量 SVG/PDF；EPS 仅 Kaleido <1.0.0 且需 poppler。
- 批量：`plotly.io.write_images(fig=[f1,f2], file=['a.png','b.png'])` 比逐个快。
- 默认值用 `plotly.io.defaults`（`default_format/width/height/scale`）；旧 `kaleido.scope` 6.2 起弃用。
- `engine` 参数与 Orca 在 6.2 弃用，2025-09 后移除——装了 Kaleido 即自动用。

【链接】https://plotly.com/python/static-image-export/ ；Kaleido https://github.com/plotly/Kaleido

【已知坑】WebGL trace 导出矢量时会内嵌位图（非真矢量）；依赖 Chrome 装环境，CI 里要预装。

---

## ggplot2 (R)

【是什么】R 的 grammar of graphics 实现，分层式声明绘图。

【可复用方法】
- 语法骨架：`ggplot(data, aes(x, y, color=grp)) + geom_point() + geom_smooth(method='lm') + facet_wrap(~cat) + theme_minimal() + labs(...)`。
- 核心概念：data + aes 映射 + geom 图层（可叠多层）+ scale（轴/色）+ facet 分面 + theme 主题 + coord 坐标。
- 出版主题：`theme_bw()`/`theme_classic()` + `theme(text=element_text(size=...))`；色盲安全 `scale_color_viridis_d()` 或 `scale_*_brewer()`。
- 导出：`ggsave('f.pdf', width=89, height=60, units='mm', dpi=300)`（直接按期刊列宽 mm 出图）。

【链接】https://ggplot2.tidyverse.org/ ；书 https://ggplot2-book.org/

【已知坑】需 R 环境；默认灰底主题不适合投稿要换；图例/分面标签精排较繁。

---

## Vega-Altair (Python)

【是什么】Python 声明式可视化，基于 Vega-Lite 语法（JSON）。

【可复用方法】
- 核心 API：`alt.Chart(data).mark_point().encode(x='hp:Q', y='mpg:Q', color='origin:N')`——mark_* 定图形，encode 映射通道，类型简写 `:Q`量 `:N`名 `:O`序 `:T`时间。
- 保存 `chart.save('f.png'/'.svg'/'.pdf'/'.html'/'.json')`，按扩展名定格式；JSON 是底层 Vega-Lite spec（`to_json()`）。
- 图像/离线 HTML 导出需 `pip install vl-convert-python`（替代旧 altair_saver，无外部依赖）。
- 分辨率：`chart.save('f.png', ppi=200)` 或 `scale_factor=2`；离线自包含 `save(..., inline=True)`；`chart.to_url()` 生成 Vega 在线编辑器链接。
- 交互：`selection`/`interactive()` 做联动（论文一般导静态，但可做补充材料网页）。

【链接】https://altair-viz.github.io/ ；保存 https://altair-viz.github.io/user_guide/saving_charts.html

【已知坑】大数据集默认 5000 行上限（需 `alt.data_transformers.disable_max_rows()`）；PDF/PNG 依赖 vl-convert；精细像素级排版不如 matplotlib。

---

## Graphviz

【是什么】DOT 语言描述图、自动布局的工具，适合自动排关系图/依赖图/流程。

【可复用方法】
- DOT：`digraph G { rankdir=LR; node[shape=box,style=rounded]; A->B->C; }`。
- 布局引擎选择：**dot**（有向分层，流程/结构图首选）、**neato/fdp**（无向弹簧模型）、**sfdp**（大图）、**circo**（环形）、**twopi**（放射）、osage/patchwork（treemap 类）。
- 关键属性：`rankdir`(TB/LR) 方向；`rank=same/min/max` 同级约束；`ranksep`/`minlen` 间距；cluster 子图（名以 `cluster` 开头）画成圈定矩形；`compound=true` + `lhead/ltail` 让边指向整个 cluster；`constraint=false` 不参与排名。
- Python 封装 `graphviz` 包：`Digraph()`，`.render('out', format='pdf')`。

【链接】https://graphviz.org/docs/layouts/dot/ ；Python https://graphviz.readthedocs.io/

【已知坑】自动布局对"想要的具体位置"控制弱；密集图易乱；精排不如手工 draw.io/TikZ。

---

## Mermaid

【是什么】文本→图的语法，GitHub/GitLab/Notion/Obsidian 原生渲染，diagram-as-code。

【可复用方法】
- 支持类型（声明关键字）：flowchart、sequenceDiagram、classDiagram、stateDiagram、erDiagram、journey、gantt、pie、quadrantChart、requirementDiagram、gitGraph、C4Context、mindmap、timeline、sankey-beta、xychart-beta、block-beta、kanban、architecture-beta；新增 radar/treemap/venn 等。
- 定义都以类型声明开头；注释 `%%`；YAML frontmatter 配置：`config: layout: elk / look: handDrawn / theme: forest`。
- 渲染/导出：mermaid.live 在线编辑器导 SVG/PNG；CLI `npx @mermaid-js/mermaid-cli mmdc -i in.mmd -o out.svg|png|pdf`；JS API `mermaid.render()`。
- 防错：`end` 单词破 flowchart 需引号；特殊字符文本加引号；`%%{ }%%` 在注释里会被误当指令。

【链接】https://mermaid.js.org/intro/syntax-reference ；编辑器 https://mermaid.live

【已知坑】拼写错静默失败；细排版/精确配色弱；出版级矢量质量一般，正文大图建议 TikZ/draw.io，Mermaid 适合草图与文档内嵌。

---

## TikZ / PGFPlots (LaTeX)

【是什么】LaTeX 内的矢量绘图（TikZ）与科学绘图（PGFPlots），与论文排版同源、字体公式完美一致，出版级矢量首选。

【可复用方法】
- PGFPlots：`\begin{axis}[xlabel=,ylabel=,legend pos=north west] \addplot table {data.dat}; \addplot {x^2}; \end{axis}`，`\addplot` 接表格/坐标/函数/文件。
- 可直接读外部数据文件画图，复现性强；坐标/误差棒/对数轴/多轴原生支持。
- 字体与正文 LaTeX 一致（公式标签无缝）；输出矢量随 PDF 编译，无需另存。
- 大图建议 `externalize` 库缓存编译产物，否则编译慢。

【链接】PGFPlots 手册 https://tikz.dev/pgfplots/ ；`\addplot` https://tikz.dev/pgfplots/reference-addplot

【已知坑】学习曲线陡；编译慢（externalize 缓解）；交互探索差，适合最终定稿出图而非数据探索。

---

## diagrams.net (draw.io)

【是什么】免费图编辑器（Apache-2.0），`.drawio` 即 XML（mxGraph 模型），可手工+可程序化编辑，适合精排框架图/系统图。

【可复用方法】
- 文件结构：`mxGraphModel > root > mxCell`；`vertex="1"` 是节点、`edge="1"` 是连线；`mxGeometry` 定位与尺寸；`style` 是分号分隔 `key=value`（如 `rounded=1;fillColor=#dae8fc;`）。
- 程序化：标准 XML，可用 Python `xml.etree.ElementTree` 或 Node `fast-xml-parser` 改 value/style/几何后回写——适合"代码生成/批量改图"。
- 导出：SVG（矢量）、PNG/JPEG、PDF、HTML 嵌入。
- 集成：VS Code 扩展 "Draw.io Integration"（Henning Dieterichs）直接编辑 `.drawio`；桌面版 CLI `drawio --export --format pdf --output out.pdf in.drawio`（可 `--page-index`）；存储接 Drive/GitHub/Confluence 等。

【链接】https://www.drawio.com/ ；VS Code 扩展 https://marketplace.visualstudio.com/items?itemName=hediet.vscode-drawio

【已知坑】2024-12 起仓库部分源被替换为压缩版、一般不接外部 patch；CLI 导出需桌面版 Electron 环境（headless/CI 需 xvfb）。

---

## BioRender

【是什么】网页版生命科学制图工具，5 万+经专家验证的科学准确图标 + 模板，无需设计技能即可做机制图/实验流程图。

【可复用方法】
- 规划层面可借鉴：图标库覆盖细胞/分子/动物/设备，适合机制示意、实验工作流（wet-lab pipeline）、通路图。
- 模板加速：CONSORT/通路/实验设计类有现成模板。
- 高校常有 premium 许可（按院系）；投稿/出版需注意其授权条款（免费层有水印/出版限制，发表通常需 publication-license）。

【链接】https://www.biorender.com/

【已知坑】非开源、付费，免费层导出/出版受限；闭环 SaaS，无 diagram-as-code（不可脚本批量生成）；偏生命科学，CS/工程领域图标少。本页未给出免费层精确导出格式，投稿前需查 BioRender 官方授权页。

---

## 出版商图宽硬规格核查表（mm，研究日期 2026-06）

【核查方法与诚实声明】只有 Nature 的 figure guide 子站对 curl 返回 HTTP 200、数值逐字实测；Science(science.org)、Cell(cell.com)、Elsevier(elsevier.com)、IEEE(ieee.org)、MDPI(mdpi.com) 的作者指南页对 curl 与 WebFetch 一律返回 **HTTP 403（付费墙/反爬）**，WebSearch 仅返回标题+URL 无正文。故下表除 Nature 外均标 **⚠️付费墙未实测**，数值为各出版商长期公开作者指南通行值，**投稿前必须以目标刊当期官网为准**。

| 出版商/刊 | 单栏 | 中间档 | 双栏/整页 | 最大高 | 核查状态 |
|---|---|---|---|---|---|
| **Nature** | 89 | — | 183 | 170 | ✅ curl 实测 www.nature.com/nature/for-authors/final-submission（HTTP 200，"89 mm" / "183 mm" / 字号 "5 pt"–"7 pt" 逐字命中；最大高 170 mm 留题注空间） |
| **Science (AAAS)** | ≈55 (5.5 cm) | 双栏 ≈120 (12 cm) | 整页 ≈183 (18.3 cm) | 约 240(版心) | ⚠️付费墙未实测；三档制，**无"175"档**（原笔记 175 系错值） |
| **Cell Press** | 85 | 1.5 栏 114 | 整页 174 | 约 240 | ⚠️付费墙未实测；整页 **174 非 178**（原笔记 178 系错值） |
| **Elsevier**（含 db01 Computers and Electronics in Agriculture、Biosystems Engineering、Animal 等） | 90 | 1.5 栏 140 | 双栏 190；最小图 30 | — | ⚠️付费墙未实测；线稿矢量或 ≥300 DPI |
| **IEEE**（IEEEtran 双栏版式，含 TPAMI/TIP/TGRS 等） | ≈88.9 (3.5 in) | — | 文本宽 ≈181.9 (7.16 in) | — | ⚠️付费墙未实测；以 \columnwidth/\textwidth 为准 |
| **MDPI**（含 db01 Animals、Agronomy、Sensors、Remote Sensing） | 单列版式正文宽 ≈170，图按此宽或整数分数 | — | ≈170 | — | ⚠️付费墙未实测；线稿/组合图建议 1000 DPI、照片 ≥300 DPI、TIFF/PNG/EPS |

【db01 目标刊补充】db01 收录的畜牧/农业刊多为上述出版商旗下：Computers and Electronics in Agriculture、Biosystems Engineering、Journal of Dairy Science、Animal、Animal Feed Science and Technology、Poultry Science 等→按 **Elsevier** 规格（单栏 90/1.5 栏 140/双栏 190）；Animals、Agronomy→按 **MDPI**（≈170 单列宽）；中文刊（农业工程学报、农业机械学报）通常 A4 双栏，正文栏宽约 84 mm、整页约 175 mm，但官网未给精确图宽硬规格，标**待核查**，以投稿系统模板为准。

【单位换算备忘】1 in = 25.4 mm；3.5 in = 88.9 mm；7.16 in = 181.9 mm；常用导出 `ggsave(width=90, units='mm', dpi=300)` 或 mpl `figsize=(90/25.4, h/25.4)`。

---

## 横向选型小结（规划时给 m11 的工具建议）

- **统计图/定量结果**：Python 栈 matplotlib（精排）+ seaborn（统计便捷）；R 用户 ggplot2；要 mm 级期刊列宽直接 `ggsave`/`savefig` 设 size。交互补充材料用 Plotly/Altair。
- **出版级矢量、公式标签多**：TikZ/PGFPlots（与 LaTeX 同源）。
- **框架图/系统图/技术路线，要精排可编辑源**：diagrams.net（XML 可程序化），或 TikZ。
- **关系/依赖/自动布局**：Graphviz。
- **文档内嵌草图/流程，快速**：Mermaid。
- **生命科学机制/实验流程图**：BioRender（注意出版授权）。
- **从自然语言快速出示意图（可接受 AI 生图、需人工核字）**：Scientific Schematics 式迭代生图+评分。
- **配色统一**：全程 Okabe-Ito（离散）+ viridis 系（连续），灰度+色盲双测。
