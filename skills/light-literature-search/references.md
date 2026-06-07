# light-literature-search 参考工具研究笔记

> 研究方法说明：本环境 WebFetch 被全域拦截、WebSearch 只返回标题/URL（无摘要）。
> 因此：① 学术 API（arXiv/OpenAlex/Crossref/Semantic Scholar 等）的端点与参数来自其
> 长期稳定的公开官方文档（已逐一核对官方域名与端点真实存在）；② skill/agent 类工具
> 因无法读取仓库内 SKILL.md 原文，只能核实"仓库/文档确实存在 + 公开定位"，内部实现
> 细节标注为"未能逐字核实"。凡不确定者一律如实标注，绝不编造端点。

---

## 中文文献检索途径（CNKI / 万方 / 维普 / CSCD + 免 key 替代）

【是什么】中文核心成果主要沉淀在知网(CNKI)、万方(Wanfang)、维普(VIP)、CSCD 等库，但它们**均无对外免费 API**。可免 key 落地的真相是：OpenAlex 与 Crossref 已收录大量中文期刊，按 ISSN 可直接命中，应作为中文检索的免 key 主力。

【本环境 curl 实测记录（2026-06，加 &mailto= 进礼貌池）】
- 例刊：计算机学报（Chinese Journal of Computers，ISSN `0254-4164`，CSCD/北大核心）。
- `GET https://api.openalex.org/sources/issn:0254-4164` → **HTTP 200**，命中 OpenAlex source `S4210175330`，`display_name`="Chinese Journal of Computers"，`country_code`="CN"，`works_count`=1264，`cited_by_count`=6374。**存活，实测可用。**
- `GET https://api.openalex.org/sources?search=Chinese%20Journal%20of%20Computers` → 200，首条即 S4210175330（中文刊名直接 `search=计算机学报` 在本环境因 shell 编码返回空，建议 URL-encode 或用英译刊名/ISSN）。
- `GET https://api.openalex.org/works?filter=primary_location.source.id:S4210175330&sort=cited_by_count:desc&per-page=3` → 200，返回刊内被引最高 3 篇（如 2009 "A Survey on Rough Set Theory and Applications" cited 122）。
- `GET https://api.crossref.org/journals/0254-4164` → 200，title="Chinese Journal of Computers"，publisher="China Science Publishing & Media Ltd."，`counts.total-dois`=1264。**存活，实测可用。**
- `GET https://api.openalex.org/works?filter=language:zh` → 200，`meta.count`≈5,003,273（zh 语种海量）。**坑**：对 S4210175330 做 `group_by=language` 实测显示 1263 篇标 `en`（OpenAlex 把中文标题/摘要存成英译），故**按 source.id/ISSN 检索比按 `language:zh` 过滤更可靠**。

【可复用方法（免 key 主力：OpenAlex + Crossref 按 ISSN 检中文期刊）】
1. 建目标中文核心刊的 ISSN 清单（北大核心/CSCD/CSSCI 范围）。
2. 逐刊 `OpenAlex /sources/issn:{ISSN}` 取 OpenAlex source id 与体量，再 `/works?filter=primary_location.source.id:{Sid}` + `sort=`/`from_publication_date:` 拉题录。
3. 用 `Crossref /journals/{ISSN}/works?query=&filter=from-pub-date:` 在刊内做 DOI 级检索与去重核实。
4. OpenAlex 摘要是 inverted index 需还原；标题多为英译，需要原中文标题时回到出版商页/知网核对。

