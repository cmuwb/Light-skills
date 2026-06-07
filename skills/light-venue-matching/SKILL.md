---
name: light-venue-matching
description: 投稿定位与期刊/会议匹配。当用户问投哪个期刊/会议、要评估录用可能性/录用概率、做投稿规划时使用。根据论文质量、方向、创新程度、实验完整性、语言水平、作者背景和预算，推荐中文/英文期刊、SCI/SSCI/EI/CCF/核心、国际/国内会议。分析投稿难度、方向匹配度、审稿周期、版面费、以可核查信号做录用可能性定性分级(高/中/低,不编百分比)、是否适合本科生/弱导师资源、预警风险，给出冲刺/稳妥/保底分层选择。
---

# 投稿定位与 venue 匹配

## 评估输入（先盘点实力）
论文质量(创新/实验完整性/理论深度)、研究方向、语言水平、作者背景(本科/硕博、是否有强导师)、时间需求(deadline/毕业要求)、预算(能否付 APC)、目标(毕业/评奖/找工作/纯发表)。

## 匹配流程
1. 用 db01 期刊会议库按方向(subject_area)筛候选；不足时按方向程序化扩候选：OpenAlex Sources `GET https://api.openalex.org/sources?filter=topics.id:<方向>,is_oa:<bool>&sort=cited_by_count:desc&per_page=50&mailto=<email>`（游标 `cursor=*` 翻页，可按 `summary_stats.2yr_mean_citedness`/`apc_usd`/`is_in_doaj` 过滤）；计算机方向直接对 CCF 目录按"领域+目标档(A/B/C)"取候选。
2. 按论文实力对齐 venue 级别——不只推"高大上"。给学生用"档位"(CCF A/B/C、中科院分区、北大核心/CSSCI)而非裸 IF。
3. 对每个候选填**统一对比字段**（抓取来源见括号）：
   - 影响指标：IF + JCR 分区(JCR/LetPub)、CiteScore + 分位(Scopus)、SJR/Eigenfactor 声望(Scimago/IEEE)、中科院分区大类/小类(分区表/LetPub)。
   - 档位：CCF A/B/C、北大核心/CSSCI/CSCD 命中情况。
   - 周期：首次决定时长 + 投稿到发表周数(JournalFinder/IEEE Recommender/LetPub)。
   - 费用与 OA：APC、是否 OA、是否 DOAJ 收录(DOAJ API `GET /api/v3/search/journals/issn:<ISSN>`)。
   - 录用可能性与背景：**官方公开接收率**(仅在该刊/会官网或正式报告披露时填具体数字并附链接，否则填"待核查—无官方公开数据")、国人发文占比(LetPub，标注为社区经验估计)、自引率、是否适合作者背景、模板与引用格式(reference_style)。**不抓取、不填写 LetPub 的"录用比例"作为概率数字**（其自承为社区投稿经验估计，非官方统计），只用下方 rubric 做定性分级。
   - 收录核查：是否被 WoS 收录及索引(SCIE/SSCI/AHCI/ESCI，查 Master Journal List)、是否被 Scopus 收录。
   **三套分区(JCR/SJR/中科院)口径不同，每项必须标来源+年份，不可混用。**
4. **预警筛查（白名单+黑名单双向）**：
   - 白名单正面信号：被 DOAJ 收录(尤其有 DOAJ Seal)、被 WoS/Scopus 正规索引。
   - 黑名单/掠夺特征：命中《中科院国际期刊预警名单》(高/中风险)，或异常自引、超快审稿、年发文激增、国人发文占比畸高、高额 APC、虚假指标。命中即标红劝退（联动 a10）。

## 分层推荐（必给三档）
- **冲刺**：够一够可能中，回报高。
- **稳妥**：实力匹配，大概率中。
- **保底**：确保能发/能毕业。
每档给 1–3 个，附理由、**录用可能性定性分级(高/中/低，见下方 rubric，不编百分比)**、周期、费用、风险。

## 录用可能性评估 rubric（定性分级，禁编概率数字）
**铁律**：除非该刊/会官网或正式报告公开了接收率(acceptance rate)且能附链接，否则**绝不给出精确录用概率/百分比**。LetPub 等聚合站的"录用比例"是社区投稿经验估计、非官方统计，**不得当作概率数字引用**。最终只输出"高/中/低 + 逐条理由"的定性分级。

