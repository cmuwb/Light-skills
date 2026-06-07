---
name: light-citation
description: 论文引用规划、审查与多格式生成。当用户需要处理参考文献、引用、bibtex 时使用。审查引用的关联度、真实性、权威性、时效性、数量、中外占比，是否引用了经典/最新/代表性/对比工作。避免虚假引用、过度引用、无关引用、堆砌、遗漏关键文献、低质量来源、引用与正文不匹配。生成 BibTeX/EndNote/GB-T 7714/APA/IEEE 等格式并按目标 venue 调整。
---

# 论文引用管理

## 引用规划
1. 列出论文每个需要引用的 claim/方法/数据集/对比工作。
2. 为每处匹配最合适的来源：经典奠基文献 + 最新进展 + 直接对比方法 + 必要背景。
3. 检查覆盖：领域经典是否引？最新(近 1–2 年)是否引？SOTA baseline 是否引？

## 引用审查（逐条核查）
- **真实性**：DOI/标题/作者/年份可核查，杜绝臆造（CONVENTIONS §4）。核验路径：
  - 优先 Crossref `https://api.crossref.org/works?query.bibliographic=<标题+作者+年>&mailto=<邮箱>`（礼貌池更稳），比对返回的 `title/author/issued/DOI`。
  - 单 DOI 直查 `https://api.crossref.org/works/{doi}`；查不到再用 OpenAlex `filter=title.search:...` 或 Semantic Scholar `/paper/search` 兜底。
  - 标准：每条引用都要能定位到真实记录；对不上即标"疑似臆造/需核查"，不放过。
- **关联度**：引用与正文论点是否匹配，不张冠李戴。可借 Anthropic Citations 思路——要求每条引用能指回被支撑的具体句子。
- **权威性**：来源层级，慎引低质量/掠夺性来源。用 Unpaywall `oa_status`、OpenAlex `primary_location.source` 看刊物属性；预印本注明未经同行评审。
- **时效性**：是否遗漏近期关键工作。用 Crossref `filter=from-pub-date:` 或 OpenAlex `filter=publication_year:>` 扫近 1–2 年高被引。
- **被引关系核验**：声称"A 引用了 B"时，用 OpenCitations `/references/{A}` 或 Semantic Scholar `/paper/{A}/references` 实证，不靠印象。
- **数量**：是否过少(支撑不足)或过多(堆砌)。用 `is-referenced-by-count`/`cited_by_count` 辅助判断代表性。
- **中外占比**：按 venue 合理（中文期刊需足量中文文献，国际会议以英文为主）。
- **自引**：比例是否过高。

## 格式生成
- **最快路径——DOI 内容协商**：对 `https://doi.org/{doi}` 带 `Accept` 头直接取格式，免转换：
  - `Accept: application/x-bibtex` → BibTeX；`application/vnd.citationstyles.csl+json` → CSL JSON；`application/x-research-info-systems` → RIS。
  - `Accept: text/x-bibliography; style=apa; locale=en-US` → 直接返回已排版书目（style 取 CSL 名：apa/ieee/chicago-author-date…）。curl 记得 `-L` 跟随重定向。
- **多格式中枢**：以 CSL JSON 存储，配 .csl 样式经 Pandoc/Zotero 渲染成任意期刊格式。`type` 字段决定模板（article-journal/paper-conference/book…），选错套错模板。
- **中文国标**：GB/T 7714-2015，安装社区 .csl（区分 `-numeric` 顺序编码 / `-author-date`），核查文献类型标识码 `[J]/[C]/[M]/[D]/[EB/OL]` 与作者 >3 取前 3 加"等"。
- **键名规范**：Better BibTeX 公式如 `auth.lower+year+shorttitle(3,3)`（zhang2024deep），冲突自动加 a/b/c；正文确定后 **pin citekey** 防元数据变动导致 \cite 失效。
- **LaTeX 后端**：先看目标模板要求——顶会模板（IEEEtran/ACM/LNCS）常锁定传统 `bibtex`+指定 .bst；现代 `biblatex+biber` 原生 UTF-8、排序更强但字段名不同（`journaltitle`/`date`）。不擅自换后端。

