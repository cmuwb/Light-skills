# 第三期执行进度台账（PROGRESS）

> 每轮收尾时由执行模型更新本文件（总纲 §5 第 6 步）。新对话接手时**先读本文件**再读对应轮次文件。
> 状态取值：`未开始 / 进行中 / 已完成 / 部分完成（见偏差）`。

## 轮次状态

| 轮 | 名称 | 状态 | 开始 | 完成 | commit 区间 | CI |
|---|---|---|---|---|---|---|
| R1 | P0 与卫生修复 | 已完成 | 2026-06-11 | 2026-06-11 | `1520d93..056165c`（8 commit） | 本地 7 门禁全绿；待推送确认 CI |
| R2 | 会话衔接协议 | 已完成 | 2026-06-11 | 2026-06-11 | `dd00835..7b60de3`（5 commit） | 绿（run 27341424084 三任务全 success） |
| R3 | 中文链路专项 | 已完成 | 2026-06-11 | 2026-06-11 | `89627e2..74a1bb0`（4 commit） | 绿（run 27346343103 三任务全 success） |
| R4 | 合规与生态吸收 | 已完成 | 2026-06-11 | 2026-06-11 | `5c7d2e1..a5a088e`（7 commit） | 绿（run 27353169946 success） |
| R5 | 资产补全 | 已完成 | 2026-06-11 | 2026-06-11 | `94f237e..cc3fd19`（9 commit） | 本地 5 门禁全绿；48 脚本 selftest 全 PASS；待推送确认 CI |
| R6 | PPT 生图流水线 | 部分完成（见偏差） | 2026-06-12 | 2026-06-12 | `55674c2..f04c12b`（5 commit） | 绿（run 27386750356 三任务全 pass）；PR #1 → master |
| R7 | 横切机制与瘦身 | 已完成 | 2026-06-12 | 2026-06-12 | `1cbfc52..961060c`（5 commit） | 绿（run 27389247644 三任务全 success）；PR #2 → master |
| R8 | CI 门禁扩建 | 未开始 | | | | |
| R9 | 数据库规模化（批1/批2/批3） | 未开始 | | | | |
| R11 | 行为评测与自动化闭环 | 未开始 | | | | |
| R12 | 安全、领域与微缺口增补 | 未开始 | | | | |
| R10 | 门面工程与发布（收官） | 未开始 | | | | |

## 基线度量（首次用到时填，后续轮引用）

- 常驻 11 技能 SKILL.md 总行数基线（R7 开工 2026-06-12 `wc -l` 量取）：**901 行**。目标 -15% → ≤765 行（须减 ≥136 行）。逐技能：file-reading 47 / memory-pm 91 / orchestrator 129 / backend-coding 89 / system-design 62 / frontend-design 99 / project-structure 90 / consistency 100 / self-review 65 / tool-selection 77 / research-ethics 52。（m16 slides 非常驻，不计入此基线。）
  - **R7 收尾实测：901 → 763 行（-15.3%，达标）**。逐技能终值：file-reading 42 / memory-pm 81 / orchestrator 111 / backend-coding 57 / system-design 50 / frontend-design 83 / project-structure 80 / consistency 63 / self-review 73(+8) / tool-selection 71 / research-ethics 52。瘦身手法=细节下沉 references/examples、多 bullet 列表合并为少行、跨技能重复内容指认单一真相源后删副本；self-review 因新增「分级执行档」(R7.5)净 +8，属能力增量非冗余。**未删任何能力**：下沉内容全部进对应 references（a03 code_examples.md、m08 examples/full_pipeline_walkthrough.md、orchestrator pipelines.md 契约表+checkpoints.md 恢复探针、file-reading references.md 视频工具链等）。
- db05/db06/db07 真实卡数基线：约 1-2 / 1-2 / 2（审计 2026-06-11 口径）
- ROUTER_EXAMPLES 必覆盖基线：7/28

## 偏差日志（只追加，不删改）

> 格式：`- [日期] R几.第几项 — 计划说什么 / 现实是什么 / 怎么处理的（自行修正|降级|跳过待用户）`

