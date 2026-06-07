---
name: light-paper-polishing
description: 对论文分模块润色——语言润色、逻辑重构、结构优化、创新点强化、论证补强、摘要精炼、引言增强、实验分析深化、结论提升。当用户需要改论文、觉得某段不通顺/逻辑弱/创新点不突出时使用。从审稿人角度找逻辑薄弱、论证不足、表达不专业、易被质疑、缺引用、需重组之处，给出具体修改方案与修改后文本。
---

# 论文润色（审稿人视角）

## 不只是改语法
分两层：**表层**（语言、术语、句式、可读性）+ **深层**（逻辑、论证、结构、创新点呈现）。深层优先——审稿人拒稿很少因为语法。

## 深层维度：审稿人五问（每个论断逐项过）
按审稿打分维度组织（综合 Elsevier reviewer 指南与会议式评审）：
1. **soundness 方法成立**：每个论断有证据(实验/引用/推导)吗？标出"裸论断"。因果是否成立、有没有"未经论证的跳跃"。
2. **novelty 创新呈现**：贡献是否在摘要/引言/结论三处措辞一致且突出？贡献句用动词开头、可度量。读者能否一眼抓到差异点。
3. **clarity 可读性**：段落间有断点吗？每段是否有主题句、只服务一个论点（"这段要让审稿人相信什么"）。
4. **reproducibility 可复现**：方法/设置/超参/数据是否足以复现？实验只报数字没解释就补"为什么"。
5. **related-work 引用充分**：对比与定位是否到位？缺引用转 m10。
> 引言按"四段式"对位：背景痛点 → 现有方法不足(动机) → 我们的洞察/做法 → 贡献列表。

## 表层维度：语言层四查（借 Grammarly 四分法，按学术稿调权重）
1. **correctness**：语法、拼写、标点、时态语态统一。
2. **clarity**：删冗余、拆长从句、消除指代不清（"don't make reviewer think"）。
3. **delivery/tone**：保持正式克制；去口语、去夸大（novel/significantly/very 慎用）。
4. **consistency**：术语前后一致(a07)、缩写首现定义、数字与单位格式统一。
> engagement/华丽用词在学术稿里弱化——别为多样性牺牲精确。
> **首选可直跑（免费匿名）**：LanguageTool 公共云端点 `POST https://api.languagetool.org/v2/check`，参数 `language=en-US`（或 `auto`）、`level=picky`（开严格风格规则）、`motherTongue=zh-CN`；匿名实测 HTTP 200，返回 `matches[]` 带 `message`/`replacements`/`offset`，逐条核对。隐私/批量场景改自托管。
> 一行可跑示例：
> ```bash
> curl -s -X POST "https://api.languagetool.org/v2/check" \
>   -d "language=en-US" -d "level=picky" \
>   --data-urlencode "text=This sentence have a error." | python -m json.tool
> ```
> **DeepL 改写需付费 key，不能匿名跑**：`/v2/write/rewrite` 两个 host 实测均 404，`/v2/translate` 实测 403（需 `Authorization: DeepL-Auth-Key`）；故 DeepL 仅作"有 key 时整句改写参考"，`writing_style=academic` 偏整句重述、易动术语与作者声音，必须人工复核（端点存活情况见 references.md）。学术措辞向 Writefull"已发表语料惯用表达"思路看齐，而非通用语法。

## 工作方式：四步流水线（distill → critique → polish → audit）
1. **distill**：先抓核心贡献，确认每段服务于哪个论点（结构/故事线层，对标 strategist 视角）。
2. **critique**：审稿人视角列弱点——逐项过"审稿人五问"，标出最易被质疑/追问处，预先补强或加 limitation。
3. **polish**：改语言——语言层四查，逐模块处理，用户可指定章节。
4. **audit**：终检一致性/术语/格式/缩写/引用（合规门槛，对标预投稿检查）。

每处修改给出：**问题 → 原因 → 修改方案 → 修改后文本**，必要时 before/after 对照。重大重构先说思路再改。保留作者声音，不过度改写（DeepL 式整句重述会冲淡声音，慎用）。摘要/引言/结论按 db02 高水平套路重写。

