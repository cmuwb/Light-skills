---
name: light-tool-selection
description: 工具选择与多工具协同。根据任务自动判断适合用什么工具——搜索、Python、R、MATLAB、LaTeX、Word、Excel、PowerPoint、Visio、Origin、数据库、Git、前端/后端框架、绘图工具、文献管理工具等（常驻，所有任务后台生效）。不盲目用工具，而是按实际任务选最高效、最稳定、最专业的实现方式。
user-invocable: false
---

# 工具选择与多工具协同

## 原则（常驻）
不为用工具而用工具。每个任务先问：**最高效、最稳定、最专业、最可复现的方式是什么？** 优先可复现(代码/脚本) > 一次性手工；优先项目已有的栈 > 引入新依赖。

## 任务 → 推荐工具映射
- **文献搜索**：arXiv/OpenAlex/Semantic Scholar/Crossref API、agent-browser/browser-use、Exa/Parallel Web。
- **浏览器自动化**：偏 CLI/稳定走 agent-browser(原生 Rust CLI、直连 CDP、accessibility-tree 快照+`@eN` 引用定位、命令间保活、4848 端口可观测面板，先 `agent-browser skills get core` 发现用法)；偏 Python 集成走 browser-use(`Agent(task,llm,browser)`+`await agent.run()`，基于 Playwright，`@tools.action` 加自定义工具，`use_cloud=True` 走 stealth 云浏览器)。
- **数据处理**：pandas(中小) / polars(快) / dask/vaex(超内存)；质量 ydata-profiling/Deepchecks/Great Expectations。
- **统计/科学计算**：Python(statsmodels/scipy/sklearn)、R(高级统计/绘图)、MATLAB(信号/控制/数值)。
- **绘图**：matplotlib/seaborn/plotly/altair、ggplot2、Origin(期刊曲线)、TikZ/Graphviz/Mermaid(框架流程图)、Illustrator/Inkscape(精修)、Visio。
- **排版**：LaTeX(latexmk/TinyTeX/TeX Live)、Word(python-docx)、Pandoc(互转)。
- **文档处理**：PDF/DOCX/PPTX/XLSX skill、MarkItDown、unstructured.io、Apache Tika。
- **PPT**：python-pptx/PptxGenJS、Marp、reveal.js、Beamer、PowerPoint/Canva/Gamma。
- **前端**：Next.js/React、shadcn/ui、Tailwind、ECharts/D3。
- **后端**：FastAPI/Django/Spring Boot、Postgres/Redis、Docker。
- **API 调用**：有 OpenAPI(3.1.x，JSON/YAML)描述就按 `paths→operationId`+参数 schema(parameters 的 name/in=path|query|header|cookie)+`components.securitySchemes`(apiKey/oauth2…)确定性调用，按 response schema 解析，别靠散文文档猜。
- **云算力**：Python serverless/GPU 训练/沙箱用 Modal(`@app.function(gpu="h100", image=...)`，`modal.Image.debian_slim().uv_pip_install(...)` 代码内定义环境，Volumes/Secrets/Sandboxes/Cron 原语，`modal run`/`modal deploy`，按秒计费无空闲成本)。
- **版本/实验**：Git、DVC、MLflow、W&B、Hydra、Snakemake。
- **文献管理**：Zotero/pyzotero、JabRef、Better BibTeX。
- **环境**：纯 Python 优先 uv；编译科学库/CUDA/跨语言用 conda(mamba/miniforge)；已有 Poetry 项目延续 Poetry。

## 选择决策要点
- 数据规模 → 选库(pandas vs polars vs dask)。
- 一次性 vs 可复现 → 手工 vs 脚本。
- 输出去向 → 决定格式(矢量图投稿、png 演示)。
- 团队/复现需求 → 是否上版本与实验管理。
- 稳定性 > 新潮：选成熟、维护活跃的工具(CONVENTIONS 依赖安全)。

> 带**数值阈值**的完整决策矩阵(数据 <100MB pandas / 2-50GB polars / >TB Spark；投稿矢量 vs 演示 png≥150dpi；skill 安装量≥1K 等)见 references/decision_matrix.md，按需载入。

### 自动检测项目技术栈
进入一个已有项目、或用户问"这个项目该用什么工具"时，先跑检测脚本而非人工翻清单：
```bash
python scripts/detect_stack.py <项目目录>        # 读 package.json/pyproject.toml/requirements.txt/environment.yml
python scripts/detect_stack.py <项目目录> --json # 机器可读
python scripts/detect_stack.py --self-test       # 无项目时合成清单自检
```
脚本识别依赖→按类别给选型建议(命中内置规则的才给，未命中标 no signal 不臆造)，并据锁文件(uv.lock/poetry.lock/environment.yml/Dockerfile)给环境/复现建议。汇报照 assets/stack_detection_report.md。

