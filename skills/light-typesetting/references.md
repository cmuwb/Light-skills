# light-typesetting 参考工具笔记

逐工具核查笔记。每条尽量给真实命令/选项/字段与可点链接。无法核实者如实标注。

## Venue Templates（期刊/会议官方模板）
【是什么】出版方为每个 venue 提供的官方排版骨架（LaTeX `.cls` 或 Word `.docx`），规定版式、字号、页边距、参考文献样式与匿名规则。不是单一软件，而是分发在各出版方 author kit、CTAN、Overleaf gallery 上的一类资产。
【可复用方法】
- 取模板优先级：venue 官网 author kit > Overleaf 官方模板页 > CTAN 包。永远不要手搓版式去"模仿"官方样式。
- Overleaf gallery 按标签检索：`overleaf.com/gallery/tagged/conference-paper`、`/tagged/acm`、`/tagged/academic-journal`，可直接 "Open as Template" 拿到可编译工程。
- 模板里通常自带 `bare_*.tex`（IEEE）或 `sample-*.tex`（ACM）骨架文件，从骨架改而不是从空文件起。
- 关键校验项：单/双栏、页数上限、字号、参考文献 `.bst`/CSL、是否要求匿名（双盲）。
【链接】
- Overleaf gallery: https://www.overleaf.com/gallery/tagged/conference-paper
- CTAN: https://ctan.org/
【已知坑】会议每年模板可能更新（如 NDSS 提供 `bare_conf_LAST-X2026.tex` 年度版本）；务必用当届指定版本，旧版会被 desk-reject。

## PACSOMATIC
【是什么】**未能核实。** 以该名称做 WebSearch 未找到任何对应的排版工具、库或项目；最接近的命中是无关的个人站点 `pacomatic1.github.io`。疑似名称有误或为私有/小众工具。
【建议】若用户提到此名，先向用户确认全称/来源链接，再决定是否采用；不要假定其功能。
【链接】无可靠来源。

## Overleaf
【是什么】基于云的协作式 LaTeX 编辑器，自带完整 TeX Live、实时协同、模板库、版本历史。
【可复用方法】
- 编译引擎在 Menu 里切换：pdfLaTeX / XeLaTeX / LuaLaTeX；中文工程选 XeLaTeX 或 LuaLaTeX 配 `ctex`。
- 后台用 latexmk 驱动多轮编译（含 bibtex/biber）。可在工程放 `latexmkrc` 自定义。
- 同步方式：付费版支持 Git（`git clone https://git.overleaf.com/<project-id>`）与 GitHub 双向同步；免费可用 "Download as zip" 导出可编译源工程。
- "Open as Template" 直接克隆 venue 官方模板。
【链接】https://www.overleaf.com/learn
【已知坑】免费版有单次编译超时；大工程或大量 TikZ 易超时，可关闭草稿包或本地编译。Git/GitHub 同步是付费功能。

## LaTeX
【是什么】基于 TeX 的文档排版系统，学术论文事实标准。
【可复用方法（论文常用包）】
- 数学：`amsmath`、`amssymb`、`mathtools`；定理 `amsthm`。
- 图表：`graphicx`（`\includegraphics`）、`booktabs`（三线表 `\toprule/\midrule/\bottomrule`）、`subcaption`（子图）。
- 算法：`algorithm2e` 或 `algorithmic`/`algpseudocode`(algorithmicx)。
- 交叉引用：`\label`/`\ref`，配 `cleveref` 用 `\cref`（自动带 "Fig./Eq." 前缀，注意 `\usepackage{cleveref}` 要最后加载）。
- 中文：`ctex` 宏包/文档类，配合 XeLaTeX/LuaLaTeX。
- 参考文献：传统 `bibtex` + `.bst`，或现代 `biblatex` + `biber`（后者排序/本地化更强）。
【链接】https://en.wikipedia.org/wiki/LaTeX ；包文档查 https://ctan.org/pkg/<name>
【已知坑】`cleveref` 与 `hyperref` 加载顺序敏感（hyperref 先、cleveref 后）；biblatex 与 bibtex 工作流不可混用。

