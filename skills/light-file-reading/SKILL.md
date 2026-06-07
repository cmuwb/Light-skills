---
name: light-file-reading
description: 强大地读文件并学习——Word、PDF、PPTX、Excel、CSV、图片、视频、代码、压缩包等。当用户提供任何文件、问"这个文件讲了什么"、或任务需要理解已有材料时使用（常驻，自动触发）。不只提取文字，而是理解结构、逻辑、图表、数据、实验结果、格式要求、章节关系、视觉风格、隐含要求与可复用内容，并转化为可执行任务。
user-invocable: false
---

# 多格式文件深度理解

## 触发
任何涉及已有文件的任务自动启用，无需显式调用。

## 即用脚本（scripts/，均带自检，可直接 python 运行）
- **`scripts/pdf_ops.py`**：`read_meta` / `extract_text(layout)` / `extract_tables`→DataFrame（pdfplumber），`merge` / `split` / `rotate`（pypdf）。`python pdf_ops.py` 跑合成自检。
- **`scripts/docx_read.py`**：`read_paragraphs` / `read_headings`（章节骨架）/ `read_runs`（样式提取）/ `read_tables` / `read_layout`（页边距纸张）。python-docx，**不读修订**。
- **`scripts/xlsx_read.py`**：`list_sheets` / `read_formulas`（不求值）/ `read_values`（缓存）/ `profile`（pandas 数据画像）。openpyxl **无求值引擎**，算值需 LibreOffice 重算。
逐格式完整 copy-paste 代码块见 `references/`（PDF-REF / DOCX-REF / XLSX-REF / PPTX-REF，渐进式按需读）。

## 按格式选工具（见 a09，细节见 references.md）
- **PDF**：机器生成 PDF 用 `pdfplumber` 抽文本(`extract_text(layout=True)`)与表格(`extract_tables`→DataFrame，策略 lines/text，调 snap_tolerance)；结构操作(合并/拆分/旋转/加密/书签)用 `pypdf`；扫描件 OCR 走 `pytesseract+pdf2image`；快速归一为 md 用 `markitdown file.pdf -o out.md`。论文 PDF 关注章节/图表/表格定位，可用 `page.crop(bbox)` 锁区域。pdfplumber/pypdf 均无 OCR、不读纯图。
- **Word(.docx)**：读用 `pandoc in.docx -o out.md`（带 `--track-changes=all` 把增删/批注包成 insertion/deletion/comment span 保留作者+时间、`--extract-media=./media` 导图、引文 `--citeproc --bibliography refs.bib --csl apa.csl`）或 `python-docx` 遍历 paragraphs→runs 读样式/题注；提取模板格式要求(页边距/字号/编号/引用风格)。需精确改原文/redline 时走「解包→直接改 XML→重打包」：插入 `<w:ins w:author=.. w:date=..>`、删除 `<w:del>` 内用 `<w:delText>`，最小化只标真正变动的词。注意 python-docx 不读修订、无渲染；pandoc AST 不保页边距等精确格式。
- **PPTX**：读用 `python -m markitdown deck.pptx` 抽文本，再渲染成图(`soffice --headless --convert-to pdf` + `pdftoppm -jpeg -r 150`)做视觉理解；逐页学版式/配色/字号层级/留白(标题36-44pt、正文14-16pt、深浅"三明治"结构)，喂 db06。改/建幻灯片后强制 QA 循环：转图视觉核对→列问题→修→重验受影响页(一处修复常引新问题)→至无新问题；占位符残留用 `markitdown out.pptx | grep -iE "xxxx|lorem|ipsum"`。
- **Excel/CSV**：`pd.read_excel(sheet_name=None)` 读全部 sheet 做数据画像(`info/describe`)；要读公式/格式用 `openpyxl.load_workbook`(读缓存值加 `data_only=True`，但注意 openpyxl 无求值引擎、保存会毁公式；要重算用 LibreOffice `recalc.py` 扫 `#REF!/#DIV/0!`)。关注多 sheet 关系、表头层级、跨表引用(`Sheet1!A1`)、远右列(FY 数据常在 50+ 列)、DataFrame 行号比 Excel 少 1(表头偏移)。转 m02。
- **图片**：视觉理解图表/截图/效果图/框架图(转 db07)。
- **视频**：抽帧/转写要点。
- **代码**：读结构、依赖、逻辑、可复用模块。
- **压缩包**：解包后递归按类型处理。
统一格式归一管线可选：`MarkItDown`(转 md 喂 LLM，`md.convert(path).text_content`，支持 Office/PDF/音视频/ZIP/YouTube；图片描述传 `llm_client`+`llm_model`，复杂文档接 `docintel_endpoint` 走 Azure)、`unstructured`(`partition(filename=..)` 切成 Title/NarrativeText/Table/ListItem element，`partition_pdf` 策略 fast(有文本层)/hi_res(detectron2 版面分析、可 `extract_image_block_types=["Image","Table"]`)/ocr_only(多栏无文本层)/auto，表格 `metadata.text_as_html`，供 RAG 分块)、`Apache Tika`(tika-server REST，PUT `/tika` 抽文本、`/rmeta` 递归元数据+内嵌文档、`/unpack` 抽附件、`/detect/stream` 探 MIME，1000+ 格式)、`LiteParse`(本地无模型、带 bbox 坐标做 visual citation，输出 JSON/版面文本/页面 PNG，复杂文档官方建议改用 LlamaParse)、`Pandoc`(格式互转)。研究流监控可参考 Paperzilla(arXiv/bioRxiv 等聚合按主题过滤，CLI `pz feed <id> --must-read --since --json`、Atom 订阅、MCP/API 消费)、Open Notebook(自托管多源 RAG 对话+向量检索+多说话人播客，FastAPI/SurrealDB/18+ 模型，支持 MCP)。

## 不止提取——要理解
读完产出"理解笔记"，而非原文堆叠：
- **结构与逻辑**：章节关系、论证链、叙事骨架。
- **关键内容**：问题/方法/数据/实验结果/结论。
- **格式与要求**：模板规范、字数、引用风格、隐含约束。
- **视觉风格**：配色/版式/图表风格(供前端 a05 / PPT m16 / 图表 m11)。
- **可复用内容**：能直接拿来用的段落/数据/图/结构。

## 转化为可执行任务
把理解结果导向下一步：论文修改(m08)、PPT(m16)、实验分析(m06)、数据处理(m02)、图表重绘(m11)、项目整理(a06)、引用提取(m10)等。明确"这个文件→接下来能做什么"。

## 合规
受版权全文不外传；敏感文件(密钥/隐私)按 key 名引用不回显值(CONVENTIONS §5、a10)。

## 衔接
理解笔记与可复用资源登记到项目库 db09。

---
即用脚本见 `scripts/`（pdf_ops / docx_read / xlsx_read，均自检通过）。逐格式完整代码块与真实端点/参数/已知坑见 `references/`（PDF-REF / DOCX-REF / XLSX-REF / PPTX-REF）。综合工具核查笔记见 `references.md`。