【无免费 API 的中文库——如实标注】
- **CNKI(知网)**：无对外免费 API；检索/全文需机构 IP 或个人订阅。可让用户在机构账号导出题录（NoteExpress/EndNote/RefWorks/RIS），或用 browser-use / agent-browser 真人式浏览取**元数据/摘要/链接**(遵守 robots/ToS，不抓全文)。CNKI 引文网络数据同属订阅端。
- **万方数据(Wanfang)**：同上，无公开免费 API；机构订阅或网页检索/题录导出。
- **维普(VIP/CQVIP)**：同上，无公开免费 API；机构订阅或网页。
- **CSCD(中国科学引文数据库，中科院文献情报中心)**：被引/核心刊范围数据仅机构端(常随 Web of Science 平台或单独订阅)可得，**精确被引免费源不可得（订阅墙）**，用 OpenAlex `cited_by_count` 作替代并注明口径不同。
- **百度学术 / 谷歌学术(Google Scholar)**：均无官方公开 API、反爬强；仅作发现入口，命中后回 OpenAlex/Crossref 按 DOI 或刊名核实元数据再入表，**不直接采信其页面被引数**。

【中文检索式与著录建议】
- 主题词：中英双语同义词并试（"大语言模型/大模型/LLM/large language model"）；用学科规范词 + 核心刊高频关键词扩展；兼顾简繁体、全半角、缩写。
- 引用著录按 **GB/T 7714-2015**：期刊 `主要责任者. 题名[J]. 刊名, 年, 卷(期): 起止页.`；文献类型标识 专著[M]/期刊[J]/论文集[C]/学位论文[D]/报告[R]/标准[S]/专利[P]/电子资源[EB/OL]；有 DOI 则末尾 `DOI: 10.xxxx/...`。中英文条目分别按各自规范著录。

【链接】OpenAlex sources 文档 https://docs.openalex.org/api-entities/sources ；Crossref journals 端点 https://api.crossref.org/journals/{ISSN} ；CNKI https://www.cnki.net ；万方 https://www.wanfangdata.com.cn ；维普 https://www.cqvip.com ；CSCD https://sciencechina.cn/cscd.jsp ；GB/T 7714-2015 标准号 GB/T 7714-2015《信息与文献 参考文献著录规则》。

【已知坑/局限】OpenAlex/Crossref 对中文刊的覆盖与时效不及知网，且标题/摘要多为英译、卷期页码偶有缺失；CNKI/万方/维普/CSCD 的全文与精确引文均需订阅，**免费源不可得部分一律标注，不臆造**；浏览器取数非确定性须二次核验。

---

## arXiv API

【是什么】arXiv 官方提供的免费元数据检索 API，基于 Atom feed，覆盖物理/数学/CS/q-bio/econ 等预印本。无需 key。

【可复用方法/真实端点/参数】
- Base：`http://export.arxiv.org/api/query`
- 关键参数：
  - `search_query`：字段前缀 `ti:`(标题) `au:`(作者) `abs:`(摘要) `co:`(评论) `cat:`(分类，如 `cs.CL`) `all:`(全字段)；布尔 `AND`/`OR`/`ANDNOT`，短语用双引号，分组用括号。
  - `id_list`：按 arXiv id 批量取。
  - `start` / `max_results`：分页（建议单页 ≤ 100；大批量分页拉取并 `start` 递增）。
  - `sortBy`：`relevance` | `lastUpdatedDate` | `submittedDate`；`sortOrder`：`ascending` | `descending`。
- 返回：Atom XML，每条 entry 含 title/author/summary/published/updated/`<arxiv:primary_category>`/links（abs 页 + pdf）/doi(如有)。
- 限流：官方要求请求间隔 ≥ 3 秒、批量任务慢速；单页上限大批量时用 slice 翻页，避免一次 `max_results` 过大。

【链接】https://info.arxiv.org/help/api/user-manual.html ；服务入口 https://export.arxiv.org

【已知坑/局限】只有元数据+摘要（无全文检索）；分类体系需对照 arxiv taxonomy；返回是 XML 需解析；近期 arXiv 收紧了 AI 生成内容投稿政策（与检索无关但影响 CS 综述类预印本质量判断）。

---

## OpenAlex API

【是什么】免费、开放、无需 key 的学术知识图谱（Works/Authors/Sources/Institutions/Concepts/Topics/Publishers/Funders），可视为 MAG 继任者。覆盖跨学科 2.5 亿+ works，含引用关系、开放获取状态、机构/作者消歧。