## 示范：润色长这样（每处都要走完四栏）
> 输出格式固定为「原句 → 问题诊断 → 修改后 → 为什么更好」。下面三例分别覆盖深层(soundness)、表层(clarity)、贡献呈现(novelty)三类。

**例 1 · 深层 / 裸论断（soundness）**
- **原句**：Our method significantly outperforms existing approaches and is much more efficient.
- **问题诊断**：① "significantly/much more" 是无证据的夸大裸论断，审稿人立刻追问"多少、比谁、显著性检验呢"；② "existing approaches" 含糊，没指明 baseline；③ efficient 维度未定义（时间？显存？）。
- **修改后**：On ImageNet, our method improves top-1 accuracy by 2.3 points over ResNet-50 (76.1% vs. 73.8%) while reducing inference latency by 18% (12.4 ms vs. 15.1 ms per image, single A100).
- **为什么更好**：把形容词换成可度量数字+具体 baseline+硬件条件，论断从"可被质疑"变成"可被复现"；删掉 significantly，让数据自己说话（呼应表层 delivery：去夸大）。

**例 2 · 表层 / 长从句+指代不清（clarity）**
- **原句**：The model, which is trained on the dataset that we collected and which contains various types of noise that may affect performance, achieves good results.
- **问题诊断**：① 三层嵌套从句(which…that…which…that)逼审稿人回读，违反"don't make reviewer think"；② "various types of noise" 指代空泛；③ "good results" 是无信息词。
- **修改后**：We train the model on our collected dataset, which contains label noise and sensor artifacts. Despite this noise, the model reaches 89.2% F1.
- **为什么更好**：一长句拆成两短句、each 一义；把 "various noise" 落实为两类具体噪声；"good results"→具体指标。可读性、correctness、信息密度同时提升。

**例 3 · 贡献呈现（novelty，引言/摘要三处一致）**
- **原句**：In this paper, we study the problem of domain adaptation and propose some techniques to improve it.
- **问题诊断**：① "study / some techniques / improve" 全是软动词，读者抓不到差异点；② 贡献不可度量，无法与 abstract/conclusion 对齐；③ 没点出"洞察"。
- **修改后**：We make three contributions: (1) we identify feature-norm collapse as the dominant failure mode in test-time domain adaptation; (2) we propose NormGuard, a regularizer that constrains feature norms during adaptation; (3) NormGuard raises mean accuracy by 3.1 points across five benchmarks.
- **为什么更好**：动词开头(identify/propose/raise)、贡献可数可度量、点明洞察(feature-norm collapse)；这三句可原样复用到 abstract 与 conclusion，保证三处措辞一致（彭思达"贡献三处一致"）。

## 可直跑脚本（scripts/）
三个产物把上面的方法落成可运行工具，输出**同构结构化发现**（schema 见 `references/findings_schema.md`）：
- **`scripts/polish.py`**：封装 LanguageTool 匿名云端点 `POST https://api.languagetool.org/v2/check`（`level=picky`、`motherTongue=zh-CN`）。自动按段落/句子**分块**（单块 <18000 字符，避开匿名 ~20k 上限），把每条 match 的 offset 映射回**原文绝对 line/col**。端点不可达或非 200 时**自动降级**为本地正则规则（`mode=local-fallback`），`_meta.http_codes` 记录运行时真实 HTTP 码，绝不伪造云端结果。
  - 实测（2026-06-06 本环境）：自带样例 → `mode=languagetool http=[200]`，返回 `EN_A_VS_AN`/`PLURAL_VERB_AFTER_THIS` 等真实规则。
  - 跑法：`python scripts/polish.py --file paper.txt --json` 或 `echo "..." | python scripts/polish.py`。
- **`scripts/mechanical_check.py`**（**无需 API**）：扫 ① overclaim 黑名单（significant/seminal/novel/outperforms…）② AI 腔/填充语（in conclusion / it is worth noting / delve into / furthermore…）③ hedge 堆叠 ④ 段落被动句占比超阈值 ⑤ 标点卫生（em-dash 间距、全角标点混入英文、多空格、标点前空格）。输出 `{line,col,category,issue,suggestion,context}`。纯 stdlib，任何环境可跑。
  - 跑法：`python scripts/mechanical_check.py --file paper.txt --json`。