## TeX Live
【是什么】跨平台的完整 TeX 发行版，含 `tlmgr` 包管理器。
【可复用方法】
- 装包：`tlmgr install <pkg>`；更新自身后再更新全部：`tlmgr update --self` 然后 `tlmgr update --all`。
- 查包/找文件归属：`tlmgr search --global --file <name.sty>`。
- 安装方案（scheme）：`scheme-full`（全量，省去缺包烦恼）vs `scheme-basic`/`scheme-small`（轻量，按需补包）。
- 无 root 时可装到 `~/texmf`，或用 TinyTeX。
【链接】https://tug.org/texlive/ ；tlmgr 手册 https://manpages.ubuntu.com/manpages/questing/man1/tlmgr.1.html
【已知坑】发行版有年度版本（texlive 2024/2025…），`tlmgr` 不能跨年度大版本升级，跨年需重装；CTAN 镜像校验失败时换镜像。

## latexmk
【是什么】Perl 写的 LaTeX 自动化构建工具，自动判定需要跑几轮、何时跑 bibtex/biber 直到引用/目录收敛。
【可复用方法（核心选项）】
- `latexmk -pdf file.tex`：用 pdflatex 出 PDF。`-pdfxe`/`-xelatex` 用 XeLaTeX；`-pdflua`/`-lualatex` 用 LuaLaTeX。
- `-pvc`：持续预览，监视源文件改动自动重编。
- `-interaction=nonstopmode`：报错不停顿，适合自动化/CI。
- `-bibtex` 强制、`-bibtex-` 禁止跑 bibtex。
- `-shell-escape`：开启 `\write18`（minted、部分 TikZ 外部化需要）。
- 清理：`-c` 删中间文件（保留 PDF），`-C` 连 PDF 一起删。
- `-f` 出错继续，`-g` 强制重跑，`-outdir=DIR` 指定输出目录。
- 配置文件 `latexmkrc`/`.latexmkrc`：设 `$pdf_mode=1`（pdflatex）/`4`（lualatex）/`5`（xelatex）、`$pdflatex`、`$bibtex_use`、`@default_files`。
【链接】https://mg.readthedocs.io/latexmk.html ；手册 https://man.archlinux.org/man/latexmk.1
【已知坑】中文/特殊字体务必用 `-xelatex`/`-lualatex`，否则字体报错；minted 需配合 `-shell-escape`；biber 工程要确保 `.bcf` 触发 biber 而非 bibtex。

## TinyTeX
【是什么】基于 TeX Live 的精简发行版，主打"够用 + 缺包自动装"，由 R 的 `tinytex` 包维护，亦可独立安装。
【可复用方法】
- R 内安装：`tinytex::install_tinytex()`；编译：`tinytex::latexmk("file.tex")`，编译时**自动探测并安装缺失的 LaTeX 包**（最省心的特性）。
- 装包：`tinytex::tlmgr_install("<pkg>")`；底层仍是 `tlmgr`。
- 命令行也有 `tlmgr`/`pdflatex`/`xelatex` 包装器；安装目录 `~/.TinyTeX`（或 `~/Library/TinyTeX`）。
- 适合 CI / 容器 / 个人机：初装小（几百 MB），按需膨胀。
【链接】https://yihui.org/tinytex/ ；https://github.com/rstudio/tinytex
【已知坑】超大依赖（如完整 CJK、某些字体包）首次自动装会变慢；需联网；R 工作流外用要确认 PATH 已含 TinyTeX bin。

## Pandoc
【是什么】通用文档转换器，markdown/docx/tex/html 等互转，论文场景常用于 md↔docx↔tex 与统一参考文献渲染。
【可复用方法】
- md→docx 套样式：`pandoc in.md -o out.docx --reference-doc=ref.docx`（`ref.docx` 提供标题/正文/题注样式，先 `pandoc -o ref.docx --print-default-data-file reference.docx` 改后复用）。
- md→PDF：`pandoc in.md -o out.pdf --pdf-engine=xelatex`（中文用 xelatex/lualatex）。
- 参考文献：`--citeproc --bibliography=refs.bib --csl=style.csl`，CSL 决定输出样式（如 GB/T 7714 可用对应 CSL）；引用语法 `[@key]`。
- md→tex：`-t latex`；可配 `--template=custom.tex` 与 YAML metadata 头注入标题/作者。
- 提取 docx 内容做转换前清洗，配合下游 LaTeX。
【链接】手册 https://pandoc.org/MANUAL.html ；引用 https://pandoc.org/MANUAL.html#citations
【已知坑】复杂 LaTeX 宏/TikZ 转 docx 会丢失；`--citeproc` 用 CSL（非 .bst），与 LaTeX 的 bibtex/.bst 是两套体系；公式转 docx 走 OMML，复杂公式可能走样。

