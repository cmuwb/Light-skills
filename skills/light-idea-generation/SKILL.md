---
name: light-idea-generation
description: 根据项目实际情况提出有潜力、有差异化、有亮点的研究 idea。当用户需要创新点、研究思路、提方案，或问"这个方向/数据能做什么"时使用。结合已有基础、数据条件、技术能力、时间周期、发表/竞赛/课题目标，说明为什么值得做、创新点、相对现有方法的优势、能解决的具体问题、适合的成果形式与投稿层次。
---

# 创新与 idea 生成

## 前置条件
开工前确认两件事：(1) m01 的文献 gap 是否清楚；(2) m02 的数据是否足以支撑。若数据不足，先回 m02，不做空想 idea。

## 输入
项目背景、已有基础、数据条件、技术栈与算力、时间周期、目标(顶刊/普刊/竞赛/课题/工程)、约束。

先判断输入属于哪一级（借 AI-Researcher 的两级抽象）：
- **Level 1 已有明确方向**：用户给了具体 idea → 重点做细化、差异化与可行性核验。
- **Level 2 只有方向/数据/参考文献**（如"这个方向能做什么"）→ 从文献 + 数据反推 idea。
Level 2 立项时，每个候选先填一张**立项卡**（借 AI Scientist v2 ideation 四件套）：Title / Keywords / TL;DR / Abstract，强制把模糊想法收敛成可讨论的单元。

## 生成策略（多角度发散，再收敛）

### 发散：独立从多个角度各生成候选，避免单一思路
1. **gap-driven**：直击文献空白。
2. **method-transfer**：把 A 领域成熟方法迁到 B 领域。
3. **data-driven**：从数据独有特征反推机会（独家数据/新模态/新标注）。查 db04 数据集卡的 `data_type`/已知偏倚/许可，找别人没用过的数据角度。
4. **problem-reframe**：重新定义问题或评价方式。
5. **combination**：方法组合，但必须说明 1+1>2 的机理，不是堆叠。
6. **theory-gap**：补理论解释/可解释性/泛化保证。
7. **efficiency**：更快/更省/更小，工程价值。

不够发散时，补用 7 个结构化激发技法（源自 Scientific Brainstorming）：跨域类比、假设反转（"反过来会怎样/资源无限会怎样"）、尺度切换（分子↔种群、毫秒↔千年）、约束增删、跨学科融合、技术外推（新技术来了能做什么）。method-transfer/combination 角度可仿 ResearchAgent：先抽取本项目领域核心实体，再找与之高共现的邻域概念作为迁移/重组来源；MAGenIdeas 证明这种跨域知识重组 + 迭代检索能把唯一新颖 idea 数提到约 3.4 倍。

### 收敛：发散后过滤排序
- 先用 db03 方法成熟度过滤掉"已过时/已被做烂"的方向。
- 候选多时用**两两 PK / 瑞士轮**排序选 Top-N（MAGenIdeas 做法），比孤立打分更能拉开差距。
- 用"影响 × 工作量"二维快评做收敛漏斗，选 Top 3（diverge-converge 做法）。

## 新颖性核验（别靠记忆，去查）
提"创新点/相对哪些工作"前，实际检索对标工作，避免"自以为新"和引用幻觉：
- **OpenAlex**（无 S2 key 时首选，免费）：`https://api.openalex.org/works?search=<关键词>&select=id,display_name,cited_by_count,publication_year&mailto=you@example.com`。
  - 看一个方向被哪些子主题占满、哪里稀疏：`/works?filter=title.search:<方向>,from_publication_date:2023-01-01&group_by=primary_topic.id`。
  - 趋势：`group_by=publication_year`。取代表作按 `cited_by_count` 排序。分页超 1 万条用游标 `&cursor=*` + `meta.next_cursor`。注意 2026 起需免费 API key、按 `cost_usd` 计费（约 $1/天免费额度）。
- **Semantic Scholar**：`GET https://api.semanticscholar.org/graph/v1/paper/search`，参数 `query/limit/fields`，header `X-API-KEY`（可选），每次查后 sleep ~1s 防限流（AI Scientist 做法）。
检索结论决定"创新点"措辞：若已有高度相似工作，回到发散重选角度，别硬说新。

## 每个 idea 必须说清（缺一不可）
- **一句话 idea**。
- **为什么值得做**：动机 + 现实/学术意义。
- **创新点**：相对哪些**具体**工作（附检索到的真实文献），差异在哪。
- **凭什么更强**：可能优于现有方法的机理假设；并列出**竞争性解释**而非只押一个（hypothesis-generation 做法）。
- **解决什么具体问题**：可量化、可证伪的目标与预测。
- **数据/算力可行性**：用现有条件能不能做。
- **成果形态**：论文/竞赛/专利/系统。
- **投稿层次**：冲刺/稳妥/保底大致定位（细化交 m13）。
- **风险**：最可能失败的点。用 What-If Oracle 的"精确 IF"写法——把"万一不行"改成可行动的条件句（"若数据量 < N 则 X 失效"），并想最好/最可能/最坏/二阶后果。

## 提交 m04 前的自检
用 ResearchAgent 五维 + AI Scientist 三维快评每个 idea，分低的回炉：
- **五维**（1–5）：清晰度 Clarity、相关性 Relevance、原创性 Originality、可行性 Feasibility、重要性 Significance。
- **三维快评**（1–10）：Interestingness、Feasibility、Novelty（打分谨慎贴近现实）。
- **7 失败模式反向自检**（源自 The AI Scientist 的 Nature 版局限，ARS 整理）：实现 bug、幻觉结果、走捷径、把 bug 当洞见、方法论造假、frame-lock（死锁单一框架）、引用幻觉。重点防 frame-lock（别在一条思路上死磕）与引用幻觉（别编对标工作）。
- 可选多视角互怼（Consciousness Council）：让"对标派 / 可行性派 / 新颖性派 / 工程派"各自挑刺再综合。

## 产出
3–6 个分层 idea（高风险高回报 / 稳妥 / 保底），按潜力排序，附对比表。每个标注成熟度与差异化强度，并带上自检的五维/三维分。

## 强制衔接
所有 idea **必须**送 m04 idea-critique 严审。被毙的 idea 带着 m04 给的方向回到本技能再生成，形成循环。通过的 idea 才进 m05。写入项目库 db09 的 decision_log。

---
方法来源与真实端点/评审维度的逐工具笔记见 [references.md](references.md)。