## 工具视角
- **元数据/真实性核验**：Crossref（DOI 权威源，礼貌池带 `mailto`，深翻页用 `cursor=*`）、OpenAlex（免 key，`filter`/`group_by` 强，摘要是倒排索引需重建）、Semantic Scholar（强在引用关系与影响力，申请免费 `x-api-key` 避 429）。
- **开放获取**：Unpaywall `/{doi}?email=`，看 `is_oa`/`oa_status`/`best_oa_location.url_for_pdf`，注意 `version` 是否正式版。
- **引用关系实证**：OpenCitations `/citations/{id}`、`/references/{id}`（只覆盖开放 DOI-DOI，不当完整计数）。
- **库管理**：Zotero（Web API v3，`format=bibtex/csljson`，`include=bib&style=`）+ pyzotero（`zot.items(content='bib', style='ieee')`、`everything()` 翻页）；纯 LaTeX 流可用 JabRef（DOI/arXiv fetcher + integrity check 体检 .bib）。
- **协作互导**：与 EndNote/Mendeley 交换统一走 RIS 或 .bib；勿假设 Mendeley 历史 API 仍可用，迁移前先验证。
（各工具真实端点/参数/坑见 references.md）

## 端到端 workflow（可运行脚本串联）
> 全部脚本免外部依赖（标准库 urllib），自带 `__main__` 自测，端点已 curl 实测（HTTP 码见 references.md）。

1. **搜索/抽取** — Crossref `query.bibliographic` 或 OpenAlex `filter=title.search:` 找候选，拿到 DOI 清单；正文 `.bib`/`.tex` 里的 DOI 也可直接抽出。
2. **去重** — 合并同一工作的多版本/多 DOI（预印本 vs 正式版优先正式版）。
3. **真实性+一致性核验** — 一条命令产机读报告：
   ```bash
   # 在本技能目录（skills/light-citation/）下运行
   python scripts/verify_refs.py --file dois.txt --self-author 张 --out report.json
   ```
   读 `report.json`：`summary.high_severity_errors` 必须为 0；查不到的 DOI 标 `severity:high`（疑似臆造）；
   另给中外占比 `cn_ratio`、自引率 `self_citation_rate`、缺近 2 年标志 `missing_recent_2y`、各源 HTTP 码。
4. **GB/T 7714 渲染 / 多格式生成** — 逐 DOI 出 BibTeX + CSL JSON + 国标排版文本：
   ```bash
   python scripts/doi_to_any.py 10.1038/s41597-023-02555-8 --format all
   ```
   `--format gbt7714` 直接给顺序编码制中文书目；CSL JSON 可再喂 Pandoc 配 .csl 渲染任意期刊样式。
5. **投稿前体检** — 逐项过 `assets/citation_checklist.md`（真实性/关联度/中外·SOTA·经典覆盖/数量健康度/格式），
   并用其中"被引阈值分档表"按文献年龄判代表性。
6. **产出报告** — 汇总 `report.json` + checklist 结论，给补引/删引/换源/改格式的修改清单。

## 脚本与资产
- `scripts/doi_to_any.py` — DOI 内容协商 → BibTeX / CSL JSON / GB-T 7714，含真 DOI 自测。
- `scripts/verify_refs.py` — 批量 DOI 经 Crossref+OpenAlex 双源核验，产机读 JSON 报告，含真/假 DOI 自测。
- `assets/citation_checklist.md` — 投稿前体检清单 + 被引阈值分档表 + 中外/SOTA/经典覆盖自检表。

## 产出
1. 引用审查报告（问题清单 + 修改建议：补引/删引/换源/改格式）。
2. 规范化 .bib / 对应格式文件。
3. 正文引用位置与编号核对。

## 衔接
与 m07/m08/m12 协同；缺关键文献回 m01 补检；格式随 m13 选定 venue 调整(具体引用样式查 db01 的 `reference_style` 字段)；引用库登记 db09。虚假/掠夺性来源风险上报 a10。

---
工具真实端点、参数、限速与已知坑详见同目录 `references.md`。