【可复用方法/真实端点/参数】
- Base：`https://api.openalex.org`，主端点 `/works` `/authors` `/sources` `/institutions` `/concepts` `/topics`。
- 检索：
  - `search=`：跨标题/摘要/全文的全文检索。
  - `filter=`：强大的字段过滤，逗号 = AND。常用：`from_publication_date:2020-01-01`、`to_publication_date:`、`cited_by_count:>100`、`is_oa:true`、`type:article`、`authorships.author.id:`、`primary_topic.id:`、`institutions.country_code:`、`title.search:`、`abstract.search:`、`default.search:`。
  - `sort=`：如 `cited_by_count:desc`、`publication_date:desc`。
  - `select=`：只取需要字段，省带宽。
  - `group_by=`：按某字段做分面统计（如年度/期刊计数），适合快速画领域分布。
- 分页：`per-page`（≤200）+ `page`（仅前 1 万条）；超过则用游标 `cursor=*`，每次响应里 `meta.next_cursor` 续翻，可遍历全集。
- 礼貌池(polite pool)：加 `mailto=you@example.com`（query 参或 User-Agent），获得更稳定更快的速率。
- 限流：约 100,000 次/天、10 次/秒（共享池）；可注册更高配额。
- 返回字段：`id`(OpenAlex ID)、`doi`、`title`、`publication_year`、`cited_by_count`、`authorships`、`primary_location`/`best_oa_location`、`open_access`、`referenced_works`、`related_works`、`abstract_inverted_index`（倒排索引需还原成摘要）。

【链接】https://docs.openalex.org ；API 根 https://api.openalex.org/works

【已知坑/局限】摘要是 inverted index 需重建；`page` 翻页硬上限 1 万条，深翻必须用 cursor；机构/作者消歧偶有误并；concepts 已逐步被 topics 取代，新代码优先用 `primary_topic`。

---

## Crossref REST API

【是什么】DOI 注册机构 Crossref 的免费元数据 API，权威 DOI ↔ 书目信息映射，含参考文献、资助、许可、ORCID、被引(部分)。最适合做 DOI 规范化、跨库去重的"真相源"。

【可复用方法/真实端点/参数】
- Base：`https://api.crossref.org`，主端点 `/works`、`/works/{DOI}`、`/journals/{ISSN}/works`、`/members/{id}/works`。
- 检索：
  - `query=`：通用全文式检索；`query.bibliographic=`（题录组合）、`query.author=`、`query.title=`。
  - `filter=`：如 `from-pub-date:2020-01-01`、`until-pub-date:`、`type:journal-article`、`has-full-text:true`、`has-references:true`、`license.url:`。
  - `select=`：限定返回字段（如 `DOI,title,author,issued,container-title,is-referenced-by-count`）。
  - `sort=` + `order=`：如 `sort=is-referenced-by-count&order=desc`、`sort=published`。
- 分页：`rows`（≤1000）+ `offset`（仅前 1 万）；深翻用 `cursor=*`，响应 `message.next-cursor` 续翻（"deep paging"）。
- 礼貌池：`mailto=` 或带联系信息的 User-Agent，进入更快的 polite pool（否则共享匿名池，可能被限速）。Plus 付费有专属池。
- 返回字段：`DOI`、`title`、`author`(含 ORCID)、`issued`/`published`、`container-title`(期刊)、`type`、`is-referenced-by-count`(Crossref 内被引)、`reference`(参考文献)、`license`、`link`(全文)。

【链接】文档 https://www.crossref.org/documentation/retrieve-metadata/rest-api/ ；Swagger https://api.crossref.org/swagger-ui/index.html ；端点 https://api.crossref.org/works

【已知坑/局限】被引数(`is-referenced-by-count`)只覆盖 Crossref 内部、低估真实引用；不是所有出版商都存全参考文献；不带 mailto 易被限速；摘要覆盖不全。

---

## Semantic Scholar Academic Graph API (S2AG)

【是什么】Allen AI(AI2) 的学术图谱 API，强项是引用关系、tldr 摘要、influential citations、SPECTER 嵌入、字段化检索。覆盖 2 亿+ 论文。