- [2026-06-11] 总纲§5 — 计划写校验器在 `tools/`；现实在 `.github/scripts/`（check_*.py + run_skill_selftests.py）。自行修正：全程用 `.github/scripts/` 路径，后续轮同。
- [2026-06-11] 总纲§5 — selftest 在 Windows 默认 GBK 控制台打印 `✓` 抛 UnicodeEncodeError（退出码1，非测试失败，45 脚本全 PASS）。处理：全程用 `PYTHONUTF8=1` 跑门禁；本身是真实可移植性隐患，但修 runner 编码属 R8 CI 范畴，本轮未改 runner，仅记录。
- [2026-06-11] R1.1 — 计划点名限流口径在 m04/m13/m10/a09；现实具体数字在 m01(literature-search)、m03(idea-generation)、venue-matching、citation、ip-application。按现实处理：m01 设真相源，其余全部指向并删数字。另发现 ip-application 有 2026-06-06 curl 实测"匿名仍 200"与官网"需 key"冲突——联网核实官网现行需 key+$1/天，保留实测为诚实存档并判定为过渡期现象。附带修正：OpenAlex 文档域名已迁 docs.openalex.org→developers.openalex.org，相关链接同步。
- [2026-06-11] R1.2 — 计划说 MDPI 栏宽"以 m09 SKILL.md 已核实表格为准"；现实 m09 表无 MDPI 行，真实来源是 m11(figure-planning) references.md「出版商图宽核查表」MDPI 行(170mm,⚠️付费墙未实测通行值)。按现实处理：figure_export.py mdpi 键 note 注明来源为 m11，verified=False。
- [2026-06-11] R1.3 — 联网核实 Science 三档为 5.5/12/18.3cm，即双栏 120mm，121mm 系换算误差。额外发现 science.mplstyle 把 121mm 写死进默认 figsize(真实出图偏差)，一并订正为 120mm(4.724in)。science.org 仍 403，数值经 WebSearch 多源一致核实。
- [2026-06-11] R1.4 — m05 模板实际文件名是连字符 experiment-matrix.md，与 orchestrator 下划线契约不符；按计划统一为下划线(git mv + 3 处引用)。仓库内 m 编号与计划标签偶有错位(如 figure-planning 内部自称 m11 指执行器)，按文件路径作业，不按编号。
- [2026-06-11] R1.5 — 计划假设 11 个 SKILL.md 有 `../../docs/design`/CONVENTIONS 硬路径会断；现实只有 orchestrator:121 一处 `../../docs/design` 硬链接(已改弱引用)，其余 16 处 CONVENTIONS 均为纯文字提及(不算断链)。仍按计划把 4 文档随装链接(sh symlink / ps1 hardlink)并加校验，使纯文字引用装后可达。已在临时/真实 ~/.claude 实测链接生成成功、内容可读。
- [2026-06-11] R1.5 — install.ps1 原为纯 ASCII；首次加中文注释触发 PowerShell 5.1 GBK 解析错误(真实 Windows 用户会中招)。修正：install.ps1 注释保持 ASCII-only。
- [2026-06-11] R1.6 — 计划假设 README:9 写"三端(Claude/Codex/Hermes)"与 install 两端冲突；现实 README 已是"Claude Code 与 Codex"两端表述，无三端硬冲突。曾按方案 B 在中英 README 补 Hermes 说明，**后经用户确认对外只支持两端，已删除该 Hermes 段**（见用户决策项，此项关闭，install 不加第三目标）。
- [2026-06-11] R1.8 — 计划说 a03 已实测 v6；现实 a03(backend-coding)确已全 v6 且有 GitHub API 实测记录。真正残留 v4/v5 在 system-design(a04 模板+references)与 tool-selection(references+detect_stack.py fixture)，已升 v6 并指向 a03 真相源。
- [2026-06-11] R1.10 — 计划说无参 selftest 落 5 PNG 到技能根；现实 `--selftest` 路径已用 tempfile(不污染)，真正污染是"无参无 JSON 的 demo 路径"(tag=selftest 落 CWD)。修正该 demo 路径改临时目录，并把 tag 由 selftest 改 demo。
- [2026-06-11] R1.12 — .gitignore 已含 __pycache__//*.py[cod]，无 tracked 缓存；out_multipanel 由 examples/example_matplotlib_multipanel.py 落 HERE 造成。改为默认临时目录(--outdir 可选)，删残留 PNG/PDF，清本地缓存目录。
- [2026-06-11] R2 全程 — 计划要求 a02 新模板放 templates/、细则下沉 references/；orchestrator §5 引用这些跨技能文件时，check_skill_links.py 会把裸 `templates/x.md` / `references/x.md` 反引号路径当成 orchestrator 自身内部路径校验而报缺失。处理：orchestrator 内一律写全 `light-memory-pm/templates/...`、`light-memory-pm/references/...` 前缀，链接门转绿。后续轮跨技能引用模板/参考时同此写法。
- [2026-06-11] R2.4-4 — 计划只说 a06 scaffold 纳入 `.light/`；执行中明确 `.light/`（passport + handoff 卡）是跨会话续跑真相源，应**纳入版本控制而非忽略**，故在 python-research.gitignore 末尾加注释显式声明不忽略 .light/，并在 scaffold selftest 断言两目录生成。
- [2026-06-11] R2.5 演练 — 示例项目 dairygoat 演练前无 `.light/`（轻项目靠 db09 卡承载）。按协议新建 .light/handoff 并落 S01/S02 两张真实卡作为工作示例；B 会话恢复用 `pytest tests/test_infer_track.py`(2 passed)实证 S01"已完成"声明无损，非口头比对。
- [2026-06-11] R3.5 — 计划说把实测栏宽写入 db01"新增字段/列"；现实 venues.csv 为固定 19 列 schema，check_databases.py 按列校验，新增列会破坏既有 332 卡。按现实处理：栏宽实测值追加进末列 catch-all `risk_note`（带来源+日期+方法），不改 schema，与 README"新增条目追加"惯例一致。
- [2026-06-11] R3.5 — 农业机械学报(j-csam.org)版心栏宽未取得：站点 PDF 入口返回反爬 JS 守卫页(`_guard/html.js`，59 字节)而非 PDF，三次重试均被拦。按诚信纪律标 GAP、db01 该刊栏宽留"待核查"，不从记忆/英文刊类比硬填。其余三刊(农业工程学报/中国农业科学/作物学报)均从发表 PDF 实测成功。
- [2026-06-11] R3.2 — 可选项 lint_gbt7714.py(GB/T 7714 中文条目 lint 脚本)本轮未实现：核验兜底以"人工浏览器比对检索结果页"为主路径(CNKI 执行环境直连不通，见验证日志§4)，脚本化 lint 价值有限且会新增 selftest 负担，判定为非必需，降级跳过。如后续要做，归 R8 CI 门禁范畴。
- [2026-06-11] R4.1 — 计划说"复用 a10 脚本接线"。现实：装到 ~/.claude/skills 后两技能平级、Python 无法跨技能 import。按现实处理：在 verify_refs.py **内联**同源判定逻辑(相同 FLAG_TYPES + update-to[] 判定)，注释指认 check_retractions.py 为同源真相，两脚本口径一致；不新增 HTTP(update-to 在已取的 Crossref 响应里)。另发现经典撤稿论文(STAP/Wakefield)本身 update-to 多为空、仅标题带 RETRACTED 前缀，故补标题前缀作补充信号。实查撤稿样例 `10.1016/j.micpro.2020.103768`(Elsevier，update-to 暴露 retraction)留痕。
- [2026-06-11] R4.3 — 计划说"db01 增 ai_policy 字段 / check_databases 认识新字段"。核查真相：check_databases.py 只 rglob databases/**/*.md 校验 db03–db08 的 YAML 卡，**根本不读 venues.csv**(db01/02 是 CSV，不在 schema 校验范围)，故"加列破坏 332 卡校验"的技术理由不准确。但用户硬约束(不加列、追加 risk_note)是明确产品意志且有独立合理性(204 卡加列需逐行补值)，遵守之：ai_policy 以 `ai_policy=` 子串追加进 risk_note。**两个坑**：①venues.csv 含多行字段，禁用 csv 模块全量重写(会把多行压成单行，205→186 行)；②追加文本禁含英文逗号(目标字段无外层引号，逗号会拆列)，改用中文分号/顿号 + 文本级唯一锚点替换，最终 diff 仅 12 增 12 删。
- [2026-06-11] R4.3 — 发现 R3 遗留瑕疵(不在 R4 范围)：venues.csv 物理行 186/187(中国农业科学、作物学报)在 HEAD 版即为 22 列(非 19)——R3 填栏宽实测时 risk_note 写入未加引号的英文逗号(如 `81mm/整页约170mm(A4双栏,来源:...,2026-06-11),2026-06`)被 CSV 解析器拆成多列。check_databases 不读 CSV 故 CI 不报。修复=给 risk_note 加引号，零风险但属扩大范围，**留 R9(db01 规模化)统一处理**。
- [2026-06-11] R4.2/R4.12/R4.13 — 实查诚信记录：①AI 图像政策 Elsevier 取得逐字原文，Nature(登录墙 303)/Science(403) 仅政策立场多源核实、确切引文标 GAP；②latexdiff 本机 MiKTeX 缺 Perl 模块 Algorithm::Diff，`latexdiff --version` 即报错，diff 输出未跑通标 GAP，流程按公开文档写并注明未本机验证；③飞书实查澄清官方云文档**无独立演示文稿 OpenAPI**，lark-slides 是 larksuite/cli 社区工具非官方 API，未凭"飞书有幻灯片"印象硬填。
- [2026-06-11] R4 跨技能引用 — 再次踩 check_skill_links 陷阱：在 A 技能 SKILL/references 用反引号写 B 技能的 `scripts/x.py`、`references/x.md` 会被当 A 自身路径报缺失。已全部加 `light-<skill>/` 前缀修正(citation↔research-ethics 脚本互引、figure-drawing/slides↔其他、typesetting↔review-rebuttal)。另：技能正文引用 `databases/db01...` 完整路径属安装后断链风险，改纯文字"db01"提及(与全仓库惯例一致)。
- [2026-06-11] R5.4 — 功效分析算例数值不凭记忆：本机 statsmodels 0.14.5 实跑 `TTestIndPower().solve_power`，d=0.3/0.5/0.8 → 每组 175.38/63.77/25.52(取 176/64/26)，反查 d=0.5 n=5 → power 仅 0.108。逐字留痕 `_verification_log/R5-04-power-analysis.md`，references 表数值与之一致并注明留痕路径。结论写实"3~5 种子只够检大效应"这一对用户最有用的功效缺口。
- [2026-06-11] R5.4 — plan_lint.py 首版在 Python 字符串里用了中文引号包"对应假设"导致 SyntaxError(全角引号≠ASCII)；改用「」书名号修复。教训:脚本内中文文案避免与 Python 语法字符冲突的全角标点。
- [2026-06-11] R5.5 — 计划要"先查有无现成 bootstrap 工具勿重写"：现实 significance_test.py 已有 `bootstrap_ci`，analyze_results 的配对差值 CI 直接 import 复用，未重写。配对识别复用合成 CSV 本就共享 seed 列(天然配对陷阱)，selftest 同时验配对/独立/共享<2 跳过/缺键四路径。
- [2026-06-11] R5.7 — er_diagram selftest 初版断言 `out.count("{")==2` 误判:Mermaid 关系符号 `||--o{` 自带花括号，把关系行也数进去了。改为只数"以 { 结尾的行"判实体块数。教训:对含特殊符号的 DSL 输出做结构断言要按行语义数，别全文 count 字符。
- [2026-06-11] R5.7 — a04 references 是 7 个常驻技能里唯一没有研究日期时效锚标头的(计划点名)，已补"研究日期 2026-06 + 落地前以所装版本官方文档为准"。
- [2026-06-11] R5.8 — m15↔m11 专利附图断链:m15 原本只写"交 m11 绘制"无具体规范、m11 无对应节。已在 m11 references 新增「专利附图规范」节(图号/标记线/黑白线条/流程图框图)作真相源，m15 SKILL 两处 + m11 SKILL 衔接段双向互指该节。专利附图规范以 CNIPA 现行审查指南为准,本节为通用要点未逐条核对最新版次(已注明),最终须代理师审。
- [2026-06-11] R5.9 — scaffold 目录有本地 `.pytest_cache/`(被 .gitignore:7 覆盖、未追踪),属跑测试的本地产物非仓库内容,未提交。pyproject 加 [tool.mypy] 后用 tomllib 实测可解析。
- [2026-06-12] R6.1 — 三家生图 API 已联网核实(2026-06-12)端点/参数/尺寸/透明支持,逐条留痕 `_verification_log/R6-imggen-api.md`并回填 references.md「生图后端」节。关键真相:①透明背景**仅 OpenAI gpt-image 有显式 `background:transparent`**,Gemini/Seedream 无开关(标 GAP,做透明图标优先 OpenAI 或 PIL 去底);②三家 seed 都不稳(OpenAI/Gemini 官方未列,Seedream 5.0 系列亦未明列),风格一致性改靠唯一 style_anchor+图生图参考,不靠 seed;③Seedream `watermark` 默认 true,封装层已默认置 false(否则 PPT 元素带"AI 生成"水印);④Gemini 图像走通用 generateContent 无独立 images 端点;⑤OpenAI size 仅固定档,16:9 用 1536x1024 近似。
- [2026-06-12] R6.6#4 — `GAP：待实测(2026-06-XX)`:有 key 端到端实跑(≥5 页 deck、五阶段产物齐全、QA 两项新检查、db06 沉风格卡)**未做**。执行环境探测到平台级 `OPENAI_API_KEY`,但真实生图请求会向第三方传 prompt 且计费,属外部副作用,未经用户显式授权不触发(与 selftest 离线纪律一致)。无 key 装配链(R6.6#3)已端到端实测 PASS:3 页 deck_spec 模板 + imagegen.py mock 占位 PNG → assemble_from_spec.py 产 3 页可编辑 pptx,重开校验 6 原生文本框(=title/body 元素数,守边界三文本未栅格化)+ 4 图片 + 0 warning。
- [2026-06-12] R6 跨技能引用 — 又踩 check_skill_links 陷阱(PROGRESS 已多次记):在 a05/a10/m17 用反引号写 m16 的 `references/imggen_pipeline.md` 被当本技能内部路径报缺失,全部加 `light-slides/` 前缀修正。imagegen.py mock selftest 在 Windows 下 `Image.open` 不 `.load()` 会锁文件致 TemporaryDirectory 清理失败(WinError 32),改 `with Image.open() as im: im.load()` 释放句柄。
- [2026-06-12] R6.2 — assemble_from_spec.py 装配 chart 元素**只 add_picture 真数据图(figures/),绝不在装配层生图**(守边界一);资产缺失画占位框+warn 不静默跳过(诚信纪律,与 to_pdf.py 同);themes.py 跨目录 import 失败时用内置兜底色板,保证离线 selftest 不依赖 import 路径。
- [2026-06-12] R7 行数目标 — 计划把 F 组瘦身列在 m07/m08/m15/m16/m17 等**手动技能**，但 -15% 目标是对**常驻 11 技能**。两者交集小（F 组直接命中常驻的只有 a03/a09），且 E 组(R7.5-R7.12)给常驻**增**内容(a08 分级档+8、orchestrator passport/并行、a01 视频)。故按 F 组「正文留决策+一行指针、细节下沉 references」手法**横向施于全部常驻**：a03 代码例/调试四法下沉 code_examples.md(-32)、consistency 工具视角+检查维度合并(-37)、orchestrator §2 契约表镜像下沉 pipelines.md + §0 探针下沉 checkpoints.md(-18)、frontend 框架 how-to 指 references(-16)、system-design 部署/RLS/迁移多 bullet 合并(-12)、memory-pm 工具映射+写入示例压缩(-10)、project-structure 质量门/模板列表压缩(-10)。最终 901→763(-15.3%)。**严格只下沉不删能力**：每处删除的正文内容均已在对应 references 存在或同轮补入，新建 a03/code_examples.md 与 m08/examples/full_pipeline_walkthrough.md 承接。
- [2026-06-12] R7.2 种子数 — 计划写 m05「≥3~5」vs m06「≥5」。统一为「≥5；算力受限 ≥3 且须在 m06 报告显式标注」，两技能同句式。功效分析数值(d=0.5 需每组~64)保留，措辞从「3~5 个种子」改为「少量种子」避免与新阈值打架。
- [2026-06-12] R7.3 uv 默认 — scaffold.py 原只有 `--poetry`。改为 pyproject **始终落地**、默认 uv 后端(hatchling + `[dependency-groups]` + `[tool.hatch]` src 布局)、`--poetry` 切备选(poetry-core)，`--uv/--poetry` 互斥组。selftest 覆盖两路径并 tomllib 解析校验。a06 SKILL 三处(整理动作/版本依赖/资产清单)同步改默认 uv。
- [2026-06-12] R7.4 vaex — 计划只点 a09 decision_matrix.md:13。现实 vaex 还活跃出现在 m02(data-engineering) SKILL:18 + references「## Vaex」节、a09 detect_stack.py:31。按验收「grep vaex 仅余已淘汰标注」全仓库处理：decision_matrix 换 DuckDB/polars streaming/dask、detect_stack 改迁移告警、m02 SKILL 换 DuckDB 并指 a09 单一口径、m02 references「## Vaex」标「已淘汰仅存档」并新增「## DuckDB」承接能力。
- [2026-06-12] R7.10 CUMCM AI 规定 — 计划写「CUMCM 2024 起 AI 使用规定」。联网核实(官方 dxs.moe.gov.cn，2026-06)：CUMCM 正式 AI 规定是**2025 年试行版(自 2025-09-01)**，非 2024。按现实写入 m17：允许但非必须、核心独立完成、未用须声明、用了须正文标注+提交 PDF「AI 工具使用详情」、违规取消评奖；带 last_checked。留痕见对话。
- [2026-06-12] R7.22 tex 编译 — 计划预案「本机无 TeX 则标注待验证」。现实本机有 MiKTeX + **Tectonic**，五份 .tex 骨架全部 `tectonic` 实编译退出 0 产 PDF(IEEE/ACM/Springer/Elsevier 走 pdflatex、ctex_chinese 走 XeLaTeX 自动装中文字体)，非 GAP。留痕 `_verification_log/R7-tex-compile.md`。
- [2026-06-12] R7 新脚本 — m14 新增 `scripts/rebuttal_budget.py`(会议 rebuttal 字数/页数预算检查，纯 stdlib，中英混排分别计词，超限返回码 1)，已登记 WHATS_INCLUDED(脚本数 50→51，meta 表计数同步)、selftest 通过。

