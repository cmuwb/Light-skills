# 脚本与模板清单

本仓库各技能内置的可运行脚本与可套用模板，按技能归类。脚本以纯 Python/常见科学计算库为主，均应至少可 `py_compile` 且带 `__main__` 入口；多数脚本支持离线 `--selftest`，少数依赖外部工具/网络或示例主程序的脚本会在资产校验报告中列为待补 selftest。

> 本清单由 `.github/scripts/check_skill_assets.py` 防漂移：新增/删除 `skills/light-*/scripts/*.py` 后必须同步本表，否则 CI 失败。

## 可运行脚本

| 技能 | 脚本 | 作用 |
|------|------|------|
| citation | `scripts/doi_to_any.py` | DOI 转 BibTeX / CSL-JSON / GB/T 7714，中文条目自动注入 `langid` |
| citation | `scripts/verify_citation_edge.py` | 核验“A 是否引用 B”，返回 confirmed / not_in_open_index / unknown 三态(OpenCitations / Semantic Scholar) |
| citation | `scripts/verify_refs.py` | 批量 DOI 真实性、元数据一致性与开放获取状态核验，产 JSON 报告 |
| competition | `scripts/market_charts.py` | 市场分析 JSON 渲染为 TAM/SAM/SOM、竞品定位矩阵、五力分级、风险热图 |
| competition | `scripts/roadmap_gen.py` | 里程碑 JSON 渲染技术路线图 / 甘特图，支撑申报书与路演路线页 |
| consistency | `scripts/consistency_audit.py` | 读取 db09 术语/方法/指标事实源，跨论文/PPT/文档检测术语、指标名、指标值与覆盖缺口 |
| data-engineering | `scripts/check_access_level.py` | 数据访问分级守门：阻断 raw 数据流向 paper/figure/public-repo 等公开产物 |
| data-engineering | `scripts/data_doctor.py` | CSV → Markdown 数据体检报告：形状、类型、缺失、重复、异常值、强相关、泄漏提示 |
| data-engineering | `scripts/quality_gate.py` | 按 YAML 规则校验 CSV，输出 PASS/FAIL 数据质量门报告，退出码可接 CI |
| data-engineering | `scripts/safe_split.py` | 构建防泄漏 split + Pipeline/ColumnTransformer，支持 clf/reg/timeseries/group 任务 |
| figure-drawing | `scripts/color_palettes.py` | 投稿级配色工具：Okabe-Ito、连续/离散色图、灰度与色盲模拟预览 |
| figure-drawing | `scripts/figure_export.py` | 按目标期刊栏宽精确导出矢量+位图，校验物理尺寸与缩放后字号 |
| figure-drawing | `scripts/figure_integrity_lint.py` | 图表诚实性静态扫描：y 轴截断、双 y 轴、bar 无误差棒、jet/rainbow、3D 扭曲等 |
| file-reading | `scripts/docx_read.py` | DOCX 结构读取：段落、表格、标题层级与基本元数据归一化 |
| file-reading | `scripts/pdf_ops.py` | PDF 读取与结构操作：文本/页级信息抽取、合并拆分等轻量操作 |
| file-reading | `scripts/xlsx_read.py` | XLSX 工作簿读取与数据画像：sheet、表头、行列、缺失与样例预览 |
| frontend-design | `scripts/ai_tell_lint.py` | 机械检测“AI 生成感”前端文案/界面痕迹，提示模板腔、空泛词和常见坏味道 |
| frontend-design | `scripts/audit_checklist.py` | 前端布局质量可计算检查：对齐、间距、层级、密度、可读性等清单化输出 |
| idea-critique | `scripts/calibration.py` | idea 审查 calibration 模式：用已知结局样本估计 FNR/FPR，校准严格度 |
| idea-critique | `scripts/score_aggregate.py` | idea 八维评分加权聚合、否决项处理与 verdict 映射 |
| idea-critique | `scripts/sycophancy_guard.py` | 反谄媚协议的可计算检查，约束 idea 评审不要迎合式放行 |
| ip-application | `scripts/copyright_source_prep.py` | 软件著作权源代码材料整理：过滤/抽样/编号，避免提交敏感或无关代码 |
| ip-application | `scripts/patent_search.py` | 在先技术检索辅助，支持引用图一跳扩展 `--snowball` |
| literature-search | `scripts/cn_journal_probe.py` | 读取 ISSN 清单批量探测 OpenAlex source 体量，用于中文期刊/来源可见性初筛 |
| literature-search | `scripts/prisma_flow.py` | 系统综述 PRISMA 2020 流程留痕：核对筛选计数勾稽并产结构化流程数据 |
| literature-search | `scripts/search_normalize.py` | 多源文献检索与规范化，首轮即带后向引用边(OpenAlex / Crossref) |
| literature-search | `scripts/snowball.py` | 按一篇文献的前向被引与后向参考做“引用滚雪球”，扩展相关文献 |
| literature-search | `scripts/verify_citations.py` | DOI 引用核验与幻觉引用标记，辅助文献真实性检查 |
| paper-drafting | `scripts/draft_lint.py` | 论文草稿诚信门机检：claim 无源、结果/引用 GAP、夸大词与占位符风险 |
| paper-polishing | `scripts/mechanical_check.py` | 离线学术文稿机械检查：弱词、夸大、被动堆叠、占位符、句式坏味道 |
| paper-polishing | `scripts/polish.py` | LanguageTool 云端/本地降级的语法风格检查，输出结构化发现与 HTTP 元数据 |
| paper-polishing | `scripts/style_fingerprint.py` | 从用户过往文稿提取文风指纹，润色时校准作者声音而非通用模板 |
| project-structure | `scripts/scaffold.py` | 一条命令生成规范科研项目骨架，含 data/src/docs/experiments/figures/paper 等目录 |
| research-ethics | `scripts/check_retractions.py` | 批量撤稿/更正检查，通过 Crossref 等公开元数据标记 retraction risk |
| research-ethics | `scripts/text_overlap.py` | 离线自查重，定位与给定语料最长逐字重合片段，辅助学术规范审查 |
| result-analysis | `scripts/analyze_results.py` | 一条命令分析结果表：指标汇总、分组比较、排序与异常模式初筛 |
| result-analysis | `scripts/explain_shap.py` | 生成 SHAP 可解释性三图（beeswarm / bar / waterfall），无 shap 库时降级 |
| result-analysis | `scripts/leakage_overfit_check.py` | train/val/test gap 与数据泄漏风险筛查，提示过拟合和异常高分模式 |
| result-analysis | `scripts/make_figs.py` | 结果分析阶段的 matplotlib 出图模板，快速生成论文级统计图初稿 |
| result-analysis | `scripts/significance_test.py` | 显著性检验工具：p 值、效应量、置信区间、BH-FDR 多重校正 |
| review-rebuttal | `scripts/fetch_openreview.py` | 抓取 OpenReview 公开评审语料，校准模拟审稿与 rebuttal 话术 |
| slides | `scripts/thumbnail.py` | 把 PPTX/PDF 渲染成缩略图网格，快速做整套 deck 视觉 QA |
| slides | `scripts/to_pdf.py` | PPTX 转 PDF，优先 LibreOffice `soffice` 无头转换，用于后续视觉审查 |
| tool-selection | `scripts/detect_stack.py` | 读取项目清单文件识别技术栈，给出工具/技能选型建议 |
| typesetting | `scripts/precheck_log.py` | 扫描 LaTeX `.log`，汇总编译错误、警告、undefined citation/reference 等问题 |