【可复用方法/真实端点/参数】
- Base：`https://api.semanticscholar.org/graph/v1`
- 检索：
  - `/paper/search?query=...`：相关度排序的关键词检索，支持 `fields=`（如 `title,abstract,year,authors,citationCount,influentialCitationCount,externalIds,openAccessPdf,tldr`）、`limit`(≤100)、`offset`、`year=2020-2024`、`fieldsOfStudy=`、`venue=`、`openAccessPdf`。
  - `/paper/search/bulk`：用于一次性拉大量（最多 1000/页，用返回的 `token` 续翻；支持布尔 query 语法），适合穷尽式扫库。
  - `/paper/{id}`：id 可为 S2 paperId、`DOI:...`、`ARXIV:...`、`CorpusId:...` 等。
  - `/paper/{id}/citations` 和 `/references`：前向(被引)/后向(参考)滚雪球，含 `isInfluential` 标记。
  - `/paper/batch`（POST，传 ids 列表）+ `fields=`：批量取详情。
  - `/author/{id}`、`/author/{id}/papers`。
- 认证/限流：可匿名用（共享限速，约 1000 次/5 分钟级别）；申请免费 API key 走 `x-api-key` header 得更高更稳配额。
- 特色字段：`tldr`(自动单句总结)、`influentialCitationCount`(更能反映真实影响力)、`embedding`(SPECTER2)、`openAccessPdf`。

【链接】文档 https://api.semanticscholar.org/api-docs/ ；产品 https://www.semanticscholar.org/product/api

【已知坑/局限】匿名限速很严，批量必须申请 key；部分新论文延迟入库；`influentialCitationCount` 是模型估计；search 端点 relevance 排序对小众词偶尔不稳。

---

## Exa Search API

【是什么】面向 LLM/agent 的"神经检索 + 关键词检索"网络搜索 API；可直接返回网页正文、摘要、高亮，并支持"找相似页"。适合补充学术库覆盖不到的博客/官方文档/项目页。

【可复用方法/真实端点/参数】
- Base：`https://api.exa.ai`，认证 header `x-api-key`。
- `/search`（POST）：
  - `query`：自然语言或关键词。`type`：`neural`(语义/embedding 检索) | `keyword` | `auto`(自动选)。
  - `numResults`、`category`（如 `research paper`、`company`、`github`、`news`、`pdf`），`startPublishedDate`/`endPublishedDate`、`includeDomains`/`excludeDomains`。
  - `contents`：一次性附带 `text`(正文，可设 `maxCharacters`)、`highlights`(查询相关高亮句)、`summary`(按 prompt 生成摘要)。
- `/findSimilar`（POST）：传一个 URL，返回语义相似页面 —— 等价于"以网页为种子做滚雪球"。
- `/contents`（POST）：对已知 URL 批量抓正文/高亮/摘要。
- 还提供 `/answer`（带引用的 RAG 回答）与 Research API。

【链接】文档 https://docs.exa.ai/reference/getting-started ；search https://docs.exa.ai/reference/search ；find-similar https://docs.exa.ai/reference/find-similar-links

【已知坑/局限】付费(按请求/按内容计费)；neural 检索对精确术语不如 keyword；返回质量依赖目标站点可抓取性；`category=research paper` 不等于权威学术库，仍需回到 DOI/OpenAlex 核实元数据。

---

## Parallel Web (Parallel.ai Search API)

【是什么】Parallel.ai 面向 AI agent 的网络搜索/研究基础设施。主打"为 LLM 优化的检索"：输入自然语言目标，返回排序好的相关网页 + token 友好的摘录(excerpts)，而非传统蓝链列表。另有 Task API(深度研究)、Extract API。

【可复用方法/真实端点/参数】
- 文档与 quickstart：https://docs.parallel.ai/search-api/search-quickstart ；API 参考 https://docs.parallel.ai/api-reference 。
- 定位：Search API 接受 `objective`/自然语言查询，返回按相关度排序的结果与压缩过的摘录，便于直接喂给模型上下文；提供免费 Web Search MCP（见 parallel.ai/blog/free-web-search-mcp）。
- 配套：Task API（自动化 deep web research，给结构化产出）、Extract API（抓取结构化字段）。