## DOCX skill（anthropics/skills 的 docx）
【是什么】Anthropic 官方文档技能之一，让模型创建/编辑 Word 文档。
【可复用工作流】
- 新建：从 markdown 经 Pandoc 生成 `.docx`，或用 JS 库 docx (docx-js) 以代码构造段落/表格/样式。
- 编辑既有文件：`.docx` 本质是 zip，解包后直接改 `word/document.xml`（及 `styles.xml`），保留原结构再重新打包，避免整篇重排丢格式。
- 修订/红线（tracked changes）：在 OOXML 里用 `<w:ins>`/`<w:del>` 标记插入/删除，配作者与时间戳。
- 用样式（Styles）控制层级，而非手动字号字体。
【链接】https://github.com/anthropics/skills/tree/main/skills/docx
【已知坑】手改 XML 易破坏文档完整性，改后需校验能正常打开；样式名称需与模板一致才能"套上"。（注：具体实现细节以仓库 SKILL.md 为准，本环境无法抓取页面正文。）

## PDF skill（anthropics/skills 的 pdf）
【是什么】Anthropic 官方文档技能之一，处理 PDF 读取/生成/表单/拆合并。
【可复用工作流】
- 文本/表格抽取：`pdfplumber`（`page.extract_text()` / `extract_tables()`）。
- 页操作：`pypdf` 做 merge/split/rotate、读写元数据、加密。
- 表单填写：`pypdf` 读取 AcroForm 字段并写值。
- 从零生成：`reportlab` 画版面，或先出 HTML/LaTeX 再转 PDF。
【链接】https://github.com/anthropics/skills/tree/main/skills/pdf
【已知坑】扫描件无文本层需 OCR；复杂版式抽取易错行错列；本环境无法抓取页面正文，库分工以仓库 SKILL.md 为准。

## MarkItDown（microsoft/markitdown）
【是什么】微软开源 Python 工具，把各类文件转成 Markdown，主打喂给 LLM/RAG。
【可复用方法】
- 安装 `pip install markitdown`（可带 extras）。
- 用法：`from markitdown import MarkItDown; md = MarkItDown(); print(md.convert("file.pdf").text_content)`。
- 支持 PDF、Word、PowerPoint、Excel、图片（可接 LLM 生成图注）、HTML、音频转写等。
- 提供 MCP server，可作为工具接入 agent。
【链接】https://github.com/microsoft/markitdown
【已知坑】保留的是"内容结构"而非精确版式，不适合做"还原排版"，适合做内容提取/转写；复杂表格与多栏 PDF 可能错乱。

## IEEEtran（IEEE 论文文档类）
【是什么】IEEE 期刊/会议官方 LaTeX 文档类。
【可复用方法】
- `\documentclass[conference]{IEEEtran}`（会议双栏）；期刊用默认/`journal`；`technote`、`peerreview`，计算机学会用 `compsoc` 选项。
- 作者块：`\author{\IEEEauthorblockN{Name}\IEEEauthorblockA{Affiliation\\email}}`。
- 关键词：`\begin{IEEEkeywords}...\end{IEEEkeywords}`；首字下沉 `\IEEEPARstart{T}{he}`。
- 参考文献：`\bibliographystyle{IEEEtran}` + `IEEEtran.bst`。
- 骨架文件：`bare_conf.tex`、`bare_jrnl.tex`、`bare_conf_compsoc.tex` 等。
【链接】README https://tug.org/docs/latex/ieeetran/README ；CTAN https://ctan.org/pkg/ieeetran
【已知坑】双栏下宽图用 `figure*`/`table*` 跨栏并多放在页顶；作者多行对齐需用 `\IEEEauthorblockN` 内换行或 `\and`；匿名投稿手动去作者信息。

