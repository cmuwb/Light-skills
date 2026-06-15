---
name: light-tool-selection
description: 工具选择与多工具协同。根据任务自动判断适合用什么工具——搜索、Python、R、MATLAB、LaTeX、Word、Excel、PowerPoint、Visio、Origin、数据库、Git、前端/后端框架、绘图工具、文献管理工具等（常驻，所有任务后台生效）。不盲目用工具，而是按实际任务选最高效、最稳定、最专业的实现方式。
user-invocable: false
---

# 工具选择与多工具协同

## 原则（常驻）
优先可复现(代码/脚本) > 一次性手工；优先项目已有的栈 > 引入新依赖。本技能的增量不在"该想到选最优工具"这种元认知(任何强模型自带)，而在三件裸模型做不到的事：①**当期可验证硬信息**(端点/命令/安装量/版本，带 last_checked)；②**no-signal 纪律**(未命中依赖明确拒绝臆造建议)；③**确定性核对**(冲突/异味/版本时效，把"铁律"变成可跑的检查而非口号)。

## 任务 → 推荐工具映射
- **文献搜索**：arXiv/OpenAlex/Semantic Scholar/Crossref API、agent-browser/browser-use、Exa/Parallel Web。
- **浏览器自动化**：偏 CLI/稳定走 agent-browser(原生 Rust CLI、直连 CDP、accessibility-tree 快照+`@eN` 引用定位、命令间保活、4848 端口可观测面板，先 `agent-browser skills get core` 发现用法)；偏 Python 集成走 browser-use(`Agent(task,llm,browser)`+`await agent.run()`，基于 Playwright，`@tools.action` 加自定义工具，`use_cloud=True` 走 stealth 云浏览器)。**投稿系统网页操作**（OpenReview/Editorial Manager 等填表、上传、查状态）可装 agent-browser 类技能（约 438K 装，last_checked 2026-06），**Light 不自建浏览器自动化**，按需引入外部技能并评估来源安全。
- **数据处理**：pandas(中小) / polars(快) / DuckDB·polars streaming·dask(超内存)；质量 ydata-profiling/Deepchecks/Great Expectations。
- **统计/科学计算**：Python(statsmodels/scipy/sklearn)、R(高级统计/绘图)、MATLAB(信号/控制/数值)。
- **绘图**：matplotlib/seaborn/plotly/altair、ggplot2、Origin(期刊曲线)、TikZ/Graphviz/Mermaid(框架流程图)、**Draw.io**(框架/系统/架构图 diagram-as-code，有官方 MCP，XML 可版本控制)、Illustrator/Inkscape(精修)、Visio。
- **3D 可视化/渲染**：Blender(开源，程序化建模渲染非 AI 生图；3D 科学可视化用 Molecular Nodes/SciBlend 等插件、路演 3D 渲染；有社区/官方 MCP，需本地装)。配 m09 figure-planning / m16 slides。
- **排版**：LaTeX(latexmk/TinyTeX/TeX Live)、Word(python-docx)、Pandoc(互转)。
- **文档处理**：PDF/DOCX/PPTX/XLSX skill、MarkItDown、unstructured.io、Apache Tika。
- **PPT**：python-pptx/PptxGenJS、Marp、reveal.js、Beamer、PowerPoint/Canva/Gamma。
- **前端**：Next.js/React、shadcn/ui、Tailwind、ECharts/D3；有设计稿时用 **Figma MCP**(读稿→IDE 出码，Remote server 免费可读写)，配 a05 frontend-design。
- **后端**：FastAPI/Django/Spring Boot、Postgres/Redis、Docker。
- **API 调用**：有 OpenAPI 描述就按 `paths→operationId`+参数 schema+`securitySchemes` 确定性调用、按 response schema 解析，别靠散文文档猜（字段细节见 references.md）。
- **云算力**：Python serverless/GPU 训练/沙箱用 Modal（代码内 `@app.function(gpu=..., image=...)` 定义环境，按秒计费；命令与原语见 references.md）。
- **版本/实验**：Git、DVC、MLflow、W&B、Hydra、Snakemake。
- **自动化/CI**：仓库事件触发用 GitHub Actions（test-on-push、schedule 定时、自动构建论文 PDF/图、release）；本地数据依赖编排用 Snakemake/Make——二者互补（Actions 管"何事件触发"，Snakemake 管"步骤间数据依赖"，见 references.md）。
- **文献管理**：Zotero/pyzotero、JabRef、Better BibTeX。
- **环境**：纯 Python 优先 uv；编译科学库/CUDA/跨语言用 conda(mamba/miniforge)；已有 Poetry 项目延续 Poetry。

