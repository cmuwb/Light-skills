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

---

## 站 2：light-data-engineering（科研主线第 2 站，进行中）

详档 7 条可优化点（用户拍板"尽量全做 + 借鉴点也做"）：
- ✅ D-1 泄漏检测强化：data_doctor 加分类目标泄漏（数值特征 η² 相关比 + 类别特征条件纯度，纯 numpy/pandas）、ID-like 列检测（近乎逐行唯一）、低基数整数目标自动当分类、高基数阈值随行数自适应；selftest 加分类泄漏(leak_num η²/leak_cat 条件纯度)+id_like 断言全过；SKILL 同步
- ✅ D-2 safe_split 时序修正：prepare_timeseries() 按 --time-col 升序重排+校验单调（不给则显式警告非静默穿越）；pick_cv 加 group_is_clf 显式参数（--group-clf/--group-reg，不靠 nunique 猜），回退启发式标注"猜测"提醒；selftest 加乱序排序+警告+显式判定断言；SKILL 同步
- ✅ D-3 规模充足性判据：新建 sample_size_check.py（clf 每类最小样本/reg 样本特征比 EPV/detection 每类实例/二分类正例 EPV Peduzzi，ok/warn/insufficient 三档，--per-class 按最小类更严谨）；明确标注"非 power analysis 是经验粗筛、主结论须正式功效论证"；纯标准库 selftest 全过；登记+SKILL 四问引用
- ✅ D-4 worked_example + quality_gate 加固：quality_gate 加 severity(error/warn 分级，退出码只看 error；warn 仅警示)+ regex_mode(search/fullmatch)；新建 examples/worked_example.md 端到端走查(体检→规模→门禁→防泄漏划分→数据卡→四问总结，奶山羊场景)；selftest 加 severity/fullmatch 断言
- ✅ D-5 GitHub 借鉴（croissant）：新建 croissant_export.py 把数据卡字段→Croissant JSON-LD（MLCommons 机读标准，name/license/url/citation+RecordSet 字段字典+dtype 映射）；标"最小骨架须官方库校验"、缺字段 warn 不臆造；selftest 全过；登记+SKILL
- ✅ D-CI 四 CI 全绿（scripts 57→59）+ 6 脚本 selftest 全过 + 记忆更新

> 本站新增 2 脚本（sample_size_check/croissant_export），改 3 脚本（data_doctor 泄漏强化、safe_split 时序、quality_gate severity），加 1 worked_example。暂不做：非表格模态脚本、访问分级细化（单列）。

> 暂不做：非表格模态脚本(image_aug_check 等，模态鸿沟大单列)、访问分级细化(偏低优先)。

---

## 待做站（科研主线顺序）
idea-generation → idea-critique(已深做P1,补剩余) → research-plan → result-analysis(顺手补 R/MATLAB 作图三选) → paper-drafting → paper-polishing → figure-planning(已补E1) → figure-drawing → citation → typesetting → venue-matching(已补P2) → review-rebuttal → ip-application → slides(已补E2) → competition；常驻技能 file-reading/memory-pm/orchestrator/backend-coding/system-design/frontend-design/project-structure/consistency/self-review/tool-selection/research-ethics 按需。