### Python 环境选型
- 纯 Python/PyPI：**uv**（Rust，比 pip 快 10-100x）。`uv init`→`uv add`→`uv lock`(写 uv.lock 跨平台锁文件)→`uv sync`(确定性安装)→`uv run`；`uv python install/pin` 替代 pyenv；`uvx` 临时跑工具。
- 编译科学库/CUDA/非 Python 依赖(HDF5/MKL)/跨语言：**conda**。`conda create`→`activate`→`install conda-forge::pkg`→`conda env export`(environment.yml 复现)；提速用 **mamba**，最小安装用 **miniforge**(默认 conda-forge，避 Anaconda 授权)。
- 既有项目用 **Poetry**：`poetry add`/`install`(按 poetry.lock)/`run`/`build`/`publish`，dependency groups 分 main/dev。三者都靠锁文件保复现，不要 pip+conda 混装同一环境。
- 容器化复现：**Docker** Dockerfile 钉 `FROM` 版本 tag(忌 latest)，依赖安装层放前、源码 COPY 放后以复用缓存，`.dockerignore` 排除杂物，数据用 `-v` volume，多服务用 compose，瘦镜像用多阶段构建。

## 多工具协同
一个任务常跨工具：如"实验→W&B 记录→pandas 汇总→seaborn 出图→LaTeX 排版→Zotero 引用"。规划好数据在工具间的流转格式(CSV/JSON/Parquet)，减少手工搬运。

## 工具发现
需要新能力时按序：
1. 先查现成 skill：先看 skills.sh 排行榜(按总安装量，顶部如 vercel-labs/agent-skills、anthropics/skills 均 100K+)，再 `npx skills find [关键词]` 搜索。质量阈值：**安装量优先 1K+、<100 谨慎；GitHub star <100 的仓库存疑；官方源(anthropics/vercel-labs/microsoft)更可信**。给用户列 名称/用途/安装量/来源/链接/安装命令，同意后 `npx skills add <owner/repo@skill> -g -y`(-g 全局、-y 免确认)；无命中就坦白、转用通用能力、并建议 `npx skills init <name>` 自建。官方办公能力看 anthropics/skills(docx/pdf/pptx/xlsx，source-available)。
2. 接外部数据/工具：查可用 **MCP server**（参考款 Everything/Fetch/Filesystem/Git/Memory/Sequential-Thinking/Time，TS 用 `npx -y @modelcontextprotocol/server-*`、Python 用 `uvx mcp-server-*`，Windows 的 npx 项要 `cmd /c` 包裹；更多在 registry.modelcontextprotocol.io）。先 `tools/list`(分页)、`resources/list` 看 server 暴露了什么再 `tools/call`/`resources/read`。
3. 自建 skill：用 **skill-creator** 路线——目录 `SKILL.md`(frontmatter 仅 name/description)+`scripts/`(确定性代码)+`references/`(按需载入)+`assets/`(输出模板)；三级渐进披露(metadata 常驻 / 正文 <500 行触发载入 / bundled 按需)；description 略"push"、枚举所有触发场景防欠触发；正文用祈使句、解释"为什么"而非堆 MUST。评估闭环：写 2-3 条真实测试 prompt → 同时跑 with-skill 与 baseline → 量化断言评分汇成 benchmark → 读 transcript 找浪费、从反馈泛化别过拟合 → 跨样例重复的活抽进 `scripts/`。批量/原型化自动生成可参考 Autoskill(LLM 运行时生成代码+reflection 自修复，需环境隔离)。
引入任何第三方 skill/MCP server 都等于授权外部指令与代码，先评估来源与安全。详见 references.md。

呈现发现结果用统一模板：找到 skill 用 assets/skill_discovery_report.md(单个/多候选对比表/未命中兜底)；找到 MCP server 用 assets/mcp_discovery_report.md(含接入前 tools/list、resources/list 探测清单)。两份模板都附 2026-06 实测过的入口与 HTTP 状态码。

## 资源清单(bundled)
- `scripts/detect_stack.py` — 技术栈检测器，读项目清单→建议工具，`--self-test` 可离线自检。
- `references/decision_matrix.md` — 任务→工具决策矩阵，带数值阈值(数据规模/dpi/安装量)。
- `references.md` — 逐工具硬信息(端点/命令/参数/坑)。
- `assets/stack_detection_report.md` — 检测结果汇报模板。
- `assets/skill_discovery_report.md` — 发现 skill 呈现模板。
- `assets/mcp_discovery_report.md` — 发现 MCP server 呈现模板。

## 衔接
为所有技能提供"用什么做"的判断；与 a06(目录)、a02(版本工具)、a03(代码栈)协同。

> 逐工具硬信息(真实端点/命令/参数/坑)见同目录 references.md。
