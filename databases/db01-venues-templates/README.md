# db01 — 期刊会议与模板资源库

覆盖中英文期刊、会议与投稿模板的知识库，供 m13(投稿匹配)、m12(排版)、m10(引用格式)、m01(调研) 使用。

## 字段 schema（统一）
`source, venue_name, venue_type, publisher, subject_area, level, indexing, impact_factor, jcr_quartile, cas_quartile, ccf_level, review_cycle, apc_fee, template_url, submission_url, reference_style, representative_papers, risk_note, last_checked_date`

- `venue_type`: journal | conference
- `level`: 中文(北大核心/CSCD/CSSCI/科技核心) | SCI | EI | CCF-A/B/C | 其他
- `indexing`: SCI/SSCI/EI/Scopus/CCF/北大核心 等
- `reference_style`: IEEE | ACM | APA | GB/T 7714 | Springer LNCS | Elsevier 等

## 数据来源（建库 & 更新去哪找）
OpenAlex Venues、Crossref、Semantic Scholar、arXiv、DOAJ、Web of Science/JCR、Scopus Sources、Scimago(SJR)、CCF 推荐目录、北大核心目录、CSCD/CSSCI 目录、各出版社官网(IEEE/ACM/Springer/Elsevier/Wiley/Nature/Science)、各会议官网、Overleaf 模板库、各社官方 LaTeX 模板页。

## 合规
受版权论文/模板**只存元数据、链接、摘要、笔记、引用关系**，不收集违规全文。优先公开资源、官方模板、arXiv、预印本、作者主页公开版。

## 更新方式
- 每月：更新元数据。
- 每季度：更新分区、版面费、模板链接、预警信息。
- 每次选投稿目标前：对候选 venue 重新核查一次并更新 `last_checked_date`。

## 维护说明
- 新增条目追加到 [venues.csv](venues.csv)（表头即上述字段）。
- 预警/掠夺性期刊在 `risk_note` 明确标注，并联动 m13/a10。
- 模板缺失时在 `template_url` 标注 "需补"。

种子数据见 [venues.csv](venues.csv)。
