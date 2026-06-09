# 脚本与模板清单

本仓库各技能内置的可运行脚本与可套用模板,按技能归类。脚本均为纯 stdlib 或常见科学计算库,支持离线自测;对外接口经实测。

## 可运行脚本

| 技能 | 脚本 | 作用 |
|------|------|------|
| literature-search | `scripts/snowball.py` | 按一篇文献的前向被引与后向参考做"引用滚雪球",扩展相关文献(OpenAlex / Semantic Scholar) |
| literature-search | `scripts/search_normalize.py` | 检索结果归一化,首轮即带后向引用边 |
| citation | `scripts/verify_citation_edge.py` | 核验"A 是否引用 B",返回 confirmed / not_in_open_index / unknown 三态(OpenCitations / S2) |
| citation | `scripts/verify_refs.py` | 校验参考文献,标注开放获取状态,仅对预印本告警 |
| citation | `scripts/doi_to_any.py` | DOI 转 BibTeX / CSL-JSON / GB-T 7714,中文条目自动注入 langid |
| result-analysis | `scripts/explain_shap.py` | 生成 SHAP 可解释性三图(beeswarm / bar / waterfall),无 shap 库时降级 |
| competition | `scripts/market_charts.py` | 渲染市场数据图:TAM/SAM/SOM 同心圆、竞品定位矩阵、五力分级、风险热图 |
| research-ethics | `scripts/text_overlap.py` | 离线自查重,定位与给定语料的最长逐字重合片段 |
| data-engineering | `scripts/check_access_level.py` | 数据访问分级守门:校验 raw/redacted/verified_only 数据能否流向某下游环节,raw 流向公开产物即阻断(退出码非零,可当 pipeline 闸门) |
| literature-search | `scripts/prisma_flow.py` | 系统综述 PRISMA 2020 流程留痕:核对各阶段计数勾稽(前阶段−排除=后阶段),抓出算术错误,产出流程图结构化数据 |
| paper-polishing | `scripts/style_fingerprint.py` | 文风校准:从用户过往文稿提取文风指纹(句长/被动/第一人称/连接词/标点),润色时校准到作者声音而非通用模板,标出待润色稿偏离最大的维度 |
| ip-application | `scripts/patent_search.py` | 在先技术检索,支持引用图一跳扩展(`--snowball`) |
| figure-drawing | `scripts/figure_export.py` | 按目标期刊栏宽精确导出图(矢量+位图),不裁剪尺寸 |

所有脚本输出已统一为 UTF-8,在 Windows 控制台不乱码。

## 可套用模板与数据文件

| 位置 | 文件 | 作用 |
|------|------|------|
| research-plan | `templates/research-plan.md` | 研究方案填空骨架,每节带成功标准/验证方式 |
| research-plan | `templates/experiment-matrix.md` | 实验矩阵:实验ID × 假设 × 数据集 × baseline × 指标 × 种子,含派生数据规格 |
| research-plan | `templates/reproducibility-checklist.md` | 可复现性勾选清单(环境/目录/配置/版本/流水线) |
| system-design | `templates/ci.yml` | GitHub Actions 轻量 CI 骨架(lint + test + 迁移校验) |
| project-structure | `templates/pre-commit-config.template.yaml` | pre-commit 质量门配置,scaffold 自动生成 |
| competition | `scripts/market_charts.py` 配套 | 市场图所需 JSON 字段与 db08 预算共用同一套 TAM/SAM/SOM |
| consistency | `assets/design_language_extract.template.md` | 从现有图/PPT/前端反推设计语言的抽取模板 |
| db05 | `design_tokens.template.json` | DTCG 格式视觉 token,论文图/PPT/前端/海报共用的取值锚点 |
| db09 | `lessons.md` | 跨项目方法论经验库,新项目立项时检索复用 |

## 技能间衔接约定

- 正文引用占位统一用 `\cite{author+year+标题首词}` 公式,从草稿(drafting)到引用(citation)到排版(typesetting)同源。
- 图表交付带 manifest(图号 F#/T# + caption + 章节 + 目标期刊/栏宽),供论文初稿直接引用。
- 实验阶段所需的派生评测集(加噪/缺失/跨域)回 data-engineering 构建。
- 各产出技能交付前过 self-review 自检闸门。

