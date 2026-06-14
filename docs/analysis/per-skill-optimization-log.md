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

## 站 3：light-idea-generation（科研主线第 3 站，已完成）

原零脚本（纯流程编排），详档核心矛盾"量化环节全靠手工不可复现"。本站把量化环节脚本化 + 补黄金样例：
- ✅ G-1 card_gate.py 立项卡交接门禁：校验 (m04复核) 字段非空/最近邻≥3带留痕/新颖性归档三档/撞车自评选档/无模糊词，残卡拒绝交 m04
- ✅ G-2 rank_ideas.py 候选排序：影响×工作量性价比确定性排序+先做/缓做/砍，收敛三套评分为唯一裁定
- ✅ G-3 candidate_dedup.py 去重/伪多样性：零依赖文本相似度(默认)或 SPECTER2 余弦(--emb)，批内 mean+1σ 自动标变体，把含糊阈值算法化
- ✅ G-4 examples/idea_candidates.example.md：2 张分层卡(稳/冲)，撞车四问留痕合格写法，可过 card_gate
- ✅ G-5 文档修：SKILL 三套评分分工(三维triage/影响工作量主排序/五维终检)+发散收敛漏斗(≥15→3-6)+脚本examples入文；references 未来日期文献标"待核"
- ✅ G-CI 四 CI 全绿（scripts 59→62）+ 记忆

---

## 站 4：light-idea-critique（科研主线第 4 站，已完成）

P1/P2/E3 已深做 7 条（阈值可调/权重敏感性/结构化多样性/领域profile/calibration三分类/批量排序/novelty_audit）。本站补详档剩余 3 条 + 1 借鉴：
- ✅ C-1 离线降级检索协议：SKILL Step2 加状态机——evidence-missing 时创新性封顶、整体最高"有条件通过"绝不放行"通过"、联网二次检索补齐才改判；无网时闸门只收紧不放松（与 m10/a10 离线降级同脉）
- ✅ C-2 sycophancy_guard 修小 N 脆弱：N<4 用绝对让步计数门限补百分比阈值脆弱（2 条 1 让步=50% 不报警的盲区）；autonomous 模式连续让步第二条自动降级到 3（不留人工口子）；selftest 加小N/自主/大N 用例
- ✅ C-3 输出压缩纪律：protocol.md 加「输出压缩纪律」（共识去重只列一次/每视角≤150字/判决正文只留可执行项/一个关切一处），治五视角+DA+IF+反驳栈冗长
- ✅ C-4 GitHub 借鉴（SciMuse）：score_aggregate decide(interestingness=) 边界复核——idea 被否决压到不通过但 Weighted 近通过线+有趣度高时出"边界复核建议"提示人工，只提示绝不自动放行（缓解二元否决误杀）；selftest 加边界用例
- ✅ C-CI 四 CI 全绿 + SKILL 同步（Step5 小N/自主、Step6 边界复核+压缩）

---

## 站 5：light-research-plan（科研主线第 5 站，进行中）

详档 6 条可优化点（用户拍板"都做 + 借鉴一个"）：
- ✅ R-1 plan_lint 语义一致性弱校验：除四要素齐全(硬 gate)外加 warning 级——①完成判定可量化阈值(数字/不等号/p值)②判定提及指标关键词(防脱节)③假设-实验覆盖度(每假设有 ABL 消融)；治核心卖点"绿了但错了"；selftest 加语义/覆盖度用例
- ✅ R-2 power_check.py 新脚本：输入效应量/重复数→实际 power+达标最小重复数，纠"≥5 种子"对中效应欠功效误区（实跑印证 d=0.5 n=5 power=0.11、需 64/组）；statsmodels 优先缺失降级正态近似(Acklam ppf)标[APPROX]；selftest 全过
- ✅ R-3 SKILL 规划档位分级（轻量 requirements+种子+目录+跑批 / 标准 +Hydra+MLflow / 完整 +DVC+Snakemake）避免重型工具劝退小课题 + Windows 友好流水线并列项（Snakemake 标 WSL，补 invoke/纯Python）
- ✅ R-4 复现日志模板 reproduction-log.md（逐次改了什么/得到的数/与目标差/下一步假设 + 失败三分归因）+ SKILL 衔接技能速查表（展开 db03/08/09）+ 算力参考价区间（4090/A100/H100 量级锚点，标必现查）
- ✅ R-5 GitHub 借鉴（ARA Rigor Reviewer）：plan_lint 加严谨性评分卡（0-100 经验扣分制+分项：四要素齐全/判定可量化/判定指标对齐/有消融覆盖），把校验升级为可审计评分
- ✅ R-CI 四 CI 全绿（scripts 62→63，模板 39→40）+ 记忆

---

## 站 6：light-result-analysis（科研主线第 6 站，已完成）

