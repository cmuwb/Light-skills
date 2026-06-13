# 逐技能详细优化 · 进行中

> 按科研主线顺序逐个技能深做,每个技能:读详档可优化点 + GitHub 借鉴点 → 逐条落地 → selftest + 四 CI。一步不省。
> 输入:docs/analysis/skills/<skill>.md 的「可优化点」+「该技能可借鉴的点」。
> 已完成的前置:P0(诚实)/P1(阈值可调)/P2(批量·检索后端)/MCP 重订/工程化升级 E1-E3/MCP 适配表——这些是横切批次,本阶段是逐技能把剩余可优化点啃完。

---

## 站 1：light-literature-search（科研主线第 1 站，进行中）

详档 9 条可优化点中 P0/P1 已做 3 条（--api-key/mailto、补多源脚本、verify 阈值可配）。本站做剩余 + GitHub 借鉴（用户拍板"尽量全做 + 借鉴点也做"）：

- ✅ L-1 相关度过滤：search_normalize 加 filter_relevance()（require/exclude/min-score 三路）+ relevance_score（标题×query Jaccard）；dropped 带 drop_reason 留痕不静默丢；CLI --require-terms/--exclude-terms/--min-score；SKILL 加说明；selftest 三路全过
- ✅ L-2 cursor 分页：search_openalex/search_crossref 重构支持 max_results + cursor=* 深翻页（提取 _oa_rec/_cr_rec helper），CLI --max-results；snowball 两跳 top-N 改 --expand-top 可配（原写死 3）；SKILL 加穷尽检索说明；两脚本 selftest 过
- ✅ L-3 verify_citations 扩展：无 DOI 条目先试 arXiv id 核验（verify_arxiv 打 export.arxiv.org，命中标 ARXIV_VERIFIED+提示预印本）、再按标题 crossref_reverse_lookup 反查候选 DOI（按 title_sim 排序给人工确认不自动采信）；_extract_arxiv_id 支持新旧式；selftest 加 arXiv+反查用例；SKILL 同步
- ✅ L-4 端到端编排：新建 pipeline.py 串 search_normalize.run→snowball→verify_batch→prisma_flow.reconcile，复用各脚本函数不重复实现，出 literature_review.md 骨架（文献表+核验摘要+人工填占位）；全 offline selftest 串通四步+PRISMA 反例；登记 WHATS_INCLUDED + SKILL
- ✅ L-5 GitHub 借鉴（paper-tracker）：新建 tracker.py SQLite 持久化追踪——检索结果 upsert 去重（DOI/标题键）、记 first/last_seen+new/seen/read 状态+被引快照随轮更新、--new 列增量、md/json 导出；标准库 sqlite3 零依赖；selftest 内存库验证全流程；登记+SKILL
- ✅ L-CI 四 CI 全绿（scripts→57）+ 7 脚本 selftest 全过 + 记忆更新

> 本站新增 2 脚本（pipeline/tracker），改 3 脚本（search_normalize 相关度过滤+cursor、snowball expand_top、verify_citations arXiv+反查）。literature-search 详档可优化点已基本啃完（剩 SPECTER2 语义去重需 embedding 重依赖、references 瘦身、MCP 封装——单列暂不做）。

> 暂不做（标注）：SPECTER2 语义去重（需 embedding 模型/重依赖，超脚本轻量边界，单列）；references.md 瘦身分文件（结构优化非能力，低优先）；MCP server 封装（分发层，非本仓重点）。

---

## 后续站（科研主线顺序，待逐个做）
data-engineering → idea-generation → idea-critique(已深做P1,补剩余) → research-plan → result-analysis(顺手补 R/MATLAB 作图三选) → paper-drafting → paper-polishing → figure-planning(已补E1) → figure-drawing → citation → typesetting → venue-matching(已补P2) → review-rebuttal → ip-application → slides(已补E2) → competition；常驻技能 file-reading/memory-pm/orchestrator/backend-coding/system-design/frontend-design/project-structure/consistency/self-review/tool-selection/research-ethics 按需。
