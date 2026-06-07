# 量化诚信门（Integrity Gate）

把"诚实第一"从口号变成可执行配额。两道门：**初稿门**（写作中持续抽样）、**终稿门**（提交前全量）。
对接 self_review_checklist.md 的 M2/M3，对接 anti-leakage 的 `[MATERIAL GAP]` / `[RESULT GAP]` 标记。

---

## 1. Claim 核查抽样配额

把正文中的**事实性 claim**（任何"是/有/达到/优于/导致"的可证伪陈述）登记到 claim 台账。

| 阶段 | 抽样比例 | 下限 | 范围 |
|---|---|---|---|
| 初稿（写作中） | **≥30%** | 至少 10 条（少于 10 条则全查） | 全文事实性 claim 随机抽样，优先抽数字类与引用类 |
| 终稿（提交前） | **100%** | 全部 | 每条 claim + 每条引用都过一遍 |

抽样不是放过其余 70%——是分摊到各模块滚动抽，终稿必须收口到 100%。
高危类**不抽样、永远全查**：所有带数字的结果句、所有他人方法的性能数字、所有"first/SOTA/outperform"措辞。

---

## 2. 每条 claim 的核查动作清单（逐条勾）

对抽中的每条 claim：

- [ ] **分类**：是 ① 本文实验结果 / ② 引用的他人结论 / ③ 公认背景 / ④ 推断？
- [ ] **①实验结果** → 指向实际运行产物（日志/表格/脚本）？有 std/CI？单次结果不得写成定论。否则改 `[RESULT GAP]`。
- [ ] **②引用结论** → 见下"引用核查"五步。
- [ ] **③背景** → 是否真"公认"？存疑则补 1 条可核引用，否则降级措辞。
- [ ] **④推断** → 是否被标为推断（"we hypothesize/suggest"）而非事实？硬写成事实即触发改写。
- [ ] **溯源状态登记**：已验证 / 待核 / GAP（写进 Material Passport）。

---

## 3. 引用核查动作清单（对接 M2 幻觉引用）

对每条参考文献（终稿 100%）：

- [ ] **存在性**：curl 实测 DOI 内容协商或 Crossref/OpenAlex 命中，记 HTTP 码。
      - `curl -sI -H "Accept: application/vnd.citationstyles.csl+json" https://doi.org/<DOI>`（期望 200/302）
      - `curl -s "https://api.crossref.org/works/<DOI>?mailto=you@x.org"`（核题名/作者/年份）
      - 无 DOI 的 arXiv：`curl -sI https://arxiv.org/abs/<ID>`
- [ ] **字段一致**：题名、第一作者、年份、venue 与正文引用一致（防张冠李戴）。
- [ ] **支撑关系**：点开看，该文是否**真的支撑**你引用它的那句话？key/DOI 对≠论点被支撑。
- [ ] **不可达/对不上** → 删除或替换，绝不保留"大概是这篇"。
- [ ] **登记**：DOI + HTTP 码 + 核查日期记入 references 台账（符合 CONVENTIONS 第 4 条）。

> 端点真实性已在 references.md 调研记录；具体 DOI 必须逐条实测，不得凭印象。
> **端点实测（2026-06，DOI 10.1109/CVPR.2016.90 为例）**：DOI 内容协商 HTTP 302（重定向至出版商，正常）；Crossref `api.crossref.org/works/<DOI>` HTTP 200；arXiv `arxiv.org/abs/<ID>` HTTP 200；OpenAlex `api.openalex.org/works/https://doi.org/<DOI>` HTTP 200。换 DOI 时重测。

---

## 4. 过门判据

- **初稿门**：抽样覆盖率达标 + 抽中 claim 无 M2/M3 未处理项 + 所有未核内容都已标 GAP。
- **终稿门**：100% claim 已分类核查 + 100% 引用存在性与字段一致 + 0 个遗留 `[MATERIAL GAP]`/`[RESULT GAP]` + 必备声明齐全（见 mandatory_inclusions.md）。
- 任一不达标 → 不得标记"可提交"。机检用 `scripts/draft_lint.py`（查残留 GAP 与缺失声明），人判覆盖机检。