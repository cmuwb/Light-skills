---
name: light-figure-drawing
description: 从顶会大牛角度进行专业绘图与组图。当用户需要把规划好的图实际画出来时使用。按情况用 Python(matplotlib/seaborn/plotly/altair)、R(ggplot2)、MATLAB、Visio、Origin、LaTeX/TikZ、Illustrator、PowerPoint 等。审美统一、专业清晰、配色合理、字体规范、线条清楚、高分辨率，适合直接投稿。不仅画图，还从论文表达角度判断怎么排、怎么组、怎么标注、怎么突出重点。
---

# 专业绘图与组图

## 工具选择（按图类型，附核心调用）
- 统计图/可复现图（首选）：
  - **matplotlib**：最可控。组图 `plt.subplots(figsize=(7,5), constrained_layout=True)`，不规则布局用 `GridSpec`（跨格 `gs[0,:]`）。
  - **seaborn**：统计/分布/分类图。`sns.set_theme(style="ticks", context="paper", palette="colorblind")` + `sns.despine()`；分面拼图用 figure-level（`relplot/catplot` 的 `col=/row=`），手动拼图用 axes-level（`scatterplot(ax=...)`）。
  - **plotly**：交互/3D，静态投稿 `fig.write_image("f.pdf", scale=3)`（需 `kaleido`），`template="simple_white"`。
  - **altair**：声明式、可复现强。`chart.save("f.svg", scale_factor=3)`（需 `vl-convert-python`），拼图用 `c1 | c2` / `c1 & c2`。
  - **ggplot2(R)**：`+ theme_classic() + scale_color_viridis_d()`，拼图用 `patchwork`（`p1+p2` 且 `plot_annotation(tag_levels="a")` 自动标号）。
- 框架图/流程图/结构图：
  - **Graphviz**（自动布局）：`digraph{rankdir=LR; node[shape=box,style=rounded]; A->B}`，选对引擎 `dot`(分层)/`neato`(无向)/`fdp`(大图)，`rank=same` 对齐同层。
  - **TikZ/PGFPlots**（字体与正文统一）：`\begin{axis}...\addplot table{data.dat};`，导言区 `\pgfplotsset{compat=1.18}` 统一样式，大图用 `external` 库缓存。
  - **Mermaid**（文档/初稿）：`graph TD; A[框]-->|标签|B{判断}`，`mmdc -i in.mmd -o out.svg` 导出。
  - 精修拼版：Illustrator / Inkscape。
- 精细科学图/期刊曲线：
  - **Origin**：Export Graphs 按出版商精确设 Width/Height+DPI（TIFF 600dpi），可 `Export as AI` 转 Illustrator；.otp 模板固化风格。
  - **MATLAB**：`exportgraphics(ax,"f.pdf","ContentType","vector")` 出矢量、`"Resolution",600` 出位图；组图用 `tiledlayout` + `nexttile`（`TileSpacing="compact"`）。
- 示意/机制图/graphical abstract：**BioRender**（生命科学图标库，注意导出授权与分辨率）。
- 组图/排版：matplotlib subplots/GridSpec、Illustrator（图层+画板对齐）、python-pptx（`add_picture(..., width=Inches(3))`，layout[6] 空白页）。
优先可复现(代码)方案，便于改数据重出；最终精修/拼大图再进 Illustrator/Inkscape。具体决策同 a09。

## 一行套刊样式与导出脚本（本技能自带资产）
- **样式**：`plt.style.use("assets/publication.mplstyle")` 是通用底；按刊叠加 `plt.style.use(["assets/publication.mplstyle","assets/nature.mplstyle"])`（或 `science.mplstyle`）。三者均为 Okabe-Ito 色盲安全色环 + 无衬线 + 矢量文字可编辑（pdf/ps fonttype42、svg 不转曲）。
- **导出**：`scripts/figure_export.py`
  - `save_publication_figure(fig, basename, formats=("pdf","png","svg"), dpi=600)` 多格式 + DPI，自动建目录、强制文字可编辑。
  - `save_for_journal(fig, basename, journal, column)` 按刊规格设物理尺寸（mm→in）再导出，返回 `(paths, info)`。
  - `check_figure_size(fig, journal=, column=)` 校验栏宽（mm）与最小字号（pt），返回合规报告。
  - `JOURNAL_SPECS` 内置逐刊规格字典（含 `verified` 标记）。