- 两脚本无输入时跑**内置自检样例**，保证 `python <script>` 永远能跑通。LanguageTool 管表层语法，mechanical_check 管 LanguageTool 漏掉的"学术腔/裸论断"，二者互补。

## 完整 before/after 范例（一段引言走完四步流水线）
> 演示从原始段落 → 跑脚本 → 逐条修改 → 终稿。这是技能输出的标准样子。

**原始段落（before）**
> In this paper, we study the problem of image segmentation. It is worth noting that segmentation is very important. Our novel method significantly outperforms existing approaches. The model was trained on a dataset and was evaluated on benchmarks and was compared with baselines. This may possibly suggest that our approach is state-of-the-art.

**step distill**：核心贡献 = 一个分割方法 + 它比 baseline 强。但全段没有一个可度量数字，贡献句被夸大词淹没。

**step critique（跑 `mechanical_check.py`）**：命中 `ai_tone: It is worth noting`、`overclaim: very/novel/significantly/outperforms/state-of-the-art`、`passive_overuse`（"was trained…was evaluated…was compared" 三连被动）、`hedge_stacking: may possibly suggest`。

**step polish（跑 `polish.py`，LanguageTool HTTP 200）**：补语法/冠词/标点；连同上面的裸论断逐条改。

四栏修改记录（节选）：
- **原句**：It is worth noting that segmentation is very important.
  - **问题诊断**：`ai_tone` 填充开头 + `overclaim: very`，零信息。
  - **修改后**：（删除整句，把"为什么重要"并入下一句的痛点。）
  - **为什么更好**：审稿人把 "it is worth noting" 读作 AI 腔；重要性应由具体痛点而非形容词承担。
- **原句**：Our novel method significantly outperforms existing approaches.
  - **问题诊断**：`overclaim: novel/significantly/outperforms` + baseline 含糊 + 无数字（裸论断）。
  - **修改后**：On Cityscapes, our method raises mIoU by 2.1 points over DeepLabv3+ (80.4 vs. 78.3).
  - **为什么更好**：夸大词换成可度量增益 + 具体 baseline + 数据集，论断从"可质疑"变"可复现"。
- **原句**：The model was trained on a dataset and was evaluated on benchmarks and was compared with baselines.
  - **问题诊断**：`passive_overuse` 三连被动 + "a dataset/benchmarks" 含糊。
  - **修改后**：We train the model on Cityscapes and evaluate it on Cityscapes and ADE20K against four baselines.
  - **为什么更好**：主动语态 + 具名数据集与 baseline 数量，信息密度上升、可复现。
- **原句**：This may possibly suggest that our approach is state-of-the-art.
  - **问题诊断**：`hedge_stacking: may possibly suggest` 同时又 `overclaim: state-of-the-art`，自相矛盾。
  - **修改后**：These gains hold across two datasets, indicating the approach generalizes beyond a single benchmark.
  - **为什么更好**：去掉三连 hedge 与空泛 SOTA，给出有边界的、可被验证的结论。

**终稿（after）**
> We study image segmentation under domain shift, where models trained on one city degrade on another. We propose a method that aligns feature norms across domains. On Cityscapes, it raises mIoU by 2.1 points over DeepLabv3+ (80.4 vs. 78.3). We train on Cityscapes and evaluate on Cityscapes and ADE20K against four baselines. These gains hold across two datasets, indicating the approach generalizes beyond a single benchmark.

> after 段：0 个 overclaim / ai_tone / hedge 命中，被动比降到阈值下，贡献句可度量、可原样复用到 abstract 与 conclusion（三处一致）。

## 衔接
与 m07 交替循环；改完跑 m14 模拟审稿验证；术语对齐 db09；引用问题转 m10。每轮记录版本到 db09。

> 工具与方法的逐条核查笔记见 `references.md`（含 LanguageTool/DeepL 真实端点参数、Writefull/Paperpal/Grammarly 能力边界、各写作 skill 工作流）；结构化发现字段契约见 `references/findings_schema.md`；可跑脚本在 `scripts/polish.py`、`scripts/mechanical_check.py`。