## 仓库级资产校验

| 位置 | 文件 | 作用 |
|------|------|------|
| `.github/scripts/check_skills.py` | 技能 frontmatter 校验 | 检查 28 个 Light 技能的 `name` / `description` 与手动/常驻数量 |
| `.github/scripts/check_databases.py` | 数据库 YAML/schema/link 校验 | 检查 db03–db08 schema、重复卡片、YAML 解析与 README 本地链接 |
| `.github/scripts/check_skill_assets.py` | 脚本资产清单校验 | 检查 45 个技能脚本均登记到本文件、可编译、带 `__main__`；报告 selftest 覆盖缺口 |

## 可套用模板与数据文件

| 位置 | 文件 | 作用 |
|------|------|------|
| research-plan | `templates/research-plan.md` | 研究方案填空骨架，每节带成功标准/验证方式 |
| research-plan | `templates/experiment-matrix.md` | 实验矩阵：实验ID × 假设 × 数据集 × baseline × 指标 × 种子，含派生数据规格 |
| research-plan | `templates/reproducibility-checklist.md` | 可复现性勾选清单（环境/目录/配置/版本/流水线） |
| system-design | `templates/ci.yml` | GitHub Actions 轻量 CI 骨架（lint + test + 迁移校验） |
| project-structure | `templates/pre-commit-config.template.yaml` | pre-commit 质量门配置，scaffold 自动生成 |
| competition | `scripts/market_charts.py` 配套 | 市场图所需 JSON 字段与 db08 预算共用同一套 TAM/SAM/SOM |
| consistency | `assets/design_language_extract.template.md` | 从现有图/PPT/前端反推设计语言的抽取模板 |
| db05 | `design_tokens.template.json` | DTCG 格式视觉 token，论文图/PPT/前端/海报共用的取值锚点 |
| db09 | `lessons.md` | 跨项目方法论经验库，新项目立项时检索复用 |

## 技能间衔接约定

- 正文引用占位统一用 `\cite{authorYearWord}` / `author+year+标题首词` 公式，从草稿(drafting)到引用(citation)到排版(typesetting)同源。
- 图表交付带 manifest：图号 F#/T# + `source_card` + 矢量/位图路径 + caption + 章节 + 目标期刊/栏宽 + 导出/字号 checks，供论文初稿与排版直接引用。
- 实验阶段所需的派生评测集（加噪/缺失/跨域）回 data-engineering 构建。
- 各产出技能交付前过 self-review 自检闸门。