- **配色**：`scripts/color_palettes.py`
  - `OKABE_ITO` / `OKABE_ITO_LIST` 8 色常量；`sequential_cmap()` / `diverging_cmap()` / `discrete_cmap()`；`apply_palette()` 设当前色环。
  - `to_grayscale()`、`simulate_cvd(kind=deuteranomaly/protanomaly/tritanomaly)`、`preview_palette()` 出原色/灰度/三种色盲对照图。有 `colorspacious` 走精确算法，缺则自动降级线性近似（`cvd_backend()` 可查）。
- **诚实性 lint**：`scripts/figure_integrity_lint.py` —— 静态扫绘图代码，提示常见误导：y 轴偷偷截断、双 y 轴伪相关、bar 无误差棒、误差棒未注明类型、jet/rainbow 色图、3D 扭曲。`python scripts/figure_integrity_lint.py --file plot.py`（含 `--selftest`）。规范见 `references/figure_integrity.md`。只提示不阻断，最终判断交作者。
- **示例**（均可 `python examples/xxx.py` 跑通，Agg 存图）：
  - `example_matplotlib_multipanel.py`：GridSpec 不规则布局 + (a)(b)(c) 标号 + 误差棒 + 显著性星标。
  - `example_seaborn_stats.py`：箱线/小提琴/条形统计对比 + despine。
  - `example_framework.dot` + `example_framework_render.py`：Graphviz 框架图，有 `dot` 二进制则渲染，否则降级 matplotlib 块图。

## 逐刊硬规格表（栏宽 mm + DPI + 格式 + 字号下限）
> verified=实测：已 curl 该刊作图规格页并记 HTTP 码；其余为依公开指南整理但本次未逐项实测（多因付费墙/反爬 403），投稿前请以目标刊“最新”作者须知为准。

| 期刊 | 单栏宽 | 双栏/整版宽 | 字号下限 | 线条 DPI | 半调/照片 DPI | 首选格式 | 实测 |
|---|---|---|---|---|---|---|---|
| **Nature** | 89 mm | 183 mm | 5 pt（面板标 8pt 粗体 a,b,c；正文 ≤7pt） | 600 | 300–600 | PDF/TIFF/EPS（文字勿转曲，Helvetica/Arial） | ✅ HTTP200 |
| **PLOS** | 83 mm | 140 mm(1.5栏) / 190 mm | 8 pt（8–12pt，Arial/Times/Symbol） | 600 | 300–600 | **仅 TIFF/EPS**；789–2250px@300dpi，<10MB | ✅ HTTP200 |
| **Science (AAAS)** | ~55 mm | ~121 mm / 整版 183 mm | 5 pt（常 6–9pt） | 600 | 300 | EPS/PDF/AI/TIFF，无衬线 | ⚠️ 页 403 未实测 |
| **Cell Press** | 85 mm | 174 mm | 5 pt | 1000（线条） | 300 | PDF/AI/EPS/TIFF | ⚠️ 页 403 未实测 |
| **IEEE** | 88.9 mm(3.5in) | 181 mm(7.16in) | 8 pt | 600 | 300 | PDF/EPS/TIFF | ⚠️ 未逐项实测 |
| **Elsevier** | 90 mm | 140 mm(1.5栏) / 190 mm | 7 pt | 1000（线条） | 300（彩/灰）、组合 500 | PDF/EPS/TIFF | ⚠️ 页 404 未实测 |

数值与 `JOURNAL_SPECS` 同源，可在代码里直接读取（如 `figure_export.JOURNAL_SPECS["nature"]`）。