## acmart（ACM 论文文档类）
【是什么】ACM 期刊与会议统一文档类。
【可复用方法】
- `\documentclass[sigconf]{acmart}`（会议双栏）；其它格式 `manuscript`（审稿单栏行距大）、`acmsmall`/`acmlarge`/`acmtog`（期刊）、`sigplan`、`sigchi`。
- 匿名审稿：`\documentclass[sigconf,review,anonymous]{acmart}`。
- 版权：`\setcopyright{...}`、`\acmConference[短名]{全名}{日期}{地点}`、`\acmDOI`、`\acmISBN`。
- 分类：CCS concepts `\begin{CCSXML}...\end{CCSXML}` + `\ccsdesc[500]{...}`（从 https://dl.acm.org/ccs 生成）；`\keywords{...}`。
【链接】CTAN https://ctan.org/pkg/acmart ；CCS https://dl.acm.org/ccs
【已知坑】缺版权信息会出红色提示框；`review` 加行号、`anonymous` 自动隐藏作者；最终版需填 venue 提供的 rights/DOI 信息。

## Springer LNCS（llncs.cls）
【是什么】Springer Lecture Notes in Computer Science 会议论文集文档类。
【可复用方法】
- `\documentclass{llncs}`；作者：`\author{Name\inst{1}}`，机构 `\institute{Org\\\email{a@b.c}}`。
- 页眉短名：`\titlerunning{}`、`\authorrunning{}`（作者多时必填，否则页眉溢出）。
- 摘要+关键词：`\begin{abstract}...\keywords{...}\end{abstract}`。
- 参考文献：`\bibliographystyle{splncs04}`（Springer 当前推荐 bst）。
【链接】CTAN https://ctan.org/pkg/llncs ；说明文档 llncsdoc。
【已知坑】Springer 要求用 `splncs04` 而非自选样式；不要随意改页边距/字号，会被退回；作者机构编号用 `\inst{}` 对应。

## elsarticle（Elsevier 论文文档类）
【是什么】Elsevier 期刊投稿用 LaTeX 文档类。
【可复用方法】
- 投稿（双倍行距审稿）：`\documentclass[preprint,review,12pt]{elsarticle}`；终排版式 `[final,5p,times,twocolumn]`，版式选项 `1p`(单栏)/`3p`/`5p`。
- 前置信息放 `\begin{frontmatter}...\end{frontmatter}`，含 `\title`、`\author[label]{}`、`\affiliation[label]{organization=...}`、`\cortext`（通讯作者）、`\begin{abstract}`、`\begin{keyword}`。
- 参考文献：`elsarticle-num`（数字）/`elsarticle-num-names`/`elsarticle-harv`（作者年）。
【链接】CTAN https://ctan.org/pkg/elsarticle ；模板 https://www.overleaf.com/latex/templates/elsevier-article-elsarticle-template/vdzfjgjbckgz
【已知坑】不同期刊指定不同参考文献模型，投前查 guide for authors；`review` 选项才出行号与宽行距，便于审稿批注。

## GB/T 7714 BibTeX 样式（zepinglee/gbt7714）
【是什么】实现中国国标 GB/T 7714-2015 文后参考文献格式的 BibTeX/biblatex 方案，CTAN 包名 `gbt7714`。
【可复用方法】
- BibTeX 路线：`\usepackage{gbt7714}` 提供 `\citet`/`\citep`；`\bibliographystyle{gbt7714-numerical}`（顺序编码）或 `gbt7714-author-year`（著者-出版年）。
- 条目需带 `language`/`langid` 区分中英文（影响 "等" vs "et al."、句点等）；电子/网络资源、arXiv、标准等类型需正确的 entry type 与字段（issue #89/#134 讨论 arXiv DOI、`[C]/[J]` 文献类型标识）。
- 现代 biblatex 路线另有 `biblatex-gb7714-2015`（配 biber）。
【链接】仓库 https://github.com/zepinglee/gbt7714-bibtex-style ；CTAN https://ctan.org/pkg/gbt7714
【已知坑】中英文混排时 `langid` 缺失会导致文献类型标识/缩写错误；InProceedings 不显示 `[C]` 等是字段/版本问题（见 issue #32）；biblatex 版与 bibtex 版不可混用。