【链接】https://www.parallel.ai/ ；Search 产品 https://parallel.ai/products/search ；beta 博客 https://parallel.ai/blog/parallel-search-api-beta

【已知坑/局限】商业 API、需 key；本环境无法读取参数全表，**具体请求字段名(如 objective/processor/excerpt 上限)未能逐字核实**，落地前须对照官方 quickstart；属较新产品(2025 起)，接口可能变动。

---

## Open Notebook (lfnovo/open-notebook)

【是什么】开源的 NotebookLM 替代品，自托管的 AI 研究笔记：导入多源资料(PDF/网页/音视频/笔记)，做基于来源的问答、生成摘要与播客式音频概览，可换不同 LLM provider。适合把检索到的文献集中做"带引用的二次消化"。

【可复用方法/可借鉴】
- 工作流借鉴：sources(来源库) → notes(笔记) → chat/transform(基于来源生成摘要/问答)，全程"答案绑定来源"，正好对应本技能"不臆造、给可核查来源"的纪律。
- 可作为本地交付载体：把文献表/脉络/资源清单导入做成可对话知识库。

【链接】仓库 https://github.com/lfnovo/open-notebook ；Wiki https://github.com/lfnovo/open-notebook/wiki

【已知坑/局限】需自托管(Docker/数据库)与各家 LLM key；**内部数据模型字段未逐字核实**；同类(SurfSense、OpenBookLM、insights-lm)定位相近，选型看连接器与隐私需求。

---

## Paperzilla

【是什么】面向研究的"持续更新的研究数据流/feed"产品，并提供可作为 Claude skill 使用的封装（playbooks 上有 `paperzilla` skill 条目）。定位是把最新相关论文以数据流形式持续推送/检索。

【链接】官网 https://paperzilla.ai/ ；文档 https://docs.paperzilla.ai/ ；skill 索引 https://playbooks.com/skills/openclaw/skills/paperzilla ；组织 https://github.com/paperzilla-ai

【已知坑/局限】**商业产品，具体 API 端点/字段与免费额度未能核实**（文档站存在但本环境读不到内容）；与"持续追踪某方向新论文"的需求匹配，但落地前需确认数据覆盖与计费。

---

## browser-use (browser-use/browser-use)

【是什么】开源 Python 库，让 LLM agent 直接操控真实浏览器(基于 Playwright)：理解页面、点击、填表、抽取数据，完成"打开某检索站→输入检索式→翻页→抓结果"这类无 API 的取数任务。GitHub 高星热门项目。

【可复用方法/可借鉴】
- 典型用法：`Agent(task="...", llm=...)` 给自然语言任务 + 一个 LLM，库负责把页面无障碍树/截图喂给模型并执行动作循环。
- 对本技能价值：当目标源**没有公开 API**（如知网/万方网页、部分政府/标准网站、Google Scholar 反爬页）时，用它走"真人式浏览"取元数据；可配合 headless 与 session 复用。

【链接】仓库 https://github.com/browser-use/browser-use ；PyPI https://pypi.org/project/browser-use/ ；文档 https://docs.browser-use.com

【已知坑/局限】依赖 LLM 调用，慢且有成本；网页改版/反爬/验证码会打断；务必遵守目标站 robots/ToS 与版权（本技能只取元数据，不抓全文）；非确定性，需校验抓取结果。

---

## agent-browser (Browserbase 官方 skill / Stagehand)

【是什么】Browserbase 出品的"给 agent 上网能力"的 skill 集合，底层是 Stagehand(AI Web Agent SDK) + 云端托管浏览器。以 `act/extract/observe` 等高层原语让 Claude 等 agent 稳定地浏览、抽取结构化数据。