### 五个可核查信号（逐项打分，每项 高/中/低，并标来源）
1. **作者相对实力**：作者近 5 年 h-index / 代表作被引（OpenAlex Authors `GET https://api.openalex.org/authors?search=<姓名>&mailto=<email>`，取 `summary_stats.h_index`）对比该 venue 的 `summary_stats.h_index`（db01 已存或 OpenAlex Sources 查）。作者影响力接近/超过该刊典型作者→高；明显低于→低。注：h-index 同名需用机构/ORCID 排歧，标"待核查"不强行认定。
2. **方向匹配度**：论文主题与该 venue 的 `subject_area`(db01) 及近年 `representative_papers`(db01 字段) 的主题重合度。核心主题命中→高；擦边/跨界→中；明显偏离该刊 scope→低。
3. **方法/数据规模匹配**：论文用的方法、数据集规模、实验体量是否达到该 venue representative_papers 体现的门槛（如顶会常要大规模实验+SOTA 对比；领域刊看是否有该刊偏好的方法范式）。达标→高；部分达标→中；明显不足→低。
4. **官方接收率档位**：仅当有官方公开接收率时按数值定档（如 <15% 记为竞争极高、15–30% 高、>30% 中）；**无官方数据则该项填"待核查—无官方接收率"，不参与编数**，并在结论里说明该项缺失。
5. **创新性自评**：让作者/评估者按"增量改进 / 显著改进 / 新问题或新范式"三档自评，对照该 venue 档位（顶会/顶刊偏好后两档）。这是主观项，须显式标注"作者自评，非客观指标"。

### 汇总规则
- 五项多数为"高"且无致命短板（方向/方法不达标算致命）→ 总评 **高（稳妥/保底候选）**。
- 信号互有高低、存在 1 项致命短板 → 总评 **中（冲刺候选，说明短板）**。
- 方向或方法明显不达标，或作者实力远低于该刊 → 总评 **低（不建议或仅作保底外的备选）**。
- 输出格式示例见下"产出"第 1 项；每条分级后必须跟"因为…(引哪个信号+来源)"，不得只给结论。

## 工具/数据视角（各司其职，别混口径）
- **程序化拉候选/元数据**：OpenAlex Sources（免费 REST，`api.openalex.org/sources`，按 ISSN/topic/OA/APC/h-index 过滤，cursor 翻页，加 `mailto` 进礼貌池）。
- **影响指标**：JCR(JIF，2 年窗，现 1 位小数，2024 起 SCIE+SSCI+ESCI 统一排名，需订阅) ｜ Scopus CiteScore(4 年窗、分母含会议/综述，免费) ｜ Scimago SJR(类 PageRank 声望加权，Scopus 数据，门户可下 Excel) ｜ Eigenfactor/Article Influence(IEEE Recommender 内置)。
- **收录核查**：WoS Master Journal List(免费查是否收录 + SCIE/SSCI/AHCI/ESCI) ｜ Scopus Source List。
- **国内档位**：CCF A/B/C 目录(计算机十大领域) ｜ 中科院分区(大类/小类，1 区约前 5%，附预警名单) ｜ 北大核心(中文核心，约 4 年一版) ｜ CSSCI(南大核心，社科) ｜ CSCD(理工)。
- **稿件-期刊匹配工具**(只发现候选，有出版商偏向)：Elsevier JournalFinder、Springer Journal Suggester、IEEE Publication Recommender——输入题目/摘要，返回同社旗下刊 + 周期/接受率/APC/OA。
- **一站查中国友好画像**：LetPub(IF/JCR 分区/中科院分区/审稿周期/录用率/国人占比/APC/预警 一处看，但关键值回官方二次核实)。
- **OA 合规**：DOAJ(免费 API `doaj.org/api/v3/search/journals/{query}`，收录=正面信号，有 Seal 更佳)。

元数据以 db01 为准并标注 last_checked_date；具体端点/参数/坑见 references.md。

## 产出
1. 候选 venue 对比表（含上述字段 + 推荐档位 + **录用可能性定性分级**）。表骨架见 `templates/venue_compare_table.md`，填表即可保证字段不漏列、口径统一。分级列写法举例：
   `中｜方向匹配=高(主题命中CVPR scope,db01 subject_area=计算机视觉);作者实力=中(作者h-index=18 vs 该会代表作者多>40,OpenAlex Authors);方法规模=中(单数据集,顶会偏好多数据集SOTA);官方接收率=待核查(CVPR官网未稳定公开逐年录用率);创新性=作者自评"显著改进"(主观)`
   —— 注意：**全程无百分比**，"待核查"如实保留。
2. 投稿策略建议（先投哪、被拒后转投顺序）。
3. 风险提示（预警/周期长/费用高/匿名要求）。

## 衔接
选定后 → m12 套对应模板、m10 调引用格式；投稿记录与决策入 db09；被拒后转投时回本技能重排。所有期刊数据投前重新核查(CONVENTIONS §1)。

> 工具真实端点/参数/已知坑详见同目录 references.md。