## 选择决策要点
量化任务维度(数据规模/输出去向/复现需求/本机算力)再查 references/decision_matrix.md 选工具——该矩阵带数值阈值。稳定性优先：选成熟、维护活跃的工具；**这条不只口头讲，detect_stack 的版本时效门会据锁文件版本 + references/tool_currency.json 标记落后大版本/已弃用包**(见下)。

> 完整决策矩阵(数据 <100MB pandas / 2-50GB polars / >TB Spark；投稿矢量 vs 演示 png≥150dpi；skill 安装量≥1K 等)见 references/decision_matrix.md，按需载入。

### 自动检测项目技术栈
进入一个已有项目、或用户问"这个项目该用什么工具"时，先跑检测脚本而非人工翻清单：
```bash
python scripts/detect_stack.py <项目目录>        # 人读报告
python scripts/detect_stack.py <项目目录> --json # 机读(含 tooling_plan)
python scripts/detect_stack.py <项目目录> --findings  # 机读 findings(冲突/版本时效门)
python scripts/detect_stack.py --selftest        # 无项目时合成清单自检
```
脚本读 package.json/pyproject.toml/requirements.txt/environment.yml/Pipfile 的**顶层直接依赖**(不解析传递依赖树——比 syft/scancode 的 SBOM 浅，措辞别夸成"全依赖图")，做四件事：
1. **选型建议**：依赖→类别建议。匹配走 精确键 → 连字符/下划线变体 → **别名规范化**(ALIASES 表：torch-geometric→torch、langchain-core→langchain、opencv-contrib-python→opencv-python、react-dom→react 等同族/别名)。未命中任何规则的依赖标 `no signal`，**绝不臆造建议**。
2. **冲突/异味检测**(check_smells，兑现下方铁律)：environment.yml 里 conda 段与 pip: 子列表声明同一包→pip/conda 混装冲突(critical)；tensorflow+torch 双框架、requests+httpx+aiohttp 三 HTTP 冗余、命中弃用集合(vaex/nose/sklearn 空壳包等)→异味(warn)；anaconda `defaults` channel→商业 license 提示(info)。
3. **版本时效门**(parse_lock_versions + check_version_currency)：解析 uv.lock/poetry.lock/package-lock.json 里钉死的版本号，比对 references/tool_currency.json(工具→最新大版本/EOL/弃用，带 last_checked)，标记落后≥2 个大版本或已 EOL/弃用。currency 元数据缺失时降级且明确标注，不臆造。
4. **环境/语言栈**：锁文件→环境工具结论；R(DESCRIPTION/renv.lock)、MATLAB(.m)、LaTeX(.tex)、Jupyter(.ipynb) 等无清单语言栈靠特征文件嗅探。

`--json` 额外产出机读 **tooling_plan**(`light.tooling_plan.v1`：每环节 任务→选定工具→理由→数据流转格式)，`--findings` 产出 **light.findings.v1**(挂接 _shared 契约，冲突=critical 阻断、版本时效=warn)，供 a01 passport gate / db09 记忆 / m02·a03 等下游消费。汇报照 assets/stack_detection_report.md。

> 规则覆盖面是有限的内置字典(非全生态)，改动 RULES/ALIASES/SMELLS 后跑 `python scripts/run_routing_eval.py` 做回归(防漂移)。

### Python 环境选型
决策表(场景→工具→命令、互斥铁律)见 references/decision_matrix.md 第 5 节，逐工具命令/坑见 references.md。口径：纯 Python/PyPI 用 **uv**，编译科学库/CUDA/跨语言用 **conda(mamba/miniforge)**，已有 Poetry 延续 **Poetry**，可移植服务用 **Docker**。"**同一环境不混 pip+conda**"这条铁律不止写在这里——detect_stack 的 pip_conda_mix 检测会在 environment.yml 真出现 conda/pip 同包声明时报 critical 冲突，是被代码 enforce 的，不是只 preach。

## 多工具协同
一个任务常跨工具：如"实验→W&B 记录→pandas 汇总→seaborn 出图→LaTeX 排版→Zotero 引用"。规划好数据在工具间的流转格式(CSV/JSON/Parquet)，减少手工搬运。