## 审美与规范（投稿级）
- **配色**：色盲友好——matplotlib/seaborn 用 `viridis/cividis/colorblind`，R 用 `scale_*_viridis`，连续数据避免 jet/rainbow。同一论文统一调色板（登记 db07）；不超过必要颜色数（离散 ≤8 类，超出手动指定）。
- **字体**：与正文一致(常 Times/Arial)；字号在缩放后仍可读(≥6–8pt)。seaborn 用 `context="paper"` 整体定字号；按目标栏宽设物理尺寸（单栏≈3.5in、双栏≈7.2in），避免投稿后被缩放失真。
- **线条/标记**：区分清楚，黑白打印仍可辨(线型 linestyle + 标记 marker 双重区分，不仅靠颜色)；线宽用绝对值(pt)。
- **分辨率/格式**：矢量优先(PDF/SVG/EPS)；位图线条图 ≥600dpi、含照片 ≥300dpi。**文字保持可编辑**便于二次精修：matplotlib 设 `rcParams["pdf.fonttype"]=42`；R 用 `device=cairo_pdf`；MATLAB 用 `exportgraphics ContentType=vector`。EPS 不支持透明，要透明背景用 PDF/SVG。
- **元素**：坐标轴标签+单位、图例、误差棒、显著性标记，去 chart junk（多余网格/边框，`sns.despine()` 或 `theme_classic()`）。
- **caption**：自洽，能独立读懂。

## 组图逻辑
- 同类对齐、共享坐标/色标、统一尺寸。matplotlib 用 `constrained_layout` 自动对齐共享色标；ggplot 用 `facet_*` 或 patchwork；MATLAB 用 `tiledlayout`。
- 子图编号(a)(b)(c)，标题精简。patchwork `tag_levels="a"` 可自动标号。
- 用留白和分组体现层次，突出主结果。
- 拼最终大图：各子图导出矢量(SVG/PDF) → Illustrator/Inkscape 置入 → 图层管理 + Align 对齐 + 统一字体线宽 → 加标号 → 按期刊要求导出(PDF/EPS/TIFF，印刷常 CMYK)。命令行拼/转格式可用 Inkscape 1.x `--export-type` / `--actions`。

## 投稿前自查清单
- 物理尺寸=目标栏宽？字号缩放后 ≥6–8pt？
- 颜色色盲安全？黑白打印可辨（线型+标记）？
- 矢量输出且文字可编辑（fonttype42 / svg.fonttype=none / cairo_pdf / vector）？位图 dpi 达标？
- 坐标轴有标签+单位？图例/误差棒/显著性标记齐全？去除 chart junk？
- **诚实性（不误导，审稿人必查）**：详见 `references/figure_integrity.md`，可跑 `scripts/figure_integrity_lint.py` 扫绘图代码。要点：误差棒在 caption 注明是 SD/SEM/95%CI 并写明 n=；y 轴截断必须显式标断点（不偷偷截断放大差异）；慎用双 y 轴（易制造伪相关，能拆分就拆分）；小样本优先散点/箱线展示原始分布，别用 bar 掩盖分布；坐标轴范围不为夸大效果而人为收紧/放大。
- 全论文调色板/字体/线宽一致（对照 db07）？

## 工作方式
按 m09 的规划卡逐图实现：给出可运行代码或源文件 + 预览说明 + 设计理由。需要数据时回 m06/m02 取。多次打磨直到达到顶会观感。
- **栏宽不臆测**：直接读规划卡的 `target_journal` 与 `column` 字段，原样传给 `save_for_journal(fig, basename, journal=target_journal, column=column)`——物理栏宽 mm、figsize、最小字号全由 `JOURNAL_SPECS` 锁定。规划卡缺这两字段时回 m09 补，不要自行猜测栏宽（猜错整张图物理尺寸作废）。`column` 取值须为该刊实有键（`single`/`double`/`full`/`onehalf`）。

## 产出
图文件(矢量+位图) + 生成代码/源文件 + 风格说明(写入 db07 与 db09，供 a07 统一) + **figure manifest**。
- **figure manifest**：交付 m07 的单一工件，把"图文件↔图号↔caption"绑定。逐图一行，含：`figure_id`(沿用 m09 规划卡的 F#/T# 编号，与 m07 模板 `[图位 F1]`/`[表位 T1]` 占位对齐) + 图片文件路径(矢量+位图) + 最终 caption + 放置章节 + target_journal/column。m07 据此把占位替换为实图与图号，无需回查规划卡。
  示例：
  ```yaml
  - figure_id: F1
    files: [figs/framework.pdf, figs/framework.png]
    caption: "图1. 方法整体框架：左输入经解耦表征模块……"
    section: 方法-框架
    target_journal: nature
    column: single
  ```

## 衔接
受 m09 驱动；交 m12 排版插入；风格一致性由 a07 跨图维护。

---
各工具真实 API/参数/导出命令/已知坑的逐条笔记见 references.md。