详档 7 条可优化点 + 你交代的 R/MATLAB 作图三选（用户拍板"都做 + 借鉴一个"）：
- ✅ A-1 claim_evidence_table 生成：analyze_results --emit-claim-table，每个比较(claim)连证据字段(检验/p/q/d/CI/n)落盘 §6.1 工件，显著性以 BH-FDR 后 q 为准+诚实写作约束(不显著不得称更好)；治"反复强调却无人产出"名实不符
- ✅ A-2 切片分析脚本化：--slice-by <col> 逐切片复算 EDA+检验+效应量+FDR+标小 n 切片"待核查"，兑现 references 切片协议(公平性敏感属性可作 slice_by)
- ✅ A-3 多组检验稳健性：k≥3 正态先 Levene 方差齐性→齐用 ANOVA 不齐切 Welch-ANOVA(纯 numpy 实现)；最小组 n<10 加 Shapiro 功效不足警告；leakage 阈值 CLI 化(--gap-overfit 等，报告标用哪套)
- ✅ A-4 R/MATLAB 作图三选：SKILL 静态出版图扩 Python(默认)/R(ggplot2 ggsave units=mm)/MATLAB(exportgraphics vector)三选并列，按项目栈选，细节指 m11
- ✅ A-5 GitHub 借鉴(DeLong)：significance_test 加 delong_two_auroc——同测试集两模型 AUROC 比较(相关样本扣协方差)，与 sklearn roc_auc_score 对齐，selftest auc 0.985 vs 0.575 p≈0
- ✅ A-CI 四 CI 全绿（scripts 仍 63，只改不增）+ 记忆

---

## 站 7：light-paper-drafting（科研主线第 7 站，已完成）