## 工具发现
需要新能力时按序：
1. 先查现成 skill：先看 skills.sh 排行榜(按总安装量，顶部如 vercel-labs/agent-skills、anthropics/skills 均 100K+，last_checked 2026-06)，再 `npx skills find [关键词]` 搜索。**质量数值阈值(安装量/GitHub star/来源信誉)权威版见 references/decision_matrix.md 第 7 节**。给用户列 名称/用途/安装量/来源/链接/安装命令，同意后 `npx skills add <owner/repo@skill> -g -y`(-g 全局、-y 免确认)；无命中就坦白、转用通用能力、并建议 `npx skills init <name>` 自建。（安装量随时间变，引用具体数字一律带 last_checked。）
2. 接外部数据/工具：查可用 **MCP server**（参考款 Everything/Fetch/Filesystem/Git/Memory/Sequential-Thinking/Time；TS 用 `npx -y @modelcontextprotocol/server-*`、Python 用 `uvx mcp-server-*`，Windows npx 要 `cmd /c` 包裹；registry.modelcontextprotocol.io 更多）。先 `tools/list`/`resources/list` 看暴露了什么再调用。**科研设计/绘图/3D/计算类已选定推荐 MCP**（路由到对应技能时按需建议）：Figma(读设计稿→前端,a05)、Canva(路演 PPT/海报,m16/m17)、Draw.io(框架/系统/架构图 diagram-as-code,m09/a04/m15)、Blender(3D 科学可视化/路演渲染,m09/m16)、MATLAB(信号/控制/数值/Simulink)——能力/费用/star 单一真相源在 **README 推荐 MCP 表**，本节不复写数字（口径同 OpenAlex key）。
3. 自建 skill：用 **skill-creator** 路线——`SKILL.md`(frontmatter 仅 name/description)+`scripts/`+`references/`+`assets/`，三级渐进披露，description 枚举触发场景防欠触发，正文用祈使句解释"为什么"。评估闭环：真实测试 prompt → with-skill vs baseline 量化对比 → 读 transcript 泛化别过拟合 → 重复活抽进 `scripts/`。（skill-creator/Autoskill 细节见 references.md。）
引入任何第三方 skill/MCP server 都等于授权外部指令与代码，先评估来源与安全。详见 references.md。

## 资源清单(bundled)
- `scripts/detect_stack.py`（技术栈检测 + 冲突/异味 + 版本时效门，`--selftest` 离线自检 / `--json` 出 tooling_plan / `--findings` 出 light.findings.v1）。
- `scripts/run_routing_eval.py`（task→tool 映射回归 eval，借 RouteLLM/skill-creator eval 思路，`--selftest` 离线全绿）。
- `references/decision_matrix.md`（带数值阈值的决策矩阵）、`references/tool_currency.json`（工具时效元数据单一真相源：最新大版本/EOL/弃用，带 last_checked）、`references.md`（逐工具端点/命令/坑）。
- `evals/tool_choice_eval.json`（路由回归基准：routing/alias/no-signal/smell 期望）。
- 呈现模板 `assets/`：`stack_detection_report.md`（检测汇报）、`skill_discovery_report.md`、`mcp_discovery_report.md`。两份发现模板附 2026-06 实测入口与 HTTP 码。

## 产出（跨技能交接，CONVENTIONS §6.1）
本技能为常驻路由知识层，不在主线串行链落标准阶段工件，但提供两类机读产物供下游按需消费（用 `--json` / `--findings` 取）：
- **tooling_plan**（`light.tooling_plan.v1`，detect_stack `--json` 的 `tooling_plan` 字段）：每环节 任务→选定工具→理由→数据流转格式 + env/version_flags/smells/no_signal。供 m02 数据工程、a03 后端、m09 figure-planning、m07 写作直接引用选型，避免各技能各自重判栈。
- **findings**（`light.findings.v1`，detect_stack `--findings`）：挂接 `_shared/gate_runner`，含 `dependency_smells`(critical 冲突阻断) 与 `version_currency`(warn) 两 gate，`producer=a09`、`target=tooling-plan`、`fresh_evidence=true`。供 a01 passport 确认点判定、db09 记忆消费（机读 verdict，不靠 prose 总结）。

## 衔接
为所有技能提供"用什么做"的判断；与 a06(目录)、a02(版本工具)、a03(代码栈)协同。挂接 `_shared` 地基契约4(findings/gate_runner)，把检测结论以 `light.findings.v1` 机读交接，不再靠聊天总结传 verdict。

> 逐工具硬信息(真实端点/命令/参数/坑)见同目录 references.md。