## 留给下一轮的话

> 每轮收尾写 1-3 行：下一轮要注意什么、有什么现场发现。

- R2 注意：orchestrator §5 已有 Handoff 格式、§0 断点恢复协议、§2 契约表(本轮已声明 CONVENTIONS §6.1 为真相源)；R2 收编 handoff 为单一口径时直接基于现有 §5，勿另起一套。
- R3 注意：会话衔接协议已就位——CONVENTIONS §9 全局纪律 + a02 两件套模板/细则 + orchestrator §5 收编 + a06 scaffold .light/ + 路由触发 + README FAQ + A/B 演练（_verification_log/session_handoff_drill.md）。后续任何轮长任务收尾都应主动留衔接卡 + 打印启动提示词（含执行本计划的轮间交接，11 号文件模板可与 handoff_prompt.md 互参）。
- R3 注意：跨技能引用别的技能的 templates//references/ 文件，反引号路径必须带 `light-<skill>/` 前缀，否则 check_skill_links.py 误判为本技能内部路径报缺失（R2 已踩，见偏差日志）。
- R3 注意：中文链路专项独立于 R2，无新增硬依赖；ROUTER_EXAMPLES 现 47 例(R2 +3 主动交接正例)，check_entry_docs 必覆盖集仍含 light-orchestrator。
- R4 注意：R3 未增减技能数(仍 28)、未加脚本、未动路由，故 WHATS_INCLUDED/MODE_REGISTRY/ROUTER_EXAMPLES 本轮无需同步(check_entry_docs 已绿)。R4 若收编外部生态技能会动技能数，记得四件套(README/ROUTER/MODE_REGISTRY/ROUTER_EXAMPLES)同步 + ROUTER_EXAMPLES 必覆盖集。
- R4 注意：db01 venues.csv 是 19 列固定 schema，任何"补字段"需求一律追加进 risk_note catch-all，勿加列(check_databases 按列校验 332 卡)。中文刊实测栏宽语义=版心栏宽(非官方图宽硬规格)，已在 db01 备注注明，引用时别当成出版商 author-guide 的 figure width。
- R4 注意：EI 收录权威源=Engineering Village 的 Compendex Source List(从产品页 View source list 现取当期 Excel，CDN 链接随版本变动，勿硬编码)；m13 已禁引第三方"EI 源刊"站。
- 全程门禁请带 `PYTHONUTF8=1`（Windows GBK 否则 selftest runner 打印 `✓` 报 UnicodeEncodeError，非测试失败）。校验器在 `.github/scripts/`，非 `tools/`。
- 安装链接已扩到 4 文档；R2 若动 CONVENTIONS/ROUTER 结构，记得 install 与 check_installation_assets.py 已对这些文件名有依赖。
- **R4 已完成（给 R5 的话）**：R4 未增减技能数(仍 28)、未加新脚本(只改 citation/verify_refs.py 现有脚本加撤稿检测)、未动路由，故四件套(README/ROUTER/MODE_REGISTRY/ROUTER_EXAMPLES)本轮无需同步，check_entry_docs 已绿。R5(资产补全)独立于 R4，按 05 号文件做。
- **R4.16(H11 图谱可视化)登记入 backlog，本轮不做**：计划 04 号文件明确 H-11 入 backlog；若未来要做，归 m01/m11 的引文网络/主题图谱可视化方向，非本期范围。
- **给 R9 的话(db01 规模化)**：①ai_policy 字段已定义为 risk_note 内 `ai_policy=` 子串口径(见 CONVENTIONS §3)，已实查填 12 家头部 venue，其余卡待 R9 批量补；②R4 发现 venues.csv 有 2 行(中国农业科学/作物学报，物理行 186/187)是 22 列(R3 填栏宽时 risk_note 含未加引号英文逗号被拆列)，R9 重做 db01 时给这两行 risk_note 加引号修回 19 列；③改 venues.csv 切记：含多行字段，禁用 csv 模块全量重写(会压平多行)，禁在无引号字段追加含英文逗号的文本(会拆列)，安全做法是文本级唯一锚点替换或给字段加引号。
- **R4 现场口径(供 a10/m07/m11/m16 后续轮引用一致性)**：AI 政策两类口径——期刊=AI 生成图像禁止+文本须披露；会议=LLM 允许+作者全责+不得署名。论文图严禁生成式 AI(figure_integrity「AI 生成图像政策」节为真相源)，R6 PPT 生图流水线只服务 PPT/前端、严禁进论文图链路(figure_integrity↔slides 已双向互指)。撤稿判定真相源=research-ethics/check_retractions.py 的 FLAG_TYPES，citation/verify_refs.py 内联同源(改判定常量须两处同步)。
- **R5 已完成（给 R6 的话）**：R5 新增 3 个脚本(plan_lint/venue_signal/er_diagram)，技能数仍 28、未动路由，故只需同步 WHATS_INCLUDED(已登记)，四件套其余无需动(check_entry_docs/check_skill_assets 已绿，48 脚本全 selftest)。零脚本技能(m13/a04)与零模板关键交付物(m03/m09)均已清零。R6(PPT 生图流水线)按 06 号文件做，注意 R4 现场口径"PPT 生图严禁进论文图链路"。
- **R5 现场口径(供后续轮引用一致性)**：①功效分析数值是 statsmodels 0.14.5 实跑(d=0.3/0.5/0.8 → 每组 176/64/26)，留痕 `_verification_log/R5-04-power-analysis.md`，改动须重跑核验；②paper2code 已按 I-1 以 references 形式并入 m05(复现五步协议)，非独立技能；③配对检验识别(m06 analyze_results --paired-by)与切片分析是结果分析两大新纪律，配对效应量用 d_z 不可与独立 d 混比；④数据增强红线"先划分再增强、只增训练折"，标注 IAA 复用 code_assets/agreement.py、标签错误检测用 cleanlab(找候选→人工裁定不全自动删)；⑤专利附图规范真相源在 m11 references「专利附图规范」节(m15↔m11 双向互引)，黑白线条不套论文配色；⑥静态类型档位:科研代码 pyright basic 起步/库代码 mypy --strict，scaffold pyproject 已带 [tool.mypy]。
- **R6 已完成（给 R7 的话）**：R6 是 m16 内部新增 mode(技能数仍 28),新增 2 脚本(imagegen/assemble_from_spec,共 50 脚本全 selftest)+1 模板(deck_spec.yaml)+1 references(imggen_pipeline.md),mode 数 8→10、有 mode 技能 3→4。四件套已同步:MODE_REGISTRY(m16 两 mode + 计数句 + footer 去 m16)、WHATS_INCLUDED(2 脚本+1 模板+计数 45→50)、check_entry_docs/check_skill_assets 已绿;ROUTER/ROUTER_EXAMPLES 未动(m16 路由触发词没变,本轮没加新触发场景)。**R7(横切机制与瘦身)注意**:①R7 要量取常驻 11 技能 SKILL.md 行数基线——m16 SKILL 本轮**只增 5 行**(两 mode 分流段),细节全下沉 imggen_pipeline.md(常驻瘦身纪律已遵守),量基线时把这 5 行算进去;②瘦身若动 m16 SKILL,别把两 mode 分流段删了(MODE_REGISTRY/check_entry_docs 依赖"两 mode"在正文可见)。
- **R6 现场口径(供后续轮/有 key 实跑引用一致性)**：①三家生图 API 真相源=`_verification_log/R6-imggen-api.md`(改端点同步 references.md「生图后端」节 + imagegen.py ENDPOINTS 常量,三处);②透明背景仅 OpenAI 原生,seed 三家都不稳→风格靠唯一 style_anchor(真相源在 deck_spec.yaml),Seedream 水印默认 true 必关;③三条硬边界(数据图不生图/论文图禁生图/文本不烤进图)三处互引锚点=m16 imggen_pipeline.md ↔ m11 figure_integrity「与 R6 生图流水线的边界」节 ↔ a10 SKILL §5,改任一处口径须同步三处;④**R6.6#4 有 key 端到端实跑是 GAP**:配 OPENAI/GEMINI/ARK key 后按 06 号文件 R6.6 第 4 条跑≥5 页 deck,回填 imggen_pipeline.md「实测记录」节 + 沉一张 db06 风格卡 + 留痕 `_verification_log/`;db06 风格卡是 R9 db06 上量的主要真实卡来源(R6.5 已声明联动)。
- **R7 已完成（给 R8 的话）**：①脚本数 50→51（新增 m14 `rebuttal_budget.py`），WHATS_INCLUDED + meta 计数已同步，check_skill_assets/run_skill_selftests 全绿（51 PASS）。R8(CI 门禁扩建)若加「行数预算门」可直接量常驻 11 技能（763/≤765，留 2 行裕度，后续轮往常驻加内容前先看这条余量）。②技能数仍 28、mode 仍 10、路由触发词未改，ROUTER/ROUTER_EXAMPLES/MODE_REGISTRY 本轮未动（仅 m07 description 精简但触发关键词全保留，check_entry_docs 已绿）——R8 若新增校验器注意 route_examples=47 不变。③R7 新建两个下沉文件（`light-backend-coding/references/code_examples.md`、`light-paper-polishing/examples/full_pipeline_walkthrough.md`）属 references/examples 非脚本，不进 selftest。④跨技能新口径供 R8+ 一致性引用：检索库数统一 ≥2（m03↔m04）、种子数统一 ≥5/受限≥3 须标注（m05↔m06）、依赖管理默认 uv（a03↔a06）、vaex 全仓库标已淘汰（迁 DuckDB/polars streaming，a09 decision_matrix 为单一口径）。⑤a08 self-review 新增「分级执行档」（轻任务最小三项证据/事实/夸大 vs 重产出全量 11 项），orchestrator checkpoints.md 已引用；R8 行为评测设计自审类任务时按此分档。
- **R7 现场口径(供后续轮引用一致性)**：①a07 consistency「变更广播」回扫的权威已产出材料清单 = orchestrator `.light/passport.yaml` 各阶段 `artifacts:` 并集（无 passport 退 db09 version_history），orchestrator §4 已双向指认——改 passport schema 须顾及 a07 消费侧。②m08 findings JSON 被 m14 模拟审稿消费（overclaim→Soundness major、ai_tone/punctuation→Presentation minor），字段映射在 m14「消费 m08 润色发现」节、schema 在 m08 references/findings_schema.md，改 category 取值两处同步。③m12 五份 .tex 骨架已 Tectonic 实编译验证（留痕 `_verification_log/R7-tex-compile.md`），R8 若上 CI TeX 编译门可复用此结论、离线环境需预置 TeX Live/MiKTeX 对应包。

## 用户决策项登记（出现一个登记一个，R10 统一找用户拍板）

- [ ] skills.sh 发布与否（审计 I-5）
- [ ] db08 脱敏高分申报书全文样例来源（用户提供或公开样例，R9）
- [x] Hermes 安装目标方案确认（2026-06-11 用户确认：对外只支持 Claude Code 与 Codex 两端，Hermes 不单独支持。已删除中英 README 的 Hermes 说明段；install 脚本不加第三目标。此项关闭。）