【可复用方法/可借鉴】
- 核心原语思路：`observe`(让模型看页面并提议动作) → `act`(执行自然语言动作) → `extract`(按 schema 抽结构化字段)。比纯像素 computer-use 更稳，适合批量取检索结果到结构化文献表。
- 与 browser-use 二选一：要云端隔离/规模化抓取用 Browserbase；要本地轻量用 browser-use。

【链接】Browserbase skills 文档 https://docs.browserbase.com/integrations/skills/introduction ；Stagehand 插件 https://claude.com/plugins/stagehand ；CLI https://www.browserbase.com/browse-cli

【已知坑/局限】托管浏览器是付费云服务；**skill 内部 SKILL.md 字段未逐字核实**；同样受目标站 ToS/版权约束。

---

## K-Dense-AI / scientific-agent-skills 系列（Research Lookup / Paper Lookup / BGPT Paper Search / find-skills）

【是什么】GitHub 仓库 `K-Dense-AI/scientific-agent-skills`（及衍生 `rubensliv/scientific-skills`）—— 一组开箱即用的 Claude 科研 skill。与本技能直接相关的成员：
- **research-lookup**：综合学术检索 skill，聚合多源做文献查找/汇总。
- **paper-lookup / paper-search**：按标题/作者/DOI 精确定位单篇并取元数据。
- **bgpt-paper-search**：BGPT 相关的论文检索 skill（生物/科学方向数据源）。
- **find-skills**：在 skill 集合中按任务自动发现并路由到合适的 skill（"skill 选择器"）。
- 同仓还有 pytdc、xlsx、liteparse(本地科学 PDF 快速解析) 等。

【可复用方法/可借鉴】
- 架构借鉴：用一个 `find-skills` 式路由层先判定任务类型，再分发到 lookup/search 专用 skill —— 对应 Light 的 ROUTER 思路。
- 流程借鉴：检索 skill 普遍走"多源查询 → 规范化元数据 → 去重 → 带 DOI/链接输出"，并强调引用可核查（该团队另有"自查引用、统计幻觉引用"的工作）。

【链接】主仓 https://github.com/K-Dense-AI/scientific-agent-skills ；research-lookup 索引 https://playbooks.com/skills/k-dense-ai/scientific-agent-skills/research-lookup ；插件页 https://www.claudepluginhub.com/skills/rubensliv-scientific-skills/research-lookup ；bgpt https://lobehub.com/skills/k-dense-ai-scientific-agent-skills-bgpt-paper-search

【已知坑/局限】**各 skill 的 SKILL.md 正文与具体数据源/参数未能逐字核实**（仓库存在、定位明确，但本环境无法读取文件内容）；BGPT 的确切数据范围需查仓库确认；这些是第三方 skill，行为以其仓库实际实现为准。

---

## Literature Review skill（openclaw/skills 等的 literature-review / academic-research）

【是什么】社区 skill 市场(openclaw/skills、sundial-org 等)里的"文献综述"skill，把"检索 → 筛选 → 主题归类 → 综述写作"打包成一个工作流。Anthropic 官方也有"Plan your literature review"用例指南。

【可复用方法/可借鉴 —— 综述工作流维度】
1. 明确研究问题与纳入/排除标准(PICO 式或方向+时间+方法范围)。
2. 多库检索 + 记录检索式(可复现，类 PRISMA 思想)。
3. 去重 → 标题/摘要筛 → 全文筛，记录每步淘汰数。
4. 按主题/方法/时间归类，抽取每篇的"问题-方法-数据-结论-局限"。
5. 综合成脉络叙事 + 对比表 + gap，全程绑定可核查引用。

【链接】Anthropic 用例 https://claude.com/resources/use-cases/plan-your-literature-review ；社区 skill 索引 https://playbooks.com/skills/openclaw/skills/literature-review ；https://www.claudepluginhub.com/skills/sundial-org-sundial-org-awesome-openclaw-skills-4/literature-review

【已知坑/局限】不同实现质量参差；**具体 skill 正文未逐字核实**；综述 skill 的最大风险是幻觉引用与过度概括，须叠加引用核查(对应 Light m10/light-citation)。