详档 8 条可优化点（用户拍板"claim台账+draft_lint重写+CS/ML规范+综述微流程 + 借鉴一个"）：
- ✅ P-1 新增 templates/claim_passport.md：claim 台账(ID/类型①②③④/来源指针/核查状态 已验证·待核·GAP/HTTP码)，补 integrity_gate 反复要求却无实体的 load-bearing 工件
- ✅ P-2 draft_lint.py 重写：HYPE×SIG 改同句/相邻句窗口共现(治长段落误报)、跳过 ``` 代码围栏(治示例代码假阳)、REQUIRED_SECTIONS 改行首标题校验(治散句误判)、加 --claims 抽候选事实句播种台账、加 --json 机读输出；selftest 加 4 条新断言全过
- ✅ P-3 guideline_map 增补 §1b CS/ML 报告件(NeurIPS/ICLR reproducibility checklist/Datasheets/Model Cards/TRIPOD+AI，治偏医学)；SKILL 相关工作加综述合成微流程(taxonomy 轴选取+delta 句骨架+强 baseline 锁定)
- ✅ P-4 GitHub 借鉴(hallucinator 精神)：对 references.md 自身执行诚信门——Nature s41586-026/arXiv 2604.05018/CNPE 2603.17588 三条未来日期文献标"待核条目，勿当既成事实"
- ✅ P-CI 四 CI 全绿（模板 40→41）+ 记忆

---

## 站 8：light-paper-polishing（科研主线第 8 站，已完成）

详档 8 条可优化点（用户拍板"全做 + 借鉴一个"）：
- ✅ PP-1 strip_latex 预处理：去 \\command/$...$/注释/environment 保纯 prose 且维护行号，mechanical_check --latex 直接吃 .tex 不爆误报（最影响实用性的缺口）
- ✅ PP-2 误报修复：overclaim 上下文豁免(statistically significant 不报、方法名专名跳过)；句切分加缩写保护(et al./e.g./Fig. 不误断)；hedge_stack 改迭代 offset 修重复句定位 bug
- ✅ PP-3 契约漂移：claim_strength 补进 findings_schema §3 类别表+§4 severity(major)+SKILL m14 映射，三处同步
- ✅ PP-4 polish.py 限流/降级修复：改每 chunk 独立降级(某 chunk 失败只降它、其余保留 LT 结果，mode=mixed)，chunk 间 sleep 控速 + 429/5xx 指数退避重试(治长论文一块失败全丢)
- ✅ PP-5 GitHub 借鉴(中文支撑)：中文夸大词(显著/大幅提升/前所未有)+AI 腔(综上所述/值得注意的是)词表子串匹配，补"英文中心、中文稿失效"
- ✅ PP-CI 四 CI 全绿（脚本只改不增）+ 记忆；mechanical_check/polish selftest 加 strip_latex/豁免/缩写/中文/per-chunk-fallback/retry 新断言全过

---

## 站 9：light-figure-planning（科研主线第 9 站，已完成）

详档 7 条可优化点中 #1(validate_plan_card)已 P2 做、#2(Draco 图型推荐)已 E1 做。本站补剩余 5 条 + 借鉴：
- ✅ FP-1 examples/worked_example.md：claim→图表清单全景(必做/可做/可删判定)+3 张填满卡(F1定量图/T1消融表/F3框架图)，展示图卡 vs 表卡字段差异
- ✅ FP-2 table_plan_card.md 表专用变体：去 color_scheme/layout，加行列结构/表头分组/对齐/有效位数/最优标注/booktabs三线表/跨页横排
- ✅ FP-3 display item 预算步骤：规划流程加 step5 统计 F#+T# 对照 venue 上限(6-8件)、超则砍序(可删→可做降附录→必做不动)；自检清单 13→14 点加数量核查
- ✅ FP-4 文档修：栏宽数据标"快照+唯一真相源 figure_export.py+同步日期"杜绝漂移；修 5pt vs 6-7pt 字号矛盾(5pt 仅 Nature 实测、通用≥6-7pt)；加代号图例表(m02/m06/m11/db07 等)；5维评分限定为示意图专用、数据图用客观 QA
- ✅ FP-5 GitHub 借鉴(figure-designer)：论文三类核心图范式速查表(动机图痛点对比/方法图管线流/结果图分组柱+误差棒)，规划落到具体范式而非"放一张图"
- ✅ FP-CI 四 CI 全绿（模板 41→42）+ 记忆

---

## 站 10：light-figure-drawing（科研主线第 10 站，已完成）

详档 7 条可优化点（用户拍板"全做 + 借鉴一个"）：
- ✅ FD-1 figure_integrity_lint 假阴性修复：ERRTYPE 排除 `.std()` 方法调用(原 \bstd\b 把 numpy 计算误当误差类型声明压掉警告)、BAR 补 `sns.barplot`、SETYLIM 补 `set_ylim(bottom=)` 关键字形式、DISTRIB_PLOT 检测;selftest 加 4 条假阴性回归全过
- ✅ FD-2 字体落空告警：figure_export 加 `_check_font_availability()`，导出前用 font_manager 查 Arial/Helvetica 首选项是否真可用，回退 DejaVu 即 WARNING 入 info["font"]，让"字体与正文一致"可验证
- ✅ FD-3 check 补校验维度：新增 `check_export_compliance()` 消费闲置字段(实测 dpi≥min_dpi/体积≤max_file_mb/高度≤max_height_px/格式∈preferred_formats)，plos 补 max_height_px+max_file_mb 字段
- ✅ FD-4 check_scaled_fonts 澄清(docstring+SKILL 标"仅大画布工作流，save_for_journal 流程空操作非 bug")+ MDPI column_caveat(single/full 都170mm,column 不分宽窄)+ examples/bad_figure_example.py 故意违规负例(端到端命中 4 类警告)
- ✅ FD-5 GitHub 借鉴(tueplots)：references 加 tueplots 对照(venue 字号联动更全，可对照补 JOURNAL_SPECS+窄栏建议字号)，承认其在 ML 会议 venue 换算上更全
- ✅ FD-CI 四 CI 全绿（scripts 仍 63 只改不增，新增 examples 负例）+ 记忆

---

## 站 11：light-citation（科研主线第 11 站，已完成）

P0/P1 已修邮箱硬编码(B2-B4)+verify_refs sim 阈值(M1)。本站补剩余 + 借鉴：
- ✅ CT-1 GB/T7714 CJK 作者特判：_has_cjk 判定，中文名整名连写不缩写(修"张伟→张 W."bug)；[EB/OL] 电子资源带访问日期(缺则显式"访问日期待补"占位不静默丢)
- ✅ CT-2 撤稿检测真兜底：verify_refs summary 加 retraction_coverage+retraction_signals_used，显式区分"已用信号"vs"未覆盖经典撤稿"，retracted_count=0≠保证干净，提示交叉查 Retraction Watch/a10 第二跳
- ✅ CT-3 新建 citekey_audit.py：\cite 键↔.bib 键双向差集(缺失/冗余/重复定义)+authorYearWord 命名校验，支持 LaTeX `\cite*` 与 pandoc `[@key]`，零依赖
- ✅ CT-4 清死引用(references 指向根 _verification_log 的断链改内联)+self-author 升级(作者姓精确匹配非整串子串，降 Wang/Li 高频姓误报)
- ✅ CT-5 GitHub 借鉴(PHY041)：verify_refs 嵌合引用检测(claimed={first_author,title} 时 DOI/标题真但首作者不符→is_chimeric，真标题配错作者的 AI 幻觉)
- ✅ CT-CI 四 CI 全绿（scripts 63→64）+ 记忆

---

## 站 12：light-typesetting（科研主线第 12 站，已完成）

详档 6 条可优化点（用户拍板"全做 + 借鉴一个"）：
- ✅ TS-1 新建 submission_check.py：投稿合规/匿名雷区扫描（双盲未匿名 \author/致谢/基金/可识别链接、PDF 元数据 /Author 露名、页数上限、残留 TODO），补零自动化的 desk-reject 盲区；纯标准库 PDF 元数据正则扫
- ✅ TS-2 precheck_log.py 加 --strict（undefined ref/cite/重复 label 升级致命阻断）+ de-wrap（79 列硬折行拼回再匹配，消除长引用名漏报）
- ✅ TS-3 docx_template.js 重写：删 topBottom(width) 死参、加真多级列表（numbering LevelFormat 自动连号替手敲编号）、默认字体加 eastAsia CJK（中英混排不回退）；node --check 语法过
- ✅ TS-4（并入 SKILL）：precheck/submission/docx 新能力写进 SKILL 步骤+脚本描述；骨架补全要点随说明
- ✅ TS-5 GitHub 借鉴（arxiv-latex-cleaner）：SKILL 加投稿出包前净化说明（去注释真名/压图/删冗余 bib，配 submission_check 双保险）
- ✅ TS-CI 四 CI 全绿（scripts 64→65）+ 记忆

---

## 站 13：light-venue-matching（科研主线第 13 站，已完成）

P2 已补转投顺序+DOAJ。本站补剩余 + 借鉴：
- ✅ VM-1 自引信号口径修：明确 outgoing 非 incoming，25%/40% 仅作参考提示非掠夺判据（综述/窄领域刊 outgoing 天然偏高），加 self_ref_direction+threshold_note，掠夺判定须看 incoming+领域+预警名单
- ✅ VM-2 五信号编号统一：summary 加 rubric_coverage 显式列脚本可程序化覆盖维度 vs 仍须人工维度（接收率/创新匹配/incoming自引/口碑），破"跑完脚本=完成评估"误解
- ✅ VM-3 最低可评估信号门槛：summary.signals_ok<2 时 min_signal_gate 给"数据不足暂不下定性结论"，防数据稀疏退化主观硬凑
- ✅ VM-4 db01 冷启动指南：SKILL step1 加"db01 为空时用 OpenAlex Sources API 现拉候选+建最小种子临时卡(字段对齐 venues.csv)"分支，消除新用户卡第一步
- ✅ VM-5 GitHub 借鉴(journal_targeter)：转投顺序加方向匹配度量化(suitability 思路，topics 重叠+关键词词重叠给 0-1 分+列命中/缺失主题词，可解释)
- ✅ VM-CI 四 CI 全绿（脚本只改不增）+ 记忆

---

## 站 14：light-review-rebuttal（科研主线第 14 站，已完成）

详档 7 条可优化点（用户拍板"全做 + 借鉴一个"）：
- ✅ RR-1 rebuttal_budget venue 预设填真值：iclr/neurips 加 max_chars(5000/6000,OpenReview 框)、cvpr max_words=1000(1页近似)，assess 支持字符/词数双口径取更严，"必跑+FAIL拦截"承诺真生效(原三会 0、形同虚设)；加 --max-chars CLI
- ✅ RR-2 新建 templates/response_matrix.md：全量意见台账(ID/原文/分类/concession分/回应/改动位置/re-review判定/承诺状态)，明确与 rereview_checklist 关系(全量台账 vs 放行门)
- ✅ RR-3 模式一两段式强化为四步不可跳过(选rubric→paper-blind写预期→visible打分→PRISM自查)，标注 paper-blind 是命门别省
- ✅ RR-4 显式声明 m10 light-citation 硬依赖(新引用必经 verify_refs+citekey_audit，rebuttal 临时加引用最易幻觉)+response_matrix 模板链接
- ✅ RR-5 GitHub 借鉴(承诺账本强制阻断)：本技能已具备 COMMITMENT_GAP+rereview 放行门，response_matrix 承诺状态列与之对接，不重复造
- ✅ RR-CI 四 CI 全绿（scripts 65→66 登记 rebuttal_budget，新增 response_matrix 模板）+ 记忆

---

## 待做站（科研主线顺序）
ip-application → slides(已补E2) → competition；常驻技能 file-reading/memory-pm/orchestrator/backend-coding/system-design/frontend-design/project-structure/consistency/self-review/tool-selection/research-ethics 按需。 → paper-polishing → figure-planning(已补E1) → figure-drawing → citation → typesetting → venue-matching(已补P2) → review-rebuttal → ip-application → slides(已补E2) → competition；常驻技能 file-reading/memory-pm/orchestrator/backend-coding/system-design/frontend-design/project-structure/consistency/self-review/tool-selection/research-ethics 按需。
